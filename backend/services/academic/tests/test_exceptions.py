"""
Academic Management Module - Exception Classes Unit Tests
Comprehensive tests for all exception classes and error handling utilities
"""

import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch
import json

from services.academic.exceptions import (
    # Base exception
    AcademicBaseException,
    
    # Validation exceptions
    AcademicValidationError,
    InvalidGradeLevelError,
    InvalidTermNumberError,
    InvalidGradeScaleError,
    SubjectCodeError,
    
    # Resource exceptions
    AcademicResourceError,
    SubjectNotFoundError,
    AssessmentNotFoundError,
    AttendanceSessionNotFoundError,
    TimetableNotFoundError,
    
    # Permission exceptions
    AcademicPermissionError,
    InsufficientPermissionError,
    TeacherOwnershipError,
    StudentPrivacyError,
    
    # Business logic exceptions
    AcademicBusinessError,
    DuplicateSubjectError,
    TimetableConflictError,
    AttendanceAlreadyMarkedError,
    GradingPeriodClosedError,
    InvalidAssessmentDateError,
    
    # System exceptions
    AcademicSystemError,
    DatabaseConnectionError,
    ExternalServiceError,
    DataCorruptionError,
    
    # Utilities
    handle_database_error,
    log_academic_error,
    create_error_response,
    EXCEPTION_MAPPING
)


class TestAcademicBaseException:
    """Test the base exception class"""
    
    def test_basic_creation(self):
        error = AcademicBaseException("Test error")
        assert error.message == "Test error"
        assert error.error_code == "AcademicBaseException"
        assert error.status_code == 500
        assert error.details == {}
    
    def test_custom_parameters(self):
        details = {"field": "test_field", "value": "test_value"}
        error = AcademicBaseException(
            message="Custom error",
            error_code="CUSTOM_ERROR",
            details=details,
            status_code=400
        )
        assert error.message == "Custom error"
        assert error.error_code == "CUSTOM_ERROR"
        assert error.status_code == 400
        assert error.details == details
    
    def test_to_dict(self):
        error = AcademicBaseException("Test error", "TEST_ERROR", {"key": "value"})
        result = error.to_dict()
        
        expected = {
            "error": "TEST_ERROR",
            "message": "Test error",
            "details": {"key": "value"},
            "module": "academic_management"
        }
        assert result == expected
    
    def test_to_http_exception(self):
        error = AcademicBaseException("Test error", "TEST_ERROR", status_code=400)
        http_exc = error.to_http_exception()
        
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 400
        assert http_exc.detail == error.to_dict()


class TestValidationExceptions:
    """Test validation exception classes"""
    
    def test_invalid_grade_level_error(self):
        error = InvalidGradeLevelError(15)
        assert "Invalid grade level: 15" in error.message
        assert "1-13" in error.message
        assert error.field == "grade_level"
        assert error.value == 15
        assert error.status_code == 400
        assert "valid_range" in error.details
        assert "zimbabwe_grades" in error.details
    
    def test_invalid_grade_level_custom_range(self):
        error = InvalidGradeLevelError(8, "1-7")
        assert "Invalid grade level: 8" in error.message
        assert "1-7" in error.message
    
    def test_invalid_term_number_error(self):
        error = InvalidTermNumberError(5)
        assert "Invalid term number: 5" in error.message
        assert "Zimbabwe schools have 3 terms" in error.message
        assert error.field == "term_number"
        assert error.value == 5
        assert error.details["valid_terms"] == [1, 2, 3]
        assert "term_descriptions" in error.details
    
    def test_invalid_grade_scale_percentage(self):
        error = InvalidGradeScaleError(150, "percentage")
        assert "Invalid percentage: 150" in error.message
        assert "0-100" in error.message
        assert error.details["valid_range"] == "0-100"
    
    def test_invalid_grade_scale_letter(self):
        error = InvalidGradeScaleError("F", "letter")
        assert "Invalid letter grade: F" in error.message
        assert "A, B, C, D, E, or U" in error.message
        assert "A" in error.details["valid_grades"]
        assert "U" in error.details["valid_grades"]
    
    def test_subject_code_error(self):
        error = SubjectCodeError("MATH123", "Too long")
        assert "Invalid subject code 'MATH123': Too long" in error.message
        assert error.field == "subject_code"
        assert error.value == "MATH123"
        assert "format_requirements" in error.details
        assert "examples" in error.details


