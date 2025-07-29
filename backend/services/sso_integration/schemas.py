"""
SSO Integration Schemas
Pydantic models for SSO integration API
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum


class SSOProviderType(str, Enum):
    """SSO Provider types"""
    SAML = "saml"
    LDAP = "ldap"
    OAUTH2 = "oauth2"


class SSOEventType(str, Enum):
    """SSO event types"""
    LOGIN = "login"
    LOGOUT = "logout"
    ERROR = "error"
    PROVISION = "provision"
    UPDATE = "update"


class SSOEventStatus(str, Enum):
    """SSO event status"""
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"


class SSOProviderBase(BaseModel):
    """Base SSO provider model"""
    provider_name: str = Field(..., min_length=1, max_length=100)
    provider_type: SSOProviderType
    display_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: bool = True
    is_default: bool = False
    auto_provision: bool = True
    attribute_mapping: Dict[str, str] = Field(default_factory=dict)
    role_mapping: Dict[str, str] = Field(default_factory=dict)


class SSOProviderCreate(SSOProviderBase):
    """SSO provider creation model"""
    school_id: str = Field(..., description="School ID")
    configuration: Dict[str, Any] = Field(default_factory=dict)


class SSOProviderUpdate(BaseModel):
    """SSO provider update model"""
    provider_name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    auto_provision: Optional[bool] = None
    attribute_mapping: Optional[Dict[str, str]] = None
    role_mapping: Optional[Dict[str, str]] = None
    configuration: Optional[Dict[str, Any]] = None


class SSOProviderResponse(SSOProviderBase):
    """SSO provider response model"""
    id: str
    school_id: str
    is_saml: bool
    is_ldap: bool
    is_oauth2: bool
    configuration: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SAMLProviderBase(BaseModel):
    """Base SAML provider model"""
    entity_id: str = Field(..., description="Identity Provider Entity ID")
    sso_url: str = Field(..., description="SSO URL")
    slo_url: Optional[str] = Field(None, description="Single Logout URL")
    x509_cert: str = Field(..., description="X.509 Certificate")
    
    # Service Provider settings
    sp_entity_id: str = Field(..., description="Service Provider Entity ID")
    sp_acs_url: str = Field(..., description="Assertion Consumer Service URL")
    sp_sls_url: Optional[str] = Field(None, description="Single Logout Service URL")
    sp_x509_cert: Optional[str] = Field(None, description="Service Provider X.509 Certificate")
    sp_private_key: Optional[str] = Field(None, description="Service Provider Private Key")
    
    # SAML settings
    name_id_format: str = Field(
        "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        description="Name ID Format"
    )
    authn_requests_signed: bool = False
    logout_requests_signed: bool = False
    want_assertions_signed: bool = True
    want_name_id_encrypted: bool = False


class SAMLProviderCreate(SAMLProviderBase):
    """SAML provider creation model"""
    sso_provider_id: str = Field(..., description="SSO Provider ID")


class SAMLProviderUpdate(BaseModel):
    """SAML provider update model"""
    entity_id: Optional[str] = None
    sso_url: Optional[str] = None
    slo_url: Optional[str] = None
    x509_cert: Optional[str] = None
    sp_entity_id: Optional[str] = None
    sp_acs_url: Optional[str] = None
    sp_sls_url: Optional[str] = None
    sp_x509_cert: Optional[str] = None
    sp_private_key: Optional[str] = None
    name_id_format: Optional[str] = None
    authn_requests_signed: Optional[bool] = None
    logout_requests_signed: Optional[bool] = None
    want_assertions_signed: Optional[bool] = None
    want_name_id_encrypted: Optional[bool] = None


class SAMLProviderResponse(SAMLProviderBase):
    """SAML provider response model"""
    id: str
    sso_provider_id: str
    
    class Config:
        from_attributes = True


class LDAPProviderBase(BaseModel):
    """Base LDAP provider model"""
    server_url: str = Field(..., description="LDAP Server URL")
    bind_dn: str = Field(..., description="Bind DN")
    bind_password: str = Field(..., description="Bind Password")
    base_dn: str = Field(..., description="Base DN")
    
    # Search filters
    user_search_filter: str = Field("(sAMAccountName={username})", description="User search filter")
    user_search_base: Optional[str] = Field(None, description="User search base")
    group_search_filter: str = Field("(member={user_dn})", description="Group search filter")
    group_search_base: Optional[str] = Field(None, description="Group search base")
    
    # Connection settings
    use_ssl: bool = True
    use_tls: bool = False
    timeout: int = Field(30, ge=1, le=300)
    
    # Attribute mappings
    username_attribute: str = Field("sAMAccountName", description="Username attribute")
    email_attribute: str = Field("mail", description="Email attribute")
    first_name_attribute: str = Field("givenName", description="First name attribute")
    last_name_attribute: str = Field("sn", description="Last name attribute")
    display_name_attribute: str = Field("displayName", description="Display name attribute")


class LDAPProviderCreate(LDAPProviderBase):
    """LDAP provider creation model"""
    sso_provider_id: str = Field(..., description="SSO Provider ID")


class LDAPProviderUpdate(BaseModel):
    """LDAP provider update model"""
    server_url: Optional[str] = None
    bind_dn: Optional[str] = None
    bind_password: Optional[str] = None
    base_dn: Optional[str] = None
    user_search_filter: Optional[str] = None
    user_search_base: Optional[str] = None
    group_search_filter: Optional[str] = None
    group_search_base: Optional[str] = None
    use_ssl: Optional[bool] = None
    use_tls: Optional[bool] = None
    timeout: Optional[int] = Field(None, ge=1, le=300)
    username_attribute: Optional[str] = None
    email_attribute: Optional[str] = None
    first_name_attribute: Optional[str] = None
    last_name_attribute: Optional[str] = None
    display_name_attribute: Optional[str] = None


class LDAPProviderResponse(LDAPProviderBase):
    """LDAP provider response model"""
    id: str
    sso_provider_id: str
    
    class Config:
        from_attributes = True


class SSOSessionBase(BaseModel):
    """Base SSO session model"""
    session_id: str
    username: str
    email: Optional[EmailStr] = None
    external_user_id: Optional[str] = None
    login_method: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class SSOSessionCreate(SSOSessionBase):
    """SSO session creation model"""
    provider_id: str
    user_id: Optional[str] = None
    external_session_id: Optional[str] = None
    expires_at: Optional[datetime] = None


class SSOSessionResponse(SSOSessionBase):
    """SSO session response model"""
    id: str
    provider_id: str
    user_id: Optional[str] = None
    external_session_id: Optional[str] = None
    is_active: bool
    is_expired: bool
    created_at: datetime
    last_activity: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SSOAuditLogBase(BaseModel):
    """Base SSO audit log model"""
    event_type: SSOEventType
    event_status: SSOEventStatus
    event_message: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    external_user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SSOAuditLogCreate(SSOAuditLogBase):
    """SSO audit log creation model"""
    provider_id: str
    user_id: Optional[str] = None


class SSOAuditLogResponse(SSOAuditLogBase):
    """SSO audit log response model"""
    id: str
    provider_id: str
    user_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SSOLoginRequest(BaseModel):
    """SSO login request model"""
    provider_id: str
    username: str
    password: Optional[str] = None
    saml_response: Optional[str] = None
    relay_state: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class SSOLoginResponse(BaseModel):
    """SSO login response model"""
    success: bool
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    redirect_url: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None


class SSOLogoutRequest(BaseModel):
    """SSO logout request model"""
    session_id: Optional[str] = None
    saml_request: Optional[str] = None
    relay_state: Optional[str] = None


class SSOLogoutResponse(BaseModel):
    """SSO logout response model"""
    success: bool
    message: str
    redirect_url: Optional[str] = None


class SSOTestConnectionRequest(BaseModel):
    """SSO test connection request model"""
    provider_type: SSOProviderType
    configuration: Dict[str, Any]


class SSOTestConnectionResponse(BaseModel):
    """SSO test connection response model"""
    success: bool
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class SSOUserProvisionRequest(BaseModel):
    """SSO user provision request model"""
    provider_id: str
    username: str
    attributes: Dict[str, Any]
    force_provision: bool = False


class SSOUserProvisionResponse(BaseModel):
    """SSO user provision response model"""
    success: bool
    message: str
    user_id: Optional[str] = None
    user_created: bool = False
    user_updated: bool = False


class SSOMetadataResponse(BaseModel):
    """SSO metadata response model"""
    provider_type: SSOProviderType
    metadata: Dict[str, Any]
    metadata_url: Optional[str] = None
    metadata_xml: Optional[str] = None


class SSOStatsResponse(BaseModel):
    """SSO statistics response model"""
    total_providers: int
    active_providers: int
    saml_providers: int
    ldap_providers: int
    oauth2_providers: int
    total_sessions: int
    active_sessions: int
    total_logins_today: int
    total_logins_week: int
    total_logins_month: int
    failed_logins_today: int


class SSOBulkProvisionRequest(BaseModel):
    """SSO bulk provision request model"""
    provider_id: str
    users: List[Dict[str, Any]]
    force_provision: bool = False


class SSOBulkProvisionResponse(BaseModel):
    """SSO bulk provision response model"""
    total_users: int
    provisioned_users: int
    updated_users: int
    failed_users: int
    results: List[Dict[str, Any]]