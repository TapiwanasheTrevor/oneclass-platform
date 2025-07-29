"""
Mobile Authentication API Routes
FastAPI routes for mobile authentication
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db_session
from shared.auth import get_current_user, require_permissions, verify_api_key
from shared.models.platform import 
from shared.models.platform_user import PlatformUserDB as User
from shared.exceptions import (
    ValidationError,
    NotFoundError,
    ConflictError,
    AuthenticationError
)
from .service import MobileAuthService
from .schemas import (
    DeviceRegistrationCreate,
    DeviceRegistrationUpdate,
    DeviceRegistrationResponse,
    MobileLoginRequest,
    MobileLoginResponse,
    MobileAuthCodeRequest,
    MobileAuthCodeResponse,
    MobileAuthCodeVerifyRequest,
    MobileAuthCodeVerifyResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    BiometricAuthRequest,
    BiometricAuthResponse,
    PushNotificationRequest,
    PushNotificationResponse,
    PushNotificationTokenUpdate,
    MobileApiKeyCreate,
    MobileApiKeyUpdate,
    MobileApiKeyResponse,
    MobileSessionResponse,
    DeviceListResponse,
    SessionListResponse,
    NotificationListResponse,
    MobileAppConfig,
    DeviceSecurityCheck
)

router = APIRouter(prefix="/mobile", tags=["Mobile Authentication"])


@router.post("/auth/login", response_model=MobileLoginResponse)
async def mobile_login(
    login_request: MobileLoginRequest,
    request: Request,
    service: MobileAuthService = Depends()
):
    """Mobile app login"""
    try:
        # Add IP address to request
        login_request.ip_address = request.client.host
        
        return await service.mobile_login(login_request)
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/auth/code", response_model=MobileAuthCodeResponse)
async def generate_auth_code(
    code_request: MobileAuthCodeRequest,
    x_api_key: str = Header(...),
    service: MobileAuthService = Depends()
):
    """Generate authentication code for device linking"""
    try:
        # Verify API key
        if not await verify_api_key(x_api_key):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
        
        return await service.generate_auth_code(code_request)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/auth/code/verify", response_model=MobileAuthCodeVerifyResponse)
async def verify_auth_code(
    verify_request: MobileAuthCodeVerifyRequest,
    current_user: User = Depends(get_current_user),
    service: MobileAuthService = Depends()
):
    """Verify authentication code from web session"""
    try:
        # Use current user's ID
        verify_request.user_id = str(current_user.id)
        
        return await service.verify_auth_code(verify_request)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/auth/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    service: MobileAuthService = Depends()
):
    """Refresh access token"""
    try:
        return await service.refresh_token(refresh_request)
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/auth/biometric", response_model=BiometricAuthResponse)
async def biometric_auth(
    biometric_request: BiometricAuthRequest,
    x_api_key: str = Header(...),
    service: MobileAuthService = Depends()
):
    """Authenticate using biometric data"""
    try:
        # Verify API key
        if not await verify_api_key(x_api_key):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
        
        return await service.biometric_auth(biometric_request)
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/auth/logout")
async def logout_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    service: MobileAuthService = Depends()
):
    """Logout from specific device"""
    try:
        await service.logout_device(device_id, str(current_user.id))
        return {"message": "Device logged out successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/auth/logout-all")
async def logout_all_devices(
    current_user: User = Depends(get_current_user),
    service: MobileAuthService = Depends()
):
    """Logout from all devices"""
    try:
        count = await service.logout_all_devices(str(current_user.id))
        return {"message": f"Logged out from {count} devices"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Device Management Routes

@router.get("/devices", response_model=DeviceListResponse)
async def get_user_devices(
    current_user: User = Depends(get_current_user),
    service: MobileAuthService = Depends()
):
    """Get all devices for current user"""
    try:
        devices = await service.get_user_devices(str(current_user.id))
        return DeviceListResponse(
            devices=devices,
            total=len(devices)
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/devices", response_model=DeviceRegistrationResponse)
async def register_device(
    device_data: DeviceRegistrationCreate,
    current_user: User = Depends(get_current_user),
    service: MobileAuthService = Depends()
):
    """Register a new device"""
    try:
        return await service.register_device(device_data, str(current_user.id))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/devices/{device_id}", response_model=DeviceRegistrationResponse)
async def update_device(
    device_id: str,
    device_update: DeviceRegistrationUpdate,
    current_user: User = Depends(get_current_user),
    service: MobileAuthService = Depends()
):
    """Update device information"""
    try:
        # This would need implementation in service
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/devices/{device_id}")
async def remove_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    service: MobileAuthService = Depends()
):
    """Remove a device"""
    try:
        await service.remove_device(device_id, str(current_user.id))
        return {"message": "Device removed successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Push Notification Routes

@router.put("/devices/{device_id}/push-token")
async def update_push_token(
    device_id: str,
    token_update: PushNotificationTokenUpdate,
    current_user: User = Depends(get_current_user),
    service: MobileAuthService = Depends()
):
    """Update push notification token"""
    try:
        await service.update_push_token(
            device_id,
            token_update.fcm_token,
            token_update.apns_token
        )
        return {"message": "Push token updated successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/notifications/send", response_model=List[PushNotificationResponse])
async def send_push_notification(
    notification: PushNotificationRequest,
    current_user: User = Depends(get_current_user),
    service: MobileAuthService = Depends()
):
    """Send push notification"""
    try:
        # Check permissions
        if notification.school_id:
            await require_permissions(current_user, "notification:send", notification.school_id)
        
        return await service.send_push_notification(notification)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    service: MobileAuthService = Depends()
):
    """Get push notifications for current user"""
    try:
        # This would need implementation in service
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    service: MobileAuthService = Depends()
):
    """Mark notification as read"""
    try:
        # This would need implementation in service
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# API Key Management Routes

@router.post("/api-keys", response_model=MobileApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: MobileApiKeyCreate,
    current_user: User = Depends(get_current_user),
    service: MobileAuthService = Depends()
):
    """Create mobile API key for school"""
    try:
        # Check permissions
        await require_permissions(current_user, "api_key:create", api_key_data.school_id)
        
        return await service.create_api_key(api_key_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/api-keys/school/{school_id}", response_model=List[MobileApiKeyResponse])
async def get_school_api_keys(
    school_id: str,
    current_user: User = Depends(get_current_user),
    service: MobileAuthService = Depends()
):
    """Get API keys for school"""
    try:
        # Check permissions
        await require_permissions(current_user, "api_key:read", school_id)
        
        # This would need implementation in service
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/api-keys/{api_key_id}", response_model=MobileApiKeyResponse)
async def update_api_key(
    api_key_id: str,
    api_key_update: MobileApiKeyUpdate,
    current_user: User = Depends(get_current_user),
    service: MobileAuthService = Depends()
):
    """Update API key"""
    try:
        # This would need implementation in service
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/api-keys/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: str,
    current_user: User = Depends(get_current_user),
    service: MobileAuthService = Depends()
):
    """Delete API key"""
    try:
        # This would need implementation in service
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Mobile App Configuration

@router.get("/config", response_model=MobileAppConfig)
async def get_mobile_config(
    platform: str,
    version: str,
    x_api_key: str = Header(...),
    service: MobileAuthService = Depends()
):
    """Get mobile app configuration"""
    try:
        # Verify API key
        if not await verify_api_key(x_api_key):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
        
        # Return configuration
        return MobileAppConfig(
            minimum_app_version="1.0.0",
            latest_app_version="1.2.0",
            force_update=False,
            update_url_ios="https://apps.apple.com/app/oneclass",
            update_url_android="https://play.google.com/store/apps/details?id=com.oneclass",
            features={
                "biometric_auth": True,
                "offline_mode": True,
                "push_notifications": True,
                "qr_code_login": True,
                "document_upload": True,
                "video_lessons": True
            },
            api_endpoints={
                "base_url": "https://api.oneclass.ac.zw",
                "auth": "/api/v1/mobile/auth",
                "sync": "/api/v1/mobile/sync",
                "media": "/api/v1/mobile/media"
            },
            push_notification_enabled=True,
            biometric_auth_enabled=True
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/security/check", response_model=DeviceSecurityCheck)
async def check_device_security(
    device_info: Dict[str, Any],
    x_api_key: str = Header(...),
    service: MobileAuthService = Depends()
):
    """Check device security status"""
    try:
        # Verify API key
        if not await verify_api_key(x_api_key):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
        
        # Analyze device security
        is_rooted = device_info.get("is_rooted", False)
        is_jailbroken = device_info.get("is_jailbroken", False)
        is_emulator = device_info.get("is_emulator", False)
        has_debugger = device_info.get("has_debugger", False)
        has_tampering = device_info.get("has_tampering", False)
        
        # Calculate security score
        security_score = 100
        recommendations = []
        
        if is_rooted or is_jailbroken:
            security_score -= 40
            recommendations.append("Device is rooted/jailbroken. This poses security risks.")
        
        if is_emulator:
            security_score -= 20
            recommendations.append("Running on emulator. Use physical device for better security.")
        
        if has_debugger:
            security_score -= 20
            recommendations.append("Debugger detected. Disable debugging for production.")
        
        if has_tampering:
            security_score -= 20
            recommendations.append("App tampering detected. Reinstall from official source.")
        
        return DeviceSecurityCheck(
            is_rooted=is_rooted,
            is_jailbroken=is_jailbroken,
            is_emulator=is_emulator,
            has_debugger=has_debugger,
            has_tampering=has_tampering,
            security_score=max(0, security_score),
            recommendations=recommendations
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Session Management Routes

@router.get("/sessions", response_model=SessionListResponse)
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    service: MobileAuthService = Depends()
):
    """Get all active sessions for current user"""
    try:
        # This would need implementation in service
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def terminate_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    service: MobileAuthService = Depends()
):
    """Terminate specific session"""
    try:
        # This would need implementation in service
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))