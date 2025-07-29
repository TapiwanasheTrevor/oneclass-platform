# =====================================================
# User Management Schemas
# Pydantic models for user management operations
# File: backend/services/users/schemas.py
# =====================================================

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from uuid import UUID
from enum import Enum

from shared.models.platform_user import PlatformRole, SchoolRole, UserStatus

class UserSortBy(str, Enum):
    """User sorting options"""
    CREATED_AT = "created_at"
    LAST_LOGIN = "last_login"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    EMAIL = "email"
    PLATFORM_ROLE = "platform_role"

class UserFilterBy(str, Enum):
    """User filtering options"""
    ALL = "all"
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"

class BulkOperation(str, Enum):
    """Bulk operation types"""
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    SUSPEND = "suspend"
    DELETE = "delete"
    UPDATE_ROLE = "update_role"
    SEND_INVITATION = "send_invitation"

class UserCreateRequest(BaseModel):
    """Request to create a new user"""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    platform_role: PlatformRole = PlatformRole.STUDENT
    
    # Optional profile information
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    
    # School membership (optional - can be added later)
    school_memberships: List[Dict[str, Any]] = Field(default_factory=list)
    primary_school_id: Optional[UUID] = None
    
    # Initial password (optional - will trigger password reset if not provided)
    initial_password: Optional[str] = Field(None, min_length=8)
    
    # Notification preferences
    send_welcome_email: bool = True
    send_credentials_email: bool = True
    
    @validator('email')
    def email_must_be_lowercase(cls, v):
        return v.lower()

class UserUpdateRequest(BaseModel):
    """Request to update user information"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    platform_role: Optional[PlatformRole] = None
    status: Optional[UserStatus] = None
    
    # Profile updates
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    
    # Preferences
    preferred_language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    notification_preferences: Optional[Dict[str, bool]] = None
    
    # Administrative
    primary_school_id: Optional[UUID] = None
    feature_flags: Optional[Dict[str, bool]] = None
    user_preferences: Optional[Dict[str, Any]] = None

class UserProfileUpdateRequest(BaseModel):
    """Request to update user profile only"""
    phone: Optional[str] = Field(None, max_length=20)
    profile_image_url: Optional[str] = Field(None, max_length=500)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = Field(None, max_length=1000)
    preferred_language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    notification_preferences: Optional[Dict[str, bool]] = None

class SchoolMembershipUpdateRequest(BaseModel):
    """Request to update school membership"""
    school_role: Optional[SchoolRole] = None
    permissions: Optional[List[str]] = None
    status: Optional[UserStatus] = None
    department: Optional[str] = Field(None, max_length=100)
    employee_id: Optional[str] = Field(None, max_length=50)
    student_id: Optional[str] = Field(None, max_length=50)
    current_grade: Optional[str] = Field(None, max_length=20)
    hire_date: Optional[date] = None
    contract_type: Optional[str] = Field(None, max_length=50)
    children_ids: Optional[List[UUID]] = None

class UserSearchRequest(BaseModel):
    """Request for user search with filters"""
    query: Optional[str] = Field(None, max_length=255)
    school_id: Optional[UUID] = None
    platform_role: Optional[PlatformRole] = None
    school_role: Optional[SchoolRole] = None
    status: Optional[UserFilterBy] = UserFilterBy.ALL
    department: Optional[str] = None
    grade: Optional[str] = None
    
    # Date filters
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    last_login_after: Optional[datetime] = None
    last_login_before: Optional[datetime] = None
    
    # Sorting and pagination
    sort_by: UserSortBy = UserSortBy.CREATED_AT
    sort_desc: bool = True
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    
    # Advanced filters
    has_profile_image: Optional[bool] = None
    has_phone: Optional[bool] = None
    email_verified: Optional[bool] = None
    multiple_schools: Optional[bool] = None

class UserBulkOperationRequest(BaseModel):
    """Request for bulk operations on users"""
    user_ids: List[UUID] = Field(..., min_items=1, max_items=100)
    operation: BulkOperation
    
    # Operation-specific parameters
    new_status: Optional[UserStatus] = None
    new_role: Optional[PlatformRole] = None
    school_id: Optional[UUID] = None  # For school-specific operations
    reason: Optional[str] = Field(None, max_length=500)
    
    # Notification settings
    send_notification: bool = True
    notification_message: Optional[str] = Field(None, max_length=1000)

class UserResponse(BaseModel):
    """User response with full details"""
    id: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    platform_role: PlatformRole
    status: UserStatus
    
    # Profile information
    profile: Optional[Dict[str, Any]] = None
    
    # School memberships
    school_memberships: List[Dict[str, Any]] = Field(default_factory=list)
    primary_school_id: Optional[str] = None
    
    # System information
    created_at: str
    updated_at: str
    last_login: Optional[str] = None
    
    # Feature flags and preferences
    feature_flags: Dict[str, bool] = Field(default_factory=dict)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    
    # Computed fields
    is_active: bool
    has_multiple_schools: bool
    profile_completion_percentage: Optional[float] = None

class UserListItem(BaseModel):
    """Simplified user information for lists"""
    id: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    platform_role: PlatformRole
    status: UserStatus
    primary_school_name: Optional[str] = None
    created_at: str
    last_login: Optional[str] = None
    profile_image_url: Optional[str] = None

class UserListResponse(BaseModel):
    """Response for user list with pagination"""
    users: List[UserListItem]
    total: int
    limit: int
    offset: int
    filters_applied: Dict[str, Any]
    sort_by: UserSortBy
    sort_desc: bool

class UserStatistics(BaseModel):
    """User statistics for dashboard"""
    total_users: int
    active_users: int
    inactive_users: int
    pending_users: int
    suspended_users: int
    
    # By role
    users_by_role: Dict[str, int]
    users_by_school: Dict[str, int]
    
    # Recent activity
    new_users_last_30_days: int
    active_users_last_7_days: int
    users_never_logged_in: int
    
    # Profile completion
    users_with_complete_profiles: int
    average_profile_completion: float

class UserActivityLog(BaseModel):
    """User activity log entry"""
    id: str
    user_id: str
    action: str
    description: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    school_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str

class UserExportRequest(BaseModel):
    """Request to export user data"""
    format: str = Field(..., pattern="^(csv|excel|json)$")
    filters: Optional[UserSearchRequest] = None
    include_profile: bool = True
    include_memberships: bool = True
    include_activity: bool = False
    
class UserImportResult(BaseModel):
    """Result of user import operation"""
    import_id: str
    total_records: int
    successful_imports: int
    failed_imports: int
    warnings: List[str] = Field(default_factory=list)
    errors: List[Dict[str, str]] = Field(default_factory=list)
    imported_user_ids: List[str] = Field(default_factory=list)

class PasswordResetRequest(BaseModel):
    """Request to reset user password"""
    user_id: UUID
    send_email: bool = True
    temporary_password: Optional[str] = None
    force_change_on_login: bool = True

class UserSessionInfo(BaseModel):
    """User session information"""
    session_id: str
    user_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Dict[str, Any] = Field(default_factory=dict)
    current_school_id: Optional[str] = None
    is_active: bool
    created_at: str
    last_activity: str
    expires_at: str

class UserPermissionCheck(BaseModel):
    """Request to check user permissions"""
    user_id: UUID
    permission: str
    school_id: Optional[UUID] = None
    resource_id: Optional[UUID] = None

class UserAuditLog(BaseModel):
    """User audit log entry"""
    id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    performed_by: str
    ip_address: Optional[str] = None
    timestamp: str
    school_id: Optional[str] = None