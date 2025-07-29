# =====================================================
# Notification Service Schemas
# Pydantic models for notifications and email
# File: backend/services/notifications/schemas.py
# =====================================================

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from enum import Enum

class NotificationType(str, Enum):
    """Types of notifications"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"

class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class EmailType(str, Enum):
    """Types of email notifications"""
    WELCOME = "welcome"
    INVITATION = "invitation"
    PASSWORD_RESET = "password_reset"
    VERIFICATION = "verification"
    NOTIFICATION = "notification"
    ALERT = "alert"
    REMINDER = "reminder"
    REPORT = "report"
    MARKETING = "marketing"

class NotificationStatus(str, Enum):
    """Status of notification delivery"""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    REJECTED = "rejected"

class EmailRequest(BaseModel):
    """Request to send email"""
    to: Union[EmailStr, List[EmailStr]]
    subject: str = Field(..., min_length=1, max_length=255)
    template_name: Optional[str] = None
    template_data: Dict[str, Any] = Field(default_factory=dict)
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    
    # Optional fields
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None
    reply_to: Optional[EmailStr] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    
    # Metadata
    email_type: EmailType = EmailType.NOTIFICATION
    priority: NotificationPriority = NotificationPriority.NORMAL
    send_at: Optional[datetime] = None  # For scheduled emails
    expires_at: Optional[datetime] = None
    
    # Tracking
    track_opens: bool = True
    track_clicks: bool = True
    
    # School context
    school_id: Optional[UUID] = None
    sender_id: Optional[UUID] = None
    
    @validator('to')
    def normalize_recipients(cls, v):
        if isinstance(v, str):
            return [v.lower()]
        return [email.lower() for email in v]

class SMSRequest(BaseModel):
    """Request to send SMS"""
    to: Union[str, List[str]]
    message: str = Field(..., min_length=1, max_length=160)
    
    # Optional fields
    sender_name: Optional[str] = Field(None, max_length=11)
    
    # Metadata
    priority: NotificationPriority = NotificationPriority.NORMAL
    send_at: Optional[datetime] = None
    
    # School context
    school_id: Optional[UUID] = None
    sender_id: Optional[UUID] = None

class PushNotificationRequest(BaseModel):
    """Request to send push notification"""
    user_ids: List[UUID]
    title: str = Field(..., min_length=1, max_length=100)
    body: str = Field(..., min_length=1, max_length=500)
    
    # Optional fields
    icon: Optional[str] = None
    image: Optional[str] = None
    click_action: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    priority: NotificationPriority = NotificationPriority.NORMAL
    send_at: Optional[datetime] = None
    
    # School context
    school_id: Optional[UUID] = None

class NotificationRequest(BaseModel):
    """General notification request"""
    notification_type: NotificationType
    recipients: List[str]  # emails, phone numbers, or user IDs
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    
    # Optional fields
    template_name: Optional[str] = None
    template_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Settings
    priority: NotificationPriority = NotificationPriority.NORMAL
    send_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Context
    school_id: Optional[UUID] = None
    sender_id: Optional[UUID] = None

class EmailTemplate(BaseModel):
    """Email template definition"""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    
    # Template content
    subject_template: str = Field(..., min_length=1)
    html_template: str = Field(..., min_length=1)
    text_template: Optional[str] = None
    
    # Template variables
    required_variables: List[str] = Field(default_factory=list)
    optional_variables: List[str] = Field(default_factory=list)
    variable_descriptions: Dict[str, str] = Field(default_factory=dict)
    
    # Metadata
    category: EmailType = EmailType.NOTIFICATION
    language: str = "en"
    is_active: bool = True
    school_id: Optional[UUID] = None  # School-specific templates
    
    # Versioning
    version: str = "1.0"
    created_by: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class NotificationResponse(BaseModel):
    """Response after sending notification"""
    notification_id: str
    status: NotificationStatus
    message: str
    recipients_sent: int
    recipients_failed: int
    
    # Delivery details
    sent_at: Optional[str] = None
    scheduled_for: Optional[str] = None
    estimated_delivery: Optional[str] = None
    
    # Tracking
    tracking_enabled: bool = False
    tracking_url: Optional[str] = None

class EmailStatusResponse(BaseModel):
    """Email delivery status response"""
    email_id: str
    recipient: str
    status: NotificationStatus
    
    # Delivery timeline
    sent_at: Optional[str] = None
    delivered_at: Optional[str] = None
    opened_at: Optional[str] = None
    clicked_at: Optional[str] = None
    failed_at: Optional[str] = None
    
    # Failure details
    failure_reason: Optional[str] = None
    bounce_type: Optional[str] = None
    
    # Tracking data
    open_count: int = 0
    click_count: int = 0
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

class BulkEmailRequest(BaseModel):
    """Request for bulk email sending"""
    recipients: List[Dict[str, Any]]  # List of recipient data
    template_name: str
    
    # Common template data
    global_template_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Email settings
    subject_prefix: Optional[str] = None
    send_individually: bool = True  # Send separate emails vs BCC
    
    # Scheduling
    send_at: Optional[datetime] = None
    batch_size: int = Field(default=100, ge=1, le=1000)
    delay_between_batches: int = Field(default=60, ge=0)  # seconds
    
    # Tracking
    track_opens: bool = True
    track_clicks: bool = True
    
    # Context
    school_id: Optional[UUID] = None
    sender_id: Optional[UUID] = None

class NotificationPreferences(BaseModel):
    """User notification preferences"""
    user_id: UUID
    
    # Channel preferences
    email_enabled: bool = True
    sms_enabled: bool = True
    push_enabled: bool = True
    in_app_enabled: bool = True
    
    # Type preferences
    invitation_emails: bool = True
    reminder_emails: bool = True
    alert_emails: bool = True
    marketing_emails: bool = False
    
    # Frequency settings
    digest_frequency: str = "daily"  # none, daily, weekly
    quiet_hours_start: Optional[str] = None  # HH:MM format
    quiet_hours_end: Optional[str] = None
    
    # School-specific settings
    school_notifications: Dict[str, bool] = Field(default_factory=dict)
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class NotificationHistory(BaseModel):
    """Notification history entry"""
    id: str
    notification_type: NotificationType
    recipient: str
    title: str
    content: str
    status: NotificationStatus
    
    # Timeline
    created_at: str
    sent_at: Optional[str] = None
    delivered_at: Optional[str] = None
    read_at: Optional[str] = None
    
    # Metadata
    school_id: Optional[str] = None
    sender_id: Optional[str] = None
    template_used: Optional[str] = None
    
    # Tracking data
    tracking_data: Dict[str, Any] = Field(default_factory=dict)

class NotificationStats(BaseModel):
    """Notification statistics"""
    total_sent: int
    total_delivered: int
    total_failed: int
    total_opened: int
    total_clicked: int
    
    # Rates
    delivery_rate: float
    open_rate: float
    click_rate: float
    bounce_rate: float
    
    # By type
    stats_by_type: Dict[str, Dict[str, int]]
    stats_by_day: List[Dict[str, Any]]
    
    # Period
    period_start: str
    period_end: str

class WebhookNotification(BaseModel):
    """Webhook notification payload"""
    event_type: str
    notification_id: str
    recipient: str
    status: NotificationStatus
    timestamp: str
    
    # Event data
    event_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Signature for verification
    signature: Optional[str] = None

class NotificationQueue(BaseModel):
    """Notification queue status"""
    queue_name: str
    total_pending: int
    total_processing: int
    total_failed: int
    
    # Performance metrics
    avg_processing_time: float
    messages_per_minute: float
    
    # Queue health
    is_healthy: bool
    last_processed: Optional[str] = None
    errors: List[str] = Field(default_factory=list)

class EmailDeliveryReport(BaseModel):
    """Email delivery report"""
    report_id: str
    period_start: str
    period_end: str
    
    # Summary statistics
    total_emails: int
    successful_deliveries: int
    failed_deliveries: int
    bounced_emails: int
    
    # Engagement metrics
    unique_opens: int
    total_opens: int
    unique_clicks: int
    total_clicks: int
    unsubscribes: int
    
    # Top performing
    top_subject_lines: List[Dict[str, Any]]
    top_templates: List[Dict[str, Any]]
    
    # Issues
    common_failures: List[Dict[str, Any]]
    blocked_domains: List[str]
    
    generated_at: str