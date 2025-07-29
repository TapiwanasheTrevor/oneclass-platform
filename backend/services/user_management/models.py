"""
User Management Models
Enhanced user models for role-based creation and management within schools
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
    Text,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
import uuid

from shared.database import Base
from shared.models.platform import School
from shared.models.platform_user import PlatformUser as User


class UserInvitationLegacy(Base):
    """
    User invitation model for role-based user creation
    """

    __tablename__ = "user_invitations_legacy"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True
    )
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    invitation_token = Column(String(255), unique=True, nullable=False, index=True)

    # Invitation metadata
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    department = Column(String(100))
    position = Column(String(100))

    # Role-specific data
    role_metadata = Column(JSON, default={})  # Role-specific information
    permissions = Column(JSON, default=[])  # Custom permissions if needed

    # Invitation status
    status = Column(
        String(20), default="pending"
    )  # pending, accepted, expired, cancelled
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    school = relationship("School", back_populates="invitations")
    inviter = relationship("User", foreign_keys=[invited_by])

    @hybrid_property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    @hybrid_property
    def is_pending(self):
        return self.status == "pending" and not self.is_expired

    def __repr__(self):
        return f"<UserInvitation(email='{self.email}', role='{self.role}', school_id='{self.school_id}')>"


class UserRole(Base):
    """
    Extended user role model with hierarchical permissions
    """

    __tablename__ = "user_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True
    )

    # Role definition
    role_name = Column(String(50), nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)

    # Permission system
    permissions = Column(JSON, default=[])
    inherited_roles = Column(JSON, default=[])  # Roles this role inherits from

    # Role configuration
    is_system_role = Column(Boolean, default=False)  # Cannot be deleted
    is_active = Column(Boolean, default=True)

    # Hierarchical data
    parent_role_id = Column(
        UUID(as_uuid=True), ForeignKey("user_roles.id"), nullable=True
    )
    level = Column(Integer, default=0)  # Hierarchy level

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    school = relationship("School")
    parent_role = relationship("UserRole", remote_side=[id])
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<UserRole(role_name='{self.role_name}', school_id='{self.school_id}')>"


class UserProfile(Base):
    """
    Extended user profile with role-specific information
    """

    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True
    )
    school_id = Column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True
    )

    # Professional information
    employee_id = Column(String(50), nullable=True)  # For staff
    student_id = Column(String(50), nullable=True)  # For students
    national_id = Column(String(20), nullable=True)

    # Contact information
    address = Column(Text)
    emergency_contact_name = Column(String(100))
    emergency_contact_phone = Column(String(20))
    emergency_contact_relationship = Column(String(50))

    # Role-specific data
    department = Column(String(100))  # For staff
    position = Column(String(100))  # For staff
    hire_date = Column(DateTime)  # For staff
    grade_level = Column(String(10))  # For students
    enrollment_date = Column(DateTime)  # For students

    # Parent/Guardian information (for students)
    parent_guardian_info = Column(JSON, default={})

    # Academic information (for students)
    academic_info = Column(JSON, default={})

    # Staff qualifications (for staff)
    qualifications = Column(JSON, default=[])

    # Profile completion
    profile_completed = Column(Boolean, default=False)
    completion_percentage = Column(Integer, default=0)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="profile")
    school = relationship("School")

    def __repr__(self):
        return f"<UserProfile(user_id='{self.user_id}', school_id='{self.school_id}')>"


class BulkUserImport(Base):
    """
    Bulk user import tracking
    """

    __tablename__ = "bulk_user_imports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True
    )
    imported_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Import metadata
    file_name = Column(String(255))
    file_path = Column(String(500))
    import_type = Column(String(50))  # csv, excel, json

    # Import statistics
    total_records = Column(Integer, default=0)
    successful_imports = Column(Integer, default=0)
    failed_imports = Column(Integer, default=0)

    # Import results
    import_results = Column(JSON, default={})
    error_log = Column(JSON, default=[])

    # Import status
    status = Column(
        String(20), default="pending"
    )  # pending, processing, completed, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    school = relationship("School")
    importer = relationship("User", foreign_keys=[imported_by])

    def __repr__(self):
        return f"<BulkUserImport(school_id='{self.school_id}', status='{self.status}')>"


# Add relationships to existing models
# This would be added to the existing User model
# User.invitations_sent = relationship("UserInvitation", foreign_keys=[UserInvitation.invited_by])
# User.profile = relationship("UserProfile", back_populates="user", uselist=False)

# This would be added to the existing School model
# School.invitations = relationship("UserInvitation", back_populates="school")
# School.user_roles = relationship("UserRole")
# School.bulk_imports = relationship("BulkUserImport")
