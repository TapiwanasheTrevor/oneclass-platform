# =====================================================
# SIS Module - Family Management Schemas
# File: backend/services/sis/family_schemas.py
# =====================================================

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from uuid import UUID
from enum import Enum

from .family_models import (
    RelationshipType,
    ContactMethod,
    FinancialResponsibilityType
)

# =====================================================
# FAMILY GROUP SCHEMAS
# =====================================================

class FamilyGroupCreate(BaseModel):
    """Schema for creating a family group"""
    family_name: str = Field(..., min_length=2, max_length=200)
    primary_contact_user_id: UUID
    household_size: Optional[int] = Field(None, ge=1, le=20)
    family_address: Optional[Dict[str, Any]] = None
    family_income_range: Optional[str] = Field(None, max_length=50)
    payment_plan_type: Optional[str] = Field(None, pattern=r'^(monthly|termly|annual)$')
    preferred_communication_language: Optional[str] = Field(None, max_length=50)
    send_combined_reports: bool = True
    send_combined_invoices: bool = True
    special_circumstances: Optional[str] = Field(None, max_length=1000)
    support_services_required: Optional[List[str]] = Field(default_factory=list)

class FamilyGroupUpdate(BaseModel):
    """Schema for updating a family group"""
    family_name: Optional[str] = Field(None, min_length=2, max_length=200)
    primary_contact_user_id: Optional[UUID] = None
    household_size: Optional[int] = Field(None, ge=1, le=20)
    family_address: Optional[Dict[str, Any]] = None
    family_income_range: Optional[str] = Field(None, max_length=50)
    payment_plan_type: Optional[str] = Field(None, pattern=r'^(monthly|termly|annual)$')
    has_discount: Optional[bool] = None
    discount_percentage: Optional[float] = Field(None, ge=0, le=100)
    discount_reason: Optional[str] = Field(None, max_length=200)
    preferred_communication_language: Optional[str] = Field(None, max_length=50)
    send_combined_reports: Optional[bool] = None
    send_combined_invoices: Optional[bool] = None
    special_circumstances: Optional[str] = Field(None, max_length=1000)
    support_services_required: Optional[List[str]] = None

class FamilyGroupResponse(BaseModel):
    """Schema for family group response"""
    id: UUID
    school_id: UUID
    family_name: str
    family_code: str
    primary_contact_user_id: Optional[UUID]
    household_size: Optional[int]
    number_of_students: int
    family_address: Optional[Dict[str, Any]]
    family_income_range: Optional[str]
    payment_plan_type: Optional[str]
    has_discount: bool
    discount_percentage: float
    discount_reason: Optional[str]
    preferred_communication_language: str
    send_combined_reports: bool
    send_combined_invoices: bool
    special_circumstances: Optional[str]
    support_services_required: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# =====================================================
# GUARDIAN RELATIONSHIP SCHEMAS
# =====================================================

class GuardianRelationshipCreateEnhanced(BaseModel):
    """Enhanced schema for creating guardian-student relationship"""
    guardian_user_id: UUID
    relationship_type: RelationshipType
    relationship_description: Optional[str] = Field(None, max_length=100)
    is_biological: bool = True
    is_legal_guardian: bool = True
    
    # Contact preferences
    is_primary_contact: bool = False
    is_emergency_contact: bool = True
    contact_priority: int = Field(default=1, ge=1, le=10)
    preferred_contact_method: ContactMethod = ContactMethod.SMS
    
    # Alternative contact information
    alternative_phone: Optional[str] = Field(None, max_length=20)
    work_phone: Optional[str] = Field(None, max_length=20)
    work_email: Optional[str] = Field(None, max_length=255)
    work_address: Optional[str] = Field(None, max_length=500)
    
    # Employment information
    employer: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=100)
    work_schedule: Optional[str] = Field(None, max_length=200)
    monthly_income_range: Optional[str] = Field(None, max_length=50)
    
    # Permissions and responsibilities
    has_pickup_permission: bool = True
    has_academic_access: bool = True
    has_medical_access: bool = True
    has_disciplinary_access: bool = True
    can_authorize_field_trips: bool = True
    can_receive_communications: bool = True
    
    # Financial responsibility
    has_financial_responsibility: bool = True
    financial_responsibility_type: FinancialResponsibilityType = FinancialResponsibilityType.FULL
    financial_responsibility_percentage: float = Field(default=100.0, ge=0, le=100)
    payment_method_preference: Optional[str] = Field(None, max_length=50)
    
    # Communication preferences
    receive_academic_reports: bool = True
    receive_financial_notices: bool = True
    receive_disciplinary_notices: bool = True
    receive_medical_alerts: bool = True
    receive_general_announcements: bool = True
    communication_frequency: str = Field(default="immediate", pattern=r'^(immediate|daily|weekly)$')
    
    # Living arrangement
    student_lives_with: bool = False
    custody_type: Optional[str] = Field(None, max_length=50)
    custody_notes: Optional[str] = Field(None, max_length=1000)
    
    # Special notes
    special_instructions: Optional[str] = Field(None, max_length=1000)
    access_restrictions: Optional[str] = Field(None, max_length=1000)
    
    # Validity
    start_date: date = Field(default_factory=date.today)
    end_date: Optional[date] = None

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

