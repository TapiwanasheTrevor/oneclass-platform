"""
Performance Monitoring Service
Core service for monitoring and observability
"""

import asyncio
import logging
import time
import psutil
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from shared.database import get_db_session
from shared.exceptions import ValidationError, NotFoundError
from .models import (
    PerformanceMetric, SystemHealth, ErrorLog, RequestTrace, Alert,
    AuditLog, DatabaseMetrics, CacheMetrics, QueueMetrics, SecurityEvent,
    BusinessMetrics
)
from .schemas import (
    MetricCreate, HealthCheckCreate, ErrorLogCreate, TraceSpanCreate,
    AlertCreate, AuditLogCreate, SecurityEventCreate, MetricQuery,
    MonitoringConfiguration, Severity, HealthStatus, AlertStatus
)

logger = logging.getLogger(__name__)


class MonitoringService:
    """Core monitoring service"""
    
    def __init__(self):
        self.config = MonitoringConfiguration()
        self.alert_rules = []
        self.active_traces = {}
        self.metric_buffer = []
        self.buffer_size = 100
        
    async def record_metric(self, metric_data: MetricCreate) -> str:
        """Record a performance metric"""
        try:
            async with get_db_session() as session:
                metric = PerformanceMetric(
                    metric_name=metric_data.metric_name,
                    metric_type=metric_data.metric_type,
                    value=metric_data.value,
                    unit=metric_data.unit,
                    tags=metric_data.tags,
                    source=metric_data.source,
                    timestamp=datetime.utcnow()
                )
                
                session.add(metric)
                await session.commit()
                await session.refresh(metric)
                
                # Check alert rules
                await self._check_alert_rules(metric)
                
                logger.debug(f"Recorded metric: {metric_data.metric_name} = {metric_data.value}")
                return str(metric.id)
                
        except Exception as e:
            logger.error(f"Failed to record metric: {str(e)}")
            raise
    
    async def record_health_check(self, health_data: HealthCheckCreate) -> str:
        """Record a health check result"""
        try:
            async with get_db_session() as session:
                health = SystemHealth(
                    service_name=health_data.service_name,
                    status=health_data.status,
                    response_time=health_data.response_time,
                    error_message=health_data.error_message,
                    metadata=health_data.metadata,
                    timestamp=datetime.utcnow()
                )
                
                session.add(health)
                await session.commit()
                await session.refresh(health)
                
                # Create alert if service is unhealthy
                if health_data.status != HealthStatus.HEALTHY:
                    await self._create_health_alert(health)
                
                logger.debug(f"Health check recorded: {health_data.service_name} = {health_data.status}")
                return str(health.id)
                
        except Exception as e:
            logger.error(f"Failed to record health check: {str(e)}")
            raise
    
    async def log_error(self, error_data: ErrorLogCreate) -> str:
        """Log an error"""
        try:
            async with get_db_session() as session:
                error_log = ErrorLog(
                    error_type=error_data.error_type,
                    error_message=error_data.error_message,
                    stack_trace=error_data.stack_trace,
                    request_id=error_data.request_id,
                    user_id=error_data.user_id,
                    endpoint=error_data.endpoint,
                    http_method=error_data.http_method,
                    http_status=error_data.http_status,
                    request_data=error_data.request_data,
                    context=error_data.context,
                    severity=error_data.severity,
                    timestamp=datetime.utcnow()
                )
                
                session.add(error_log)
                await session.commit()
                await session.refresh(error_log)
                
                # Create alert for critical errors
                if error_data.severity == Severity.CRITICAL:
                    await self._create_error_alert(error_log)
                
                logger.debug(f"Error logged: {error_data.error_type} - {error_data.severity}")
                return str(error_log.id)
                
        except Exception as e:
            logger.error(f"Failed to log error: {str(e)}")
            raise
    
    async def start_trace(self, trace_data: TraceSpanCreate) -> str:
        """Start a new trace span"""
        try:
            async with get_db_session() as session:
                trace = RequestTrace(
                    trace_id=trace_data.trace_id,
                    span_id=trace_data.span_id,
                    parent_span_id=trace_data.parent_span_id,
                    operation_name=trace_data.operation_name,
                    service_name=trace_data.service_name,
                    start_time=trace_data.start_time,
                    end_time=trace_data.end_time,
                    duration=trace_data.duration,
                    status=trace_data.status,
                    tags=trace_data.tags,
                    logs=trace_data.logs
                )
                
                session.add(trace)
                await session.commit()
                await session.refresh(trace)
                
                # Store active trace
                self.active_traces[trace_data.trace_id] = trace
                
                logger.debug(f"Trace started: {trace_data.operation_name}")
                return str(trace.id)
                
        except Exception as e:
            logger.error(f"Failed to start trace: {str(e)}")
            raise
    
    async def finish_trace(self, trace_id: str, end_time: datetime, status: str) -> None:
        """Finish a trace span"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(RequestTrace).filter(RequestTrace.trace_id == trace_id)
                )
                trace = result.scalar_one_or_none()
                
                if trace:
                    trace.end_time = end_time
                    trace.status = status
                    trace.duration = (end_time - trace.start_time).total_seconds() * 1000
                    
                    await session.commit()
                    
                    # Remove from active traces
                    self.active_traces.pop(trace_id, None)
                    
                    logger.debug(f"Trace finished: {trace_id} - {trace.duration}ms")
                
        except Exception as e:
            logger.error(f"Failed to finish trace: {str(e)}")
            raise
    
    async def create_alert(self, alert_data: AlertCreate) -> str:
        """Create a new alert"""
        try:
            async with get_db_session() as session:
                alert = Alert(
                    alert_name=alert_data.alert_name,
                    alert_type=alert_data.alert_type,
                    severity=alert_data.severity,
                    description=alert_data.description,
                    metric_name=alert_data.metric_name,
                    threshold_value=alert_data.threshold_value,
                    current_value=alert_data.current_value,
                    condition=alert_data.condition,
                    tags=alert_data.tags,
                    status=AlertStatus.ACTIVE,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                session.add(alert)
                await session.commit()
                await session.refresh(alert)
                
                # Send notification
                await self._send_alert_notification(alert)
                
                logger.info(f"Alert created: {alert_data.alert_name} - {alert_data.severity}")
                return str(alert.id)
                
        except Exception as e:
            logger.error(f"Failed to create alert: {str(e)}")
            raise
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(Alert).filter(Alert.id == alert_id)
                )
                alert = result.scalar_one_or_none()
                
                if not alert:
                    raise NotFoundError("Alert not found")
                
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.utcnow()
                alert.updated_at = datetime.utcnow()
                
                await session.commit()
                
                logger.info(f"Alert resolved: {alert.alert_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to resolve alert: {str(e)}")
            raise
    
    async def log_audit_event(self, audit_data: AuditLogCreate) -> str:
        """Log an audit event"""
        try:
            async with get_db_session() as session:
                audit_log = AuditLog(
                    user_id=audit_data.user_id,
                    username=audit_data.username,
                    action=audit_data.action,
                    resource_type=audit_data.resource_type,
                    resource_id=audit_data.resource_id,
                    old_values=audit_data.old_values,
                    new_values=audit_data.new_values,
                    ip_address=audit_data.ip_address,
                    user_agent=audit_data.user_agent,
                    request_id=audit_data.request_id,
                    school_id=audit_data.school_id,
                    success=audit_data.success,
                    error_message=audit_data.error_message,
                    timestamp=datetime.utcnow()
                )
                
                session.add(audit_log)
                await session.commit()
                await session.refresh(audit_log)
                
                logger.debug(f"Audit event logged: {audit_data.action} by {audit_data.username}")
                return str(audit_log.id)
                
        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
            raise
    
    async def log_security_event(self, security_data: SecurityEventCreate) -> str:
        """Log a security event"""
        try:
            async with get_db_session() as session:
                security_event = SecurityEvent(
                    event_type=security_data.event_type,
                    severity=security_data.severity,
                    description=security_data.description,
                    user_id=security_data.user_id,
                    username=security_data.username,
                    ip_address=security_data.ip_address,
                    user_agent=security_data.user_agent,
                    request_id=security_data.request_id,
                    endpoint=security_data.endpoint,
                    additional_data=security_data.additional_data,
                    timestamp=datetime.utcnow()
                )
                
                session.add(security_event)
                await session.commit()
                await session.refresh(security_event)
                
                # Create alert for critical security events
                if security_data.severity == Severity.CRITICAL:
                    await self._create_security_alert(security_event)
                
                logger.warning(f"Security event logged: {security_data.event_type} - {security_data.severity}")
                return str(security_event.id)
                
        except Exception as e:
            logger.error(f"Failed to log security event: {str(e)}")
            raise
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # Load average
            load_avg = psutil.getloadavg()
            
            # System uptime
            uptime = time.time() - psutil.boot_time()
            
            metrics = {
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'disk_usage': disk_usage,
                'network_io': network_io,
                'load_average': list(load_avg),
                'uptime': uptime,
                'timestamp': datetime.utcnow()
            }
            
            # Record metrics in database
            await self.record_metric(MetricCreate(
                metric_name="system.cpu_usage",
                metric_type="gauge",
                value=cpu_usage,
                unit="percent",
                source="system"
            ))
            
            await self.record_metric(MetricCreate(
                metric_name="system.memory_usage",
                metric_type="gauge",
                value=memory_usage,
                unit="percent",
                source="system"
            ))
            
            await self.record_metric(MetricCreate(
                metric_name="system.disk_usage",
                metric_type="gauge",
                value=disk_usage,
                unit="percent",
                source="system"
            ))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {str(e)}")
            raise
    
    async def get_database_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        try:
            async with get_db_session() as session:
                # Get connection count
                connection_result = await session.execute(
                    "SELECT count(*) FROM pg_stat_activity"
                )
                connection_count = connection_result.scalar()
                
                # Get active connections
                active_result = await session.execute(
                    "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
                )
                active_connections = active_result.scalar()
                
                # Get idle connections
                idle_result = await session.execute(
                    "SELECT count(*) FROM pg_stat_activity WHERE state = 'idle'"
                )
                idle_connections = idle_result.scalar()
                
                # Get database size
                size_result = await session.execute(
                    "SELECT pg_database_size(current_database())"
                )
                db_size = size_result.scalar()
                
                metrics = {
                    'connection_count': connection_count,
                    'active_connections': active_connections,
                    'idle_connections': idle_connections,
                    'database_size': db_size,
                    'timestamp': datetime.utcnow()
                }
                
                # Record metrics
                db_metrics = DatabaseMetrics(
                    database_name="oneclass_platform",
                    connection_count=connection_count,
                    active_connections=active_connections,
                    idle_connections=idle_connections,
                    table_size=db_size,
                    timestamp=datetime.utcnow()
                )
                
                session.add(db_metrics)
                await session.commit()
                
                return metrics
                
        except Exception as e:
            logger.error(f"Failed to get database metrics: {str(e)}")
            raise
    
    async def query_metrics(self, query: MetricQuery) -> List[Dict[str, Any]]:
        """Query performance metrics"""
        try:
            async with get_db_session() as session:
                # Build query
                stmt = select(PerformanceMetric)
                
                # Apply filters
                if query.metric_name:
                    stmt = stmt.filter(PerformanceMetric.metric_name == query.metric_name)
                
                if query.source:
                    stmt = stmt.filter(PerformanceMetric.source == query.source)
                
                if query.start_time:
                    stmt = stmt.filter(PerformanceMetric.timestamp >= query.start_time)
                
                if query.end_time:
                    stmt = stmt.filter(PerformanceMetric.timestamp <= query.end_time)
                
                # Apply ordering and limit
                stmt = stmt.order_by(PerformanceMetric.timestamp.desc())
                
                if query.limit:
                    stmt = stmt.limit(query.limit)
                
                result = await session.execute(stmt)
                metrics = result.scalars().all()
                
                # Convert to dict
                metric_data = []
                for metric in metrics:
                    metric_data.append({
                        'id': str(metric.id),
                        'metric_name': metric.metric_name,
                        'metric_type': metric.metric_type,
                        'value': metric.value,
                        'unit': metric.unit,
                        'tags': metric.tags,
                        'source': metric.source,
                        'timestamp': metric.timestamp
                    })
                
                return metric_data
                
        except Exception as e:
            logger.error(f"Failed to query metrics: {str(e)}")
            raise
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(Alert).filter(Alert.status == AlertStatus.ACTIVE)
                    .order_by(Alert.created_at.desc())
                )
                alerts = result.scalars().all()
                
                alert_data = []
                for alert in alerts:
                    alert_data.append({
                        'id': str(alert.id),
                        'alert_name': alert.alert_name,
                        'alert_type': alert.alert_type,
                        'severity': alert.severity,
                        'description': alert.description,
                        'metric_name': alert.metric_name,
                        'threshold_value': alert.threshold_value,
                        'current_value': alert.current_value,
                        'condition': alert.condition,
                        'tags': alert.tags,
                        'created_at': alert.created_at,
                        'updated_at': alert.updated_at
                    })
                
                return alert_data
                
        except Exception as e:
            logger.error(f"Failed to get active alerts: {str(e)}")
            raise
    
    async def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the last N hours"""
        try:
            async with get_db_session() as session:
                start_time = datetime.utcnow() - timedelta(hours=hours)
                
                # Total errors
                total_result = await session.execute(
                    select(func.count(ErrorLog.id))
                    .filter(ErrorLog.timestamp >= start_time)
                )
                total_errors = total_result.scalar()
                
                # Errors by severity
                severity_result = await session.execute(
                    select(ErrorLog.severity, func.count(ErrorLog.id))
                    .filter(ErrorLog.timestamp >= start_time)
                    .group_by(ErrorLog.severity)
                )
                severity_counts = dict(severity_result.fetchall())
                
                # Errors by type
                type_result = await session.execute(
                    select(ErrorLog.error_type, func.count(ErrorLog.id))
                    .filter(ErrorLog.timestamp >= start_time)
                    .group_by(ErrorLog.error_type)
                    .order_by(func.count(ErrorLog.id).desc())
                    .limit(10)
                )
                type_counts = dict(type_result.fetchall())
                
                # Error rate
                error_rate = total_errors / hours if hours > 0 else 0
                
                return {
                    'total_errors': total_errors,
                    'error_rate': error_rate,
                    'severity_breakdown': severity_counts,
                    'top_error_types': type_counts,
                    'time_period': f"{hours} hours",
                    'timestamp': datetime.utcnow()
                }
                
        except Exception as e:
            logger.error(f"Failed to get error summary: {str(e)}")
            raise
    
    async def _check_alert_rules(self, metric: PerformanceMetric) -> None:
        """Check if metric triggers any alert rules"""
        try:
            # This would check configured alert rules
            # For now, implement basic thresholds
            
            if metric.metric_name == "system.cpu_usage" and metric.value > 80:
                await self.create_alert(AlertCreate(
                    alert_name="High CPU Usage",
                    alert_type="threshold",
                    severity=Severity.WARNING,
                    description=f"CPU usage is {metric.value}%",
                    metric_name=metric.metric_name,
                    threshold_value=80,
                    current_value=metric.value,
                    condition="greater_than"
                ))
            
            if metric.metric_name == "system.memory_usage" and metric.value > 85:
                await self.create_alert(AlertCreate(
                    alert_name="High Memory Usage",
                    alert_type="threshold",
                    severity=Severity.WARNING,
                    description=f"Memory usage is {metric.value}%",
                    metric_name=metric.metric_name,
                    threshold_value=85,
                    current_value=metric.value,
                    condition="greater_than"
                ))
                
        except Exception as e:
            logger.error(f"Failed to check alert rules: {str(e)}")
    
    async def _create_health_alert(self, health: SystemHealth) -> None:
        """Create alert for unhealthy service"""
        try:
            await self.create_alert(AlertCreate(
                alert_name=f"Service Health Alert - {health.service_name}",
                alert_type="health_check",
                severity=Severity.ERROR if health.status == HealthStatus.UNHEALTHY else Severity.WARNING,
                description=f"Service {health.service_name} is {health.status}",
                tags={"service": health.service_name}
            ))
        except Exception as e:
            logger.error(f"Failed to create health alert: {str(e)}")
    
    async def _create_error_alert(self, error: ErrorLog) -> None:
        """Create alert for critical error"""
        try:
            await self.create_alert(AlertCreate(
                alert_name=f"Critical Error - {error.error_type}",
                alert_type="error",
                severity=Severity.CRITICAL,
                description=f"Critical error: {error.error_message}",
                tags={"error_type": error.error_type, "endpoint": error.endpoint}
            ))
        except Exception as e:
            logger.error(f"Failed to create error alert: {str(e)}")
    
    async def _create_security_alert(self, security_event: SecurityEvent) -> None:
        """Create alert for security event"""
        try:
            await self.create_alert(AlertCreate(
                alert_name=f"Security Alert - {security_event.event_type}",
                alert_type="security",
                severity=Severity.CRITICAL,
                description=f"Security event: {security_event.description}",
                tags={"event_type": security_event.event_type, "ip": security_event.ip_address}
            ))
        except Exception as e:
            logger.error(f"Failed to create security alert: {str(e)}")
    
    async def _send_alert_notification(self, alert: Alert) -> None:
        """Send alert notification"""
        try:
            # This would integrate with notification systems
            # For now, just log the alert
            logger.warning(f"ALERT: {alert.alert_name} - {alert.severity} - {alert.description}")
        except Exception as e:
            logger.error(f"Failed to send alert notification: {str(e)}")
    
    async def cleanup_old_data(self) -> None:
        """Clean up old monitoring data"""
        try:
            async with get_db_session() as session:
                # Clean up old metrics
                metric_cutoff = datetime.utcnow() - timedelta(days=self.config.metric_retention_days)
                await session.execute(
                    PerformanceMetric.__table__.delete().where(
                        PerformanceMetric.timestamp < metric_cutoff
                    )
                )
                
                # Clean up old logs
                log_cutoff = datetime.utcnow() - timedelta(days=self.config.log_retention_days)
                await session.execute(
                    ErrorLog.__table__.delete().where(
                        ErrorLog.timestamp < log_cutoff
                    )
                )
                
                # Clean up old alerts
                alert_cutoff = datetime.utcnow() - timedelta(days=self.config.alert_retention_days)
                await session.execute(
                    Alert.__table__.delete().where(
                        and_(
                            Alert.created_at < alert_cutoff,
                            Alert.status == AlertStatus.RESOLVED
                        )
                    )
                )
                
                await session.commit()
                logger.info("Old monitoring data cleaned up")
                
        except Exception as e:
            logger.error(f"Failed to clean up old data: {str(e)}")
            raise


# Global monitoring service instance
monitoring_service = MonitoringService()