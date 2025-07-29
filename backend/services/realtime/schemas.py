# =====================================================
# Real-time Progress Tracking Schemas
# Pydantic models for progress tracking and WebSocket events
# File: backend/services/realtime/schemas.py
# =====================================================

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
import uuid
from enum import Enum

class ProgressStatus(str, Enum):
    """Progress status types"""
    PENDING = "pending"
    STARTING = "starting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class OperationType(str, Enum):
    """Types of operations that can be tracked"""
    FILE_UPLOAD = "file_upload"
    BULK_IMPORT = "bulk_import"
    BULK_EMAIL = "bulk_email"
    USER_CREATION = "user_creation"
    DATA_EXPORT = "data_export"
    BACKUP_CREATION = "backup_creation"
    SYSTEM_UPDATE = "system_update"
    MIGRATION = "migration"

class EventType(str, Enum):
    """WebSocket event types"""
    PROGRESS_UPDATE = "progress_update"
    STATUS_CHANGE = "status_change"
    ERROR_OCCURRED = "error_occurred"
    OPERATION_COMPLETED = "operation_completed"
    CONNECTION_ESTABLISHED = "connection_established"
    HEARTBEAT = "heartbeat"

class ProgressUpdate(BaseModel):
    """Progress update data"""
    operation_id: str
    operation_type: OperationType
    status: ProgressStatus
    
    # Progress metrics
    progress_percentage: float = Field(..., ge=0, le=100)
    current_step: int = Field(..., ge=0)
    total_steps: int = Field(..., ge=1)
    
    # Timing information
    started_at: datetime
    estimated_completion: Optional[datetime] = None
    elapsed_time: float = 0  # seconds
    
    # Operation details
    current_task: Optional[str] = None
    processed_items: int = 0
    total_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    
    # User context
    user_id: UUID
    school_id: Optional[UUID] = None
    
    # Additional data
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('progress_percentage')
    def validate_percentage(cls, v):
        return round(v, 2)

class BulkOperationProgress(BaseModel):
    """Specific progress tracking for bulk operations"""
    operation_id: str
    operation_type: OperationType
    status: ProgressStatus
    
    # Batch processing details
    total_batches: int
    completed_batches: int
    current_batch: int
    batch_size: int
    
    # Item-level tracking
    total_items: int
    processed_items: int
    successful_items: int
    failed_items: int
    skipped_items: int = 0
    
    # Progress metrics
    progress_percentage: float
    items_per_second: float = 0
    estimated_completion: Optional[datetime] = None
    
    # Error tracking
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Timing
    started_at: datetime
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Results summary
    results_summary: Dict[str, Any] = Field(default_factory=dict)

class RealTimeEvent(BaseModel):
    """Real-time event for WebSocket communication"""
    event_type: EventType
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Event data
    operation_id: Optional[str] = None
    user_id: Optional[UUID] = None
    school_id: Optional[UUID] = None
    
    # Event payload
    data: Dict[str, Any] = Field(default_factory=dict)
    message: Optional[str] = None
    
    # Targeting
    target_users: Optional[List[UUID]] = None
    target_schools: Optional[List[UUID]] = None
    broadcast: bool = False

class ConnectionInfo(BaseModel):
    """WebSocket connection information"""
    connection_id: str
    user_id: UUID
    school_id: Optional[UUID] = None
    connected_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    
    # Connection metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    subscriptions: List[str] = Field(default_factory=list)  # Operation IDs user is subscribed to
    
    # Status
    is_active: bool = True

class SubscriptionRequest(BaseModel):
    """Request to subscribe to operation updates"""
    operation_ids: List[str]
    event_types: List[EventType] = Field(default_factory=lambda: list(EventType))

class ProgressSummary(BaseModel):
    """Summary of all active operations for a user"""
    user_id: UUID
    active_operations: List[ProgressUpdate]
    recent_completed: List[ProgressUpdate]
    total_active: int
    total_completed_today: int

class OperationLog(BaseModel):
    """Log entry for an operation"""
    operation_id: str
    timestamp: datetime
    level: str  # info, warning, error
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)

class SystemMetrics(BaseModel):
    """System-wide metrics for monitoring"""
    active_operations: int
    total_connections: int
    operations_per_minute: float
    average_completion_time: float
    error_rate: float
    
    # Resource usage
    memory_usage: float
    cpu_usage: float
    
    # Queue status
    pending_operations: int
    processing_operations: int
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PerformanceMetrics(BaseModel):
    """Performance metrics for operations"""
    operation_type: OperationType
    avg_duration: float
    min_duration: float
    max_duration: float
    success_rate: float
    throughput: float  # items per second
    
    # Recent performance
    last_24h_count: int
    last_24h_success_rate: float
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AlertConfig(BaseModel):
    """Configuration for progress alerts"""
    operation_types: List[OperationType]
    alert_on_error: bool = True
    alert_on_completion: bool = True
    alert_on_slow_progress: bool = True
    
    # Thresholds
    slow_progress_threshold: float = 0.5  # items per second
    error_rate_threshold: float = 0.1  # 10%
    
    # Notification settings
    email_alerts: bool = True
    in_app_alerts: bool = True
    webhook_url: Optional[str] = None

class ProgressFilter(BaseModel):
    """Filter for progress queries"""
    user_id: Optional[UUID] = None
    school_id: Optional[UUID] = None
    operation_types: Optional[List[OperationType]] = None
    statuses: Optional[List[ProgressStatus]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class BatchUpdate(BaseModel):
    """Batch update for multiple operations"""
    updates: List[ProgressUpdate]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class OperationConfig(BaseModel):
    """Configuration for operation tracking"""
    operation_type: OperationType
    track_items: bool = True
    track_timing: bool = True
    track_errors: bool = True
    send_notifications: bool = True
    
    # Update frequency
    update_interval: int = 1  # seconds
    batch_size: int = 100
    
    # Retention
    keep_logs_days: int = 30
    keep_completed_hours: int = 24

class ErrorDetail(BaseModel):
    """Detailed error information"""
    error_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    operation_id: str
    error_type: str
    error_message: str
    error_details: Dict[str, Any] = Field(default_factory=dict)
    
    # Context
    item_index: Optional[int] = None
    batch_number: Optional[int] = None
    retry_count: int = 0
    
    # Timing
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    
    # Resolution
    is_resolved: bool = False
    resolution_notes: Optional[str] = None

class ProgressSnapshot(BaseModel):
    """Point-in-time snapshot of operation progress"""
    operation_id: str
    snapshot_time: datetime
    status: ProgressStatus
    progress_percentage: float
    items_processed: int
    items_remaining: int
    current_rate: float  # items per second
    estimated_completion: Optional[datetime] = None