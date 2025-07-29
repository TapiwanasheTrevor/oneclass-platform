# =====================================================
# Fast User Context Middleware for High Performance
# Optimized middleware for user context resolution with caching
# File: backend/shared/middleware/fast_user_context_middleware.py
# =====================================================

import asyncio
import json
import logging
from typing import Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime, timedelta
from functools import lru_cache

# FastAPI imports
from fastapi import Request, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Our imports
from shared.cache.user_context_cache import UserContextCache
from shared.services.optimized_user_service import OptimizedUserService, MinimalUserContext
from shared.models.platform_user import PlatformUser, PlatformRole, SchoolRole

logger = logging.getLogger(__name__)


class FastUserContextMiddleware:
    """
    High-performance middleware for user context resolution
    Implements multi-layer caching and optimized queries for minimal latency
    """
    
    def __init__(
        self, 
        cache: UserContextCache, 
        user_service: OptimizedUserService,
        clerk_api_key: Optional[str] = None
    ):
        """
        Initialize middleware with cache and user service
        
        Args:
            cache: UserContextCache instance
            user_service: OptimizedUserService instance
            clerk_api_key: Clerk API key for validation (optional)
        """
        self.cache = cache
        self.user_service = user_service
        self.clerk_api_key = clerk_api_key
        self.logger = logger
        
        # Performance optimization settings
        self.enable_clerk_validation = bool(clerk_api_key)
        self.default_cache_ttl = 300  # 5 minutes
        self.minimal_context_endpoints = {
            '/api/health', '/api/metrics', '/api/status',
            '/api/auth/validate', '/api/auth/refresh'
        }
    
    async def get_user_context(
        self, 
        request: Request,
        minimal: bool = False
    ) -> Optional[Union[PlatformUser, MinimalUserContext]]:
        """
        Get user context with performance optimizations
        
        Args:
            request: FastAPI request object
            minimal: If True, returns lightweight context for better performance
        
        Returns:
            PlatformUser or MinimalUserContext depending on minimal flag
        """
        try:
            # Extract authentication info from request
            auth_info = await self._extract_auth_info(request)
            if not auth_info:
                return None
            
            # Get subdomain for school context
            subdomain = self._extract_subdomain(request)
            school_id = None
            if subdomain:
                school_id = await self._get_school_id_by_subdomain(subdomain)
            
            # Route to appropriate context resolution method
            if minimal or self._is_minimal_context_endpoint(request):
                return await self._get_minimal_context(auth_info, school_id)
            else:
                return await self._get_full_context(auth_info, school_id)
                
        except Exception as e:
            self.logger.error(f"Error getting user context: {e}")
            return None
    
    async def _extract_auth_info(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract authentication information from request"""
        # Try JWT token first
        jwt_token = self._extract_jwt_token(request)
        if jwt_token:
            return {'type': 'jwt', 'token': jwt_token}
        
        # Try Clerk session
        clerk_session = self._extract_clerk_session(request)
        if clerk_session:
            return {'type': 'clerk', 'session_id': clerk_session}
        
        return None
    
    def _extract_jwt_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from Authorization header"""
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None
        
        scheme, token = get_authorization_scheme_param(authorization)
        if scheme.lower() != "bearer":
            return None
        
        return token
    
    def _extract_clerk_session(self, request: Request) -> Optional[str]:
        """Extract Clerk session from headers or cookies"""
        # Check custom header first
        clerk_session = request.headers.get("X-Clerk-Session-Id")
        if clerk_session:
            return clerk_session
        
        # Check cookie
        clerk_session = request.cookies.get("__clerk_session")
        if clerk_session:
            return clerk_session
        
        return None
    
    def _extract_subdomain(self, request: Request) -> Optional[str]:
        """Extract subdomain from request host"""
        host = request.headers.get("host") or ""
        
        # Handle localhost development
        if "localhost" in host or "127.0.0.1" in host:
            # Check for subdomain in custom header for local dev
            return request.headers.get("X-School-Subdomain")
        
        # Extract subdomain from host
        parts = host.split(".")
        if len(parts) >= 3:  # subdomain.domain.com
            return parts[0]
        
        return None
    
    def _is_minimal_context_endpoint(self, request: Request) -> bool:
        """Check if endpoint requires only minimal context"""
        path = request.url.path
        return any(path.startswith(endpoint) for endpoint in self.minimal_context_endpoints)
    
    async def _get_minimal_context(
        self, 
        auth_info: Dict[str, Any], 
        school_id: Optional[UUID]
    ) -> Optional[MinimalUserContext]:
        """Get minimal user context for performance-critical operations"""
        user_id = await self._resolve_user_id(auth_info)
        if not user_id:
            return None
        
        return await self.user_service.get_minimal_user_context(
            user_id, school_id, use_cache=True
        )
    
    async def _get_full_context(
        self, 
        auth_info: Dict[str, Any], 
        school_id: Optional[UUID]
    ) -> Optional[PlatformUser]:
        """Get full user context with all details"""
        user_id = await self._resolve_user_id(auth_info)
        if not user_id:
            return None
        
        user = await self.user_service.get_user_by_id(user_id, use_cache=True)
        
        # Validate school access if school_id is provided
        if school_id and user:
            has_access = await self.user_service.check_user_school_access(user_id, school_id)
            if not has_access:
                self.logger.warning(f"User {user_id} denied access to school {school_id}")
                return None
        
        return user
    
    async def _resolve_user_id(self, auth_info: Dict[str, Any]) -> Optional[UUID]:
        """Resolve user ID from authentication info"""
        if auth_info['type'] == 'jwt':
            return await self._resolve_user_id_from_jwt(auth_info['token'])
        elif auth_info['type'] == 'clerk':
            return await self._resolve_user_id_from_clerk(auth_info['session_id'])
        
        return None
    
    async def _resolve_user_id_from_jwt(self, token: str) -> Optional[UUID]:
        """Resolve user ID from JWT token"""
        try:
            # This would integrate with your JWT validation logic
            # For now, we'll use a placeholder implementation
            from shared.auth import validate_token
            
            token_data = await validate_token(token)
            user_id = token_data.get("sub")
            return UUID(user_id) if user_id else None
            
        except Exception as e:
            self.logger.warning(f"Error validating JWT token: {e}")
            return None
    
    async def _resolve_user_id_from_clerk(self, session_id: str) -> Optional[UUID]:
        """Resolve user ID from Clerk session"""
        try:
            # Check cache first
            cached_user_id = await self.cache.get_user_by_clerk_id(session_id)
            if cached_user_id:
                return cached_user_id
            
            # Validate with Clerk API
            clerk_user = await self._validate_clerk_session(session_id)
            if not clerk_user:
                return None
            
            # Get platform user ID from Clerk user ID
            user = await self.user_service.get_user_by_clerk_id(
                clerk_user['id'], use_cache=True
            )
            
            if user:
                # Cache the session -> user_id mapping
                await self.cache.set_user_by_clerk_id(session_id, user.id)
                return user.id
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error resolving Clerk session {session_id}: {e}")
            return None
    
    @lru_cache(maxsize=1000)
    async def _validate_clerk_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate Clerk session with caching"""
        if not self.enable_clerk_validation:
            # In development, return mock data
            return {
                'id': 'clerk_user_' + session_id[:8],
                'email': f'user+{session_id[:8]}@example.com',
                'verified': True
            }
        
        try:
            # Check cache first
            cached_user = await self.cache.get_clerk_user(session_id)
            if cached_user:
                return cached_user
            
            # Validate with Clerk API
            # This would be implemented with actual Clerk SDK calls
            # import clerk
            # clerk_client = clerk.Client(api_key=self.clerk_api_key)
            # user_data = await clerk_client.sessions.verify(session_id)
            
            # For now, return None (implement with real Clerk integration)
            return None
            
        except Exception as e:
            self.logger.error(f"Error validating Clerk session {session_id}: {e}")
            return None
    
    async def _get_school_id_by_subdomain(self, subdomain: str) -> Optional[UUID]:
        """Get school ID from subdomain with caching"""
        try:
            # Check cache first
            cached_school_id = await self.cache.get_school_by_subdomain(subdomain)
            if cached_school_id:
                return cached_school_id
            
            # Query database through user service
            # This would need to be implemented in the user service
            # For now, return None
            return None
            
        except Exception as e:
            self.logger.warning(f"Error resolving subdomain {subdomain}: {e}")
            return None


class FastUserContextHTTPMiddleware(BaseHTTPMiddleware):
    """
    HTTP Middleware wrapper for FastUserContextMiddleware
    Automatically adds user context to request state
    """
    
    def __init__(
        self, 
        app, 
        cache: UserContextCache, 
        user_service: OptimizedUserService,
        clerk_api_key: Optional[str] = None
    ):
        super().__init__(app)
        self.context_middleware = FastUserContextMiddleware(
            cache, user_service, clerk_api_key
        )
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add user context to request state"""
        start_time = datetime.utcnow()
        
        try:
            # Skip auth for public endpoints
            if self._is_public_endpoint(request):
                request.state.user = None
                request.state.user_context = None
                response = await call_next(request)
                return response
            
            # Determine if minimal context is sufficient
            minimal = self._should_use_minimal_context(request)
            
            # Get user context
            user_context = await self.context_middleware.get_user_context(
                request, minimal=minimal
            )
            
            # Add to request state
            request.state.user = user_context
            request.state.user_context = user_context
            request.state.auth_method = 'fast_middleware'
            
            # Process request
            response = await call_next(request)
            
            # Add performance headers
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            response.headers["X-Auth-Time"] = f"{elapsed:.3f}s"
            response.headers["X-Auth-Method"] = "fast_middleware"
            if minimal:
                response.headers["X-Context-Type"] = "minimal"
            
            return response
            
        except Exception as e:
            logger.error(f"Error in FastUserContextHTTPMiddleware: {e}")
            # Continue without auth context
            request.state.user = None
            request.state.user_context = None
            response = await call_next(request)
            response.headers["X-Auth-Error"] = "middleware_error"
            return response
    
    def _is_public_endpoint(self, request: Request) -> bool:
        """Check if endpoint is public and doesn't require authentication"""
        public_paths = {
            '/docs', '/redoc', '/openapi.json',
            '/health', '/metrics',
            '/api/auth/login', '/api/auth/register',
            '/api/public/'
        }
        
        path = request.url.path
        return any(path.startswith(public_path) for public_path in public_paths)
    
    def _should_use_minimal_context(self, request: Request) -> bool:
        """Determine if minimal context is sufficient for this request"""
        # Use minimal context for:
        # - GET requests to list endpoints
        # - Health checks and monitoring
        # - Quick validation endpoints
        
        path = request.url.path
        method = request.method
        
        if method == "GET" and any(segment in path for segment in ['/list', '/search', '/count']):
            return True
        
        if any(path.startswith(endpoint) for endpoint in ['/api/health', '/api/auth/validate']):
            return True
        
        return False


# Dependency functions for FastAPI

async def get_current_user_fast(request: Request) -> Optional[PlatformUser]:
    """
    FastAPI dependency to get current user from fast middleware
    Returns full PlatformUser object
    """
    if not hasattr(request.state, 'user_context'):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="FastUserContextMiddleware not configured"
        )
    
    user_context = request.state.user_context
    if not user_context:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # If we have minimal context but need full user, upgrade
    if isinstance(user_context, MinimalUserContext):
        # This would require access to user service - implement as needed
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Full user context required but only minimal available"
        )
    
    return user_context


