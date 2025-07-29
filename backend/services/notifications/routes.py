# =====================================================
# Notification Service Routes
# API endpoints for notifications and email management
# File: backend/services/notifications/routes.py
# =====================================================

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, timedelta
from uuid import UUID
import logging

from shared.database import get_async_session
from shared.models.platform_user import PlatformUserDB
from shared.auth import get_current_active_user
from .schemas import (
    EmailRequest, NotificationRequest, BulkEmailRequest, NotificationResponse,
    EmailStatusResponse, NotificationPreferences, NotificationStats,
    EmailTemplate, NotificationHistory
)
from .notification_service import NotificationService
from .email_service import EmailService
from .templates import EmailTemplateService

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])
logger = logging.getLogger(__name__)

# Initialize services
notification_service = NotificationService()
email_service = EmailService()
template_service = EmailTemplateService()

@router.post("/send", response_model=NotificationResponse)
async def send_notification(
    notification: NotificationRequest,
    background_tasks: BackgroundTasks,
    current_user: PlatformUserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Send a notification via specified channel
    Supports email, SMS, push, and in-app notifications
    """
    try:
        # Check permissions
        if current_user.platform_role not in ['super_admin', 'school_admin', 'teacher']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to send notifications"
            )
        
        # Set sender context
        notification.sender_id = current_user.id
        
        # Send notification
        result = await notification_service.send_notification(notification, db)
        
        logger.info(f"Notification sent by {current_user.email}: {result.notification_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )

@router.post("/email/send", response_model=dict)
async def send_email(
    email_request: EmailRequest,
    background_tasks: BackgroundTasks,
    current_user: PlatformUserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Send email with template support
    """
    try:
        # Check permissions
        if current_user.platform_role not in ['super_admin', 'school_admin', 'teacher']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to send emails"
            )
        
        # Set sender context
        email_request.sender_id = current_user.id
        
        # Send email
        result = await email_service.send_email(email_request)
        
        logger.info(f"Email sent by {current_user.email}: {result['email_id']}")
        return result
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )

@router.post("/email/bulk", response_model=NotificationResponse)
async def send_bulk_email(
    bulk_request: BulkEmailRequest,
    background_tasks: BackgroundTasks,
    current_user: PlatformUserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Send bulk emails with template support
    """
    try:
        # Check permissions
        if current_user.platform_role not in ['super_admin', 'school_admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for bulk email"
            )
        
        # Set sender context
        bulk_request.sender_id = current_user.id
        
        # Send bulk emails in background
        background_tasks.add_task(
            notification_service.send_bulk_email,
            bulk_request,
            db
        )
        
        return NotificationResponse(
            notification_id=f"bulk_{current_user.id}_{datetime.utcnow().timestamp()}",
            status="queued",
            message="Bulk email queued for processing",
            recipients_sent=0,
            recipients_failed=0,
            scheduled_for=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error queueing bulk email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue bulk email: {str(e)}"
        )

@router.post("/schedule")
async def schedule_notification(
    notification: NotificationRequest,
    send_at: datetime,
    current_user: PlatformUserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Schedule a notification for later delivery
    """
    try:
        # Check permissions
        if current_user.platform_role not in ['super_admin', 'school_admin', 'teacher']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to schedule notifications"
            )
        
        # Validate send time
        if send_at <= datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scheduled time must be in the future"
            )
        
        # Set sender context
        notification.sender_id = current_user.id
        
        # Schedule notification
        notification_id = await notification_service.schedule_notification(
            notification, send_at, db
        )
        
        return {
            "notification_id": notification_id,
            "message": "Notification scheduled successfully",
            "scheduled_for": send_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule notification: {str(e)}"
        )

@router.get("/{notification_id}/status")
async def get_notification_status(
    notification_id: str,
    current_user: PlatformUserDB = Depends(get_current_active_user)
):
    """
    Get status of a notification
    """
    try:
        status_data = await notification_service.get_notification_status(notification_id)
        
        if not status_data or status_data.get("status") == "not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return status_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification status"
        )

@router.delete("/{notification_id}/cancel")
async def cancel_scheduled_notification(
    notification_id: str,
    current_user: PlatformUserDB = Depends(get_current_active_user)
):
    """
    Cancel a scheduled notification
    """
    try:
        success = await notification_service.cancel_scheduled_notification(notification_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found or cannot be cancelled"
            )
        
        return {"message": "Notification cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel notification"
        )