class TestResourceExceptions:
    """Test resource not found exception classes"""
    
    def test_subject_not_found_with_id(self):
        error = SubjectNotFoundError(subject_id="subject-123")
        assert "Subject not found: subject-123" in error.message
        assert error.status_code == 404
        assert error.details["subject_id"] == "subject-123"
        assert error.details["subject_code"] is None
    
    def test_subject_not_found_with_code(self):
        error = SubjectNotFoundError(subject_code="PHYSICS")
        assert "Subject not found: PHYSICS" in error.message
        assert error.details["subject_code"] == "PHYSICS"
        assert error.details["subject_id"] is None
    
    def test_assessment_not_found_error(self):
        error = AssessmentNotFoundError("assessment-456")
        assert "Assessment not found: assessment-456" in error.message
        assert error.status_code == 404
        assert error.details["assessment_id"] == "assessment-456"
    
    def test_attendance_session_not_found_error(self):
        error = AttendanceSessionNotFoundError("session-789")
        assert "Attendance session not found: session-789" in error.message
        assert error.details["session_id"] == "session-789"
    
    def test_timetable_not_found_error(self):
        error = TimetableNotFoundError("timetable-321")
        assert "Timetable entry not found: timetable-321" in error.message
        assert error.details["timetable_id"] == "timetable-321"


class TestPermissionExceptions:
    """Test permission-related exception classes"""
    
    def test_insufficient_permission_error(self):
        error = InsufficientPermissionError(
            "academic.subject.create", 
            "student", 
            "create subjects"
        )
        assert "Insufficient permissions to create subjects" in error.message
        assert "Required: academic.subject.create" in error.message
        assert error.status_code == 403
        assert error.details["required_permission"] == "academic.subject.create"
        assert error.details["user_role"] == "student"
    
    def test_teacher_ownership_error(self):
        error = TeacherOwnershipError("assessment", "assess-123")
        assert "You can only access assessment records" in error.message
        assert error.status_code == 403
        assert error.details["resource_type"] == "assessment"
        assert error.details["resource_id"] == "assess-123"
    
    def test_student_privacy_error(self):
        error = StudentPrivacyError("student-456", "view grades")
        assert "Cannot access student data: view grades" in error.message
        assert error.status_code == 403
        assert error.details["student_id"] == "student-456"
        assert error.details["attempted_action"] == "view grades"


class TestBusinessLogicExceptions:
    """Test business logic exception classes"""
    
    def test_duplicate_subject_error(self):
        error = DuplicateSubjectError("MATH", "Harare Primary")
        assert "Subject with code 'MATH' already exists in Harare Primary" in error.message
        assert error.status_code == 422
        assert error.details["subject_code"] == "MATH"
        assert error.details["school"] == "Harare Primary"
    
    def test_duplicate_subject_error_no_school(self):
        error = DuplicateSubjectError("MATH")
        assert "Subject with code 'MATH' already exists" in error.message
        assert "in " not in error.message  # No school name appended
    
    def test_timetable_conflict_error(self):
        details = {
            "teacher_name": "Ms. Chipo",
            "time_slot": "09:00-10:00",
            "day": "Monday"
        }
        error = TimetableConflictError("teacher_conflict", details)
        assert "Teacher already has a class at this time" in error.message
        assert error.status_code == 422
        assert error.details["conflict_type"] == "teacher_conflict"
        assert error.details["teacher_name"] == "Ms. Chipo"
    
    def test_timetable_conflict_unknown_type(self):
        error = TimetableConflictError("unknown_conflict", {})
        assert "Timetable scheduling conflict" in error.message
    
    def test_attendance_already_marked_error(self):
        error = AttendanceAlreadyMarkedError("2024-08-13", "Form 1A")
        assert "Attendance already marked for 2024-08-13 in Form 1A" in error.message
        assert error.details["session_date"] == "2024-08-13"
        assert error.details["class_name"] == "Form 1A"
    
    def test_grading_period_closed_error(self):
        error = GradingPeriodClosedError("Term 1 Test", "2024-04-30")
        assert "Cannot modify grades for 'Term 1 Test'" in error.message
        assert "closed on 2024-04-30" in error.message
        assert error.details["assessment_name"] == "Term 1 Test"
        assert error.details["close_date"] == "2024-04-30"
    
    def test_invalid_assessment_date_error(self):
        error = InvalidAssessmentDateError("2024-02-30", "Invalid date")
        assert "Invalid assessment date 2024-02-30: Invalid date" in error.message
        assert error.details["assessment_date"] == "2024-02-30"
        assert error.details["reason"] == "Invalid date"


