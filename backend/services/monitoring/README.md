# Performance Monitoring and Observability Service

The Performance Monitoring and Observability Service provides comprehensive monitoring, logging, alerting, and performance tracking for the OneClass Platform. This service ensures system reliability, performance optimization, and proactive issue detection.

## Features

### 📊 **Performance Monitoring**
- Real-time system metrics (CPU, memory, disk, network)
- Application performance metrics (response times, throughput)
- Database performance monitoring
- Cache performance tracking
- Queue and background job monitoring

### 🔍 **Observability**
- Distributed tracing with OpenTelemetry
- Structured logging with correlation IDs
- Request/response tracking
- Error tracking and aggregation
- Performance profiling

### 🚨 **Alerting System**
- Configurable alert rules and thresholds
- Multiple notification channels (Email, Slack, Webhook, SMS)
- Alert escalation and suppression
- Automatic alert resolution
- Cooldown periods to prevent spam

### 🔒 **Security Monitoring**
- Security event tracking
- Suspicious activity detection
- Authentication failure monitoring
- Rate limiting and abuse detection
- Audit trail logging

### 📈 **Business Intelligence**
- Custom business metrics
- Performance reports and analytics
- Trend analysis and forecasting
- SLA monitoring and reporting
- User behavior analytics

## Quick Start

### 1. Integration with FastAPI

```python
from fastapi import FastAPI
from backend.services.monitoring.middleware import MonitoringMiddleware
from backend.services.monitoring.routes import router

app = FastAPI()

# Add monitoring middleware
app.add_middleware(MonitoringMiddleware)

# Include monitoring routes
app.include_router(router)
```

### 2. Basic Usage

```python
from backend.services.monitoring.service import monitoring_service
from backend.services.monitoring.schemas import MetricCreate, MetricType

# Record a performance metric
await monitoring_service.record_metric(MetricCreate(
    metric_name="api.response_time",
    metric_type=MetricType.HISTOGRAM,
    value=125.5,
    unit="ms",
    tags={"endpoint": "/api/v1/students", "method": "GET"},
    source="api"
))

# Log an error
await monitoring_service.log_error(ErrorLogCreate(
    error_type="ValidationError",
    error_message="Invalid student ID format",
    severity=Severity.WARNING,
    endpoint="/api/v1/students",
    http_method="POST"
))
```

### 3. Health Checks

```python
# Check system health
health_status = await monitoring_service.get_system_metrics()
print(f"CPU Usage: {health_status['cpu_usage']}%")
print(f"Memory Usage: {health_status['memory_usage']}%")
```

## API Endpoints

### Public Endpoints

- `GET /api/v1/monitoring/health` - System health check
- `GET /api/v1/monitoring/status` - Service status
- `GET /api/v1/monitoring/export/prometheus` - Prometheus metrics export

### Protected Endpoints (Authentication Required)

- `GET /api/v1/monitoring/metrics` - Query performance metrics
- `POST /api/v1/monitoring/metrics` - Record custom metrics
- `GET /api/v1/monitoring/alerts` - Get active alerts
- `GET /api/v1/monitoring/dashboard` - Monitoring dashboard data
- `GET /api/v1/monitoring/system` - System performance metrics
- `GET /api/v1/monitoring/database` - Database performance metrics
- `GET /api/v1/monitoring/errors` - Error logs and statistics
- `GET /api/v1/monitoring/traces/{trace_id}` - Distributed trace details

### Admin Endpoints

- `POST /api/v1/monitoring/alerts` - Create new alerts
- `POST /api/v1/monitoring/alerts/{alert_id}/resolve` - Resolve alerts
- `POST /api/v1/monitoring/cleanup` - Clean up old monitoring data

## Configuration

### Environment Variables

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/oneclass_monitoring

# SMTP Configuration for Email Alerts
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=alerts@oneclass.ac.zw
SMTP_PASSWORD=your_app_password
ALERT_FROM_EMAIL=alerts@oneclass.ac.zw
ALERT_TO_EMAILS=admin@oneclass.ac.zw,ops@oneclass.ac.zw

# Slack Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
SLACK_CHANNEL=#alerts
SLACK_USERNAME=OneClass Alerts