@router.get("/email/{email_id}/status", response_model=EmailStatusResponse)
async def get_email_status(
    email_id: str,
    current_user: PlatformUserDB = Depends(get_current_active_user)
):
    """
    Get email delivery status with tracking data
    """
    try:
        status = await email_service.get_email_status(email_id)
        
        if not status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found"
            )
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get email status"
        )

@router.get("/templates", response_model=List[dict])
async def list_email_templates(
    current_user: PlatformUserDB = Depends(get_current_active_user)
):
    """
    List available email templates
    """
    try:
        templates = template_service.list_templates()
        return templates
        
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list templates"
        )

@router.get("/templates/{template_name}")
async def get_email_template(
    template_name: str,
    current_user: PlatformUserDB = Depends(get_current_active_user)
):
    """
    Get email template details
    """
    try:
        template = await template_service.get_template(template_name)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get template"
        )

@router.post("/templates/{template_name}/preview")
async def preview_email_template(
    template_name: str,
    template_data: dict,
    current_user: PlatformUserDB = Depends(get_current_active_user)
):
    """
    Preview email template with data
    """
    try:
        rendered = await template_service.render_template(template_name, template_data)
        return rendered
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error previewing template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to preview template"
        )

@router.put("/preferences", response_model=dict)
async def update_notification_preferences(
    preferences: NotificationPreferences,
    current_user: PlatformUserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Update user notification preferences
    """
    try:
        # Set user ID
        preferences.user_id = current_user.id
        
        success = await notification_service.update_notification_preferences(
            db, current_user.id, preferences
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update preferences"
            )
        
        return {"message": "Notification preferences updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification preferences"
        )

@router.get("/statistics", response_model=dict)
async def get_notification_statistics(
    days: int = Query(30, ge=1, le=365),
    school_id: Optional[UUID] = Query(None),
    current_user: PlatformUserDB = Depends(get_current_active_user)
):
    """
    Get notification statistics
    """
    try:
        # Check permissions for school-specific stats
        if school_id and current_user.platform_role not in ['super_admin', 'school_admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for school statistics"
            )
        
        # Get statistics (placeholder implementation)
        start_date = datetime.utcnow() - timedelta(days=days)
        end_date = datetime.utcnow()
        
        # TODO: Implement actual statistics calculation
        stats = {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_notifications": 0,
            "by_type": {
                "email": 0,
                "sms": 0,
                "push": 0,
                "in_app": 0
            },
            "by_status": {
                "sent": 0,
                "failed": 0,
                "pending": 0
            },
            "engagement": {
                "email_open_rate": 0.0,
                "email_click_rate": 0.0,
                "push_open_rate": 0.0
            }
        }
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification statistics"
        )

@router.get("/email/report")
async def get_email_delivery_report(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    school_id: Optional[str] = Query(None),
    current_user: PlatformUserDB = Depends(get_current_active_user)
):
    """
    Get email delivery report
    """
    try:
        # Check permissions
        if current_user.platform_role not in ['super_admin', 'school_admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for email reports"
            )
        
        report = await email_service.get_delivery_report(start_date, end_date, school_id)
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating email report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate email report"
        )

@router.get("/health")
async def get_service_health(
    current_user: PlatformUserDB = Depends(get_current_active_user)
):
    """
    Get notification service health status
    """
    try:
        # Check permissions
        if current_user.platform_role not in ['super_admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for health check"
            )
        
        health = notification_service.get_service_health()
        email_stats = email_service.get_service_statistics()
        
        return {
            "notification_service": health,
            "email_service": email_stats,
            "overall_status": "healthy" if health["status"] == "healthy" else "degraded"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get service health"
        )

@router.post("/webhook/email")
async def handle_email_webhook(
    event_data: dict
):
    """
    Handle email delivery webhook events
    """
    try:
        success = await email_service.handle_webhook_event(event_data)
        
        if success:
            return {"message": "Webhook processed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook data"
            )
        
    except Exception as e:
        logger.error(f"Error handling email webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )

@router.get("/track/open/{email_id}")
async def track_email_open(email_id: str):
    """
    Track email open (tracking pixel endpoint)
    """
    try:
        # Update tracking data
        await email_service.handle_webhook_event({
            'email_id': email_id,
            'event_type': 'opened',
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Return 1x1 transparent GIF
        from fastapi.responses import Response
        
        # 1x1 transparent GIF in base64
        gif_data = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x04\x01\x00;'
        
        return Response(
            content=gif_data,
            media_type="image/gif",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
        
    except Exception as e:
        logger.error(f"Error tracking email open: {str(e)}")
        # Return tracking pixel even on error
        from fastapi.responses import Response
        gif_data = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x04\x01\x00;'
        return Response(content=gif_data, media_type="image/gif")