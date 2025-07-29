# =====================================================
# Custom Exception Classes
# Domain-specific exceptions for the OneClass platform
# File: backend/shared/errors/exceptions.py
# =====================================================

from typing import Optional, Dict, Any, List, Union
from uuid import UUID


class OneClassException(Exception):
    """Base exception for all OneClass platform errors"""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.user_message = user_message or message


class ValidationError(OneClassException):
    """Raised when request validation fails"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        errors: Optional[List[Dict[str, Any]]] = None,
    ):
        details = {"field": field, "value": value, "errors": errors or []}
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details,
            user_message="Please check your input and try again",
        )


class AuthenticationError(OneClassException):
    """Raised when authentication fails"""

    def __init__(
        self, message: str = "Authentication failed", reason: Optional[str] = None
    ):
        details = {"reason": reason} if reason else {}
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details,
            user_message="Please log in to continue",
        )


class AuthorizationError(OneClassException):
    """Raised when user lacks required permissions"""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permission: Optional[str] = None,
        user_role: Optional[str] = None,
    ):
        details = {"required_permission": required_permission, "user_role": user_role}
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
            details=details,
            user_message="You don't have permission to perform this action",
        )


class NotFoundError(OneClassException):
    """Raised when a requested resource is not found"""

    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[Union[str, UUID]] = None,
        message: Optional[str] = None,
    ):
        if not message:
            message = f"{resource_type} not found"
            if resource_id:
                message += f": {resource_id}"

        details = {
            "resource_type": resource_type,
            "resource_id": str(resource_id) if resource_id else None,
        }
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=404,
            details=details,
            user_message=f"The requested {resource_type.lower()} could not be found",
        )


class ConflictError(OneClassException):
    """Raised when there's a resource conflict"""

    def __init__(
        self,
        message: str,
        resource_type: str,
        conflicting_field: Optional[str] = None,
        existing_value: Optional[Any] = None,
    ):
        details = {
            "resource_type": resource_type,
            "conflicting_field": conflicting_field,
            "existing_value": existing_value,
        }
        super().__init__(
            message=message,
            error_code="CONFLICT",
            status_code=409,
            details=details,
            user_message="This operation conflicts with existing data",
        )


class RateLimitError(OneClassException):
    """Raised when rate limit is exceeded"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit: Optional[int] = None,
        window: Optional[str] = None,
        retry_after: Optional[int] = None,
    ):
        details = {"limit": limit, "window": window, "retry_after": retry_after}
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details,
            user_message="Too many requests. Please try again later",
        )


class ExternalServiceError(OneClassException):
    """Raised when an external service fails"""

    def __init__(
        self,
        service_name: str,
        message: str,
        original_error: Optional[str] = None,
        retry_possible: bool = True,
    ):
        details = {
            "service_name": service_name,
            "original_error": original_error,
            "retry_possible": retry_possible,
        }
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=503,
            details=details,
            user_message=f"Service temporarily unavailable. Please try again later",
        )


class DatabaseError(OneClassException):
    """Raised when a database operation fails"""

    def __init__(
        self,
        message: str,
        operation: str,
        table: Optional[str] = None,
        original_error: Optional[str] = None,
    ):
        details = {
            "operation": operation,
            "table": table,
            "original_error": original_error,
        }
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            details=details,
            user_message="A database error occurred. Please try again",
        )


class FileProcessingError(OneClassException):
    """Raised when file processing fails"""

    def __init__(
        self,
        message: str,
        filename: str,
        file_type: Optional[str] = None,
        size: Optional[int] = None,
        reason: Optional[str] = None,
    ):
        details = {
            "filename": filename,
            "file_type": file_type,
            "size": size,
            "reason": reason,
        }
        super().__init__(
            message=message,
            error_code="FILE_PROCESSING_ERROR",
            status_code=422,
            details=details,
            user_message="Failed to process the uploaded file",
        )


class BulkOperationError(OneClassException):
    """Raised when a bulk operation encounters errors"""

    def __init__(
        self,
        message: str,
        operation_type: str,
        total_items: int,
        failed_items: int,
        errors: List[Dict[str, Any]],
        partial_success: bool = True,
    ):
        details = {
            "operation_type": operation_type,
            "total_items": total_items,
            "failed_items": failed_items,
            "successful_items": total_items - failed_items,
            "errors": errors,
            "partial_success": partial_success,
        }
        super().__init__(
            message=message,
            error_code="BULK_OPERATION_ERROR",
            status_code=207,  # Multi-Status
            details=details,
            user_message=f"Bulk operation partially completed: {failed_items} items failed",
        )


class SchoolContextError(OneClassException):
    """Raised when school context is invalid or missing"""

    def __init__(
        self,
        message: str = "Invalid school context",
        school_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        required_role: Optional[str] = None,
    ):
        details = {
            "school_id": str(school_id) if school_id else None,
            "user_id": str(user_id) if user_id else None,
            "required_role": required_role,
        }
        super().__init__(
            message=message,
            error_code="SCHOOL_CONTEXT_ERROR",
            status_code=400,
            details=details,
            user_message="Invalid school context for this operation",
        )


class InvitationError(OneClassException):
    """Raised when invitation operations fail"""

    def __init__(
        self,
        message: str,
        invitation_id: Optional[str] = None,
        email: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        details = {"invitation_id": invitation_id, "email": email, "reason": reason}
        super().__init__(
            message=message,
            error_code="INVITATION_ERROR",
            status_code=400,
            details=details,
            user_message="Invitation operation failed",
        )


class OnboardingError(OneClassException):
    """Raised when onboarding process fails"""

    def __init__(
        self,
        message: str,
        step: str,
        user_type: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        details = {"step": step, "user_type": user_type, "reason": reason}
        super().__init__(
            message=message,
            error_code="ONBOARDING_ERROR",
            status_code=400,
            details=details,
            user_message="Onboarding process failed. Please contact support",
        )


class NotificationError(OneClassException):
    """Raised when notification delivery fails"""

    def __init__(
        self,
        message: str,
        notification_type: str,
        recipient: Optional[str] = None,
        channel: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        details = {
            "notification_type": notification_type,
            "recipient": recipient,
            "channel": channel,
            "reason": reason,
        }
        super().__init__(
            message=message,
            error_code="NOTIFICATION_ERROR",
            status_code=500,
            details=details,
            user_message="Failed to send notification",
        )


class PaymentError(OneClassException):
    """Raised when payment processing fails"""

    def __init__(
        self,
        message: str,
        payment_method: Optional[str] = None,
        amount: Optional[float] = None,
        currency: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        details = {
            "payment_method": payment_method,
            "amount": amount,
            "currency": currency,
            "reason": reason,
        }
        super().__init__(
            message=message,
            error_code="PAYMENT_ERROR",
            status_code=402,
            details=details,
            user_message="Payment processing failed",
        )


class SubscriptionError(OneClassException):
    """Raised when subscription operations fail"""

    def __init__(
        self,
        message: str,
        school_id: Optional[UUID] = None,
        current_tier: Optional[str] = None,
        requested_tier: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        details = {
            "school_id": str(school_id) if school_id else None,
            "current_tier": current_tier,
            "requested_tier": requested_tier,
            "reason": reason,
        }
        super().__init__(
            message=message,
            error_code="SUBSCRIPTION_ERROR",
            status_code=403,
            details=details,
            user_message="Subscription operation failed",
        )


# Typing fix
from typing import Union
