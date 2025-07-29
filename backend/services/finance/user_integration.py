# =====================================================
# Finance Service User Integration
# Integration layer for finance service with consolidated user system
# File: backend/services/finance/user_integration.py
# =====================================================

from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import HTTPException, status, Depends

from shared.models.platform_user import PlatformUser, PlatformRole, SchoolRole
from shared.auth import get_current_active_user
from shared.services.api_integration_service import APIIntegrationService


class FinanceUserIntegration:
    """
    Integration service for finance operations with the consolidated user system
    Handles user context, permissions, and school access for finance operations
    """
    
    def __init__(self, api_service: APIIntegrationService):
        self.api_service = api_service
    
    def check_finance_access(self, user: PlatformUser, school_id: Optional[UUID] = None) -> bool:
        """Check if user has access to finance features"""
        # Super admin always has access
        if user.platform_role == PlatformRole.SUPER_ADMIN:
            return True
        
        # Check if user has finance permissions in the school
        target_school_id = school_id or user.primary_school_id
        if not target_school_id:
            return False
        
        return user.has_permission_in_school("finance.read", target_school_id)
    
    def check_finance_management_access(self, user: PlatformUser, school_id: Optional[UUID] = None) -> bool:
        """Check if user can manage finance settings"""
        # Super admin always has access
        if user.platform_role == PlatformRole.SUPER_ADMIN:
            return True
        
        target_school_id = school_id or user.primary_school_id
        if not target_school_id:
            return False
        
        # School admins and bursars can manage finance
        return (
            user.has_role_in_school(SchoolRole.PRINCIPAL, target_school_id) or
            user.has_role_in_school(SchoolRole.BURSAR, target_school_id) or
            user.has_permission_in_school("finance.manage", target_school_id)
        )
    
    def check_payment_processing_access(self, user: PlatformUser, school_id: Optional[UUID] = None) -> bool:
        """Check if user can process payments"""
        target_school_id = school_id or user.primary_school_id
        if not target_school_id:
            return False
        
        # Super admin, school admin, and bursar can process payments
        return (
            user.platform_role == PlatformRole.SUPER_ADMIN or
            user.has_role_in_school(SchoolRole.PRINCIPAL, target_school_id) or
            user.has_role_in_school(SchoolRole.BURSAR, target_school_id) or
            user.has_permission_in_school("payments.process", target_school_id)
        )
    
    def check_financial_reporting_access(self, user: PlatformUser, school_id: Optional[UUID] = None) -> bool:
        """Check if user can access financial reports"""
        target_school_id = school_id or user.primary_school_id
        if not target_school_id:
            return False
        
        return (
            user.platform_role == PlatformRole.SUPER_ADMIN or
            user.has_role_in_school(SchoolRole.PRINCIPAL, target_school_id) or
            user.has_role_in_school(SchoolRole.BURSAR, target_school_id) or
            user.has_permission_in_school("reports.financial", target_school_id)
        )
    
    def get_accessible_schools_for_finance(self, user: PlatformUser) -> List[UUID]:
        """Get list of schools where user has finance access"""
        if user.platform_role == PlatformRole.SUPER_ADMIN:
            # Super admin can access all schools - would need to fetch from database
            return []  # Implementation would fetch all school IDs
        
        accessible_schools = []
        for membership in user.school_memberships:
            if self.check_finance_access(user, membership.school_id):
                accessible_schools.append(membership.school_id)
        
        return accessible_schools
    
    def validate_school_finance_access(self, user: PlatformUser, school_id: UUID) -> None:
        """Validate user has finance access to specific school"""
        if not self.check_finance_access(user, school_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to finance features for this school"
            )
    
    def validate_finance_management_access(self, user: PlatformUser, school_id: UUID) -> None:
        """Validate user can manage finance for specific school"""
        if not self.check_finance_management_access(user, school_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to manage finance settings"
            )
    
    def get_user_finance_context(self, user: PlatformUser, school_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get user's finance context for the school"""
        target_school_id = school_id or user.primary_school_id
        
        if not target_school_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No school context available"
            )
        
        membership = user.get_school_membership(target_school_id)
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No access to specified school"
            )
        
        return {
            "user_id": user.id,
            "school_id": target_school_id,
            "school_name": membership.school_name,
            "user_role": membership.role.value,
            "permissions": membership.permissions,
            "can_read_finance": self.check_finance_access(user, target_school_id),
            "can_manage_finance": self.check_finance_management_access(user, target_school_id),
            "can_process_payments": self.check_payment_processing_access(user, target_school_id),
            "can_view_reports": self.check_financial_reporting_access(user, target_school_id)
        }


