"""
LDAP Authentication Handler
Handles LDAP-based SSO authentication
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta

import ldap3
from ldap3 import Server, Connection, ALL, NTLM, SIMPLE, SYNC, ASYNC
from ldap3.core.exceptions import LDAPException, LDAPBindError

from shared.exceptions import ValidationError, AuthenticationError
from .models import LDAPProvider, SSOSession, SSOAuditLog
from .schemas import SSOLoginResponse, SSOLogoutResponse

logger = logging.getLogger(__name__)


class LDAPHandler:
    """LDAP authentication handler"""
    
    def __init__(self, ldap_provider: LDAPProvider):
        self.ldap_provider = ldap_provider
        self.server = self._create_server()
    
    def _create_server(self) -> Server:
        """Create LDAP server object"""
        return Server(
            self.ldap_provider.server_url,
            use_ssl=self.ldap_provider.use_ssl,
            use_tls=self.ldap_provider.use_tls,
            get_info=ALL,
            connect_timeout=self.ldap_provider.timeout
        )
    
    def _create_connection(self, bind_dn: Optional[str] = None, password: Optional[str] = None, auto_bind: bool = True) -> Connection:
        """Create LDAP connection"""
        bind_dn = bind_dn or self.ldap_provider.bind_dn
        password = password or self.ldap_provider.bind_password
        
        return Connection(
            self.server,
            user=bind_dn,
            password=password,
            auto_bind=auto_bind,
            raise_exceptions=True
        )
    
    async def authenticate(self, username: str, password: str) -> Tuple[bool, Dict[str, Any]]:
        """Authenticate user against LDAP"""
        try:
            # Search for user
            user_dn, user_attrs = await self._search_user(username)
            if not user_dn:
                logger.warning(f"LDAP user not found: {username}")
                return False, {
                    "error": "User not found",
                    "username": username
                }
            
            # Authenticate user
            try:
                conn = self._create_connection(bind_dn=user_dn, password=password, auto_bind=True)
                conn.unbind()
                
                logger.info(f"LDAP authentication successful for user: {username}")
                
                # Get user groups
                user_groups = await self._get_user_groups(user_dn)
                
                # Map attributes
                mapped_user = self._map_attributes(user_attrs, username)
                mapped_user["groups"] = user_groups
                mapped_user["user_dn"] = user_dn
                
                return True, mapped_user
                
            except LDAPBindError as e:
                logger.warning(f"LDAP authentication failed for user {username}: {str(e)}")
                return False, {
                    "error": "Invalid credentials",
                    "username": username
                }
            
        except Exception as e:
            logger.error(f"LDAP authentication error for user {username}: {str(e)}")
            return False, {
                "error": "Authentication error",
                "details": str(e),
                "username": username
            }
    
    async def _search_user(self, username: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Search for user in LDAP"""
        try:
            conn = self._create_connection()
            
            # Build search filter
            search_filter = self.ldap_provider.user_search_filter.format(username=username)
            search_base = self.ldap_provider.user_search_base or self.ldap_provider.base_dn
            
            # Search for user
            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                attributes=ldap3.ALL_ATTRIBUTES
            )
            
            if not conn.entries:
                return None, {}
            
            # Get first entry
            entry = conn.entries[0]
            user_dn = entry.entry_dn
            
            # Extract attributes
            user_attrs = {}
            for attr_name in entry.entry_attributes:
                attr_value = getattr(entry, attr_name)
                if isinstance(attr_value, list) and len(attr_value) == 1:
                    user_attrs[attr_name] = attr_value[0]
                else:
                    user_attrs[attr_name] = attr_value
            
            conn.unbind()
            
            return user_dn, user_attrs
            
        except Exception as e:
            logger.error(f"LDAP user search error: {str(e)}")
            return None, {}
    
    async def _get_user_groups(self, user_dn: str) -> List[str]:
        """Get user's groups from LDAP"""
        try:
            conn = self._create_connection()
            
            # Build group search filter
            search_filter = self.ldap_provider.group_search_filter.format(user_dn=user_dn)
            search_base = self.ldap_provider.group_search_base or self.ldap_provider.base_dn
            
            # Search for groups
            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                attributes=['cn', 'name', 'displayName']
            )
            
            groups = []
            for entry in conn.entries:
                # Try to get group name from various attributes
                group_name = None
                for attr in ['cn', 'name', 'displayName']:
                    if hasattr(entry, attr):
                        group_name = getattr(entry, attr)
                        if isinstance(group_name, list):
                            group_name = group_name[0]
                        break
                
                if group_name:
                    groups.append(str(group_name))
            
            conn.unbind()
            
            return groups
            
        except Exception as e:
            logger.error(f"LDAP group search error: {str(e)}")
            return []
    
    def _map_attributes(self, attributes: Dict[str, Any], username: str) -> Dict[str, Any]:
        """Map LDAP attributes to user fields"""
        mapping = self.ldap_provider.sso_provider.attribute_mapping
        
        mapped_user = {
            "username": username,
            "email": None,
            "first_name": "",
            "last_name": "",
            "display_name": username
        }
        
        # Apply attribute mapping
        for local_attr, ldap_attr in mapping.items():
            if ldap_attr in attributes:
                mapped_user[local_attr] = str(attributes[ldap_attr])
        
        # Extract common attributes with fallbacks
        email_attr = self.ldap_provider.email_attribute
        if email_attr in attributes:
            mapped_user["email"] = str(attributes[email_attr])
        
        first_name_attr = self.ldap_provider.first_name_attribute
        if first_name_attr in attributes:
            mapped_user["first_name"] = str(attributes[first_name_attr])
        
        last_name_attr = self.ldap_provider.last_name_attribute
        if last_name_attr in attributes:
            mapped_user["last_name"] = str(attributes[last_name_attr])
        
        display_name_attr = self.ldap_provider.display_name_attribute
        if display_name_attr in attributes:
            mapped_user["display_name"] = str(attributes[display_name_attr])
        
        return mapped_user
    
    def extract_roles(self, groups: List[str]) -> List[str]:
        """Extract user roles from LDAP groups"""
        role_mapping = self.ldap_provider.sso_provider.role_mapping
        
        mapped_roles = []
        for group in groups:
            if group in role_mapping:
                mapped_roles.append(role_mapping[group])
            else:
                # Default role mapping based on group names
                if "admin" in group.lower():
                    mapped_roles.append("admin")
                elif "teacher" in group.lower() or "staff" in group.lower():
                    mapped_roles.append("staff")
                elif "student" in group.lower():
                    mapped_roles.append("student")
                elif "parent" in group.lower():
                    mapped_roles.append("parent")
                else:
                    mapped_roles.append("user")
        
        return list(set(mapped_roles))  # Remove duplicates
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test LDAP connection"""
        try:
            # Test basic connection
            conn = self._create_connection()
            
            # Test search
            conn.search(
                search_base=self.ldap_provider.base_dn,
                search_filter="(objectClass=*)",
                search_scope=ldap3.BASE,
                attributes=['objectClass']
            )
            
            conn.unbind()
            
            return {
                "success": True,
                "message": "LDAP connection test successful",
                "server_url": self.ldap_provider.server_url,
                "base_dn": self.ldap_provider.base_dn
            }
            
        except LDAPBindError as e:
            logger.error(f"LDAP bind error: {str(e)}")
            return {
                "success": False,
                "message": f"LDAP bind failed: {str(e)}"
            }
        except LDAPException as e:
            logger.error(f"LDAP connection error: {str(e)}")
            return {
                "success": False,
                "message": f"LDAP connection failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"LDAP test error: {str(e)}")
            return {
                "success": False,
                "message": f"LDAP test failed: {str(e)}"
            }
    
    async def search_users(self, search_term: str = "*", limit: int = 100) -> List[Dict[str, Any]]:
        """Search for users in LDAP"""
        try:
            conn = self._create_connection()
            
            # Build search filter
            if search_term == "*":
                search_filter = f"({self.ldap_provider.username_attribute}=*)"
            else:
                search_filter = f"({self.ldap_provider.username_attribute}=*{search_term}*)"
            
            search_base = self.ldap_provider.user_search_base or self.ldap_provider.base_dn
            
            # Search for users
            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                attributes=[
                    self.ldap_provider.username_attribute,
                    self.ldap_provider.email_attribute,
                    self.ldap_provider.first_name_attribute,
                    self.ldap_provider.last_name_attribute,
                    self.ldap_provider.display_name_attribute
                ],
                size_limit=limit
            )
            
            users = []
            for entry in conn.entries:
                user_data = {
                    "dn": entry.entry_dn,
                    "username": getattr(entry, self.ldap_provider.username_attribute, [""])[0],
                    "email": getattr(entry, self.ldap_provider.email_attribute, [""])[0],
                    "first_name": getattr(entry, self.ldap_provider.first_name_attribute, [""])[0],
                    "last_name": getattr(entry, self.ldap_provider.last_name_attribute, [""])[0],
                    "display_name": getattr(entry, self.ldap_provider.display_name_attribute, [""])[0]
                }
                users.append(user_data)
            
            conn.unbind()
            
            return users
            
        except Exception as e:
            logger.error(f"LDAP user search error: {str(e)}")
            return []
    
    async def get_user_details(self, username: str) -> Optional[Dict[str, Any]]:
        """Get detailed user information from LDAP"""
        try:
            user_dn, user_attrs = await self._search_user(username)
            if not user_dn:
                return None
            
            # Get user groups
            user_groups = await self._get_user_groups(user_dn)
            
            # Map attributes
            mapped_user = self._map_attributes(user_attrs, username)
            mapped_user["groups"] = user_groups
            mapped_user["user_dn"] = user_dn
            mapped_user["roles"] = self.extract_roles(user_groups)
            
            return mapped_user
            
        except Exception as e:
            logger.error(f"LDAP user details error: {str(e)}")
            return None
    
    async def sync_users(self, limit: int = 1000) -> Dict[str, Any]:
        """Sync users from LDAP"""
        try:
            users = await self.search_users("*", limit)
            
            synced_users = []
            for user in users:
                if user["username"] and user["email"]:
                    # Get full user details
                    user_details = await self.get_user_details(user["username"])
                    if user_details:
                        synced_users.append(user_details)
            
            return {
                "success": True,
                "message": f"Synced {len(synced_users)} users from LDAP",
                "users": synced_users,
                "total_found": len(users),
                "total_synced": len(synced_users)
            }
            
        except Exception as e:
            logger.error(f"LDAP user sync error: {str(e)}")
            return {
                "success": False,
                "message": f"LDAP user sync failed: {str(e)}"
            }
    
    async def validate_configuration(self) -> Dict[str, Any]:
        """Validate LDAP configuration"""
        errors = []
        warnings = []
        
        # Test connection
        conn_test = await self.test_connection()
        if not conn_test["success"]:
            errors.append(f"Connection test failed: {conn_test['message']}")
        
        # Test user search
        try:
            users = await self.search_users("*", 1)
            if not users:
                warnings.append("No users found in LDAP directory")
        except Exception as e:
            errors.append(f"User search test failed: {str(e)}")
        
        # Validate configuration
        if not self.ldap_provider.server_url:
            errors.append("Server URL is required")
        
        if not self.ldap_provider.bind_dn:
            errors.append("Bind DN is required")
        
        if not self.ldap_provider.bind_password:
            errors.append("Bind password is required")
        
        if not self.ldap_provider.base_dn:
            errors.append("Base DN is required")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }