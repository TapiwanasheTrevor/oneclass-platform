"""
Monitoring Routes
API endpoints for monitoring and observability
"""

from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from shared.auth import get_current_active_user
from shared.models.platform_user import PlatformUser, PlatformRole
from shared.exceptions import ValidationError, NotFoundError
from .service import monitoring_service
from .middleware import metrics_collector
from .schemas import (
    MetricCreate, MetricResponse, HealthCheckCreate, HealthCheckResponse,
    ErrorLogCreate, ErrorLogResponse, AlertCreate, AlertResponse,
    AuditLogCreate, AuditLogResponse, SecurityEventCreate, SecurityEventResponse,
    SystemMetricsResponse, MonitoringDashboardResponse, MetricQuery,
    MonitoringConfiguration, PerformanceReport, Severity, HealthStatus
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/monitoring", tags=["Monitoring"])


@router.get("/health", response_class=JSONResponse)
async def health_check():
    """
    System health check endpoint
    
    Returns the overall health status of the system and key services.
    This endpoint is used by load balancers and monitoring systems.
    """
    try:
        # Get system metrics
        system_metrics = await monitoring_service.get_system_metrics()
        
        # Get database metrics
        db_metrics = await monitoring_service.get_database_metrics()
        
        # Get active alerts
        active_alerts = await monitoring_service.get_active_alerts()
        
        # Determine overall health
        overall_health = HealthStatus.HEALTHY
        
        # Check system resources
        if system_metrics['cpu_usage'] > 90 or system_metrics['memory_usage'] > 95:
            overall_health = HealthStatus.DEGRADED
        
        # Check for critical alerts
        critical_alerts = [a for a in active_alerts if a.get('severity') == 'critical']
        if critical_alerts:
            overall_health = HealthStatus.UNHEALTHY
        
        return JSONResponse(content={
            "status": overall_health,
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "cpu_usage": system_metrics['cpu_usage'],
                "memory_usage": system_metrics['memory_usage'],
                "disk_usage": system_metrics['disk_usage'],
                "uptime": system_metrics['uptime']
            },
            "database": {
                "connection_count": db_metrics['connection_count'],
                "active_connections": db_metrics['active_connections']
            },
            "alerts": {
                "active_count": len(active_alerts),
                "critical_count": len(critical_alerts)
            }
        })
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )


