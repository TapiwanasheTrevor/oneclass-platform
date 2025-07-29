"""
Academic Management API Routes
FastAPI routes for academic management with comprehensive error handling
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.auth import get_current_user, require_permissions
from core.exceptions import NotFoundError, ValidationError, DuplicateError
from core.models import User
from core.pagination import PaginationParams, PaginatedResponse
from core.cache import cache_response

from .schemas import (
    # Subject schemas
    SubjectCreate, SubjectUpdate, Subject,
    # Curriculum schemas
    CurriculumCreate, CurriculumUpdate, Curriculum,
    # Period schemas
    PeriodCreate, PeriodUpdate, Period,
    # Timetable schemas
    TimetableCreate, TimetableUpdate, Timetable, TimetableWithDetails,
    # Attendance schemas
    AttendanceSessionCreate, AttendanceSession, AttendanceRecordCreate,
    AttendanceRecord, BulkAttendanceCreate, AttendanceStats,
    # Assessment schemas
    AssessmentCreate, AssessmentUpdate, Assessment,
    # Grade schemas
    GradeCreate, GradeUpdate, Grade, BulkGradeCreate,
    # Lesson plan schemas
    LessonPlanCreate, LessonPlanUpdate, LessonPlan,
    # Calendar schemas
    CalendarEventCreate, CalendarEventUpdate, CalendarEvent,
    # Dashboard schemas
    AcademicDashboard, TeacherDashboard, StudentPerformance,
    # Response schemas
    BulkOperationResponse, ErrorResponse,
    # Enums
    TermNumber, AssessmentType, AttendanceStatus
)
from .crud import (
    # Subject operations
    create_subject, get_subject, get_subjects, update_subject, delete_subject,
    # Curriculum operations
    create_curriculum, get_curriculum, get_curricula,
    # Period operations
    create_period,
    # Timetable operations
    create_timetable_entry,
    # Attendance operations
    create_attendance_session, mark_bulk_attendance, get_attendance_stats,
    # Assessment operations
    create_assessment, submit_bulk_grades,
    # Dashboard operations
    get_academic_dashboard, get_teacher_dashboard
)

router = APIRouter(prefix="/api/v1/academic", tags=["academic"])

# =====================================================
# SUBJECT ENDPOINTS
# =====================================================

@router.post("/subjects", response_model=Subject, status_code=status.HTTP_201_CREATED)
async def create_subject_endpoint(
    subject_data: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Subject:
    """Create a new subject"""
    try:
        # Check permissions
        await require_permissions(current_user, ["academic.subject.create"])
        
        return await create_subject(
            db=db,
            subject_data=subject_data,
            school_id=current_user.school_id,
            created_by=current_user.id
        )
    except DuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.get("/subjects", response_model=PaginatedResponse[Subject])
async def get_subjects_endpoint(
    grade_level: Optional[int] = Query(None, ge=1, le=13),
    department: Optional[str] = Query(None),
    is_core: Optional[bool] = Query(None),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PaginatedResponse[Subject]:
    """Get subjects with filtering and pagination"""
    try:
        # Check permissions
        await require_permissions(current_user, ["academic.subject.read"])
        
        subjects, total_count = await get_subjects(
            db=db,
            school_id=current_user.school_id,
            grade_level=grade_level,
            department=department,
            is_core=is_core,
            skip=pagination.skip,
            limit=pagination.limit
        )
        
        return PaginatedResponse(
            items=subjects,
            total_count=total_count,
            page=pagination.page,
            page_size=pagination.page_size
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subjects"
        )


@router.get("/subjects/{subject_id}", response_model=Subject)
async def get_subject_endpoint(
    subject_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Subject:
    """Get a specific subject"""
    try:
        # Check permissions
        await require_permissions(current_user, ["academic.subject.read"])
        
        subject = await get_subject(
            db=db,
            subject_id=subject_id,
            school_id=current_user.school_id
        )
        
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )
        
        return subject
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subject"
        )


@router.put("/subjects/{subject_id}", response_model=Subject)
async def update_subject_endpoint(
    subject_id: UUID,
    subject_data: SubjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Subject:
    """Update a subject"""
    try:
        # Check permissions
        await require_permissions(current_user, ["academic.subject.update"])
        
        subject = await update_subject(
            db=db,
            subject_id=subject_id,
            subject_data=subject_data,
            school_id=current_user.school_id,
            updated_by=current_user.id
        )
        
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )
        
        return subject
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    except DuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject_endpoint(
    subject_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a subject"""
    try:
        # Check permissions
        await require_permissions(current_user, ["academic.subject.delete"])
        
        await delete_subject(
            db=db,
            subject_id=subject_id,
            school_id=current_user.school_id,
            deleted_by=current_user.id
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


# =====================================================
# CURRICULUM ENDPOINTS
# =====================================================

@router.post("/curriculum", response_model=Curriculum, status_code=status.HTTP_201_CREATED)
async def create_curriculum_endpoint(
    curriculum_data: CurriculumCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Curriculum:
    """Create a new curriculum"""
    try:
        # Check permissions
        await require_permissions(current_user, ["academic.curriculum.create"])
        
        return await create_curriculum(
            db=db,
            curriculum_data=curriculum_data,
            school_id=current_user.school_id,
            created_by=current_user.id
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except DuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.get("/curriculum", response_model=PaginatedResponse[Curriculum])
async def get_curricula_endpoint(
    academic_year_id: Optional[UUID] = Query(None),
    grade_level: Optional[int] = Query(None, ge=1, le=13),
    subject_id: Optional[UUID] = Query(None),
    term_number: Optional[int] = Query(None, ge=1, le=3),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PaginatedResponse[Curriculum]:
    """Get curricula with filtering and pagination"""
    try:
        # Check permissions
        await require_permissions(current_user, ["academic.curriculum.read"])
        
        curricula, total_count = await get_curricula(
            db=db,
            school_id=current_user.school_id,
            academic_year_id=academic_year_id,
            grade_level=grade_level,
            subject_id=subject_id,
            term_number=term_number,
            skip=pagination.skip,
            limit=pagination.limit
        )
        
        return PaginatedResponse(
            items=curricula,
            total_count=total_count,
            page=pagination.page,
            page_size=pagination.page_size
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve curricula"
        )


@router.get("/curriculum/{curriculum_id}", response_model=Curriculum)
async def get_curriculum_endpoint(
    curriculum_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Curriculum:
    """Get a specific curriculum"""
    try:
        # Check permissions
        await require_permissions(current_user, ["academic.curriculum.read"])
        
        curriculum = await get_curriculum(
            db=db,
            curriculum_id=curriculum_id,
            school_id=current_user.school_id
        )
        
        if not curriculum:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Curriculum not found"
            )
        
        return curriculum
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve curriculum"
        )


# =====================================================
# TIMETABLE ENDPOINTS
# =====================================================

@router.post("/periods", response_model=Period, status_code=status.HTTP_201_CREATED)
async def create_period_endpoint(
    period_data: PeriodCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Period:
    """Create a new period"""
    try:
        # Check permissions
        await require_permissions(current_user, ["academic.timetable.create"])
        
        return await create_period(
            db=db,
            period_data=period_data,
            school_id=current_user.school_id,
            created_by=current_user.id
        )
    except DuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.post("/timetables", response_model=Timetable, status_code=status.HTTP_201_CREATED)
async def create_timetable_endpoint(
    timetable_data: TimetableCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Timetable:
    """Create a new timetable entry"""
    try:
        # Check permissions
        await require_permissions(current_user, ["academic.timetable.create"])
        
        return await create_timetable_entry(
            db=db,
            timetable_data=timetable_data,
            school_id=current_user.school_id,
            created_by=current_user.id
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


# =====================================================
# ATTENDANCE ENDPOINTS
# =====================================================

@router.post("/attendance/sessions", response_model=AttendanceSession, status_code=status.HTTP_201_CREATED)
async def create_attendance_session_endpoint(
    session_data: AttendanceSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AttendanceSession:
    """Create a new attendance session"""
    try:
        # Check permissions
        await require_permissions(current_user, ["academic.attendance.create"])
        
        return await create_attendance_session(
            db=db,
            session_data=session_data,
            school_id=current_user.school_id,
            created_by=current_user.id
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.post("/attendance/bulk", response_model=BulkOperationResponse, status_code=status.HTTP_201_CREATED)
async def mark_bulk_attendance_endpoint(
    attendance_data: BulkAttendanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> BulkOperationResponse:
    """Mark attendance for multiple students"""
    try:
        # Check permissions
        await require_permissions(current_user, ["academic.attendance.create"])
        
        records = await mark_bulk_attendance(
            db=db,
            attendance_data=attendance_data,
            school_id=current_user.school_id,
            marked_by=current_user.id
        )
        
        return BulkOperationResponse(
            total_processed=len(attendance_data.attendance_records),
            successful=len(records),
            failed=0,
            errors=[],
            created_ids=[record.id for record in records]
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.get("/attendance/stats", response_model=AttendanceStats)
async def get_attendance_stats_endpoint(
    class_id: Optional[UUID] = Query(None),
    subject_id: Optional[UUID] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AttendanceStats:
    """Get attendance statistics"""
    try:
        # Check permissions
        await require_permissions(current_user, ["academic.attendance.read"])
        
        return await get_attendance_stats(
            db=db,
            school_id=current_user.school_id,
            class_id=class_id,
            subject_id=subject_id,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve attendance statistics"
        )


# =====================================================
# ASSESSMENT ENDPOINTS
# =====================================================

@router.post("/assessments", response_model=Assessment, status_code=status.HTTP_201_CREATED)
async def create_assessment_endpoint(
    assessment_data: AssessmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Assessment:
    """Create a new assessment"""
    try:
        # Check permissions
        await require_permissions(current_user, ["academic.assessment.create"])
        
        return await create_assessment(
            db=db,
            assessment_data=assessment_data,
            school_id=current_user.school_id,
            created_by=current_user.id
        )
    except DuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.post("/assessments/{assessment_id}/grades/bulk", response_model=BulkOperationResponse)
async def submit_bulk_grades_endpoint(
    assessment_id: UUID,
    grades_data: BulkGradeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> BulkOperationResponse:
    """Submit grades for multiple students"""
    try:
        # Check permissions
        await require_permissions(current_user, ["academic.grade.create"])
        
        # Ensure assessment_id matches
        grades_data.assessment_id = assessment_id
        
        grades = await submit_bulk_grades(
            db=db,
            grades_data=grades_data,
            school_id=current_user.school_id,
            graded_by=current_user.id
        )
        
        return BulkOperationResponse(
            total_processed=len(grades_data.grades),
            successful=len(grades),
            failed=0,
            errors=[],
            created_ids=[grade.id for grade in grades]
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


# =====================================================
# DASHBOARD ENDPOINTS
# =====================================================

@router.get("/dashboard", response_model=AcademicDashboard)
@cache_response(ttl=300)  # Cache for 5 minutes
async def get_academic_dashboard_endpoint(
    academic_year_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AcademicDashboard:
    """Get academic dashboard data"""
    try:
        # Check permissions
        await require_permissions(current_user, ["academic.dashboard.read"])
        
        return await get_academic_dashboard(
            db=db,
            school_id=current_user.school_id,
            academic_year_id=academic_year_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data"
        )


@router.get("/dashboard/teacher", response_model=TeacherDashboard)
@cache_response(ttl=300)  # Cache for 5 minutes
async def get_teacher_dashboard_endpoint(
    academic_year_id: UUID = Query(...),
    teacher_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TeacherDashboard:
    """Get teacher dashboard data"""
    try:
        # Check permissions
        await require_permissions(current_user, ["academic.dashboard.read"])
        
        # Use current user as teacher if not specified
        if teacher_id is None:
            teacher_id = current_user.id
        
        return await get_teacher_dashboard(
            db=db,
            teacher_id=teacher_id,
            school_id=current_user.school_id,
            academic_year_id=academic_year_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve teacher dashboard data"
        )


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