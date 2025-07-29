"""
Domain Management Models
Handles custom domain support for schools with subdomain and email integration
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
import re

from shared.models.base import Base


class Domain(Base):
    """
    Domain model for managing school domains and subdomains
    """

    __tablename__ = "domains"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(
        UUID(as_uuid=True),
        ForeignKey("schools.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Domain configuration
    subdomain = Column(String(50), unique=True, nullable=False, index=True)
    custom_domain = Column(
        String(255), unique=True, nullable=True
    )  # For schools wanting their own domain

    # Domain status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), unique=True, nullable=True)

    # SSL configuration
    ssl_certificate_id = Column(String(255), nullable=True)
    ssl_certificate_expires = Column(DateTime, nullable=True)
    ssl_auto_renew = Column(Boolean, default=True)

    # Email configuration
    email_domain_enabled = Column(Boolean, default=True)
    email_mx_records = Column(JSON, default=list)
    email_provider = Column(
        String(50), default="internal"
    )  # internal, google, microsoft
    email_provider_config = Column(JSON, default=dict)

    # DNS configuration
    dns_records = Column(JSON, default=list)
    dns_provider = Column(String(50), default="cloudflare")
    dns_zone_id = Column(String(255), nullable=True)

    # Metadata
    domain_metadata = Column(JSON, default=dict)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    school = relationship("School", back_populates="domain")
    creator = relationship("User", foreign_keys=[created_by])
    email_addresses = relationship("EmailAddress", back_populates="domain")
    ssl_certificates = relationship("SSLCertificate", back_populates="domain")

    @hybrid_property
    def full_domain(self):
        """Get the full domain (subdomain + base domain)"""
        return f"{self.subdomain}.oneclass.ac.zw"

    @hybrid_property
    def primary_domain(self):
        """Get the primary domain (custom domain if available, otherwise subdomain)"""
        return self.custom_domain if self.custom_domain else self.full_domain

    @hybrid_property
    def email_domain(self):
        """Get the email domain"""
        return (
            self.custom_domain
            if self.custom_domain
            else f"{self.subdomain}.oneclass.ac.zw"
        )

    @hybrid_property
    def is_ssl_valid(self):
        """Check if SSL certificate is valid"""
        if not self.ssl_certificate_expires:
            return False
        return datetime.utcnow() < self.ssl_certificate_expires

    @hybrid_property
    def ssl_expires_soon(self):
        """Check if SSL certificate expires within 30 days"""
        if not self.ssl_certificate_expires:
            return True
        return datetime.utcnow() + timedelta(days=30) > self.ssl_certificate_expires

    def validate_subdomain(self, subdomain: str) -> bool:
        """Validate subdomain format"""
        # Must be 3-50 characters, alphanumeric and hyphens, start/end with alphanumeric
        pattern = r"^[a-zA-Z0-9][a-zA-Z0-9-]{1,48}[a-zA-Z0-9]$"
        return bool(re.match(pattern, subdomain))

    def validate_custom_domain(self, domain: str) -> bool:
        """Validate custom domain format"""
        # Basic domain validation
        pattern = r"^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, domain))

    def __repr__(self):
        return f"<Domain(subdomain='{self.subdomain}', school_id='{self.school_id}')>"


class EmailAddress(Base):
    """
    Email address model for managing school email addresses
    """

    __tablename__ = "email_addresses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain_id = Column(
        UUID(as_uuid=True), ForeignKey("domains.id"), nullable=False, index=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )

    # Email configuration
    email_address = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False)

    # Email status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), unique=True, nullable=True)

    # Email provider configuration
    provider_user_id = Column(String(255), nullable=True)  # ID in external provider
    provider_config = Column(JSON, default=dict)

    # Forwarding configuration
    forward_to = Column(String(255), nullable=True)
    forward_enabled = Column(Boolean, default=False)

    # Quota and limits
    storage_quota_mb = Column(Integer, default=1000)  # 1GB default
    daily_send_limit = Column(Integer, default=100)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)

    # Relationships
    domain = relationship("Domain", back_populates="email_addresses")
    user = relationship("User", back_populates="email_addresses")

    @hybrid_property
    def is_school_email(self):
        """Check if this is a school email address"""
        return self.domain_id is not None

    @hybrid_property
    def provider_name(self):
        """Get the email provider name"""
        return self.domain.email_provider if self.domain else "unknown"

    def __repr__(self):
        return f"<EmailAddress(email='{self.email_address}', domain_id='{self.domain_id}')>"


class SSLCertificate(Base):
    """
    SSL certificate model for managing domain certificates
    """

    __tablename__ = "ssl_certificates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain_id = Column(
        UUID(as_uuid=True), ForeignKey("domains.id"), nullable=False, index=True
    )

    # Certificate information
    certificate_id = Column(String(255), unique=True, nullable=False)
    certificate_type = Column(
        String(50), default="lets_encrypt"
    )  # lets_encrypt, custom, cloudflare

    # Certificate details
    issued_by = Column(String(255), nullable=True)
    issued_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Certificate data
    certificate_data = Column(Text, nullable=True)  # PEM format
    private_key_data = Column(Text, nullable=True)  # PEM format (encrypted)
    certificate_chain = Column(Text, nullable=True)  # PEM format

    # Status
    is_active = Column(Boolean, default=True)
    is_valid = Column(Boolean, default=True)

    # Auto-renewal
    auto_renew = Column(Boolean, default=True)
    renewal_threshold_days = Column(Integer, default=30)

    # Provider configuration
    provider_config = Column(JSON, default=dict)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    domain = relationship("Domain", back_populates="ssl_certificates")

    @hybrid_property
    def is_expired(self):
        """Check if certificate is expired"""
        if not self.expires_at:
            return True
        return datetime.utcnow() > self.expires_at

    @hybrid_property
    def expires_soon(self):
        """Check if certificate expires within renewal threshold"""
        if not self.expires_at:
            return True
        return (
            datetime.utcnow() + timedelta(days=self.renewal_threshold_days)
            > self.expires_at
        )

    @hybrid_property
    def days_until_expiry(self):
        """Get days until certificate expires"""
        if not self.expires_at:
            return 0
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)

    def __repr__(self):
        return f"<SSLCertificate(certificate_id='{self.certificate_id}', domain_id='{self.domain_id}')>"


class DomainVerification(Base):
    """
    Domain verification model for managing domain ownership verification
    """

    __tablename__ = "domain_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain_id = Column(
        UUID(as_uuid=True), ForeignKey("domains.id"), nullable=False, index=True
    )

    # Verification details
    verification_type = Column(String(50), nullable=False)  # dns, file, meta
    verification_method = Column(
        String(50), nullable=False
    )  # txt_record, cname, file_upload

    # Verification data
    verification_token = Column(String(255), unique=True, nullable=False)
    verification_value = Column(String(500), nullable=False)
    verification_record = Column(String(255), nullable=True)  # DNS record name

    # Status
    is_verified = Column(Boolean, default=False)
    verification_attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=10)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    domain = relationship("Domain")

    @hybrid_property
    def is_expired(self):
        """Check if verification token is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @hybrid_property
    def can_retry(self):
        """Check if verification can be retried"""
        return self.verification_attempts < self.max_attempts and not self.is_expired

    def __repr__(self):
        return f"<DomainVerification(domain_id='{self.domain_id}', type='{self.verification_type}')>"


class DomainTemplate(Base):
    """
    Domain template model for managing domain configuration templates
    """

    __tablename__ = "domain_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Template information
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    template_type = Column(String(50), nullable=False)  # standard, premium, custom

    # Template configuration
    dns_records_template = Column(JSON, default=list)
    email_config_template = Column(JSON, default=dict)
    ssl_config_template = Column(JSON, default=dict)

    # Features
    features = Column(JSON, default=list)
    restrictions = Column(JSON, default=dict)

    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<DomainTemplate(name='{self.name}', type='{self.template_type}')>"


# Add relationships to existing models
# This would be added to the existing School model
from shared.models.platform import School
from shared.models.platform_user import PlatformUserDB as User

School.domain = relationship("Domain", back_populates="school", uselist=False)
User.email_addresses = relationship("EmailAddress", back_populates="user")
