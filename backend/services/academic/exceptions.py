"""
Academic Management Module - Custom Exceptions
Comprehensive error handling for academic operations
"""

from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

class AcademicBaseException(Exception):
    """Base exception for Academic Management module"""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = None,
        details: Dict[str, Any] = None,
        status_code: int = 500
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
            "module": "academic_management"
        }
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException"""
        return HTTPException(
            status_code=self.status_code,
            detail=self.to_dict()
        )

# =====================================================
# VALIDATION EXCEPTIONS
# =====================================================

class AcademicValidationError(AcademicBaseException):
    """Raised when academic data validation fails"""
    
    def __init__(self, message: str, field: str = None, value: Any = None, details: Dict = None):
        self.field = field
        self.value = value
        error_details = details or {}
        if field:
            error_details["field"] = field
        if value is not None:
            error_details["invalid_value"] = str(value)
        
        super().__init__(
            message=message,
            error_code="ACADEMIC_VALIDATION_ERROR",
            details=error_details,
            status_code=status.HTTP_400_BAD_REQUEST
        )

class InvalidGradeLevelError(AcademicValidationError):
    """Raised when invalid grade level is provided"""
    
    def __init__(self, grade_level: int, valid_range: str = "1-13"):
        super().__init__(
            message=f"Invalid grade level: {grade_level}. Must be between {valid_range} for Zimbabwe education system.",
            field="grade_level",
            value=grade_level,
            details={
                "valid_range": valid_range,
                "zimbabwe_grades": "Grades 1-7 (Primary), Forms 1-6 (Secondary)"
            }
        )

class InvalidTermNumberError(AcademicValidationError):
    """Raised when invalid term number is provided"""
    
    def __init__(self, term_number: int):
        super().__init__(
            message=f"Invalid term number: {term_number}. Zimbabwe schools have 3 terms (1, 2, 3).",
            field="term_number",
            value=term_number,
            details={
                "valid_terms": [1, 2, 3],
                "term_descriptions": {
                    1: "Term 1 (January - April)",
                    2: "Term 2 (May - August)", 
                    3: "Term 3 (September - December)"
                }
            }
        )

class InvalidGradeScaleError(AcademicValidationError):
    """Raised when invalid grade or percentage is provided"""
    
    def __init__(self, grade_value: Any, grade_type: str = "percentage"):
        if grade_type == "percentage":
            message = f"Invalid percentage: {grade_value}. Must be between 0-100."
            details = {"valid_range": "0-100", "type": "percentage"}
        elif grade_type == "letter":
            message = f"Invalid letter grade: {grade_value}. Must be A, B, C, D, E, or U."
            details = {
                "valid_grades": ["A", "B", "C", "D", "E", "U"],
                "grading_scale": "Zimbabwe A-U scale"
            }
        else:
            message = f"Invalid grade: {grade_value}"
            details = {"type": grade_type}
        
        super().__init__(
            message=message,
            field="grade",
            value=grade_value,
            details=details
        )

class SubjectCodeError(AcademicValidationError):
    """Raised when subject code is invalid"""
    
    def __init__(self, subject_code: str, reason: str = "Invalid format"):
        super().__init__(
            message=f"Invalid subject code '{subject_code}': {reason}",
            field="subject_code",
            value=subject_code,
            details={
                "format_requirements": "2-10 characters, alphanumeric, uppercase",
                "examples": ["MATH", "ENG", "PHYS", "CHEM", "BIO"]
            }
        )

# =====================================================
# RESOURCE EXCEPTIONS
# =====================================================

class AcademicResourceError(AcademicBaseException):
    """Base exception for resource-related errors"""
    pass

class SubjectNotFoundError(AcademicResourceError):
    """Raised when subject is not found"""
    
    def __init__(self, subject_id: str = None, subject_code: str = None):
        identifier = subject_id or subject_code or "unknown"
        super().__init__(
            message=f"Subject not found: {identifier}",
            error_code="SUBJECT_NOT_FOUND",
            details={
                "subject_id": subject_id,
                "subject_code": subject_code,
                "suggestion": "Check if the subject exists and you have permission to access it"
            },
            status_code=status.HTTP_404_NOT_FOUND
        )

class AssessmentNotFoundError(AcademicResourceError):
    """Raised when assessment is not found"""
    
    def __init__(self, assessment_id: str):
        super().__init__(
            message=f"Assessment not found: {assessment_id}",
            error_code="ASSESSMENT_NOT_FOUND",
            details={
                "assessment_id": assessment_id,
                "suggestion": "Check if the assessment exists and you have permission to access it"
            },
            status_code=status.HTTP_404_NOT_FOUND
        )

class AttendanceSessionNotFoundError(AcademicResourceError):
    """Raised when attendance session is not found"""
    
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Attendance session not found: {session_id}",
            error_code="ATTENDANCE_SESSION_NOT_FOUND",
            details={
                "session_id": session_id,
                "suggestion": "Check if the session exists and you have permission to access it"
            },
            status_code=status.HTTP_404_NOT_FOUND
        )

class TimetableNotFoundError(AcademicResourceError):
    """Raised when timetable entry is not found"""
    
    def __init__(self, timetable_id: str):
        super().__init__(
            message=f"Timetable entry not found: {timetable_id}",
            error_code="TIMETABLE_NOT_FOUND",
            details={
                "timetable_id": timetable_id,
                "suggestion": "Check if the timetable entry exists and you have permission to access it"
            },
            status_code=status.HTTP_404_NOT_FOUND
        )

# =====================================================
# PERMISSION EXCEPTIONS  
# =====================================================

class AcademicPermissionError(AcademicBaseException):
    """Base exception for permission-related errors"""
    
    def __init__(self, message: str, required_permission: str = None, user_role: str = None):
        details = {}
        if required_permission:
            details["required_permission"] = required_permission
        if user_role:
            details["user_role"] = user_role
        
        super().__init__(
            message=message,
            error_code="ACADEMIC_PERMISSION_ERROR",
            details=details,
            status_code=status.HTTP_403_FORBIDDEN
        )

class InsufficientPermissionError(AcademicPermissionError):
    """Raised when user lacks required permissions"""
    
    def __init__(self, permission: str, user_role: str, action: str = "perform this action"):
        super().__init__(
            message=f"Insufficient permissions to {action}. Required: {permission}",
            required_permission=permission,
            user_role=user_role
        )

class TeacherOwnershipError(AcademicPermissionError):
    """Raised when teacher tries to access resources they don't own"""
    
    def __init__(self, resource_type: str, resource_id: str):
        message = f"You can only access {resource_type} records you created or are assigned to."
        super().__init__(message)
        self.details.update({
            "resource_type": resource_type,
            "resource_id": resource_id,
            "explanation": "Teachers can only modify their own assessments, grades, and attendance records"
        })

