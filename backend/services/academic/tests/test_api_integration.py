"""
Academic Management Module - API Integration Tests
Comprehensive integration tests for Academic Management API endpoints
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4, UUID
from datetime import datetime, date

from services.academic.main import router as academic_router
from services.academic.middleware import AcademicAuthContext
from services.academic.exceptions import (
    SubjectNotFoundError,
    InvalidGradeLevelError,
    InsufficientPermissionError,
    DuplicateSubjectError
)

# Test fixtures and mock data
MOCK_SCHOOL_ID = "123e4567-e89b-12d3-a456-426614174000"
MOCK_USER_ID = "456e7890-e12b-34d5-a678-901234567890"
MOCK_SUBJECT_ID = "789e0123-e45b-67d8-a901-234567890123"

MOCK_SUBJECT_DATA = {
    "id": MOCK_SUBJECT_ID,
    "code": "MATH",
    "name": "Mathematics",
    "description": "Core mathematics curriculum",
    "department": "Sciences",
    "grade_level": 10,
    "is_core": True,
    "credit_hours": 5,
    "school_id": MOCK_SCHOOL_ID,
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": datetime.utcnow().isoformat(),
    "is_active": True
}

MOCK_PAGINATED_SUBJECTS = {
    "items": [MOCK_SUBJECT_DATA],
    "total_count": 1,
    "page": 1,
    "page_size": 20,
    "total_pages": 1,
    "has_next": False,
    "has_prev": False
}

MOCK_ASSESSMENT_DATA = {
    "id": "abc01234-e567-89ab-cdef-0123456789ab",
    "name": "Term 1 Mathematics Test",
    "description": "Mid-term assessment",
    "subject_id": MOCK_SUBJECT_ID,
    "class_id": "def01234-e567-89ab-cdef-0123456789ab",
    "teacher_id": MOCK_USER_ID,
    "assessment_type": "test",
    "term_number": 1,
    "total_marks": 100,
    "pass_mark": 50,
    "assessment_date": "2024-03-15",
    "school_id": MOCK_SCHOOL_ID,
    "created_at": datetime.utcnow().isoformat()
}

MOCK_GRADE_DATA = {
    "id": "ghi01234-e567-89ab-cdef-0123456789ab",
    "assessment_id": MOCK_ASSESSMENT_DATA["id"],
    "student_id": "jkl01234-e567-89ab-cdef-0123456789ab",
    "marks_obtained": 85,
    "total_marks": 100,
    "percentage": 85.0,
    "letter_grade": "A",
    "grade_points": 4.0,
    "school_id": MOCK_SCHOOL_ID
}

MOCK_ATTENDANCE_SESSION = {
    "id": "mno01234-e567-89ab-cdef-0123456789ab",
    "subject_id": MOCK_SUBJECT_ID,
    "class_id": "def01234-e567-89ab-cdef-0123456789ab",
    "teacher_id": MOCK_USER_ID,
    "session_date": "2024-08-13",
    "period_number": 3,
    "lesson_topic": "Quadratic Equations",
    "total_students": 30,
    "students_present": 28,
    "students_absent": 2,
    "school_id": MOCK_SCHOOL_ID
}


class MockAuthContext:
    """Mock authentication context for testing"""
    
    def __init__(self, user_role="teacher", permissions=None, school_id=MOCK_SCHOOL_ID):
        self.user = Mock()
        self.user.id = MOCK_USER_ID
        self.tenant = Mock()
        self.school_id = UUID(school_id)
        self.user_role = user_role
        self.permissions = permissions or ["academic.subject.read", "academic.subject.create"]
        self.teacher_id = UUID(MOCK_USER_ID) if user_role == "teacher" else None
        self.student_id = None
    
    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions or "*" in self.permissions
    
    def can_manage_subjects(self) -> bool:
        return self.has_permission("academic.subject.create")
    
    def can_manage_assessments(self) -> bool:
        return self.has_permission("academic.assessment.create")
    
    def can_enter_grades(self) -> bool:
        return self.has_permission("academic.grade.create")
    
    def can_mark_attendance(self) -> bool:
        return self.has_permission("academic.attendance.create")


@pytest.fixture
def mock_auth_context():
    """Provide mock authentication context"""
    return MockAuthContext()


@pytest.fixture
def mock_admin_auth_context():
    """Provide mock admin authentication context"""
    return MockAuthContext(user_role="school_admin", permissions=["*"])


@pytest.fixture
def mock_student_auth_context():
    """Provide mock student authentication context"""
    return MockAuthContext(user_role="student", permissions=["academic.subject.read"])


class TestSubjectEndpoints:
    """Test subject management endpoints"""
    
    @patch('services.academic.api.crud.create_subject')
    @patch('services.academic.api.require_subject_write')
    async def test_create_subject_success(self, mock_auth, mock_crud, mock_auth_context):
        """Test successful subject creation"""
        mock_auth.return_value = mock_auth_context
        mock_crud.return_value = MOCK_SUBJECT_DATA
        
        # Test data
        subject_data = {
            "code": "MATH",
            "name": "Mathematics", 
            "description": "Core mathematics curriculum",
            "department": "Sciences",
            "grade_level": 10,
            "is_core": True,
            "credit_hours": 5
        }
        
        # Mock the endpoint
        from services.academic.api import create_subject_endpoint
        
        with patch('services.academic.api.get_db'):
            result = await create_subject_endpoint(
                subject_data=Mock(**subject_data),
                db=Mock(),
                auth_context=mock_auth_context
            )
        
        assert result == MOCK_SUBJECT_DATA
        mock_crud.assert_called_once()
    
    @patch('services.academic.api.crud.create_subject')
    @patch('services.academic.api.require_subject_write')
    async def test_create_subject_duplicate_error(self, mock_auth, mock_crud, mock_auth_context):
        """Test subject creation with duplicate code"""
        mock_auth.return_value = mock_auth_context
        mock_crud.side_effect = DuplicateSubjectError("MATH", "Test School")
        
        subject_data = {"code": "MATH", "name": "Mathematics"}
        
        from services.academic.api import create_subject_endpoint
        
        with pytest.raises(Exception) as exc_info:
            with patch('services.academic.api.get_db'):
                await create_subject_endpoint(
                    subject_data=Mock(**subject_data),
                    db=Mock(),
                    auth_context=mock_auth_context
                )
        
        # Should raise HTTPException with duplicate error details
        assert "MATH" in str(exc_info.value)
    
    @patch('services.academic.api.crud.get_subjects')
    @patch('services.academic.api.require_subject_read')
    async def test_get_subjects_success(self, mock_auth, mock_crud, mock_auth_context):
        """Test successful subjects listing"""
        mock_auth.return_value = mock_auth_context
        mock_crud.return_value = ([MOCK_SUBJECT_DATA], 1)
        
        from services.academic.api import get_subjects_endpoint
        
        with patch('services.academic.api.get_db'):
            result = await get_subjects_endpoint(
                page=1,
                page_size=20,
                grade_level=None,
                department=None,
                is_core=None,
                search=None,
                db=Mock(),
                auth_context=mock_auth_context
            )
        
        assert result.items == [MOCK_SUBJECT_DATA]
        assert result.total_count == 1
        assert result.page == 1
        assert result.page_size == 20
    
    @patch('services.academic.api.require_subject_read')
    async def test_get_subjects_invalid_grade_level(self, mock_auth, mock_auth_context):
        """Test subjects listing with invalid grade level"""
        mock_auth.return_value = mock_auth_context
        
        from services.academic.api import get_subjects_endpoint
        
        with pytest.raises(Exception) as exc_info:
            with patch('services.academic.api.get_db'):
                await get_subjects_endpoint(
                    page=1,
                    page_size=20,
                    grade_level=15,  # Invalid grade level
                    department=None,
                    is_core=None,
                    search=None,
                    db=Mock(),
                    auth_context=mock_auth_context
                )
        
        # Should raise InvalidGradeLevelError
        assert "15" in str(exc_info.value)
    
    @patch('services.academic.api.crud.get_subject')
    @patch('services.academic.api.require_subject_read')
    async def test_get_subject_success(self, mock_auth, mock_crud, mock_auth_context):
        """Test successful single subject retrieval"""
        mock_auth.return_value = mock_auth_context
        mock_crud.return_value = MOCK_SUBJECT_DATA
        
        from services.academic.api import get_subject_endpoint
        
        with patch('services.academic.api.get_db'):
            result = await get_subject_endpoint(
                subject_id=UUID(MOCK_SUBJECT_ID),
                db=Mock(),
                auth_context=mock_auth_context
            )
        
        assert result == MOCK_SUBJECT_DATA
    
    @patch('services.academic.api.crud.get_subject')
    @patch('services.academic.api.require_subject_read')
    async def test_get_subject_not_found(self, mock_auth, mock_crud, mock_auth_context):
        """Test subject retrieval when subject doesn't exist"""
        mock_auth.return_value = mock_auth_context
        mock_crud.return_value = None
        
        from services.academic.api import get_subject_endpoint
        
        with pytest.raises(Exception) as exc_info:
            with patch('services.academic.api.get_db'):
                await get_subject_endpoint(
                    subject_id=UUID(MOCK_SUBJECT_ID),
                    db=Mock(),
                    auth_context=mock_auth_context
                )
        
        # Should raise SubjectNotFoundError
        assert "not found" in str(exc_info.value).lower()


