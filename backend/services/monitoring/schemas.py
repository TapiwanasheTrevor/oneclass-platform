"""
Performance Monitoring Schemas
Pydantic models for monitoring and observability
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum


class MetricType(str, Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    SET = "set"


class HealthStatus(str, Enum):
    """Health check status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    """Severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    ACKNOWLEDGED = "acknowledged"


class MetricCreate(BaseModel):
    """Create performance metric"""
    metric_name: str = Field(..., description="Metric name")
    metric_type: MetricType = Field(..., description="Metric type")
    value: float = Field(..., description="Metric value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    tags: Optional[Dict[str, Any]] = Field(None, description="Metric tags")
    source: str = Field(..., description="Metric source")
    
    @validator('metric_name')
    def validate_metric_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Metric name cannot be empty')
        return v.strip()


class MetricResponse(BaseModel):
    """Performance metric response"""
    id: str = Field(..., description="Metric ID")
    metric_name: str = Field(..., description="Metric name")
    metric_type: MetricType = Field(..., description="Metric type")
    value: float = Field(..., description="Metric value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    tags: Optional[Dict[str, Any]] = Field(None, description="Metric tags")
    source: str = Field(..., description="Metric source")
    timestamp: datetime = Field(..., description="Timestamp")
    
    class Config:
        from_attributes = True


class HealthCheckCreate(BaseModel):
    """Create health check"""
    service_name: str = Field(..., description="Service name")
    status: HealthStatus = Field(..., description="Health status")
    response_time: Optional[float] = Field(None, description="Response time in ms")
    error_message: Optional[str] = Field(None, description="Error message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class HealthCheckResponse(BaseModel):
    """Health check response"""
    id: str = Field(..., description="Health check ID")
    service_name: str = Field(..., description="Service name")
    status: HealthStatus = Field(..., description="Health status")
    response_time: Optional[float] = Field(None, description="Response time in ms")
    error_message: Optional[str] = Field(None, description="Error message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    timestamp: datetime = Field(..., description="Timestamp")
    
    class Config:
        from_attributes = True


class ErrorLogCreate(BaseModel):
    """Create error log"""
    error_type: str = Field(..., description="Error type")
    error_message: str = Field(..., description="Error message")
    stack_trace: Optional[str] = Field(None, description="Stack trace")
    request_id: Optional[str] = Field(None, description="Request ID")
    user_id: Optional[str] = Field(None, description="User ID")
    endpoint: Optional[str] = Field(None, description="API endpoint")
    http_method: Optional[str] = Field(None, description="HTTP method")
    http_status: Optional[int] = Field(None, description="HTTP status code")
    request_data: Optional[Dict[str, Any]] = Field(None, description="Request data")
    context: Optional[Dict[str, Any]] = Field(None, description="Error context")
    severity: Severity = Field(Severity.ERROR, description="Error severity")


class ErrorLogResponse(BaseModel):
    """Error log response"""
    id: str = Field(..., description="Error log ID")
    error_type: str = Field(..., description="Error type")
    error_message: str = Field(..., description="Error message")
    stack_trace: Optional[str] = Field(None, description="Stack trace")
    request_id: Optional[str] = Field(None, description="Request ID")
    user_id: Optional[str] = Field(None, description="User ID")
    endpoint: Optional[str] = Field(None, description="API endpoint")
    http_method: Optional[str] = Field(None, description="HTTP method")
    http_status: Optional[int] = Field(None, description="HTTP status code")
    severity: Severity = Field(..., description="Error severity")
    resolved: bool = Field(..., description="Resolution status")
    timestamp: datetime = Field(..., description="Timestamp")
    
    class Config:
        from_attributes = True


class TraceSpanCreate(BaseModel):
    """Create trace span"""
    trace_id: str = Field(..., description="Trace ID")
    span_id: str = Field(..., description="Span ID")
    parent_span_id: Optional[str] = Field(None, description="Parent span ID")
    operation_name: str = Field(..., description="Operation name")
    service_name: str = Field(..., description="Service name")
    start_time: datetime = Field(..., description="Start time")
    end_time: Optional[datetime] = Field(None, description="End time")
    duration: Optional[float] = Field(None, description="Duration in ms")
    status: str = Field(..., description="Span status")
    tags: Optional[Dict[str, Any]] = Field(None, description="Span tags")
    logs: Optional[List[Dict[str, Any]]] = Field(None, description="Span logs")


class TraceSpanResponse(BaseModel):
    """Trace span response"""
    id: str = Field(..., description="Span database ID")
    trace_id: str = Field(..., description="Trace ID")
    span_id: str = Field(..., description="Span ID")
    parent_span_id: Optional[str] = Field(None, description="Parent span ID")
    operation_name: str = Field(..., description="Operation name")
    service_name: str = Field(..., description="Service name")
    start_time: datetime = Field(..., description="Start time")
    end_time: Optional[datetime] = Field(None, description="End time")
    duration: Optional[float] = Field(None, description="Duration in ms")
    status: str = Field(..., description="Span status")
    tags: Optional[Dict[str, Any]] = Field(None, description="Span tags")
    logs: Optional[List[Dict[str, Any]]] = Field(None, description="Span logs")
    
    class Config:
        from_attributes = True


class AlertCreate(BaseModel):
    """Create alert"""
    alert_name: str = Field(..., description="Alert name")
    alert_type: str = Field(..., description="Alert type")
    severity: Severity = Field(..., description="Alert severity")
    description: str = Field(..., description="Alert description")
    metric_name: Optional[str] = Field(None, description="Related metric name")
    threshold_value: Optional[float] = Field(None, description="Threshold value")
    current_value: Optional[float] = Field(None, description="Current value")
    condition: Optional[str] = Field(None, description="Alert condition")
    tags: Optional[Dict[str, Any]] = Field(None, description="Alert tags")


class AlertResponse(BaseModel):
    """Alert response"""
    id: str = Field(..., description="Alert ID")
    alert_name: str = Field(..., description="Alert name")
    alert_type: str = Field(..., description="Alert type")
    severity: Severity = Field(..., description="Alert severity")
    status: AlertStatus = Field(..., description="Alert status")
    description: str = Field(..., description="Alert description")
    metric_name: Optional[str] = Field(None, description="Related metric name")
    threshold_value: Optional[float] = Field(None, description="Threshold value")
    current_value: Optional[float] = Field(None, description="Current value")
    condition: Optional[str] = Field(None, description="Alert condition")
    tags: Optional[Dict[str, Any]] = Field(None, description="Alert tags")
    created_at: datetime = Field(..., description="Created timestamp")
    updated_at: datetime = Field(..., description="Updated timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolved timestamp")
    
    class Config:
        from_attributes = True


class AuditLogCreate(BaseModel):
    """Create audit log"""
    user_id: Optional[str] = Field(None, description="User ID")
    username: Optional[str] = Field(None, description="Username")
    action: str = Field(..., description="Action performed")
    resource_type: str = Field(..., description="Resource type")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    old_values: Optional[Dict[str, Any]] = Field(None, description="Old values")
    new_values: Optional[Dict[str, Any]] = Field(None, description="New values")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    request_id: Optional[str] = Field(None, description="Request ID")
    school_id: Optional[str] = Field(None, description="School ID")
    success: bool = Field(True, description="Success status")
    error_message: Optional[str] = Field(None, description="Error message")


class AuditLogResponse(BaseModel):
    """Audit log response"""
    id: str = Field(..., description="Audit log ID")
    user_id: Optional[str] = Field(None, description="User ID")
    username: Optional[str] = Field(None, description="Username")
    action: str = Field(..., description="Action performed")
    resource_type: str = Field(..., description="Resource type")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    old_values: Optional[Dict[str, Any]] = Field(None, description="Old values")
    new_values: Optional[Dict[str, Any]] = Field(None, description="New values")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    request_id: Optional[str] = Field(None, description="Request ID")
    school_id: Optional[str] = Field(None, description="School ID")
    success: bool = Field(..., description="Success status")
    error_message: Optional[str] = Field(None, description="Error message")
    timestamp: datetime = Field(..., description="Timestamp")
    
    class Config:
        from_attributes = True


class SystemMetricsResponse(BaseModel):
    """System metrics response"""
    cpu_usage: float = Field(..., description="CPU usage percentage")
    memory_usage: float = Field(..., description="Memory usage percentage")
    disk_usage: float = Field(..., description="Disk usage percentage")
    network_io: Dict[str, float] = Field(..., description="Network I/O stats")
    load_average: List[float] = Field(..., description="Load average")
    uptime: float = Field(..., description="System uptime in seconds")
    timestamp: datetime = Field(..., description="Timestamp")


class DatabaseMetricsResponse(BaseModel):
    """Database metrics response"""
    database_name: str = Field(..., description="Database name")
    connection_count: Optional[int] = Field(None, description="Total connections")
    active_connections: Optional[int] = Field(None, description="Active connections")
    idle_connections: Optional[int] = Field(None, description="Idle connections")
    query_count: Optional[int] = Field(None, description="Total queries")
    slow_query_count: Optional[int] = Field(None, description="Slow queries")
    deadlock_count: Optional[int] = Field(None, description="Deadlocks")
    cache_hit_ratio: Optional[float] = Field(None, description="Cache hit ratio")
    table_size: Optional[int] = Field(None, description="Table size in bytes")
    index_size: Optional[int] = Field(None, description="Index size in bytes")
    timestamp: datetime = Field(..., description="Timestamp")
    
    class Config:
        from_attributes = True


class CacheMetricsResponse(BaseModel):
    """Cache metrics response"""
    cache_name: str = Field(..., description="Cache name")
    cache_type: str = Field(..., description="Cache type")
    hit_count: Optional[int] = Field(None, description="Cache hits")
    miss_count: Optional[int] = Field(None, description="Cache misses")
    hit_ratio: Optional[float] = Field(None, description="Hit ratio percentage")
    eviction_count: Optional[int] = Field(None, description="Evictions")
    memory_usage: Optional[int] = Field(None, description="Memory usage in bytes")
    key_count: Optional[int] = Field(None, description="Number of keys")
    expired_keys: Optional[int] = Field(None, description="Expired keys")
    timestamp: datetime = Field(..., description="Timestamp")
    
    class Config:
        from_attributes = True


class SecurityEventCreate(BaseModel):
    """Create security event"""
    event_type: str = Field(..., description="Event type")
    severity: Severity = Field(..., description="Event severity")
    description: str = Field(..., description="Event description")
    user_id: Optional[str] = Field(None, description="User ID")
    username: Optional[str] = Field(None, description="Username")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    request_id: Optional[str] = Field(None, description="Request ID")
    endpoint: Optional[str] = Field(None, description="API endpoint")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Additional data")


class SecurityEventResponse(BaseModel):
    """Security event response"""
    id: str = Field(..., description="Security event ID")
    event_type: str = Field(..., description="Event type")
    severity: Severity = Field(..., description="Event severity")
    description: str = Field(..., description="Event description")
    user_id: Optional[str] = Field(None, description="User ID")
    username: Optional[str] = Field(None, description="Username")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    request_id: Optional[str] = Field(None, description="Request ID")
    endpoint: Optional[str] = Field(None, description="API endpoint")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Additional data")
    resolved: bool = Field(..., description="Resolution status")
    timestamp: datetime = Field(..., description="Timestamp")
    
    class Config:
        from_attributes = True


class MonitoringDashboardResponse(BaseModel):
    """Monitoring dashboard response"""
    system_health: HealthStatus = Field(..., description="Overall system health")
    active_alerts: int = Field(..., description="Number of active alerts")
    error_rate: float = Field(..., description="Error rate percentage")
    response_time: float = Field(..., description="Average response time")
    throughput: float = Field(..., description="Requests per second")
    cpu_usage: float = Field(..., description="CPU usage percentage")
    memory_usage: float = Field(..., description="Memory usage percentage")
    database_health: HealthStatus = Field(..., description="Database health")
    cache_health: HealthStatus = Field(..., description="Cache health")
    queue_health: HealthStatus = Field(..., description="Queue health")
    timestamp: datetime = Field(..., description="Timestamp")


class AlertRule(BaseModel):
    """Alert rule definition"""
    name: str = Field(..., description="Rule name")
    metric_name: str = Field(..., description="Metric to monitor")
    condition: str = Field(..., description="Alert condition")
    threshold: float = Field(..., description="Threshold value")
    duration: int = Field(..., description="Duration in seconds")
    severity: Severity = Field(..., description="Alert severity")
    enabled: bool = Field(True, description="Rule enabled status")
    tags: Optional[Dict[str, Any]] = Field(None, description="Rule tags")


class MetricQuery(BaseModel):
    """Metric query parameters"""
    metric_name: Optional[str] = Field(None, description="Metric name filter")
    source: Optional[str] = Field(None, description="Source filter")
    start_time: Optional[datetime] = Field(None, description="Start time")
    end_time: Optional[datetime] = Field(None, description="End time")
    tags: Optional[Dict[str, Any]] = Field(None, description="Tag filters")
    aggregation: Optional[str] = Field(None, description="Aggregation method")
    group_by: Optional[List[str]] = Field(None, description="Group by fields")
    limit: Optional[int] = Field(100, description="Result limit")


class MetricAggregation(BaseModel):
    """Metric aggregation result"""
    metric_name: str = Field(..., description="Metric name")
    aggregation_type: str = Field(..., description="Aggregation type")
    value: float = Field(..., description="Aggregated value")
    timestamp: datetime = Field(..., description="Timestamp")
    tags: Optional[Dict[str, Any]] = Field(None, description="Tags")


class BusinessMetricsResponse(BaseModel):
    """Business metrics response"""
    metric_name: str = Field(..., description="Metric name")
    metric_category: str = Field(..., description="Metric category")
    value: float = Field(..., description="Metric value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    school_id: Optional[str] = Field(None, description="School ID")
    period: Optional[str] = Field(None, description="Time period")
    dimensions: Optional[Dict[str, Any]] = Field(None, description="Dimensions")
    timestamp: datetime = Field(..., description="Timestamp")
    
    class Config:
        from_attributes = True


class MonitoringConfiguration(BaseModel):
    """Monitoring configuration"""
    metric_retention_days: int = Field(30, description="Metric retention period")
    log_retention_days: int = Field(90, description="Log retention period")
    alert_retention_days: int = Field(365, description="Alert retention period")
    health_check_interval: int = Field(60, description="Health check interval in seconds")
    metric_collection_interval: int = Field(15, description="Metric collection interval")
    enable_tracing: bool = Field(True, description="Enable distributed tracing")
    enable_profiling: bool = Field(False, description="Enable performance profiling")
    sample_rate: float = Field(0.1, description="Trace sampling rate")
    alert_rules: List[AlertRule] = Field(default_factory=list, description="Alert rules")
    notification_channels: List[str] = Field(default_factory=list, description="Notification channels")


class PerformanceReport(BaseModel):
    """Performance report"""
    report_id: str = Field(..., description="Report ID")
    report_type: str = Field(..., description="Report type")
    period: str = Field(..., description="Report period")
    metrics: List[MetricAggregation] = Field(..., description="Metrics")
    summary: Dict[str, Any] = Field(..., description="Summary statistics")
    recommendations: List[str] = Field(..., description="Performance recommendations")
    generated_at: datetime = Field(..., description="Generation timestamp")
    generated_by: Optional[str] = Field(None, description="Generated by user")