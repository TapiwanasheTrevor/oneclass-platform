# =====================================================
# Input Validators
# Comprehensive validation functions for OneClass platform
# File: backend/shared/errors/validators.py
# =====================================================

import re
import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from email_validator import validate_email as _validate_email, EmailNotValidError

from .exceptions import ValidationError

# Zimbabwe-specific validation patterns
ZIMBABWE_ID_PATTERN = re.compile(r'^\d{2}-\d{6,7}[A-Z]\d{2}$')
ZIMBABWE_PHONE_PATTERN = re.compile(r'^(\+263|0)(7[7-9]|86)\d{7}$')
SCHOOL_CODE_PATTERN = re.compile(r'^[A-Z]{2,4}\d{3,5}$')

# File type mappings
ALLOWED_IMAGE_TYPES = {
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'
}

ALLOWED_DOCUMENT_TYPES = {
    'application/pdf', 'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain'
}

ALLOWED_SPREADSHEET_TYPES = {
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/csv'
}

def validate_email(email: str, field_name: str = "email") -> str:
    """Validate email address format"""
    
    if not email:
        raise ValidationError(
            message=f"{field_name} is required",
            field=field_name,
            value=email
        )
    
    try:
        # Use email-validator library for comprehensive validation
        valid_email = _validate_email(email)
        return valid_email.email
    except EmailNotValidError as e:
        raise ValidationError(
            message=f"Invalid {field_name} format: {str(e)}",
            field=field_name,
            value=email
        )

def validate_phone_number(phone: str, field_name: str = "phone_number") -> str:
    """Validate Zimbabwe phone number format"""
    
    if not phone:
        raise ValidationError(
            message=f"{field_name} is required",
            field=field_name,
            value=phone
        )
    
    # Remove spaces and hyphens
    cleaned_phone = re.sub(r'[\s\-]', '', phone)
    
    if not ZIMBABWE_PHONE_PATTERN.match(cleaned_phone):
        raise ValidationError(
            message=f"Invalid {field_name} format. Use +263 or 0 followed by mobile number",
            field=field_name,
            value=phone,
            errors=[{
                "constraint": "format",
                "expected_format": "+263771234567 or 0771234567",
                "pattern": "Zimbabwean mobile number"
            }]
        )
    
    # Standardize to international format
    if cleaned_phone.startswith('0'):
        cleaned_phone = '+263' + cleaned_phone[1:]
    
    return cleaned_phone

def validate_zimbabwe_id(national_id: str, field_name: str = "national_id") -> str:
    """Validate Zimbabwe national ID format"""
    
    if not national_id:
        raise ValidationError(
            message=f"{field_name} is required",
            field=field_name,
            value=national_id
        )
    
    # Remove spaces and hyphens
    cleaned_id = re.sub(r'[\s\-]', '', national_id)
    
    if not ZIMBABWE_ID_PATTERN.match(cleaned_id):
        raise ValidationError(
            message=f"Invalid {field_name} format",
            field=field_name,
            value=national_id,
            errors=[{
                "constraint": "format",
                "expected_format": "XX-XXXXXXXX or XX-XXXXXXXXX",
                "pattern": "Zimbabwe national ID",
                "example": "63-123456A12"
            }]
        )
    
    # Additional validation: check birth year
    try:
        birth_year = int(cleaned_id[:2])
        current_year = datetime.datetime.now().year % 100
        
        # Assume people are not older than 100 years
        if birth_year > current_year:
            birth_year += 1900
        else:
            birth_year += 2000
        
        if birth_year > datetime.datetime.now().year:
            raise ValidationError(
                message=f"Invalid birth year in {field_name}",
                field=field_name,
                value=national_id
            )
    except ValueError:
        raise ValidationError(
            message=f"Invalid birth year format in {field_name}",
            field=field_name,
            value=national_id
        )
    
    return cleaned_id

def validate_school_id(school_id: Union[str, UUID], field_name: str = "school_id") -> UUID:
    """Validate school ID format"""
    
    if not school_id:
        raise ValidationError(
            message=f"{field_name} is required",
            field=field_name,
            value=school_id
        )
    
    try:
        if isinstance(school_id, str):
            return UUID(school_id)
        elif isinstance(school_id, UUID):
            return school_id
        else:
            raise ValueError("Invalid type")
    except (ValueError, TypeError):
        raise ValidationError(
            message=f"Invalid {field_name} format",
            field=field_name,
            value=str(school_id),
            errors=[{
                "constraint": "format",
                "expected_type": "UUID",
                "actual_type": type(school_id).__name__
            }]
        )

