"""
Academic Management Module - Simplified Main Router
Minimal version for testing integration without database dependencies
"""

from fastapi import APIRouter

# Create main router for the Academic module
router = APIRouter(
    prefix="/api/v1/academic",
    tags=["academic"],
    responses={404: {"description": "Not found"}},
)

# Module information
MODULE_INFO = {
    "name": "Academic Management System",
    "version": "1.0.0",
    "description": "Comprehensive academic management for Zimbabwe schools",
    "features": [
        "subject_management",
        "curriculum_planning", 
        "timetable_scheduling",
        "attendance_tracking",
        "assessment_creation",
        "grade_management",
        "lesson_planning",
        "academic_calendar",
        "teacher_dashboard",
        "academic_dashboard",
        "zimbabwe_compliance"
    ],
    "zimbabwe_features": [
        "three_term_system",
        "zimsec_grading",
        "multilingual_support",
        "practical_subjects",
        "core_subjects"
    ]
}

@router.get("/health")
async def academic_health():
    """Academic module health check"""
    return {
        "status": "healthy",
        "service": "academic",
        "version": MODULE_INFO["version"],
        "module": MODULE_INFO["name"],
        "features": MODULE_INFO["features"],
        "zimbabwe_features": MODULE_INFO["zimbabwe_features"]
    }

@router.get("/info")
async def academic_info():
    """Academic module information"""
    return MODULE_INFO