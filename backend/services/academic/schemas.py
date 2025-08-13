"""
Academic Management Pydantic Models
Comprehensive schemas for academic management with Zimbabwe-specific validation
"""

from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, validator, root_validator
import re


# =====================================================
# ENUMS AND CONSTANTS
# =====================================================

class GradingScale(str, Enum):
    """Zimbabwe grading scale"""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    U = "U"


class AttendanceStatus(str, Enum):
    """Student attendance status"""
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


class AssessmentType(str, Enum):
    """Types of assessments"""
    TEST = "test"
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
    PROJECT = "project"
    PRACTICAL = "practical"
    ORAL = "oral"
    EXAM = "exam"


class AssessmentCategory(str, Enum):
    """Assessment categories"""
    CONTINUOUS = "continuous"
    FORMATIVE = "formative"
    SUMMATIVE = "summative"
    FINAL = "final"


class EventType(str, Enum):
    """Calendar event types"""
    HOLIDAY = "holiday"
    EXAM = "exam"
    ASSESSMENT = "assessment"
    SPORTS = "sports"
    CULTURAL = "cultural"
    MEETING = "meeting"
    TRAINING = "training"
    OTHER = "other"


class SessionType(str, Enum):
    """Attendance session types"""
    REGULAR = "regular"
    MAKEUP = "makeup"
    EXTRA = "extra"
    EXAM = "exam"


class DayOfWeek(int, Enum):
    """Days of the week"""
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


class TermNumber(int, Enum):
    """Zimbabwe school terms"""
    TERM_1 = 1
    TERM_2 = 2
    TERM_3 = 3


class LanguageOfInstruction(str, Enum):
    """Languages of instruction in Zimbabwe"""
    ENGLISH = "English"
    SHONA = "Shona"
    NDEBELE = "Ndebele"


# =====================================================
# VALIDATION FUNCTIONS
# =====================================================

def validate_zimbabwe_grade_level(grade_level: int) -> int:
    """Validate Zimbabwe grade level (1-13)"""
    if not 1 <= grade_level <= 13:
        raise ValueError("Grade level must be between 1 and 13")
    return grade_level


def validate_subject_code(code: str) -> str:
    """Validate subject code format"""
    if not re.match(r'^[A-Z]{2,10}$', code):
        raise ValueError("Subject code must be 2-10 uppercase letters")
    return code


def validate_percentage(value: float) -> float:
    """Validate percentage value (0-100)"""
    if not 0 <= value <= 100:
        raise ValueError("Percentage must be between 0 and 100")
    return value


def validate_time_order(start_time: time, end_time: time) -> bool:
    """Validate that end time is after start time"""
    return end_time > start_time


# =====================================================
# SUBJECT SCHEMAS
# =====================================================

class SubjectBase(BaseModel):
    """Base subject schema"""
    code: str = Field(..., min_length=2, max_length=10)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    grade_levels: List[int] = Field(..., min_items=1)
    is_core: bool = False
    is_practical: bool = False
    requires_lab: bool = False
    pass_mark: Decimal = Field(default=Decimal("50.00"), ge=0, le=100)
    max_mark: Decimal = Field(default=Decimal("100.00"), gt=0)
    credit_hours: int = Field(default=1, gt=0)
    department: Optional[str] = Field(None, max_length=50)
    language_of_instruction: LanguageOfInstruction = LanguageOfInstruction.ENGLISH
    display_order: int = Field(default=0, ge=0)

    @validator('code')
    def validate_code(cls, v):
        return validate_subject_code(v)

    @validator('grade_levels')
    def validate_grade_levels(cls, v):
        for grade in v:
            validate_zimbabwe_grade_level(grade)
        return sorted(list(set(v)))  # Remove duplicates and sort

    @validator('pass_mark')
    def validate_pass_mark(cls, v, values):
        if 'max_mark' in values and v > values['max_mark']:
            raise ValueError("Pass mark cannot exceed max mark")
        return v


class SubjectCreate(SubjectBase):
    """Subject creation schema"""
    pass


