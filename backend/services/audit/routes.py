"""
Audit Service API Routes
Provides REST endpoints for audit logging and reporting
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field

from .audit_service import AuditService, AuditLogRequest, AuditLogFilter, AuditReportRequest
from ..shared.models.audit_log import ActionCategory, ActionType, RiskLevel, ComplianceCategory
from ..shared.auth import get_current_user, get_current_school_context
from ..shared.database import get_async_session
from ..shared.models.unified_user import UnifiedUser, SchoolRole

import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()

# =====================================================
# API MODELS
# =====================================================

class CreateAuditLogRequest(BaseModel):
    """API request model for creating audit logs"""
    
    action_category: ActionCategory
    action_type: ActionType
    action_description: str
    risk_level: RiskLevel = RiskLevel.LOW
    
    # Optional context
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    
    # Additional metadata
    action_context: Optional[Dict[str, Any]] = None
    action_details: Optional[Dict[str, Any]] = None
    success: str = "success"
    error_message: Optional[str] = None
    compliance_categories: List[ComplianceCategory] = Field(default_factory=list)


class AuditLogResponse(BaseModel):
    """API response model for audit logs"""
    
    id: str
    timestamp: str
    school_name: str
    user: Dict[str, Any]
    action: Dict[str, Any]
    risk_level: str
    success: str
    resource: Optional[Dict[str, Any]] = None


class AuditLogsResponse(BaseModel):
    """API response for audit logs list"""
    
    audit_logs: List[Dict[str, Any]]
    total_count: int
    limit: int
    offset: int
    has_more: bool


class ActivitySummaryResponse(BaseModel):
    """API response for user activity summary"""
    
    user_id: str
    school_id: str
    period_days: int
    category_stats: Dict[str, int]
    risk_stats: Dict[str, int]
    total_activities: int
    high_risk_activities: List[Dict[str, Any]]


# =====================================================
# ROUTE DEFINITIONS
# =====================================================

router = APIRouter(prefix="/api/v1/audit", tags=["Audit & Compliance"])


@router.post("/logs", response_model=Dict[str, Any])
async def create_audit_log(
    request_data: CreateAuditLogRequest,
    current_user: UnifiedUser = Depends(get_current_user),
    school_context = Depends(get_current_school_context),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Create a new audit log entry
    
    This endpoint allows authorized users to create audit log entries
    for tracking important actions within the school system.
    """
    
    try:
        audit_service = AuditService(session)
        
        # Create audit log request
        audit_request = AuditLogRequest(
            school_id=str(school_context["school_id"]),
            user_id=str(current_user.id),
            action_category=request_data.action_category,
            action_type=request_data.action_type,
            action_description=request_data.action_description,
            risk_level=request_data.risk_level,
            resource_type=request_data.resource_type,
            resource_id=request_data.resource_id,
            resource_name=request_data.resource_name,
            action_context=request_data.action_context,
            action_details=request_data.action_details,
            success=request_data.success,
            error_message=request_data.error_message,
            compliance_categories=request_data.compliance_categories
        )
        
        # Create audit log
        audit_log = await audit_service.create_audit_log(audit_request)
        
        return {
            "message": "Audit log created successfully",
            "audit_log_id": str(audit_log.id),
            "timestamp": audit_log.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to create audit log: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create audit log: {str(e)}")


@router.get("/logs", response_model=AuditLogsResponse)
async def get_audit_logs(
    # Filters
    user_email: Optional[str] = Query(None, description="Filter by user email"),
    action_category: Optional[ActionCategory] = Query(None, description="Filter by action category"),
    action_type: Optional[ActionType] = Query(None, description="Filter by action type"),
    risk_level: Optional[RiskLevel] = Query(None, description="Filter by risk level"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    success: Optional[str] = Query(None, description="Filter by success status"),
    
    # Pagination
    limit: int = Query(50, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    
    # Sorting
    sort_by: str = Query("timestamp", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    
    # Dependencies
    current_user: UnifiedUser = Depends(get_current_user),
    school_context = Depends(get_current_school_context),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get audit logs with filtering and pagination
    
    This endpoint allows authorized users (principals and admins) to view
    audit logs for their school with comprehensive filtering options.
    """
    
    try:
        # Check permissions - only principals and admins can view audit logs
        user_role = school_context.get("user_role", "").lower()
        if user_role not in ["principal", "school_admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions to view audit logs")
        
        audit_service = AuditService(session)
        
        # Build filter
        filter_params = AuditLogFilter(
            school_id=str(school_context["school_id"]),
            user_email=user_email,
            action_category=action_category,
            action_type=action_type,
            risk_level=risk_level,
            resource_type=resource_type,
            start_date=start_date,
            end_date=end_date,
            success=success,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Get audit logs
        result = await audit_service.get_audit_logs(filter_params)
        
        return AuditLogsResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get audit logs: {str(e)}")


@router.get("/logs/{log_id}", response_model=Dict[str, Any])
async def get_audit_log_by_id(
    log_id: str,
    current_user: UnifiedUser = Depends(get_current_user),
    school_context = Depends(get_current_school_context),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get specific audit log by ID
    
    This endpoint allows authorized users to view detailed information
    about a specific audit log entry.
    """
    
    try:
        # Check permissions
        user_role = school_context.get("user_role", "").lower()
        if user_role not in ["principal", "school_admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions to view audit logs")
        
        audit_service = AuditService(session)
        
        # Get audit log
        audit_log = await audit_service.get_audit_log_by_id(log_id)
        
        if not audit_log:
            raise HTTPException(status_code=404, detail="Audit log not found")
        
        # Verify school access
        if str(audit_log.school_id) != str(school_context["school_id"]):
            raise HTTPException(status_code=403, detail="Access denied to this audit log")
        
        # Serialize and return
        return audit_service._serialize_audit_log(audit_log)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit log: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get audit log: {str(e)}")


@router.get("/users/{user_id}/activity", response_model=ActivitySummaryResponse)
async def get_user_activity_summary(
    user_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: UnifiedUser = Depends(get_current_user),
    school_context = Depends(get_current_school_context),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get activity summary for a specific user
    
    This endpoint provides a comprehensive activity summary for a user
    within the current school context.
    """
    
    try:
        # Check permissions
        user_role = school_context.get("user_role", "").lower()
        if user_role not in ["principal", "school_admin"]:
            # Users can view their own activity
            if str(current_user.id) != user_id:
                raise HTTPException(status_code=403, detail="Insufficient permissions to view user activity")
        
        audit_service = AuditService(session)
        
        # Get activity summary
        summary = await audit_service.get_user_activity_summary(
            user_id=user_id,
            school_id=str(school_context["school_id"]),
            days=days
        )
        
        return ActivitySummaryResponse(**summary)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user activity summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get user activity summary: {str(e)}")


@router.post("/reports/generate", response_model=Dict[str, Any])
async def generate_audit_report(
    report_type: str = Query(..., regex="^(daily|weekly|monthly|custom)$"),
    start_date: datetime = Query(..., description="Report start date"),
    end_date: datetime = Query(..., description="Report end date"),
    include_categories: List[ActionCategory] = Query([], description="Categories to include"),
    include_users: List[str] = Query([], description="Specific users to include"),
    risk_levels: List[RiskLevel] = Query([], description="Risk levels to include"),
    include_summaries: bool = Query(True, description="Include summary statistics"),
    include_details: bool = Query(False, description="Include detailed activities"),
    include_compliance: bool = Query(True, description="Include compliance information"),
    format: str = Query("json", regex="^(json|csv)$", description="Report format"),
    current_user: UnifiedUser = Depends(get_current_user),
    school_context = Depends(get_current_school_context),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Generate comprehensive audit report
    
    This endpoint generates detailed audit reports for compliance and
    operational oversight purposes.
    """
    
    try:
        # Check permissions - only principals and admins can generate reports
        user_role = school_context.get("user_role", "").lower()
        if user_role not in ["principal", "school_admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions to generate audit reports")
        
        # Validate date range
        if end_date <= start_date:
            raise HTTPException(status_code=400, detail="End date must be after start date")
        
        # Limit report range to prevent performance issues
        max_days = 365
        if (end_date - start_date).days > max_days:
            raise HTTPException(status_code=400, detail=f"Report range cannot exceed {max_days} days")
        
        audit_service = AuditService(session)
        
        # Create report request
        report_request = AuditReportRequest(
            school_id=str(school_context["school_id"]),
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            include_categories=include_categories,
            include_users=include_users,
            risk_levels=risk_levels,
            include_summaries=include_summaries,
            include_details=include_details,
            include_compliance=include_compliance,
            format=format
        )
        
        # Generate report
        report = await audit_service.generate_audit_report(report_request)
        
        # Add metadata
        report["metadata"] = {
            "requested_by": {
                "user_id": str(current_user.id),
                "email": current_user.email,
                "role": user_role
            },
            "school": {
                "id": str(school_context["school_id"]),
                "name": school_context.get("school_name", "Unknown")
            }
        }
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate audit report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate audit report: {str(e)}")


@router.get("/compliance/summary", response_model=Dict[str, Any])
async def get_compliance_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: UnifiedUser = Depends(get_current_user),
    school_context = Depends(get_current_school_context),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get compliance-focused summary
    
    This endpoint provides a summary of compliance-related activities
    and highlights areas that require attention.
    """
    
    try:
        # Check permissions
        user_role = school_context.get("user_role", "").lower()
        if user_role not in ["principal", "school_admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions to view compliance data")
        
        audit_service = AuditService(session)
        
        # Build report request for compliance
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        end_date = datetime.now(timezone.utc)
        
        report_request = AuditReportRequest(
            school_id=str(school_context["school_id"]),
            report_type="custom",
            start_date=start_date,
            end_date=end_date,
            include_summaries=True,
            include_details=False,
            include_compliance=True
        )
        
        # Generate compliance-focused report
        report = await audit_service.generate_audit_report(report_request)
        
        # Extract compliance summary
        compliance_summary = {
            "period_days": days,
            "school_id": str(school_context["school_id"]),
            "compliance_activities": report.get("compliance", {}),
            "overall_summary": report.get("summaries", {}),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        return compliance_summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get compliance summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get compliance summary: {str(e)}")


@router.get("/security/alerts", response_model=Dict[str, Any])
async def get_security_alerts(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    current_user: UnifiedUser = Depends(get_current_user),
    school_context = Depends(get_current_school_context),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get security alerts and high-risk activities
    
    This endpoint provides a focused view of security-related events
    that require administrator attention.
    """
    
    try:
        # Check permissions - only principals and admins
        user_role = school_context.get("user_role", "").lower()
        if user_role not in ["principal", "school_admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions to view security alerts")
        
        audit_service = AuditService(session)
        
        # Get high-risk activities
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        filter_params = AuditLogFilter(
            school_id=str(school_context["school_id"]),
            start_date=start_date,
            end_date=datetime.now(timezone.utc),
            risk_level=RiskLevel.HIGH,  # Start with high risk
            limit=100,
            sort_by="timestamp",
            sort_order="desc"
        )
        
        high_risk_result = await audit_service.get_audit_logs(filter_params)
        
        # Get critical risk activities
        filter_params.risk_level = RiskLevel.CRITICAL
        critical_risk_result = await audit_service.get_audit_logs(filter_params)
        
        # Get failed activities
        filter_params.risk_level = None
        filter_params.success = "failure"
        failed_activities_result = await audit_service.get_audit_logs(filter_params)
        
        return {
            "period_days": days,
            "school_id": str(school_context["school_id"]),
            "alerts": {
                "critical_risk_count": critical_risk_result["total_count"],
                "high_risk_count": high_risk_result["total_count"],
                "failed_activities_count": failed_activities_result["total_count"]
            },
            "recent_critical_activities": critical_risk_result["audit_logs"][:10],
            "recent_high_risk_activities": high_risk_result["audit_logs"][:10],
            "recent_failed_activities": failed_activities_result["audit_logs"][:10],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get security alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get security alerts: {str(e)}")


# =====================================================
# HEALTH CHECK
# =====================================================

@router.get("/health")
async def audit_service_health():
    """Health check for audit service"""
    return {
        "service": "audit",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }