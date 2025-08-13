# =====================================================
# SIS Students Routes with Multitenancy Support
# File: backend/services/sis/routes/students.py
# =====================================================

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import io

from shared.auth import get_current_active_user, require_permission, require_feature
from shared.models.platform_user import PlatformUser as EnhancedUser
from shared.database import get_db_session
from shared.file_storage import upload_student_document, upload_student_photo
from ..schemas import (
    StudentCreate, StudentUpdate, StudentResponse, StudentSearchRequest,
    StudentSearchResponse, GuardianRelationshipCreate, GuardianRelationshipResponse
)
from ..crud import StudentCRUD, GuardianCRUD
from ..family_crud import FamilyCRUD, EnhancedGuardianCRUD, EmergencyContactCRUD
from ..bulk_operations import BulkImportService, BulkExportService
from ..zimbabwe_validators import ZimbabweValidator
from ..family_schemas import (
    FamilyGroupCreate, FamilyGroupResponse, FamilyOverviewResponse,
    GuardianRelationshipCreateEnhanced, GuardianRelationshipResponseEnhanced,
    EmergencyContactCreate, EmergencyContactResponse, EmergencyContactUpdate,
    StudentFamilyMembershipCreate, GuardianFamilyMembershipCreate
)

router = APIRouter(prefix="/students", tags=["students"])

# =====================================================
# ENHANCED STUDENT CRUD ENDPOINTS
# =====================================================

