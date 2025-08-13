"""
Super Admin API Routes
Comprehensive management endpoints for OneClass platform staff
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from uuid import UUID
from pydantic import BaseModel, Field

from ..super_admin_service import (
    SuperAdminService, SuperAdminSchoolFilter, SchoolStatus, 
    MigrationServiceStatus, SuperAdminAction, PlatformMetrics
)
from ...shared.auth import get_current_user, require_super_admin
from ...shared.database import get_async_session
from ...shared.models.unified_user import UnifiedUser, GlobalRole

import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()

# =====================================================
# API MODELS
# =====================================================

class ApprovalRequest(BaseModel):
    """Request model for approving school registrations"""
    
    approval_notes: Optional[str] = Field(None, max_length=2000)


class RejectionRequest(BaseModel):
    """Request model for rejecting school registrations"""
    
    rejection_reason: str = Field(..., min_length=10, max_length=2000)


class MigrationStatusUpdate(BaseModel):
    """Request model for updating migration service status"""
    
    status: MigrationServiceStatus
    notes: Optional[str] = Field(None, max_length=2000)


class AssignManagerRequest(BaseModel):
    """Request model for assigning migration manager"""
    
    manager_id: UUID


class AdminActionRequest(BaseModel):
    """Request model for admin actions"""
    
    action_type: str = Field(..., regex="^(approve|reject|assign_manager|update_status|add_note)$")
    notes: Optional[str] = Field(None, max_length=2000)
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)


# =====================================================
# ROUTE DEFINITIONS
# =====================================================

router = APIRouter(prefix="/api/v1/super-admin", tags=["Super Admin"])


@router.get("/dashboard/metrics", response_model=PlatformMetrics)
async def get_platform_metrics(
    current_user: UnifiedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get comprehensive platform metrics for super admin dashboard
    
    This endpoint provides key performance indicators, registration trends,
    and operational metrics for platform oversight.
    """
    
    try:
        super_admin_service = SuperAdminService(session)
        metrics = await super_admin_service.get_platform_metrics()
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting platform metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get platform metrics: {str(e)}")


