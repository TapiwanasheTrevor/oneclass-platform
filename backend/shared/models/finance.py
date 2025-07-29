"""
Finance Management Models
Database models for financial entities (fees, payments, invoices, budgets)
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, JSON, ForeignKey, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()

class FeeStructure(Base):
    """Fee structure model for different grades/classes"""
    __tablename__ = "fee_structures"
    __table_args__ = {"schema": "finance"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Fee structure details
    name = Column(String(255), nullable=False)  # "Grade 1 Annual Fees"
    description = Column(Text)
    grade_level = Column(String(20))  # "Grade_1", "Form_1", "All"
    class_type = Column(String(50))  # "day", "boarding", "all"
    
    # Academic period
    academic_year_id = Column(UUID(as_uuid=True))  # References academic.academic_years
    term_id = Column(UUID(as_uuid=True))  # References academic.terms (if term-specific)
    
    # Fee breakdown
    fee_items = Column(JSON, nullable=False)  # [{"name": "Tuition", "amount": 500, "category": "academic"}]
    total_amount = Column(Numeric(10,2), nullable=False)
    currency = Column(String(3), default="USD")
    
    # Payment terms
    payment_schedule = Column(JSON, default=[])  # [{"due_date": "2024-01-15", "amount": 250}]
    late_fee_policy = Column(JSON, default={})  # {"grace_days": 7, "penalty_rate": 5}
    discount_policy = Column(JSON, default={})  # {"sibling_discount": 10, "early_bird": 5}
    
    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<FeeStructure(id={self.id}, name='{self.name}', amount={self.total_amount})>"

class StudentFeeAssignment(Base):
    """Assignment of fee structure to individual students"""
    __tablename__ = "student_fee_assignments"
    __table_args__ = {"schema": "finance"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Student and fee structure
    student_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # References sis.students
    fee_structure_id = Column(UUID(as_uuid=True), ForeignKey('finance.fee_structures.id'), nullable=False)
    
    # Academic period
    academic_year_id = Column(UUID(as_uuid=True))
    term_id = Column(UUID(as_uuid=True))
    
    # Customizations
    custom_amount = Column(Numeric(10,2))  # Override total amount if needed
    custom_fee_items = Column(JSON)  # Override specific fee items
    applied_discounts = Column(JSON, default=[])  # [{"type": "sibling", "amount": 50}]
    
    # Assignment details
    assigned_by = Column(UUID(as_uuid=True), nullable=False)  # References platform.users
    assignment_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    
    # Status
    status = Column(String(20), default="assigned")  # assigned, invoiced, paid, overdue, cancelled
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<StudentFeeAssignment(id={self.id}, student_id={self.student_id}, status='{self.status}')>"

class Invoice(Base):
    """Invoice model for student fees"""
    __tablename__ = "invoices"
    __table_args__ = {"schema": "finance"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Invoice details
    invoice_number = Column(String(50), unique=True, nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    
    # Student information
    student_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    student_name = Column(String(255), nullable=False)  # Cached for reporting
    parent_id = Column(UUID(as_uuid=True))  # References platform.users
    
    # Fee assignment
    fee_assignment_id = Column(UUID(as_uuid=True), ForeignKey('finance.student_fee_assignments.id'))
    
    # Amounts
    subtotal = Column(Numeric(10,2), nullable=False)
    discount_amount = Column(Numeric(10,2), default=0)
    tax_amount = Column(Numeric(10,2), default=0)
    late_fee_amount = Column(Numeric(10,2), default=0)
    total_amount = Column(Numeric(10,2), nullable=False)
    paid_amount = Column(Numeric(10,2), default=0)
    balance_amount = Column(Numeric(10,2))
    
    # Currency
    currency = Column(String(3), default="USD")
    
    # Invoice items
    line_items = Column(JSON, nullable=False)  # Detailed breakdown of charges
    
    # Status
    status = Column(String(20), default="pending")  # pending, sent, paid, overdue, cancelled
    payment_status = Column(String(20), default="unpaid")  # unpaid, partial, paid, overpaid
    
    # Communication
    sent_to_email = Column(String(255))
    sent_at = Column(DateTime(timezone=True))
    last_reminder_sent = Column(DateTime(timezone=True))
    reminder_count = Column(Integer, default=0)
    
    # Generated by
    created_by = Column(UUID(as_uuid=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', amount={self.total_amount})>"

class Payment(Base):
    """Payment records model"""
    __tablename__ = "payments"
    __table_args__ = {"schema": "finance"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Payment details
    payment_reference = Column(String(100), unique=True, nullable=False)
    payment_date = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Numeric(10,2), nullable=False)
    currency = Column(String(3), default="USD")
    
    # Student and invoice
    student_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey('finance.invoices.id'))
    
    # Payment method
    payment_method = Column(String(50), nullable=False)  # cash, bank_transfer, mobile_money, card, cheque
    payment_gateway = Column(String(50))  # ecocash, paynow, stripe, etc.
    
    # Transaction details
    transaction_id = Column(String(255))  # External transaction ID
    gateway_reference = Column(String(255))  # Gateway-specific reference
    gateway_response = Column(JSON)  # Full gateway response
    
    # Bank/Cheque details
    bank_name = Column(String(100))
    account_number = Column(String(50))
    cheque_number = Column(String(50))
    cheque_date = Column(Date)
    
    # Processing
    processed_by = Column(UUID(as_uuid=True))  # References platform.users
    verified_by = Column(UUID(as_uuid=True))  # References platform.users
    verification_date = Column(DateTime(timezone=True))
    
    # Status
    status = Column(String(20), default="pending")  # pending, processing, completed, failed, cancelled
    verification_status = Column(String(20), default="unverified")  # unverified, verified, rejected
    
    # Notes and attachments
    notes = Column(Text)
    receipt_url = Column(String(500))
    attachments = Column(JSON, default=[])  # Supporting documents
    
    # Refund information
    is_refund = Column(Boolean, default=False)
    original_payment_id = Column(UUID(as_uuid=True))  # References payments.id if refund
    refund_reason = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Payment(id={self.id}, reference='{self.payment_reference}', amount={self.amount})>"

class FinancialReport(Base):
    """Financial reports and summaries"""
    __tablename__ = "financial_reports"
    __table_args__ = {"schema": "finance"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Report details
    report_name = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False)  # monthly, termly, annual, custom
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Financial data
    total_invoiced = Column(Numeric(12,2), default=0)
    total_collected = Column(Numeric(12,2), default=0)
    total_outstanding = Column(Numeric(12,2), default=0)
    collection_rate = Column(Numeric(5,2))  # Percentage
    
    # Breakdown by category
    category_breakdown = Column(JSON, default={})  # {"tuition": 50000, "transport": 15000}
    payment_method_breakdown = Column(JSON, default={})
    grade_level_breakdown = Column(JSON, default={})
    
    # Additional metrics
    overdue_amount = Column(Numeric(12,2), default=0)
    advance_payments = Column(Numeric(12,2), default=0)
    refunds_issued = Column(Numeric(12,2), default=0)
    
    # Report generation
    generated_by = Column(UUID(as_uuid=True), nullable=False)
    report_data = Column(JSON)  # Detailed report data
    report_url = Column(String(500))  # Generated report file URL
    
    # Status
    status = Column(String(20), default="generated")  # generated, sent, archived
    
    # Timestamps
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<FinancialReport(id={self.id}, name='{self.report_name}', period={self.period_start}-{self.period_end})>"

class Budget(Base):
    """School budget model"""
    __tablename__ = "budgets"
    __table_args__ = {"schema": "finance"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Budget details
    budget_name = Column(String(255), nullable=False)
    budget_type = Column(String(50), nullable=False)  # operational, capital, project
    fiscal_year = Column(Integer, nullable=False)
    
    # Period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Amounts
    total_budget = Column(Numeric(12,2), nullable=False)
    allocated_amount = Column(Numeric(12,2), default=0)
    spent_amount = Column(Numeric(12,2), default=0)
    remaining_amount = Column(Numeric(12,2))
    
    # Budget categories
    budget_categories = Column(JSON, nullable=False)  # Detailed budget breakdown
    
    # Approval
    approved_by = Column(UUID(as_uuid=True))
    approved_at = Column(DateTime(timezone=True))
    approval_status = Column(String(20), default="draft")  # draft, submitted, approved, rejected
    
    # Created by
    created_by = Column(UUID(as_uuid=True), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Budget(id={self.id}, name='{self.budget_name}', total={self.total_budget})>"

class Expense(Base):
    """School expenses model"""
    __tablename__ = "expenses"
    __table_args__ = {"schema": "finance"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Expense details
    expense_number = Column(String(50), unique=True, nullable=False)
    expense_date = Column(Date, nullable=False)
    description = Column(Text, nullable=False)
    
    # Category and budget
    category = Column(String(100), nullable=False)  # utilities, salaries, maintenance, supplies
    subcategory = Column(String(100))
    budget_id = Column(UUID(as_uuid=True), ForeignKey('finance.budgets.id'))
    
    # Amount
    amount = Column(Numeric(10,2), nullable=False)
    currency = Column(String(3), default="USD")
    tax_amount = Column(Numeric(10,2), default=0)
    
    # Vendor information
    vendor_name = Column(String(255))
    vendor_contact = Column(String(255))
    invoice_reference = Column(String(100))
    
    # Payment details
    payment_method = Column(String(50))  # cash, bank_transfer, cheque
    payment_reference = Column(String(100))
    payment_date = Column(Date)
    payment_status = Column(String(20), default="pending")  # pending, paid, cancelled
    
    # Approval workflow
    requested_by = Column(UUID(as_uuid=True), nullable=False)
    approved_by = Column(UUID(as_uuid=True))
    approval_date = Column(DateTime(timezone=True))
    approval_status = Column(String(20), default="pending")  # pending, approved, rejected
    
    # Supporting documents
    receipt_url = Column(String(500))
    attachments = Column(JSON, default=[])
    
    # Status
    status = Column(String(20), default="draft")  # draft, submitted, approved, paid, cancelled
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Expense(id={self.id}, number='{self.expense_number}', amount={self.amount})>"