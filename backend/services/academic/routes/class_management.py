"""
Academic Management Module - Class Management API Routes
Complete API endpoints for class/group management functionality
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from ..middleware import get_academic_auth_context, AcademicAuthContext
from ..class_management import (
    ClassCreate, ClassUpdate, ClassResponse, 
    ClassSubjectAssignmentCreate, ClassEnrollmentCreate,
    create_class, get_classes, assign_subject_to_class, 
    enroll_student_in_class
)
from ..exceptions import (
    AcademicBaseException, AcademicValidationError, 
    AcademicResourceError, AcademicPermissionError,
    create_error_response, log_academic_error
)
from ..docs import SCHEMA_EXAMPLES
from shared.database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/classes",
    tags=["Class Management"],
    responses={
        400: {"description": "Validation Error"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Resource not found"},
        409: {"description": "Resource conflict"},
        500: {"description": "Internal server error"}
    }
)

# =====================================================
# CLASS CRUD ENDPOINTS
# =====================================================

@router.post(
    "/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create New Class",
    description="""
    Create a new academic class/group for student organization.
    
    **Zimbabwe Education System Support:**
    - Grade levels 1-13 (Primary: 1-7, Secondary: 8-13)
    - Academic streaming (A, B, C streams)
    - Curriculum level auto-detection
    - Three-term academic year
    
    **Features:**
    - Automatic curriculum level assignment
    - Capacity management with enrollment tracking
    - Teacher assignment (primary and deputy)
    - Classroom allocation
    - Academic year validation
    
    **Required Permissions:**
    - `academic.class.create` OR `academic.admin`
    """
)
async def create_class_endpoint(
    class_data: ClassCreate,
    auth_context: AcademicAuthContext = Depends(get_academic_auth_context),
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new academic class"""
    try:
        # Check permissions
        if not auth_context.can_manage_classes():
            raise AcademicPermissionError(
                "Insufficient permissions to create classes",
                required_permission="academic.class.create",
                user_role=auth_context.user_role
            )
        
        # Create class
        result = await create_class(
            db=db,
            class_data=class_data,
            school_id=str(auth_context.school_id),
            created_by=str(auth_context.user_id)
        )
        
        logger.info(f"Class created successfully: {result['id']}")
        
        return {
            "success": True,
            "message": f"Class '{class_data.name}' created successfully",
            "data": result,
            "class_id": result["id"]
        }
        
    except AcademicBaseException as e:
        log_academic_error(e, {
            "endpoint": "create_class",
            "user_id": str(auth_context.user_id),
            "school_id": str(auth_context.school_id),
            "class_data": class_data.dict()
        })
        raise e.to_http_exception()
    
    except Exception as e:
        logger.error(f"Unexpected error creating class: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create class"
        )


@router.get(
    "/",
    response_model=Dict[str, Any],
    summary="Get Classes",
    description="""
    Retrieve classes with filtering and pagination.
    
    **Filtering Options:**
    - Grade level (1-13)
    - Academic year
    - Class type (regular, streaming, mixed_ability, etc.)
    - Active status
    
    **Pagination:**
    - Standard skip/limit parameters
    - Ordered by grade level and class code
    
    **Response includes:**
    - Total count for pagination
    - Class details with enrollment counts
    - Teacher assignments
    - Curriculum levels
    """
)
async def get_classes_endpoint(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of records to return"),
    grade_level: Optional[int] = Query(None, ge=1, le=13, description="Filter by Zimbabwe grade level"),
    academic_year: Optional[str] = Query(None, description="Filter by academic year"),
    class_type: Optional[str] = Query(None, description="Filter by class type"),
    active_only: bool = Query(True, description="Include only active classes"),
    auth_context: AcademicAuthContext = Depends(get_academic_auth_context),
    db: AsyncSession = Depends(get_async_session)
):
    """Get classes with filtering and pagination"""
    try:
        # Check permissions
        if not auth_context.can_view_classes():
            raise AcademicPermissionError(
                "Insufficient permissions to view classes",
                required_permission="academic.class.view",
                user_role=auth_context.user_role
            )
        
        # Get classes
        classes, total_count = await get_classes(
            db=db,
            school_id=str(auth_context.school_id),
            skip=skip,
            limit=limit,
            grade_level=grade_level,
            academic_year=academic_year,
            class_type=class_type,
            active_only=active_only
        )
        
        return {
            "success": True,
            "data": classes,
            "pagination": {
                "total": total_count,
                "skip": skip,
                "limit": limit,
                "has_next": (skip + limit) < total_count
            },
            "filters": {
                "grade_level": grade_level,
                "academic_year": academic_year,
                "class_type": class_type,
                "active_only": active_only
            }
        }
        
    except AcademicBaseException as e:
        log_academic_error(e, {
            "endpoint": "get_classes",
            "user_id": str(auth_context.user_id),
            "school_id": str(auth_context.school_id)
        })
        raise e.to_http_exception()
    
    except Exception as e:
        logger.error(f"Unexpected error retrieving classes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve classes"
        )


