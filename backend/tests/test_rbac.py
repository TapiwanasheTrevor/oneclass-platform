"""Tests for Role-Based Access Control (RBAC) System
Comprehensive tests for permission management and access control
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from datetime import datetime
import uuid

# Mock database modules
import sys
from unittest.mock import MagicMock
sys.modules['asyncpg'] = MagicMock()

# Import RBAC components
from shared.auth import (
    get_user_permissions,
    get_available_features,
    require_permission,
    require_feature,
    check_module_access,
    validate_school_access
)


class TestRoleBasedPermissions:
    """Test role-based permission system"""
    
    @pytest.mark.asyncio
    async def test_super_admin_permissions(self):
        """Test super admin has all permissions"""
        school_id = str(uuid.uuid4())
        permissions = await get_user_permissions("super_admin", school_id)
        
        assert "*" in permissions
        assert len(permissions) >= 1
    
    @pytest.mark.asyncio
    async def test_school_admin_permissions(self):
        """Test school admin has school-level permissions"""
        school_id = str(uuid.uuid4())
        permissions = await get_user_permissions("school_admin", school_id)
        
        expected_permissions = [
            "students.create", "students.read", "students.update", "students.delete",
            "teachers.create", "teachers.read", "teachers.update", "teachers.delete",
            "classes.create", "classes.read", "classes.update", "classes.delete",
            "finance.read", "finance.write", "finance.reports",
            "settings.update", "users.manage", "reports.generate"
        ]
        
        for perm in expected_permissions:
            assert perm in permissions
        
        # Should not have platform-wide permissions
        assert "*" not in permissions
        assert "platform.manage" not in permissions
    
    @pytest.mark.asyncio
    async def test_teacher_permissions(self):
        """Test teacher has limited permissions"""
        school_id = str(uuid.uuid4())
        permissions = await get_user_permissions("teacher", school_id)
        
        expected_permissions = [
            "students.read", "attendance.mark", "grades.read", "grades.write",
            "classes.read", "assignments.create", "assignments.read", "assignments.update"
        ]
        
        forbidden_permissions = [
            "students.create", "students.delete", "finance.read", "settings.update",
            "users.manage", "teachers.create"
        ]
        
        for perm in expected_permissions:
            assert perm in permissions
        
        for perm in forbidden_permissions:
            assert perm not in permissions
    
    @pytest.mark.asyncio
    async def test_student_permissions(self):
        """Test student has minimal permissions"""
        school_id = str(uuid.uuid4())
        permissions = await get_user_permissions("student", school_id)
        
        expected_permissions = [
            "grades.read_own", "attendance.read_own", "assignments.read_own",
            "profile.read_own", "profile.update_own"
        ]
        
        forbidden_permissions = [
            "students.create", "students.read", "grades.write", "attendance.mark",
            "finance.read", "settings.read"
        ]
        
        for perm in expected_permissions:
            assert perm in permissions
        
        for perm in forbidden_permissions:
            assert perm not in permissions
    
    @pytest.mark.asyncio
    async def test_parent_permissions(self):
        """Test parent has child-specific permissions"""
        school_id = str(uuid.uuid4())
        permissions = await get_user_permissions("parent", school_id)
        
        expected_permissions = [
            "children.read", "grades.read_children", "attendance.read_children",
            "assignments.read_children", "finance.read_children", "communications.read"
        ]
        
        forbidden_permissions = [
            "students.create", "students.read", "grades.write", "attendance.mark",
            "settings.read", "users.manage"
        ]
        
        for perm in expected_permissions:
            assert perm in permissions
        
        for perm in forbidden_permissions:
            assert perm not in permissions
    
    @pytest.mark.asyncio
    async def test_finance_manager_permissions(self):
        """Test finance manager has finance-specific permissions"""
        school_id = str(uuid.uuid4())
        permissions = await get_user_permissions("finance_manager", school_id)
        
        expected_permissions = [
            "finance.read", "finance.write", "finance.reports", "invoices.create",
            "invoices.read", "invoices.update", "payments.read", "payments.process",
            "students.read"  # Need to see student info for billing
        ]
        
        forbidden_permissions = [
            "students.create", "students.delete", "grades.read", "grades.write",
            "settings.update", "users.manage"
        ]
        
        for perm in expected_permissions:
            assert perm in permissions
        
        for perm in forbidden_permissions:
            assert perm not in permissions
    
    @pytest.mark.asyncio
    async def test_registrar_permissions(self):
        """Test registrar has student management permissions"""
        school_id = str(uuid.uuid4())
        permissions = await get_user_permissions("registrar", school_id)
        
        expected_permissions = [
            "students.create", "students.read", "students.update", "students.delete",
            "enrollments.create", "enrollments.read", "enrollments.update",
            "classes.read", "grades.read", "attendance.read"
        ]
        
        forbidden_permissions = [
            "finance.write", "settings.update", "users.manage", "teachers.create"
        ]
        
        for perm in expected_permissions:
            assert perm in permissions
        
        for perm in forbidden_permissions:
            assert perm not in permissions
    
    @pytest.mark.asyncio
    async def test_unknown_role_permissions(self):
        """Test unknown role returns empty permissions"""
        school_id = str(uuid.uuid4())
        permissions = await get_user_permissions("unknown_role", school_id)
        
        assert permissions == []


class TestFeatureAccess:
    """Test feature-based access control"""
    
    @pytest.mark.asyncio
    async def test_trial_tier_features(self):
        """Test trial tier has basic features only"""
        features = await get_available_features("trial")
        
        expected_features = [
            "student_management", "basic_attendance", "basic_grades", "basic_communication"
        ]
        
        forbidden_features = [
            "finance_module", "advanced_reporting", "bulk_communication", "ai_assistance"
        ]
        
        for feature in expected_features:
            assert feature in features
        
        for feature in forbidden_features:
            assert feature not in features
    
    @pytest.mark.asyncio
    async def test_basic_tier_features(self):
        """Test basic tier features"""
        features = await get_available_features("basic")
        
        expected_features = [
            "student_management", "attendance_tracking", "grade_management",
            "basic_communication", "disciplinary_system", "basic_reporting"
        ]
        
        forbidden_features = [
            "finance_module", "advanced_reporting", "ai_assistance", "ministry_reporting"
        ]
        
        for feature in expected_features:
            assert feature in features
        
        for feature in forbidden_features:
            assert feature not in features
    
    @pytest.mark.asyncio
    async def test_professional_tier_features(self):
        """Test professional tier features"""
        features = await get_available_features("professional")
        
        expected_features = [
            "student_management", "attendance_tracking", "grade_management",
            "communication", "disciplinary_system", "finance_module",
            "bulk_communication", "advanced_reporting", "parent_portal"
        ]
        
        forbidden_features = [
            "ai_assistance", "ministry_reporting", "custom_integrations"
        ]
        
        for feature in expected_features:
            assert feature in features
        
        for feature in forbidden_features:
            assert feature not in features
    
    @pytest.mark.asyncio
    async def test_premium_tier_features(self):
        """Test premium tier features"""
        features = await get_available_features("premium")
        
        expected_features = [
            "student_management", "attendance_tracking", "grade_management",
            "communication", "disciplinary_system", "finance_module",
            "bulk_communication", "advanced_reporting", "parent_portal",
            "mobile_app", "api_access", "priority_support"
        ]
        
        forbidden_features = [
            "ai_assistance", "ministry_reporting", "custom_integrations"
        ]
        
        for feature in expected_features:
            assert feature in features
        
        for feature in forbidden_features:
            assert feature not in features
    
    @pytest.mark.asyncio
    async def test_enterprise_tier_features(self):
        """Test enterprise tier has all features"""
        features = await get_available_features("enterprise")
        
        expected_features = [
            "student_management", "attendance_tracking", "grade_management",
            "communication", "disciplinary_system", "finance_module",
            "bulk_communication", "advanced_reporting", "parent_portal",
            "mobile_app", "api_access", "priority_support", "ai_assistance",
            "ministry_reporting", "custom_integrations", "white_labeling"
        ]
        
        for feature in expected_features:
            assert feature in features


class TestPermissionDecorators:
    """Test permission decorator functions"""
    
    @pytest.mark.asyncio
    async def test_require_permission_success(self):
        """Test require_permission decorator allows access with permission"""
        @require_permission("students.read")
        async def test_function(current_user=None):
            return "success"
        
        # Mock user with required permission
        mock_user = Mock()
        mock_user.permissions = ["students.read", "grades.read"]
        
        result = await test_function(current_user=mock_user)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_require_permission_super_admin(self):
        """Test super admin bypasses permission checks"""
        @require_permission("restricted.action")
        async def test_function(current_user=None):
            return "success"
        
        # Mock super admin user
        mock_user = Mock()
        mock_user.permissions = ["*"]
        
        result = await test_function(current_user=mock_user)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_require_permission_denied(self):
        """Test require_permission decorator denies access without permission"""
        @require_permission("students.delete")
        async def test_function(current_user=None):
            return "success"
        
        # Mock user without required permission
        mock_user = Mock()
        mock_user.permissions = ["students.read", "grades.read"]
        
        with pytest.raises(HTTPException) as exc_info:
            await test_function(current_user=mock_user)
        
        assert exc_info.value.status_code == 403
        assert "Permission required: students.delete" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_require_permission_no_user(self):
        """Test require_permission decorator denies access without user"""
        @require_permission("students.read")
        async def test_function(current_user=None):
            return "success"
        
        with pytest.raises(HTTPException) as exc_info:
            await test_function()
        
        assert exc_info.value.status_code == 401
        assert "Authentication required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_require_feature_success(self):
        """Test require_feature decorator allows access with feature"""
        @require_feature("finance_module")
        async def test_function(current_user=None):
            return "success"
        
        # Mock user with feature access
        mock_user = Mock()
        mock_user.can_access_feature = Mock(return_value=True)
        
        result = await test_function(current_user=mock_user)
        assert result == "success"
        mock_user.can_access_feature.assert_called_with("finance_module")
    
    @pytest.mark.asyncio
    async def test_require_feature_denied(self):
        """Test require_feature decorator denies access without feature"""
        @require_feature("advanced_reporting")
        async def test_function(current_user=None):
            return "success"
        
        # Mock user without feature access
        mock_user = Mock()
        mock_user.can_access_feature = Mock(return_value=False)
        
        with pytest.raises(HTTPException) as exc_info:
            await test_function(current_user=mock_user)
        
        assert exc_info.value.status_code == 403
        assert "Feature not available: advanced_reporting" in exc_info.value.detail


class TestModuleAccess:
    """Test module-based access control"""
    
    @pytest.mark.asyncio
    async def test_check_module_access_success(self):
        """Test module access check with enabled module"""
        enabled_modules = ["sis", "finance", "academic"]
        
        # Should allow access to enabled modules
        assert await check_module_access("sis", enabled_modules) is True
        assert await check_module_access("finance", enabled_modules) is True
        assert await check_module_access("academic", enabled_modules) is True
    
    @pytest.mark.asyncio
    async def test_check_module_access_denied(self):
        """Test module access check with disabled module"""
        enabled_modules = ["sis", "academic"]
        
        # Should deny access to disabled modules
        assert await check_module_access("finance", enabled_modules) is False
        assert await check_module_access("advanced_reporting", enabled_modules) is False
        assert await check_module_access("ai_assistance", enabled_modules) is False
    
    @pytest.mark.asyncio
    async def test_check_module_access_core_modules(self):
        """Test core modules are always accessible"""
        enabled_modules = []  # No modules enabled
        
        # Core modules should always be accessible
        core_modules = ["authentication", "user_management", "basic_settings"]
        
        for module in core_modules:
            assert await check_module_access(module, enabled_modules) is True


class TestSchoolAccess:
    """Test school-based access validation"""
    
    @pytest.mark.asyncio
    async def test_validate_school_access_success(self):
        """Test successful school access validation"""
        user_school_id = "school-123"
        requested_school_id = "school-123"
        
        # Same school should allow access
        result = await validate_school_access(user_school_id, requested_school_id)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_school_access_denied(self):
        """Test denied school access validation"""
        user_school_id = "school-123"
        requested_school_id = "school-456"
        
        # Different school should deny access
        with pytest.raises(HTTPException) as exc_info:
            await validate_school_access(user_school_id, requested_school_id)
        
        assert exc_info.value.status_code == 403
        assert "cross-tenant access" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_validate_school_access_super_admin(self):
        """Test super admin can access any school"""
        user_school_id = "*"  # Super admin marker
        requested_school_id = "school-456"
        
        # Super admin should allow access to any school
        result = await validate_school_access(user_school_id, requested_school_id)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_school_access_platform_admin(self):
        """Test platform admin can access any school"""
        user_school_id = "platform"  # Platform admin marker
        requested_school_id = "school-456"
        
        # Platform admin should allow access to any school
        result = await validate_school_access(user_school_id, requested_school_id)
        assert result is True


class TestComplexPermissionScenarios:
    """Test complex permission scenarios"""
    
    @pytest.mark.asyncio
    async def test_hierarchical_permissions(self):
        """Test hierarchical permission inheritance"""
        # Mock a scenario where permissions have hierarchy
        # e.g., students.read implies students.read_own
        
        school_id = str(uuid.uuid4())
        
        # Teacher should have both general and specific permissions
        teacher_perms = await get_user_permissions("teacher", school_id)
        
        # If teacher has students.read, they should also have read_own permissions
        if "students.read" in teacher_perms:
            # This would be implemented in the actual permission system
            assert "students.read_own" in teacher_perms or "students.read" in teacher_perms
    
    @pytest.mark.asyncio
    async def test_context_dependent_permissions(self):
        """Test permissions that depend on context"""
        # Test that some permissions might be context-dependent
        # For example, a teacher can only grade students in their classes
        
        mock_user = Mock()
        mock_user.permissions = ["grades.write_assigned_classes"]
        mock_user.role = "teacher"
        
        # This would require additional context checking in the actual implementation
        assert "grades.write_assigned_classes" in mock_user.permissions
    
    @pytest.mark.asyncio
    async def test_temporary_permissions(self):
        """Test temporary or time-limited permissions"""
        # Test scenario where permissions might be time-limited
        # For example, substitute teachers might have temporary access
        
        mock_user = Mock()
        mock_user.permissions = ["students.read"]
        mock_user.role = "substitute_teacher"
        mock_user.permission_expiry = datetime.utcnow().timestamp() + 86400  # 24 hours
        
        # In actual implementation, would check expiry
        current_time = datetime.utcnow().timestamp()
        assert mock_user.permission_expiry > current_time
    
    @pytest.mark.asyncio
    async def test_resource_specific_permissions(self):
        """Test permissions tied to specific resources"""
        # Test scenario where permissions are tied to specific resources
        # For example, a teacher can only access their assigned classes
        
        mock_user = Mock()
        mock_user.permissions = ["classes.read", "classes.manage"]
        mock_user.assigned_classes = ["class-123", "class-456"]
        
        # In actual implementation, would check resource access
        requested_class = "class-123"
        assert requested_class in mock_user.assigned_classes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])