class GuardianRelationshipUpdate(BaseModel):
    """Schema for updating guardian relationship"""
    relationship_type: Optional[RelationshipType] = None
    relationship_description: Optional[str] = Field(None, max_length=100)
    is_legal_guardian: Optional[bool] = None
    
    # Contact preferences
    is_primary_contact: Optional[bool] = None
    is_emergency_contact: Optional[bool] = None
    contact_priority: Optional[int] = Field(None, ge=1, le=10)
    preferred_contact_method: Optional[ContactMethod] = None
    
    # Alternative contact information
    alternative_phone: Optional[str] = Field(None, max_length=20)
    work_phone: Optional[str] = Field(None, max_length=20)
    work_email: Optional[str] = Field(None, max_length=255)
    work_address: Optional[str] = Field(None, max_length=500)
    
    # Employment information
    employer: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=100)
    work_schedule: Optional[str] = Field(None, max_length=200)
    monthly_income_range: Optional[str] = Field(None, max_length=50)
    
    # Permissions
    has_pickup_permission: Optional[bool] = None
    has_academic_access: Optional[bool] = None
    has_medical_access: Optional[bool] = None
    has_disciplinary_access: Optional[bool] = None
    can_authorize_field_trips: Optional[bool] = None
    
    # Financial responsibility
    has_financial_responsibility: Optional[bool] = None
    financial_responsibility_type: Optional[FinancialResponsibilityType] = None
    financial_responsibility_percentage: Optional[float] = Field(None, ge=0, le=100)
    
    # Communication preferences
    receive_academic_reports: Optional[bool] = None
    receive_financial_notices: Optional[bool] = None
    receive_disciplinary_notices: Optional[bool] = None
    receive_medical_alerts: Optional[bool] = None
    communication_frequency: Optional[str] = Field(None, pattern=r'^(immediate|daily|weekly)$')
    
    # Living arrangement
    student_lives_with: Optional[bool] = None
    custody_type: Optional[str] = Field(None, max_length=50)
    custody_notes: Optional[str] = Field(None, max_length=1000)
    
    # Special notes
    special_instructions: Optional[str] = Field(None, max_length=1000)
    access_restrictions: Optional[str] = Field(None, max_length=1000)
    
    # Status
    is_active: Optional[bool] = None
    end_date: Optional[date] = None
    termination_reason: Optional[str] = Field(None, max_length=200)

class GuardianRelationshipResponseEnhanced(BaseModel):
    """Enhanced schema for guardian relationship response"""
    id: UUID
    student_id: UUID
    guardian_user_id: UUID
    relationship_type: RelationshipType
    relationship_description: Optional[str]
    is_biological: bool
    is_legal_guardian: bool
    
    # Contact preferences
    is_primary_contact: bool
    is_emergency_contact: bool
    contact_priority: int
    preferred_contact_method: ContactMethod
    
    # Alternative contact information
    alternative_phone: Optional[str]
    work_phone: Optional[str]
    work_email: Optional[str]
    work_address: Optional[str]
    
    # Employment information
    employer: Optional[str]
    job_title: Optional[str]
    work_schedule: Optional[str]
    monthly_income_range: Optional[str]
    
    # Permissions and responsibilities
    has_pickup_permission: bool
    has_academic_access: bool
    has_medical_access: bool
    has_disciplinary_access: bool
    can_authorize_field_trips: bool
    can_receive_communications: bool
    
    # Financial responsibility
    has_financial_responsibility: bool
    financial_responsibility_type: FinancialResponsibilityType
    financial_responsibility_percentage: float
    payment_method_preference: Optional[str]
    
    # Communication preferences
    receive_academic_reports: bool
    receive_financial_notices: bool
    receive_disciplinary_notices: bool
    receive_medical_alerts: bool
    receive_general_announcements: bool
    communication_frequency: str
    
    # Living arrangement
    student_lives_with: bool
    custody_type: Optional[str]
    custody_notes: Optional[str]
    
    # Verification
    is_verified: bool
    verified_by: Optional[UUID]
    verification_date: Optional[datetime]
    
    # Special notes
    special_instructions: Optional[str]
    access_restrictions: Optional[str]
    
    # Status
    is_active: bool
    start_date: date
    end_date: Optional[date]
    termination_reason: Optional[str]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    created_by: UUID

    class Config:
        from_attributes = True

