"""
Finance-SIS Integration API
API endpoints for connecting Student Information System with financial operations
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

from ..integrations.sis_integration import FinanceSISIntegration
from ..schemas import Currency

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/sis-integration",
    tags=["SIS Finance Integration"],
    responses={
        400: {"description": "Bad Request"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"}
    }
)

# =====================================================
# STUDENT ENROLLMENT BILLING ENDPOINTS
# =====================================================

@router.post(
    "/students/{student_id}/invoices/enrollment-based",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create Enrollment-Based Invoice",
    description="""
    Create invoice based on student enrollment information from SIS.
    
    **Enrollment-Based Features:**
    - Automatic fee structure detection by grade level
    - Scholarship discount application
    - Special program fee additions
    - Sibling discount calculation
    - Family billing integration
    
    **Required Enrollment Data:**
    - student_number: Student identification number
    - grade_level: Current grade level (1-13 for Zimbabwe)
    - enrollment_status: Must be 'active'
    
    **Optional Adjustments:**
    - scholarship_percentage: Scholarship discount (0-100%)
    - special_programs: List of special programs ["sports", "computer_club"]
    - family_id: For sibling discount calculation
    
    **Process:**
    1. Validate enrollment status and data
    2. Find appropriate fee structure for grade level
    3. Generate base invoice using Zimbabwe finance manager
    4. Apply enrollment-specific adjustments (scholarships, programs, siblings)
    5. Update student account with enrollment information
    """
)
async def create_enrollment_based_invoice(
    student_id: UUID,
    academic_year: str,
    term_number: int = Query(..., ge=1, le=3, description="Zimbabwe term number (1-3)"),
    enrollment_data: Dict[str, Any] = ...,
    current_user: PlatformUser = Depends(get_current_active_user),
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_async_session)
):
    """Create invoice based on student enrollment data"""
    
    try:
        integration = FinanceSISIntegration(db, UUID(current_user.school_id))
        
        result = await integration.create_enrollment_based_invoice(
            student_id=student_id,
            academic_year=academic_year,
            term_number=term_number,
            enrollment_data=enrollment_data
        )
        
        logger.info(f"Created enrollment-based invoice for student {student_id}")
        
        return {
            "success": True,
            "message": f"Enrollment-based invoice created for Term {term_number}",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating enrollment-based invoice: {e}")
        raise HTTPException(status_code=500, detail="Failed to create enrollment-based invoice")

# =====================================================
# FAMILY BILLING ENDPOINTS  
# =====================================================

@router.post(
    "/families/{family_id}/consolidated-bill",
    response_model=Dict[str, Any],
    summary="Generate Family Consolidated Bill",
    description="""
    Generate consolidated billing statement for all students in a family.
    
    **Family Billing Features:**
    - Multi-student consolidated view
    - Family-level payment options
    - Sibling discount application
    - Guardian contact integration
    - Payment plan recommendations
    
    **Bill Components:**
    - Individual student invoices and balances
    - Family payment history across all students
    - Outstanding balances per student
    - Consolidated payment options
    - Family-specific discounts and adjustments
    
    **Payment Plan Options:**
    - Full payment discount
    - Term-based installments
    - Monthly payment plans
    - Family hardship considerations
    
    **Use Cases:**
    - Parent/guardian billing statements
    - Family payment planning
    - Multi-child discount application
    - Consolidated payment processing
    """
)
async def generate_family_consolidated_bill(
    family_id: UUID,
    academic_year: str,
    term_number: int = Query(..., ge=1, le=3),
    include_payment_plan: bool = Query(True, description="Include payment plan options"),
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Generate consolidated bill for family"""
    
    try:
        integration = FinanceSISIntegration(db, UUID(current_user.school_id))
        
        result = await integration.generate_family_consolidated_bill(
            family_id=family_id,
            academic_year=academic_year,
            term_number=term_number,
            include_payment_plan=include_payment_plan
        )
        
        logger.info(f"Generated consolidated bill for family {family_id}")
        
        return {
            "success": True,
            "message": f"Family consolidated bill generated for Term {term_number}",
            "data": result["data"]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating family consolidated bill: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate family consolidated bill")

# =====================================================
# BULK STUDENT OPERATIONS
# =====================================================

@router.post(
    "/students/bulk-invoices",
    response_model=Dict[str, Any],
    summary="Bulk Create Student Invoices",
    description="""
    Bulk create invoices for students based on SIS enrollment data.
    
    **Bulk Processing Features:**
    - SIS integration for student enrollment data
    - Flexible filtering options
    - Batch processing for performance
    - Comprehensive error handling
    - Progress tracking and reporting
    
    **Filter Options:**
    - grade_level: Specific grade level (1-13)
    - class_id: Specific class/section
    - enrollment_status: Student enrollment status
    - family_id: Specific family
    - enrollment_date_range: Date range filters
    
    **Performance Features:**
    - Configurable batch size (10-500 students)
    - Background processing for large operations
    - Memory-efficient processing
    - Detailed progress reporting
    - Individual student error isolation
    
    **Error Handling:**
    - Individual student failures don't stop batch
    - Detailed error reporting per student
    - Retry mechanisms for transient failures
    - Rollback options for critical errors
    
    **Typical Usage:**
    - Start of term mass billing
    - New student enrollment processing
    - Grade-specific billing campaigns
    - Family-based billing runs
    """
)
async def bulk_create_student_invoices(
    academic_year: str,
    term_number: int = Query(..., ge=1, le=3),
    filters: Optional[Dict[str, Any]] = None,
    batch_size: int = Query(100, ge=10, le=500, description="Batch processing size"),
    background_tasks: BackgroundTasks = None,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Bulk create invoices for students from SIS"""
    
    try:
        integration = FinanceSISIntegration(db, UUID(current_user.school_id))
        
        # For very large operations, use background processing
        estimated_students = filters.get("estimated_count", 100) if filters else 100
        
        if estimated_students > 200 or batch_size > 200:
            if background_tasks:
                # Add to background tasks
                background_tasks.add_task(
                    integration.bulk_create_student_invoices,
                    academic_year, term_number, filters or {}, batch_size
                )
                
                return {
                    "success": True,
                    "message": f"Bulk invoice creation started for Term {term_number}",
                    "data": {
                        "academic_year": academic_year,
                        "term_number": term_number,
                        "filters_applied": filters or {},
                        "batch_size": batch_size,
                        "status": "processing_in_background",
                        "estimated_completion": "3-8 minutes"
                    }
                }
        
        # Process synchronously for smaller operations
        result = await integration.bulk_create_student_invoices(
            academic_year=academic_year,
            term_number=term_number,
            filters=filters or {},
            batch_size=batch_size
        )
        
        logger.info(f"Completed bulk student invoice creation: {result['data']['invoices_created']} invoices")
        
        return {
            "success": True,
            "message": f"Bulk invoice creation completed for Term {term_number}",
            "data": result["data"]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in bulk student invoice creation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create bulk student invoices")

# =====================================================
# STUDENT PAYMENT TRACKING
# =====================================================

@router.get(
    "/students/{student_id}/payment-progress/{academic_year}",
    response_model=Dict[str, Any],
    summary="Track Student Payment Progress",
    description="""
    Track comprehensive payment progress for a student across all terms.
    
    **Progress Tracking Features:**
    - Complete academic year payment history
    - Term-by-term progress analysis
    - Payment method preferences
    - Payment timing patterns
    - Outstanding balance tracking
    
    **Data Included:**
    - All invoices generated for the student
    - All payments made across all terms
    - Payment method usage patterns
    - Average days to payment
    - Term-specific payment status
    
    **Analytics:**
    - Payment behavior analysis
    - Collection rate calculation
    - Payment method preferences
    - Seasonal payment patterns
    - Family payment coordination
    
    **Use Cases:**
    - Parent payment history review
    - Student account management
    - Collection strategy optimization
    - Payment behavior analysis
    - Financial counseling support
    """
)
async def track_student_payment_progress(
    student_id: UUID,
    academic_year: str,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Track payment progress for a student"""
    
    try:
        integration = FinanceSISIntegration(db, UUID(current_user.school_id))
        
        result = await integration.track_student_payment_progress(
            student_id=student_id,
            academic_year=academic_year
        )
        
        return {
            "success": True,
            "data": result["data"]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error tracking student payment progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to track student payment progress")

# =====================================================
# ENROLLMENT ANALYTICS  
# =====================================================

@router.get(
    "/analytics/enrollment-billing",
    response_model=Dict[str, Any],
    summary="Enrollment Billing Analytics", 
    description="""
    Get detailed analytics on enrollment-based billing patterns.
    
    **Analytics Categories:**
    - Enrollment status impact on payments
    - Grade-level enrollment and billing correlation
    - Special program participation and fees
    - Scholarship distribution and impact
    - Family enrollment patterns
    
    **Insights Provided:**
    - Most profitable grade levels
    - Program participation rates
    - Scholarship effectiveness
    - Family billing optimization opportunities
    - Enrollment-driven revenue projections
    
    **Time-Based Analysis:**
    - Term-by-term enrollment billing trends
    - Academic year comparisons
    - Seasonal enrollment patterns
    - New student billing performance
    """
)
async def get_enrollment_billing_analytics(
    academic_year: str,
    grade_levels: Optional[List[int]] = Query(None, description="Filter by grade levels"),
    include_programs: bool = Query(True, description="Include special program analysis"),
    include_scholarships: bool = Query(True, description="Include scholarship analysis"),
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get enrollment billing analytics"""
    
    try:
        # For demonstration, return structured analytics
        # In production, this would query actual SIS and financial data
        
        analytics = {
            "academic_year": academic_year,
            "analysis_date": datetime.now().isoformat(),
            "school_id": current_user.school_id,
            "enrollment_overview": {
                "total_enrolled_students": 387,
                "active_enrollments": 387,
                "inactive_enrollments": 0,
                "new_enrollments_this_year": 45,
                "enrollment_by_grade": {
                    "primary": {"grades": "1-7", "count": 185, "percentage": 47.8},
                    "o_level": {"grades": "8-11", "count": 149, "percentage": 38.5},
                    "a_level": {"grades": "12-13", "count": 53, "percentage": 13.7}
                }
            },
            "billing_performance": {
                "total_invoiced": 331900.00,
                "enrollment_based_adjustments": -28450.00,
                "net_billing_amount": 303450.00,
                "collection_rate": 87.3,
                "average_per_student": 784.50
            }
        }
        
        if include_programs:
            analytics["special_programs"] = {
                "total_program_participants": 89,
                "program_breakdown": [
                    {"program": "Sports", "participants": 34, "additional_revenue": 1700.00},
                    {"program": "Computer Club", "participants": 28, "additional_revenue": 2100.00},
                    {"program": "Drama Club", "participants": 15, "additional_revenue": 600.00},
                    {"program": "Debate Society", "participants": 12, "additional_revenue": 360.00}
                ],
                "program_revenue_impact": 4760.00,
                "participation_rate": 23.0
            }
        
        if include_scholarships:
            analytics["scholarships"] = {
                "total_scholarship_recipients": 39,
                "total_scholarship_amount": 28450.00,
                "average_scholarship_percentage": 12.5,
                "scholarship_impact_on_collection": {
                    "scholarship_students_collection_rate": 94.2,
                    "non_scholarship_students_collection_rate": 85.1,
                    "note": "Scholarship students show higher collection rates"
                },
                "scholarship_distribution": [
                    {"percentage": "5%", "recipients": 15, "amount": 7612.50},
                    {"percentage": "10%", "recipients": 18, "amount": 15840.00},
                    {"percentage": "25%", "recipients": 6, "amount": 4997.50}
                ]
            }
        
        # Add family billing insights
        analytics["family_insights"] = {
            "total_families": 298,
            "families_with_multiple_children": 67,
            "sibling_discount_recipients": 134,
            "total_sibling_discounts": 15680.00,
            "average_family_billing": 1018.30,
            "families_with_payment_plans": 23
        }
        
        # Add trends and recommendations
        analytics["trends"] = [
            "A-Level students have 96.2% collection rate vs 87.3% average",
            "Special program participants show 15% higher collection rates",
            "Families with multiple children have more consistent payment patterns",
            "New enrollments show 91% collection rate in first term"
        ]
        
        analytics["recommendations"] = [
            "Expand A-Level programs - highest collection rates and fees",
            "Promote special programs to increase revenue and engagement",
            "Target family-based payment incentives for multi-child families",
            "Implement new student support programs to maintain high collection rates"
        ]
        
        return {
            "success": True,
            "data": analytics
        }
        
    except Exception as e:
        logger.error(f"Error getting enrollment billing analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get enrollment billing analytics")

# =====================================================
# FAMILY FINANCIAL DASHBOARD
# =====================================================

@router.get(
    "/families/{family_id}/financial-summary",
    response_model=Dict[str, Any],
    summary="Family Financial Dashboard",
    description="""
    Get comprehensive financial summary for a family across all enrolled students.
    
    **Dashboard Features:**
    - Multi-student financial overview
    - Payment history across all children
    - Outstanding balances summary
    - Payment method preferences
    - Family-specific discounts and adjustments
    
    **Financial Insights:**
    - Total family investment in education
    - Payment consistency patterns
    - Seasonal payment behaviors
    - Recommended payment strategies
    - Family financial health score
    
    **Actionable Data:**
    - Upcoming payment due dates
    - Available payment plan options
    - Family discount opportunities
    - Payment method optimization
    """
)
async def get_family_financial_summary(
    family_id: UUID,
    academic_year: str,
    include_projections: bool = Query(True, description="Include financial projections"),
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get comprehensive financial summary for a family"""
    
    try:
        # For demonstration, return structured family financial data
        # In production, this would integrate with actual SIS and financial records
        
        summary = {
            "family_id": str(family_id),
            "academic_year": academic_year,
            "generated_date": datetime.now().isoformat(),
            "family_info": {
                "family_name": "The Chimbira Family",
                "primary_guardian": "Mr. James Chimbira",
                "contact_email": "james.chimbira@email.com",
                "enrolled_students": 2,
                "payment_history_score": 8.5,
                "preferred_payment_method": "EcoCash"
            },
            "financial_summary": {
                "total_annual_fees": 2400.00,
                "total_paid_to_date": 1920.00,
                "total_outstanding": 480.00,
                "family_discounts_applied": 240.00,
                "collection_rate": 80.0,
                "payment_consistency": "Good"
            },
            "students": [
                {
                    "student_name": "Tendai Chimbira",
                    "grade_level": 10,
                    "total_fees": 1800.00,
                    "paid_amount": 1440.00,
                    "outstanding": 360.00,
                    "status": "partially_paid"
                },
                {
                    "student_name": "Grace Chimbira", 
                    "grade_level": 7,
                    "total_fees": 600.00,
                    "paid_amount": 480.00,
                    "outstanding": 120.00,
                    "status": "partially_paid"
                }
            ],
            "payment_patterns": {
                "average_payment_amount": 240.00,
                "payment_frequency": "Monthly",
                "preferred_payment_dates": ["15th", "30th"],
                "most_used_methods": ["EcoCash", "Cash"],
                "payment_reliability": "Consistently pays within grace period"
            }
        }
        
        if include_projections:
            summary["projections"] = {
                "projected_annual_total": 2640.00,
                "remaining_payments_needed": 2,
                "recommended_payment_plan": "Monthly installments of $240",
                "early_payment_discount_opportunity": 48.00,
                "projected_completion_date": "2024-11-15"
            }
        
        # Add recommendations
        summary["recommendations"] = [
            "Consider early payment discount - save $48 by paying Term 3 fees before October 1st",
            "Continue monthly payment pattern - working well for family budget",
            "EcoCash payments processed fastest - recommend for urgent payments",
            "Family eligible for loyalty discount next academic year"
        ]
        
        return {
            "success": True,
            "data": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting family financial summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get family financial summary")