"""
Mobile Authentication Service
Core service for mobile app authentication and device management
"""

import uuid
import secrets
import string
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, and_, or_, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import logging
import jwt
import hashlib
import hmac

from shared.database import get_db_session
from shared.exceptions import (
    ValidationError,
    NotFoundError,
    ConflictError,
    AuthenticationError,
    ExternalServiceError,
)
from shared.auth import create_access_token, create_refresh_token, verify_password
from shared.models.platform_user import PlatformUser as User
from shared.models.platform import School
from .models import (
    DeviceRegistration,
    MobileSession,
    MobileAuthCode,
    MobileApiKey,
    MobilePushNotification,
)
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
    MobileApiKeyCreate,
    MobileApiKeyResponse,
    DeviceType,
)

logger = logging.getLogger(__name__)


class MobileAuthService:
    """Service for mobile authentication and device management"""

    def __init__(self):
        self.access_token_expire_minutes = 60  # 1 hour
        self.refresh_token_expire_days = 30
        self.auth_code_expire_minutes = 5
        self.max_devices_per_user = 5
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=30)

    async def register_device(
        self, device_data: DeviceRegistrationCreate, user_id: Optional[str] = None
    ) -> DeviceRegistrationResponse:
        """Register a new device"""
        async with get_db_session() as session:
            # Check if device already exists
            existing_device = await session.execute(
                select(DeviceRegistration).where(
                    DeviceRegistration.device_id == device_data.device_id
                )
            )
            device = existing_device.scalar_one_or_none()

            if device:
                # Update existing device
                for field, value in device_data.dict(exclude_unset=True).items():
                    setattr(device, field, value)

                device.updated_at = datetime.utcnow()
                device.last_used_at = datetime.utcnow()
            else:
                # Create new device
                device = DeviceRegistration(
                    id=uuid.uuid4(), user_id=user_id, **device_data.dict()
                )
                session.add(device)

            await session.commit()
            await session.refresh(device)

            logger.info(f"Device registered: {device.device_id}")

            return DeviceRegistrationResponse.from_orm(device)

    async def mobile_login(
        self, login_request: MobileLoginRequest
    ) -> MobileLoginResponse:
        """Authenticate user from mobile app"""
        async with get_db_session() as session:
            # Get school if subdomain provided
            school = None
            if login_request.school_subdomain:
                school_result = await session.execute(
                    select(School).where(
                        School.subdomain == login_request.school_subdomain
                    )
                )
                school = school_result.scalar_one_or_none()
                if not school:
                    raise NotFoundError(
                        f"School not found: {login_request.school_subdomain}"
                    )

            # Find user
            user_query = select(User).where(
                or_(
                    User.username == login_request.username,
                    User.email == login_request.username,
                )
            )

            if school:
                user_query = user_query.where(User.school_id == school.id)

            result = await session.execute(user_query)
            user = result.scalar_one_or_none()

            if not user:
                raise AuthenticationError("Invalid credentials")

            # Verify password
            if not verify_password(login_request.password, user.password_hash):
                raise AuthenticationError("Invalid credentials")

            # Check if user is active
            if not user.is_active:
                raise AuthenticationError("Account is disabled")

            # Register or update device
            if login_request.device_info:
                device_data = login_request.device_info
                device_data.user_id = str(user.id)
            else:
                device_data = DeviceRegistrationCreate(
                    device_id=login_request.device_id,
                    device_type=DeviceType.ANDROID,  # Default
                    user_id=str(user.id),
                )

            device = await self.register_device(device_data, str(user.id))

            # Create mobile session
            access_token = create_access_token(
                data={
                    "sub": str(user.id),
                    "email": user.email,
                    "device_id": device.id,
                    "school_id": str(user.school_id) if user.school_id else None,
                }
            )

            refresh_token = create_refresh_token(
                data={"sub": str(user.id), "device_id": device.id}
            )

            # Save session
            session_id = secrets.token_urlsafe(32)
            mobile_session = MobileSession(
                id=uuid.uuid4(),
                user_id=user.id,
                device_id=device.id,
                access_token=access_token,
                refresh_token=refresh_token,
                session_id=session_id,
                expires_at=datetime.utcnow()
                + timedelta(days=self.refresh_token_expire_days),
            )

            session.add(mobile_session)
            await session.commit()

            # Prepare response
            user_data = {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "school_id": str(user.school_id) if user.school_id else None,
            }

            school_data = None
            if school:
                school_data = {
                    "id": str(school.id),
                    "name": school.name,
                    "subdomain": school.subdomain,
                    "type": school.type,
                }

            logger.info(f"Mobile login successful for user: {user.email}")

            return MobileLoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self.access_token_expire_minutes * 60,
                user=user_data,
                device=device,
                school=school_data,
            )

    async def generate_auth_code(
        self, request: MobileAuthCodeRequest
    ) -> MobileAuthCodeResponse:
        """Generate authentication code for device linking"""
        async with get_db_session() as session:
            # Generate unique 6-digit code
            code = self._generate_auth_code()

            # Check if code already exists
            while await self._auth_code_exists(session, code):
                code = self._generate_auth_code()

            # Create auth code
            auth_code = MobileAuthCode(
                id=uuid.uuid4(),
                code=code,
                client_id=request.client_id,
                expires_at=datetime.utcnow()
                + timedelta(minutes=self.auth_code_expire_minutes),
            )

            session.add(auth_code)
            await session.commit()

            logger.info(f"Auth code generated for device: {request.device_id}")

            return MobileAuthCodeResponse(
                code=code, expires_in=self.auth_code_expire_minutes * 60
            )

    async def verify_auth_code(
        self, request: MobileAuthCodeVerifyRequest
    ) -> MobileAuthCodeVerifyResponse:
        """Verify authentication code and link device to user"""
        async with get_db_session() as session:
            # Find auth code
            result = await session.execute(
                select(MobileAuthCode).where(MobileAuthCode.code == request.code)
            )
            auth_code = result.scalar_one_or_none()

            if not auth_code:
                return MobileAuthCodeVerifyResponse(
                    success=False, message="Invalid code"
                )

            # Check if code is valid
            if not auth_code.is_valid:
                return MobileAuthCodeVerifyResponse(
                    success=False, message="Code is expired or already used"
                )

            # Link code to user
            auth_code.user_id = request.user_id
            auth_code.is_used = True
            auth_code.used_at = datetime.utcnow()

            await session.commit()

            logger.info(f"Auth code verified for user: {request.user_id}")

            return MobileAuthCodeVerifyResponse(
                success=True,
                message="Device linked successfully",
                device_id=auth_code.client_id,
            )

    async def refresh_token(self, request: RefreshTokenRequest) -> RefreshTokenResponse:
        """Refresh access token"""
        async with get_db_session() as session:
            # Find session by refresh token
            result = await session.execute(
                select(MobileSession)
                .where(MobileSession.refresh_token == request.refresh_token)
                .options(selectinload(MobileSession.user))
            )
            mobile_session = result.scalar_one_or_none()

            if not mobile_session:
                raise AuthenticationError("Invalid refresh token")

            if not mobile_session.is_active or mobile_session.is_expired:
                raise AuthenticationError("Session expired")

            # Verify device
            if str(mobile_session.device_id) != request.device_id:
                raise AuthenticationError("Invalid device")

            # Generate new tokens
            access_token = create_access_token(
                data={
                    "sub": str(mobile_session.user_id),
                    "email": mobile_session.user.email,
                    "device_id": str(mobile_session.device_id),
                    "school_id": (
                        str(mobile_session.user.school_id)
                        if mobile_session.user.school_id
                        else None
                    ),
                }
            )

            refresh_token = create_refresh_token(
                data={
                    "sub": str(mobile_session.user_id),
                    "device_id": str(mobile_session.device_id),
                }
            )

            # Update session
            mobile_session.access_token = access_token
            mobile_session.refresh_token = refresh_token
            mobile_session.last_activity = datetime.utcnow()

            await session.commit()

            logger.info(f"Token refreshed for user: {mobile_session.user_id}")

            return RefreshTokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self.access_token_expire_minutes * 60,
            )

    async def biometric_auth(
        self, request: BiometricAuthRequest
    ) -> BiometricAuthResponse:
        """Authenticate using biometric data"""
        async with get_db_session() as session:
            # Get device
            result = await session.execute(
                select(DeviceRegistration)
                .where(DeviceRegistration.device_id == request.device_id)
                .options(selectinload(DeviceRegistration.user))
            )
            device = result.scalar_one_or_none()

            if not device:
                raise NotFoundError("Device not found")

            if not device.biometric_enabled:
                raise ValidationError("Biometric authentication not enabled")

            if device.biometric_type != request.biometric_type:
                raise ValidationError("Biometric type mismatch")

            # Verify biometric token (implementation depends on platform)
            # For now, we'll do a simple verification
            if not self._verify_biometric_token(request.biometric_token, device):
                raise AuthenticationError("Biometric authentication failed")

            # Create session
            access_token = create_access_token(
                data={
                    "sub": str(device.user_id),
                    "email": device.user.email,
                    "device_id": str(device.id),
                    "school_id": (
                        str(device.user.school_id) if device.user.school_id else None
                    ),
                }
            )

            refresh_token = create_refresh_token(
                data={"sub": str(device.user_id), "device_id": str(device.id)}
            )

            # Save session
            session_id = secrets.token_urlsafe(32)
            mobile_session = MobileSession(
                id=uuid.uuid4(),
                user_id=device.user_id,
                device_id=device.id,
                access_token=access_token,
                refresh_token=refresh_token,
                session_id=session_id,
                expires_at=datetime.utcnow()
                + timedelta(days=self.refresh_token_expire_days),
            )

            session.add(mobile_session)
            await session.commit()

            logger.info(f"Biometric auth successful for user: {device.user_id}")

            return BiometricAuthResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self.access_token_expire_minutes * 60,
            )

    async def logout_device(self, device_id: str, user_id: str) -> bool:
        """Logout from specific device"""
        async with get_db_session() as session:
            # Get device
            result = await session.execute(
                select(DeviceRegistration).where(
                    and_(
                        DeviceRegistration.device_id == device_id,
                        DeviceRegistration.user_id == user_id,
                    )
                )
            )
            device = result.scalar_one_or_none()

            if not device:
                raise NotFoundError("Device not found")

            # Deactivate all sessions for this device
            await session.execute(
                update(MobileSession)
                .where(MobileSession.device_id == device.id)
                .values(is_active=False)
            )

            await session.commit()

            logger.info(f"Device logged out: {device_id}")

            return True

    async def logout_all_devices(self, user_id: str) -> int:
        """Logout from all devices"""
        async with get_db_session() as session:
            # Deactivate all sessions for this user
            result = await session.execute(
                update(MobileSession)
                .where(MobileSession.user_id == user_id)
                .values(is_active=False)
            )

            await session.commit()

            count = result.rowcount
            logger.info(
                f"All devices logged out for user: {user_id} ({count} sessions)"
            )

            return count

    async def get_user_devices(self, user_id: str) -> List[DeviceRegistrationResponse]:
        """Get all devices for a user"""
        async with get_db_session() as session:
            result = await session.execute(
                select(DeviceRegistration)
                .where(DeviceRegistration.user_id == user_id)
                .order_by(DeviceRegistration.last_used_at.desc())
            )
            devices = result.scalars().all()

            return [DeviceRegistrationResponse.from_orm(device) for device in devices]

    async def remove_device(self, device_id: str, user_id: str) -> bool:
        """Remove a device"""
        async with get_db_session() as session:
            # Get device
            result = await session.execute(
                select(DeviceRegistration).where(
                    and_(
                        DeviceRegistration.device_id == device_id,
                        DeviceRegistration.user_id == user_id,
                    )
                )
            )
            device = result.scalar_one_or_none()

            if not device:
                raise NotFoundError("Device not found")

            # Delete sessions
            await session.execute(
                delete(MobileSession).where(MobileSession.device_id == device.id)
            )

            # Delete device
            await session.delete(device)
            await session.commit()

            logger.info(f"Device removed: {device_id}")

            return True

    async def update_push_token(
        self,
        device_id: str,
        fcm_token: Optional[str] = None,
        apns_token: Optional[str] = None,
    ) -> bool:
        """Update push notification token for device"""
        async with get_db_session() as session:
            result = await session.execute(
                select(DeviceRegistration).where(
                    DeviceRegistration.device_id == device_id
                )
            )
            device = result.scalar_one_or_none()

            if not device:
                raise NotFoundError("Device not found")

            if fcm_token:
                device.fcm_token = fcm_token
            if apns_token:
                device.apns_token = apns_token

            device.updated_at = datetime.utcnow()
            await session.commit()

            logger.info(f"Push token updated for device: {device_id}")

            return True

    async def send_push_notification(
        self, notification: PushNotificationRequest
    ) -> List[PushNotificationResponse]:
        """Send push notification to users"""
        async with get_db_session() as session:
            notifications = []

            for user_id in notification.user_ids:
                # Get user's devices
                result = await session.execute(
                    select(DeviceRegistration).where(
                        and_(
                            DeviceRegistration.user_id == user_id,
                            DeviceRegistration.is_active == True,
                        )
                    )
                )
                devices = result.scalars().all()

                for device in devices:
                    # Create notification record
                    push_notification = MobilePushNotification(
                        id=uuid.uuid4(),
                        user_id=user_id,
                        device_id=device.id,
                        title=notification.title,
                        body=notification.body,
                        data=notification.data,
                        notification_type=notification.notification_type,
                        priority=notification.priority,
                    )

                    session.add(push_notification)

                    # Send to push service (FCM/APNS)
                    if device.fcm_token or device.apns_token:
                        await self._send_to_push_service(push_notification, device)

                    notifications.append(
                        PushNotificationResponse.from_orm(push_notification)
                    )

            await session.commit()

            logger.info(f"Push notifications sent: {len(notifications)}")

            return notifications

    async def create_api_key(
        self, api_key_data: MobileApiKeyCreate
    ) -> MobileApiKeyResponse:
        """Create mobile API key for school"""
        async with get_db_session() as session:
            # Generate API key and secret
            api_key = self._generate_api_key()
            api_secret = self._generate_api_secret()

            # Create API key record
            mobile_api_key = MobileApiKey(
                id=uuid.uuid4(),
                school_id=api_key_data.school_id,
                name=api_key_data.name,
                api_key=api_key,
                api_secret=self._hash_secret(api_secret),
                permissions=api_key_data.permissions,
                rate_limit=api_key_data.rate_limit,
                allowed_platforms=api_key_data.allowed_platforms,
                allowed_versions=api_key_data.allowed_versions,
                expires_at=api_key_data.expires_at,
            )

            session.add(mobile_api_key)
            await session.commit()
            await session.refresh(mobile_api_key)

            # Return with unhashed secret (only shown once)
            response = MobileApiKeyResponse.from_orm(mobile_api_key)
            response.api_secret = api_secret

            logger.info(f"API key created: {mobile_api_key.name}")

            return response

    def _generate_auth_code(self) -> str:
        """Generate 6-digit authentication code"""
        return "".join(secrets.choice(string.digits) for _ in range(6))

    async def _auth_code_exists(self, session: AsyncSession, code: str) -> bool:
        """Check if auth code already exists"""
        result = await session.execute(
            select(MobileAuthCode).where(MobileAuthCode.code == code)
        )
        return result.scalar_one_or_none() is not None

    def _verify_biometric_token(self, token: str, device: DeviceRegistration) -> bool:
        """Verify biometric authentication token"""
        # This would integrate with platform-specific biometric APIs
        # For now, we'll do a simple verification
        expected_token = hmac.new(
            device.device_fingerprint.encode() if device.device_fingerprint else b"",
            f"{device.user_id}:{device.device_id}".encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(token, expected_token)

    def _generate_api_key(self) -> str:
        """Generate API key"""
        return f"mak_{secrets.token_urlsafe(32)}"

    def _generate_api_secret(self) -> str:
        """Generate API secret"""
        return f"mas_{secrets.token_urlsafe(48)}"

    def _hash_secret(self, secret: str) -> str:
        """Hash API secret"""
        return hashlib.sha256(secret.encode()).hexdigest()

    async def _send_to_push_service(
        self, notification: MobilePushNotification, device: DeviceRegistration
    ):
        """Send notification to FCM/APNS"""
        # This would integrate with Firebase Cloud Messaging or Apple Push Notification Service
        # For now, we'll just mark as sent
        notification.status = "sent"
        notification.sent_at = datetime.utcnow()

        logger.info(f"Push notification sent to device: {device.device_id}")
