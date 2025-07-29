# =====================================================
# Comprehensive Notification Service
# Handle all types of notifications with queuing and tracking
# File: backend/services/notifications/notification_service.py
# =====================================================

import asyncio
import uuid
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from .email_service import EmailService
from .templates import EmailTemplateService
from .schemas import (
    NotificationRequest, EmailRequest, SMSRequest, PushNotificationRequest,
    NotificationResponse, NotificationStatus, NotificationType, NotificationPriority,
    NotificationPreferences, BulkEmailRequest
)

logger = logging.getLogger(__name__)

class NotificationService:
    """Comprehensive notification service with multi-channel support"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.template_service = EmailTemplateService()
        self.notification_queue = {}  # In production, use Redis/RabbitMQ
        self.delivery_tracking = {}   # In production, use database
        
        # Service configurations
        self.max_retries = 3
        self.retry_delays = [60, 300, 900]  # 1min, 5min, 15min
        self.batch_size = 100
        
    async def send_notification(
        self,
        notification: NotificationRequest,
        db: AsyncSession
    ) -> NotificationResponse:
        """Send notification via appropriate channel"""
        
        notification_id = str(uuid.uuid4())
        
        try:
            # Check user preferences
            filtered_recipients = await self._filter_recipients_by_preferences(
                db, notification.recipients, notification.notification_type
            )
            
            if not filtered_recipients:
                return NotificationResponse(
                    notification_id=notification_id,
                    status=NotificationStatus.FAILED,
                    message="No recipients after filtering preferences",
                    recipients_sent=0,
                    recipients_failed=len(notification.recipients)
                )
            
            # Route to appropriate service
            if notification.notification_type == NotificationType.EMAIL:
                result = await self._send_email_notification(notification, filtered_recipients, db)
            elif notification.notification_type == NotificationType.SMS:
                result = await self._send_sms_notification(notification, filtered_recipients, db)
            elif notification.notification_type == NotificationType.PUSH:
                result = await self._send_push_notification(notification, filtered_recipients, db)
            elif notification.notification_type == NotificationType.IN_APP:
                result = await self._send_in_app_notification(notification, filtered_recipients, db)
            else:
                raise ValueError(f"Unsupported notification type: {notification.notification_type}")
            
            # Track notification
            await self._track_notification(notification_id, notification, result, db)
            
            return NotificationResponse(
                notification_id=notification_id,
                status=result['status'],
                message=result['message'],
                recipients_sent=result['sent_count'],
                recipients_failed=result['failed_count'],
                sent_at=datetime.utcnow().isoformat() if result['status'] == NotificationStatus.SENT else None,
                tracking_enabled=True,
                tracking_url=f"/api/v1/notifications/{notification_id}/tracking"
            )
            
        except Exception as e:
            logger.error(f"Error sending notification {notification_id}: {str(e)}")
            
            return NotificationResponse(
                notification_id=notification_id,
                status=NotificationStatus.FAILED,
                message=f"Failed to send notification: {str(e)}",
                recipients_sent=0,
                recipients_failed=len(notification.recipients)
            )
    
    async def send_bulk_email(
        self,
        bulk_request: BulkEmailRequest,
        db: AsyncSession
    ) -> NotificationResponse:
        """Send bulk emails with batching and progress tracking"""
        
        bulk_id = str(uuid.uuid4())
        
        try:
            # Get template
            template = await self.template_service.get_template(bulk_request.template_name)
            if not template:
                raise ValueError(f"Template '{bulk_request.template_name}' not found")
            
            # Process recipients in batches
            total_recipients = len(bulk_request.recipients)
            sent_count = 0
            failed_count = 0
            
            for i in range(0, total_recipients, bulk_request.batch_size):
                batch = bulk_request.recipients[i:i + bulk_request.batch_size]
                
                # Process batch
                batch_results = await self._process_email_batch(
                    batch, template, bulk_request, db
                )
                
                sent_count += batch_results['sent']
                failed_count += batch_results['failed']
                
                # Update progress
                progress = (i + len(batch)) / total_recipients * 100
                await self._update_bulk_progress(bulk_id, progress, sent_count, failed_count)
                
                # Delay between batches
                if i + bulk_request.batch_size < total_recipients and bulk_request.delay_between_batches > 0:
                    await asyncio.sleep(bulk_request.delay_between_batches)
            
            status = NotificationStatus.SENT if failed_count == 0 else NotificationStatus.FAILED
            
            return NotificationResponse(
                notification_id=bulk_id,
                status=status,
                message=f"Bulk email completed: {sent_count} sent, {failed_count} failed",
                recipients_sent=sent_count,
                recipients_failed=failed_count,
                sent_at=datetime.utcnow().isoformat(),
                tracking_enabled=bulk_request.track_opens
            )
            
        except Exception as e:
            logger.error(f"Error in bulk email {bulk_id}: {str(e)}")
            raise
    
    async def schedule_notification(
        self,
        notification: NotificationRequest,
        send_at: datetime,
        db: AsyncSession
    ) -> str:
        """Schedule notification for later delivery"""
        
        notification_id = str(uuid.uuid4())
        
        # Store in queue (in production, use proper job queue)
        self.notification_queue[notification_id] = {
            'notification': notification,
            'send_at': send_at,
            'status': 'scheduled',
            'created_at': datetime.utcnow()
        }
        
        logger.info(f"Notification {notification_id} scheduled for {send_at}")
        return notification_id
    
    async def cancel_scheduled_notification(self, notification_id: str) -> bool:
        """Cancel a scheduled notification"""
        
        if notification_id in self.notification_queue:
            queue_item = self.notification_queue[notification_id]
            if queue_item['status'] == 'scheduled':
                queue_item['status'] = 'cancelled'
                logger.info(f"Cancelled notification {notification_id}")
                return True
        
        return False
    
    async def get_notification_status(self, notification_id: str) -> Dict[str, Any]:
        """Get status of a notification"""
        
        # Check queue first
        if notification_id in self.notification_queue:
            return self.notification_queue[notification_id]
        
        # Check delivery tracking
        if notification_id in self.delivery_tracking:
            return self.delivery_tracking[notification_id]
        
        return {"status": "not_found"}
    
    async def update_notification_preferences(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        preferences: NotificationPreferences
    ) -> bool:
        """Update user notification preferences"""
        
        try:
            # TODO: Implement database storage for preferences
            # For now, store in memory
            self.user_preferences = getattr(self, 'user_preferences', {})
            self.user_preferences[str(user_id)] = preferences.dict()
            
            logger.info(f"Updated notification preferences for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating preferences for user {user_id}: {str(e)}")
            return False
    
    async def _send_email_notification(
        self,
        notification: NotificationRequest,
        recipients: List[str],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Send email notification"""
        
        try:
            # Prepare email request
            email_request = EmailRequest(
                to=recipients,
                subject=notification.title,
                template_name=notification.template_name,
                template_data=notification.template_data,
                html_content=notification.content if not notification.template_name else None,
                school_id=notification.school_id,
                sender_id=notification.sender_id,
                priority=notification.priority
            )
            
            # Send email
            result = await self.email_service.send_email(email_request)
            
            return {
                'status': NotificationStatus.SENT if result['success'] else NotificationStatus.FAILED,
                'message': result['message'],
                'sent_count': len(recipients) if result['success'] else 0,
                'failed_count': 0 if result['success'] else len(recipients)
            }
            
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return {
                'status': NotificationStatus.FAILED,
                'message': str(e),
                'sent_count': 0,
                'failed_count': len(recipients)
            }
    
    async def _send_sms_notification(
        self,
        notification: NotificationRequest,
        recipients: List[str],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Send SMS notification"""
        
        try:
            # TODO: Implement SMS service integration
            # For now, simulate SMS sending
            
            sent_count = 0
            failed_count = 0
            
            for recipient in recipients:
                try:
                    # Simulate SMS API call
                    await self._send_single_sms(recipient, notification.content)
                    sent_count += 1
                    logger.info(f"SMS sent to {recipient}")
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to send SMS to {recipient}: {str(e)}")
            
            status = NotificationStatus.SENT if failed_count == 0 else NotificationStatus.FAILED
            
            return {
                'status': status,
                'message': f'SMS notification processed: {sent_count} sent, {failed_count} failed',
                'sent_count': sent_count,
                'failed_count': failed_count
            }
            
        except Exception as e:
            logger.error(f"Error in SMS notification: {str(e)}")
            return {
                'status': NotificationStatus.FAILED,
                'message': str(e),
                'sent_count': 0,
                'failed_count': len(recipients)
            }
    
    async def _send_push_notification(
        self,
        notification: NotificationRequest,
        recipients: List[str],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Send push notification"""
        
        try:
            # TODO: Implement push notification service (Firebase, etc.)
            # For now, simulate push notification
            
            sent_count = len(recipients)
            logger.info(f"Push notification sent to {sent_count} users: {notification.title}")
            
            return {
                'status': NotificationStatus.SENT,
                'message': f'Push notification sent to {sent_count} users',
                'sent_count': sent_count,
                'failed_count': 0
            }
            
        except Exception as e:
            logger.error(f"Error in push notification: {str(e)}")
            return {
                'status': NotificationStatus.FAILED,
                'message': str(e),
                'sent_count': 0,
                'failed_count': len(recipients)
            }
    
    async def _send_in_app_notification(
        self,
        notification: NotificationRequest,
        recipients: List[str],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Send in-app notification"""
        
        try:
            # TODO: Implement in-app notification storage
            # For now, simulate storage in database
            
            for recipient in recipients:
                # Store notification in user's inbox
                await self._store_in_app_notification(recipient, notification)
            
            return {
                'status': NotificationStatus.SENT,
                'message': f'In-app notification sent to {len(recipients)} users',
                'sent_count': len(recipients),
                'failed_count': 0
            }
            
        except Exception as e:
            logger.error(f"Error in in-app notification: {str(e)}")
            return {
                'status': NotificationStatus.FAILED,
                'message': str(e),
                'sent_count': 0,
                'failed_count': len(recipients)
            }
    
    async def _filter_recipients_by_preferences(
        self,
        db: AsyncSession,
        recipients: List[str],
        notification_type: NotificationType
    ) -> List[str]:
        """Filter recipients based on their notification preferences"""
        
        # TODO: Implement actual preference checking from database
        # For now, return all recipients
        return recipients
    
    async def _process_email_batch(
        self,
        batch: List[Dict[str, Any]],
        template: Dict[str, Any],
        bulk_request: BulkEmailRequest,
        db: AsyncSession
    ) -> Dict[str, int]:
        """Process a batch of emails"""
        
        sent = 0
        failed = 0
        
        for recipient_data in batch:
            try:
                # Merge global and recipient-specific data
                template_data = {**bulk_request.global_template_data, **recipient_data}
                
                # Prepare email
                email_request = EmailRequest(
                    to=[recipient_data['email']],
                    subject=template_data.get('subject', template['subject_template']),
                    template_name=bulk_request.template_name,
                    template_data=template_data,
                    school_id=bulk_request.school_id,
                    sender_id=bulk_request.sender_id,
                    track_opens=bulk_request.track_opens,
                    track_clicks=bulk_request.track_clicks
                )
                
                # Send email
                result = await self.email_service.send_email(email_request)
                
                if result['success']:
                    sent += 1
                else:
                    failed += 1
                    logger.error(f"Failed to send email to {recipient_data['email']}: {result['message']}")
                    
            except Exception as e:
                failed += 1
                logger.error(f"Error processing email for {recipient_data.get('email', 'unknown')}: {str(e)}")
        
        return {'sent': sent, 'failed': failed}
    
    async def _track_notification(
        self,
        notification_id: str,
        notification: NotificationRequest,
        result: Dict[str, Any],
        db: AsyncSession
    ):
        """Track notification for analytics and debugging"""
        
        tracking_data = {
            'notification_id': notification_id,
            'type': notification.notification_type,
            'recipients_count': len(notification.recipients),
            'sent_count': result['sent_count'],
            'failed_count': result['failed_count'],
            'status': result['status'],
            'created_at': datetime.utcnow().isoformat(),
            'school_id': str(notification.school_id) if notification.school_id else None,
            'sender_id': str(notification.sender_id) if notification.sender_id else None
        }
        
        self.delivery_tracking[notification_id] = tracking_data
        logger.info(f"Tracked notification {notification_id}: {tracking_data}")
    
    async def _update_bulk_progress(
        self,
        bulk_id: str,
        progress: float,
        sent_count: int,
        failed_count: int
    ):
        """Update bulk operation progress"""
        
        progress_data = {
            'bulk_id': bulk_id,
            'progress_percentage': progress,
            'sent_count': sent_count,
            'failed_count': failed_count,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # In production, store in Redis or database for real-time updates
        self.delivery_tracking[f"{bulk_id}_progress"] = progress_data
        logger.info(f"Bulk progress {bulk_id}: {progress:.1f}% ({sent_count} sent, {failed_count} failed)")
    
    async def _send_single_sms(self, phone_number: str, message: str):
        """Send single SMS (placeholder implementation)"""
        
        # TODO: Integrate with SMS provider (Twilio, etc.)
        await asyncio.sleep(0.1)  # Simulate API call
        
        # Simulate occasional failures
        import random
        if random.random() < 0.05:  # 5% failure rate
            raise Exception("SMS delivery failed")
    
    async def _store_in_app_notification(
        self,
        user_id: str,
        notification: NotificationRequest
    ):
        """Store in-app notification for user"""
        
        # TODO: Implement database storage
        notification_data = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'title': notification.title,
            'content': notification.content,
            'read': False,
            'created_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Stored in-app notification for user {user_id}")
    
    async def process_scheduled_notifications(self):
        """Process scheduled notifications (background task)"""
        
        current_time = datetime.utcnow()
        
        for notification_id, queue_item in list(self.notification_queue.items()):
            if (queue_item['status'] == 'scheduled' and 
                queue_item['send_at'] <= current_time):
                
                try:
                    # Send the notification
                    # TODO: Implement actual sending
                    queue_item['status'] = 'sent'
                    queue_item['sent_at'] = current_time
                    
                    logger.info(f"Processed scheduled notification {notification_id}")
                    
                except Exception as e:
                    queue_item['status'] = 'failed'
                    queue_item['error'] = str(e)
                    logger.error(f"Failed to process scheduled notification {notification_id}: {str(e)}")
    
    async def cleanup_old_tracking_data(self, days_to_keep: int = 30):
        """Clean up old tracking data"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        for tracking_id in list(self.delivery_tracking.keys()):
            tracking_data = self.delivery_tracking[tracking_id]
            
            if 'created_at' in tracking_data:
                created_at = datetime.fromisoformat(tracking_data['created_at'])
                if created_at < cutoff_date:
                    del self.delivery_tracking[tracking_id]
                    logger.debug(f"Cleaned up old tracking data: {tracking_id}")
    
    def get_service_health(self) -> Dict[str, Any]:
        """Get notification service health status"""
        
        return {
            'status': 'healthy',
            'queued_notifications': len([q for q in self.notification_queue.values() if q['status'] == 'scheduled']),
            'tracked_notifications': len(self.delivery_tracking),
            'email_service_healthy': True,  # TODO: Check actual email service
            'sms_service_healthy': True,    # TODO: Check actual SMS service
            'last_health_check': datetime.utcnow().isoformat()
        }