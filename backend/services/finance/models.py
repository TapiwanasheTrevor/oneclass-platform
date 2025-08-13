"""
Finance Management Module - Database Models
Complete financial management system for Zimbabwe schools
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, Text, DECIMAL, JSON, ForeignKey, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, ARRAY, ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from enum import Enum

from shared.database import Base

# Create audit mixins
class AuditMixin:
    """Audit mixin for tracking creation and updates"""
    created_by = Column("created_by", String(255), nullable=True)
    updated_by = Column("updated_by", String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class SoftDeleteMixin:
    """Soft delete mixin"""
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

# =====================================================
# ENUMS FOR FINANCE MODULE
# =====================================================

class FeeType(str, Enum):
    """Types of fees that can be charged"""
    TUITION = "tuition"
    REGISTRATION = "registration"
    EXAMINATION = "examination"
    SPORTS = "sports"
    LIBRARY = "library"
    TRANSPORT = "transport"
    MEALS = "meals"
    UNIFORM = "uniform"
    BOOKS = "books"
    TECHNOLOGY = "technology"
    ACTIVITIES = "activities"
    FIELD_TRIP = "field_trip"
    OTHER = "other"

class PaymentStatus(str, Enum):
    """Payment status options"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"

class PaymentMethod(str, Enum):
    """Available payment methods in Zimbabwe"""
    CASH = "cash"
    ECOCASH = "ecocash"
    ONEMONEY = "onemoney"
    TELECASH = "telecash"
    BANK_TRANSFER = "bank_transfer"
    PAYNOW = "paynow"
    ZIPIT = "zipit"
    CHEQUE = "cheque"
    OTHER = "other"

class InvoiceStatus(str, Enum):
    """Invoice status options"""
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class Currency(str, Enum):
    """Supported currencies in Zimbabwe"""
    USD = "USD"  # US Dollar (primary)
    ZWL = "ZWL"  # Zimbabwe Dollar
    ZAR = "ZAR"  # South African Rand
    BWP = "BWP"  # Botswana Pula

# =====================================================
# FEE STRUCTURE MODELS
# =====================================================

class FeeStructure(Base, AuditMixin, SoftDeleteMixin):
    """Fee structure model for defining school fees"""
    __tablename__ = "fee_structures"
    __table_args__ = (
        UniqueConstraint('school_id', 'name', 'academic_year', name='unique_fee_structure_per_year'),
        CheckConstraint('grade_level_min >= 1 AND grade_level_min <= 13', name='valid_min_grade_level'),
        CheckConstraint('grade_level_max >= 1 AND grade_level_max <= 13', name='valid_max_grade_level'),
        CheckConstraint('grade_level_max >= grade_level_min', name='valid_grade_level_range'),
        CheckConstraint('effective_to IS NULL OR effective_to >= effective_from', name='valid_effective_dates'),
        Index('idx_fee_structures_school_year', 'school_id', 'academic_year'),
        Index('idx_fee_structures_grade_levels', 'grade_level_min', 'grade_level_max'),
        Index('idx_fee_structures_active', 'is_active'),
        {'schema': 'finance'}
    )
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    school_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    
    # Basic information
    name = Column(String(200), nullable=False)
    description = Column(Text)
    academic_year = Column(String(10), nullable=False, index=True)
    
    # Grade level targeting
    grade_level_min = Column(Integer, nullable=False, index=True)  # 1-13 for Zimbabwe
    grade_level_max = Column(Integer, nullable=False, index=True)  # 1-13 for Zimbabwe
    
    # Applicable classes/streams
    class_streams = Column(ARRAY(String), default=list)  # ['A', 'B', 'C'] or [] for all
    
    # Currency and timing
    currency = Column(ENUM(Currency), default=Currency.USD, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date)
    
    # Fee calculation settings
    is_per_term = Column(Boolean, default=True, nullable=False)  # Per term vs annual
    allow_installments = Column(Boolean, default=True, nullable=False)
    installment_count = Column(Integer, default=3)  # Default: 3 terms
    
    # Late payment settings
    late_fee_amount = Column(DECIMAL(10, 2), default=Decimal('0.00'))
    late_fee_percentage = Column(DECIMAL(5, 2), default=Decimal('0.00'))
    grace_period_days = Column(Integer, default=7)
    
    # Discount settings
    early_payment_discount_percentage = Column(DECIMAL(5, 2), default=Decimal('0.00'))
    early_payment_days = Column(Integer, default=30)
    sibling_discount_percentage = Column(DECIMAL(5, 2), default=Decimal('0.00'))
    
    # Status
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    fee_items = relationship("FeeStructureItem", back_populates="fee_structure", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="fee_structure")
    
    def __repr__(self):
        return f"<FeeStructure(name='{self.name}', year='{self.academic_year}')>"

