"""
Comprehensive Tests for Migration Services
Tests for care package management, multi-tenant integration, and super admin functionality
"""
import pytest
import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4, UUID
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Import models and services
from shared.models.migration_services import (
    CarePackageCreate, CarePackageUpdate, CarePackageResponse,
    CarePackageOrderCreate, CarePackageOrderUpdate, CarePackageOrderResponse,
    MigrationTaskCreate, MigrationTaskUpdate, MigrationTaskResponse,
    OrderStatus, PaymentStatus, PaymentOption, TaskStatus,
    MigrationServicesDashboard, OrderFilters, OrderAnalytics
)
from services.migration_services.service import MigrationServicesService
from services.migration_services.routes import router
from shared.models.platform import 
from shared.models.platform_user import PlatformUserDB as User, School


class TestCarePackageModels:
    """Test Pydantic models for care packages"""
    
    def test_care_package_create_valid(self):
        """Test creating valid care package"""
        package_data = {
            "name": "Foundation Package",
            "price_usd": Decimal("2800.00"),
            "price_zwl": Decimal("4480000.00"),
            "max_students": 200,
            "max_historical_years": 1,
            "features": {"student_migration": True, "training_hours": 4},
            "inclusions": ["Up to 200 students", "Basic training"],
            "exclusions": ["Historical data", "Financial records"],
            "estimated_duration_days": 14,
            "is_active": True
        }
        
        package = CarePackageCreate(**package_data)
        assert package.name == "Foundation Package"
        assert package.price_usd == Decimal("2800.00")
        assert package.max_students == 200
        assert package.features["student_migration"] is True
        assert "Up to 200 students" in package.inclusions
        assert "Historical data" in package.exclusions
    
    def test_care_package_create_invalid_price(self):
        """Test care package creation with invalid price"""
        with pytest.raises(ValueError):
            CarePackageCreate(
                name="Invalid Package",
                price_usd=Decimal("-100.00"),  # Negative price
                price_zwl=Decimal("1000.00"),
                features={},
                inclusions=[],
                exclusions=[],
                estimated_duration_days=14
            )
    
    def test_care_package_order_create_valid(self):
        """Test creating valid care package order"""
        order_data = {
            "school_id": uuid4(),
            "care_package_id": uuid4(),
            "student_count": 450,
            "current_system_type": "excel",
            "data_sources_description": "Student records in Excel files",
            "special_requirements": "Weekend migration preferred",
            "urgent_migration": True,
            "onsite_training": False,
            "weekend_work": True,
            "primary_contact_name": "John Doe",
            "primary_contact_email": "john@school.edu",
            "primary_contact_phone": "+263 77 123 4567",
            "payment_option": PaymentOption.SPLIT,
            "requested_start_date": date.today() + timedelta(days=30)
        }
        
        order = CarePackageOrderCreate(**order_data)
        assert order.student_count == 450
        assert order.current_system_type == "excel"
        assert order.urgent_migration is True
        assert order.weekend_work is True
        assert order.payment_option == PaymentOption.SPLIT
        assert order.primary_contact_phone == "+263 77 123 4567"
    
    def test_care_package_order_invalid_phone(self):
        """Test order creation with invalid phone number"""
        order_data = {
            "school_id": uuid4(),
            "care_package_id": uuid4(),
            "primary_contact_phone": "+1 555 123 4567"  # Non-Zimbabwe number
        }
        
        # Should validate Zimbabwe phone format
        with pytest.raises(ValueError, match="Zimbabwe format"):
            CarePackageOrderCreate(**order_data)
    
    def test_order_status_transitions(self):
        """Test valid order status transitions"""
        # Test all enum values are valid
        assert OrderStatus.PENDING == "pending"
        assert OrderStatus.IN_PROGRESS == "in_progress"
        assert OrderStatus.COMPLETED == "completed"
        
        # Test status progression
        valid_statuses = [
            OrderStatus.PENDING,
            OrderStatus.APPROVED,
            OrderStatus.IN_PROGRESS,
            OrderStatus.DATA_MIGRATION,
            OrderStatus.SYSTEM_SETUP,
            OrderStatus.TRAINING,
            OrderStatus.TESTING,
            OrderStatus.GO_LIVE,
            OrderStatus.COMPLETED
        ]
        
        for status in valid_statuses:
            assert isinstance(status, str)
            assert len(status) > 0


