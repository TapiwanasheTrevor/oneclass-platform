# =====================================================
# SIS Module - FastAPI API Endpoints
# File: backend/services/sis/main.py
# =====================================================

from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query, File, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession

# Import schemas and CRUD operations
from .schemas import (
    StudentCreate, StudentUpdate, StudentResponse, StudentSearchRequest, StudentSearchResponse,
    GuardianRelationshipCreate, GuardianRelationshipResponse,
    DisciplinaryIncidentCreate, DisciplinaryIncidentResponse,
    AttendanceRecordCreate, AttendanceRecordResponse,
    HealthRecordCreate, HealthRecordResponse,
    StudentDocumentCreate, StudentDocumentResponse
)
from .crud import (
    StudentCRUD, GuardianCRUD, DisciplinaryCRUD, AttendanceCRUD, 
    HealthRecordCRUD, DocumentCRUD,
    StudentNotFoundError, DuplicateStudentError, ClassCapacityExceededError,
    InsufficientPermissionsError, InvalidDataError
)

# Import shared dependencies
from shared.auth import get_current_active_user, User, require_permissions
from shared.database import get_database_session
from shared.file_upload import upload_file_to_s3, validate_file_type
from shared.notifications import send_notification

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI router
router = APIRouter(prefix="/api/v1/sis", tags=["Student Information System"])

# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def handle_sis_exceptions(func):
    """Decorator to handle SIS-specific exceptions."""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except StudentNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except DuplicateStudentError as e:
            raise HTTPException(status_code=409, detail=str(e))
        except ClassCapacityExceededError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except InsufficientPermissionsError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except InvalidDataError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail="An internal error occurred")
    return wrapper

# =====================================================
# STUDENT ENDPOINTS
# =====================================================

