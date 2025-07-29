# OneClass Error Handling System

A comprehensive error handling system for the OneClass platform that provides standardized error responses, validation, logging, and monitoring.

## Features

- **Standardized Error Responses** - Consistent error format across all APIs
- **Custom Exception Classes** - Domain-specific exceptions with proper context
- **Comprehensive Validation** - Input validation with Zimbabwe-specific rules
- **Error Middleware** - Request tracking, rate limiting, and security headers
- **Error Logging** - Structured logging with correlation IDs
- **Error Recovery** - Retry mechanisms and user guidance

## Quick Start

### 1. Setup Error Handlers

```python
from fastapi import FastAPI
from shared.errors import setup_error_handlers, ErrorHandlingMiddleware

app = FastAPI()

# Add error handling middleware
app.add_middleware(ErrorHandlingMiddleware)

# Setup error handlers
setup_error_handlers(app)
```

### 2. Using Custom Exceptions

```python
from shared.errors import ValidationError, NotFoundError, AuthorizationError

# Validation error
raise ValidationError(
    message="Invalid email format",
    field="email",
    value="invalid-email"
)

# Not found error
raise NotFoundError(
    resource_type="User",
    resource_id=user_id
)

# Authorization error
raise AuthorizationError(
    message="Insufficient permissions",
    required_permission="students.create",
    user_role="teacher"
)
```

### 3. Using Validators

```python
from shared.errors.validators import (
    validate_email, validate_phone_number, validate_zimbabwe_id
)

# Validate email
email = validate_email("user@example.com")

# Validate Zimbabwe phone number
phone = validate_phone_number("+263771234567")

# Validate Zimbabwe national ID
national_id = validate_zimbabwe_id("63-123456A12")
```

### 4. Error Handler Decorator

```python
from shared.errors.handlers import error_handler
from shared.errors.schemas import ErrorCategory

@error_handler(
    default_message="User creation failed",
    error_code="USER_CREATION_ERROR",
    category=ErrorCategory.DATABASE
)
async def create_user(user_data: dict):
    # Your implementation here
    pass
```

## Exception Classes

### Base Exception
- `OneClassException` - Base class for all custom exceptions

### Authentication & Authorization
- `AuthenticationError` - Authentication failures
- `AuthorizationError` - Permission failures

### Data & Validation
- `ValidationError` - Input validation failures
- `NotFoundError` - Resource not found
- `ConflictError` - Resource conflicts

### System & External
- `DatabaseError` - Database operation failures
- `ExternalServiceError` - Third-party service failures
- `RateLimitError` - Rate limiting

### Domain-Specific
- `SchoolContextError` - School context issues
- `InvitationError` - Invitation system failures
- `OnboardingError` - User onboarding failures
- `FileProcessingError` - File upload/processing failures
- `BulkOperationError` - Bulk operation failures
- `NotificationError` - Notification delivery failures
- `PaymentError` - Payment processing failures
- `SubscriptionError` - Subscription management failures

## Error Response Format

All errors return a standardized JSON response:

```json
{
  "success": false,
  "error_code": "VALIDATION_ERROR",
  "message": "Validation failed",
  "user_message": "Please check your input and try again",
  "category": "validation",
  "severity": "medium",
  "details": {
    "field": "email",
    "value": "invalid-email"
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "correlation_id": "uuid-here",
  "suggestions": [
    "Check that all required fields are provided",
    "Verify that field formats match the expected patterns"
  ],
  "retry_possible": false
}
```

## Validation Functions

### Zimbabwe-Specific Validators
- `validate_zimbabwe_id()` - National ID format validation
- `validate_phone_number()` - Zimbabwe mobile number validation
- `validate_zimbabwe_school_code()` - School code validation

### General Validators
- `validate_email()` - Email format validation
- `validate_user_role()` - User role validation
- `validate_file_type()` - File type and extension validation
- `validate_date_range()` - Date range validation
- `validate_pagination()` - Pagination parameter validation
- `validate_password_strength()` - Password security validation
- `validate_bulk_data()` - Bulk data import validation

## Middleware Components

### ErrorHandlingMiddleware
- Adds correlation IDs to requests
- Tracks request performance
- Logs errors with context
- Provides error metrics

### RequestContextMiddleware
- Adds request metadata to state
- Extracts school context from headers/subdomain
- Sets request IDs

### SecurityHeadersMiddleware
- Adds security headers to responses
- Implements CORS and CSP policies

### RateLimitMiddleware
- Implements rate limiting per user/IP
- Configurable limits and burst capacity

