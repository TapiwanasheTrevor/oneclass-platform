"""
Test configuration for Migration Services
Provides fixtures and setup for migration services tests
"""
import pytest
import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Import models and services
from shared.models.migration_services import (
    CarePackageCreate, CarePackageResponse,
    CarePackageOrderCreate, CarePackageOrderResponse,
    OrderStatus, PaymentStatus, PaymentOption, TaskStatus
)
from services.migration_services.service import MigrationServicesService
from services.migration_services.routes import router
from shared.models.platform import 
from shared.models.platform_user import PlatformUserDB as User, School


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_session():
    """Create a mock database session for testing"""
    mock_session = Mock(spec=Session)
    mock_session.query = Mock()
    mock_session.add = Mock()
    mock_session.commit = Mock()
    mock_session.rollback = Mock()
    mock_session.refresh = Mock()
    mock_session.close = Mock()
    mock_session.execute = Mock()
    return mock_session


@pytest.fixture
def migration_service(mock_db_session):
    """Create MigrationServicesService instance with mocked database"""
    return MigrationServicesService(mock_db_session)


@pytest.fixture
def test_client():
    """Create FastAPI test client"""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def sample_school():
    """Create a sample school for testing"""
    return {
        "id": uuid4(),
        "name": "Test School",
        "code": "TEST",
        "subdomain": "testschool",
        "subscription_tier": "professional",
        "enabled_modules": ["sis", "finance", "migration_services"],
        "settings": {
            "timezone": "Africa/Harare",
            "academic_year": "2024-2025"
        }
    }


@pytest.fixture
def sample_user(sample_school):
    """Create a sample user for testing"""
    return Mock(
        id=uuid4(),
        email="admin@testschool.oneclass.ac.zw",
        first_name="Test",
        last_name="Admin",
        role="school_admin",
        school_id=sample_school["id"],
        permissions=["migration_services.create", "migration_services.read", "migration_services.update"]
    )


@pytest.fixture
def super_admin_user():
    """Create a super admin user for testing"""
    return Mock(
        id=uuid4(),
        email="admin@oneclass.ac.zw",
        first_name="Super",
        last_name="Admin",
        role="platform_admin",
        school_id=None,
        permissions=["*"]
    )