# Webhook Configuration
ALERT_WEBHOOK_URL=https://your-webhook-endpoint.com/alerts
ALERT_WEBHOOK_HEADERS={"Authorization": "Bearer token"}

# Monitoring Configuration
METRIC_RETENTION_DAYS=30
LOG_RETENTION_DAYS=90
ALERT_RETENTION_DAYS=365
ENABLE_DISTRIBUTED_TRACING=true
TRACE_SAMPLE_RATE=0.1
```

### Programmatic Configuration

```python
from backend.services.monitoring.service import monitoring_service
from backend.services.monitoring.schemas import MonitoringConfiguration

config = MonitoringConfiguration(
    metric_retention_days=30,
    log_retention_days=90,
    alert_retention_days=365,
    health_check_interval=60,
    enable_tracing=True,
    sample_rate=0.1
)

monitoring_service.config = config
```

## Components

### 1. Monitoring Service (`service.py`)

Core service for recording metrics, logging errors, and managing monitoring data.

```python
from backend.services.monitoring.service import monitoring_service

# Record system metrics
await monitoring_service.get_system_metrics()

# Query historical metrics
metrics = await monitoring_service.query_metrics(MetricQuery(
    metric_name="api.response_time",
    start_time=datetime.utcnow() - timedelta(hours=24),
    limit=1000
))
```

### 2. Monitoring Middleware (`middleware.py`)

Automatic monitoring middleware for FastAPI applications.

```python
from backend.services.monitoring.middleware import MonitoringMiddleware

# Add to FastAPI app
app.add_middleware(MonitoringMiddleware, 
                   enable_tracing=True, 
                   enable_metrics=True)
```

### 3. Alerting System (`alerting.py`)

Advanced alerting with multiple notification channels.

```python
from backend.services.monitoring.alerting import alerting_service, AlertRule, AlertCondition

# Add custom alert rule
rule = AlertRule(
    name="High API Error Rate",
    metric_name="api.error_rate",
    condition=AlertCondition.GREATER_THAN,
    threshold=5.0,
    duration=300,
    severity=Severity.WARNING,
    notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK]
)

alerting_service.add_rule(rule)
```

### 4. Database Models (`models.py`)

Comprehensive database models for storing monitoring data.

- `PerformanceMetric` - Performance metrics storage
- `SystemHealth` - Health check results
- `ErrorLog` - Error logging
- `RequestTrace` - Distributed tracing
- `Alert` - Alert management
- `AuditLog` - Audit trail
- `SecurityEvent` - Security monitoring

## Monitoring Dashboard

Access the monitoring dashboard at `/api/v1/monitoring/dashboard` to get:

- System health overview
- Active alerts summary
- Performance metrics visualization
- Error rate trends
- Resource utilization charts

## Alerting Rules

### Default Alert Rules

1. **High CPU Usage** (>80% for 5 minutes)
2. **Critical CPU Usage** (>95% for 1 minute)
3. **High Memory Usage** (>85% for 5 minutes)
4. **Critical Memory Usage** (>95% for 1 minute)
5. **High Error Rate** (>5% for 5 minutes)
6. **Database Connection Issues** (>100 connections for 3 minutes)
7. **Slow Response Time** (>2000ms for 5 minutes)
8. **Service Down** (Health check failed for 1 minute)

### Custom Alert Rules

```python
from backend.services.monitoring.alerting import AlertRule, AlertCondition

# Create custom rule
custom_rule = AlertRule(
    name="High Student Registration Rate",
    description="Unusual spike in student registrations",
    metric_name="business.student_registrations",
    condition=AlertCondition.GREATER_THAN,
    threshold=100.0,
    duration=600,  # 10 minutes
    severity=Severity.INFO,
    notification_channels=[NotificationChannel.EMAIL]
)

alerting_service.add_rule(custom_rule)
```

## Distributed Tracing

### Automatic Tracing

The monitoring middleware automatically creates traces for HTTP requests:

```python
# Traces are created automatically for all HTTP requests
# No additional code required
```

### Manual Tracing

```python
from backend.services.monitoring.service import monitoring_service
from backend.services.monitoring.schemas import TraceSpanCreate

# Start custom trace
trace_data = TraceSpanCreate(
    trace_id="custom_trace_123",
    span_id="span_456",
    operation_name="process_student_data",
    service_name="student_service",
    start_time=datetime.utcnow(),
    tags={"student_id": "123", "operation": "enrollment"}
)

