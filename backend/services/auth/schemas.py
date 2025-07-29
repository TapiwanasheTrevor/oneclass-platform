# =====================================================
# Authentication Service Schemas
# Pydantic models for authentication requests and responses
# File: backend/services/auth/schemas.py
# =====================================================

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from shared.models.platform_user import PlatformRole, SchoolRole, UserStatus

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str
    user: Dict[str, Any]

class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = None

class UserRegistrationRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    platform_role: PlatformRole = PlatformRole.STUDENT
    phone: Optional[str] = Field(None, max_length=20)
    
    @validator('email')
    def email_must_be_lowercase(cls, v):
        return v.lower()

class PasswordResetRequest(BaseModel):
    email: EmailStr
    
class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)

class SchoolMembershipData(BaseModel):
    school_id: str
    school_name: str
    role: SchoolRole
    department: Optional[str] = None
    employee_id: Optional[str] = None
    student_id: Optional[str] = None
    current_grade: Optional[str] = None
    children_ids: Optional[List[str]] = None

class OnboardingCompleteRequest(BaseModel):
    # Basic user info
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = Field(None, pattern="^(male|female|other|prefer_not_to_say)$")
    address: Optional[str] = Field(None, max_length=500)
    
    # Onboarding context
    invitation_type: str = Field(..., pattern="^(new_user|existing_user|bulk_import|self_signup)$")
    source_school_id: Optional[str] = None
    source_school_name: Optional[str] = None
    invitation_token: Optional[str] = None
    
    # Role and school info
    primary_role: PlatformRole
    school_memberships: List[SchoolMembershipData]
    
    # Role-specific data
    teaching_subjects: Optional[List[str]] = None
    qualifications: Optional[List[str]] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    
    # Parent-specific
    children_info: Optional[List[Dict[str, str]]] = None
    
    # Student-specific
    previous_school: Optional[str] = Field(None, max_length=200)
    transfer_reason: Optional[str] = Field(None, max_length=500)
    medical_info: Optional[str] = Field(None, max_length=1000)
    
    # Preferences
    preferred_language: str = Field(default="en", pattern="^(en|sn|nd)$")
    timezone: str = Field(default="Africa/Harare")
    notification_preferences: Dict[str, bool] = Field(default_factory=lambda: {
        "email_notifications": True,
        "sms_notifications": True,
        "push_notifications": True,
        "marketing_emails": False
    })
    
    # Password for new users
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    
    @validator('email')
    def email_must_be_lowercase(cls, v):
        return v.lower()

class UserProfileData(BaseModel):
    phone_number: Optional[str] = None
    profile_image_url: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    bio: Optional[str] = None
    preferred_language: str = "en"
    timezone: str = "Africa/Harare"
    notification_preferences: Dict[str, bool]

class SchoolMembershipResponse(BaseModel):
    school_id: str
    school_name: str
    school_subdomain: str
    role: str
    permissions: List[str]
    joined_date: str
    status: str
    student_id: Optional[str] = None
    current_grade: Optional[str] = None
    admission_date: Optional[str] = None
    graduation_date: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    hire_date: Optional[str] = None
    contract_type: Optional[str] = None
    children_ids: List[str] = []

class UserContextResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    platform_role: str
    status: str
    primary_school_id: Optional[str] = None
    school_memberships: List[SchoolMembershipResponse]
    profile: Optional[UserProfileData] = None
    created_at: str
    last_login: Optional[str] = None
    feature_flags: Dict[str, bool]
    user_preferences: Dict[str, Any]

class TokenData(BaseModel):
    user_id: str
    email: str
    session_id: str
    school_id: Optional[str] = None
    platform_role: str
    school_role: Optional[str] = None

class SessionInfo(BaseModel):
    id: str
    user_id: str
    school_id: Optional[str]
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    is_active: bool

# Error response schemas
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    
class ValidationErrorResponse(BaseModel):
    detail: str
    errors: List[Dict[str, Any]]