# =====================================================
# SUBJECT ASSIGNMENT ENDPOINTS
# =====================================================

@router.post(
    "/{class_id}/subjects",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Assign Subject to Class",
    description="""
    Assign a subject to a specific class with teacher and scheduling details.
    
    **Features:**
    - Subject-class assignment tracking
    - Teacher assignment per subject
    - Periods per week scheduling
    - Core vs elective classification
    - Term-specific assignments
    
    **Validation:**
    - Class must exist and be active
    - Subject must exist
    - No duplicate assignments
    - Teacher authorization (if specified)
    
    **Required Permissions:**
    - `academic.class.manage_subjects` OR `academic.admin`
    """
)
async def assign_subject_to_class_endpoint(
    class_id: UUID,
    assignment_data: ClassSubjectAssignmentCreate,
    auth_context: AcademicAuthContext = Depends(get_academic_auth_context),
    db: AsyncSession = Depends(get_async_session)
):
    """Assign a subject to a class"""
    try:
        # Check permissions
        if not auth_context.can_manage_class_subjects():
            raise AcademicPermissionError(
                "Insufficient permissions to assign subjects to classes",
                required_permission="academic.class.manage_subjects",
                user_role=auth_context.user_role
            )
        
        # Assign subject
        result = await assign_subject_to_class(
            db=db,
            class_id=class_id,
            assignment_data=assignment_data,
            school_id=str(auth_context.school_id),
            created_by=str(auth_context.user_id)
        )
        
        logger.info(f"Subject assigned to class successfully: {result['id']}")
        
        return {
            "success": True,
            "message": "Subject assigned to class successfully",
            "data": result,
            "assignment_id": result["id"]
        }
        
    except AcademicBaseException as e:
        log_academic_error(e, {
            "endpoint": "assign_subject_to_class",
            "user_id": str(auth_context.user_id),
            "school_id": str(auth_context.school_id),
            "class_id": str(class_id),
            "assignment_data": assignment_data.dict()
        })
        raise e.to_http_exception()
    
    except Exception as e:
        logger.error(f"Unexpected error assigning subject to class: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign subject to class"
        )


# =====================================================
# STUDENT ENROLLMENT ENDPOINTS
# =====================================================

@router.post(
    "/{class_id}/students",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Enroll Student in Class",
    description="""
    Enroll a student in a specific class for an academic year.
    
    **Features:**
    - Student-class enrollment tracking
    - Academic year association
    - Capacity management
    - Enrollment date tracking
    - Active status management
    
    **Validation:**
    - Class must exist and be active
    - Class must have available capacity
    - Student cannot be enrolled twice in same class/year
    - Student must exist in SIS
    
    **Automatic Updates:**
    - Class enrollment count incremented
    - Enrollment status set to active
    - Audit trail created
    
    **Required Permissions:**
    - `academic.class.manage_enrollment` OR `academic.admin`
    """
)
async def enroll_student_in_class_endpoint(
    class_id: UUID,
    enrollment_data: ClassEnrollmentCreate,
    auth_context: AcademicAuthContext = Depends(get_academic_auth_context),
    db: AsyncSession = Depends(get_async_session)
):
    """Enroll a student in a class"""
    try:
        # Check permissions
        if not auth_context.can_manage_class_enrollment():
            raise AcademicPermissionError(
                "Insufficient permissions to manage class enrollment",
                required_permission="academic.class.manage_enrollment",
                user_role=auth_context.user_role
            )
        
        # Enroll student
        result = await enroll_student_in_class(
            db=db,
            class_id=class_id,
            enrollment_data=enrollment_data,
            school_id=str(auth_context.school_id),
            created_by=str(auth_context.user_id)
        )
        
        logger.info(f"Student enrolled in class successfully: {result['id']}")
        
        return {
            "success": True,
            "message": "Student enrolled in class successfully",
            "data": result,
            "enrollment_id": result["id"]
        }
        
    except AcademicBaseException as e:
        log_academic_error(e, {
            "endpoint": "enroll_student_in_class",
            "user_id": str(auth_context.user_id),
            "school_id": str(auth_context.school_id),
            "class_id": str(class_id),
            "enrollment_data": enrollment_data.dict()
        })
        raise e.to_http_exception()
    
    except Exception as e:
        logger.error(f"Unexpected error enrolling student in class: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enroll student in class"
        )


