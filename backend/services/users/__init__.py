# =====================================================
# User Management Service Module
# Complete CRUD operations for user management
# File: backend/services/users/__init__.py
# =====================================================

from .routes import router
from .services import UserManagementService
from .schemas import (
    UserCreateRequest, UserUpdateRequest, UserResponse, UserListResponse,
    UserSearchRequest, UserBulkOperationRequest, UserProfileUpdateRequest
)

__all__ = [
    "router",
    "UserManagementService",
    "UserCreateRequest",
    "UserUpdateRequest", 
    "UserResponse",
    "UserListResponse",
    "UserSearchRequest",
    "UserBulkOperationRequest",
    "UserProfileUpdateRequest"
]