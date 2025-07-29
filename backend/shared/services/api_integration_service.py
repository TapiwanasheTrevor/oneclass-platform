# =====================================================
# API Endpoints Integration Service
# Provides consistent user context and permission handling across all API endpoints
# File: backend/shared/services/api_integration_service.py
# =====================================================

from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from fastapi import HTTPException, status, Depends, Request
from functools import wraps

# Our imports
from shared.models.platform_user import PlatformUser, PlatformRole, SchoolRole, UserStatus
from shared.auth import get_current_active_user
from shared.middleware.fast_user_context_middleware import (
    get_current_user_fast, get_current_user_minimal, MinimalUserContext
)
from shared.services.optimized_user_service import OptimizedUserService
from shared.cache.user_context_cache import UserContextCache


class APIIntegrationService:
    """
    Service to handle API endpoint integration with the new consolidated user model
    Provides consistent user context, permission checking, and role validation
    """
    
    def __init__(self, user_service: OptimizedUserService, cache: UserContextCache):
        self.user_service = user_service
        self.cache = cache
    
    # Permission Checking Methods
    
    def check_platform_role(self, user: PlatformUser, required_role: PlatformRole) -> bool:
        """Check if user has required platform role"""
        # Super admin can access everything
        if user.platform_role == PlatformRole.SUPER_ADMIN:
            return True
        
        return user.platform_role == required_role
    
    def check_school_role(self, user: PlatformUser, school_id: UUID, required_role: SchoolRole) -> bool:
        """Check if user has required school role"""
        # Super admin can access everything
        if user.platform_role == PlatformRole.SUPER_ADMIN:
            return True
        
        return user.has_role_in_school(required_role, school_id)
    
    def check_permission(self, user: PlatformUser, permission: str, school_id: Optional[UUID] = None) -> bool:
        """Check if user has specific permission"""
        # Super admin has all permissions
        if user.platform_role == PlatformRole.SUPER_ADMIN:
            return True
        
        # Check school-specific permission
        if school_id:
            return user.has_permission_in_school(permission, school_id)
        
        # Check if user has permission in any school
        for membership in user.school_memberships:
            if permission in membership.permissions or "*" in membership.permissions:
                return True
        
        return False
    
    def check_school_access(self, user: PlatformUser, school_id: UUID) -> bool:
        """Check if user can access specific school"""
        return user.can_access_school(school_id)
    
    def check_user_access(self, current_user: PlatformUser, target_user_id: UUID, school_id: Optional[UUID] = None) -> bool:
        """Check if current user can access target user's data"""
        # Users can always access their own data
        if current_user.id == target_user_id:
            return True
        
        # Super admin can access all users
        if current_user.platform_role == PlatformRole.SUPER_ADMIN:
            return True
        
        # School admins can access users in their schools
        if school_id and current_user.has_role_in_school(SchoolRole.PRINCIPAL, school_id):
            return True
        
        return False
    
    # Context Resolution Methods
    
    async def get_user_context_for_endpoint(self, request: Request, minimal: bool = False) -> Optional[Union[PlatformUser, MinimalUserContext]]:
        """Get appropriate user context for API endpoint"""
        if minimal:
            return await get_current_user_minimal(request)
        else:
            return await get_current_user_fast(request)
    
    async def resolve_school_context(self, user: PlatformUser, school_id: Optional[UUID] = None) -> Optional[UUID]:
        """Resolve school context for user"""
        if school_id:
            # Verify user has access to specified school
            if user.can_access_school(school_id):
                return school_id
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to specified school"
                )
        
        # Use primary school if no school specified
        return user.primary_school_id
    
    # Response Transformation Methods
    
    def transform_user_for_response(self, user: PlatformUser, requesting_user: PlatformUser) -> Dict[str, Any]:
        """Transform PlatformUser for API response based on requesting user's permissions"""
        # Base user data
        user_data = {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "status": user.status.value,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
        
        # Add role information based on permissions
        if requesting_user.platform_role == PlatformRole.SUPER_ADMIN:
            # Super admin sees everything
            user_data.update({
                "platform_role": user.platform_role.value,
                "primary_school_id": str(user.primary_school_id) if user.primary_school_id else None,
                "school_memberships": [
                    {
                        "school_id": str(membership.school_id),
                        "school_name": membership.school_name,
                        "role": membership.role.value,
                        "joined_date": membership.joined_date.isoformat(),
                        "status": membership.status.value
                    }
                    for membership in user.school_memberships
                ]
            })
        else:
            # Limited view for non-admin users
            # Only show schools where requesting user has admin access
            accessible_memberships = []
            for membership in user.school_memberships:
                if requesting_user.has_role_in_school(SchoolRole.PRINCIPAL, membership.school_id):
                    accessible_memberships.append({
                        "school_id": str(membership.school_id),
                        "school_name": membership.school_name,
                        "role": membership.role.value,
                        "joined_date": membership.joined_date.isoformat(),
                        "status": membership.status.value
                    })
            
            user_data["school_memberships"] = accessible_memberships
        
        # Add profile data if available and permitted
        if user.profile and (requesting_user.id == user.id or requesting_user.platform_role == PlatformRole.SUPER_ADMIN):
            user_data["profile"] = {
                "phone_number": user.profile.phone_number,
                "profile_image_url": user.profile.profile_image_url,
                "preferred_language": user.profile.preferred_language,
                "timezone": user.profile.timezone
            }
        
        return user_data
    
    # Error Handling Methods
    
    def permission_denied_error(self, message: str = "Insufficient permissions") -> HTTPException:
        """Create standardized permission denied error"""
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message
        )
    
    def user_not_found_error(self, user_id: Optional[UUID] = None) -> HTTPException:
        """Create standardized user not found error"""
        detail = f"User {user_id} not found" if user_id else "User not found"
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )
    
    def school_access_denied_error(self, school_id: UUID) -> HTTPException:
        """Create standardized school access denied error"""
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to school {school_id}"
        )