class TestAssessmentEndpoints:
    """Test assessment management endpoints"""
    
    @patch('services.academic.api.crud.create_assessment')
    @patch('services.academic.api.require_assessment_write')
    async def test_create_assessment_success(self, mock_auth, mock_crud, mock_auth_context):
        """Test successful assessment creation"""
        mock_auth.return_value = mock_auth_context
        mock_crud.return_value = MOCK_ASSESSMENT_DATA
        
        assessment_data = {
            "name": "Term 1 Mathematics Test",
            "subject_id": MOCK_SUBJECT_ID,
            "assessment_type": "test",
            "term_number": 1,
            "total_marks": 100
        }
        
        from services.academic.api import create_assessment_endpoint
        
        with patch('services.academic.api.get_db'):
            result = await create_assessment_endpoint(
                assessment_data=Mock(**assessment_data),
                db=Mock(),
                auth_context=mock_auth_context
            )
        
        assert result == MOCK_ASSESSMENT_DATA
    
    @patch('services.academic.api.crud.get_assessments')
    @patch('services.academic.api.get_academic_auth_context')
    async def test_get_assessments_success(self, mock_auth, mock_crud, mock_auth_context):
        """Test successful assessments listing"""
        mock_auth.return_value = mock_auth_context
        mock_crud.return_value = ([MOCK_ASSESSMENT_DATA], 1)
        
        from services.academic.api import get_assessments_endpoint
        
        with patch('services.academic.api.get_db'):
            result = await get_assessments_endpoint(
                page=1,
                page_size=20,
                subject_id=None,
                class_id=None,
                term_number=None,
                assessment_type=None,
                db=Mock(),
                auth_context=mock_auth_context
            )
        
        assert result.items == [MOCK_ASSESSMENT_DATA]
        assert result.total_count == 1
    
    @patch('services.academic.api.get_academic_auth_context')
    async def test_get_assessments_invalid_term(self, mock_auth, mock_auth_context):
        """Test assessments listing with invalid term number"""
        mock_auth.return_value = mock_auth_context
        
        from services.academic.api import get_assessments_endpoint
        
        with pytest.raises(Exception) as exc_info:
            with patch('services.academic.api.get_db'):
                await get_assessments_endpoint(
                    page=1,
                    page_size=20,
                    subject_id=None,
                    class_id=None,
                    term_number=5,  # Invalid term
                    assessment_type=None,
                    db=Mock(),
                    auth_context=mock_auth_context
                )
        
        assert "5" in str(exc_info.value)


