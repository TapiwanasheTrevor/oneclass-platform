# =====================================================
# Email Service for Invitations
# Handles sending invitation emails with templates
# File: backend/services/invitations/email_service.py
# =====================================================

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails with templates"""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@oneclass.ac.zw")
        self.from_name = os.getenv("FROM_NAME", "OneClass Platform")
        
    async def send_invitation_email(self, email_data: Dict[str, Any]) -> bool:
        """Send invitation email using template"""
        
        try:
            # Generate email content
            subject = self.generate_invitation_subject(email_data)
            html_content = self.generate_invitation_html(email_data)
            text_content = self.generate_invitation_text(email_data)
            
            # Send email
            success = await self.send_email(
                to_email=email_data["recipient_email"],
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                logger.info(f"Successfully sent invitation email to {email_data['recipient_email']}")
            else:
                logger.error(f"Failed to send invitation email to {email_data['recipient_email']}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending invitation email: {str(e)}")
            return False
    
    def generate_invitation_subject(self, data: Dict[str, Any]) -> str:
        """Generate email subject for invitation"""
        
        if data["invitation_type"] == "existing_user":
            return f"You're invited to join {data['school_name']} on OneClass"
        else:
            return f"Welcome to {data['school_name']} - Complete your OneClass setup"
    
    def generate_invitation_html(self, data: Dict[str, Any]) -> str:
        """Generate HTML email content for invitation"""
        
        # Base HTML template
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Invitation to {data['school_name']}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .content {{
            background: #ffffff;
            padding: 30px;
            border: 1px solid #e1e5e9;
            border-top: none;
        }}
        .school-info {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .role-badge {{
            background: #4f46e5;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
        }}
        .cta-button {{
            display: inline-block;
            background: #4f46e5;
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 500;
            margin: 20px 0;
        }}
        .cta-button:hover {{
            background: #4338ca;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 14px;
            color: #6b7280;
            border-radius: 0 0 10px 10px;
            border: 1px solid #e1e5e9;
            border-top: none;
        }}
        .personal-message {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }}
        .features {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 20px 0;
        }}
        .feature {{
            text-align: center;
            padding: 15px;
            background: #f3f4f6;
            border-radius: 8px;
        }}
        .feature-icon {{
            font-size: 24px;
            margin-bottom: 8px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎓 You're Invited!</h1>
        <p>Join {data['school_name']} on OneClass Platform</p>
    </div>
    
    <div class="content">
        <h2>Hello {data['recipient_name']}!</h2>
        
        <p>
            <strong>{data['inviter_name']}</strong> ({data['inviter_role']}) has invited you to join 
            <strong>{data['school_name']}</strong> on the OneClass platform.
        </p>
        
        <div class="school-info">
            <h3>🏫 {data['school_name']}</h3>
            <p><strong>Your Role:</strong> <span class="role-badge">{data['invited_role']}</span></p>
            <p><strong>What you'll do:</strong> {data['role_description']}</p>
        </div>
        
        {f'''
        <div class="personal-message">
            <h4>💬 Personal Message</h4>
            <p>{data['personal_message']}</p>
        </div>
        ''' if data.get('personal_message') else ''}
        
        <div class="features">
            <div class="feature">
                <div class="feature-icon">📱</div>
                <h4>Mobile Ready</h4>
                <p>Access on any device</p>
            </div>
            <div class="feature">
                <div class="feature-icon">🔒</div>
                <h4>Secure</h4>
                <p>Your data is protected</p>
            </div>
            <div class="feature">
                <div class="feature-icon">⚡</div>
                <h4>Fast</h4>
                <p>Lightning-fast performance</p>
            </div>
            <div class="feature">
                <div class="feature-icon">🇿🇼</div>
                <h4>Made for Zimbabwe</h4>
                <p>Built for local schools</p>
            </div>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{data['invitation_url']}" class="cta-button">
                {'Accept Invitation' if data['invitation_type'] == 'existing_user' else 'Complete Setup'}
            </a>
        </div>
        
        <div style="background: #fef2f2; border: 1px solid #fecaca; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 0; color: #dc2626;">
                <strong>⏰ Important:</strong> This invitation expires on {data['expires_at']}. 
                Please accept it before then.
            </p>
        </div>
        
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
        
        <h3>What happens next?</h3>
        <ol>
            <li>Click the invitation link above</li>
            <li>{'Add this school to your existing account' if data['invitation_type'] == 'existing_user' else 'Complete your profile setup'}</li>
            <li>Start using OneClass immediately</li>
            <li>Download the mobile app for on-the-go access</li>
        </ol>
        
        <p>
            If you have any questions, please contact <strong>{data['inviter_name']}</strong> or 
            our support team at <a href="mailto:support@{data['school_subdomain']}.oneclass.ac.zw">
            support@{data['school_subdomain']}.oneclass.ac.zw</a>
        </p>
    </div>
    
    <div class="footer">
        <p>
            <strong>OneClass Platform</strong> - Zimbabwe's Premier School Management System<br>
            <a href="https://oneclass.ac.zw">oneclass.ac.zw</a> | 
            <a href="mailto:support@oneclass.ac.zw">support@oneclass.ac.zw</a>
        </p>
        <p style="font-size: 12px; margin-top: 15px;">
            This invitation was sent to {data['recipient_email']} by {data['school_name']}.<br>
            If you didn't expect this email, you can safely ignore it.
        </p>
    </div>
</body>
</html>
        """
        
        return html_template
    
    def generate_invitation_text(self, data: Dict[str, Any]) -> str:
        """Generate plain text email content for invitation"""
        
        text_content = f"""
OneClass Platform - Invitation to {data['school_name']}

Hello {data['recipient_name']}!

{data['inviter_name']} ({data['inviter_role']}) has invited you to join {data['school_name']} on the OneClass platform.

Your Role: {data['invited_role']}
What you'll do: {data['role_description']}

{'Personal Message: ' + data['personal_message'] if data.get('personal_message') else ''}

To accept this invitation, please visit:
{data['invitation_url']}

IMPORTANT: This invitation expires on {data['expires_at']}. Please accept it before then.

What happens next?
1. Click the invitation link above
2. {'Add this school to your existing account' if data['invitation_type'] == 'existing_user' else 'Complete your profile setup'}
3. Start using OneClass immediately
4. Download the mobile app for on-the-go access

OneClass Features:
- Mobile-ready access on any device
- Secure data protection
- Lightning-fast performance
- Built specifically for Zimbabwe schools

If you have any questions, please contact {data['inviter_name']} or our support team at support@{data['school_subdomain']}.oneclass.ac.zw

---
OneClass Platform - Zimbabwe's Premier School Management System
https://oneclass.ac.zw | support@oneclass.ac.zw

This invitation was sent to {data['recipient_email']} by {data['school_name']}.
If you didn't expect this email, you can safely ignore it.
        """
        
        return text_content.strip()
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        attachments: Optional[list] = None
    ) -> bool:
        """Send email via SMTP"""
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    with open(attachment['path'], 'rb') as file:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(file.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {attachment["filename"]}'
                        )
                        msg.attach(part)
            
            # Send email
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured - email not sent")
                # In development, just log the email
                logger.info(f"EMAIL TO: {to_email}")
                logger.info(f"EMAIL SUBJECT: {subject}")
                logger.info(f"EMAIL CONTENT: {text_content[:200]}...")
                return True
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False
    
    async def send_welcome_email(self, user_data: Dict[str, Any]) -> bool:
        """Send welcome email to new user"""
        
        try:
            subject = f"Welcome to {user_data['school_name']} on OneClass!"
            
            html_content = self.generate_welcome_html(user_data)
            text_content = self.generate_welcome_text(user_data)
            
            return await self.send_email(
                to_email=user_data["email"],
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error sending welcome email: {str(e)}")
            return False
    
    def generate_welcome_html(self, data: Dict[str, Any]) -> str:
        """Generate welcome email HTML"""
        # Similar to invitation template but for successful signup
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Welcome to OneClass!</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: #4f46e5; color: white; padding: 20px; text-align: center;">
        <h1>🎉 Welcome to OneClass!</h1>
    </div>
    <div style="padding: 20px;">
        <h2>Hello {data['first_name']}!</h2>
        <p>Your OneClass account has been successfully created for <strong>{data['school_name']}</strong>.</p>
        <p>You can now access your dashboard at: <a href="https://{data['school_subdomain']}.oneclass.ac.zw">
        {data['school_subdomain']}.oneclass.ac.zw</a></p>
        <p>Download our mobile app to stay connected on the go!</p>
        <hr>
        <p style="color: #666; font-size: 14px;">
            OneClass Platform - support@oneclass.ac.zw
        </p>
    </div>
</body>
</html>
        """
    
    def generate_welcome_text(self, data: Dict[str, Any]) -> str:
        """Generate welcome email text"""
        return f"""
Welcome to OneClass!

Hello {data['first_name']}!

Your OneClass account has been successfully created for {data['school_name']}.

You can now access your dashboard at: https://{data['school_subdomain']}.oneclass.ac.zw

Download our mobile app to stay connected on the go!

OneClass Platform - support@oneclass.ac.zw
        """