class StudentPrivacyError(AcademicPermissionError):
    """Raised when trying to access student data without permission"""
    
    def __init__(self, student_id: str, attempted_action: str):
        message = f"Cannot access student data: {attempted_action}"
        super().__init__(message)
        self.details.update({
            "student_id": student_id,
            "attempted_action": attempted_action,
            "explanation": "Students can only view their own academic records"
        })

# =====================================================
# BUSINESS LOGIC EXCEPTIONS
# =====================================================

class AcademicBusinessError(AcademicBaseException):
    """Base exception for business logic errors"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        super().__init__(
            message=message,
            error_code=error_code or "ACADEMIC_BUSINESS_ERROR",
            details=details or {},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

class DuplicateSubjectError(AcademicBusinessError):
    """Raised when trying to create duplicate subject"""
    
    def __init__(self, subject_code: str, school_name: str = None):
        super().__init__(
            message=f"Subject with code '{subject_code}' already exists" + (f" in {school_name}" if school_name else ""),
            error_code="DUPLICATE_SUBJECT_CODE",
            details={
                "subject_code": subject_code,
                "school": school_name,
                "suggestion": "Use a different subject code or update the existing subject"
            }
        )

class TimetableConflictError(AcademicBusinessError):
    """Raised when timetable scheduling conflict occurs"""
    
    def __init__(self, conflict_type: str, details: Dict[str, Any]):
        conflict_messages = {
            "teacher_conflict": "Teacher already has a class at this time",
            "class_conflict": "Class already has a subject scheduled at this time",
            "room_conflict": "Room is already booked at this time",
            "period_conflict": "Invalid period or time slot"
        }
        
        message = conflict_messages.get(conflict_type, "Timetable scheduling conflict")
        
        super().__init__(
            message=message,
            error_code="TIMETABLE_CONFLICT",
            details={
                "conflict_type": conflict_type,
                **details,
                "suggestion": "Choose a different time slot or resolve the conflict"
            }
        )

class AttendanceAlreadyMarkedError(AcademicBusinessError):
    """Raised when trying to mark attendance that's already been marked"""
    
    def __init__(self, session_date: str, class_name: str = None):
        super().__init__(
            message=f"Attendance already marked for {session_date}" + (f" in {class_name}" if class_name else ""),
            error_code="ATTENDANCE_ALREADY_MARKED",
            details={
                "session_date": session_date,
                "class_name": class_name,
                "suggestion": "Update existing attendance records instead of creating new ones"
            }
        )

class GradingPeriodClosedError(AcademicBusinessError):
    """Raised when trying to modify grades after grading period is closed"""
    
    def __init__(self, assessment_name: str, close_date: str):
        super().__init__(
            message=f"Cannot modify grades for '{assessment_name}'. Grading period closed on {close_date}.",
            error_code="GRADING_PERIOD_CLOSED",
            details={
                "assessment_name": assessment_name,
                "close_date": close_date,
                "suggestion": "Contact administrator to reopen grading period if changes are needed"
            }
        )

