"""
Academic Management Module - Error Handling Middleware
Centralized error handling and exception processing for Academic APIs
"""

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging
import traceback
from datetime import datetime

from .exceptions import (
    AcademicBaseException,
    AcademicSystemError,
    create_error_response,
    log_academic_error
)

logger = logging.getLogger(__name__)


class AcademicErrorMiddleware(BaseHTTPMiddleware):
    """Middleware for handling Academic module exceptions and errors"""
    
    def __init__(self, app):
        super().__init__(app)
        
        # Paths that this middleware should handle
        self.academic_paths = [
            "/api/v1/academic/",
            "/academic/"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with Academic error handling"""
        
        # Only process Academic module requests
        if not any(request.url.path.startswith(path) for path in self.academic_paths):
            return await call_next(request)
        
        start_time = datetime.utcnow()
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Log successful requests in debug mode
            duration = (datetime.utcnow() - start_time).total_seconds()
            if response.status_code >= 400:
                logger.warning(
                    f"Academic API warning: {request.method} {request.url.path} "
                    f"- {response.status_code} - {duration:.3f}s"
                )
            
            return response
            
        except AcademicBaseException as e:
            # Handle our custom Academic exceptions
            return await self._handle_academic_exception(e, request, request_id)
            
        except HTTPException as e:
            # Handle FastAPI HTTPExceptions (pass through)
            return await self._handle_http_exception(e, request, request_id)
            
        except Exception as e:
            # Handle unexpected system errors
            return await self._handle_system_exception(e, request, request_id)
    
    async def _handle_academic_exception(
        self, 
        error: AcademicBaseException, 
        request: Request,
        request_id: str
    ) -> JSONResponse:
        """Handle Academic module custom exceptions"""
        
        # Get additional context from request
        context = {
            "request_id": request_id,
            "endpoint": request.url.path,
            "method": request.method,
            "user_agent": request.headers.get("user-agent"),
            "ip_address": request.client.host if request.client else None
        }
        
        # Add tenant context if available
        if hasattr(request.state, 'tenant'):
            context["school_id"] = request.state.tenant.school_id
            context["school_name"] = request.state.tenant.school_name
        
        # Log the error with context
        log_academic_error(error, context)
        
        # Create standardized error response
        error_response = error.to_dict()
        error_response["request_id"] = request_id
        error_response["timestamp"] = datetime.utcnow().isoformat()
        
        return JSONResponse(
            status_code=error.status_code,
            content=error_response
        )
    
    async def _handle_http_exception(
        self, 
        error: HTTPException, 
        request: Request,
        request_id: str
    ) -> JSONResponse:
        """Handle FastAPI HTTPExceptions"""
        
        # Log HTTP exceptions
        logger.warning(
            f"Academic API HTTP exception: {request.method} {request.url.path} "
            f"- {error.status_code} - {error.detail}"
        )
        
        # Standardize response format
        if isinstance(error.detail, dict):
            response_content = error.detail
        else:
            response_content = {
                "error": "http_exception",
                "message": str(error.detail),
                "module": "academic_management"
            }
        
        response_content["request_id"] = request_id
        response_content["timestamp"] = datetime.utcnow().isoformat()
        
        return JSONResponse(
            status_code=error.status_code,
            content=response_content
        )
    
    async def _handle_system_exception(
        self, 
        error: Exception, 
        request: Request,
        request_id: str
    ) -> JSONResponse:
        """Handle unexpected system exceptions"""
        
        # Log the full traceback for system errors
        logger.error(
            f"Academic API system error: {request.method} {request.url.path} "
            f"- {type(error).__name__}: {str(error)}",
            exc_info=True
        )
        
        # Convert to Academic system error
        academic_error = AcademicSystemError(
            message="An unexpected error occurred while processing your request",
            error_code="SYSTEM_ERROR",
            original_error=error
        )
        
        # Get context for logging
        context = {
            "request_id": request_id,
            "endpoint": request.url.path,
            "method": request.method,
            "error_type": type(error).__name__,
            "traceback": traceback.format_exc()
        }
        
        # Add tenant context if available
        if hasattr(request.state, 'tenant'):
            context["school_id"] = request.state.tenant.school_id
        
        # Log with context
        log_academic_error(academic_error, context)
        
        # Create error response (hide internal details in production)
        error_response = academic_error.to_dict()
        error_response["request_id"] = request_id
        error_response["timestamp"] = datetime.utcnow().isoformat()
        
        # In development, include more details
        import os
        if os.getenv("ENVIRONMENT", "production").lower() in ["development", "dev", "local"]:
            error_response["debug_info"] = {
                "error_type": type(error).__name__,
                "error_message": str(error)
            }
        
        return JSONResponse(
            status_code=500,
            content=error_response
        )


class AcademicValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for Academic module request validation"""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate Academic module requests"""
        
        # Only process Academic module requests
        if not request.url.path.startswith("/api/v1/academic/"):
            return await call_next(request)
        
        try:
            # Validate request size
            if request.headers.get("content-length"):
                content_length = int(request.headers["content-length"])
                max_size = 10 * 1024 * 1024  # 10MB limit
                
                if content_length > max_size:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "request_too_large",
                            "message": f"Request size {content_length} exceeds maximum allowed size {max_size}",
                            "module": "academic_management"
                        }
                    )
            
            # Validate content type for POST/PUT requests
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("content-type", "")
                
                if not content_type.startswith("application/json"):
                    return JSONResponse(
                        status_code=415,
                        content={
                            "error": "unsupported_media_type",
                            "message": "Content-Type must be application/json for this endpoint",
                            "module": "academic_management"
                        }
                    )
            
            # Continue with request processing
            response = await call_next(request)
            
            # Add Academic module headers
            response.headers["X-Academic-Module"] = "academic_management"
            response.headers["X-Academic-Version"] = "1.0.0"
            
            return response
            
        except Exception as e:
            logger.error(f"Academic validation middleware error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "validation_middleware_error",
                    "message": "An error occurred during request validation",
                    "module": "academic_management"
                }
            )


# Helper function to add Academic error middleware to FastAPI app
def add_academic_error_middleware(app):
    """Add Academic error handling middleware to FastAPI application"""
    app.add_middleware(AcademicErrorMiddleware)
    app.add_middleware(AcademicValidationMiddleware)
    
    logger.info("Academic Management error handling middleware added")


# Global exception handlers for Academic module
def setup_academic_exception_handlers(app):
    """Set up global exception handlers for Academic module"""
    
    @app.exception_handler(AcademicBaseException)
    async def academic_exception_handler(request: Request, exc: AcademicBaseException):
        """Handle Academic base exceptions globally"""
        
        context = {
            "endpoint": request.url.path,
            "method": request.method,
            "global_handler": True
        }
        
        log_academic_error(exc, context)
        
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict()
        )
    
    logger.info("Academic Management global exception handlers registered")