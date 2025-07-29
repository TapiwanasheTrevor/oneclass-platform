#!/usr/bin/env python3
"""
Simple test runner for migration services to bypass pytest configuration issues
"""

import sys
import os

# Add the backend directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_imports():
    """Test basic imports work"""
    try:
        from shared.models.migration_services import CarePackageCreate, CarePackageResponse
        from services.migration_services.service import MigrationServicesService
        print("✓ Basic imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_care_package_model():
    """Test CarePackage model creation"""
    try:
        from shared.models.migration_services import CarePackageCreate
        from decimal import Decimal
        
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
        print("✓ CarePackage model creation successful")
        return True
    except Exception as e:
        print(f"✗ CarePackage model test failed: {e}")
        return False

def test_care_package_order_model():
    """Test CarePackageOrder model creation"""
    try:
        from shared.models.migration_services import CarePackageOrderCreate, PaymentOption
        from uuid import uuid4
        from datetime import date, timedelta
        
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
        print("✓ CarePackageOrder model creation successful")
        return True
    except Exception as e:
        print(f"✗ CarePackageOrder model test failed: {e}")
        return False

def test_zimbabwe_phone_validation():
    """Test Zimbabwe phone number validation"""
    try:
        from shared.models.migration_services import CarePackageOrderCreate
        from uuid import uuid4
        
        # Test valid Zimbabwe phone
        order_data = {
            "school_id": uuid4(),
            "care_package_id": uuid4(),
            "student_count": 100,
            "primary_contact_name": "John Doe",
            "primary_contact_email": "john@school.edu",
            "primary_contact_phone": "+263 77 123 4567"
        }
        
        order = CarePackageOrderCreate(**order_data)
        assert order.primary_contact_phone == "+263 77 123 4567"
        print("✓ Zimbabwe phone validation successful")
        return True
    except Exception as e:
        print(f"✗ Zimbabwe phone validation failed: {e}")
        return False

def test_order_status_enums():
    """Test order status enums work correctly"""
    try:
        from shared.models.migration_services import OrderStatus, PaymentStatus, TaskStatus
        
        # Test OrderStatus enum
        assert OrderStatus.PENDING == "pending"
        assert OrderStatus.IN_PROGRESS == "in_progress"
        assert OrderStatus.COMPLETED == "completed"
        
        # Test PaymentStatus enum
        assert PaymentStatus.PENDING == "pending"
        assert PaymentStatus.FULLY_PAID == "fully_paid"
        assert PaymentStatus.REFUNDED == "refunded"
        
        # Test TaskStatus enum
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.COMPLETED == "completed"
        
        print("✓ Status enums working correctly")
        return True
    except Exception as e:
        print(f"✗ Status enums test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Running Migration Services Tests...")
    print("=" * 50)
    
    tests = [
        test_basic_imports,
        test_care_package_model,
        test_care_package_order_model,
        test_zimbabwe_phone_validation,
        test_order_status_enums
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())