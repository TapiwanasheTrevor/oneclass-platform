"""
Mobile Authentication Models
Handles device registration and mobile sessions
"""

from datetime import datetime
from typing import Optional
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

from shared.models.base import Base


class DeviceRegistration(Base):
    """
    Registered mobile devices for users
    """

    __tablename__ = "device_registrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Device information
    device_id = Column(String(255), unique=True, nullable=False, index=True)
    device_name = Column(String(255), nullable=True)
    device_type = Column(String(50), nullable=False)  # ios, android
    device_model = Column(String(255), nullable=True)
    device_os = Column(String(50), nullable=True)
    device_os_version = Column(String(50), nullable=True)

    # App information
    app_version = Column(String(50), nullable=True)
    app_build = Column(String(50), nullable=True)

    # Push notification tokens
    fcm_token = Column(String(500), nullable=True)
    apns_token = Column(String(500), nullable=True)

    # Security
    device_fingerprint = Column(String(255), nullable=True)
    is_trusted = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Biometric authentication
    biometric_enabled = Column(Boolean, default=False)
    biometric_type = Column(String(50), nullable=True)  # face, fingerprint, iris

    # Location
    last_ip_address = Column(String(45), nullable=True)
    last_location = Column(JSON, nullable=True)  # {lat, lng, country, city}

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="devices")
    sessions = relationship("MobileSession", back_populates="device")

    @hybrid_property
    def is_ios(self):
        """Check if device is iOS"""
        return self.device_type == "ios"

    @hybrid_property
    def is_android(self):
        """Check if device is Android"""
        return self.device_type == "android"

    def __repr__(self):
        return f"<DeviceRegistration(device_id='{self.device_id}', user_id='{self.user_id}')>"


class MobileSession(Base):
    """
    Mobile app sessions with enhanced security
    """

    __tablename__ = "mobile_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    device_id = Column(
        UUID(as_uuid=True),
        ForeignKey("device_registrations.id"),
        nullable=False,
        index=True,
    )

    # Session tokens
    access_token = Column(String(500), unique=True, nullable=False, index=True)
    refresh_token = Column(String(500), unique=True, nullable=False, index=True)

    # Session information
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)

    # Security
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="mobile_sessions")
    device = relationship("DeviceRegistration", back_populates="sessions")

    @hybrid_property
    def is_expired(self):
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return (
            f"<MobileSession(session_id='{self.session_id}', user_id='{self.user_id}')>"
        )


class MobileAuthCode(Base):
    """
    Authentication codes for mobile app login
    """

    __tablename__ = "mobile_auth_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Code information
    code = Column(String(10), unique=True, nullable=False, index=True)
    client_id = Column(String(255), nullable=False)

    # User association (after successful authentication)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )

    # Status
    is_used = Column(Boolean, default=False)
    is_expired = Column(Boolean, default=False)

    # Security
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User")

    @hybrid_property
    def is_valid(self):
        """Check if code is valid"""
        return (
            not self.is_used
            and not self.is_expired
            and datetime.utcnow() < self.expires_at
        )

    def __repr__(self):
        return f"<MobileAuthCode(code='{self.code}', is_used={self.is_used})>"


class MobileApiKey(Base):
    """
    API keys for mobile app access
    """

    __tablename__ = "mobile_api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True
    )

    # Key information
    name = Column(String(255), nullable=False)
    api_key = Column(String(255), unique=True, nullable=False, index=True)
    api_secret = Column(String(500), nullable=False)

    # Permissions
    permissions = Column(JSON, default=list)  # List of allowed endpoints/actions
    rate_limit = Column(Integer, default=1000)  # Requests per hour

    # Platform restrictions
    allowed_platforms = Column(JSON, default=list)  # ['ios', 'android']
    allowed_versions = Column(JSON, default=list)  # Minimum app versions

    # Status
    is_active = Column(Boolean, default=True)

    # Usage tracking
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    school = relationship("School", back_populates="mobile_api_keys")

    @hybrid_property
    def is_expired(self):
        """Check if API key is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f"<MobileApiKey(name='{self.name}', school_id='{self.school_id}')>"


class MobilePushNotification(Base):
    """
    Push notification history and management
    """

    __tablename__ = "mobile_push_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    device_id = Column(
        UUID(as_uuid=True),
        ForeignKey("device_registrations.id"),
        nullable=False,
        index=True,
    )

    # Notification content
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    data = Column(JSON, default=dict)

    # Notification type
    notification_type = Column(
        String(50), nullable=False
    )  # grade, attendance, payment, announcement
    priority = Column(String(20), default="normal")  # normal, high

    # Status
    status = Column(String(20), default="pending")  # pending, sent, delivered, failed

    # Delivery information
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    device = relationship("DeviceRegistration")

    def __repr__(self):
        return (
            f"<MobilePushNotification(title='{self.title}', user_id='{self.user_id}')>"
        )


# Add relationships to existing models
from shared.models.platform import School
from shared.models.platform_user import PlatformUser as User

School.mobile_api_keys = relationship("MobileApiKey", back_populates="school")
User.devices = relationship("DeviceRegistration", back_populates="user")
User.mobile_sessions = relationship("MobileSession", back_populates="user")
