"""
Shared Exception Classes
Reusable exceptions for all backend services.
"""


class OneClassError(Exception):
    """Base exception for OneClass platform."""

    def __init__(self, message: str = "An error occurred", code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ValidationError(OneClassError):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Validation failed", details: dict | None = None):
        self.details = details or {}
        super().__init__(message=message, code="VALIDATION_ERROR")


class NotFoundError(OneClassError):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str = "Resource", identifier: str = ""):
        message = f"{resource} not found" if not identifier else f"{resource} '{identifier}' not found"
        self.resource = resource
        self.identifier = identifier
        super().__init__(message=message, code="NOT_FOUND")


class ConflictError(OneClassError):
    """Raised when an operation conflicts with existing state."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message=message, code="CONFLICT")


class ExternalServiceError(OneClassError):
    """Raised when a third-party or external dependency fails."""

    def __init__(self, message: str = "External service failure"):
        super().__init__(message=message, code="EXTERNAL_SERVICE_ERROR")


class AuthenticationError(OneClassError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, code="AUTHENTICATION_ERROR")


class AuthorizationError(OneClassError):
    """Raised when a user lacks permission for an action."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, code="AUTHORIZATION_ERROR")


class InsufficientFundsError(OneClassError):
    """Raised when a financial operation fails due to insufficient funds."""

    def __init__(self, message: str = "Insufficient funds"):
        super().__init__(message=message, code="INSUFFICIENT_FUNDS")


class RateLimitError(OneClassError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(message=message, code="RATE_LIMIT_EXCEEDED")


class TenantError(OneClassError):
    """Raised for multi-tenant isolation issues."""

    def __init__(self, message: str = "Tenant operation failed"):
        super().__init__(message=message, code="TENANT_ERROR")