@pytest.fixture
def sample_care_packages():
    """Create sample care packages for testing"""
    return [
        CarePackageResponse(
            id=uuid4(),
            name="Foundation Package",
            price_usd=Decimal("2800.00"),
            price_zwl=Decimal("4480000.00"),
            max_students=200,
            max_historical_years=1,
            features={"student_migration": True, "training_hours": 4},
            inclusions=[
                "Up to 200 current students",
                "Basic parent/guardian contacts",
                "Current year class assignments",
                "School branding setup"
            ],
            exclusions=[
                "Historical data beyond current year",
                "Financial record migration",
                "Attendance history"
            ],
            estimated_duration_days=14,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        CarePackageResponse(
            id=uuid4(),
            name="Growth Package",
            price_usd=Decimal("6500.00"),
            price_zwl=Decimal("10400000.00"),
            max_students=800,
            max_historical_years=3,
            features={"student_migration": True, "financial_migration": True, "training_hours": 12},
            inclusions=[
                "Up to 800 students (3-year history)",
                "Complete academic records",
                "Financial data migration",
                "Payment gateway setup"
            ],
            exclusions=[
                "Government system integration",
                "Multi-campus setup"
            ],
            estimated_duration_days=21,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        CarePackageResponse(
            id=uuid4(),
            name="Enterprise Package",
            price_usd=Decimal("15000.00"),
            price_zwl=Decimal("24000000.00"),
            max_students=None,
            max_historical_years=5,
            features={"unlimited_students": True, "government_integration": True, "training_hours": 24},
            inclusions=[
                "Unlimited students (5+ year history)",
                "Government system integration",
                "Multi-campus support",
                "Custom API development"
            ],
            exclusions=[],
            estimated_duration_days=30,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]


@pytest.fixture
def sample_care_package_order(sample_school, sample_care_packages):
    """Create a sample care package order for testing"""
    return CarePackageOrderResponse(
        id=uuid4(),
        order_number="CP-2025-001",
        school_id=sample_school["id"],
        care_package_id=sample_care_packages[1].id,  # Growth Package
        order_date=date.today(),
        status=OrderStatus.PENDING,
        package_price=Decimal("6500.00"),
        additional_costs=Decimal("1500.00"),  # With add-ons
        total_price=Decimal("8000.00"),
        payment_status=PaymentStatus.PENDING,
        payment_option=PaymentOption.SPLIT,
        currency="USD",
        progress_percentage=0,
        estimated_hours=160,
        actual_hours=0,
        student_count=450,
        current_system_type="excel",
        data_sources_description="Student records in Excel files",
        special_requirements="Weekend migration preferred",
        urgent_migration=True,
        onsite_training=False,
        weekend_work=True,
        primary_contact_name="John Doe",
        primary_contact_email="john@testschool.oneclass.ac.zw",
        primary_contact_phone="+263 77 123 4567",
        requested_start_date=date.today() + timedelta(days=30),
        estimated_completion_date=date.today() + timedelta(days=51),
        assigned_migration_manager=None,
        assigned_technical_lead=None,
        assigned_data_specialist=None,
        assigned_training_specialist=None,
        initial_assessment_notes=None,
        completion_notes=None,
        customer_feedback=None,
        internal_notes=None,
        care_package=sample_care_packages[1],
        school_name=sample_school["name"],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def sample_migration_tasks(sample_care_package_order):
    """Create sample migration tasks for testing"""
    return [
        {
            "id": uuid4(),
            "care_package_order_id": sample_care_package_order.id,
            "phase": "discovery",
            "task_name": "Initial Assessment",
            "description": "Assess current system and requirements",
            "status": TaskStatus.PENDING,
            "priority": "high",
            "estimated_hours": Decimal("8.0"),
            "actual_hours": Decimal("0.0"),
            "due_date": date.today() + timedelta(days=3),
            "assigned_to": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "id": uuid4(),
            "care_package_order_id": sample_care_package_order.id,
            "phase": "data_extraction",
            "task_name": "Data Collection",
            "description": "Collect all source data from school",
            "status": TaskStatus.PENDING,
            "priority": "high",
            "estimated_hours": Decimal("16.0"),
            "actual_hours": Decimal("0.0"),
            "due_date": date.today() + timedelta(days=7),
            "assigned_to": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    ]


@pytest.fixture
def mock_tenant_context(sample_school):
    """Mock tenant context for testing"""
    return {
        "school_id": sample_school["id"],
        "school_name": sample_school["name"],
        "school_code": sample_school["code"],
        "subscription_tier": sample_school["subscription_tier"],
        "enabled_modules": sample_school["enabled_modules"],
        "school_settings": sample_school["settings"]
    }


@pytest.fixture
def mock_authentication(sample_user):
    """Mock authentication for testing"""
    with patch('services.migration_services.routes.get_current_active_user') as mock_get_user:
        mock_get_user.return_value = sample_user
        yield mock_get_user


@pytest.fixture
def mock_super_admin_authentication(super_admin_user):
    """Mock super admin authentication for testing"""
    with patch('services.migration_services.routes.get_current_active_user') as mock_get_user:
        mock_get_user.return_value = super_admin_user
        yield mock_get_user


@pytest.fixture
def mock_tenant_middleware(mock_tenant_context):
    """Mock tenant middleware for testing"""
    with patch('shared.middleware.tenant_middleware.get_tenant_context') as mock_get_context:
        mock_get_context.return_value = mock_tenant_context
        yield mock_get_context


@pytest.fixture
def mock_database_operations(mock_db_session):
    """Mock common database operations"""
    # Mock successful database operations
    mock_db_session.commit.return_value = None
    mock_db_session.add.return_value = None
    mock_db_session.refresh.return_value = None
    
    # Mock query operations
    mock_query = Mock()
    mock_db_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.join.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.options.return_value = mock_query
    
    return mock_db_session


@pytest.fixture
def mock_rls_context():
    """Mock Row Level Security context for testing"""
    with patch('services.migration_services.service.text') as mock_text:
        mock_text.return_value = "SELECT set_config('app.current_school_id', 'school-id', true)"
        yield mock_text


@pytest.fixture
def sample_dashboard_data():
    """Create sample dashboard data for testing"""
    from shared.models.migration_services import MigrationServicesDashboard
    
    return MigrationServicesDashboard(
        active_projects=15,
        monthly_revenue=Decimal("85000.00"),
        team_utilization=Decimal("87.5"),
        success_rate=Decimal("96.2"),
        projects_trend="+12% this month",
        revenue_trend="+23% vs last month",
        utilization_trend="Optimal capacity",
        success_rate_trend="Above target",
        recent_orders=[],
        team_performance=[]
    )


@pytest.fixture
def mock_order_generation():
    """Mock order number generation for testing"""
    with patch('services.migration_services.service.MigrationServicesService._generate_order_number') as mock_gen:
        mock_gen.return_value = "CP-2025-001"
        yield mock_gen


@pytest.fixture
def mock_milestone_creation():
    """Mock milestone creation for testing"""
    with patch('services.migration_services.service.MigrationServicesService._create_default_milestones') as mock_milestones:
        mock_milestones.return_value = None
        yield mock_milestones


@pytest.fixture
def mock_communication_logging():
    """Mock communication logging for testing"""
    with patch('services.migration_services.service.MigrationServicesService._log_communication') as mock_log:
        mock_log.return_value = None
        yield mock_log


@pytest.fixture
def mock_payment_processing():
    """Mock payment processing for testing"""
    return {
        "payment_gateway": "paynow",
        "payment_methods": ["ecocash", "onemoney", "bank_transfer"],
        "currency_support": ["USD", "ZWL"],
        "transaction_fees": {"ecocash": 0.035, "onemoney": 0.030, "bank_transfer": 0.025}
    }


@pytest.fixture
def mock_sms_service():
    """Mock SMS service for testing"""
    return {
        "provider": "telone",
        "api_url": "https://sms.telone.co.zw/api/v1",
        "sender_id": "ONECLASS",
        "rate_limit": 1000,
        "delivery_reports": True
    }


@pytest.fixture
def mock_email_service():
    """Mock email service for testing"""
    return {
        "provider": "google_workspace",
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "use_tls": True,
        "template_engine": "jinja2"
    }


@pytest.fixture
def zimbabwe_test_data():
    """Create Zimbabwe-specific test data"""
    return {
        "phone_numbers": [
            "+263 77 123 4567",  # Valid mobile
            "+263 71 987 6543",  # Valid mobile
            "+263 4 123 456",    # Valid landline
        ],
        "invalid_phone_numbers": [
            "+1 555 123 4567",   # US number
            "+44 20 1234 5678",  # UK number
            "077 123 4567",      # Missing country code
        ],
        "school_types": [
            "primary",
            "secondary", 
            "combined",
            "technical",
            "special_needs"
        ],
        "grade_levels": list(range(1, 14)),  # Grade 1-13
        "terms": [
            {"number": 1, "start": "January", "end": "April"},
            {"number": 2, "start": "May", "end": "August"},
            {"number": 3, "start": "September", "end": "December"}
        ],
        "currencies": ["USD", "ZWL"],
        "exchange_rate": 1600  # USD to ZWL
    }


@pytest.fixture
def performance_test_data():
    """Create large dataset for performance testing"""
    return {
        "large_order_count": 1000,
        "concurrent_users": 50,
        "api_response_time_limit": 200,  # milliseconds
        "database_query_time_limit": 100,  # milliseconds
        "memory_usage_limit": 100,  # MB
        "cpu_usage_limit": 80  # percent
    }


@pytest.fixture
def security_test_data():
    """Create security test data"""
    return {
        "sql_injection_attempts": [
            "'; DROP TABLE care_packages; --",
            "test'; DELETE FROM users; --",
            "union select * from users"
        ],
        "xss_attempts": [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ],
        "malicious_subdomains": [
            "'; DROP TABLE schools; --",
            "<script>alert('xss')</script>",
            "../../../etc/passwd"
        ],
        "invalid_uuids": [
            "not-a-uuid",
            "123-456-789",
            "malicious-id"
        ]
    }


@pytest.fixture
def integration_test_config():
    """Configuration for integration tests"""
    return {
        "test_database_url": "postgresql://test:test@localhost:5432/test_oneclass",
        "test_redis_url": "redis://localhost:6379/1",
        "test_file_storage": {
            "provider": "local",
            "path": "/tmp/test_files"
        },
        "test_email_backend": "console",
        "test_sms_backend": "console",
        "enable_debug_logging": True,
        "skip_external_services": True
    }


# Helper functions for tests
def create_test_order_data(school_id: str, care_package_id: str, **kwargs):
    """Create test order data with defaults"""
    default_data = {
        "school_id": school_id,
        "care_package_id": care_package_id,
        "student_count": 450,
        "current_system_type": "excel",
        "data_sources_description": "Student records in Excel files",
        "special_requirements": "Weekend migration preferred",
        "urgent_migration": False,
        "onsite_training": False,
        "weekend_work": False,
        "primary_contact_name": "John Doe",
        "primary_contact_email": "john@school.edu",
        "primary_contact_phone": "+263 77 123 4567",
        "payment_option": PaymentOption.SPLIT,
        "requested_start_date": date.today() + timedelta(days=30)
    }
    
    default_data.update(kwargs)
    return CarePackageOrderCreate(**default_data)


def create_test_care_package(**kwargs):
    """Create test care package with defaults"""
    default_data = {
        "name": "Test Package",
        "price_usd": Decimal("5000.00"),
        "price_zwl": Decimal("8000000.00"),
        "max_students": 500,
        "max_historical_years": 2,
        "features": {"test_feature": True},
        "inclusions": ["Test inclusion"],
        "exclusions": ["Test exclusion"],
        "estimated_duration_days": 20,
        "is_active": True
    }
    
    default_data.update(kwargs)
    return CarePackageCreate(**default_data)


def assert_uuid_format(uuid_string):
    """Assert that a string is a valid UUID format"""
    try:
        uuid4(uuid_string)
        return True
    except (ValueError, TypeError):
        return False


def assert_zimbabwe_phone_format(phone_number):
    """Assert that a phone number is in Zimbabwe format"""
    import re
    pattern = r'^\+263[1-9]\d{8}$'
    return bool(re.match(pattern, phone_number))


def assert_order_number_format(order_number):
    """Assert that an order number follows the correct format"""
    import re
    pattern = r'^CP-\d{4}-\d{3}$'
    return bool(re.match(pattern, order_number))


# Mark tests that require specific conditions
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.performance = pytest.mark.performance
pytest.mark.security = pytest.mark.security
pytest.mark.slow = pytest.mark.slow
pytest.mark.zimbabwe = pytest.mark.zimbabwe