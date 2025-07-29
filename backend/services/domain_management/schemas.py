"""
Domain Management Schemas
Pydantic models for domain management API
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
import re


class DomainBase(BaseModel):
    """Base domain model"""
    subdomain: str = Field(..., min_length=3, max_length=50, description="School subdomain")
    custom_domain: Optional[str] = Field(None, description="Custom domain if available")
    email_domain_enabled: bool = Field(True, description="Enable email for this domain")
    email_provider: str = Field("internal", description="Email provider (internal, google, microsoft)")
    
    @validator('subdomain')
    def validate_subdomain(cls, v):
        """Validate subdomain format"""
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]{1,48}[a-zA-Z0-9]$', v):
            raise ValueError('Subdomain must be 3-50 characters, alphanumeric and hyphens, start/end with alphanumeric')
        return v.lower()
    
    @validator('custom_domain')
    def validate_custom_domain(cls, v):
        """Validate custom domain format"""
        if v and not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid custom domain format')
        return v.lower() if v else None


class DomainCreate(DomainBase):
    """Domain creation model"""
    school_id: str = Field(..., description="School ID")
    dns_provider: str = Field("cloudflare", description="DNS provider")
    email_provider_config: Dict[str, Any] = Field(default_factory=dict)


class DomainUpdate(BaseModel):
    """Domain update model"""
    custom_domain: Optional[str] = None
    is_active: Optional[bool] = None
    email_domain_enabled: Optional[bool] = None
    email_provider: Optional[str] = None
    email_provider_config: Optional[Dict[str, Any]] = None
    ssl_auto_renew: Optional[bool] = None


class DomainResponse(DomainBase):
    """Domain response model"""
    id: str
    school_id: str
    full_domain: str
    primary_domain: str
    email_domain: str
    is_active: bool
    is_verified: bool
    ssl_certificate_id: Optional[str] = None
    ssl_certificate_expires: Optional[datetime] = None
    is_ssl_valid: bool
    ssl_expires_soon: bool
    dns_provider: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EmailAddressBase(BaseModel):
    """Base email address model"""
    username: str = Field(..., min_length=1, max_length=100, description="Email username")
    forward_to: Optional[EmailStr] = Field(None, description="Forward emails to this address")
    forward_enabled: bool = Field(False, description="Enable email forwarding")
    storage_quota_mb: int = Field(1000, ge=100, le=10000, description="Storage quota in MB")
    daily_send_limit: int = Field(100, ge=10, le=1000, description="Daily send limit")
    
    @validator('username')
    def validate_username(cls, v):
        """Validate email username"""
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]$', v):
            raise ValueError('Username must be alphanumeric with dots, hyphens, underscores')
        return v.lower()


class EmailAddressCreate(EmailAddressBase):
    """Email address creation model"""
    domain_id: str = Field(..., description="Domain ID")
    user_id: Optional[str] = Field(None, description="User ID if linked to user")


class EmailAddressUpdate(BaseModel):
    """Email address update model"""
    forward_to: Optional[EmailStr] = None
    forward_enabled: Optional[bool] = None
    storage_quota_mb: Optional[int] = Field(None, ge=100, le=10000)
    daily_send_limit: Optional[int] = Field(None, ge=10, le=1000)
    is_active: Optional[bool] = None


class EmailAddressResponse(EmailAddressBase):
    """Email address response model"""
    id: str
    domain_id: str
    user_id: Optional[str] = None
    email_address: str
    is_active: bool
    is_verified: bool
    provider_user_id: Optional[str] = None
    provider_name: str
    created_at: datetime
    updated_at: datetime
    last_used: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SSLCertificateBase(BaseModel):
    """Base SSL certificate model"""
    certificate_type: str = Field("lets_encrypt", description="Certificate type")
    auto_renew: bool = Field(True, description="Auto-renew certificate")
    renewal_threshold_days: int = Field(30, ge=1, le=90, description="Renewal threshold in days")


class SSLCertificateCreate(SSLCertificateBase):
    """SSL certificate creation model"""
    domain_id: str = Field(..., description="Domain ID")


class SSLCertificateUpdate(BaseModel):
    """SSL certificate update model"""
    auto_renew: Optional[bool] = None
    renewal_threshold_days: Optional[int] = Field(None, ge=1, le=90)
    is_active: Optional[bool] = None


class SSLCertificateResponse(SSLCertificateBase):
    """SSL certificate response model"""
    id: str
    domain_id: str
    certificate_id: str
    issued_by: Optional[str] = None
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool
    is_valid: bool
    is_expired: bool
    expires_soon: bool
    days_until_expiry: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DomainVerificationBase(BaseModel):
    """Base domain verification model"""
    verification_type: str = Field(..., description="Verification type (dns, file, meta)")
    verification_method: str = Field(..., description="Verification method (txt_record, cname, file_upload)")


class DomainVerificationCreate(DomainVerificationBase):
    """Domain verification creation model"""
    domain_id: str = Field(..., description="Domain ID")


class DomainVerificationResponse(DomainVerificationBase):
    """Domain verification response model"""
    id: str
    domain_id: str
    verification_token: str
    verification_value: str
    verification_record: Optional[str] = None
    is_verified: bool
    verification_attempts: int
    max_attempts: int
    can_retry: bool
    is_expired: bool
    created_at: datetime
    updated_at: datetime
    verified_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DomainTemplateBase(BaseModel):
    """Base domain template model"""
    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    template_type: str = Field(..., description="Template type (standard, premium, custom)")
    features: List[str] = Field(default_factory=list, description="Template features")
    restrictions: Dict[str, Any] = Field(default_factory=dict, description="Template restrictions")


class DomainTemplateCreate(DomainTemplateBase):
    """Domain template creation model"""
    dns_records_template: List[Dict[str, Any]] = Field(default_factory=list)
    email_config_template: Dict[str, Any] = Field(default_factory=dict)
    ssl_config_template: Dict[str, Any] = Field(default_factory=dict)


class DomainTemplateUpdate(BaseModel):
    """Domain template update model"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    features: Optional[List[str]] = None
    restrictions: Optional[Dict[str, Any]] = None


class DomainTemplateResponse(DomainTemplateBase):
    """Domain template response model"""
    id: str
    dns_records_template: List[Dict[str, Any]]
    email_config_template: Dict[str, Any]
    ssl_config_template: Dict[str, Any]
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DomainValidationRequest(BaseModel):
    """Domain validation request model"""
    subdomain: str = Field(..., description="Subdomain to validate")
    custom_domain: Optional[str] = Field(None, description="Custom domain to validate")


class DomainValidationResponse(BaseModel):
    """Domain validation response model"""
    is_valid: bool
    subdomain_available: bool
    custom_domain_available: bool
    suggestions: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class DomainStatsResponse(BaseModel):
    """Domain statistics response model"""
    total_domains: int
    active_domains: int
    verified_domains: int
    ssl_certificates: int
    expired_certificates: int
    expiring_soon: int
    email_addresses: int
    active_email_addresses: int


class BulkEmailCreateRequest(BaseModel):
    """Bulk email address creation request"""
    domain_id: str = Field(..., description="Domain ID")
    email_addresses: List[Dict[str, Any]] = Field(..., description="Email addresses to create")


class BulkEmailCreateResponse(BaseModel):
    """Bulk email address creation response"""
    created: List[EmailAddressResponse]
    failed: List[Dict[str, Any]]
    total_created: int
    total_failed: int