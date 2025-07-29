"""
Analytics & Reporting Module Main
Entry point for the Advanced Analytics & Reporting module
"""
from fastapi import APIRouter
from .routes.analytics import router as analytics_router
from .routes.reports import router as reports_router

# Create main analytics router
analytics_main_router = APIRouter()

# Include sub-routers
analytics_main_router.include_router(analytics_router)
analytics_main_router.include_router(reports_router)

# Module metadata
MODULE_INFO = {
    "name": "Advanced Analytics & Reporting",
    "version": "1.0.0",
    "description": "Comprehensive analytics, insights, and custom reporting capabilities",
    "tier_required": "professional",
    "endpoints": [
        "/api/v1/analytics/*",
        "/api/v1/reports/*"
    ],
    "features": [
        "Real-time analytics dashboard",
        "Student performance insights",
        "Financial analytics and trends",
        "Custom report generation",
        "Data export in multiple formats",
        "AI-powered insights and recommendations",
        "Period-over-period comparisons",
        "Interactive charts and visualizations"
    ]
}