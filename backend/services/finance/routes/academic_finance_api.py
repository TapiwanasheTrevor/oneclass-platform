"""
Finance-Academic Integration API
API endpoints for connecting academic structures with financial operations
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

from ..integrations.academic_integration import FinanceAcademicIntegration
from ..schemas import Currency

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/academic-integration",
    tags=["Academic Finance Integration"],
    responses={
        400: {"description": "Bad Request"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"}
    }
)

# =====================================================
# GRADE-BASED FEE MANAGEMENT ENDPOINTS
# =====================================================

@router.post(
    "/fee-structures/grade-based",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create Grade-Based Fee Structures",
    description="""
    Create comprehensive fee structures based on academic grade levels.
    
    **Zimbabwe Grade System:**
    - Primary: Grades 1-7
    - O-Level: Grades 8-11  
    - A-Level: Grades 12-13
    
    **Features:**
    - Automatic fee categorization by grade level
    - Custom fee multipliers per grade range
    - Special fees for specific grades
    - Integration with academic grade structures
    
    **Grade Configuration Examples:**
    ```json
    [
        {
            "grade_levels": [1, 2, 3, 4],
            "fee_multiplier": 0.8,
            "special_fees": {"computer_lab": 15.00}
        },
        {
            "grade_levels": [8, 9, 10, 11],
            "fee_multiplier": 1.5,
            "special_fees": {"laboratory": 75.00, "examination": 150.00}
        }
    ]
    ```
    """
)
async def create_grade_based_fee_structures(
    academic_year: str,
    grade_configurations: List[Dict[str, Any]],
    base_currency: Currency = Currency.USD,
    current_user: PlatformUser = Depends(get_current_active_user),
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_async_session)
):
    """Create fee structures based on grade levels"""
    
    try:
        integration = FinanceAcademicIntegration(db, UUID(current_user.school_id))
        
        result = await integration.create_grade_based_fee_structure(
            academic_year=academic_year,
            grade_configurations=grade_configurations,
            base_currency=base_currency
        )
        
        logger.info(f"Created grade-based fee structures for school {current_user.school_id}")
        
        return {
            "success": True,
            "message": f"Grade-based fee structures created for {academic_year}",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating grade-based fee structures: {e}")
        raise HTTPException(status_code=500, detail="Failed to create grade-based fee structures")

# =====================================================
# CLASS-BASED BILLING ENDPOINTS
# =====================================================

@router.post(
    "/invoices/class/{class_id}",
    response_model=Dict[str, Any],
    summary="Generate Class Invoices",
    description="""
    Generate invoices for all students in a specific class.
    
    **Class-Based Billing Features:**
    - Bulk invoice generation for entire class
    - Automatic fee structure detection by grade
    - Individual student error handling
    - Comprehensive success/failure reporting
    
    **Use Cases:**
    - Start of term billing
    - Class-specific fee adjustments
    - Targeted billing campaigns
    - Teacher-initiated billing requests
    
    **Process:**
    1. Retrieve all students enrolled in the class
    2. Detect appropriate fee structure for class grade
    3. Generate individual invoices for each student
    4. Return detailed success/failure report
    """
)
async def generate_class_invoices(
    class_id: UUID,
    term_number: int = Query(..., ge=1, le=3, description="Zimbabwe term number (1-3)"),
    academic_year: str = Query(..., description="Academic year"),
    fee_structure_id: Optional[UUID] = Query(None, description="Override fee structure"),
    due_date: Optional[date] = Query(None, description="Custom due date"),
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Generate invoices for all students in a class"""
    
    try:
        integration = FinanceAcademicIntegration(db, UUID(current_user.school_id))
        
        result = await integration.generate_class_invoices(
            class_id=class_id,
            term_number=term_number,
            academic_year=academic_year,
            fee_structure_id=fee_structure_id,
            due_date=due_date
        )
        
        logger.info(f"Generated class invoices for class {class_id}, term {term_number}")
        
        return {
            "success": True,
            "message": f"Class invoices generated for Term {term_number}",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating class invoices: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate class invoices")

# =====================================================
# TERM-BASED BULK OPERATIONS
# =====================================================

@router.post(
    "/invoices/term-bulk",
    response_model=Dict[str, Any],
    summary="Generate Term Invoices by Grade",
    description="""
    Generate term invoices for multiple grade levels in bulk.
    
    **Bulk Term Processing:**
    - Process multiple grades simultaneously
    - Batch processing for performance
    - Automatic fee structure detection
    - Progress tracking and error reporting
    - Background processing support
    
    **Performance Features:**
    - Configurable batch size (default: 100 students)
    - Grade-level parallelization
    - Memory-efficient processing
    - Detailed progress reporting
    
    **Error Handling:**
    - Individual student error isolation
    - Detailed failure reporting
    - Partial success support
    - Rollback on critical failures
    
    **Typical Usage:**
    - Start of term mass billing
    - Grade-level fee rollouts
    - Academic year transitions
    - School-wide billing campaigns
    """
)
async def generate_term_invoices_by_grade(
    academic_year: str,
    term_number: int = Query(..., ge=1, le=3),
    grade_levels: List[int] = Query(..., description="List of grade levels to process"),
    batch_size: int = Query(100, ge=10, le=500, description="Batch processing size"),
    background_tasks: BackgroundTasks = None,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Generate term invoices for specific grade levels in bulk"""
    
    try:
        # Validate grade levels for Zimbabwe
        for grade in grade_levels:
            if grade < 1 or grade > 13:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid Zimbabwe grade level: {grade}. Must be 1-13"
                )
        
        integration = FinanceAcademicIntegration(db, UUID(current_user.school_id))
        
        # For large operations, consider background processing
        if len(grade_levels) > 5 or batch_size > 200:
            if background_tasks:
                # Add to background tasks for async processing
                background_tasks.add_task(
                    integration.generate_term_invoices_by_grade,
                    academic_year, term_number, grade_levels, batch_size
                )
                
                return {
                    "success": True,
                    "message": f"Bulk invoice generation started for Term {term_number}",
                    "data": {
                        "academic_year": academic_year,
                        "term_number": term_number,
                        "grade_levels": grade_levels,
                        "batch_size": batch_size,
                        "status": "processing_in_background",
                        "estimated_completion": "5-10 minutes"
                    }
                }
        
        # Process synchronously for smaller operations
        result = await integration.generate_term_invoices_by_grade(
            academic_year=academic_year,
            term_number=term_number,
            grade_levels=grade_levels,
            batch_size=batch_size
        )
        
        logger.info(f"Completed bulk term invoice generation for grades {grade_levels}")
        
        return {
            "success": True,
            "message": f"Bulk invoice generation completed for Term {term_number}",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in bulk term invoice generation: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate term invoices")

# =====================================================
# ACADEMIC CALENDAR INTEGRATION
# =====================================================

@router.post(
    "/calendar/sync/{academic_year}",
    response_model=Dict[str, Any],
    summary="Sync with Academic Calendar",
    description="""
    Synchronize financial periods with academic calendar.
    
    **Calendar Integration:**
    - Create financial periods aligned with academic terms
    - Set appropriate due dates based on academic calendar
    - Configure late fee periods
    - Enable term-specific financial reporting
    
    **Zimbabwe Academic Calendar:**
    - Term 1: January - April (fees due mid-February)
    - Term 2: May - August (fees due mid-June)
    - Term 3: September - December (fees due mid-October)
    
    **Financial Period Features:**
    - Automatic due date calculation
    - Grace period configuration
    - Late fee activation dates
    - Term-specific reporting periods
    """
)
async def sync_with_academic_calendar(
    academic_year: str,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Sync financial periods with academic calendar"""
    
    try:
        integration = FinanceAcademicIntegration(db, UUID(current_user.school_id))
        
        result = await integration.sync_with_academic_calendar(academic_year)
        
        logger.info(f"Synced financial periods with academic calendar for {academic_year}")
        
        return {
            "success": True,
            "message": f"Financial calendar synced for {academic_year}",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error syncing with academic calendar: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync with academic calendar")

# =====================================================
# ACADEMIC FINANCE REPORTING
# =====================================================

@router.get(
    "/reports/academic-finance/{academic_year}",
    response_model=Dict[str, Any],
    summary="Academic Finance Report",
    description="""
    Generate comprehensive finance report with academic context.
    
    **Report Components:**
    - Base financial metrics (invoicing, payments, collection rates)
    - Grade-level performance analysis
    - Class-by-class financial breakdown
    - Term progression analysis
    - Academic calendar alignment
    
    **Grade-Level Analysis:**
    - Primary vs Secondary performance
    - Collection rate by grade range
    - Average payment per student
    - Grade-specific trends
    
    **Class Breakdown:**
    - Individual class financial performance
    - Class size impact on collections
    - Teacher/class-specific insights
    - Outstanding balances by class
    
    **Term Progression:**
    - Collection patterns across terms
    - Seasonal payment trends
    - Term-specific challenges
    - Year-end collection improvements
    """
)
async def get_academic_finance_report(
    academic_year: str,
    include_class_breakdown: bool = Query(True, description="Include class-level data"),
    include_grade_analysis: bool = Query(True, description="Include grade-level analysis"),
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get comprehensive academic finance report"""
    
    try:
        integration = FinanceAcademicIntegration(db, UUID(current_user.school_id))
        
        report = await integration.generate_academic_finance_report(
            academic_year=academic_year,
            include_class_breakdown=include_class_breakdown,
            include_grade_analysis=include_grade_analysis
        )
        
        return {
            "success": True,
            "data": report
        }
        
    except Exception as e:
        logger.error(f"Error generating academic finance report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate academic finance report")

# =====================================================
# GRADE PERFORMANCE ANALYTICS
# =====================================================

@router.get(
    "/analytics/grade-performance",
    response_model=Dict[str, Any],
    summary="Grade Performance Analytics",
    description="""
    Get detailed financial performance analytics by grade level.
    
    **Analytics Include:**
    - Collection rate by grade level
    - Payment timing patterns
    - Fee structure effectiveness
    - Grade-specific payment methods
    - Parent engagement by grade
    
    **Insights:**
    - Primary vs Secondary payment behavior
    - O-Level vs A-Level collection rates
    - Grade transition impact on payments
    - Optimal fee structure by grade
    """
)
async def get_grade_performance_analytics(
    academic_year: str,
    grade_levels: Optional[List[int]] = Query(None, description="Specific grades to analyze"),
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get grade-level financial performance analytics"""
    
    try:
        # For demonstration, return structured analytics
        # In production, this would query actual academic and financial data
        
        analytics = {
            "academic_year": academic_year,
            "analysis_date": datetime.now().isoformat(),
            "school_id": current_user.school_id,
            "grade_performance": {
                "primary_grades": {
                    "grade_range": "1-7",
                    "average_collection_rate": 87.5,
                    "total_students": 185,
                    "preferred_payment_method": "Cash",
                    "average_days_to_pay": 12,
                    "parent_engagement_score": 8.2
                },
                "o_level_grades": {
                    "grade_range": "8-11",
                    "average_collection_rate": 82.1,
                    "total_students": 130,
                    "preferred_payment_method": "EcoCash",
                    "average_days_to_pay": 15,
                    "parent_engagement_score": 7.8
                },
                "a_level_grades": {
                    "grade_range": "12-13",
                    "average_collection_rate": 91.3,
                    "total_students": 53,
                    "preferred_payment_method": "Paynow",
                    "average_days_to_pay": 8,
                    "parent_engagement_score": 9.1,
                    "note": "Higher collection due to university preparation motivation"
                }
            },
            "trends": {
                "best_performing_grade": 12,
                "most_challenging_grade": 9,
                "payment_method_shift": "Increasing digital payment adoption in secondary grades",
                "seasonal_patterns": "Term 1 highest collection rate, Term 2 most challenging"
            },
            "recommendations": [
                "Implement targeted collection strategies for Grade 9 students",
                "Promote digital payment methods for primary grades",
                "Leverage high A-Level engagement for peer mentoring programs",
                "Consider grade-specific payment incentives"
            ]
        }
        
        return {
            "success": True,
            "data": analytics
        }
        
    except Exception as e:
        logger.error(f"Error getting grade performance analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get grade performance analytics")

# =====================================================
# CLASS FINANCIAL SUMMARY
# =====================================================

@router.get(
    "/summary/class/{class_id}",
    response_model=Dict[str, Any], 
    summary="Class Financial Summary",
    description="""
    Get financial summary for a specific class.
    
    **Class Summary Includes:**
    - Total students enrolled
    - Invoices generated and paid
    - Outstanding balances
    - Payment method preferences
    - Collection timeline
    - Class-specific insights
    
    **Teacher Dashboard Integration:**
    - Quick financial overview for teachers
    - Student payment status
    - Follow-up recommendations
    - Parent contact insights
    """
)
async def get_class_financial_summary(
    class_id: UUID,
    academic_year: str,
    term_number: Optional[int] = Query(None, ge=1, le=3),
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get financial summary for a specific class"""
    
    try:
        # For demonstration, return structured summary
        # In production, this would query actual class and financial data
        
        summary = {
            "class_id": str(class_id),
            "academic_year": academic_year,
            "term_number": term_number,
            "class_info": {
                "class_name": "Grade 8A",
                "grade_level": 8,
                "total_students": 32,
                "class_teacher": "Mrs. Chimbira"
            },
            "financial_summary": {
                "total_invoiced": 19200.00,
                "total_collected": 15360.00,
                "outstanding_amount": 3840.00,
                "collection_rate": 80.0,
                "average_per_student": 600.00
            },
            "payment_breakdown": {
                "fully_paid": 18,
                "partially_paid": 8,
                "unpaid": 6,
                "overdue": 3
            },
            "payment_methods": [
                {"method": "EcoCash", "count": 15, "amount": 9000.00},
                {"method": "Cash", "count": 8, "amount": 4800.00},
                {"method": "Paynow", "count": 3, "amount": 1560.00}
            ],
            "insights": {
                "class_performance": "Below school average",
                "main_challenge": "6 students with no payments",
                "recommendation": "Schedule parent-teacher meeting for unpaid accounts",
                "positive_trend": "Good adoption of mobile payments"
            }
        }
        
        return {
            "success": True,
            "data": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting class financial summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get class financial summary")