class InvalidAssessmentDateError(AcademicBusinessError):
    """Raised when assessment date is invalid"""
    
    def __init__(self, assessment_date: str, reason: str):
        super().__init__(
            message=f"Invalid assessment date {assessment_date}: {reason}",
            error_code="INVALID_ASSESSMENT_DATE",
            details={
                "assessment_date": assessment_date,
                "reason": reason,
                "suggestion": "Ensure assessment date falls within the academic term"
            }
        )

# =====================================================
# SYSTEM EXCEPTIONS
# =====================================================

class AcademicSystemError(AcademicBaseException):
    """Base exception for system-level errors"""
    
    def __init__(self, message: str, error_code: str = None, original_error: Exception = None):
        details = {}
        if original_error:
            details["original_error"] = str(original_error)
            details["error_type"] = type(original_error).__name__
        
        super().__init__(
            message=message,
            error_code=error_code or "ACADEMIC_SYSTEM_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        self.original_error = original_error

class DatabaseConnectionError(AcademicSystemError):
    """Raised when database connection fails"""
    
    def __init__(self, operation: str, original_error: Exception = None):
        super().__init__(
            message=f"Database connection failed during {operation}",
            error_code="DATABASE_CONNECTION_ERROR",
            original_error=original_error
        )

class ExternalServiceError(AcademicSystemError):
    """Raised when external service integration fails"""
    
    def __init__(self, service_name: str, operation: str, original_error: Exception = None):
        super().__init__(
            message=f"External service '{service_name}' failed during {operation}",
            error_code="EXTERNAL_SERVICE_ERROR",
            original_error=original_error
        )
        self.service_name = service_name
        self.operation = operation

class DataCorruptionError(AcademicSystemError):
    """Raised when data corruption is detected"""
    
    def __init__(self, data_type: str, identifier: str, corruption_details: str):
        super().__init__(
            message=f"Data corruption detected in {data_type} (ID: {identifier}): {corruption_details}",
            error_code="DATA_CORRUPTION_ERROR"
        )
        self.data_type = data_type
        self.identifier = identifier

# =====================================================
# EXCEPTION UTILITIES
# =====================================================

def handle_database_error(error: Exception, operation: str) -> AcademicBaseException:
    """Convert database errors to academic exceptions"""
    error_str = str(error).lower()
    
    if "unique" in error_str or "duplicate" in error_str:
        if "subject" in error_str and "code" in error_str:
            return DuplicateSubjectError("Unknown", "current school")
        return AcademicBusinessError(
            "Duplicate record detected",
            "DUPLICATE_RECORD_ERROR",
            {"operation": operation, "database_error": str(error)}
        )
    
    if "foreign key" in error_str or "violates" in error_str:
        return AcademicValidationError(
            "Referenced record not found or invalid relationship",
            details={"operation": operation, "constraint_violation": str(error)}
        )
    
    if "connection" in error_str or "timeout" in error_str:
        return DatabaseConnectionError(operation, error)
    
    # Generic database error
    return AcademicSystemError(
        f"Database error during {operation}",
        "DATABASE_ERROR",
        error
    )

def log_academic_error(error: AcademicBaseException, context: Dict[str, Any] = None):
    """Log academic errors with context"""
    log_data = {
        "error_type": type(error).__name__,
        "error_code": error.error_code,
        "message": error.message,
        "details": error.details,
        "status_code": error.status_code
    }
    
    if context:
        log_data["context"] = context
    
    if error.status_code >= 500:
        logger.error(f"Academic system error: {log_data}")
    elif error.status_code >= 400:
        logger.warning(f"Academic client error: {log_data}")
    else:
        logger.info(f"Academic error: {log_data}")

def create_error_response(error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create standardized error response"""
    if isinstance(error, AcademicBaseException):
        academic_error = error
    else:
        # Convert generic exceptions to academic exceptions
        academic_error = handle_database_error(error, "unknown_operation")
    
    # Log the error
    log_academic_error(academic_error, context)
    
    return academic_error.to_dict()

# Exception mapping for common FastAPI exceptions
EXCEPTION_MAPPING = {
    ValueError: lambda e: AcademicValidationError(str(e)),
    KeyError: lambda e: AcademicValidationError(f"Missing required field: {str(e)}"),
    TypeError: lambda e: AcademicValidationError(f"Invalid data type: {str(e)}"),
    FileNotFoundError: lambda e: AcademicResourceError(f"Resource not found: {str(e)}", "RESOURCE_NOT_FOUND"),
    PermissionError: lambda e: AcademicPermissionError(f"Permission denied: {str(e)}")
}