# =====================================================
# Invitation Service Schemas
# Pydantic models for invitation requests and responses
# File: backend/services/invitations/schemas.py
# =====================================================

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from shared.models.platform_user import PlatformRole, SchoolRole
from services.auth.schemas import OnboardingCompleteRequest

class CreateInvitationRequest(BaseModel):
    email: EmailStr
    school_id: UUID
    platform_role: PlatformRole
    school_role: SchoolRole
    department: Optional[str] = Field(None, max_length=100)
    employee_id: Optional[str] = Field(None, max_length=50)
    student_id: Optional[str] = Field(None, max_length=50)
    teaching_subjects: Optional[List[str]] = None
    assigned_classes: Optional[List[str]] = None
    personal_message: Optional[str] = Field(None, max_length=500)
    
    @validator('email')
    def email_must_be_lowercase(cls, v):
        return v.lower()

class BulkInvitationData(BaseModel):
    email: EmailStr
    platform_role: PlatformRole
    school_role: SchoolRole
    department: Optional[str] = None
    employee_id: Optional[str] = None
    student_id: Optional[str] = None
    teaching_subjects: Optional[List[str]] = None
    assigned_classes: Optional[List[str]] = None
    
    @validator('email')
    def email_must_be_lowercase(cls, v):
        return v.lower()

class BulkInvitationRequest(BaseModel):
    school_id: UUID
    invitations: List[BulkInvitationData]
    personal_message: Optional[str] = Field(None, max_length=500)

class InvitationResponse(BaseModel):
    id: str
    email: str
    school_id: str
    school_name: str
    status: str
    invitation_token: str
    expires_at: str
    invitation_type: str

class InvitationDetailResponse(BaseModel):
    id: str
    email: str
    school_id: str
    school_name: str
    school_subdomain: str
    invited_role: PlatformRole
    school_role: SchoolRole
    inviter_name: str
    inviter_role: str
    created_at: str
    expires_at: str
    status: str
    invitation_type: str
    existing_user_id: Optional[str] = None
    additional_context: Dict[str, Any] = {}

class InvitationAcceptRequest(BaseModel):
    onboarding_data: Optional[OnboardingCompleteRequest] = None
    accept_terms: bool = True

class InvitationListItem(BaseModel):
    id: str
    email: str
    invited_role: PlatformRole
    school_role: SchoolRole
    status: str
    created_at: str
    expires_at: str
    invitation_type: str

class InvitationListResponse(BaseModel):
    invitations: List[InvitationListItem]
    total: int
    limit: int
    offset: int

class InvitationStatsResponse(BaseModel):
    total_sent: int
    pending: int
    accepted: int
    declined: int
    expired: int
    acceptance_rate: float

class ResendInvitationRequest(BaseModel):
    invitation_id: UUID
    new_expiry_days: Optional[int] = Field(default=7, ge=1, le=30)

class InvitationEmailTemplate(BaseModel):
    subject: str
    html_content: str
    text_content: str
    sender_name: str
    sender_email: str
    school_name: str
    school_logo_url: Optional[str] = None
    invitation_url: str
    recipient_name: Optional[str] = None
    personal_message: Optional[str] = None
    role_description: str
    expires_at: str

class BulkInvitationProgress(BaseModel):
    total_invitations: int
    processed: int
    successful: int
    failed: int
    errors: List[Dict[str, str]]
    progress_percentage: float
    
class InvitationAnalytics(BaseModel):
    period_start: str
    period_end: str
    total_invitations: int
    by_role: Dict[str, int]
    by_status: Dict[str, int]
    by_school: Dict[str, int]
    acceptance_trends: List[Dict[str, Any]]
    
class UpdateInvitationRequest(BaseModel):
    school_role: Optional[SchoolRole] = None
    department: Optional[str] = None
    employee_id: Optional[str] = None
    student_id: Optional[str] = None
    teaching_subjects: Optional[List[str]] = None
    assigned_classes: Optional[List[str]] = None
    personal_message: Optional[str] = None

class CancelInvitationRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=500)

class InvitationNotificationSettings(BaseModel):
    send_reminder_emails: bool = True
    reminder_days_before_expiry: int = Field(default=2, ge=1, le=7)
    notify_inviter_on_accept: bool = True
    notify_inviter_on_decline: bool = True
    notify_admin_on_bulk_complete: bool = True