"""
Analytics Data Models
Database models for analytics and reporting data
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel
import uuid

Base = declarative_base()

class AnalyticsSnapshot(Base):
    """Daily/Weekly/Monthly analytics snapshots"""
    __tablename__ = "analytics_snapshots"
    __table_args__ = {"schema": "analytics"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Snapshot metadata
    snapshot_type = Column(String(20), nullable=False)  # daily, weekly, monthly, yearly
    snapshot_date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Student metrics
    total_students = Column(Integer, default=0)
    active_students = Column(Integer, default=0)
    new_enrollments = Column(Integer, default=0)
    withdrawals = Column(Integer, default=0)
    
    # Academic metrics
    average_attendance_rate = Column(Float, default=0.0)
    total_classes_held = Column(Integer, default=0)
    average_grade = Column(Float, default=0.0)
    pass_rate = Column(Float, default=0.0)
    
    # Financial metrics
    total_fees_collected = Column(Float, default=0.0)
    outstanding_fees = Column(Float, default=0.0)
    fee_collection_rate = Column(Float, default=0.0)
    
    # Staff metrics
    total_staff = Column(Integer, default=0)
    teacher_student_ratio = Column(Float, default=0.0)
    
    # System usage metrics
    total_logins = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    
    # Additional data (JSON)
    metrics_data = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ReportTemplate(Base):
    """Custom report templates"""
    __tablename__ = "report_templates"
    __table_args__ = {"schema": "analytics"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Template metadata
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100), nullable=False)  # academic, financial, administrative, custom
    
    # Template configuration
    report_type = Column(String(50), nullable=False)  # table, chart, dashboard, pdf
    data_sources = Column(JSON, nullable=False)  # List of data source configurations
    filters = Column(JSON, default={})  # Default filters
    columns = Column(JSON, default=[])  # Column configurations
    charts = Column(JSON, default=[])  # Chart configurations
    
    # Access control
    created_by = Column(UUID(as_uuid=True), nullable=False)
    is_public = Column(Boolean, default=False)
    allowed_roles = Column(JSON, default=[])
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ReportExecution(Base):
    """Report execution history and results"""
    __tablename__ = "report_executions"
    __table_args__ = {"schema": "analytics"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    template_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Execution metadata
    executed_by = Column(UUID(as_uuid=True), nullable=False)
    execution_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Parameters and filters used
    parameters = Column(JSON, default={})
    filters_applied = Column(JSON, default={})
    
    # Execution results
    status = Column(String(20), default='pending')  # pending, running, completed, failed
    execution_time_ms = Column(Integer)
    row_count = Column(Integer)
    file_path = Column(String(500))  # For saved reports
    
    # Error handling
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

# Pydantic models for API
class AnalyticsOverview(BaseModel):
    """Analytics overview response model"""
    school_id: str
    period: str
    start_date: datetime
    end_date: datetime
    
    # Student metrics
    total_students: int
    active_students: int
    new_enrollments: int
    student_growth_rate: float
    
    # Academic metrics
    average_attendance_rate: float
    academic_performance: Dict[str, float]
    
    # Financial metrics
    total_revenue: float
    collection_rate: float
    outstanding_amount: float
    
    # System metrics
    user_activity: Dict[str, int]
    
    # Trends and insights
    trends: Dict[str, Any]
    insights: List[Dict[str, str]]

class ReportTemplateCreate(BaseModel):
    """Report template creation model"""
    name: str
    description: Optional[str] = None
    category: str
    report_type: str
    data_sources: List[Dict[str, Any]]
    filters: Dict[str, Any] = {}
    columns: List[Dict[str, Any]] = []
    charts: List[Dict[str, Any]] = []
    is_public: bool = False
    allowed_roles: List[str] = []

class ReportTemplateResponse(BaseModel):
    """Report template response model"""
    id: str
    name: str
    description: Optional[str]
    category: str
    report_type: str
    is_public: bool
    created_by: str
    created_at: datetime
    updated_at: datetime

class ReportExecutionRequest(BaseModel):
    """Report execution request model"""
    template_id: str
    parameters: Dict[str, Any] = {}
    filters: Dict[str, Any] = {}
    output_format: str = "json"  # json, csv, pdf, excel

class ReportExecutionResponse(BaseModel):
    """Report execution response model"""
    id: str
    template_id: str
    status: str
    execution_date: datetime
    parameters: Dict[str, Any]
    row_count: Optional[int]
    file_path: Optional[str]
    download_url: Optional[str]

class DashboardWidget(BaseModel):
    """Dashboard widget configuration"""
    id: str
    type: str  # chart, metric, table, text
    title: str
    data_source: str
    configuration: Dict[str, Any]
    position: Dict[str, int]  # x, y, width, height
    refresh_interval: int = 300  # seconds

class Dashboard(BaseModel):
    """Dashboard configuration"""
    id: str
    name: str
    description: Optional[str]
    widgets: List[DashboardWidget]
    layout: str = "grid"
    is_public: bool = False
    created_by: str
    created_at: datetime