# Dependency functions for FastAPI endpoints

async def get_api_integration_service() -> APIIntegrationService:
    """Dependency to get API integration service"""
    # This would be properly configured with DI container
    # For now, return a placeholder
    return None


# Decorator functions for role/permission checking

def require_platform_role(required_role: PlatformRole):
    """Decorator to require specific platform role"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from function arguments
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, PlatformUser):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if current_user.platform_role != required_role and current_user.platform_role != PlatformRole.SUPER_ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Platform role {required_role.value} required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_school_role(required_role: SchoolRole, school_id_param: str = "school_id"):
    """Decorator to require specific school role"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user and school_id from function arguments
            current_user = None
            school_id = None
            
            for key, value in kwargs.items():
                if isinstance(value, PlatformUser):
                    current_user = value
                elif key == school_id_param and isinstance(value, UUID):
                    school_id = value
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not school_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="School ID required"
                )
            
            # Super admin bypasses school role check
            if current_user.platform_role == PlatformRole.SUPER_ADMIN:
                return await func(*args, **kwargs)
            
            if not current_user.has_role_in_school(required_role, school_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"School role {required_role.value} required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission(permission: str, school_id_param: Optional[str] = None):
    """Decorator to require specific permission"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user and optionally school_id from function arguments
            current_user = None
            school_id = None
            
            for key, value in kwargs.items():
                if isinstance(value, PlatformUser):
                    current_user = value
                elif school_id_param and key == school_id_param and isinstance(value, UUID):
                    school_id = value
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Super admin has all permissions
            if current_user.platform_role == PlatformRole.SUPER_ADMIN:
                return await func(*args, **kwargs)
            
            # Check permission
            has_permission = False
            if school_id:
                has_permission = current_user.has_permission_in_school(permission, school_id)
            else:
                # Check if user has permission in any school
                for membership in current_user.school_memberships:
                    if permission in membership.permissions or "*" in membership.permissions:
                        has_permission = True
                        break
            
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission {permission} required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Helper functions for common operations

async def validate_school_access(user: PlatformUser, school_id: UUID, service: APIIntegrationService) -> None:
    """Validate user has access to school"""
    if not service.check_school_access(user, school_id):
        raise service.school_access_denied_error(school_id)


async def validate_user_access(current_user: PlatformUser, target_user_id: UUID, 
                              school_id: Optional[UUID], service: APIIntegrationService) -> None:
    """Validate user can access target user's data"""
    if not service.check_user_access(current_user, target_user_id, school_id):
        raise service.permission_denied_error("Cannot access user data")


def get_safe_user_response(user: PlatformUser, requesting_user: PlatformUser, 
                          service: APIIntegrationService) -> Dict[str, Any]:
    """Get user data safe for API response"""
    return service.transform_user_for_response(user, requesting_user)


# Migration helpers for updating existing endpoints

def migrate_permission_check(old_permission_func, new_permission: str, school_id: Optional[UUID] = None):
    """Helper to migrate from old permission function to new permission check"""
    def check_permission(user: PlatformUser) -> bool:
        if user.platform_role == PlatformRole.SUPER_ADMIN:
            return True
        
        if school_id:
            return user.has_permission_in_school(new_permission, school_id)
        
        # Check any school
        for membership in user.school_memberships:
            if new_permission in membership.permissions or "*" in membership.permissions:
                return True
        
        return False
    
    return check_permission