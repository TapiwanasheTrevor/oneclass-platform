# =====================================================
# Error Handlers
# Centralized error handling for the OneClass platform
# File: backend/shared/errors/handlers.py
# =====================================================

import logging
import traceback
import uuid
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import OneClassException
from .schemas import (
    ErrorResponse,
    ValidationErrorResponse,
    ValidationErrorDetail,
    ErrorCategory,
    ErrorSeverity,
    create_error_response,
    create_validation_error_response,
)


def custom_json_encoder(obj):
    """Custom JSON encoder for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def create_json_response(status_code: int, content: Any) -> JSONResponse:
    """Create a JSONResponse with custom datetime encoding"""
    if hasattr(content, "model_dump"):
        # Use Pydantic's model_dump for proper serialization
        json_content = content.model_dump()
    elif hasattr(content, "dict"):
        # Fallback to dict() method
        json_content = content.dict()
    else:
        json_content = content

    # Convert to JSON string with custom encoder, then back to dict for JSONResponse
    json_str = json.dumps(json_content, default=custom_json_encoder)
    return JSONResponse(status_code=status_code, content=json.loads(json_str))


logger = logging.getLogger(__name__)


class ErrorLogger:
    """Centralized error logging with context"""

    @staticmethod
    def log_error(
        error: Exception,
        request: Optional[Request] = None,
        user_id: Optional[str] = None,
        school_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """Log error with full context"""

        context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "school_id": school_id,
        }

        if request:
            context.update(
                {
                    "method": request.method,
                    "url": str(request.url),
                    "headers": dict(request.headers),
                    "client_ip": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                }
            )

        if extra_context:
            context.update(extra_context)

        # Log at appropriate level
        if isinstance(error, OneClassException):
            if error.status_code >= 500:
                logger.error(f"Server error: {error.message}", extra=context)
            elif error.status_code >= 400:
                logger.warning(f"Client error: {error.message}", extra=context)
            else:
                logger.info(f"Application error: {error.message}", extra=context)
        else:
            logger.error(
                f"Unexpected error: {str(error)}", extra=context, exc_info=True
            )

        return context["correlation_id"]


def extract_user_context(request: Request) -> Dict[str, Optional[str]]:
    """Extract user context from request"""

    user_id = None
    school_id = None

    # Try to get user context from state (set by auth middleware)
    if hasattr(request.state, "user"):
        user = request.state.user
        user_id = str(user.id) if hasattr(user, "id") else None
        if hasattr(user, "primary_school_id") and user.primary_school_id:
            school_id = str(user.primary_school_id)

    return {"user_id": user_id, "school_id": school_id}


async def oneclass_exception_handler(
    request: Request, exc: OneClassException
) -> JSONResponse:
    """Handle OneClass custom exceptions"""

    user_context = extract_user_context(request)
    correlation_id = ErrorLogger.log_error(error=exc, request=request, **user_context)

    # Map exception to error category
    category_mapping = {
        "ValidationError": ErrorCategory.VALIDATION,
        "AuthenticationError": ErrorCategory.AUTHENTICATION,
        "AuthorizationError": ErrorCategory.AUTHORIZATION,
        "NotFoundError": ErrorCategory.NOT_FOUND,
        "ConflictError": ErrorCategory.CONFLICT,
        "RateLimitError": ErrorCategory.RATE_LIMIT,
        "ExternalServiceError": ErrorCategory.EXTERNAL_SERVICE,
        "DatabaseError": ErrorCategory.DATABASE,
        "FileProcessingError": ErrorCategory.FILE_PROCESSING,
        "BulkOperationError": ErrorCategory.BULK_OPERATION,
        "SchoolContextError": ErrorCategory.SCHOOL_CONTEXT,
        "InvitationError": ErrorCategory.INVITATION,
        "OnboardingError": ErrorCategory.ONBOARDING,
        "NotificationError": ErrorCategory.NOTIFICATION,
        "PaymentError": ErrorCategory.PAYMENT,
        "SubscriptionError": ErrorCategory.SUBSCRIPTION,
    }

    category = category_mapping.get(type(exc).__name__, ErrorCategory.SYSTEM)

    # Determine severity based on status code
    if exc.status_code >= 500:
        severity = ErrorSeverity.HIGH
    elif exc.status_code >= 400:
        severity = ErrorSeverity.MEDIUM
    else:
        severity = ErrorSeverity.LOW

    error_response = ErrorResponse(
        error_code=exc.error_code,
        message=exc.message,
        user_message=exc.user_message,
        category=category,
        severity=severity,
        details=exc.details,
        correlation_id=correlation_id,
        retry_possible=exc.status_code >= 500,
        suggestions=get_error_suggestions(exc),
    )

    return create_json_response(status_code=exc.status_code, content=error_response)


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle FastAPI validation errors"""

    user_context = extract_user_context(request)
    correlation_id = ErrorLogger.log_error(error=exc, request=request, **user_context)

    # Convert FastAPI validation errors to our format
    validation_errors = []
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])

        validation_error = ValidationErrorDetail(
            field=field_path,
            message=error["msg"],
            code=error["type"],
            value=error.get("input"),
            location="body" if error["loc"][0] == "body" else str(error["loc"][0]),
        )
        validation_errors.append(validation_error)

    error_response = create_validation_error_response(
        message="Request validation failed", errors=validation_errors
    )
    error_response.correlation_id = correlation_id

    return create_json_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error_response
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""

    user_context = extract_user_context(request)
    correlation_id = ErrorLogger.log_error(error=exc, request=request, **user_context)

    # Map HTTP status codes to categories
    category_mapping = {
        400: ErrorCategory.VALIDATION,
        401: ErrorCategory.AUTHENTICATION,
        403: ErrorCategory.AUTHORIZATION,
        404: ErrorCategory.NOT_FOUND,
        409: ErrorCategory.CONFLICT,
        422: ErrorCategory.VALIDATION,
        429: ErrorCategory.RATE_LIMIT,
        500: ErrorCategory.SYSTEM,
        502: ErrorCategory.EXTERNAL_SERVICE,
        503: ErrorCategory.EXTERNAL_SERVICE,
        504: ErrorCategory.EXTERNAL_SERVICE,
    }

    category = category_mapping.get(exc.status_code, ErrorCategory.SYSTEM)
    severity = ErrorSeverity.HIGH if exc.status_code >= 500 else ErrorSeverity.MEDIUM

    error_response = create_error_response(
        error_code=f"HTTP_{exc.status_code}",
        message=exc.detail,
        category=category,
        severity=severity,
        retry_possible=exc.status_code >= 500,
    )
    error_response.correlation_id = correlation_id

    return create_json_response(status_code=exc.status_code, content=error_response)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""

    user_context = extract_user_context(request)
    correlation_id = ErrorLogger.log_error(
        error=exc,
        request=request,
        **user_context,
        extra_context={"traceback": traceback.format_exc()},
    )

    # Don't expose internal error details to users
    error_response = create_error_response(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.CRITICAL,
        user_message="Something went wrong. Please try again or contact support",
        suggestions=[
            "Try refreshing the page",
            "Check your internet connection",
            "Contact support if the problem persists",
        ],
        retry_possible=True,
    )
    error_response.correlation_id = correlation_id
    error_response.support_contact = "support@oneclass.ac.zw"

    return create_json_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_response
    )


