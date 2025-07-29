"""
SSO Integration Service
Core service for managing SSO providers and authentication
"""

import uuid
import secrets
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, and_, or_, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import logging

from shared.database import get_db_session
from shared.exceptions import (
    ValidationError,
    NotFoundError,
    ConflictError,
    AuthenticationError,
    ExternalServiceError
)
from shared.models.platform import 
from shared.models.platform_user import PlatformUserDB as User, School
from .models import (
    SSOProvider,
    SAMLProvider,
    LDAPProvider,
    SSOSession,
    SSOAuditLog
)
from .schemas import (
    SSOProviderCreate,
    SSOProviderUpdate,
    SSOProviderResponse,
    SAMLProviderCreate,
    SAMLProviderUpdate,
    SAMLProviderResponse,
    LDAPProviderCreate,
    LDAPProviderUpdate,
    LDAPProviderResponse,
    SSOSessionCreate,
    SSOSessionResponse,
    SSOLoginRequest,
    SSOLoginResponse,
    SSOLogoutRequest,
    SSOLogoutResponse,
    SSOTestConnectionRequest,
    SSOTestConnectionResponse,
    SSOUserProvisionRequest,
    SSOUserProvisionResponse,
    SSOStatsResponse,
    SSOProviderType,
    SSOEventType,
    SSOEventStatus
)
from .saml_handler import SAMLHandler
from .ldap_handler import LDAPHandler

logger = logging.getLogger(__name__)


