"""
Academic Management Models
Database models for academic-related entities (courses, assessments, grades, timetables)
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, JSON, ForeignKey, Numeric, Date, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()

class Subject(Base):
    """Subject/Course model"""
    __tablename__ = "subjects"
    __table_args__ = {"schema": "academic"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Subject details
    name = Column(String(255), nullable=False)
    code = Column(String(20), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # core, elective, extra_curricular
    
    # Academic requirements
    grade_level = Column(String(20))  # ECD_A, Grade_1, Form_1, etc.
    department = Column(String(100))
    credits = Column(Integer, default=1)
    
    # Subject configuration
    has_practical = Column(Boolean, default=False)
    assessment_methods = Column(JSON, default=[])  # ["written", "practical", "oral", "coursework"]
    
    # Pass requirements
    minimum_pass_mark = Column(Integer, default=50)
    maximum_mark = Column(Integer, default=100)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Subject(id={self.id}, name='{self.name}', code='{self.code}')>"

class AcademicYear(Base):
    """Academic year model"""
    __tablename__ = "academic_years"
    __table_args__ = {"schema": "academic"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Year details
    name = Column(String(100), nullable=False)  # "2024 Academic Year"
    year = Column(Integer, nullable=False)  # 2024
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Status
    is_current = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<AcademicYear(id={self.id}, name='{self.name}', year={self.year})>"

class Term(Base):
    """Academic term/semester model"""
    __tablename__ = "terms"
    __table_args__ = {"schema": "academic"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey('academic.academic_years.id'), nullable=False)
    
    # Term details
    name = Column(String(100), nullable=False)  # "Term 1", "Semester 1"
    term_number = Column(Integer, nullable=False)  # 1, 2, 3
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Holidays and breaks
    holidays = Column(JSON, default=[])  # [{"name": "Mid-term break", "start": "2024-05-01", "end": "2024-05-07"}]
    
    # Status
    is_current = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Term(id={self.id}, name='{self.name}', term_number={self.term_number})>"

class Class(Base):
    """Class/Grade model"""
    __tablename__ = "classes"
    __table_args__ = {"schema": "academic"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Class details
    name = Column(String(100), nullable=False)  # "Grade 5A", "Form 1B"
    grade_level = Column(String(20), nullable=False)  # "Grade_5", "Form_1"
    section = Column(String(10))  # "A", "B", "C"
    
    # Class teacher
    class_teacher_id = Column(UUID(as_uuid=True))  # References platform.users
    
    # Capacity and enrollment
    capacity = Column(Integer, default=40)
    current_enrollment = Column(Integer, default=0)
    
    # Class configuration
    classroom = Column(String(50))  # "Room 101"
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey('academic.academic_years.id'))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Class(id={self.id}, name='{self.name}', grade_level='{self.grade_level}')>"

class Assessment(Base):
    """Assessment/Exam model"""
    __tablename__ = "assessments"
    __table_args__ = {"schema": "academic"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Assessment details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    assessment_type = Column(String(50), nullable=False)  # test, exam, quiz, assignment, project
    
    # Subject and class
    subject_id = Column(UUID(as_uuid=True), ForeignKey('academic.subjects.id'), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey('academic.classes.id'), nullable=False)
    term_id = Column(UUID(as_uuid=True), ForeignKey('academic.terms.id'))
    
    # Timing
    scheduled_date = Column(DateTime(timezone=True))
    duration_minutes = Column(Integer)  # Duration in minutes
    
    # Marking
    total_marks = Column(Integer, nullable=False)
    pass_mark = Column(Integer)
    weighting = Column(Numeric(5,2), default=1.0)  # Weight in final grade calculation
    
    # Instructions
    instructions = Column(Text)
    materials_required = Column(JSON, default=[])  # ["calculator", "ruler", "textbook"]
    
    # Teacher
    created_by = Column(UUID(as_uuid=True), nullable=False)  # References platform.users
    
    # Status
    status = Column(String(20), default="draft")  # draft, published, completed, graded
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Assessment(id={self.id}, title='{self.title}', type='{self.assessment_type}')>"

class Grade(Base):
    """Student grade/mark model"""
    __tablename__ = "grades"
    __table_args__ = {"schema": "academic"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Student and assessment
    student_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # References sis.students
    assessment_id = Column(UUID(as_uuid=True), ForeignKey('academic.assessments.id'), nullable=False)
    
    # Grades
    marks_obtained = Column(Numeric(5,2))
    total_marks = Column(Integer)
    percentage = Column(Numeric(5,2))
    letter_grade = Column(String(5))  # A, B, C, D, E, F
    grade_points = Column(Numeric(3,2))  # GPA points
    
    # Status
    status = Column(String(20), default="pending")  # pending, submitted, graded, published
    is_published = Column(Boolean, default=False)
    
    # Grading details
    graded_by = Column(UUID(as_uuid=True))  # References platform.users (teacher)
    graded_at = Column(DateTime(timezone=True))
    comments = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Grade(id={self.id}, student_id={self.student_id}, marks={self.marks_obtained}/{self.total_marks})>"

class Timetable(Base):
    """Class timetable model"""
    __tablename__ = "timetables"
    __table_args__ = {"schema": "academic"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Class and term
    class_id = Column(UUID(as_uuid=True), ForeignKey('academic.classes.id'), nullable=False)
    term_id = Column(UUID(as_uuid=True), ForeignKey('academic.terms.id'))
    
    # Schedule details
    day_of_week = Column(Integer, nullable=False)  # 1=Monday, 7=Sunday
    period_number = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    
    # Subject and teacher
    subject_id = Column(UUID(as_uuid=True), ForeignKey('academic.subjects.id'), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), nullable=False)  # References platform.users
    
    # Location
    classroom = Column(String(50))
    venue = Column(String(100))  # For special venues like lab, library, field
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Timetable(id={self.id}, day={self.day_of_week}, period={self.period_number})>"

class Lesson(Base):
    """Individual lesson model"""
    __tablename__ = "lessons"
    __table_args__ = {"schema": "academic"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Lesson details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    lesson_date = Column(Date, nullable=False)
    
    # References
    timetable_id = Column(UUID(as_uuid=True), ForeignKey('academic.timetables.id'))
    subject_id = Column(UUID(as_uuid=True), ForeignKey('academic.subjects.id'), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey('academic.classes.id'), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Lesson content
    objectives = Column(JSON, default=[])  # Learning objectives
    lesson_plan = Column(Text)
    resources = Column(JSON, default=[])  # ["textbook", "projector", "worksheets"]
    homework = Column(Text)
    
    # Status
    status = Column(String(20), default="planned")  # planned, ongoing, completed, cancelled
    attendance_taken = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Lesson(id={self.id}, title='{self.title}', date={self.lesson_date})>"

class Curriculum(Base):
    """Curriculum standards and requirements"""
    __tablename__ = "curriculum"
    __table_args__ = {"schema": "academic"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Curriculum details
    name = Column(String(255), nullable=False)  # "Grade 5 Mathematics Curriculum"
    curriculum_type = Column(String(50))  # "national", "cambridge", "ib", "custom"
    
    # Subject and grade
    subject_id = Column(UUID(as_uuid=True), ForeignKey('academic.subjects.id'), nullable=False)
    grade_level = Column(String(20), nullable=False)
    
    # Content
    learning_outcomes = Column(JSON, default=[])
    topics = Column(JSON, default=[])
    assessment_criteria = Column(JSON, default=[])
    
    # Requirements
    minimum_teaching_hours = Column(Integer)
    recommended_resources = Column(JSON, default=[])
    
    # Status
    is_active = Column(Boolean, default=True)
    version = Column(String(20), default="1.0")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Curriculum(id={self.id}, name='{self.name}', type='{self.curriculum_type}')>"