#!/usr/bin/env python3
"""
OneClass Platform - Main FastAPI Application
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

# Import tenant middleware
from shared.middleware.tenant_middleware import TenantMiddleware

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="OneClass Platform API",
    description="Educational Management System for Zimbabwe Schools",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware (before tenant middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8000",
        "http://frontend:3000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8000",
        # Local development subdomains
        "http://oneclass.local:3000",
        "http://palm-springs-jnr.oneclass.local:3000",
        "http://admin.oneclass.local:3000",
        "*.oneclass.local:3000",  # Allow all local subdomains
        # Production domains
        "*.oneclass.ac.zw",  # Allow all subdomains
        "https://*.oneclass.ac.zw",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tenant isolation middleware
app.add_middleware(TenantMiddleware)

# Set up error handlers
try:
    from shared.errors.handlers import setup_error_handlers

    setup_error_handlers(app)
    logger.info("Error handlers configured successfully")
except ImportError as e:
    logger.warning(f"Error handlers not available: {e}")


@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    """Handle CORS preflight requests"""
    return {}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "OneClass Platform API",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "oneclass-platform",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if os.getenv("DATABASE_URL") else "not_configured",
    }


@app.get("/api/health")
async def api_health():
    """API health check"""
    return {
        "status": "healthy",
        "api_version": "v1",
        "timestamp": datetime.utcnow().isoformat(),
    }


# Include API Gateway routes
try:
    from api.router import api_router
    from api.subdomain import subdomain_router

    # Include main API routes
    app.include_router(api_router)
    app.include_router(subdomain_router)

    logger.info("API Gateway routes loaded successfully")

except ImportError as e:
    logger.error(f"Failed to load API Gateway routes: {e}")

# Include Platform Public routes (for tenant discovery)
try:
    from services.platform.routes.schools_public import router as schools_public_router

    # Include public schools routes
    app.include_router(schools_public_router, prefix="/api/v1/platform")

    logger.info("Platform public routes loaded successfully")

except ImportError as e:
    logger.warning(f"Platform public routes not available: {e}")

# Include Simple Platform routes (bypass tenant middleware)
try:
    from services.platform.routes.schools_simple import router as schools_simple_router

    # Include simple schools routes
    app.include_router(schools_simple_router, prefix="/api/v1/platform")

    logger.info("Platform simple routes loaded successfully")

except ImportError as e:
    logger.warning(f"Platform simple routes not available: {e}")

# Include Authentication module
try:
    from services.auth import router as auth_router

    # Include auth routes
    app.include_router(auth_router, prefix="/api/v1")

    logger.info("Authentication module loaded successfully")

except ImportError as e:
    logger.warning(f"Authentication module not available: {e}")

# Include module-specific routes
try:
    from services.sis.main import router as sis_router

    # Include SIS routes
    app.include_router(sis_router)

    logger.info("SIS module routes loaded successfully")

except ImportError as e:
    logger.warning(f"SIS module not available: {e}")

    @app.get("/api/v1/sis/health")
    async def sis_health_fallback():
        """SIS module health check fallback"""
        return {
            "status": "unavailable",
            "service": "sis",
            "error": "Module not loaded",
            "timestamp": datetime.utcnow().isoformat(),
        }


# Include Academic Management module
try:
    from services.academic.main import router as academic_router
    from services.academic.error_middleware import add_academic_error_middleware, setup_academic_exception_handlers

    # Add Academic error handling middleware
    add_academic_error_middleware(app)
    setup_academic_exception_handlers(app)
    
    # Include academic routes
    app.include_router(academic_router)

    @app.get("/api/v1/academic/health")
    async def academic_health():
        """Academic module health check"""
        return {
            "status": "healthy",
            "service": "academic",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "module": "academic_management",
            "features": [
                "subject_management",
                "curriculum_planning",
                "timetable_scheduling",
                "attendance_tracking",
                "assessment_management",
                "grade_calculation",
                "lesson_planning",
                "academic_calendar",
                "performance_analytics",
                "zimbabwe_compliance",
                "comprehensive_error_handling",
                "audit_logging",
                "role_based_permissions"
            ],
            "zimbabwe_features": [
                "three_term_system",
                "a_to_u_grading_scale",
                "primary_secondary_structure",
                "cambridge_curriculum_support",
                "zimsec_integration_ready"
            ],
        }

    logger.info("Academic Management module with error handling loaded successfully")

except ImportError as e:
    logger.warning(f"Academic module not available: {e}")

    @app.get("/api/v1/academic/health")
    async def academic_health_fallback():
        """Academic module health check fallback"""
        return {
            "status": "unavailable",
            "service": "academic",
            "error": "Module not loaded",
            "timestamp": datetime.utcnow().isoformat(),
        }


# Include Analytics & Reporting module
try:
    from services.analytics.main import (
        analytics_main_router,
        MODULE_INFO as analytics_info,
    )

    # Include analytics routes
    app.include_router(analytics_main_router)

    @app.get("/api/v1/analytics/health")
    async def analytics_health():
        """Analytics module health check"""
        return {
            "status": "healthy",
            "service": "analytics",
            "version": analytics_info["version"],
            "timestamp": datetime.utcnow().isoformat(),
            "module": analytics_info["name"],
            "features": analytics_info["features"],
        }

    logger.info("Analytics & Reporting module loaded successfully")

except ImportError as e:
    logger.warning(f"Analytics module not available: {e}")

    @app.get("/api/v1/analytics/health")
    async def analytics_health_fallback():
        """Analytics module health check fallback"""
        return {
            "status": "unavailable",
            "service": "analytics",
            "error": "Module not loaded",
            "timestamp": datetime.utcnow().isoformat(),
        }


# Include User Management module
try:
    from services.user_management.routes import router as user_management_router

    # Include user management routes
    app.include_router(user_management_router, prefix="/api/v1")

    @app.get("/api/v1/users/health")
    async def user_management_health():
        """User Management module health check"""
        return {
            "status": "healthy",
            "service": "user_management",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "module": "User Management System",
            "features": [
                "role_based_user_creation",
                "user_invitations",
                "bulk_user_import",
                "user_profile_management",
                "custom_roles",
            ],
        }

    logger.info("User Management module loaded successfully")

except ImportError as e:
    logger.warning(f"User Management module not available: {e}")

    @app.get("/api/v1/users/health")
    async def user_management_health_fallback():
        """User Management module health check fallback"""
        return {
            "status": "unavailable",
            "service": "user_management",
            "error": "Module not loaded",
            "timestamp": datetime.utcnow().isoformat(),
        }


# Include Realtime module
try:
    from services.realtime.routes import router as realtime_router

    # Include realtime routes
    app.include_router(realtime_router)

    @app.get("/api/v1/realtime/health")
    async def realtime_health():
        """Realtime module health check"""
        return {
            "status": "healthy",
            "service": "realtime",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "module": "Real-time Communication",
            "features": [
                "websocket_connections",
                "progress_tracking",
                "real_time_notifications",
                "bulk_operation_monitoring",
            ],
        }

    logger.info("Realtime module loaded successfully")

except ImportError as e:
    logger.warning(f"Realtime module not available: {e}")

    @app.get("/api/v1/realtime/health")
    async def realtime_health_fallback():
        """Realtime module health check fallback"""
        return {
            "status": "unavailable",
            "service": "realtime",
            "error": "Module not loaded",
            "timestamp": datetime.utcnow().isoformat(),
        }


# Include Migration Services module
try:
    from services.migration_services.routes import router as migration_router

    # Include migration services routes
    app.include_router(migration_router)

    @app.get("/api/v1/migration-services/health")
    async def migration_services_health():
        """Migration Services module health check"""
        return {
            "status": "healthy",
            "service": "migration_services",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "module": "Migration Services",
            "features": [
                "data_migration",
                "care_packages",
                "admin_statistics",
                "order_management",
            ],
        }

    logger.info("Migration Services module loaded successfully")

except ImportError as e:
    logger.warning(f"Migration Services module not available: {e}")

    @app.get("/api/v1/migration-services/health")
    async def migration_services_health_fallback():
        """Migration Services module health check fallback"""
        return {
            "status": "unavailable",
            "service": "migration_services",
            "error": "Module not loaded",
            "timestamp": datetime.utcnow().isoformat(),
        }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": str(request.url.path),
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