class SSOIntegrationService:
    """Service for managing SSO providers and authentication"""
    
    def __init__(self):
        self.session_timeout = timedelta(hours=8)
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
    
    async def create_sso_provider(self, provider_data: SSOProviderCreate, created_by: str) -> SSOProviderResponse:
        """Create a new SSO provider"""
        async with get_db_session() as session:
            # Check if school already has a default provider of this type
            if provider_data.is_default:
                existing_default = await session.execute(
                    select(SSOProvider).where(
                        and_(
                            SSOProvider.school_id == provider_data.school_id,
                            SSOProvider.provider_type == provider_data.provider_type,
                            SSOProvider.is_default == True
                        )
                    )
                )
                if existing_default.scalar_one_or_none():
                    raise ConflictError(f"School already has a default {provider_data.provider_type.upper()} provider")
            
            # Create SSO provider
            sso_provider = SSOProvider(
                id=uuid.uuid4(),
                school_id=provider_data.school_id,
                provider_name=provider_data.provider_name,
                provider_type=provider_data.provider_type,
                display_name=provider_data.display_name,
                description=provider_data.description,
                is_active=provider_data.is_active,
                is_default=provider_data.is_default,
                auto_provision=provider_data.auto_provision,
                configuration=provider_data.configuration,
                attribute_mapping=provider_data.attribute_mapping,
                role_mapping=provider_data.role_mapping,
                created_by=created_by
            )
            
            session.add(sso_provider)
            await session.commit()
            await session.refresh(sso_provider)
            
            logger.info(f"SSO provider created: {sso_provider.provider_name} ({sso_provider.provider_type})")
            
            return SSOProviderResponse.from_orm(sso_provider)
    
    async def get_sso_provider(self, provider_id: str) -> SSOProviderResponse:
        """Get SSO provider by ID"""
        async with get_db_session() as session:
            provider = await session.get(SSOProvider, provider_id)
            if not provider:
                raise NotFoundError(f"SSO provider not found: {provider_id}")
            
            return SSOProviderResponse.from_orm(provider)
    
    async def get_school_sso_providers(self, school_id: str) -> List[SSOProviderResponse]:
        """Get all SSO providers for a school"""
        async with get_db_session() as session:
            result = await session.execute(
                select(SSOProvider)
                .where(SSOProvider.school_id == school_id)
                .order_by(SSOProvider.is_default.desc(), SSOProvider.created_at.desc())
            )
            providers = result.scalars().all()
            
            return [SSOProviderResponse.from_orm(provider) for provider in providers]
    
    async def update_sso_provider(self, provider_id: str, provider_data: SSOProviderUpdate) -> SSOProviderResponse:
        """Update SSO provider"""
        async with get_db_session() as session:
            provider = await session.get(SSOProvider, provider_id)
            if not provider:
                raise NotFoundError(f"SSO provider not found: {provider_id}")
            
            # Check if making this provider default
            if provider_data.is_default and provider_data.is_default != provider.is_default:
                # Remove default flag from other providers of same type
                await session.execute(
                    update(SSOProvider)
                    .where(
                        and_(
                            SSOProvider.school_id == provider.school_id,
                            SSOProvider.provider_type == provider.provider_type,
                            SSOProvider.id != provider_id
                        )
                    )
                    .values(is_default=False)
                )
            
            # Update provider
            update_data = provider_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(provider, field, value)
            
            provider.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(provider)
            
            logger.info(f"SSO provider updated: {provider.provider_name}")
            
            return SSOProviderResponse.from_orm(provider)
    
    async def delete_sso_provider(self, provider_id: str) -> bool:
        """Delete SSO provider"""
        async with get_db_session() as session:
            provider = await session.get(SSOProvider, provider_id)
            if not provider:
                raise NotFoundError(f"SSO provider not found: {provider_id}")
            
            # Delete related records
            await session.execute(
                delete(SSOSession).where(SSOSession.provider_id == provider_id)
            )
            await session.execute(
                delete(SSOAuditLog).where(SSOAuditLog.provider_id == provider_id)
            )
            
            # Delete provider-specific configurations
            if provider.provider_type == SSOProviderType.SAML:
                await session.execute(
                    delete(SAMLProvider).where(SAMLProvider.sso_provider_id == provider_id)
                )
            elif provider.provider_type == SSOProviderType.LDAP:
                await session.execute(
                    delete(LDAPProvider).where(LDAPProvider.sso_provider_id == provider_id)
                )
            
            # Delete provider
            await session.delete(provider)
            await session.commit()
            
            logger.info(f"SSO provider deleted: {provider.provider_name}")
            
            return True
    
    async def create_saml_provider(self, saml_data: SAMLProviderCreate) -> SAMLProviderResponse:
        """Create SAML provider configuration"""
        async with get_db_session() as session:
            # Check if SSO provider exists
            sso_provider = await session.get(SSOProvider, saml_data.sso_provider_id)
            if not sso_provider:
                raise NotFoundError(f"SSO provider not found: {saml_data.sso_provider_id}")
            
            if sso_provider.provider_type != SSOProviderType.SAML:
                raise ValidationError("SSO provider must be of type SAML")
            
            # Create SAML provider
            saml_provider = SAMLProvider(
                id=uuid.uuid4(),
                sso_provider_id=saml_data.sso_provider_id,
                entity_id=saml_data.entity_id,
                sso_url=saml_data.sso_url,
                slo_url=saml_data.slo_url,
                x509_cert=saml_data.x509_cert,
                sp_entity_id=saml_data.sp_entity_id,
                sp_acs_url=saml_data.sp_acs_url,
                sp_sls_url=saml_data.sp_sls_url,
                sp_x509_cert=saml_data.sp_x509_cert,
                sp_private_key=saml_data.sp_private_key,
                name_id_format=saml_data.name_id_format,
                authn_requests_signed=saml_data.authn_requests_signed,
                logout_requests_signed=saml_data.logout_requests_signed,
                want_assertions_signed=saml_data.want_assertions_signed,
                want_name_id_encrypted=saml_data.want_name_id_encrypted
            )
            
            session.add(saml_provider)
            await session.commit()
            await session.refresh(saml_provider)
            
            logger.info(f"SAML provider created: {saml_provider.entity_id}")
            
            return SAMLProviderResponse.from_orm(saml_provider)
    
    async def create_ldap_provider(self, ldap_data: LDAPProviderCreate) -> LDAPProviderResponse:
        """Create LDAP provider configuration"""
        async with get_db_session() as session:
            # Check if SSO provider exists
            sso_provider = await session.get(SSOProvider, ldap_data.sso_provider_id)
            if not sso_provider:
                raise NotFoundError(f"SSO provider not found: {ldap_data.sso_provider_id}")
            
            if sso_provider.provider_type != SSOProviderType.LDAP:
                raise ValidationError("SSO provider must be of type LDAP")
            
            # Create LDAP provider
            ldap_provider = LDAPProvider(
                id=uuid.uuid4(),
                sso_provider_id=ldap_data.sso_provider_id,
                server_url=ldap_data.server_url,
                bind_dn=ldap_data.bind_dn,
                bind_password=ldap_data.bind_password,
                base_dn=ldap_data.base_dn,
                user_search_filter=ldap_data.user_search_filter,
                user_search_base=ldap_data.user_search_base,
                group_search_filter=ldap_data.group_search_filter,
                group_search_base=ldap_data.group_search_base,
                use_ssl=ldap_data.use_ssl,
                use_tls=ldap_data.use_tls,
                timeout=ldap_data.timeout,
                username_attribute=ldap_data.username_attribute,
                email_attribute=ldap_data.email_attribute,
                first_name_attribute=ldap_data.first_name_attribute,
                last_name_attribute=ldap_data.last_name_attribute,
                display_name_attribute=ldap_data.display_name_attribute
            )
            
            session.add(ldap_provider)
            await session.commit()
            await session.refresh(ldap_provider)
            
            logger.info(f"LDAP provider created: {ldap_provider.server_url}")
            
            return LDAPProviderResponse.from_orm(ldap_provider)
    
    async def authenticate_user(self, login_request: SSOLoginRequest) -> SSOLoginResponse:
        """Authenticate user via SSO"""
        async with get_db_session() as session:
            # Get SSO provider
            provider = await session.get(SSOProvider, login_request.provider_id)
            if not provider:
                raise NotFoundError(f"SSO provider not found: {login_request.provider_id}")
            
            if not provider.is_active:
                raise ValidationError("SSO provider is not active")
            
            # Log authentication attempt
            await self._log_audit_event(
                session,
                provider.id,
                SSOEventType.LOGIN,
                SSOEventStatus.PENDING,
                username=login_request.username,
                ip_address=login_request.ip_address,
                user_agent=login_request.user_agent
            )
            
            try:
                # Authenticate based on provider type
                if provider.provider_type == SSOProviderType.SAML:
                    return await self._authenticate_saml(session, provider, login_request)
                elif provider.provider_type == SSOProviderType.LDAP:
                    return await self._authenticate_ldap(session, provider, login_request)
                else:
                    raise ValidationError(f"Unsupported provider type: {provider.provider_type}")
                
            except Exception as e:
                # Log failed authentication
                await self._log_audit_event(
                    session,
                    provider.id,
                    SSOEventType.LOGIN,
                    SSOEventStatus.FAILURE,
                    username=login_request.username,
                    ip_address=login_request.ip_address,
                    user_agent=login_request.user_agent,
                    event_message=str(e)
                )
                raise
    
    async def _authenticate_saml(self, session: AsyncSession, provider: SSOProvider, login_request: SSOLoginRequest) -> SSOLoginResponse:
        """Authenticate via SAML"""
        # Get SAML provider configuration
        saml_result = await session.execute(
            select(SAMLProvider).where(SAMLProvider.sso_provider_id == provider.id)
        )
        saml_provider = saml_result.scalar_one_or_none()
        if not saml_provider:
            raise ValidationError("SAML provider configuration not found")
        
        # Initialize SAML handler
        saml_handler = SAMLHandler(saml_provider)
        
        # Process SAML response
        if login_request.saml_response:
            request_data = {
                'post_data': {
                    'SAMLResponse': login_request.saml_response,
                    'RelayState': login_request.relay_state or ''
                }
            }
            
            success, result = saml_handler.process_response(request_data)
            
            if success:
                # Provision or update user
                user = await self._provision_user(session, provider, result)
                
                # Create SSO session
                sso_session = await self._create_sso_session(
                    session,
                    provider.id,
                    user.id,
                    login_request.username,
                    result.get('email'),
                    "saml",
                    login_request.ip_address,
                    login_request.user_agent,
                    result
                )
                
                # Log successful authentication
                await self._log_audit_event(
                    session,
                    provider.id,
                    SSOEventType.LOGIN,
                    SSOEventStatus.SUCCESS,
                    user_id=user.id,
                    username=login_request.username,
                    ip_address=login_request.ip_address,
                    user_agent=login_request.user_agent
                )
                
                return SSOLoginResponse(
                    success=True,
                    message="SAML authentication successful",
                    user_id=str(user.id),
                    session_id=sso_session.session_id,
                    redirect_url=login_request.relay_state
                )
            else:
                raise AuthenticationError(f"SAML authentication failed: {result.get('error')}")
        else:
            # Generate SAML login URL
            request_data = {
                'http_host': 'localhost',  # This should be dynamic
                'server_port': '443',
                'https': 'on'
            }
            
            login_url = saml_handler.generate_login_url(request_data, login_request.relay_state)
            
            return SSOLoginResponse(
                success=True,
                message="SAML login URL generated",
                redirect_url=login_url
            )
    
    async def _authenticate_ldap(self, session: AsyncSession, provider: SSOProvider, login_request: SSOLoginRequest) -> SSOLoginResponse:
        """Authenticate via LDAP"""
        # Get LDAP provider configuration
        ldap_result = await session.execute(
            select(LDAPProvider).where(LDAPProvider.sso_provider_id == provider.id)
        )
        ldap_provider = ldap_result.scalar_one_or_none()
        if not ldap_provider:
            raise ValidationError("LDAP provider configuration not found")
        
        # Initialize LDAP handler
        ldap_handler = LDAPHandler(ldap_provider)
        
        # Authenticate user
        if not login_request.password:
            raise ValidationError("Password is required for LDAP authentication")
        
        success, result = await ldap_handler.authenticate(login_request.username, login_request.password)
        
        if success:
            # Provision or update user
            user = await self._provision_user(session, provider, result)
            
            # Create SSO session
            sso_session = await self._create_sso_session(
                session,
                provider.id,
                user.id,
                login_request.username,
                result.get('email'),
                "ldap",
                login_request.ip_address,
                login_request.user_agent,
                result
            )
            
            # Log successful authentication
            await self._log_audit_event(
                session,
                provider.id,
                SSOEventType.LOGIN,
                SSOEventStatus.SUCCESS,
                user_id=user.id,
                username=login_request.username,
                ip_address=login_request.ip_address,
                user_agent=login_request.user_agent
            )
            
            return SSOLoginResponse(
                success=True,
                message="LDAP authentication successful",
                user_id=str(user.id),
                session_id=sso_session.session_id
            )
        else:
            raise AuthenticationError(f"LDAP authentication failed: {result.get('error')}")
    
    async def _provision_user(self, session: AsyncSession, provider: SSOProvider, user_data: Dict[str, Any]) -> User:
        """Provision or update user from SSO"""
        # Look for existing user
        email = user_data.get('email')
        username = user_data.get('username')
        
        user = None
        if email:
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
        
        if not user and username:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()
        
        if user:
            # Update existing user
            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)
            user.display_name = user_data.get('display_name', user.display_name)
            user.updated_at = datetime.utcnow()
            
            logger.info(f"Updated existing user: {user.email}")
        else:
            # Create new user if auto-provisioning is enabled
            if not provider.auto_provision:
                raise ValidationError("User not found and auto-provisioning is disabled")
            
            user = User(
                id=uuid.uuid4(),
                username=username,
                email=email,
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                display_name=user_data.get('display_name', username),
                school_id=provider.school_id,
                is_active=True,
                email_verified=True,
                created_at=datetime.utcnow()
            )
            
            session.add(user)
            logger.info(f"Created new user: {user.email}")
        
        await session.commit()
        await session.refresh(user)
        
        return user
    
    async def _create_sso_session(self, session: AsyncSession, provider_id: str, user_id: str, username: str, email: Optional[str], login_method: str, ip_address: Optional[str], user_agent: Optional[str], attributes: Dict[str, Any]) -> SSOSession:
        """Create SSO session"""
        sso_session = SSOSession(
            id=uuid.uuid4(),
            provider_id=provider_id,
            user_id=user_id,
            session_id=secrets.token_urlsafe(32),
            username=username,
            email=email,
            login_method=login_method,
            ip_address=ip_address,
            user_agent=user_agent,
            attributes=attributes,
            expires_at=datetime.utcnow() + self.session_timeout
        )
        
        session.add(sso_session)
        await session.commit()
        await session.refresh(sso_session)
        
        return sso_session
    
    async def _log_audit_event(self, session: AsyncSession, provider_id: str, event_type: SSOEventType, event_status: SSOEventStatus, user_id: Optional[str] = None, username: Optional[str] = None, email: Optional[str] = None, ip_address: Optional[str] = None, user_agent: Optional[str] = None, event_message: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """Log SSO audit event"""
        audit_log = SSOAuditLog(
            id=uuid.uuid4(),
            provider_id=provider_id,
            user_id=user_id,
            event_type=event_type,
            event_status=event_status,
            event_message=event_message,
            username=username,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
        
        session.add(audit_log)
    
    async def test_sso_connection(self, test_request: SSOTestConnectionRequest) -> SSOTestConnectionResponse:
        """Test SSO provider connection"""
        try:
            if test_request.provider_type == SSOProviderType.SAML:
                return await self._test_saml_connection(test_request.configuration)
            elif test_request.provider_type == SSOProviderType.LDAP:
                return await self._test_ldap_connection(test_request.configuration)
            else:
                raise ValidationError(f"Unsupported provider type: {test_request.provider_type}")
        
        except Exception as e:
            logger.error(f"SSO connection test failed: {str(e)}")
            return SSOTestConnectionResponse(
                success=False,
                message=f"Connection test failed: {str(e)}"
            )
    
    async def _test_saml_connection(self, configuration: Dict[str, Any]) -> SSOTestConnectionResponse:
        """Test SAML connection"""
        # Create temporary SAML provider for testing
        saml_provider = SAMLProvider(
            entity_id=configuration.get('entity_id'),
            sso_url=configuration.get('sso_url'),
            x509_cert=configuration.get('x509_cert'),
            sp_entity_id=configuration.get('sp_entity_id'),
            sp_acs_url=configuration.get('sp_acs_url')
        )
        
        # Create temporary SSO provider
        sso_provider = SSOProvider(
            provider_type=SSOProviderType.SAML,
            attribute_mapping=configuration.get('attribute_mapping', {}),
            role_mapping=configuration.get('role_mapping', {})
        )
        
        saml_provider.sso_provider = sso_provider
        
        # Test connection
        saml_handler = SAMLHandler(saml_provider)
        result = saml_handler.test_connection()
        
        return SSOTestConnectionResponse(
            success=result["success"],
            message=result["message"],
            details=result
        )
    
    async def _test_ldap_connection(self, configuration: Dict[str, Any]) -> SSOTestConnectionResponse:
        """Test LDAP connection"""
        # Create temporary LDAP provider for testing
        ldap_provider = LDAPProvider(
            server_url=configuration.get('server_url'),
            bind_dn=configuration.get('bind_dn'),
            bind_password=configuration.get('bind_password'),
            base_dn=configuration.get('base_dn'),
            use_ssl=configuration.get('use_ssl', True),
            use_tls=configuration.get('use_tls', False),
            timeout=configuration.get('timeout', 30)
        )
        
        # Create temporary SSO provider
        sso_provider = SSOProvider(
            provider_type=SSOProviderType.LDAP,
            attribute_mapping=configuration.get('attribute_mapping', {}),
            role_mapping=configuration.get('role_mapping', {})
        )
        
        ldap_provider.sso_provider = sso_provider
        
        # Test connection
        ldap_handler = LDAPHandler(ldap_provider)
        result = await ldap_handler.test_connection()
        
        return SSOTestConnectionResponse(
            success=result["success"],
            message=result["message"],
            details=result
        )
    
    async def get_sso_stats(self, school_id: str) -> SSOStatsResponse:
        """Get SSO statistics for a school"""
        async with get_db_session() as session:
            # Get provider counts
            provider_counts = await session.execute(
                select(
                    func.count(SSOProvider.id).label('total'),
                    func.count(SSOProvider.id).filter(SSOProvider.is_active == True).label('active'),
                    func.count(SSOProvider.id).filter(SSOProvider.provider_type == 'saml').label('saml'),
                    func.count(SSOProvider.id).filter(SSOProvider.provider_type == 'ldap').label('ldap'),
                    func.count(SSOProvider.id).filter(SSOProvider.provider_type == 'oauth2').label('oauth2')
                )
                .where(SSOProvider.school_id == school_id)
            )
            provider_stats = provider_counts.first()
            
            # Get session counts
            session_counts = await session.execute(
                select(
                    func.count(SSOSession.id).label('total'),
                    func.count(SSOSession.id).filter(SSOSession.is_active == True).label('active')
                )
                .join(SSOProvider, SSOSession.provider_id == SSOProvider.id)
                .where(SSOProvider.school_id == school_id)
            )
            session_stats = session_counts.first()
            
            # Get login counts
            today = datetime.utcnow().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            login_counts = await session.execute(
                select(
                    func.count(SSOAuditLog.id).filter(
                        and_(
                            SSOAuditLog.event_type == 'login',
                            SSOAuditLog.event_status == 'success',
                            func.date(SSOAuditLog.created_at) == today
                        )
                    ).label('today'),
                    func.count(SSOAuditLog.id).filter(
                        and_(
                            SSOAuditLog.event_type == 'login',
                            SSOAuditLog.event_status == 'success',
                            func.date(SSOAuditLog.created_at) >= week_ago
                        )
                    ).label('week'),
                    func.count(SSOAuditLog.id).filter(
                        and_(
                            SSOAuditLog.event_type == 'login',
                            SSOAuditLog.event_status == 'success',
                            func.date(SSOAuditLog.created_at) >= month_ago
                        )
                    ).label('month'),
                    func.count(SSOAuditLog.id).filter(
                        and_(
                            SSOAuditLog.event_type == 'login',
                            SSOAuditLog.event_status == 'failure',
                            func.date(SSOAuditLog.created_at) == today
                        )
                    ).label('failed_today')
                )
                .join(SSOProvider, SSOAuditLog.provider_id == SSOProvider.id)
                .where(SSOProvider.school_id == school_id)
            )
            login_stats = login_counts.first()
            
            return SSOStatsResponse(
                total_providers=provider_stats.total or 0,
                active_providers=provider_stats.active or 0,
                saml_providers=provider_stats.saml or 0,
                ldap_providers=provider_stats.ldap or 0,
                oauth2_providers=provider_stats.oauth2 or 0,
                total_sessions=session_stats.total or 0,
                active_sessions=session_stats.active or 0,
                total_logins_today=login_stats.today or 0,
                total_logins_week=login_stats.week or 0,
                total_logins_month=login_stats.month or 0,
                failed_logins_today=login_stats.failed_today or 0
            )