class SubjectUpdate(BaseModel):
    """Subject update schema"""
    code: Optional[str] = Field(None, min_length=2, max_length=10)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    grade_levels: Optional[List[int]] = None
    is_core: Optional[bool] = None
    is_practical: Optional[bool] = None
    requires_lab: Optional[bool] = None
    pass_mark: Optional[Decimal] = Field(None, ge=0, le=100)
    max_mark: Optional[Decimal] = Field(None, gt=0)
    credit_hours: Optional[int] = Field(None, gt=0)
    department: Optional[str] = Field(None, max_length=50)
    language_of_instruction: Optional[LanguageOfInstruction] = None
    display_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

    @validator('code')
    def validate_code(cls, v):
        if v is not None:
            return validate_subject_code(v)
        return v

    @validator('grade_levels')
    def validate_grade_levels(cls, v):
        if v is not None:
            for grade in v:
                validate_zimbabwe_grade_level(grade)
            return sorted(list(set(v)))
        return v


class Subject(SubjectBase):
    """Subject response schema"""
    id: UUID
    school_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: Optional[UUID]

    class Config:
        from_attributes = True


# =====================================================
# CURRICULUM SCHEMAS
# =====================================================

class CurriculumBase(BaseModel):
    """Base curriculum schema"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    grade_level: int
    term_number: Optional[TermNumber] = None
    subject_id: UUID
    learning_objectives: List[str] = Field(default=[])
    learning_outcomes: List[str] = Field(default=[])
    assessment_methods: List[str] = Field(default=[])
    resources_required: List[str] = Field(default=[])
    total_periods: int = Field(default=1, gt=0)
    practical_periods: int = Field(default=0, ge=0)
    effective_from: date
    effective_to: Optional[date] = None

    @validator('grade_level')
    def validate_grade_level(cls, v):
        return validate_zimbabwe_grade_level(v)

    @validator('practical_periods')
    def validate_practical_periods(cls, v, values):
        if 'total_periods' in values and v > values['total_periods']:
            raise ValueError("Practical periods cannot exceed total periods")
        return v

    @validator('effective_to')
    def validate_effective_dates(cls, v, values):
        if v is not None and 'effective_from' in values and v < values['effective_from']:
            raise ValueError("Effective to date must be after effective from date")
        return v


class CurriculumCreate(CurriculumBase):
    """Curriculum creation schema"""
    academic_year_id: UUID


class CurriculumUpdate(BaseModel):
    """Curriculum update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    term_number: Optional[TermNumber] = None
    learning_objectives: Optional[List[str]] = None
    learning_outcomes: Optional[List[str]] = None
    assessment_methods: Optional[List[str]] = None
    resources_required: Optional[List[str]] = None
    total_periods: Optional[int] = Field(None, gt=0)
    practical_periods: Optional[int] = Field(None, ge=0)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    status: Optional[str] = Field(None, pattern=r'^(draft|active|archived)$')
    is_active: Optional[bool] = None


class Curriculum(CurriculumBase):
    """Curriculum response schema"""
    id: UUID
    school_id: UUID
    academic_year_id: UUID
    status: str
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: Optional[UUID]

    class Config:
        from_attributes = True


# =====================================================
# TIMETABLE SCHEMAS
# =====================================================

class PeriodBase(BaseModel):
    """Base period schema"""
    period_number: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=50)
    start_time: time
    end_time: time
    is_break: bool = False
    break_type: Optional[str] = Field(None, pattern=r'^(tea|lunch|assembly)$')

    @validator('end_time')
    def validate_time_order(cls, v, values):
        if 'start_time' in values and not validate_time_order(values['start_time'], v):
            raise ValueError("End time must be after start time")
        return v


class PeriodCreate(PeriodBase):
    """Period creation schema"""
    pass


class PeriodUpdate(BaseModel):
    """Period update schema"""
    period_number: Optional[int] = Field(None, gt=0)
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_break: Optional[bool] = None
    break_type: Optional[str] = Field(None, pattern=r'^(tea|lunch|assembly)$')
    is_active: Optional[bool] = None


