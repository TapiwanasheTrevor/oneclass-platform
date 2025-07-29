# =====================================================
# Finance Fee Management Routes
# File: backend/services/finance/routes/fee_management.py
# =====================================================

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from shared.auth import get_current_active_user
from shared.models.platform_user import PlatformUser, PlatformRole
from shared.services.api_integration_service import require_permission
from ..schemas import (
    FeeCategoryCreate, FeeCategoryUpdate, FeeCategoryResponse,
    FeeStructureCreate, FeeStructureUpdate, FeeStructureResponse,
    FeeItemCreate, FeeItemUpdate, FeeItemResponse,
    StudentFeeAssignmentCreate, StudentFeeAssignmentUpdate, StudentFeeAssignmentResponse,
    FinanceSearchRequest
)
from ..crud import FeeCategoryCRUD, FeeStructureCRUD

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
    
    # TODO: Implement update logic
    raise HTTPException(status_code=501, detail="Fee structure update not implemented yet")

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
    
    # TODO: Implement delete logic (should archive, not delete)
    raise HTTPException(status_code=501, detail="Fee structure deletion not implemented yet")

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
    
    # TODO: Implement fee items retrieval
    raise HTTPException(status_code=501, detail="Fee items retrieval not implemented yet")

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
    
    # TODO: Implement fee item creation
    raise HTTPException(status_code=501, detail="Fee item creation not implemented yet")

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
    # TODO: Implement fee item update
    raise HTTPException(status_code=501, detail="Fee item update not implemented yet")

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
    # TODO: Implement fee item deletion
    raise HTTPException(status_code=501, detail="Fee item deletion not implemented yet")

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
    # TODO: Implement student fee assignments retrieval
    raise HTTPException(status_code=501, detail="Student fee assignments retrieval not implemented yet")

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
    # TODO: Implement student fee assignment creation
    raise HTTPException(status_code=501, detail="Student fee assignment creation not implemented yet")

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
    # TODO: Implement student fee assignment update
    raise HTTPException(status_code=501, detail="Student fee assignment update not implemented yet")

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
    # TODO: Implement student fee assignment deletion
    raise HTTPException(status_code=501, detail="Student fee assignment deletion not implemented yet")

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
    
    # TODO: Implement bulk assignment logic
    raise HTTPException(status_code=501, detail="Bulk fee assignment not implemented yet")

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
    
    # TODO: Implement bulk assignment by grade logic
    raise HTTPException(status_code=501, detail="Bulk fee assignment by grade not implemented yet")

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
    
    # TODO: Implement approval logic
    raise HTTPException(status_code=501, detail="Fee structure approval not implemented yet")

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
    
    # TODO: Implement rejection logic
    raise HTTPException(status_code=501, detail="Fee structure rejection not implemented yet")

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
    # TODO: Implement template retrieval
    raise HTTPException(status_code=501, detail="Fee structure templates not implemented yet")

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
    # TODO: Implement template creation
    raise HTTPException(status_code=501, detail="Fee structure template creation not implemented yet")

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