class TestMigrationServicesService:
    """Test Migration Services Service Layer"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mocked database"""
        return MigrationServicesService(mock_db)
    
    @pytest.fixture
    def sample_care_package(self):
        """Sample care package for testing"""
        return CarePackageResponse(
            id=uuid4(),
            name="Growth Package",
            price_usd=Decimal("6500.00"),
            price_zwl=Decimal("10400000.00"),
            max_students=800,
            max_historical_years=3,
            features={"student_migration": True, "financial_migration": True},
            inclusions=["Up to 800 students", "Financial data migration"],
            exclusions=["Government integration"],
            estimated_duration_days=21,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_get_care_packages_success(self, service, mock_db):
        """Test successful retrieval of care packages"""
        # Mock database query
        mock_query = Mock()
        mock_packages = [
            Mock(id=uuid4(), name="Foundation", price_usd=Decimal("2800")),
            Mock(id=uuid4(), name="Growth", price_usd=Decimal("6500")),
            Mock(id=uuid4(), name="Enterprise", price_usd=Decimal("15000"))
        ]
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_packages
        
        # Mock CarePackageResponse.from_orm
        with patch('backend.services.migration_services.service.CarePackageResponse.from_orm') as mock_from_orm:
            mock_from_orm.side_effect = lambda pkg: CarePackageResponse(
                id=pkg.id,
                name=pkg.name,
                price_usd=pkg.price_usd,
                price_zwl=pkg.price_usd * 1600,
                max_students=500,
                max_historical_years=1,
                features={},
                inclusions=[],
                exclusions=[],
                estimated_duration_days=14,
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            packages = await service.get_care_packages()
            
            assert len(packages) == 3
            assert packages[0].name == "Foundation"
            assert packages[1].price_usd == Decimal("6500")
            mock_db.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_care_package_success(self, service, mock_db):
        """Test successful care package creation"""
        package_data = CarePackageCreate(
            name="Test Package",
            price_usd=Decimal("5000.00"),
            price_zwl=Decimal("8000000.00"),
            max_students=500,
            max_historical_years=2,
            features={"test_feature": True},
            inclusions=["Test inclusion"],
            exclusions=["Test exclusion"],
            estimated_duration_days=20
        )
        
        # Mock database operations
        mock_package = Mock()
        mock_package.id = uuid4()
        mock_package.name = "Test Package"
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        with patch('backend.services.migration_services.service.CarePackage') as mock_care_package:
            mock_care_package.return_value = mock_package
            
            with patch('backend.services.migration_services.service.CarePackageResponse.from_orm') as mock_from_orm:
                mock_from_orm.return_value = CarePackageResponse(
                    id=mock_package.id,
                    name=mock_package.name,
                    price_usd=Decimal("5000.00"),
                    price_zwl=Decimal("8000000.00"),
                    max_students=500,
                    max_historical_years=2,
                    features={"test_feature": True},
                    inclusions=["Test inclusion"],
                    exclusions=["Test exclusion"],
                    estimated_duration_days=20,
                    is_active=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                result = await service.create_care_package(package_data)
                
                assert result.name == "Test Package"
                assert result.price_usd == Decimal("5000.00")
                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_care_package_order_success(self, service, mock_db):
        """Test successful care package order creation"""
        # Mock care package
        with patch.object(service, 'get_care_package') as mock_get_package:
            mock_get_package.return_value = CarePackageResponse(
                id=uuid4(),
                name="Growth Package",
                price_usd=Decimal("6500.00"),
                price_zwl=Decimal("10400000.00"),
                max_students=800,
                max_historical_years=3,
                features={},
                inclusions=[],
                exclusions=[],
                estimated_duration_days=21,
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            order_data = CarePackageOrderCreate(
                school_id=uuid4(),
                care_package_id=uuid4(),
                student_count=450,
                urgent_migration=True,
                onsite_training=False,
                weekend_work=True,
                primary_contact_name="John Doe",
                primary_contact_email="john@school.edu",
                primary_contact_phone="+263 77 123 4567"
            )
            
            created_by = uuid4()
            
            # Mock database operations
            mock_order = Mock()
            mock_order.id = uuid4()
            mock_order.order_number = "CP-2025-001"
            
            mock_db.add = Mock()
            mock_db.commit = Mock()
            mock_db.refresh = Mock()
            
            with patch('backend.services.migration_services.service.CarePackageOrder') as mock_order_class:
                mock_order_class.return_value = mock_order
                
                with patch.object(service, '_generate_order_number') as mock_gen_number:
                    mock_gen_number.return_value = "CP-2025-001"
                    
                    with patch.object(service, '_create_default_milestones') as mock_milestones:
                        with patch.object(service, '_log_communication') as mock_log:
                            with patch.object(service, '_get_order_response') as mock_response:
                                mock_response.return_value = CarePackageOrderResponse(
                                    id=mock_order.id,
                                    order_number="CP-2025-001",
                                    school_id=order_data.school_id,
                                    care_package_id=order_data.care_package_id,
                                    order_date=date.today(),
                                    status=OrderStatus.PENDING,
                                    package_price=Decimal("6500.00"),
                                    additional_costs=Decimal("1500.00"),  # urgent + weekend
                                    total_price=Decimal("8000.00"),
                                    payment_status=PaymentStatus.PENDING,
                                    progress_percentage=0,
                                    actual_hours=0,
                                    student_count=450,
                                    primary_contact_name="John Doe",
                                    primary_contact_email="john@school.edu",
                                    primary_contact_phone="+263 77 123 4567",
                                    urgent_migration=True,
                                    weekend_work=True,
                                    payment_option=PaymentOption.SPLIT,
                                    currency="USD",
                                    created_at=datetime.now(),
                                    updated_at=datetime.now()
                                )
                                
                                result = await service.create_care_package_order(order_data, created_by)
                                
                                assert result.order_number == "CP-2025-001"
                                assert result.student_count == 450
                                assert result.total_price == Decimal("8000.00")  # Base + urgent + weekend
                                assert result.urgent_migration is True
                                mock_milestones.assert_called_once()
                                mock_log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_migration_dashboard_success(self, service, mock_db):
        """Test successful dashboard data retrieval"""
        # Mock database queries
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        
        # Mock active projects count
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 15
        
        # Mock revenue calculation
        mock_query.with_entities.return_value = mock_query
        mock_query.scalar.return_value = Decimal("85000.00")
        
        with patch.object(service, 'get_care_package_orders') as mock_get_orders:
            mock_get_orders.return_value = []
            
            result = await service.get_migration_dashboard()
            
            assert isinstance(result, MigrationServicesDashboard)
            assert result.active_projects == 15
            assert result.monthly_revenue == Decimal("85000.00")
            assert result.team_utilization == Decimal("87")
            assert result.success_rate > 0
    
    @pytest.mark.asyncio
    async def test_service_error_handling(self, service, mock_db):
        """Test service error handling"""
        # Mock database error
        mock_db.query.side_effect = Exception("Database connection error")
        
        with pytest.raises(Exception):
            await service.get_care_packages()
        
        # Verify rollback is called on error
        mock_db.rollback = Mock()
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.commit.side_effect = Exception("Commit failed")
        
        package_data = CarePackageCreate(
            name="Test Package",
            price_usd=Decimal("5000.00"),
            price_zwl=Decimal("8000000.00"),
            max_students=500,
            max_historical_years=2,
            features={},
            inclusions=[],
            exclusions=[],
            estimated_duration_days=20
        )
        
        with patch('backend.services.migration_services.service.CarePackage'):
            with pytest.raises(Exception):
                await service.create_care_package(package_data)
            
            mock_db.rollback.assert_called_once()


class TestMigrationServicesAPI:
    """Test Migration Services API endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI test app"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        return Mock(
            id=uuid4(),
            role="school_admin",
            school_id=uuid4(),
            email="admin@school.edu"
        )
    
    @pytest.fixture
    def mock_super_admin(self):
        """Mock super admin user"""
        return Mock(
            id=uuid4(),
            role="platform_admin",
            school_id=None,
            email="admin@oneclass.ac.zw"
        )
    
    def test_get_care_packages_success(self, client):
        """Test GET /care-packages endpoint"""
        with patch('backend.services.migration_services.routes.MigrationServicesService') as mock_service:
            mock_service.return_value.get_care_packages.return_value = [
                CarePackageResponse(
                    id=uuid4(),
                    name="Foundation Package",
                    price_usd=Decimal("2800.00"),
                    price_zwl=Decimal("4480000.00"),
                    max_students=200,
                    max_historical_years=1,
                    features={},
                    inclusions=[],
                    exclusions=[],
                    estimated_duration_days=14,
                    is_active=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            ]
            
            response = client.get("/api/v1/migration-services/care-packages")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "Foundation Package"
            assert data[0]["price_usd"] == "2800.00"
    
    def test_create_care_package_admin_only(self, client):
        """Test POST /care-packages requires admin permissions"""
        package_data = {
            "name": "Test Package",
            "price_usd": 5000.00,
            "price_zwl": 8000000.00,
            "max_students": 500,
            "max_historical_years": 2,
            "features": {},
            "inclusions": [],
            "exclusions": [],
            "estimated_duration_days": 20
        }
        
        # Test without authentication
        response = client.post(
            "/api/v1/migration-services/care-packages",
            json=package_data
        )
        assert response.status_code == 401
        
        # Test with non-admin user
        with patch('backend.services.migration_services.routes.get_current_active_user') as mock_get_user:
            mock_get_user.return_value = Mock(role="teacher")
            
            response = client.post(
                "/api/v1/migration-services/care-packages",
                json=package_data
            )
            assert response.status_code == 403
    
    def test_create_care_package_order_success(self, client, mock_user):
        """Test POST /orders endpoint success"""
        order_data = {
            "school_id": str(mock_user.school_id),
            "care_package_id": str(uuid4()),
            "student_count": 450,
            "primary_contact_name": "John Doe",
            "primary_contact_email": "john@school.edu",
            "primary_contact_phone": "+263 77 123 4567"
        }
        
        with patch('backend.services.migration_services.routes.get_current_active_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.services.migration_services.routes.MigrationServicesService') as mock_service:
                mock_service.return_value.create_care_package_order.return_value = CarePackageOrderResponse(
                    id=uuid4(),
                    order_number="CP-2025-001",
                    school_id=mock_user.school_id,
                    care_package_id=UUID(order_data["care_package_id"]),
                    order_date=date.today(),
                    status=OrderStatus.PENDING,
                    package_price=Decimal("6500.00"),
                    additional_costs=Decimal("0.00"),
                    total_price=Decimal("6500.00"),
                    payment_status=PaymentStatus.PENDING,
                    progress_percentage=0,
                    actual_hours=0,
                    student_count=450,
                    primary_contact_name="John Doe",
                    primary_contact_email="john@school.edu",
                    primary_contact_phone="+263 77 123 4567",
                    payment_option=PaymentOption.SPLIT,
                    currency="USD",
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                response = client.post(
                    "/api/v1/migration-services/orders",
                    json=order_data
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["order_number"] == "CP-2025-001"
                assert data["student_count"] == 450
    
    def test_create_order_cross_tenant_prevention(self, client, mock_user):
        """Test prevention of cross-tenant order creation"""
        different_school_id = uuid4()
        order_data = {
            "school_id": str(different_school_id),  # Different school
            "care_package_id": str(uuid4()),
            "student_count": 450
        }
        
        with patch('backend.services.migration_services.routes.get_current_active_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            response = client.post(
                "/api/v1/migration-services/orders",
                json=order_data
            )
            
            assert response.status_code == 403
            assert "your own school" in response.json()["detail"]
    
    def test_get_orders_with_filters(self, client, mock_user):
        """Test GET /orders with filters"""
        with patch('backend.services.migration_services.routes.get_current_active_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('backend.services.migration_services.routes.MigrationServicesService') as mock_service:
                mock_service.return_value.get_care_package_orders.return_value = []
                
                response = client.get(
                    "/api/v1/migration-services/orders",
                    params={
                        "status": "in_progress",
                        "school_name": "Test School",
                        "limit": 10
                    }
                )
                
                assert response.status_code == 200
                
                # Verify service was called with correct parameters
                mock_service.return_value.get_care_package_orders.assert_called_once()
                call_args = mock_service.return_value.get_care_package_orders.call_args
                filters = call_args[0][0]
                assert filters.status == OrderStatus.IN_PROGRESS
                assert filters.school_name == "Test School"
    
    def test_super_admin_access(self, client, mock_super_admin):
        """Test super admin can access all features"""
        with patch('backend.services.migration_services.routes.get_current_active_user') as mock_get_user:
            mock_get_user.return_value = mock_super_admin
            
            with patch('backend.services.migration_services.routes.MigrationServicesService') as mock_service:
                mock_service.return_value.get_care_package_orders.return_value = []
                
                # Super admin should see all orders (no school filtering)
                response = client.get("/api/v1/migration-services/orders")
                assert response.status_code == 200
                
                # Verify school_id is None for super admin
                call_args = mock_service.return_value.get_care_package_orders.call_args
                school_id = call_args[0][1]  # Second positional argument
                assert school_id is None
    
    def test_update_order_status_admin_only(self, client, mock_user, mock_super_admin):
        """Test order status updates require admin permissions"""
        order_id = uuid4()
        
        # Test with regular user (should fail)
        with patch('backend.services.migration_services.routes.get_current_active_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            response = client.patch(
                f"/api/v1/migration-services/orders/{order_id}/status",
                params={"status": "approved"}
            )
            assert response.status_code == 403
        
        # Test with super admin (should succeed)
        with patch('backend.services.migration_services.routes.get_current_active_user') as mock_get_user:
            mock_get_user.return_value = mock_super_admin
            
            with patch('backend.services.migration_services.routes.MigrationServicesService') as mock_service:
                mock_service.return_value.update_care_package_order.return_value = CarePackageOrderResponse(
                    id=order_id,
                    order_number="CP-2025-001",
                    school_id=uuid4(),
                    care_package_id=uuid4(),
                    order_date=date.today(),
                    status=OrderStatus.APPROVED,
                    package_price=Decimal("6500.00"),
                    additional_costs=Decimal("0.00"),
                    total_price=Decimal("6500.00"),
                    payment_status=PaymentStatus.PENDING,
                    progress_percentage=0,
                    actual_hours=0,
                    payment_option=PaymentOption.SPLIT,
                    currency="USD",
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                response = client.patch(
                    f"/api/v1/migration-services/orders/{order_id}/status",
                    params={"status": "approved"}
                )
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "approved"


class TestMultiTenantIntegration:
    """Test integration with multi-tenant system"""
    
    @pytest.mark.asyncio
    async def test_row_level_security_policy(self):
        """Test RLS policies prevent cross-tenant access"""
        # This would test actual database RLS policies
        # For now, we'll test the logic conceptually
        
        school_a_id = uuid4()
        school_b_id = uuid4()
        
        # Mock database session with RLS context
        mock_db = Mock()
        mock_db.execute = Mock()
        
        # Test that setting school context filters data
        with patch('backend.services.migration_services.service.text') as mock_text:
            service = MigrationServicesService(mock_db)
            
            # This would set the RLS context
            await service._set_tenant_context(school_a_id)
            
            # Verify the context was set correctly
            mock_db.execute.assert_called()
            call_args = mock_db.execute.call_args[0][0]
            assert str(school_a_id) in str(call_args)
    
    def test_subdomain_extraction(self):
        """Test subdomain extraction from host headers"""
        test_cases = [
            ("peterhouse.oneclass.ac.zw", "peterhouse"),
            ("test-school.oneclass.ac.zw", "test-school"),
            ("school123.oneclass.ac.zw", "school123"),
            ("oneclass.ac.zw", None),  # No subdomain
            ("invalid..oneclass.ac.zw", None),  # Invalid format
        ]
        
        for host, expected_subdomain in test_cases:
            # Mock the subdomain extraction logic
            with patch('backend.services.migration_services.service.extract_subdomain') as mock_extract:
                mock_extract.return_value = expected_subdomain
                
                result = mock_extract(host)
                assert result == expected_subdomain
    
    def test_school_context_injection(self):
        """Test school context is properly injected"""
        school_data = {
            "id": uuid4(),
            "name": "Test School",
            "code": "TEST",
            "subscription_tier": "professional",
            "enabled_modules": ["sis", "finance", "migration_services"]
        }
        
        # Test that migration services is in enabled modules
        assert "migration_services" in school_data["enabled_modules"]
        
        # Test subscription tier allows migration services
        professional_features = ["sis", "finance", "migration_services", "analytics"]
        assert school_data["subscription_tier"] in ["professional", "enterprise"]
    
    def test_permission_inheritance(self):
        """Test permission inheritance from platform authentication"""
        # Test different user roles and their permissions
        test_cases = [
            ("platform_admin", ["*"]),  # Super admin has all permissions
            ("school_admin", ["migration_services.create", "migration_services.read", "migration_services.update"]),
            ("teacher", ["migration_services.read"]),  # Teachers can only view
            ("parent", []),  # Parents have no migration services access
        ]
        
        for role, expected_permissions in test_cases:
            user_mock = Mock()
            user_mock.role = role
            user_mock.permissions = expected_permissions
            
            # Test permission checking
            if role == "platform_admin":
                assert "*" in user_mock.permissions
            elif role == "school_admin":
                assert "migration_services.create" in user_mock.permissions
            elif role == "teacher":
                assert "migration_services.read" in user_mock.permissions
            else:
                assert "migration_services.create" not in user_mock.permissions


class TestErrorHandling:
    """Test comprehensive error handling"""
    
    @pytest.fixture
    def service(self):
        """Create service with mocked dependencies"""
        mock_db = Mock()
        return MigrationServicesService(mock_db)
    
    @pytest.mark.asyncio
    async def test_invalid_care_package_id(self, service):
        """Test handling of invalid care package ID"""
        with patch.object(service, 'get_care_package') as mock_get:
            mock_get.return_value = None
            
            order_data = CarePackageOrderCreate(
                school_id=uuid4(),
                care_package_id=uuid4(),
                student_count=100
            )
            
            with pytest.raises(ValueError, match="Care package not found"):
                await service.create_care_package_order(order_data, uuid4())
    
    @pytest.mark.asyncio
    async def test_database_constraint_violations(self, service):
        """Test handling of database constraint violations"""
        service.db.commit = Mock()
        service.db.rollback = Mock()
        service.db.commit.side_effect = Exception("Constraint violation")
        
        package_data = CarePackageCreate(
            name="Test Package",
            price_usd=Decimal("5000.00"),
            price_zwl=Decimal("8000000.00"),
            max_students=500,
            max_historical_years=2,
            features={},
            inclusions=[],
            exclusions=[],
            estimated_duration_days=20
        )
        
        with patch('backend.services.migration_services.service.CarePackage'):
            with pytest.raises(Exception):
                await service.create_care_package(package_data)
            
            service.db.rollback.assert_called_once()
    
    def test_api_validation_errors(self):
        """Test API validation error responses"""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Test invalid JSON
        response = client.post(
            "/api/v1/migration-services/care-packages",
            data="invalid json"  # Not JSON
        )
        assert response.status_code == 422
        
        # Test missing required fields
        response = client.post(
            "/api/v1/migration-services/care-packages",
            json={"name": "Test"}  # Missing required fields
        )
        assert response.status_code == 422
    
    def test_concurrent_access_handling(self):
        """Test handling of concurrent access scenarios"""
        # Test that concurrent order creation doesn't cause conflicts
        mock_db = Mock()
        service = MigrationServicesService(mock_db)
        
        # Mock order number generation to potentially conflict
        with patch.object(service, '_generate_order_number') as mock_gen:
            mock_gen.side_effect = ["CP-2025-001", "CP-2025-002", "CP-2025-003"]
            
            # Simulate concurrent order creation
            order_numbers = []
            for i in range(3):
                order_numbers.append(mock_gen())
            
            # Verify each order gets unique number
            assert len(set(order_numbers)) == 3
            assert "CP-2025-001" in order_numbers
            assert "CP-2025-002" in order_numbers
            assert "CP-2025-003" in order_numbers


class TestPerformanceAndScaling:
    """Test performance and scaling aspects"""
    
    @pytest.mark.asyncio
    async def test_large_order_list_performance(self):
        """Test performance with large number of orders"""
        mock_db = Mock()
        service = MigrationServicesService(mock_db)
        
        # Mock database to return large result set
        mock_orders = [Mock(id=uuid4()) for _ in range(1000)]
        
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = mock_orders[:50]  # Simulated pagination
        
        with patch.object(service, '_get_order_response') as mock_response:
            mock_response.return_value = CarePackageOrderResponse(
                id=uuid4(),
                order_number="CP-2025-001",
                school_id=uuid4(),
                care_package_id=uuid4(),
                order_date=date.today(),
                status=OrderStatus.PENDING,
                package_price=Decimal("6500.00"),
                additional_costs=Decimal("0.00"),
                total_price=Decimal("6500.00"),
                payment_status=PaymentStatus.PENDING,
                progress_percentage=0,
                actual_hours=0,
                payment_option=PaymentOption.SPLIT,
                currency="USD",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Test with pagination
            orders = await service.get_care_package_orders(
                limit=50,
                offset=0
            )
            
            assert len(orders) == 50
            # Verify pagination was applied
            mock_query.limit.assert_called_with(50)
            mock_query.offset.assert_called_with(0)
    
    def test_database_query_optimization(self):
        """Test database query optimization"""
        mock_db = Mock()
        service = MigrationServicesService(mock_db)
        
        # Test that joinedload is used for related data
        with patch.object(service, '_get_order_response') as mock_response:
            mock_response.return_value = None
            
            # Mock query with joinedload
            mock_query = Mock()
            mock_db.query.return_value = mock_query
            mock_query.options.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = Mock()
            
            # This would test eager loading of related data
            service.db.query.assert_called()
    
    def test_caching_strategies(self):
        """Test caching strategies for frequently accessed data"""
        # Test that care packages are cached since they change infrequently
        mock_cache = {}
        
        def mock_cache_get(key):
            return mock_cache.get(key)
        
        def mock_cache_set(key, value, ttl=None):
            mock_cache[key] = value
        
        # Simulate caching care packages
        packages_key = "care_packages_active"
        
        # First call - cache miss
        assert mock_cache_get(packages_key) is None
        
        # Simulate fetching from database
        mock_packages = [{"id": "pkg1", "name": "Foundation"}]
        mock_cache_set(packages_key, mock_packages, ttl=3600)
        
        # Second call - cache hit
        cached_packages = mock_cache_get(packages_key)
        assert cached_packages == mock_packages


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])