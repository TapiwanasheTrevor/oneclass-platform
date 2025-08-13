"""
Tenant Management Dashboard API Routes
Platform admin interface for managing all tenants
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from shared.database import get_async_session
from shared.auth import verify_platform_admin_access
from shared.models.platform_user import PlatformUser
from ..tenant_management_service import (
    TenantManagementService,
    TenantSummary,
    TenantDetail,
    TenantHealthCheck,
    BulkOperationRequest,
    SubscriptionUpdateRequest,
    TenantHealth,
    ActionType,
    SubscriptionAction
)

router = APIRouter(prefix="/api/v1/platform/tenant-management", tags=["tenant-management"])
logger = logging.getLogger(__name__)


# =====================================================
# TENANT OVERVIEW ROUTES
# =====================================================

@router.get("/tenants", response_model=Dict[str, Any])
async def get_all_tenants(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    tier_filter: Optional[str] = Query(None, description="Filter by subscription tier"),
    health_filter: Optional[TenantHealth] = Query(None, description="Filter by health status"),
    search_query: Optional[str] = Query(None, description="Search by name or subdomain"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: PlatformUser = Depends(verify_platform_admin_access),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get all tenants with filtering and pagination
    Platform admin only
    """
    try:
        service = TenantManagementService(db)
        
        tenants, total = await service.get_all_tenants(
            status_filter=status_filter,
            tier_filter=tier_filter,
            health_filter=health_filter,
            search_query=search_query,
            limit=limit,
            offset=offset
        )
        
        # Convert to dict format for response
        tenant_list = [tenant.dict() for tenant in tenants]
        
        return {
            "tenants": tenant_list,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
        
    except Exception as e:
        logger.error(f"Error getting tenants: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tenants"
        )


@router.get("/tenants/{school_id}", response_model=TenantDetail)
async def get_tenant_detail(
    school_id: UUID,
    current_user: PlatformUser = Depends(verify_platform_admin_access),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get detailed information for a specific tenant
    Platform admin only
    """
    try:
        service = TenantManagementService(db)
        
        tenant_detail = await service.get_tenant_detail(school_id)
        
        if not tenant_detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        return tenant_detail
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tenant detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tenant detail"
        )


@router.get("/tenants/{school_id}/health", response_model=TenantHealthCheck)
async def get_tenant_health(
    school_id: UUID,
    current_user: PlatformUser = Depends(verify_platform_admin_access),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Perform health check for a specific tenant
    Platform admin only
    """
    try:
        service = TenantManagementService(db)
        
        health_check = await service.perform_tenant_health_check(school_id)
        
        return health_check
        
    except Exception as e:
        logger.error(f"Error performing health check: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform health check"
        )


# =====================================================
# TENANT OPERATIONS ROUTES
# =====================================================

@router.post("/tenants/{school_id}/activate")
async def activate_tenant(
    school_id: UUID,
    activation_notes: Optional[str] = None,
    current_user: PlatformUser = Depends(verify_platform_admin_access),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Activate a tenant
    Platform admin only
    """
    try:
        service = TenantManagementService(db)
        
        result = await service.activate_tenant(
            school_id, current_user.id, activation_notes
        )
        
        logger.info(f"Tenant activated by admin {current_user.id}: {school_id}")
        
        return {
            "success": True,
            "message": "Tenant activated successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error activating tenant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate tenant"
        )


@router.post("/tenants/{school_id}/suspend")
async def suspend_tenant(
    school_id: UUID,
    suspension_reason: str,
    suspension_duration_days: Optional[int] = None,
    current_user: PlatformUser = Depends(verify_platform_admin_access),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Suspend a tenant
    Platform admin only
    """
    try:
        if not suspension_reason.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Suspension reason is required"
            )
        
        service = TenantManagementService(db)
        
        result = await service.suspend_tenant(
            school_id, current_user.id, suspension_reason, suspension_duration_days
        )
        
        logger.info(f"Tenant suspended by admin {current_user.id}: {school_id}")
        
        return {
            "success": True,
            "message": "Tenant suspended successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error suspending tenant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend tenant"
        )


@router.post("/tenants/{school_id}/subscription/update")
async def update_tenant_subscription(
    school_id: UUID,
    update_request: SubscriptionUpdateRequest,
    current_user: PlatformUser = Depends(verify_platform_admin_access),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Update tenant subscription
    Platform admin only
    """
    try:
        service = TenantManagementService(db)
        
        result = await service.update_tenant_subscription(
            school_id, current_user.id, update_request
        )
        
        logger.info(f"Subscription updated by admin {current_user.id}: {school_id}")
        
        return {
            "success": True,
            "message": "Subscription updated successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subscription"
        )


@router.post("/bulk-operations")
async def perform_bulk_operation(
    bulk_request: BulkOperationRequest,
    current_user: PlatformUser = Depends(verify_platform_admin_access),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Perform bulk operation on multiple tenants
    Platform admin only
    """
    try:
        if not bulk_request.school_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one school ID is required"
            )
        
        if len(bulk_request.school_ids) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot perform bulk operation on more than 100 schools at once"
            )
        
        service = TenantManagementService(db)
        
        result = await service.perform_bulk_operation(
            current_user.id, bulk_request
        )
        
        logger.info(f"Bulk operation performed by admin {current_user.id}: {bulk_request.operation_type}")
        
        return {
            "success": True,
            "message": "Bulk operation completed",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error performing bulk operation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk operation"
        )


# =====================================================
# ANALYTICS AND REPORTING ROUTES
# =====================================================

@router.get("/analytics")
async def get_platform_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    current_user: PlatformUser = Depends(verify_platform_admin_access),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get platform-wide analytics
    Platform admin only
    """
    try:
        # Default to last 30 days if dates not provided
        if not end_date:
            end_date = datetime.now(timezone.utc)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        service = TenantManagementService(db)
        
        analytics = await service.get_platform_analytics(start_date, end_date)
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "analytics": analytics
        }
        
    except Exception as e:
        logger.error(f"Error getting platform analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get platform analytics"
        )


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    current_user: PlatformUser = Depends(verify_platform_admin_access),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get dashboard summary statistics
    Platform admin only
    """
    try:
        # Get basic tenant counts
        tenant_counts_query = """
            SELECT 
                COUNT(*) as total_tenants,
                COUNT(*) FILTER (WHERE status = 'active') as active_tenants,
                COUNT(*) FILTER (WHERE status = 'suspended') as suspended_tenants,
                COUNT(*) FILTER (WHERE status IN ('pending_verification', 'email_verified', 'documents_approved')) as pending_tenants
            FROM platform.schools
        """
        
        result = await db.execute(tenant_counts_query)
        counts = result.fetchone()
        
        # Get subscription distribution
        subscription_query = """
            SELECT 
                tier,
                COUNT(*) as count
            FROM platform.school_subscriptions
            WHERE status = 'active'
            GROUP BY tier
        """
        
        sub_result = await db.execute(subscription_query)
        subscription_distribution = {row.tier: row.count for row in sub_result}
        
        # Get recent activity
        recent_activity_query = """
            SELECT 
                COUNT(DISTINCT sm.user_id) as active_users_today,
                COUNT(DISTINCT sm.school_id) as active_schools_today
            FROM platform.school_memberships sm
            JOIN platform.user_sessions us ON sm.user_id = us.user_id
            WHERE us.last_activity_at > NOW() - INTERVAL '1 day'
        """
        
        activity_result = await db.execute(recent_activity_query)
        activity = activity_result.fetchone()
        
        # Calculate health distribution (simplified)
        health_distribution = {
            "healthy": counts.active_tenants,
            "warning": 0,
            "critical": counts.suspended_tenants,
            "inactive": counts.pending_tenants
        }
        
        return {
            "tenant_counts": {
                "total": counts.total_tenants,
                "active": counts.active_tenants,
                "suspended": counts.suspended_tenants,
                "pending": counts.pending_tenants
            },
            "subscription_distribution": subscription_distribution,
            "health_distribution": health_distribution,
            "recent_activity": {
                "active_users_today": activity.active_users_today or 0,
                "active_schools_today": activity.active_schools_today or 0
            },
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard summary"
        )


# =====================================================
# TENANT SEARCH AND DISCOVERY
# =====================================================

@router.get("/search")
async def search_tenants(
    q: str = Query(..., min_length=2, description="Search query"),
    filters: Optional[str] = Query(None, description="JSON string of additional filters"),
    limit: int = Query(20, ge=1, le=50),
    current_user: PlatformUser = Depends(verify_platform_admin_access),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Search tenants by various criteria
    Platform admin only
    """
    try:
        search_query = """
            SELECT 
                s.id,
                s.name,
                s.subdomain,
                s.status,
                s.city,
                s.province,
                sub.tier as subscription_tier,
                s.created_at
            FROM platform.schools s
            LEFT JOIN platform.school_subscriptions sub ON s.id = sub.school_id
            WHERE (
                s.name ILIKE :search_term OR 
                s.subdomain ILIKE :search_term OR
                s.city ILIKE :search_term OR
                s.province ILIKE :search_term
            )
            ORDER BY 
                CASE WHEN s.name ILIKE :exact_search THEN 1 ELSE 2 END,
                s.name
            LIMIT :limit
        """
        
        search_term = f"%{q}%"
        exact_search = f"%{q}%"
        
        result = await db.execute(search_query, {
            "search_term": search_term,
            "exact_search": exact_search,
            "limit": limit
        })
        
        tenants = []
        for row in result:
            tenants.append({
                "id": str(row.id),
                "name": row.name,
                "subdomain": row.subdomain,
                "status": row.status,
                "location": f"{row.city}, {row.province}" if row.city and row.province else row.city or row.province or "",
                "subscription_tier": row.subscription_tier or "basic",
                "created_at": row.created_at.isoformat()
            })
        
        return {
            "query": q,
            "results": tenants,
            "count": len(tenants),
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error searching tenants: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search tenants"
        )


# =====================================================
# TENANT MONITORING ROUTES
# =====================================================

@router.get("/monitoring/alerts")
async def get_tenant_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: critical, warning, info"),
    limit: int = Query(50, ge=1, le=100),
    current_user: PlatformUser = Depends(verify_platform_admin_access),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get tenant monitoring alerts
    Platform admin only
    """
    try:
        # This would integrate with a monitoring system
        # For now, return sample data structure
        
        alerts = []
        
        # Check for inactive tenants
        inactive_query = """
            SELECT s.id, s.name, s.subdomain
            FROM platform.schools s
            LEFT JOIN platform.user_sessions us ON us.current_school_id = s.id
            WHERE s.status = 'active'
            AND (us.last_activity_at IS NULL OR us.last_activity_at < NOW() - INTERVAL '7 days')
            GROUP BY s.id, s.name, s.subdomain
            LIMIT 10
        """
        
        result = await db.execute(inactive_query)
        for row in result:
            alerts.append({
                "id": str(uuid4()),
                "school_id": str(row.id),
                "school_name": row.name,
                "severity": "warning",
                "type": "inactivity",
                "message": f"School {row.name} has been inactive for more than 7 days",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        
        # Filter by severity if provided
        if severity:
            alerts = [alert for alert in alerts if alert["severity"] == severity]
        
        return {
            "alerts": alerts[:limit],
            "total": len(alerts),
            "severity_filter": severity
        }
        
    except Exception as e:
        logger.error(f"Error getting tenant alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tenant alerts"
        )


@router.get("/monitoring/metrics")
async def get_monitoring_metrics(
    current_user: PlatformUser = Depends(verify_platform_admin_access),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get real-time monitoring metrics
    Platform admin only
    """
    try:
        # Get system-wide metrics
        metrics_query = """
            SELECT 
                COUNT(DISTINCT s.id) as total_schools,
                COUNT(DISTINCT sm.user_id) as total_users,
                COUNT(DISTINCT us.session_id) as active_sessions,
                AVG(EXTRACT(EPOCH FROM (NOW() - us.last_activity_at))/60) as avg_session_age_minutes
            FROM platform.schools s
            LEFT JOIN platform.school_memberships sm ON s.id = sm.school_id
            LEFT JOIN platform.user_sessions us ON sm.user_id = us.user_id AND us.is_active = true
            WHERE s.status = 'active'
        """
        
        result = await db.execute(metrics_query)
        metrics = result.fetchone()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system_metrics": {
                "total_schools": metrics.total_schools or 0,
                "total_users": metrics.total_users or 0,
                "active_sessions": metrics.active_sessions or 0,
                "avg_session_age_minutes": float(metrics.avg_session_age_minutes or 0)
            },
            "performance_metrics": {
                "avg_response_time_ms": 250,  # Placeholder
                "error_rate_percent": 0.1,   # Placeholder
                "uptime_percent": 99.9       # Placeholder
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting monitoring metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get monitoring metrics"
        )


# =====================================================
# EXPORT AND REPORTING
# =====================================================

@router.get("/export/tenants")
async def export_tenant_data(
    format: str = Query("csv", description="Export format: csv, json"),
    filters: Optional[str] = Query(None, description="JSON string of filters"),
    current_user: PlatformUser = Depends(verify_platform_admin_access),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Export tenant data for reporting
    Platform admin only
    """
    try:
        # Get tenant data for export
        export_query = """
            SELECT 
                s.id,
                s.name,
                s.subdomain,
                s.school_type,
                s.status,
                s.city,
                s.province,
                s.country,
                s.created_at,
                s.activated_at,
                sub.tier as subscription_tier,
                sub.status as subscription_status,
                COUNT(sm.user_id) as total_users
            FROM platform.schools s
            LEFT JOIN platform.school_subscriptions sub ON s.id = sub.school_id
            LEFT JOIN platform.school_memberships sm ON s.id = sm.school_id
            GROUP BY s.id, s.name, s.subdomain, s.school_type, s.status, 
                     s.city, s.province, s.country, s.created_at, s.activated_at,
                     sub.tier, sub.status
            ORDER BY s.created_at DESC
        """
        
        result = await db.execute(export_query)
        
        export_data = []
        for row in result:
            export_data.append({
                "School ID": str(row.id),
                "School Name": row.name,
                "Subdomain": row.subdomain,
                "School Type": row.school_type or "",
                "Status": row.status,
                "City": row.city or "",
                "Province": row.province or "",
                "Country": row.country or "",
                "Created At": row.created_at.isoformat(),
                "Activated At": row.activated_at.isoformat() if row.activated_at else "",
                "Subscription Tier": row.subscription_tier or "basic",
                "Subscription Status": row.subscription_status or "pending",
                "Total Users": row.total_users or 0
            })
        
        if format.lower() == "json":
            return {
                "export_format": "json",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_records": len(export_data),
                "data": export_data
            }
        else:
            # For CSV, would normally return a file download
            # Here we'll return the data structure
            return {
                "export_format": "csv",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_records": len(export_data),
                "csv_data": export_data,
                "note": "In production, this would trigger a CSV file download"
            }
        
    except Exception as e:
        logger.error(f"Error exporting tenant data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export tenant data"
        )


# =====================================================
# HEALTH CHECK
# =====================================================

@router.get("/health")
async def health_check():
    """Health check for tenant management service"""
    return {
        "status": "healthy",
        "service": "tenant-management",
        "timestamp": datetime.utcnow().isoformat()
    }