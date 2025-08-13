"""
Enhanced Tenant Middleware
Uses the new tenant resolver for robust multi-tenant support
"""

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Optional, Dict, Any
import logging
from datetime import datetime

from shared.auth import verify_token, UserSession
from shared.database import set_current_school_id
from .resolver import get_tenant_resolver, TenantResolution, SubdomainPattern

logger = logging.getLogger(__name__)


class EnhancedTenantContext:
    """Enhanced context object for tenant information"""
    
    def __init__(
        self,
        resolution: TenantResolution,
        user_session: Optional[UserSession] = None,
        request_id: Optional[str] = None
    ):
        # Core tenant info from resolution
        self.school_id = resolution.school_id
        self.school_name = resolution.school_name
        self.subdomain = resolution.subdomain
        self.subscription_tier = resolution.subscription_tier
        self.enabled_modules = resolution.enabled_modules
        
        # Enhanced properties
        self.pattern = resolution.pattern
        self.custom_domain = resolution.custom_domain
        self.is_active = resolution.is_active
        self.cache_key = resolution.cache_key
        self.resolved_at = resolution.resolved_at
        
        # Request context
        self.user_session = user_session
        self.request_id = request_id
        self.timestamp = datetime.utcnow()
        
        # Multi-school support
        self.user_school_memberships = []
        self.is_school_switch = False
        self.original_school_id = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary"""
        return {
            "school_id": self.school_id,
            "school_name": self.school_name,
            "subdomain": self.subdomain,
            "subscription_tier": self.subscription_tier,
            "enabled_modules": self.enabled_modules,
            "pattern": self.pattern.value,
            "custom_domain": self.custom_domain,
            "is_active": self.is_active,
            "user_session": self.user_session.dict() if self.user_session else None,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "user_school_memberships": len(self.user_school_memberships),
            "is_school_switch": self.is_school_switch
        }
    
    def has_module_access(self, module_name: str) -> bool:
        """Check if tenant has access to a module"""
        return module_name in self.enabled_modules
    
    def is_development_mode(self) -> bool:
        """Check if running in development mode"""
        return self.pattern in [SubdomainPattern.LOCALHOST_DEV, SubdomainPattern.IP_ACCESS]


class EnhancedTenantMiddleware(BaseHTTPMiddleware):
    """Enhanced middleware for tenant isolation and context injection"""
    
    def __init__(self, app, enable_caching: bool = True):
        super().__init__(app)
        self.enable_caching = enable_caching
        
        # Routes that don't require tenant context
        self.public_routes = {
            '/',
            '/health',
            '/docs',
            '/redoc', 
            '/openapi.json',
            '/api/health',
            '/api/v1/platform/schools',
            '/api/v1/platform/schools/by-subdomain',
            '/api/v1/platform/schools/validate-subdomain',
            '/api/v1/platform/schools/suggest-subdomains',
            '/api/v1/schools/validate-subdomain',
            '/api/v1/schools/suggest-subdomains',
            '/api/v1/schools/by-subdomain',
            '/api/v1/schools/onboard',
            '/api/v1/auth/login',
            '/api/v1/auth/signup',
            '/api/v1/auth/refresh',
            '/api/v1/auth/logout'
        }
        
        # Platform admin routes (no tenant isolation)
        self.platform_routes = {
            '/api/v1/platform',
            '/api/v1/admin'
        }
        
        # Public platform routes
        self.public_platform_routes = {
            '/api/v1/platform/schools/public',
            '/api/v1/platform/schools/by-subdomain',
            '/api/v1/platform/schools/subdomain-check',
            '/api/v1/platform/schools/health',
            '/api/v1/platform/schools-simple',
            '/api/v1/platform/tenant/stats'
        }
        
        # School switching routes
        self.school_switch_routes = {
            '/api/v1/user/schools',
            '/api/v1/user/switch-school',
            '/api/v1/user/current-school'
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with enhanced tenant context"""
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
                await self._validate_platform_admin(request)
                response = await call_next(request)
                self._add_response_headers(response, request_id=request_id)
                return response
            
            # Extract tenant context using enhanced resolver
            tenant_context = await self._extract_enhanced_tenant_context(request)
            
            if not tenant_context:
                return self._create_tenant_error_response(request_id, "tenant_not_found")
            
            # Check if school is active
            if not tenant_context.is_active:
                return self._create_tenant_error_response(
                    request_id, 
                    "school_inactive",
                    f"School '{tenant_context.school_name}' is currently inactive"
                )
            
            # Handle school switching requests
            if self._is_school_switch_route(request.url.path):
                tenant_context = await self._handle_school_switch(request, tenant_context)
            
            # Inject enhanced tenant context into request state
            request.state.tenant = tenant_context
            request.state.school_id = tenant_context.school_id
            
            # Set up database context with RLS
            await self._setup_database_context(request, tenant_context)
            
            # Validate module access
            if not self._validate_module_access(request, tenant_context):
                return self._create_module_access_error(request_id, tenant_context)
            
            # Process request
            response = await call_next(request)
            
            # Add enhanced tenant context to response headers
            self._add_response_headers(
                response,
                tenant_context=tenant_context,
                request_id=request_id
            )
            
            # Log request completion with performance metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._log_request_completion(request, tenant_context, duration)
            
            return response
            
        except Exception as e:
            logger.error(
                f"Enhanced tenant middleware error: {str(e)} - {request.method} {request.url.path}",
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
    
    # =====================================================
    # ENHANCED TENANT RESOLUTION
    # =====================================================
    
    async def _extract_enhanced_tenant_context(
        self, 
        request: Request
    ) -> Optional[EnhancedTenantContext]:
        """Extract tenant context using enhanced resolver"""
        
        try:
            # Get host and headers
            host = request.headers.get('host', '')
            headers = dict(request.headers)
            
            # Check for force refresh parameter (for admin/debug)
            force_refresh = request.query_params.get('force_tenant_refresh') == 'true'
            
            # Use enhanced resolver
            resolver = get_tenant_resolver()
            resolution = await resolver.resolve_tenant(
                host=host,
                headers=headers,
                force_refresh=force_refresh
            )
            
            if not resolution:
                return None
            
            # Extract user session
            user_session = await self._extract_user_session(request)
            
            # Create enhanced context
            context = EnhancedTenantContext(
                resolution=resolution,
                user_session=user_session,
                request_id=request.state.request_id
            )
            
            # If user is authenticated, load their school memberships
            if user_session:
                await self._load_user_school_memberships(context)
            
            return context
            
        except Exception as e:
            logger.error(f"Error extracting enhanced tenant context: {e}")
            return None
    
    async def _load_user_school_memberships(self, context: EnhancedTenantContext):
        """Load user's school memberships for multi-school support"""
        
        if not context.user_session:
            return
        
        try:
            from shared.database import get_async_session
            from sqlalchemy import text
            
            async for db in get_async_session():
                query = text("""
                    SELECT 
                        sm.school_id,
                        sm.school_name,
                        sm.school_subdomain,
                        sm.role,
                        sm.status,
                        s.subscription_tier
                    FROM platform.school_memberships sm
                    JOIN platform.schools s ON sm.school_id = s.id
                    WHERE sm.user_id = :user_id 
                        AND sm.status = 'active'
                        AND s.is_active = true
                    ORDER BY sm.school_name
                """)
                
                result = await db.execute(query, {"user_id": context.user_session.user_id})
                
                memberships = []
                for row in result:
                    memberships.append({
                        'school_id': str(row.school_id),
                        'school_name': row.school_name,
                        'school_subdomain': row.school_subdomain,
                        'role': row.role,
                        'status': row.status,
                        'subscription_tier': row.subscription_tier,
                        'is_current': str(row.school_id) == context.school_id
                    })
                
                context.user_school_memberships = memberships
                
        except Exception as e:
            logger.warning(f"Error loading user school memberships: {e}")
    
    # =====================================================
    # SCHOOL SWITCHING SUPPORT
    # =====================================================
    
    async def _handle_school_switch(
        self, 
        request: Request, 
        context: EnhancedTenantContext
    ) -> EnhancedTenantContext:
        """Handle school switching requests"""
        
        # Check for school switch in headers or request body
        target_school_id = request.headers.get('x-target-school-id')
        
        if not target_school_id:
            # Check request body for POST requests
            if request.method == 'POST':
                try:
                    body = await request.json()
                    target_school_id = body.get('target_school_id')
                except:
                    pass
        
        if target_school_id and target_school_id != context.school_id:
            # Validate user has access to target school
            target_membership = None
            for membership in context.user_school_memberships:
                if membership['school_id'] == target_school_id:
                    target_membership = membership
                    break
            
            if target_membership:
                # Create new context for target school
                resolver = get_tenant_resolver()
                target_resolution = await resolver.resolve_tenant(
                    host=f"{target_membership['school_subdomain']}.oneclass.ac.zw"
                )
                
                if target_resolution:
                    new_context = EnhancedTenantContext(
                        resolution=target_resolution,
                        user_session=context.user_session,
                        request_id=context.request_id
                    )
                    
                    new_context.user_school_memberships = context.user_school_memberships
                    new_context.is_school_switch = True
                    new_context.original_school_id = context.school_id
                    
                    return new_context
        
        return context
    
    # =====================================================
    # VALIDATION METHODS
    # =====================================================
    
    async def _extract_user_session(self, request: Request) -> Optional[UserSession]:
        """Extract user session from Authorization token or secure cookie"""
        
        # Check Authorization header
        auth_header = request.headers.get('authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
            return await verify_token(token)
        
        # Check cookies
        token = request.cookies.get('auth-token')
        if token:
            return await verify_token(token)
        
        return None
    
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
    
    def _validate_module_access(
        self, 
        request: Request, 
        tenant_context: EnhancedTenantContext
    ) -> bool:
        """Validate if the requested module is available for the tenant"""
        
        path = request.url.path
        
        # Extract module from path
        if '/finance/' in path or path.startswith('/api/v1/finance'):
            return tenant_context.has_module_access('finance_management')
        elif '/academic/' in path or path.startswith('/api/v1/academic'):
            return tenant_context.has_module_access('academic_management')
        elif '/sis/' in path or path.startswith('/api/v1/sis'):
            return tenant_context.has_module_access('student_information_system')
        elif '/lms/' in path or path.startswith('/api/v1/lms'):
            return tenant_context.has_module_access('learning_management')
        elif '/hr/' in path or path.startswith('/api/v1/hr'):
            return tenant_context.has_module_access('human_resources')
        
        # Default: allow access for non-module-specific routes
        return True
    
    # =====================================================
    # ROUTE CLASSIFICATION
    # =====================================================
    
    def _is_public_route(self, path: str) -> bool:
        """Check if route is public"""
        return any(path.startswith(route) or path == route for route in self.public_routes)
    
    def _is_platform_route(self, path: str) -> bool:
        """Check if route is platform admin route"""
        return any(path.startswith(route) for route in self.platform_routes)
    
    def _is_public_platform_route(self, path: str) -> bool:
        """Check if route is public platform route"""
        return any(path.startswith(route) or path == route for route in self.public_platform_routes)
    
    def _is_school_switch_route(self, path: str) -> bool:
        """Check if route is school switching route"""
        return any(path.startswith(route) or path == route for route in self.school_switch_routes)
    
    # =====================================================
    # ERROR HANDLING
    # =====================================================
    
    def _create_tenant_error_response(
        self, 
        request_id: str, 
        error_code: str, 
        message: str = None
    ) -> JSONResponse:
        """Create standardized tenant error response"""
        
        error_messages = {
            "tenant_not_found": "Unable to determine school context for this request",
            "school_inactive": "School is currently inactive",
            "module_not_available": "The requested module is not available in your subscription"
        }
        
        return JSONResponse(
            status_code=400 if error_code == "tenant_not_found" else 403,
            content={
                "error": error_code,
                "message": message or error_messages.get(error_code, "Tenant resolution error"),
                "request_id": request_id
            }
        )
    
    def _create_module_access_error(
        self, 
        request_id: str, 
        tenant_context: EnhancedTenantContext
    ) -> JSONResponse:
        """Create module access error response"""
        
        return JSONResponse(
            status_code=403,
            content={
                "error": "module_not_available",
                "message": "The requested module is not available in your subscription",
                "subscription_tier": tenant_context.subscription_tier,
                "enabled_modules": tenant_context.enabled_modules,
                "school_id": tenant_context.school_id,
                "request_id": request_id
            }
        )
    
    # =====================================================
    # UTILITY METHODS
    # =====================================================
    
    async def _setup_database_context(
        self, 
        request: Request, 
        tenant_context: EnhancedTenantContext
    ):
        """Set up database context for Row Level Security"""
        set_current_school_id(tenant_context.school_id)
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _add_response_headers(
        self,
        response: Response,
        tenant_context: Optional[EnhancedTenantContext] = None,
        request_id: Optional[str] = None
    ):
        """Add enhanced tenant context and tracking headers to response"""
        
        if request_id:
            response.headers['X-Request-ID'] = request_id
        
        if tenant_context:
            response.headers['X-Tenant-ID'] = tenant_context.school_id
            response.headers['X-Tenant-Name'] = tenant_context.school_name
            response.headers['X-Tenant-Tier'] = tenant_context.subscription_tier
            response.headers['X-Tenant-Pattern'] = tenant_context.pattern.value
            
            if tenant_context.is_school_switch:
                response.headers['X-School-Switch'] = 'true'
                response.headers['X-Original-School'] = tenant_context.original_school_id or ''
            
            if tenant_context.cache_key:
                response.headers['X-Cache-Key'] = tenant_context.cache_key
        
        response.headers['X-Service'] = 'oneclass-platform'
        response.headers['X-Timestamp'] = datetime.utcnow().isoformat()
    
    def _log_request_completion(
        self,
        request: Request,
        tenant_context: EnhancedTenantContext,
        duration: float
    ):
        """Log request completion with enhanced metrics"""
        
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"[{tenant_context.school_name}:{tenant_context.school_id}] "
            f"[{tenant_context.pattern.value}] "
            f"- {duration:.3f}s"
        )


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def get_enhanced_tenant_context(request: Request) -> EnhancedTenantContext:
    """Get enhanced tenant context from request state"""
    if not hasattr(request.state, 'tenant'):
        raise HTTPException(
            status_code=500,
            detail={
                "error": "missing_tenant_context",
                "message": "Enhanced tenant context not found in request"
            }
        )
    
    return request.state.tenant


def get_school_id(request: Request) -> str:
    """Get school ID from request state"""
    tenant = get_enhanced_tenant_context(request)
    return tenant.school_id


def get_user_session(request: Request) -> Optional[UserSession]:
    """Get user session from request state"""
    tenant = get_enhanced_tenant_context(request)
    return tenant.user_session