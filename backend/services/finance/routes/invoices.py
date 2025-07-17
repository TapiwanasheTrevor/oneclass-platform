# =====================================================
# Finance Invoice Management Routes
# File: backend/services/finance/routes/invoices.py
# =====================================================

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from shared.auth import get_current_active_user, EnhancedUser, require_permission, require_feature
from ..schemas import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse,
    BulkInvoiceGenerationRequest, BulkInvoiceGenerationResponse,
    InvoiceSearchFilters, FinanceSearchRequest
)
from ..crud import InvoiceCRUD

router = APIRouter(prefix="/invoices", tags=["invoices"])

# =====================================================
# INVOICE MANAGEMENT ENDPOINTS
# =====================================================

@router.get("/", response_model=Dict[str, Any])
@require_permission("finance.read")
@require_feature("finance_module")
async def get_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student_id: Optional[UUID] = Query(None, description="Filter by student ID"),
    grade_level: Optional[int] = Query(None, ge=1, le=13, description="Filter by grade level"),
    class_id: Optional[UUID] = Query(None, description="Filter by class ID"),
    payment_status: Optional[str] = Query(None, description="Filter by payment status"),
    academic_year_id: Optional[UUID] = Query(None, description="Filter by academic year"),
    term_id: Optional[UUID] = Query(None, description="Filter by term"),
    due_date_from: Optional[str] = Query(None, description="Filter by due date from (YYYY-MM-DD)"),
    due_date_to: Optional[str] = Query(None, description="Filter by due date to (YYYY-MM-DD)"),
    amount_min: Optional[float] = Query(None, ge=0, description="Filter by minimum amount"),
    amount_max: Optional[float] = Query(None, ge=0, description="Filter by maximum amount"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get invoices list with pagination and filtering.
    Automatically filtered by school context.
    """
    # Build filters
    filters = InvoiceSearchFilters(
        student_id=student_id,
        grade_level=grade_level,
        class_id=class_id,
        payment_status=payment_status,
        academic_year_id=academic_year_id,
        term_id=term_id,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        amount_min=amount_min,
        amount_max=amount_max
    )
    
    result = await InvoiceCRUD.get_invoices(current_user.school_id, filters, page, page_size)
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "invoice_management", "list_invoices")
    
    return result

@router.get("/{invoice_id}", response_model=InvoiceResponse)
@require_permission("finance.read")
@require_feature("finance_module")
async def get_invoice(
    invoice_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get detailed invoice information.
    Automatically validates school context.
    """
    invoice = await InvoiceCRUD.get_invoice_by_id(invoice_id, current_user.school_id)
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return invoice

@router.post("/", response_model=InvoiceResponse)
@require_permission("finance.create")
@require_feature("finance_module")
async def create_invoice(
    invoice_data: InvoiceCreate,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Create a new invoice.
    Automatically sets school context and validates limits.
    """
    # Check subscription limits
    current_count = await InvoiceCRUD.get_invoice_count(current_user.school_id)
    if current_count >= current_user.school_config.max_invoices_per_month:
        raise HTTPException(
            status_code=400,
            detail=f"Monthly invoice limit reached. Maximum {current_user.school_config.max_invoices_per_month} invoices allowed."
        )
    
    invoice = await InvoiceCRUD.create_invoice(invoice_data, current_user)
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "invoice_management", "create_invoice")
    
    return invoice

@router.put("/{invoice_id}", response_model=InvoiceResponse)
@require_permission("finance.update")
@require_feature("finance_module")
async def update_invoice(
    invoice_id: UUID,
    invoice_data: InvoiceUpdate,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Update invoice information.
    Automatically validates school context.
    """
    # Verify invoice belongs to current school
    existing_invoice = await InvoiceCRUD.get_invoice_by_id(invoice_id, current_user.school_id)
    if not existing_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check if invoice can be updated (not paid/cancelled)
    if existing_invoice.status in ['paid', 'cancelled']:
        raise HTTPException(status_code=400, detail="Cannot update paid or cancelled invoice")
    
    invoice = await InvoiceCRUD.update_invoice(invoice_id, invoice_data, current_user.school_id)
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "invoice_management", "update_invoice")
    
    return invoice

@router.delete("/{invoice_id}")
@require_permission("finance.delete")
@require_feature("finance_module")
async def cancel_invoice(
    invoice_id: UUID,
    cancellation_reason: str = Query(..., description="Reason for cancellation"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Cancel an invoice.
    Automatically validates school context.
    """
    # Verify invoice belongs to current school
    existing_invoice = await InvoiceCRUD.get_invoice_by_id(invoice_id, current_user.school_id)
    if not existing_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check if invoice can be cancelled
    if existing_invoice.status == 'paid':
        raise HTTPException(status_code=400, detail="Cannot cancel paid invoice")
    
    await InvoiceCRUD.cancel_invoice(invoice_id, cancellation_reason, current_user.id)
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "invoice_management", "cancel_invoice")
    
    return {"message": "Invoice cancelled successfully"}

# =====================================================
# BULK INVOICE OPERATIONS
# =====================================================

@router.post("/bulk-generate", response_model=BulkInvoiceGenerationResponse)
@require_permission("finance.create")
@require_feature("finance_module")
async def bulk_generate_invoices(
    request: BulkInvoiceGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Generate invoices in bulk.
    Automatically validates school context and limits.
    """
    # Check subscription limits
    current_count = await InvoiceCRUD.get_invoice_count(current_user.school_id)
    estimated_new_invoices = await InvoiceCRUD.estimate_bulk_invoice_count(request, current_user.school_id)
    
    if current_count + estimated_new_invoices > current_user.school_config.max_invoices_per_month:
        raise HTTPException(
            status_code=400,
            detail=f"Would exceed monthly invoice limit. Current: {current_count}, Estimated new: {estimated_new_invoices}, Limit: {current_user.school_config.max_invoices_per_month}"
        )
    
    # Generate invoices
    result = await InvoiceCRUD.bulk_generate_invoices(request, current_user)
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "invoice_management", "bulk_generate")
    
    return result

@router.post("/bulk-send")
@require_permission("finance.send")
@require_feature("finance_module")
async def bulk_send_invoices(
    invoice_ids: List[UUID],
    background_tasks: BackgroundTasks,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Send multiple invoices to parents.
    Automatically validates school context.
    """
    # Verify all invoices belong to current school
    for invoice_id in invoice_ids:
        existing_invoice = await InvoiceCRUD.get_invoice_by_id(invoice_id, current_user.school_id)
        if not existing_invoice:
            raise HTTPException(status_code=404, detail=f"Invoice {invoice_id} not found")
    
    # Add to background task
    background_tasks.add_task(
        InvoiceCRUD.bulk_send_invoices,
        invoice_ids,
        current_user.school_id,
        current_user.id
    )
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "invoice_management", "bulk_send")
    
    return {"message": f"Sending {len(invoice_ids)} invoices in background"}

@router.post("/bulk-reminder")
@require_permission("finance.send")
@require_feature("finance_module")
async def bulk_send_reminders(
    invoice_ids: List[UUID],
    reminder_message: Optional[str] = None,
    background_tasks: BackgroundTasks,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Send payment reminders for multiple invoices.
    Automatically validates school context.
    """
    # Verify all invoices belong to current school and are overdue
    for invoice_id in invoice_ids:
        existing_invoice = await InvoiceCRUD.get_invoice_by_id(invoice_id, current_user.school_id)
        if not existing_invoice:
            raise HTTPException(status_code=404, detail=f"Invoice {invoice_id} not found")
        if existing_invoice.payment_status not in ['pending', 'partial', 'overdue']:
            raise HTTPException(status_code=400, detail=f"Invoice {invoice_id} does not need reminder")
    
    # Add to background task
    background_tasks.add_task(
        InvoiceCRUD.bulk_send_reminders,
        invoice_ids,
        reminder_message,
        current_user.school_id,
        current_user.id
    )
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "invoice_management", "bulk_reminder")
    
    return {"message": f"Sending reminders for {len(invoice_ids)} invoices in background"}

# =====================================================
# INVOICE STATUS OPERATIONS
# =====================================================

@router.post("/{invoice_id}/send")
@require_permission("finance.send")
@require_feature("finance_module")
async def send_invoice(
    invoice_id: UUID,
    send_sms: bool = Query(False, description="Also send SMS notification"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Send invoice to parent/guardian.
    Automatically validates school context.
    """
    # Verify invoice belongs to current school
    existing_invoice = await InvoiceCRUD.get_invoice_by_id(invoice_id, current_user.school_id)
    if not existing_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if existing_invoice.status != 'draft':
        raise HTTPException(status_code=400, detail="Only draft invoices can be sent")
    
    await InvoiceCRUD.send_invoice(invoice_id, send_sms, current_user.id)
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "invoice_management", "send_invoice")
    
    return {"message": "Invoice sent successfully"}

@router.post("/{invoice_id}/reminder")
@require_permission("finance.send")
@require_feature("finance_module")
async def send_payment_reminder(
    invoice_id: UUID,
    reminder_message: Optional[str] = None,
    send_sms: bool = Query(False, description="Also send SMS reminder"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Send payment reminder for invoice.
    Automatically validates school context.
    """
    # Verify invoice belongs to current school
    existing_invoice = await InvoiceCRUD.get_invoice_by_id(invoice_id, current_user.school_id)
    if not existing_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if existing_invoice.payment_status not in ['pending', 'partial', 'overdue']:
        raise HTTPException(status_code=400, detail="Invoice does not need reminder")
    
    await InvoiceCRUD.send_payment_reminder(invoice_id, reminder_message, send_sms, current_user.id)
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "invoice_management", "send_reminder")
    
    return {"message": "Payment reminder sent successfully"}

# =====================================================
# INVOICE REPORTS AND EXPORTS
# =====================================================

@router.get("/{invoice_id}/pdf")
@require_permission("finance.read")
@require_feature("finance_module")
async def generate_invoice_pdf(
    invoice_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Generate PDF version of invoice.
    Automatically validates school context.
    """
    # Verify invoice belongs to current school
    existing_invoice = await InvoiceCRUD.get_invoice_by_id(invoice_id, current_user.school_id)
    if not existing_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # TODO: Implement PDF generation
    raise HTTPException(status_code=501, detail="PDF generation not implemented yet")

@router.get("/{invoice_id}/statement")
@require_permission("finance.read")
@require_feature("finance_module")
async def generate_statement(
    invoice_id: UUID,
    include_payment_history: bool = Query(True, description="Include payment history"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Generate student statement including this invoice.
    Automatically validates school context.
    """
    # Verify invoice belongs to current school
    existing_invoice = await InvoiceCRUD.get_invoice_by_id(invoice_id, current_user.school_id)
    if not existing_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # TODO: Implement statement generation
    raise HTTPException(status_code=501, detail="Statement generation not implemented yet")

# =====================================================
# INVOICE ANALYTICS
# =====================================================

@router.get("/analytics/summary")
@require_permission("finance.read")
@require_feature("finance_module")
async def get_invoice_analytics(
    academic_year_id: Optional[UUID] = Query(None, description="Filter by academic year"),
    term_id: Optional[UUID] = Query(None, description="Filter by term"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get invoice analytics summary.
    Automatically filtered by school context.
    """
    analytics = await InvoiceCRUD.get_invoice_analytics(
        current_user.school_id,
        academic_year_id,
        term_id
    )
    
    return analytics

@router.get("/analytics/overdue")
@require_permission("finance.read")
@require_feature("finance_module")
async def get_overdue_invoices_analytics(
    days_overdue: int = Query(7, ge=1, description="Minimum days overdue"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get overdue invoices analytics.
    Automatically filtered by school context.
    """
    analytics = await InvoiceCRUD.get_overdue_analytics(
        current_user.school_id,
        days_overdue
    )
    
    return analytics

# =====================================================
# STUDENT-SPECIFIC ENDPOINTS
# =====================================================

@router.get("/student/{student_id}", response_model=List[InvoiceResponse])
@require_permission("finance.read")
@require_feature("finance_module")
async def get_student_invoices(
    student_id: UUID,
    academic_year_id: Optional[UUID] = Query(None, description="Filter by academic year"),
    payment_status: Optional[str] = Query(None, description="Filter by payment status"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get all invoices for a specific student.
    Automatically validates school context.
    """
    # Verify student belongs to current school
    from ...sis.crud import StudentCRUD
    student = await StudentCRUD.get_student_by_id(student_id, current_user.school_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    invoices = await InvoiceCRUD.get_student_invoices(
        student_id,
        current_user.school_id,
        academic_year_id,
        payment_status
    )
    
    return invoices

@router.get("/student/{student_id}/balance")
@require_permission("finance.read")
@require_feature("finance_module")
async def get_student_balance(
    student_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get student's current balance summary.
    Automatically validates school context.
    """
    # Verify student belongs to current school
    from ...sis.crud import StudentCRUD
    student = await StudentCRUD.get_student_by_id(student_id, current_user.school_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    balance = await InvoiceCRUD.get_student_balance(student_id, current_user.school_id)
    
    return balance

# =====================================================
# PARENT PORTAL ENDPOINTS
# =====================================================

@router.get("/parent/my-invoices", response_model=List[InvoiceResponse])
@require_permission("parent.read")
@require_feature("parent_portal")
async def get_parent_invoices(
    academic_year_id: Optional[UUID] = Query(None, description="Filter by academic year"),
    payment_status: Optional[str] = Query(None, description="Filter by payment status"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get all invoices for parent's children.
    Automatically filtered by parent's students.
    """
    # Get parent's children
    from ...sis.crud import StudentCRUD
    children = await StudentCRUD.get_parent_children(current_user.id, current_user.school_id)
    
    if not children:
        return []
    
    child_ids = [child.id for child in children]
    invoices = await InvoiceCRUD.get_multiple_students_invoices(
        child_ids,
        current_user.school_id,
        academic_year_id,
        payment_status
    )
    
    return invoices

@router.get("/parent/balance-summary")
@require_permission("parent.read")
@require_feature("parent_portal")
async def get_parent_balance_summary(
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get balance summary for all parent's children.
    Automatically filtered by parent's students.
    """
    # Get parent's children
    from ...sis.crud import StudentCRUD
    children = await StudentCRUD.get_parent_children(current_user.id, current_user.school_id)
    
    if not children:
        return {"total_outstanding": 0, "total_overdue": 0, "children_balances": []}
    
    child_ids = [child.id for child in children]
    summary = await InvoiceCRUD.get_multiple_students_balance_summary(
        child_ids,
        current_user.school_id
    )
    
    return summary

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