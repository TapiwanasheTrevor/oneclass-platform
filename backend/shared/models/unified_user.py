"""
Unified User Model System
Supports single accounts with multi-school memberships and role management
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
import uuid

from pydantic import BaseModel, Field, validator

Base = declarative_base()

# =====================================================
# ENUMS FOR USER ROLES AND STATUS
# =====================================================

class GlobalRole(str, Enum):
    """Global platform roles that transcend schools"""
    
    SUPER_ADMIN = "super_admin"          # Platform super administrator
    PLATFORM_ADMIN = "platform_admin"    # Platform administrator
    REGIONAL_ADMIN = "regional_admin"     # Regional education administrator
    EDUCATION_OFFICER = "education_officer"  # Ministry of Education official
    SYSTEM_USER = "system_user"          # Regular platform user


class SchoolRole(str, Enum):
    """School-specific roles"""
    
    # Administrative roles
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
    
    ACTIVE = "active"                    # Active membership
    INACTIVE = "inactive"                # Temporarily inactive
    SUSPENDED = "suspended"              # Suspended membership
    PENDING_APPROVAL = "pending_approval"  # Awaiting approval
    GRADUATED = "graduated"              # Student graduated
    TRANSFERRED = "transferred"          # Transferred to another school
    EXPELLED = "expelled"                # Expelled from school
    ARCHIVED = "archived"                # Historical record


class UserStatus(str, Enum):
    """Overall user account status"""
    
    ACTIVE = "active"                    # Active user
    INACTIVE = "inactive"                # Inactive user
    SUSPENDED = "suspended"              # Suspended user
    PENDING_VERIFICATION = "pending_verification"  # Email not verified
    ARCHIVED = "archived"                # Archived user


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


# =====================================================
# CORE USER MODELS
# =====================================================

class UnifiedUser(Base):
    """
    Unified user model supporting multi-school memberships
    One account can have roles in multiple schools
    """
    
    __tablename__ = "unified_users"
    __table_args__ = (
        Index('idx_unified_users_email', 'email'),
        Index('idx_unified_users_global_role', 'global_role'),
        Index('idx_unified_users_status', 'status'),
        {"schema": "platform"}
    )
    
    # Primary identification
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    
    # Basic information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    display_name = Column(String(200))
    
    # Authentication
    password_hash = Column(String(255))
    clerk_user_id = Column(String(255), unique=True, nullable=True)
    oauth_provider = Column(String(50))
    oauth_provider_id = Column(String(255))
    
    # Global role and status
    global_role = Column(String(50), nullable=False, default=GlobalRole.SYSTEM_USER.value)
    status = Column(String(50), nullable=False, default=UserStatus.ACTIVE.value)
    
    # Verification and security
    is_email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255))
    password_reset_token = Column(String(255))
    password_reset_expires = Column(DateTime(timezone=True))
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255))
    
    # Profile and preferences (JSON fields)
    contact_information = Column(JSON, default=dict)
    personal_profile = Column(JSON, default=dict)
    user_preferences = Column(JSON, default=dict)
    
    # Audit fields
    last_login_at = Column(DateTime(timezone=True))
    last_activity_at = Column(DateTime(timezone=True))
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    last_failed_login = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    school_memberships = relationship("SchoolMembership", back_populates="user", cascade="all, delete-orphan")
    user_sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    # Properties
    @property
    def full_name(self) -> str:
        """User's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def contact_info(self) -> ContactInformation:
        """Get contact information as Pydantic model"""
        return ContactInformation(**self.contact_information or {})
    
    @property
    def profile(self) -> PersonalProfile:
        """Get personal profile as Pydantic model"""
        return PersonalProfile(**self.personal_profile or {})
    
    @property
    def preferences(self) -> UserPreferences:
        """Get user preferences as Pydantic model"""
        return UserPreferences(**self.user_preferences or {})
    
    @property
    def is_active(self) -> bool:
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE.value
    
    @property
    def is_platform_admin(self) -> bool:
        """Check if user is platform admin"""
        return self.global_role in [GlobalRole.SUPER_ADMIN.value, GlobalRole.PLATFORM_ADMIN.value]
    
    def get_active_school_memberships(self) -> List["SchoolMembership"]:
        """Get all active school memberships"""
        return [m for m in self.school_memberships if m.status == MembershipStatus.ACTIVE.value]
    
    def get_school_membership(self, school_id: str) -> Optional["SchoolMembership"]:
        """Get membership for specific school"""
        for membership in self.school_memberships:
            if str(membership.school_id) == school_id:
                return membership
        return None
    
    def has_school_access(self, school_id: str) -> bool:
        """Check if user has access to school"""
        membership = self.get_school_membership(school_id)
        return membership is not None and membership.status == MembershipStatus.ACTIVE.value
    
    def __repr__(self):
        return f"<UnifiedUser(id={self.id}, email='{self.email}', global_role='{self.global_role}')>"


