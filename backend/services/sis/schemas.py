# =====================================================
# SIS Module - Pydantic Models and Schemas
# File: backend/services/sis/schemas.py
# =====================================================

from pydantic import BaseModel, Field, EmailStr, validator, root_validator
from typing import List, Optional, Dict, Any, Union
from datetime import date, datetime, time
from enum import Enum
from uuid import UUID
import re

# =====================================================
# ENUMS FOR VALIDATION
# =====================================================

class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"

class StudentStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRANSFERRED = "transferred"
    GRADUATED = "graduated"
    EXPELLED = "expelled"
    DECEASED = "deceased"

class HomeLanguage(str, Enum):
    ENGLISH = "English"
    SHONA = "Shona"
    NDEBELE = "Ndebele"
    TONGA = "Tonga"
    KALANGA = "Kalanga"
    NAMBYA = "Nambya"
    OTHER = "Other"

class BloodType(str, Enum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"

class IncidentSeverity(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    SERIOUS = "serious"
    SEVERE = "severe"

class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"
    SICK = "sick"
    SUSPENDED = "suspended"

class ContactMethod(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    CALL = "call"

class DocumentType(str, Enum):
    BIRTH_CERTIFICATE = "birth_certificate"
    PASSPORT = "passport"
    NATIONAL_ID = "national_id"
    MEDICAL_CERTIFICATE = "medical_certificate"
    PREVIOUS_SCHOOL_REPORT = "previous_school_report"
    IMMUNIZATION_RECORD = "immunization_record"
    COURT_ORDER = "court_order"
    RECOMMENDATION_LETTER = "recommendation_letter"
    OTHER = "other"

# =====================================================
# SHARED/COMMON SCHEMAS
# =====================================================

class ZimbabweAddress(BaseModel):
    """Standard Zimbabwe address format"""
    street: str = Field(..., min_length=5, max_length=200, description="Street address")
    suburb: str = Field(..., min_length=2, max_length=100, description="Suburb/Area")
    city: str = Field(..., min_length=2, max_length=100, description="City/Town")
    province: str = Field(..., description="Zimbabwe province")
    postal_code: Optional[str] = Field(None, max_length=10, description="Postal code")

    @validator('province')
    def validate_zimbabwe_province(cls, v):
        valid_provinces = [
            'Harare', 'Bulawayo', 'Manicaland', 'Mashonaland Central',
            'Mashonaland East', 'Mashonaland West', 'Masvingo',
            'Matabeleland North', 'Matabeleland South', 'Midlands'
        ]
        if v not in valid_provinces:
            raise ValueError(f'Invalid Zimbabwe province. Must be one of: {", ".join(valid_provinces)}')
        return v

class EmergencyContact(BaseModel):
    """Emergency contact information"""
    name: str = Field(..., min_length=2, max_length=100)
    relationship: str = Field(..., min_length=2, max_length=50)
    phone: str = Field(..., description="Phone number in international format")
    alternative_phone: Optional[str] = None
    is_primary: bool = False
    can_pickup: bool = True
    address: Optional[str] = Field(None, max_length=500)

    @validator('phone', 'alternative_phone')
    def validate_zimbabwe_phone(cls, v):
        if v is None:
            return v
        # Zimbabwe phone number validation: +263 followed by area code and number
        pattern = r'^\+263[0-9]{9}$|^0[0-9]{9}$'
        if not re.match(pattern, v.replace(' ', '').replace('-', '')):
            raise ValueError('Invalid Zimbabwe phone number format. Use +263XXXXXXXXX or 0XXXXXXXXX')
        return v

class MedicalCondition(BaseModel):
    """Medical condition information"""
    condition: str = Field(..., min_length=2, max_length=100)
    severity: str = Field(..., pattern=r'^(Mild|Moderate|Severe)$')
    medication: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None, max_length=500)
    diagnosed_date: Optional[date] = None
    doctor_name: Optional[str] = Field(None, max_length=100)

class Allergy(BaseModel):
    """Allergy information"""
    allergen: str = Field(..., min_length=2, max_length=100)
    reaction: str = Field(..., min_length=5, max_length=200)
    severity: str = Field(..., pattern=r'^(Mild|Moderate|Severe|Life-threatening)$')
    epipen_required: bool = False
    treatment: Optional[str] = Field(None, max_length=200)

# =====================================================
# STUDENT SCHEMAS
# =====================================================

class StudentBase(BaseModel):
    """Base student information"""
    first_name: str = Field(..., min_length=2, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    preferred_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: date = Field(...)
    gender: Gender
    nationality: str = Field(default="Zimbabwean", max_length=100)
    home_language: Optional[HomeLanguage] = None
    religion: Optional[str] = Field(None, max_length=100)
    tribe: Optional[str] = Field(None, max_length=100)

    @validator('date_of_birth')
    def validate_age(cls, v):
        from datetime import date
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 3 or age > 25:
            raise ValueError('Student age must be between 3 and 25 years')
        return v

class StudentContactInfo(BaseModel):
    """Student contact information"""
    mobile_number: Optional[str] = Field(None, description="Student's mobile number")
    email: Optional[EmailStr] = None
    residential_address: ZimbabweAddress
    postal_address: Optional[ZimbabweAddress] = None

    @validator('mobile_number')
    def validate_mobile(cls, v):
        if v:
            pattern = r'^\+263[0-9]{9}$|^0[0-9]{9}$'
            if not re.match(pattern, v.replace(' ', '').replace('-', '')):
                raise ValueError('Invalid Zimbabwe mobile number format')
        return v

class StudentAcademicInfo(BaseModel):
    """Student academic information"""
    current_grade_level: int = Field(..., ge=1, le=13, description="Grade level 1-13")
    current_class_id: Optional[UUID] = None
    enrollment_date: date = Field(default_factory=date.today)
    expected_graduation_date: Optional[date] = None
    previous_school_name: Optional[str] = Field(None, max_length=255)
    previous_school_address: Optional[str] = Field(None, max_length=500)
    transfer_reason: Optional[str] = Field(None, max_length=500)

    @validator('expected_graduation_date')
    def validate_graduation_date(cls, v, values):
        if v and 'enrollment_date' in values:
            enrollment = values['enrollment_date']
            if v <= enrollment:
                raise ValueError('Graduation date must be after enrollment date')
        return v

class StudentMedicalInfo(BaseModel):
    """Student medical information"""
    blood_type: Optional[BloodType] = None
    medical_conditions: List[MedicalCondition] = Field(default_factory=list)
    allergies: List[Allergy] = Field(default_factory=list)
    medications: List[Dict[str, Any]] = Field(default_factory=list)
    medical_aid_provider: Optional[str] = Field(None, max_length=100)
    medical_aid_number: Optional[str] = Field(None, max_length=50)
    special_needs: Optional[Dict[str, Any]] = None
    dietary_requirements: Optional[str] = Field(None, max_length=500)

class StudentCreate(BaseModel):
    """Schema for creating a new student"""
    # Basic Information
    first_name: str = Field(..., min_length=2, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    preferred_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: date = Field(...)
    gender: Gender
    nationality: str = Field(default="Zimbabwean", max_length=100)
    home_language: Optional[HomeLanguage] = None
    religion: Optional[str] = Field(None, max_length=100)
    tribe: Optional[str] = Field(None, max_length=100)

    # Contact Information
    mobile_number: Optional[str] = None
    email: Optional[EmailStr] = None
    residential_address: ZimbabweAddress
    postal_address: Optional[ZimbabweAddress] = None

    # Academic Information
    current_grade_level: int = Field(..., ge=1, le=13)
    current_class_id: Optional[UUID] = None
    enrollment_date: date = Field(default_factory=date.today)
    previous_school_name: Optional[str] = Field(None, max_length=255)
    transfer_reason: Optional[str] = Field(None, max_length=500)

    # Medical Information
    blood_type: Optional[BloodType] = None
    medical_conditions: List[MedicalCondition] = Field(default_factory=list)
    allergies: List[Allergy] = Field(default_factory=list)
    medical_aid_provider: Optional[str] = Field(None, max_length=100)
    medical_aid_number: Optional[str] = Field(None, max_length=50)
    special_needs: Optional[Dict[str, Any]] = None
    dietary_requirements: Optional[str] = Field(None, max_length=500)

    # Emergency Contacts (minimum 2 required)
    emergency_contacts: List[EmergencyContact] = Field(..., min_items=2, max_items=5)

    # Additional Information
    transport_needs: Optional[str] = Field(None, max_length=100)
    identifying_marks: Optional[str] = Field(None, max_length=500)

    @validator('emergency_contacts')
    def validate_emergency_contacts(cls, v):
        if len(v) < 2:
            raise ValueError('At least 2 emergency contacts are required')
        
        primary_contacts = [contact for contact in v if contact.is_primary]
        if len(primary_contacts) != 1:
            raise ValueError('Exactly one emergency contact must be marked as primary')
        
        # Check for duplicate phone numbers
        phones = [contact.phone for contact in v if contact.phone]
        if len(phones) != len(set(phones)):
            raise ValueError('Emergency contacts cannot have duplicate phone numbers')
        
        return v

    @validator('mobile_number')
    def validate_mobile(cls, v):
        if v:
            pattern = r'^\+263[0-9]{9}$|^0[0-9]{9}$'
            if not re.match(pattern, v.replace(' ', '').replace('-', '')):
                raise ValueError('Invalid Zimbabwe mobile number format')
        return v

class StudentUpdate(BaseModel):
    """Schema for updating student information"""
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    preferred_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[Gender] = None
    home_language: Optional[HomeLanguage] = None
    religion: Optional[str] = Field(None, max_length=100)
    mobile_number: Optional[str] = None
    email: Optional[EmailStr] = None
    current_grade_level: Optional[int] = Field(None, ge=1, le=13)
    current_class_id: Optional[UUID] = None
    status: Optional[StudentStatus] = None
    residential_address: Optional[ZimbabweAddress] = None
    postal_address: Optional[ZimbabweAddress] = None
    medical_conditions: Optional[List[MedicalCondition]] = None
    allergies: Optional[List[Allergy]] = None
    emergency_contacts: Optional[List[EmergencyContact]] = None
    special_needs: Optional[Dict[str, Any]] = None
    dietary_requirements: Optional[str] = Field(None, max_length=500)
    transport_needs: Optional[str] = Field(None, max_length=100)

class StudentResponse(BaseModel):
    """Complete student response schema"""
    id: UUID
    school_id: UUID
    user_id: Optional[UUID]
    student_number: str
    zimsec_number: Optional[str]
    
    # Personal Information
    first_name: str
    middle_name: Optional[str]
    last_name: str
    preferred_name: Optional[str]
    date_of_birth: date
    gender: Gender
    nationality: str
    home_language: Optional[HomeLanguage]
    religion: Optional[str]
    tribe: Optional[str]
    
    # Contact Information
    mobile_number: Optional[str]
    email: Optional[str]
    residential_address: Dict[str, Any]
    postal_address: Optional[Dict[str, Any]]
    
    # Academic Information
    current_grade_level: Optional[int]
    current_class_id: Optional[UUID]
    enrollment_date: date
    expected_graduation_date: Optional[date]
    status: StudentStatus
    
    # Points and Behavior
    disciplinary_points: int
    merit_points: int
    
    # Medical Information (basic only for privacy)
    blood_type: Optional[BloodType]
    medical_aid_provider: Optional[str]
    has_medical_conditions: bool
    has_allergies: bool
    special_needs: Optional[Dict[str, Any]]
    dietary_requirements: Optional[str]
    
    # System Information
    created_at: datetime
    updated_at: datetime
    
    # Computed Properties
    age: Optional[int] = None
    full_name: str = None

    class Config:
        from_attributes = True

    @validator('full_name', always=True)
    def compute_full_name(cls, v, values):
        if 'first_name' in values and 'last_name' in values:
            middle = f" {values.get('middle_name')}" if values.get('middle_name') else ""
            return f"{values['first_name']}{middle} {values['last_name']}"
        return v

    @validator('age', always=True)
    def compute_age(cls, v, values):
        if 'date_of_birth' in values:
            today = date.today()
            dob = values['date_of_birth']
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return v

# =====================================================
# GUARDIAN SCHEMAS
# =====================================================

class GuardianRelationshipCreate(BaseModel):
    """Schema for creating guardian-student relationship"""
    guardian_user_id: UUID
    relationship: str = Field(..., min_length=2, max_length=50)
    is_primary_contact: bool = False
    is_emergency_contact: bool = True
    contact_priority: int = Field(default=1, ge=1, le=10)
    has_pickup_permission: bool = True
    has_academic_access: bool = True
    has_financial_responsibility: bool = True
    financial_responsibility_percentage: float = Field(default=100.0, ge=0, le=100)
    preferred_contact_method: ContactMethod = ContactMethod.SMS
    alternative_phone: Optional[str] = None
    work_phone: Optional[str] = None
    employer: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=100)

class GuardianRelationshipResponse(BaseModel):
    """Guardian relationship response"""
    id: UUID
    student_id: UUID
    guardian_user_id: UUID
    relationship: str
    is_primary_contact: bool
    is_emergency_contact: bool
    contact_priority: int
    has_pickup_permission: bool
    has_academic_access: bool
    has_financial_responsibility: bool
    financial_responsibility_percentage: float
    preferred_contact_method: ContactMethod
    alternative_phone: Optional[str]
    work_phone: Optional[str]
    employer: Optional[str]
    job_title: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# =====================================================
# DISCIPLINARY SCHEMAS
# =====================================================

class DisciplinaryIncidentCreate(BaseModel):
    """Schema for creating disciplinary incident"""
    student_id: UUID
    incident_date: date = Field(default_factory=date.today)
    incident_time: Optional[time] = None
    incident_type: str = Field(..., min_length=5, max_length=100)
    severity: IncidentSeverity
    description: str = Field(..., min_length=10, max_length=1000)
    location: Optional[str] = Field(None, max_length=100)
    witnesses: Optional[str] = Field(None, max_length=500)
    action_taken: str = Field(..., min_length=10, max_length=500)
    points_deducted: int = Field(default=0, ge=0, le=50)
    suspension_days: int = Field(default=0, ge=0, le=30)
    detention_hours: int = Field(default=0, ge=0, le=40)
    counseling_required: bool = False
    parent_meeting_required: bool = False
    behavioral_contract_required: bool = False

    @validator('incident_date')
    def validate_incident_date(cls, v):
        if v > date.today():
            raise ValueError('Incident date cannot be in the future')
        return v

class DisciplinaryIncidentResponse(BaseModel):
    """Disciplinary incident response"""
    id: UUID
    student_id: UUID
    incident_date: date
    incident_time: Optional[time]
    incident_type: str
    severity: IncidentSeverity
    description: str
    location: Optional[str]
    action_taken: str
    points_deducted: int
    suspension_days: int
    detention_hours: int
    status: str
    parent_notified: bool
    parent_notification_date: Optional[datetime]
    reported_by: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# =====================================================
# ATTENDANCE SCHEMAS
# =====================================================

class AttendanceRecordCreate(BaseModel):
    """Schema for creating attendance record"""
    student_id: UUID
    attendance_date: date = Field(default_factory=date.today)
    period: str = Field(..., min_length=1, max_length=20)
    status: AttendanceStatus
    arrival_time: Optional[time] = None
    departure_time: Optional[time] = None
    absence_reason: Optional[str] = Field(None, max_length=100)
    excuse_provided: bool = False
    notes: Optional[str] = Field(None, max_length=500)

class AttendanceRecordResponse(BaseModel):
    """Attendance record response"""
    id: UUID
    student_id: UUID
    attendance_date: date
    period: str
    status: AttendanceStatus
    arrival_time: Optional[time]
    absence_reason: Optional[str]
    excuse_provided: bool
    parent_notified: bool
    marked_by: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# =====================================================
# HEALTH RECORD SCHEMAS
# =====================================================

class HealthRecordCreate(BaseModel):
    """Schema for creating health record"""
    student_id: UUID
    record_type: str = Field(..., pattern=r'^(checkup|illness|injury|vaccination|screening|medication_change)$')
    record_date: date = Field(default_factory=date.today)
    recorded_by: str = Field(..., min_length=2, max_length=100)
    symptoms: Optional[str] = Field(None, max_length=500)
    diagnosis: Optional[str] = Field(None, max_length=500)
    treatment_given: Optional[str] = Field(None, max_length=500)
    temperature_celsius: Optional[float] = Field(None, ge=30, le=45)
    blood_pressure: Optional[str] = Field(None, pattern=r'^\d{2,3}/\d{2,3}$')
    pulse_rate: Optional[int] = Field(None, ge=40, le=200)
    weight_kg: Optional[float] = Field(None, ge=1, le=200)
    height_cm: Optional[int] = Field(None, ge=50, le=250)
    recommendations: Optional[str] = Field(None, max_length=1000)
    follow_up_required: bool = False
    follow_up_date: Optional[date] = None
    parent_contacted: bool = False
    sent_home: bool = False

class HealthRecordResponse(BaseModel):
    """Health record response"""
    id: UUID
    student_id: UUID
    record_type: str
    record_date: date
    recorded_by: str
    symptoms: Optional[str]
    diagnosis: Optional[str]
    treatment_given: Optional[str]
    temperature_celsius: Optional[float]
    recommendations: Optional[str]
    follow_up_required: bool
    parent_contacted: bool
    sent_home: bool
    created_at: datetime

    class Config:
        from_attributes = True

# =====================================================
# DOCUMENT SCHEMAS
# =====================================================

class StudentDocumentCreate(BaseModel):
    """Schema for uploading student document"""
    student_id: UUID
    document_type: DocumentType
    document_name: str = Field(..., min_length=1, max_length=255)
    file_url: str = Field(..., description="URL to the uploaded file")
    file_size_bytes: int = Field(..., gt=0)
    file_format: str = Field(..., min_length=2, max_length=10)
    is_confidential: bool = False
    access_level: str = Field(default="school", pattern=r'^(student|guardian|teacher|admin|school)$')
    description: Optional[str] = Field(None, max_length=500)
    expiry_date: Optional[date] = None

class StudentDocumentResponse(BaseModel):
    """Student document response"""
    id: UUID
    student_id: UUID
    document_type: DocumentType
    document_name: str
    file_url: str
    file_size_bytes: int
    file_format: str
    is_verified: bool
    verified_by: Optional[UUID]
    verification_date: Optional[datetime]
    expiry_date: Optional[date]
    is_confidential: bool
    access_level: str
    description: Optional[str]
    uploaded_by: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# =====================================================
# SEARCH AND FILTER SCHEMAS
# =====================================================

class StudentSearchFilters(BaseModel):
    """Filters for student search"""
    grade_level: Optional[int] = Field(None, ge=1, le=13)
    class_id: Optional[UUID] = None
    status: Optional[StudentStatus] = None
    gender: Optional[Gender] = None
    home_language: Optional[HomeLanguage] = None
    has_medical_conditions: Optional[bool] = None
    has_special_needs: Optional[bool] = None
    enrollment_year: Optional[int] = None
    age_min: Optional[int] = Field(None, ge=3, le=25)
    age_max: Optional[int] = Field(None, ge=3, le=25)

class StudentSearchRequest(BaseModel):
    """Student search request"""
    search_query: Optional[str] = Field(None, min_length=2, max_length=100, description="Search in names and student number")
    filters: Optional[StudentSearchFilters] = None
    sort_by: str = Field(default="last_name", pattern=r'^(first_name|last_name|student_number|enrollment_date|grade_level)$')
    sort_order: str = Field(default="asc", pattern=r'^(asc|desc)$')
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

class StudentSearchResponse(BaseModel):
    """Student search response"""
    students: List[StudentResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool