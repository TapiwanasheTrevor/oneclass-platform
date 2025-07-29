# =====================================================
# SIS Students Routes with Multitenancy Support
# File: backend/services/sis/routes/students.py
# =====================================================

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from shared.auth import get_current_active_user, require_permission, require_feature
from shared.models.platform_user import PlatformUser as EnhancedUser
from shared.file_storage import upload_student_document, upload_student_photo
from ..schemas import (
    StudentCreate, StudentUpdate, StudentResponse, StudentListResponse,
    StudentDetailResponse, StudentSearchParams
)
from ..crud import StudentCRUD

router = APIRouter(prefix="/students", tags=["students"])

@router.get("/", response_model=StudentListResponse)
@require_permission("students.read")
@require_feature("student_management")
async def get_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    grade_level: Optional[int] = None,
    class_id: Optional[UUID] = None,
    status: Optional[str] = None,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get students list with pagination and filtering.
    Automatically filtered by school context.
    """
    search_params = StudentSearchParams(
        school_id=current_user.school_id,
        search=search,
        grade_level=grade_level,
        class_id=class_id,
        status=status,
        page=page,
        page_size=page_size
    )
    
    students = await StudentCRUD.get_students(search_params)
    return students

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