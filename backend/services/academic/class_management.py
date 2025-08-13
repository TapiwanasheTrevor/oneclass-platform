"""
Academic Management Module - Class Management
Complete class/group management system for academic organization
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, Text, ForeignKey, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, ARRAY
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from fastapi import HTTPException, status
from pydantic import BaseModel, Field, validator
from enum import Enum

from shared.database import Base
from .models import AuditMixin, SoftDeleteMixin
from .exceptions import (
    AcademicValidationError,
    InvalidGradeLevelError,
    DuplicateSubjectError,
    create_error_response,
    log_academic_error
)


# =====================================================
# CLASS MANAGEMENT MODELS
# =====================================================

class ClassType(str, Enum):
    """Types of academic classes"""
    REGULAR = "regular"
    STREAMING = "streaming"  # Academic streaming (A, B, C streams)
    MIXED_ABILITY = "mixed_ability"
    REMEDIAL = "remedial"
    ADVANCED = "advanced"
    PRACTICAL = "practical"
    TUTORIAL = "tutorial"


class Class(Base, AuditMixin, SoftDeleteMixin):
    """Class/Group model for organizing students academically"""
    __tablename__ = "classes"
    __table_args__ = (
        UniqueConstraint('school_id', 'code', name='unique_class_code_per_school'),
        UniqueConstraint('school_id', 'name', 'academic_year', name='unique_class_name_per_year'),
        CheckConstraint('grade_level >= 1 AND grade_level <= 13', name='valid_zimbabwe_grade_level'),
        CheckConstraint('capacity > 0', name='positive_capacity'),
        CheckConstraint('current_enrollment >= 0', name='non_negative_enrollment'),
        CheckConstraint('current_enrollment <= capacity', name='enrollment_within_capacity'),
        Index('idx_classes_school_active', 'school_id', 'is_active'),
        Index('idx_classes_grade_level', 'grade_level'),
        Index('idx_classes_teacher', 'class_teacher_id'),
        {'extend_existing': True}
    )
    
    # Primary identification
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    school_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    
    # Class details
    code = Column(String(20), nullable=False, index=True)  # e.g., "1A", "F4B", "G7"
    name = Column(String(100), nullable=False)  # e.g., "Grade 1 Class A", "Form 4 Science"
    description = Column(Text)
    
    # Academic classification
    grade_level = Column(Integer, nullable=False, index=True)  # 1-13 for Zimbabwe system
    academic_year = Column(String(10), nullable=False, index=True)  # e.g., "2024"
    class_type = Column(String(50), default=ClassType.REGULAR, nullable=False)
    stream = Column(String(10))  # A, B, C for academic streaming
    
    # Capacity management
    capacity = Column(Integer, nullable=False, default=35)
    current_enrollment = Column(Integer, default=0, nullable=False)
    
    # Staff assignment
    class_teacher_id = Column(PostgresUUID(as_uuid=True), index=True)  # Primary class teacher
    deputy_teacher_id = Column(PostgresUUID(as_uuid=True))  # Deputy/assistant teacher
    
    # Schedule and location
    classroom = Column(String(50))  # Room assignment
    schedule_notes = Column(Text)
    
    # Zimbabwe specific
    curriculum_level = Column(String(20))  # "Primary", "ZJC", "O-Level", "A-Level"
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)


class ClassSubjectAssignment(Base, AuditMixin):
    """Assignment of subjects to classes"""
    __tablename__ = "class_subject_assignments"
    __table_args__ = (
        UniqueConstraint('class_id', 'subject_id', name='unique_class_subject'),
        Index('idx_class_subjects_class', 'class_id'),
        Index('idx_class_subjects_subject', 'subject_id'),
        {'extend_existing': True}
    )
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    class_id = Column(PostgresUUID(as_uuid=True), nullable=False)
    subject_id = Column(PostgresUUID(as_uuid=True), nullable=False)
    teacher_id = Column(PostgresUUID(as_uuid=True))  # Subject teacher for this class
    
    # Schedule details
    periods_per_week = Column(Integer, default=1)
    is_core = Column(Boolean, default=True)  # Core vs elective
    
    # Academic year context
    academic_year = Column(String(10), nullable=False)
    term_number = Column(Integer)  # 1, 2, 3 for Zimbabwe terms


class ClassStudentEnrollment(Base, AuditMixin):
    """Student enrollment in classes"""
    __tablename__ = "class_student_enrollments"
    __table_args__ = (
        UniqueConstraint('class_id', 'student_id', 'academic_year', name='unique_student_class_year'),
        Index('idx_enrollments_class', 'class_id'),
        Index('idx_enrollments_student', 'student_id'),
        Index('idx_enrollments_active', 'is_active'),
        {'extend_existing': True}
    )
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    class_id = Column(PostgresUUID(as_uuid=True), nullable=False)
    student_id = Column(PostgresUUID(as_uuid=True), nullable=False)
    
    # Enrollment details
    enrollment_date = Column(Date, default=date.today)
    withdrawal_date = Column(Date)
    academic_year = Column(String(10), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    enrollment_status = Column(String(20), default="active")  # active, withdrawn, transferred


# =====================================================
# CLASS MANAGEMENT SCHEMAS
# =====================================================

class ClassCreate(BaseModel):
    """Schema for creating a new class"""
    code: str = Field(..., min_length=1, max_length=20, description="Unique class code (e.g., '1A', 'F4B')")
    name: str = Field(..., min_length=1, max_length=100, description="Class name")
    description: Optional[str] = Field(None, max_length=500)
    grade_level: int = Field(..., ge=1, le=13, description="Zimbabwe grade level (1-13)")
    academic_year: str = Field(..., min_length=4, max_length=10, description="Academic year (e.g., '2024')")
    class_type: ClassType = Field(ClassType.REGULAR, description="Type of class")
    stream: Optional[str] = Field(None, max_length=10, description="Academic stream (A, B, C)")
    capacity: int = Field(35, ge=1, le=100, description="Maximum class capacity")
    class_teacher_id: Optional[UUID] = Field(None, description="Primary class teacher ID")
    deputy_teacher_id: Optional[UUID] = Field(None, description="Deputy teacher ID")
    classroom: Optional[str] = Field(None, max_length=50, description="Assigned classroom")
    curriculum_level: Optional[str] = Field(None, description="Curriculum level")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    @validator('grade_level')
    def validate_grade_level(cls, v):
        if v < 1 or v > 13:
            raise InvalidGradeLevelError(v)
        return v
    
    @validator('academic_year')
    def validate_academic_year(cls, v):
        try:
            year = int(v)
            if year < 2020 or year > 2030:
                raise ValueError("Academic year must be between 2020 and 2030")
        except ValueError:
            raise AcademicValidationError("Invalid academic year format", "academic_year", v)
        return v


class ClassUpdate(BaseModel):
    """Schema for updating a class"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    class_type: Optional[ClassType] = None
    capacity: Optional[int] = Field(None, ge=1, le=100)
    class_teacher_id: Optional[UUID] = None
    deputy_teacher_id: Optional[UUID] = None
    classroom: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class ClassResponse(BaseModel):
    """Schema for class response"""
    id: UUID
    school_id: UUID
    code: str
    name: str
    description: Optional[str]
    grade_level: int
    academic_year: str
    class_type: str
    stream: Optional[str]
    capacity: int
    current_enrollment: int
    class_teacher_id: Optional[UUID]
    deputy_teacher_id: Optional[UUID]
    classroom: Optional[str]
    curriculum_level: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ClassSubjectAssignmentCreate(BaseModel):
    """Schema for assigning subjects to classes"""
    subject_id: UUID = Field(..., description="Subject ID to assign")
    teacher_id: Optional[UUID] = Field(None, description="Teacher for this subject in this class")
    periods_per_week: int = Field(1, ge=1, le=10, description="Number of periods per week")
    is_core: bool = Field(True, description="Whether this is a core subject")
    term_number: Optional[int] = Field(None, ge=1, le=3, description="Specific term (1-3)")


