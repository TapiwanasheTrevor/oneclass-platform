# =====================================================
# Email Template Service
# Manage email templates with Zimbabwe-specific designs
# File: backend/services/notifications/templates.py
# =====================================================

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
import logging

logger = logging.getLogger(__name__)

class EmailTemplateService:
    """Service for managing email templates"""
    
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Create template directory if it doesn't exist
        os.makedirs(self.template_dir, exist_ok=True)
        
        # Initialize built-in templates
        self._create_builtin_templates()
    
    def _create_builtin_templates(self):
        """Create built-in email templates for OneClass"""
        
        templates = {
            'welcome': {
                'name': 'welcome',
                'display_name': 'Welcome Email',
                'description': 'Welcome new users to OneClass platform',
                'subject_template': 'Welcome to {{school_name}} on OneClass! 🎓',
                'html_template': self._get_welcome_template(),
                'text_template': self._get_welcome_text_template(),
                'required_variables': ['first_name', 'school_name', 'login_url'],
                'optional_variables': ['school_logo_url', 'support_email', 'mobile_app_link']
            },
            'invitation': {
                'name': 'invitation',
                'display_name': 'School Invitation',
                'description': 'Invite users to join a school',
                'subject_template': 'You\'re invited to join {{school_name}} on OneClass',
                'html_template': self._get_invitation_template(),
                'text_template': self._get_invitation_text_template(),
                'required_variables': ['recipient_name', 'school_name', 'inviter_name', 'invitation_url'],
                'optional_variables': ['role', 'personal_message', 'school_logo_url']
            },
            'password_reset': {
                'name': 'password_reset',
                'display_name': 'Password Reset',
                'description': 'Password reset instructions',
                'subject_template': 'Reset your OneClass password',
                'html_template': self._get_password_reset_template(),
                'text_template': self._get_password_reset_text_template(),
                'required_variables': ['first_name', 'reset_url'],
                'optional_variables': ['school_name']
            },
            'bulk_import_complete': {
                'name': 'bulk_import_complete',
                'display_name': 'Bulk Import Complete',
                'description': 'Notification when bulk import is completed',
                'subject_template': 'Bulk import completed for {{school_name}}',
                'html_template': self._get_bulk_import_template(),
                'text_template': self._get_bulk_import_text_template(),
                'required_variables': ['admin_name', 'school_name', 'total_users', 'successful_imports'],
                'optional_variables': ['failed_imports', 'import_summary_url']
            },
            'system_alert': {
                'name': 'system_alert',
                'display_name': 'System Alert',
                'description': 'System maintenance and alert notifications',
                'subject_template': '{{alert_type}}: {{alert_title}}',
                'html_template': self._get_system_alert_template(),
                'text_template': self._get_system_alert_text_template(),
                'required_variables': ['alert_type', 'alert_title', 'alert_message'],
                'optional_variables': ['action_required', 'action_url', 'estimated_resolution']
            }
        }
        
        # Store templates (in production, save to database)
        self.builtin_templates = templates
    
    def _get_welcome_template(self) -> str:
        """Get welcome email HTML template"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to OneClass</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }
        .content {
            padding: 40px 30px;
        }
        .school-info {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
        }
        .cta-button {
            display: inline-block;
            background: #4f46e5;
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 500;
            margin: 20px 0;
            text-align: center;
        }
        .features {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 30px 0;
        }
        .feature {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 14px;
            color: #6b7280;
        }
        .zimbabwe-flag {
            color: #006400;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            {% if school_logo_url %}
                <img src="{{school_logo_url}}" alt="{{school_name}}" style="max-height: 60px; margin-bottom: 20px;">
            {% endif %}
            <h1>🎓 Welcome to OneClass!</h1>
            <p>Zimbabwe's Premier School Management Platform</p>
        </div>
        
        <div class="content">
            <h2>Hello {{first_name}}! 👋</h2>
            
            <p>Welcome to <strong>{{school_name}}</strong> on the OneClass platform! We're excited to have you join our growing community of educators, students, and parents across Zimbabwe.</p>
            
            <div class="school-info">
                <h3>🏫 {{school_name}}</h3>
                <p>Your educational journey with us starts here!</p>
            </div>
            
            <div style="text-align: center;">
                <a href="{{login_url}}" class="cta-button">
                    Access Your Dashboard
                </a>
            </div>
            
            <div class="features">
                <div class="feature">
                    <div style="font-size: 24px; margin-bottom: 10px;">📱</div>
                    <h4>Mobile Ready</h4>
                    <p>Access anywhere, anytime on any device</p>
                </div>
                <div class="feature">
                    <div style="font-size: 24px; margin-bottom: 10px;">🇿🇼</div>
                    <h4>Made for Zimbabwe</h4>
                    <p>Built specifically for our local education system</p>
                </div>
                <div class="feature">
                    <div style="font-size: 24px; margin-bottom: 10px;">⚡</div>
                    <h4>Lightning Fast</h4>
                    <p>Optimized for speed and reliability</p>
                </div>
                <div class="feature">
                    <div style="font-size: 24px; margin-bottom: 10px;">🔒</div>
                    <h4>Secure</h4>
                    <p>Your data is protected and private</p>
                </div>
            </div>
            
            <h3>What's Next?</h3>
            <ol>
                <li>Click the button above to access your dashboard</li>
                <li>Complete your profile setup</li>
                <li>Explore the platform features</li>
                <li>{% if mobile_app_link %}Download our mobile app for on-the-go access{% else %}Bookmark your school's dashboard{% endif %}</li>
            </ol>
            
            <p>If you have any questions or need assistance, don't hesitate to reach out to our support team at 
            <a href="mailto:{{support_email|default('support@oneclass.ac.zw')}}">{{support_email|default('support@oneclass.ac.zw')}}</a>.</p>
            
            <p>Welcome aboard! 🚀</p>
            
            <p>
                <strong>The OneClass Team</strong><br>
                <span class="zimbabwe-flag">🇿🇼 Proudly Zimbabwean</span>
            </p>
        </div>
        
        <div class="footer">
            <p>
                <strong>OneClass Platform</strong> - Zimbabwe's Premier School Management System<br>
                <a href="https://oneclass.ac.zw">oneclass.ac.zw</a>
            </p>
            <p style="font-size: 12px; margin-top: 15px;">
                This email was sent to you because you have an account with {{school_name}}.<br>
                If you didn't create this account, please contact us immediately.
            </p>
        </div>
    </div>
</body>
</html>
        """
    
    def _get_welcome_text_template(self) -> str:
        """Get welcome email text template"""
        return """
Welcome to OneClass - {{school_name}}!

Hello {{first_name}}!

Welcome to {{school_name}} on the OneClass platform! We're excited to have you join our growing community of educators, students, and parents across Zimbabwe.

Your educational journey with us starts here!

Access your dashboard: {{login_url}}

OneClass Features:
📱 Mobile Ready - Access anywhere, anytime on any device
🇿🇼 Made for Zimbabwe - Built specifically for our local education system  
⚡ Lightning Fast - Optimized for speed and reliability
🔒 Secure - Your data is protected and private

What's Next?
1. Visit your dashboard using the link above
2. Complete your profile setup
3. Explore the platform features
4. {% if mobile_app_link %}Download our mobile app for on-the-go access{% else %}Bookmark your school's dashboard{% endif %}

If you have any questions or need assistance, contact our support team at {{support_email|default('support@oneclass.ac.zw')}}.

Welcome aboard!

The OneClass Team
🇿🇼 Proudly Zimbabwean

OneClass Platform - Zimbabwe's Premier School Management System
https://oneclass.ac.zw
        """
    
    def _get_invitation_template(self) -> str:
        """Get invitation email HTML template"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Invitation to {{school_name}}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }
        .content {
            padding: 40px 30px;
        }
        .invitation-details {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .role-badge {
            background: #4f46e5;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
        }
        .cta-button {
            display: inline-block;
            background: #4f46e5;
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 500;
            margin: 20px 0;
        }
        .personal-message {
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }
        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 14px;
            color: #6b7280;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            {% if school_logo_url %}
                <img src="{{school_logo_url}}" alt="{{school_name}}" style="max-height: 60px; margin-bottom: 20px;">
            {% endif %}
            <h1>🎓 You're Invited!</h1>
            <p>Join {{school_name}} on OneClass Platform</p>
        </div>
        
        <div class="content">
            <h2>Hello {{recipient_name}}!</h2>
            
            <p><strong>{{inviter_name}}</strong> has invited you to join <strong>{{school_name}}</strong> on the OneClass platform.</p>
            
            <div class="invitation-details">
                <h3>🏫 {{school_name}}</h3>
                {% if role %}
                <p><strong>Your Role:</strong> <span class="role-badge">{{role}}</span></p>
                {% endif %}
                <p>Join Zimbabwe's premier school management platform designed specifically for our education system.</p>
            </div>
            
            {% if personal_message %}
            <div class="personal-message">
                <h4>💬 Personal Message from {{inviter_name}}</h4>
                <p>{{personal_message}}</p>
            </div>
            {% endif %}
            
            <div style="text-align: center;">
                <a href="{{invitation_url}}" class="cta-button">
                    Accept Invitation
                </a>
            </div>
            
            <h3>What happens next?</h3>
            <ol>
                <li>Click the invitation link above</li>
                <li>Complete your profile setup</li>
                <li>Start using OneClass immediately</li>
                <li>Download the mobile app for on-the-go access</li>
            </ol>
            
            <p>If you have any questions, please contact <strong>{{inviter_name}}</strong> or our support team.</p>
        </div>
        
        <div class="footer">
            <p>
                <strong>OneClass Platform</strong> - Zimbabwe's Premier School Management System<br>
                <a href="https://oneclass.ac.zw">oneclass.ac.zw</a>
            </p>
        </div>
    </div>
</body>
</html>
        """
    
    def _get_invitation_text_template(self) -> str:
        """Get invitation email text template"""
        return """
OneClass Platform - Invitation to {{school_name}}

Hello {{recipient_name}}!

{{inviter_name}} has invited you to join {{school_name}} on the OneClass platform.

{% if role %}Your Role: {{role}}{% endif %}

{% if personal_message %}
Personal Message from {{inviter_name}}:
{{personal_message}}
{% endif %}

To accept this invitation, please visit:
{{invitation_url}}

What happens next?
1. Click the invitation link above
2. Complete your profile setup  
3. Start using OneClass immediately
4. Download the mobile app for on-the-go access

OneClass Features:
- Mobile-ready access on any device
- Secure data protection
- Lightning-fast performance  
- Built specifically for Zimbabwe schools

If you have any questions, please contact {{inviter_name}} or our support team.

OneClass Platform - Zimbabwe's Premier School Management System
https://oneclass.ac.zw
        """
    
    def _get_password_reset_template(self) -> str:
        """Get password reset HTML template"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your OneClass Password</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }
        .content {
            padding: 40px 30px;
        }
        .cta-button {
            display: inline-block;
            background: #4f46e5;
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 500;
            margin: 20px 0;
        }
        .security-notice {
            background: #fef2f2;
            border: 1px solid #fecaca;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 14px;
            color: #6b7280;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Password Reset</h1>
            <p>Reset your OneClass password securely</p>
        </div>
        
        <div class="content">
            <h2>Hello {{first_name}}!</h2>
            
            <p>We received a request to reset your OneClass password{% if school_name %} for {{school_name}}{% endif %}.</p>
            
            <div style="text-align: center;">
                <a href="{{reset_url}}" class="cta-button">
                    Reset Your Password
                </a>
            </div>
            
            <div class="security-notice">
                <p style="margin: 0; color: #dc2626;">
                    <strong>⏰ Important:</strong> This password reset link expires in 30 minutes for your security.
                </p>
            </div>
            
            <p><strong>If you didn't request this password reset:</strong></p>
            <ul>
                <li>You can safely ignore this email</li>
                <li>Your password will remain unchanged</li>
                <li>Consider changing your password if you suspect unauthorized access</li>
            </ul>
            
            <p>For additional security, we recommend:</p>
            <ul>
                <li>Using a strong, unique password</li>
                <li>Enabling two-factor authentication if available</li>
                <li>Not sharing your login credentials</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>
                <strong>OneClass Platform</strong> - Zimbabwe's Premier School Management System<br>
                <a href="https://oneclass.ac.zw">oneclass.ac.zw</a>
            </p>
        </div>
    </div>
</body>
</html>
        """
    
    def _get_password_reset_text_template(self) -> str:
        """Get password reset text template"""
        return """
OneClass Platform - Password Reset

Hello {{first_name}}!

We received a request to reset your OneClass password{% if school_name %} for {{school_name}}{% endif %}.

Reset your password: {{reset_url}}

IMPORTANT: This password reset link expires in 30 minutes for your security.

If you didn't request this password reset:
- You can safely ignore this email
- Your password will remain unchanged  
- Consider changing your password if you suspect unauthorized access

For additional security, we recommend:
- Using a strong, unique password
- Enabling two-factor authentication if available
- Not sharing your login credentials

OneClass Platform - Zimbabwe's Premier School Management System
https://oneclass.ac.zw
        """
    
    def _get_bulk_import_template(self) -> str:
        """Get bulk import completion template"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bulk Import Complete</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }
        .content {
            padding: 40px 30px;
        }
        .stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 20px 0;
        }
        .stat {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-number {
            font-size: 28px;
            font-weight: bold;
            color: #4f46e5;
        }
        .cta-button {
            display: inline-block;
            background: #4f46e5;
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 500;
            margin: 20px 0;
        }
        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 14px;
            color: #6b7280;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Import Complete!</h1>
            <p>Your bulk user import has finished processing</p>
        </div>
        
        <div class="content">
            <h2>Hello {{admin_name}}!</h2>
            
            <p>Your bulk user import for <strong>{{school_name}}</strong> has been completed successfully.</p>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-number">{{total_users}}</div>
                    <div>Total Users</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{{successful_imports}}</div>
                    <div>Successfully Imported</div>
                </div>
                {% if failed_imports and failed_imports > 0 %}
                <div class="stat">
                    <div class="stat-number" style="color: #dc2626;">{{failed_imports}}</div>
                    <div>Failed Imports</div>
                </div>
                {% endif %}
            </div>
            
            {% if import_summary_url %}
            <div style="text-align: center;">
                <a href="{{import_summary_url}}" class="cta-button">
                    View Detailed Report
                </a>
            </div>
            {% endif %}
            
            <h3>What's Next?</h3>
            <ul>
                <li>Review the imported users in your dashboard</li>
                <li>Send welcome emails to new users</li>
                <li>Configure user permissions as needed</li>
                {% if failed_imports and failed_imports > 0 %}
                <li>Review and fix any failed imports</li>
                {% endif %}
            </ul>
            
            <p>All imported users will receive welcome emails with their login instructions.</p>
        </div>
        
        <div class="footer">
            <p>
                <strong>OneClass Platform</strong> - Zimbabwe's Premier School Management System<br>
                <a href="https://oneclass.ac.zw">oneclass.ac.zw</a>
            </p>
        </div>
    </div>
</body>
</html>
        """
    
    def _get_bulk_import_text_template(self) -> str:
        """Get bulk import completion text template"""
        return """
OneClass Platform - Bulk Import Complete

Hello {{admin_name}}!

Your bulk user import for {{school_name}} has been completed successfully.

Import Summary:
- Total Users: {{total_users}}
- Successfully Imported: {{successful_imports}}
{% if failed_imports and failed_imports > 0 %}- Failed Imports: {{failed_imports}}{% endif %}

{% if import_summary_url %}View detailed report: {{import_summary_url}}{% endif %}

What's Next?
- Review the imported users in your dashboard
- Send welcome emails to new users  
- Configure user permissions as needed
{% if failed_imports and failed_imports > 0 %}- Review and fix any failed imports{% endif %}

All imported users will receive welcome emails with their login instructions.

OneClass Platform - Zimbabwe's Premier School Management System
https://oneclass.ac.zw
        """
    
    def _get_system_alert_template(self) -> str:
        """Get system alert template"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{alert_type}}: {{alert_title}}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }
        .content {
            padding: 40px 30px;
        }
        .alert-message {
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }
        .cta-button {
            display: inline-block;
            background: #4f46e5;
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 500;
            margin: 20px 0;
        }
        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 14px;
            color: #6b7280;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ {{alert_type}}</h1>
            <p>{{alert_title}}</p>
        </div>
        
        <div class="content">
            <div class="alert-message">
                <p style="margin: 0;">{{alert_message}}</p>
            </div>
            
            {% if action_required %}
            <h3>Action Required</h3>
            <p>{{action_required}}</p>
            
            {% if action_url %}
            <div style="text-align: center;">
                <a href="{{action_url}}" class="cta-button">
                    Take Action
                </a>
            </div>
            {% endif %}
            {% endif %}
            
            {% if estimated_resolution %}
            <p><strong>Estimated Resolution:</strong> {{estimated_resolution}}</p>
            {% endif %}
            
            <p>We appreciate your patience and will keep you updated on any developments.</p>
        </div>
        
        <div class="footer">
            <p>
                <strong>OneClass Platform</strong> - Zimbabwe's Premier School Management System<br>
                <a href="https://oneclass.ac.zw">oneclass.ac.zw</a>
            </p>
        </div>
    </div>
</body>
</html>
        """
    
    def _get_system_alert_text_template(self) -> str:
        """Get system alert text template"""
        return """
OneClass Platform - {{alert_type}}: {{alert_title}}

{{alert_message}}

{% if action_required %}
Action Required:
{{action_required}}

{% if action_url %}Take action: {{action_url}}{% endif %}
{% endif %}

{% if estimated_resolution %}Estimated Resolution: {{estimated_resolution}}{% endif %}

We appreciate your patience and will keep you updated on any developments.

OneClass Platform - Zimbabwe's Premier School Management System
https://oneclass.ac.zw
        """
    
    async def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get template by name"""
        return self.builtin_templates.get(template_name)
    
    async def render_template(
        self,
        template_name: str,
        template_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Render template with data"""
        
        template = await self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Validate required variables
        missing_vars = []
        for var in template['required_variables']:
            if var not in template_data:
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required template variables: {missing_vars}")
        
        try:
            # Render subject
            subject_template = self.jinja_env.from_string(template['subject_template'])
            subject = subject_template.render(**template_data)
            
            # Render HTML content
            html_template = self.jinja_env.from_string(template['html_template'])
            html_content = html_template.render(**template_data)
            
            # Render text content
            text_content = None
            if template.get('text_template'):
                text_template = self.jinja_env.from_string(template['text_template'])
                text_content = text_template.render(**template_data)
            
            return {
                'subject': subject,
                'html_content': html_content,
                'text_content': text_content
            }
            
        except Exception as e:
            logger.error(f"Error rendering template '{template_name}': {str(e)}")
            raise ValueError(f"Template rendering failed: {str(e)}")
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates"""
        return [
            {
                'name': template['name'],
                'display_name': template['display_name'],
                'description': template['description'],
                'required_variables': template['required_variables'],
                'optional_variables': template['optional_variables']
            }
            for template in self.builtin_templates.values()
        ]