class Period(PeriodBase):
    """Period response schema"""
    id: UUID
    school_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: Optional[UUID]

    class Config:
        from_attributes = True


class TimetableBase(BaseModel):
    """Base timetable schema"""
    class_id: UUID
    subject_id: UUID
    teacher_id: UUID
    period_id: UUID
    day_of_week: DayOfWeek
    room_number: Optional[str] = Field(None, max_length=20)
    is_double_period: bool = False
    is_practical: bool = False
    week_pattern: str = Field(default="all", pattern=r'^(all|odd|even)$')
    effective_from: date
    effective_to: Optional[date] = None
    notes: Optional[str] = None

    @validator('effective_to')
    def validate_effective_dates(cls, v, values):
        if v is not None and 'effective_from' in values and v < values['effective_from']:
            raise ValueError("Effective to date must be after effective from date")
        return v


class TimetableCreate(TimetableBase):
    """Timetable creation schema"""
    academic_year_id: UUID
    term_number: TermNumber


class TimetableUpdate(BaseModel):
    """Timetable update schema"""
    subject_id: Optional[UUID] = None
    teacher_id: Optional[UUID] = None
    period_id: Optional[UUID] = None
    day_of_week: Optional[DayOfWeek] = None
    room_number: Optional[str] = Field(None, max_length=20)
    is_double_period: Optional[bool] = None
    is_practical: Optional[bool] = None
    week_pattern: Optional[str] = Field(None, pattern=r'^(all|odd|even)$')
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class Timetable(TimetableBase):
    """Timetable response schema"""
    id: UUID
    school_id: UUID
    academic_year_id: UUID
    term_number: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: Optional[UUID]

    class Config:
        from_attributes = True


class TimetableWithDetails(Timetable):
    """Timetable with related details"""
    subject_name: str
    teacher_name: str
    period_name: str
    class_name: str
    start_time: time
    end_time: time


# =====================================================
# ATTENDANCE SCHEMAS
# =====================================================

class AttendanceSessionBase(BaseModel):
    """Base attendance session schema"""
    session_date: date
    session_type: SessionType = SessionType.REGULAR
    notes: Optional[str] = None


class AttendanceSessionCreate(AttendanceSessionBase):
    """Attendance session creation schema"""
    timetable_id: UUID


class AttendanceSession(AttendanceSessionBase):
    """Attendance session response schema"""
    id: UUID
    school_id: UUID
    timetable_id: UUID
    period_id: UUID
    teacher_id: UUID
    subject_id: UUID
    class_id: UUID
    session_status: str
    attendance_marked: bool
    marked_by: Optional[UUID]
    marked_at: Optional[datetime]
    total_students: int
    present_students: int
    absent_students: int
    late_students: int
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: Optional[UUID]

    class Config:
        from_attributes = True


class AttendanceRecordBase(BaseModel):
    """Base attendance record schema"""
    student_id: UUID
    attendance_status: AttendanceStatus
    arrival_time: Optional[time] = None
    departure_time: Optional[time] = None
    excuse_reason: Optional[str] = None
    is_excused: bool = False
    notes: Optional[str] = None

    @validator('departure_time')
    def validate_departure_time(cls, v, values):
        if v is not None and 'arrival_time' in values and values['arrival_time'] is not None:
            if not validate_time_order(values['arrival_time'], v):
                raise ValueError("Departure time must be after arrival time")
        return v


class AttendanceRecordCreate(AttendanceRecordBase):
    """Attendance record creation schema"""
    pass


class AttendanceRecord(AttendanceRecordBase):
    """Attendance record response schema"""
    id: UUID
    school_id: UUID
    attendance_session_id: UUID
    marked_by: UUID
    marked_at: datetime
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: Optional[UUID]

    class Config:
        from_attributes = True


class BulkAttendanceCreate(BaseModel):
    """Bulk attendance creation schema"""
    attendance_session_id: UUID
    attendance_records: List[AttendanceRecordCreate]


class AttendanceStats(BaseModel):
    """Attendance statistics schema"""
    total_students: int
    present_students: int
    absent_students: int
    late_students: int
    attendance_rate: Decimal


