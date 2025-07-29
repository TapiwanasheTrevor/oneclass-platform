"""
Migration Services Models
Professional data migration and care package management models
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, validator, EmailStr
from pydantic.types import PositiveInt, constr


class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    DATA_MIGRATION = "data_migration"
    SYSTEM_SETUP = "system_setup"
    TRAINING = "training"
    TESTING = "testing"
    GO_LIVE = "go_live"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentOption(str, Enum):
    """Payment option enumeration"""
    FULL_UPFRONT = "full_upfront"
    SPLIT = "split"
    EXTENDED = "extended"


class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    DEPOSIT_PAID = "deposit_paid"
    FULLY_PAID = "fully_paid"
    REFUNDED = "refunded"


class TaskStatus(str, Enum):
    """Task status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class TaskPriority(str, Enum):
    """Task priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class DataSourceType(str, Enum):
    """Data source type enumeration"""
    EXCEL = "excel"
    CSV = "csv"
    DATABASE = "database"
    PAPER = "paper"
    API = "api"


class DataSourceStatus(str, Enum):
    """Data source status enumeration"""
    RECEIVED = "received"
    ANALYZED = "analyzed"
    CLEANED = "cleaned"
    VALIDATED = "validated"
    IMPORTED = "imported"
    VERIFIED = "verified"


class CommunicationType(str, Enum):
    """Communication type enumeration"""
    EMAIL = "email"
    PHONE = "phone"
    MEETING = "meeting"
    SYSTEM = "system"


class CommunicationDirection(str, Enum):
    """Communication direction enumeration"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class PaymentType(str, Enum):
    """Payment type enumeration"""
    DEPOSIT = "deposit"
    MILESTONE = "milestone"
    FINAL = "final"
    REFUND = "refund"