class TestGradeEndpoints:
    """Test grade management endpoints"""
    
    @patch('services.academic.api.crud.submit_bulk_grades')
    @patch('services.academic.api.require_grade_write')
    async def test_submit_bulk_grades_success(self, mock_auth, mock_crud, mock_auth_context):
        """Test successful bulk grade submission"""
        mock_auth.return_value = mock_auth_context
        mock_crud.return_value = {"grades_submitted": 5, "grades_updated": 2}
        
        grade_data = Mock()
        grade_data.assessment_id = UUID(MOCK_ASSESSMENT_DATA["id"])
        
        from services.academic.api import submit_bulk_grades_endpoint
        
        with patch('services.academic.api.get_db'):
            result = await submit_bulk_grades_endpoint(
                grade_data=grade_data,
                db=Mock(),
                auth_context=mock_auth_context
            )
        
        assert result["message"] == "Grades submitted successfully"
        assert result["grades_submitted"] == 5
        assert result["grades_updated"] == 2
    
    @patch('services.academic.api.crud.get_assessment_grades')
    @patch('services.academic.api.get_academic_auth_context')
    async def test_get_assessment_grades_success(self, mock_auth, mock_crud, mock_auth_context):
        """Test successful assessment grades retrieval"""
        mock_auth.return_value = mock_auth_context
        mock_crud.return_value = [MOCK_GRADE_DATA]
        
        from services.academic.api import get_assessment_grades_endpoint
        
        with patch('services.academic.api.get_db'):
            result = await get_assessment_grades_endpoint(
                assessment_id=UUID(MOCK_ASSESSMENT_DATA["id"]),
                db=Mock(),
                auth_context=mock_auth_context
            )
        
        assert result == [MOCK_GRADE_DATA]


