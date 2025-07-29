# =====================================================
# User Management Routes
# Complete CRUD API for user management
# File: backend/services/users/routes.py
# =====================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
import logging

from shared.database import get_async_session
from shared.models.platform_user import PlatformUser, PlatformRole
from shared.auth import get_current_active_user, require_permission
from .schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserListResponse,
    UserSearchRequest,
    UserBulkOperationRequest,
    UserStatistics,
    UserProfileUpdateRequest,
    SchoolMembershipUpdateRequest,
    UserListItem,
)
from .services import UserManagementService

router = APIRouter(prefix="/api/v1/users", tags=["user-management"])
logger = logging.getLogger(__name__)

# Initialize service
user_service = UserManagementService()


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: PlatformUserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Create a new user account
    Requires admin permissions
    """
    try:
        # Check permissions
        # TODO: Implement proper permission checking
        if current_user.platform_role not in ["super_admin", "school_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create users",
            )

        # Create user
        user = await user_service.create_user(db, user_data, current_user.id)

        # Send welcome email in background if requested
        if user_data.send_welcome_email:
            background_tasks.add_task(send_welcome_email, user.email, user.first_name)

        # Convert to response format
        user_response = await _convert_user_to_response(db, user)

        logger.info(f"User created: {user.email} by {current_user.email}")
        return user_response

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: PlatformUserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get user details by ID
    Users can view their own profile, admins can view any user
    """
    try:
        # Check permissions
        if str(user_id) != str(current_user.id) and current_user.platform_role not in [
            "super_admin",
            "school_admin",
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        user = await user_service.get_user_by_id(db, user_id, include_memberships=True)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return await _convert_user_to_response(db, user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user",
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdateRequest,
    current_user: PlatformUserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update user information
    Users can update their own profile, admins can update any user
    """
    try:
        # Check permissions
        if str(user_id) != str(current_user.id) and current_user.platform_role not in [
            "super_admin",
            "school_admin",
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        # Restrict what regular users can update
        if str(user_id) == str(current_user.id) and current_user.platform_role not in [
            "super_admin",
            "school_admin",
        ]:
            # Regular users can't change their role or status
            user_data.platform_role = None
            user_data.status = None
            user_data.feature_flags = None

        user = await user_service.update_user(db, user_id, user_data, current_user.id)
        return await _convert_user_to_response(db, user)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    permanent: bool = Query(False, description="Permanently delete user"),
    current_user: PlatformUserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Delete user account
    Requires admin permissions
    """
    try:
        # Check permissions
        if current_user.platform_role not in ["super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to delete users",
            )

        # Prevent self-deletion
        if str(user_id) == str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account",
            )

        success = await user_service.delete_user(
            db, user_id, current_user.id, permanent
        )

        if success:
            return {"message": "User deleted successfully", "user_id": str(user_id)}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user",
        )


