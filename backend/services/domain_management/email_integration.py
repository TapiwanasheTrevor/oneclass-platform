"""
Email Integration Service
Handles email provider integration for school domains
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import imaplib
import email

from shared.config import settings
from shared.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


@dataclass
class EmailAccount:
    """Email account data structure"""
    email_address: str
    password: str
    display_name: Optional[str] = None
    storage_quota_mb: int = 1000
    daily_send_limit: int = 100
    forward_to: Optional[str] = None
    auto_forward: bool = False


class EmailProviderBase(ABC):
    """Base class for email providers"""
    
    @abstractmethod
    async def create_email_account(self, account: EmailAccount) -> Dict[str, Any]:
        """Create email account"""
        pass
    
    @abstractmethod
    async def update_email_account(self, email_address: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update email account"""
        pass
    
    @abstractmethod
    async def delete_email_account(self, email_address: str) -> bool:
        """Delete email account"""
        pass
    
    @abstractmethod
    async def get_email_account(self, email_address: str) -> Optional[Dict[str, Any]]:
        """Get email account details"""
        pass
    
    @abstractmethod
    async def list_email_accounts(self, domain: str) -> List[Dict[str, Any]]:
        """List email accounts for domain"""
        pass
    
    @abstractmethod
    async def send_email(self, from_email: str, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Send email"""
        pass


class GoogleWorkspaceProvider(EmailProviderBase):
    """Google Workspace email provider"""
    
    def __init__(self, admin_email: str, credentials_path: str):
        self.admin_email = admin_email
        self.credentials_path = credentials_path
        # This would use Google Admin SDK
        logger.info("Google Workspace provider initialized")
    
    async def create_email_account(self, account: EmailAccount) -> Dict[str, Any]:
        """Create email account in Google Workspace"""
        # Implementation would use Google Admin SDK
        # https://developers.google.com/admin-sdk/directory/v1/guides/manage-users
        
        user_data = {
            "name": {
                "givenName": account.display_name or account.email_address.split('@')[0],
                "familyName": "User"
            },
            "password": account.password,
            "primaryEmail": account.email_address,
            "quotaInGb": account.storage_quota_mb // 1024,
            "suspended": False
        }
        
        # Mock implementation - would use actual Google Admin SDK
        logger.info(f"Would create Google Workspace account: {account.email_address}")
        
        return {
            "id": f"google_{account.email_address}",
            "email": account.email_address,
            "status": "active",
            "provider": "google",
            "storage_quota_mb": account.storage_quota_mb
        }
    
    async def update_email_account(self, email_address: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update email account in Google Workspace"""
        logger.info(f"Would update Google Workspace account: {email_address}")
        return {"email": email_address, "updated": True}
    
    async def delete_email_account(self, email_address: str) -> bool:
        """Delete email account from Google Workspace"""
        logger.info(f"Would delete Google Workspace account: {email_address}")
        return True
    
    async def get_email_account(self, email_address: str) -> Optional[Dict[str, Any]]:
        """Get email account from Google Workspace"""
        logger.info(f"Would get Google Workspace account: {email_address}")
        return None
    
    async def list_email_accounts(self, domain: str) -> List[Dict[str, Any]]:
        """List email accounts for domain from Google Workspace"""
        logger.info(f"Would list Google Workspace accounts for domain: {domain}")
        return []
    
    async def send_email(self, from_email: str, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Send email via Google Workspace"""
        logger.info(f"Would send email from {from_email} to {to_email}")
        return True


class Microsoft365Provider(EmailProviderBase):
    """Microsoft 365 email provider"""
    
    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        # This would use Microsoft Graph API
        logger.info("Microsoft 365 provider initialized")
    
    async def create_email_account(self, account: EmailAccount) -> Dict[str, Any]:
        """Create email account in Microsoft 365"""
        # Implementation would use Microsoft Graph API
        # https://docs.microsoft.com/en-us/graph/api/user-post-users
        
        user_data = {
            "accountEnabled": True,
            "displayName": account.display_name or account.email_address.split('@')[0],
            "mailNickname": account.email_address.split('@')[0],
            "userPrincipalName": account.email_address,
            "passwordProfile": {
                "forceChangePasswordNextSignIn": False,
                "password": account.password
            }
        }
        
        # Mock implementation - would use actual Microsoft Graph API
        logger.info(f"Would create Microsoft 365 account: {account.email_address}")
        
        return {
            "id": f"ms365_{account.email_address}",
            "email": account.email_address,
            "status": "active",
            "provider": "microsoft",
            "storage_quota_mb": account.storage_quota_mb
        }
    
    async def update_email_account(self, email_address: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update email account in Microsoft 365"""
        logger.info(f"Would update Microsoft 365 account: {email_address}")
        return {"email": email_address, "updated": True}
    
    async def delete_email_account(self, email_address: str) -> bool:
        """Delete email account from Microsoft 365"""
        logger.info(f"Would delete Microsoft 365 account: {email_address}")
        return True
    
    async def get_email_account(self, email_address: str) -> Optional[Dict[str, Any]]:
        """Get email account from Microsoft 365"""
        logger.info(f"Would get Microsoft 365 account: {email_address}")
        return None
    
    async def list_email_accounts(self, domain: str) -> List[Dict[str, Any]]:
        """List email accounts for domain from Microsoft 365"""
        logger.info(f"Would list Microsoft 365 accounts for domain: {domain}")
        return []
    
    async def send_email(self, from_email: str, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Send email via Microsoft 365"""
        logger.info(f"Would send email from {from_email} to {to_email}")
        return True


class InternalEmailProvider(EmailProviderBase):
    """Internal email provider using SMTP/IMAP"""
    
    def __init__(self, smtp_host: str, smtp_port: int, imap_host: str, imap_port: int, admin_user: str, admin_password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.accounts_db = {}  # In-memory storage for demo
        logger.info("Internal email provider initialized")
    
    async def create_email_account(self, account: EmailAccount) -> Dict[str, Any]:
        """Create email account in internal system"""
        # Store account in database or mail server
        self.accounts_db[account.email_address] = {
            "email": account.email_address,
            "password": account.password,
            "display_name": account.display_name,
            "storage_quota_mb": account.storage_quota_mb,
            "daily_send_limit": account.daily_send_limit,
            "forward_to": account.forward_to,
            "auto_forward": account.auto_forward,
            "created_at": "2024-01-01T00:00:00Z",
            "status": "active"
        }
        
        logger.info(f"Created internal email account: {account.email_address}")
        
        return {
            "id": f"internal_{account.email_address}",
            "email": account.email_address,
            "status": "active",
            "provider": "internal",
            "storage_quota_mb": account.storage_quota_mb
        }
    
    async def update_email_account(self, email_address: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update email account in internal system"""
        if email_address in self.accounts_db:
            self.accounts_db[email_address].update(updates)
            logger.info(f"Updated internal email account: {email_address}")
            return self.accounts_db[email_address]
        
        raise ExternalServiceError(f"Email account not found: {email_address}")
    
    async def delete_email_account(self, email_address: str) -> bool:
        """Delete email account from internal system"""
        if email_address in self.accounts_db:
            del self.accounts_db[email_address]
            logger.info(f"Deleted internal email account: {email_address}")
            return True
        
        return False
    
    async def get_email_account(self, email_address: str) -> Optional[Dict[str, Any]]:
        """Get email account from internal system"""
        return self.accounts_db.get(email_address)
    
    async def list_email_accounts(self, domain: str) -> List[Dict[str, Any]]:
        """List email accounts for domain from internal system"""
        return [
            account for account in self.accounts_db.values()
            if account["email"].endswith(f"@{domain}")
        ]
    
    async def send_email(self, from_email: str, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Send email via internal SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = to_email
            
            # Add text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.admin_user, self.admin_password)
                server.send_message(msg)
            
            logger.info(f"Sent email from {from_email} to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False


class EmailIntegrationService:
    """Email integration service"""
    
    def __init__(self):
        self.providers: Dict[str, EmailProviderBase] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize email providers"""
        # Initialize Google Workspace provider
        if (hasattr(settings, 'GOOGLE_ADMIN_EMAIL') and settings.GOOGLE_ADMIN_EMAIL and
            hasattr(settings, 'GOOGLE_CREDENTIALS_PATH') and settings.GOOGLE_CREDENTIALS_PATH):
            self.providers["google"] = GoogleWorkspaceProvider(
                settings.GOOGLE_ADMIN_EMAIL,
                settings.GOOGLE_CREDENTIALS_PATH
            )
        
        # Initialize Microsoft 365 provider
        if (hasattr(settings, 'MS365_TENANT_ID') and settings.MS365_TENANT_ID and
            hasattr(settings, 'MS365_CLIENT_ID') and settings.MS365_CLIENT_ID and
            hasattr(settings, 'MS365_CLIENT_SECRET') and settings.MS365_CLIENT_SECRET):
            self.providers["microsoft"] = Microsoft365Provider(
                settings.MS365_TENANT_ID,
                settings.MS365_CLIENT_ID,
                settings.MS365_CLIENT_SECRET
            )
        
        # Initialize internal email provider
        if (hasattr(settings, 'SMTP_HOST') and settings.SMTP_HOST and
            hasattr(settings, 'SMTP_USER') and settings.SMTP_USER and
            hasattr(settings, 'SMTP_PASSWORD') and settings.SMTP_PASSWORD):
            self.providers["internal"] = InternalEmailProvider(
                settings.SMTP_HOST,
                getattr(settings, 'SMTP_PORT', 587),
                getattr(settings, 'IMAP_HOST', settings.SMTP_HOST),
                getattr(settings, 'IMAP_PORT', 993),
                settings.SMTP_USER,
                settings.SMTP_PASSWORD
            )
    
    def get_provider(self, provider_name: str) -> EmailProviderBase:
        """Get email provider by name"""
        if provider_name not in self.providers:
            raise ValueError(f"Email provider '{provider_name}' not configured")
        return self.providers[provider_name]
    
    async def create_email_account(self, provider_name: str, account: EmailAccount) -> Dict[str, Any]:
        """Create email account using specified provider"""
        provider = self.get_provider(provider_name)
        return await provider.create_email_account(account)
    
    async def update_email_account(self, provider_name: str, email_address: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update email account using specified provider"""
        provider = self.get_provider(provider_name)
        return await provider.update_email_account(email_address, updates)
    
    async def delete_email_account(self, provider_name: str, email_address: str) -> bool:
        """Delete email account using specified provider"""
        provider = self.get_provider(provider_name)
        return await provider.delete_email_account(email_address)
    
    async def get_email_account(self, provider_name: str, email_address: str) -> Optional[Dict[str, Any]]:
        """Get email account using specified provider"""
        provider = self.get_provider(provider_name)
        return await provider.get_email_account(email_address)
    
    async def list_email_accounts(self, provider_name: str, domain: str) -> List[Dict[str, Any]]:
        """List email accounts for domain using specified provider"""
        provider = self.get_provider(provider_name)
        return await provider.list_email_accounts(domain)
    
    async def send_email(self, provider_name: str, from_email: str, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Send email using specified provider"""
        provider = self.get_provider(provider_name)
        return await provider.send_email(from_email, to_email, subject, body, html_body)
    
    async def setup_domain_email(self, domain: str, provider_name: str = "internal") -> Dict[str, Any]:
        """Set up email for domain"""
        provider = self.get_provider(provider_name)
        
        # Set up admin account
        admin_account = EmailAccount(
            email_address=f"admin@{domain}",
            password="temp_password_123",
            display_name="Administrator",
            storage_quota_mb=5000,
            daily_send_limit=500
        )
        
        admin_result = await provider.create_email_account(admin_account)
        
        # Set up no-reply account
        noreply_account = EmailAccount(
            email_address=f"noreply@{domain}",
            password="temp_password_123",
            display_name="No Reply",
            storage_quota_mb=1000,
            daily_send_limit=1000
        )
        
        noreply_result = await provider.create_email_account(noreply_account)
        
        logger.info(f"Set up email for domain: {domain}")
        
        return {
            "domain": domain,
            "provider": provider_name,
            "admin_account": admin_result,
            "noreply_account": noreply_result
        }
    
    async def send_welcome_email(self, email_address: str, username: str, school_name: str, temporary_password: str) -> bool:
        """Send welcome email to new user"""
        subject = f"Welcome to {school_name} - OneClass Platform"
        
        body = f"""
        Dear {username},
        
        Welcome to the OneClass Platform for {school_name}!
        
        Your school email account has been created:
        Email: {email_address}
        Temporary Password: {temporary_password}
        
        Please log in to your account and change your password immediately.
        
        You can access your account at: https://{email_address.split('@')[1]}
        
        If you have any questions, please contact your school administrator.
        
        Best regards,
        OneClass Platform Team
        """
        
        html_body = f"""
        <html>
        <head></head>
        <body>
            <h2>Welcome to {school_name} - OneClass Platform</h2>
            
            <p>Dear {username},</p>
            
            <p>Welcome to the OneClass Platform for {school_name}!</p>
            
            <p>Your school email account has been created:</p>
            <ul>
                <li><strong>Email:</strong> {email_address}</li>
                <li><strong>Temporary Password:</strong> {temporary_password}</li>
            </ul>
            
            <p>Please log in to your account and change your password immediately.</p>
            
            <p>You can access your account at: <a href="https://{email_address.split('@')[1]}">https://{email_address.split('@')[1]}</a></p>
            
            <p>If you have any questions, please contact your school administrator.</p>
            
            <p>Best regards,<br>
            OneClass Platform Team</p>
        </body>
        </html>
        """
        
        # Send via internal provider
        try:
            return await self.send_email(
                "internal",
                f"noreply@{email_address.split('@')[1]}",
                email_address,
                subject,
                body,
                html_body
            )
        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")
            return False