async def get_current_user_minimal(request: Request) -> Optional[MinimalUserContext]:
    """
    FastAPI dependency to get current user minimal context
    Much faster for simple operations
    """
    if not hasattr(request.state, 'user_context'):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="FastUserContextMiddleware not configured"
        )
    
    user_context = request.state.user_context
    if not user_context:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Convert full user to minimal if needed
    if isinstance(user_context, PlatformUser):
        primary_membership = user_context.get_primary_school_membership()
        return MinimalUserContext(
            user_id=user_context.id,
            email=user_context.email,
            full_name=user_context.full_name,
            platform_role=user_context.platform_role,
            school_role=primary_membership.role if primary_membership else None,
            school_id=user_context.primary_school_id,
            permissions=primary_membership.permissions if primary_membership else [],
            is_active=user_context.is_active
        )
    
    return user_context


async def get_optional_user(request: Request) -> Optional[Union[PlatformUser, MinimalUserContext]]:
    """
    FastAPI dependency to get current user if available, None if not authenticated
    Useful for endpoints that work for both authenticated and anonymous users
    """
    if not hasattr(request.state, 'user_context'):
        return None
    
    return request.state.user_context


def require_role(required_role: PlatformRole):
    """
    Decorator to require specific platform role
    
    Usage:
        @require_role(PlatformRole.SUPER_ADMIN)
        async def admin_only_endpoint():
            pass
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user context from function args
            user_context = None
            for arg in args:
                if isinstance(arg, (PlatformUser, MinimalUserContext)):
                    user_context = arg
                    break
            
            if not user_context:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if user_context.platform_role != required_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role {required_role.value} required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_school_role(required_role: SchoolRole):
    """
    Decorator to require specific school role
    
    Usage:
        @require_school_role(SchoolRole.TEACHER)
        async def teacher_only_endpoint():
            pass
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user context from function args
            user_context = None
            for arg in args:
                if isinstance(arg, (PlatformUser, MinimalUserContext)):
                    user_context = arg
                    break
            
            if not user_context:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not user_context.school_role or user_context.school_role != required_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"School role {required_role.value} required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator