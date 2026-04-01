# =====================================================
# Finance Fee Management Routes
# File: backend/services/finance/routes/fee_management.py
# =====================================================

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from shared.auth import get_current_active_user, require_feature, EnhancedUser
from shared.models.platform_user import PlatformUser, PlatformRole
from shared.services.api_integration_service import require_permission
from ..schemas import (
    FeeCategoryCreate, FeeCategoryUpdate, FeeCategoryResponse,
    FeeStructureCreate, FeeStructureUpdate, FeeStructureResponse,
    FeeItemCreate, FeeItemUpdate, FeeItemResponse,
    StudentFeeAssignmentCreate, StudentFeeAssignmentUpdate, StudentFeeAssignmentResponse,
    FinanceSearchRequest
)
from ..crud import FeeCategoryCRUD, FeeStructureCRUD, FeeItemCRUD, StudentFeeAssignmentCRUD

router = APIRouter(prefix="/fee-management", tags=["fee-management"])

# =====================================================
# FEE CATEGORIES ENDPOINTS
# =====================================================

@router.get("/categories", response_model=List[FeeCategoryResponse])
@require_permission("finance.read")
async def get_fee_categories(
    active_only: bool = Query(True, description="Return only active categories"),
    current_user: PlatformUser = Depends(get_current_active_user)
):
    """
    Get all fee categories for the school.
    Automatically filtered by school context.
    """
    # Check if user has finance module access
    if not current_user.can_access_feature("finance_module"):
        raise HTTPException(status_code=403, detail="Finance module not available")
    
    school_id = current_user.primary_school_id
    if not school_id:
        raise HTTPException(status_code=400, detail="No school context available")
    
    categories = await FeeCategoryCRUD.get_fee_categories(school_id, active_only)
    return categories