@router.post("/search", response_model=UserListResponse)
async def search_users(
    search_params: UserSearchRequest,
    current_user: PlatformUserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Search users with filters and pagination
    """
    try:
        # Check permissions
        if current_user.platform_role not in ["super_admin", "school_admin", "teacher"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        # Restrict search scope for non-admins
        if current_user.platform_role == "teacher":
            # Teachers can only see users from their schools
            # TODO: Implement school membership check
            pass

        users, total_count = await user_service.search_users(db, search_params)

        # Convert to list items
        user_items = []
        for user in users:
            user_items.append(
                UserListItem(
                    id=str(user.id),
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    full_name=f"{user.first_name} {user.last_name}",
                    platform_role=PlatformRole(user.platform_role),
                    status=user.status,
                    primary_school_name=None,  # TODO: Get school name
                    created_at=user.created_at.isoformat(),
                    last_login=user.last_login.isoformat() if user.last_login else None,
                    profile_image_url=(
                        user.profile.get("profile_image_url") if user.profile else None
                    ),
                )
            )

        return UserListResponse(
            users=user_items,
            total=total_count,
            limit=search_params.limit,
            offset=search_params.offset,
            filters_applied={
                "query": search_params.query,
                "platform_role": (
                    search_params.platform_role.value
                    if search_params.platform_role
                    else None
                ),
                "status": search_params.status.value,
                "school_id": (
                    str(search_params.school_id) if search_params.school_id else None
                ),
            },
            sort_by=search_params.sort_by,
            sort_desc=search_params.sort_desc,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search users",
        )


@router.post("/bulk-operation")
async def bulk_operation(
    operation_data: UserBulkOperationRequest,
    current_user: PlatformUserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Perform bulk operations on multiple users
    Requires admin permissions
    """
    try:
        # Check permissions
        if current_user.platform_role not in ["super_admin", "school_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for bulk operations",
            )

        results = await user_service.bulk_operation(db, operation_data, current_user.id)

        return {
            "message": f"Bulk operation {operation_data.operation} completed",
            "results": results,
        }

    except Exception as e:
        logger.error(f"Error in bulk operation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk operation failed",
        )


@router.get("/statistics/overview", response_model=UserStatistics)
async def get_user_statistics(
    school_id: Optional[UUID] = Query(None, description="Filter by school"),
    current_user: PlatformUserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get user statistics for dashboard
    """
    try:
        # Check permissions
        if current_user.platform_role not in ["super_admin", "school_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        statistics = await user_service.get_user_statistics(db, school_id)
        return statistics

    except Exception as e:
        logger.error(f"Error getting user statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics",
        )


@router.put("/{user_id}/profile", response_model=UserResponse)
async def update_user_profile(
    user_id: UUID,
    profile_data: UserProfileUpdateRequest,
    current_user: PlatformUserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update user profile information
    """
    try:
        # Check permissions - users can update their own profile
        if str(user_id) != str(current_user.id) and current_user.platform_role not in [
            "super_admin",
            "school_admin",
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        # Convert profile update to general user update
        user_update = UserUpdateRequest(
            phone=profile_data.phone,
            date_of_birth=profile_data.date_of_birth,
            gender=profile_data.gender,
            address=profile_data.address,
            emergency_contact_name=profile_data.emergency_contact_name,
            emergency_contact_phone=profile_data.emergency_contact_phone,
            preferred_language=profile_data.preferred_language,
            timezone=profile_data.timezone,
            notification_preferences=profile_data.notification_preferences,
        )

        user = await user_service.update_user(db, user_id, user_update, current_user.id)
        return await _convert_user_to_response(db, user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile",
        )


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: UUID,
    send_email: bool = Query(True, description="Send password reset email"),
    current_user: PlatformUserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Reset user password
    Requires admin permissions or self-service
    """
    try:
        # Check permissions
        if str(user_id) != str(current_user.id) and current_user.platform_role not in [
            "super_admin",
            "school_admin",
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        user = await user_service.get_user_by_id(db, user_id, include_memberships=False)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Generate reset token (placeholder implementation)
        reset_token = "temp_reset_token_123"

        # TODO: Implement actual password reset logic
        # - Generate secure reset token
        # - Store token with expiration
        # - Send email if requested

        return {
            "message": "Password reset initiated",
            "user_id": str(user_id),
            "reset_token": reset_token if not send_email else None,
            "email_sent": send_email,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password",
        )


@router.get("/{user_id}/sessions")
async def get_user_sessions(
    user_id: UUID,
    current_user: PlatformUserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get active sessions for a user
    """
    try:
        # Check permissions
        if str(user_id) != str(current_user.id) and current_user.platform_role not in [
            "super_admin",
            "school_admin",
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        # TODO: Implement session listing
        return {"user_id": str(user_id), "sessions": [], "active_sessions": 0}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sessions for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user sessions",
        )


async def _convert_user_to_response(
    db: AsyncSession, user: PlatformUserDB
) -> UserResponse:
    """Convert database user model to API response"""

    # Convert school memberships
    school_memberships = []
    for membership in user.school_memberships or []:
        school_memberships.append(
            {
                "school_id": str(membership.school_id),
                "school_name": membership.school_name,
                "school_subdomain": membership.school_subdomain,
                "role": membership.role,
                "permissions": membership.permissions or [],
                "status": membership.status,
                "joined_date": membership.joined_date.isoformat(),
                "department": membership.department,
                "employee_id": membership.employee_id,
                "student_id": membership.student_id,
                "current_grade": membership.current_grade,
            }
        )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=f"{user.first_name} {user.last_name}",
        platform_role=PlatformRole(user.platform_role),
        status=user.status,
        profile=user.profile,
        school_memberships=school_memberships,
        primary_school_id=(
            str(user.primary_school_id) if user.primary_school_id else None
        ),
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat(),
        last_login=user.last_login.isoformat() if user.last_login else None,
        feature_flags=user.feature_flags or {},
        user_preferences=user.user_preferences or {},
        is_active=user.status == "active",
        has_multiple_schools=len(school_memberships) > 1,
        profile_completion_percentage=None,  # TODO: Calculate profile completion
    )


async def send_welcome_email(email: str, first_name: str):
    """Send welcome email to new user (background task)"""
    # TODO: Implement email sending
    logger.info(f"Sending welcome email to {email} ({first_name})")
    pass
