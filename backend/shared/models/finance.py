"""
Finance Management Models
Re-exports authoritative models from services/finance/models.py where they exist,
and defines models that only live in the shared layer.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, JSON, ForeignKey, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from shared.database import Base

# ---------------------------------------------------------------------------
# Models that have authoritative definitions in services/finance/models.py
# We re-export them so that ``from shared.models.finance import FeeStructure``
# still works but there is only ONE SQLAlchemy mapper per table.
# ---------------------------------------------------------------------------
try:
    from services.finance.models import FeeStructure, Invoice, Payment
except ImportError:
    # Fallback stubs when the finance service package is not on sys.path.
    # These are intentionally minimal – just enough for init_database() to
    # call Base.metadata.create_all without crashing.
    class FeeStructure(Base):  # type: ignore[no-redef]
        __tablename__ = "fee_structures"
        __table_args__ = {"schema": "finance", "extend_existing": True}
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
        name = Column(String(255), nullable=False)

    class Invoice(Base):  # type: ignore[no-redef]
        __tablename__ = "invoices"
        __table_args__ = {"schema": "finance", "extend_existing": True}
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
        invoice_number = Column(String(50), unique=True, nullable=False)

    class Payment(Base):  # type: ignore[no-redef]
        __tablename__ = "payments"
        __table_args__ = {"schema": "finance", "extend_existing": True}
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        school_id = Column(UUID(as_uuid=True), nullable=False, index=True)

# ---------------------------------------------------------------------------
# Models that only exist in the shared layer (no service-level counterpart)
# ---------------------------------------------------------------------------

class StudentFeeAssignment(Base):
    """Assignment of fee structure to individual students"""
    __tablename__ = "student_fee_assignments"
    __table_args__ = {"schema": "finance", "extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    student_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    fee_structure_id = Column(UUID(as_uuid=True), ForeignKey('finance.fee_structures.id'), nullable=False)

    academic_year_id = Column(UUID(as_uuid=True))
    term_id = Column(UUID(as_uuid=True))

    custom_amount = Column(Numeric(10, 2))
    custom_fee_items = Column(JSON)
    applied_discounts = Column(JSON, default=[])

    assigned_by = Column(UUID(as_uuid=True), nullable=False)
    assignment_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)

    status = Column(String(20), default="assigned")
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class FinancialReport(Base):
    """Financial reports and summaries"""
    __tablename__ = "financial_reports"
    __table_args__ = {"schema": "finance", "extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    report_name = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    total_invoiced = Column(Numeric(12, 2), default=0)
    total_collected = Column(Numeric(12, 2), default=0)
    total_outstanding = Column(Numeric(12, 2), default=0)
    collection_rate = Column(Numeric(5, 2))

    category_breakdown = Column(JSON, default={})
    payment_method_breakdown = Column(JSON, default={})
    grade_level_breakdown = Column(JSON, default={})

    overdue_amount = Column(Numeric(12, 2), default=0)
    advance_payments = Column(Numeric(12, 2), default=0)
    refunds_issued = Column(Numeric(12, 2), default=0)

    generated_by = Column(UUID(as_uuid=True), nullable=False)
    report_data = Column(JSON)
    report_url = Column(String(500))

    status = Column(String(20), default="generated")

    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Budget(Base):
    """School budget model"""
    __tablename__ = "budgets"
    __table_args__ = {"schema": "finance", "extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    budget_name = Column(String(255), nullable=False)
    budget_type = Column(String(50), nullable=False)
    fiscal_year = Column(Integer, nullable=False)

    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    total_budget = Column(Numeric(12, 2), nullable=False)
    allocated_amount = Column(Numeric(12, 2), default=0)
    spent_amount = Column(Numeric(12, 2), default=0)
    remaining_amount = Column(Numeric(12, 2))

    budget_categories = Column(JSON, nullable=False)

    approved_by = Column(UUID(as_uuid=True))
    approved_at = Column(DateTime(timezone=True))
    approval_status = Column(String(20), default="draft")

    created_by = Column(UUID(as_uuid=True), nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Expense(Base):
    """School expenses model"""
    __tablename__ = "expenses"
    __table_args__ = {"schema": "finance", "extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    expense_number = Column(String(50), unique=True, nullable=False)
    expense_date = Column(Date, nullable=False)
    description = Column(Text, nullable=False)

    category = Column(String(100), nullable=False)
    subcategory = Column(String(100))
    budget_id = Column(UUID(as_uuid=True), ForeignKey('finance.budgets.id'))

    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    tax_amount = Column(Numeric(10, 2), default=0)

    vendor_name = Column(String(255))
    vendor_contact = Column(String(255))
    invoice_reference = Column(String(100))

    payment_method = Column(String(50))
    payment_reference = Column(String(100))
    payment_date = Column(Date)
    payment_status = Column(String(20), default="pending")

    requested_by = Column(UUID(as_uuid=True), nullable=False)
    approved_by = Column(UUID(as_uuid=True))
    approval_date = Column(DateTime(timezone=True))
    approval_status = Column(String(20), default="pending")

    receipt_url = Column(String(500))
    attachments = Column(JSON, default=[])

    status = Column(String(20), default="draft")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
