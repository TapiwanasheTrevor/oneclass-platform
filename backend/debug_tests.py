#!/usr/bin/env python3
"""
Debug failing tests
"""

import sys
import os
import asyncio
from unittest.mock import Mock, patch

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_permission_checks():
    """Debug permission checking"""
    try:
        from shared.auth import EnhancedUser, SchoolConfiguration
        from uuid import uuid4
        from datetime import datetime
        
        print("Creating school configuration...")
        school_config = SchoolConfiguration(
            school_id=uuid4(),
            features_enabled={"migration_services": True},
            subscription_tier="professional",
            grading_system={},
            notification_settings={}
        )
        print(f"School config created: {school_config}")
        
        print("Creating school admin user...")
        school_admin = EnhancedUser(
            id=uuid4(),
            email="admin@school.edu",
            first_name="School",
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
        print(f"School admin: {school_admin}")
        print(f"Is admin: {school_admin.is_admin}")
        print(f"Permissions: {school_admin.permissions}")
        
        return True
    except Exception as e:
        print(f"Error in permission checks: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_feature_availability():
    """Debug feature availability"""
    try:
        from shared.auth import get_available_features
        
        print("Testing feature availability...")
        
        async def test_features():
            try:
                print("Getting trial features...")
                trial_features = await get_available_features("trial")
                print(f"Trial features: {trial_features}")
                
                print("Getting basic features...")
                basic_features = await get_available_features("basic")
                print(f"Basic features: {basic_features}")
                
                print("Getting professional features...")
                professional_features = await get_available_features("premium")
                print(f"Professional features: {professional_features}")
                
                print("Getting enterprise features...")
                enterprise_features = await get_available_features("enterprise")
                print(f"Enterprise features: {enterprise_features}")
                
                return True
            except Exception as e:
                print(f"Error in async test: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        result = asyncio.run(test_features())
        return result
    except Exception as e:
        print(f"Error in feature availability: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run debug tests"""
    print("Debugging Migration Services Tests...")
    print("=" * 50)
    
    print("1. Debug permission checks:")
    debug_permission_checks()
    
    print("\n2. Debug feature availability:")
    debug_feature_availability()

if __name__ == "__main__":
    main()