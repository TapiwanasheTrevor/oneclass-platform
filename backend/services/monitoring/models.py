"""
Performance Monitoring Models
Database models for monitoring and observability
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

Base = declarative_base()


class PerformanceMetric(Base):
    """Performance metrics model"""
    __tablename__ = "performance_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(255), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)  # counter, gauge, histogram, timer
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=True)  # ms, bytes, count, percent
    tags = Column(JSON, nullable=True)  # Additional metadata
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    source = Column(String(100), nullable=False)  # api, database, cache, etc.
    
    def __repr__(self):
        return f"<PerformanceMetric {self.metric_name}: {self.value} {self.unit}>"


class SystemHealth(Base):
    """System health checks model"""
    __tablename__ = "system_health"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_name = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False)  # healthy, unhealthy, degraded
    response_time = Column(Float, nullable=True)  # Response time in milliseconds
    error_message = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<SystemHealth {self.service_name}: {self.status}>"


class ErrorLog(Base):
    """Error logging model"""
    __tablename__ = "error_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    error_type = Column(String(100), nullable=False, index=True)
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    endpoint = Column(String(255), nullable=True)
    http_method = Column(String(10), nullable=True)
    http_status = Column(Integer, nullable=True)
    request_data = Column(JSON, nullable=True)
    context = Column(JSON, nullable=True)
    severity = Column(String(20), nullable=False, default="error")  # debug, info, warning, error, critical
    resolved = Column(Boolean, default=False, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<ErrorLog {self.error_type}: {self.severity}>"


class RequestTrace(Base):
    """Request tracing model"""
    __tablename__ = "request_traces"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id = Column(String(100), nullable=False, unique=True, index=True)
    span_id = Column(String(100), nullable=False, index=True)
    parent_span_id = Column(String(100), nullable=True, index=True)
    operation_name = Column(String(255), nullable=False)
    service_name = Column(String(100), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # Duration in milliseconds
    status = Column(String(20), nullable=False)  # success, error, timeout
    tags = Column(JSON, nullable=True)
    logs = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<RequestTrace {self.operation_name}: {self.duration}ms>"


class Alert(Base):
    """Alert model for monitoring alerts"""
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_name = Column(String(255), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)  # threshold, anomaly, health_check
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    status = Column(String(20), nullable=False, default="active")  # active, resolved, suppressed
    description = Column(Text, nullable=False)
    metric_name = Column(String(255), nullable=True)
    threshold_value = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)
    condition = Column(String(50), nullable=True)  # greater_than, less_than, equals
    tags = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Alert {self.alert_name}: {self.severity}>"


class AuditLog(Base):
    """Audit log model for tracking important actions"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    username = Column(String(255), nullable=True)
    action = Column(String(255), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(255), nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(100), nullable=True, index=True)
    school_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<AuditLog {self.action} by {self.username}>"


class DatabaseMetrics(Base):
    """Database performance metrics"""
    __tablename__ = "database_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    database_name = Column(String(100), nullable=False)
    connection_count = Column(Integer, nullable=True)
    active_connections = Column(Integer, nullable=True)
    idle_connections = Column(Integer, nullable=True)
    query_count = Column(Integer, nullable=True)
    slow_query_count = Column(Integer, nullable=True)
    deadlock_count = Column(Integer, nullable=True)
    cache_hit_ratio = Column(Float, nullable=True)
    table_size = Column(Integer, nullable=True)  # in bytes
    index_size = Column(Integer, nullable=True)  # in bytes
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<DatabaseMetrics {self.database_name}>"


class CacheMetrics(Base):
    """Cache performance metrics"""
    __tablename__ = "cache_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cache_name = Column(String(100), nullable=False)
    cache_type = Column(String(50), nullable=False)  # redis, memcached, local
    hit_count = Column(Integer, nullable=True)
    miss_count = Column(Integer, nullable=True)
    hit_ratio = Column(Float, nullable=True)
    eviction_count = Column(Integer, nullable=True)
    memory_usage = Column(Integer, nullable=True)  # in bytes
    key_count = Column(Integer, nullable=True)
    expired_keys = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<CacheMetrics {self.cache_name}: {self.hit_ratio}% hit ratio>"


class QueueMetrics(Base):
    """Queue performance metrics"""
    __tablename__ = "queue_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    queue_name = Column(String(100), nullable=False)
    queue_type = Column(String(50), nullable=False)  # celery, rq, custom
    pending_jobs = Column(Integer, nullable=True)
    active_jobs = Column(Integer, nullable=True)
    completed_jobs = Column(Integer, nullable=True)
    failed_jobs = Column(Integer, nullable=True)
    retry_jobs = Column(Integer, nullable=True)
    average_processing_time = Column(Float, nullable=True)  # in seconds
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<QueueMetrics {self.queue_name}: {self.pending_jobs} pending>"


class SecurityEvent(Base):
    """Security event logging"""
    __tablename__ = "security_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    description = Column(Text, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    username = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(100), nullable=True, index=True)
    endpoint = Column(String(255), nullable=True)
    additional_data = Column(JSON, nullable=True)
    resolved = Column(Boolean, default=False, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<SecurityEvent {self.event_type}: {self.severity}>"


class BusinessMetrics(Base):
    """Business-specific metrics"""
    __tablename__ = "business_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(255), nullable=False, index=True)
    metric_category = Column(String(100), nullable=False)  # user_activity, academic, financial
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=True)
    school_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    period = Column(String(50), nullable=True)  # daily, weekly, monthly
    dimensions = Column(JSON, nullable=True)  # Additional grouping dimensions
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<BusinessMetrics {self.metric_name}: {self.value}>"