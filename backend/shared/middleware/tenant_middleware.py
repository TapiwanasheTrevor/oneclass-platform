"""Tenant Isolation Middleware
Middleware for multi-tenant request processing and data isolation"""

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import Callable, Optional, Dict, Any
import re
import logging
from datetime import datetime

from shared.models.platform import School
from shared.auth import verify_token, validate_token, UserSession, db_manager
from shared.database import set_current_school_id

logger = logging.getLogger(__name__)


class TenantContext:
    """Context object for tenant information"""
    
    def __init__(
        self,
        school_id: str,
        school_name: str,
        subdomain: str,
        subscription_tier: str,
        enabled_modules: list,
        user_session: Optional[UserSession] = None
    ):
        self.school_id = school_id
        self.school_name = school_name
        self.subdomain = subdomain
        self.subscription_tier = subscription_tier
        self.enabled_modules = enabled_modules
        self.user_session = user_session
        self.request_id = None
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "school_id": self.school_id,
            "school_name": self.school_name,
            "subdomain": self.subdomain,
            "subscription_tier": self.subscription_tier,
            "enabled_modules": self.enabled_modules,
            "user_session": self.user_session.dict() if self.user_session else None,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat()
        }


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware for tenant isolation and context injection"""
    
    def __init__(self, app, db_session_factory=None):
        super().__init__(app)
        self.db_session_factory = db_session_factory or self._get_db_connection
        
        # Routes that don't require tenant context
        self.public_routes = {
            '/',
            '/health',
            '/docs',
            '/redoc',
            '/openapi.json',
            '/api/health',
            '/api/v1/platform/schools',  # School creation
            '/api/v1/platform/schools/by-subdomain',  # Subdomain lookup
            '/api/v1/schools/validate-subdomain',
            '/api/v1/schools/suggest-subdomains',
            '/api/v1/schools/by-subdomain',
            '/api/v1/schools/onboard',
            '/api/v1/auth/login',
            '/api/v1/auth/signup',
            '/api/v1/auth/refresh',
            '/api/v1/sis/health',
            '/api/v1/analytics/health'
        }
        
        # Platform admin routes (no tenant isolation)
        self.platform_routes = {
            '/api/v1/platform',
            '/api/v1/admin'
        }

        # Public routes that don't need tenant context
        self.public_platform_routes = {
            '/api/v1/platform/schools/public',
            '/api/v1/platform/schools/by-subdomain',
            '/api/v1/platform/schools/subdomain-check',
            '/api/v1/platform/schools/health',
            '/api/v1/platform/schools-simple'
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with tenant context"""
        start_time = datetime.utcnow()
        
        # Generate request ID for tracing
        request_id = self._generate_request_id()
        request.state.request_id = request_id
        
        try:
            # Skip tenant processing for public routes
            if self._is_public_route(request.url.path):
                response = await call_next(request)
                self._add_response_headers(response, request_id=request_id)
                return response

            # Skip tenant processing for public platform routes
            if self._is_public_platform_route(request.url.path):
                response = await call_next(request)
                self._add_response_headers(response, request_id=request_id)
                return response

            # Skip tenant processing for platform admin routes
            if self._is_platform_route(request.url.path):
                # Still validate platform admin authentication
                await self._validate_platform_admin(request)
                response = await call_next(request)
                self._add_response_headers(response, request_id=request_id)
                return response
            
            # Extract tenant context
            tenant_context = await self._extract_tenant_context(request)
            
            if not tenant_context:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "missing_tenant_context",
                        "message": "Unable to determine school context for this request",
                        "request_id": request_id
                    }
                )
            
            # Inject tenant context into request state
            request.state.tenant = tenant_context
            request.state.school_id = tenant_context.school_id
            
            # Set up database session with RLS context
            await self._setup_database_context(request, tenant_context)
            
            # Validate module access
            if not self._validate_module_access(request, tenant_context):
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "module_not_available",
                        "message": "The requested module is not available in your subscription",
                        "subscription_tier": tenant_context.subscription_tier,
                        "request_id": request_id
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add tenant context to response headers
            self._add_response_headers(
                response, 
                tenant_context=tenant_context,
                request_id=request_id
            )
            
            # Log request completion
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"[{tenant_context.school_id}] - {duration:.3f}s"
            )
            
            return response
            
        except Exception as e:
            logger.error(
                f"Tenant middleware error: {str(e)} - {request.method} {request.url.path}",
                exc_info=True
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "tenant_middleware_error",
                    "message": "An error occurred while processing tenant context",
                    "request_id": request_id
                }
            )
    
    async def _extract_tenant_context(self, request: Request) -> Optional[TenantContext]:
        """Extract tenant context from trusted sources only (Host/JWT)."""
        # Do NOT trust client-provided X-* headers for tenant resolution

        # 1) Extract from subdomain in host header (primary)
        host = request.headers.get('host', '')
        subdomain = self._extract_subdomain_from_host(host)

        if subdomain:
            return await self._get_tenant_by_subdomain(subdomain, request)

        # 2) Fallback: try to extract from JWT token (must be validated later)
        jwt_context = await self._extract_from_jwt_token(request)
        if jwt_context:
            return jwt_context

        # Development mode: if localhost, try to get user's primary school
        if self._is_development_mode(request):
            return await self._get_development_tenant_context(request)

        return None

    async def _extract_from_jwt_token(self, request: Request) -> Optional[TenantContext]:
        """Extract tenant context from JWT token as fallback"""
        try:
            # Get authorization header
            auth_header = request.headers.get('authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return None

            # Extract and validate token
            token = auth_header.split(' ')[1]
            payload = await validate_token(token)

            # Extract school information from JWT
            school_id = payload.get('school_id')
            if not school_id:
                return None

            # Get school details from database
            from shared.database import get_async_session
            from sqlalchemy import select, text

            async for db in get_async_session():
                # Get school information
                school_query = text("""
                    SELECT id, name, subdomain, subscription_tier
                    FROM platform.schools
                    WHERE id = :school_id
                """)
                result = await db.execute(school_query, {"school_id": school_id})
                school = result.fetchone()

                if not school:
                    return None

                # Get enabled modules for this school
                enabled_modules = await self._get_school_modules(school_id)

                # Create user session from JWT payload (minimal; full context via verify_token elsewhere)
                user_session = UserSession(
                    user_id=payload.get('sub'),
                    role=payload.get('school_role', 'student'),
                    permissions=[],
                    features=[],
                    school_id=school_id
                )

                return TenantContext(
                    school_id=school_id,
                    school_name=school.name,
                    subdomain=school.subdomain,
                    subscription_tier=school.subscription_tier or 'basic',
                    enabled_modules=enabled_modules,
                    user_session=user_session
                )

        except Exception as e:
            # Log error but don't fail the request
            print(f"Error extracting tenant context from JWT: {e}")
            return None

    async def _extract_user_session(self, request: Request) -> Optional[UserSession]:
        """Extract user session from Authorization token or secure cookie only."""
        # Only accept Authorization or secure cookie, not client-provided headers
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
            return await verify_token(token)
        
        # Try cookies
        token = request.cookies.get('auth-token')
        if token:
            return await verify_token(token)
        
        return None
    
    async def _get_db_connection(self):
        """Get database connection using auth module's db manager"""
        return db_manager.get_connection()
    
    async def _get_tenant_by_subdomain(self, subdomain: str, request: Request) -> Optional[TenantContext]:
        """Get tenant context by subdomain"""
        async with db_manager.get_connection() as db:
            query = """
                SELECT id, name, subdomain, subscription_tier, status, is_active
                FROM platform.schools 
                WHERE subdomain = $1 AND is_active = true
            """
            
            result = await db.fetchrow(query, subdomain.lower())
            
            if not result:
                return None
            
            enabled_modules = await self._get_school_modules(str(result["id"]))
            user_session = await self._extract_user_session(request)
            
            return TenantContext(
                school_id=str(result["id"]),
                school_name=result["name"],
                subdomain=result["subdomain"],
                subscription_tier=result["subscription_tier"] or "basic",
                enabled_modules=enabled_modules,
                user_session=user_session
            )
    
    async def _get_school_modules(self, school_id: str) -> list:
        """Get enabled modules for school"""
        try:
            async with db_manager.get_connection() as db:
                # Fetch enabled modules from school configuration
                query = """
                    SELECT sc.enabled_modules
                    FROM platform.school_configurations sc
                    WHERE sc.school_id = $1
                """
                result = await db.fetchval(query, school_id)
                
                if result:
                    # Parse JSON string if needed
                    if isinstance(result, str):
                        import json
                        try:
                            return json.loads(result)
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in enabled_modules for school {school_id}")
                    elif isinstance(result, list):
                        return result
                
                # Fallback to default modules if no configuration found
                return [
                    'student_information_system',
                    'finance_management',
                    'academic_management'
                ]
        except Exception as e:
            logger.warning(f"Failed to fetch school modules for {school_id}: {e}")
            # Return default modules on error
            return [
                'student_information_system',
                'finance_management',
                'academic_management'
            ]
    
    async def _setup_database_context(self, request: Request, tenant_context: TenantContext):
        """Set up database context for Row Level Security by setting contextvar."""
        set_current_school_id(tenant_context.school_id)
    
    async def _validate_platform_admin(self, request: Request):
        """Validate platform admin access"""
        user_session = await self._extract_user_session(request)
        
        if not user_session or user_session.role != 'platform_admin':
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "platform_admin_required",
                    "message": "Platform administrator access required"
                }
            )
    
    def _validate_module_access(self, request: Request, tenant_context: TenantContext) -> bool:
        """Validate if the requested module is available for the tenant"""
        path = request.url.path
        
        # Extract module from path
        if '/finance/' in path or path.startswith('/api/v1/finance'):
            return 'finance_management' in tenant_context.enabled_modules
        elif '/academic/' in path or path.startswith('/api/v1/academic'):
            return 'academic_management' in tenant_context.enabled_modules
        elif '/sis/' in path or path.startswith('/api/v1/sis'):
            return 'student_information_system' in tenant_context.enabled_modules
        
        # Default: allow access
        return True
    
    def _is_public_route(self, path: str) -> bool:
        """Check if route is public"""
        return any(path.startswith(route) for route in self.public_routes)
    
    def _is_platform_route(self, path: str) -> bool:
        """Check if route is platform admin route"""
        return any(path.startswith(route) for route in self.platform_routes)

    def _is_public_platform_route(self, path: str) -> bool:
        """Check if route is public platform route (no tenant context needed)"""
        # Check exact matches and path prefixes
        for route in self.public_platform_routes:
            if path == route or path.startswith(route + '/'):
                return True
        return False
    
    def _extract_subdomain_from_host(self, host: str) -> Optional[str]:
        """Extract subdomain from host header"""
        if not host:
            return None
        
        # Remove port if present
        clean_host = host.split(':')[0]
        
        # Skip localhost
        if clean_host in ['localhost', '127.0.0.1']:
            return None
        
        parts = clean_host.split('.')
        if len(parts) >= 3 and parts[0] != 'www':
            return parts[0]
        
        return None
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _add_response_headers(
        self, 
        response: Response, 
        tenant_context: Optional[TenantContext] = None,
        request_id: Optional[str] = None
    ):
        """Add tenant context and tracking headers to response"""
        if request_id:
            response.headers['X-Request-ID'] = request_id
        
        if tenant_context:
            response.headers['X-Tenant-ID'] = tenant_context.school_id
            response.headers['X-Tenant-Name'] = tenant_context.school_name
            response.headers['X-Tenant-Tier'] = tenant_context.subscription_tier
        
        response.headers['X-Service'] = 'oneclass-platform'
        response.headers['X-Timestamp'] = datetime.utcnow().isoformat()


# Helper function to get tenant context from request
def get_tenant_context(request: Request) -> TenantContext:
    """Get tenant context from request state"""
    if not hasattr(request.state, 'tenant'):
        raise HTTPException(
            status_code=500,
            detail={
                "error": "missing_tenant_context",
                "message": "Tenant context not found in request"
            }
        )
    
    return request.state.tenant


# Helper function to get school ID from request
def get_school_id(request: Request) -> str:
    """Get school ID from request state"""
    tenant = get_tenant_context(request)
    return tenant.school_id


# Helper function to get user session from request
def get_user_session(request: Request) -> Optional[UserSession]:
    """Get user session from request state"""
    tenant = get_tenant_context(request)
    return tenant.user_session
