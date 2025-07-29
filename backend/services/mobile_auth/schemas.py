"""
Mobile Authentication Schemas
Pydantic models for mobile authentication API
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class DeviceType(str, Enum):
    """Device types"""
    IOS = "ios"
    ANDROID = "android"


class BiometricType(str, Enum):
    """Biometric authentication types"""
    FACE = "face"
    FINGERPRINT = "fingerprint"
    IRIS = "iris"


class NotificationType(str, Enum):
    """Push notification types"""
    GRADE = "grade"
    ATTENDANCE = "attendance"
    PAYMENT = "payment"
    ANNOUNCEMENT = "announcement"
    MESSAGE = "message"
    REMINDER = "reminder"


class DeviceRegistrationBase(BaseModel):
    """Base device registration model"""
    device_id: str = Field(..., min_length=1, max_length=255)
    device_name: Optional[str] = None
    device_type: DeviceType
    device_model: Optional[str] = None
    device_os: Optional[str] = None
    device_os_version: Optional[str] = None
    app_version: Optional[str] = None
    app_build: Optional[str] = None
    fcm_token: Optional[str] = None
    apns_token: Optional[str] = None
    device_fingerprint: Optional[str] = None


class DeviceRegistrationCreate(DeviceRegistrationBase):
    """Device registration creation model"""
    user_id: Optional[str] = None  # Optional for initial registration


class DeviceRegistrationUpdate(BaseModel):
    """Device registration update model"""
    device_name: Optional[str] = None
    fcm_token: Optional[str] = None
    apns_token: Optional[str] = None
    app_version: Optional[str] = None
    app_build: Optional[str] = None
    is_trusted: Optional[bool] = None
    biometric_enabled: Optional[bool] = None
    biometric_type: Optional[BiometricType] = None


class DeviceRegistrationResponse(DeviceRegistrationBase):
    """Device registration response model"""
    id: str
    user_id: Optional[str] = None
    is_trusted: bool
    is_active: bool
    biometric_enabled: bool
    biometric_type: Optional[BiometricType] = None
    last_ip_address: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MobileLoginRequest(BaseModel):
    """Mobile login request model"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")
    device_id: str = Field(..., description="Device ID")
    device_info: Optional[DeviceRegistrationCreate] = None
    school_subdomain: Optional[str] = Field(None, description="School subdomain")


class MobileLoginResponse(BaseModel):
    """Mobile login response model"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: Dict[str, Any]
    device: DeviceRegistrationResponse
    school: Optional[Dict[str, Any]] = None


class MobileAuthCodeRequest(BaseModel):
    """Mobile auth code request model"""
    client_id: str = Field(..., description="Mobile app client ID")
    device_id: str = Field(..., description="Device ID")


class MobileAuthCodeResponse(BaseModel):
    """Mobile auth code response model"""
    code: str
    expires_in: int = 300  # 5 minutes
    instructions: str = "Enter this code in the web browser to link your device"


class MobileAuthCodeVerifyRequest(BaseModel):
    """Mobile auth code verification request"""
    code: str = Field(..., min_length=6, max_length=10)
    user_id: str = Field(..., description="User ID from web session")


class MobileAuthCodeVerifyResponse(BaseModel):
    """Mobile auth code verification response"""
    success: bool
    message: str
    device_id: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    refresh_token: str = Field(..., description="Refresh token")
    device_id: str = Field(..., description="Device ID")


class RefreshTokenResponse(BaseModel):
    """Refresh token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class BiometricAuthRequest(BaseModel):
    """Biometric authentication request"""
    device_id: str = Field(..., description="Device ID")
    biometric_token: str = Field(..., description="Biometric authentication token")
    biometric_type: BiometricType


class BiometricAuthResponse(BaseModel):
    """Biometric authentication response"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class PushNotificationTokenUpdate(BaseModel):
    """Push notification token update"""
    device_id: str
    fcm_token: Optional[str] = None
    apns_token: Optional[str] = None


class PushNotificationRequest(BaseModel):
    """Push notification request"""
    user_ids: List[str] = Field(..., description="Target user IDs")
    title: str = Field(..., max_length=255)
    body: str
    notification_type: NotificationType
    data: Dict[str, Any] = Field(default_factory=dict)
    priority: str = Field("normal", description="normal or high")
    school_id: Optional[str] = None


class PushNotificationResponse(BaseModel):
    """Push notification response"""
    id: str
    title: str
    body: str
    notification_type: NotificationType
    status: str
    created_at: datetime
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MobileApiKeyBase(BaseModel):
    """Base mobile API key model"""
    name: str = Field(..., min_length=1, max_length=255)
    permissions: List[str] = Field(default_factory=list)
    rate_limit: int = Field(1000, ge=100, le=10000)
    allowed_platforms: List[DeviceType] = Field(default_factory=list)
    allowed_versions: List[str] = Field(default_factory=list)


class MobileApiKeyCreate(MobileApiKeyBase):
    """Mobile API key creation model"""
    school_id: str = Field(..., description="School ID")
    expires_at: Optional[datetime] = None


class MobileApiKeyUpdate(BaseModel):
    """Mobile API key update model"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    permissions: Optional[List[str]] = None
    rate_limit: Optional[int] = Field(None, ge=100, le=10000)
    allowed_platforms: Optional[List[DeviceType]] = None
    allowed_versions: Optional[List[str]] = None
    is_active: Optional[bool] = None


class MobileApiKeyResponse(MobileApiKeyBase):
    """Mobile API key response model"""
    id: str
    school_id: str
    api_key: str
    is_active: bool
    last_used_at: Optional[datetime] = None
    usage_count: int
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    is_expired: bool
    
    class Config:
        from_attributes = True


class MobileSessionResponse(BaseModel):
    """Mobile session response model"""
    id: str
    user_id: str
    device_id: str
    session_id: str
    is_active: bool
    ip_address: Optional[str] = None
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_expired: bool
    
    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    """Device list response"""
    devices: List[DeviceRegistrationResponse]
    total: int


class SessionListResponse(BaseModel):
    """Session list response"""
    sessions: List[MobileSessionResponse]
    total: int
    active_count: int


class NotificationListResponse(BaseModel):
    """Notification list response"""
    notifications: List[PushNotificationResponse]
    total: int
    unread_count: int


class MobileAppConfig(BaseModel):
    """Mobile app configuration"""
    minimum_app_version: str
    latest_app_version: str
    force_update: bool
    update_url_ios: str
    update_url_android: str
    features: Dict[str, bool]
    api_endpoints: Dict[str, str]
    push_notification_enabled: bool
    biometric_auth_enabled: bool


class DeviceSecurityCheck(BaseModel):
    """Device security check response"""
    is_rooted: bool
    is_jailbroken: bool
    is_emulator: bool
    has_debugger: bool
    has_tampering: bool
    security_score: int = Field(ge=0, le=100)
    recommendations: List[str]