@router.get("/categories/{category_id}", response_model=FeeCategoryResponse)
@require_permission("finance.read")
@require_feature("finance_module")
async def get_fee_category(
    category_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get a specific fee category by ID.
    Automatically validates school context.
    """
    category = await FeeCategoryCRUD.get_fee_category_by_id(category_id, current_user.school_id)
    
    if not category:
        raise HTTPException(status_code=404, detail="Fee category not found")
    
    return category

@router.post("/categories", response_model=FeeCategoryResponse)
@require_permission("finance.create")
@require_feature("finance_module")
async def create_fee_category(
    category_data: FeeCategoryCreate,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Create a new fee category.
    Automatically sets school context.
    """
    category = await FeeCategoryCRUD.create_fee_category(category_data, current_user)
    return category

@router.put("/categories/{category_id}", response_model=FeeCategoryResponse)
@require_permission("finance.update")
@require_feature("finance_module")
async def update_fee_category(
    category_id: UUID,
    category_data: FeeCategoryUpdate,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Update a fee category.
    Automatically validates school context.
    """
    # Verify category exists and belongs to school
    existing_category = await FeeCategoryCRUD.get_fee_category_by_id(category_id, current_user.school_id)
    if not existing_category:
        raise HTTPException(status_code=404, detail="Fee category not found")
    
    category = await FeeCategoryCRUD.update_fee_category(category_id, category_data, current_user.school_id)
    return category

@router.delete("/categories/{category_id}")
@require_permission("finance.delete")
@require_feature("finance_module")
async def delete_fee_category(
    category_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Delete (deactivate) a fee category.
    Automatically validates school context.
    """
    # Verify category exists and belongs to school
    existing_category = await FeeCategoryCRUD.get_fee_category_by_id(category_id, current_user.school_id)
    if not existing_category:
        raise HTTPException(status_code=404, detail="Fee category not found")
    
    await FeeCategoryCRUD.delete_fee_category(category_id, current_user.school_id)
    return {"message": "Fee category deleted successfully"}

# =====================================================
# FEE STRUCTURES ENDPOINTS
# =====================================================

@router.get("/structures", response_model=List[FeeStructureResponse])
@require_permission("finance.read")
@require_feature("finance_module")
async def get_fee_structures(
    academic_year_id: Optional[UUID] = Query(None, description="Filter by academic year"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get all fee structures for the school.
    Automatically filtered by school context.
    """
    structures = await FeeStructureCRUD.get_fee_structures(current_user.school_id, academic_year_id, status)
    return structures

@router.get("/structures/{structure_id}", response_model=FeeStructureResponse)
@require_permission("finance.read")
@require_feature("finance_module")
async def get_fee_structure(
    structure_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get a specific fee structure by ID.
    Automatically validates school context.
    """
    structure = await FeeStructureCRUD.get_fee_structure_by_id(structure_id, current_user.school_id)
    
    if not structure:
        raise HTTPException(status_code=404, detail="Fee structure not found")
    
    return structure

@router.get("/structures/{structure_id}/details")
@require_permission("finance.read")
@require_feature("finance_module")
async def get_fee_structure_details(
    structure_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get fee structure with all its items and calculated totals.
    Automatically validates school context.
    """
    details = await FeeStructureCRUD.get_fee_structure_with_items(structure_id, current_user.school_id)
    
    if not details:
        raise HTTPException(status_code=404, detail="Fee structure not found")
    
    return details

@router.post("/structures", response_model=FeeStructureResponse)
@require_permission("finance.create")
@require_feature("finance_module")
async def create_fee_structure(
    structure_data: FeeStructureCreate,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Create a new fee structure.
    Automatically sets school context.
    """
    structure = await FeeStructureCRUD.create_fee_structure(structure_data, current_user)
    return structure

@router.put("/structures/{structure_id}", response_model=FeeStructureResponse)
@require_permission("finance.update")
@require_feature("finance_module")
async def update_fee_structure(
    structure_id: UUID,
    structure_data: FeeStructureUpdate,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Update a fee structure.
    Automatically validates school context.
    """
    # Verify structure exists and belongs to school
    existing_structure = await FeeStructureCRUD.get_fee_structure_by_id(structure_id, current_user.school_id)
    if not existing_structure:
        raise HTTPException(status_code=404, detail="Fee structure not found")

    structure = await FeeStructureCRUD.update_fee_structure(structure_id, structure_data, current_user.school_id)
    return structure

@router.delete("/structures/{structure_id}")
@require_permission("finance.delete")
@require_feature("finance_module")
async def delete_fee_structure(
    structure_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Delete (archive) a fee structure.
    Automatically validates school context.
    """
    # Verify structure exists and belongs to school
    existing_structure = await FeeStructureCRUD.get_fee_structure_by_id(structure_id, current_user.school_id)
    if not existing_structure:
        raise HTTPException(status_code=404, detail="Fee structure not found")

    await FeeStructureCRUD.delete_fee_structure(structure_id, current_user.school_id)
    return {"message": "Fee structure archived successfully"}

# =====================================================
# FEE ITEMS ENDPOINTS
# =====================================================

@router.get("/structures/{structure_id}/items", response_model=List[FeeItemResponse])
@require_permission("finance.read")
@require_feature("finance_module")
async def get_fee_items(
    structure_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get all fee items for a specific structure.
    Automatically validates school context.
    """
    # Verify structure exists and belongs to school
    existing_structure = await FeeStructureCRUD.get_fee_structure_by_id(structure_id, current_user.school_id)
    if not existing_structure:
        raise HTTPException(status_code=404, detail="Fee structure not found")

    items = await FeeItemCRUD.get_fee_items(structure_id, current_user.school_id)
    return items

@router.post("/structures/{structure_id}/items", response_model=FeeItemResponse)
@require_permission("finance.create")
@require_feature("finance_module")
async def create_fee_item(
    structure_id: UUID,
    item_data: FeeItemCreate,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Create a new fee item within a structure.
    Automatically validates school context.
    """
    # Verify structure exists and belongs to school
    existing_structure = await FeeStructureCRUD.get_fee_structure_by_id(structure_id, current_user.school_id)
    if not existing_structure:
        raise HTTPException(status_code=404, detail="Fee structure not found")

    item = await FeeItemCRUD.create_fee_item(structure_id, item_data, current_user)
    return item

@router.put("/items/{item_id}", response_model=FeeItemResponse)
@require_permission("finance.update")
@require_feature("finance_module")
async def update_fee_item(
    item_id: UUID,
    item_data: FeeItemUpdate,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Update a fee item.
    Automatically validates school context.
    """
    item = await FeeItemCRUD.update_fee_item(item_id, item_data, current_user.school_id)
    return item

@router.delete("/items/{item_id}")
@require_permission("finance.delete")
@require_feature("finance_module")
async def delete_fee_item(
    item_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Delete a fee item.
    Automatically validates school context.
    """
    await FeeItemCRUD.delete_fee_item(item_id, current_user.school_id)
    return {"message": "Fee item deleted successfully"}

# =====================================================
# STUDENT FEE ASSIGNMENTS ENDPOINTS
# =====================================================

@router.get("/assignments/student/{student_id}", response_model=List[StudentFeeAssignmentResponse])
@require_permission("finance.read")
@require_feature("finance_module")
async def get_student_fee_assignments(
    student_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get all fee assignments for a specific student.
    Automatically validates school context.
    """
    assignments = await StudentFeeAssignmentCRUD.get_student_assignments(student_id, current_user.school_id)
    return assignments

@router.post("/assignments", response_model=StudentFeeAssignmentResponse)
@require_permission("finance.create")
@require_feature("finance_module")
async def create_student_fee_assignment(
    assignment_data: StudentFeeAssignmentCreate,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Assign a fee structure to a student.
    Automatically validates school context.
    """
    assignment = await StudentFeeAssignmentCRUD.create_assignment(assignment_data, current_user)
    return assignment

@router.put("/assignments/{assignment_id}", response_model=StudentFeeAssignmentResponse)
@require_permission("finance.update")
@require_feature("finance_module")
async def update_student_fee_assignment(
    assignment_id: UUID,
    assignment_data: StudentFeeAssignmentUpdate,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Update a student fee assignment.
    Automatically validates school context.
    """
    assignment = await StudentFeeAssignmentCRUD.update_assignment(assignment_id, assignment_data, current_user.school_id)
    return assignment

@router.delete("/assignments/{assignment_id}")
@require_permission("finance.delete")
@require_feature("finance_module")
async def delete_student_fee_assignment(
    assignment_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Remove a student fee assignment.
    Automatically validates school context.
    """
    await StudentFeeAssignmentCRUD.delete_assignment(assignment_id, current_user.school_id)
    return {"message": "Student fee assignment cancelled successfully"}

# =====================================================
# BULK OPERATIONS ENDPOINTS
# =====================================================

@router.post("/assignments/bulk-assign")
@require_permission("finance.create")
@require_feature("finance_module")
async def bulk_assign_fee_structure(
    fee_structure_id: UUID,
    student_ids: List[UUID],
    background_tasks: BackgroundTasks,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Bulk assign fee structure to multiple students.
    Automatically validates school context.
    """
    # Verify structure exists and belongs to school
    existing_structure = await FeeStructureCRUD.get_fee_structure_by_id(fee_structure_id, current_user.school_id)
    if not existing_structure:
        raise HTTPException(status_code=404, detail="Fee structure not found")

    result = await StudentFeeAssignmentCRUD.bulk_assign(fee_structure_id, student_ids, current_user)
    return result

@router.post("/assignments/bulk-assign-by-grade")
@require_permission("finance.create")
@require_feature("finance_module")
async def bulk_assign_fee_structure_by_grade(
    fee_structure_id: UUID,
    grade_levels: List[int],
    background_tasks: BackgroundTasks,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Bulk assign fee structure to students by grade level.
    Automatically validates school context.
    """
    # Verify structure exists and belongs to school
    existing_structure = await FeeStructureCRUD.get_fee_structure_by_id(fee_structure_id, current_user.school_id)
    if not existing_structure:
        raise HTTPException(status_code=404, detail="Fee structure not found")

    result = await StudentFeeAssignmentCRUD.bulk_assign_by_grade(fee_structure_id, grade_levels, current_user)
    return result

# =====================================================
# APPROVAL ENDPOINTS
# =====================================================

@router.post("/structures/{structure_id}/approve")
@require_permission("finance.approve")
@require_feature("finance_module")
async def approve_fee_structure(
    structure_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Approve a fee structure for use.
    Automatically validates school context.
    """
    # Verify structure exists and belongs to school
    existing_structure = await FeeStructureCRUD.get_fee_structure_by_id(structure_id, current_user.school_id)
    if not existing_structure:
        raise HTTPException(status_code=404, detail="Fee structure not found")

    structure = await FeeStructureCRUD.approve_fee_structure(structure_id, current_user.school_id, current_user.id)
    return {"message": "Fee structure approved successfully", "structure": structure}

@router.post("/structures/{structure_id}/reject")
@require_permission("finance.approve")
@require_feature("finance_module")
async def reject_fee_structure(
    structure_id: UUID,
    rejection_reason: str,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Reject a fee structure.
    Automatically validates school context.
    """
    # Verify structure exists and belongs to school
    existing_structure = await FeeStructureCRUD.get_fee_structure_by_id(structure_id, current_user.school_id)
    if not existing_structure:
        raise HTTPException(status_code=404, detail="Fee structure not found")

    structure = await FeeStructureCRUD.reject_fee_structure(structure_id, current_user.school_id, current_user.id, rejection_reason)
    return {"message": "Fee structure rejected", "structure": structure}

# =====================================================
# UTILITY ENDPOINTS
# =====================================================

@router.get("/templates/fee-structure")
@require_permission("finance.read")
@require_feature("finance_module")
async def get_fee_structure_templates(
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get fee structure templates for quick setup.
    """
    templates = [
        {
            "id": "zw-primary",
            "name": "Zimbabwe Primary School (Grade 1-7)",
            "description": "Standard fee structure for Zimbabwe primary schools",
            "grade_levels": list(range(1, 8)),
            "items": [
                {"name": "Tuition Fee", "fee_type": "tuition", "amount": 150.00, "frequency": "term", "is_mandatory": True},
                {"name": "Registration Fee", "fee_type": "registration", "amount": 25.00, "frequency": "one_time", "is_mandatory": True},
                {"name": "Sports Levy", "fee_type": "sports", "amount": 15.00, "frequency": "term", "is_mandatory": True},
                {"name": "Stationery", "fee_type": "books", "amount": 20.00, "frequency": "term", "is_mandatory": True},
                {"name": "Computer Levy", "fee_type": "technology", "amount": 10.00, "frequency": "term", "is_mandatory": False},
            ]
        },
        {
            "id": "zw-secondary-olevel",
            "name": "Zimbabwe Secondary O-Level (Form 1-4)",
            "description": "Standard fee structure for Zimbabwe secondary O-Level",
            "grade_levels": list(range(8, 12)),
            "items": [
                {"name": "Tuition Fee", "fee_type": "tuition", "amount": 250.00, "frequency": "term", "is_mandatory": True},
                {"name": "Registration Fee", "fee_type": "registration", "amount": 35.00, "frequency": "one_time", "is_mandatory": True},
                {"name": "Laboratory Fee", "fee_type": "technology", "amount": 20.00, "frequency": "term", "is_mandatory": True},
                {"name": "Sports Levy", "fee_type": "sports", "amount": 20.00, "frequency": "term", "is_mandatory": True},
                {"name": "Library Fee", "fee_type": "library", "amount": 10.00, "frequency": "term", "is_mandatory": True},
                {"name": "Examination Fee", "fee_type": "examination", "amount": 30.00, "frequency": "annual", "is_mandatory": True},
            ]
        },
        {
            "id": "zw-secondary-alevel",
            "name": "Zimbabwe Secondary A-Level (Form 5-6)",
            "description": "Standard fee structure for Zimbabwe secondary A-Level",
            "grade_levels": [12, 13],
            "items": [
                {"name": "Tuition Fee", "fee_type": "tuition", "amount": 350.00, "frequency": "term", "is_mandatory": True},
                {"name": "Registration Fee", "fee_type": "registration", "amount": 40.00, "frequency": "one_time", "is_mandatory": True},
                {"name": "Laboratory Fee", "fee_type": "technology", "amount": 30.00, "frequency": "term", "is_mandatory": True},
                {"name": "Sports Levy", "fee_type": "sports", "amount": 20.00, "frequency": "term", "is_mandatory": True},
                {"name": "Library Fee", "fee_type": "library", "amount": 15.00, "frequency": "term", "is_mandatory": True},
                {"name": "ZIMSEC Exam Fee", "fee_type": "examination", "amount": 50.00, "frequency": "annual", "is_mandatory": True},
            ]
        },
        {
            "id": "zw-boarding",
            "name": "Boarding School Add-on",
            "description": "Additional fees for boarding students",
            "grade_levels": list(range(1, 14)),
            "items": [
                {"name": "Boarding Fee", "fee_type": "tuition", "amount": 400.00, "frequency": "term", "is_mandatory": True},
                {"name": "Meals", "fee_type": "meals", "amount": 200.00, "frequency": "term", "is_mandatory": True},
                {"name": "Laundry", "fee_type": "other", "amount": 30.00, "frequency": "term", "is_mandatory": False},
            ]
        }
    ]
    return templates

@router.post("/templates/fee-structure")
@require_permission("finance.create")
@require_feature("finance_module")
async def create_fee_structure_template(
    template_data: dict,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Create a fee structure template for reuse.
    """
    # Create fee structure from template data
    if "name" not in template_data or "items" not in template_data:
        raise HTTPException(status_code=400, detail="Template must include 'name' and 'items'")

    return {"message": "Use POST /fee-management/structures to create a fee structure, then add items via POST /fee-management/structures/{id}/items"}

# Helper function to track feature usage
async def track_feature_usage(school_id: UUID, feature_name: str, action: str):
    """Track feature usage for analytics"""
    try:
        from shared.database import get_database_connection
        
        async with get_database_connection() as conn:
            await conn.execute(
                """
                INSERT INTO platform.school_feature_usage (school_id, feature_name, usage_count, last_used_at)
                VALUES ($1, $2, 1, NOW())
                ON CONFLICT (school_id, feature_name) 
                DO UPDATE SET 
                    usage_count = school_feature_usage.usage_count + 1,
                    last_used_at = NOW()
                """, 
                school_id, f"{feature_name}.{action}"
            )
    except Exception as e:
        # Log error but don't fail the request
        import logging
        logging.error(f"Failed to track feature usage: {e}")
        pass