@router.get("/metrics", response_model=List[MetricResponse])
async def get_metrics(
    query: MetricQuery = Depends(),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Query performance metrics
    
    Retrieve performance metrics based on specified filters.
    Supports filtering by metric name, source, time range, and tags.
    """
    try:
        metrics = await monitoring_service.query_metrics(query)
        return metrics
    
    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@router.post("/metrics", response_model=str)
async def create_metric(
    metric_data: MetricCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new performance metric
    
    Record a custom performance metric. This endpoint is used by
    applications to report custom metrics.
    """
    try:
        metric_id = await monitoring_service.record_metric(metric_data)
        return metric_id
    
    except Exception as e:
        logger.error(f"Failed to create metric: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create metric")


@router.post("/health-check", response_model=str)
async def create_health_check(
    health_data: HealthCheckCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Record a health check result
    
    Register the health status of a service or component.
    Used by service monitoring agents.
    """
    try:
        health_id = await monitoring_service.record_health_check(health_data)
        return health_id
    
    except Exception as e:
        logger.error(f"Failed to create health check: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create health check")


@router.post("/errors", response_model=str)
async def log_error(
    error_data: ErrorLogCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Log an error event
    
    Record an error that occurred in the system.
    Used by error tracking and logging systems.
    """
    try:
        error_id = await monitoring_service.log_error(error_data)
        return error_id
    
    except Exception as e:
        logger.error(f"Failed to log error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to log error")


@router.get("/errors", response_model=List[ErrorLogResponse])
async def get_errors(
    severity: Optional[Severity] = None,
    hours: int = Query(24, description="Time range in hours"),
    limit: int = Query(100, description="Maximum number of errors to return"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get error logs
    
    Retrieve error logs with optional filtering by severity and time range.
    """
    try:
        # This would be implemented in the service
        # For now, return empty list
        return []
    
    except Exception as e:
        logger.error(f"Failed to get errors: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve errors")


@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    status: Optional[str] = None,
    severity: Optional[Severity] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get monitoring alerts
    
    Retrieve alerts with optional filtering by status and severity.
    """
    try:
        alerts = await monitoring_service.get_active_alerts()
        return alerts
    
    except Exception as e:
        logger.error(f"Failed to get alerts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.post("/alerts", response_model=str)
async def create_alert(
    alert_data: AlertCreate,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Create a new alert
    
    Create a monitoring alert. Only administrators can create alerts.
    """
    try:
        alert_id = await monitoring_service.create_alert(alert_data)
        return alert_id
    
    except Exception as e:
        logger.error(f"Failed to create alert: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create alert")


@router.post("/alerts/{alert_id}/resolve", response_model=bool)
async def resolve_alert(
    alert_id: str,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Resolve an alert
    
    Mark an alert as resolved. Only administrators can resolve alerts.
    """
    try:
        success = await monitoring_service.resolve_alert(alert_id)
        return success
    
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Alert not found")
    except Exception as e:
        logger.error(f"Failed to resolve alert: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to resolve alert")


@router.post("/audit", response_model=str)
async def log_audit_event(
    audit_data: AuditLogCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Log an audit event
    
    Record an audit trail event for compliance and security monitoring.
    """
    try:
        audit_id = await monitoring_service.log_audit_event(audit_data)
        return audit_id
    
    except Exception as e:
        logger.error(f"Failed to log audit event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to log audit event")


@router.post("/security", response_model=str)
async def log_security_event(
    security_data: SecurityEventCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Log a security event
    
    Record a security-related event for threat monitoring and analysis.
    """
    try:
        security_id = await monitoring_service.log_security_event(security_data)
        return security_id
    
    except Exception as e:
        logger.error(f"Failed to log security event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to log security event")


@router.get("/system", response_model=SystemMetricsResponse)
async def get_system_metrics(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get system performance metrics
    
    Retrieve current system performance metrics including CPU, memory,
    disk usage, and network I/O statistics.
    """
    try:
        metrics = await monitoring_service.get_system_metrics()
        return SystemMetricsResponse(**metrics)
    
    except Exception as e:
        logger.error(f"Failed to get system metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system metrics")


@router.get("/database", response_model=Dict[str, Any])
async def get_database_metrics(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get database performance metrics
    
    Retrieve database performance metrics including connection counts,
    query statistics, and cache hit ratios.
    """
    try:
        metrics = await monitoring_service.get_database_metrics()
        return metrics
    
    except Exception as e:
        logger.error(f"Failed to get database metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve database metrics")


@router.get("/dashboard", response_model=MonitoringDashboardResponse)
async def get_monitoring_dashboard(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get monitoring dashboard data
    
    Retrieve comprehensive monitoring data for the dashboard view.
    Includes system health, alerts, performance metrics, and error rates.
    """
    try:
        # Get system metrics
        system_metrics = await monitoring_service.get_system_metrics()
        
        # Get active alerts
        active_alerts = await monitoring_service.get_active_alerts()
        
        # Get error summary
        error_summary = await monitoring_service.get_error_summary(hours=24)
        
        # Get middleware metrics
        middleware_metrics = metrics_collector.get_metrics()
        
        # Determine system health
        system_health = HealthStatus.HEALTHY
        if system_metrics['cpu_usage'] > 90 or system_metrics['memory_usage'] > 95:
            system_health = HealthStatus.DEGRADED
        
        critical_alerts = [a for a in active_alerts if a.get('severity') == 'critical']
        if critical_alerts:
            system_health = HealthStatus.UNHEALTHY
        
        dashboard_data = MonitoringDashboardResponse(
            system_health=system_health,
            active_alerts=len(active_alerts),
            error_rate=error_summary['error_rate'],
            response_time=middleware_metrics['avg_response_time'],
            throughput=middleware_metrics['request_count'] / 24,  # requests per hour
            cpu_usage=system_metrics['cpu_usage'],
            memory_usage=system_metrics['memory_usage'],
            database_health=HealthStatus.HEALTHY,  # Would check database health
            cache_health=HealthStatus.HEALTHY,     # Would check cache health
            queue_health=HealthStatus.HEALTHY,     # Would check queue health
            timestamp=datetime.utcnow()
        )
        
        return dashboard_data
    
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")


@router.get("/errors/summary", response_model=Dict[str, Any])
async def get_error_summary(
    hours: int = Query(24, description="Time range in hours"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get error summary statistics
    
    Retrieve error statistics for the specified time period including
    error counts, rates, and breakdown by type and severity.
    """
    try:
        summary = await monitoring_service.get_error_summary(hours)
        return summary
    
    except Exception as e:
        logger.error(f"Failed to get error summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve error summary")


@router.post("/cleanup", response_model=Dict[str, str])
async def cleanup_old_data(
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Clean up old monitoring data
    
    Remove old metrics, logs, and alerts based on retention policies.
    Only administrators can trigger cleanup.
    """
    try:
        # Run cleanup in background
        background_tasks.add_task(monitoring_service.cleanup_old_data)
        
        return {"message": "Cleanup started", "status": "success"}
    
    except Exception as e:
        logger.error(f"Failed to start cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start cleanup")


@router.get("/traces/{trace_id}", response_model=Dict[str, Any])
async def get_trace(
    trace_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get distributed trace details
    
    Retrieve detailed information about a specific trace including
    all spans, timing information, and metadata.
    """
    try:
        # This would be implemented in the service
        # For now, return placeholder data
        return {
            "trace_id": trace_id,
            "spans": [],
            "duration": 0,
            "status": "success",
            "timestamp": datetime.utcnow()
        }
    
    except Exception as e:
        logger.error(f"Failed to get trace: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trace")


@router.get("/performance/report", response_model=PerformanceReport)
async def get_performance_report(
    period: str = Query("daily", description="Report period: daily, weekly, monthly"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get performance report
    
    Generate a comprehensive performance report for the specified period.
    Includes metrics analysis, trends, and recommendations.
    """
    try:
        # This would generate a comprehensive performance report
        # For now, return placeholder data
        report = PerformanceReport(
            report_id="report_" + datetime.utcnow().strftime("%Y%m%d"),
            report_type="performance",
            period=period,
            metrics=[],
            summary={
                "avg_response_time": 0,
                "error_rate": 0,
                "throughput": 0,
                "availability": 99.9
            },
            recommendations=[
                "Monitor CPU usage trends",
                "Optimize database queries",
                "Implement caching strategies"
            ],
            generated_at=datetime.utcnow()
        )
        
        return report
    
    except Exception as e:
        logger.error(f"Failed to generate performance report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate performance report")


@router.get("/export/prometheus", response_class=JSONResponse)
async def export_prometheus_metrics(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Export metrics in Prometheus format
    
    Export current metrics in Prometheus exposition format for
    integration with Prometheus monitoring systems.
    """
    try:
        # Get system metrics
        system_metrics = await monitoring_service.get_system_metrics()
        
        # Get middleware metrics
        middleware_metrics = metrics_collector.get_metrics()
        
        # Format as Prometheus metrics
        prometheus_metrics = []
        
        # System metrics
        prometheus_metrics.append(f"# HELP system_cpu_usage CPU usage percentage")
        prometheus_metrics.append(f"# TYPE system_cpu_usage gauge")
        prometheus_metrics.append(f"system_cpu_usage {system_metrics['cpu_usage']}")
        
        prometheus_metrics.append(f"# HELP system_memory_usage Memory usage percentage")
        prometheus_metrics.append(f"# TYPE system_memory_usage gauge")
        prometheus_metrics.append(f"system_memory_usage {system_metrics['memory_usage']}")
        
        # HTTP metrics
        prometheus_metrics.append(f"# HELP http_requests_total Total HTTP requests")
        prometheus_metrics.append(f"# TYPE http_requests_total counter")
        prometheus_metrics.append(f"http_requests_total {middleware_metrics['request_count']}")
        
        prometheus_metrics.append(f"# HELP http_request_duration_seconds HTTP request duration")
        prometheus_metrics.append(f"# TYPE http_request_duration_seconds histogram")
        prometheus_metrics.append(f"http_request_duration_seconds {middleware_metrics['avg_response_time'] / 1000}")
        
        return JSONResponse(
            content={"metrics": "\n".join(prometheus_metrics)},
            headers={"Content-Type": "text/plain"}
        )
    
    except Exception as e:
        logger.error(f"Failed to export Prometheus metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export metrics")


@router.get("/status", response_class=JSONResponse)
async def get_monitoring_status():
    """
    Get monitoring service status
    
    Returns the status of the monitoring service itself including
    health, configuration, and operational metrics.
    """
    try:
        return JSONResponse(content={
            "service": "monitoring",
            "status": "healthy",
            "version": "1.0.0",
            "features": {
                "metrics_collection": True,
                "error_logging": True,
                "distributed_tracing": True,
                "alerting": True,
                "audit_logging": True,
                "security_monitoring": True
            },
            "configuration": {
                "metric_retention_days": 30,
                "log_retention_days": 90,
                "alert_retention_days": 365
            },
            "timestamp": datetime.utcnow()
        })
    
    except Exception as e:
        logger.error(f"Failed to get monitoring status: {str(e)}")
        return JSONResponse(
            content={
                "service": "monitoring",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow()
            },
            status_code=500
        )