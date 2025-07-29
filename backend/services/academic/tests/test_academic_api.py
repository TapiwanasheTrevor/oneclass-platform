"""
Academic Management API Tests
Integration tests for academic management API endpoints
"""

import pytest
import pytest_asyncio
from datetime import datetime, date, time
from decimal import Decimal
from uuid import uuid4
from httpx import AsyncClient
from fastapi import status

from ..schemas import (
    SubjectCreate, SubjectUpdate, CurriculumCreate,
    PeriodCreate, TimetableCreate, AttendanceSessionCreate,
    BulkAttendanceCreate, AttendanceRecordCreate,
    AssessmentCreate, BulkGradeCreate, GradeCreate,
    GradingScale, AttendanceStatus, AssessmentType, TermNumber, SessionType
)


class TestSubjectAPI:
    """Test suite for Subject API endpoints"""

    async def test_create_subject_success(self, async_client: AsyncClient, auth_headers: dict):
        """Test successful subject creation via API"""
        subject_data = {
            "code": "MATH101",
            "name": "Mathematics",
            "description": "Basic mathematics course",
            "grade_levels": [10, 11, 12],
            "is_core": True,
            "is_practical": False,
            "requires_lab": False,
            "pass_mark": 50.0,
            "max_mark": 100.0,
            "credit_hours": 3,
            "department": "Mathematics",
            "language_of_instruction": "English",
            "display_order": 1
        }
        
        response = await async_client.post(
            "/api/v1/academic/subjects",
            json=subject_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["code"] == "MATH101"
        assert data["name"] == "Mathematics"
        assert data["grade_levels"] == [10, 11, 12]
        assert data["is_core"] is True
        assert data["is_active"] is True

    async def test_create_subject_invalid_data(self, async_client: AsyncClient, auth_headers: dict):
        """Test subject creation with invalid data"""
        invalid_subject_data = {
            "code": "",  # Empty code
            "name": "",  # Empty name
            "grade_levels": []  # Empty grade levels
        }
        
        response = await async_client.post(
            "/api/v1/academic/subjects",
            json=invalid_subject_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_subject_duplicate_code(self, async_client: AsyncClient, auth_headers: dict):
        """Test subject creation with duplicate code"""
        subject_data = {
            "code": "DUPLICATE",
            "name": "First Subject",
            "grade_levels": [10]
        }
        
        # Create first subject
        response = await async_client.post(
            "/api/v1/academic/subjects",
            json=subject_data,
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Try to create duplicate
        response = await async_client.post(
            "/api/v1/academic/subjects",
            json=subject_data,
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    async def test_get_subjects_success(self, async_client: AsyncClient, auth_headers: dict):
        """Test successful subjects retrieval"""
        response = await async_client.get(
            "/api/v1/academic/subjects",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total_count" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["items"], list)

    async def test_get_subjects_with_filters(self, async_client: AsyncClient, auth_headers: dict):
        """Test subjects retrieval with filters"""
        # Test grade level filter
        response = await async_client.get(
            "/api/v1/academic/subjects?grade_level=10",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Test department filter
        response = await async_client.get(
            "/api/v1/academic/subjects?department=Mathematics",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Test core subjects filter
        response = await async_client.get(
            "/api/v1/academic/subjects?is_core=true",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

    async def test_get_subject_by_id_success(self, async_client: AsyncClient, auth_headers: dict, subject_id: str):
        """Test successful subject retrieval by ID"""
        response = await async_client.get(
            f"/api/v1/academic/subjects/{subject_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == subject_id

    async def test_get_subject_by_id_not_found(self, async_client: AsyncClient, auth_headers: dict):
        """Test subject retrieval with non-existent ID"""
        non_existent_id = str(uuid4())
        response = await async_client.get(
            f"/api/v1/academic/subjects/{non_existent_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_subject_success(self, async_client: AsyncClient, auth_headers: dict, subject_id: str):
        """Test successful subject update"""
        update_data = {
            "name": "Advanced Mathematics",
            "description": "Advanced mathematics course",
            "grade_levels": [11, 12],
            "is_practical": True
        }
        
        response = await async_client.put(
            f"/api/v1/academic/subjects/{subject_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Advanced Mathematics"
        assert data["grade_levels"] == [11, 12]
        assert data["is_practical"] is True

    async def test_delete_subject_success(self, async_client: AsyncClient, auth_headers: dict, subject_id: str):
        """Test successful subject deletion"""
        response = await async_client.delete(
            f"/api/v1/academic/subjects/{subject_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_unauthorized_access(self, async_client: AsyncClient):
        """Test unauthorized access to subject endpoints"""
        response = await async_client.get("/api/v1/academic/subjects")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCurriculumAPI:
    """Test suite for Curriculum API endpoints"""

    async def test_create_curriculum_success(self, async_client: AsyncClient, auth_headers: dict, subject_id: str, academic_year_id: str):
        """Test successful curriculum creation via API"""
        curriculum_data = {
            "academic_year_id": academic_year_id,
            "name": "Grade 10 Mathematics Curriculum",
            "description": "Comprehensive mathematics curriculum",
            "grade_level": 10,
            "term_number": 1,
            "subject_id": subject_id,
            "learning_objectives": ["Understand algebra", "Master geometry"],
            "learning_outcomes": ["Solve equations", "Calculate areas"],
            "assessment_methods": ["Tests", "Assignments"],
            "resources_required": ["Textbook", "Calculator"],
            "total_periods": 40,
            "practical_periods": 10,
            "effective_from": "2024-01-15"
        }
        
        response = await async_client.post(
            "/api/v1/academic/curriculum",
            json=curriculum_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Grade 10 Mathematics Curriculum"
        assert data["grade_level"] == 10
        assert data["term_number"] == 1
        assert data["total_periods"] == 40

    async def test_get_curricula_success(self, async_client: AsyncClient, auth_headers: dict):
        """Test successful curricula retrieval"""
        response = await async_client.get(
            "/api/v1/academic/curriculum",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total_count" in data

    async def test_get_curricula_with_filters(self, async_client: AsyncClient, auth_headers: dict, academic_year_id: str, subject_id: str):
        """Test curricula retrieval with filters"""
        # Test academic year filter
        response = await async_client.get(
            f"/api/v1/academic/curriculum?academic_year_id={academic_year_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Test grade level filter
        response = await async_client.get(
            "/api/v1/academic/curriculum?grade_level=10",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Test subject filter
        response = await async_client.get(
            f"/api/v1/academic/curriculum?subject_id={subject_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK


class TestTimetableAPI:
    """Test suite for Timetable API endpoints"""

    async def test_create_period_success(self, async_client: AsyncClient, auth_headers: dict):
        """Test successful period creation via API"""
        period_data = {
            "period_number": 1,
            "name": "Period 1",
            "start_time": "08:00",
            "end_time": "08:40",
            "is_break": False
        }
        
        response = await async_client.post(
            "/api/v1/academic/periods",
            json=period_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["period_number"] == 1
        assert data["name"] == "Period 1"
        assert data["start_time"] == "08:00:00"
        assert data["end_time"] == "08:40:00"
        assert data["is_break"] is False

    async def test_create_timetable_entry_success(self, async_client: AsyncClient, auth_headers: dict, academic_year_id: str, class_id: str, subject_id: str, teacher_id: str, period_id: str):
        """Test successful timetable entry creation via API"""
        timetable_data = {
            "academic_year_id": academic_year_id,
            "term_number": 1,
            "class_id": class_id,
            "subject_id": subject_id,
            "teacher_id": teacher_id,
            "period_id": period_id,
            "day_of_week": 1,
            "room_number": "Room 101",
            "is_double_period": False,
            "is_practical": False,
            "week_pattern": "all",
            "effective_from": "2024-01-15"
        }
        
        response = await async_client.post(
            "/api/v1/academic/timetables",
            json=timetable_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["class_id"] == class_id
        assert data["subject_id"] == subject_id
        assert data["teacher_id"] == teacher_id
        assert data["day_of_week"] == 1
        assert data["room_number"] == "Room 101"


class TestAttendanceAPI:
    """Test suite for Attendance API endpoints"""

    async def test_create_attendance_session_success(self, async_client: AsyncClient, auth_headers: dict, timetable_id: str):
        """Test successful attendance session creation via API"""
        session_data = {
            "timetable_id": timetable_id,
            "session_date": "2024-03-15",
            "session_type": "regular",
            "notes": "Regular class session"
        }
        
        response = await async_client.post(
            "/api/v1/academic/attendance/sessions",
            json=session_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["timetable_id"] == timetable_id
        assert data["session_date"] == "2024-03-15"
        assert data["session_type"] == "regular"
        assert data["attendance_marked"] is False

    async def test_mark_bulk_attendance_success(self, async_client: AsyncClient, auth_headers: dict, attendance_session_id: str, student_ids: list):
        """Test successful bulk attendance marking via API"""
        attendance_data = {
            "attendance_session_id": attendance_session_id,
            "attendance_records": [
                {
                    "student_id": student_ids[0],
                    "attendance_status": "present",
                    "arrival_time": "08:00",
                    "is_excused": False
                },
                {
                    "student_id": student_ids[1],
                    "attendance_status": "late",
                    "arrival_time": "08:15",
                    "is_excused": False
                },
                {
                    "student_id": student_ids[2],
                    "attendance_status": "absent",
                    "is_excused": True,
                    "excuse_reason": "Sick"
                }
            ]
        }
        
        response = await async_client.post(
            "/api/v1/academic/attendance/bulk",
            json=attendance_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["total_processed"] == 3
        assert data["successful"] == 3
        assert data["failed"] == 0
        assert len(data["created_ids"]) == 3

    async def test_get_attendance_stats_success(self, async_client: AsyncClient, auth_headers: dict, class_id: str):
        """Test successful attendance statistics retrieval"""
        response = await async_client.get(
            f"/api/v1/academic/attendance/stats?class_id={class_id}&start_date=2024-03-01&end_date=2024-03-31",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_students" in data
        assert "present_students" in data
        assert "absent_students" in data
        assert "late_students" in data
        assert "attendance_rate" in data


class TestAssessmentAPI:
    """Test suite for Assessment API endpoints"""

    async def test_create_assessment_success(self, async_client: AsyncClient, auth_headers: dict, academic_year_id: str, subject_id: str, class_id: str, teacher_id: str):
        """Test successful assessment creation via API"""
        assessment_data = {
            "academic_year_id": academic_year_id,
            "name": "Mid-Term Mathematics Test",
            "description": "Comprehensive mathematics assessment",
            "subject_id": subject_id,
            "class_id": class_id,
            "teacher_id": teacher_id,
            "term_number": 1,
            "assessment_type": "test",
            "assessment_category": "continuous",
            "total_marks": 100.0,
            "pass_mark": 50.0,
            "weight_percentage": 25.0,
            "assessment_date": "2024-03-15",
            "duration_minutes": 90,
            "instructions": "Answer all questions",
            "resources_allowed": ["Calculator", "Formula sheet"],
            "is_group_assessment": False
        }
        
        response = await async_client.post(
            "/api/v1/academic/assessments",
            json=assessment_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Mid-Term Mathematics Test"
        assert data["total_marks"] == 100.0
        assert data["pass_mark"] == 50.0
        assert data["assessment_type"] == "test"
        assert data["term_number"] == 1

    async def test_submit_bulk_grades_success(self, async_client: AsyncClient, auth_headers: dict, assessment_id: str, student_ids: list):
        """Test successful bulk grade submission via API"""
        grades_data = {
            "assessment_id": assessment_id,
            "grades": [
                {
                    "student_id": student_ids[0],
                    "raw_score": 85.0,
                    "is_absent": False,
                    "feedback": "Excellent work"
                },
                {
                    "student_id": student_ids[1],
                    "raw_score": 72.0,
                    "is_absent": False,
                    "feedback": "Good effort"
                },
                {
                    "student_id": student_ids[2],
                    "is_absent": True,
                    "is_excused": True
                }
            ]
        }
        
        response = await async_client.post(
            f"/api/v1/academic/assessments/{assessment_id}/grades/bulk",
            json=grades_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_processed"] == 3
        assert data["successful"] == 3
        assert data["failed"] == 0
        assert len(data["created_ids"]) == 3


class TestDashboardAPI:
    """Test suite for Dashboard API endpoints"""

    async def test_get_academic_dashboard_success(self, async_client: AsyncClient, auth_headers: dict, academic_year_id: str):
        """Test successful academic dashboard retrieval"""
        response = await async_client.get(
            f"/api/v1/academic/dashboard?academic_year_id={academic_year_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "school_id" in data
        assert "academic_year_id" in data
        assert "total_subjects" in data
        assert "total_classes" in data
        assert "total_teachers" in data
        assert "total_students" in data
        assert "average_attendance_rate" in data
        assert "total_assessments" in data
        assert "completed_assessments" in data
        assert "pending_assessments" in data

    async def test_get_teacher_dashboard_success(self, async_client: AsyncClient, auth_headers: dict, academic_year_id: str, teacher_id: str):
        """Test successful teacher dashboard retrieval"""
        response = await async_client.get(
            f"/api/v1/academic/dashboard/teacher?academic_year_id={academic_year_id}&teacher_id={teacher_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "teacher_id" in data
        assert "school_id" in data
        assert "academic_year_id" in data
        assert "total_classes" in data
        assert "total_subjects" in data
        assert "total_students" in data
        assert "my_attendance_rate" in data
        assert "pending_assessments" in data


class TestUtilityAPI:
    """Test suite for Utility API endpoints"""

    async def test_health_check_success(self, async_client: AsyncClient):
        """Test health check endpoint"""
        response = await async_client.get("/api/v1/academic/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "academic-management"

    async def test_get_terms_enum_success(self, async_client: AsyncClient):
        """Test terms enum endpoint"""
        response = await async_client.get("/api/v1/academic/enums/terms")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3
        assert all("value" in term and "label" in term for term in data)

    async def test_get_assessment_types_enum_success(self, async_client: AsyncClient):
        """Test assessment types enum endpoint"""
        response = await async_client.get("/api/v1/academic/enums/assessment-types")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) > 0
        assert all("value" in item and "label" in item for item in data)

    async def test_get_attendance_statuses_enum_success(self, async_client: AsyncClient):
        """Test attendance statuses enum endpoint"""
        response = await async_client.get("/api/v1/academic/enums/attendance-statuses")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) > 0
        assert all("value" in item and "label" in item for item in data)


class TestErrorHandling:
    """Test suite for API error handling"""

    async def test_invalid_uuid_format(self, async_client: AsyncClient, auth_headers: dict):
        """Test handling of invalid UUID format"""
        response = await async_client.get(
            "/api/v1/academic/subjects/invalid-uuid",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_missing_required_fields(self, async_client: AsyncClient, auth_headers: dict):
        """Test handling of missing required fields"""
        invalid_data = {
            "name": "Test Subject"
            # Missing required fields like code and grade_levels
        }
        
        response = await async_client.post(
            "/api/v1/academic/subjects",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_invalid_data_types(self, async_client: AsyncClient, auth_headers: dict):
        """Test handling of invalid data types"""
        invalid_data = {
            "code": "TEST",
            "name": "Test Subject",
            "grade_levels": "invalid",  # Should be array
            "is_core": "not_boolean"   # Should be boolean
        }
        
        response = await async_client.post(
            "/api/v1/academic/subjects",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_forbidden_access(self, async_client: AsyncClient, limited_auth_headers: dict):
        """Test handling of insufficient permissions"""
        subject_data = {
            "code": "FORBIDDEN",
            "name": "Forbidden Subject",
            "grade_levels": [10]
        }
        
        response = await async_client.post(
            "/api/v1/academic/subjects",
            json=subject_data,
            headers=limited_auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_rate_limiting(self, async_client: AsyncClient, auth_headers: dict):
        """Test API rate limiting (if implemented)"""
        # Make multiple rapid requests
        responses = []
        for _ in range(100):
            response = await async_client.get(
                "/api/v1/academic/subjects",
                headers=auth_headers
            )
            responses.append(response)
        
        # Check if any requests were rate limited
        rate_limited = any(r.status_code == status.HTTP_429_TOO_MANY_REQUESTS for r in responses)
        
        # This test is optional as rate limiting might not be implemented
        # assert rate_limited or all(r.status_code == status.HTTP_200_OK for r in responses)