await monitoring_service.start_trace(trace_data)

# ... perform operation ...

# Finish trace
await monitoring_service.finish_trace(
    "custom_trace_123",
    datetime.utcnow(),
    "success"
)
```

## Security Monitoring

### Automatic Security Event Detection

The system automatically detects and logs:

- Authentication failures
- Suspicious request patterns
- SQL injection attempts
- XSS attempts
- Rate limit violations
- Unusual access patterns

### Manual Security Event Logging

```python
from backend.services.monitoring.service import monitoring_service
from backend.services.monitoring.schemas import SecurityEventCreate

await monitoring_service.log_security_event(SecurityEventCreate(
    event_type="suspicious_login",
    severity=Severity.WARNING,
    description="Multiple failed login attempts from same IP",
    ip_address="192.168.1.100",
    user_id="user123",
    additional_data={"attempt_count": 5}
))
```

## Performance Optimization

### Metric Aggregation

```python
# Query aggregated metrics
from backend.services.monitoring.service import monitoring_service

metrics = await monitoring_service.query_metrics(MetricQuery(
    metric_name="api.response_time",
    start_time=datetime.utcnow() - timedelta(hours=24),
    aggregation="avg",
    group_by=["endpoint", "method"]
))
```

### Data Retention

Automatic cleanup of old data based on retention policies:

- Metrics: 30 days (configurable)
- Logs: 90 days (configurable)
- Alerts: 365 days (configurable)

## Integration Examples

### Prometheus Integration

```python
# Export metrics in Prometheus format
GET /api/v1/monitoring/export/prometheus

# Sample output:
# system_cpu_usage 45.2
# system_memory_usage 72.1
# http_requests_total{method="GET",endpoint="/api/v1/students"} 1247
```

### Grafana Dashboard

Create Grafana dashboards using the Prometheus metrics endpoint or direct database queries.

### ELK Stack Integration

Forward logs to Elasticsearch for advanced log analysis:

```python
# Configure log forwarding
import logging
from pythonjsonlogger import jsonlogger

# Setup JSON logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
```

## Testing

### Unit Tests

```python
import pytest
from backend.services.monitoring.service import monitoring_service
from backend.services.monitoring.schemas import MetricCreate, MetricType

@pytest.mark.asyncio
async def test_record_metric():
    metric_data = MetricCreate(
        metric_name="test.metric",
        metric_type=MetricType.COUNTER,
        value=1.0,
        source="test"
    )
    
    metric_id = await monitoring_service.record_metric(metric_data)
    assert metric_id is not None
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_monitoring_middleware():
    from fastapi.testclient import TestClient
    from backend.services.monitoring.middleware import MonitoringMiddleware
    
    app = FastAPI()
    app.add_middleware(MonitoringMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    client = TestClient(app)
    response = client.get("/test")
    
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Check database credentials and connectivity
   - Verify database schema is up to date
   - Check connection pool settings

2. **Alert Notifications Not Working**
   - Verify SMTP/Slack/Webhook configuration
   - Check network connectivity
   - Review notification target settings

3. **High Memory Usage**
   - Adjust metric retention periods
   - Implement metric sampling
   - Monitor metric buffer sizes

4. **Missing Metrics**
   - Check middleware configuration
   - Verify metric recording calls
   - Review error logs for failures

### Debug Mode

Enable debug logging:

```python
import logging

logging.getLogger("backend.services.monitoring").setLevel(logging.DEBUG)
```

## Best Practices

1. **Metric Naming**
   - Use consistent naming conventions
   - Include relevant tags for filtering
   - Avoid high-cardinality dimensions

2. **Alert Configuration**
   - Set appropriate thresholds
   - Use cooldown periods to prevent spam
   - Test alert channels regularly

3. **Data Retention**
   - Balance storage costs with data needs
   - Implement data archiving for compliance
   - Regular cleanup of old data

4. **Performance**
   - Use sampling for high-volume metrics
   - Buffer metrics for batch processing
   - Monitor the monitoring system itself

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For support and questions:

- **Email**: monitoring@oneclass.ac.zw
- **Documentation**: https://docs.oneclass.ac.zw/monitoring
- **GitHub Issues**: https://github.com/oneclass/platform/issues