class TestAttendanceEndpoints:
    """Test attendance management endpoints"""
    
    @patch('services.academic.api.crud.create_attendance_session')
    @patch('services.academic.api.require_attendance_write')
    async def test_create_attendance_session_success(self, mock_auth, mock_crud, mock_auth_context):
        """Test successful attendance session creation"""
        mock_auth.return_value = mock_auth_context
        mock_crud.return_value = MOCK_ATTENDANCE_SESSION
        
        session_data = {
            "subject_id": MOCK_SUBJECT_ID,
            "class_id": "def01234-e567-89ab-cdef-0123456789ab",
            "session_date": "2024-08-13",
            "period_number": 3,
            "lesson_topic": "Quadratic Equations"
        }
        
        from services.academic.api import create_attendance_session_endpoint
        
        with patch('services.academic.api.get_db'):
            result = await create_attendance_session_endpoint(
                session_data=Mock(**session_data),
                db=Mock(),
                auth_context=mock_auth_context
            )
        
        assert result == MOCK_ATTENDANCE_SESSION
    
    @patch('services.academic.api.crud.mark_bulk_attendance')
    @patch('services.academic.api.require_attendance_write')
    async def test_mark_bulk_attendance_success(self, mock_auth, mock_crud, mock_auth_context):
        """Test successful bulk attendance marking"""
        mock_auth.return_value = mock_auth_context
        mock_crud.return_value = {"records_processed": 30}
        
        attendance_data = Mock()
        
        from services.academic.api import mark_bulk_attendance_endpoint
        
        with patch('services.academic.api.get_db'):
            result = await mark_bulk_attendance_endpoint(
                attendance_data=attendance_data,
                db=Mock(),
                auth_context=mock_auth_context
            )
        
        assert result["message"] == "Attendance marked successfully"
        assert result["records_processed"] == 30


class TestPermissionHandling:
    """Test permission-based access control"""
    
    @patch('services.academic.api.require_subject_write')
    async def test_create_subject_insufficient_permissions(self, mock_auth, mock_student_auth_context):
        """Test subject creation with insufficient permissions"""
        # Student trying to create subject should fail
        mock_auth.side_effect = InsufficientPermissionError(
            "academic.subject.create", "student", "create subjects"
        )
        
        from services.academic.api import create_subject_endpoint
        
        with pytest.raises(Exception) as exc_info:
            with patch('services.academic.api.get_db'):
                await create_subject_endpoint(
                    subject_data=Mock(),
                    db=Mock(),
                    auth_context=mock_student_auth_context
                )
        
        assert "Insufficient permissions" in str(exc_info.value)


