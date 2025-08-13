"""
Academic Management Module - Main Application Integration
Integrates Academic module with OneClass platform
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from .api import router as academic_api_router
from .middleware import get_academic_auth_context, AcademicAuthContext
from .error_middleware import add_academic_error_middleware, setup_academic_exception_handlers
from .docs import get_enhanced_openapi_metadata, ACADEMIC_TAGS

logger = logging.getLogger(__name__)

# Create the main Academic module router with comprehensive documentation
router = APIRouter(
    prefix="/api/v1/academic",
    tags=["academic"],
    responses={
        400: {
            "description": "Bad Request - Invalid input or validation error",
            "content": {
                "application/json": {
                    "example": {
                        "error": "ACADEMIC_VALIDATION_ERROR",
                        "message": "Invalid grade level: 15. Must be between 1-13 for Zimbabwe education system.",
                        "details": {
                            "field": "grade_level",
                            "invalid_value": "15",
                            "valid_range": "1-13"
                        },
                        "module": "academic_management"
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - authentication required",
            "content": {
                "application/json": {
                    "example": {
                        "error": "AUTHENTICATION_REQUIRED",
                        "message": "Valid authentication token required",
                        "module": "academic_management"
                    }
                }
            }
        },
        403: {
            "description": "Forbidden - insufficient permissions",
            "content": {
                "application/json": {
                    "example": {
                        "error": "ACADEMIC_PERMISSION_ERROR",
                        "message": "Insufficient permissions to perform this action",
                        "details": {
                            "required_permission": "academic.subject.create",
                            "user_role": "student"
                        },
                        "module": "academic_management"
                    }
                }
            }
        },
        404: {
            "description": "Not found - resource does not exist",
            "content": {
                "application/json": {
                    "example": {
                        "error": "SUBJECT_NOT_FOUND",
                        "message": "Subject not found: PHYSICS",
                        "details": {
                            "subject_code": "PHYSICS",
                            "suggestion": "Check if the subject exists and you have permission to access it"
                        },
                        "module": "academic_management"
                    }
                }
            }
        },
        409: {
            "description": "Conflict - duplicate resource or business logic violation",
            "content": {
                "application/json": {
                    "example": {
                        "error": "DUPLICATE_SUBJECT_CODE",
                        "message": "Subject with code 'MATH' already exists in this school",
                        "details": {
                            "subject_code": "MATH",
                            "suggestion": "Use a different subject code or update the existing subject"
                        },
                        "module": "academic_management"
                    }
                }
            }
        },
        422: {
            "description": "Unprocessable Entity - business logic error",
            "content": {
                "application/json": {
                    "example": {
                        "error": "GRADING_PERIOD_CLOSED",
                        "message": "Cannot modify grades. Grading period closed on 2024-04-30.",
                        "details": {
                            "assessment_name": "Term 1 Test",
                            "close_date": "2024-04-30"
                        },
                        "module": "academic_management"
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error - system error",
            "content": {
                "application/json": {
                    "example": {
                        "error": "ACADEMIC_SYSTEM_ERROR",
                        "message": "An unexpected error occurred while processing your request",
                        "module": "academic_management"
                    }
                }
            }
        }
    }
)

# Include all academic API routes
router.include_router(academic_api_router)

# Health check endpoint
@router.get(
    "/health", 
    status_code=200,
    summary="Academic Module Health Check",
    description="Check the health and status of the Academic Management module",
    tags=["health"],
    responses={
        200: {
            "description": "Module is healthy and operational",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "module": "academic_management",
                        "version": "1.0.0",
                        "uptime": "72h 15m",
                        "features": ["subject_management", "assessment_management"]
                    }
                }
            }
        }
    }
)
async def health_check():
    """Health check for Academic Management module"""
    return {
        "status": "healthy",
        "module": "academic_management",
        "version": "1.0.0",
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
        ]
    }

# Module information endpoint
@router.get(
    "/info",
    summary="Academic Module Information",
    description="Get detailed information about the Academic Management module and user capabilities",
    tags=["info"],
    responses={
        200: {
            "description": "Module information and user capabilities",
            "content": {
                "application/json": {
                    "example": {
                        "module": "academic_management",
                        "school_name": "Harare Primary School",
                        "user_role": "teacher",
                        "user_capabilities": {
                            "can_manage_subjects": True,
                            "can_enter_grades": True,
                            "can_mark_attendance": True
                        }
                    }
                }
            }
        }
    }
)
async def module_info(
    auth_context: AcademicAuthContext = Depends(get_academic_auth_context)
):
    """Get Academic module information and user capabilities"""
    return {
        "module": "academic_management",
        "school_id": str(auth_context.school_id),
        "school_name": auth_context.tenant.school_name,
        "subscription_tier": auth_context.tenant.subscription_tier,
        "user_role": auth_context.user_role,
        "user_permissions": auth_context.permissions,
        "available_features": auth_context.tenant.enabled_modules,
        "user_capabilities": {
            "can_manage_subjects": auth_context.can_manage_subjects(),
            "can_manage_assessments": auth_context.can_manage_assessments(),
            "can_enter_grades": auth_context.can_enter_grades(),
            "can_mark_attendance": auth_context.can_mark_attendance(),
            "can_view_analytics": auth_context.can_view_analytics(),
            "can_access_all_data": auth_context.can_access_all_data()
        },
        "teacher_context": {
            "is_teacher": auth_context.teacher_id is not None,
            "teacher_id": str(auth_context.teacher_id) if auth_context.teacher_id else None
        },
        "student_context": {
            "is_student": auth_context.student_id is not None,
            "student_id": str(auth_context.student_id) if auth_context.student_id else None
        }
    }

# Zimbabwe education system endpoints
@router.get("/zimbabwe/grade-levels")
async def get_zimbabwe_grade_levels():
    """Get Zimbabwe education system grade levels"""
    return {
        "primary": [
            {"value": 1, "label": "Grade 1", "description": "Primary - Age 6-7"},
            {"value": 2, "label": "Grade 2", "description": "Primary - Age 7-8"},
            {"value": 3, "label": "Grade 3", "description": "Primary - Age 8-9"},
            {"value": 4, "label": "Grade 4", "description": "Primary - Age 9-10"},
            {"value": 5, "label": "Grade 5", "description": "Primary - Age 10-11"},
            {"value": 6, "label": "Grade 6", "description": "Primary - Age 11-12"},
            {"value": 7, "label": "Grade 7", "description": "Primary - Age 12-13"}
        ],
        "secondary": [
            {"value": 8, "label": "Form 1", "description": "Secondary - Age 13-14"},
            {"value": 9, "label": "Form 2", "description": "Secondary - Age 14-15"},
            {"value": 10, "label": "Form 3", "description": "O-Level - Age 15-16"},
            {"value": 11, "label": "Form 4", "description": "O-Level - Age 16-17"},
            {"value": 12, "label": "Form 5", "description": "A-Level - Age 17-18"},
            {"value": 13, "label": "Form 6", "description": "A-Level - Age 18-19"}
        ]
    }

@router.get("/zimbabwe/terms")
async def get_zimbabwe_terms():
    """Get Zimbabwe academic calendar terms"""
    return {
        "terms": [
            {
                "number": 1,
                "name": "Term 1",
                "description": "January - April",
                "months": "Jan-Apr",
                "typical_start": "January 15",
                "typical_end": "April 18"
            },
            {
                "number": 2,
                "name": "Term 2", 
                "description": "May - August",
                "months": "May-Aug",
                "typical_start": "May 6",
                "typical_end": "August 22"
            },
            {
                "number": 3,
                "name": "Term 3",
                "description": "September - December", 
                "months": "Sep-Dec",
                "typical_start": "September 9",
                "typical_end": "December 5"
            }
        ],
        "holidays": [
            {"name": "Independence Day", "date": "April 18"},
            {"name": "Workers Day", "date": "May 1"},
            {"name": "Heroes Day", "date": "August 11"},
            {"name": "Defence Forces Day", "date": "August 12"}
        ]
    }

@router.get("/zimbabwe/grading-scale")
async def get_zimbabwe_grading_scale():
    """Get Zimbabwe grading scale information"""
    return {
        "scale_type": "letter_grade",
        "scale_name": "Zimbabwe A-U Scale",
        "grades": [
            {
                "grade": "A",
                "percentage_range": "80-100%",
                "description": "Excellent",
                "points": 4.0,
                "pass": True
            },
            {
                "grade": "B", 
                "percentage_range": "70-79%",
                "description": "Good",
                "points": 3.0,
                "pass": True
            },
            {
                "grade": "C",
                "percentage_range": "60-69%", 
                "description": "Credit",
                "points": 2.0,
                "pass": True
            },
            {
                "grade": "D",
                "percentage_range": "50-59%",
                "description": "Pass", 
                "points": 1.0,
                "pass": True
            },
            {
                "grade": "E",
                "percentage_range": "40-49%",
                "description": "Marginal",
                "points": 0.5,
                "pass": False
            },
            {
                "grade": "U",
                "percentage_range": "0-39%",
                "description": "Ungraded/Fail",
                "points": 0.0,
                "pass": False
            }
        ],
        "pass_mark": 50,
        "distinction_mark": 80
    }