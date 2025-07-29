# =====================================================
# Error Response Schemas
# Standardized error response models
# File: backend/shared/errors/schemas.py
# =====================================================

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class ErrorSeverity(str, Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for classification"""

    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RATE_LIMIT = "rate_limit"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    FILE_PROCESSING = "file_processing"
    BULK_OPERATION = "bulk_operation"
    SCHOOL_CONTEXT = "school_context"
    INVITATION = "invitation"
    ONBOARDING = "onboarding"
    NOTIFICATION = "notification"
    PAYMENT = "payment"
    SUBSCRIPTION = "subscription"
    SYSTEM = "system"


class ErrorDetail(BaseModel):
    """Individual error detail"""

    field: Optional[str] = None
    message: str
    code: Optional[str] = None
    value: Optional[Any] = None
    location: Optional[str] = None  # query, body, path, header


class ValidationErrorDetail(ErrorDetail):
    """Validation-specific error detail"""

    constraint: Optional[str] = None  # required, format, range, etc.
    expected_type: Optional[str] = None
    actual_type: Optional[str] = None
    allowed_values: Optional[List[Any]] = None


class BulkOperationErrorDetail(BaseModel):
    """Error detail for bulk operations"""

    item_index: int
    item_id: Optional[str] = None
    item_data: Optional[Dict[str, Any]] = None
    errors: List[ErrorDetail]
    severity: ErrorSeverity = ErrorSeverity.MEDIUM


class ErrorResponse(BaseModel):
    """Standardized error response"""

    # Basic error information
    success: bool = False
    error_code: str
    message: str
    user_message: Optional[str] = None

    # Categorization
    category: ErrorCategory
    severity: ErrorSeverity = ErrorSeverity.MEDIUM

    # Detailed error information
    details: Optional[Dict[str, Any]] = None
    errors: Optional[List[Union[ErrorDetail, ValidationErrorDetail]]] = None

    # Context information
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None

    # User guidance
    suggestions: Optional[List[str]] = None
    documentation_url: Optional[str] = None
    support_contact: Optional[str] = None

    # Technical details (for debugging)
    trace_id: Optional[str] = None
    service: Optional[str] = "oneclass-backend"
    version: Optional[str] = None

    # Recovery information
    retry_possible: bool = False
    retry_after: Optional[int] = None  # seconds

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class BulkOperationErrorResponse(ErrorResponse):
    """Error response for bulk operations"""

    total_items: int
    successful_items: int
    failed_items: int
    item_errors: List[BulkOperationErrorDetail]
    partial_success: bool = True


class ValidationErrorResponse(ErrorResponse):
    """Error response for validation failures"""

    validation_errors: List[ValidationErrorDetail]
    invalid_fields: List[str]


class RateLimitErrorResponse(ErrorResponse):
    """Error response for rate limiting"""

    limit: int
    window: str  # "1 minute", "1 hour", etc.
    retry_after: int
    usage_reset_time: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ExternalServiceErrorResponse(ErrorResponse):
    """Error response for external service failures"""

    service_name: str
    service_status: Optional[str] = None
    estimated_recovery_time: Optional[datetime] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class FileProcessingErrorResponse(ErrorResponse):
    """Error response for file processing failures"""

    filename: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    supported_formats: Optional[List[str]] = None
    max_file_size: Optional[int] = None


class DatabaseErrorResponse(ErrorResponse):
    """Error response for database failures"""

    operation: str
    affected_table: Optional[str] = None
    query_id: Optional[str] = None


class AuthenticationErrorResponse(ErrorResponse):
    """Error response for authentication failures"""

    login_url: Optional[str] = None
    token_expired: bool = False
    multi_factor_required: bool = False


class AuthorizationErrorResponse(ErrorResponse):
    """Error response for authorization failures"""

    required_permissions: Optional[List[str]] = None
    current_role: Optional[str] = None
    required_role: Optional[str] = None
    school_context_required: bool = False


class HealthCheckErrorResponse(BaseModel):
    """Health check error response"""

    service: str
    status: str = "unhealthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    errors: List[str]
    dependencies: Optional[Dict[str, str]] = None  # service_name -> status

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ErrorMetrics(BaseModel):
    """Error metrics for monitoring"""

    error_code: str
    count: int
    rate: float  # errors per minute
    first_occurrence: datetime
    last_occurrence: datetime
    affected_users: int
    affected_schools: int

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ErrorSummary(BaseModel):
    """Summary of errors for a time period"""

    period_start: datetime
    period_end: datetime
    total_errors: int
    unique_errors: int
    error_rate: float
    top_errors: List[ErrorMetrics]
    by_category: Dict[ErrorCategory, int]
    by_severity: Dict[ErrorSeverity, int]
    by_service: Dict[str, int]

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# Helper functions for creating standardized responses
def create_error_response(
    error_code: str,
    message: str,
    category: ErrorCategory,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    user_message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    suggestions: Optional[List[str]] = None,
    retry_possible: bool = False,
) -> ErrorResponse:
    """Create a standardized error response"""

    return ErrorResponse(
        error_code=error_code,
        message=message,
        user_message=user_message or message,
        category=category,
        severity=severity,
        details=details,
        suggestions=suggestions,
        retry_possible=retry_possible,
    )


def create_validation_error_response(
    message: str = "Validation failed",
    errors: List[ValidationErrorDetail] = None,
    user_message: str = "Please check your input and try again",
) -> ValidationErrorResponse:
    """Create a validation error response"""

    errors = errors or []
    invalid_fields = [error.field for error in errors if error.field]

    return ValidationErrorResponse(
        error_code="VALIDATION_ERROR",
        message=message,
        user_message=user_message,
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.LOW,
        validation_errors=errors,
        invalid_fields=invalid_fields,
        suggestions=[
            "Check required fields are provided",
            "Verify data formats are correct",
            "Ensure values are within acceptable ranges",
        ],
    )


def create_bulk_operation_error_response(
    operation_type: str,
    total_items: int,
    failed_items: int,
    item_errors: List[BulkOperationErrorDetail],
    message: Optional[str] = None,
) -> BulkOperationErrorResponse:
    """Create a bulk operation error response"""

    successful_items = total_items - failed_items
    message = message or f"Bulk {operation_type} completed with {failed_items} failures"

    return BulkOperationErrorResponse(
        error_code="BULK_OPERATION_ERROR",
        message=message,
        user_message=f"Operation completed: {successful_items} successful, {failed_items} failed",
        category=ErrorCategory.BULK_OPERATION,
        severity=(
            ErrorSeverity.MEDIUM
            if failed_items < total_items // 2
            else ErrorSeverity.HIGH
        ),
        total_items=total_items,
        successful_items=successful_items,
        failed_items=failed_items,
        item_errors=item_errors,
        partial_success=successful_items > 0,
        suggestions=[
            "Review failed items and correct any data issues",
            "Retry the operation for failed items only",
            "Contact support if errors persist",
        ],
    )