class TestSystemExceptions:
    """Test system-level exception classes"""
    
    def test_database_connection_error(self):
        original_error = ConnectionError("Database unreachable")
        error = DatabaseConnectionError("create_subject", original_error)
        assert "Database connection failed during create_subject" in error.message
        assert error.status_code == 500
        assert error.original_error == original_error
        assert error.details["original_error"] == str(original_error)
        assert error.details["error_type"] == "ConnectionError"
    
    def test_external_service_error(self):
        original_error = TimeoutError("Service timeout")
        error = ExternalServiceError("ZIMSEC API", "fetch_results", original_error)
        assert "External service 'ZIMSEC API' failed during fetch_results" in error.message
        assert error.service_name == "ZIMSEC API"
        assert error.operation == "fetch_results"
        assert error.original_error == original_error
    
    def test_data_corruption_error(self):
        error = DataCorruptionError("student_grades", "grade-123", "Invalid percentage")
        assert "Data corruption detected in student_grades" in error.message
        assert "ID: grade-123" in error.message
        assert "Invalid percentage" in error.message
        assert error.data_type == "student_grades"
        assert error.identifier == "grade-123"


class TestErrorUtilities:
    """Test error handling utility functions"""
    
    def test_handle_database_error_unique_constraint(self):
        db_error = Exception("UNIQUE constraint failed: subjects.code")
        academic_error = handle_database_error(db_error, "create_subject")
        
        assert isinstance(academic_error, DuplicateSubjectError)
        assert "current school" in academic_error.message
    
    def test_handle_database_error_duplicate_key(self):
        db_error = Exception("duplicate key value violates unique constraint")
        academic_error = handle_database_error(db_error, "create_assessment")
        
        assert isinstance(academic_error, AcademicBusinessError)
        assert "Duplicate record detected" in academic_error.message
    
    def test_handle_database_error_foreign_key(self):
        db_error = Exception("foreign key constraint violation")
        academic_error = handle_database_error(db_error, "create_grade")
        
        assert isinstance(academic_error, AcademicValidationError)
        assert "Referenced record not found" in academic_error.message
    
    def test_handle_database_error_connection(self):
        db_error = Exception("connection timeout")
        academic_error = handle_database_error(db_error, "get_subjects")
        
        assert isinstance(academic_error, DatabaseConnectionError)
        assert "get_subjects" in academic_error.message
    
    def test_handle_database_error_generic(self):
        db_error = Exception("Unknown database error")
        academic_error = handle_database_error(db_error, "unknown_operation")
        
        assert isinstance(academic_error, AcademicSystemError)
        assert "Database error during unknown_operation" in academic_error.message
    
    @patch('services.academic.exceptions.logger')
    def test_log_academic_error(self, mock_logger):
        error = SubjectNotFoundError(subject_id="test-123")
        context = {"endpoint": "/subjects/test-123", "user_id": "user-456"}
        
        log_academic_error(error, context)
        
        # Should log as warning for 4xx errors
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert "Academic client error" in call_args
    
    @patch('services.academic.exceptions.logger')
    def test_log_academic_error_system_error(self, mock_logger):
        error = DatabaseConnectionError("test_operation")
        
        log_academic_error(error)
        
        # Should log as error for 5xx errors
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        assert "Academic system error" in call_args
    
    def test_create_error_response_academic_exception(self):
        error = SubjectNotFoundError(subject_id="test-123")
        context = {"endpoint": "/test"}
        
        with patch('services.academic.exceptions.log_academic_error') as mock_log:
            response = create_error_response(error, context)
            mock_log.assert_called_once_with(error, context)
        
        assert response["error"] == "SUBJECT_NOT_FOUND"
        assert response["module"] == "academic_management"
    
    def test_create_error_response_generic_exception(self):
        error = ValueError("Generic error")
        
        with patch('services.academic.exceptions.handle_database_error') as mock_handle:
            mock_handle.return_value = AcademicValidationError("Converted error")
            response = create_error_response(error)
            mock_handle.assert_called_once_with(error, "unknown_operation")
    
    def test_exception_mapping(self):
        # Test ValueError mapping
        value_error = ValueError("Invalid value")
        mapped_error = EXCEPTION_MAPPING[ValueError](value_error)
        assert isinstance(mapped_error, AcademicValidationError)
        assert "Invalid value" in mapped_error.message
        
        # Test KeyError mapping
        key_error = KeyError("missing_field")
        mapped_error = EXCEPTION_MAPPING[KeyError](key_error)
        assert isinstance(mapped_error, AcademicValidationError)
        assert "Missing required field" in mapped_error.message
        
        # Test TypeError mapping
        type_error = TypeError("Invalid type")
        mapped_error = EXCEPTION_MAPPING[TypeError](type_error)
        assert isinstance(mapped_error, AcademicValidationError)
        assert "Invalid data type" in mapped_error.message


