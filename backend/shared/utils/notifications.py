"""
Notifications Utility Module
Handles in-app notifications and alerts for OneClass Platform
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class NotificationType(str, Enum):
    """Notification types"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    URGENT = "urgent"

class NotificationCategory(str, Enum):
    """Notification categories"""
    ACADEMIC = "academic"
    ATTENDANCE = "attendance"
    DISCIPLINARY = "disciplinary"
    HEALTH = "health"
    FINANCIAL = "financial"
    SYSTEM = "system"
    COMMUNICATION = "communication"

class NotificationService:
    """Service for managing notifications"""
    
    def __init__(self):
        # In a real implementation, this would connect to a database
        # or message queue system
        self.notifications = []
    
    async def send_notification(
        self,
        user_id: UUID,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        category: NotificationCategory = NotificationCategory.SYSTEM,
        data: Optional[Dict[str, Any]] = None,
        send_email: bool = False,
        send_sms: bool = False
    ) -> bool:
        """Send a notification to a user"""
        try:
            notification = {
                "id": len(self.notifications) + 1,
                "user_id": user_id,
                "title": title,
                "message": message,
                "type": notification_type,
                "category": category,
                "data": data or {},
                "read": False,
                "created_at": datetime.utcnow(),
                "send_email": send_email,
                "send_sms": send_sms
            }
            
            self.notifications.append(notification)
            
            # In a real implementation, you would:
            # 1. Save to database
            # 2. Send real-time notification via WebSocket
            # 3. Send email if requested
            # 4. Send SMS if requested
            
            logger.info(f"Notification sent to user {user_id}: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {str(e)}")
            return False
    
    async def send_bulk_notification(
        self,
        user_ids: List[UUID],
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        category: NotificationCategory = NotificationCategory.SYSTEM,
        data: Optional[Dict[str, Any]] = None
    ) -> int:
        """Send notification to multiple users"""
        success_count = 0
        
        for user_id in user_ids:
            if await self.send_notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                category=category,
                data=data
            ):
                success_count += 1
        
        return success_count
    
    async def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        category: Optional[NotificationCategory] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        user_notifications = [
            n for n in self.notifications 
            if n["user_id"] == user_id
        ]
        
        if unread_only:
            user_notifications = [n for n in user_notifications if not n["read"]]
        
        if category:
            user_notifications = [n for n in user_notifications if n["category"] == category]
        
        # Sort by creation date (newest first)
        user_notifications.sort(key=lambda x: x["created_at"], reverse=True)
        
        return user_notifications[:limit]
    
    async def mark_notification_read(self, notification_id: int, user_id: UUID) -> bool:
        """Mark a notification as read"""
        try:
            for notification in self.notifications:
                if (notification["id"] == notification_id and 
                    notification["user_id"] == user_id):
                    notification["read"] = True
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to mark notification {notification_id} as read: {str(e)}")
            return False

# Global notification service instance
notification_service = NotificationService()

# Convenience functions
async def send_notification(
    user_id: UUID,
    title: str,
    message: str,
    notification_type: NotificationType = NotificationType.INFO,
    category: NotificationCategory = NotificationCategory.SYSTEM,
    data: Optional[Dict[str, Any]] = None,
    send_email: bool = False,
    send_sms: bool = False
) -> bool:
    """Send notification using the global service"""
    return await notification_service.send_notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        category=category,
        data=data,
        send_email=send_email,
        send_sms=send_sms
    )

async def send_attendance_alert(student_id: UUID, parent_ids: List[UUID], student_name: str) -> bool:
    """Send attendance alert to parents"""
    title = f"Attendance Alert - {student_name}"
    message = f"{student_name} was marked absent today. Please contact the school if this is unexpected."
    
    success_count = 0
    for parent_id in parent_ids:
        if await send_notification(
            user_id=parent_id,
            title=title,
            message=message,
            notification_type=NotificationType.WARNING,
            category=NotificationCategory.ATTENDANCE,
            data={"student_id": str(student_id)},
            send_email=True
        ):
            success_count += 1
    
    return success_count > 0

async def send_disciplinary_alert(
    student_id: UUID, 
    parent_ids: List[UUID], 
    student_name: str, 
    incident_type: str
) -> bool:
    """Send disciplinary incident alert to parents"""
    title = f"Disciplinary Notice - {student_name}"
    message = f"A disciplinary incident ({incident_type}) has been recorded for {student_name}. Please contact the school for more details."
    
    success_count = 0
    for parent_id in parent_ids:
        if await send_notification(
            user_id=parent_id,
            title=title,
            message=message,
            notification_type=NotificationType.URGENT,
            category=NotificationCategory.DISCIPLINARY,
            data={"student_id": str(student_id), "incident_type": incident_type},
            send_email=True
        ):
            success_count += 1
    
    return success_count > 0

async def send_health_alert(
    student_id: UUID, 
    parent_ids: List[UUID], 
    student_name: str, 
    health_issue: str
) -> bool:
    """Send health alert to parents"""
    title = f"Health Notice - {student_name}"
    message = f"A health record has been created for {student_name}: {health_issue}. Please contact the school nurse for more information."
    
    success_count = 0
    for parent_id in parent_ids:
        if await send_notification(
            user_id=parent_id,
            title=title,
            message=message,
            notification_type=NotificationType.URGENT,
            category=NotificationCategory.HEALTH,
            data={"student_id": str(student_id), "health_issue": health_issue},
            send_email=True
        ):
            success_count += 1
    
    return success_count > 0
