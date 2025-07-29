# =====================================================
# Clean Platform User Models - SQLAlchemy Only
# Consolidated models with intuitive naming (no DB suffixes)
# File: backend/shared/models/platform_user_clean.py
# =====================================================

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from enum import Enum
import uuid

Base = declarative_base()


# Pydantic models for complex JSON fields
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class UserProfile(BaseModel):
    """User profile information stored as JSON"""

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


class ClerkIntegration(BaseModel):
    """Clerk integration data stored as JSON"""

    clerk_user_id: str
    last_sync: datetime
    clerk_metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class PlatformRole(str, Enum):
    """Platform-level roles for users"""

    SUPER_ADMIN = "super_admin"
    SCHOOL_ADMIN = "school_admin"
    REGISTRAR = "registrar"
    TEACHER = "teacher"
    PARENT = "parent"
    STUDENT = "student"
    STAFF = "staff"


class SchoolRole(str, Enum):
    """School-specific roles"""

    PRINCIPAL = "principal"
    DEPUTY_PRINCIPAL = "deputy_principal"
    ACADEMIC_HEAD = "academic_head"
    DEPARTMENT_HEAD = "department_head"
    TEACHER = "teacher"
    FORM_TEACHER = "form_teacher"
    REGISTRAR = "registrar"
    BURSAR = "bursar"
    LIBRARIAN = "librarian"
    IT_SUPPORT = "it_support"
    SECURITY = "security"
    PARENT = "parent"
    STUDENT = "student"


class UserStatus(str, Enum):
    """User account status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    ARCHIVED = "archived"


class PlatformUser(Base):
    """SQLAlchemy model for platform users"""

    __tablename__ = "users"
    __table_args__ = {"schema": "platform"}

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(
        PGUUID(as_uuid=True), nullable=False
    )  # Required in current schema
    primary_school_id = Column(
        PGUUID(as_uuid=True), nullable=True
    )  # User's primary school
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))

    # Authentication fields
    clerk_user_id = Column(String(255), unique=True)
    password_hash = Column(String(255))  # For local authentication
    role = Column(
        String(50), nullable=False, default="student"
    )  # User role (this is the actual database field)

    # JSON fields for complex data (matching current schema)
    user_metadata = Column(JSON, default={})  # User metadata
    preferences = Column(JSON, default={})  # User preferences

    # Status fields
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True))  # Last login timestamp

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Properties for backward compatibility
    @property
    def platform_role(self) -> str:
        """Map role to platform_role for backward compatibility"""
        return self.role

    @platform_role.setter
    def platform_role(self, value: str):
        """Set role when platform_role is assigned"""
        self.role = value

    @property
    def status(self) -> str:
        """Map is_active to status for backward compatibility"""
        return "active" if self.is_active else "inactive"

    @status.setter
    def status(self, value: str):
        """Set is_active when status is assigned"""
        self.is_active = value in ("active", "verified")

    @property
    def profile(self) -> dict:
        """Map user_metadata to profile for backward compatibility"""
        return self.user_metadata or {}

    @profile.setter
    def profile(self, value: dict):
        """Set user_metadata when profile is assigned"""
        self.user_metadata = value

    @property
    def user_preferences(self) -> dict:
        """Map preferences to user_preferences for backward compatibility"""
        return self.preferences or {}

    @user_preferences.setter
    def user_preferences(self, value: dict):
        """Set preferences when user_preferences is assigned"""
        self.preferences = value

    @property
    def feature_flags(self) -> dict:
        """Return empty dict for feature_flags (not stored in this table)"""
        return {}

    @feature_flags.setter
    def feature_flags(self, value: dict):
        """Ignore feature_flags assignment (not stored in this table)"""
        pass
    last_login = Column(DateTime(timezone=True))

    # Relationships
    school_memberships = relationship("SchoolMembership", back_populates="user")

    @property
    def full_name(self) -> str:
        """User's full name"""
        return f"{self.first_name} {self.last_name}"

    @property
    def platform_role(self) -> PlatformRole:
        """Get platform role as enum"""
        try:
            return PlatformRole(self.role)
        except ValueError:
            return PlatformRole.STUDENT

    @property
    def status(self) -> UserStatus:
        """Get user status as enum"""
        return UserStatus.ACTIVE if self.is_active else UserStatus.INACTIVE

    def __repr__(self):
        return f"<PlatformUser(id={self.id}, email='{self.email}', role='{self.role}')>"