@router.post("/", response_model=StudentResponse)
@require_permission("students.create")
@require_feature("student_management")
async def create_student(
    student_data: StudentCreate,
    db = Depends(get_db_session),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Create a new student with Zimbabwe-specific validation.
    Includes comprehensive validation for emergency contacts and medical data.
    """
    try:
        # Validate National ID if provided
        if hasattr(student_data, 'national_id') and student_data.national_id:
            valid, formatted_id = ZimbabweValidator.validate_national_id(student_data.national_id)
            if not valid:
                raise HTTPException(status_code=400, detail=formatted_id)
        
        student = await StudentCRUD.create_student_full_workflow(
            db, student_data, current_user.school_id, current_user.id
        )
        
        return StudentResponse.from_orm(student)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{student_id}", response_model=StudentResponse)
@require_permission("students.read")
async def get_student(
    student_id: UUID,
    db = Depends(get_db_session),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """Get a specific student by ID with role-based access control."""
    student = await StudentCRUD.get_student_by_id_with_permission_check(
        db, current_user, student_id
    )
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return StudentResponse.from_orm(student)

@router.put("/{student_id}", response_model=StudentResponse)
@require_permission("students.update")
async def update_student(
    student_id: UUID,
    student_update: StudentUpdate,
    db = Depends(get_db_session),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """Update student information with audit trail."""
    try:
        student = await StudentCRUD.update_student(
            db, student_id, student_update, current_user.id
        )
        return StudentResponse.from_orm(student)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{student_id}")
@require_permission("students.delete")
async def delete_student(
    student_id: UUID,
    soft_delete: bool = Query(True, description="Perform soft delete to preserve records"),
    db = Depends(get_db_session),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """Delete student (soft delete by default)."""
    try:
        success = await StudentCRUD.delete_student(
            db, student_id, current_user.id, soft_delete=soft_delete
        )
        return {"success": success, "message": "Student deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# =====================================================
# GUARDIAN RELATIONSHIP ENDPOINTS
# =====================================================

@router.post("/{student_id}/guardians", response_model=GuardianRelationshipResponse)
@require_permission("students.update")
async def add_guardian_relationship(
    student_id: UUID,
    guardian_data: GuardianRelationshipCreate,
    db = Depends(get_db_session),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """Add a guardian relationship to a student."""
    try:
        relationship = await GuardianCRUD.create_guardian_relationship(
            db, student_id, guardian_data, current_user.id
        )
        return GuardianRelationshipResponse.from_orm(relationship)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{student_id}/guardians", response_model=List[GuardianRelationshipResponse])
@require_permission("students.read")
async def get_student_guardians(
    student_id: UUID,
    db = Depends(get_db_session),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """Get all guardians for a student."""
    guardians = await GuardianCRUD.get_student_guardians(db, student_id)
    return [GuardianRelationshipResponse.from_orm(g) for g in guardians]

# =====================================================
# BULK OPERATIONS ENDPOINTS
# =====================================================

@router.post("/bulk/import-csv")
@require_permission("students.bulk_import")
@require_feature("bulk_operations")
async def bulk_import_csv(
    file: UploadFile = File(...),
    validate_only: bool = Form(False),
    db = Depends(get_db_session),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Bulk import students from CSV file.
    Includes comprehensive validation and error reporting.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV format")
    
    try:
        file_content = await file.read()
        
        results = await BulkImportService.import_from_csv(
            db, file_content, current_user.school_id, current_user.id, validate_only
        )
        
        return {
            "success": True,
            "message": f"Import completed: {results['successful']} successful, {results['failed']} failed",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")

@router.post("/bulk/import-excel")
@require_permission("students.bulk_import")
@require_feature("bulk_operations")
async def bulk_import_excel(
    file: UploadFile = File(...),
    sheet_name: Optional[str] = Form(None),
    validate_only: bool = Form(False),
    db = Depends(get_db_session),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """Bulk import students from Excel file."""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be Excel format")
    
    try:
        file_content = await file.read()
        
        results = await BulkImportService.import_from_excel(
            db, file_content, current_user.school_id, current_user.id, sheet_name, validate_only
        )
        
        return {
            "success": True,
            "message": f"Import completed: {results['successful']} successful, {results['failed']} failed",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")

@router.get("/bulk/export-csv")
@require_permission("students.export")
async def export_students_csv(
    include_sensitive: bool = Query(False, description="Include sensitive medical/contact data"),
    grade_level: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    class_id: Optional[UUID] = Query(None),
    db = Depends(get_db_session),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """Export students to CSV format."""
    try:
        filters = {}
        if grade_level:
            filters['grade_level'] = grade_level
        if status:
            filters['status'] = status
        if class_id:
            filters['class_id'] = class_id
        
        csv_data = await BulkExportService.export_to_csv(
            db, current_user.school_id, filters, include_sensitive
        )
        
        return StreamingResponse(
            io.BytesIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=students.csv"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/bulk/template")
@require_permission("students.bulk_import")
async def download_import_template():
    """Download CSV template for bulk import."""
    template_data = BulkImportService.generate_import_template()
    
    return StreamingResponse(
        io.BytesIO(template_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=student_import_template.csv"}
    )

# =====================================================
# VALIDATION ENDPOINTS
# =====================================================

@router.post("/validate/national-id")
async def validate_national_id(
    national_id: str = Form(...),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """Validate Zimbabwe National ID format and extract information."""
    valid, message = ZimbabweValidator.validate_national_id(national_id)
    
    result = {
        "valid": valid,
        "formatted_id": message if valid else None,
        "error": message if not valid else None
    }
    
    if valid:
        # Extract additional info from ID
        age = ZimbabweValidator.calculate_age_from_id(message)
        if age:
            result["calculated_age"] = age
    
    return result

@router.post("/validate/phone")
async def validate_phone_number(
    phone: str = Form(...),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """Validate Zimbabwe phone number format."""
    valid, formatted = ZimbabweValidator.validate_phone_number(phone)
    
    return {
        "valid": valid,
        "formatted_phone": formatted if valid else None,
        "error": formatted if not valid else None
    }

# =====================================================
# ENHANCED FAMILY MANAGEMENT ENDPOINTS
# =====================================================

@router.post("/{student_id}/guardians/enhanced", response_model=GuardianRelationshipResponseEnhanced)
@require_permission("students.update")
async def create_enhanced_guardian_relationship(
    student_id: UUID,
    guardian_data: GuardianRelationshipCreateEnhanced,
    db = Depends(get_db_session),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """Create an enhanced guardian-student relationship with comprehensive details."""
    try:
        relationship = await EnhancedGuardianCRUD.create_comprehensive_guardian_relationship(
            db, student_id, guardian_data.guardian_user_id, 
            guardian_data.dict(exclude={'guardian_user_id'}), current_user.id
        )
        return GuardianRelationshipResponseEnhanced.from_orm(relationship)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{student_id}/guardians/comprehensive", response_model=List[GuardianRelationshipResponseEnhanced])
@require_permission("students.read")
async def get_comprehensive_guardian_relationships(
    student_id: UUID,
    include_inactive: bool = Query(False),
    db = Depends(get_db_session),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """Get comprehensive guardian relationships for a student."""
    relationships = await EnhancedGuardianCRUD.get_student_guardians_comprehensive(
        db, student_id, include_inactive
    )
    return [GuardianRelationshipResponseEnhanced.from_orm(r) for r in relationships]

@router.put("/guardian-relationships/{relationship_id}", response_model=GuardianRelationshipResponseEnhanced)
@require_permission("students.update")
async def update_guardian_relationship(
    relationship_id: UUID,
    update_data: Dict[str, Any],
    db = Depends(get_db_session),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """Update a guardian relationship."""
    try:
        relationship = await EnhancedGuardianCRUD.update_guardian_relationship(
            db, relationship_id, update_data, current_user.id
        )
        return GuardianRelationshipResponseEnhanced.from_orm(relationship)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# =====================================================
# FAMILY GROUP MANAGEMENT ENDPOINTS
# =====================================================

@router.post("/families", response_model=FamilyGroupResponse)
@require_permission("families.create")
async def create_family_group(
    family_data: FamilyGroupCreate,
    db = Depends(get_db_session),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """Create a new family group."""
    try:
        family_group = await FamilyCRUD.create_family_group(
            db, 
            family_data.family_name,
            family_data.primary_contact_user_id,
            current_user.school_id,
            current_user.id,
            family_data.dict(exclude={'family_name', 'primary_contact_user_id'})
        )
        return FamilyGroupResponse.from_orm(family_group)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{student_id}/families/{family_id}/add", response_model=Dict[str, Any])
@require_permission("students.update")
async def add_student_to_family(
    student_id: UUID,
    family_id: UUID,
    membership_data: StudentFamilyMembershipCreate,
    db = Depends(get_db_session),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """Add a student to a family group."""
    try:
        membership = await FamilyCRUD.add_student_to_family(
            db, student_id, family_id, membership_data.dict(exclude={'family_group_id'})
        )
        return {
            "success": True,
            "message": "Student added to family successfully",
            "membership_id": str(membership.id)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/families/{family_id}/guardians/add", response_model=Dict[str, Any])
@require_permission("families.update")
async def add_guardian_to_family(
    family_id: UUID,
    guardian_data: GuardianFamilyMembershipCreate,
    db = Depends(get_db_session),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """Add a guardian to a family group."""
    try:
        membership = await FamilyCRUD.add_guardian_to_family(
            db, guardian_data.guardian_user_id, family_id, 
            guardian_data.dict(exclude={'family_group_id', 'guardian_user_id'})
        )
        return {
            "success": True,
            "message": "Guardian added to family successfully",
            "membership_id": str(membership.id)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/families/{family_id}/overview", response_model=FamilyOverviewResponse)
@require_permission("families.read")
async def get_family_overview(
    family_id: UUID,
    db = Depends(get_db_session),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """Get comprehensive overview of a family group."""
    try:
        # Get family group details
        family_query = select(FamilyGroup).where(FamilyGroup.id == family_id)
        result = await db.execute(family_query)
        family_group = result.scalar_one_or_none()
        
        if not family_group:
            raise HTTPException(status_code=404, detail="Family group not found")
        
        # Get family students
        students = await FamilyCRUD.get_family_students(db, family_id)
        
        # Get emergency contacts for all students
        emergency_contacts = []
        for student in students:
            contacts = await EmergencyContactCRUD.get_student_emergency_contacts(db, student.id)
            emergency_contacts.extend(contacts)
        
        return FamilyOverviewResponse(
            family_group=FamilyGroupResponse.from_orm(family_group),
            students=[{
                "id": str(s.id),
                "name": f"{s.first_name} {s.last_name}",
                "grade": s.current_grade_level,
                "status": s.enrollment_status
            } for s in students],
            guardians=[],  # Would need to implement guardian details fetch
            emergency_contacts=[EmergencyContactResponse.from_orm(ec) for ec in emergency_contacts]
        )
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================
# EMERGENCY CONTACT ENDPOINTS
# =====================================================

@router.post("/{student_id}/emergency-contacts", response_model=EmergencyContactResponse)
@require_permission("students.update")
async def create_emergency_contact(
    student_id: UUID,
    contact_data: EmergencyContactCreate,
    db = Depends(get_db_session),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """Create an emergency contact for a student."""
    try:
        contact = await EmergencyContactCRUD.create_emergency_contact(
            db, student_id, contact_data.dict(), current_user.id
        )
        return EmergencyContactResponse.from_orm(contact)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{student_id}/emergency-contacts", response_model=List[EmergencyContactResponse])
@require_permission("students.read")
async def get_student_emergency_contacts(
    student_id: UUID,
    active_only: bool = Query(True),
    db = Depends(get_db_session),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """Get emergency contacts for a student."""
    contacts = await EmergencyContactCRUD.get_student_emergency_contacts(
        db, student_id, active_only
    )
    return [EmergencyContactResponse.from_orm(c) for c in contacts]

@router.put("/emergency-contacts/{contact_id}", response_model=EmergencyContactResponse)
@require_permission("students.update")
async def update_emergency_contact(
    contact_id: UUID,
    update_data: EmergencyContactUpdate,
    db = Depends(get_db_session),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """Update an emergency contact."""
    try:
        # Get existing contact
        query = select(EmergencyContact).where(EmergencyContact.id == contact_id)
        result = await db.execute(query)
        contact = result.scalar_one_or_none()
        
        if not contact:
            raise HTTPException(status_code=404, detail="Emergency contact not found")
        
        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            if hasattr(contact, field):
                setattr(contact, field, value)
        
        contact.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(contact)
        
        return EmergencyContactResponse.from_orm(contact)
        
    except Exception as e:
        await db.rollback()
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=StudentSearchResponse)
@require_permission("students.read")
@require_feature("student_management")
async def get_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    grade_level: Optional[int] = None,
    class_id: Optional[UUID] = None,
    status: Optional[str] = None,
    db = Depends(get_db_session),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get students list with pagination and filtering.
    Automatically filtered by school context.
    """
    search_request = StudentSearchRequest(
        search_query=search,
        filters={
            "grade_level": grade_level,
            "class_id": class_id,
            "status": status
        },
        page=page,
        page_size=page_size
    )
    
    students = await StudentCRUD.get_students(
        db, current_user, class_id=class_id, status=status,
        search_query=search, skip=(page-1)*page_size, limit=page_size
    )
    
    total_count = len(students)  # Would need separate count query in production
    total_pages = (total_count + page_size - 1) // page_size
    
    return StudentSearchResponse(
        students=[StudentResponse.from_orm(s) for s in students],
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1
    )

@router.get("/{student_id}", response_model=StudentDetailResponse)
@require_permission("students.read")
@require_feature("student_management")
async def get_student(
    student_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get detailed student information.
    Automatically validates school context.
    """
    student = await StudentCRUD.get_student_by_id(student_id, current_user.school_id)
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return student

@router.post("/", response_model=StudentResponse)
@require_permission("students.create")
@require_feature("student_management")
async def create_student(
    student_data: StudentCreate,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Create a new student.
    Automatically sets school context and validates limits.
    """
    # Check subscription limits
    current_count = await StudentCRUD.get_student_count(current_user.school_id)
    if current_count >= current_user.school_config.max_students:
        raise HTTPException(
            status_code=400,
            detail=f"Student limit reached. Maximum {current_user.school_config.max_students} students allowed."
        )
    
    # Set school context
    student_data.school_id = current_user.school_id
    student_data.created_by = current_user.id
    
    # Generate student number using school format
    student_number = await StudentCRUD.generate_student_number(
        current_user.school_id,
        current_user.school_config.student_id_format
    )
    student_data.student_number = student_number
    
    student = await StudentCRUD.create_student(student_data)
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "student_management")
    
    return student

@router.put("/{student_id}", response_model=StudentResponse)
@require_permission("students.update")
@require_feature("student_management")
async def update_student(
    student_id: UUID,
    student_data: StudentUpdate,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Update student information.
    Automatically validates school context.
    """
    # Verify student belongs to current school
    existing_student = await StudentCRUD.get_student_by_id(student_id, current_user.school_id)
    if not existing_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student = await StudentCRUD.update_student(student_id, student_data)
    return student

@router.delete("/{student_id}")
@require_permission("students.delete")
@require_feature("student_management")
async def delete_student(
    student_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Delete (soft delete) a student.
    Automatically validates school context.
    """
    # Verify student belongs to current school
    existing_student = await StudentCRUD.get_student_by_id(student_id, current_user.school_id)
    if not existing_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    await StudentCRUD.delete_student(student_id)
    return {"message": "Student deleted successfully"}

@router.post("/{student_id}/photo")
@require_permission("students.update")
@require_feature("student_management")
async def upload_student_photo_endpoint(
    student_id: UUID,
    file: UploadFile = File(...),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Upload student profile photo.
    Uses school-isolated file storage.
    """
    # Verify student belongs to current school
    existing_student = await StudentCRUD.get_student_by_id(student_id, current_user.school_id)
    if not existing_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Upload photo with school isolation
    result = await upload_student_photo(file, current_user.school_id, student_id)
    
    # Update student record with photo URL
    await StudentCRUD.update_student_photo(student_id, result["file_url"])
    
    return result

@router.post("/{student_id}/documents")
@require_permission("students.update")
@require_feature("student_management")
async def upload_student_document_endpoint(
    student_id: UUID,
    file: UploadFile = File(...),
    document_type: str = "other",
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Upload student document.
    Uses school-isolated file storage.
    """
    # Verify student belongs to current school
    existing_student = await StudentCRUD.get_student_by_id(student_id, current_user.school_id)
    if not existing_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Upload document with school isolation
    result = await upload_student_document(file, current_user.school_id, student_id)
    
    # Save document record
    await StudentCRUD.add_student_document(
        student_id=student_id,
        document_type=document_type,
        file_url=result["file_url"],
        file_name=result["original_filename"],
        uploaded_by=current_user.id
    )
    
    return result

@router.get("/{student_id}/academic-history")
@require_permission("students.read")
@require_feature("student_management")
async def get_student_academic_history(
    student_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get student academic history.
    Automatically validates school context.
    """
    # Verify student belongs to current school
    existing_student = await StudentCRUD.get_student_by_id(student_id, current_user.school_id)
    if not existing_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    history = await StudentCRUD.get_academic_history(student_id)
    return history

@router.get("/{student_id}/guardians")
@require_permission("students.read")
@require_feature("student_management")
async def get_student_guardians(
    student_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get student guardians.
    Automatically validates school context.
    """
    # Verify student belongs to current school
    existing_student = await StudentCRUD.get_student_by_id(student_id, current_user.school_id)
    if not existing_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    guardians = await StudentCRUD.get_student_guardians(student_id)
    return guardians

@router.post("/{student_id}/guardians")
@require_permission("students.update")
@require_feature("student_management")
async def add_student_guardian(
    student_id: UUID,
    guardian_id: UUID,
    relationship: str,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Add guardian to student.
    Automatically validates school context.
    """
    # Verify student belongs to current school
    existing_student = await StudentCRUD.get_student_by_id(student_id, current_user.school_id)
    if not existing_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Verify guardian belongs to current school
    guardian = await StudentCRUD.get_guardian_by_id(guardian_id, current_user.school_id)
    if not guardian:
        raise HTTPException(status_code=404, detail="Guardian not found")
    
    await StudentCRUD.add_student_guardian(student_id, guardian_id, relationship)
    return {"message": "Guardian added successfully"}

# Helper function to track feature usage
async def track_feature_usage(school_id: UUID, feature_name: str):
    """Track feature usage for analytics"""
    try:
        from shared.database import get_database_connection
        
        async with get_database_connection() as conn:
            await conn.execute("""
                INSERT INTO platform.school_feature_usage (school_id, feature_name, usage_count, last_used_at)
                VALUES ($1, $2, 1, NOW())
                ON CONFLICT (school_id, feature_name) 
                DO UPDATE SET 
                    usage_count = school_feature_usage.usage_count + 1,
                    last_used_at = NOW()
            """, school_id, feature_name)
    except Exception as e:
        # Log error but don't fail the request
        import logging
        logging.error(f"Failed to track feature usage: {e}")
        pass