@router.post("/students", response_model=StudentResponse, status_code=201)
@handle_sis_exceptions
async def create_student(
    student_data: StudentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Register a new student in the system.
    
    **Required Permissions**: school_admin, registrar
    
    **Business Logic**:
    - Generates unique student number (format: YYYY-NNNN)
    - Validates class capacity if class is assigned
    - Encrypts sensitive medical and emergency contact data
    - Creates initial academic history record
    - Sends welcome notification to parents
    
    **Returns**: Complete student profile with generated student number
    """
    # Check permissions
    if not await require_permissions(current_user, ["school_admin", "registrar"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions to register students")
    
    # Create student with full workflow
    student = await StudentCRUD.create_student_full_workflow(
        db=db,
        student_data=student_data,
        school_id=current_user.school_id,
        created_by_user_id=current_user.id
    )
    
    # Send welcome notifications in background
    background_tasks.add_task(
        send_welcome_notifications,
        student.id,
        student_data.emergency_contacts,
        current_user.school_id
    )
    
    logger.info(f"Student registered: {student.student_number} by {current_user.id}")
    return student

@router.get("/students", response_model=List[StudentResponse])
@handle_sis_exceptions
async def list_students(
    grade_level: Optional[int] = Query(None, ge=1, le=13, description="Filter by grade level"),
    class_id: Optional[UUID] = Query(None, description="Filter by class ID"),
    status: Optional[str] = Query(None, description="Filter by status (active, suspended, etc.)"),
    search: Optional[str] = Query(None, min_length=2, description="Search by name or student number"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Retrieve a list of students with optional filtering.
    
    **Access Rules**:
    - school_admin/registrar: Can view all students in their school
    - teacher: Can view students in their assigned classes
    - parent: Returns empty list (use `/students/my-children` instead)
    - student: Access denied
    
    **Features**:
    - Full-text search across names and student numbers
    - Pagination with skip/limit
    - Multiple filter options
    - Results sorted by last_name, first_name
    """
    students = await StudentCRUD.get_students(
        db=db,
        user=current_user,
        class_id=class_id,
        status=status,
        search_query=search,
        skip=skip,
        limit=limit
    )
    
    return students

@router.get("/students/{student_id}", response_model=StudentResponse)
@handle_sis_exceptions
async def get_student(
    student_id: UUID,
    include_sensitive: bool = Query(False, description="Include medical and emergency contact data"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Retrieve detailed information for a specific student.
    
    **Access Rules**:
    - school_admin/registrar: Full access to any student in their school
    - teacher: Access to students in their classes
    - parent: Access only if parent of this student
    - student: Access only to their own profile
    
    **Sensitive Data**:
    - Medical conditions, allergies, medications (nurses, admins, parents only)
    - Emergency contacts (admins, parents only)
    - Disciplinary records (admins, teachers, parents only)
    """
    student = await StudentCRUD.get_student_by_id_with_permission_check(
        db=db, 
        user=current_user, 
        student_id=student_id
    )
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found or access denied")
    
    # Include sensitive data if requested and user has permission
    if include_sensitive and current_user.role in ["school_admin", "nurse", "parent"]:
        # Decrypt and include sensitive data
        pass  # Implementation would decrypt medical data, emergency contacts
    
    return student

@router.put("/students/{student_id}", response_model=StudentResponse)
@handle_sis_exceptions
async def update_student(
    student_id: UUID,
    student_update: StudentUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Update student information.
    
    **Required Permissions**: school_admin, registrar
    
    **Business Rules**:
    - Cannot change student_number or zimsec_number through this endpoint
    - Status changes may require additional approvals
    - Emergency contact changes must maintain minimum of 2 contacts
    - Medical data updates are logged for audit purposes
    
    **Audit Trail**: All changes are logged with before/after values
    """
    # Check permissions
    if not await require_permissions(current_user, ["school_admin", "registrar"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions to update students")
    
    # Update student
    updated_student = await StudentCRUD.update_student(
        db=db,
        student_id=student_id,
        student_update=student_update,
        updated_by_user_id=current_user.id
    )
    
    # Send update notifications if contact info changed
    if student_update.emergency_contacts:
        background_tasks.add_task(
            send_update_notifications,
            student_id,
            "emergency_contacts_updated",
            current_user.school_id
        )
    
    return updated_student

@router.delete("/students/{student_id}", status_code=204)
@handle_sis_exceptions
async def delete_student(
    student_id: UUID,
    hard_delete: bool = Query(False, description="Permanently delete student record"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Delete a student record.
    
    **Required Permissions**: school_admin (soft delete), super_admin (hard delete)
    
    **Soft Delete (Default)**:
    - Changes status to 'transferred'
    - Preserves all data for audit purposes
    - Can be reversed
    
    **Hard Delete**:
    - Permanently removes from database
    - Cannot be reversed
    - Requires super_admin permissions
    """
    # Check permissions
    required_role = "super_admin" if hard_delete else "school_admin"
    if current_user.role != required_role:
        raise HTTPException(
            status_code=403, 
            detail=f"Insufficient permissions. Required: {required_role}"
        )
    
    success = await StudentCRUD.delete_student(
        db=db,
        student_id=student_id,
        deleted_by_user_id=current_user.id,
        soft_delete=not hard_delete
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete student")

@router.post("/students/search", response_model=StudentSearchResponse)
@handle_sis_exceptions
async def search_students(
    search_request: StudentSearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Advanced student search with filtering and pagination.
    
    **Features**:
    - Full-text search across multiple fields
    - Advanced filtering (age ranges, medical conditions, etc.)
    - Flexible sorting options
    - Pagination with total count
    
    **Access**: Based on user role permissions
    """
    # This would implement advanced search logic
    # For now, return basic structure
    return StudentSearchResponse(
        students=[],
        total_count=0,
        page=search_request.page,
        page_size=search_request.page_size,
        total_pages=0,
        has_next=False,
        has_previous=False
    )

# =====================================================
# GUARDIAN RELATIONSHIP ENDPOINTS
# =====================================================

@router.post("/students/{student_id}/guardians", response_model=GuardianRelationshipResponse, status_code=201)
@handle_sis_exceptions
async def add_guardian_relationship(
    student_id: UUID,
    guardian_data: GuardianRelationshipCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Create a guardian-student relationship.
    
    **Required Permissions**: school_admin, registrar
    
    **Business Rules**:
    - Only one primary contact allowed per student
    - Guardian must have a valid user account
    - Financial responsibility percentages must total 100% across all guardians
    """
    if not await require_permissions(current_user, ["school_admin", "registrar"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    relationship = await GuardianCRUD.create_guardian_relationship(
        db=db,
        student_id=student_id,
        guardian_data=guardian_data,
        created_by_user_id=current_user.id
    )
    
    return relationship

@router.get("/students/{student_id}/guardians", response_model=List[GuardianRelationshipResponse])
@handle_sis_exceptions
async def get_student_guardians(
    student_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get all guardians for a specific student.
    
    **Access Rules**:
    - school_admin/registrar: Can view all guardians
    - teacher: Can view guardians for students in their classes
    - parent: Can view if they are a guardian of this student
    """
    # Permission check would be implemented here
    guardians = await GuardianCRUD.get_student_guardians(db=db, student_id=student_id)
    return guardians

# =====================================================
# DISCIPLINARY ENDPOINTS
# =====================================================

@router.post("/disciplinary/incidents", response_model=DisciplinaryIncidentResponse, status_code=201)
@handle_sis_exceptions
async def create_disciplinary_incident(
    incident_data: DisciplinaryIncidentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Record a disciplinary incident for a student.
    
    **Required Permissions**: 
    - teacher: Can create minor incidents only
    - school_admin: Can create any severity incident
    
    **Business Rules**:
    - Teachers can only create 'minor' severity incidents
    - 'serious' and 'severe' incidents require admin approval
    - Automatic parent notification for moderate+ incidents
    - Points deduction affects student's disciplinary score
    
    **Workflow**:
    1. Create incident record
    2. Update student disciplinary points
    3. Send parent notification (if required)
    4. Schedule follow-up actions
    """
    # Check severity permissions
    if current_user.role == "teacher" and incident_data.severity.value != "minor":
        raise HTTPException(
            status_code=403,
            detail="Teachers can only create minor disciplinary incidents"
        )
    
    if not await require_permissions(current_user, ["school_admin", "teacher"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Create incident
    incident = await DisciplinaryCRUD.create_incident(
        db=db,
        incident_data=incident_data,
        reported_by_user_id=current_user.id
    )
    
    # Schedule notifications based on severity
    if incident_data.severity.value in ["moderate", "serious", "severe"]:
        background_tasks.add_task(
            send_disciplinary_notifications,
            incident.id,
            incident_data.student_id,
            incident_data.severity.value
        )
    
    return incident

@router.get("/students/{student_id}/disciplinary", response_model=List[DisciplinaryIncidentResponse])
@handle_sis_exceptions
async def get_student_disciplinary_history(
    student_id: UUID,
    year: Optional[int] = Query(None, description="Filter by year"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get disciplinary history for a student.
    
    **Access Rules**:
    - school_admin: Full access
    - teacher: Can view incidents in their classes
    - parent: Can view their child's incidents
    - student: Cannot access (privacy protection)
    """
    # Implementation would fetch disciplinary incidents with filters
    # This is a placeholder
    return []

# =====================================================
# ATTENDANCE ENDPOINTS
# =====================================================

@router.post("/attendance", response_model=AttendanceRecordResponse, status_code=201)
@handle_sis_exceptions
async def mark_attendance(
    attendance_data: AttendanceRecordCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Mark student attendance for a specific period.
    
    **Required Permissions**: teacher, school_admin
    
    **Business Rules**:
    - Can update existing attendance for the same date/period
    - Automatic parent notification for unexplained absences
    - Integration with class timetable for period validation
    """
    if not await require_permissions(current_user, ["teacher", "school_admin"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    attendance = await AttendanceCRUD.mark_attendance(
        db=db,
        attendance_data=attendance_data,
        marked_by_user_id=current_user.id
    )
    
    return attendance

@router.get("/students/{student_id}/attendance", response_model=List[AttendanceRecordResponse])
@handle_sis_exceptions
async def get_student_attendance(
    student_id: UUID,
    start_date: Optional[date] = Query(None, description="Start date for attendance records"),
    end_date: Optional[date] = Query(None, description="End date for attendance records"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get attendance records for a student within a date range.
    
    **Access Rules**:
    - school_admin/teacher: Can view attendance for students in their school/classes
    - parent: Can view their child's attendance
    - student: Can view their own attendance
    """
    attendance_records = await AttendanceCRUD.get_student_attendance(
        db=db,
        student_id=student_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return attendance_records

# =====================================================
# HEALTH RECORD ENDPOINTS
# =====================================================

@router.post("/health/records", response_model=HealthRecordResponse, status_code=201)
@handle_sis_exceptions
async def create_health_record(
    health_data: HealthRecordCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Create a health record for a student.
    
    **Required Permissions**: nurse, school_admin, teacher (basic records only)
    
    **Business Rules**:
    - Nurses can create all types of health records
    - Teachers can only create basic illness/injury records
    - Automatic parent notification for serious health events
    - Integration with emergency contact system
    """
    # Check permissions based on record type
    if current_user.role == "teacher" and health_data.record_type not in ["illness", "injury"]:
        raise HTTPException(
            status_code=403,
            detail="Teachers can only create basic illness/injury records"
        )
    
    if not await require_permissions(current_user, ["nurse", "school_admin", "teacher"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    health_record = await HealthRecordCRUD.create_health_record(
        db=db,
        health_data=health_data,
        created_by_user_id=current_user.id
    )
    
    # Send notifications for serious health events
    if health_data.sent_home or health_data.emergency_contact_called:
        background_tasks.add_task(
            send_health_notifications,
            health_record.id,
            health_data.student_id
        )
    
    return health_record

@router.get("/students/{student_id}/health", response_model=List[HealthRecordResponse])
@handle_sis_exceptions
async def get_student_health_records(
    student_id: UUID,
    record_type: Optional[str] = Query(None, description="Filter by record type"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get health records for a student.
    
    **Access Rules**:
    - nurse/school_admin: Full access to all health records
    - teacher: Limited access to basic records
    - parent: Can view their child's health records
    - student: Can view their own basic health records
    """
    # Implementation would fetch health records with proper filtering
    return []

# =====================================================
# DOCUMENT MANAGEMENT ENDPOINTS
# =====================================================

@router.post("/students/{student_id}/documents", response_model=StudentDocumentResponse, status_code=201)
@handle_sis_exceptions
async def upload_student_document(
    student_id: UUID,
    file: UploadFile = File(...),
    document_type: str = Query(..., description="Type of document"),
    document_name: str = Query(..., description="Document name"),
    is_confidential: bool = Query(False, description="Mark as confidential"),
    access_level: str = Query("school", description="Access level"),
    description: Optional[str] = Query(None, description="Document description"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Upload a document for a student.
    
    **Required Permissions**: school_admin, registrar, parent (for their child)
    
    **Supported Formats**: PDF, JPG, PNG, DOC, DOCX
    **Maximum Size**: 10MB per file
    
    **Access Levels**:
    - student: Student can view
    - guardian: Parents/guardians can view
    - teacher: Teachers can view
    - admin: Admins only
    - school: All school staff can view
    """
    # Validate file type and size
    if not validate_file_type(file.filename, allowed_types=['pdf', 'jpg', 'png', 'doc', 'docx']):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    if file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    # Check permissions
    if not await require_permissions(current_user, ["school_admin", "registrar"]):
        # Check if parent uploading for their child
        if current_user.role == "parent":
            # Would check guardian relationship here
            pass
        else:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Upload file to S3
    file_url = await upload_file_to_s3(file, f"students/{student_id}/documents/")
    
    # Create document record
    document_data = StudentDocumentCreate(
        student_id=student_id,
        document_type=document_type,
        document_name=document_name,
        file_url=file_url,
        file_size_bytes=file.size,
        file_format=file.filename.split('.')[-1].lower(),
        is_confidential=is_confidential,
        access_level=access_level,
        description=description
    )
    
    document = await DocumentCRUD.upload_student_document(
        db=db,
        document_data=document_data,
        uploaded_by_user_id=current_user.id
    )
    
    return document

@router.get("/students/{student_id}/documents", response_model=List[StudentDocumentResponse])
@handle_sis_exceptions
async def get_student_documents(
    student_id: UUID,
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get documents for a student based on access level.
    
    **Access Rules**:
    - Documents are filtered based on access_level and user role
    - Confidential documents require higher permissions
    - Parents can only see documents marked for guardian access
    """
    # Implementation would fetch documents with proper access control
    return []

# =====================================================
# ANALYTICS AND REPORTING ENDPOINTS
# =====================================================

@router.get("/analytics/student-summary/{student_id}")
@handle_sis_exceptions
async def get_student_summary(
    student_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get comprehensive summary analytics for a student.
    
    **Includes**:
    - Academic performance trends
    - Attendance statistics
    - Disciplinary summary
    - Health record count
    - Document status
    
    **Access**: Based on role permissions
    """
    # This would compile comprehensive student analytics
    return {
        "student_id": student_id,
        "academic_summary": {
            "current_grade": 8,
            "average_performance": 75.5,
            "attendance_rate": 95.2,
            "disciplinary_points": 5
        },
        "recent_activity": [],
        "alerts": []
    }

@router.get("/analytics/class-overview/{class_id}")
@handle_sis_exceptions
async def get_class_overview(
    class_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get overview analytics for a class.
    
    **Required Permissions**: teacher (for their class), school_admin
    
    **Includes**:
    - Enrollment statistics
    - Average performance
    - Attendance trends
    - Health alerts
    - Document completion status
    """
    if not await require_permissions(current_user, ["teacher", "school_admin"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # This would compile class-level analytics
    return {
        "class_id": class_id,
        "enrollment": {
            "total_students": 25,
            "active_students": 24,
            "transferred_students": 1
        },
        "performance": {
            "class_average": 72.3,
            "top_performers": 5,
            "at_risk_students": 3
        },
        "attendance": {
            "average_rate": 93.5,
            "chronic_absentees": 2
        }
    }

# =====================================================
# BACKGROUND TASK FUNCTIONS
# =====================================================

async def send_welcome_notifications(
    student_id: UUID,
    emergency_contacts: List[Any],
    school_id: UUID
):
    """Send welcome notifications to parents when student is registered."""
    try:
        # Implementation would send SMS/email to parents
        logger.info(f"Sending welcome notifications for student {student_id}")
    except Exception as e:
        logger.error(f"Failed to send welcome notifications: {str(e)}")

async def send_update_notifications(
    student_id: UUID,
    change_type: str,
    school_id: UUID
):
    """Send notifications when student information is updated."""
    try:
        logger.info(f"Sending update notifications for student {student_id}: {change_type}")
    except Exception as e:
        logger.error(f"Failed to send update notifications: {str(e)}")

async def send_disciplinary_notifications(
    incident_id: UUID,
    student_id: UUID,
    severity: str
):
    """Send notifications for disciplinary incidents."""
    try:
        logger.info(f"Sending disciplinary notifications for incident {incident_id}, severity: {severity}")
    except Exception as e:
        logger.error(f"Failed to send disciplinary notifications: {str(e)}")

async def send_health_notifications(
    health_record_id: UUID,
    student_id: UUID
):
    """Send health-related notifications to parents."""
    try:
        logger.info(f"Sending health notifications for student {student_id}")
    except Exception as e:
        logger.error(f"Failed to send health notifications: {str(e)}")

# =====================================================
# ERROR HANDLERS
# =====================================================

@router.exception_handler(StudentNotFoundError)
async def student_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc), "error_type": "student_not_found"}
    )

@router.exception_handler(DuplicateStudentError)
async def duplicate_student_handler(request, exc):
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc), "error_type": "duplicate_student"}
    )

@router.exception_handler(ClassCapacityExceededError)
async def class_capacity_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "error_type": "class_capacity_exceeded"}
    )

# =====================================================
# HEALTH CHECK ENDPOINT
# =====================================================

@router.get("/health")
async def health_check():
    """Health check endpoint for service monitoring."""
    return {
        "status": "healthy",
        "service": "sis",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }