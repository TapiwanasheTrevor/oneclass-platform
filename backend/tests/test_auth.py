"""
Tests for Enhanced Authentication System
"""
import pytest
from datetime import datetime
from uuid import uuid4, UUID
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException

# Mock asyncpg before importing auth
import sys
from unittest.mock import MagicMock

sys.modules['asyncpg'] = MagicMock()

from shared.auth import (
    SchoolConfiguration,
    SchoolDomain,
    EnhancedUser,
    create_access_token,
    validate_token,
    get_user_permissions,
    get_available_features,
    require_permission,
    require_feature
)


class TestSchoolConfiguration:
    """Test SchoolConfiguration model"""
    
    def test_school_configuration_defaults(self):
        """Test SchoolConfiguration with default values"""
        school_id = uuid4()
        config = SchoolConfiguration(
            school_id=school_id,
            features_enabled={},
            grading_system={},
            notification_settings={}
        )
        
        assert config.school_id == school_id
        assert config.primary_color == "#1e40af"
        assert config.secondary_color == "#10b981"
        assert config.timezone == "Africa/Harare"
        assert config.subscription_tier == "basic"
        assert config.max_students == 500
    
    def test_school_configuration_custom_values(self):
        """Test SchoolConfiguration with custom values"""
        school_id = uuid4()
        config = SchoolConfiguration(
            school_id=school_id,
            logo_url="https://example.com/logo.png",
            primary_color="#FF0000",
            subscription_tier="premium",
            max_students=1000,
            features_enabled={"attendance_tracking": True},
            grading_system={"type": "letter"},
            notification_settings={"email_enabled": True}
        )
        
        assert config.logo_url == "https://example.com/logo.png"
        assert config.primary_color == "#FF0000"
        assert config.subscription_tier == "premium"
        assert config.max_students == 1000


class TestEnhancedUser:
    """Test EnhancedUser model"""
    
    def test_enhanced_user_properties(self):
        """Test EnhancedUser properties and methods"""
        user_id = uuid4()
        school_id = uuid4()
        
        school_config = SchoolConfiguration(
            school_id=school_id,
            features_enabled={
                "attendance_tracking": True,
                "finance_module": False
            },
            grading_system={},
            notification_settings={}
        )
        
        user = EnhancedUser(
            id=user_id,
            email="admin@test.school",
            first_name="John",
            last_name="Doe",
            role="school_admin",
            is_active=True,
            school_id=school_id,
            school_name="Test School",
            school_type="primary",
            school_config=school_config,
            school_domains=[],
            permissions=["students.create", "students.read"],
            available_features=["attendance_tracking", "finance_module"],
            created_at=datetime.now()
        )
        
        assert user.full_name == "John Doe"
        assert user.is_admin is True
        assert user.can_modify_students is True
        
        # Test feature access
        assert user.can_access_feature("attendance_tracking") is True
        assert user.can_access_feature("finance_module") is False
        assert user.can_access_feature("unknown_feature") is False
    
    def test_enhanced_user_role_checks(self):
        """Test role-based property checks"""
        base_user = {
            "id": uuid4(),
            "email": "user@test.school",
            "first_name": "Test",
            "last_name": "User",
            "is_active": True,
            "school_id": uuid4(),
            "school_name": "Test School",
            "school_type": "primary",
            "school_config": SchoolConfiguration(
                school_id=uuid4(),
                features_enabled={},
                grading_system={},
                notification_settings={}
            ),
            "school_domains": [],
            "permissions": [],
            "available_features": [],
            "created_at": datetime.now()
        }
        
        # Test teacher role
        teacher = EnhancedUser(**{**base_user, "role": "teacher"})
        assert teacher.is_admin is False
        assert teacher.can_modify_students is False
        
        # Test registrar role
        registrar = EnhancedUser(**{**base_user, "role": "registrar"})
        assert registrar.is_admin is False
        assert registrar.can_modify_students is True
        
        # Test super_admin role
        super_admin = EnhancedUser(**{**base_user, "role": "super_admin"})
        assert super_admin.is_admin is True
        assert super_admin.can_modify_students is True