class TestUtilityEndpoints:
    """Test utility and information endpoints"""
    
    async def test_health_check(self):
        """Test health check endpoint"""
        from services.academic.api import health_check
        
        result = await health_check()
        
        assert result["status"] == "healthy"
        assert result["service"] == "academic-management"
    
    async def test_get_terms_enum(self):
        """Test terms enumeration endpoint"""
        from services.academic.api import get_terms_enum
        
        result = await get_terms_enum()
        
        assert len(result) == 3
        assert result[0]["value"] == 1
        assert result[0]["label"] == "Term 1"
        assert "January - April" in result[0]["description"]
    
    async def test_get_assessment_types_enum(self):
        """Test assessment types enumeration"""
        from services.academic.api import get_assessment_types_enum
        
        with patch('services.academic.api.AssessmentType') as mock_enum:
            mock_enum.__iter__ = Mock(return_value=iter([Mock(value="test"), Mock(value="exam")]))
            
            result = await get_assessment_types_enum()
            
            assert len(result) == 2
            assert result[0]["value"] == "test"
            assert result[0]["label"] == "Test"


class TestErrorHandling:
    """Test comprehensive error handling"""
    
    @patch('services.academic.api.crud.create_subject')
    @patch('services.academic.api.require_subject_write')
    async def test_database_error_handling(self, mock_auth, mock_crud, mock_auth_context):
        """Test handling of database errors"""
        mock_auth.return_value = mock_auth_context
        mock_crud.side_effect = Exception("Database connection failed")
        
        from services.academic.api import create_subject_endpoint
        
        with pytest.raises(Exception) as exc_info:
            with patch('services.academic.api.get_db'):
                await create_subject_endpoint(
                    subject_data=Mock(),
                    db=Mock(),
                    auth_context=mock_auth_context
                )
        
        # Should be converted to academic exception
        assert "Database" in str(exc_info.value) or "error" in str(exc_info.value).lower()
    
    @patch('services.academic.api.log_academic_error')
    @patch('services.academic.api.crud.get_subject')
    @patch('services.academic.api.require_subject_read')
    async def test_error_logging(self, mock_auth, mock_crud, mock_log, mock_auth_context):
        """Test that errors are properly logged"""
        mock_auth.return_value = mock_auth_context
        mock_crud.return_value = None  # Subject not found
        
        from services.academic.api import get_subject_endpoint
        
        with pytest.raises(Exception):
            with patch('services.academic.api.get_db'):
                await get_subject_endpoint(
                    subject_id=UUID(MOCK_SUBJECT_ID),
                    db=Mock(),
                    auth_context=mock_auth_context
                )
        
        # Should have logged the error
        mock_log.assert_called()


class TestZimbabweEducationCompliance:
    """Test Zimbabwe education system compliance"""
    
    async def test_grade_level_validation(self):
        """Test grade level validation for Zimbabwe system"""
        from services.academic.api import get_subjects_endpoint
        
        # Test invalid grade levels
        invalid_grades = [0, -1, 14, 15, 100]
        
        for grade in invalid_grades:
            with pytest.raises(Exception):
                with patch('services.academic.api.get_db'), \
                     patch('services.academic.api.require_subject_read'):
                    await get_subjects_endpoint(
                        page=1,
                        page_size=20,
                        grade_level=grade,
                        department=None,
                        is_core=None,
                        search=None,
                        db=Mock(),
                        auth_context=MockAuthContext()
                    )
    
    async def test_term_validation(self):
        """Test academic term validation"""
        from services.academic.api import get_assessments_endpoint
        
        # Test invalid terms
        invalid_terms = [0, -1, 4, 5, 10]
        
        for term in invalid_terms:
            with pytest.raises(Exception):
                with patch('services.academic.api.get_db'), \
                     patch('services.academic.api.get_academic_auth_context'):
                    await get_assessments_endpoint(
                        page=1,
                        page_size=20,
                        subject_id=None,
                        class_id=None,
                        term_number=term,
                        assessment_type=None,
                        db=Mock(),
                        auth_context=MockAuthContext()
                    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])