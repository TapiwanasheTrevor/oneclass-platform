"""
Academic Management API Routes
FastAPI routes for academic management with comprehensive error handling
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Generic, TypeVar
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

# Import database session
from shared.database import get_db

# Import authentication and middleware
from .middleware import (
    get_academic_auth_context, 
    AcademicAuthContext,
    require_subject_read,
    require_subject_write,
    require_assessment_write,
    require_grade_write,
    require_attendance_write,
    require_analytics_read,
    AcademicPermissions
)

# Create pagination classes
class PaginationParams:
    def __init__(self, page: int = 1, page_size: int = 20):
        self.page = page
        self.page_size = page_size
        self.skip = (page - 1) * page_size
        self.limit = page_size

from pydantic import BaseModel

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    class Config:
        arbitrary_types_allowed = True
    
    @classmethod
    def create(cls, items: List[T], total_count: int, page: int, page_size: int):
        total_pages = (total_count + page_size - 1) // page_size
        return cls(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )

def cache_response(ttl=300):
    """Cache decorator for performance optimization"""
    def decorator(func):
        # TODO: Implement Redis caching
        return func
    return decorator

# Import custom exceptions
from .exceptions import (
    AcademicBaseException,
    SubjectNotFoundError,
    AssessmentNotFoundError,
    AttendanceSessionNotFoundError,
    InvalidGradeLevelError,
    InvalidTermNumberError,
    DuplicateSubjectError,
    TimetableConflictError,
    InsufficientPermissionError,
    create_error_response,
    handle_database_error,
    log_academic_error
)

# Import CRUD operations
from . import crud

from .schemas import (
    # Subject schemas
    SubjectCreate, SubjectUpdate, Subject,
    # Assessment schemas
    AssessmentCreate, AssessmentUpdate, Assessment,
    # Grade schemas
    GradeCreate, GradeUpdate, Grade, BulkGradeCreate,
    # Attendance schemas
    AttendanceSessionCreate, AttendanceSession,
    AttendanceRecordCreate, BulkAttendanceCreate,
    # Enums
    TermNumber, AssessmentType, AttendanceStatus, GradingScale
)

from .docs import SCHEMA_EXAMPLES, RESPONSE_EXAMPLES, ERROR_EXAMPLES

# Import route modules
from .routes.class_management import router as class_management_router
from .routes.calendar_management import router as calendar_management_router

# Create the router
router = APIRouter()

# Include sub-routers
router.include_router(class_management_router)
router.include_router(calendar_management_router)

# =====================================================
# SUBJECT MANAGEMENT ENDPOINTS
# =====================================================

@router.post(
    "/subjects", 
    response_model=Subject, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new subject",
    description="""
    Create a new academic subject with Zimbabwe curriculum compliance.
    
    This endpoint allows authorized users (administrators and teachers with appropriate permissions) 
    to create new academic subjects that will be available for curriculum planning, assessment 
    creation, and timetable scheduling.
    
    **Requirements:**
    - User must have `academic.subject.create` permission
    - Subject code must be unique within the school
    - Grade level must be valid for Zimbabwe education system (1-13)
    - Department and curriculum framework should align with school offerings
    
    **Zimbabwe Education System Compliance:**
    - Supports Grades 1-7 (Primary) and Forms 1-6 (Secondary)
    - Compatible with Zimbabwe Junior Certificate, ZIMSEC O-Level, and A-Level curricula
    - Validates core vs elective subject classifications
    """,
    tags=["subjects"],
    responses={
        201: {
            "description": "Subject created successfully",
            "content": {
                "application/json": {
                    "example": SCHEMA_EXAMPLES["Subject"]["value"]
                }
            }
        },
        400: {
            "description": "Invalid input data",
            "content": {
                "application/json": {
                    "example": ERROR_EXAMPLES["validation_error"]["value"]
                }
            }
        },
        409: {
            "description": "Subject code already exists",
            "content": {
                "application/json": {
                    "example": ERROR_EXAMPLES["business_logic_error"]["value"]
                }
            }
        }
    }
)
async def create_subject_endpoint(
    subject_data: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    auth_context: AcademicAuthContext = Depends(require_subject_write)
):
    """Create a new subject"""
    try:
        subject = await crud.create_subject(
            db=db,
            subject_data=subject_data,
            school_id=str(auth_context.school_id),
            created_by=str(auth_context.user.id)
        )
        return subject
    except AcademicBaseException as e:
        log_academic_error(e, {"endpoint": "create_subject", "user_id": str(auth_context.user.id)})
        raise e.to_http_exception()
    except Exception as e:
        academic_error = handle_database_error(e, "create_subject")
        log_academic_error(academic_error, {"endpoint": "create_subject", "user_id": str(auth_context.user.id)})
        raise academic_error.to_http_exception()

@router.get(
    "/subjects", 
    response_model=PaginatedResponse[Subject],
    summary="List subjects with filtering",
    description="""
    Retrieve a paginated list of academic subjects with advanced filtering options.
    
    This endpoint provides comprehensive subject listing with support for:
    - **Pagination**: Efficient loading of large subject catalogs
    - **Grade Level Filtering**: Filter by specific Zimbabwe education levels (1-13)
    - **Department Filtering**: Filter by academic departments (Sciences, Arts, etc.)
    - **Core Subject Filtering**: Distinguish between core and elective subjects
    - **Search**: Full-text search across subject names and codes
    
    **Use Cases:**
    - Curriculum planning and subject selection
    - Timetable creation and scheduling
    - Assessment setup and grade book configuration
    - Academic reporting and analytics
    
    **Performance:**
    - Results are cached for improved response times
    - Maximum 100 items per page to ensure optimal performance
    - Supports efficient database indexing for fast filtering
    """,
    tags=["subjects"],
    responses={
        200: {
            "description": "List of subjects retrieved successfully",
            "content": {
                "application/json": {
                    "example": RESPONSE_EXAMPLES["subjects_list_success"]["value"]
                }
            }
        }
    }
)
async def get_subjects_endpoint(
    page: int = Query(1, ge=1, description="Page number for pagination (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page (max 100)"),
    grade_level: Optional[int] = Query(None, ge=1, le=13, description="Filter by Zimbabwe grade level (1-13)"),
    department: Optional[str] = Query(None, description="Filter by academic department"),
    is_core: Optional[bool] = Query(None, description="Filter by core/elective status"),
    search: Optional[str] = Query(None, min_length=2, description="Search by subject name or code"),
    db: AsyncSession = Depends(get_db),
    auth_context: AcademicAuthContext = Depends(require_subject_read)
):
    """Get paginated list of subjects with filtering"""
    # Validate grade level if provided
    if grade_level and (grade_level < 1 or grade_level > 13):
        raise InvalidGradeLevelError(grade_level).to_http_exception()
    
    try:
        subjects, total_count = await crud.get_subjects(
            db=db,
            school_id=str(auth_context.school_id),
            skip=(page - 1) * page_size,
            limit=page_size,
            grade_level=grade_level,
            department=department,
            is_core=is_core,
            search=search
        )
        return PaginatedResponse.create(
            items=subjects,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
    except AcademicBaseException as e:
        log_academic_error(e, {"endpoint": "get_subjects", "filters": {"grade_level": grade_level, "department": department}})
        raise e.to_http_exception()
    except Exception as e:
        academic_error = handle_database_error(e, "get_subjects")
        log_academic_error(academic_error, {"endpoint": "get_subjects"})
        raise academic_error.to_http_exception()

@router.get("/subjects/{subject_id}", response_model=Subject)
async def get_subject_endpoint(
    subject_id: UUID,
    db: AsyncSession = Depends(get_db),
    auth_context: AcademicAuthContext = Depends(require_subject_read)
):
    """Get a specific subject by ID"""
    try:
        subject = await crud.get_subject(
            db=db,
            subject_id=subject_id,
            school_id=str(auth_context.school_id)
        )
        if not subject:
            raise SubjectNotFoundError(subject_id=str(subject_id))
        return subject
    except AcademicBaseException as e:
        log_academic_error(e, {"endpoint": "get_subject", "subject_id": str(subject_id)})
        raise e.to_http_exception()
    except Exception as e:
        academic_error = handle_database_error(e, "get_subject")
        log_academic_error(academic_error, {"endpoint": "get_subject", "subject_id": str(subject_id)})
        raise academic_error.to_http_exception()

@router.put("/subjects/{subject_id}", response_model=Subject)
async def update_subject_endpoint(
    subject_id: UUID,
    subject_data: SubjectUpdate,
    db: AsyncSession = Depends(get_db),
    auth_context: AcademicAuthContext = Depends(require_subject_write)
):
    """Update an existing subject"""
    try:
        subject = await crud.update_subject(
            db=db,
            subject_id=subject_id,
            subject_data=subject_data,
            school_id=str(auth_context.school_id),
            updated_by=str(auth_context.user.id)
        )
        if not subject:
            raise SubjectNotFoundError(subject_id=str(subject_id))
        return subject
    except AcademicBaseException as e:
        log_academic_error(e, {"endpoint": "update_subject", "subject_id": str(subject_id)})
        raise e.to_http_exception()
    except Exception as e:
        academic_error = handle_database_error(e, "update_subject")
        log_academic_error(academic_error, {"endpoint": "update_subject", "subject_id": str(subject_id)})
        raise academic_error.to_http_exception()

@router.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject_endpoint(
    subject_id: UUID,
    db: AsyncSession = Depends(get_db),
    auth_context: AcademicAuthContext = Depends(require_subject_write)
):
    """Soft delete a subject"""
    # Only allow deletion if user has delete permission
    if not auth_context.has_permission(AcademicPermissions.SUBJECT_DELETE):
        raise InsufficientPermissionError(
            permission=AcademicPermissions.SUBJECT_DELETE,
            user_role=auth_context.user_role,
            action="delete subjects"
        ).to_http_exception()
    
    try:
        result = await crud.delete_subject(
            db=db,
            subject_id=subject_id,
            school_id=str(auth_context.school_id),
            deleted_by=str(auth_context.user.id)
        )
        if not result:
            raise SubjectNotFoundError(subject_id=str(subject_id))
    except AcademicBaseException as e:
        log_academic_error(e, {"endpoint": "delete_subject", "subject_id": str(subject_id)})
        raise e.to_http_exception()
    except Exception as e:
        academic_error = handle_database_error(e, "delete_subject")
        log_academic_error(academic_error, {"endpoint": "delete_subject", "subject_id": str(subject_id)})
        raise academic_error.to_http_exception()

# =====================================================
# ASSESSMENT MANAGEMENT ENDPOINTS  
# =====================================================

@router.post("/assessments", response_model=Assessment, status_code=status.HTTP_201_CREATED)
async def create_assessment_endpoint(
    assessment_data: AssessmentCreate,
    db: AsyncSession = Depends(get_db),
    auth_context: AcademicAuthContext = Depends(require_assessment_write)
):
    """Create a new assessment"""
    try:
        # Set teacher_id if user is a teacher
        if auth_context.user_role == 'teacher' and auth_context.teacher_id:
            assessment_data.teacher_id = auth_context.teacher_id
        
        assessment = await crud.create_assessment(
            db=db,
            assessment_data=assessment_data,
            school_id=str(auth_context.school_id),
            created_by=str(auth_context.user.id)
        )
        return assessment
    except AcademicBaseException as e:
        log_academic_error(e, {"endpoint": "create_assessment", "user_id": str(auth_context.user.id)})
        raise e.to_http_exception()
    except Exception as e:
        academic_error = handle_database_error(e, "create_assessment")
        log_academic_error(academic_error, {"endpoint": "create_assessment", "user_id": str(auth_context.user.id)})
        raise academic_error.to_http_exception()

@router.get("/assessments", response_model=PaginatedResponse[Assessment])
async def get_assessments_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    subject_id: Optional[UUID] = Query(None, description="Filter by subject"),
    class_id: Optional[UUID] = Query(None, description="Filter by class"),
    term_number: Optional[TermNumber] = Query(None, description="Filter by term"),
    assessment_type: Optional[AssessmentType] = Query(None, description="Filter by type"),
    db: AsyncSession = Depends(get_db),
    auth_context: AcademicAuthContext = Depends(get_academic_auth_context)
):
    """Get paginated list of assessments with filtering"""
    # Check permission
    if not auth_context.has_permission(AcademicPermissions.ASSESSMENT_READ):
        raise InsufficientPermissionError(
            permission=AcademicPermissions.ASSESSMENT_READ,
            user_role=auth_context.user_role,
            action="read assessments"
        ).to_http_exception()
    
    # Validate term number if provided
    if term_number and term_number not in [1, 2, 3]:
        raise InvalidTermNumberError(term_number).to_http_exception()
    
    try:
        assessments, total_count = await crud.get_assessments(
            db=db,
            school_id=str(auth_context.school_id),
            skip=(page - 1) * page_size,
            limit=page_size,
            subject_id=subject_id,
            class_id=class_id,
            term_number=term_number,
            assessment_type=assessment_type
        )
        return PaginatedResponse.create(
            items=assessments,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
    except AcademicBaseException as e:
        log_academic_error(e, {"endpoint": "get_assessments", "filters": {"subject_id": str(subject_id) if subject_id else None}})
        raise e.to_http_exception()
    except Exception as e:
        academic_error = handle_database_error(e, "get_assessments")
        log_academic_error(academic_error, {"endpoint": "get_assessments"})
        raise academic_error.to_http_exception()

# =====================================================
# GRADE MANAGEMENT ENDPOINTS
# =====================================================

@router.post("/grades/bulk", response_model=Dict[str, Any])
async def submit_bulk_grades_endpoint(
    grade_data: BulkGradeCreate,
    db: AsyncSession = Depends(get_db),
    auth_context: AcademicAuthContext = Depends(require_grade_write)
):
    """Submit grades in bulk for an assessment"""
    try:
        # Verify teacher can grade this assessment if not admin
        if auth_context.user_role == 'teacher' and auth_context.teacher_id:
            from .middleware import verify_teacher_ownership
            can_grade = await verify_teacher_ownership(
                teacher_id=auth_context.teacher_id,
                auth_context=auth_context,
                resource_type='assessment',
                resource_id=grade_data.assessment_id,
                db=db
            )
            if not can_grade:
                from .exceptions import TeacherOwnershipError
                raise TeacherOwnershipError(
                    resource_type="assessment",
                    resource_id=str(grade_data.assessment_id)
                ).to_http_exception()
        
        result = await crud.submit_bulk_grades(
            db=db,
            grade_data=grade_data,
            school_id=str(auth_context.school_id),
            graded_by=str(auth_context.user.id)
        )
        return {
            "message": "Grades submitted successfully",
            "grades_submitted": result["grades_submitted"],
            "grades_updated": result["grades_updated"]
        }
    except AcademicBaseException as e:
        log_academic_error(e, {"endpoint": "submit_bulk_grades", "assessment_id": str(grade_data.assessment_id)})
        raise e.to_http_exception()
    except Exception as e:
        academic_error = handle_database_error(e, "submit_bulk_grades")
        log_academic_error(academic_error, {"endpoint": "submit_bulk_grades", "assessment_id": str(grade_data.assessment_id)})
        raise academic_error.to_http_exception()

@router.get("/grades/{assessment_id}", response_model=List[Grade])
async def get_assessment_grades_endpoint(
    assessment_id: UUID,
    db: AsyncSession = Depends(get_db),
    auth_context: AcademicAuthContext = Depends(get_academic_auth_context)
):
    """Get all grades for a specific assessment"""
    # Check permission
    if not auth_context.has_permission(AcademicPermissions.GRADE_READ):
        raise InsufficientPermissionError(
            permission=AcademicPermissions.GRADE_READ,
            user_role=auth_context.user_role,
            action="read grades"
        ).to_http_exception()
    
    try:
        grades = await crud.get_assessment_grades(
            db=db,
            assessment_id=assessment_id,
            school_id=str(auth_context.school_id)
        )
        if not grades:
            raise AssessmentNotFoundError(str(assessment_id))
        return grades
    except AcademicBaseException as e:
        log_academic_error(e, {"endpoint": "get_assessment_grades", "assessment_id": str(assessment_id)})
        raise e.to_http_exception()
    except Exception as e:
        academic_error = handle_database_error(e, "get_assessment_grades")
        log_academic_error(academic_error, {"endpoint": "get_assessment_grades", "assessment_id": str(assessment_id)})
        raise academic_error.to_http_exception()

# =====================================================
# ATTENDANCE MANAGEMENT ENDPOINTS
# =====================================================

@router.post("/attendance/sessions", response_model=AttendanceSession, status_code=status.HTTP_201_CREATED)
async def create_attendance_session_endpoint(
    session_data: AttendanceSessionCreate,
    db: AsyncSession = Depends(get_db),
    auth_context: AcademicAuthContext = Depends(require_attendance_write)
):
    """Create a new attendance session"""
    try:
        session = await crud.create_attendance_session(
            db=db,
            session_data=session_data,
            school_id=str(auth_context.school_id),
            created_by=str(auth_context.user.id)
        )
        return session
    except AcademicBaseException as e:
        log_academic_error(e, {"endpoint": "create_attendance_session", "user_id": str(auth_context.user.id)})
        raise e.to_http_exception()
    except Exception as e:
        academic_error = handle_database_error(e, "create_attendance_session")
        log_academic_error(academic_error, {"endpoint": "create_attendance_session", "user_id": str(auth_context.user.id)})
        raise academic_error.to_http_exception()

@router.post("/attendance/bulk")
async def mark_bulk_attendance_endpoint(
    attendance_data: BulkAttendanceCreate,
    db: AsyncSession = Depends(get_db),
    auth_context: AcademicAuthContext = Depends(require_attendance_write)
):
    """Mark attendance in bulk for a session"""
    try:
        result = await crud.mark_bulk_attendance(
            db=db,
            attendance_data=attendance_data,
            school_id=str(auth_context.school_id),
            marked_by=str(auth_context.user.id)
        )
        return {
            "message": "Attendance marked successfully",
            "records_processed": result["records_processed"]
        }
    except AcademicBaseException as e:
        log_academic_error(e, {"endpoint": "mark_bulk_attendance", "session_id": str(attendance_data.session_id) if hasattr(attendance_data, 'session_id') else None})
        raise e.to_http_exception()
    except Exception as e:
        academic_error = handle_database_error(e, "mark_bulk_attendance")
        log_academic_error(academic_error, {"endpoint": "mark_bulk_attendance"})
        raise academic_error.to_http_exception()

# =====================================================
# UTILITY ENDPOINTS
# =====================================================

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "academic-management"}

@router.get("/enums/terms", response_model=List[Dict[str, Any]])
async def get_terms_enum():
    """Get available terms"""
    return [
        {"value": 1, "label": "Term 1", "description": "January - April"},
        {"value": 2, "label": "Term 2", "description": "May - August"},
        {"value": 3, "label": "Term 3", "description": "September - December"}
    ]

@router.get("/enums/assessment-types", response_model=List[Dict[str, Any]])
async def get_assessment_types_enum():
    """Get available assessment types"""
    return [
        {"value": type.value, "label": type.value.title()}
        for type in AssessmentType
    ]

@router.get("/enums/attendance-statuses", response_model=List[Dict[str, Any]])
async def get_attendance_statuses_enum():
    """Get available attendance statuses"""
    return [
        {"value": status.value, "label": status.value.title()}
        for status in AttendanceStatus
    ]