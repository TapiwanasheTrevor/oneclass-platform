"""
Email Utility Module
Handles email sending functionality for OneClass Platform
"""

import os
import logging
from typing import List, Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@oneclass.ac.zw")
FROM_NAME = os.getenv("FROM_NAME", "OneClass Platform")

class EmailService:
    """Email service for sending emails"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    def _send_email_sync(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Send email synchronously"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
            msg['To'] = ", ".join(to_emails)
            msg['Subject'] = subject
            
            # Add text body
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML body if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # Send email
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                if SMTP_USE_TLS:
                    server.starttls()
                if SMTP_USERNAME and SMTP_PASSWORD:
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_emails}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_emails}: {str(e)}")
            return False
    
    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Send email asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._send_email_sync,
            to_emails,
            subject,
            body,
            html_body,
            attachments
        )

# Global email service instance
email_service = EmailService()

# Convenience functions
async def send_email(
    to_emails: List[str],
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None
) -> bool:
    """Send email using the global email service"""
    return await email_service.send_email(
        to_emails=to_emails,
        subject=subject,
        body=body,
        html_body=html_body,
        attachments=attachments
    )

async def send_welcome_email(user_email: str, user_name: str, school_name: str) -> bool:
    """Send welcome email to new user"""
    subject = f"Welcome to {school_name} - OneClass Platform"
    body = f"""
Dear {user_name},

Welcome to the OneClass Platform for {school_name}!

Your account has been successfully created. You can now access the platform to:
- View student information
- Track attendance
- Communicate with teachers and parents
- Access academic resources

If you have any questions, please contact your school administrator.

Best regards,
The OneClass Team
"""
    
    html_body = f"""
<html>
<body>
    <h2>Welcome to {school_name}</h2>
    <p>Dear {user_name},</p>
    
    <p>Welcome to the OneClass Platform for <strong>{school_name}</strong>!</p>
    
    <p>Your account has been successfully created. You can now access the platform to:</p>
    <ul>
        <li>View student information</li>
        <li>Track attendance</li>
        <li>Communicate with teachers and parents</li>
        <li>Access academic resources</li>
    </ul>
    
    <p>If you have any questions, please contact your school administrator.</p>
    
    <p>Best regards,<br>The OneClass Team</p>
</body>
</html>
"""
    
    return await send_email([user_email], subject, body, html_body)

async def send_invitation_email(
    email: str, 
    inviter_name: str, 
    school_name: str, 
    role: str,
    invitation_link: str
) -> bool:
    """Send invitation email"""
    subject = f"Invitation to join {school_name} on OneClass Platform"
    body = f"""
Dear Colleague,

{inviter_name} has invited you to join {school_name} on the OneClass Platform as a {role}.

Please click the following link to accept the invitation and set up your account:
{invitation_link}

This invitation will expire in 7 days.

Best regards,
The OneClass Team
"""
    
    return await send_email([email], subject, body)

async def send_password_reset_email(email: str, reset_link: str) -> bool:
    """Send password reset email"""
    subject = "Reset your OneClass Platform password"
    body = f"""
Hello,

You have requested to reset your password for the OneClass Platform.

Please click the following link to reset your password:
{reset_link}

This link will expire in 1 hour.

If you did not request this password reset, please ignore this email.

Best regards,
The OneClass Team
"""
    
    return await send_email([email], subject, body)
