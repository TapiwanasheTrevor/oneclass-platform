"""Test Configuration and Fixtures
Shared test configuration and fixtures for authentication tests
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
import uuid
from datetime import datetime

# Mock database modules globally
import sys
sys.modules['asyncpg'] = MagicMock()
sys.modules['psycopg2'] = MagicMock()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_school_data():
    """Mock school data for testing"""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "Demo High School",
        "code": "DEMO",
        "subdomain": "demo",
        "status": "active",
        "subscription_tier": "professional",
        "enabled_modules": ["sis", "finance", "academic", "advanced_reporting"],
        "configuration": {
            "branding": {
                "primary_color": "#2563eb",
                "secondary_color": "#10b981",
                "logo_url": "https://example.com/logo.png"
            },
            "features": {
                "attendance_tracking": True,
                "grade_management": True,
                "finance_module": True,
                "parent_portal": True
            },
            "academic": {
                "grading_system": "percentage",
                "term_system": "trimester",
                "grade_levels": ["1", "2", "3", "4", "5", "6", "7", "Form 1", "Form 2", "Form 3", "Form 4", "Lower 6", "Upper 6"]
            },
            "timezone": "Africa/Harare",
            "currency": "USD"
        },
        "settings": {
            "max_students": 1000,
            "academic_year": "2024",
            "contact_email": "info@demo.school",
            "phone": "+263123456789"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_user_data():
    """Mock user data for testing"""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440101",
        "email": "admin@demo.school",
        "first_name": "School",
        "last_name": "Administrator",
        "role": "school_admin",
        "is_active": True,
        "school_id": "550e8400-e29b-41d4-a716-446655440001",
        "permissions": [
            "students.create", "students.read", "students.update", "students.delete",
            "teachers.create", "teachers.read", "teachers.update", "teachers.delete",
            "classes.create", "classes.read", "classes.update", "classes.delete",
            "finance.read", "finance.write", "finance.reports",
            "settings.update", "users.manage", "reports.generate"
        ],
        "available_features": [
            "student_management", "attendance_tracking", "grade_management",
            "finance_module", "advanced_reporting", "parent_portal"
        ],
        "metadata": {
            "last_login": datetime.utcnow().isoformat(),
            "login_count": 50,
            "preferred_language": "en",
            "timezone": "Africa/Harare"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_teacher_data():
    """Mock teacher user data for testing"""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440102",
        "email": "teacher@demo.school",
        "first_name": "John",
        "last_name": "Teacher",
        "role": "teacher",
        "is_active": True,
        "school_id": "550e8400-e29b-41d4-a716-446655440001",
        "permissions": [
            "students.read", "attendance.mark", "grades.read", "grades.write",
            "classes.read", "assignments.create", "assignments.read", "assignments.update"
        ],
        "available_features": [
            "student_management", "attendance_tracking", "grade_management"
        ],
        "assigned_classes": ["class-math-101", "class-math-102"],
        "subjects": ["Mathematics", "Physics"],
        "metadata": {
            "employee_id": "EMP001",
            "department": "Mathematics",
            "qualification": "B.Sc Mathematics"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_student_data():
    """Mock student user data for testing"""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440103",
        "email": "student@demo.school",
        "first_name": "Jane",
        "last_name": "Student",
        "role": "student",
        "is_active": True,
        "school_id": "550e8400-e29b-41d4-a716-446655440001",
        "permissions": [
            "grades.read_own", "attendance.read_own", "assignments.read_own",
            "profile.read_own", "profile.update_own"
        ],
        "available_features": [
            "student_portal", "assignment_submission", "grade_viewing"
        ],
        "student_info": {
            "student_number": "2024001",
            "grade_level": "Form 4",
            "class": "4A",
            "enrollment_date": "2024-01-15",
            "guardian_email": "parent@demo.school"
        },
        "metadata": {
            "birth_date": "2008-03-15",
            "gender": "female",
            "address": "123 Student Street, Harare"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_parent_data():
    """Mock parent user data for testing"""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440104",
        "email": "parent@demo.school",
        "first_name": "Mary",
        "last_name": "Parent",
        "role": "parent",
        "is_active": True,
        "school_id": "550e8400-e29b-41d4-a716-446655440001",
        "permissions": [
            "children.read", "grades.read_children", "attendance.read_children",
            "assignments.read_children", "finance.read_children", "communications.read"
        ],
        "available_features": [
            "parent_portal", "child_progress_tracking", "communication"
        ],
        "children": [
            {
                "student_id": "550e8400-e29b-41d4-a716-446655440103",
                "student_name": "Jane Student",
                "grade_level": "Form 4",
                "relationship": "mother"
            }
        ],
        "metadata": {
            "phone": "+263771234567",
            "occupation": "Engineer",
            "emergency_contact": True
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_database():
    """Mock database connection and operations"""
    mock_db = AsyncMock()
    
    # Mock common database operations
    mock_db.fetch.return_value = []
    mock_db.fetchrow.return_value = None
    mock_db.fetchval.return_value = None
    mock_db.execute.return_value = None
    
    return mock_db


@pytest.fixture
def mock_db_manager(mock_database):
    """Mock database manager"""
    mock_manager = AsyncMock()
    mock_manager.get_connection.return_value.__aenter__.return_value = mock_database
    mock_manager.get_connection.return_value.__aexit__.return_value = None
    return mock_manager


@pytest.fixture
def mock_auth_tokens():
    """Mock authentication tokens for testing"""
    return {
        "valid_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyLTEyMyIsInNjaG9vbF9pZCI6InNjaG9vbC0xMjMiLCJpYXQiOjE2MjQ1NjA0ODcsImV4cCI6MTYyNDU2NDA4N30.example",
        "expired_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyLTEyMyIsInNjaG9vbF9pZCI6InNjaG9vbC0xMjMiLCJpYXQiOjE2MjQ1NjA0ODcsImV4cCI6MTYyNDU2MDQ4N30.expired",
        "invalid_token": "invalid.token.format",
        "malformed_token": "not.a.jwt"
    }


@pytest.fixture
def mock_request():
    """Mock FastAPI request object"""
    mock_req = MagicMock()
    mock_req.headers = {}
    mock_req.url.path = "/test"
    mock_req.method = "GET"
    mock_req.state = MagicMock()
    return mock_req


@pytest.fixture
def mock_clerk_user():
    """Mock Clerk user object for frontend tests"""
    return {
        "id": "user_clerk_123",
        "firstName": "John",
        "lastName": "Doe",
        "emailAddresses": [
            {
                "emailAddress": "john.doe@peterhouse.oneclass.ac.zw",
                "verification": {"status": "verified"}
            }
        ],
        "publicMetadata": {
            "school_id": "school-123",
            "school_name": "Peterhouse School",
            "role": "teacher",
            "permissions": ["sis:read", "academic:write"],
            "features": ["student_management", "grade_management"]
        },
        "lastSignInAt": datetime.utcnow().timestamp() * 1000,
        "createdAt": datetime.utcnow().timestamp() * 1000,
        "update": AsyncMock()
    }


@pytest.fixture
def mock_clerk_organization():
    """Mock Clerk organization object for frontend tests"""
    return {
        "id": "org_clerk_123",
        "name": "Peterhouse School",
        "slug": "peterhouse",
        "publicMetadata": {
            "school_id": "school-123",
            "school_code": "PETERHOUSE",
            "subscription_tier": "professional",
            "enabled_modules": ["sis", "academic", "finance"],
            "branding": {
                "primary_color": "#2563eb",
                "logo_url": "https://example.com/logo.png"
            }
        },
        "membersCount": 150,
        "maxAllowedMemberships": 200,
        "createdAt": datetime.utcnow().timestamp() * 1000
    }


@pytest.fixture
def mock_tenant_context(mock_school_data):
    """Mock tenant context for middleware tests"""
    from shared.middleware.tenant_middleware import TenantContext
    
    return TenantContext(
        school_id=mock_school_data["id"],
        school_name=mock_school_data["name"],
        school_code=mock_school_data["code"],
        subscription_tier=mock_school_data["subscription_tier"],
        enabled_modules=mock_school_data["enabled_modules"],
        school_settings=mock_school_data["settings"]
    )


@pytest.fixture
def mock_permission_matrix():
    """Mock permission matrix for RBAC testing"""
    return {
        "super_admin": ["*"],
        "platform_admin": ["platform:*", "schools:*", "users:*"],
        "school_admin": [
            "students:*", "teachers:*", "classes:*", "finance:*",
            "settings:school", "users:school", "reports:*"
        ],
        "teacher": [
            "students:read", "attendance:mark", "grades:read", "grades:write",
            "classes:read", "assignments:*", "parents:communicate"
        ],
        "student": [
            "grades:read_own", "attendance:read_own", "assignments:read_own",
            "profile:read_own", "profile:update_own"
        ],
        "parent": [
            "children:read", "grades:read_children", "attendance:read_children",
            "assignments:read_children", "finance:read_children", "communications:read"
        ],
        "finance_manager": [
            "finance:*", "invoices:*", "payments:*", "students:read", "reports:financial"
        ],
        "registrar": [
            "students:*", "enrollments:*", "classes:read", "grades:read", "attendance:read"
        ]
    }


@pytest.fixture
def mock_feature_matrix():
    """Mock feature availability matrix for testing"""
    return {
        "trial": [
            "student_management", "basic_attendance", "basic_grades", "basic_communication"
        ],
        "basic": [
            "student_management", "attendance_tracking", "grade_management",
            "basic_communication", "disciplinary_system", "basic_reporting"
        ],
        "professional": [
            "student_management", "attendance_tracking", "grade_management",
            "communication", "disciplinary_system", "finance_module",
            "bulk_communication", "advanced_reporting", "parent_portal"
        ],
        "premium": [
            "student_management", "attendance_tracking", "grade_management",
            "communication", "disciplinary_system", "finance_module",
            "bulk_communication", "advanced_reporting", "parent_portal",
            "mobile_app", "api_access", "priority_support"
        ],
        "enterprise": [
            "student_management", "attendance_tracking", "grade_management",
            "communication", "disciplinary_system", "finance_module",
            "bulk_communication", "advanced_reporting", "parent_portal",
            "mobile_app", "api_access", "priority_support", "ai_assistance",
            "ministry_reporting", "custom_integrations", "white_labeling"
        ]
    }


# Custom pytest markers
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "auth: mark test as authentication related"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security related"
    )
    config.addinivalue_line(
        "markers", "rbac: mark test as role-based access control related"
    )
    config.addinivalue_line(
        "markers", "multitenancy: mark test as multi-tenancy related"
    )


# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Cleanup test data after each test"""
    yield
    # Cleanup code would go here in real implementation
    pass