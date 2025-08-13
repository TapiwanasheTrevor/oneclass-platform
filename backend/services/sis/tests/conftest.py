# =====================================================
# SIS Module - Test Configuration
# File: backend/services/sis/tests/conftest.py
# =====================================================

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from uuid import uuid4
from datetime import date, datetime

# Configure pytest for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Common test fixtures
@pytest.fixture
def sample_school_id():
    """Provide a consistent school ID for tests"""
    return uuid4()

@pytest.fixture
def sample_user_id():
    """Provide a consistent user ID for tests"""
    return uuid4()

@pytest.fixture
def sample_student_id():
    """Provide a consistent student ID for tests"""
    return uuid4()

@pytest.fixture
def mock_async_db_session():
    """Create a mock async database session for testing"""
    session = Mock()
    session.add = Mock()
    session.delete = Mock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.close = AsyncMock()
    return session

@pytest.fixture
def sample_zimbabwe_address():
    """Provide sample Zimbabwe address for testing"""
    return {
        "street": "123 Borrowdale Road",
        "suburb": "Borrowdale",
        "city": "Harare",
        "province": "Harare",
        "postal_code": "00263"
    }

@pytest.fixture
def sample_emergency_contacts():
    """Provide sample emergency contacts for testing"""
    return [
        {
            "name": "Mary Mukamuri",
            "relationship": "Mother",
            "phone": "+263771234567",
            "email": "mary.mukamuri@example.com",
            "is_primary": True,
            "can_pickup": True
        },
        {
            "name": "James Mukamuri",
            "relationship": "Father", 
            "phone": "+263772345678",
            "email": "james.mukamuri@example.com",
            "is_primary": False,
            "can_pickup": True
        }
    ]

# Test markers
def pytest_configure(config):
    """Configure custom test markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "bulk: mark test as bulk operation test"
    )
    config.addinivalue_line(
        "markers", "family: mark test as family management test"
    )
    config.addinivalue_line(
        "markers", "validation: mark test as validation test"
    )

# Skip integration tests by default
def pytest_collection_modifyitems(config, items):
    """Automatically skip integration tests unless explicitly requested"""
    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(reason="need --run-integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
    
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)

def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run integration tests"
    )
    parser.addoption(
        "--run-slow",
        action="store_true", 
        default=False,
        help="run slow tests"
    )
    parser.addoption(
        "--database-url",
        action="store",
        default="sqlite:///:memory:",
        help="database URL for integration tests"
    )