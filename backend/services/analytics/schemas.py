"""
Analytics API Schemas
Pydantic models for API request/response validation
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, date
from enum import Enum

class PeriodType(str, Enum):
    """Analytics period types"""
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"
    custom = "custom"

class MetricType(str, Enum):
    """Available metric types"""
    student_enrollment = "student_enrollment"
    attendance = "attendance"
    academic_performance = "academic_performance"
    financial = "financial"
    staff = "staff"
    system_usage = "system_usage"

class ChartType(str, Enum):
    """Chart types for visualizations"""
    line = "line"
    bar = "bar"
    pie = "pie"
    doughnut = "doughnut"
    area = "area"
    scatter = "scatter"
    table = "table"
    metric = "metric"

# Request schemas
class AnalyticsRequest(BaseModel):
    """Base analytics request"""
    period: PeriodType = PeriodType.monthly
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    metrics: List[MetricType] = []
    
    @validator('end_date')
    def end_date_after_start_date(cls, v, values):
        if v and values.get('start_date') and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

class DashboardRequest(BaseModel):
    """Dashboard data request"""
    period: PeriodType = PeriodType.monthly
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    widgets: List[str] = []  # Widget IDs to include

class StudentAnalyticsRequest(BaseModel):
    """Student analytics request"""
    period: PeriodType = PeriodType.monthly
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    grade_levels: List[str] = []
    classes: List[str] = []
    include_demographics: bool = False

class AcademicAnalyticsRequest(BaseModel):
    """Academic performance analytics request"""
    period: PeriodType = PeriodType.monthly
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    subjects: List[str] = []
    assessment_types: List[str] = []
    grade_levels: List[str] = []

class FinancialAnalyticsRequest(BaseModel):
    """Financial analytics request"""
    period: PeriodType = PeriodType.monthly
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    fee_types: List[str] = []
    payment_methods: List[str] = []

# Response schemas
class MetricValue(BaseModel):
    """Individual metric value"""
    value: Union[int, float, str]
    previous_value: Optional[Union[int, float, str]] = None
    change: Optional[float] = None
    change_percentage: Optional[float] = None
    trend: Optional[str] = None  # up, down, stable
    format: str = "number"  # number, percentage, currency, text

class TimeSeriesDataPoint(BaseModel):
    """Time series data point"""
    date: date
    value: Union[int, float]
    label: Optional[str] = None

class ChartData(BaseModel):
    """Chart data structure"""
    type: ChartType
    title: str
    data: List[TimeSeriesDataPoint]
    labels: List[str] = []
    datasets: List[Dict[str, Any]] = []
    options: Dict[str, Any] = {}

class StudentMetrics(BaseModel):
    """Student-related metrics"""
    total_students: MetricValue
    active_students: MetricValue
    new_enrollments: MetricValue
    withdrawals: MetricValue
    attendance_rate: MetricValue
    enrollment_trend: ChartData
    demographics: Optional[Dict[str, Any]] = None

class AcademicMetrics(BaseModel):
    """Academic performance metrics"""
    average_grade: MetricValue
    pass_rate: MetricValue
    attendance_rate: MetricValue
    assignment_completion: MetricValue
    grade_distribution: ChartData
    subject_performance: ChartData
    trends: List[ChartData] = []

class FinancialMetrics(BaseModel):
    """Financial metrics"""
    total_revenue: MetricValue
    fees_collected: MetricValue
    outstanding_fees: MetricValue
    collection_rate: MetricValue
    revenue_trend: ChartData
    fee_breakdown: ChartData
    payment_methods: ChartData

class SystemMetrics(BaseModel):
    """System usage metrics"""
    total_users: MetricValue
    active_users: MetricValue
    daily_logins: MetricValue
    feature_usage: Dict[str, MetricValue]
    usage_trends: List[ChartData] = []

class AnalyticsOverviewResponse(BaseModel):
    """Complete analytics overview"""
    school_id: str
    period: PeriodType
    start_date: date
    end_date: date
    generated_at: datetime
    
    student_metrics: StudentMetrics
    academic_metrics: AcademicMetrics
    financial_metrics: FinancialMetrics
    system_metrics: SystemMetrics
    
    insights: List[Dict[str, str]] = []
    recommendations: List[Dict[str, str]] = []

class DashboardResponse(BaseModel):
    """Dashboard response"""
    dashboard_id: str
    name: str
    description: Optional[str]
    widgets: List[Dict[str, Any]]
    last_updated: datetime

# Report schemas
class ReportColumn(BaseModel):
    """Report column configuration"""
    field: str
    title: str
    type: str = "text"  # text, number, date, currency, percentage
    width: Optional[int] = None
    sortable: bool = True
    filterable: bool = True
    aggregation: Optional[str] = None  # sum, avg, count, min, max

class ReportFilter(BaseModel):
    """Report filter configuration"""
    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, in, like
    value: Any
    label: Optional[str] = None

class CustomReportRequest(BaseModel):
    """Custom report generation request"""
    name: str
    description: Optional[str] = None
    data_source: str
    columns: List[ReportColumn]
    filters: List[ReportFilter] = []
    sort_by: Optional[str] = None
    sort_order: str = "asc"
    limit: Optional[int] = None
    export_format: str = "json"  # json, csv, excel, pdf

class ReportDataResponse(BaseModel):
    """Report data response"""
    columns: List[ReportColumn]
    data: List[Dict[str, Any]]
    total_rows: int
    page: int = 1
    page_size: int = 100
    filters_applied: List[ReportFilter] = []

# Comparison schemas
class ComparisonRequest(BaseModel):
    """Analytics comparison request"""
    base_period: PeriodType
    base_start_date: date
    base_end_date: date
    compare_period: PeriodType
    compare_start_date: date
    compare_end_date: date
    metrics: List[MetricType]

class ComparisonResponse(BaseModel):
    """Analytics comparison response"""
    base_period: Dict[str, Any]
    compare_period: Dict[str, Any]
    changes: Dict[str, MetricValue]
    insights: List[str] = []

# Export schemas
class ExportRequest(BaseModel):
    """Data export request"""
    report_id: Optional[str] = None
    data_source: str
    format: str = "csv"  # csv, excel, pdf
    filters: Dict[str, Any] = {}
    columns: List[str] = []
    
class ExportResponse(BaseModel):
    """Export response"""
    export_id: str
    status: str  # queued, processing, completed, failed
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime

# Report Template schemas (for API routes)
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