class ClassEnrollmentCreate(BaseModel):
    """Schema for enrolling students in classes"""
    student_id: UUID = Field(..., description="Student ID to enroll")
    enrollment_date: date = Field(default_factory=date.today)
    academic_year: str = Field(..., description="Academic year for enrollment")


# =====================================================
# CLASS MANAGEMENT CRUD OPERATIONS
# =====================================================

async def create_class(
    db: AsyncSession,
    class_data: ClassCreate,
    school_id: str,
    created_by: str
) -> Dict[str, Any]:
    """Create a new class"""
    try:
        # Check for duplicate class code
        existing_class = await db.execute(
            select(Class).where(
                and_(
                    Class.school_id == UUID(school_id),
                    Class.code == class_data.code,
                    Class.academic_year == class_data.academic_year,
                    Class.is_active == True
                )
            )
        )
        if existing_class.scalar_one_or_none():
            raise DuplicateSubjectError(class_data.code, f"class in {class_data.academic_year}")
        
        # Determine curriculum level based on grade
        curriculum_level = _get_curriculum_level(class_data.grade_level)
        
        # Create class
        new_class = Class(
            school_id=UUID(school_id),
            code=class_data.code,
            name=class_data.name,
            description=class_data.description,
            grade_level=class_data.grade_level,
            academic_year=class_data.academic_year,
            class_type=class_data.class_type,
            stream=class_data.stream,
            capacity=class_data.capacity,
            class_teacher_id=class_data.class_teacher_id,
            deputy_teacher_id=class_data.deputy_teacher_id,
            classroom=class_data.classroom,
            curriculum_level=curriculum_level,
            start_date=class_data.start_date,
            end_date=class_data.end_date,
            created_by=created_by
        )
        
        db.add(new_class)
        await db.commit()
        await db.refresh(new_class)
        
        return _class_to_dict(new_class)
        
    except Exception as e:
        await db.rollback()
        if isinstance(e, DuplicateSubjectError):
            raise
        raise AcademicValidationError(f"Failed to create class: {str(e)}")