class TestTokenManagement:
    """Test JWT token creation and validation"""
    
    def test_create_access_token(self):
        """Test access token creation"""
        user_id = str(uuid4())
        school_id = str(uuid4())
        
        token = create_access_token(user_id, school_id)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    @pytest.mark.asyncio
    async def test_validate_token_success(self):
        """Test successful token validation"""
        user_id = str(uuid4())
        school_id = str(uuid4())
        
        token = create_access_token(user_id, school_id)
        payload = await validate_token(token)
        
        assert payload["sub"] == user_id
        assert payload["school_id"] == school_id
        assert "iat" in payload
        assert "exp" in payload
    
    @pytest.mark.asyncio
    async def test_validate_token_invalid(self):
        """Test invalid token validation"""
        with pytest.raises(HTTPException) as exc_info:
            await validate_token("invalid.token.here")
        
        assert exc_info.value.status_code == 401
        assert "Invalid token" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_validate_token_expired(self):
        """Test expired token validation"""
        # Create a token with past expiration
        import jwt
        from datetime import timedelta
        
        payload = {
            "sub": str(uuid4()),
            "school_id": str(uuid4()),
            "iat": datetime.utcnow() - timedelta(days=2),
            "exp": datetime.utcnow() - timedelta(days=1)
        }
        
        expired_token = jwt.encode(payload, "test-secret-key", algorithm="HS256")
        
        with pytest.raises(HTTPException) as exc_info:
            await validate_token(expired_token)
        
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()


class TestPermissions:
    """Test permission system"""
    
    @pytest.mark.asyncio
    async def test_get_user_permissions(self):
        """Test permission retrieval for different roles"""
        school_id = uuid4()
        
        # Test super_admin
        perms = await get_user_permissions("super_admin", school_id)
        assert "*" in perms
        
        # Test school_admin
        perms = await get_user_permissions("school_admin", school_id)
        assert "students.create" in perms
        assert "settings.update" in perms
        assert "*" not in perms
        
        # Test teacher
        perms = await get_user_permissions("teacher", school_id)
        assert "students.read" in perms
        assert "attendance.mark" in perms
        assert "students.create" not in perms
        
        # Test parent
        perms = await get_user_permissions("parent", school_id)
        assert "children.read" in perms
        assert "students.read" not in perms
        
        # Test unknown role
        perms = await get_user_permissions("unknown_role", school_id)
        assert perms == []
    
    @pytest.mark.asyncio
    async def test_get_available_features(self):
        """Test feature availability by subscription tier"""
        # Test trial tier
        features = await get_available_features("trial")
        assert "student_management" in features
        assert "finance_module" not in features
        
        # Test basic tier
        features = await get_available_features("basic")
        assert "student_management" in features
        assert "disciplinary_system" in features
        assert "ai_assistance" not in features
        
        # Test premium tier
        features = await get_available_features("premium")
        assert "finance_module" in features
        assert "bulk_communication" in features
        assert "ministry_reporting" not in features
        
        # Test enterprise tier
        features = await get_available_features("enterprise")
        assert "ai_assistance" in features
        assert "custom_integrations" in features
        assert "priority_support" in features


class TestDecorators:
    """Test permission and feature decorators"""
    
    @pytest.mark.asyncio
    async def test_require_permission_decorator(self):
        """Test require_permission decorator"""
        @require_permission("students.create")
        async def create_student(**kwargs):
            return "Student created"
        
        # Test with user having permission
        user_with_perm = Mock()
        user_with_perm.permissions = ["students.create"]
        
        result = await create_student(current_user=user_with_perm)
        assert result == "Student created"
        
        # Test with user without permission
        user_without_perm = Mock()
        user_without_perm.permissions = ["students.read"]
        
        with pytest.raises(HTTPException) as exc_info:
            await create_student(current_user=user_without_perm)
        
        assert exc_info.value.status_code == 403
        assert "Permission required: students.create" in exc_info.value.detail
        
        # Test with super admin (has all permissions)
        super_admin = Mock()
        super_admin.permissions = ["*"]
        
        result = await create_student(current_user=super_admin)
        assert result == "Student created"
        
        # Test without current_user
        with pytest.raises(HTTPException) as exc_info:
            await create_student()
        
        assert exc_info.value.status_code == 401
        assert "Authentication required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_require_feature_decorator(self):
        """Test require_feature decorator"""
        @require_feature("finance_module")
        async def process_payment(**kwargs):
            return "Payment processed"
        
        # Create mock user with feature access
        user_with_feature = Mock()
        user_with_feature.can_access_feature = Mock(return_value=True)
        
        result = await process_payment(current_user=user_with_feature)
        assert result == "Payment processed"
        user_with_feature.can_access_feature.assert_called_with("finance_module")
        
        # Test with user without feature access
        user_without_feature = Mock()
        user_without_feature.can_access_feature = Mock(return_value=False)
        
        with pytest.raises(HTTPException) as exc_info:
            await process_payment(current_user=user_without_feature)
        
        assert exc_info.value.status_code == 403
        assert "Feature not available: finance_module" in exc_info.value.detail
        
        # Test without current_user
        with pytest.raises(HTTPException) as exc_info:
            await process_payment()
        
        assert exc_info.value.status_code == 401
        assert "Authentication required" in exc_info.value.detail


if __name__ == "__main__":
    pytest.main([__file__, "-v"])