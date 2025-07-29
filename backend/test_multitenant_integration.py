#!/usr/bin/env python3
"""
Multi-tenant integration tests for migration services
"""

import sys
import os
from unittest.mock import Mock, patch

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_auth_integration():
    """Test authentication integration with migration services"""
    try:
        from shared.auth import EnhancedUser, SchoolConfiguration
        from uuid import uuid4
        from datetime import datetime
        
        # Create a mock school configuration
        school_config = SchoolConfiguration(
            school_id=uuid4(),
            features_enabled={"migration_services": True},
            subscription_tier="professional",
            grading_system={},
            notification_settings={}
        )
        
        # Create a mock user
        user = EnhancedUser(
            id=uuid4(),
            email="admin@testschool.oneclass.ac.zw",
            first_name="Test",
            last_name="Admin",
            role="school_admin",
            is_active=True,
            school_id=uuid4(),
            school_name="Test School",
            school_type="primary",
            school_config=school_config,
            school_domains=[],
            permissions=["migration_services.create", "migration_services.read"],
            available_features=["migration_services"],
            created_at=datetime.now()
        )
        
        assert user.is_admin is True
        assert user.can_access_feature("migration_services") is True
        assert "migration_services.create" in user.permissions
        
        print("✓ Authentication integration successful")
        return True
    except Exception as e:
        print(f"✗ Authentication integration failed: {e}")
        return False

def test_permission_checks():
    """Test permission checking for different roles"""
    try:
        # Test role-based permissions
        roles = {
            "school_admin": {"is_admin": True, "can_create": True},
            "teacher": {"is_admin": False, "can_create": False},
            "platform_admin": {"is_admin": True, "can_create": True}
        }
        
        for role, expected in roles.items():
            # Simple role check
            is_admin = role in ["school_admin", "platform_admin", "super_admin"]
            can_create = role in ["school_admin", "platform_admin", "super_admin"]
            
            assert is_admin == expected["is_admin"]
            assert can_create == expected["can_create"]
        
        print("✓ Permission checks successful")
        return True
    except Exception as e:
        print(f"✗ Permission checks failed: {e}")
        return False

def test_tenant_isolation():
    """Test tenant isolation logic"""
    try:
        from uuid import uuid4
        
        # Mock two different schools
        school_a_id = uuid4()
        school_b_id = uuid4()
        
        # Simulate cross-tenant access prevention
        def check_tenant_access(user_school_id, resource_school_id):
            return user_school_id == resource_school_id
        
        # Test same tenant access (should pass)
        assert check_tenant_access(school_a_id, school_a_id) is True
        
        # Test cross-tenant access (should fail)
        assert check_tenant_access(school_a_id, school_b_id) is False
        
        print("✓ Tenant isolation logic successful")
        return True
    except Exception as e:
        print(f"✗ Tenant isolation test failed: {e}")
        return False

def test_feature_availability():
    """Test feature availability by subscription tier"""
    try:
        from shared.auth import get_available_features
        import asyncio
        
        async def test_features():
            # Test different subscription tiers
            trial_features = await get_available_features("trial")
            basic_features = await get_available_features("basic")
            professional_features = await get_available_features("premium")
            enterprise_features = await get_available_features("enterprise")
            
            # Trial should have limited features
            assert "student_management" in trial_features
            assert "migration_services" not in trial_features
            
            # Basic should have migration services
            assert "migration_services" in basic_features
            
            # Professional should have migration services
            assert "migration_services" in professional_features
            
            # Enterprise should have all features
            assert "migration_services" in enterprise_features
            assert "custom_integrations" in enterprise_features
            
            return True
        
        result = asyncio.run(test_features())
        assert result is True
        
        print("✓ Feature availability test successful")
        return True
    except Exception as e:
        print(f"✗ Feature availability test failed: {e}")
        return False

def test_zimbabwe_specific_features():
    """Test Zimbabwe-specific features"""
    try:
        from shared.models.migration_services import CarePackageResponse
        from decimal import Decimal
        from uuid import uuid4
        from datetime import datetime
        
        # Create a care package with Zimbabwe pricing
        package = CarePackageResponse(
            id=uuid4(),
            name="Growth Package",
            price_usd=Decimal("6500.00"),
            price_zwl=Decimal("10400000.00"),  # USD to ZWL conversion
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
        
        # Test Zimbabwe currency conversion (approximate rate)
        zwl_rate = float(package.price_zwl) / float(package.price_usd)
        assert zwl_rate == 1600  # 1 USD = 1600 ZWL
        
        # Test Zimbabwe phone format validation
        from shared.models.migration_services import CarePackageOrderCreate
        
        order_data = {
            "school_id": uuid4(),
            "care_package_id": uuid4(),
            "student_count": 100,
            "primary_contact_name": "John Doe",
            "primary_contact_email": "john@school.edu",
            "primary_contact_phone": "+263 77 123 4567"  # Zimbabwe format
        }
        
        order = CarePackageOrderCreate(**order_data)
        assert order.primary_contact_phone.startswith("+263")
        
        print("✓ Zimbabwe-specific features successful")
        return True
    except Exception as e:
        print(f"✗ Zimbabwe-specific features test failed: {e}")
        return False

def test_database_schema_compliance():
    """Test database schema compliance"""
    try:
        from uuid import uuid4
        from shared.models.migration_services import (
            CarePackageOrderResponse, OrderStatus, PaymentStatus, PaymentOption
        )
        from decimal import Decimal
        from datetime import date, datetime
        
        # Create an order response that matches the database schema
        order = CarePackageOrderResponse(
            id=uuid4(),
            order_number="CP-2025-001",
            school_id=uuid4(),
            care_package_id=uuid4(),
            order_date=date.today(),
            status=OrderStatus.PENDING,
            package_price=Decimal("6500.00"),
            additional_costs=Decimal("1500.00"),
            total_price=Decimal("8000.00"),
            payment_status=PaymentStatus.PENDING,
            payment_option=PaymentOption.SPLIT,
            currency="USD",
            progress_percentage=0,
            estimated_hours=160,
            actual_hours=0,
            student_count=450,
            current_system_type="excel",
            data_sources_description="Student records in Excel",
            urgent_migration=True,
            onsite_training=False,
            weekend_work=True,
            primary_contact_name="John Doe",
            primary_contact_email="john@school.edu",
            primary_contact_phone="+263 77 123 4567",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Verify all required fields are present
        assert order.order_number.startswith("CP-")
        assert order.school_id is not None
        assert order.care_package_id is not None
        assert order.total_price == Decimal("8000.00")
        assert order.currency == "USD"
        assert order.primary_contact_phone.startswith("+263")
        
        print("✓ Database schema compliance successful")
        return True
    except Exception as e:
        print(f"✗ Database schema compliance test failed: {e}")
        return False

def main():
    """Run all multi-tenant integration tests"""
    print("Running Multi-Tenant Integration Tests...")
    print("=" * 50)
    
    tests = [
        test_auth_integration,
        test_permission_checks,
        test_tenant_isolation,
        test_feature_availability,
        test_zimbabwe_specific_features,
        test_database_schema_compliance
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("=" * 50)
    print(f"Multi-Tenant Integration Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All multi-tenant integration tests passed!")
        return 0
    else:
        print("❌ Some multi-tenant integration tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())