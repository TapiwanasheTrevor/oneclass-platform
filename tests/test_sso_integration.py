"""
SSO Integration Tests
Comprehensive test suite for SSO integration service
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import uuid

from backend.services.sso_integration.service import SSOIntegrationService
from backend.services.sso_integration.models import SSOProvider, SAMLProvider, LDAPProvider
from backend.services.sso_integration.schemas import (
    SSOProviderCreate,
    SSOProviderUpdate,
    SAMLProviderCreate,
    LDAPProviderCreate,
    SSOLoginRequest,
    SSOTestConnectionRequest,
    SSOProviderType
)
from shared.exceptions import ValidationError, NotFoundError, ConflictError


class TestSSOIntegrationService:
    """Test SSO integration service"""
    
    @pytest.fixture
    def service(self):
        return SSOIntegrationService()
    
    @pytest.fixture
    def mock_school_id(self):
        return str(uuid.uuid4())
    
    @pytest.fixture
    def mock_user_id(self):
        return str(uuid.uuid4())
    
    @pytest.fixture
    def saml_provider_data(self, mock_school_id):
        return SSOProviderCreate(
            school_id=mock_school_id,
            provider_name="Test SAML Provider",
            provider_type=SSOProviderType.SAML,
            display_name="Test SAML",
            description="Test SAML provider",
            is_active=True,
            is_default=True,
            auto_provision=True,
            configuration={
                "entity_id": "https://idp.example.com/saml",
                "sso_url": "https://idp.example.com/sso",
                "x509_cert": "test_cert"
            },
            attribute_mapping={
                "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
                "first_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname",
                "last_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname"
            },
            role_mapping={
                "Administrators": "admin",
                "Teachers": "staff",
                "Students": "student"
            }
        )
    
    @pytest.fixture
    def ldap_provider_data(self, mock_school_id):
        return SSOProviderCreate(
            school_id=mock_school_id,
            provider_name="Test LDAP Provider",
            provider_type=SSOProviderType.LDAP,
            display_name="Test LDAP",
            description="Test LDAP provider",
            is_active=True,
            is_default=False,
            auto_provision=True,
            configuration={
                "server_url": "ldaps://ldap.example.com:636",
                "bind_dn": "cn=admin,dc=example,dc=com",
                "bind_password": "password",
                "base_dn": "dc=example,dc=com"
            },
            attribute_mapping={
                "email": "mail",
                "first_name": "givenName",
                "last_name": "sn"
            },
            role_mapping={
                "cn=administrators,ou=groups,dc=example,dc=com": "admin",
                "cn=teachers,ou=groups,dc=example,dc=com": "staff",
                "cn=students,ou=groups,dc=example,dc=com": "student"
            }
        )
    
    @pytest.mark.asyncio
    async def test_create_sso_provider_saml(self, service, saml_provider_data, mock_user_id):
        """Test creating SAML SSO provider"""
        with patch('backend.services.sso_integration.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock database operations
            mock_session.execute.return_value.scalar_one_or_none.return_value = None
            mock_session.commit = Mock()
            mock_session.refresh = Mock()
            
            result = await service.create_sso_provider(saml_provider_data, mock_user_id)
            
            assert result.provider_name == "Test SAML Provider"
            assert result.provider_type == SSOProviderType.SAML
            assert result.is_active == True
            assert result.is_default == True
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_sso_provider_ldap(self, service, ldap_provider_data, mock_user_id):
        """Test creating LDAP SSO provider"""
        with patch('backend.services.sso_integration.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock database operations
            mock_session.execute.return_value.scalar_one_or_none.return_value = None
            mock_session.commit = Mock()
            mock_session.refresh = Mock()
            
            result = await service.create_sso_provider(ldap_provider_data, mock_user_id)
            
            assert result.provider_name == "Test LDAP Provider"
            assert result.provider_type == SSOProviderType.LDAP
            assert result.is_active == True
            assert result.is_default == False
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_sso_provider_conflict(self, service, saml_provider_data, mock_user_id):
        """Test creating SSO provider with conflict"""
        with patch('backend.services.sso_integration.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock existing default provider
            mock_session.execute.return_value.scalar_one_or_none.return_value = Mock()
            
            with pytest.raises(ConflictError):
                await service.create_sso_provider(saml_provider_data, mock_user_id)
    
    @pytest.mark.asyncio
    async def test_get_sso_provider(self, service):
        """Test getting SSO provider"""
        provider_id = str(uuid.uuid4())
        
        with patch('backend.services.sso_integration.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock provider
            mock_provider = Mock()
            mock_provider.id = provider_id
            mock_provider.provider_name = "Test Provider"
            mock_provider.provider_type = SSOProviderType.SAML
            mock_session.get.return_value = mock_provider
            
            result = await service.get_sso_provider(provider_id)
            
            mock_session.get.assert_called_once_with(SSOProvider, provider_id)
    
    @pytest.mark.asyncio
    async def test_get_sso_provider_not_found(self, service):
        """Test getting non-existent SSO provider"""
        provider_id = str(uuid.uuid4())
        
        with patch('backend.services.sso_integration.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock provider not found
            mock_session.get.return_value = None
            
            with pytest.raises(NotFoundError):
                await service.get_sso_provider(provider_id)
    
    @pytest.mark.asyncio
    async def test_update_sso_provider(self, service):
        """Test updating SSO provider"""
        provider_id = str(uuid.uuid4())
        update_data = SSOProviderUpdate(
            display_name="Updated Provider",
            is_active=False
        )
        
        with patch('backend.services.sso_integration.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock existing provider
            mock_provider = Mock()
            mock_provider.id = provider_id
            mock_provider.provider_name = "Test Provider"
            mock_provider.display_name = "Test Provider"
            mock_provider.is_active = True
            mock_provider.is_default = False
            mock_session.get.return_value = mock_provider
            mock_session.commit = Mock()
            mock_session.refresh = Mock()
            
            result = await service.update_sso_provider(provider_id, update_data)
            
            assert mock_provider.display_name == "Updated Provider"
            assert mock_provider.is_active == False
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_sso_provider(self, service):
        """Test deleting SSO provider"""
        provider_id = str(uuid.uuid4())
        
        with patch('backend.services.sso_integration.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock existing provider
            mock_provider = Mock()
            mock_provider.id = provider_id
            mock_provider.provider_name = "Test Provider"
            mock_provider.provider_type = SSOProviderType.SAML
            mock_session.get.return_value = mock_provider
            mock_session.execute = Mock()
            mock_session.delete = Mock()
            mock_session.commit = Mock()
            
            result = await service.delete_sso_provider(provider_id)
            
            assert result == True
            mock_session.delete.assert_called_once_with(mock_provider)
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_saml_provider(self, service):
        """Test creating SAML provider configuration"""
        provider_id = str(uuid.uuid4())
        saml_data = SAMLProviderCreate(
            sso_provider_id=provider_id,
            entity_id="https://idp.example.com/saml",
            sso_url="https://idp.example.com/sso",
            x509_cert="test_cert",
            sp_entity_id="https://sp.example.com/saml",
            sp_acs_url="https://sp.example.com/acs"
        )
        
        with patch('backend.services.sso_integration.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock SSO provider
            mock_sso_provider = Mock()
            mock_sso_provider.id = provider_id
            mock_sso_provider.provider_type = SSOProviderType.SAML
            mock_session.get.return_value = mock_sso_provider
            mock_session.add = Mock()
            mock_session.commit = Mock()
            mock_session.refresh = Mock()
            
            result = await service.create_saml_provider(saml_data)
            
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_ldap_provider(self, service):
        """Test creating LDAP provider configuration"""
        provider_id = str(uuid.uuid4())
        ldap_data = LDAPProviderCreate(
            sso_provider_id=provider_id,
            server_url="ldaps://ldap.example.com:636",
            bind_dn="cn=admin,dc=example,dc=com",
            bind_password="password",
            base_dn="dc=example,dc=com"
        )
        
        with patch('backend.services.sso_integration.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock SSO provider
            mock_sso_provider = Mock()
            mock_sso_provider.id = provider_id
            mock_sso_provider.provider_type = SSOProviderType.LDAP
            mock_session.get.return_value = mock_sso_provider
            mock_session.add = Mock()
            mock_session.commit = Mock()
            mock_session.refresh = Mock()
            
            result = await service.create_ldap_provider(ldap_data)
            
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_test_saml_connection(self, service):
        """Test SAML connection testing"""
        test_request = SSOTestConnectionRequest(
            provider_type=SSOProviderType.SAML,
            configuration={
                "entity_id": "https://idp.example.com/saml",
                "sso_url": "https://idp.example.com/sso",
                "x509_cert": "test_cert",
                "sp_entity_id": "https://sp.example.com/saml",
                "sp_acs_url": "https://sp.example.com/acs"
            }
        )
        
        with patch('backend.services.sso_integration.service.SAMLHandler') as mock_handler:
            mock_handler.return_value.test_connection.return_value = {
                "success": True,
                "message": "Connection successful"
            }
            
            result = await service.test_sso_connection(test_request)
            
            assert result.success == True
            assert result.message == "Connection successful"
    
    @pytest.mark.asyncio
    async def test_test_ldap_connection(self, service):
        """Test LDAP connection testing"""
        test_request = SSOTestConnectionRequest(
            provider_type=SSOProviderType.LDAP,
            configuration={
                "server_url": "ldaps://ldap.example.com:636",
                "bind_dn": "cn=admin,dc=example,dc=com",
                "bind_password": "password",
                "base_dn": "dc=example,dc=com"
            }
        )
        
        with patch('backend.services.sso_integration.service.LDAPHandler') as mock_handler:
            mock_handler.return_value.test_connection.return_value = {
                "success": True,
                "message": "Connection successful"
            }
            
            result = await service.test_sso_connection(test_request)
            
            assert result.success == True
            assert result.message == "Connection successful"
    
    @pytest.mark.asyncio
    async def test_get_sso_stats(self, service, mock_school_id):
        """Test getting SSO statistics"""
        with patch('backend.services.sso_integration.service.get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock statistics queries
            mock_session.execute.return_value.first.side_effect = [
                Mock(total=2, active=2, saml=1, ldap=1, oauth2=0),  # Provider stats
                Mock(total=5, active=3),  # Session stats
                Mock(today=10, week=50, month=200, failed_today=2)  # Login stats
            ]
            
            result = await service.get_sso_stats(mock_school_id)
            
            assert result.total_providers == 2
            assert result.active_providers == 2
            assert result.saml_providers == 1
            assert result.ldap_providers == 1
            assert result.oauth2_providers == 0
            assert result.total_sessions == 5
            assert result.active_sessions == 3
            assert result.total_logins_today == 10
            assert result.total_logins_week == 50
            assert result.total_logins_month == 200
            assert result.failed_logins_today == 2


class TestSAMLHandler:
    """Test SAML handler"""
    
    @pytest.fixture
    def mock_saml_provider(self):
        """Mock SAML provider"""
        provider = Mock()
        provider.entity_id = "https://idp.example.com/saml"
        provider.sso_url = "https://idp.example.com/sso"
        provider.slo_url = "https://idp.example.com/slo"
        provider.x509_cert = "test_cert"
        provider.sp_entity_id = "https://sp.example.com/saml"
        provider.sp_acs_url = "https://sp.example.com/acs"
        provider.sp_sls_url = "https://sp.example.com/sls"
        provider.name_id_format = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
        provider.authn_requests_signed = False
        provider.logout_requests_signed = False
        provider.want_assertions_signed = True
        provider.want_name_id_encrypted = False
        provider.sso_provider = Mock()
        provider.sso_provider.attribute_mapping = {
            "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
        }
        provider.sso_provider.role_mapping = {
            "Administrators": "admin"
        }
        return provider
    
    @pytest.mark.asyncio
    async def test_saml_handler_initialization(self, mock_saml_provider):
        """Test SAML handler initialization"""
        from backend.services.sso_integration.saml_handler import SAMLHandler
        
        handler = SAMLHandler(mock_saml_provider)
        
        assert handler.saml_provider == mock_saml_provider
        assert handler.settings is not None
        assert handler.settings["sp"]["entityId"] == "https://sp.example.com/saml"
        assert handler.settings["idp"]["entityId"] == "https://idp.example.com/saml"
    
    def test_saml_metadata_validation(self, mock_saml_provider):
        """Test SAML metadata validation"""
        from backend.services.sso_integration.saml_handler import SAMLHandler
        
        handler = SAMLHandler(mock_saml_provider)
        
        # Test with invalid XML
        result = handler.validate_metadata("invalid xml")
        assert result["valid"] == False
        assert "Invalid XML format" in result["error"]
        
        # Test with valid XML structure
        valid_xml = '''<?xml version="1.0"?>
        <EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata" entityID="https://idp.example.com/saml">
            <IDPSSODescriptor>
                <SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect" Location="https://idp.example.com/sso"/>
                <KeyDescriptor use="signing">
                    <KeyInfo xmlns="http://www.w3.org/2000/09/xmldsig#">
                        <X509Data>
                            <X509Certificate>test_cert</X509Certificate>
                        </X509Data>
                    </KeyInfo>
                </KeyDescriptor>
            </IDPSSODescriptor>
        </EntityDescriptor>'''
        
        result = handler.validate_metadata(valid_xml)
        assert result["valid"] == True
        assert result["entity_id"] == "https://idp.example.com/saml"
        assert result["sso_url"] == "https://idp.example.com/sso"


class TestLDAPHandler:
    """Test LDAP handler"""
    
    @pytest.fixture
    def mock_ldap_provider(self):
        """Mock LDAP provider"""
        provider = Mock()
        provider.server_url = "ldaps://ldap.example.com:636"
        provider.bind_dn = "cn=admin,dc=example,dc=com"
        provider.bind_password = "password"
        provider.base_dn = "dc=example,dc=com"
        provider.user_search_filter = "(sAMAccountName={username})"
        provider.user_search_base = "ou=users,dc=example,dc=com"
        provider.group_search_filter = "(member={user_dn})"
        provider.group_search_base = "ou=groups,dc=example,dc=com"
        provider.use_ssl = True
        provider.use_tls = False
        provider.timeout = 30
        provider.username_attribute = "sAMAccountName"
        provider.email_attribute = "mail"
        provider.first_name_attribute = "givenName"
        provider.last_name_attribute = "sn"
        provider.display_name_attribute = "displayName"
        provider.sso_provider = Mock()
        provider.sso_provider.attribute_mapping = {
            "email": "mail"
        }
        provider.sso_provider.role_mapping = {
            "cn=administrators,ou=groups,dc=example,dc=com": "admin"
        }
        return provider
    
    @pytest.mark.asyncio
    async def test_ldap_handler_initialization(self, mock_ldap_provider):
        """Test LDAP handler initialization"""
        from backend.services.sso_integration.ldap_handler import LDAPHandler
        
        handler = LDAPHandler(mock_ldap_provider)
        
        assert handler.ldap_provider == mock_ldap_provider
        assert handler.server is not None
    
    @pytest.mark.asyncio
    async def test_ldap_attribute_mapping(self, mock_ldap_provider):
        """Test LDAP attribute mapping"""
        from backend.services.sso_integration.ldap_handler import LDAPHandler
        
        handler = LDAPHandler(mock_ldap_provider)
        
        # Test attribute mapping
        attributes = {
            "sAMAccountName": "testuser",
            "mail": "testuser@example.com",
            "givenName": "Test",
            "sn": "User",
            "displayName": "Test User"
        }
        
        mapped_user = handler._map_attributes(attributes, "testuser")
        
        assert mapped_user["username"] == "testuser"
        assert mapped_user["email"] == "testuser@example.com"
        assert mapped_user["first_name"] == "Test"
        assert mapped_user["last_name"] == "User"
        assert mapped_user["display_name"] == "Test User"
    
    def test_ldap_role_extraction(self, mock_ldap_provider):
        """Test LDAP role extraction"""
        from backend.services.sso_integration.ldap_handler import LDAPHandler
        
        handler = LDAPHandler(mock_ldap_provider)
        
        # Test role extraction
        groups = [
            "cn=administrators,ou=groups,dc=example,dc=com",
            "cn=teachers,ou=groups,dc=example,dc=com",
            "cn=students,ou=groups,dc=example,dc=com"
        ]
        
        roles = handler.extract_roles(groups)
        
        assert "admin" in roles
        assert "staff" in roles
        assert "student" in roles


if __name__ == "__main__":
    pytest.main([__file__, "-v"])