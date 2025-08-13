"""
Comprehensive Audit Logging System
Tracks all user actions within school contexts for compliance and security
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
import uuid
import json
from pydantic import BaseModel, Field

Base = declarative_base()

# =====================================================
# AUDIT LOG ENUMS
# =====================================================

class ActionCategory(str, Enum):
    """High-level categories of actions"""
    
    # User Management
    USER_MANAGEMENT = "user_management"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    
    # Student Management
    STUDENT_MANAGEMENT = "student_management"
    ACADEMIC_RECORDS = "academic_records"
    ATTENDANCE = "attendance"
    
    # Staff Management
    STAFF_MANAGEMENT = "staff_management"
    TEACHER_ACTIVITIES = "teacher_activities"
    
    # Financial Operations
    FINANCIAL_OPERATIONS = "financial_operations"
    PAYMENT_PROCESSING = "payment_processing"
    
    # Administrative Actions
    SCHOOL_CONFIGURATION = "school_configuration"
    SYSTEM_ADMINISTRATION = "system_administration"
    
    # Data Operations
    DATA_IMPORT = "data_import"
    DATA_EXPORT = "data_export"
    DATA_BACKUP = "data_backup"
    
    # Communication
    COMMUNICATION = "communication"
    NOTIFICATIONS = "notifications"
    
    # Security Events
    SECURITY_EVENTS = "security_events"
    COMPLIANCE = "compliance"


class ActionType(str, Enum):
    """Specific action types"""
    
    # CRUD Operations
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    BULK_CREATE = "bulk_create"
    BULK_UPDATE = "bulk_update"
    BULK_DELETE = "bulk_delete"
    
    # Authentication & Authorization
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    
    # Data Operations
    IMPORT = "import"
    EXPORT = "export"
    BACKUP = "backup"
    RESTORE = "restore"
    
    # Communication
    EMAIL_SENT = "email_sent"
    SMS_SENT = "sms_sent"
    NOTIFICATION_SENT = "notification_sent"
    
    # Financial
    PAYMENT_PROCESSED = "payment_processed"
    PAYMENT_FAILED = "payment_failed"
    INVOICE_GENERATED = "invoice_generated"
    FEE_ADJUSTMENT = "fee_adjustment"
    
    # Configuration
    SETTINGS_CHANGE = "settings_change"
    CONFIGURATION_UPDATE = "configuration_update"
    
    # Security
    ACCESS_DENIED = "access_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"


class RiskLevel(str, Enum):
    """Risk level classification for actions"""
    
    LOW = "low"           # Normal operations, minimal risk
    MEDIUM = "medium"     # Important operations, moderate oversight needed
    HIGH = "high"         # Critical operations, high oversight required
    CRITICAL = "critical" # Security-sensitive operations, immediate attention


class ComplianceCategory(str, Enum):
    """Compliance categories for Zimbabwe education regulations"""
    
    DATA_PROTECTION = "data_protection"     # Student data privacy
    FINANCIAL_RECORD = "financial_record"   # Financial transparency
    ACADEMIC_RECORD = "academic_record"     # Academic integrity
    MINISTRY_REPORTING = "ministry_reporting" # Government compliance
    SAFETY_COMPLIANCE = "safety_compliance" # Student safety
    EMPLOYMENT_RECORD = "employment_record" # Staff employment records


# =====================================================
# PYDANTIC MODELS FOR STRUCTURED DATA
# =====================================================

class ActionContext(BaseModel):
    """Context information for the action"""
    
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    api_endpoint: Optional[str] = None
    http_method: Optional[str] = None
    
    # Geographic context
    country: Optional[str] = "Zimbabwe"
    city: Optional[str] = None
    timezone: str = "Africa/Harare"
    
    # Business context
    academic_year: Optional[str] = None
    term: Optional[str] = None
    department: Optional[str] = None


class ActionDetails(BaseModel):
    """Detailed information about what was changed"""
    
    # What was affected
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    
    # Changes made (for updates)
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    changed_fields: Optional[List[str]] = None
    
    # Bulk operations
    affected_count: Optional[int] = None
    success_count: Optional[int] = None
    failure_count: Optional[int] = None
    
    # Additional metadata
    reason: Optional[str] = None
    notes: Optional[str] = None
    file_attachments: Optional[List[str]] = None


class SecurityMetadata(BaseModel):
    """Security-related metadata"""
    
    requires_approval: bool = False
    approved_by: Optional[str] = None
    approval_timestamp: Optional[datetime] = None
    
    # Risk assessment
    automated_risk_score: Optional[float] = None
    risk_factors: Optional[List[str]] = None
    
    # Compliance flags
    compliance_categories: List[ComplianceCategory] = Field(default_factory=list)
    retention_required_until: Optional[datetime] = None
    
    # Incident tracking
    incident_id: Optional[str] = None
    investigation_required: bool = False


# =====================================================
# MAIN AUDIT LOG MODEL
# =====================================================

class AuditLog(Base):
    """
    Comprehensive audit log for tracking all actions within schools
    Designed for compliance, security monitoring, and operational oversight
    """
    
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index('idx_audit_logs_school_user', 'school_id', 'user_id'),
        Index('idx_audit_logs_timestamp', 'timestamp'),
        Index('idx_audit_logs_action_category', 'action_category'),
        Index('idx_audit_logs_action_type', 'action_type'),
        Index('idx_audit_logs_risk_level', 'risk_level'),
        Index('idx_audit_logs_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_logs_compliance', 'compliance_categories'),
        {
            "schema": "platform",
            "postgresql_with": ["fillfactor=90"],  # Optimize for heavy writes
        }
    )
    
    # Primary identification
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Context - WHO, WHERE, WHEN
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    school_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    school_name = Column(String(255), nullable=False)  # Cached for performance
    
    # User identification
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("platform.unified_users.id"), nullable=False)
    user_email = Column(String(255), nullable=False)  # Cached for reports
    user_full_name = Column(String(200), nullable=False)  # Cached for reports
    user_role = Column(String(50), nullable=False)  # Role at time of action
    
    # Action classification - WHAT
    action_category = Column(String(50), nullable=False, index=True)
    action_type = Column(String(50), nullable=False, index=True)
    action_description = Column(String(500), nullable=False)  # Human-readable description
    
    # Risk and compliance
    risk_level = Column(String(20), nullable=False, default=RiskLevel.LOW.value, index=True)
    compliance_categories = Column(JSON, default=list)  # List of ComplianceCategory values
    
    # What was affected
    resource_type = Column(String(100), index=True)  # student, teacher, payment, etc.
    resource_id = Column(String(100), index=True)    # ID of affected resource
    resource_name = Column(String(255))              # Name/title of affected resource
    
    # Detailed information (JSON fields)
    action_context = Column(JSON, default=dict)      # ActionContext as JSON
    action_details = Column(JSON, default=dict)      # ActionDetails as JSON
    security_metadata = Column(JSON, default=dict)   # SecurityMetadata as JSON
    
    # Results and status
    success = Column(String(20), nullable=False, default="success")  # success, failure, partial
    error_message = Column(Text)                      # If action failed
    duration_ms = Column(Integer)                     # How long action took
    
    # Administrative fields
    correlation_id = Column(String(100))              # Link related actions
    parent_log_id = Column(PGUUID(as_uuid=True))     # For hierarchical actions
    batch_id = Column(String(100))                    # For bulk operations
    
    # Data retention and archival
    retention_until = Column(DateTime(timezone=True)) # When this log can be deleted
    archived = Column(String(20), default="active")   # active, archived, purged
    
    # Relationships
    user = relationship("UnifiedUser", foreign_keys=[user_id])
    
    # Properties
    @property
    def context(self) -> ActionContext:
        """Get action context as Pydantic model"""
        return ActionContext(**self.action_context or {})
    
    @property
    def details(self) -> ActionDetails:
        """Get action details as Pydantic model"""
        return ActionDetails(**self.action_details or {})
    
    @property
    def security(self) -> SecurityMetadata:
        """Get security metadata as Pydantic model"""
        return SecurityMetadata(**self.security_metadata or {})
    
    @property
    def is_high_risk(self) -> bool:
        """Check if action is high risk or critical"""
        return self.risk_level in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]
    
    @property
    def requires_retention(self) -> bool:
        """Check if log must be retained for compliance"""
        return self.retention_until is not None and self.retention_until > datetime.now(timezone.utc)
    
    @property
    def compliance_required(self) -> bool:
        """Check if action has compliance implications"""
        return bool(self.compliance_categories)
    
    def get_sensitive_data_redacted(self) -> Dict[str, Any]:
        """Get log data with sensitive information redacted"""
        log_dict = {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "school_name": self.school_name,
            "user_email": self._redact_email(self.user_email),
            "user_full_name": self._redact_name(self.user_full_name),
            "user_role": self.user_role,
            "action_category": self.action_category,
            "action_type": self.action_type,
            "action_description": self.action_description,
            "risk_level": self.risk_level,
            "resource_type": self.resource_type,
            "resource_name": self.resource_name,
            "success": self.success
        }
        return log_dict
    
    def _redact_email(self, email: str) -> str:
        """Redact email for privacy"""
        if not email or "@" not in email:
            return "[REDACTED]"
        local, domain = email.split("@", 1)
        return f"{local[:2]}***@{domain}"
    
    def _redact_name(self, name: str) -> str:
        """Redact name for privacy"""
        if not name:
            return "[REDACTED]"
        parts = name.split()
        if len(parts) == 1:
            return f"{parts[0][:2]}***"
        return f"{parts[0][:2]}*** {parts[-1][:2]}***"
    
    def __repr__(self):
        return f"<AuditLog(school='{self.school_name}', user='{self.user_email}', action='{self.action_type}', timestamp='{self.timestamp}')>"


# =====================================================
# AUDIT LOG SUMMARY MODEL
# =====================================================

class AuditLogSummary(Base):
    """
    Daily/hourly summaries of audit logs for performance and reporting
    Pre-computed aggregations to avoid heavy queries on main audit table
    """
    
    __tablename__ = "audit_log_summaries"
    __table_args__ = (
        Index('idx_audit_summaries_school_date', 'school_id', 'summary_date'),
        Index('idx_audit_summaries_category', 'action_category'),
        {
            "schema": "platform"
        }
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Summary scope
    school_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    school_name = Column(String(255), nullable=False)
    summary_date = Column(DateTime(timezone=True), nullable=False, index=True)
    summary_period = Column(String(20), nullable=False, default="daily")  # daily, hourly
    
    # Action summaries
    action_category = Column(String(50), nullable=False, index=True)
    total_actions = Column(Integer, nullable=False, default=0)
    successful_actions = Column(Integer, nullable=False, default=0)
    failed_actions = Column(Integer, nullable=False, default=0)
    
    # Risk summaries
    low_risk_count = Column(Integer, default=0)
    medium_risk_count = Column(Integer, default=0)
    high_risk_count = Column(Integer, default=0)
    critical_risk_count = Column(Integer, default=0)
    
    # User activity
    unique_users = Column(Integer, default=0)
    most_active_user = Column(String(255))
    most_active_user_actions = Column(Integer, default=0)
    
    # Performance metrics
    avg_action_duration_ms = Column(Integer)
    max_action_duration_ms = Column(Integer)
    min_action_duration_ms = Column(Integer)
    
    # Compliance tracking
    compliance_actions_count = Column(Integer, default=0)
    retention_required_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<AuditLogSummary(school='{self.school_name}', date='{self.summary_date}', category='{self.action_category}', total={self.total_actions})>"