# =====================================================
# EMERGENCY CONTACT SCHEMAS
# =====================================================

class EmergencyContactCreate(BaseModel):
    """Schema for creating emergency contact"""
    full_name: str = Field(..., min_length=2, max_length=200)
    relationship_to_student: str = Field(..., min_length=2, max_length=100)
    primary_phone: str = Field(..., min_length=10, max_length=20)
    secondary_phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=1000)
    
    # Emergency contact details
    priority_order: int = Field(default=1, ge=1, le=10)
    available_24_7: bool = True
    availability_notes: Optional[str] = Field(None, max_length=500)
    
    # Permissions
    can_pickup_student: bool = False
    can_authorize_medical_treatment: bool = False
    can_receive_student_information: bool = True
    
    # Additional information
    medical_knowledge: Optional[str] = Field(None, max_length=1000)
    special_instructions: Optional[str] = Field(None, max_length=1000)
    languages_spoken: Optional[str] = Field(None, max_length=200)

class EmergencyContactUpdate(BaseModel):
    """Schema for updating emergency contact"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    relationship_to_student: Optional[str] = Field(None, min_length=2, max_length=100)
    primary_phone: Optional[str] = Field(None, min_length=10, max_length=20)
    secondary_phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=1000)
    
    priority_order: Optional[int] = Field(None, ge=1, le=10)
    available_24_7: Optional[bool] = None
    availability_notes: Optional[str] = Field(None, max_length=500)
    
    can_pickup_student: Optional[bool] = None
    can_authorize_medical_treatment: Optional[bool] = None
    can_receive_student_information: Optional[bool] = None
    
    medical_knowledge: Optional[str] = Field(None, max_length=1000)
    special_instructions: Optional[str] = Field(None, max_length=1000)
    languages_spoken: Optional[str] = Field(None, max_length=200)
    
    is_active: Optional[bool] = None

class EmergencyContactResponse(BaseModel):
    """Schema for emergency contact response"""
    id: UUID
    student_id: UUID
    full_name: str
    relationship_to_student: str
    primary_phone: str
    secondary_phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    
    priority_order: int
    available_24_7: bool
    availability_notes: Optional[str]
    
    can_pickup_student: bool
    can_authorize_medical_treatment: bool
    can_receive_student_information: bool
    
    identity_verified: bool
    verification_method: Optional[str]
    verification_date: Optional[date]
    
    medical_knowledge: Optional[str]
    special_instructions: Optional[str]
    languages_spoken: Optional[str]
    
    is_active: bool
    last_contacted: Optional[datetime]
    contact_successful: Optional[bool]
    
    created_at: datetime
    updated_at: datetime
    created_by: UUID

    class Config:
        from_attributes = True

# =====================================================
# FAMILY MEMBERSHIP SCHEMAS
# =====================================================

class StudentFamilyMembershipCreate(BaseModel):
    """Schema for adding student to family"""
    family_group_id: UUID
    relationship_to_family: str = Field(default="child", max_length=50)
    is_primary_student: bool = False
    lives_with_family: bool = True
    custody_arrangement: Optional[str] = Field(None, max_length=100)
    custody_percentage: float = Field(default=100.0, ge=0, le=100)
    family_pays_fees: bool = True
    fee_responsibility_percentage: float = Field(default=100.0, ge=0, le=100)
    start_date: date = Field(default_factory=date.today)
    end_date: Optional[date] = None

class GuardianFamilyMembershipCreate(BaseModel):
    """Schema for adding guardian to family"""
    family_group_id: UUID
    role_in_family: str = Field(..., max_length=50)
    is_head_of_household: bool = False
    is_primary_contact: bool = False
    can_make_academic_decisions: bool = True
    can_make_medical_decisions: bool = True
    can_make_financial_decisions: bool = True
    financial_contribution_percentage: float = Field(default=50.0, ge=0, le=100)
    is_primary_payer: bool = False

# =====================================================
# COMPREHENSIVE FAMILY VIEW SCHEMAS
# =====================================================

class FamilyOverviewResponse(BaseModel):
    """Comprehensive family overview"""
    family_group: FamilyGroupResponse
    students: List[Dict[str, Any]]  # Student details with membership info
    guardians: List[Dict[str, Any]]  # Guardian details with membership info
    emergency_contacts: List[EmergencyContactResponse]
    total_outstanding_fees: Optional[float] = None
    payment_status: Optional[str] = None

class GuardianStudentSummary(BaseModel):
    """Summary of all students for a guardian"""
    guardian_user_id: UUID
    total_students: int
    students_by_school: Dict[str, List[Dict[str, Any]]]
    total_outstanding_fees: Optional[float] = None
    upcoming_payment_due_dates: Optional[List[date]] = None