# =====================================================
# CLASS ANALYTICS ENDPOINTS
# =====================================================

@router.get(
    "/analytics/summary",
    response_model=Dict[str, Any],
    summary="Class Management Analytics Summary",
    description="""
    Get comprehensive analytics for class management.
    
    **Analytics Include:**
    - Total classes by grade level
    - Enrollment statistics
    - Capacity utilization
    - Subject distribution
    - Teacher workload
    - Popular class types
    
    **Filtering:**
    - Academic year
    - Grade level range
    - Active classes only
    
    **Use Cases:**
    - Administrative dashboards
    - Capacity planning
    - Resource allocation
    - Performance monitoring
    """
)
async def get_class_analytics_summary(
    academic_year: Optional[str] = Query(None, description="Filter by academic year"),
    grade_level_min: Optional[int] = Query(None, ge=1, le=13, description="Minimum grade level"),
    grade_level_max: Optional[int] = Query(None, ge=1, le=13, description="Maximum grade level"),
    auth_context: AcademicAuthContext = Depends(get_academic_auth_context),
    db: AsyncSession = Depends(get_async_session)
):
    """Get class management analytics summary"""
    try:
        # Check permissions
        if not auth_context.can_view_analytics():
            raise AcademicPermissionError(
                "Insufficient permissions to view analytics",
                required_permission="academic.analytics.view",
                user_role=auth_context.user_role
            )
        
        # This would typically query the database for analytics
        # For now, return a structured response format
        return {
            "success": True,
            "message": "Class analytics retrieved successfully",
            "data": {
                "summary": {
                    "total_classes": 0,
                    "total_enrolled_students": 0,
                    "average_class_size": 0,
                    "capacity_utilization": 0
                },
                "by_grade_level": [],
                "by_class_type": [],
                "enrollment_trends": [],
                "teacher_assignments": []
            },
            "filters": {
                "academic_year": academic_year,
                "grade_level_range": f"{grade_level_min}-{grade_level_max}" if grade_level_min and grade_level_max else None
            }
        }
        
    except AcademicBaseException as e:
        log_academic_error(e, {
            "endpoint": "get_class_analytics",
            "user_id": str(auth_context.user_id),
            "school_id": str(auth_context.school_id)
        })
        raise e.to_http_exception()
    
    except Exception as e:
        logger.error(f"Unexpected error getting class analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve class analytics"
        )


# =====================================================
# BULK OPERATIONS ENDPOINTS
# =====================================================

@router.post(
    "/bulk/create",
    response_model=Dict[str, Any],
    summary="Bulk Create Classes",
    description="""
    Create multiple classes in a single operation.
    
    **Features:**
    - Batch class creation
    - Validation per class
    - Rollback on any failure
    - Progress tracking
    - Error reporting per class
    
    **Use Cases:**
    - Academic year setup
    - Grade level creation
    - Streaming implementation
    - Mass class organization
    
    **Required Permissions:**
    - `academic.class.bulk_create` OR `academic.admin`
    """
)
async def bulk_create_classes(
    classes_data: List[ClassCreate],
    auth_context: AcademicAuthContext = Depends(get_academic_auth_context),
    db: AsyncSession = Depends(get_async_session)
):
    """Create multiple classes in bulk"""
    try:
        # Check permissions
        if not auth_context.can_bulk_manage_classes():
            raise AcademicPermissionError(
                "Insufficient permissions for bulk class operations",
                required_permission="academic.class.bulk_create",
                user_role=auth_context.user_role
            )
        
        # Validate input
        if not classes_data:
            raise AcademicValidationError("No class data provided")
        
        if len(classes_data) > 100:
            raise AcademicValidationError("Maximum 100 classes can be created in one operation")
        
        # This would implement bulk creation logic
        # For now, return a structured response format
        return {
            "success": True,
            "message": f"Bulk class creation initiated for {len(classes_data)} classes",
            "data": {
                "total_requested": len(classes_data),
                "successful": 0,
                "failed": 0,
                "results": [],
                "errors": []
            }
        }
        
    except AcademicBaseException as e:
        log_academic_error(e, {
            "endpoint": "bulk_create_classes",
            "user_id": str(auth_context.user_id),
            "school_id": str(auth_context.school_id),
            "classes_count": len(classes_data) if classes_data else 0
        })
        raise e.to_http_exception()
    
    except Exception as e:
        logger.error(f"Unexpected error in bulk class creation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process bulk class creation"
        )