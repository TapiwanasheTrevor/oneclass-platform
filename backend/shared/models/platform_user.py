"""
Platform User Models
Single user model supporting multi-school memberships and role management.
Clerk handles authentication identity; this model handles school context and roles.

Table: platform.users
"""

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, JSON, Integer,
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
import uuid

from pydantic import BaseModel, Field, validator

from shared.database import Base


# =====================================================
# ENUMS
# =====================================================

class GlobalRole(str, Enum):
    """Platform-level roles that transcend schools"""
    SUPER_ADMIN = "super_admin"
    PLATFORM_ADMIN = "platform_admin"
    REGIONAL_ADMIN = "regional_admin"
    EDUCATION_OFFICER = "education_officer"
    SYSTEM_USER = "system_user"


# Keep PlatformRole as alias for backward compat in imports
PlatformRole = GlobalRole


class SchoolRole(str, Enum):
    """School-specific roles assigned per membership"""
    # Administrative
    PRINCIPAL = "principal"
    DEPUTY_PRINCIPAL = "deputy_principal"
    SCHOOL_ADMIN = "school_admin"
    # Academic leadership
    ACADEMIC_HEAD = "academic_head"
    DEPARTMENT_HEAD = "department_head"
    FORM_TEACHER = "form_teacher"
    # Teaching staff
    TEACHER = "teacher"
    SUBSTITUTE_TEACHER = "substitute_teacher"
    TRAINEE_TEACHER = "trainee_teacher"
    # Support staff
    REGISTRAR = "registrar"
    BURSAR = "bursar"
    LIBRARIAN = "librarian"
    IT_SUPPORT = "it_support"
    SECURITY = "security"
    MAINTENANCE = "maintenance"
    # Students and families
    STUDENT = "student"
    PARENT = "parent"
    GUARDIAN = "guardian"


class MembershipStatus(str, Enum):
    """School membership status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_APPROVAL = "pending_approval"
    GRADUATED = "graduated"
    TRANSFERRED = "transferred"
    EXPELLED = "expelled"
    ARCHIVED = "archived"


class UserStatus(str, Enum):
    """Overall user account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    ARCHIVED = "archived"


# =====================================================
# PYDANTIC MODELS FOR JSON FIELDS
# =====================================================

class ContactInformation(BaseModel):
    """Contact information stored as JSON"""
    primary_phone: Optional[str] = None
    secondary_phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    personal_email: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "Zimbabwe"

    @validator('primary_phone', 'secondary_phone', 'whatsapp_number')
    def validate_zimbabwe_phone(cls, v):
        if v and not (v.startswith('+263') or v.startswith('07') or v.startswith('08')):
            raise ValueError('Phone number must be valid Zimbabwe format')
        return v


class PersonalProfile(BaseModel):
    """Personal profile information"""
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    national_id: Optional[str] = None
    passport_number: Optional[str] = None
    nationality: str = "Zimbabwean"
    languages_spoken: List[str] = Field(default_factory=lambda: ["English"])
    profile_image_url: Optional[str] = None
    bio: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class UserPreferences(BaseModel):
    """User preferences and settings"""
    language: str = "en"
    timezone: str = "Africa/Harare"
    date_format: str = "DD/MM/YYYY"
    time_format: str = "24h"
    # Notification preferences
    email_notifications: bool = True
    sms_notifications: bool = True
    push_notifications: bool = True
    whatsapp_notifications: bool = False
    # UI preferences
    theme: str = "light"
    sidebar_collapsed: bool = False
    dashboard_layout: str = "default"
    # Communication preferences
    preferred_communication_method: str = "email"
    communication_language: str = "en"


class ClerkIntegration(BaseModel):
    """Clerk integration data stored as JSON"""
    clerk_user_id: str
    last_sync: Optional[datetime] = None
    clerk_metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class UserProfile(BaseModel):
    """Simple user profile (legacy compat)"""
    phone_number: Optional[str] = None
    profile_image_url: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    bio: Optional[str] = None
    display_name: Optional[str] = None
    emergency_contact: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# =====================================================
# CORE USER MODEL
# =====================================================

