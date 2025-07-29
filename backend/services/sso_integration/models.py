"""
SSO Integration Models
Handles SAML and LDAP configuration for schools
"""

from datetime import datetime
from typing import Optional, Dict, Any
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


class SSOProvider(Base):
    """
    SSO Provider configuration for schools
    """

    __tablename__ = "sso_providers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True
    )

    # Provider information
    provider_name = Column(String(100), nullable=False)
    provider_type = Column(String(20), nullable=False)  # saml, ldap, oauth2
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Provider status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    auto_provision = Column(Boolean, default=True)  # Auto-create users on first login

    # Configuration
    configuration = Column(JSON, default=dict)
    metadata = Column(JSON, default=dict)

    # Mapping configuration
    attribute_mapping = Column(JSON, default=dict)
    role_mapping = Column(JSON, default=dict)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    school = relationship("School", back_populates="sso_providers")
    creator = relationship("User", foreign_keys=[created_by])
    sessions = relationship("SSOSession", back_populates="provider")

    @hybrid_property
    def is_saml(self):
        """Check if provider is SAML"""
        return self.provider_type == "saml"

    @hybrid_property
    def is_ldap(self):
        """Check if provider is LDAP"""
        return self.provider_type == "ldap"

    @hybrid_property
    def is_oauth2(self):
        """Check if provider is OAuth2"""
        return self.provider_type == "oauth2"

    def __repr__(self):
        return f"<SSOProvider(name='{self.provider_name}', type='{self.provider_type}', school_id='{self.school_id}')>"


class SAMLProvider(Base):
    """
    SAML-specific provider configuration
    """

    __tablename__ = "saml_providers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sso_provider_id = Column(
        UUID(as_uuid=True), ForeignKey("sso_providers.id"), nullable=False, unique=True
    )

    # SAML Configuration
    entity_id = Column(String(500), nullable=False)
    sso_url = Column(String(500), nullable=False)
    slo_url = Column(String(500), nullable=True)
    x509_cert = Column(Text, nullable=False)

    # Service Provider Configuration
    sp_entity_id = Column(String(500), nullable=False)
    sp_acs_url = Column(String(500), nullable=False)
    sp_sls_url = Column(String(500), nullable=True)
    sp_x509_cert = Column(Text, nullable=True)
    sp_private_key = Column(Text, nullable=True)

    # SAML Settings
    name_id_format = Column(
        String(200), default="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
    )
    authn_requests_signed = Column(Boolean, default=False)
    logout_requests_signed = Column(Boolean, default=False)
    want_assertions_signed = Column(Boolean, default=True)
    want_name_id_encrypted = Column(Boolean, default=False)

    # Relationships
    sso_provider = relationship("SSOProvider", back_populates="saml_config")

    def __repr__(self):
        return f"<SAMLProvider(entity_id='{self.entity_id}', sso_url='{self.sso_url}')>"


class LDAPProvider(Base):
    """
    LDAP-specific provider configuration
    """

    __tablename__ = "ldap_providers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sso_provider_id = Column(
        UUID(as_uuid=True), ForeignKey("sso_providers.id"), nullable=False, unique=True
    )

    # LDAP Connection
    server_url = Column(String(500), nullable=False)
    bind_dn = Column(String(500), nullable=False)
    bind_password = Column(String(500), nullable=False)

    # LDAP Settings
    base_dn = Column(String(500), nullable=False)
    user_search_filter = Column(String(500), default="(sAMAccountName={username})")
    user_search_base = Column(String(500), nullable=True)
    group_search_filter = Column(String(500), default="(member={user_dn})")
    group_search_base = Column(String(500), nullable=True)

    # Connection Settings
    use_ssl = Column(Boolean, default=True)
    use_tls = Column(Boolean, default=False)
    timeout = Column(Integer, default=30)

    # Attribute Mappings
    username_attribute = Column(String(100), default="sAMAccountName")
    email_attribute = Column(String(100), default="mail")
    first_name_attribute = Column(String(100), default="givenName")
    last_name_attribute = Column(String(100), default="sn")
    display_name_attribute = Column(String(100), default="displayName")

    # Relationships
    sso_provider = relationship("SSOProvider", back_populates="ldap_config")

    def __repr__(self):
        return (
            f"<LDAPProvider(server_url='{self.server_url}', base_dn='{self.base_dn}')>"
        )


class SSOSession(Base):
    """
    SSO session tracking
    """

    __tablename__ = "sso_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(
        UUID(as_uuid=True), ForeignKey("sso_providers.id"), nullable=False, index=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )

    # Session information
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    external_session_id = Column(String(255), nullable=True)

    # Authentication details
    username = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    external_user_id = Column(String(255), nullable=True)

    # Session status
    is_active = Column(Boolean, default=True)
    login_method = Column(String(50), nullable=False)  # saml, ldap, oauth2

    # Session metadata
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    attributes = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    provider = relationship("SSOProvider", back_populates="sessions")
    user = relationship("User", back_populates="sso_sessions")

    @hybrid_property
    def is_expired(self):
        """Check if session is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return (
            f"<SSOSession(session_id='{self.session_id}', username='{self.username}')>"
        )


class SSOAuditLog(Base):
    """
    SSO audit log for tracking authentication events
    """

    __tablename__ = "sso_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(
        UUID(as_uuid=True), ForeignKey("sso_providers.id"), nullable=False, index=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )

    # Event information
    event_type = Column(String(50), nullable=False)  # login, logout, error, provision
    event_status = Column(String(20), nullable=False)  # success, failure, pending
    event_message = Column(Text, nullable=True)

    # User information
    username = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    external_user_id = Column(String(255), nullable=True)

    # Request information
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    session_id = Column(String(255), nullable=True)

    # Additional data
    metadata = Column(JSON, default=dict)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    provider = relationship("SSOProvider")
    user = relationship("User")

    def __repr__(self):
        return f"<SSOAuditLog(event_type='{self.event_type}', status='{self.event_status}', username='{self.username}')>"


# Add relationships to existing models
# This would be added to the existing School and User models
from shared.models.platform import School
from shared.models.platform_user import PlatformUserDB as User

School.sso_providers = relationship("SSOProvider", back_populates="school")
User.sso_sessions = relationship("SSOSession", back_populates="user")

# Add back-references to new models
SSOProvider.saml_config = relationship(
    "SAMLProvider", back_populates="sso_provider", uselist=False
)
SSOProvider.ldap_config = relationship(
    "LDAPProvider", back_populates="sso_provider", uselist=False
)