# Dependency functions for FastAPI

async def get_finance_user_integration() -> FinanceUserIntegration:
    """Dependency to get finance user integration service"""
    # This would be properly configured with DI container
    api_service = APIIntegrationService(None, None)  # Would be injected
    return FinanceUserIntegration(api_service)


async def get_current_finance_user(
    current_user: PlatformUser = Depends(get_current_active_user),
    finance_integration: FinanceUserIntegration = Depends(get_finance_user_integration)
) -> PlatformUser:
    """Get current user with finance access validation"""
    if not finance_integration.check_finance_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to finance features"
        )
    return current_user


async def get_current_finance_manager(
    current_user: PlatformUser = Depends(get_current_active_user),
    finance_integration: FinanceUserIntegration = Depends(get_finance_user_integration)
) -> PlatformUser:
    """Get current user with finance management access validation"""
    if not finance_integration.check_finance_management_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to manage finance"
        )
    return current_user


async def get_finance_context_for_school(
    school_id: UUID,
    current_user: PlatformUser = Depends(get_current_active_user),
    finance_integration: FinanceUserIntegration = Depends(get_finance_user_integration)
) -> Dict[str, Any]:
    """Get finance context for specific school"""
    finance_integration.validate_school_finance_access(current_user, school_id)
    return finance_integration.get_user_finance_context(current_user, school_id)


# Permission decorators for finance operations

def require_finance_access(func):
    """Decorator to require finance access"""
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')
        if not current_user or not isinstance(current_user, PlatformUser):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        finance_integration = FinanceUserIntegration(None)  # Would be injected
        if not finance_integration.check_finance_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to finance features"
            )
        
        return await func(*args, **kwargs)
    return wrapper


def require_finance_management(func):
    """Decorator to require finance management access"""
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')
        if not current_user or not isinstance(current_user, PlatformUser):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        finance_integration = FinanceUserIntegration(None)  # Would be injected
        if not finance_integration.check_finance_management_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to manage finance"
            )
        
        return await func(*args, **kwargs)
    return wrapper


def require_payment_processing(func):
    """Decorator to require payment processing access"""
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')
        if not current_user or not isinstance(current_user, PlatformUser):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        finance_integration = FinanceUserIntegration(None)  # Would be injected
        if not finance_integration.check_payment_processing_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to process payments"
            )
        
        return await func(*args, **kwargs)
    return wrapper


# Helper functions for finance operations

def get_user_payment_context(user: PlatformUser, school_id: Optional[UUID] = None) -> Dict[str, Any]:
    """Get user context for payment operations"""
    target_school_id = school_id or user.primary_school_id
    
    if not target_school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No school context for payment"
        )
    
    membership = user.get_school_membership(target_school_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access to school for payment"
        )
    
    return {
        "payer_id": user.id,
        "payer_email": user.email,
        "payer_name": user.full_name,
        "school_id": target_school_id,
        "school_name": membership.school_name,
        "user_role": membership.role.value,
        "student_id": membership.student_id if membership.role == SchoolRole.STUDENT else None,
        "children_ids": membership.children_ids if membership.role == SchoolRole.PARENT else None
    }


def filter_financial_data_by_access(user: PlatformUser, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter financial data based on user's access level"""
    if user.platform_role == PlatformRole.SUPER_ADMIN:
        return data  # Super admin sees everything
    
    # Filter based on schools user has access to
    accessible_schools = set()
    for membership in user.school_memberships:
        finance_integration = FinanceUserIntegration(None)
        if finance_integration.check_finance_access(user, membership.school_id):
            accessible_schools.add(str(membership.school_id))
    
    return [
        item for item in data 
        if item.get('school_id') in accessible_schools
    ]