class FeeStructureItem(Base, AuditMixin):
    """Individual fee items within a fee structure"""
    __tablename__ = "fee_structure_items"
    __table_args__ = (
        UniqueConstraint('fee_structure_id', 'fee_type', 'term_number', name='unique_fee_item_per_term'),
        CheckConstraint('amount >= 0', name='non_negative_amount'),
        CheckConstraint('term_number IS NULL OR (term_number >= 1 AND term_number <= 3)', name='valid_term_number'),
        CheckConstraint('display_order >= 0', name='non_negative_display_order'),
        Index('idx_fee_items_structure', 'fee_structure_id'),
        Index('idx_fee_items_type', 'fee_type'),
        {'schema': 'finance'}
    )
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    fee_structure_id = Column(PostgresUUID(as_uuid=True), ForeignKey('finance.fee_structures.id'), nullable=False)
    
    # Fee details
    fee_type = Column(ENUM(FeeType), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    amount = Column(DECIMAL(10, 2), nullable=False)
    
    # Term specification
    term_number = Column(Integer)  # NULL = applies to all terms, 1-3 for specific term
    
    # Settings
    is_mandatory = Column(Boolean, default=True, nullable=False)
    is_refundable = Column(Boolean, default=False, nullable=False)
    allow_partial_payment = Column(Boolean, default=True, nullable=False)
    
    # Display and categorization
    display_order = Column(Integer, default=0, nullable=False)
    category = Column(String(50))  # Grouping for invoice display
    
    # Relationships
    fee_structure = relationship("FeeStructure", back_populates="fee_items")
    invoice_items = relationship("InvoiceItem", back_populates="fee_structure_item")
    
    def __repr__(self):
        return f"<FeeStructureItem(name='{self.name}', amount={self.amount})>"

# =====================================================
# INVOICE MODELS
# =====================================================

class Invoice(Base, AuditMixin, SoftDeleteMixin):
    """Invoice model for student billing"""
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint('school_id', 'invoice_number', name='unique_invoice_number_per_school'),
        CheckConstraint('total_amount >= 0', name='non_negative_total_amount'),
        CheckConstraint('tax_amount >= 0', name='non_negative_tax_amount'),
        CheckConstraint('discount_amount >= 0', name='non_negative_discount_amount'),
        CheckConstraint('outstanding_amount >= 0', name='non_negative_outstanding_amount'),
        CheckConstraint('paid_amount >= 0', name='non_negative_paid_amount'),
        CheckConstraint('due_date >= issue_date', name='due_date_after_issue_date'),
        Index('idx_invoices_school_student', 'school_id', 'student_id'),
        Index('idx_invoices_number', 'invoice_number'),
        Index('idx_invoices_status', 'status'),
        Index('idx_invoices_due_date', 'due_date'),
        Index('idx_invoices_academic_year', 'academic_year'),
        {'schema': 'finance'}
    )
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    school_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    student_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    fee_structure_id = Column(PostgresUUID(as_uuid=True), ForeignKey('finance.fee_structures.id'))
    
    # Invoice identification
    invoice_number = Column(String(50), nullable=False, unique=True, index=True)
    reference_number = Column(String(100))  # External reference
    
    # Academic context
    academic_year = Column(String(10), nullable=False, index=True)
    term_number = Column(Integer)  # 1-3 for Zimbabwe terms
    grade_level = Column(Integer)  # Student's grade level when invoice was created
    
    # Timing
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    
    # Financial details
    currency = Column(ENUM(Currency), default=Currency.USD, nullable=False)
    subtotal_amount = Column(DECIMAL(10, 2), default=Decimal('0.00'), nullable=False)
    discount_amount = Column(DECIMAL(10, 2), default=Decimal('0.00'), nullable=False)
    tax_amount = Column(DECIMAL(10, 2), default=Decimal('0.00'), nullable=False)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    paid_amount = Column(DECIMAL(10, 2), default=Decimal('0.00'), nullable=False)
    outstanding_amount = Column(DECIMAL(10, 2), nullable=False)
    
    # Status and workflow
    status = Column(ENUM(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False)
    
    # Communication tracking
    sent_at = Column(DateTime)
    viewed_at = Column(DateTime)
    first_viewed_at = Column(DateTime)
    view_count = Column(Integer, default=0, nullable=False)
    
    # Parent/guardian information (cached for performance)
    parent_name = Column(String(200))
    parent_email = Column(String(100))
    parent_phone = Column(String(20))
    
    # Additional information
    notes = Column(Text)
    payment_instructions = Column(Text)
    
    # Relationships
    fee_structure = relationship("FeeStructure", back_populates="invoices")
    invoice_items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice")
    
    @hybrid_property
    def is_overdue(self):
        """Check if invoice is overdue"""
        return self.due_date < date.today() and self.outstanding_amount > 0
    
    @hybrid_property
    def is_fully_paid(self):
        """Check if invoice is fully paid"""
        return self.outstanding_amount == 0
    
    @hybrid_property
    def payment_percentage(self):
        """Calculate payment percentage"""
        if self.total_amount == 0:
            return Decimal('0.00')
        return (self.paid_amount / self.total_amount) * 100
    
    def __repr__(self):
        return f"<Invoice(number='{self.invoice_number}', total={self.total_amount})>"

class InvoiceItem(Base, AuditMixin):
    """Individual line items on an invoice"""
    __tablename__ = "invoice_items"
    __table_args__ = (
        CheckConstraint('quantity > 0', name='positive_quantity'),
        CheckConstraint('unit_price >= 0', name='non_negative_unit_price'),
        CheckConstraint('total_price >= 0', name='non_negative_total_price'),
        CheckConstraint('discount_amount >= 0', name='non_negative_item_discount'),
        Index('idx_invoice_items_invoice', 'invoice_id'),
        Index('idx_invoice_items_fee_type', 'fee_type'),
        {'schema': 'finance'}
    )
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    invoice_id = Column(PostgresUUID(as_uuid=True), ForeignKey('finance.invoices.id'), nullable=False)
    fee_structure_item_id = Column(PostgresUUID(as_uuid=True), ForeignKey('finance.fee_structure_items.id'))
    
    # Item details
    fee_type = Column(ENUM(FeeType), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Pricing
    quantity = Column(DECIMAL(8, 2), default=Decimal('1.00'), nullable=False)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    discount_amount = Column(DECIMAL(10, 2), default=Decimal('0.00'), nullable=False)
    total_price = Column(DECIMAL(10, 2), nullable=False)
    
    # Term and categorization
    term_number = Column(Integer)  # Specific term this item applies to
    category = Column(String(50))
    
    # Display order
    line_number = Column(Integer, default=1, nullable=False)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="invoice_items")
    fee_structure_item = relationship("FeeStructureItem", back_populates="invoice_items")
    
    def __repr__(self):
        return f"<InvoiceItem(name='{self.name}', total={self.total_price})>"

# =====================================================
# PAYMENT MODELS
# =====================================================

class Payment(Base, AuditMixin, SoftDeleteMixin):
    """Payment model for tracking student payments"""
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint('school_id', 'payment_reference', name='unique_payment_reference_per_school'),
        CheckConstraint('amount > 0', name='positive_amount'),
        CheckConstraint('transaction_fee >= 0', name='non_negative_transaction_fee'),
        CheckConstraint('net_amount > 0', name='positive_net_amount'),
        Index('idx_payments_school_student', 'school_id', 'student_id'),
        Index('idx_payments_invoice', 'invoice_id'),
        Index('idx_payments_reference', 'payment_reference'),
        Index('idx_payments_status', 'status'),
        Index('idx_payments_method', 'payment_method'),
        Index('idx_payments_date', 'payment_date'),
        {'schema': 'finance'}
    )
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    school_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    student_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    invoice_id = Column(PostgresUUID(as_uuid=True), ForeignKey('finance.invoices.id'), nullable=False)
    
    # Payment identification
    payment_reference = Column(String(100), nullable=False, unique=True, index=True)
    external_reference = Column(String(100))  # Gateway reference
    transaction_id = Column(String(100))  # Payment gateway transaction ID
    
    # Payment details
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(ENUM(Currency), default=Currency.USD, nullable=False)
    transaction_fee = Column(DECIMAL(8, 2), default=Decimal('0.00'), nullable=False)
    net_amount = Column(DECIMAL(10, 2), nullable=False)  # Amount after fees
    
    # Payment method and gateway
    payment_method = Column(ENUM(PaymentMethod), nullable=False)
    payment_gateway = Column(String(50))  # 'paynow', 'ecocash', etc.
    
    # Timing
    payment_date = Column(DateTime, nullable=False)
    processed_date = Column(DateTime)
    
    # Status tracking
    status = Column(ENUM(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    
    # Parent information (for tracking who made payment)
    payer_name = Column(String(200))
    payer_email = Column(String(100))
    payer_phone = Column(String(20))
    
    # Gateway response data
    gateway_response = Column(JSON)  # Store full gateway response
    
    # Reconciliation
    is_reconciled = Column(Boolean, default=False, nullable=False)
    reconciled_at = Column(DateTime)
    reconciled_by = Column(String(255))
    
    # Additional information
    notes = Column(Text)
    receipt_sent_at = Column(DateTime)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
    
    @hybrid_property
    def is_successful(self):
        """Check if payment was successful"""
        return self.status == PaymentStatus.COMPLETED
    
    def __repr__(self):
        return f"<Payment(reference='{self.payment_reference}', amount={self.amount})>"

# =====================================================
# PAYMENT METHOD CONFIGURATION
# =====================================================

class PaymentMethodConfig(Base, AuditMixin, SoftDeleteMixin):
    """Configuration for payment methods per school"""
    __tablename__ = "payment_method_configs"
    __table_args__ = (
        UniqueConstraint('school_id', 'payment_method', name='unique_payment_method_per_school'),
        CheckConstraint('transaction_fee_percentage >= 0', name='non_negative_fee_percentage'),
        CheckConstraint('transaction_fee_fixed >= 0', name='non_negative_fee_fixed'),
        CheckConstraint('minimum_amount >= 0', name='non_negative_minimum_amount'),
        CheckConstraint('maximum_amount >= minimum_amount', name='valid_amount_range'),
        CheckConstraint('display_order >= 0', name='non_negative_display_order'),
        Index('idx_payment_methods_school', 'school_id'),
        Index('idx_payment_methods_active', 'is_active'),
        {'schema': 'finance'}
    )
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    school_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    
    # Payment method configuration
    payment_method = Column(ENUM(PaymentMethod), nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Gateway configuration
    gateway_name = Column(String(50))  # 'paynow', 'ecocash_api', etc.
    gateway_config = Column(JSON)  # Store API keys, endpoints, etc.
    
    # Fee structure
    transaction_fee_percentage = Column(DECIMAL(5, 2), default=Decimal('0.00'), nullable=False)
    transaction_fee_fixed = Column(DECIMAL(8, 2), default=Decimal('0.00'), nullable=False)
    
    # Limits
    minimum_amount = Column(DECIMAL(10, 2), default=Decimal('1.00'), nullable=False)
    maximum_amount = Column(DECIMAL(12, 2))
    
    # Settings
    requires_reference = Column(Boolean, default=False, nullable=False)
    supports_partial_payment = Column(Boolean, default=True, nullable=False)
    auto_reconcile = Column(Boolean, default=False, nullable=False)
    
    # Display and availability
    is_enabled = Column(Boolean, default=True, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    
    # Instructions for users
    payment_instructions = Column(Text)
    
    def __repr__(self):
        return f"<PaymentMethodConfig(method='{self.payment_method}', enabled={self.is_enabled})>"

# =====================================================
# FINANCIAL REPORTING MODELS
# =====================================================

class FinancialPeriod(Base, AuditMixin):
    """Financial reporting periods"""
    __tablename__ = "financial_periods"
    __table_args__ = (
        UniqueConstraint('school_id', 'name', 'period_type', name='unique_financial_period'),
        CheckConstraint('end_date >= start_date', name='valid_period_dates'),
        CheckConstraint("period_type IN ('term', 'semester', 'year', 'quarter')", name='valid_period_type'),
        CheckConstraint("status IN ('active', 'closed', 'archived')", name='valid_period_status'),
        Index('idx_financial_periods_school', 'school_id'),
        Index('idx_financial_periods_dates', 'start_date', 'end_date'),
        {'schema': 'finance'}
    )
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    school_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    
    # Period identification
    name = Column(String(100), nullable=False)  # "Term 1 2024", "Year 2024"
    period_type = Column(String(20), nullable=False)  # 'term', 'semester', 'year', 'quarter'
    academic_year = Column(String(10), nullable=False, index=True)
    term_number = Column(Integer)  # For Zimbabwe terms: 1, 2, 3
    
    # Period dates
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Status
    status = Column(String(20), default='active', nullable=False)
    closed_at = Column(DateTime)
    closed_by = Column(String(255))
    
    # Financial summary (calculated/cached values)
    total_revenue = Column(DECIMAL(15, 2), default=Decimal('0.00'), nullable=False)
    total_outstanding = Column(DECIMAL(15, 2), default=Decimal('0.00'), nullable=False)
    total_invoiced = Column(DECIMAL(15, 2), default=Decimal('0.00'), nullable=False)
    collection_rate = Column(DECIMAL(5, 2), default=Decimal('0.00'), nullable=False)
    
    def __repr__(self):
        return f"<FinancialPeriod(name='{self.name}', type='{self.period_type}')>"

# =====================================================
# STUDENT ACCOUNT MODELS
# =====================================================

class StudentAccount(Base, AuditMixin, SoftDeleteMixin):
    """Student financial account for tracking balances and transactions"""
    __tablename__ = "student_accounts"
    __table_args__ = (
        UniqueConstraint('school_id', 'student_id', name='unique_student_account'),
        CheckConstraint('current_balance >= 0 OR allow_negative_balance = true', name='valid_balance_or_allowed_negative'),
        CheckConstraint('total_invoiced >= 0', name='non_negative_total_invoiced'),
        CheckConstraint('total_paid >= 0', name='non_negative_total_paid'),
        CheckConstraint('credit_limit >= 0', name='non_negative_credit_limit'),
        Index('idx_student_accounts_school', 'school_id'),
        Index('idx_student_accounts_student', 'student_id'),
        Index('idx_student_accounts_balance', 'current_balance'),
        {'schema': 'finance'}
    )
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    school_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    student_id = Column(PostgresUUID(as_uuid=True), nullable=False, unique=True, index=True)
    
    # Account identification
    account_number = Column(String(50), unique=True, index=True)
    
    # Financial summary
    current_balance = Column(DECIMAL(12, 2), default=Decimal('0.00'), nullable=False)
    total_invoiced = Column(DECIMAL(12, 2), default=Decimal('0.00'), nullable=False)
    total_paid = Column(DECIMAL(12, 2), default=Decimal('0.00'), nullable=False)
    total_outstanding = Column(DECIMAL(12, 2), default=Decimal('0.00'), nullable=False)
    
    # Account settings
    credit_limit = Column(DECIMAL(10, 2), default=Decimal('0.00'), nullable=False)
    allow_negative_balance = Column(Boolean, default=False, nullable=False)
    
    # Payment preferences
    preferred_payment_method = Column(ENUM(PaymentMethod))
    payment_reminder_email = Column(Boolean, default=True, nullable=False)
    payment_reminder_sms = Column(Boolean, default=True, nullable=False)
    
    # Parent/Guardian information (cached)
    primary_contact_name = Column(String(200))
    primary_contact_email = Column(String(100))
    primary_contact_phone = Column(String(20))
    
    # Status
    account_status = Column(String(20), default='active', nullable=False)  # active, suspended, closed
    
    # Last activity tracking
    last_payment_date = Column(DateTime)
    last_invoice_date = Column(DateTime)
    
    @hybrid_property
    def is_in_good_standing(self):
        """Check if account is in good standing (not over credit limit)"""
        if self.allow_negative_balance:
            return self.current_balance >= -self.credit_limit
        return self.current_balance >= 0
    
    def __repr__(self):
        return f"<StudentAccount(student_id={self.student_id}, balance={self.current_balance})>"