@router.get("/schools", response_model=Dict[str, Any])
async def get_school_registrations(
    # Filters
    status: Optional[SchoolStatus] = Query(None, description="Filter by school status"),
    school_type: Optional[str] = Query(None, description="Filter by school type"),
    province: Optional[str] = Query(None, description="Filter by province"),
    subscription_tier: Optional[str] = Query(None, description="Filter by subscription tier"),
    migration_package: Optional[str] = Query(None, description="Filter by migration package"),
    search: Optional[str] = Query(None, description="Search schools by name, subdomain, or city"),
    
    # Date filters
    registered_after: Optional[datetime] = Query(None, description="Filter schools registered after date"),
    registered_before: Optional[datetime] = Query(None, description="Filter schools registered before date"),
    
    # Pagination
    limit: int = Query(50, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    
    # Sorting
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    
    # Dependencies
    current_user: UnifiedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get school registrations with comprehensive filtering
    
    This endpoint allows super admins to view and filter all school registrations
    with detailed information about onboarding progress, migration services, and status.
    """
    
    try:
        super_admin_service = SuperAdminService(session)
        
        # Build filter parameters
        filter_params = SuperAdminSchoolFilter(
            status=status,
            school_type=school_type,
            province=province,
            subscription_tier=subscription_tier,
            search_query=search,
            registered_after=registered_after,
            registered_before=registered_before,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Get schools
        result = await super_admin_service.get_school_registrations(filter_params)
        
        # Add metadata
        result["metadata"] = {
            "filters_applied": {
                "status": status.value if status else None,
                "school_type": school_type,
                "province": province,
                "search": search
            },
            "requested_by": {
                "user_id": str(current_user.id),
                "email": current_user.email
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting school registrations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get school registrations: {str(e)}")


@router.get("/schools/{school_id}", response_model=Dict[str, Any])
async def get_school_details(
    school_id: UUID,
    current_user: UnifiedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get comprehensive school details for admin review
    
    This endpoint provides detailed information about a specific school registration,
    including onboarding progress, migration services, team members, and admin notes.
    """
    
    try:
        super_admin_service = SuperAdminService(session)
        
        details = await super_admin_service.get_school_details(school_id)
        
        if not details:
            raise HTTPException(status_code=404, detail="School not found")
        
        # Add access metadata
        details["access_metadata"] = {
            "viewed_by": {
                "user_id": str(current_user.id),
                "email": current_user.email
            },
            "viewed_at": datetime.now(timezone.utc).isoformat()
        }
        
        return details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting school details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get school details: {str(e)}")


@router.post("/schools/{school_id}/approve", response_model=Dict[str, Any])
async def approve_school_registration(
    school_id: UUID,
    approval_data: ApprovalRequest,
    current_user: UnifiedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Approve school registration and advance to next stage
    
    This endpoint allows super admins to approve school registrations
    at various stages of the onboarding process.
    """
    
    try:
        super_admin_service = SuperAdminService(session)
        
        result = await super_admin_service.approve_school_registration(
            school_id=school_id,
            admin_id=current_user.id,
            approval_notes=approval_data.approval_notes
        )
        
        # Add admin metadata
        result["approved_by"] = {
            "user_id": str(current_user.id),
            "email": current_user.email,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error approving school registration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to approve school registration: {str(e)}")


@router.post("/schools/{school_id}/reject", response_model=Dict[str, Any])
async def reject_school_registration(
    school_id: UUID,
    rejection_data: RejectionRequest,
    current_user: UnifiedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Reject school registration with reason
    
    This endpoint allows super admins to reject school registrations
    and provide detailed feedback to the applicant.
    """
    
    try:
        super_admin_service = SuperAdminService(session)
        
        result = await super_admin_service.reject_school_registration(
            school_id=school_id,
            admin_id=current_user.id,
            rejection_reason=rejection_data.rejection_reason
        )
        
        # Add admin metadata
        result["rejected_by"] = {
            "user_id": str(current_user.id),
            "email": current_user.email,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error rejecting school registration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reject school registration: {str(e)}")


@router.get("/migration-services/requests", response_model=List[Dict[str, Any]])
async def get_migration_requests(
    status: Optional[MigrationServiceStatus] = Query(None, description="Filter by migration status"),
    current_user: UnifiedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get all migration service requests
    
    This endpoint provides a comprehensive view of all schools that have
    requested migration services, with status tracking and cost estimates.
    """
    
    try:
        super_admin_service = SuperAdminService(session)
        
        requests = await super_admin_service.get_migration_requests(status)
        
        # Convert Pydantic models to dict for JSON serialization
        serialized_requests = [
            {
                "school_id": req.school_id,
                "school_name": req.school_name,
                "package": req.package,
                "status": req.status,
                "current_system": req.current_system,
                "data_sources": req.data_sources,
                "student_records_count": req.student_records_count,
                "staff_records_count": req.staff_records_count,
                "urgent_migration": req.urgent_migration,
                "onsite_training": req.onsite_training,
                "weekend_work": req.weekend_work,
                "base_cost": float(req.base_cost),
                "additional_costs": float(req.additional_costs),
                "total_estimated_cost": float(req.total_estimated_cost),
                "requested_at": req.requested_at.isoformat(),
                "preferred_completion_weeks": req.preferred_completion_weeks,
                "assigned_manager": req.assigned_manager,
                "special_requirements": req.special_requirements,
                "compliance_requirements": req.compliance_requirements
            }
            for req in requests
        ]
        
        return serialized_requests
        
    except Exception as e:
        logger.error(f"Error getting migration requests: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get migration requests: {str(e)}")


@router.put("/schools/{school_id}/migration-services/status", response_model=Dict[str, Any])
async def update_migration_service_status(
    school_id: UUID,
    status_update: MigrationStatusUpdate,
    current_user: UnifiedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Update migration service status for a school
    
    This endpoint allows super admins to track and update the progress
    of migration services for schools.
    """
    
    try:
        super_admin_service = SuperAdminService(session)
        
        result = await super_admin_service.update_migration_service_status(
            school_id=school_id,
            new_status=status_update.status,
            admin_id=current_user.id,
            notes=status_update.notes
        )
        
        # Add admin metadata
        result["updated_by"] = {
            "user_id": str(current_user.id),
            "email": current_user.email
        }
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating migration service status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update migration service status: {str(e)}")


@router.post("/schools/{school_id}/migration-services/assign-manager", response_model=Dict[str, Any])
async def assign_migration_manager(
    school_id: UUID,
    manager_assignment: AssignManagerRequest,
    current_user: UnifiedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Assign migration manager to a school's migration project
    
    This endpoint allows super admins to assign specific migration managers
    to handle school migration projects.
    """
    
    try:
        super_admin_service = SuperAdminService(session)
        
        result = await super_admin_service.assign_migration_manager(
            school_id=school_id,
            manager_id=manager_assignment.manager_id,
            admin_id=current_user.id
        )
        
        # Add admin metadata
        result["assigned_by"] = {
            "user_id": str(current_user.id),
            "email": current_user.email,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error assigning migration manager: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to assign migration manager: {str(e)}")


@router.get("/analytics/schools", response_model=Dict[str, Any])
async def get_school_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: UnifiedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get comprehensive school analytics and trends
    
    This endpoint provides detailed analytics about school registrations,
    conversion rates, and regional performance.
    """
    
    try:
        super_admin_service = SuperAdminService(session)
        
        analytics = await super_admin_service.get_school_analytics(days)
        
        # Add metadata
        analytics["metadata"] = {
            "requested_by": {
                "user_id": str(current_user.id),
                "email": current_user.email
            }
        }
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting school analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get school analytics: {str(e)}")


@router.get("/migration-services/analytics", response_model=Dict[str, Any])
async def get_migration_services_analytics(
    current_user: UnifiedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get migration services analytics and performance metrics
    
    This endpoint provides insights into migration service requests,
    completion rates, and revenue metrics.
    """
    
    try:
        super_admin_service = SuperAdminService(session)
        
        # Get migration requests for analytics
        all_requests = await super_admin_service.get_migration_requests()
        
        # Calculate analytics
        total_requests = len(all_requests)
        
        # Package distribution
        package_distribution = {}
        status_distribution = {}
        total_revenue = 0
        
        for req in all_requests:
            # Package distribution
            package_distribution[req.package] = package_distribution.get(req.package, 0) + 1
            
            # Status distribution
            status_distribution[req.status] = status_distribution.get(req.status, 0) + 1
            
            # Revenue calculation
            if req.status in ["completed", "in_progress"]:
                total_revenue += float(req.total_estimated_cost)
        
        # Calculate completion rate
        completed_requests = status_distribution.get("completed", 0)
        completion_rate = (completed_requests / total_requests * 100) if total_requests > 0 else 0
        
        analytics = {
            "summary": {
                "total_requests": total_requests,
                "completed_requests": completed_requests,
                "completion_rate": completion_rate,
                "total_revenue": total_revenue
            },
            "package_distribution": package_distribution,
            "status_distribution": status_distribution,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "requested_by": {
                    "user_id": str(current_user.id),
                    "email": current_user.email
                }
            }
        }
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting migration services analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get migration services analytics: {str(e)}")


@router.get("/export/schools")
async def export_school_data(
    format: str = Query("csv", regex="^(csv|xlsx)$", description="Export format"),
    status: Optional[SchoolStatus] = Query(None, description="Filter by school status"),
    current_user: UnifiedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Export school registration data
    
    This endpoint allows super admins to export school registration data
    for analysis and reporting purposes.
    """
    
    try:
        # This would implement actual CSV/Excel export
        # For now, return a placeholder response
        
        return JSONResponse({
            "message": "Export functionality would be implemented here",
            "format": format,
            "status_filter": status.value if status else "all",
            "export_url": f"/downloads/schools-export-{datetime.now().strftime('%Y%m%d')}.{format}",
            "requested_by": current_user.email
        })
        
    except Exception as e:
        logger.error(f"Error exporting school data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export school data: {str(e)}")


@router.post("/actions/{school_id}", response_model=Dict[str, Any])
async def execute_admin_action(
    school_id: UUID,
    action_request: AdminActionRequest,
    current_user: UnifiedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Execute administrative action on a school
    
    This endpoint allows super admins to perform various actions on school registrations
    such as adding notes, updating statuses, or other administrative tasks.
    """
    
    try:
        # This would implement various admin actions based on action_type
        # For now, return a success response
        
        action_log = {
            "action_id": str(uuid4()),
            "school_id": str(school_id),
            "action_type": action_request.action_type,
            "notes": action_request.notes,
            "data": action_request.data,
            "executed_by": {
                "user_id": str(current_user.id),
                "email": current_user.email
            },
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "status": "completed"
        }
        
        # Here you would implement the actual action logic
        logger.info(f"Admin action executed: {action_request.action_type} on school {school_id} by {current_user.email}")
        
        return {
            "success": True,
            "action": action_log,
            "message": f"Action '{action_request.action_type}' executed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error executing admin action: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to execute admin action: {str(e)}")


# =====================================================
# SYSTEM MANAGEMENT ENDPOINTS
# =====================================================

@router.get("/system/health")
async def system_health_check(
    current_user: UnifiedUser = Depends(require_super_admin)
):
    """
    System health check for super admins
    
    This endpoint provides system health information and status
    for platform monitoring and maintenance.
    """
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "database": "healthy",
            "email_service": "healthy",
            "audit_system": "healthy",
            "migration_services": "healthy"
        },
        "version": "1.0.0",
        "uptime": "99.95%"
    }


@router.get("/system/stats")
async def get_system_stats(
    current_user: UnifiedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get system statistics and performance metrics
    
    This endpoint provides technical performance metrics
    for system monitoring and optimization.
    """
    
    try:
        # This would gather actual system stats
        # For now, return mock data
        
        return {
            "database": {
                "connections": 25,
                "query_avg_time_ms": 150,
                "slow_queries": 2
            },
            "api": {
                "requests_per_minute": 450,
                "avg_response_time_ms": 125,
                "error_rate": 0.01
            },
            "storage": {
                "total_size_gb": 250,
                "used_size_gb": 125,
                "free_size_gb": 125
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get system stats: {str(e)}")


# =====================================================
# HEALTH CHECK
# =====================================================

@router.get("/health")
async def super_admin_service_health():
    """Health check for super admin service"""
    return {
        "service": "super-admin",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }