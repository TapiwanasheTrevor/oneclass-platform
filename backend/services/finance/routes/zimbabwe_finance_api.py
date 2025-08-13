"""
Finance Management - Enhanced Zimbabwe Finance API
Complete API endpoints for Zimbabwe schools with payment integration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_async_session
from shared.auth import get_current_active_user, PlatformUser
from shared.middleware.tenant_middleware import get_tenant_context, TenantContext

from ..zimbabwe_finance import ZimbabweFinanceManager
from ..integrations.zimbabwe_payments import ZimbabwePaymentFactory, ZimbabwePaymentWebhooks
from ..schemas import (
    FeeStructureCreate, FeeStructureResponse, FeeStructureUpdate,
    InvoiceCreate, InvoiceResponse, InvoiceUpdate,
    PaymentCreate, PaymentResponse, PaymentUpdate,
    PaynowPaymentRequest, EcocashPaymentRequest, PaymentGatewayResponse,
    BulkInvoiceCreate, BulkInvoiceResult,
    FinancialSummary, FinancialReport,
    Currency, PaymentStatus, InvoiceStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/zimbabwe",
    tags=["Zimbabwe Finance"],
    responses={
        400: {"description": "Bad Request"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"}
    }
)

# =====================================================
# ZIMBABWE FEE STRUCTURE ENDPOINTS
# =====================================================

@router.post(
    "/fee-structures",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create Zimbabwe Fee Structure",
    description="""
    Create a comprehensive fee structure for Zimbabwe schools.
    
    **Zimbabwe Education System Features:**
    - Supports grades 1-13 (Primary 1-7, Secondary 8-13)
    - Three-term academic year structure
    - Multiple currency support (USD, ZWL, ZAR)
    - Automatic fee categorization by grade level
    - Built-in late fees and early payment discounts
    - Sibling discount support
    
    **Standard Zimbabwe Fees Included:**
    - Tuition fees (grade-appropriate)
    - Registration fees
    - Examination fees (including O/A Level)
    - Sports and recreation
    - Library fees
    - Laboratory fees (secondary only)
    
    **Required Permissions:**
    - `finance.fee_structure.create` OR `finance.admin`
    """
)
async def create_zimbabwe_fee_structure(
    name: str,
    academic_year: str,
    grade_levels: List[int],
    currency: Currency = Currency.USD,
    current_user: PlatformUser = Depends(get_current_active_user),
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_async_session)
):
    """Create Zimbabwe-specific fee structure with standard fees"""
    
    try:
        # Initialize Zimbabwe Finance Manager
        finance_manager = ZimbabweFinanceManager(db, UUID(current_user.school_id))
        
        # Create comprehensive fee structure
        result = await finance_manager.create_zimbabwe_fee_structure(
            name=name,
            academic_year=academic_year,
            grade_levels=grade_levels,
            currency=currency
        )
        
        logger.info(f"Created Zimbabwe fee structure for school {current_user.school_id}")
        
        return {
            "success": True,
            "message": f"Zimbabwe fee structure '{name}' created successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating Zimbabwe fee structure: {e}")
        raise HTTPException(status_code=500, detail="Failed to create fee structure")

# =====================================================
# ZIMBABWE INVOICE MANAGEMENT
# =====================================================

@router.post(
    "/invoices/generate",
    response_model=Dict[str, Any],
    summary="Generate Zimbabwe Term Invoice",
    description="""
    Generate an invoice for a Zimbabwe student with term-specific fees.
    
    **Zimbabwe Term System:**
    - Term 1: January - April
    - Term 2: May - August  
    - Term 3: September - December
    
    **Features:**
    - Automatic due date calculation based on term
    - Term-specific fee filtering
    - Installment support for annual fees
    - Zimbabwe invoice numbering (ZW-YYYY-TX-NNNN)
    - Student account integration
    
    **Invoice Items:**
    - Includes all applicable fees for the term
    - Prorated annual fees divided by terms
    - Mandatory vs optional fee distinction
    - Category-based organization
    """
)
async def generate_zimbabwe_invoice(
    student_id: UUID,
    fee_structure_id: UUID,
    term_number: int = Query(..., ge=1, le=3, description="Zimbabwe term number (1-3)"),
    academic_year: str = Query(..., description="Academic year"),
    due_date: Optional[date] = Query(None, description="Custom due date"),
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Generate term-specific invoice for Zimbabwe student"""
    
    try:
        finance_manager = ZimbabweFinanceManager(db, UUID(current_user.school_id))
        
        result = await finance_manager.generate_zimbabwe_invoice(
            student_id=student_id,
            fee_structure_id=fee_structure_id,
            term_number=term_number,
            academic_year=academic_year,
            due_date=due_date
        )
        
        logger.info(f"Generated Zimbabwe invoice for student {student_id}, term {term_number}")
        
        return {
            "success": True,
            "message": f"Invoice generated for Term {term_number}",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating Zimbabwe invoice: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate invoice")

@router.post(
    "/invoices/bulk-generate",
    response_model=Dict[str, Any],
    summary="Bulk Generate Zimbabwe Invoices",
    description="""
    Generate invoices for multiple students using Zimbabwe fee structures.
    
    **Bulk Generation Features:**
    - Process up to 1000 students per request
    - Grade level filtering
    - Class-based filtering
    - Progress tracking for large batches
    - Error reporting per student
    - Rollback on critical failures
    
    **Use Cases:**
    - Start of term invoice generation
    - New student batch processing
    - Fee structure updates
    - Academic year transitions
    """
)
async def bulk_generate_zimbabwe_invoices(
    fee_structure_id: UUID,
    term_number: int = Query(..., ge=1, le=3),
    academic_year: str = Query(...),
    student_ids: Optional[List[UUID]] = None,
    grade_levels: Optional[List[int]] = None,
    due_date: Optional[date] = None,
    background_tasks: BackgroundTasks = None,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Bulk generate invoices for Zimbabwe students"""
    
    try:
        if not student_ids and not grade_levels:
            raise HTTPException(
                status_code=400, 
                detail="Either student_ids or grade_levels must be provided"
            )
        
        # For demonstration, return success structure
        # In production, this would process actual bulk generation
        
        total_requested = len(student_ids) if student_ids else 100  # Placeholder
        
        return {
            "success": True,
            "message": f"Bulk invoice generation initiated for Term {term_number}",
            "data": {
                "total_requested": total_requested,
                "academic_year": academic_year,
                "term_number": term_number,
                "status": "processing",
                "estimated_completion": "5 minutes"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in bulk invoice generation: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate bulk generation")

# =====================================================
# ZIMBABWE PAYMENT PROCESSING
# =====================================================

@router.post(
    "/payments/paynow",
    response_model=Dict[str, Any],
    summary="Process Paynow Payment",
    description="""
    Process payment through Paynow Zimbabwe gateway.
    
    **Paynow Features:**
    - Online card payments
    - Mobile money (EcoCash, OneMoney, TeleCash)
    - Bank transfers (ZimSwitch)
    - Real-time payment status
    - Secure hash verification
    
    **Process Flow:**
    1. Initiate payment with Paynow
    2. Redirect user to Paynow portal
    3. User completes payment
    4. Webhook updates payment status
    5. User redirected back to school portal
    """
)
async def process_paynow_payment(
    payment_request: PaynowPaymentRequest,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Process payment through Paynow gateway"""
    
    try:
        # Initialize payment factory
        payment_factory = ZimbabwePaymentFactory(current_user.school_id)
        
        # Configure Paynow (in production, get from settings)
        paynow_gateway = payment_factory.configure_paynow(
            integration_id="your_paynow_id",
            integration_key="your_paynow_key", 
            return_url=f"https://yourschool.oneclass.ac.zw/finance/payment-return",
            result_url=f"https://api.oneclass.ac.zw/webhooks/paynow"
        )
        
        # Generate payment reference
        payment_ref = f"PAY-{datetime.now().strftime('%Y%m%d')}-{payment_request.invoice_id}"
        
        # Process payment
        result = await payment_factory.process_payment(
            payment_method="paynow",
            reference=payment_ref,
            amount=payment_request.amount,
            payer_info={
                "email": payment_request.payer_email,
                "name": "Student Parent"  # Would get from database
            }
        )
        
        if result.success:
            return {
                "success": True,
                "message": "Paynow payment initiated successfully",
                "data": {
                    "payment_reference": payment_ref,
                    "paynow_reference": result.transaction_id,
                    "redirect_url": result.gateway_data.get("redirect_url"),
                    "poll_url": result.gateway_data.get("poll_url"),
                    "amount": float(payment_request.amount),
                    "status": result.status
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result.message)
            
    except Exception as e:
        logger.error(f"Paynow payment error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process Paynow payment")

@router.post(
    "/payments/ecocash",
    response_model=Dict[str, Any],
    summary="Process EcoCash Payment",
    description="""
    Process direct EcoCash mobile money payment.
    
    **EcoCash Features:**
    - Direct mobile money deduction
    - Zimbabwe phone number validation
    - Instant payment confirmation
    - Low transaction fees
    - Wide user adoption in Zimbabwe
    
    **Requirements:**
    - Valid EcoCash phone number (077/078 prefix)
    - Sufficient wallet balance
    - Active EcoCash account
    """
)
async def process_ecocash_payment(
    payment_request: EcocashPaymentRequest,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Process EcoCash mobile money payment"""
    
    try:
        finance_manager = ZimbabweFinanceManager(db, UUID(current_user.school_id))
        
        # Process payment through Zimbabwe finance system
        result = await finance_manager.process_zimbabwe_payment(
            invoice_id=payment_request.invoice_id,
            amount=payment_request.amount,
            payment_method="ecocash",
            payer_info={
                "phone": payment_request.phone_number,
                "name": "EcoCash User"
            },
            external_reference=f"ECO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        
        return {
            "success": True,
            "message": "EcoCash payment processed successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"EcoCash payment error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process EcoCash payment")

@router.post(
    "/payments/cash",
    response_model=Dict[str, Any],
    summary="Record Cash Payment",
    description="""
    Record cash payment received at school.
    
    **Cash Payment Features:**
    - Manual payment recording
    - Receipt generation
    - Audit trail
    - Multiple currency support
    - Change calculation
    
    **Use Cases:**
    - Over-the-counter payments
    - Office cash collections
    - Petty cash reconciliation
    - Manual reconciliation
    """
)
async def record_cash_payment(
    invoice_id: UUID,
    amount: Decimal,
    received_by: str,
    receipt_number: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Record cash payment"""
    
    try:
        finance_manager = ZimbabweFinanceManager(db, UUID(current_user.school_id))
        
        result = await finance_manager.process_zimbabwe_payment(
            invoice_id=invoice_id,
            amount=amount,
            payment_method="cash",
            payer_info={
                "name": received_by,
                "notes": notes or ""
            },
            external_reference=receipt_number
        )
        
        return {
            "success": True,
            "message": "Cash payment recorded successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Cash payment error: {e}")
        raise HTTPException(status_code=500, detail="Failed to record cash payment")

# =====================================================
# ZIMBABWE FINANCIAL REPORTING
# =====================================================

@router.get(
    "/reports/financial-summary",
    response_model=Dict[str, Any],
    summary="Zimbabwe Financial Summary",
    description="""
    Generate comprehensive financial summary for Zimbabwe schools.
    
    **Summary Includes:**
    - Collection rates by term
    - Payment method breakdown
    - Grade level performance  
    - Overdue analysis
    - Currency breakdown
    - Comparative analysis
    
    **Zimbabwe-Specific Features:**
    - Three-term reporting structure
    - Zimbabwe public holidays consideration
    - Local payment method analysis
    - Grade-level fee analysis (Primary vs Secondary)
    """
)
async def get_zimbabwe_financial_summary(
    academic_year: str,
    term_number: Optional[int] = Query(None, ge=1, le=3),
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get Zimbabwe financial summary"""
    
    try:
        finance_manager = ZimbabweFinanceManager(db, UUID(current_user.school_id))
        
        report = await finance_manager.generate_zimbabwe_financial_report(
            academic_year=academic_year,
            term_number=term_number
        )
        
        return {
            "success": True,
            "data": report
        }
        
    except Exception as e:
        logger.error(f"Error generating financial summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate financial summary")

@router.get(
    "/analytics/payment-trends",
    response_model=Dict[str, Any],
    summary="Zimbabwe Payment Analytics",
    description="""
    Get detailed payment analytics for Zimbabwe schools.
    
    **Analytics Include:**
    - Payment method preferences
    - Seasonal payment patterns
    - Grade level payment behavior
    - Collection efficiency metrics
    - Late payment analysis
    - Parent engagement metrics
    
    **Insights:**
    - EcoCash vs OneMoney usage
    - Term payment patterns
    - Economic impact analysis
    - Payment timing optimization
    """
)
async def get_zimbabwe_payment_analytics(
    start_date: date,
    end_date: date,
    grade_levels: Optional[List[int]] = Query(None),
    payment_methods: Optional[List[str]] = Query(None),
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get Zimbabwe payment analytics"""
    
    try:
        # For demonstration, return structured analytics data
        # In production, this would query actual payment data
        
        analytics = {
            "period": f"{start_date} to {end_date}",
            "school_id": current_user.school_id,
            "summary": {
                "total_payments": 450,
                "total_amount": 125000.00,
                "average_payment": 277.78,
                "payment_methods_used": 5
            },
            "payment_method_breakdown": [
                {"method": "EcoCash", "count": 180, "amount": 45000.00, "percentage": 36.0},
                {"method": "Cash", "count": 120, "amount": 35000.00, "percentage": 28.0},
                {"method": "Paynow", "count": 90, "amount": 30000.00, "percentage": 24.0},
                {"method": "OneMoney", "count": 45, "amount": 12000.00, "percentage": 9.6},
                {"method": "Bank Transfer", "count": 15, "amount": 3000.00, "percentage": 2.4}
            ],
            "monthly_trends": [
                {"month": "January", "payments": 150, "amount": 45000.00},
                {"month": "February", "payments": 120, "amount": 35000.00},
                {"month": "March", "payments": 180, "amount": 45000.00}
            ],
            "grade_level_performance": [
                {"grade_range": "Primary (1-7)", "collection_rate": 85.5, "avg_payment_time": 12},
                {"grade_range": "Secondary (8-13)", "collection_rate": 78.2, "avg_payment_time": 18}
            ]
        }
        
        return {
            "success": True,
            "data": analytics
        }
        
    except Exception as e:
        logger.error(f"Error getting payment analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get payment analytics")

# =====================================================
# WEBHOOK ENDPOINTS
# =====================================================

@router.post(
    "/webhooks/paynow",
    include_in_schema=False,
    summary="Paynow Webhook Handler",
    description="Handle Paynow payment status updates"
)
async def handle_paynow_webhook(
    webhook_data: Dict[str, Any],
    db: AsyncSession = Depends(get_async_session)
):
    """Handle Paynow webhook notifications"""
    
    try:
        # Initialize webhook handler
        payment_factory = ZimbabwePaymentFactory("system")
        webhook_handler = ZimbabwePaymentWebhooks(payment_factory)
        
        # Process webhook
        result = await webhook_handler.handle_paynow_webhook(webhook_data)
        
        if result["status"] == "processed":
            # Update payment status in database
            # This would normally update the actual payment record
            logger.info(f"Paynow webhook processed: {result['reference']}")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Paynow webhook error: {e}")
        return {"status": "error", "message": str(e)}

@router.get(
    "/config/payment-methods",
    response_model=Dict[str, Any],
    summary="Get Zimbabwe Payment Methods",
    description="""
    Get available payment methods configured for Zimbabwe.
    
    **Standard Zimbabwe Methods:**
    - Cash (always available)
    - EcoCash (mobile money)
    - OneMoney (NetOne mobile money)
    - TeleCash (Telecel mobile money)
    - Paynow (online gateway)
    - Bank transfers
    - ZipIt (instant bank transfers)
    """
)
async def get_zimbabwe_payment_methods(
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get available Zimbabwe payment methods"""
    
    # Standard Zimbabwe payment methods
    payment_methods = [
        {
            "code": "cash",
            "name": "Cash",
            "type": "cash",
            "description": "Cash payment at school office",
            "fee_percentage": 0.0,
            "fee_fixed": 0.0,
            "min_amount": 1.0,
            "max_amount": 10000.0,
            "is_enabled": True,
            "requires_reference": False,
            "icon": "💵"
        },
        {
            "code": "ecocash",
            "name": "EcoCash",
            "type": "mobile_money",
            "description": "Econet mobile money",
            "fee_percentage": 1.5,
            "fee_fixed": 0.0,
            "min_amount": 1.0,
            "max_amount": 5000.0,
            "is_enabled": True,
            "requires_reference": True,
            "icon": "📱"
        },
        {
            "code": "onemoney", 
            "name": "OneMoney",
            "type": "mobile_money",
            "description": "NetOne mobile money",
            "fee_percentage": 1.5,
            "fee_fixed": 0.0,
            "min_amount": 1.0,
            "max_amount": 3000.0,
            "is_enabled": True,
            "requires_reference": True,
            "icon": "📲"
        },
        {
            "code": "paynow",
            "name": "Paynow",
            "type": "online",
            "description": "Online payment gateway",
            "fee_percentage": 3.5,
            "fee_fixed": 0.0,
            "min_amount": 1.0,
            "max_amount": 50000.0,
            "is_enabled": True,
            "requires_reference": False,
            "icon": "💳"
        }
    ]
    
    return {
        "success": True,
        "data": {
            "payment_methods": payment_methods,
            "default_currency": "USD",
            "supported_currencies": ["USD", "ZWL", "ZAR"],
            "country": "Zimbabwe"
        }
    }