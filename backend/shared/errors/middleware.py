# =====================================================
# Error Handling Middleware
# Request/response middleware for error tracking and context
# File: backend/shared/errors/middleware.py
# =====================================================

import time
import uuid
import logging
from typing import Callable, Optional, Dict, Any
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .schemas import ErrorResponse, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for error context tracking and monitoring"""
    
    def __init__(
        self,
        app,
        service_name: str = "oneclass-backend",
        version: str = "1.0.0",
        enable_request_logging: bool = True,
        enable_performance_tracking: bool = True
    ):
        super().__init__(app)
        self.service_name = service_name
        self.version = version
        self.enable_request_logging = enable_request_logging
        self.enable_performance_tracking = enable_performance_tracking
        
        # Error tracking
        self.error_counts: Dict[str, int] = {}
        self.request_counts: Dict[str, int] = {}
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add error context"""
        
        # Generate correlation ID for request tracking
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Track request start time
        start_time = time.time()
        request.state.start_time = start_time
        
        # Add correlation ID to response headers
        response_headers = {"X-Correlation-ID": correlation_id}
        
        # Log request if enabled
        if self.enable_request_logging:
            self._log_request(request, correlation_id)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Add standard headers
            for key, value in response_headers.items():
                response.headers[key] = value
            
            # Track performance if enabled
            if self.enable_performance_tracking:
                self._track_performance(request, response, start_time)
            
            # Log successful response
            if self.enable_request_logging:
                self._log_response(request, response, correlation_id)
            
            return response
            
        except Exception as exc:
            # Handle unexpected middleware errors
            logger.error(
                f"Middleware error: {str(exc)}",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "url": str(request.url),
                    "client_ip": request.client.host if request.client else None
                },
                exc_info=True
            )
            
            # Return generic error response
            error_response = ErrorResponse(
                error_code="MIDDLEWARE_ERROR",
                message="Request processing failed",
                user_message="Something went wrong. Please try again",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                correlation_id=correlation_id,
                service=self.service_name,
                version=self.version,
                retry_possible=True
            )
            
            response = JSONResponse(
                status_code=500,
                content=error_response.dict()
            )
            
            # Add headers
            for key, value in response_headers.items():
                response.headers[key] = value
            
            return response
    
    def _log_request(self, request: Request, correlation_id: str):
        """Log incoming request"""
        
        user_id = None
        if hasattr(request.state, "user") and request.state.user:
            user_id = str(request.state.user.id)
        
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def _log_response(self, request: Request, response: Response, correlation_id: str):
        """Log response"""
        
        duration = time.time() - request.state.start_time
        
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "response_size": len(response.body) if hasattr(response, "body") else None
            }
        )
    
    def _track_performance(self, request: Request, response: Response, start_time: float):
        """Track request performance metrics"""
        
        duration = time.time() - start_time
        endpoint = f"{request.method} {request.url.path}"
        
        # Track request counts
        self.request_counts[endpoint] = self.request_counts.get(endpoint, 0) + 1
        
        # Track error counts
        if response.status_code >= 400:
            error_key = f"{endpoint}:{response.status_code}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Log slow requests
        if duration > 5.0:  # 5 seconds threshold
            logger.warning(
                f"Slow request detected: {endpoint}",
                extra={
                    "duration_ms": round(duration * 1000, 2),
                    "method": request.method,
                    "url": str(request.url),
                    "status_code": response.status_code
                }
            )
    
    def get_error_metrics(self) -> Dict[str, Any]:
        """Get current error metrics"""
        
        total_requests = sum(self.request_counts.values())
        total_errors = sum(self.error_counts.values())
        
        return {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": (total_errors / total_requests * 100) if total_requests > 0 else 0,
            "request_counts": self.request_counts.copy(),
            "error_counts": self.error_counts.copy(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def reset_metrics(self):
        """Reset error metrics"""
        self.error_counts.clear()
        self.request_counts.clear()

class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to add request context to all requests"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request context"""
        
        # Add request metadata to state
        request.state.request_id = str(uuid.uuid4())
        request.state.timestamp = datetime.utcnow()
        request.state.client_ip = request.client.host if request.client else None
        request.state.user_agent = request.headers.get("user-agent")
        
        # Extract school context from headers or subdomain
        school_context = self._extract_school_context(request)
        if school_context:
            request.state.school_context = school_context
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response
        response.headers["X-Request-ID"] = request.state.request_id
        
        return response
    
    def _extract_school_context(self, request: Request) -> Optional[str]:
        """Extract school context from request"""
        
        # Try to get from custom header
        school_id = request.headers.get("X-School-ID")
        if school_id:
            return school_id
        
        # Try to extract from subdomain
        host = request.headers.get("host", "")
        if host and host != "localhost" and "oneclass.ac.zw" in host:
            parts = host.split(".")
            if len(parts) >= 3 and parts[0] != "www":
                # Subdomain format: schoolname.oneclass.ac.zw
                return parts[0]
        
        return None

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response"""
        
        response = await call_next(request)
        
        # Add security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self' https:; frame-ancestors 'none'"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_limit: int = 100
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.request_history: Dict[str, list] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting"""
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Check rate limit
        if self._is_rate_limited(client_id):
            from .schemas import RateLimitErrorResponse
            
            error_response = RateLimitErrorResponse(
                error_code="RATE_LIMIT_EXCEEDED",
                message="Too many requests",
                user_message="Please slow down and try again later",
                category=ErrorCategory.RATE_LIMIT,
                severity=ErrorSeverity.MEDIUM,
                limit=self.requests_per_minute,
                window="1 minute",
                retry_after=60
            )
            
            return JSONResponse(
                status_code=429,
                content=error_response.dict(),
                headers={"Retry-After": "60"}
            )
        
        # Record request
        self._record_request(client_id)
        
        # Process request
        return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        
        # Try to get user ID from state
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.id}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def _is_rate_limited(self, client_id: str) -> bool:
        """Check if client is rate limited"""
        
        now = time.time()
        
        # Get request history
        if client_id not in self.request_history:
            return False
        
        requests = self.request_history[client_id]
        
        # Remove old requests (older than 1 minute)
        cutoff_time = now - 60
        requests[:] = [req_time for req_time in requests if req_time > cutoff_time]
        
        # Check limits
        return len(requests) >= self.requests_per_minute
    
    def _record_request(self, client_id: str):
        """Record a request for rate limiting"""
        
        now = time.time()
        
        if client_id not in self.request_history:
            self.request_history[client_id] = []
        
        self.request_history[client_id].append(now)
        
        # Keep only recent requests to prevent memory bloat
        if len(self.request_history[client_id]) > self.burst_limit:
            self.request_history[client_id] = self.request_history[client_id][-self.burst_limit:]