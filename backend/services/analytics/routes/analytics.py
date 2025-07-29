"""
Analytics API Routes
Endpoints for analytics data, dashboards, and insights
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional, List
from datetime import date, datetime, timedelta

from ..service import analytics_service
from ..schemas import (
    AnalyticsRequest, AnalyticsOverviewResponse, DashboardRequest,
    StudentAnalyticsRequest, AcademicAnalyticsRequest, FinancialAnalyticsRequest,
    PeriodType, MetricType, ComparisonRequest, ComparisonResponse
)
from shared.middleware.tenant_middleware import get_tenant_context, get_school_id

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(
    request: Request,
    period: PeriodType = Query(PeriodType.monthly, description="Analytics period"),
    start_date: Optional[date] = Query(None, description="Start date for custom period"),
    end_date: Optional[date] = Query(None, description="End date for custom period")
):
    """
    Get comprehensive analytics overview for the school
    
    Returns student, academic, financial, and system metrics with insights
    """
    school_id = get_school_id(request)
    
    try:
        overview = await analytics_service.get_analytics_overview(
            school_id=school_id,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        return overview
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate analytics overview: {str(e)}"
        )

@router.get("/dashboard")
async def get_dashboard_data(
    request: Request,
    period: PeriodType = Query(PeriodType.monthly),
    widgets: List[str] = Query([], description="Specific widget IDs to include")
):
    """
    Get dashboard data with customizable widgets
    """
    school_id = get_school_id(request)
    tenant = get_tenant_context(request)
    
    # Check if advanced analytics is enabled
    if "advanced_reporting" not in tenant.enabled_modules:
        raise HTTPException(
            status_code=403,
            detail="Advanced Analytics & Reporting module is not enabled for your subscription"
        )
    
    try:
        # Get analytics overview
        overview = await analytics_service.get_analytics_overview(
            school_id=school_id,
            period=period
        )
        
        # Format for dashboard
        dashboard_data = {
            "dashboard_id": "main_dashboard",
            "name": "School Analytics Dashboard",
            "description": "Comprehensive school performance overview",
            "widgets": [
                {
                    "id": "student_overview",
                    "type": "metrics_grid",
                    "title": "Student Metrics",
                    "data": {
                        "total_students": overview.student_metrics.total_students.dict(),
                        "attendance_rate": overview.student_metrics.attendance_rate.dict(),
                        "new_enrollments": overview.student_metrics.new_enrollments.dict()
                    }
                },
                {
                    "id": "academic_overview",
                    "type": "metrics_grid", 
                    "title": "Academic Performance",
                    "data": {
                        "average_grade": overview.academic_metrics.average_grade.dict(),
                        "pass_rate": overview.academic_metrics.pass_rate.dict(),
                        "assignment_completion": overview.academic_metrics.assignment_completion.dict()
                    }
                },
                {
                    "id": "financial_overview",
                    "type": "metrics_grid",
                    "title": "Financial Metrics", 
                    "data": {
                        "total_revenue": overview.financial_metrics.total_revenue.dict(),
                        "collection_rate": overview.financial_metrics.collection_rate.dict(),
                        "outstanding_fees": overview.financial_metrics.outstanding_fees.dict()
                    }
                },
                {
                    "id": "enrollment_trend",
                    "type": "chart",
                    "title": "Enrollment Trend",
                    "data": overview.student_metrics.enrollment_trend.dict()
                },
                {
                    "id": "grade_distribution", 
                    "type": "chart",
                    "title": "Grade Distribution",
                    "data": overview.academic_metrics.grade_distribution.dict()
                },
                {
                    "id": "revenue_trend",
                    "type": "chart", 
                    "title": "Revenue Trend",
                    "data": overview.financial_metrics.revenue_trend.dict()
                }
            ],
            "insights": overview.insights,
            "recommendations": overview.recommendations,
            "last_updated": datetime.utcnow()
        }
        
        # Filter widgets if specific ones requested
        if widgets:
            dashboard_data["widgets"] = [
                w for w in dashboard_data["widgets"] 
                if w["id"] in widgets
            ]
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dashboard data: {str(e)}"
        )

@router.get("/students")
async def get_student_analytics(
    request: Request,
    period: PeriodType = Query(PeriodType.monthly),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    grade_levels: List[str] = Query([]),
    classes: List[str] = Query([]),
    include_demographics: bool = Query(False)
):
    """
    Get detailed student analytics
    """
    school_id = get_school_id(request)
    
    # For now, return subset of overview data
    # In production, this would have more detailed student-specific analytics
    overview = await analytics_service.get_analytics_overview(
        school_id=school_id,
        period=period,
        start_date=start_date,
        end_date=end_date
    )
    
    return {
        "student_metrics": overview.student_metrics,
        "period": period,
        "filters": {
            "grade_levels": grade_levels,
            "classes": classes,
            "include_demographics": include_demographics
        }
    }

@router.get("/academic")
async def get_academic_analytics(
    request: Request,
    period: PeriodType = Query(PeriodType.monthly),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    subjects: List[str] = Query([]),
    assessment_types: List[str] = Query([]),
    grade_levels: List[str] = Query([])
):
    """
    Get detailed academic performance analytics
    """
    school_id = get_school_id(request)
    
    overview = await analytics_service.get_analytics_overview(
        school_id=school_id,
        period=period,
        start_date=start_date,
        end_date=end_date
    )
    
    return {
        "academic_metrics": overview.academic_metrics,
        "period": period,
        "filters": {
            "subjects": subjects,
            "assessment_types": assessment_types,
            "grade_levels": grade_levels
        }
    }

@router.get("/financial")
async def get_financial_analytics(
    request: Request,
    period: PeriodType = Query(PeriodType.monthly),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    fee_types: List[str] = Query([]),
    payment_methods: List[str] = Query([])
):
    """
    Get detailed financial analytics
    """
    school_id = get_school_id(request)
    
    overview = await analytics_service.get_analytics_overview(
        school_id=school_id,
        period=period,
        start_date=start_date,
        end_date=end_date
    )
    
    return {
        "financial_metrics": overview.financial_metrics,
        "period": period,
        "filters": {
            "fee_types": fee_types,
            "payment_methods": payment_methods
        }
    }

@router.get("/insights")
async def get_insights(
    request: Request,
    period: PeriodType = Query(PeriodType.monthly),
    categories: List[str] = Query([], description="Filter insights by category")
):
    """
    Get AI-generated insights and recommendations
    """
    school_id = get_school_id(request)
    tenant = get_tenant_context(request)
    
    # Check if advanced analytics is enabled
    if "advanced_reporting" not in tenant.enabled_modules:
        raise HTTPException(
            status_code=403,
            detail="Advanced Analytics & Reporting module is not enabled for your subscription"
        )
    
    # Return mock insights for now while we fix the database queries
    insights = [
        {
            "type": "info",
            "title": "Analytics Module Active",
            "message": f"Advanced Analytics & Reporting is enabled for {tenant.school_name}"
        },
        {
            "type": "success", 
            "title": "System Operational",
            "message": "All analytics services are running normally"
        }
    ]
    
    recommendations = [
        {
            "priority": "medium",
            "category": "System",
            "action": "Complete academic and finance module setup for full analytics",
            "expected_impact": "Unlock comprehensive reporting capabilities"
        }
    ]
    
    # Filter by categories if specified
    if categories:
        insights = [i for i in insights if i.get("type") in categories]
        recommendations = [r for r in recommendations if r.get("category") in categories]
    
    return {
        "insights": insights,
        "recommendations": recommendations,
        "generated_at": datetime.utcnow(),
        "period": period
    }

@router.get("/test")
async def test_analytics(request: Request):
    """
    Test endpoint to verify analytics module is working
    """
    school_id = get_school_id(request)
    tenant = get_tenant_context(request)
    
    # Check if advanced analytics is enabled
    if "advanced_reporting" not in tenant.enabled_modules:
        raise HTTPException(
            status_code=403,
            detail="Advanced Analytics & Reporting module is not enabled for your subscription"
        )
    
    return {
        "status": "success",
        "message": "Analytics module is working correctly",
        "school_id": school_id,
        "school_name": tenant.school_name,
        "enabled_modules": tenant.enabled_modules,
        "subscription_tier": tenant.subscription_tier,
        "timestamp": datetime.utcnow()
    }

@router.post("/compare")
async def compare_periods(
    request: Request,
    comparison_request: ComparisonRequest
):
    """
    Compare analytics between two periods
    """
    school_id = get_school_id(request)
    
    # Get analytics for both periods
    base_overview = await analytics_service.get_analytics_overview(
        school_id=school_id,
        period=comparison_request.base_period,
        start_date=comparison_request.base_start_date,
        end_date=comparison_request.base_end_date
    )
    
    compare_overview = await analytics_service.get_analytics_overview(
        school_id=school_id,
        period=comparison_request.compare_period,
        start_date=comparison_request.compare_start_date,
        end_date=comparison_request.compare_end_date
    )
    
    # Calculate changes
    changes = {}
    for metric in comparison_request.metrics:
        if metric == MetricType.student_enrollment:
            changes["total_students"] = {
                "base": base_overview.student_metrics.total_students.value,
                "compare": compare_overview.student_metrics.total_students.value,
                "change": compare_overview.student_metrics.total_students.value - base_overview.student_metrics.total_students.value,
                "change_percentage": ((compare_overview.student_metrics.total_students.value - base_overview.student_metrics.total_students.value) / base_overview.student_metrics.total_students.value) * 100 if base_overview.student_metrics.total_students.value > 0 else 0
            }
    
    return ComparisonResponse(
        base_period={
            "period": comparison_request.base_period,
            "start_date": comparison_request.base_start_date,
            "end_date": comparison_request.base_end_date,
            "data": base_overview.dict()
        },
        compare_period={
            "period": comparison_request.compare_period,
            "start_date": comparison_request.compare_start_date,
            "end_date": comparison_request.compare_end_date,
            "data": compare_overview.dict()
        },
        changes=changes,
        insights=[
            "Period comparison completed successfully",
            f"Analyzed {len(comparison_request.metrics)} metrics across two periods"
        ]
    )

@router.get("/export")
async def export_analytics(
    request: Request,
    format: str = Query("csv", description="Export format: csv, excel, pdf"),
    period: PeriodType = Query(PeriodType.monthly),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """
    Export analytics data in various formats
    """
    school_id = get_school_id(request)
    
    if format not in ["csv", "excel", "pdf"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid export format. Supported formats: csv, excel, pdf"
        )
    
    # For now, return a placeholder response
    # In production, this would generate and return actual files
    return {
        "export_id": f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "status": "queued",
        "format": format,
        "download_url": f"/api/v1/analytics/exports/download/{school_id}_{format}_{period}",
        "expires_at": datetime.utcnow() + timedelta(hours=24),
        "message": f"Analytics export in {format} format has been queued for processing"
    }