def validate_user_role(role: str, field_name: str = "role", allowed_roles: Optional[List[str]] = None) -> str:
    """Validate user role"""
    
    if not role:
        raise ValidationError(
            message=f"{field_name} is required",
            field=field_name,
            value=role
        )
    
    default_roles = [
        "super_admin", "school_admin", "registrar", "teacher", 
        "parent", "student", "bursar", "principal", "deputy_principal"
    ]
    
    valid_roles = allowed_roles or default_roles
    
    if role not in valid_roles:
        raise ValidationError(
            message=f"Invalid {field_name}",
            field=field_name,
            value=role,
            errors=[{
                "constraint": "choice",
                "allowed_values": valid_roles
            }]
        )
    
    return role

def validate_file_type(
    filename: str,
    file_type: str,
    allowed_types: Optional[List[str]] = None,
    field_name: str = "file"
) -> bool:
    """Validate file type and extension"""
    
    if not filename:
        raise ValidationError(
            message=f"{field_name} name is required",
            field=field_name,
            value=filename
        )
    
    # Get file extension
    if '.' not in filename:
        raise ValidationError(
            message=f"{field_name} must have an extension",
            field=field_name,
            value=filename
        )
    
    extension = filename.lower().split('.')[-1]
    
    # Default allowed types based on context
    if allowed_types is None:
        allowed_types = list(ALLOWED_IMAGE_TYPES | ALLOWED_DOCUMENT_TYPES | ALLOWED_SPREADSHEET_TYPES)
    
    if file_type not in allowed_types:
        # Try to suggest based on extension
        suggestions = []
        if extension in ['jpg', 'jpeg', 'png', 'gif']:
            suggestions.extend(ALLOWED_IMAGE_TYPES)
        elif extension in ['pdf', 'doc', 'docx', 'txt']:
            suggestions.extend(ALLOWED_DOCUMENT_TYPES)
        elif extension in ['csv', 'xls', 'xlsx']:
            suggestions.extend(ALLOWED_SPREADSHEET_TYPES)
        
        raise ValidationError(
            message=f"Invalid {field_name} type: {file_type}",
            field=field_name,
            value=file_type,
            errors=[{
                "constraint": "file_type",
                "allowed_values": allowed_types,
                "suggestions": list(suggestions) if suggestions else None,
                "extension": extension
            }]
        )
    
    return True

def validate_date_range(
    start_date: datetime.date,
    end_date: datetime.date,
    field_name: str = "date_range",
    max_days: Optional[int] = None
) -> tuple:
    """Validate date range"""
    
    if not start_date:
        raise ValidationError(
            message="Start date is required",
            field=f"{field_name}.start_date",
            value=start_date
        )
    
    if not end_date:
        raise ValidationError(
            message="End date is required",
            field=f"{field_name}.end_date",
            value=end_date
        )
    
    if start_date > end_date:
        raise ValidationError(
            message="Start date must be before end date",
            field=field_name,
            value={"start_date": start_date, "end_date": end_date}
        )
    
    if max_days:
        delta = (end_date - start_date).days
        if delta > max_days:
            raise ValidationError(
                message=f"Date range cannot exceed {max_days} days",
                field=field_name,
                value={"start_date": start_date, "end_date": end_date, "days": delta},
                errors=[{
                    "constraint": "max_days",
                    "max_allowed": max_days,
                    "actual": delta
                }]
            )
    
    return start_date, end_date

def validate_pagination(
    page: int = 1,
    page_size: int = 20,
    max_page_size: int = 100
) -> tuple:
    """Validate pagination parameters"""
    
    if page < 1:
        raise ValidationError(
            message="Page number must be at least 1",
            field="page",
            value=page,
            errors=[{
                "constraint": "min_value",
                "min_allowed": 1,
                "actual": page
            }]
        )
    
    if page_size < 1:
        raise ValidationError(
            message="Page size must be at least 1",
            field="page_size",
            value=page_size,
            errors=[{
                "constraint": "min_value",
                "min_allowed": 1,
                "actual": page_size
            }]
        )
    
    if page_size > max_page_size:
        raise ValidationError(
            message=f"Page size cannot exceed {max_page_size}",
            field="page_size",
            value=page_size,
            errors=[{
                "constraint": "max_value",
                "max_allowed": max_page_size,
                "actual": page_size
            }]
        )
    
    return page, page_size

