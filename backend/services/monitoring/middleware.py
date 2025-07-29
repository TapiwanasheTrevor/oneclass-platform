"""
Monitoring Middleware
FastAPI middleware for automatic performance monitoring
"""

import time
import uuid
import logging
from typing import Callable, Dict, Any, Optional
from datetime import datetime
from fastapi import Request, Response, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.types import Message
import json

from .service import monitoring_service
from .schemas import (
    MetricCreate, ErrorLogCreate, TraceSpanCreate, AuditLogCreate,
    SecurityEventCreate, Severity, MetricType
)

logger = logging.getLogger(__name__)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic performance monitoring"""
    
    def __init__(self, app, enable_tracing: bool = True, enable_metrics: bool = True):
        super().__init__(app)
        self.enable_tracing = enable_tracing
        self.enable_metrics = enable_metrics
        self.excluded_paths = {
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/favicon.ico"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and response with monitoring"""
        start_time = time.time()
        request_id = str(uuid.uuid4())
        trace_id = request.headers.get("X-Trace-Id", request_id)
        
        # Add request ID to request state
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        
        # Skip monitoring for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Start tracing
        if self.enable_tracing:
            await self._start_trace(request, trace_id, start_time)
        
        # Process request
        response = None
        error = None
        
        try:
            response = await call_next(request)
            
        except Exception as e:
            error = e
            # Log error
            await self._log_error(request, e, request_id)
            
            # Create error response
            if isinstance(e, HTTPException):
                response = Response(
                    content=json.dumps({"error": str(e.detail)}),
                    status_code=e.status_code,
                    headers={"content-type": "application/json"}
                )
            else:
                response = Response(
                    content=json.dumps({"error": "Internal server error"}),
                    status_code=500,
                    headers={"content-type": "application/json"}
                )
        
        # Calculate response time
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Add monitoring headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = str(response_time)
        
        # Record metrics
        if self.enable_metrics:
            await self._record_metrics(request, response, response_time, error)
        
        # Finish tracing
        if self.enable_tracing:
            await self._finish_trace(trace_id, end_time, error)
        
        # Log audit event for sensitive operations
        await self._log_audit_event(request, response, request_id)
        
        # Check for security events
        await self._check_security_events(request, response, request_id)
        
        return response
    
    async def _start_trace(self, request: Request, trace_id: str, start_time: float) -> None:
        """Start distributed tracing"""
        try:
            trace_data = TraceSpanCreate(
                trace_id=trace_id,
                span_id=str(uuid.uuid4()),
                parent_span_id=request.headers.get("X-Parent-Span-Id"),
                operation_name=f"{request.method} {request.url.path}",
                service_name="oneclass-api",
                start_time=datetime.fromtimestamp(start_time),
                status="active",
                tags={
                    "http.method": request.method,
                    "http.url": str(request.url),
                    "http.route": request.url.path,
                    "user.agent": request.headers.get("user-agent", ""),
                    "client.ip": self._get_client_ip(request)
                }
            )
            
            await monitoring_service.start_trace(trace_data)
            
        except Exception as e:
            logger.error(f"Failed to start trace: {str(e)}")
    
    async def _finish_trace(self, trace_id: str, end_time: float, error: Optional[Exception]) -> None:
        """Finish distributed tracing"""
        try:
            status = "error" if error else "success"
            await monitoring_service.finish_trace(
                trace_id,
                datetime.fromtimestamp(end_time),
                status
            )
            
        except Exception as e:
            logger.error(f"Failed to finish trace: {str(e)}")
    
    async def _record_metrics(self, request: Request, response: Response, response_time: float, error: Optional[Exception]) -> None:
        """Record performance metrics"""
        try:
            # Request count metric
            await monitoring_service.record_metric(MetricCreate(
                metric_name="http.requests.total",
                metric_type=MetricType.COUNTER,
                value=1,
                unit="count",
                tags={
                    "method": request.method,
                    "endpoint": request.url.path,
                    "status": str(response.status_code),
                    "error": str(error.__class__.__name__) if error else "none"
                },
                source="api"
            ))
            
            # Response time metric
            await monitoring_service.record_metric(MetricCreate(
                metric_name="http.request.duration",
                metric_type=MetricType.HISTOGRAM,
                value=response_time,
                unit="ms",
                tags={
                    "method": request.method,
                    "endpoint": request.url.path,
                    "status": str(response.status_code)
                },
                source="api"
            ))
            
            # Error rate metric
            if error or response.status_code >= 400:
                await monitoring_service.record_metric(MetricCreate(
                    metric_name="http.errors.total",
                    metric_type=MetricType.COUNTER,
                    value=1,
                    unit="count",
                    tags={
                        "method": request.method,
                        "endpoint": request.url.path,
                        "status": str(response.status_code),
                        "error_type": str(error.__class__.__name__) if error else "http_error"
                    },
                    source="api"
                ))
            
        except Exception as e:
            logger.error(f"Failed to record metrics: {str(e)}")
    
    async def _log_error(self, request: Request, error: Exception, request_id: str) -> None:
        """Log error details"""
        try:
            # Get request body if available
            request_data = None
            if hasattr(request, '_body'):
                try:
                    request_data = json.loads(request._body.decode())
                except:
                    request_data = {"body": request._body.decode() if request._body else None}
            
            # Determine severity
            severity = Severity.ERROR
            if isinstance(error, HTTPException):
                if error.status_code >= 500:
                    severity = Severity.ERROR
                elif error.status_code >= 400:
                    severity = Severity.WARNING
            else:
                severity = Severity.CRITICAL
            
            error_data = ErrorLogCreate(
                error_type=error.__class__.__name__,
                error_message=str(error),
                stack_trace=self._get_stack_trace(error),
                request_id=request_id,
                user_id=getattr(request.state, 'user_id', None),
                endpoint=request.url.path,
                http_method=request.method,
                http_status=getattr(error, 'status_code', 500),
                request_data=request_data,
                context={
                    "headers": dict(request.headers),
                    "query_params": dict(request.query_params),
                    "path_params": dict(request.path_params),
                    "client_ip": self._get_client_ip(request)
                },
                severity=severity
            )
            
            await monitoring_service.log_error(error_data)
            
        except Exception as e:
            logger.error(f"Failed to log error: {str(e)}")
    
    async def _log_audit_event(self, request: Request, response: Response, request_id: str) -> None:
        """Log audit events for sensitive operations"""
        try:
            # Define sensitive operations
            sensitive_operations = {
                "POST": ["users", "schools", "students", "teachers"],
                "PUT": ["users", "schools", "students", "teachers"],
                "DELETE": ["users", "schools", "students", "teachers"],
                "PATCH": ["users", "schools", "students", "teachers"]
            }
            
            # Check if this is a sensitive operation
            method = request.method
            path = request.url.path
            
            if method in sensitive_operations:
                for resource in sensitive_operations[method]:
                    if resource in path:
                        audit_data = AuditLogCreate(
                            user_id=getattr(request.state, 'user_id', None),
                            username=getattr(request.state, 'username', None),
                            action=f"{method} {path}",
                            resource_type=resource,
                            resource_id=request.path_params.get('id'),
                            ip_address=self._get_client_ip(request),
                            user_agent=request.headers.get("user-agent", ""),
                            request_id=request_id,
                            school_id=getattr(request.state, 'school_id', None),
                            success=response.status_code < 400
                        )
                        
                        await monitoring_service.log_audit_event(audit_data)
                        break
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
    
    async def _check_security_events(self, request: Request, response: Response, request_id: str) -> None:
        """Check for security events"""
        try:
            # Check for suspicious patterns
            
            # Multiple failed authentication attempts
            if response.status_code == 401:
                await monitoring_service.log_security_event(SecurityEventCreate(
                    event_type="authentication_failure",
                    severity=Severity.WARNING,
                    description="Authentication failed",
                    user_id=getattr(request.state, 'user_id', None),
                    username=getattr(request.state, 'username', None),
                    ip_address=self._get_client_ip(request),
                    user_agent=request.headers.get("user-agent", ""),
                    request_id=request_id,
                    endpoint=request.url.path,
                    additional_data={
                        "method": request.method,
                        "status": response.status_code
                    }
                ))
            
            # Suspicious request patterns
            suspicious_patterns = [
                "script", "javascript", "eval", "alert", "onload",
                "union", "select", "drop", "delete", "insert",
                "../", "..\\", "cmd", "powershell", "bash"
            ]
            
            query_string = str(request.query_params).lower()
            path = request.url.path.lower()
            
            for pattern in suspicious_patterns:
                if pattern in query_string or pattern in path:
                    await monitoring_service.log_security_event(SecurityEventCreate(
                        event_type="suspicious_request",
                        severity=Severity.WARNING,
                        description=f"Suspicious pattern detected: {pattern}",
                        ip_address=self._get_client_ip(request),
                        user_agent=request.headers.get("user-agent", ""),
                        request_id=request_id,
                        endpoint=request.url.path,
                        additional_data={
                            "pattern": pattern,
                            "query_params": dict(request.query_params)
                        }
                    ))
                    break
            
        except Exception as e:
            logger.error(f"Failed to check security events: {str(e)}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(',')[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        return request.client.host if request.client else "unknown"
    
    def _get_stack_trace(self, error: Exception) -> str:
        """Get stack trace from exception"""
        import traceback
        return traceback.format_exc()


class MetricsCollectionMiddleware:
    """Middleware for collecting custom metrics"""
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Collect metrics during request processing"""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Update counters
            self.request_count += 1
            
            # Record response time
            response_time = (time.time() - start_time) * 1000
            self.response_times.append(response_time)
            
            # Keep only last 1000 response times
            if len(self.response_times) > 1000:
                self.response_times = self.response_times[-1000:]
            
            # Count errors
            if response.status_code >= 400:
                self.error_count += 1
            
            return response
            
        except Exception as e:
            self.error_count += 1
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics"""
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)
            max_response_time = max(self.response_times)
            min_response_time = min(self.response_times)
        else:
            avg_response_time = 0
            max_response_time = 0
            min_response_time = 0
        
        error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0
        
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": error_rate,
            "avg_response_time": avg_response_time,
            "max_response_time": max_response_time,
            "min_response_time": min_response_time
        }


# Global metrics collection instance
metrics_collector = MetricsCollectionMiddleware()