"""
Migration Services - SQLAlchemy ORM Models
Maps to the migration_services schema tables defined in database/schemas/06_migration_services.sql
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PostgresUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DECIMAL

from shared.database import Base


class CarePackage(Base):
    """Care package definitions (Foundation, Growth, Enterprise)"""

    __tablename__ = "care_packages"
    __table_args__ = ({"schema": "migration_services", "extend_existing": True},)

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    name = Column(String(50), nullable=False)
    price_usd = Column(DECIMAL(10, 2), nullable=False)
    price_zwl = Column(DECIMAL(15, 2), nullable=False)
    max_students = Column(Integer, nullable=True)
    max_historical_years = Column(Integer, nullable=True)
    features = Column(Text, nullable=False)  # JSONB in Postgres, mapped as Text for portability
    inclusions = Column(ARRAY(Text), nullable=True)
    exclusions = Column(ARRAY(Text), nullable=True)
    estimated_duration_days = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    orders = relationship("CarePackageOrder", back_populates="care_package")


class CarePackageOrder(Base):
    """School orders for migration services"""

    __tablename__ = "care_package_orders"
    __table_args__ = (
        CheckConstraint("progress_percentage BETWEEN 0 AND 100", name="ck_progress_pct"),
        {"schema": "migration_services", "extend_existing": True},
    )

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    order_number = Column(String(20), unique=True, nullable=False)
    school_id = Column(PostgresUUID(as_uuid=True), ForeignKey("platform.schools.id"), nullable=False)
    care_package_id = Column(PostgresUUID(as_uuid=True), ForeignKey("migration_services.care_packages.id"), nullable=False)

    # Order details
    order_date = Column(Date, nullable=False, server_default=func.current_date())
    requested_start_date = Column(Date, nullable=True)
    estimated_completion_date = Column(Date, nullable=True)
    actual_completion_date = Column(Date, nullable=True)

    # Status
    status = Column(String(20), nullable=False, default="pending")

    # Pricing
    package_price = Column(DECIMAL(10, 2), nullable=False)
    additional_costs = Column(DECIMAL(10, 2), default=0)
    # total_price is a GENERATED column in Postgres — read-only
    currency = Column(String(3), default="USD")
    payment_option = Column(String(20), default="split")
    payment_status = Column(String(20), default="pending")

    # Team assignment
    assigned_migration_manager = Column(PostgresUUID(as_uuid=True), ForeignKey("platform.users.id"), nullable=True)
    assigned_technical_lead = Column(PostgresUUID(as_uuid=True), ForeignKey("platform.users.id"), nullable=True)
    assigned_data_specialist = Column(PostgresUUID(as_uuid=True), ForeignKey("platform.users.id"), nullable=True)
    assigned_training_specialist = Column(PostgresUUID(as_uuid=True), ForeignKey("platform.users.id"), nullable=True)

    # Requirements
    student_count = Column(Integer, nullable=True)
    current_system_type = Column(String(50), nullable=True)
    data_sources_description = Column(Text, nullable=True)
    special_requirements = Column(Text, nullable=True)
    custom_integrations_needed = Column(ARRAY(Text), nullable=True)

    # Additional options
    urgent_migration = Column(Boolean, default=False)
    onsite_training = Column(Boolean, default=False)
    weekend_work = Column(Boolean, default=False)

    # Progress
    progress_percentage = Column(Integer, default=0)
    estimated_hours = Column(Integer, nullable=True)
    actual_hours = Column(Integer, default=0)

    # Contact
    primary_contact_name = Column(String(100), nullable=True)
    primary_contact_email = Column(String(255), nullable=True)
    primary_contact_phone = Column(String(20), nullable=True)
    secondary_contact_name = Column(String(100), nullable=True)
    secondary_contact_email = Column(String(255), nullable=True)

    # Notes
    initial_assessment_notes = Column(Text, nullable=True)
    completion_notes = Column(Text, nullable=True)
    customer_feedback = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    care_package = relationship("CarePackage", back_populates="orders")
    school = relationship("School", foreign_keys=[school_id])
    tasks = relationship("MigrationTask", back_populates="order")
    milestones = relationship("Milestone", back_populates="order")
    communication_logs = relationship("CommunicationLog", back_populates="order")
    payments = relationship("MigrationPayment", back_populates="order")
    data_sources = relationship("DataSource", back_populates="order")

    @property
    def total_price(self):
        return (self.package_price or Decimal("0")) + (self.additional_costs or Decimal("0"))


class MigrationTask(Base):
    """Individual tasks within migration projects"""

    __tablename__ = "migration_tasks"
    __table_args__ = ({"schema": "migration_services", "extend_existing": True},)

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    care_package_order_id = Column(PostgresUUID(as_uuid=True), ForeignKey("migration_services.care_package_orders.id"), nullable=False)
    phase = Column(String(30), nullable=False)
    task_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assigned_to = Column(PostgresUUID(as_uuid=True), ForeignKey("platform.users.id"), nullable=True)

    status = Column(String(20), default="pending")
    priority = Column(String(10), default="medium")

    estimated_hours = Column(DECIMAL(5, 2), nullable=True)
    actual_hours = Column(DECIMAL(5, 2), default=0)

    due_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)

    depends_on = Column(PostgresUUID(as_uuid=True), ForeignKey("migration_services.migration_tasks.id"), nullable=True)
    blocking_reason = Column(Text, nullable=True)

    task_notes = Column(Text, nullable=True)
    completion_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    order = relationship("CarePackageOrder", back_populates="tasks")
    assigned_user = relationship("PlatformUser", foreign_keys=[assigned_to])


class DataSource(Base):
    """Source data files and systems for migration"""

    __tablename__ = "data_sources"
    __table_args__ = ({"schema": "migration_services", "extend_existing": True},)

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    care_package_order_id = Column(PostgresUUID(as_uuid=True), ForeignKey("migration_services.care_package_orders.id"), nullable=False)
    source_name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)
    file_path = Column(Text, nullable=True)
    file_size = Column(Integer, nullable=True)
    record_count = Column(Integer, nullable=True)

    status = Column(String(20), default="received")

    data_quality_score = Column(Integer, nullable=True)
    issues_found = Column(ARRAY(Text), nullable=True)
    cleaning_notes = Column(Text, nullable=True)

    processed_at = Column(DateTime(timezone=True), nullable=True)
    processed_by = Column(PostgresUUID(as_uuid=True), ForeignKey("platform.users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    order = relationship("CarePackageOrder", back_populates="data_sources")


class CommunicationLog(Base):
    """Communication history for migration projects"""

    __tablename__ = "communication_log"
    __table_args__ = ({"schema": "migration_services", "extend_existing": True},)

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    care_package_order_id = Column(PostgresUUID(as_uuid=True), ForeignKey("migration_services.care_package_orders.id"), nullable=False)
    communication_type = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)
    subject = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    participants = Column(ARRAY(Text), nullable=True)

    created_by = Column(PostgresUUID(as_uuid=True), ForeignKey("platform.users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    order = relationship("CarePackageOrder", back_populates="communication_logs")


class MigrationPayment(Base):
    """Payment tracking for care packages"""

    __tablename__ = "payments"
    __table_args__ = ({"schema": "migration_services", "extend_existing": True},)

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    care_package_order_id = Column(PostgresUUID(as_uuid=True), ForeignKey("migration_services.care_package_orders.id"), nullable=False)
    payment_type = Column(String(20), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), default="USD")

    payment_method = Column(String(20), nullable=True)
    reference_number = Column(String(100), nullable=True)

    due_date = Column(Date, nullable=True)
    paid_date = Column(Date, nullable=True)

    status = Column(String(20), default="pending")

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    order = relationship("CarePackageOrder", back_populates="payments")


class Milestone(Base):
    """Project milestones and deliverables"""

    __tablename__ = "milestones"
    __table_args__ = ({"schema": "migration_services", "extend_existing": True},)

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    care_package_order_id = Column(PostgresUUID(as_uuid=True), ForeignKey("migration_services.care_package_orders.id"), nullable=True)
    milestone_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    sequence_order = Column(Integer, nullable=False)

    status = Column(String(20), default="pending")

    planned_start_date = Column(Date, nullable=True)
    planned_end_date = Column(Date, nullable=True)
    actual_start_date = Column(Date, nullable=True)
    actual_end_date = Column(Date, nullable=True)

    deliverables = Column(ARRAY(Text), nullable=True)
    acceptance_criteria = Column(ARRAY(Text), nullable=True)

    completion_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    order = relationship("CarePackageOrder", back_populates="milestones")


class TeamPerformance(Base):
    """Team member performance metrics"""

    __tablename__ = "team_performance"
    __table_args__ = (
        UniqueConstraint("user_id", "month_year", name="uq_team_perf_user_month"),
        {"schema": "migration_services", "extend_existing": True},
    )

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("platform.users.id"), nullable=False)
    month_year = Column(Date, nullable=False)

    projects_assigned = Column(Integer, default=0)
    projects_completed = Column(Integer, default=0)
    projects_delayed = Column(Integer, default=0)

    billable_hours = Column(DECIMAL(6, 2), default=0)
    utilization_percentage = Column(DECIMAL(5, 2), default=0)

    customer_satisfaction_avg = Column(DECIMAL(3, 2), default=0)
    on_time_delivery_rate = Column(DECIMAL(5, 2), default=0)

    overall_rating = Column(DECIMAL(3, 2), default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
