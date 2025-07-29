"""
API Gateway Router
Central routing for all OneClass Platform API endpoints
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

from shared.middleware.tenant_middleware import get_tenant_context, get_school_id, get_user_session
from .platform import platform_router

logger = logging.getLogger(__name__)

# Create main API router
api_router = APIRouter(prefix="/api/v1", tags=["API Gateway"])

# Include sub-routers
api_router.include_router(platform_router, prefix="")

@api_router.get("/status")
async def api_status(request: Request):
    """API Gateway status with tenant context"""
    try:
        tenant = get_tenant_context(request)
        user_session = get_user_session(request)
        
        return {
            "status": "operational",
            "service": "oneclass-platform-api",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "tenant": {
                "school_id": tenant.school_id,
                "school_name": tenant.school_name,
                "subscription_tier": tenant.subscription_tier,
                "enabled_modules": tenant.enabled_modules
            },
            "user": {
                "user_id": user_session.user_id if user_session else None,
                "role": user_session.role if user_session else None,
                "authenticated": user_session is not None
            }
        }
    except HTTPException:
        # Public endpoint, no tenant context required
        return {
            "status": "operational",
            "service": "oneclass-platform-api",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "tenant": None,
            "user": None
        }

@api_router.get("/tenant/info")
async def tenant_info(request: Request):
    """Get current tenant information"""
    tenant = get_tenant_context(request)
    
    return {
        "school_id": tenant.school_id,
        "school_name": tenant.school_name,
        "subdomain": tenant.subdomain,
        "subscription_tier": tenant.subscription_tier,
        "enabled_modules": tenant.enabled_modules,
        "timestamp": tenant.timestamp.isoformat()
    }

@api_router.get("/user/context")
async def user_context(request: Request):
    """Get current user context"""
    tenant = get_tenant_context(request)
    user_session = get_user_session(request)
    
    if not user_session:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "user_not_authenticated",
                "message": "User authentication required"
            }
        )
    
    return {
        "user_id": user_session.user_id,
        "role": user_session.role,
        "permissions": user_session.permissions,
        "features": user_session.features,
        "school_context": {
            "school_id": tenant.school_id,
            "school_name": tenant.school_name,
            "subscription_tier": tenant.subscription_tier
        }
    }

@api_router.get("/modules/available")
async def available_modules(request: Request):
    """Get available modules for current tenant"""
    tenant = get_tenant_context(request)
    
    # Module definitions with feature requirements
    all_modules = {
        "student_information_system": {
            "name": "Student Information System",
            "description": "Student enrollment, records, and management",
            "tier_required": "basic",
            "routes": ["/api/v1/sis/*"]
        },
        "finance_management": {
            "name": "Finance & Billing",
            "description": "Fee management, invoicing, and payments",
            "tier_required": "basic",
            "routes": ["/api/v1/finance/*"]
        },
        "academic_management": {
            "name": "Academic Management",
            "description": "Courses, grades, timetables, and assessments",
            "tier_required": "basic",
            "routes": ["/api/v1/academic/*"]
        },
        "advanced_reporting": {
            "name": "Advanced Analytics & Reporting",
            "description": "Detailed insights and custom reports",
            "tier_required": "professional",
            "routes": ["/api/v1/analytics/*", "/api/v1/reports/*"]
        },
        "communication_hub": {
            "name": "Communication Hub",
            "description": "Messaging, notifications, and announcements",
            "tier_required": "professional",
            "routes": ["/api/v1/communication/*"]
        },
        "parent_portal": {
            "name": "Parent Portal",
            "description": "Parent access and engagement tools",
            "tier_required": "professional",
            "routes": ["/api/v1/parent/*"]
        },
        "api_access": {
            "name": "API Access",
            "description": "Third-party integrations and webhooks",
            "tier_required": "enterprise",
            "routes": ["/api/v1/integrations/*", "/api/v1/webhooks/*"]
        }
    }
    
    # Filter modules based on subscription tier and enabled modules
    available = {}
    for module_id, module_info in all_modules.items():
        if module_id in tenant.enabled_modules:
            available[module_id] = {
                **module_info,
                "status": "enabled",
                "accessible": True
            }
        else:
            available[module_id] = {
                **module_info,
                "status": "disabled",
                "accessible": False,
                "upgrade_required": module_info["tier_required"] != tenant.subscription_tier
            }
    
    return {
        "school_id": tenant.school_id,
        "subscription_tier": tenant.subscription_tier,
        "modules": available,
        "total_enabled": len(tenant.enabled_modules),
        "total_available": len(all_modules)
    }

# Note: Error handlers should be added to the main FastAPI app, not router