class MilestoneStatus(str, Enum):
    """Milestone status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


# Base Models
class BaseModelWithTimestamps(BaseModel):
    """Base model with timestamp fields"""
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Care Package Models
class CarePackageBase(BaseModel):
    """Base care package model"""
    name: constr(max_length=50) = Field(..., description="Package name")
    price_usd: Decimal = Field(..., description="Price in USD")
    price_zwl: Decimal = Field(..., description="Price in ZWL")
    max_students: Optional[PositiveInt] = Field(None, description="Maximum students")
    max_historical_years: Optional[PositiveInt] = Field(None, description="Maximum historical years")
    features: Dict[str, Any] = Field(..., description="Package features")
    inclusions: List[str] = Field(..., description="What's included")
    exclusions: List[str] = Field(..., description="What's not included")
    estimated_duration_days: PositiveInt = Field(..., description="Estimated duration in days")
    is_active: bool = Field(True, description="Is package active")


class CarePackageCreate(CarePackageBase):
    """Create care package model"""
    pass


class CarePackageUpdate(BaseModel):
    """Update care package model"""
    name: Optional[constr(max_length=50)] = None
    price_usd: Optional[Decimal] = None
    price_zwl: Optional[Decimal] = None
    max_students: Optional[PositiveInt] = None
    max_historical_years: Optional[PositiveInt] = None
    features: Optional[Dict[str, Any]] = None
    inclusions: Optional[List[str]] = None
    exclusions: Optional[List[str]] = None
    estimated_duration_days: Optional[PositiveInt] = None
    is_active: Optional[bool] = None


class CarePackageResponse(CarePackageBase, BaseModelWithTimestamps):
    """Care package response model"""
    id: UUID


# Care Package Order Models
class CarePackageOrderBase(BaseModel):
    """Base care package order model"""
    school_id: UUID = Field(..., description="School ID")
    care_package_id: UUID = Field(..., description="Care package ID")
    requested_start_date: Optional[date] = Field(None, description="Requested start date")
    student_count: Optional[PositiveInt] = Field(None, description="Student count")
    current_system_type: Optional[str] = Field(None, description="Current system type")
    data_sources_description: Optional[str] = Field(None, description="Data sources description")
    special_requirements: Optional[str] = Field(None, description="Special requirements")
    custom_integrations_needed: Optional[List[str]] = Field(None, description="Custom integrations needed")
    
    # Additional options
    urgent_migration: bool = Field(False, description="Rush migration")
    onsite_training: bool = Field(False, description="On-site training")
    weekend_work: bool = Field(False, description="Weekend work")
    
    # Contact information
    primary_contact_name: Optional[constr(max_length=100)] = Field(None, description="Primary contact name")
    primary_contact_email: Optional[EmailStr] = Field(None, description="Primary contact email")
    primary_contact_phone: Optional[constr(max_length=20)] = Field(None, description="Primary contact phone")
    secondary_contact_name: Optional[constr(max_length=100)] = Field(None, description="Secondary contact name")
    secondary_contact_email: Optional[EmailStr] = Field(None, description="Secondary contact email")
    
    # Payment details
    payment_option: PaymentOption = Field(PaymentOption.SPLIT, description="Payment option")
    currency: str = Field("USD", description="Currency")


class CarePackageOrderCreate(CarePackageOrderBase):
    """Create care package order model"""
    pass


class CarePackageOrderUpdate(BaseModel):
    """Update care package order model"""
    status: Optional[OrderStatus] = None
    estimated_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    assigned_migration_manager: Optional[UUID] = None
    assigned_technical_lead: Optional[UUID] = None
    assigned_data_specialist: Optional[UUID] = None
    assigned_training_specialist: Optional[UUID] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    estimated_hours: Optional[PositiveInt] = None
    actual_hours: Optional[int] = Field(None, ge=0)
    payment_status: Optional[PaymentStatus] = None
    initial_assessment_notes: Optional[str] = None
    completion_notes: Optional[str] = None
    customer_feedback: Optional[str] = None
    internal_notes: Optional[str] = None


class CarePackageOrderResponse(CarePackageOrderBase, BaseModelWithTimestamps):
    """Care package order response model"""
    id: UUID
    order_number: str
    order_date: date
    status: OrderStatus
    package_price: Decimal
    additional_costs: Decimal
    total_price: Decimal
    payment_status: PaymentStatus
    progress_percentage: int
    estimated_hours: Optional[int] = None
    actual_hours: int
    estimated_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    
    # Team assignments
    assigned_migration_manager: Optional[UUID] = None
    assigned_technical_lead: Optional[UUID] = None
    assigned_data_specialist: Optional[UUID] = None
    assigned_training_specialist: Optional[UUID] = None
    
    # Notes
    initial_assessment_notes: Optional[str] = None
    completion_notes: Optional[str] = None
    customer_feedback: Optional[str] = None
    internal_notes: Optional[str] = None
    
    # Related objects
    care_package: Optional[CarePackageResponse] = None
    school_name: Optional[str] = None


# Migration Task Models
class MigrationTaskBase(BaseModel):
    """Base migration task model"""
    care_package_order_id: UUID = Field(..., description="Care package order ID")
    phase: str = Field(..., description="Project phase")
    task_name: constr(max_length=255) = Field(..., description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    assigned_to: Optional[UUID] = Field(None, description="Assigned user ID")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Task priority")
    estimated_hours: Optional[Decimal] = Field(None, description="Estimated hours")
    due_date: Optional[date] = Field(None, description="Due date")
    depends_on: Optional[UUID] = Field(None, description="Dependent task ID")
    task_notes: Optional[str] = Field(None, description="Task notes")


class MigrationTaskCreate(MigrationTaskBase):
    """Create migration task model"""
    pass


class MigrationTaskUpdate(BaseModel):
    """Update migration task model"""
    phase: Optional[str] = None
    task_name: Optional[constr(max_length=255)] = None
    description: Optional[str] = None
    assigned_to: Optional[UUID] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    estimated_hours: Optional[Decimal] = None
    actual_hours: Optional[Decimal] = None
    due_date: Optional[date] = None
    completion_date: Optional[date] = None
    depends_on: Optional[UUID] = None
    blocking_reason: Optional[str] = None
    task_notes: Optional[str] = None
    completion_notes: Optional[str] = None


class MigrationTaskResponse(MigrationTaskBase, BaseModelWithTimestamps):
    """Migration task response model"""
    id: UUID
    status: TaskStatus
    actual_hours: Decimal
    completion_date: Optional[date] = None
    blocking_reason: Optional[str] = None
    completion_notes: Optional[str] = None
    
    # Related objects
    assigned_user_name: Optional[str] = None


# Data Source Models
class DataSourceBase(BaseModel):
    """Base data source model"""
    care_package_order_id: UUID = Field(..., description="Care package order ID")
    source_name: constr(max_length=255) = Field(..., description="Source name")
    source_type: DataSourceType = Field(..., description="Source type")
    file_path: Optional[str] = Field(None, description="File path")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    record_count: Optional[PositiveInt] = Field(None, description="Record count")


class DataSourceCreate(DataSourceBase):
    """Create data source model"""
    pass


class DataSourceUpdate(BaseModel):
    """Update data source model"""
    status: Optional[DataSourceStatus] = None
    data_quality_score: Optional[int] = Field(None, ge=0, le=100)
    issues_found: Optional[List[str]] = None
    cleaning_notes: Optional[str] = None
    processed_at: Optional[datetime] = None
    processed_by: Optional[UUID] = None


class DataSourceResponse(DataSourceBase, BaseModelWithTimestamps):
    """Data source response model"""
    id: UUID
    status: DataSourceStatus
    data_quality_score: Optional[int] = None
    issues_found: Optional[List[str]] = None
    cleaning_notes: Optional[str] = None
    processed_at: Optional[datetime] = None
    processed_by: Optional[UUID] = None
    
    # Related objects
    processed_by_name: Optional[str] = None


# Communication Log Models
class CommunicationLogBase(BaseModel):
    """Base communication log model"""
    care_package_order_id: UUID = Field(..., description="Care package order ID")
    communication_type: CommunicationType = Field(..., description="Communication type")
    direction: CommunicationDirection = Field(..., description="Communication direction")
    subject: Optional[constr(max_length=255)] = Field(None, description="Subject")
    content: Optional[str] = Field(None, description="Content")
    participants: Optional[List[str]] = Field(None, description="Participants")


class CommunicationLogCreate(CommunicationLogBase):
    """Create communication log model"""
    pass


class CommunicationLogResponse(CommunicationLogBase, BaseModelWithTimestamps):
    """Communication log response model"""
    id: UUID
    created_by: Optional[UUID] = None
    
    # Related objects
    created_by_name: Optional[str] = None


# Payment Models
class PaymentBase(BaseModel):
    """Base payment model"""
    care_package_order_id: UUID = Field(..., description="Care package order ID")
    payment_type: PaymentType = Field(..., description="Payment type")
    amount: Decimal = Field(..., description="Payment amount")
    currency: str = Field("USD", description="Currency")
    payment_method: Optional[str] = Field(None, description="Payment method")
    reference_number: Optional[constr(max_length=100)] = Field(None, description="Reference number")
    due_date: Optional[date] = Field(None, description="Due date")
    notes: Optional[str] = Field(None, description="Payment notes")


class PaymentCreate(PaymentBase):
    """Create payment model"""
    pass


class PaymentUpdate(BaseModel):
    """Update payment model"""
    paid_date: Optional[date] = None
    status: Optional[PaymentStatus] = None
    notes: Optional[str] = None


class PaymentResponse(PaymentBase, BaseModelWithTimestamps):
    """Payment response model"""
    id: UUID
    paid_date: Optional[date] = None
    status: PaymentStatus


# Milestone Models
class MilestoneBase(BaseModel):
    """Base milestone model"""
    care_package_order_id: UUID = Field(..., description="Care package order ID")
    milestone_name: constr(max_length=255) = Field(..., description="Milestone name")
    description: Optional[str] = Field(None, description="Milestone description")
    sequence_order: PositiveInt = Field(..., description="Sequence order")
    planned_start_date: Optional[date] = Field(None, description="Planned start date")
    planned_end_date: Optional[date] = Field(None, description="Planned end date")
    deliverables: Optional[List[str]] = Field(None, description="Deliverables")
    acceptance_criteria: Optional[List[str]] = Field(None, description="Acceptance criteria")


class MilestoneCreate(MilestoneBase):
    """Create milestone model"""
    pass


class MilestoneUpdate(BaseModel):
    """Update milestone model"""
    milestone_name: Optional[constr(max_length=255)] = None
    description: Optional[str] = None
    sequence_order: Optional[PositiveInt] = None
    status: Optional[MilestoneStatus] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    deliverables: Optional[List[str]] = None
    acceptance_criteria: Optional[List[str]] = None
    completion_notes: Optional[str] = None


class MilestoneResponse(MilestoneBase, BaseModelWithTimestamps):
    """Milestone response model"""
    id: UUID
    status: MilestoneStatus
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    completion_notes: Optional[str] = None


# Team Performance Models
class TeamPerformanceBase(BaseModel):
    """Base team performance model"""
    user_id: UUID = Field(..., description="User ID")
    month_year: date = Field(..., description="Month/year")
    projects_assigned: int = Field(0, description="Projects assigned")
    projects_completed: int = Field(0, description="Projects completed")
    projects_delayed: int = Field(0, description="Projects delayed")
    billable_hours: Decimal = Field(0, description="Billable hours")
    utilization_percentage: Decimal = Field(0, description="Utilization percentage")
    customer_satisfaction_avg: Decimal = Field(0, description="Customer satisfaction average")
    on_time_delivery_rate: Decimal = Field(0, description="On-time delivery rate")
    overall_rating: Decimal = Field(0, description="Overall rating")


class TeamPerformanceCreate(TeamPerformanceBase):
    """Create team performance model"""
    pass


class TeamPerformanceUpdate(BaseModel):
    """Update team performance model"""
    projects_assigned: Optional[int] = None
    projects_completed: Optional[int] = None
    projects_delayed: Optional[int] = None
    billable_hours: Optional[Decimal] = None
    utilization_percentage: Optional[Decimal] = None
    customer_satisfaction_avg: Optional[Decimal] = None
    on_time_delivery_rate: Optional[Decimal] = None
    overall_rating: Optional[Decimal] = None


class TeamPerformanceResponse(TeamPerformanceBase, BaseModelWithTimestamps):
    """Team performance response model"""
    id: UUID
    
    # Related objects
    user_name: Optional[str] = None
    user_role: Optional[str] = None


# Dashboard Models
class MigrationServicesDashboard(BaseModel):
    """Migration services dashboard model"""
    active_projects: int
    monthly_revenue: Decimal
    team_utilization: Decimal
    success_rate: Decimal
    
    # Trends
    projects_trend: str
    revenue_trend: str
    utilization_trend: str
    success_rate_trend: str
    
    # Recent orders
    recent_orders: List[CarePackageOrderResponse]
    
    # Team performance
    team_performance: List[TeamPerformanceResponse]


class OrderFilters(BaseModel):
    """Order filters model"""
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    assigned_manager: Optional[UUID] = None
    package_type: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    school_name: Optional[str] = None


class OrderAnalytics(BaseModel):
    """Order analytics model"""
    total_orders: int
    total_revenue: Decimal
    average_order_value: Decimal
    completion_rate: Decimal
    average_delivery_time: int
    customer_satisfaction: Decimal
    
    # By package type
    package_breakdown: Dict[str, Dict[str, Any]]
    
    # Monthly trends
    monthly_trends: List[Dict[str, Any]]


# Validators
@validator('primary_contact_phone', 'secondary_contact_phone', pre=True, always=True)
def validate_zimbabwe_phone(cls, v):
    """Validate Zimbabwe phone number format"""
    if v and not v.startswith('+263'):
        raise ValueError('Phone number must be in Zimbabwe format (+263)')
    return v


# Export all models
__all__ = [
    # Enums
    "OrderStatus", "PaymentOption", "PaymentStatus", "TaskStatus", "TaskPriority",
    "DataSourceType", "DataSourceStatus", "CommunicationType", "CommunicationDirection",
    "PaymentType", "MilestoneStatus",
    
    # Base models
    "BaseModelWithTimestamps",
    
    # Care Package models
    "CarePackageBase", "CarePackageCreate", "CarePackageUpdate", "CarePackageResponse",
    
    # Order models
    "CarePackageOrderBase", "CarePackageOrderCreate", "CarePackageOrderUpdate", "CarePackageOrderResponse",
    
    # Task models
    "MigrationTaskBase", "MigrationTaskCreate", "MigrationTaskUpdate", "MigrationTaskResponse",
    
    # Data Source models
    "DataSourceBase", "DataSourceCreate", "DataSourceUpdate", "DataSourceResponse",
    
    # Communication models
    "CommunicationLogBase", "CommunicationLogCreate", "CommunicationLogResponse",
    
    # Payment models
    "PaymentBase", "PaymentCreate", "PaymentUpdate", "PaymentResponse",
    
    # Milestone models
    "MilestoneBase", "MilestoneCreate", "MilestoneUpdate", "MilestoneResponse",
    
    # Team Performance models
    "TeamPerformanceBase", "TeamPerformanceCreate", "TeamPerformanceUpdate", "TeamPerformanceResponse",
    
    # Dashboard models
    "MigrationServicesDashboard", "OrderFilters", "OrderAnalytics"
]