async def get_classes(
    db: AsyncSession,
    school_id: str,
    skip: int = 0,
    limit: int = 100,
    grade_level: Optional[int] = None,
    academic_year: Optional[str] = None,
    class_type: Optional[str] = None,
    active_only: bool = True
) -> tuple[List[Dict[str, Any]], int]:
    """Get list of classes with filtering"""
    try:
        # Build query
        query = select(Class).where(Class.school_id == UUID(school_id))
        
        if active_only:
            query = query.where(Class.is_active == True)
        
        if grade_level:
            query = query.where(Class.grade_level == grade_level)
        
        if academic_year:
            query = query.where(Class.academic_year == academic_year)
        
        if class_type:
            query = query.where(Class.class_type == class_type)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_count = await db.execute(count_query)
        total_count = total_count.scalar()
        
        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(Class.grade_level, Class.code)
        result = await db.execute(query)
        classes = result.scalars().all()
        
        return [_class_to_dict(cls) for cls in classes], total_count
        
    except Exception as e:
        raise AcademicValidationError(f"Failed to retrieve classes: {str(e)}")


async def assign_subject_to_class(
    db: AsyncSession,
    class_id: UUID,
    assignment_data: ClassSubjectAssignmentCreate,
    school_id: str,
    created_by: str
) -> Dict[str, Any]:
    """Assign a subject to a class"""
    try:
        # Verify class exists and belongs to school
        class_obj = await db.execute(
            select(Class).where(
                and_(
                    Class.id == class_id,
                    Class.school_id == UUID(school_id),
                    Class.is_active == True
                )
            )
        )
        class_obj = class_obj.scalar_one_or_none()
        if not class_obj:
            from .exceptions import AcademicResourceError
            raise AcademicResourceError(f"Class not found: {class_id}", "CLASS_NOT_FOUND")
        
        # Check for existing assignment
        existing = await db.execute(
            select(ClassSubjectAssignment).where(
                and_(
                    ClassSubjectAssignment.class_id == class_id,
                    ClassSubjectAssignment.subject_id == assignment_data.subject_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateSubjectError("subject assignment", f"class {class_obj.name}")
        
        # Create assignment
        assignment = ClassSubjectAssignment(
            class_id=class_id,
            subject_id=assignment_data.subject_id,
            teacher_id=assignment_data.teacher_id,
            periods_per_week=assignment_data.periods_per_week,
            is_core=assignment_data.is_core,
            academic_year=class_obj.academic_year,
            term_number=assignment_data.term_number,
            created_by=created_by
        )
        
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)
        
        return _assignment_to_dict(assignment)
        
    except Exception as e:
        await db.rollback()
        if isinstance(e, (DuplicateSubjectError, AcademicValidationError)):
            raise
        raise AcademicValidationError(f"Failed to assign subject: {str(e)}")


async def enroll_student_in_class(
    db: AsyncSession,
    class_id: UUID,
    enrollment_data: ClassEnrollmentCreate,
    school_id: str,
    created_by: str
) -> Dict[str, Any]:
    """Enroll a student in a class"""
    try:
        # Verify class exists and has capacity
        class_obj = await db.execute(
            select(Class).where(
                and_(
                    Class.id == class_id,
                    Class.school_id == UUID(school_id),
                    Class.is_active == True
                )
            )
        )
        class_obj = class_obj.scalar_one_or_none()
        if not class_obj:
            from .exceptions import AcademicResourceError
            raise AcademicResourceError(f"Class not found: {class_id}", "CLASS_NOT_FOUND")
        
        # Check capacity
        if class_obj.current_enrollment >= class_obj.capacity:
            raise AcademicValidationError("Class is at full capacity", "class_id", str(class_id))
        
        # Check for existing enrollment
        existing = await db.execute(
            select(ClassStudentEnrollment).where(
                and_(
                    ClassStudentEnrollment.class_id == class_id,
                    ClassStudentEnrollment.student_id == enrollment_data.student_id,
                    ClassStudentEnrollment.academic_year == enrollment_data.academic_year,
                    ClassStudentEnrollment.is_active == True
                )
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateSubjectError("student enrollment", f"class {class_obj.name}")
        
        # Create enrollment
        enrollment = ClassStudentEnrollment(
            class_id=class_id,
            student_id=enrollment_data.student_id,
            enrollment_date=enrollment_data.enrollment_date,
            academic_year=enrollment_data.academic_year,
            created_by=created_by
        )
        
        db.add(enrollment)
        
        # Update class enrollment count
        class_obj.current_enrollment += 1
        
        await db.commit()
        await db.refresh(enrollment)
        
        return _enrollment_to_dict(enrollment)
        
    except Exception as e:
        await db.rollback()
        if isinstance(e, (DuplicateSubjectError, AcademicValidationError)):
            raise
        raise AcademicValidationError(f"Failed to enroll student: {str(e)}")


# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def _get_curriculum_level(grade_level: int) -> str:
    """Determine curriculum level from grade level"""
    if 1 <= grade_level <= 7:
        return "Primary"
    elif grade_level == 8 or grade_level == 9:
        return "ZJC"  # Zimbabwe Junior Certificate
    elif grade_level == 10 or grade_level == 11:
        return "O-Level"
    elif grade_level == 12 or grade_level == 13:
        return "A-Level"
    else:
        return "Unknown"


def _class_to_dict(class_obj: Class) -> Dict[str, Any]:
    """Convert Class model to dictionary"""
    return {
        "id": str(class_obj.id),
        "school_id": str(class_obj.school_id),
        "code": class_obj.code,
        "name": class_obj.name,
        "description": class_obj.description,
        "grade_level": class_obj.grade_level,
        "academic_year": class_obj.academic_year,
        "class_type": class_obj.class_type,
        "stream": class_obj.stream,
        "capacity": class_obj.capacity,
        "current_enrollment": class_obj.current_enrollment,
        "class_teacher_id": str(class_obj.class_teacher_id) if class_obj.class_teacher_id else None,
        "deputy_teacher_id": str(class_obj.deputy_teacher_id) if class_obj.deputy_teacher_id else None,
        "classroom": class_obj.classroom,
        "curriculum_level": class_obj.curriculum_level,
        "is_active": class_obj.is_active,
        "created_at": class_obj.created_at,
        "updated_at": class_obj.updated_at
    }


def _assignment_to_dict(assignment: ClassSubjectAssignment) -> Dict[str, Any]:
    """Convert ClassSubjectAssignment to dictionary"""
    return {
        "id": str(assignment.id),
        "class_id": str(assignment.class_id),
        "subject_id": str(assignment.subject_id),
        "teacher_id": str(assignment.teacher_id) if assignment.teacher_id else None,
        "periods_per_week": assignment.periods_per_week,
        "is_core": assignment.is_core,
        "academic_year": assignment.academic_year,
        "term_number": assignment.term_number,
        "created_at": assignment.created_at
    }


def _enrollment_to_dict(enrollment: ClassStudentEnrollment) -> Dict[str, Any]:
    """Convert ClassStudentEnrollment to dictionary"""
    return {
        "id": str(enrollment.id),
        "class_id": str(enrollment.class_id),
        "student_id": str(enrollment.student_id),
        "enrollment_date": enrollment.enrollment_date.isoformat() if enrollment.enrollment_date else None,
        "withdrawal_date": enrollment.withdrawal_date.isoformat() if enrollment.withdrawal_date else None,
        "academic_year": enrollment.academic_year,
        "is_active": enrollment.is_active,
        "enrollment_status": enrollment.enrollment_status,
        "created_at": enrollment.created_at
    }