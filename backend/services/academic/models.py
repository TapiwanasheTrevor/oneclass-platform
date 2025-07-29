"""
Academic Management SQLAlchemy Models
Database models for academic management with comprehensive relationships
"""

from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, Time, Text, DECIMAL, JSON, ForeignKey, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, ARRAY
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func

from core.database import Base
from core.models import AuditMixin, SoftDeleteMixin

# =====================================================
# SUBJECT MODELS
# =====================================================

class Subject(Base, AuditMixin, SoftDeleteMixin):
    """Subject model for academic subjects"""
    __tablename__ = "subjects"
    __table_args__ = (
        UniqueConstraint('school_id', 'code', name='unique_subject_code_per_school'),
        CheckConstraint('array_length(grade_levels, 1) > 0', name='grade_levels_not_empty'),
        CheckConstraint('pass_mark >= 0 AND pass_mark <= 100', name='valid_pass_mark'),
        CheckConstraint('max_mark > 0', name='positive_max_mark'),
        CheckConstraint('credit_hours > 0', name='positive_credit_hours'),
        CheckConstraint('display_order >= 0', name='non_negative_display_order'),
        Index('idx_subjects_school_active', 'school_id', 'is_active'),
        Index('idx_subjects_code', 'code'),
        Index('idx_subjects_grade_levels', 'grade_levels', postgresql_using='gin'),
        {'schema': 'academic'}
    )
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    school_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    code = Column(String(10), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    grade_levels = Column(ARRAY(Integer), nullable=False, default=list)
    is_core = Column(Boolean, default=False, nullable=False)
    is_practical = Column(Boolean, default=False, nullable=False)
    requires_lab = Column(Boolean, default=False, nullable=False)
    pass_mark = Column(DECIMAL(5, 2), default=Decimal('50.00'), nullable=False)
    max_mark = Column(DECIMAL(5, 2), default=Decimal('100.00'), nullable=False)
    credit_hours = Column(Integer, default=1, nullable=False)
    department = Column(String(50))
    language_of_instruction = Column(String(20), default='English', nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    
    # Relationships
    curricula = relationship("Curriculum", back_populates="subject")
    timetables = relationship("Timetable", back_populates="subject")
    assessments = relationship("Assessment", back_populates="subject")
    lesson_plans = relationship("LessonPlan", back_populates="subject")
    calendar_events = relationship("CalendarEvent", secondary="academic.calendar_event_subjects", back_populates="subjects")
    
    def __repr__(self):
        return f"<Subject(code='{self.code}', name='{self.name}')>"


# =====================================================
# CURRICULUM MODELS
# =====================================================

class Curriculum(Base, AuditMixin, SoftDeleteMixin):
    """Curriculum model for academic curriculum management"""
    __tablename__ = "curricula"
    __table_args__ = (
        UniqueConstraint('school_id', 'academic_year_id', 'subject_id', 'grade_level', 'term_number', name='unique_curriculum_per_term'),
        CheckConstraint('grade_level >= 1 AND grade_level <= 13', name='valid_grade_level'),
        CheckConstraint('term_number >= 1 AND term_number <= 3', name='valid_term_number'),
        CheckConstraint('total_periods > 0', name='positive_total_periods'),
        CheckConstraint('practical_periods >= 0', name='non_negative_practical_periods'),
        CheckConstraint('practical_periods <= total_periods', name='practical_not_exceed_total'),
        CheckConstraint('effective_to IS NULL OR effective_to >= effective_from', name='valid_effective_dates'),
        CheckConstraint('status IN (\'draft\', \'active\', \'archived\')', name='valid_status'),
        Index('idx_curricula_school_year', 'school_id', 'academic_year_id'),
        Index('idx_curricula_subject_grade', 'subject_id', 'grade_level'),
        Index('idx_curricula_term', 'term_number'),
        {'schema': 'academic'}
    )
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    school_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    academic_year_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    grade_level = Column(Integer, nullable=False)
    term_number = Column(Integer)
    subject_id = Column(PostgresUUID(as_uuid=True), ForeignKey('academic.subjects.id'), nullable=False)
    learning_objectives = Column(JSON, default=list)
    learning_outcomes = Column(JSON, default=list)
    assessment_methods = Column(JSON, default=list)
    resources_required = Column(JSON, default=list)
    total_periods = Column(Integer, default=1, nullable=False)
    practical_periods = Column(Integer, default=0, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date)
    status = Column(String(20), default='draft', nullable=False)
    approved_by = Column(PostgresUUID(as_uuid=True))
    approved_at = Column(DateTime)
    
    # Relationships
    subject = relationship("Subject", back_populates="curricula")
    lesson_plans = relationship("LessonPlan", back_populates="curriculum")
    
    def __repr__(self):
        return f"<Curriculum(name='{self.name}', grade_level={self.grade_level})>"


# =====================================================
# TIMETABLE MODELS
# =====================================================

class Period(Base, AuditMixin, SoftDeleteMixin):
    """Period model for class periods"""
    __tablename__ = "periods"
    __table_args__ = (
        UniqueConstraint('school_id', 'period_number', name='unique_period_number_per_school'),
        CheckConstraint('period_number > 0', name='positive_period_number'),
        CheckConstraint('end_time > start_time', name='valid_time_order'),
        CheckConstraint('break_type IS NULL OR break_type IN (\'tea\', \'lunch\', \'assembly\')', name='valid_break_type'),
        Index('idx_periods_school_active', 'school_id', 'is_active'),
        Index('idx_periods_time', 'start_time', 'end_time'),
        {'schema': 'academic'}
    )
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    school_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    period_number = Column(Integer, nullable=False)
    name = Column(String(50), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_break = Column(Boolean, default=False, nullable=False)
    break_type = Column(String(20))
    
    # Relationships
    timetables = relationship("Timetable", back_populates="period")
    attendance_sessions = relationship("AttendanceSession", back_populates="period")
    
    def __repr__(self):
        return f"<Period(number={self.period_number}, name='{self.name}')>"


class Timetable(Base, AuditMixin, SoftDeleteMixin):
    """Timetable model for class scheduling"""
    __tablename__ = "timetables"
    __table_args__ = (
        UniqueConstraint('school_id', 'class_id', 'period_id', 'day_of_week', 'academic_year_id', 'term_number', 'effective_from', name='unique_class_period_slot'),
        CheckConstraint('day_of_week >= 1 AND day_of_week <= 7', name='valid_day_of_week'),
        CheckConstraint('term_number >= 1 AND term_number <= 3', name='valid_term_number'),
        CheckConstraint('week_pattern IN (\'all\', \'odd\', \'even\')', name='valid_week_pattern'),
        CheckConstraint('effective_to IS NULL OR effective_to >= effective_from', name='valid_effective_dates'),
        Index('idx_timetables_school_year', 'school_id', 'academic_year_id'),
        Index('idx_timetables_teacher', 'teacher_id'),
        Index('idx_timetables_class', 'class_id'),
        Index('idx_timetables_subject', 'subject_id'),
        Index('idx_timetables_day_period', 'day_of_week', 'period_id'),
        {'schema': 'academic'}
    )
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    school_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    academic_year_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    term_number = Column(Integer, nullable=False)
    class_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    subject_id = Column(PostgresUUID(as_uuid=True), ForeignKey('academic.subjects.id'), nullable=False)
    teacher_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    period_id = Column(PostgresUUID(as_uuid=True), ForeignKey('academic.periods.id'), nullable=False)
    day_of_week = Column(Integer, nullable=False)
    room_number = Column(String(20))
    is_double_period = Column(Boolean, default=False, nullable=False)
    is_practical = Column(Boolean, default=False, nullable=False)
    week_pattern = Column(String(10), default='all', nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date)
    notes = Column(Text)
    
    # Relationships
    subject = relationship("Subject", back_populates="timetables")
    period = relationship("Period", back_populates="timetables")
    attendance_sessions = relationship("AttendanceSession", back_populates="timetable")
    
    def __repr__(self):
        return f"<Timetable(class_id={self.class_id}, subject_id={self.subject_id}, day={self.day_of_week})>"


# =====================================================
# ATTENDANCE MODELS
# =====================================================

class AttendanceSession(Base, AuditMixin, SoftDeleteMixin):
    """Attendance session model for tracking class sessions"""
    __tablename__ = "attendance_sessions"
    __table_args__ = (
        UniqueConstraint('school_id', 'timetable_id', 'session_date', name='unique_session_per_date'),
        CheckConstraint('session_type IN (\'regular\', \'makeup\', \'extra\', \'exam\')', name='valid_session_type'),
        CheckConstraint('session_status IN (\'scheduled\', \'active\', \'completed\', \'cancelled\')', name='valid_session_status'),
        CheckConstraint('total_students >= 0', name='non_negative_total_students'),
        CheckConstraint('present_students >= 0', name='non_negative_present_students'),
        CheckConstraint('absent_students >= 0', name='non_negative_absent_students'),
        CheckConstraint('late_students >= 0', name='non_negative_late_students'),
        CheckConstraint('present_students + absent_students + late_students = total_students', name='attendance_sum_check'),
        Index('idx_attendance_sessions_school_date', 'school_id', 'session_date'),
        Index('idx_attendance_sessions_timetable', 'timetable_id'),
        Index('idx_attendance_sessions_teacher', 'teacher_id'),
        Index('idx_attendance_sessions_class', 'class_id'),
        {'schema': 'academic'}
    )
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    school_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    timetable_id = Column(PostgresUUID(as_uuid=True), ForeignKey('academic.timetables.id'), nullable=False)
    period_id = Column(PostgresUUID(as_uuid=True), ForeignKey('academic.periods.id'), nullable=False)
    teacher_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    subject_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    class_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    session_date = Column(Date, nullable=False)
    session_type = Column(String(20), default='regular', nullable=False)
    session_status = Column(String(20), default='scheduled', nullable=False)
    attendance_marked = Column(Boolean, default=False, nullable=False)
    marked_by = Column(PostgresUUID(as_uuid=True))
    marked_at = Column(DateTime)
    total_students = Column(Integer, default=0, nullable=False)
    present_students = Column(Integer, default=0, nullable=False)
    absent_students = Column(Integer, default=0, nullable=False)
    late_students = Column(Integer, default=0, nullable=False)
    notes = Column(Text)
    
    # Relationships
    timetable = relationship("Timetable", back_populates="attendance_sessions")
    period = relationship("Period", back_populates="attendance_sessions")
    attendance_records = relationship("AttendanceRecord", back_populates="attendance_session", cascade="all, delete-orphan")
    
    @hybrid_property
    def attendance_rate(self):
        if self.total_students == 0:
            return Decimal('0.00')
        return Decimal(self.present_students + self.late_students) / Decimal(self.total_students) * 100
    
    def __repr__(self):
        return f"<AttendanceSession(class_id={self.class_id}, date={self.session_date})>"


class AttendanceRecord(Base, AuditMixin):
    """Attendance record model for individual student attendance"""
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint('school_id', 'attendance_session_id', 'student_id', name='unique_student_attendance_per_session'),
        CheckConstraint('attendance_status IN (\'present\', \'absent\', \'late\', \'excused\')', name='valid_attendance_status'),
        CheckConstraint('departure_time IS NULL OR arrival_time IS NULL OR departure_time >= arrival_time', name='valid_attendance_times'),
        Index('idx_attendance_records_school_session', 'school_id', 'attendance_session_id'),
        Index('idx_attendance_records_student', 'student_id'),
        Index('idx_attendance_records_status', 'attendance_status'),
        {'schema': 'academic'}
    )
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    school_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    attendance_session_id = Column(PostgresUUID(as_uuid=True), ForeignKey('academic.attendance_sessions.id'), nullable=False)
    student_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    attendance_status = Column(String(20), nullable=False)
    arrival_time = Column(Time)
    departure_time = Column(Time)
    excuse_reason = Column(Text)
    is_excused = Column(Boolean, default=False, nullable=False)
    notes = Column(Text)
    marked_by = Column(PostgresUUID(as_uuid=True), nullable=False)
    marked_at = Column(DateTime, nullable=False)
    
    # Relationships
    attendance_session = relationship("AttendanceSession", back_populates="attendance_records")
    
    def __repr__(self):
        return f"<AttendanceRecord(student_id={self.student_id}, status='{self.attendance_status}')>"


# =====================================================
# ASSESSMENT MODELS
# =====================================================

class Assessment(Base, AuditMixin, SoftDeleteMixin):
    """Assessment model for tests, quizzes, and assignments"""
    __tablename__ = "assessments"
    __table_args__ = (
        CheckConstraint('term_number >= 1 AND term_number <= 3', name='valid_term_number'),
        CheckConstraint('assessment_type IN (\'test\', \'quiz\', \'assignment\', \'project\', \'practical\', \'oral\', \'exam\')', name='valid_assessment_type'),
        CheckConstraint('assessment_category IN (\'continuous\', \'formative\', \'summative\', \'final\')', name='valid_assessment_category'),
        CheckConstraint('total_marks > 0', name='positive_total_marks'),
        CheckConstraint('pass_mark >= 0', name='non_negative_pass_mark'),
        CheckConstraint('pass_mark <= total_marks', name='pass_mark_not_exceed_total'),
        CheckConstraint('weight_percentage > 0 AND weight_percentage <= 100', name='valid_weight_percentage'),
        CheckConstraint('due_date IS NULL OR due_date >= assessment_date', name='valid_due_date'),
        CheckConstraint('duration_minutes IS NULL OR duration_minutes > 0', name='positive_duration'),
        CheckConstraint('max_group_size IS NULL OR max_group_size > 1', name='valid_max_group_size'),
        CheckConstraint('status IN (\'draft\', \'published\', \'completed\', \'cancelled\')', name='valid_status'),
        Index('idx_assessments_school_year', 'school_id', 'academic_year_id'),
        Index('idx_assessments_subject_class', 'subject_id', 'class_id'),
        Index('idx_assessments_teacher', 'teacher_id'),
        Index('idx_assessments_date', 'assessment_date'),
        Index('idx_assessments_term', 'term_number'),
        {'schema': 'academic'}
    )
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    school_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    academic_year_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    subject_id = Column(PostgresUUID(as_uuid=True), ForeignKey('academic.subjects.id'), nullable=False)
    class_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    teacher_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    term_number = Column(Integer, nullable=False)
    assessment_type = Column(String(20), nullable=False)
    assessment_category = Column(String(20), default='continuous', nullable=False)
    total_marks = Column(DECIMAL(8, 2), default=Decimal('100.00'), nullable=False)
    pass_mark = Column(DECIMAL(8, 2), default=Decimal('50.00'), nullable=False)
    weight_percentage = Column(DECIMAL(5, 2), default=Decimal('100.00'), nullable=False)
    assessment_date = Column(Date, nullable=False)
    due_date = Column(Date)
    duration_minutes = Column(Integer)
    instructions = Column(Text)
    resources_allowed = Column(JSON, default=list)
    is_group_assessment = Column(Boolean, default=False, nullable=False)
    max_group_size = Column(Integer)
    status = Column(String(20), default='draft', nullable=False)
    published_at = Column(DateTime)
    published_by = Column(PostgresUUID(as_uuid=True))
    results_published = Column(Boolean, default=False, nullable=False)
    results_published_at = Column(DateTime)
    
    # Relationships
    subject = relationship("Subject", back_populates="assessments")
    grades = relationship("Grade", back_populates="assessment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Assessment(name='{self.name}', type='{self.assessment_type}')>"


class Grade(Base, AuditMixin):
    """Grade model for individual student grades"""
    __tablename__ = "grades"
    __table_args__ = (
        UniqueConstraint('school_id', 'assessment_id', 'student_id', name='unique_student_grade_per_assessment'),
        CheckConstraint('raw_score IS NULL OR raw_score >= 0', name='non_negative_raw_score'),
        CheckConstraint('percentage_score IS NULL OR (percentage_score >= 0 AND percentage_score <= 100)', name='valid_percentage_score'),
        CheckConstraint('letter_grade IS NULL OR letter_grade IN (\'A\', \'B\', \'C\', \'D\', \'E\', \'U\')', name='valid_letter_grade'),
        CheckConstraint('grade_points IS NULL OR (grade_points >= 0 AND grade_points <= 4)', name='valid_grade_points'),
        Index('idx_grades_school_assessment', 'school_id', 'assessment_id'),
        Index('idx_grades_student', 'student_id'),
        Index('idx_grades_graded_by', 'graded_by'),
        Index('idx_grades_letter_grade', 'letter_grade'),
        {'schema': 'academic'}
    )
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    school_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    assessment_id = Column(PostgresUUID(as_uuid=True), ForeignKey('academic.assessments.id'), nullable=False)
    student_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    raw_score = Column(DECIMAL(8, 2))
    percentage_score = Column(DECIMAL(5, 2))
    letter_grade = Column(String(1))
    grade_points = Column(DECIMAL(3, 2))
    is_absent = Column(Boolean, default=False, nullable=False)
    is_excused = Column(Boolean, default=False, nullable=False)
    submission_date = Column(DateTime)
    feedback = Column(Text)
    improvement_suggestions = Column(Text)
    next_steps = Column(Text)
    graded_by = Column(PostgresUUID(as_uuid=True), nullable=False)
    graded_at = Column(DateTime, nullable=False)
    parent_viewed = Column(Boolean, default=False, nullable=False)
    parent_viewed_at = Column(DateTime)
    is_final = Column(Boolean, default=False, nullable=False)
    moderated_by = Column(PostgresUUID(as_uuid=True))
    moderated_at = Column(DateTime)
    
    # Relationships
    assessment = relationship("Assessment", back_populates="grades")
    
    def __repr__(self):
        return f"<Grade(student_id={self.student_id}, letter_grade='{self.letter_grade}')>"


# =====================================================
# LESSON PLAN MODELS
# =====================================================

class LessonPlan(Base, AuditMixin, SoftDeleteMixin):
    """Lesson plan model for teacher lesson planning"""
    __tablename__ = "lesson_plans"
    __table_args__ = (
        CheckConstraint('term_number >= 1 AND term_number <= 3', name='valid_term_number'),
        CheckConstraint('duration_minutes > 0', name='positive_duration'),
        CheckConstraint('status IN (\'draft\', \'active\', \'completed\', \'archived\')', name='valid_status'),
        CheckConstraint('version >= 1', name='positive_version'),
        Index('idx_lesson_plans_school_year', 'school_id', 'academic_year_id'),
        Index('idx_lesson_plans_subject_class', 'subject_id', 'class_id'),
        Index('idx_lesson_plans_teacher', 'teacher_id'),
        Index('idx_lesson_plans_date', 'lesson_date'),
        Index('idx_lesson_plans_term', 'term_number'),
        {'schema': 'academic'}
    )
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    school_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    academic_year_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    subject_id = Column(PostgresUUID(as_uuid=True), ForeignKey('academic.subjects.id'), nullable=False)
    class_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    teacher_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    term_number = Column(Integer, nullable=False)
    curriculum_id = Column(PostgresUUID(as_uuid=True), ForeignKey('academic.curricula.id'))
    lesson_date = Column(Date, nullable=False)
    duration_minutes = Column(Integer, default=40, nullable=False)
    learning_objectives = Column(JSON, default=list)
    learning_outcomes = Column(JSON, default=list)
    prerequisite_knowledge = Column(JSON, default=list)
    materials_required = Column(JSON, default=list)
    teaching_methods = Column(JSON, default=list)
    lesson_structure = Column(JSON)
    assessment_activities = Column(JSON, default=list)
    homework_assignments = Column(JSON, default=list)
    differentiation_strategies = Column(JSON, default=list)
    extension_activities = Column(JSON, default=list)
    reflection_notes = Column(Text)
    shared_with = Column(JSON, default=list)
    is_template = Column(Boolean, default=False, nullable=False)
    template_category = Column(String(50))
    status = Column(String(20), default='draft', nullable=False)
    version = Column(Integer, default=1, nullable=False)
    parent_lesson_id = Column(PostgresUUID(as_uuid=True), ForeignKey('academic.lesson_plans.id'))
    
    # Relationships
    subject = relationship("Subject", back_populates="lesson_plans")
    curriculum = relationship("Curriculum", back_populates="lesson_plans")
    parent_lesson = relationship("LessonPlan", remote_side=[id])
    
    def __repr__(self):
        return f"<LessonPlan(title='{self.title}', date={self.lesson_date})>"


# =====================================================
# CALENDAR MODELS
# =====================================================

class CalendarEvent(Base, AuditMixin, SoftDeleteMixin):
    """Calendar event model for academic events"""
    __tablename__ = "calendar_events"
    __table_args__ = (
        CheckConstraint('event_type IN (\'holiday\', \'exam\', \'assessment\', \'sports\', \'cultural\', \'meeting\', \'training\', \'other\')', name='valid_event_type'),
        CheckConstraint('event_category IN (\'academic\', \'administrative\', \'social\', \'sports\', \'cultural\')', name='valid_event_category'),
        CheckConstraint('end_date IS NULL OR end_date >= start_date', name='valid_end_date'),
        CheckConstraint('end_time IS NULL OR start_time IS NULL OR end_time > start_time', name='valid_end_time'),
        CheckConstraint('term_number IS NULL OR (term_number >= 1 AND term_number <= 3)', name='valid_term_number'),
        CheckConstraint('max_participants IS NULL OR max_participants > 0', name='positive_max_participants'),
        CheckConstraint('registration_deadline IS NULL OR registration_deadline <= start_date', name='valid_registration_deadline'),
        CheckConstraint('recurrence_end_date IS NULL OR recurrence_end_date >= start_date', name='valid_recurrence_end_date'),
        CheckConstraint('status IN (\'scheduled\', \'confirmed\', \'cancelled\', \'completed\', \'postponed\')', name='valid_status'),
        Index('idx_calendar_events_school_year', 'school_id', 'academic_year_id'),
        Index('idx_calendar_events_date', 'start_date', 'end_date'),
        Index('idx_calendar_events_type', 'event_type'),
        Index('idx_calendar_events_term', 'term_number'),
        {'schema': 'academic'}
    )
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    school_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    academic_year_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    event_type = Column(String(20), nullable=False)
    event_category = Column(String(20), default='academic', nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)
    is_all_day = Column(Boolean, default=True, nullable=False)
    location = Column(String(200))
    term_number = Column(Integer)
    grade_levels = Column(ARRAY(Integer), default=list)
    class_ids = Column(ARRAY(PostgresUUID), default=list)
    teacher_ids = Column(ARRAY(PostgresUUID), default=list)
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurrence_pattern = Column(String(50))
    recurrence_end_date = Column(Date)
    reminder_days = Column(ARRAY(Integer), default=list)
    is_public = Column(Boolean, default=False, nullable=False)
    requires_attendance = Column(Boolean, default=False, nullable=False)
    max_participants = Column(Integer)
    registration_required = Column(Boolean, default=False, nullable=False)
    registration_deadline = Column(Date)
    status = Column(String(20), default='scheduled', nullable=False)
    
    # Relationships
    subjects = relationship("Subject", secondary="academic.calendar_event_subjects", back_populates="calendar_events")
    
    def __repr__(self):
        return f"<CalendarEvent(title='{self.title}', date={self.start_date})>"


# =====================================================
# ASSOCIATION TABLES
# =====================================================

from sqlalchemy import Table

calendar_event_subjects = Table(
    'calendar_event_subjects',
    Base.metadata,
    Column('calendar_event_id', PostgresUUID(as_uuid=True), ForeignKey('academic.calendar_events.id'), primary_key=True),
    Column('subject_id', PostgresUUID(as_uuid=True), ForeignKey('academic.subjects.id'), primary_key=True),
    schema='academic'
)