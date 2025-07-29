"""
Domain Management Service
Core service for managing school domains and email addresses
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
    ExternalServiceError
)
from .models import (
    Domain,
    EmailAddress,
    SSLCertificate,
    DomainVerification,
    DomainTemplate
)
from .schemas import (
    DomainCreate,
    DomainUpdate,
    DomainResponse,
    EmailAddressCreate,
    EmailAddressUpdate,
    EmailAddressResponse,
    SSLCertificateCreate,
    SSLCertificateResponse,
    DomainVerificationCreate,
    DomainVerificationResponse,
    DomainValidationResponse,
    DomainStatsResponse,
    BulkEmailCreateRequest,
    BulkEmailCreateResponse
)

logger = logging.getLogger(__name__)


class DomainManagementService:
    """Service for managing school domains and email addresses"""
    
    def __init__(self):
        self.base_domain = "oneclass.ac.zw"
        self.max_subdomain_length = 50
        self.min_subdomain_length = 3
    
    async def create_domain(self, domain_data: DomainCreate, created_by: str) -> DomainResponse:
        """Create a new domain for a school"""
        async with get_db_session() as session:
            # Check if school already has a domain
            existing_domain = await session.execute(
                select(Domain).where(Domain.school_id == domain_data.school_id)
            )
            if existing_domain.scalar_one_or_none():
                raise ConflictError(f"School already has a domain configured")
            
            # Check if subdomain is available
            subdomain_exists = await session.execute(
                select(Domain).where(Domain.subdomain == domain_data.subdomain)
            )
            if subdomain_exists.scalar_one_or_none():
                raise ConflictError(f"Subdomain '{domain_data.subdomain}' is already taken")
            
            # Check custom domain if provided
            if domain_data.custom_domain:
                custom_domain_exists = await session.execute(
                    select(Domain).where(Domain.custom_domain == domain_data.custom_domain)
                )
                if custom_domain_exists.scalar_one_or_none():
                    raise ConflictError(f"Custom domain '{domain_data.custom_domain}' is already taken")
            
            # Create domain
            domain = Domain(
                id=uuid.uuid4(),
                school_id=domain_data.school_id,
                subdomain=domain_data.subdomain,
                custom_domain=domain_data.custom_domain,
                email_domain_enabled=domain_data.email_domain_enabled,
                email_provider=domain_data.email_provider,
                email_provider_config=domain_data.email_provider_config,
                dns_provider=domain_data.dns_provider,
                verification_token=secrets.token_urlsafe(32),
                created_by=created_by
            )
            
            session.add(domain)
            await session.commit()
            await session.refresh(domain)
            
            # Create verification record
            await self._create_domain_verification(session, domain.id)
            
            # Set up DNS records
            await self._setup_dns_records(domain)
            
            # Set up SSL certificate
            await self._setup_ssl_certificate(domain)
            
            logger.info(f"Domain created: {domain.full_domain} for school {domain.school_id}")
            
            return DomainResponse.from_orm(domain)
    
    async def get_domain(self, domain_id: str) -> DomainResponse:
        """Get domain by ID"""
        async with get_db_session() as session:
            domain = await session.get(Domain, domain_id)
            if not domain:
                raise NotFoundError(f"Domain not found: {domain_id}")
            
            return DomainResponse.from_orm(domain)
    
    async def get_domain_by_subdomain(self, subdomain: str) -> DomainResponse:
        """Get domain by subdomain"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Domain).where(Domain.subdomain == subdomain)
            )
            domain = result.scalar_one_or_none()
            if not domain:
                raise NotFoundError(f"Domain not found: {subdomain}")
            
            return DomainResponse.from_orm(domain)
    
    async def get_school_domain(self, school_id: str) -> DomainResponse:
        """Get domain for a school"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Domain).where(Domain.school_id == school_id)
            )
            domain = result.scalar_one_or_none()
            if not domain:
                raise NotFoundError(f"No domain found for school: {school_id}")
            
            return DomainResponse.from_orm(domain)
    
    async def update_domain(self, domain_id: str, domain_data: DomainUpdate) -> DomainResponse:
        """Update domain"""
        async with get_db_session() as session:
            domain = await session.get(Domain, domain_id)
            if not domain:
                raise NotFoundError(f"Domain not found: {domain_id}")
            
            # Check custom domain availability if changing
            if domain_data.custom_domain and domain_data.custom_domain != domain.custom_domain:
                custom_domain_exists = await session.execute(
                    select(Domain).where(
                        and_(
                            Domain.custom_domain == domain_data.custom_domain,
                            Domain.id != domain_id
                        )
                    )
                )
                if custom_domain_exists.scalar_one_or_none():
                    raise ConflictError(f"Custom domain '{domain_data.custom_domain}' is already taken")
            
            # Update domain
            update_data = domain_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(domain, field, value)
            
            domain.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(domain)
            
            logger.info(f"Domain updated: {domain.full_domain}")
            
            return DomainResponse.from_orm(domain)
    
    async def delete_domain(self, domain_id: str) -> bool:
        """Delete domain"""
        async with get_db_session() as session:
            domain = await session.get(Domain, domain_id)
            if not domain:
                raise NotFoundError(f"Domain not found: {domain_id}")
            
            # Delete related records
            await session.execute(
                delete(EmailAddress).where(EmailAddress.domain_id == domain_id)
            )
            await session.execute(
                delete(SSLCertificate).where(SSLCertificate.domain_id == domain_id)
            )
            await session.execute(
                delete(DomainVerification).where(DomainVerification.domain_id == domain_id)
            )
            
            # Delete domain
            await session.delete(domain)
            await session.commit()
            
            logger.info(f"Domain deleted: {domain.full_domain}")
            
            return True
    
    async def validate_domain(self, subdomain: str, custom_domain: Optional[str] = None) -> DomainValidationResponse:
        """Validate domain availability and format"""
        async with get_db_session() as session:
            errors = []
            suggestions = []
            
            # Validate subdomain format
            if not Domain().validate_subdomain(subdomain):
                errors.append("Invalid subdomain format")
            
            # Check subdomain availability
            subdomain_exists = await session.execute(
                select(Domain).where(Domain.subdomain == subdomain)
            )
            subdomain_available = subdomain_exists.scalar_one_or_none() is None
            
            if not subdomain_available:
                # Generate suggestions
                for i in range(1, 6):
                    suggestion = f"{subdomain}{i}"
                    suggestion_exists = await session.execute(
                        select(Domain).where(Domain.subdomain == suggestion)
                    )
                    if suggestion_exists.scalar_one_or_none() is None:
                        suggestions.append(suggestion)
            
            # Validate custom domain if provided
            custom_domain_available = True
            if custom_domain:
                if not Domain().validate_custom_domain(custom_domain):
                    errors.append("Invalid custom domain format")
                
                custom_domain_exists = await session.execute(
                    select(Domain).where(Domain.custom_domain == custom_domain)
                )
                custom_domain_available = custom_domain_exists.scalar_one_or_none() is None
            
            is_valid = len(errors) == 0
            
            return DomainValidationResponse(
                is_valid=is_valid,
                subdomain_available=subdomain_available,
                custom_domain_available=custom_domain_available,
                suggestions=suggestions,
                errors=errors
            )
    
    async def create_email_address(self, email_data: EmailAddressCreate) -> EmailAddressResponse:
        """Create email address for domain"""
        async with get_db_session() as session:
            # Get domain
            domain = await session.get(Domain, email_data.domain_id)
            if not domain:
                raise NotFoundError(f"Domain not found: {email_data.domain_id}")
            
            if not domain.email_domain_enabled:
                raise ValidationError("Email domain is not enabled for this domain")
            
            # Generate email address
            email_address = f"{email_data.username}@{domain.email_domain}"
            
            # Check if email address already exists
            existing_email = await session.execute(
                select(EmailAddress).where(EmailAddress.email_address == email_address)
            )
            if existing_email.scalar_one_or_none():
                raise ConflictError(f"Email address '{email_address}' already exists")
            
            # Create email address
            email = EmailAddress(
                id=uuid.uuid4(),
                domain_id=email_data.domain_id,
                user_id=email_data.user_id,
                email_address=email_address,
                username=email_data.username,
                forward_to=email_data.forward_to,
                forward_enabled=email_data.forward_enabled,
                storage_quota_mb=email_data.storage_quota_mb,
                daily_send_limit=email_data.daily_send_limit,
                verification_token=secrets.token_urlsafe(32)
            )
            
            session.add(email)
            await session.commit()
            await session.refresh(email)
            
            # Set up email in provider
            await self._setup_email_in_provider(email, domain)
            
            logger.info(f"Email address created: {email.email_address}")
            
            return EmailAddressResponse.from_orm(email)
    
    async def get_domain_emails(self, domain_id: str, skip: int = 0, limit: int = 100) -> List[EmailAddressResponse]:
        """Get email addresses for domain"""
        async with get_db_session() as session:
            result = await session.execute(
                select(EmailAddress)
                .where(EmailAddress.domain_id == domain_id)
                .offset(skip)
                .limit(limit)
                .order_by(EmailAddress.created_at.desc())
            )
            emails = result.scalars().all()
            
            return [EmailAddressResponse.from_orm(email) for email in emails]
    
    async def get_domain_stats(self, domain_id: str) -> DomainStatsResponse:
        """Get domain statistics"""
        async with get_db_session() as session:
            # Get domain info
            domain = await session.get(Domain, domain_id)
            if not domain:
                raise NotFoundError(f"Domain not found: {domain_id}")
            
            # Get email counts
            email_count = await session.execute(
                select(func.count(EmailAddress.id))
                .where(EmailAddress.domain_id == domain_id)
            )
            total_emails = email_count.scalar() or 0
            
            active_email_count = await session.execute(
                select(func.count(EmailAddress.id))
                .where(
                    and_(
                        EmailAddress.domain_id == domain_id,
                        EmailAddress.is_active == True
                    )
                )
            )
            active_emails = active_email_count.scalar() or 0
            
            # Get SSL certificate info
            ssl_count = await session.execute(
                select(func.count(SSLCertificate.id))
                .where(SSLCertificate.domain_id == domain_id)
            )
            ssl_certificates = ssl_count.scalar() or 0
            
            expired_ssl_count = await session.execute(
                select(func.count(SSLCertificate.id))
                .where(
                    and_(
                        SSLCertificate.domain_id == domain_id,
                        SSLCertificate.expires_at < datetime.utcnow()
                    )
                )
            )
            expired_certificates = expired_ssl_count.scalar() or 0
            
            expiring_soon_count = await session.execute(
                select(func.count(SSLCertificate.id))
                .where(
                    and_(
                        SSLCertificate.domain_id == domain_id,
                        SSLCertificate.expires_at < datetime.utcnow() + timedelta(days=30)
                    )
                )
            )
            expiring_soon = expiring_soon_count.scalar() or 0
            
            return DomainStatsResponse(
                total_domains=1,
                active_domains=1 if domain.is_active else 0,
                verified_domains=1 if domain.is_verified else 0,
                ssl_certificates=ssl_certificates,
                expired_certificates=expired_certificates,
                expiring_soon=expiring_soon,
                email_addresses=total_emails,
                active_email_addresses=active_emails
            )
    
    async def verify_domain(self, domain_id: str) -> bool:
        """Verify domain ownership"""
        async with get_db_session() as session:
            domain = await session.get(Domain, domain_id)
            if not domain:
                raise NotFoundError(f"Domain not found: {domain_id}")
            
            # Get verification record
            verification = await session.execute(
                select(DomainVerification)
                .where(DomainVerification.domain_id == domain_id)
                .order_by(DomainVerification.created_at.desc())
            )
            verification_record = verification.scalar_one_or_none()
            
            if not verification_record:
                raise NotFoundError(f"No verification record found for domain: {domain_id}")
            
            if verification_record.is_verified:
                return True
            
            # Perform verification check
            verified = await self._check_domain_verification(domain, verification_record)
            
            if verified:
                domain.is_verified = True
                verification_record.is_verified = True
                verification_record.verified_at = datetime.utcnow()
                await session.commit()
                
                logger.info(f"Domain verified: {domain.full_domain}")
                return True
            else:
                verification_record.verification_attempts += 1
                await session.commit()
                
                logger.warning(f"Domain verification failed: {domain.full_domain}")
                return False
    
    async def _create_domain_verification(self, session: AsyncSession, domain_id: str) -> DomainVerification:
        """Create domain verification record"""
        verification = DomainVerification(
            id=uuid.uuid4(),
            domain_id=domain_id,
            verification_type="dns",
            verification_method="txt_record",
            verification_token=secrets.token_urlsafe(32),
            verification_value=f"oneclass-verification={secrets.token_urlsafe(16)}",
            verification_record=f"_oneclass.{domain_id}",
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        session.add(verification)
        return verification
    
    async def _setup_dns_records(self, domain: Domain) -> bool:
        """Set up DNS records for domain"""
        # This would integrate with DNS provider API (Cloudflare, etc.)
        # For now, we'll just log the DNS records that need to be created
        
        dns_records = [
            {
                "type": "A",
                "name": domain.subdomain,
                "value": "YOUR_SERVER_IP",
                "ttl": 300
            },
            {
                "type": "CNAME",
                "name": f"www.{domain.subdomain}",
                "value": f"{domain.subdomain}.{self.base_domain}",
                "ttl": 300
            },
            {
                "type": "MX",
                "name": domain.subdomain,
                "value": f"10 mail.{self.base_domain}",
                "ttl": 300
            },
            {
                "type": "TXT",
                "name": f"_oneclass.{domain.subdomain}",
                "value": domain.verification_token,
                "ttl": 300
            }
        ]
        
        domain.dns_records = dns_records
        
        logger.info(f"DNS records configured for domain: {domain.full_domain}")
        return True
    
    async def _setup_ssl_certificate(self, domain: Domain) -> bool:
        """Set up SSL certificate for domain"""
        # This would integrate with Let's Encrypt or other SSL provider
        # For now, we'll create a placeholder SSL certificate record
        
        async with get_db_session() as session:
            ssl_cert = SSLCertificate(
                id=uuid.uuid4(),
                domain_id=domain.id,
                certificate_id=f"cert_{secrets.token_urlsafe(16)}",
                certificate_type="lets_encrypt",
                issued_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=90),
                auto_renew=True
            )
            
            session.add(ssl_cert)
            await session.commit()
            
            # Update domain with SSL certificate ID
            domain.ssl_certificate_id = ssl_cert.certificate_id
            domain.ssl_certificate_expires = ssl_cert.expires_at
            
            logger.info(f"SSL certificate configured for domain: {domain.full_domain}")
            return True
    
    async def _setup_email_in_provider(self, email: EmailAddress, domain: Domain) -> bool:
        """Set up email address in email provider"""
        # This would integrate with email provider API (Google Workspace, Microsoft 365, etc.)
        # For now, we'll just log the email setup
        
        if domain.email_provider == "google":
            # Google Workspace integration
            pass
        elif domain.email_provider == "microsoft":
            # Microsoft 365 integration
            pass
        else:
            # Internal email system
            pass
        
        logger.info(f"Email address configured in provider: {email.email_address}")
        return True
    
    async def _check_domain_verification(self, domain: Domain, verification: DomainVerification) -> bool:
        """Check if domain verification is valid"""
        # This would check DNS records or file verification
        # For now, we'll simulate verification
        
        if verification.verification_type == "dns":
            # Check TXT record
            # import dns.resolver
            # try:
            #     answers = dns.resolver.resolve(verification.verification_record, 'TXT')
            #     for answer in answers:
            #         if verification.verification_value in str(answer):
            #             return True
            # except:
            #     pass
            pass
        
        # For development, return True after first attempt
        return verification.verification_attempts == 0