class PlatformUser(Base):
    """
    The ONE user model for the entire platform.
    Clerk handles authentication; this model handles identity, profile,
    school memberships, and role management.

    One account can have roles in multiple schools.
    """

    __tablename__ = "users"
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_global_role', 'global_role'),
        Index('idx_users_status', 'status'),
        Index('idx_users_clerk_user_id', 'clerk_user_id'),
        {"schema": "platform", "extend_existing": True}
    )

    # Primary identification
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)

    # Basic information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    display_name = Column(String(200))

    # Authentication — Clerk is the source of truth
    clerk_user_id = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255))  # Fallback for dev/testing only
    oauth_provider = Column(String(50))
    oauth_provider_id = Column(String(255))

    # Platform role and status
    global_role = Column(
        String(50), nullable=False, default=GlobalRole.SYSTEM_USER.value
    )
    status = Column(
        String(50), nullable=False, default=UserStatus.ACTIVE.value
    )

    # Default school context
    primary_school_id = Column(PGUUID(as_uuid=True), nullable=True)

    # Verification and security
    is_email_verified = Column(Boolean, default=False)
    two_factor_enabled = Column(Boolean, default=False)

    # Profile and preferences (JSON fields)
    contact_information = Column(JSON, default=dict)
    personal_profile = Column(JSON, default=dict)
    user_preferences = Column(JSON, default=dict)

    # Audit fields
    last_login_at = Column(DateTime(timezone=True))
    last_activity_at = Column(DateTime(timezone=True))
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    school_memberships = relationship(
        "SchoolMembership", back_populates="user", cascade="all, delete-orphan"
    )
    user_sessions = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )

    # --- Properties ---

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def contact_info(self) -> ContactInformation:
        return ContactInformation(**(self.contact_information or {}))

    @property
    def profile(self) -> PersonalProfile:
        return PersonalProfile(**(self.personal_profile or {}))

    @property
    def preferences(self) -> UserPreferences:
        return UserPreferences(**(self.user_preferences or {}))

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE.value

    @property
    def is_platform_admin(self) -> bool:
        return self.global_role in [
            GlobalRole.SUPER_ADMIN.value, GlobalRole.PLATFORM_ADMIN.value
        ]

    # Alias for code that references platform_role
    @property
    def platform_role(self) -> str:
        return self.global_role

    @property
    def role(self) -> str:
        return self.global_role

    def get_active_memberships(self) -> List["SchoolMembership"]:
        return [
            m for m in self.school_memberships
            if m.status == MembershipStatus.ACTIVE.value
        ]

    def get_membership(self, school_id: str) -> Optional["SchoolMembership"]:
        for m in self.school_memberships:
            if str(m.school_id) == str(school_id):
                return m
        return None

    def has_school_access(self, school_id: str) -> bool:
        m = self.get_membership(school_id)
        return m is not None and m.status == MembershipStatus.ACTIVE.value

    def __repr__(self):
        return f"<PlatformUser(id={self.id}, email='{self.email}', role='{self.global_role}')>"


# Backward-compat alias so existing code importing UnifiedUser still works
UnifiedUser = PlatformUser


# =====================================================
# SCHOOL MEMBERSHIP
# =====================================================

class SchoolMembership(Base):
    """
    Links a user to a school with a specific role.
    One user can have memberships in multiple schools.
    """

    __tablename__ = "school_memberships"
    __table_args__ = (
        UniqueConstraint('user_id', 'school_id', name='uq_user_school'),
        Index('idx_school_memberships_school_role', 'school_id', 'role'),
        Index('idx_school_memberships_status', 'status'),
        Index('idx_school_memberships_user_id', 'user_id'),
        {"schema": "platform", "extend_existing": True}
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("platform.users.id", ondelete="CASCADE"),
        nullable=False
    )
    school_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Cached school info (denormalized for performance)
    school_name = Column(String(255), nullable=False)
    school_subdomain = Column(String(50), nullable=False)
    school_region = Column(String(100))

    # Role and permissions
    role = Column(String(50), nullable=False)
    status = Column(
        String(50), nullable=False, default=MembershipStatus.ACTIVE.value
    )
    permissions = Column(JSON, default=list)

    # Role-specific identifiers
    employee_id = Column(String(50))
    student_id = Column(String(50))
    registration_number = Column(String(50))

    # Academic information (students)
    current_grade = Column(String(20))
    current_class = Column(String(50))
    admission_date = Column(DateTime(timezone=True))
    graduation_date = Column(DateTime(timezone=True))
    academic_status = Column(String(50))

    # Employment information (staff)
    department = Column(String(100))
    position = Column(String(100))
    hire_date = Column(DateTime(timezone=True))
    contract_type = Column(String(50))
    employment_status = Column(String(50))

    # Family relationships (parents/guardians)
    children_ids = Column(JSON, default=list)
    relationship_type = Column(String(50))

    # Timeline
    joined_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    left_date = Column(DateTime(timezone=True))

    # Additional metadata
    role_metadata = Column(JSON, default=dict)
    membership_notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("PlatformUser", back_populates="school_memberships")

    # --- Properties ---

    @property
    def school_role(self) -> str:
        """Alias for role — used by some frontend serialization"""
        return self.role

    @property
    def is_active(self) -> bool:
        return self.status == MembershipStatus.ACTIVE.value

    @property
    def is_student(self) -> bool:
        return self.role == SchoolRole.STUDENT.value

    @property
    def is_staff(self) -> bool:
        return self.role in [
            SchoolRole.PRINCIPAL.value, SchoolRole.DEPUTY_PRINCIPAL.value,
            SchoolRole.SCHOOL_ADMIN.value, SchoolRole.ACADEMIC_HEAD.value,
            SchoolRole.DEPARTMENT_HEAD.value, SchoolRole.TEACHER.value,
            SchoolRole.FORM_TEACHER.value, SchoolRole.SUBSTITUTE_TEACHER.value,
            SchoolRole.TRAINEE_TEACHER.value, SchoolRole.REGISTRAR.value,
            SchoolRole.BURSAR.value, SchoolRole.LIBRARIAN.value,
            SchoolRole.IT_SUPPORT.value, SchoolRole.SECURITY.value,
            SchoolRole.MAINTENANCE.value,
        ]

    @property
    def is_parent_guardian(self) -> bool:
        return self.role in [SchoolRole.PARENT.value, SchoolRole.GUARDIAN.value]

    @property
    def is_teaching_staff(self) -> bool:
        return self.role in [
            SchoolRole.TEACHER.value, SchoolRole.FORM_TEACHER.value,
            SchoolRole.SUBSTITUTE_TEACHER.value, SchoolRole.TRAINEE_TEACHER.value,
        ]

    def has_permission(self, permission: str) -> bool:
        return permission in (self.permissions or [])

    def __repr__(self):
        return (
            f"<SchoolMembership(user_id={self.user_id}, "
            f"school='{self.school_name}', role='{self.role}')>"
        )


