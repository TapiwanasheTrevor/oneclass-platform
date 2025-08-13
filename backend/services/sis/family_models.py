# =====================================================
# SIS Module - Family Relationship Models
# File: backend/services/sis/family_models.py
# =====================================================

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, JSON, ForeignKey, Date, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

Base = declarative_base()

class RelationshipType(str, enum.Enum):
    """Types of family relationships"""
    MOTHER = "mother"
    FATHER = "father"
    STEP_MOTHER = "step_mother"
    STEP_FATHER = "step_father"
    GRANDMOTHER = "grandmother"
    GRANDFATHER = "grandfather"
    AUNT = "aunt"
    UNCLE = "uncle"
    SIBLING = "sibling"
    GUARDIAN = "guardian"
    FOSTER_PARENT = "foster_parent"
    OTHER = "other"

class ContactMethod(str, enum.Enum):
    """Preferred contact methods"""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PHONE_CALL = "phone_call"
    IN_PERSON = "in_person"

class FinancialResponsibilityType(str, enum.Enum):
    """Types of financial responsibility"""
    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"
    SHARED = "shared"

class StudentGuardianRelationship(Base):
    """
    Enhanced model for student-guardian relationships with comprehensive tracking
    """
    __tablename__ = "student_guardian_relationships"
    __table_args__ = {"schema": "sis"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core relationship
    student_id = Column(UUID(as_uuid=True), ForeignKey('sis.students.id'), nullable=False, index=True)
    guardian_user_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # References platform.users
    
    # Relationship details
    relationship_type = Column(Enum(RelationshipType), nullable=False)
    relationship_description = Column(String(100))  # Custom description if "other"
    is_biological = Column(Boolean, default=True)
    is_legal_guardian = Column(Boolean, default=True)
    
    # Contact preferences
    is_primary_contact = Column(Boolean, default=False)
    is_emergency_contact = Column(Boolean, default=True)
    contact_priority = Column(Integer, default=1)  # 1 = highest priority
    preferred_contact_method = Column(Enum(ContactMethod), default=ContactMethod.SMS)
    
    # Alternative contact information
    alternative_phone = Column(String(20))
    work_phone = Column(String(20))
    work_email = Column(String(255))
    work_address = Column(Text)
    
    # Employment information
    employer = Column(String(255))
    job_title = Column(String(100))
    work_schedule = Column(String(200))  # e.g., "Monday-Friday 8AM-5PM"
    monthly_income_range = Column(String(50))  # e.g., "$500-1000"
    
    # Permissions and responsibilities
    has_pickup_permission = Column(Boolean, default=True)
    has_academic_access = Column(Boolean, default=True)
    has_medical_access = Column(Boolean, default=True)
    has_disciplinary_access = Column(Boolean, default=True)
    can_authorize_field_trips = Column(Boolean, default=True)
    can_receive_communications = Column(Boolean, default=True)
    
    # Financial responsibility
    has_financial_responsibility = Column(Boolean, default=True)
    financial_responsibility_type = Column(Enum(FinancialResponsibilityType), default=FinancialResponsibilityType.FULL)
    financial_responsibility_percentage = Column(Float, default=100.0)  # Percentage of fees responsible for
    payment_method_preference = Column(String(50))  # EcoCash, Bank Transfer, etc.
    
    # Communication preferences
    receive_academic_reports = Column(Boolean, default=True)
    receive_financial_notices = Column(Boolean, default=True)
    receive_disciplinary_notices = Column(Boolean, default=True)
    receive_medical_alerts = Column(Boolean, default=True)
    receive_general_announcements = Column(Boolean, default=True)
    communication_frequency = Column(String(20), default="immediate")  # immediate, daily, weekly
    
    # Living arrangement
    student_lives_with = Column(Boolean, default=False)
    custody_type = Column(String(50))  # "full", "joint", "weekends", "holidays", etc.
    custody_notes = Column(Text)
    
    # Verification and approval
    is_verified = Column(Boolean, default=False)
    verified_by = Column(UUID(as_uuid=True))  # References platform.users (admin who verified)
    verification_date = Column(DateTime(timezone=True))
    verification_documents = Column(JSON, default=list)  # List of document URLs/IDs
    
    # Special notes and restrictions
    special_instructions = Column(Text)
    access_restrictions = Column(Text)  # Any restrictions on guardian access
    court_orders = Column(JSON, default=list)  # Any relevant court orders
    
    # Status and validity
    is_active = Column(Boolean, default=True)
    start_date = Column(Date, default=func.current_date())
    end_date = Column(Date)  # For temporary guardianship
    termination_reason = Column(String(200))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), nullable=False)  # User who created this relationship
    
    def __repr__(self):
        return f"<StudentGuardianRelationship(student_id={self.student_id}, guardian_id={self.guardian_user_id}, type={self.relationship_type})>"

