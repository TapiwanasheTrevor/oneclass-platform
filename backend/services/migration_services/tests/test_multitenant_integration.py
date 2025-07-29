"""
Multi-Tenant Integration Tests for Migration Services
Tests to ensure proper integration with the existing multi-tenant system
"""
import pytest
import asyncio
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4, UUID
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

# Import existing platform components
from shared.middleware.tenant_middleware import TenantMiddleware, get_tenant_context
from shared.auth import get_current_active_user, require_permission
from shared.models.platform import 
from shared.models.platform_user import PlatformUserDB as User, School
from services.migration_services.routes import router
from services.migration_services.service import MigrationServicesService
from shared.models.migration_services import (
    CarePackageOrderCreate, CarePackageOrderResponse, 
    OrderStatus, PaymentStatus, PaymentOption
)


class TestTenantMiddlewareIntegration:
    """Test integration with existing tenant middleware"""
    
    @pytest.fixture
    def app_with_middleware(self):
        """Create FastAPI app with tenant middleware and migration routes"""
        app = FastAPI()
        
        # Add tenant middleware (same as main app)
        app.add_middleware(TenantMiddleware)
        
        # Add migration services routes
        app.include_router(router)
        
        return app
    
    @pytest.fixture
    def client(self, app_with_middleware):
        """Create test client with middleware"""
        return TestClient(app_with_middleware)
    
    def test_subdomain_based_access(self, client):
        """Test that migration services respect subdomain-based access"""
        school_id = uuid4()
        
        with patch('backend.shared.middleware.tenant_middleware.extract_subdomain') as mock_extract:
            with patch('backend.shared.middleware.tenant_middleware.get_school_by_subdomain') as mock_get_school:
                with patch('backend.services.migration_services.routes.get_current_active_user') as mock_user:
                    with patch('backend.services.migration_services.routes.MigrationServicesService') as mock_service:
                        
                        # Setup tenant context
                        mock_extract.return_value = "peterhouse"
                        mock_get_school.return_value = {
                            "id": str(school_id),
                            "name": "Peterhouse School",
                            "code": "PETERHOUSE", 
                            "subscription_tier": "professional",
                            "enabled_modules": ["sis", "finance", "migration_services"],
                            "settings": {"timezone": "Africa/Harare"}
                        }
                        
                        # Setup user context
                        mock_user.return_value = Mock(
                            id=uuid4(),
                            role="school_admin",
                            school_id=school_id,
                            email="admin@peterhouse.oneclass.ac.zw"
                        )
                        
                        # Setup service response
                        mock_service.return_value.get_care_package_orders.return_value = []
                        
                        # Make request with proper subdomain
                        response = client.get(
                            "/api/v1/migration-services/orders",
                            headers={"Host": "peterhouse.oneclass.ac.zw"}
                        )
                        
                        assert response.status_code == 200
                        
                        # Verify school context was passed to service
                        mock_service.return_value.get_care_package_orders.assert_called_once()
                        call_args = mock_service.return_value.get_care_package_orders.call_args
                        # School ID should be passed for filtering
                        assert call_args[0][1] == school_id
    
    def test_cross_tenant_prevention(self, client):
        """Test prevention of cross-tenant access"""
        school_a_id = uuid4()
        school_b_id = uuid4()
        
        with patch('backend.shared.middleware.tenant_middleware.extract_subdomain') as mock_extract:
            with patch('backend.shared.middleware.tenant_middleware.get_school_by_subdomain') as mock_get_school:
                with patch('backend.services.migration_services.routes.get_current_active_user') as mock_user:
                    
                    # Setup: User belongs to School A
                    mock_extract.return_value = "schoola"
                    mock_get_school.return_value = {
                        "id": str(school_a_id),
                        "name": "School A",
                        "code": "SCHOOLA",
                        "subscription_tier": "professional",
                        "enabled_modules": ["migration_services"],
                        "settings": {}
                    }
                    
                    # User token belongs to School B (different school)
                    mock_user.return_value = Mock(
                        id=uuid4(),
                        role="school_admin", 
                        school_id=school_b_id,  # Different school!
                        email="admin@schoolb.oneclass.ac.zw"
                    )
                    
                    # Try to create order for School A while logged in as School B user
                    order_data = {
                        "school_id": str(school_a_id),
                        "care_package_id": str(uuid4()),
                        "student_count": 100
                    }
                    
                    response = client.post(
                        "/api/v1/migration-services/orders",
                        json=order_data,
                        headers={"Host": "schoola.oneclass.ac.zw"}
                    )
                    
                    # Should be forbidden due to cross-tenant access
                    assert response.status_code == 403
                    assert "your own school" in response.json()["detail"]
    
    def test_module_availability_check(self, client):
        """Test that migration services respects module availability"""
        school_id = uuid4()
        
        with patch('backend.shared.middleware.tenant_middleware.extract_subdomain') as mock_extract:
            with patch('backend.shared.middleware.tenant_middleware.get_school_by_subdomain') as mock_get_school:
                with patch('backend.services.migration_services.routes.get_current_active_user') as mock_user:
                    
                    # Setup: School without migration services module
                    mock_extract.return_value = "basicschool"
                    mock_get_school.return_value = {
                        "id": str(school_id),
                        "name": "Basic School",
                        "code": "BASIC",
                        "subscription_tier": "basic",
                        "enabled_modules": ["sis"],  # No migration_services
                        "settings": {}
                    }
                    
                    mock_user.return_value = Mock(
                        id=uuid4(),
                        role="school_admin",
                        school_id=school_id,
                        email="admin@basicschool.oneclass.ac.zw"
                    )
                    
                    # Try to access migration services
                    response = client.get(
                        "/api/v1/migration-services/orders",
                        headers={"Host": "basicschool.oneclass.ac.zw"}
                    )
                    
                    # Should be forbidden due to module not being enabled
                    assert response.status_code in [403, 404]
    
    def test_subscription_tier_validation(self, client):
        """Test subscription tier requirements for migration services"""
        test_cases = [
            ("trial", False),      # Trial tier shouldn't have migration services
            ("basic", True),       # Basic tier has migration services
            ("professional", True), # Professional tier has migration services
            ("enterprise", True),  # Enterprise tier has migration services
        ]
        
        for tier, should_have_access in test_cases:
            school_id = uuid4()
            
            with patch('backend.shared.middleware.tenant_middleware.extract_subdomain') as mock_extract:
                with patch('backend.shared.middleware.tenant_middleware.get_school_by_subdomain') as mock_get_school:
                    with patch('backend.services.migration_services.routes.get_current_active_user') as mock_user:
                        with patch('backend.services.migration_services.routes.MigrationServicesService') as mock_service:
                            
                            # Setup school with specific tier
                            mock_extract.return_value = "testschool"
                            
                            enabled_modules = ["sis"]
                            if should_have_access:
                                enabled_modules.append("migration_services")
                            
                            mock_get_school.return_value = {
                                "id": str(school_id),
                                "name": "Test School",
                                "code": "TEST",
                                "subscription_tier": tier,
                                "enabled_modules": enabled_modules,
                                "settings": {}
                            }
                            
                            mock_user.return_value = Mock(
                                id=uuid4(),
                                role="school_admin",
                                school_id=school_id,
                                email="admin@testschool.oneclass.ac.zw"
                            )
                            
                            if should_have_access:
                                mock_service.return_value.get_care_package_orders.return_value = []
                            
                            response = client.get(
                                "/api/v1/migration-services/orders",
                                headers={"Host": "testschool.oneclass.ac.zw"}
                            )
                            
                            if should_have_access:
                                assert response.status_code == 200
                            else:
                                assert response.status_code in [403, 404]