class SchoolMembership(Base):
    """
    School membership model linking users to schools with specific roles
    Supports multiple memberships per user (teacher at one school, parent at another)
    """
    
    __tablename__ = "school_memberships"
    __table_args__ = (
        UniqueConstraint('user_id', 'school_id', name='uq_user_school'),
        Index('idx_school_memberships_school_role', 'school_id', 'role'),
        Index('idx_school_memberships_status', 'status'),
        Index('idx_school_memberships_user_id', 'user_id'),
        {"schema": "platform"}
    )
    
    # Primary identification
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("platform.unified_users.id"), nullable=False)
    school_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Basic school information (cached for performance)
    school_name = Column(String(255), nullable=False)
    school_subdomain = Column(String(50), nullable=False)
    school_region = Column(String(100))
    
    # Membership details
    role = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default=MembershipStatus.ACTIVE.value)
    permissions = Column(JSON, default=list)
    
    # Role-specific identifiers
    employee_id = Column(String(50))        # For staff members
    student_id = Column(String(50))         # For students
    registration_number = Column(String(50)) # Official registration number
    
    # Academic information (for students)
    current_grade = Column(String(20))
    current_class = Column(String(50))
    admission_date = Column(DateTime(timezone=True))
    graduation_date = Column(DateTime(timezone=True))
    academic_status = Column(String(50))    # enrolled, graduated, transferred, etc.
    
    # Employment information (for staff)
    department = Column(String(100))
    position = Column(String(100))
    hire_date = Column(DateTime(timezone=True))
    contract_type = Column(String(50))      # permanent, temporary, contract
    employment_status = Column(String(50))   # active, on_leave, terminated
    
    # Family relationships (for parents/guardians)
    children_ids = Column(JSON, default=list)  # List of student IDs they are responsible for
    relationship_type = Column(String(50))      # parent, guardian, sponsor
    
    # Membership timeline
    joined_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    left_date = Column(DateTime(timezone=True))
    
    # Additional metadata
    role_metadata = Column(JSON, default=dict)  # Role-specific additional data
    membership_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("UnifiedUser", back_populates="school_memberships")
    
    # Properties
    @property
    def is_active(self) -> bool:
        """Check if membership is active"""
        return self.status == MembershipStatus.ACTIVE.value
    
    @property
    def is_student(self) -> bool:
        """Check if this is a student membership"""
        return self.role == SchoolRole.STUDENT.value
    
    @property
    def is_staff(self) -> bool:
        """Check if this is a staff membership"""
        return self.role in [
            SchoolRole.PRINCIPAL.value,
            SchoolRole.DEPUTY_PRINCIPAL.value,
            SchoolRole.SCHOOL_ADMIN.value,
            SchoolRole.ACADEMIC_HEAD.value,
            SchoolRole.DEPARTMENT_HEAD.value,
            SchoolRole.TEACHER.value,
            SchoolRole.FORM_TEACHER.value,
            SchoolRole.SUBSTITUTE_TEACHER.value,
            SchoolRole.TRAINEE_TEACHER.value,
            SchoolRole.REGISTRAR.value,
            SchoolRole.BURSAR.value,
            SchoolRole.LIBRARIAN.value,
            SchoolRole.IT_SUPPORT.value,
            SchoolRole.SECURITY.value,
            SchoolRole.MAINTENANCE.value
        ]
    
    @property
    def is_parent_guardian(self) -> bool:
        """Check if this is a parent/guardian membership"""
        return self.role in [SchoolRole.PARENT.value, SchoolRole.GUARDIAN.value]
    
    @property
    def is_teaching_staff(self) -> bool:
        """Check if this is teaching staff"""
        return self.role in [
            SchoolRole.TEACHER.value,
            SchoolRole.FORM_TEACHER.value,
            SchoolRole.SUBSTITUTE_TEACHER.value,
            SchoolRole.TRAINEE_TEACHER.value
        ]
    
    def has_permission(self, permission: str) -> bool:
        """Check if membership has specific permission"""
        return permission in (self.permissions or [])
    
    def get_children_count(self) -> int:
        """Get number of children for parent/guardian"""
        if self.is_parent_guardian and self.children_ids:
            return len(self.children_ids)
        return 0
    
    def __repr__(self):
        return f"<SchoolMembership(user_id={self.user_id}, school_id={self.school_id}, role='{self.role}', status='{self.status}')>"


