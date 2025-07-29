"""
User Management Schemas
Pydantic schemas for user creation, invitation, and management
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, EmailStr, validator, Field
from enum import Enum


class UserRoleEnum(str, Enum):
    """Available user roles"""
    PLATFORM_ADMIN = "platform_admin"
    SCHOOL_ADMIN = "school_admin"
    REGISTRAR = "registrar"
    TEACHER = "teacher"
    PARENT = "parent"
    STUDENT = "student"
    STAFF = "staff"


class InvitationStatusEnum(str, Enum):
    """Invitation status options"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ImportStatusEnum(str, Enum):
    """Import status options"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Base user schemas
class UserBase(BaseModel):
    """Base user information"""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: UserRoleEnum
    
    class Config:
        use_enum_values = True


class UserCreate(UserBase):
    """User creation schema"""
    password: Optional[str] = Field(None, min_length=8)
    send_invitation: bool = True
    
    # Role-specific fields
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    employee_id: Optional[str] = Field(None, max_length=50)
    student_id: Optional[str] = Field(None, max_length=50)
    grade_level: Optional[str] = Field(None, max_length=10)
    
    # Additional metadata
    role_metadata: Optional[Dict[str, Any]] = {}
    permissions: Optional[List[str]] = []


class UserUpdate(BaseModel):
    """User update schema"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: Optional[UserRoleEnum] = None
    is_active: Optional[bool] = None
    
    # Profile fields
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    employee_id: Optional[str] = Field(None, max_length=50)
    student_id: Optional[str] = Field(None, max_length=50)
    grade_level: Optional[str] = Field(None, max_length=10)
    
    class Config:
        use_enum_values = True


class UserResponse(BaseModel):
    """User response schema"""
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    # Profile information
    profile: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


# User invitation schemas
class UserInvitationCreate(BaseModel):
    """User invitation creation schema"""
    email: EmailStr
    role: UserRoleEnum
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    
    # Role-specific fields
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    
    # Invitation settings
    expires_in_days: int = Field(7, ge=1, le=30)
    role_metadata: Optional[Dict[str, Any]] = {}
    permissions: Optional[List[str]] = []
    
    class Config:
        use_enum_values = True


class UserInvitationResponse(BaseModel):
    """User invitation response schema"""
    id: str
    email: str
    role: str
    first_name: Optional[str]
    last_name: Optional[str]
    status: str
    expires_at: datetime
    created_at: datetime
    inviter_name: str
    
    class Config:
        from_attributes = True


class UserInvitationAccept(BaseModel):
    """User invitation acceptance schema"""
    token: str
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    
    # Profile completion
    profile_data: Optional[Dict[str, Any]] = {}


# Bulk user import schemas
class BulkUserImportCreate(BaseModel):
    """Bulk user import creation schema"""
    import_type: str = Field(..., pattern="^(csv|excel|json)$")
    default_role: UserRoleEnum = UserRoleEnum.STUDENT
    send_invitations: bool = True
    
    class Config:
        use_enum_values = True


class BulkUserRecord(BaseModel):
    """Individual user record for bulk import"""
    email: EmailStr
    first_name: str
    last_name: str
    role: Optional[UserRoleEnum] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    employee_id: Optional[str] = None
    student_id: Optional[str] = None
    grade_level: Optional[str] = None
    
    class Config:
        use_enum_values = True


class BulkUserImportResponse(BaseModel):
    """Bulk user import response schema"""
    id: str
    file_name: str
    import_type: str
    status: str
    total_records: int
    successful_imports: int
    failed_imports: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# User role management schemas
class UserRoleCreate(BaseModel):
    """User role creation schema"""
    role_name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: List[str] = []
    inherited_roles: List[str] = []
    parent_role_id: Optional[str] = None


class UserRoleUpdate(BaseModel):
    """User role update schema"""
    display_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    inherited_roles: Optional[List[str]] = None
    is_active: Optional[bool] = None


class UserRoleResponse(BaseModel):
    """User role response schema"""
    id: str
    role_name: str
    display_name: str
    description: Optional[str]
    permissions: List[str]
    inherited_roles: List[str]
    is_system_role: bool
    is_active: bool
    level: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# User profile schemas
class UserProfileUpdate(BaseModel):
    """User profile update schema"""
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)
    
    # Staff-specific fields
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    hire_date: Optional[datetime] = None
    qualifications: Optional[List[Dict[str, Any]]] = []
    
    # Student-specific fields
    grade_level: Optional[str] = Field(None, max_length=10)
    enrollment_date: Optional[datetime] = None
    parent_guardian_info: Optional[Dict[str, Any]] = {}
    academic_info: Optional[Dict[str, Any]] = {}


class UserProfileResponse(BaseModel):
    """User profile response schema"""
    id: str
    user_id: str
    employee_id: Optional[str]
    student_id: Optional[str]
    national_id: Optional[str]
    address: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    emergency_contact_relationship: Optional[str]
    department: Optional[str]
    position: Optional[str]
    hire_date: Optional[datetime]
    grade_level: Optional[str]
    enrollment_date: Optional[datetime]
    profile_completed: bool
    completion_percentage: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Search and filter schemas
class UserSearchFilter(BaseModel):
    """User search and filter schema"""
    query: Optional[str] = None
    role: Optional[UserRoleEnum] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    
    # Pagination
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    
    class Config:
        use_enum_values = True


class UserListResponse(BaseModel):
    """User list response schema"""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    class Config:
        from_attributes = True


# Role-specific schemas
class TeacherCreate(UserBase):
    """Teacher-specific creation schema"""
    role: UserRoleEnum = UserRoleEnum.TEACHER
    department: str = Field(..., max_length=100)
    position: str = Field(..., max_length=100)
    employee_id: Optional[str] = Field(None, max_length=50)
    qualifications: Optional[List[Dict[str, Any]]] = []
    hire_date: Optional[datetime] = None


class StudentCreate(UserBase):
    """Student-specific creation schema"""
    role: UserRoleEnum = UserRoleEnum.STUDENT
    student_id: str = Field(..., max_length=50)
    grade_level: str = Field(..., max_length=10)
    enrollment_date: Optional[datetime] = None
    parent_guardian_info: Optional[Dict[str, Any]] = {}


class ParentCreate(UserBase):
    """Parent-specific creation schema"""
    role: UserRoleEnum = UserRoleEnum.PARENT
    children_ids: List[str] = []  # Student IDs
    relationship: str = Field(..., max_length=50)  # mother, father, guardian, etc.


class StaffCreate(UserBase):
    """Staff-specific creation schema"""
    role: UserRoleEnum = UserRoleEnum.STAFF
    department: str = Field(..., max_length=100)
    position: str = Field(..., max_length=100)
    employee_id: Optional[str] = Field(None, max_length=50)
    hire_date: Optional[datetime] = None