def get_error_suggestions(exc: OneClassException) -> List[str]:
    """Get contextual suggestions based on error type"""

    suggestions_map = {
        "ValidationError": [
            "Check that all required fields are provided",
            "Verify that field formats match the expected patterns",
            "Ensure numeric values are within valid ranges",
        ],
        "AuthenticationError": [
            "Check your login credentials",
            "Try logging out and logging back in",
            "Contact your administrator if you're locked out",
        ],
        "AuthorizationError": [
            "Contact your school administrator for access",
            "Verify you're logged into the correct school",
            "Check if your account permissions have changed",
        ],
        "NotFoundError": [
            "Verify the resource ID is correct",
            "Check if the resource was deleted",
            "Try refreshing the page",
        ],
        "ConflictError": [
            "Check for duplicate entries",
            "Verify the resource isn't already in use",
            "Try using a different identifier",
        ],
        "FileProcessingError": [
            "Check the file format is supported",
            "Ensure the file isn't corrupted",
            "Try using a smaller file size",
            "Verify the file contains valid data",
        ],
        "ExternalServiceError": [
            "Try again in a few minutes",
            "Check your internet connection",
            "Contact support if the issue persists",
        ],
        "BulkOperationError": [
            "Review the failed items in the error details",
            "Correct any data format issues",
            "Retry the operation with fixed data",
        ],
    }

    return suggestions_map.get(
        type(exc).__name__,
        ["Try the operation again", "Contact support if the problem persists"],
    )


def setup_error_handlers(app: FastAPI):
    """Set up all error handlers for the FastAPI app"""

    # Custom OneClass exceptions
    app.add_exception_handler(OneClassException, oneclass_exception_handler)

    # FastAPI validation errors
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    # HTTP exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # Generic exception handler (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Error handlers registered successfully")


# Error handler decorator for service methods
def error_handler(
    default_message: str = "Operation failed",
    error_code: str = "OPERATION_ERROR",
    category: ErrorCategory = ErrorCategory.SYSTEM,
    reraise: bool = True,
):
    """Decorator to handle and log errors in service methods"""

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except OneClassException:
                # Re-raise OneClass exceptions as-is
                if reraise:
                    raise
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                if reraise:
                    raise OneClassException(
                        message=f"{default_message}: {str(e)}",
                        error_code=error_code,
                        status_code=500,
                        details={"function": func.__name__, "original_error": str(e)},
                    )
                return None

        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except OneClassException:
                # Re-raise OneClass exceptions as-is
                if reraise:
                    raise
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                if reraise:
                    raise OneClassException(
                        message=f"{default_message}: {str(e)}",
                        error_code=error_code,
                        status_code=500,
                        details={"function": func.__name__, "original_error": str(e)},
                    )
                return None

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