# =====================================================
# ASSESSMENT SCHEMAS
# =====================================================

class AssessmentBase(BaseModel):
    """Base assessment schema"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    subject_id: UUID
    class_id: UUID
    teacher_id: UUID
    term_number: TermNumber
    assessment_type: AssessmentType
    assessment_category: AssessmentCategory = AssessmentCategory.CONTINUOUS
    total_marks: Decimal = Field(default=Decimal("100.00"), gt=0)
    pass_mark: Decimal = Field(default=Decimal("50.00"), ge=0)
    weight_percentage: Decimal = Field(default=Decimal("100.00"), gt=0, le=100)
    assessment_date: date
    due_date: Optional[date] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    instructions: Optional[str] = None
    resources_allowed: List[str] = Field(default=[])
    is_group_assessment: bool = False
    max_group_size: Optional[int] = Field(None, gt=1)

    @validator('pass_mark')
    def validate_pass_mark(cls, v, values):
        if 'total_marks' in values and v > values['total_marks']:
            raise ValueError("Pass mark cannot exceed total marks")
        return v

    @validator('due_date')
    def validate_due_date(cls, v, values):
        if v is not None and 'assessment_date' in values and v < values['assessment_date']:
            raise ValueError("Due date must be on or after assessment date")
        return v


class AssessmentCreate(AssessmentBase):
    """Assessment creation schema"""
    academic_year_id: UUID


class AssessmentUpdate(BaseModel):
    """Assessment update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    assessment_type: Optional[AssessmentType] = None
    assessment_category: Optional[AssessmentCategory] = None
    total_marks: Optional[Decimal] = Field(None, gt=0)
    pass_mark: Optional[Decimal] = Field(None, ge=0)
    weight_percentage: Optional[Decimal] = Field(None, gt=0, le=100)
    assessment_date: Optional[date] = None
    due_date: Optional[date] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    instructions: Optional[str] = None
    resources_allowed: Optional[List[str]] = None
    is_group_assessment: Optional[bool] = None
    max_group_size: Optional[int] = Field(None, gt=1)
    status: Optional[str] = Field(None, pattern=r'^(draft|published|completed|cancelled)$')
    results_published: Optional[bool] = None


class Assessment(AssessmentBase):
    """Assessment response schema"""
    id: UUID
    school_id: UUID
    academic_year_id: UUID
    status: str
    published_at: Optional[datetime]
    published_by: Optional[UUID]
    results_published: bool
    results_published_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: Optional[UUID]

    class Config:
        from_attributes = True


class GradeBase(BaseModel):
    """Base grade schema"""
    student_id: UUID
    raw_score: Optional[Decimal] = Field(None, ge=0)
    percentage_score: Optional[Decimal] = Field(None, ge=0, le=100)
    letter_grade: Optional[GradingScale] = None
    grade_points: Optional[Decimal] = Field(None, ge=0, le=4)
    is_absent: bool = False
    is_excused: bool = False
    submission_date: Optional[datetime] = None
    feedback: Optional[str] = None
    improvement_suggestions: Optional[str] = None
    next_steps: Optional[str] = None

    @validator('percentage_score')
    def validate_percentage_score(cls, v):
        if v is not None:
            return validate_percentage(float(v))
        return v


class GradeCreate(GradeBase):
    """Grade creation schema"""
    assessment_id: UUID


class GradeUpdate(BaseModel):
    """Grade update schema"""
    raw_score: Optional[Decimal] = Field(None, ge=0)
    percentage_score: Optional[Decimal] = Field(None, ge=0, le=100)
    letter_grade: Optional[GradingScale] = None
    grade_points: Optional[Decimal] = Field(None, ge=0, le=4)
    is_absent: Optional[bool] = None
    is_excused: Optional[bool] = None
    submission_date: Optional[datetime] = None
    feedback: Optional[str] = None
    improvement_suggestions: Optional[str] = None
    next_steps: Optional[str] = None
    is_final: Optional[bool] = None


