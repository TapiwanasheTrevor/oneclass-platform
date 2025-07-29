"""
SAML Authentication Handler
Handles SAML-based SSO authentication
"""

import base64
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse, parse_qs
import logging

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from onelogin.saml2.settings import OneLogin_Saml2_Settings

from shared.exceptions import ValidationError, AuthenticationError
from .models import SAMLProvider, SSOSession, SSOAuditLog
from .schemas import SSOLoginResponse, SSOLogoutResponse

logger = logging.getLogger(__name__)


class SAMLHandler:
    """SAML authentication handler"""
    
    def __init__(self, saml_provider: SAMLProvider):
        self.saml_provider = saml_provider
        self.settings = self._build_saml_settings()
    
    def _build_saml_settings(self) -> Dict[str, Any]:
        """Build SAML settings from provider configuration"""
        return {
            "sp": {
                "entityId": self.saml_provider.sp_entity_id,
                "assertionConsumerService": {
                    "url": self.saml_provider.sp_acs_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                },
                "singleLogoutService": {
                    "url": self.saml_provider.sp_sls_url or "",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                "NameIDFormat": self.saml_provider.name_id_format,
                "x509cert": self.saml_provider.sp_x509_cert or "",
                "privateKey": self.saml_provider.sp_private_key or ""
            },
            "idp": {
                "entityId": self.saml_provider.entity_id,
                "singleSignOnService": {
                    "url": self.saml_provider.sso_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                "singleLogoutService": {
                    "url": self.saml_provider.slo_url or "",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                "x509cert": self.saml_provider.x509_cert
            },
            "security": {
                "nameIdEncrypted": self.saml_provider.want_name_id_encrypted,
                "authnRequestsSigned": self.saml_provider.authn_requests_signed,
                "logoutRequestSigned": self.saml_provider.logout_requests_signed,
                "logoutResponseSigned": self.saml_provider.logout_requests_signed,
                "signMetadata": False,
                "wantAssertionsSigned": self.saml_provider.want_assertions_signed,
                "wantNameId": True,
                "wantAssertionsEncrypted": False,
                "wantNameIdEncrypted": self.saml_provider.want_name_id_encrypted,
                "requestedAuthnContext": True,
                "signatureAlgorithm": "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
                "digestAlgorithm": "http://www.w3.org/2001/04/xmlenc#sha256"
            }
        }
    
    def _init_saml_auth(self, req: Dict[str, Any]) -> OneLogin_Saml2_Auth:
        """Initialize SAML auth object"""
        return OneLogin_Saml2_Auth(req, self.settings)
    
    def _prepare_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare request data for SAML library"""
        return {
            'https': 'on' if request_data.get('https') else 'off',
            'http_host': request_data.get('http_host', 'localhost'),
            'server_port': request_data.get('server_port', '443'),
            'script_name': request_data.get('script_name', '/'),
            'get_data': request_data.get('get_data', {}),
            'post_data': request_data.get('post_data', {})
        }
    
    def generate_login_url(self, request_data: Dict[str, Any], relay_state: Optional[str] = None) -> str:
        """Generate SAML login URL"""
        req = self._prepare_request(request_data)
        auth = self._init_saml_auth(req)
        
        return auth.login(return_to=relay_state)
    
    def process_response(self, request_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Process SAML response"""
        req = self._prepare_request(request_data)
        auth = self._init_saml_auth(req)
        
        try:
            auth.process_response()
            
            errors = auth.get_errors()
            if errors:
                logger.error(f"SAML authentication errors: {errors}")
                return False, {
                    "error": "SAML authentication failed",
                    "details": errors,
                    "last_error_reason": auth.get_last_error_reason()
                }
            
            if not auth.is_authenticated():
                logger.warning("SAML authentication not successful")
                return False, {
                    "error": "Authentication not successful",
                    "authenticated": False
                }
            
            # Extract user attributes
            attributes = auth.get_attributes()
            name_id = auth.get_nameid()
            session_index = auth.get_session_index()
            
            user_data = {
                "name_id": name_id,
                "session_index": session_index,
                "attributes": attributes,
                "authenticated": True
            }
            
            # Map attributes to user fields
            mapped_user = self._map_attributes(attributes, name_id)
            user_data.update(mapped_user)
            
            logger.info(f"SAML authentication successful for user: {mapped_user.get('email', name_id)}")
            
            return True, user_data
            
        except Exception as e:
            logger.error(f"SAML response processing error: {str(e)}")
            return False, {
                "error": "SAML response processing failed",
                "details": str(e)
            }
    
    def _map_attributes(self, attributes: Dict[str, Any], name_id: str) -> Dict[str, Any]:
        """Map SAML attributes to user fields"""
        mapping = self.saml_provider.sso_provider.attribute_mapping
        
        mapped_user = {
            "username": name_id,
            "email": name_id if "@" in name_id else None,
            "first_name": "",
            "last_name": "",
            "display_name": name_id
        }
        
        # Apply attribute mapping
        for local_attr, saml_attr in mapping.items():
            if saml_attr in attributes:
                attr_value = attributes[saml_attr]
                if isinstance(attr_value, list) and attr_value:
                    mapped_user[local_attr] = attr_value[0]
                else:
                    mapped_user[local_attr] = attr_value
        
        # Extract common attributes with fallbacks
        if "email" in attributes:
            mapped_user["email"] = attributes["email"][0] if isinstance(attributes["email"], list) else attributes["email"]
        
        if "givenName" in attributes:
            mapped_user["first_name"] = attributes["givenName"][0] if isinstance(attributes["givenName"], list) else attributes["givenName"]
        
        if "sn" in attributes:
            mapped_user["last_name"] = attributes["sn"][0] if isinstance(attributes["sn"], list) else attributes["sn"]
        
        if "displayName" in attributes:
            mapped_user["display_name"] = attributes["displayName"][0] if isinstance(attributes["displayName"], list) else attributes["displayName"]
        
        return mapped_user
    
    def generate_logout_url(self, request_data: Dict[str, Any], name_id: str, session_index: Optional[str] = None, relay_state: Optional[str] = None) -> str:
        """Generate SAML logout URL"""
        req = self._prepare_request(request_data)
        auth = self._init_saml_auth(req)
        
        return auth.logout(
            return_to=relay_state,
            name_id=name_id,
            session_index=session_index
        )
    
    def process_logout_response(self, request_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Process SAML logout response"""
        req = self._prepare_request(request_data)
        auth = self._init_saml_auth(req)
        
        try:
            url = auth.process_slo(delete_session_cb=lambda: None)
            
            errors = auth.get_errors()
            if errors:
                logger.error(f"SAML logout errors: {errors}")
                return False, {
                    "error": "SAML logout failed",
                    "details": errors
                }
            
            logger.info("SAML logout successful")
            
            return True, {
                "success": True,
                "redirect_url": url
            }
            
        except Exception as e:
            logger.error(f"SAML logout processing error: {str(e)}")
            return False, {
                "error": "SAML logout processing failed",
                "details": str(e)
            }
    
    def get_metadata(self) -> str:
        """Get SAML metadata XML"""
        try:
            saml_settings = OneLogin_Saml2_Settings(self.settings)
            metadata = saml_settings.get_sp_metadata()
            
            errors = saml_settings.check_sp_metadata(metadata)
            if errors:
                logger.error(f"SAML metadata errors: {errors}")
                raise ValidationError(f"SAML metadata validation failed: {errors}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"SAML metadata generation error: {str(e)}")
            raise ValidationError(f"Failed to generate SAML metadata: {str(e)}")
    
    def validate_metadata(self, metadata_xml: str) -> Dict[str, Any]:
        """Validate SAML metadata XML"""
        try:
            # Parse XML
            root = ET.fromstring(metadata_xml)
            
            # Extract basic information
            entity_id = root.get('entityID')
            
            # Find SSO service
            sso_service = root.find('.//{urn:oasis:names:tc:SAML:2.0:metadata}SingleSignOnService')
            sso_url = sso_service.get('Location') if sso_service is not None else None
            
            # Find SLO service
            slo_service = root.find('.//{urn:oasis:names:tc:SAML:2.0:metadata}SingleLogoutService')
            slo_url = slo_service.get('Location') if slo_service is not None else None
            
            # Find X.509 certificate
            cert_element = root.find('.//{http://www.w3.org/2000/09/xmldsig#}X509Certificate')
            x509_cert = cert_element.text if cert_element is not None else None
            
            return {
                "valid": True,
                "entity_id": entity_id,
                "sso_url": sso_url,
                "slo_url": slo_url,
                "x509_cert": x509_cert
            }
            
        except ET.ParseError as e:
            logger.error(f"SAML metadata XML parsing error: {str(e)}")
            return {
                "valid": False,
                "error": f"Invalid XML format: {str(e)}"
            }
        except Exception as e:
            logger.error(f"SAML metadata validation error: {str(e)}")
            return {
                "valid": False,
                "error": f"Metadata validation failed: {str(e)}"
            }
    
    def extract_roles(self, attributes: Dict[str, Any]) -> List[str]:
        """Extract user roles from SAML attributes"""
        roles = []
        role_mapping = self.saml_provider.sso_provider.role_mapping
        
        # Check for direct role attributes
        for role_attr in ["Role", "Groups", "memberOf"]:
            if role_attr in attributes:
                attr_value = attributes[role_attr]
                if isinstance(attr_value, list):
                    roles.extend(attr_value)
                else:
                    roles.append(attr_value)
        
        # Apply role mapping
        mapped_roles = []
        for role in roles:
            if role in role_mapping:
                mapped_roles.append(role_mapping[role])
            else:
                mapped_roles.append(role)
        
        return mapped_roles
    
    def test_connection(self) -> Dict[str, Any]:
        """Test SAML connection"""
        try:
            # Validate settings
            saml_settings = OneLogin_Saml2_Settings(self.settings)
            
            # Check SP metadata
            metadata = saml_settings.get_sp_metadata()
            errors = saml_settings.check_sp_metadata(metadata)
            
            if errors:
                return {
                    "success": False,
                    "message": "SAML settings validation failed",
                    "errors": errors
                }
            
            # Test IdP metadata if available
            idp_metadata_url = self.saml_provider.configuration.get('idp_metadata_url')
            if idp_metadata_url:
                # This would fetch and validate IdP metadata
                pass
            
            return {
                "success": True,
                "message": "SAML connection test successful",
                "entity_id": self.saml_provider.entity_id,
                "sso_url": self.saml_provider.sso_url
            }
            
        except Exception as e:
            logger.error(f"SAML connection test error: {str(e)}")
            return {
                "success": False,
                "message": f"SAML connection test failed: {str(e)}"
            }