# =====================================================
# USER SESSION
# =====================================================

class UserSession(Base):
    """User session with school context tracking"""

    __tablename__ = "user_sessions"
    __table_args__ = (
        Index('idx_user_sessions_session_id', 'session_id'),
        Index('idx_user_sessions_user_school', 'user_id', 'current_school_id'),
        {"schema": "platform", "extend_existing": True}
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("platform.users.id", ondelete="CASCADE"),
        nullable=False
    )
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(500), unique=True, nullable=True)

    # Session metadata
    ip_address = Column(String(50))
    user_agent = Column(Text)
    device_info = Column(JSON, default=dict)

    # Multi-school session context
    current_school_id = Column(PGUUID(as_uuid=True))
    available_school_ids = Column(JSON, default=list)
    school_switch_count = Column(Integer, default=0)

    # Status
    is_active = Column(Boolean, default=True)
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    last_school_switch_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    user = relationship("PlatformUser", back_populates="user_sessions")

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        return self.is_active and not self.is_expired

    def switch_school(self, school_id: str):
        available = self.available_school_ids or []
        if school_id in available:
            self.current_school_id = school_id
            self.school_switch_count = (self.school_switch_count or 0) + 1
            self.last_school_switch_at = datetime.now(timezone.utc)

    def __repr__(self):
        return (
            f"<UserSession(user_id={self.user_id}, "
            f"session='{str(self.session_id)[:8]}...', "
            f"school={self.current_school_id})>"
        )


# =====================================================
# USER INVITATION
# =====================================================

class UserInvitation(Base):
    """Invitation to join a school with a specific role"""

    __tablename__ = "user_invitations"
    __table_args__ = (
        Index('idx_user_invitations_token', 'invitation_token'),
        Index('idx_user_invitations_email_school', 'email', 'school_id'),
        {"schema": "platform", "extend_existing": True}
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Invitation target
    email = Column(String(255), nullable=False, index=True)
    school_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Pre-filled user info
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    department = Column(String(100))
    position = Column(String(100))

    # Roles
    invited_role = Column(String(50), nullable=False)  # SchoolRole value
    school_role = Column(String(50))  # Alias/additional role info

    # Invitation management
    invitation_token = Column(String(255), unique=True, nullable=False, index=True)
    invitation_type = Column(String(50), nullable=False)  # new_user, existing_user, bulk
    status = Column(String(50), nullable=False, default="pending")

    # References
    inviter_id = Column(PGUUID(as_uuid=True), nullable=False)
    inviter_name = Column(String(200))
    invitation_message = Column(Text)
    existing_user_id = Column(PGUUID(as_uuid=True))

    # Additional data
    role_metadata = Column(JSON, default=dict)
    permissions = Column(JSON, default=list)
    additional_context = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True))

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_pending(self) -> bool:
        return self.status == "pending" and not self.is_expired

    def __repr__(self):
        return (
            f"<UserInvitation(email='{self.email}', "
            f"school_id={self.school_id}, role='{self.invited_role}')>"
        )


# Alias for code that imports SchoolInvitation
SchoolInvitation = UserInvitation