class Grade(GradeBase):
    """Grade response schema"""
    id: UUID
    school_id: UUID
    assessment_id: UUID
    graded_by: UUID
    graded_at: datetime
    parent_viewed: bool
    parent_viewed_at: Optional[datetime]
    is_final: bool
    moderated_by: Optional[UUID]
    moderated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: Optional[UUID]

    class Config:
        from_attributes = True


class BulkGradeCreate(BaseModel):
    """Bulk grade creation schema"""
    assessment_id: UUID
    grades: List[GradeCreate]


# =====================================================
# LESSON PLAN SCHEMAS
# =====================================================

class LessonPlanBase(BaseModel):
    """Base lesson plan schema"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    subject_id: UUID
    class_id: UUID
    teacher_id: UUID
    term_number: TermNumber
    curriculum_id: Optional[UUID] = None
    lesson_date: date
    duration_minutes: int = Field(default=40, gt=0)
    learning_objectives: List[str] = Field(default=[])
    learning_outcomes: List[str] = Field(default=[])
    prerequisite_knowledge: List[str] = Field(default=[])
    materials_required: List[str] = Field(default=[])
    teaching_methods: List[str] = Field(default=[])
    lesson_structure: Optional[Dict[str, Any]] = None
    assessment_activities: List[str] = Field(default=[])
    homework_assignments: List[str] = Field(default=[])
    differentiation_strategies: List[str] = Field(default=[])
    extension_activities: List[str] = Field(default=[])
    reflection_notes: Optional[str] = None
    shared_with: List[UUID] = Field(default=[])
    is_template: bool = False
    template_category: Optional[str] = Field(None, max_length=50)


class LessonPlanCreate(LessonPlanBase):
    """Lesson plan creation schema"""
    academic_year_id: UUID


class LessonPlanUpdate(BaseModel):
    """Lesson plan update schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    curriculum_id: Optional[UUID] = None
    lesson_date: Optional[date] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    learning_objectives: Optional[List[str]] = None
    learning_outcomes: Optional[List[str]] = None
    prerequisite_knowledge: Optional[List[str]] = None
    materials_required: Optional[List[str]] = None
    teaching_methods: Optional[List[str]] = None
    lesson_structure: Optional[Dict[str, Any]] = None
    assessment_activities: Optional[List[str]] = None
    homework_assignments: Optional[List[str]] = None
    differentiation_strategies: Optional[List[str]] = None
    extension_activities: Optional[List[str]] = None
    reflection_notes: Optional[str] = None
    shared_with: Optional[List[UUID]] = None
    is_template: Optional[bool] = None
    template_category: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, pattern=r'^(draft|active|completed|archived)$')


class LessonPlan(LessonPlanBase):
    """Lesson plan response schema"""
    id: UUID
    school_id: UUID
    academic_year_id: UUID
    status: str
    version: int
    parent_lesson_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: Optional[UUID]

    class Config:
        from_attributes = True


# =====================================================
# CALENDAR SCHEMAS
# =====================================================

