# =====================================================
# Finance Module - Pydantic Models and Schemas
# File: backend/services/finance/schemas.py
# =====================================================

from pydantic import BaseModel, Field, EmailStr, validator, root_validator
from typing import List, Optional, Dict, Any, Union
from datetime import date, datetime, time
from enum import Enum
from uuid import UUID
from decimal import Decimal
import re

# =====================================================
# ENUMS FOR VALIDATION
# =====================================================

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentMethodType(str, Enum):
    CASH = "cash"
    MOBILE_MONEY = "mobile_money"
    BANK_TRANSFER = "bank_transfer"
    ONLINE = "online"
    CARD = "card"

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentFrequency(str, Enum):
    TERM = "term"
    ANNUAL = "annual"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ONE_TIME = "one_time"

class FeeStructureStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

class Currency(str, Enum):
    USD = "USD"
    ZWL = "ZWL"
    ZAR = "ZAR"
    GBP = "GBP"

class RefundType(str, Enum):
    PAYMENT_REVERSAL = "payment_reversal"
    OVERPAYMENT = "overpayment"
    WITHDRAWAL = "withdrawal"
    ADJUSTMENT = "adjustment"

class PaymentPlanStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DEFAULTED = "defaulted"
    CANCELLED = "cancelled"

class InstallmentFrequency(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"

# =====================================================
# SHARED/COMMON SCHEMAS
# =====================================================

class MoneyAmount(BaseModel):
    """Standard money amount with currency"""
    amount: Decimal = Field(..., decimal_places=2, description="Amount in decimal format")
    currency: Currency = Field(default=Currency.USD, description="Currency code")
    
    @validator('amount')
    def validate_amount(cls, v):
        if v < 0:
            raise ValueError('Amount cannot be negative')
        if v > Decimal('999999999.99'):
            raise ValueError('Amount too large')
        return v

class ZimbabwePhoneNumber(BaseModel):
    """Zimbabwe phone number validation"""
    phone: str = Field(..., description="Phone number")
    
    @validator('phone')
    def validate_zimbabwe_phone(cls, v):
        if not v:
            return v
        # Zimbabwe phone number validation: +263 or 0 followed by area code and number
        pattern = r'^(\+263|0)[0-9]{9}$'
        if not re.match(pattern, v.replace(' ', '').replace('-', '')):
            raise ValueError('Invalid Zimbabwe phone number format. Use +263XXXXXXXXX or 0XXXXXXXXX')
        return v

class PaynowConfig(BaseModel):
    """Paynow integration configuration"""
    integration_id: str = Field(..., description="Paynow integration ID")
    integration_key: str = Field(..., description="Paynow integration key")
    return_url: str = Field(..., description="Return URL after payment")
    result_url: str = Field(..., description="Result URL for webhook")
    
    @validator('integration_id', 'integration_key')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

# =====================================================
# FEE MANAGEMENT SCHEMAS
# =====================================================

class FeeCategoryBase(BaseModel):
    """Base fee category information"""
    name: str = Field(..., min_length=2, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=500, description="Category description")
    code: str = Field(..., min_length=2, max_length=20, description="Category code")
    is_mandatory: bool = Field(default=True, description="Is this category mandatory")
    is_refundable: bool = Field(default=False, description="Is this category refundable")
    allows_partial_payment: bool = Field(default=True, description="Allows partial payments")
    display_order: int = Field(default=1, ge=1, le=100, description="Display order")
    is_active: bool = Field(default=True, description="Is category active")

class FeeCategoryCreate(FeeCategoryBase):
    """Schema for creating fee category"""
    pass

class FeeCategoryUpdate(BaseModel):
    """Schema for updating fee category"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_mandatory: Optional[bool] = None
    is_refundable: Optional[bool] = None
    allows_partial_payment: Optional[bool] = None
    display_order: Optional[int] = Field(None, ge=1, le=100)
    is_active: Optional[bool] = None

class FeeCategoryResponse(FeeCategoryBase):
    """Fee category response"""
    id: UUID
    school_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class FeeStructureBase(BaseModel):
    """Base fee structure information"""
    name: str = Field(..., min_length=2, max_length=200, description="Structure name")
    description: Optional[str] = Field(None, max_length=1000, description="Structure description")
    academic_year_id: UUID = Field(..., description="Academic year ID")
    grade_levels: List[int] = Field(..., min_items=1, description="Applicable grade levels")
    class_ids: Optional[List[UUID]] = Field(None, description="Specific class IDs")
    is_default: bool = Field(default=False, description="Default structure for new students")
    applicable_from: date = Field(default_factory=date.today, description="Applicable from date")
    applicable_to: Optional[date] = Field(None, description="Applicable to date")
    status: FeeStructureStatus = Field(default=FeeStructureStatus.DRAFT, description="Structure status")
    
    @validator('grade_levels')
    def validate_grade_levels(cls, v):
        if not v:
            raise ValueError('At least one grade level must be specified')
        for level in v:
            if level < 1 or level > 13:
                raise ValueError(f'Invalid grade level: {level}. Must be between 1 and 13')
        return sorted(list(set(v)))  # Remove duplicates and sort
    
    @validator('applicable_to')
    def validate_applicable_dates(cls, v, values):
        if v and 'applicable_from' in values:
            if v <= values['applicable_from']:
                raise ValueError('Applicable to date must be after applicable from date')
        return v

class FeeStructureCreate(FeeStructureBase):
    """Schema for creating fee structure"""
    pass

class FeeStructureUpdate(BaseModel):
    """Schema for updating fee structure"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    grade_levels: Optional[List[int]] = None
    class_ids: Optional[List[UUID]] = None
    is_default: Optional[bool] = None
    applicable_from: Optional[date] = None
    applicable_to: Optional[date] = None
    status: Optional[FeeStructureStatus] = None

class FeeStructureResponse(FeeStructureBase):
    """Fee structure response"""
    id: UUID
    school_id: UUID
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class FeeItemBase(BaseModel):
    """Base fee item information"""
    name: str = Field(..., min_length=2, max_length=200, description="Item name")
    description: Optional[str] = Field(None, max_length=1000, description="Item description")
    base_amount: Decimal = Field(..., decimal_places=2, ge=0, description="Base amount")
    currency: Currency = Field(default=Currency.USD, description="Currency")
    frequency: PaymentFrequency = Field(default=PaymentFrequency.TERM, description="Payment frequency")
    due_date_offset_days: int = Field(default=0, ge=0, le=365, description="Due date offset in days")
    allows_installments: bool = Field(default=False, description="Allows installments")
    max_installments: int = Field(default=1, ge=1, le=12, description="Maximum installments")
    installment_interval_days: int = Field(default=30, ge=1, le=365, description="Installment interval")
    late_fee_amount: Decimal = Field(default=Decimal('0.00'), decimal_places=2, ge=0, description="Late fee amount")
    late_fee_grace_days: int = Field(default=7, ge=0, le=90, description="Late fee grace period")
    daily_penalty_rate: Decimal = Field(default=Decimal('0.0000'), decimal_places=4, ge=0, le=1, description="Daily penalty rate")
    
    @validator('max_installments')
    def validate_installments(cls, v, values):
        if 'allows_installments' in values and values['allows_installments'] and v <= 1:
            raise ValueError('Max installments must be greater than 1 when installments are allowed')
        elif 'allows_installments' in values and not values['allows_installments'] and v > 1:
            raise ValueError('Max installments must be 1 when installments are not allowed')
        return v

class FeeItemCreate(FeeItemBase):
    """Schema for creating fee item"""
    fee_category_id: UUID = Field(..., description="Fee category ID")

class FeeItemUpdate(BaseModel):
    """Schema for updating fee item"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    base_amount: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    currency: Optional[Currency] = None
    frequency: Optional[PaymentFrequency] = None
    due_date_offset_days: Optional[int] = Field(None, ge=0, le=365)
    allows_installments: Optional[bool] = None
    max_installments: Optional[int] = Field(None, ge=1, le=12)
    installment_interval_days: Optional[int] = Field(None, ge=1, le=365)
    late_fee_amount: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    late_fee_grace_days: Optional[int] = Field(None, ge=0, le=90)
    daily_penalty_rate: Optional[Decimal] = Field(None, decimal_places=4, ge=0, le=1)

class FeeItemResponse(FeeItemBase):
    """Fee item response"""
    id: UUID
    fee_structure_id: UUID
    fee_category_id: UUID
    fee_category: Optional[FeeCategoryResponse]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class StudentFeeAssignmentBase(BaseModel):
    """Base student fee assignment"""
    effective_from: date = Field(default_factory=date.today, description="Effective from date")
    effective_to: Optional[date] = Field(None, description="Effective to date")
    discount_percentage: Decimal = Field(default=Decimal('0.00'), decimal_places=2, ge=0, le=100, description="Discount percentage")
    discount_amount: Decimal = Field(default=Decimal('0.00'), decimal_places=2, ge=0, description="Discount amount")
    discount_reason: Optional[str] = Field(None, max_length=500, description="Discount reason")
    status: str = Field(default="active", pattern=r'^(active|suspended|cancelled)$', description="Assignment status")
    
    @validator('effective_to')
    def validate_effective_dates(cls, v, values):
        if v and 'effective_from' in values:
            if v <= values['effective_from']:
                raise ValueError('Effective to date must be after effective from date')
        return v
    
    @root_validator
    def validate_discount(cls, values):
        discount_percentage = values.get('discount_percentage', Decimal('0.00'))
        discount_amount = values.get('discount_amount', Decimal('0.00'))
        
        if discount_percentage > 0 and discount_amount > 0:
            raise ValueError('Cannot have both percentage and amount discount')
        
        return values

class StudentFeeAssignmentCreate(StudentFeeAssignmentBase):
    """Schema for creating student fee assignment"""
    student_id: UUID = Field(..., description="Student ID")
    fee_structure_id: UUID = Field(..., description="Fee structure ID")

class StudentFeeAssignmentUpdate(BaseModel):
    """Schema for updating student fee assignment"""
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    discount_percentage: Optional[Decimal] = Field(None, decimal_places=2, ge=0, le=100)
    discount_amount: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    discount_reason: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, pattern=r'^(active|suspended|cancelled)$')

class StudentFeeAssignmentResponse(StudentFeeAssignmentBase):
    """Student fee assignment response"""
    id: UUID
    student_id: UUID
    fee_structure_id: UUID
    fee_structure: Optional[FeeStructureResponse]
    assigned_by: UUID
    assigned_date: date
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# =====================================================
# INVOICE SCHEMAS
# =====================================================

class InvoiceBase(BaseModel):
    """Base invoice information"""
    due_date: date = Field(..., description="Invoice due date")
    academic_year_id: UUID = Field(..., description="Academic year ID")
    term_id: Optional[UUID] = Field(None, description="Term ID")
    currency: Currency = Field(default=Currency.USD, description="Invoice currency")
    exchange_rate: Decimal = Field(default=Decimal('1.0000'), decimal_places=4, gt=0, description="Exchange rate")
    notes: Optional[str] = Field(None, max_length=1000, description="Invoice notes")
    
    @validator('due_date')
    def validate_due_date(cls, v):
        if v < date.today():
            raise ValueError('Due date cannot be in the past')
        return v

class InvoiceCreate(InvoiceBase):
    """Schema for creating invoice"""
    student_id: UUID = Field(..., description="Student ID")
    fee_structure_id: UUID = Field(..., description="Fee structure ID to generate from")

class InvoiceUpdate(BaseModel):
    """Schema for updating invoice"""
    due_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=1000)
    status: Optional[InvoiceStatus] = None

class InvoiceLineItemBase(BaseModel):
    """Base invoice line item"""
    description: str = Field(..., min_length=1, max_length=500, description="Item description")
    quantity: Decimal = Field(default=Decimal('1.00'), decimal_places=2, gt=0, description="Quantity")
    unit_price: Decimal = Field(..., decimal_places=2, ge=0, description="Unit price")
    discount_percentage: Decimal = Field(default=Decimal('0.00'), decimal_places=2, ge=0, le=100, description="Discount percentage")
    discount_amount: Decimal = Field(default=Decimal('0.00'), decimal_places=2, ge=0, description="Discount amount")
    
    @root_validator
    def validate_discount(cls, values):
        discount_percentage = values.get('discount_percentage', Decimal('0.00'))
        discount_amount = values.get('discount_amount', Decimal('0.00'))
        
        if discount_percentage > 0 and discount_amount > 0:
            raise ValueError('Cannot have both percentage and amount discount')
        
        return values

class InvoiceLineItemCreate(InvoiceLineItemBase):
    """Schema for creating invoice line item"""
    fee_item_id: UUID = Field(..., description="Fee item ID")

class InvoiceLineItemResponse(InvoiceLineItemBase):
    """Invoice line item response"""
    id: UUID
    invoice_id: UUID
    fee_item_id: UUID
    line_total: Decimal
    created_at: datetime
    
    class Config:
        orm_mode = True

class InvoiceResponse(InvoiceBase):
    """Invoice response"""
    id: UUID
    school_id: UUID
    student_id: UUID
    invoice_number: str
    invoice_date: date
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    outstanding_amount: Decimal
    payment_status: str
    late_fee_amount: Decimal
    penalty_amount: Decimal
    sent_to_parent: bool
    sent_date: Optional[datetime]
    reminder_count: int
    last_reminder_date: Optional[datetime]
    status: InvoiceStatus
    line_items: List[InvoiceLineItemResponse] = []
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class BulkInvoiceGenerationRequest(BaseModel):
    """Schema for bulk invoice generation"""
    fee_structure_id: UUID = Field(..., description="Fee structure ID")
    student_ids: Optional[List[UUID]] = Field(None, description="Specific student IDs (optional)")
    grade_levels: Optional[List[int]] = Field(None, description="Specific grade levels (optional)")
    class_ids: Optional[List[UUID]] = Field(None, description="Specific class IDs (optional)")
    due_date: date = Field(..., description="Invoice due date")
    academic_year_id: UUID = Field(..., description="Academic year ID")
    term_id: Optional[UUID] = Field(None, description="Term ID")
    
    @validator('due_date')
    def validate_due_date(cls, v):
        if v < date.today():
            raise ValueError('Due date cannot be in the past')
        return v
    
    @root_validator
    def validate_criteria(cls, values):
        student_ids = values.get('student_ids')
        grade_levels = values.get('grade_levels')
        class_ids = values.get('class_ids')
        
        if not any([student_ids, grade_levels, class_ids]):
            raise ValueError('At least one selection criteria must be provided')
        
        return values

class BulkInvoiceGenerationResponse(BaseModel):
    """Bulk invoice generation response"""
    total_invoices_generated: int
    total_students_processed: int
    total_amount: Decimal
    failed_students: List[Dict[str, str]] = []
    invoice_ids: List[UUID] = []

# =====================================================
# PAYMENT SCHEMAS
# =====================================================

class PaymentMethodBase(BaseModel):
    """Base payment method"""
    name: str = Field(..., min_length=2, max_length=100, description="Payment method name")
    code: str = Field(..., min_length=2, max_length=20, description="Payment method code")
    type: PaymentMethodType = Field(..., description="Payment method type")
    is_active: bool = Field(default=True, description="Is payment method active")
    requires_reference: bool = Field(default=False, description="Requires reference number")
    supports_partial_payment: bool = Field(default=True, description="Supports partial payments")
    transaction_fee_percentage: Decimal = Field(default=Decimal('0.00'), decimal_places=2, ge=0, le=100, description="Transaction fee percentage")
    transaction_fee_fixed: Decimal = Field(default=Decimal('0.00'), decimal_places=2, ge=0, description="Fixed transaction fee")
    display_order: int = Field(default=1, ge=1, le=100, description="Display order")
    icon_url: Optional[str] = Field(None, description="Icon URL")
    
    @validator('code')
    def validate_code(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError('Code must be alphanumeric (underscores allowed)')
        return v.upper()

class PaymentMethodCreate(PaymentMethodBase):
    """Schema for creating payment method"""
    gateway_config: Optional[Dict[str, Any]] = Field(None, description="Gateway configuration")

class PaymentMethodUpdate(BaseModel):
    """Schema for updating payment method"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    is_active: Optional[bool] = None
    requires_reference: Optional[bool] = None
    supports_partial_payment: Optional[bool] = None
    transaction_fee_percentage: Optional[Decimal] = Field(None, decimal_places=2, ge=0, le=100)
    transaction_fee_fixed: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    display_order: Optional[int] = Field(None, ge=1, le=100)
    icon_url: Optional[str] = None
    gateway_config: Optional[Dict[str, Any]] = None

class PaymentMethodResponse(PaymentMethodBase):
    """Payment method response"""
    id: UUID
    school_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class PaymentBase(BaseModel):
    """Base payment information"""
    amount: Decimal = Field(..., decimal_places=2, gt=0, description="Payment amount")
    currency: Currency = Field(default=Currency.USD, description="Payment currency")
    exchange_rate: Decimal = Field(default=Decimal('1.0000'), decimal_places=4, gt=0, description="Exchange rate")
    payer_name: Optional[str] = Field(None, max_length=200, description="Payer name")
    payer_email: Optional[EmailStr] = Field(None, description="Payer email")
    payer_phone: Optional[str] = Field(None, description="Payer phone")
    notes: Optional[str] = Field(None, max_length=1000, description="Payment notes")
    
    @validator('payer_phone')
    def validate_phone(cls, v):
        if v:
            # Zimbabwe phone number validation
            pattern = r'^(\+263|0)[0-9]{9}$'
            if not re.match(pattern, v.replace(' ', '').replace('-', '')):
                raise ValueError('Invalid Zimbabwe phone number format')
        return v

class PaymentCreate(PaymentBase):
    """Schema for creating payment"""
    student_id: UUID = Field(..., description="Student ID")
    payment_method_id: UUID = Field(..., description="Payment method ID")
    transaction_id: Optional[str] = Field(None, max_length=200, description="External transaction ID")
    gateway_reference: Optional[str] = Field(None, max_length=200, description="Gateway reference")

class PaymentUpdate(BaseModel):
    """Schema for updating payment"""
    status: Optional[PaymentStatus] = None
    transaction_id: Optional[str] = Field(None, max_length=200)
    gateway_reference: Optional[str] = Field(None, max_length=200)
    failure_reason: Optional[str] = Field(None, max_length=1000)
    notes: Optional[str] = Field(None, max_length=1000)
    reconciled: Optional[bool] = None

class PaymentResponse(PaymentBase):
    """Payment response"""
    id: UUID
    school_id: UUID
    student_id: UUID
    payment_reference: str
    payment_date: date
    payment_method_id: UUID
    payment_method: Optional[PaymentMethodResponse]
    transaction_id: Optional[str]
    gateway_reference: Optional[str]
    status: PaymentStatus
    gateway_response: Optional[Dict[str, Any]]
    failure_reason: Optional[str]
    reconciled: bool
    reconciled_at: Optional[datetime]
    reconciled_by: Optional[UUID]
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class PaymentAllocationBase(BaseModel):
    """Base payment allocation"""
    allocated_amount: Decimal = Field(..., decimal_places=2, gt=0, description="Allocated amount")
    allocation_date: date = Field(default_factory=date.today, description="Allocation date")

class PaymentAllocationCreate(PaymentAllocationBase):
    """Schema for creating payment allocation"""
    payment_id: UUID = Field(..., description="Payment ID")
    invoice_id: UUID = Field(..., description="Invoice ID")

class PaymentAllocationResponse(PaymentAllocationBase):
    """Payment allocation response"""
    id: UUID
    payment_id: UUID
    invoice_id: UUID
    created_at: datetime
    
    class Config:
        orm_mode = True

# =====================================================
# PAYNOW INTEGRATION SCHEMAS
# =====================================================

class PaynowPaymentRequest(BaseModel):
    """Paynow payment initiation request"""
    student_id: UUID = Field(..., description="Student ID")
    invoice_ids: List[UUID] = Field(..., min_items=1, description="Invoice IDs to pay")
    amount: Decimal = Field(..., decimal_places=2, gt=0, description="Total amount")
    payer_email: EmailStr = Field(..., description="Payer email")
    payer_phone: str = Field(..., description="Payer phone")
    
    @validator('payer_phone')
    def validate_phone(cls, v):
        # Zimbabwe phone number validation
        pattern = r'^(\+263|0)[0-9]{9}$'
        if not re.match(pattern, v.replace(' ', '').replace('-', '')):
            raise ValueError('Invalid Zimbabwe phone number format')
        return v

class PaynowPaymentResponse(BaseModel):
    """Paynow payment response"""
    payment_id: UUID
    paynow_reference: str
    poll_url: str
    redirect_url: str
    status: str
    success: bool
    hash_valid: bool

class PaynowStatusResponse(BaseModel):
    """Paynow status check response"""
    payment_id: UUID
    status: PaymentStatus
    paynow_reference: str
    amount: Decimal
    success: bool
    hash_valid: bool
    message: str

# =====================================================
# FINANCIAL REPORTING SCHEMAS
# =====================================================

class FinancialSummaryBase(BaseModel):
    """Base financial summary"""
    summary_date: date = Field(..., description="Summary date")
    summary_type: str = Field(..., pattern=r'^(daily|weekly|monthly|quarterly|annual)$', description="Summary type")
    academic_year_id: Optional[UUID] = Field(None, description="Academic year ID")
    total_invoiced: Decimal = Field(default=Decimal('0.00'), decimal_places=2, ge=0, description="Total invoiced")
    total_collected: Decimal = Field(default=Decimal('0.00'), decimal_places=2, ge=0, description="Total collected")
    total_outstanding: Decimal = Field(default=Decimal('0.00'), decimal_places=2, ge=0, description="Total outstanding")
    total_overdue: Decimal = Field(default=Decimal('0.00'), decimal_places=2, ge=0, description="Total overdue")
    collection_rate: Decimal = Field(default=Decimal('0.00'), decimal_places=2, ge=0, le=100, description="Collection rate")
    average_payment_time_days: int = Field(default=0, ge=0, description="Average payment time")
    students_with_outstanding: int = Field(default=0, ge=0, description="Students with outstanding fees")
    students_fully_paid: int = Field(default=0, ge=0, description="Students fully paid")

class FinancialSummaryResponse(FinancialSummaryBase):
    """Financial summary response"""
    id: UUID
    school_id: UUID
    calculated_at: datetime
    
    class Config:
        orm_mode = True

class FinanceDashboardResponse(BaseModel):
    """Finance dashboard response"""
    school_id: UUID
    academic_year_id: UUID
    
    # Current term summary
    current_term_invoiced: Decimal
    current_term_collected: Decimal
    current_term_outstanding: Decimal
    current_term_collection_rate: Decimal
    
    # Academic year summary
    year_to_date_invoiced: Decimal
    year_to_date_collected: Decimal
    year_to_date_outstanding: Decimal
    year_to_date_collection_rate: Decimal
    
    # Recent activity
    recent_payments: List[PaymentResponse]
    overdue_invoices_count: int
    pending_payments_count: int
    
    # Charts data
    monthly_collection_trend: List[Dict[str, Any]]
    payment_method_breakdown: List[Dict[str, Any]]
    fee_category_breakdown: List[Dict[str, Any]]

class CollectionReportRequest(BaseModel):
    """Collection report request"""
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    grade_levels: Optional[List[int]] = Field(None, description="Grade levels filter")
    class_ids: Optional[List[UUID]] = Field(None, description="Class IDs filter")
    fee_categories: Optional[List[UUID]] = Field(None, description="Fee category IDs filter")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('End date must be after start date')
        return v

class CollectionReportResponse(BaseModel):
    """Collection report response"""
    report_period: str
    total_students: int
    total_invoiced: Decimal
    total_collected: Decimal
    total_outstanding: Decimal
    collection_rate: Decimal
    
    # Breakdown by categories
    category_breakdown: List[Dict[str, Any]]
    
    # Payment method breakdown
    payment_method_breakdown: List[Dict[str, Any]]
    
    # Grade level breakdown
    grade_level_breakdown: List[Dict[str, Any]]
    
    # Top outstanding students
    top_outstanding_students: List[Dict[str, Any]]

# =====================================================
# SEARCH AND FILTER SCHEMAS
# =====================================================

class InvoiceSearchFilters(BaseModel):
    """Invoice search filters"""
    student_id: Optional[UUID] = None
    grade_level: Optional[int] = Field(None, ge=1, le=13)
    class_id: Optional[UUID] = None
    payment_status: Optional[str] = Field(None, pattern=r'^(pending|partial|paid|overdue)$')
    academic_year_id: Optional[UUID] = None
    term_id: Optional[UUID] = None
    due_date_from: Optional[date] = None
    due_date_to: Optional[date] = None
    amount_min: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    amount_max: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    
    @validator('due_date_to')
    def validate_date_range(cls, v, values):
        if v and 'due_date_from' in values and values['due_date_from'] and v < values['due_date_from']:
            raise ValueError('Due date to must be after due date from')
        return v

class PaymentSearchFilters(BaseModel):
    """Payment search filters"""
    student_id: Optional[UUID] = None
    payment_method_id: Optional[UUID] = None
    status: Optional[PaymentStatus] = None
    payment_date_from: Optional[date] = None
    payment_date_to: Optional[date] = None
    amount_min: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    amount_max: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    reconciled: Optional[bool] = None
    
    @validator('payment_date_to')
    def validate_date_range(cls, v, values):
        if v and 'payment_date_from' in values and values['payment_date_from'] and v < values['payment_date_from']:
            raise ValueError('Payment date to must be after payment date from')
        return v

class FinanceSearchRequest(BaseModel):
    """Finance search request"""
    search_query: Optional[str] = Field(None, min_length=2, max_length=100, description="Search query")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", pattern=r'^(asc|desc)$', description="Sort order")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Page size")

class FinanceSearchResponse(BaseModel):
    """Finance search response"""
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    results: List[Any]  # This will be typed based on specific search