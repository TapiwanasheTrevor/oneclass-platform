"""
Email Service for OneClass Platform
Handles all email communications using SendGrid
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition

logger = logging.getLogger(__name__)

class EmailService:
    """SendGrid-powered email service for the OneClass platform"""
    
    def __init__(self):
        self.api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@oneclass.ac.zw')
        self.from_name = os.getenv('SENDGRID_FROM_NAME', 'OneClass Platform')
        
        if not self.api_key:
            logger.warning("SendGrid API key not configured - emails will be logged only")
            self.sg = None
        else:
            self.sg = SendGridAPIClient(api_key=self.api_key)
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Send email via SendGrid"""
        
        try:
            # Log email for development/testing
            logger.info(f"Sending email to {to_email}: {subject}")
            
            if not self.sg:
                logger.warning(f"Email not sent (no API key): {subject} to {to_email}")
                return False
            
            # Create email
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            if text_content:
                message.content = [
                    Content("text/plain", text_content),
                    Content("text/html", html_content)
                ]
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    file_attachment = Attachment(
                        file_content=FileContent(attachment['content']),
                        file_name=FileName(attachment['filename']),
                        file_type=FileType(attachment.get('type', 'application/pdf')),
                        disposition=Disposition('attachment')
                    )
                    message.attachment = file_attachment
            
            # Send email
            response = self.sg.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email to {to_email}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False
    
    # =====================================================
    # SCHOOL ONBOARDING EMAILS
    # =====================================================
    
    async def send_verification_email(self, school_name: str, principal_email: str, verification_token: str, school_id: str) -> bool:
        """Send email verification for school registration"""
        
        verification_url = f"{os.getenv('FRONTEND_URL', 'https://oneclass.ac.zw')}/onboarding/verify-email/{school_id}?token={verification_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your School Registration - OneClass</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #2563eb; margin-bottom: 10px;">🎓 OneClass Platform</h1>
                <h2 style="color: #64748b; font-weight: normal;">Verify Your School Registration</h2>
            </div>
            
            <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <p>Dear Principal,</p>
                
                <p>Thank you for registering <strong>{school_name}</strong> with OneClass Platform. To complete your registration, please verify your email address by clicking the button below:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">
                        Verify Email Address
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #64748b;">
                    If the button doesn't work, copy and paste this link into your browser:<br>
                    <a href="{verification_url}" style="color: #2563eb; word-break: break-all;">{verification_url}</a>
                </p>
                
                <p style="font-size: 14px; color: #64748b;">
                    This verification link will expire in 7 days.
                </p>
            </div>
            
            <div style="border-top: 1px solid #e2e8f0; padding-top: 20px; font-size: 12px; color: #64748b;">
                <p>Need help? Contact our support team at <a href="mailto:support@oneclass.ac.zw" style="color: #2563eb;">support@oneclass.ac.zw</a></p>
                <p>&copy; 2024 OneClass Platform. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        OneClass Platform - Verify Your School Registration
        
        Dear Principal,
        
        Thank you for registering {school_name} with OneClass Platform. To complete your registration, please verify your email address by visiting:
        
        {verification_url}
        
        This verification link will expire in 7 days.
        
        Need help? Contact our support team at support@oneclass.ac.zw
        
        © 2024 OneClass Platform. All rights reserved.
        """
        
        return await self.send_email(
            to_email=principal_email,
            subject=f"Verify your OneClass registration for {school_name}",
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_document_approval_email(self, school_name: str, principal_email: str, setup_token: str, school_id: str) -> bool:
        """Send document approval and subscription setup email"""
        
        setup_url = f"{os.getenv('FRONTEND_URL', 'https://oneclass.ac.zw')}/onboarding/subscription-setup/{school_id}?token={setup_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Documents Approved - Set Up Subscription - OneClass</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #2563eb; margin-bottom: 10px;">🎓 OneClass Platform</h1>
                <h2 style="color: #16a34a; font-weight: normal;">✅ Documents Approved!</h2>
            </div>
            
            <div style="background: #f0fdf4; border: 1px solid #16a34a; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <p>Congratulations! Your school documents for <strong>{school_name}</strong> have been reviewed and approved by our team.</p>
                
                <p><strong>Next Step:</strong> Set up your subscription and payment method to activate your school account.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{setup_url}" 
                       style="background: #16a34a; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">
                        Set Up Subscription
                    </a>
                </div>
            </div>
            
            <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="color: #2563eb; margin-top: 0;">What's Next?</h3>
                <ul style="padding-left: 20px;">
                    <li>Choose your subscription plan</li>
                    <li>Set up payment method (EcoCash, Paynow, or Bank Transfer)</li>
                    <li>Create your principal administrator account</li>
                    <li>Configure your school settings</li>
                    <li>Start your 30-day free trial</li>
                </ul>
            </div>
            
            <p style="font-size: 14px; color: #64748b;">
                If the button doesn't work, copy and paste this link into your browser:<br>
                <a href="{setup_url}" style="color: #2563eb; word-break: break-all;">{setup_url}</a>
            </p>
            
            <div style="border-top: 1px solid #e2e8f0; padding-top: 20px; font-size: 12px; color: #64748b;">
                <p>Questions? Contact our support team at <a href="mailto:support@oneclass.ac.zw" style="color: #2563eb;">support@oneclass.ac.zw</a></p>
                <p>&copy; 2024 OneClass Platform. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(
            to_email=principal_email,
            subject=f"Documents Approved - Set Up Your OneClass Subscription for {school_name}",
            html_content=html_content
        )
    
    async def send_admin_setup_email(self, school_name: str, principal_email: str, setup_data: Dict[str, Any]) -> bool:
        """Send admin account setup instructions"""
        
        setup_url = setup_data["setup_url"]
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Create Your Administrator Account - OneClass</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #2563eb; margin-bottom: 10px;">🎓 OneClass Platform</h1>
                <h2 style="color: #7c3aed; font-weight: normal;">Create Your Administrator Account</h2>
            </div>
            
            <div style="background: #faf5ff; border: 1px solid #7c3aed; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <p>Your OneClass subscription for <strong>{school_name}</strong> is now active! It's time to create your administrator account and start using the platform.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{setup_url}" 
                       style="background: #7c3aed; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">
                        Create Administrator Account
                    </a>
                </div>
            </div>
            
            <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="color: #2563eb; margin-top: 0;">Your Account Setup Includes:</h3>
                <ul style="padding-left: 20px;">
                    <li><strong>Principal Account:</strong> Full administrative privileges</li>
                    <li><strong>School Admin Account:</strong> Same privileges as principal (backup admin)</li>
                    <li><strong>Module Configuration:</strong> Enable features for your school</li>
                    <li><strong>School Branding:</strong> Upload logo and customize colors</li>
                    <li><strong>Academic Calendar:</strong> Set up terms and holidays</li>
                </ul>
                
                <div style="background: #dbeafe; padding: 15px; border-radius: 6px; margin-top: 15px;">
                    <p style="margin: 0; font-weight: bold; color: #1d4ed8;">💡 Pro Tip:</p>
                    <p style="margin: 5px 0 0 0; font-size: 14px;">Both Principal and Admin accounts have identical privileges for backup access. You can create multiple admin accounts later.</p>
                </div>
            </div>
            
            <p style="font-size: 14px; color: #64748b;">
                This setup link will expire in 7 days. If you need a new link, contact our support team.
            </p>
            
            <div style="border-top: 1px solid #e2e8f0; padding-top: 20px; font-size: 12px; color: #64748b;">
                <p>Need assistance? Contact our support team at <a href="mailto:support@oneclass.ac.zw" style="color: #2563eb;">support@oneclass.ac.zw</a></p>
                <p>&copy; 2024 OneClass Platform. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(
            to_email=principal_email,
            subject=f"Create Your Administrator Account - {school_name} | OneClass",
            html_content=html_content
        )
    
    async def send_welcome_email(self, school_name: str, principal_email: str, school_subdomain: str, pricing_info: Dict[str, Any]) -> bool:
        """Send welcome email after onboarding completion"""
        
        school_url = f"https://{school_subdomain}.oneclass.ac.zw"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to OneClass - Your School is Live! 🎉</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #2563eb; margin-bottom: 10px;">🎓 OneClass Platform</h1>
                <h2 style="color: #16a34a; font-weight: normal;">🎉 Welcome to OneClass!</h2>
            </div>
            
            <div style="background: #f0fdf4; border: 1px solid #16a34a; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <p style="font-size: 18px; font-weight: bold; color: #16a34a; margin-top: 0;">Congratulations! {school_name} is now live on OneClass!</p>
                
                <p>Your school management platform is ready to use. You can now access your dedicated portal at:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{school_url}" 
                       style="background: #16a34a; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold; font-size: 16px;">
                        Access Your School Portal
                    </a>
                </div>
                
                <p style="text-align: center; font-size: 14px; color: #64748b;">
                    <strong>Your School URL:</strong> <a href="{school_url}" style="color: #2563eb;">{school_url}</a>
                </p>
            </div>
            
            <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="color: #2563eb; margin-top: 0;">Your Subscription Details</h3>
                <ul style="list-style: none; padding: 0;">
                    <li style="padding: 8px 0; border-bottom: 1px solid #e2e8f0;"><strong>Plan:</strong> {pricing_info.get('tier', 'Professional').title()}</li>
                    <li style="padding: 8px 0; border-bottom: 1px solid #e2e8f0;"><strong>Students:</strong> {pricing_info.get('student_count', 0)}</li>
                    <li style="padding: 8px 0; border-bottom: 1px solid #e2e8f0;"><strong>Per Student:</strong> ${pricing_info.get('price_per_student_monthly', 5.50)}/month</li>
                    <li style="padding: 8px 0; border-bottom: 1px solid #e2e8f0;"><strong>Monthly Total:</strong> ${pricing_info.get('monthly_total', 0):,.2f}</li>
                    <li style="padding: 8px 0;"><strong>Trial Period:</strong> 30 days (no charge)</li>
                </ul>
            </div>
            
            <div style="background: #eff6ff; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="color: #2563eb; margin-top: 0;">Quick Start Guide</h3>
                <ol style="padding-left: 20px;">
                    <li>Log in to your school portal</li>
                    <li>Complete your school profile setup</li>
                    <li>Add your teaching staff and create their accounts</li>
                    <li>Import or add your student data</li>
                    <li>Set up your academic calendar and class structures</li>
                    <li>Invite parents to the parent portal</li>
                    <li>Explore the modules and features available in your plan</li>
                </ol>
                
                <p style="margin-bottom: 0;"><strong>Need help getting started?</strong> Our support team is ready to assist you with onboarding and training.</p>
            </div>
            
            <div style="background: #fef3c7; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                <p style="margin: 0; font-weight: bold; color: #92400e;">🔔 Important Reminder:</p>
                <p style="margin: 5px 0 0 0; font-size: 14px; color: #92400e;">Your 30-day free trial has started. You'll receive billing reminders before your trial ends.</p>
            </div>
            
            <div style="border-top: 1px solid #e2e8f0; padding-top: 20px; font-size: 12px; color: #64748b;">
                <p><strong>Support Resources:</strong></p>
                <ul style="margin: 0; padding-left: 20px;">
                    <li>Email: <a href="mailto:support@oneclass.ac.zw" style="color: #2563eb;">support@oneclass.ac.zw</a></li>
                    <li>Help Center: <a href="https://help.oneclass.ac.zw" style="color: #2563eb;">help.oneclass.ac.zw</a></li>
                    <li>Training Videos: Available in your admin dashboard</li>
                </ul>
                <p style="margin-top: 15px;">&copy; 2024 OneClass Platform. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(
            to_email=principal_email,
            subject=f"🎉 {school_name} is now live on OneClass!",
            html_content=html_content
        )
    
    async def send_document_rejection_email(self, school_name: str, principal_email: str, rejection_reason: str) -> bool:
        """Send document rejection email"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Document Review Update - OneClass</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #2563eb; margin-bottom: 10px;">🎓 OneClass Platform</h1>
                <h2 style="color: #dc2626; font-weight: normal;">Document Review Update</h2>
            </div>
            
            <div style="background: #fef2f2; border: 1px solid #dc2626; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <p>Dear Principal,</p>
                
                <p>We have completed the review of your registration documents for <strong>{school_name}</strong>. Unfortunately, we need additional information before we can approve your application.</p>
                
                <div style="background: white; padding: 15px; border-radius: 6px; margin: 15px 0;">
                    <h4 style="margin-top: 0; color: #dc2626;">Review Notes:</h4>
                    <p style="margin-bottom: 0;">{rejection_reason}</p>
                </div>
                
                <p><strong>Next Steps:</strong></p>
                <ul>
                    <li>Review the feedback above</li>
                    <li>Prepare the requested documents or information</li>
                    <li>Upload updated documents to your onboarding portal</li>
                    <li>Contact our support team if you need clarification</li>
                </ul>
            </div>
            
            <div style="border-top: 1px solid #e2e8f0; padding-top: 20px; font-size: 12px; color: #64748b;">
                <p>Need assistance? Contact our support team at <a href="mailto:support@oneclass.ac.zw" style="color: #2563eb;">support@oneclass.ac.zw</a></p>
                <p>&copy; 2024 OneClass Platform. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(
            to_email=principal_email,
            subject=f"Document Review Update - Additional Information Required for {school_name}",
            html_content=html_content
        )


# Singleton instance
email_service = EmailService()