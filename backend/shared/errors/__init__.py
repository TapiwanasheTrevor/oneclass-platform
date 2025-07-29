# =====================================================
# Comprehensive Error Handling System
# Centralized error management for the OneClass platform
# File: backend/shared/errors/__init__.py
# =====================================================

from .exceptions import (
    OneClassException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    ExternalServiceError,
    DatabaseError,
    FileProcessingError,
    BulkOperationError,
    SchoolContextError,
    InvitationError,
    OnboardingError,
    NotificationError,
    PaymentError,
    SubscriptionError
)

from .handlers import (
    error_handler,
    validation_error_handler,
    http_exception_handler,
    generic_exception_handler,
    setup_error_handlers
)

from .schemas import (
    ErrorResponse,
    ErrorDetail,
    ValidationErrorDetail,
    BulkOperationErrorDetail
)

from .middleware import ErrorHandlingMiddleware

from .validators import (
    validate_email,
    validate_phone_number,
    validate_zimbabwe_id,
    validate_school_id,
    validate_user_role,
    validate_file_type,
    validate_date_range,
    validate_pagination
)

__all__ = [
    # Exceptions
    "OneClassException",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "ExternalServiceError",
    "DatabaseError",
    "FileProcessingError",
    "BulkOperationError",
    "SchoolContextError",
    "InvitationError",
    "OnboardingError",
    "NotificationError",
    "PaymentError",
    "SubscriptionError",
    
    # Handlers
    "error_handler",
    "validation_error_handler",
    "http_exception_handler",
    "generic_exception_handler",
    "setup_error_handlers",
    
    # Schemas
    "ErrorResponse",
    "ErrorDetail",
    "ValidationErrorDetail",
    "BulkOperationErrorDetail",
    
    # Middleware
    "ErrorHandlingMiddleware",
    
    # Validators
    "validate_email",
    "validate_phone_number",
    "validate_zimbabwe_id",
    "validate_school_id",
    "validate_user_role",
    "validate_file_type",
    "validate_date_range",
    "validate_pagination"
]