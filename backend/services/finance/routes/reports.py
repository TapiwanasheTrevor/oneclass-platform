# =====================================================
# Finance Reporting and Analytics Routes
# File: backend/services/finance/routes/reports.py
# =====================================================

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from shared.auth import get_current_active_user, EnhancedUser, require_permission, require_feature
from ..schemas import (
    FinanceDashboardResponse, FinancialSummaryResponse,
    CollectionReportRequest, CollectionReportResponse
)
from ..crud import FinancialReportingCRUD

router = APIRouter(prefix="/reports", tags=["financial-reports"])

# =====================================================
# DASHBOARD ENDPOINTS
# =====================================================

@router.get("/dashboard", response_model=FinanceDashboardResponse)
@require_permission("finance.read")
@require_feature("finance_module")
async def get_finance_dashboard(
    academic_year_id: Optional[UUID] = Query(None, description="Academic year filter"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get comprehensive finance dashboard data.
    Automatically filtered by school context.
    """
    # Use current academic year if not specified
    if not academic_year_id:
        academic_year_id = current_user.school_config.current_academic_year_id
    
    dashboard = await FinancialReportingCRUD.get_finance_dashboard(
        current_user.school_id,
        academic_year_id
    )
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "financial_reporting", "dashboard")
    
    return dashboard

@router.get("/dashboard/summary")
@require_permission("finance.read")
@require_feature("finance_module")
async def get_dashboard_summary(
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get quick dashboard summary metrics.
    Automatically filtered by school context.
    """
    summary = await FinancialReportingCRUD.get_dashboard_summary(current_user.school_id)
    
    return summary

# =====================================================
# COLLECTION REPORTS
# =====================================================

@router.post("/collection", response_model=CollectionReportResponse)
@require_permission("finance.read")
@require_feature("finance_module")
async def generate_collection_report(
    request: CollectionReportRequest,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Generate collection report for specified period.
    Automatically filtered by school context.
    """
    report = await FinancialReportingCRUD.generate_collection_report(
        current_user.school_id,
        request
    )
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "financial_reporting", "collection_report")
    
    return report

@router.get("/collection/summary")
@require_permission("finance.read")
@require_feature("finance_module")
async def get_collection_summary(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get collection summary for quick overview.
    Automatically filtered by school context.
    """
    summary = await FinancialReportingCRUD.get_collection_summary(
        current_user.school_id,
        start_date,
        end_date
    )
    
    return summary

# =====================================================
# OUTSTANDING BALANCES REPORTS
# =====================================================

@router.get("/outstanding-balances")
@require_permission("finance.read")
@require_feature("finance_module")
async def get_outstanding_balances_report(
    grade_level: Optional[int] = Query(None, ge=1, le=13, description="Filter by grade level"),
    class_id: Optional[UUID] = Query(None, description="Filter by class ID"),
    academic_year_id: Optional[UUID] = Query(None, description="Filter by academic year"),
    include_overdue_only: bool = Query(False, description="Include only overdue balances"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get outstanding balances report.
    Automatically filtered by school context.
    """
    report = await FinancialReportingCRUD.get_outstanding_balances_report(
        current_user.school_id,
        grade_level,
        class_id,
        academic_year_id,
        include_overdue_only
    )
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "financial_reporting", "outstanding_balances")
    
    return report

@router.get("/outstanding-balances/summary")
@require_permission("finance.read")
@require_feature("finance_module")
async def get_outstanding_balances_summary(
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get outstanding balances summary metrics.
    Automatically filtered by school context.
    """
    summary = await FinancialReportingCRUD.get_outstanding_balances_summary(
        current_user.school_id
    )
    
    return summary

# =====================================================
# REVENUE REPORTS
# =====================================================

@router.get("/revenue/monthly")
@require_permission("finance.read")
@require_feature("finance_module")
async def get_monthly_revenue_report(
    academic_year_id: Optional[UUID] = Query(None, description="Academic year filter"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get monthly revenue breakdown.
    Automatically filtered by school context.
    """
    report = await FinancialReportingCRUD.get_monthly_revenue_report(
        current_user.school_id,
        academic_year_id
    )
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "financial_reporting", "monthly_revenue")
    
    return report

@router.get("/revenue/by-category")
@require_permission("finance.read")
@require_feature("finance_module")
async def get_revenue_by_category(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get revenue breakdown by fee category.
    Automatically filtered by school context.
    """
    report = await FinancialReportingCRUD.get_revenue_by_category(
        current_user.school_id,
        start_date,
        end_date
    )
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "financial_reporting", "revenue_by_category")
    
    return report

@router.get("/revenue/by-grade")
@require_permission("finance.read")
@require_feature("finance_module")
async def get_revenue_by_grade(
    academic_year_id: Optional[UUID] = Query(None, description="Academic year filter"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get revenue breakdown by grade level.
    Automatically filtered by school context.
    """
    report = await FinancialReportingCRUD.get_revenue_by_grade(
        current_user.school_id,
        academic_year_id
    )
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "financial_reporting", "revenue_by_grade")
    
    return report

# =====================================================
# PAYMENT METHOD ANALYTICS
# =====================================================

@router.get("/payment-methods/usage")
@require_permission("finance.read")
@require_feature("finance_module")
async def get_payment_method_usage(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get payment method usage analytics.
    Automatically filtered by school context.
    """
    analytics = await FinancialReportingCRUD.get_payment_method_usage(
        current_user.school_id,
        start_date,
        end_date
    )
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "financial_reporting", "payment_method_usage")
    
    return analytics

@router.get("/payment-methods/trends")
@require_permission("finance.read")
@require_feature("finance_module")
async def get_payment_method_trends(
    academic_year_id: Optional[UUID] = Query(None, description="Academic year filter"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get payment method trends over time.
    Automatically filtered by school context.
    """
    trends = await FinancialReportingCRUD.get_payment_method_trends(
        current_user.school_id,
        academic_year_id
    )
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "financial_reporting", "payment_method_trends")
    
    return trends

# =====================================================
# STUDENT FINANCIAL ANALYTICS
# =====================================================

@router.get("/students/payment-behavior")
@require_permission("finance.read")
@require_feature("finance_module")
async def get_student_payment_behavior(
    grade_level: Optional[int] = Query(None, ge=1, le=13, description="Filter by grade level"),
    academic_year_id: Optional[UUID] = Query(None, description="Academic year filter"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get student payment behavior analytics.
    Automatically filtered by school context.
    """
    analytics = await FinancialReportingCRUD.get_student_payment_behavior(
        current_user.school_id,
        grade_level,
        academic_year_id
    )
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "financial_reporting", "payment_behavior")
    
    return analytics

@router.get("/students/top-debtors")
@require_permission("finance.read")
@require_feature("finance_module")
async def get_top_debtors(
    limit: int = Query(20, ge=1, le=100, description="Number of top debtors to return"),
    academic_year_id: Optional[UUID] = Query(None, description="Academic year filter"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get top debtors (students with highest outstanding balances).
    Automatically filtered by school context.
    """
    debtors = await FinancialReportingCRUD.get_top_debtors(
        current_user.school_id,
        limit,
        academic_year_id
    )
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "financial_reporting", "top_debtors")
    
    return debtors

# =====================================================
# FINANCIAL FORECASTING
# =====================================================

@router.get("/forecasting/revenue")
@require_permission("finance.read")
@require_feature("finance_module")
async def get_revenue_forecast(
    months_ahead: int = Query(6, ge=1, le=12, description="Months to forecast ahead"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get revenue forecasting based on historical data.
    Automatically filtered by school context.
    """
    forecast = await FinancialReportingCRUD.get_revenue_forecast(
        current_user.school_id,
        months_ahead
    )
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "financial_reporting", "revenue_forecast")
    
    return forecast

@router.get("/forecasting/collection-rate")
@require_permission("finance.read")
@require_feature("finance_module")
async def get_collection_rate_forecast(
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get collection rate forecasting.
    Automatically filtered by school context.
    """
    forecast = await FinancialReportingCRUD.get_collection_rate_forecast(
        current_user.school_id
    )
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "financial_reporting", "collection_rate_forecast")
    
    return forecast

# =====================================================
# EXPORT ENDPOINTS
# =====================================================

@router.get("/export/collection-report")
@require_permission("finance.read")
@require_feature("finance_module")
async def export_collection_report(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    format: str = Query("csv", description="Export format (csv, xlsx, pdf)"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Export collection report in specified format.
    Automatically filtered by school context.
    """
    if format not in ["csv", "xlsx", "pdf"]:
        raise HTTPException(status_code=400, detail="Invalid export format")
    
    # Generate export file
    file_content, filename, media_type = await FinancialReportingCRUD.export_collection_report(
        current_user.school_id,
        start_date,
        end_date,
        format
    )
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "financial_reporting", f"export_{format}")
    
    return Response(
        content=file_content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/export/outstanding-balances")
@require_permission("finance.read")
@require_feature("finance_module")
async def export_outstanding_balances(
    format: str = Query("csv", description="Export format (csv, xlsx, pdf)"),
    grade_level: Optional[int] = Query(None, ge=1, le=13, description="Filter by grade level"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Export outstanding balances report.
    Automatically filtered by school context.
    """
    if format not in ["csv", "xlsx", "pdf"]:
        raise HTTPException(status_code=400, detail="Invalid export format")
    
    # Generate export file
    file_content, filename, media_type = await FinancialReportingCRUD.export_outstanding_balances(
        current_user.school_id,
        format,
        grade_level
    )
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "financial_reporting", f"export_outstanding_{format}")
    
    return Response(
        content=file_content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/export/student-statements")
@require_permission("finance.read")
@require_feature("finance_module")
async def export_student_statements(
    student_ids: List[UUID] = Query(..., description="Student IDs to generate statements for"),
    academic_year_id: Optional[UUID] = Query(None, description="Academic year filter"),
    format: str = Query("pdf", description="Export format (pdf)"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Export student financial statements.
    Automatically validates school context.
    """
    if format not in ["pdf"]:
        raise HTTPException(status_code=400, detail="Invalid export format")
    
    # Verify all students belong to current school
    for student_id in student_ids:
        from ...sis.crud import StudentCRUD
        student = await StudentCRUD.get_student_by_id(student_id, current_user.school_id)
        if not student:
            raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    
    # Generate statements
    file_content, filename, media_type = await FinancialReportingCRUD.export_student_statements(
        student_ids,
        current_user.school_id,
        academic_year_id,
        format
    )
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "financial_reporting", f"export_statements_{format}")
    
    return Response(
        content=file_content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# =====================================================
# SCHEDULED REPORTS
# =====================================================

@router.post("/schedule/collection-report")
@require_permission("finance.admin")
@require_feature("finance_module")
async def schedule_collection_report(
    frequency: str = Query(..., description="Report frequency (daily, weekly, monthly)"),
    recipients: List[str] = Query(..., description="Email recipients"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Schedule automated collection report.
    Automatically sets school context.
    """
    if frequency not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Invalid frequency")
    
    # Validate email addresses
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    for email in recipients:
        if not re.match(email_pattern, email):
            raise HTTPException(status_code=400, detail=f"Invalid email address: {email}")
    
    schedule_id = await FinancialReportingCRUD.schedule_collection_report(
        current_user.school_id,
        frequency,
        recipients,
        current_user.id
    )
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "financial_reporting", "schedule_report")
    
    return {"schedule_id": schedule_id, "message": "Report scheduled successfully"}

@router.get("/schedule/active")
@require_permission("finance.admin")
@require_feature("finance_module")
async def get_active_schedules(
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get active report schedules.
    Automatically filtered by school context.
    """
    schedules = await FinancialReportingCRUD.get_active_schedules(current_user.school_id)
    
    return schedules

@router.delete("/schedule/{schedule_id}")
@require_permission("finance.admin")
@require_feature("finance_module")
async def cancel_scheduled_report(
    schedule_id: UUID,
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Cancel scheduled report.
    Automatically validates school context.
    """
    # Verify schedule belongs to current school
    schedule = await FinancialReportingCRUD.get_schedule_by_id(schedule_id, current_user.school_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Scheduled report not found")
    
    await FinancialReportingCRUD.cancel_scheduled_report(schedule_id)
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "financial_reporting", "cancel_schedule")
    
    return {"message": "Scheduled report cancelled successfully"}

# =====================================================
# AUDIT TRAIL ENDPOINTS
# =====================================================

@router.get("/audit/financial-changes")
@require_permission("finance.admin")
@require_feature("finance_module")
async def get_financial_audit_trail(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    current_user: EnhancedUser = Depends(get_current_active_user)
):
    """
    Get financial audit trail.
    Automatically filtered by school context.
    """
    audit_trail = await FinancialReportingCRUD.get_financial_audit_trail(
        current_user.school_id,
        start_date,
        end_date,
        user_id,
        action_type
    )
    
    # Track feature usage
    await track_feature_usage(current_user.school_id, "financial_reporting", "audit_trail")
    
    return audit_trail

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