class SchoolMembership(Base):
    """SQLAlchemy model for school memberships"""

    __tablename__ = "school_memberships"
    __table_args__ = {"schema": "platform"}

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        PGUUID(as_uuid=True), ForeignKey("platform.users.id"), nullable=False
    )
    school_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    school_name = Column(String(255), nullable=False)
    school_subdomain = Column(String(50), nullable=False)
    role = Column(String(50), nullable=False)
    permissions = Column(JSON, default=[])
    joined_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), nullable=False, default="active")

    # Role-specific data
    student_id = Column(String(50))
    current_grade = Column(String(20))
    admission_date = Column(DateTime(timezone=True))
    graduation_date = Column(DateTime(timezone=True))

    employee_id = Column(String(50))
    department = Column(String(100))
    hire_date = Column(DateTime(timezone=True))
    contract_type = Column(String(50))

    children_ids = Column(JSON, default=[])

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("PlatformUser", back_populates="school_memberships")

    @property
    def school_role(self) -> SchoolRole:
        """Get school role as enum"""
        try:
            return SchoolRole(self.role)
        except ValueError:
            return SchoolRole.STUDENT

    def __repr__(self):
        return f"<SchoolMembership(user_id={self.user_id}, school_id={self.school_id}, role='{self.role}')>"


class UserInvitation(Base):
    """SQLAlchemy model for user invitations - Enhanced for user onboarding"""

    __tablename__ = "user_invitations"
    __table_args__ = {"schema": "platform"}

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    school_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    # User metadata for onboarding
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    department = Column(String(100))
    position = Column(String(100))

    # Roles
    invited_role = Column(String(50), nullable=False)  # PlatformRole
    school_role = Column(String(50), nullable=False)  # SchoolRole

    # Invitation details
    invitation_token = Column(String(255), unique=True, nullable=False, index=True)
    invitation_type = Column(
        String(50), nullable=False
    )  # "new_user" or "existing_user"
    status = Column(
        String(50), nullable=False, default="pending"
    )  # pending, accepted, declined, expired

    # User references
    inviter_id = Column(PGUUID(as_uuid=True), nullable=False)
    existing_user_id = Column(
        PGUUID(as_uuid=True), nullable=True
    )  # If inviting existing user

    # Role-specific data and permissions
    role_metadata = Column(JSON, default={})  # Role-specific information
    permissions = Column(JSON, default=[])  # Custom permissions if needed
    additional_context = Column(JSON, default={})  # Department, employee_id, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)

    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired"""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_pending(self) -> bool:
        """Check if invitation is still pending and valid"""
        return self.status == "pending" and not self.is_expired

    def __repr__(self):
        return f"<UserInvitation(email='{self.email}', school_id={self.school_id}, status='{self.status}')>"


class UserSession(Base):
    """SQLAlchemy model for user sessions"""

    __tablename__ = "user_sessions"
    __table_args__ = {"schema": "platform"}

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        PGUUID(as_uuid=True), ForeignKey("platform.users.id"), nullable=False
    )
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(500), unique=True, nullable=False, index=True)

    # Session metadata
    ip_address = Column(String(50))
    user_agent = Column(Text)
    device_info = Column(JSON, default={})

    # School context
    current_school_id = Column(PGUUID(as_uuid=True), nullable=True)

    # Session status
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    user = relationship("PlatformUser")

    @property
    def is_expired(self) -> bool:
        """Check if session has expired"""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if session is valid and active"""
        return self.is_active and not self.is_expired

    def __repr__(self):
        return f"<UserSession(user_id={self.user_id}, session_id='{self.session_id[:8]}...', active={self.is_active})>"