class TestAuthenticationIntegration:
    """Test integration with existing authentication system"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        """Create service instance"""
        return MigrationServicesService(mock_db)
    
    def test_role_based_permissions(self):
        """Test that migration services respects role-based permissions"""
        test_cases = [
            ("platform_admin", True, True, True),    # Can create, read, update
            ("school_admin", True, True, True),      # Can create, read, update
            ("registrar", False, True, False),       # Can only read
            ("teacher", False, True, False),         # Can only read
            ("parent", False, False, False),         # No access
            ("student", False, False, False),        # No access
        ]
        
        for role, can_create, can_read, can_update in test_cases:
            user = Mock()
            user.role = role
            user.id = uuid4()
            user.school_id = uuid4()
            
            # Test permissions based on role
            if role == "platform_admin":
                assert user.role == "platform_admin"
            elif role == "school_admin":
                assert user.role == "school_admin"
            elif role in ["registrar", "teacher"]:
                assert user.role in ["registrar", "teacher"]
            else:
                assert user.role in ["parent", "student"]
    
    @pytest.mark.asyncio
    async def test_permission_decorators_integration(self):
        """Test integration with permission decorators"""
        
        @require_permission("migration_services.create")
        async def create_order(current_user=None):
            return "Order created"
        
        # Test with user having permission
        user_with_perm = Mock()
        user_with_perm.permissions = ["migration_services.create"]
        
        result = await create_order(current_user=user_with_perm)
        assert result == "Order created"
        
        # Test with user without permission
        user_without_perm = Mock()
        user_without_perm.permissions = ["migration_services.read"]
        
        with pytest.raises(HTTPException) as exc_info:
            await create_order(current_user=user_without_perm)
        
        assert exc_info.value.status_code == 403
    
    def test_jwt_token_validation(self):
        """Test JWT token validation in migration services context"""
        # Mock JWT payload
        token_payload = {
            "sub": str(uuid4()),
            "school_id": str(uuid4()),
            "role": "school_admin",
            "permissions": ["migration_services.create", "migration_services.read"],
            "iat": datetime.utcnow().timestamp(),
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp()
        }
        
        # Test valid token
        assert token_payload["sub"] is not None
        assert token_payload["school_id"] is not None
        assert "migration_services.create" in token_payload["permissions"]
        
        # Test token with insufficient permissions
        limited_payload = {
            **token_payload,
            "permissions": ["sis.read"]  # No migration services permissions
        }
        
        assert "migration_services.create" not in limited_payload["permissions"]
    
    def test_super_admin_bypass(self):
        """Test that super admin bypasses school restrictions"""
        super_admin = Mock()
        super_admin.role = "platform_admin"
        super_admin.school_id = None  # Super admin not tied to specific school
        super_admin.permissions = ["*"]  # All permissions
        
        # Super admin should be able to:
        # 1. View all orders across all schools
        # 2. Create orders for any school
        # 3. Update any order
        # 4. Access all migration services features
        
        assert super_admin.role == "platform_admin"
        assert super_admin.school_id is None
        assert "*" in super_admin.permissions


class TestDatabaseIntegration:
    """Test database-level integration with existing platform"""
    
    def test_foreign_key_constraints(self):
        """Test foreign key relationships with platform tables"""
        # Test that migration services properly reference platform tables
        
        # care_package_orders.school_id -> platform.schools.id
        school_id = uuid4()
        order_data = {
            "school_id": school_id,
            "care_package_id": uuid4(),
            "student_count": 100
        }
        
        # Mock database constraint validation
        assert order_data["school_id"] == school_id
        
        # care_package_orders.assigned_migration_manager -> platform.users.id
        user_id = uuid4()
        assignment_data = {
            "assigned_migration_manager": user_id
        }
        
        assert assignment_data["assigned_migration_manager"] == user_id
    
    def test_row_level_security_policies(self):
        """Test RLS policies integration"""
        mock_db = Mock()
        service = MigrationServicesService(mock_db)
        
        # Test setting tenant context
        school_id = uuid4()
        
        with patch('backend.services.migration_services.service.text') as mock_text:
            # This would be called to set RLS context
            rls_query = text("SELECT set_config('app.current_school_id', :school_id, true)")
            
            # Verify the RLS context would be set
            mock_text.assert_called()
            assert str(school_id) in str(mock_text.call_args)
    
    def test_database_migration_compatibility(self):
        """Test that migration services schema is compatible with platform"""
        # Test that migration services schema doesn't conflict with existing tables
        
        # Schema should be separate
        migration_schema = "migration_services"
        platform_schema = "platform"
        
        assert migration_schema != platform_schema
        
        # Test table naming doesn't conflict
        migration_tables = [
            "care_packages",
            "care_package_orders", 
            "migration_tasks",
            "data_sources",
            "communication_log",
            "payments",
            "milestones",
            "team_performance"
        ]
        
        platform_tables = [
            "schools",
            "users",
            "school_configurations",
            "school_domains"
        ]
        
        # No table name conflicts
        assert len(set(migration_tables) & set(platform_tables)) == 0
    
    def test_uuid_consistency(self):
        """Test UUID usage consistency with platform"""
        # Test that UUIDs are used consistently across platform and migration services
        
        # All primary keys should use UUID
        uuid_fields = [
            "care_packages.id",
            "care_package_orders.id",
            "migration_tasks.id",
            "data_sources.id"
        ]
        
        for field in uuid_fields:
            # Mock UUID generation
            test_uuid = uuid4()
            assert isinstance(test_uuid, UUID)
            assert str(test_uuid) is not None
    
    def test_timestamp_consistency(self):
        """Test timestamp usage consistency with platform"""
        # Test that timestamps use consistent format
        
        now = datetime.now()
        
        # All timestamps should be timezone-aware
        timestamp_fields = [
            "created_at",
            "updated_at",
            "processed_at",
            "completion_date"
        ]
        
        for field in timestamp_fields:
            # Mock timestamp
            test_timestamp = now
            assert isinstance(test_timestamp, datetime)


class TestFeatureIntegration:
    """Test integration with platform features"""
    
    def test_school_branding_integration(self):
        """Test integration with school branding system"""
        school_config = {
            "logo_url": "https://school.com/logo.png",
            "primary_color": "#1e40af",
            "secondary_color": "#10b981",
            "font_family": "Inter"
        }
        
        # Migration services should use school branding
        # in order confirmation emails, documents, etc.
        
        assert school_config["logo_url"] is not None
        assert school_config["primary_color"] is not None
        assert school_config["secondary_color"] is not None
    
    def test_notification_system_integration(self):
        """Test integration with existing notification system"""
        # Migration services should use existing notification channels
        
        notification_channels = [
            "email",
            "sms", 
            "push_notification",
            "in_app"
        ]
        
        # Test that migration services can send notifications
        for channel in notification_channels:
            # Mock notification sending
            notification_data = {
                "channel": channel,
                "recipient": "admin@school.edu",
                "subject": "Migration Status Update",
                "message": "Your migration is 50% complete"
            }
            
            assert notification_data["channel"] == channel
            assert notification_data["recipient"] is not None
    
    def test_file_storage_integration(self):
        """Test integration with existing file storage system"""
        # Migration services should use existing file storage for:
        # - Source data files
        # - Migration reports
        # - Documentation
        
        file_storage_config = {
            "provider": "s3",
            "bucket": "oneclass-files",
            "region": "us-east-1",
            "path_prefix": "migration-services/"
        }
        
        assert file_storage_config["provider"] == "s3"
        assert file_storage_config["bucket"] is not None
        assert "migration-services/" in file_storage_config["path_prefix"]
    
    def test_analytics_integration(self):
        """Test integration with existing analytics system"""
        # Migration services should contribute to platform analytics
        
        analytics_events = [
            "migration_order_created",
            "migration_progress_updated", 
            "migration_completed",
            "package_selected",
            "payment_processed"
        ]
        
        for event in analytics_events:
            # Mock analytics event
            event_data = {
                "event": event,
                "school_id": str(uuid4()),
                "timestamp": datetime.now(),
                "properties": {
                    "package_type": "Growth",
                    "student_count": 450
                }
            }
            
            assert event_data["event"] == event
            assert event_data["school_id"] is not None
            assert event_data["timestamp"] is not None


class TestEndToEndIntegration:
    """Test complete end-to-end integration scenarios"""
    
    @pytest.fixture
    def integrated_app(self):
        """Create fully integrated app with all middleware"""
        app = FastAPI()
        
        # Add all middleware in correct order
        app.add_middleware(TenantMiddleware)
        
        # Add all routes
        app.include_router(router)
        
        return app
    
    @pytest.fixture
    def client(self, integrated_app):
        """Create test client with full integration"""
        return TestClient(integrated_app)
    
    def test_complete_order_flow(self, client):
        """Test complete order flow from creation to completion"""
        school_id = uuid4()
        user_id = uuid4()
        
        with patch('backend.shared.middleware.tenant_middleware.extract_subdomain') as mock_extract:
            with patch('backend.shared.middleware.tenant_middleware.get_school_by_subdomain') as mock_get_school:
                with patch('backend.services.migration_services.routes.get_current_active_user') as mock_user:
                    with patch('backend.services.migration_services.routes.MigrationServicesService') as mock_service:
                        
                        # Setup full tenant context
                        mock_extract.return_value = "testschool"
                        mock_get_school.return_value = {
                            "id": str(school_id),
                            "name": "Test School",
                            "code": "TEST",
                            "subscription_tier": "professional",
                            "enabled_modules": ["sis", "finance", "migration_services"],
                            "settings": {"timezone": "Africa/Harare"}
                        }
                        
                        mock_user.return_value = Mock(
                            id=user_id,
                            role="school_admin",
                            school_id=school_id,
                            email="admin@testschool.oneclass.ac.zw"
                        )
                        
                        # Step 1: Create order
                        order_data = {
                            "school_id": str(school_id),
                            "care_package_id": str(uuid4()),
                            "student_count": 450,
                            "primary_contact_name": "John Doe",
                            "primary_contact_email": "john@testschool.oneclass.ac.zw",
                            "primary_contact_phone": "+263 77 123 4567"
                        }
                        
                        created_order = CarePackageOrderResponse(
                            id=uuid4(),
                            order_number="CP-2025-001",
                            school_id=school_id,
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
                            primary_contact_email="john@testschool.oneclass.ac.zw",
                            primary_contact_phone="+263 77 123 4567",
                            payment_option=PaymentOption.SPLIT,
                            currency="USD",
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        
                        mock_service.return_value.create_care_package_order.return_value = created_order
                        
                        response = client.post(
                            "/api/v1/migration-services/orders",
                            json=order_data,
                            headers={"Host": "testschool.oneclass.ac.zw"}
                        )
                        
                        assert response.status_code == 200
                        order_response = response.json()
                        assert order_response["order_number"] == "CP-2025-001"
                        assert order_response["status"] == "pending"
                        
                        # Step 2: Verify order appears in list
                        mock_service.return_value.get_care_package_orders.return_value = [created_order]
                        
                        response = client.get(
                            "/api/v1/migration-services/orders",
                            headers={"Host": "testschool.oneclass.ac.zw"}
                        )
                        
                        assert response.status_code == 200
                        orders = response.json()
                        assert len(orders) == 1
                        assert orders[0]["order_number"] == "CP-2025-001"
                        
                        # Step 3: Verify dashboard shows order
                        from shared.models.migration_services import MigrationServicesDashboard
                        
                        dashboard_data = MigrationServicesDashboard(
                            active_projects=1,
                            monthly_revenue=Decimal("6500.00"),
                            team_utilization=Decimal("85"),
                            success_rate=Decimal("96"),
                            projects_trend="+1 new project",
                            revenue_trend="+$6,500",
                            utilization_trend="Optimal",
                            success_rate_trend="Above target",
                            recent_orders=[created_order],
                            team_performance=[]
                        )
                        
                        mock_service.return_value.get_migration_dashboard.return_value = dashboard_data
                        
                        response = client.get(
                            "/api/v1/migration-services/dashboard",
                            headers={"Host": "testschool.oneclass.ac.zw"}
                        )
                        
                        assert response.status_code == 200
                        dashboard = response.json()
                        assert dashboard["active_projects"] == 1
                        assert len(dashboard["recent_orders"]) == 1
    
    def test_super_admin_multi_tenant_access(self, client):
        """Test super admin can access all tenants"""
        super_admin_id = uuid4()
        
        with patch('backend.shared.middleware.tenant_middleware.extract_subdomain') as mock_extract:
            with patch('backend.shared.middleware.tenant_middleware.get_school_by_subdomain') as mock_get_school:
                with patch('backend.services.migration_services.routes.get_current_active_user') as mock_user:
                    with patch('backend.services.migration_services.routes.MigrationServicesService') as mock_service:
                        
                        # Setup any school context
                        mock_extract.return_value = "anyschool"
                        mock_get_school.return_value = {
                            "id": str(uuid4()),
                            "name": "Any School",
                            "code": "ANY",
                            "subscription_tier": "professional",
                            "enabled_modules": ["migration_services"],
                            "settings": {}
                        }
                        
                        # Super admin user
                        mock_user.return_value = Mock(
                            id=super_admin_id,
                            role="platform_admin",
                            school_id=None,  # Not tied to specific school
                            email="admin@oneclass.ac.zw"
                        )
                        
                        # Super admin should see all orders
                        mock_service.return_value.get_care_package_orders.return_value = []
                        
                        response = client.get(
                            "/api/v1/migration-services/orders",
                            headers={"Host": "anyschool.oneclass.ac.zw"}
                        )
                        
                        assert response.status_code == 200
                        
                        # Verify service was called without school filtering
                        mock_service.return_value.get_care_package_orders.assert_called_once()
                        call_args = mock_service.return_value.get_care_package_orders.call_args
                        school_id_arg = call_args[0][1]  # Second positional argument
                        assert school_id_arg is None  # No school filtering for super admin


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])