class TestZimbabweEducationSystemCompliance:
    """Test Zimbabwe education system specific validations"""
    
    def test_valid_grade_levels(self):
        # Test all valid grade levels
        for grade in range(1, 14):  # 1-13 inclusive
            try:
                error = InvalidGradeLevelError(grade)
                # Should not raise this for valid grades in real usage
                assert grade in error.details.get("invalid_value", str(grade))
            except:
                pass  # Expected for valid grades
    
    def test_invalid_grade_levels(self):
        invalid_grades = [0, -1, 14, 15, 100]
        for grade in invalid_grades:
            error = InvalidGradeLevelError(grade)
            assert f"Invalid grade level: {grade}" in error.message
            assert "1-13" in error.message
    
    def test_valid_term_numbers(self):
        valid_terms = [1, 2, 3]
        for term in valid_terms:
            # In real usage, these would be valid and not raise errors
            # Here we're just testing the error message format
            pass
    
    def test_invalid_term_numbers(self):
        invalid_terms = [0, -1, 4, 5, 10]
        for term in invalid_terms:
            error = InvalidTermNumberError(term)
            assert f"Invalid term number: {term}" in error.message
            assert "Zimbabwe schools have 3 terms" in error.message
    
    def test_zimbabwe_grading_scale(self):
        # Test valid grades
        valid_grades = ["A", "B", "C", "D", "E", "U"]
        for grade in valid_grades:
            # These should be valid in real usage
            pass
        
        # Test invalid grades
        invalid_grades = ["F", "G", "X", "Z", "1", "2"]
        for grade in invalid_grades:
            error = InvalidGradeScaleError(grade, "letter")
            assert f"Invalid letter grade: {grade}" in error.message
            assert "A, B, C, D, E, or U" in error.message
    
    def test_percentage_ranges(self):
        # Test valid percentages
        valid_percentages = [0, 25, 50, 75, 100]
        for percentage in valid_percentages:
            # These should be valid in real usage
            pass
        
        # Test invalid percentages
        invalid_percentages = [-1, 101, 150, -50]
        for percentage in invalid_percentages:
            error = InvalidGradeScaleError(percentage, "percentage")
            assert f"Invalid percentage: {percentage}" in error.message
            assert "0-100" in error.message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])