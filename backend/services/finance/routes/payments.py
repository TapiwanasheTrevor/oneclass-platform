# =====================================================
# Finance Payment Processing Routes
# File: backend/services/finance/routes/payments.py
# =====================================================

from fastapi import APIRouter, Depends, HTTPException, Query, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from shared.auth import get_current_active_user, EnhancedUser, require_permission, require_feature
from ..schemas import (
    PaymentCreate, PaymentUpdate, PaymentResponse,
    PaymentMethodCreate, PaymentMethodUpdate, PaymentMethodResponse,
    PaymentAllocationCreate, PaymentAllocationResponse,
    PaynowPaymentRequest, PaynowPaymentResponse, PaynowStatusResponse,
    PaymentSearchFilters, FinanceSearchRequest
)
from ..crud import PaymentCRUD
from ..paynow_integration import create_paynow_integration, validate_zimbabwe_phone, format_zimbabwe_phone

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["payments"])

# =====================================================
# PAYMENT METHODS MANAGEMENT
# =====================================================

@router.get("/methods", response_model=List[PaymentMethodResponse])
@require_permission("finance.read")
@require_feature("finance_module")
async def get_payment_methods(
    active_only: bool = Query(True, description="Return only active payment methods"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get all payment methods for the school.
    Automatically filtered by school context.
    """
    methods = await PaymentCRUD.get_payment_methods(current_user.school_id, active_only)
    return methods

@router.post("/methods", response_model=PaymentMethodResponse)
@require_permission("finance.create")
@require_feature("finance_module")
async def create_payment_method(
    method_data: PaymentMethodCreate,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Create a new payment method.
    Automatically sets school context.
    """
    method = await PaymentCRUD.create_payment_method(method_data, current_user)
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "payment_processing", "create_method")
    
    return method

@router.put("/methods/{method_id}", response_model=PaymentMethodResponse)
@require_permission("finance.update")
@require_feature("finance_module")
async def update_payment_method(
    method_id: UUID,
    method_data: PaymentMethodUpdate,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Update a payment method.
    Automatically validates school context.
    """
    # Verify method exists and belongs to school
    existing_method = await PaymentCRUD.get_payment_method_by_id(method_id, current_user.school_id)
    if not existing_method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    method = await PaymentCRUD.update_payment_method(method_id, method_data, current_user.school_id)
    return method

# =====================================================
# PAYMENT MANAGEMENT
# =====================================================

@router.get("/", response_model=Dict[str, Any])
@require_permission("finance.read")
@require_feature("finance_module")
async def get_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student_id: Optional[UUID] = Query(None, description="Filter by student ID"),
    payment_method_id: Optional[UUID] = Query(None, description="Filter by payment method"),
    status: Optional[str] = Query(None, description="Filter by status"),
    payment_date_from: Optional[str] = Query(None, description="Filter by payment date from"),
    payment_date_to: Optional[str] = Query(None, description="Filter by payment date to"),
    amount_min: Optional[float] = Query(None, ge=0, description="Filter by minimum amount"),
    amount_max: Optional[float] = Query(None, ge=0, description="Filter by maximum amount"),
    reconciled: Optional[bool] = Query(None, description="Filter by reconciliation status"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get payments list with pagination and filtering.
    Automatically filtered by school context.
    """
    # Build filters
    filters = PaymentSearchFilters(
        student_id=student_id,
        payment_method_id=payment_method_id,
        status=status,
        payment_date_from=payment_date_from,
        payment_date_to=payment_date_to,
        amount_min=amount_min,
        amount_max=amount_max,
        reconciled=reconciled
    )
    
    result = await PaymentCRUD.get_payments(current_user.school_id, filters, page, page_size)
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "payment_processing", "list_payments")
    
    return result

@router.get("/{payment_id}", response_model=PaymentResponse)
@require_permission("finance.read")
@require_feature("finance_module")
async def get_payment(
    payment_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get detailed payment information.
    Automatically validates school context.
    """
    payment = await PaymentCRUD.get_payment_by_id(payment_id, current_user.school_id)
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return payment

@router.post("/", response_model=PaymentResponse)
@require_permission("finance.create")
@require_feature("finance_module")
async def create_payment(
    payment_data: PaymentCreate,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Create a new payment record.
    Automatically sets school context.
    """
    payment = await PaymentCRUD.create_payment(payment_data, current_user)
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "payment_processing", "create_payment")
    
    return payment

@router.put("/{payment_id}", response_model=PaymentResponse)
@require_permission("finance.update")
@require_feature("finance_module")
async def update_payment(
    payment_id: UUID,
    payment_data: PaymentUpdate,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Update payment information.
    Automatically validates school context.
    """
    # Verify payment exists and belongs to school
    existing_payment = await PaymentCRUD.get_payment_by_id(payment_id, current_user.school_id)
    if not existing_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    payment = await PaymentCRUD.update_payment(payment_id, payment_data, current_user.school_id)
    return payment

# =====================================================
# PAYNOW INTEGRATION ENDPOINTS
# =====================================================

@router.post("/paynow/initiate", response_model=PaynowPaymentResponse)
@require_permission("finance.create")
@require_feature("finance_module")
async def initiate_paynow_payment(
    payment_request: PaynowPaymentRequest,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Initiate Paynow payment for invoices.
    Automatically validates school context and creates payment record.
    """
    # Validate phone number
    if not validate_zimbabwe_phone(payment_request.payer_phone):
        raise HTTPException(
            status_code=400,
            detail="Invalid Zimbabwe phone number format"
        )
    
    # Verify student belongs to school
    from ...sis.crud import StudentCRUD
    student = await StudentCRUD.get_student_by_id(payment_request.student_id, current_user.school_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Verify invoices exist and belong to school
    from ..crud import InvoiceCRUD
    total_amount = 0
    for invoice_id in payment_request.invoice_ids:
        invoice = await InvoiceCRUD.get_invoice_by_id(invoice_id, current_user.school_id)
        if not invoice:
            raise HTTPException(status_code=404, detail=f"Invoice {invoice_id} not found")
        if invoice.student_id != payment_request.student_id:
            raise HTTPException(status_code=400, detail="Invoice does not belong to specified student")
        total_amount += invoice.outstanding_amount
    
    # Validate amount
    if payment_request.amount != total_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Payment amount {payment_request.amount} does not match total outstanding {total_amount}"
        )
    
    # Create payment record
    payment_data = PaymentCreate(
        student_id=payment_request.student_id,
        payment_method_id=await PaymentCRUD.get_paynow_payment_method_id(current_user.school_id),
        amount=payment_request.amount,
        payer_name=f"{student.first_name} {student.last_name}",
        payer_email=payment_request.payer_email,
        payer_phone=format_zimbabwe_phone(payment_request.payer_phone),
        notes=f"Payment for {len(payment_request.invoice_ids)} invoice(s)"
    )
    
    payment = await PaymentCRUD.create_payment(payment_data, current_user)
    
    # Get school's Paynow configuration
    paynow_integration = create_paynow_integration(current_user.school_config.gateway_config)
    
    # Initiate payment with Paynow
    paynow_response = await paynow_integration.initiate_payment(
        payment_request, 
        payment.payment_reference
    )
    
    # Update payment with Paynow details
    await PaymentCRUD.update_payment(
        payment.id,
        PaymentUpdate(
            gateway_reference=paynow_response.poll_url,
            transaction_id=paynow_response.paynow_reference,
            status="processing"
        ),
        current_user.school_id
    )
    
    # Store invoice IDs for later allocation
    await PaymentCRUD.store_payment_invoice_mapping(payment.id, payment_request.invoice_ids)
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "payment_processing", "initiate_paynow")
    
    # Return response with payment ID
    paynow_response.payment_id = payment.id
    return paynow_response

@router.post("/paynow/mobile", response_model=PaynowPaymentResponse)
@require_permission("finance.create")
@require_feature("finance_module")
async def initiate_mobile_money_payment(
    payment_request: PaynowPaymentRequest,
    method: str = Query(..., description="Mobile money method: ecocash, onemoney"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Initiate mobile money payment (EcoCash, OneMoney).
    Automatically validates school context and creates payment record.
    """
    if method not in ['ecocash', 'onemoney']:
        raise HTTPException(
            status_code=400,
            detail="Invalid mobile money method. Use 'ecocash' or 'onemoney'"
        )
    
    # Validate phone number
    if not validate_zimbabwe_phone(payment_request.payer_phone):
        raise HTTPException(
            status_code=400,
            detail="Invalid Zimbabwe phone number format"
        )
    
    # Similar validation as above (student, invoices, amount)
    from ...sis.crud import StudentCRUD
    student = await StudentCRUD.get_student_by_id(payment_request.student_id, current_user.school_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Create payment record
    payment_data = PaymentCreate(
        student_id=payment_request.student_id,
        payment_method_id=await PaymentCRUD.get_mobile_money_payment_method_id(current_user.school_id, method),
        amount=payment_request.amount,
        payer_name=f"{student.first_name} {student.last_name}",
        payer_email=payment_request.payer_email,
        payer_phone=format_zimbabwe_phone(payment_request.payer_phone),
        notes=f"Mobile money payment ({method})"
    )
    
    payment = await PaymentCRUD.create_payment(payment_data, current_user)
    
    # Get school's Paynow configuration
    paynow_integration = create_paynow_integration(current_user.school_config.gateway_config)
    
    # Initiate mobile payment
    paynow_response = await paynow_integration.initiate_mobile_payment(
        payment_request, 
        payment.payment_reference,
        method
    )
    
    # Update payment with Paynow details
    await PaymentCRUD.update_payment(
        payment.id,
        PaymentUpdate(
            gateway_reference=paynow_response.poll_url,
            transaction_id=paynow_response.paynow_reference,
            status="processing"
        ),
        current_user.school_id
    )
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "payment_processing", f"initiate_{method}")
    
    paynow_response.payment_id = payment.id
    return paynow_response

@router.get("/paynow/status/{payment_id}", response_model=PaynowStatusResponse)
@require_permission("finance.read")
@require_feature("finance_module")
async def check_paynow_status(
    payment_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Check Paynow payment status.
    Automatically validates school context.
    """
    # Get payment
    payment = await PaymentCRUD.get_payment_by_id(payment_id, current_user.school_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if not payment.gateway_reference:
        raise HTTPException(status_code=400, detail="No gateway reference for status check")
    
    # Get school's Paynow configuration
    paynow_integration = create_paynow_integration(current_user.school_config.gateway_config)
    
    # Check status
    status_response = await paynow_integration.check_payment_status(payment.gateway_reference)
    
    # Update payment status if changed
    if str(status_response.status) != payment.status:
        await PaymentCRUD.update_payment(
            payment_id,
            PaymentUpdate(status=status_response.status),
            current_user.school_id
        )
        
        # If payment completed, allocate to invoices
        if status_response.status == "completed":
            await PaymentCRUD.auto_allocate_payment_to_invoices(payment_id)
    
    status_response.payment_id = payment_id
    return status_response

@router.post("/paynow/webhook")
async def paynow_webhook(request: Request):
    """
    Handle Paynow webhook notifications.
    Public endpoint for Paynow callbacks.
    """
    try:
        # Get webhook data
        webhook_data = await request.form()
        webhook_dict = dict(webhook_data)
        
        logger.info(f"Received Paynow webhook: {webhook_dict}")
        
        # Process webhook (school context will be determined from payment reference)
        result = await PaymentCRUD.process_paynow_webhook(webhook_dict)
        
        if result['success']:
            return JSONResponse(
                content={"status": "ok", "message": "Webhook processed successfully"},
                status_code=200
            )
        else:
            logger.error(f"Webhook processing failed: {result.get('error', 'Unknown error')}")
            return JSONResponse(
                content={"status": "error", "message": "Webhook processing failed"},
                status_code=400
            )
    
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return JSONResponse(
            content={"status": "error", "message": "Internal server error"},
            status_code=500
        )

# =====================================================
# PAYMENT ALLOCATION
# =====================================================

@router.post("/allocate", response_model=List[PaymentAllocationResponse])
@require_permission("finance.create")
@require_feature("finance_module")
async def allocate_payment_to_invoices(
    payment_id: UUID,
    invoice_ids: List[UUID],
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Allocate payment to specific invoices.
    Automatically validates school context.
    """
    # Verify payment exists and belongs to school
    payment = await PaymentCRUD.get_payment_by_id(payment_id, current_user.school_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.status != "completed":
        raise HTTPException(status_code=400, detail="Can only allocate completed payments")
    
    # Verify invoices exist and belong to school
    from ..crud import InvoiceCRUD
    for invoice_id in invoice_ids:
        invoice = await InvoiceCRUD.get_invoice_by_id(invoice_id, current_user.school_id)
        if not invoice:
            raise HTTPException(status_code=404, detail=f"Invoice {invoice_id} not found")
        if invoice.student_id != payment.student_id:
            raise HTTPException(status_code=400, detail="Invoice does not belong to payment student")
    
    # Allocate payment
    allocations = await PaymentCRUD.allocate_payment_to_invoices(payment_id, invoice_ids, current_user)
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "payment_processing", "allocate_payment")
    
    return allocations

@router.get("/{payment_id}/allocations", response_model=List[PaymentAllocationResponse])
@require_permission("finance.read")
@require_feature("finance_module")
async def get_payment_allocations(
    payment_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get payment allocations.
    Automatically validates school context.
    """
    # Verify payment exists and belongs to school
    payment = await PaymentCRUD.get_payment_by_id(payment_id, current_user.school_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    allocations = await PaymentCRUD.get_payment_allocations(payment_id)
    return allocations

# =====================================================
# PAYMENT RECONCILIATION
# =====================================================

@router.post("/{payment_id}/reconcile")
@require_permission("finance.reconcile")
@require_feature("finance_module")
async def reconcile_payment(
    payment_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Mark payment as reconciled.
    Automatically validates school context.
    """
    # Verify payment exists and belongs to school
    payment = await PaymentCRUD.get_payment_by_id(payment_id, current_user.school_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.reconciled:
        raise HTTPException(status_code=400, detail="Payment already reconciled")
    
    await PaymentCRUD.reconcile_payment(payment_id, current_user.id)
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "payment_processing", "reconcile_payment")
    
    return {"message": "Payment reconciled successfully"}

@router.post("/bulk-reconcile")
@require_permission("finance.reconcile")
@require_feature("finance_module")
async def bulk_reconcile_payments(
    payment_ids: List[UUID],
    background_tasks: BackgroundTasks,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Bulk reconcile multiple payments.
    Automatically validates school context.
    """
    # Verify all payments exist and belong to school
    for payment_id in payment_ids:
        payment = await PaymentCRUD.get_payment_by_id(payment_id, current_user.school_id)
        if not payment:
            raise HTTPException(status_code=404, detail=f"Payment {payment_id} not found")
    
    # Add to background task
    background_tasks.add_task(
        PaymentCRUD.bulk_reconcile_payments,
        payment_ids,
        current_user.id
    )
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "payment_processing", "bulk_reconcile")
    
    return {"message": f"Reconciling {len(payment_ids)} payments in background"}

# =====================================================
# PAYMENT ANALYTICS
# =====================================================

@router.get("/analytics/summary")
@require_permission("finance.read")
@require_feature("finance_module")
async def get_payment_analytics(
    period: str = Query("monthly", description="Period: daily, weekly, monthly, yearly"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get payment analytics summary.
    Automatically filtered by school context.
    """
    analytics = await PaymentCRUD.get_payment_analytics(current_user.school_id, period)
    return analytics

@router.get("/analytics/methods")
@require_permission("finance.read")
@require_feature("finance_module")
async def get_payment_methods_analytics(
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get payment methods usage analytics.
    Automatically filtered by school context.
    """
    analytics = await PaymentCRUD.get_payment_methods_analytics(current_user.school_id)
    return analytics

# =====================================================
# STUDENT-SPECIFIC ENDPOINTS
# =====================================================

@router.get("/student/{student_id}", response_model=List[PaymentResponse])
@require_permission("finance.read")
@require_feature("finance_module")
async def get_student_payments(
    student_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get all payments for a specific student.
    Automatically validates school context.
    """
    # Verify student belongs to school
    from ...sis.crud import StudentCRUD
    student = await StudentCRUD.get_student_by_id(student_id, current_user.school_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    payments = await PaymentCRUD.get_student_payments(student_id, current_user.school_id)
    return payments

@router.get("/student/{student_id}/history")
@require_permission("finance.read")
@require_feature("finance_module")
async def get_student_payment_history(
    student_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get detailed payment history for a student.
    Automatically validates school context.
    """
    # Verify student belongs to school
    from ...sis.crud import StudentCRUD
    student = await StudentCRUD.get_student_by_id(student_id, current_user.school_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    history = await PaymentCRUD.get_student_payment_history(student_id, current_user.school_id)
    return history

# =====================================================
# PARENT PORTAL ENDPOINTS
# =====================================================

@router.get("/parent/my-payments", response_model=List[PaymentResponse])
@require_permission("parent.read")
@require_feature("parent_portal")
async def get_parent_payments(
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get all payments for parent's children.
    Automatically filtered by parent's students.
    """
    # Get parent's children
    from ...sis.crud import StudentCRUD
    children = await StudentCRUD.get_parent_children(current_user.id, current_user.school_id)
    
    if not children:
        return []
    
    child_ids = [child.id for child in children]
    payments = await PaymentCRUD.get_multiple_students_payments(child_ids, current_user.school_id)
    
    return payments

@router.post("/parent/paynow/initiate", response_model=PaynowPaymentResponse)
@require_permission("parent.pay")
@require_feature("parent_portal")
async def parent_initiate_paynow_payment(
    payment_request: PaynowPaymentRequest,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Parent initiates Paynow payment for their child.
    Automatically validates parent-child relationship.
    """
    # Verify parent-child relationship
    from ...sis.crud import StudentCRUD
    is_parent = await StudentCRUD.verify_parent_child_relationship(
        current_user.id, 
        payment_request.student_id, 
        current_user.school_id
    )
    
    if not is_parent:
        raise HTTPException(status_code=403, detail="Not authorized to make payments for this student")
    
    # Use the same logic as admin payment initiation
    return await initiate_paynow_payment(payment_request, current_user)

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
        logger.error(f"Failed to track feature usage: {e}")
        pass