class FamilyGroup(Base):
    """
    Model to group related students and guardians into family units
    Useful for sibling management and family communications
    """
    __tablename__ = "family_groups"
    __table_args__ = {"schema": "sis"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Family identification
    family_name = Column(String(200), nullable=False)  # Primary family surname
    family_code = Column(String(20), unique=True, index=True)  # Auto-generated family code
    
    # Primary contact for family
    primary_contact_user_id = Column(UUID(as_uuid=True))  # References platform.users
    
    # Family details
    household_size = Column(Integer)
    number_of_students = Column(Integer, default=0)
    family_address = Column(JSON, default=dict)  # Primary family address
    
    # Financial information
    family_income_range = Column(String(50))
    payment_plan_type = Column(String(50))  # monthly, termly, annual
    has_discount = Column(Boolean, default=False)
    discount_percentage = Column(Float, default=0.0)
    discount_reason = Column(String(200))
    
    # Communication preferences
    preferred_communication_language = Column(String(50), default="English")
    send_combined_reports = Column(Boolean, default=True)  # Single report for all students
    send_combined_invoices = Column(Boolean, default=True)
    
    # Special circumstances
    special_circumstances = Column(Text)  # Single parent, financial hardship, etc.
    support_services_required = Column(JSON, default=list)  # Social services, counseling, etc.
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), nullable=False)
    
    def __repr__(self):
        return f"<FamilyGroup(id={self.id}, name='{self.family_name}', code='{self.family_code}')>"

class StudentFamilyMembership(Base):
    """
    Links students to family groups (many-to-many relationship)
    """
    __tablename__ = "student_family_memberships"
    __table_args__ = {"schema": "sis"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    student_id = Column(UUID(as_uuid=True), ForeignKey('sis.students.id'), nullable=False, index=True)
    family_group_id = Column(UUID(as_uuid=True), ForeignKey('sis.family_groups.id'), nullable=False, index=True)
    
    # Membership details
    relationship_to_family = Column(String(50), default="child")  # child, dependent, ward
    is_primary_student = Column(Boolean, default=False)  # Main student in family (eldest, etc.)
    
    # Living situation
    lives_with_family = Column(Boolean, default=True)
    custody_arrangement = Column(String(100))
    custody_percentage = Column(Float, default=100.0)  # Percentage of time with this family
    
    # Financial
    family_pays_fees = Column(Boolean, default=True)
    fee_responsibility_percentage = Column(Float, default=100.0)
    
    # Status
    is_active = Column(Boolean, default=True)
    start_date = Column(Date, default=func.current_date())
    end_date = Column(Date)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<StudentFamilyMembership(student_id={self.student_id}, family_id={self.family_group_id})>"

class GuardianFamilyMembership(Base):
    """
    Links guardians to family groups (many-to-many relationship)
    """
    __tablename__ = "guardian_family_memberships"
    __table_args__ = {"schema": "sis"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    guardian_user_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # References platform.users
    family_group_id = Column(UUID(as_uuid=True), ForeignKey('sis.family_groups.id'), nullable=False, index=True)
    
    # Role in family
    role_in_family = Column(String(50))  # parent, step-parent, guardian, grandparent, etc.
    is_head_of_household = Column(Boolean, default=False)
    is_primary_contact = Column(Boolean, default=False)
    
    # Decision making authority
    can_make_academic_decisions = Column(Boolean, default=True)
    can_make_medical_decisions = Column(Boolean, default=True)
    can_make_financial_decisions = Column(Boolean, default=True)
    
    # Financial responsibility for family
    financial_contribution_percentage = Column(Float, default=50.0)
    is_primary_payer = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<GuardianFamilyMembership(guardian_id={self.guardian_user_id}, family_id={self.family_group_id})>"

class EmergencyContact(Base):
    """
    Emergency contacts that are not necessarily guardians
    """
    __tablename__ = "emergency_contacts"
    __table_args__ = {"schema": "sis"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Associated student
    student_id = Column(UUID(as_uuid=True), ForeignKey('sis.students.id'), nullable=False, index=True)
    
    # Contact information
    full_name = Column(String(200), nullable=False)
    relationship_to_student = Column(String(100), nullable=False)
    primary_phone = Column(String(20), nullable=False)
    secondary_phone = Column(String(20))
    email = Column(String(255))
    address = Column(Text)
    
    # Emergency contact details
    priority_order = Column(Integer, default=1)  # 1 = first to call
    available_24_7 = Column(Boolean, default=True)
    availability_notes = Column(String(500))  # Work hours, restrictions, etc.
    
    # Permissions
    can_pickup_student = Column(Boolean, default=False)
    can_authorize_medical_treatment = Column(Boolean, default=False)
    can_receive_student_information = Column(Boolean, default=True)
    
    # Verification
    identity_verified = Column(Boolean, default=False)
    verification_method = Column(String(100))  # photo_id, reference_check, etc.
    verification_date = Column(Date)
    
    # Additional information
    medical_knowledge = Column(Text)  # Knowledge of student's medical conditions
    special_instructions = Column(Text)
    languages_spoken = Column(String(200))
    
    # Status
    is_active = Column(Boolean, default=True)
    last_contacted = Column(DateTime(timezone=True))
    contact_successful = Column(Boolean)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), nullable=False)
    
    def __repr__(self):
        return f"<EmergencyContact(student_id={self.student_id}, name='{self.full_name}', priority={self.priority_order})>"