class CalendarEventBase(BaseModel):
    """Base calendar event schema"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    event_type: EventType
    event_category: str = Field(default="academic", pattern=r'^(academic|administrative|social|sports|cultural)$')
    start_date: date
    end_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_all_day: bool = True
    location: Optional[str] = Field(None, max_length=200)
    term_number: Optional[TermNumber] = None
    grade_levels: List[int] = Field(default=[])
    class_ids: List[UUID] = Field(default=[])
    subject_ids: List[UUID] = Field(default=[])
    teacher_ids: List[UUID] = Field(default=[])
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = Field(None, max_length=50)
    recurrence_end_date: Optional[date] = None
    reminder_days: List[int] = Field(default=[1, 7])
    is_public: bool = False
    requires_attendance: bool = False
    max_participants: Optional[int] = Field(None, gt=0)
    registration_required: bool = False
    registration_deadline: Optional[date] = None

    @validator('grade_levels')
    def validate_grade_levels(cls, v):
        if v:
            for grade in v:
                validate_zimbabwe_grade_level(grade)
        return v

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v is not None and 'start_date' in values and v < values['start_date']:
            raise ValueError("End date must be on or after start date")
        return v

    @validator('end_time')
    def validate_end_time(cls, v, values):
        if v is not None and 'start_time' in values and values['start_time'] is not None:
            if not validate_time_order(values['start_time'], v):
                raise ValueError("End time must be after start time")
        return v

    @validator('recurrence_end_date')
    def validate_recurrence_end_date(cls, v, values):
        if v is not None and 'start_date' in values and v < values['start_date']:
            raise ValueError("Recurrence end date must be on or after start date")
        return v

    @validator('registration_deadline')
    def validate_registration_deadline(cls, v, values):
        if v is not None and 'start_date' in values and v > values['start_date']:
            raise ValueError("Registration deadline must be before start date")
        return v


class CalendarEventCreate(CalendarEventBase):
    """Calendar event creation schema"""
    academic_year_id: UUID


class CalendarEventUpdate(BaseModel):
    """Calendar event update schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    event_type: Optional[EventType] = None
    event_category: Optional[str] = Field(None, pattern=r'^(academic|administrative|social|sports|cultural)$')
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_all_day: Optional[bool] = None
    location: Optional[str] = Field(None, max_length=200)
    term_number: Optional[TermNumber] = None
    grade_levels: Optional[List[int]] = None
    class_ids: Optional[List[UUID]] = None
    subject_ids: Optional[List[UUID]] = None
    teacher_ids: Optional[List[UUID]] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = Field(None, max_length=50)
    recurrence_end_date: Optional[date] = None
    reminder_days: Optional[List[int]] = None
    is_public: Optional[bool] = None
    requires_attendance: Optional[bool] = None
    max_participants: Optional[int] = Field(None, gt=0)
    registration_required: Optional[bool] = None
    registration_deadline: Optional[date] = None
    status: Optional[str] = Field(None, pattern=r'^(scheduled|confirmed|cancelled|completed|postponed)$')


class CalendarEvent(CalendarEventBase):
    """Calendar event response schema"""
    id: UUID
    school_id: UUID
    academic_year_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: Optional[UUID]

    class Config:
        from_attributes = True


# =====================================================
# DASHBOARD AND ANALYTICS SCHEMAS
# =====================================================

class AcademicDashboard(BaseModel):
    """Academic dashboard data schema"""
    school_id: UUID
    academic_year_id: UUID
    total_subjects: int
    total_classes: int
    total_teachers: int
    total_students: int
    average_attendance_rate: Decimal
    total_assessments: int
    completed_assessments: int
    pending_assessments: int
    recent_grades: List[Dict[str, Any]]
    upcoming_events: List[Dict[str, Any]]
    attendance_trend: List[Dict[str, Any]]
    grade_distribution: List[Dict[str, Any]]
    subject_performance: List[Dict[str, Any]]


class TeacherDashboard(BaseModel):
    """Teacher dashboard data schema"""
    teacher_id: UUID
    school_id: UUID
    academic_year_id: UUID
    total_classes: int
    total_subjects: int
    total_students: int
    my_attendance_rate: Decimal
    pending_assessments: int
    recent_lesson_plans: List[Dict[str, Any]]
    upcoming_sessions: List[Dict[str, Any]]
    grade_summary: List[Dict[str, Any]]


class StudentPerformance(BaseModel):
    """Student performance summary schema"""
    student_id: UUID
    student_name: str
    grade_level: int
    class_name: str
    overall_average: Decimal
    attendance_rate: Decimal
    subject_grades: List[Dict[str, Any]]
    recent_assessments: List[Dict[str, Any]]
    strengths: List[str]
    areas_for_improvement: List[str]


# =====================================================
# RESPONSE SCHEMAS
# =====================================================

class PaginatedResponse(BaseModel):
    """Paginated response schema"""
    items: List[Any]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class BulkOperationResponse(BaseModel):
    """Bulk operation response schema"""
    total_processed: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]]
    created_ids: List[UUID]


class ValidationError(BaseModel):
    """Validation error schema"""
    field: str
    message: str
    code: str


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    validation_errors: Optional[List[ValidationError]] = None