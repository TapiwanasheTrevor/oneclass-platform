"""
Mobile Authentication Tests
Comprehensive test suite for mobile authentication service
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import uuid
import secrets

from backend.services.mobile_auth.service import MobileAuthService
from backend.services.mobile_auth.models import DeviceRegistration, MobileSession, MobileAuthCode
from backend.services.mobile_auth.schemas import (
    DeviceRegistrationCreate,
    MobileLoginRequest,
    MobileAuthCodeRequest,
    MobileAuthCodeVerifyRequest,
    RefreshTokenRequest,
    BiometricAuthRequest,
    DeviceType,
    BiometricType
)
from shared.exceptions import ValidationError, NotFoundError, ConflictError, AuthenticationError


class TestMobileAuthService:
    """Test mobile authentication service"""
    
    @pytest.fixture
    def service(self):
        return MobileAuthService()
    
    @pytest.fixture
    def mock_user_id(self):
        return str(uuid.uuid4())
    
    @pytest.fixture
    def mock_device_id(self):
        return "test_device_123"
    
    @pytest.fixture
    def device_registration_data(self, mock_device_id):
        return DeviceRegistrationCreate(
            device_id=mock_device_id,
            device_name="Test iPhone",
            device_type=DeviceType.IOS,
            device_model="iPhone 14",
            device_os="iOS",
            device_os_version="16.0",
            app_version="1.0.0",
            app_build="100",
            fcm_token="test_fcm_token",
            device_fingerprint="test_fingerprint"
        )
    
    @pytest.fixture
    def mobile_login_data(self, mock_device_id):
        return MobileLoginRequest(
            username="testuser@example.com",
            password="testpassword123",
            device_id=mock_device_id,
            school_subdomain="testschool"
        )
    
    @pytest.mark.asyncio
    async def test_register_device_new(self, service, device_registration_data, mock_user_id):
        """Test registering a new device"""
        with patch('backend.services.mobile_auth.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock no existing device
            mock_session.execute.return_value.scalar_one_or_none.return_value = None
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            
            # Mock device creation
            mock_device = Mock()
            mock_device.id = str(uuid.uuid4())
            mock_device.device_id = device_registration_data.device_id
            mock_device.device_name = device_registration_data.device_name
            mock_device.device_type = device_registration_data.device_type
            mock_device.is_trusted = False
            mock_device.is_active = True
            mock_device.biometric_enabled = False
            mock_device.created_at = datetime.utcnow()
            mock_device.updated_at = datetime.utcnow()
            mock_device.last_used_at = None
            
            mock_session.refresh.return_value = mock_device
            
            result = await service.register_device(device_registration_data, mock_user_id)
            
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_register_device_existing(self, service, device_registration_data, mock_user_id):
        """Test updating an existing device"""
        with patch('backend.services.mobile_auth.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock existing device
            mock_device = Mock()
            mock_device.id = str(uuid.uuid4())
            mock_device.device_id = device_registration_data.device_id
            mock_device.user_id = mock_user_id
            mock_device.updated_at = datetime.utcnow()
            mock_device.last_used_at = datetime.utcnow()
            
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_device
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            
            result = await service.register_device(device_registration_data, mock_user_id)
            
            mock_session.commit.assert_called_once()
            assert mock_device.updated_at is not None
            assert mock_device.last_used_at is not None
    
    @pytest.mark.asyncio
    async def test_mobile_login_success(self, service, mobile_login_data):
        """Test successful mobile login"""
        with patch('backend.services.mobile_auth.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock school lookup
            mock_school = Mock()
            mock_school.id = str(uuid.uuid4())
            mock_school.name = "Test School"
            mock_school.subdomain = "testschool"
            mock_school.type = "Primary"
            
            # Mock user lookup
            mock_user = Mock()
            mock_user.id = str(uuid.uuid4())
            mock_user.username = "testuser"
            mock_user.email = "testuser@example.com"
            mock_user.password_hash = "hashed_password"
            mock_user.is_active = True
            mock_user.first_name = "Test"
            mock_user.last_name = "User"
            mock_user.role = "student"
            mock_user.school_id = mock_school.id
            
            mock_session.execute.side_effect = [
                Mock(scalar_one_or_none=Mock(return_value=mock_school)),  # School lookup
                Mock(scalar_one_or_none=Mock(return_value=mock_user))     # User lookup
            ]
            
            with patch('backend.services.mobile_auth.service.verify_password') as mock_verify:
                mock_verify.return_value = True
                
                with patch.object(service, 'register_device') as mock_register:
                    mock_device = Mock()
                    mock_device.id = str(uuid.uuid4())
                    mock_device.device_id = mobile_login_data.device_id
                    mock_register.return_value = mock_device
                    
                    with patch('backend.services.mobile_auth.service.create_access_token') as mock_access_token:
                        mock_access_token.return_value = "mock_access_token"
                        
                        with patch('backend.services.mobile_auth.service.create_refresh_token') as mock_refresh_token:
                            mock_refresh_token.return_value = "mock_refresh_token"
                            
                            mock_session.add = Mock()
                            mock_session.commit = AsyncMock()
                            
                            result = await service.mobile_login(mobile_login_data)
                            
                            assert result.access_token == "mock_access_token"
                            assert result.refresh_token == "mock_refresh_token"
                            assert result.user["email"] == "testuser@example.com"
                            assert result.school["name"] == "Test School"
                            mock_session.add.assert_called_once()
                            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mobile_login_invalid_credentials(self, service, mobile_login_data):
        """Test mobile login with invalid credentials"""
        with patch('backend.services.mobile_auth.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock school lookup
            mock_school = Mock()
            mock_school.id = str(uuid.uuid4())
            
            # Mock user not found
            mock_session.execute.side_effect = [
                Mock(scalar_one_or_none=Mock(return_value=mock_school)),  # School lookup
                Mock(scalar_one_or_none=Mock(return_value=None))          # User not found
            ]
            
            with pytest.raises(AuthenticationError):
                await service.mobile_login(mobile_login_data)
    
    @pytest.mark.asyncio
    async def test_generate_auth_code(self, service, mock_device_id):
        """Test generating authentication code"""
        with patch('backend.services.mobile_auth.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock no existing code
            mock_session.execute.return_value.scalar_one_or_none.return_value = None
            mock_session.add = Mock()
            mock_session.commit = AsyncMock()
            
            auth_code_request = MobileAuthCodeRequest(
                client_id="test_client_id",
                device_id=mock_device_id
            )
            
            result = await service.generate_auth_code(auth_code_request)
            
            assert len(result.code) == 6
            assert result.code.isdigit()
            assert result.expires_in == 300
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_auth_code_success(self, service, mock_user_id):
        """Test successful auth code verification"""
        with patch('backend.services.mobile_auth.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock valid auth code
            mock_auth_code = Mock()
            mock_auth_code.code = "123456"
            mock_auth_code.is_valid = True
            mock_auth_code.client_id = "test_client_id"
            mock_auth_code.is_used = False
            mock_auth_code.used_at = None
            
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_auth_code
            mock_session.commit = AsyncMock()
            
            verify_request = MobileAuthCodeVerifyRequest(
                code="123456",
                user_id=mock_user_id
            )
            
            result = await service.verify_auth_code(verify_request)
            
            assert result.success == True
            assert result.message == "Device linked successfully"
            assert result.device_id == "test_client_id"
            assert mock_auth_code.is_used == True
            assert mock_auth_code.user_id == mock_user_id
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_auth_code_invalid(self, service, mock_user_id):
        """Test auth code verification with invalid code"""
        with patch('backend.services.mobile_auth.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock no auth code found
            mock_session.execute.return_value.scalar_one_or_none.return_value = None
            
            verify_request = MobileAuthCodeVerifyRequest(
                code="invalid",
                user_id=mock_user_id
            )
            
            result = await service.verify_auth_code(verify_request)
            
            assert result.success == False
            assert result.message == "Invalid code"
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, service, mock_device_id):
        """Test successful token refresh"""
        with patch('backend.services.mobile_auth.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock valid session
            mock_user = Mock()
            mock_user.id = str(uuid.uuid4())
            mock_user.email = "test@example.com"
            mock_user.school_id = str(uuid.uuid4())
            
            mock_session_obj = Mock()
            mock_session_obj.refresh_token = "valid_refresh_token"
            mock_session_obj.user_id = mock_user.id
            mock_session_obj.device_id = mock_device_id
            mock_session_obj.is_active = True
            mock_session_obj.is_expired = False
            mock_session_obj.user = mock_user
            
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_session_obj
            mock_session.commit = AsyncMock()
            
            with patch('backend.services.mobile_auth.service.create_access_token') as mock_access_token:
                mock_access_token.return_value = "new_access_token"
                
                with patch('backend.services.mobile_auth.service.create_refresh_token') as mock_refresh_token:
                    mock_refresh_token.return_value = "new_refresh_token"
                    
                    refresh_request = RefreshTokenRequest(
                        refresh_token="valid_refresh_token",
                        device_id=mock_device_id
                    )
                    
                    result = await service.refresh_token(refresh_request)
                    
                    assert result.access_token == "new_access_token"
                    assert result.refresh_token == "new_refresh_token"
                    assert result.expires_in == 3600
                    mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, service, mock_device_id):
        """Test token refresh with invalid token"""
        with patch('backend.services.mobile_auth.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock no session found
            mock_session.execute.return_value.scalar_one_or_none.return_value = None
            
            refresh_request = RefreshTokenRequest(
                refresh_token="invalid_token",
                device_id=mock_device_id
            )
            
            with pytest.raises(AuthenticationError):
                await service.refresh_token(refresh_request)
    
    @pytest.mark.asyncio
    async def test_biometric_auth_success(self, service, mock_device_id):
        """Test successful biometric authentication"""
        with patch('backend.services.mobile_auth.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock device with biometric enabled
            mock_user = Mock()
            mock_user.id = str(uuid.uuid4())
            mock_user.email = "test@example.com"
            mock_user.school_id = str(uuid.uuid4())
            
            mock_device = Mock()
            mock_device.id = str(uuid.uuid4())
            mock_device.device_id = mock_device_id
            mock_device.user_id = mock_user.id
            mock_device.biometric_enabled = True
            mock_device.biometric_type = BiometricType.FINGERPRINT
            mock_device.user = mock_user
            
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_device
            mock_session.add = Mock()
            mock_session.commit = AsyncMock()
            
            with patch.object(service, '_verify_biometric_token') as mock_verify:
                mock_verify.return_value = True
                
                with patch('backend.services.mobile_auth.service.create_access_token') as mock_access_token:
                    mock_access_token.return_value = "biometric_access_token"
                    
                    with patch('backend.services.mobile_auth.service.create_refresh_token') as mock_refresh_token:
                        mock_refresh_token.return_value = "biometric_refresh_token"
                        
                        biometric_request = BiometricAuthRequest(
                            device_id=mock_device_id,
                            biometric_token="test_biometric_token",
                            biometric_type=BiometricType.FINGERPRINT
                        )
                        
                        result = await service.biometric_auth(biometric_request)
                        
                        assert result.access_token == "biometric_access_token"
                        assert result.refresh_token == "biometric_refresh_token"
                        mock_session.add.assert_called_once()
                        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_biometric_auth_not_enabled(self, service, mock_device_id):
        """Test biometric authentication when not enabled"""
        with patch('backend.services.mobile_auth.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock device without biometric enabled
            mock_device = Mock()
            mock_device.device_id = mock_device_id
            mock_device.biometric_enabled = False
            
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_device
            
            biometric_request = BiometricAuthRequest(
                device_id=mock_device_id,
                biometric_token="test_token",
                biometric_type=BiometricType.FINGERPRINT
            )
            
            with pytest.raises(ValidationError):
                await service.biometric_auth(biometric_request)
    
    @pytest.mark.asyncio
    async def test_logout_device(self, service, mock_device_id, mock_user_id):
        """Test logging out from a specific device"""
        with patch('backend.services.mobile_auth.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock device
            mock_device = Mock()
            mock_device.id = str(uuid.uuid4())
            mock_device.device_id = mock_device_id
            mock_device.user_id = mock_user_id
            
            mock_session.execute.side_effect = [
                Mock(scalar_one_or_none=Mock(return_value=mock_device)),  # Device lookup
                Mock(rowcount=2)  # Sessions updated
            ]
            mock_session.commit = AsyncMock()
            
            result = await service.logout_device(mock_device_id, mock_user_id)
            
            assert result == True
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_logout_all_devices(self, service, mock_user_id):
        """Test logging out from all devices"""
        with patch('backend.services.mobile_auth.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock session update
            mock_session.execute.return_value.rowcount = 3
            mock_session.commit = AsyncMock()
            
            result = await service.logout_all_devices(mock_user_id)
            
            assert result == 3
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_devices(self, service, mock_user_id):
        """Test getting user devices"""
        with patch('backend.services.mobile_auth.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock devices
            mock_device1 = Mock()
            mock_device1.id = str(uuid.uuid4())
            mock_device1.device_id = "device_1"
            mock_device1.device_name = "iPhone"
            mock_device1.device_type = "ios"
            
            mock_device2 = Mock()
            mock_device2.id = str(uuid.uuid4())
            mock_device2.device_id = "device_2"
            mock_device2.device_name = "Android"
            mock_device2.device_type = "android"
            
            mock_session.execute.return_value.scalars.return_value.all.return_value = [mock_device1, mock_device2]
            
            result = await service.get_user_devices(mock_user_id)
            
            assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_remove_device(self, service, mock_device_id, mock_user_id):
        """Test removing a device"""
        with patch('backend.services.mobile_auth.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock device
            mock_device = Mock()
            mock_device.id = str(uuid.uuid4())
            mock_device.device_id = mock_device_id
            mock_device.user_id = mock_user_id
            
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_device
            mock_session.delete = Mock()
            mock_session.commit = AsyncMock()
            
            result = await service.remove_device(mock_device_id, mock_user_id)
            
            assert result == True
            mock_session.delete.assert_called_once_with(mock_device)
            mock_session.commit.assert_called_once()
    
    def test_generate_auth_code_format(self, service):
        """Test auth code generation format"""
        code = service._generate_auth_code()
        
        assert len(code) == 6
        assert code.isdigit()
        assert code != "000000"  # Should not be all zeros
    
    def test_verify_biometric_token(self, service):
        """Test biometric token verification"""
        mock_device = Mock()
        mock_device.device_fingerprint = "test_fingerprint"
        mock_device.user_id = "test_user_id"
        mock_device.device_id = "test_device_id"
        
        # Test with valid token
        import hmac
        import hashlib
        
        expected_token = hmac.new(
            mock_device.device_fingerprint.encode(),
            f"{mock_device.user_id}:{mock_device.device_id}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        assert service._verify_biometric_token(expected_token, mock_device) == True
        
        # Test with invalid token
        assert service._verify_biometric_token("invalid_token", mock_device) == False
    
    def test_generate_api_key(self, service):
        """Test API key generation"""
        api_key = service._generate_api_key()
        
        assert api_key.startswith("mak_")
        assert len(api_key) > 10
    
    def test_generate_api_secret(self, service):
        """Test API secret generation"""
        api_secret = service._generate_api_secret()
        
        assert api_secret.startswith("mas_")
        assert len(api_secret) > 20
    
    def test_hash_secret(self, service):
        """Test secret hashing"""
        secret = "test_secret"
        hashed = service._hash_secret(secret)
        
        assert len(hashed) == 64  # SHA256 hex digest length
        assert hashed != secret
        
        # Same secret should produce same hash
        assert service._hash_secret(secret) == hashed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])