## Best Practices

### 1. Exception Handling in Services

```python
from shared.errors import NotFoundError, DatabaseError

async def get_user(user_id: str):
    try:
        user = await db.get_user(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        return user
    except DatabaseError:
        raise  # Re-raise database errors
    except Exception as e:
        raise DatabaseError(
            message="Failed to retrieve user",
            operation="select",
            table="users",
            original_error=str(e)
        )
```

### 2. Input Validation

```python
from shared.errors.validators import validate_email, validate_phone_number

def validate_user_input(data: dict):
    # Validate required fields
    data["email"] = validate_email(data.get("email"))
    data["phone"] = validate_phone_number(data.get("phone"))
    
    return data
```

### 3. API Route Error Handling

```python
from fastapi import HTTPException
from shared.errors import ValidationError, NotFoundError

@router.post("/users")
async def create_user(user_data: UserCreate):
    try:
        # Validate input
        validated_data = validate_user_input(user_data.dict())
        
        # Create user
        user = await user_service.create_user(validated_data)
        
        return {"success": True, "user": user}
        
    except ValidationError as e:
        # Validation errors are automatically handled by middleware
        raise
    except NotFoundError as e:
        # Domain errors are automatically handled
        raise
    except Exception as e:
        # Unexpected errors are caught by global handler
        logger.error(f"Unexpected error creating user: {str(e)}")
        raise
```

### 4. Bulk Operation Error Handling

```python
from shared.errors import BulkOperationError

async def import_users(user_data_list: List[dict]):
    successful = 0
    failed = 0
    errors = []
    
    for index, user_data in enumerate(user_data_list):
        try:
            await create_user(user_data)
            successful += 1
        except Exception as e:
            failed += 1
            errors.append({
                "index": index,
                "item_id": user_data.get("email"),
                "error": str(e)
            })
    
    if failed > 0:
        raise BulkOperationError(
            message=f"User import completed with {failed} failures",
            operation_type="user_import",
            total_items=len(user_data_list),
            failed_items=failed,
            errors=errors
        )
    
    return {"successful": successful, "failed": failed}
```

## Configuration

### Environment Variables

```bash
# Error handling configuration
ERROR_REPORTING_ENABLED=true
ERROR_CORRELATION_ENABLED=true
REQUEST_LOGGING_ENABLED=true
PERFORMANCE_TRACKING_ENABLED=true

# Rate limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST_LIMIT=100

# Security
SECURITY_HEADERS_ENABLED=true
```

### Error Categories

The system categorizes errors for better tracking and handling:

- `validation` - Input validation failures
- `authentication` - Authentication issues
- `authorization` - Permission issues
- `not_found` - Resource not found
- `conflict` - Resource conflicts
- `rate_limit` - Rate limiting
- `external_service` - Third-party service issues
- `database` - Database operation failures
- `file_processing` - File handling issues
- `bulk_operation` - Bulk operation issues
- `system` - General system errors

### Error Severity Levels

- `low` - Minor issues, user can continue
- `medium` - Issues that prevent operation completion
- `high` - Serious issues affecting functionality
- `critical` - System-wide issues requiring immediate attention

## Monitoring and Metrics

The error handling system provides metrics for monitoring:

```python
from shared.errors.middleware import ErrorHandlingMiddleware

# Get error metrics
middleware = ErrorHandlingMiddleware(app)
metrics = middleware.get_error_metrics()

print(f"Total requests: {metrics['total_requests']}")
print(f"Total errors: {metrics['total_errors']}")
print(f"Error rate: {metrics['error_rate']}%")
```

## Integration with Logging

All errors are automatically logged with structured data:

```python
import logging

logger = logging.getLogger(__name__)

# Error logs include:
# - correlation_id
# - user_id 
# - school_id
# - request_method
# - request_url
# - error_type
# - error_message
# - timestamp
```

## Testing Error Handling

```python
import pytest
from shared.errors import ValidationError, NotFoundError

def test_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        validate_email("invalid-email")
    
    assert exc_info.value.error_code == "VALIDATION_ERROR"
    assert exc_info.value.status_code == 400

def test_not_found_error():
    with pytest.raises(NotFoundError) as exc_info:
        raise NotFoundError("User", "123")
    
    assert exc_info.value.error_code == "NOT_FOUND"
    assert exc_info.value.status_code == 404
```

This comprehensive error handling system ensures consistent, user-friendly error responses across the entire OneClass platform while providing developers with detailed debugging information and administrators with monitoring capabilities.