"""
Student Information System Models
Database models for student-related entities (students, attendance, enrollment)
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, JSON, ForeignKey, Date, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()

class Student(Base):
    """Student model"""
    __tablename__ = "students"
    __table_args__ = {"schema": "sis"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Student identification
    student_number = Column(String(50), nullable=False, index=True)  # School-specific ID
    national_id = Column(String(50), index=True)  # National ID/Birth Certificate
    
    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10), nullable=False)  # male, female, other
    
    # Contact information
    email = Column(String(255), index=True)
    phone = Column(String(20))
    address = Column(Text)
    city = Column(String(100))
    province = Column(String(100))
    postal_code = Column(String(20))
    
    # Academic information
    current_class_id = Column(UUID(as_uuid=True))  # References academic.classes
    current_grade_level = Column(String(20))  # Grade_1, Form_1, etc.
    admission_date = Column(Date, nullable=False)
    graduation_date = Column(Date)
    
    # Student status
    enrollment_status = Column(String(20), default="active")  # active, inactive, graduated, transferred, expelled
    is_active = Column(Boolean, default=True)
    
    # Parent/Guardian information
    primary_guardian_id = Column(UUID(as_uuid=True))  # References platform.users
    secondary_guardian_id = Column(UUID(as_uuid=True))  # References platform.users
    emergency_contact = Column(JSON, default={})  # Emergency contact details
    
    # Medical information
    medical_conditions = Column(JSON, default=[])
    allergies = Column(JSON, default=[])
    medications = Column(JSON, default=[])
    emergency_medical_info = Column(Text)
    
    # Additional information
    religion = Column(String(50))
    nationality = Column(String(50))
    language_spoken = Column(String(50))
    previous_school = Column(String(255))
    
    # Student metadata
    student_metadata = Column(JSON, default={})  # Additional custom fields
    
    # Profile photo
    profile_photo_url = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Student(id={self.id}, student_number='{self.student_number}', name='{self.first_name} {self.last_name}')>"

class Enrollment(Base):
    """Student enrollment history"""
    __tablename__ = "enrollments"
    __table_args__ = {"schema": "sis"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Student and academic details
    student_id = Column(UUID(as_uuid=True), ForeignKey('sis.students.id'), nullable=False, index=True)
    academic_year_id = Column(UUID(as_uuid=True), nullable=False)  # References academic.academic_years
    class_id = Column(UUID(as_uuid=True), nullable=False)  # References academic.classes
    
    # Enrollment details
    enrollment_date = Column(Date, nullable=False)
    enrollment_type = Column(String(20), default="new")  # new, transfer, returning, promotion
    enrollment_status = Column(String(20), default="active")  # active, withdrawn, completed, transferred
    
    # Previous academic information (for transfers)
    previous_school = Column(String(255))
    previous_grade = Column(String(20))
    transfer_reason = Column(Text)
    
    # Enrollment documents
    documents_submitted = Column(JSON, default=[])  # List of required documents
    documents_verified = Column(Boolean, default=False)
    verified_by = Column(UUID(as_uuid=True))  # References platform.users
    verification_date = Column(DateTime(timezone=True))
    
    # Exit information
    exit_date = Column(Date)
    exit_reason = Column(String(100))  # graduation, transfer, withdrawal, expulsion
    exit_destination = Column(String(255))  # Next school/institution
    
    # Enrollment processed by
    enrolled_by = Column(UUID(as_uuid=True), nullable=False)  # References platform.users
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Enrollment(id={self.id}, student_id={self.student_id}, status='{self.enrollment_status}')>"

class AttendanceRecord(Base):
    """Daily attendance records"""
    __tablename__ = "attendance_records"
    __table_args__ = {"schema": "sis"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Student and date
    student_id = Column(UUID(as_uuid=True), ForeignKey('sis.students.id'), nullable=False, index=True)
    attendance_date = Column(Date, nullable=False, index=True)
    
    # Class information
    class_id = Column(UUID(as_uuid=True), nullable=False)  # References academic.classes
    academic_year_id = Column(UUID(as_uuid=True))
    term_id = Column(UUID(as_uuid=True))
    
    # Attendance status
    status = Column(String(20), nullable=False)  # present, absent, late, excused
    check_in_time = Column(Time)
    check_out_time = Column(Time)
    
    # Absence details
    absence_reason = Column(String(100))  # sick, family_emergency, disciplinary, other
    is_excused = Column(Boolean, default=False)
    excuse_note = Column(Text)
    medical_certificate = Column(Boolean, default=False)
    
    # Period-specific attendance (for secondary schools)
    period_attendance = Column(JSON, default={})  # {"period_1": "present", "period_2": "absent"}
    
    # Recorded by
    recorded_by = Column(UUID(as_uuid=True), nullable=False)  # References platform.users (teacher)
    recording_method = Column(String(20), default="manual")  # manual, biometric, rfid, app
    
    # Parent notification
    parent_notified = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<AttendanceRecord(id={self.id}, student_id={self.student_id}, date={self.attendance_date}, status='{self.status}')>"

class DisciplinaryRecord(Base):
    """Student disciplinary records"""
    __tablename__ = "disciplinary_records"
    __table_args__ = {"schema": "sis"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Student information
    student_id = Column(UUID(as_uuid=True), ForeignKey('sis.students.id'), nullable=False, index=True)
    incident_date = Column(Date, nullable=False)
    
    # Incident details
    incident_type = Column(String(50), nullable=False)  # misconduct, academic_dishonesty, attendance, other
    severity_level = Column(String(20), default="minor")  # minor, major, severe
    description = Column(Text, nullable=False)
    location = Column(String(100))  # Where incident occurred
    
    # People involved
    reported_by = Column(UUID(as_uuid=True), nullable=False)  # References platform.users (teacher/staff)
    witnesses = Column(JSON, default=[])  # List of witness IDs
    other_students_involved = Column(JSON, default=[])  # Other student IDs
    
    # Actions taken
    action_taken = Column(String(100))  # warning, detention, suspension, expulsion, counseling
    action_details = Column(Text)
    action_date = Column(Date)
    action_by = Column(UUID(as_uuid=True))  # References platform.users
    
    # Follow-up
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(Date)
    follow_up_notes = Column(Text)
    follow_up_by = Column(UUID(as_uuid=True))
    
    # Parent communication
    parent_contacted = Column(Boolean, default=False)
    parent_contact_date = Column(DateTime(timezone=True))
    parent_contact_method = Column(String(20))  # phone, email, meeting, letter
    parent_response = Column(Text)
    
    # Resolution
    resolution_status = Column(String(20), default="open")  # open, resolved, escalated
    resolution_date = Column(Date)
    resolution_notes = Column(Text)
    
    # Supporting documents
    attachments = Column(JSON, default=[])  # Photos, documents, etc.
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<DisciplinaryRecord(id={self.id}, student_id={self.student_id}, type='{self.incident_type}')>"

class MedicalRecord(Base):
    """Student medical records"""
    __tablename__ = "medical_records"
    __table_args__ = {"schema": "sis"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Student information
    student_id = Column(UUID(as_uuid=True), ForeignKey('sis.students.id'), nullable=False, index=True)
    record_date = Column(Date, nullable=False)
    
    # Medical information
    record_type = Column(String(50), nullable=False)  # checkup, illness, injury, vaccination, allergy
    description = Column(Text, nullable=False)
    symptoms = Column(JSON, default=[])
    diagnosis = Column(Text)
    treatment = Column(Text)
    
    # Medical professional
    medical_professional = Column(String(255))  # Doctor/Nurse name
    medical_facility = Column(String(255))  # Hospital/Clinic
    
    # Medications
    prescribed_medications = Column(JSON, default=[])
    medication_instructions = Column(Text)
    
    # Follow-up
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(Date)
    follow_up_instructions = Column(Text)
    
    # Restrictions
    activity_restrictions = Column(JSON, default=[])  # ["no_sports", "limited_physical_activity"]
    dietary_restrictions = Column(JSON, default=[])
    
    # Emergency information
    emergency_action_plan = Column(Text)
    requires_emergency_medication = Column(Boolean, default=False)
    emergency_medication_details = Column(JSON, default={})
    
    # Parent notification
    parent_notified = Column(Boolean, default=False)
    notification_date = Column(DateTime(timezone=True))
    
    # Confidentiality
    confidential = Column(Boolean, default=True)
    access_level = Column(String(20), default="medical_staff")  # medical_staff, teachers, all
    
    # Recorded by
    recorded_by = Column(UUID(as_uuid=True), nullable=False)  # References platform.users
    
    # Supporting documents
    medical_documents = Column(JSON, default=[])  # Medical certificates, test results
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<MedicalRecord(id={self.id}, student_id={self.student_id}, type='{self.record_type}')>"

class StudentNote(Base):
    """General notes about students"""
    __tablename__ = "student_notes"
    __table_args__ = {"schema": "sis"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Student information
    student_id = Column(UUID(as_uuid=True), ForeignKey('sis.students.id'), nullable=False, index=True)
    
    # Note details
    note_type = Column(String(50), nullable=False)  # academic, behavioral, social, achievement, concern
    title = Column(String(255))
    content = Column(Text, nullable=False)
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    
    # Visibility and sharing
    visibility = Column(String(20), default="staff")  # private, staff, teachers, parents
    shared_with = Column(JSON, default=[])  # Specific user IDs who can see this note
    
    # Follow-up
    requires_follow_up = Column(Boolean, default=False)
    follow_up_date = Column(Date)
    follow_up_assigned_to = Column(UUID(as_uuid=True))  # References platform.users
    
    # Tags and categorization
    tags = Column(JSON, default=[])  # ["needs_support", "high_achiever", "leadership"]
    
    # Created by
    created_by = Column(UUID(as_uuid=True), nullable=False)  # References platform.users
    
    # Status
    is_active = Column(Boolean, default=True)
    is_archived = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<StudentNote(id={self.id}, student_id={self.student_id}, type='{self.note_type}')>"