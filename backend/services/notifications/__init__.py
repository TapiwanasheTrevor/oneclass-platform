# =====================================================
# Notification Service Module
# Comprehensive email and notification system
# File: backend/services/notifications/__init__.py
# =====================================================

from .email_service import EmailService
from .notification_service import NotificationService
from .templates import EmailTemplateService
from .routes import router
from .schemas import (
    EmailRequest, NotificationRequest, EmailTemplate, 
    NotificationResponse, EmailStatusResponse
)

__all__ = [
    "EmailService",
    "NotificationService", 
    "EmailTemplateService",
    "router",
    "EmailRequest",
    "NotificationRequest",
    "EmailTemplate",
    "NotificationResponse",
    "EmailStatusResponse"
]