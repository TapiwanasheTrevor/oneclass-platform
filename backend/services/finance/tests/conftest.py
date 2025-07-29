"""
Pytest configuration for Finance module tests
Sets up test database, fixtures, and coverage reporting
"""

import pytest
import asyncio
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from testcontainers.postgres import PostgresContainer

# Test database configuration
TEST_DB_URL = "postgresql+asyncpg://test:test@localhost:5432/finance_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def postgres_container():
    """Start a PostgreSQL container for testing."""
    if os.getenv("USE_TESTCONTAINERS", "true").lower() == "true":
        with PostgresContainer("postgres:14") as postgres:
            yield postgres
    else:
        # Use existing database for CI/CD environments
        yield None


@pytest.fixture(scope="session")
async def db_engine(postgres_container):
    """Create database engine for testing."""
    if postgres_container:
        db_url = postgres_container.get_connection_url().replace("psycopg2", "asyncpg")
    else:
        db_url = TEST_DB_URL
    
    engine = create_async_engine(
        db_url,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=300
    )
    
    # Run database migrations
    async with engine.begin() as conn:
        # Create extensions
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS uuid-ossp"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        
        # Run schema migrations
        with open("database/schemas/00_platform_foundation.sql", "r") as f:
            await conn.execute(text(f.read()))
        
        with open("database/schemas/01_platform_enhanced.sql", "r") as f:
            await conn.execute(text(f.read()))
        
        with open("database/schemas/10_finance.sql", "r") as f:
            await conn.execute(text(f.read()))
    
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def db_session_factory(db_engine):
    """Create session factory for testing."""
    return async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def db_session(db_session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for each test."""
    async with db_session_factory() as session:
        # Start a transaction
        await session.begin()
        
        try:
            yield session
        finally:
            # Rollback transaction after test
            await session.rollback()


@pytest.fixture(autouse=True)
async def cleanup_test_data(db_session: AsyncSession):
    """Clean up test data after each test."""
    yield
    
    # Clean up in reverse order of foreign key dependencies
    tables = [
        "finance.payment_allocations",
        "finance.installments",
        "finance.payment_plans",
        "finance.refunds",
        "finance.payments",
        "finance.invoice_line_items",
        "finance.invoices",
        "finance.student_fee_assignments",
        "finance.fee_items",
        "finance.fee_structures",
        "finance.fee_categories",
        "finance.payment_methods",
        "finance.financial_summaries"
    ]
    
    for table in tables:
        await db_session.execute(text(f"DELETE FROM {table}"))
    
    await db_session.commit()


# Test markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "paynow: mark test as requiring Paynow integration"
    )


# Test collection configuration
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add unit marker to all tests in test_crud.py
        if "test_crud" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to all tests in test_api.py
        if "test_api" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add integration marker to payment integration tests
        if "test_payment_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to tests that take longer
        if any(slow_test in item.nodeid for slow_test in [
            "test_bulk_", "test_large_", "test_performance_"
        ]):
            item.add_marker(pytest.mark.slow)
        
        # Add paynow marker to Paynow integration tests
        if "paynow" in item.nodeid.lower():
            item.add_marker(pytest.mark.paynow)


# Fixtures for commonly used test data
@pytest.fixture
def sample_school_data():
    """Sample school data for testing."""
    return {
        "id": "school-test-123",
        "name": "Test School",
        "type": "secondary",
        "subscription_tier": "premium",
        "currency": "USD",
        "timezone": "Africa/Harare"
    }


@pytest.fixture
def sample_academic_year():
    """Sample academic year for testing."""
    return {
        "id": "ay-test-2025",
        "name": "2025 Academic Year",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "is_current": True
    }


@pytest.fixture
def sample_student_data():
    """Sample student data for testing."""
    return {
        "id": "student-test-123",
        "student_number": "STU-TEST-001",
        "first_name": "Test",
        "last_name": "Student",
        "grade_level": 1,
        "class_id": "class-test-1a",
        "is_active": True
    }


# Performance testing fixtures
@pytest.fixture
def performance_test_data():
    """Generate performance test data."""
    return {
        "students_count": 1000,
        "invoices_count": 5000,
        "payments_count": 2500,
        "bulk_operations": 100
    }


# Mock external services
@pytest.fixture
def mock_paynow_service():
    """Mock Paynow service for testing."""
    class MockPaynowService:
        def __init__(self):
            self.payments = {}
            self.should_fail = False
        
        async def initiate_payment(self, request):
            if self.should_fail:
                return {
                    "status": "error",
                    "error": "Mock payment failure"
                }
            
            payment_id = f"mock-{len(self.payments) + 1}"
            self.payments[payment_id] = {
                "status": "pending",
                "amount": request.amount,
                "reference": f"PR-{payment_id}"
            }
            
            return {
                "status": "ok",
                "payment_id": payment_id,
                "redirect_url": f"https://mock.paynow.co.zw/pay/{payment_id}",
                "poll_url": f"https://mock.paynow.co.zw/poll/{payment_id}"
            }
        
        async def check_status(self, payment_id):
            payment = self.payments.get(payment_id)
            if not payment:
                return {"status": "Not found"}
            
            return {
                "status": "Paid" if payment["status"] == "completed" else "Pending",
                "amount": payment["amount"],
                "reference": payment["reference"]
            }
        
        def complete_payment(self, payment_id):
            """Helper method to simulate payment completion."""
            if payment_id in self.payments:
                self.payments[payment_id]["status"] = "completed"
    
    return MockPaynowService()


@pytest.fixture
def mock_email_service():
    """Mock email service for testing."""
    class MockEmailService:
        def __init__(self):
            self.sent_emails = []
        
        async def send_invoice(self, invoice_id, recipient_email, student_name):
            self.sent_emails.append({
                "type": "invoice",
                "invoice_id": invoice_id,
                "recipient": recipient_email,
                "student_name": student_name,
                "sent_at": "2025-07-17T10:00:00Z"
            })
            return {"success": True, "message_id": f"msg-{len(self.sent_emails)}"}
        
        async def send_payment_receipt(self, payment_id, recipient_email, amount):
            self.sent_emails.append({
                "type": "receipt",
                "payment_id": payment_id,
                "recipient": recipient_email,
                "amount": amount,
                "sent_at": "2025-07-17T10:00:00Z"
            })
            return {"success": True, "message_id": f"msg-{len(self.sent_emails)}"}
    
    return MockEmailService()


@pytest.fixture
def mock_sms_service():
    """Mock SMS service for testing."""
    class MockSMSService:
        def __init__(self):
            self.sent_messages = []
        
        async def send_payment_reminder(self, phone_number, student_name, amount):
            self.sent_messages.append({
                "type": "reminder",
                "phone": phone_number,
                "student_name": student_name,
                "amount": amount,
                "sent_at": "2025-07-17T10:00:00Z"
            })
            return {"success": True, "message_id": f"sms-{len(self.sent_messages)}"}
        
        async def send_payment_confirmation(self, phone_number, amount, reference):
            self.sent_messages.append({
                "type": "confirmation",
                "phone": phone_number,
                "amount": amount,
                "reference": reference,
                "sent_at": "2025-07-17T10:00:00Z"
            })
            return {"success": True, "message_id": f"sms-{len(self.sent_messages)}"}
    
    return MockSMSService()


# Test report configuration
@pytest.fixture(scope="session", autouse=True)
def configure_test_reporting():
    """Configure test reporting and coverage."""
    # Set up coverage reporting
    os.environ["COVERAGE_PROCESS_START"] = "1"
    
    # Configure test output
    os.environ["PYTEST_CURRENT_TEST"] = "1"
    
    yield
    
    # Clean up after all tests
    if os.path.exists(".coverage"):
        print("Coverage data collected")


# Database utilities for tests
@pytest.fixture
def db_utils():
    """Database utilities for testing."""
    class DatabaseUtils:
        @staticmethod
        async def count_records(session: AsyncSession, table_name: str) -> int:
            """Count records in a table."""
            result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar()
        
        @staticmethod
        async def table_exists(session: AsyncSession, table_name: str) -> bool:
            """Check if table exists."""
            result = await session.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables "
                "WHERE table_name = :table_name)"
            ), {"table_name": table_name})
            return result.scalar()
        
        @staticmethod
        async def get_table_columns(session: AsyncSession, table_name: str) -> list:
            """Get table columns."""
            result = await session.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = :table_name ORDER BY ordinal_position"
            ), {"table_name": table_name})
            return [row[0] for row in result.fetchall()]
    
    return DatabaseUtils()


# Test data generators
@pytest.fixture
def data_generators():
    """Data generators for testing."""
    import random
    from datetime import datetime, timedelta
    from decimal import Decimal
    
    class DataGenerators:
        @staticmethod
        def generate_student_data(count: int = 100):
            """Generate student test data."""
            students = []
            for i in range(count):
                students.append({
                    "student_number": f"STU-{i:04d}",
                    "first_name": f"Student{i}",
                    "last_name": f"Surname{i}",
                    "grade_level": random.randint(1, 13),
                    "is_active": True
                })
            return students
        
        @staticmethod
        def generate_invoice_data(student_count: int = 100, invoices_per_student: int = 3):
            """Generate invoice test data."""
            invoices = []
            for student_idx in range(student_count):
                for invoice_idx in range(invoices_per_student):
                    invoices.append({
                        "student_id": f"student-{student_idx}",
                        "due_date": datetime.now() + timedelta(days=random.randint(1, 90)),
                        "total_amount": Decimal(random.randint(100, 1000)),
                        "currency": "USD",
                        "status": random.choice(["pending", "sent", "paid", "overdue"])
                    })
            return invoices
        
        @staticmethod
        def generate_payment_data(count: int = 500):
            """Generate payment test data."""
            payments = []
            for i in range(count):
                payments.append({
                    "amount": Decimal(random.randint(50, 1000)),
                    "currency": "USD",
                    "payment_date": datetime.now() - timedelta(days=random.randint(0, 30)),
                    "status": random.choice(["pending", "completed", "failed"]),
                    "payer_phone": f"+26377{random.randint(1000000, 9999999)}"
                })
            return payments
    
    return DataGenerators()