def validate_password_strength(password: str, field_name: str = "password") -> str:
    """Validate password strength"""
    
    if not password:
        raise ValidationError(
            message=f"{field_name} is required",
            field=field_name,
            value=""
        )
    
    errors = []
    
    # Length check
    if len(password) < 8:
        errors.append({
            "constraint": "min_length",
            "min_required": 8,
            "actual": len(password),
            "message": "Password must be at least 8 characters long"
        })
    
    # Character type checks
    if not re.search(r'[a-z]', password):
        errors.append({
            "constraint": "lowercase_required",
            "message": "Password must contain at least one lowercase letter"
        })
    
    if not re.search(r'[A-Z]', password):
        errors.append({
            "constraint": "uppercase_required",
            "message": "Password must contain at least one uppercase letter"
        })
    
    if not re.search(r'\d', password):
        errors.append({
            "constraint": "digit_required",
            "message": "Password must contain at least one digit"
        })
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append({
            "constraint": "special_char_required",
            "message": "Password must contain at least one special character"
        })
    
    # Common password check (simplified)
    common_passwords = [
        "password", "123456", "password123", "admin", "qwerty",
        "letmein", "welcome", "monkey", "1234567890"
    ]
    
    if password.lower() in common_passwords:
        errors.append({
            "constraint": "common_password",
            "message": "Password is too common, please choose a more secure password"
        })
    
    if errors:
        raise ValidationError(
            message="Password does not meet security requirements",
            field=field_name,
            value="[REDACTED]",
            errors=errors
        )
    
    return password

def validate_bulk_data(
    data: List[Dict[str, Any]],
    required_fields: List[str],
    field_validators: Optional[Dict[str, callable]] = None,
    max_items: int = 1000
) -> List[Dict[str, Any]]:
    """Validate bulk data import"""
    
    if not data:
        raise ValidationError(
            message="Data is required",
            field="data",
            value=data
        )
    
    if len(data) > max_items:
        raise ValidationError(
            message=f"Too many items. Maximum {max_items} allowed",
            field="data",
            value=len(data),
            errors=[{
                "constraint": "max_items",
                "max_allowed": max_items,
                "actual": len(data)
            }]
        )
    
    validated_data = []
    bulk_errors = []
    
    for index, item in enumerate(data):
        item_errors = []
        
        # Check required fields
        for field in required_fields:
            if field not in item or item[field] is None or item[field] == "":
                item_errors.append({
                    "field": field,
                    "message": f"{field} is required",
                    "constraint": "required"
                })
        
        # Apply field validators
        if field_validators:
            for field, validator in field_validators.items():
                if field in item and item[field] is not None:
                    try:
                        item[field] = validator(item[field])
                    except ValidationError as e:
                        item_errors.append({
                            "field": field,
                            "message": e.message,
                            "constraint": "validation",
                            "details": e.details
                        })
        
        if item_errors:
            bulk_errors.append({
                "index": index,
                "item_id": item.get("id") or item.get("email") or f"item_{index}",
                "errors": item_errors
            })
        else:
            validated_data.append(item)
    
    if bulk_errors:
        from .exceptions import BulkOperationError
        raise BulkOperationError(
            message=f"Validation failed for {len(bulk_errors)} items",
            operation_type="data_validation",
            total_items=len(data),
            failed_items=len(bulk_errors),
            errors=bulk_errors
        )
    
    return validated_data

def validate_zimbabwe_school_code(code: str, field_name: str = "school_code") -> str:
    """Validate Zimbabwe school code format"""
    
    if not code:
        raise ValidationError(
            message=f"{field_name} is required",
            field=field_name,
            value=code
        )
    
    # Remove spaces and convert to uppercase
    cleaned_code = re.sub(r'\s', '', code.upper())
    
    if not SCHOOL_CODE_PATTERN.match(cleaned_code):
        raise ValidationError(
            message=f"Invalid {field_name} format",
            field=field_name,
            value=code,
            errors=[{
                "constraint": "format",
                "expected_format": "2-4 letters followed by 3-5 digits",
                "pattern": "Zimbabwe school code",
                "example": "ABC123 or WXYZ12345"
            }]
        )
    
    return cleaned_code