class UserSession(Base):
    """Enhanced user session model with school context"""
    
    __tablename__ = "user_sessions"
    __table_args__ = (
        Index('idx_user_sessions_session_id', 'session_id'),
        Index('idx_user_sessions_refresh_token', 'refresh_token'),
        Index('idx_user_sessions_user_school', 'user_id', 'current_school_id'),
        {"schema": "platform"}
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("platform.unified_users.id"), nullable=False)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(500), unique=True, nullable=False, index=True)
    
    # Session metadata
    ip_address = Column(String(50))
    user_agent = Column(Text)
    device_info = Column(JSON, default=dict)
    
    # Multi-school session context
    current_school_id = Column(PGUUID(as_uuid=True))  # Currently active school
    available_school_ids = Column(JSON, default=list)  # Schools user can switch to
    school_switch_count = Column(Integer, default=0)   # Number of school switches
    
    # Session status and activity
    is_active = Column(Boolean, default=True)
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    last_school_switch_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    user = relationship("UnifiedUser", back_populates="user_sessions")
    
    # Properties
    @property
    def is_expired(self) -> bool:
        """Check if session has expired"""
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if session is valid and active"""
        return self.is_active and not self.is_expired
    
    @property
    def time_since_last_activity(self) -> Optional[timedelta]:
        """Get time since last activity"""
        if self.last_activity_at:
            return datetime.now(timezone.utc) - self.last_activity_at
        return None
    
    def can_switch_to_school(self, school_id: str) -> bool:
        """Check if session can switch to school"""
        return school_id in (self.available_school_ids or [])
    
    def switch_school(self, school_id: str):
        """Switch to different school"""
        if self.can_switch_to_school(school_id):
            self.current_school_id = school_id
            self.school_switch_count += 1
            self.last_school_switch_at = datetime.now(timezone.utc)
    
    def __repr__(self):
        return f"<UserSession(user_id={self.user_id}, session_id='{self.session_id[:8]}...', current_school={self.current_school_id})>"


# =====================================================
# INVITATION AND ONBOARDING MODELS  
# =====================================================

class SchoolInvitation(Base):
    """Enhanced invitation system for multi-school support"""
    
    __tablename__ = "school_invitations"
    __table_args__ = (
        Index('idx_school_invitations_token', 'invitation_token'),
        Index('idx_school_invitations_email_school', 'email', 'school_id'),
        {"schema": "platform"}
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Invitation details
    email = Column(String(255), nullable=False, index=True)
    school_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    invited_role = Column(String(50), nullable=False)
    
    # Inviter information
    inviter_id = Column(PGUUID(as_uuid=True), nullable=False)
    inviter_name = Column(String(200), nullable=False)
    invitation_message = Column(Text)
    
    # Pre-filled user information
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone_number = Column(String(20))
    
    # Role-specific data
    employee_id = Column(String(50))
    student_id = Column(String(50))
    department = Column(String(100))
    position = Column(String(100))
    grade_level = Column(String(20))
    
    # Invitation management
    invitation_token = Column(String(255), unique=True, nullable=False, index=True)
    invitation_type = Column(String(50), nullable=False)  # new_user, existing_user, bulk_import
    status = Column(String(50), nullable=False, default="pending")
    
    # References
    existing_user_id = Column(PGUUID(as_uuid=True))  # If inviting existing user
    parent_invitation_id = Column(PGUUID(as_uuid=True))  # For bulk invitations
    
    # Additional context
    role_metadata = Column(JSON, default=dict)
    permissions = Column(JSON, default=list)
    additional_context = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True))
    declined_at = Column(DateTime(timezone=True))
    
    # Properties
    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired"""
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_pending(self) -> bool:
        """Check if invitation is still pending and valid"""
        return self.status == "pending" and not self.is_expired
    
    @property
    def is_for_existing_user(self) -> bool:
        """Check if invitation is for existing user"""
        return self.existing_user_id is not None
    
    def __repr__(self):
        return f"<SchoolInvitation(email='{self.email}', school_id={self.school_id}, role='{self.invited_role}', status='{self.status}')>"