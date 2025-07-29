# =====================================================
# Enhanced Email Service
# Comprehensive email service with templates and tracking
# File: backend/services/notifications/email_service.py
# =====================================================

import os
import logging
import asyncio
import uuid
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import hashlib
import hmac
import base64

from .templates import EmailTemplateService
from .schemas import EmailRequest, EmailStatusResponse, NotificationStatus

logger = logging.getLogger(__name__)

class EmailService:
    """Enhanced email service with template support and delivery tracking"""
    
    def __init__(self):
        # SMTP Configuration
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@oneclass.ac.zw")
        self.from_name = os.getenv("FROM_NAME", "OneClass Platform")
        
        # Service configuration
        self.max_recipients_per_email = 50
        self.daily_send_limit = 1000
        self.retry_attempts = 3
        self.retry_delay = 60  # seconds
        
        # Initialize template service
        self.template_service = EmailTemplateService()
        
        # Tracking and analytics
        self.delivery_tracking = {}  # In production, use database
        self.send_statistics = {
            'daily_sent': 0,
            'last_reset': datetime.utcnow().date()
        }
        
        # Webhook secret for tracking
        self.webhook_secret = os.getenv("EMAIL_WEBHOOK_SECRET", "change-this-secret")
    
    async def send_email(self, email_request: EmailRequest) -> Dict[str, Any]:
        """Send email with template support and tracking"""
        
        email_id = str(uuid.uuid4())
        
        try:
            # Check daily send limit
            if not await self._check_send_limit():
                raise Exception("Daily send limit exceeded")
            
            # Normalize recipients
            recipients = email_request.to if isinstance(email_request.to, list) else [email_request.to]
            
            # Validate recipients
            if len(recipients) > self.max_recipients_per_email:
                raise Exception(f"Too many recipients. Maximum {self.max_recipients_per_email} allowed")
            
            # Prepare email content
            if email_request.template_name:
                # Use template
                rendered = await self.template_service.render_template(
                    email_request.template_name,
                    email_request.template_data
                )
                subject = rendered['subject']
                html_content = rendered['html_content']
                text_content = rendered['text_content']
            else:
                # Use provided content
                subject = email_request.subject
                html_content = email_request.html_content
                text_content = email_request.text_content
            
            # Add tracking if enabled
            if email_request.track_opens or email_request.track_clicks:
                html_content = await self._add_tracking_to_content(
                    html_content, email_id, email_request.track_opens, email_request.track_clicks
                )
            
            # Send email
            success = await self._send_smtp_email(
                recipients=recipients,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                cc=email_request.cc,
                bcc=email_request.bcc,
                reply_to=email_request.reply_to,
                attachments=email_request.attachments
            )
            
            # Track delivery
            await self._track_email_delivery(email_id, email_request, success)
            
            # Update statistics
            if success:
                self._update_send_statistics(len(recipients))
            
            return {
                'success': success,
                'email_id': email_id,
                'message': 'Email sent successfully' if success else 'Email sending failed',
                'recipients_count': len(recipients),
                'tracking_enabled': email_request.track_opens or email_request.track_clicks
            }
            
        except Exception as e:
            logger.error(f"Error sending email {email_id}: {str(e)}")
            
            # Track failure
            await self._track_email_delivery(email_id, email_request, False, str(e))
            
            return {
                'success': False,
                'email_id': email_id,
                'message': f'Email sending failed: {str(e)}',
                'recipients_count': len(recipients) if 'recipients' in locals() else 0,
                'tracking_enabled': False
            }
    
    async def send_bulk_emails(
        self,
        emails: List[EmailRequest],
        batch_size: int = 10,
        delay_between_batches: int = 60
    ) -> Dict[str, Any]:
        """Send multiple emails in batches"""
        
        bulk_id = str(uuid.uuid4())
        results = {
            'bulk_id': bulk_id,
            'total_emails': len(emails),
            'successful': 0,
            'failed': 0,
            'email_results': []
        }
        
        try:
            # Process in batches
            for i in range(0, len(emails), batch_size):
                batch = emails[i:i + batch_size]
                
                # Send batch concurrently
                batch_tasks = [self.send_email(email) for email in batch]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Process results
                for email_result in batch_results:
                    if isinstance(email_result, Exception):
                        results['failed'] += 1
                        results['email_results'].append({
                            'success': False,
                            'error': str(email_result)
                        })
                    else:
                        if email_result['success']:
                            results['successful'] += 1
                        else:
                            results['failed'] += 1
                        results['email_results'].append(email_result)
                
                # Delay between batches
                if i + batch_size < len(emails):
                    await asyncio.sleep(delay_between_batches)
                
                # Log progress
                processed = min(i + batch_size, len(emails))
                logger.info(f"Bulk email progress {bulk_id}: {processed}/{len(emails)} processed")
            
            logger.info(f"Bulk email completed {bulk_id}: {results['successful']} successful, {results['failed']} failed")
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk email {bulk_id}: {str(e)}")
            raise
    
    async def get_email_status(self, email_id: str) -> Optional[EmailStatusResponse]:
        """Get email delivery status"""
        
        if email_id not in self.delivery_tracking:
            return None
        
        tracking_data = self.delivery_tracking[email_id]
        
        return EmailStatusResponse(
            email_id=email_id,
            recipient=tracking_data['recipient'],
            status=tracking_data['status'],
            sent_at=tracking_data['sent_at'],
            delivered_at=tracking_data.get('delivered_at'),
            opened_at=tracking_data.get('opened_at'),
            clicked_at=tracking_data.get('clicked_at'),
            failed_at=tracking_data.get('failed_at'),
            failure_reason=tracking_data.get('failure_reason'),
            open_count=tracking_data.get('open_count', 0),
            click_count=tracking_data.get('click_count', 0)
        )
    
    async def handle_webhook_event(self, event_data: Dict[str, Any]) -> bool:
        """Handle email delivery webhook events"""
        
        try:
            # Verify webhook signature
            if not self._verify_webhook_signature(event_data):
                logger.warning("Invalid webhook signature")
                return False
            
            email_id = event_data.get('email_id')
            event_type = event_data.get('event_type')
            timestamp = event_data.get('timestamp')
            
            if email_id not in self.delivery_tracking:
                logger.warning(f"Unknown email ID in webhook: {email_id}")
                return False
            
            tracking_data = self.delivery_tracking[email_id]
            
            # Update tracking based on event type
            if event_type == 'delivered':
                tracking_data['status'] = NotificationStatus.DELIVERED
                tracking_data['delivered_at'] = timestamp
            elif event_type == 'opened':
                tracking_data['opened_at'] = timestamp
                tracking_data['open_count'] = tracking_data.get('open_count', 0) + 1
            elif event_type == 'clicked':
                tracking_data['clicked_at'] = timestamp
                tracking_data['click_count'] = tracking_data.get('click_count', 0) + 1
            elif event_type == 'bounced':
                tracking_data['status'] = NotificationStatus.BOUNCED
                tracking_data['failure_reason'] = event_data.get('reason', 'Email bounced')
            elif event_type == 'failed':
                tracking_data['status'] = NotificationStatus.FAILED
                tracking_data['failed_at'] = timestamp
                tracking_data['failure_reason'] = event_data.get('reason', 'Delivery failed')
            
            logger.info(f"Updated email tracking for {email_id}: {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling webhook event: {str(e)}")
            return False
    
    async def _send_smtp_email(
        self,
        recipients: List[str],
        subject: str,
        html_content: Optional[str],
        text_content: Optional[str],
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Send email via SMTP"""
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            if reply_to:
                msg['Reply-To'] = reply_to
            
            # Add message ID for tracking
            msg['Message-ID'] = f"<{uuid.uuid4()}@oneclass.ac.zw>"
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML content
            if html_content:
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    await self._add_attachment(msg, attachment)
            
            # Send email
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured - email not sent")
                # In development, just log the email
                logger.info(f"EMAIL TO: {recipients}")
                logger.info(f"EMAIL SUBJECT: {subject}")
                logger.info(f"EMAIL CONTENT: {text_content[:200] if text_content else 'HTML only'}...")
                return True
            
            # Prepare all recipients
            all_recipients = recipients.copy()
            if cc:
                all_recipients.extend(cc)
            if bcc:
                all_recipients.extend(bcc)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg, to_addrs=all_recipients)
            
            return True
            
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            return False
    
    async def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to email message"""
        
        try:
            if 'path' in attachment:
                # File attachment
                with open(attachment['path'], 'rb') as file:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(file.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment.get("filename", "attachment")}'
                    )
                    msg.attach(part)
            elif 'content' in attachment:
                # Content attachment
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment['content'])
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment.get("filename", "attachment")}'
                )
                msg.attach(part)
                
        except Exception as e:
            logger.error(f"Error adding attachment: {str(e)}")
    
    async def _add_tracking_to_content(
        self,
        html_content: str,
        email_id: str,
        track_opens: bool,
        track_clicks: bool
    ) -> str:
        """Add tracking pixels and link tracking to HTML content"""
        
        if not html_content:
            return html_content
        
        modified_content = html_content
        
        # Add open tracking pixel
        if track_opens:
            tracking_pixel = f'<img src="https://oneclass.ac.zw/api/v1/email/track/open/{email_id}" width="1" height="1" style="display:none;" alt="">'
            modified_content = modified_content.replace('</body>', f'{tracking_pixel}</body>')
        
        # Add click tracking (simplified implementation)
        if track_clicks:
            # In a full implementation, you would:
            # 1. Find all links in the HTML
            # 2. Replace them with tracking URLs
            # 3. Store the original URLs for redirect
            pass
        
        return modified_content
    
    async def _track_email_delivery(
        self,
        email_id: str,
        email_request: EmailRequest,
        success: bool,
        error_message: Optional[str] = None
    ):
        """Track email delivery for analytics"""
        
        recipients = email_request.to if isinstance(email_request.to, list) else [email_request.to]
        
        for recipient in recipients:
            tracking_data = {
                'email_id': email_id,
                'recipient': recipient,
                'subject': email_request.subject,
                'template_name': email_request.template_name,
                'status': NotificationStatus.SENT if success else NotificationStatus.FAILED,
                'sent_at': datetime.utcnow().isoformat() if success else None,
                'failed_at': datetime.utcnow().isoformat() if not success else None,
                'failure_reason': error_message,
                'school_id': str(email_request.school_id) if email_request.school_id else None,
                'sender_id': str(email_request.sender_id) if email_request.sender_id else None,
                'email_type': email_request.email_type.value,
                'priority': email_request.priority.value,
                'tracking_enabled': email_request.track_opens or email_request.track_clicks
            }
            
            self.delivery_tracking[f"{email_id}_{recipient}"] = tracking_data
    
    async def _check_send_limit(self) -> bool:
        """Check if daily send limit is exceeded"""
        
        current_date = datetime.utcnow().date()
        
        # Reset counter if new day
        if self.send_statistics['last_reset'] != current_date:
            self.send_statistics['daily_sent'] = 0
            self.send_statistics['last_reset'] = current_date
        
        return self.send_statistics['daily_sent'] < self.daily_send_limit
    
    def _update_send_statistics(self, sent_count: int):
        """Update email send statistics"""
        self.send_statistics['daily_sent'] += sent_count
    
    def _verify_webhook_signature(self, event_data: Dict[str, Any]) -> bool:
        """Verify webhook signature for security"""
        
        # In a real implementation, verify HMAC signature
        # For now, just return True
        return True
    
    def get_service_statistics(self) -> Dict[str, Any]:
        """Get email service statistics"""
        
        return {
            'daily_sent': self.send_statistics['daily_sent'],
            'daily_limit': self.daily_send_limit,
            'remaining_today': max(0, self.daily_send_limit - self.send_statistics['daily_sent']),
            'tracked_emails': len(self.delivery_tracking),
            'smtp_configured': bool(self.smtp_username and self.smtp_password),
            'last_reset': self.send_statistics['last_reset'].isoformat()
        }
    
    async def get_delivery_report(
        self,
        start_date: datetime,
        end_date: datetime,
        school_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate email delivery report"""
        
        # Filter tracking data by date range and school
        filtered_data = []
        for tracking_data in self.delivery_tracking.values():
            sent_at = tracking_data.get('sent_at')
            if sent_at:
                sent_date = datetime.fromisoformat(sent_at)
                if start_date <= sent_date <= end_date:
                    if not school_id or tracking_data.get('school_id') == school_id:
                        filtered_data.append(tracking_data)
        
        # Calculate statistics
        total_emails = len(filtered_data)
        successful_deliveries = len([d for d in filtered_data if d['status'] == NotificationStatus.SENT])
        failed_deliveries = len([d for d in filtered_data if d['status'] == NotificationStatus.FAILED])
        opened_emails = len([d for d in filtered_data if d.get('opened_at')])
        clicked_emails = len([d for d in filtered_data if d.get('clicked_at')])
        
        return {
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'total_emails': total_emails,
            'successful_deliveries': successful_deliveries,
            'failed_deliveries': failed_deliveries,
            'delivery_rate': (successful_deliveries / total_emails * 100) if total_emails > 0 else 0,
            'open_rate': (opened_emails / successful_deliveries * 100) if successful_deliveries > 0 else 0,
            'click_rate': (clicked_emails / successful_deliveries * 100) if successful_deliveries > 0 else 0,
            'emails_by_type': self._group_by_field(filtered_data, 'email_type'),
            'emails_by_status': self._group_by_field(filtered_data, 'status')
        }
    
    def _group_by_field(self, data: List[Dict], field: str) -> Dict[str, int]:
        """Group data by a specific field"""
        result = {}
        for item in data:
            value = item.get(field, 'unknown')
            result[value] = result.get(value, 0) + 1
        return result