"""
Academic Management CRUD Operations
Comprehensive database operations for academic management with Zimbabwe-specific features
"""

from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
from sqlalchemy import and_, or_, func, text, select, update, delete, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError
import logging

from .models import (
    Subject, Curriculum, Period, Timetable, AttendanceSession, AttendanceRecord,
    Assessment, Grade, LessonPlan, CalendarEvent
)
from .schemas import (
    SubjectCreate, SubjectUpdate, CurriculumCreate, CurriculumUpdate,
    PeriodCreate, PeriodUpdate, TimetableCreate, TimetableUpdate,
    AttendanceSessionCreate, AttendanceRecordCreate, BulkAttendanceCreate,
    AssessmentCreate, AssessmentUpdate, GradeCreate, GradeUpdate, BulkGradeCreate,
    LessonPlanCreate, LessonPlanUpdate, CalendarEventCreate, CalendarEventUpdate,
    AttendanceStats, StudentPerformance, AcademicDashboard, TeacherDashboard,
    GradingScale, AttendanceStatus, AssessmentType, TermNumber
)
from core.exceptions import NotFoundError, ValidationError, DuplicateError
from core.utils import validate_uuid, calculate_grade_points, get_zimbabwe_grade

logger = logging.getLogger(__name__)

# =====================================================
# SUBJECT CRUD OPERATIONS
# =====================================================

async def create_subject(
    db: AsyncSession,
    subject_data: SubjectCreate,
    school_id: UUID,
    created_by: UUID
) -> Subject:
    """Create a new subject"""
    try:
        # Check for duplicate subject code within school
        existing = await db.execute(
            select(Subject).where(
                and_(
                    Subject.school_id == school_id,
                    Subject.code == subject_data.code.upper(),
                    Subject.is_active == True
                )
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateError(f"Subject with code '{subject_data.code}' already exists")

        subject = Subject(
            id=uuid4(),
            school_id=school_id,
            code=subject_data.code.upper(),
            name=subject_data.name,
            description=subject_data.description,
            grade_levels=subject_data.grade_levels,
            is_core=subject_data.is_core,
            is_practical=subject_data.is_practical,
            requires_lab=subject_data.requires_lab,
            pass_mark=subject_data.pass_mark,
            max_mark=subject_data.max_mark,
            credit_hours=subject_data.credit_hours,
            department=subject_data.department,
            language_of_instruction=subject_data.language_of_instruction,
            display_order=subject_data.display_order,
            created_by=created_by,
            updated_by=created_by
        )
        
        db.add(subject)
        await db.commit()
        await db.refresh(subject)
        
        logger.info(f"Created subject {subject.code} for school {school_id}")
        return subject
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Failed to create subject: {str(e)}")
        raise DuplicateError("Subject with this code already exists")


async def get_subject(
    db: AsyncSession,
    subject_id: UUID,
    school_id: UUID
) -> Optional[Subject]:
    """Get a subject by ID"""
    result = await db.execute(
        select(Subject).where(
            and_(
                Subject.id == subject_id,
                Subject.school_id == school_id,
                Subject.is_active == True
            )
        )
    )
    return result.scalar_one_or_none()


async def get_subjects(
    db: AsyncSession,
    school_id: UUID,
    grade_level: Optional[int] = None,
    department: Optional[str] = None,
    is_core: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
) -> Tuple[List[Subject], int]:
    """Get subjects with filtering and pagination"""
    query = select(Subject).where(
        and_(
            Subject.school_id == school_id,
            Subject.is_active == True
        )
    )
    
    # Apply filters
    if grade_level is not None:
        query = query.where(Subject.grade_levels.any(grade_level))
    
    if department:
        query = query.where(Subject.department == department)
        
    if is_core is not None:
        query = query.where(Subject.is_core == is_core)
    
    # Get total count
    count_query = select(func.count(Subject.id)).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total_count = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.order_by(Subject.display_order, Subject.name).offset(skip).limit(limit)
    
    result = await db.execute(query)
    subjects = result.scalars().all()
    
    return subjects, total_count


async def update_subject(
    db: AsyncSession,
    subject_id: UUID,
    subject_data: SubjectUpdate,
    school_id: UUID,
    updated_by: UUID
) -> Optional[Subject]:
    """Update a subject"""
    subject = await get_subject(db, subject_id, school_id)
    if not subject:
        raise NotFoundError("Subject not found")
    
    # Check for duplicate code if updating
    if subject_data.code and subject_data.code != subject.code:
        existing = await db.execute(
            select(Subject).where(
                and_(
                    Subject.school_id == school_id,
                    Subject.code == subject_data.code.upper(),
                    Subject.id != subject_id,
                    Subject.is_active == True
                )
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateError(f"Subject with code '{subject_data.code}' already exists")
    
    # Update fields
    update_data = subject_data.dict(exclude_unset=True)
    if 'code' in update_data:
        update_data['code'] = update_data['code'].upper()
    
    for field, value in update_data.items():
        setattr(subject, field, value)
    
    subject.updated_by = updated_by
    subject.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(subject)
    
    logger.info(f"Updated subject {subject.code} for school {school_id}")
    return subject


async def delete_subject(
    db: AsyncSession,
    subject_id: UUID,
    school_id: UUID,
    deleted_by: UUID
) -> bool:
    """Soft delete a subject"""
    subject = await get_subject(db, subject_id, school_id)
    if not subject:
        raise NotFoundError("Subject not found")
    
    # Check if subject has active timetables or assessments
    active_timetables = await db.execute(
        select(func.count(Timetable.id)).where(
            and_(
                Timetable.subject_id == subject_id,
                Timetable.is_active == True
            )
        )
    )
    
    if active_timetables.scalar() > 0:
        raise ValidationError("Cannot delete subject with active timetables")
    
    subject.is_active = False
    subject.updated_by = deleted_by
    subject.updated_at = datetime.utcnow()
    
    await db.commit()
    logger.info(f"Deleted subject {subject.code} for school {school_id}")
    return True


# =====================================================
# CURRICULUM CRUD OPERATIONS
# =====================================================

async def create_curriculum(
    db: AsyncSession,
    curriculum_data: CurriculumCreate,
    school_id: UUID,
    created_by: UUID
) -> Curriculum:
    """Create a new curriculum"""
    try:
        # Validate subject exists
        subject = await get_subject(db, curriculum_data.subject_id, school_id)
        if not subject:
            raise NotFoundError("Subject not found")
        
        # Check grade level compatibility
        if curriculum_data.grade_level not in subject.grade_levels:
            raise ValidationError(f"Subject {subject.code} is not available for grade {curriculum_data.grade_level}")
        
        curriculum = Curriculum(
            id=uuid4(),
            school_id=school_id,
            academic_year_id=curriculum_data.academic_year_id,
            name=curriculum_data.name,
            description=curriculum_data.description,
            grade_level=curriculum_data.grade_level,
            term_number=curriculum_data.term_number,
            subject_id=curriculum_data.subject_id,
            learning_objectives=curriculum_data.learning_objectives,
            learning_outcomes=curriculum_data.learning_outcomes,
            assessment_methods=curriculum_data.assessment_methods,
            resources_required=curriculum_data.resources_required,
            total_periods=curriculum_data.total_periods,
            practical_periods=curriculum_data.practical_periods,
            effective_from=curriculum_data.effective_from,
            effective_to=curriculum_data.effective_to,
            created_by=created_by,
            updated_by=created_by
        )
        
        db.add(curriculum)
        await db.commit()
        await db.refresh(curriculum)
        
        logger.info(f"Created curriculum {curriculum.name} for school {school_id}")
        return curriculum
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Failed to create curriculum: {str(e)}")
        raise DuplicateError("Curriculum with this name already exists")


async def get_curriculum(
    db: AsyncSession,
    curriculum_id: UUID,
    school_id: UUID
) -> Optional[Curriculum]:
    """Get a curriculum by ID"""
    result = await db.execute(
        select(Curriculum).where(
            and_(
                Curriculum.id == curriculum_id,
                Curriculum.school_id == school_id,
                Curriculum.is_active == True
            )
        ).options(selectinload(Curriculum.subject))
    )
    return result.scalar_one_or_none()


async def get_curricula(
    db: AsyncSession,
    school_id: UUID,
    academic_year_id: Optional[UUID] = None,
    grade_level: Optional[int] = None,
    subject_id: Optional[UUID] = None,
    term_number: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> Tuple[List[Curriculum], int]:
    """Get curricula with filtering and pagination"""
    query = select(Curriculum).where(
        and_(
            Curriculum.school_id == school_id,
            Curriculum.is_active == True
        )
    )
    
    # Apply filters
    if academic_year_id:
        query = query.where(Curriculum.academic_year_id == academic_year_id)
    
    if grade_level is not None:
        query = query.where(Curriculum.grade_level == grade_level)
        
    if subject_id:
        query = query.where(Curriculum.subject_id == subject_id)
        
    if term_number is not None:
        query = query.where(Curriculum.term_number == term_number)
    
    # Get total count
    count_query = select(func.count(Curriculum.id)).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total_count = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.order_by(Curriculum.grade_level, Curriculum.term_number, Curriculum.name).offset(skip).limit(limit)
    query = query.options(selectinload(Curriculum.subject))
    
    result = await db.execute(query)
    curricula = result.scalars().all()
    
    return curricula, total_count


# =====================================================
# TIMETABLE CRUD OPERATIONS
# =====================================================

async def create_period(
    db: AsyncSession,
    period_data: PeriodCreate,
    school_id: UUID,
    created_by: UUID
) -> Period:
    """Create a new period"""
    try:
        # Check for duplicate period number
        existing = await db.execute(
            select(Period).where(
                and_(
                    Period.school_id == school_id,
                    Period.period_number == period_data.period_number,
                    Period.is_active == True
                )
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateError(f"Period {period_data.period_number} already exists")
        
        # Check for time conflicts
        time_conflict = await db.execute(
            select(Period).where(
                and_(
                    Period.school_id == school_id,
                    Period.is_active == True,
                    or_(
                        and_(
                            Period.start_time <= period_data.start_time,
                            Period.end_time > period_data.start_time
                        ),
                        and_(
                            Period.start_time < period_data.end_time,
                            Period.end_time >= period_data.end_time
                        )
                    )
                )
            )
        )
        if time_conflict.scalar_one_or_none():
            raise ValidationError("Time slot conflicts with existing period")
        
        period = Period(
            id=uuid4(),
            school_id=school_id,
            period_number=period_data.period_number,
            name=period_data.name,
            start_time=period_data.start_time,
            end_time=period_data.end_time,
            is_break=period_data.is_break,
            break_type=period_data.break_type,
            created_by=created_by,
            updated_by=created_by
        )
        
        db.add(period)
        await db.commit()
        await db.refresh(period)
        
        logger.info(f"Created period {period.period_number} for school {school_id}")
        return period
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Failed to create period: {str(e)}")
        raise DuplicateError("Period with this number already exists")


async def create_timetable_entry(
    db: AsyncSession,
    timetable_data: TimetableCreate,
    school_id: UUID,
    created_by: UUID
) -> Timetable:
    """Create a new timetable entry"""
    try:
        # Check for teacher conflicts
        teacher_conflict = await db.execute(
            select(Timetable).where(
                and_(
                    Timetable.school_id == school_id,
                    Timetable.teacher_id == timetable_data.teacher_id,
                    Timetable.period_id == timetable_data.period_id,
                    Timetable.day_of_week == timetable_data.day_of_week,
                    Timetable.academic_year_id == timetable_data.academic_year_id,
                    Timetable.term_number == timetable_data.term_number,
                    Timetable.is_active == True,
                    or_(
                        and_(
                            Timetable.effective_from <= timetable_data.effective_from,
                            or_(
                                Timetable.effective_to.is_(None),
                                Timetable.effective_to >= timetable_data.effective_from
                            )
                        ),
                        and_(
                            Timetable.effective_from <= (timetable_data.effective_to or date.max),
                            or_(
                                Timetable.effective_to.is_(None),
                                Timetable.effective_to >= (timetable_data.effective_to or date.max)
                            )
                        )
                    )
                )
            )
        )
        if teacher_conflict.scalar_one_or_none():
            raise ValidationError("Teacher already has a class at this time")
        
        # Check for class conflicts
        class_conflict = await db.execute(
            select(Timetable).where(
                and_(
                    Timetable.school_id == school_id,
                    Timetable.class_id == timetable_data.class_id,
                    Timetable.period_id == timetable_data.period_id,
                    Timetable.day_of_week == timetable_data.day_of_week,
                    Timetable.academic_year_id == timetable_data.academic_year_id,
                    Timetable.term_number == timetable_data.term_number,
                    Timetable.is_active == True,
                    or_(
                        and_(
                            Timetable.effective_from <= timetable_data.effective_from,
                            or_(
                                Timetable.effective_to.is_(None),
                                Timetable.effective_to >= timetable_data.effective_from
                            )
                        ),
                        and_(
                            Timetable.effective_from <= (timetable_data.effective_to or date.max),
                            or_(
                                Timetable.effective_to.is_(None),
                                Timetable.effective_to >= (timetable_data.effective_to or date.max)
                            )
                        )
                    )
                )
            )
        )
        if class_conflict.scalar_one_or_none():
            raise ValidationError("Class already has a subject at this time")
        
        timetable = Timetable(
            id=uuid4(),
            school_id=school_id,
            academic_year_id=timetable_data.academic_year_id,
            term_number=timetable_data.term_number,
            class_id=timetable_data.class_id,
            subject_id=timetable_data.subject_id,
            teacher_id=timetable_data.teacher_id,
            period_id=timetable_data.period_id,
            day_of_week=timetable_data.day_of_week,
            room_number=timetable_data.room_number,
            is_double_period=timetable_data.is_double_period,
            is_practical=timetable_data.is_practical,
            week_pattern=timetable_data.week_pattern,
            effective_from=timetable_data.effective_from,
            effective_to=timetable_data.effective_to,
            notes=timetable_data.notes,
            created_by=created_by,
            updated_by=created_by
        )
        
        db.add(timetable)
        await db.commit()
        await db.refresh(timetable)
        
        logger.info(f"Created timetable entry for school {school_id}")
        return timetable
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Failed to create timetable entry: {str(e)}")
        raise ValidationError("Timetable entry conflicts with existing schedule")


# =====================================================
# ATTENDANCE CRUD OPERATIONS
# =====================================================

async def create_attendance_session(
    db: AsyncSession,
    session_data: AttendanceSessionCreate,
    school_id: UUID,
    created_by: UUID
) -> AttendanceSession:
    """Create a new attendance session"""
    try:
        # Validate timetable entry exists
        timetable = await db.execute(
            select(Timetable).where(
                and_(
                    Timetable.id == session_data.timetable_id,
                    Timetable.school_id == school_id,
                    Timetable.is_active == True
                )
            )
        )
        timetable_entry = timetable.scalar_one_or_none()
        if not timetable_entry:
            raise NotFoundError("Timetable entry not found")
        
        # Check for duplicate session
        existing = await db.execute(
            select(AttendanceSession).where(
                and_(
                    AttendanceSession.school_id == school_id,
                    AttendanceSession.timetable_id == session_data.timetable_id,
                    AttendanceSession.session_date == session_data.session_date
                )
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateError("Attendance session already exists for this date")
        
        session = AttendanceSession(
            id=uuid4(),
            school_id=school_id,
            timetable_id=session_data.timetable_id,
            period_id=timetable_entry.period_id,
            teacher_id=timetable_entry.teacher_id,
            subject_id=timetable_entry.subject_id,
            class_id=timetable_entry.class_id,
            session_date=session_data.session_date,
            session_type=session_data.session_type,
            notes=session_data.notes,
            created_by=created_by,
            updated_by=created_by
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        logger.info(f"Created attendance session for school {school_id}")
        return session
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Failed to create attendance session: {str(e)}")
        raise DuplicateError("Attendance session already exists")


async def mark_bulk_attendance(
    db: AsyncSession,
    attendance_data: BulkAttendanceCreate,
    school_id: UUID,
    marked_by: UUID
) -> List[AttendanceRecord]:
    """Mark attendance for multiple students"""
    try:
        # Validate attendance session exists
        session = await db.execute(
            select(AttendanceSession).where(
                and_(
                    AttendanceSession.id == attendance_data.attendance_session_id,
                    AttendanceSession.school_id == school_id
                )
            )
        )
        attendance_session = session.scalar_one_or_none()
        if not attendance_session:
            raise NotFoundError("Attendance session not found")
        
        # Clear existing attendance records
        await db.execute(
            delete(AttendanceRecord).where(
                AttendanceRecord.attendance_session_id == attendance_data.attendance_session_id
            )
        )
        
        # Create new attendance records
        attendance_records = []
        for record_data in attendance_data.attendance_records:
            record = AttendanceRecord(
                id=uuid4(),
                school_id=school_id,
                attendance_session_id=attendance_data.attendance_session_id,
                student_id=record_data.student_id,
                attendance_status=record_data.attendance_status,
                arrival_time=record_data.arrival_time,
                departure_time=record_data.departure_time,
                excuse_reason=record_data.excuse_reason,
                is_excused=record_data.is_excused,
                notes=record_data.notes,
                marked_by=marked_by,
                marked_at=datetime.utcnow(),
                created_by=marked_by,
                updated_by=marked_by
            )
            attendance_records.append(record)
        
        db.add_all(attendance_records)
        
        # Update session statistics
        total_students = len(attendance_records)
        present_students = sum(1 for r in attendance_records if r.attendance_status == AttendanceStatus.PRESENT)
        absent_students = sum(1 for r in attendance_records if r.attendance_status == AttendanceStatus.ABSENT)
        late_students = sum(1 for r in attendance_records if r.attendance_status == AttendanceStatus.LATE)
        
        attendance_session.total_students = total_students
        attendance_session.present_students = present_students
        attendance_session.absent_students = absent_students
        attendance_session.late_students = late_students
        attendance_session.attendance_marked = True
        attendance_session.marked_by = marked_by
        attendance_session.marked_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"Marked bulk attendance for {total_students} students")
        return attendance_records
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Failed to mark bulk attendance: {str(e)}")
        raise ValidationError("Failed to mark attendance")


async def get_attendance_stats(
    db: AsyncSession,
    school_id: UUID,
    class_id: Optional[UUID] = None,
    subject_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> AttendanceStats:
    """Get attendance statistics"""
    query = select(
        func.count(AttendanceRecord.id).label('total_records'),
        func.sum(func.case([(AttendanceRecord.attendance_status == AttendanceStatus.PRESENT, 1)], else_=0)).label('present'),
        func.sum(func.case([(AttendanceRecord.attendance_status == AttendanceStatus.ABSENT, 1)], else_=0)).label('absent'),
        func.sum(func.case([(AttendanceRecord.attendance_status == AttendanceStatus.LATE, 1)], else_=0)).label('late')
    ).select_from(
        AttendanceRecord.join(AttendanceSession)
    ).where(
        AttendanceRecord.school_id == school_id
    )
    
    if class_id:
        query = query.where(AttendanceSession.class_id == class_id)
    
    if subject_id:
        query = query.where(AttendanceSession.subject_id == subject_id)
    
    if start_date:
        query = query.where(AttendanceSession.session_date >= start_date)
    
    if end_date:
        query = query.where(AttendanceSession.session_date <= end_date)
    
    result = await db.execute(query)
    stats = result.first()
    
    total_students = stats.total_records if stats.total_records else 0
    present_students = stats.present if stats.present else 0
    absent_students = stats.absent if stats.absent else 0
    late_students = stats.late if stats.late else 0
    
    attendance_rate = Decimal(0)
    if total_students > 0:
        attendance_rate = Decimal(present_students + late_students) / Decimal(total_students) * 100
    
    return AttendanceStats(
        total_students=total_students,
        present_students=present_students,
        absent_students=absent_students,
        late_students=late_students,
        attendance_rate=attendance_rate.quantize(Decimal('0.01'))
    )


# =====================================================
# ASSESSMENT CRUD OPERATIONS
# =====================================================

async def create_assessment(
    db: AsyncSession,
    assessment_data: AssessmentCreate,
    school_id: UUID,
    created_by: UUID
) -> Assessment:
    """Create a new assessment"""
    try:
        assessment = Assessment(
            id=uuid4(),
            school_id=school_id,
            academic_year_id=assessment_data.academic_year_id,
            name=assessment_data.name,
            description=assessment_data.description,
            subject_id=assessment_data.subject_id,
            class_id=assessment_data.class_id,
            teacher_id=assessment_data.teacher_id,
            term_number=assessment_data.term_number,
            assessment_type=assessment_data.assessment_type,
            assessment_category=assessment_data.assessment_category,
            total_marks=assessment_data.total_marks,
            pass_mark=assessment_data.pass_mark,
            weight_percentage=assessment_data.weight_percentage,
            assessment_date=assessment_data.assessment_date,
            due_date=assessment_data.due_date,
            duration_minutes=assessment_data.duration_minutes,
            instructions=assessment_data.instructions,
            resources_allowed=assessment_data.resources_allowed,
            is_group_assessment=assessment_data.is_group_assessment,
            max_group_size=assessment_data.max_group_size,
            created_by=created_by,
            updated_by=created_by
        )
        
        db.add(assessment)
        await db.commit()
        await db.refresh(assessment)
        
        logger.info(f"Created assessment {assessment.name} for school {school_id}")
        return assessment
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Failed to create assessment: {str(e)}")
        raise DuplicateError("Assessment with this name already exists")


async def submit_bulk_grades(
    db: AsyncSession,
    grades_data: BulkGradeCreate,
    school_id: UUID,
    graded_by: UUID
) -> List[Grade]:
    """Submit grades for multiple students"""
    try:
        # Validate assessment exists
        assessment = await db.execute(
            select(Assessment).where(
                and_(
                    Assessment.id == grades_data.assessment_id,
                    Assessment.school_id == school_id
                )
            )
        )
        assessment_record = assessment.scalar_one_or_none()
        if not assessment_record:
            raise NotFoundError("Assessment not found")
        
        # Clear existing grades
        await db.execute(
            delete(Grade).where(
                Grade.assessment_id == grades_data.assessment_id
            )
        )
        
        # Create new grades
        grades = []
        for grade_data in grades_data.grades:
            # Calculate percentage and letter grade
            percentage_score = None
            letter_grade = None
            grade_points = None
            
            if grade_data.raw_score is not None:
                percentage_score = (grade_data.raw_score / assessment_record.total_marks) * 100
                letter_grade = get_zimbabwe_grade(percentage_score)
                grade_points = calculate_grade_points(letter_grade)
            
            grade = Grade(
                id=uuid4(),
                school_id=school_id,
                assessment_id=grades_data.assessment_id,
                student_id=grade_data.student_id,
                raw_score=grade_data.raw_score,
                percentage_score=percentage_score,
                letter_grade=letter_grade,
                grade_points=grade_points,
                is_absent=grade_data.is_absent,
                is_excused=grade_data.is_excused,
                submission_date=grade_data.submission_date,
                feedback=grade_data.feedback,
                improvement_suggestions=grade_data.improvement_suggestions,
                next_steps=grade_data.next_steps,
                graded_by=graded_by,
                graded_at=datetime.utcnow(),
                created_by=graded_by,
                updated_by=graded_by
            )
            grades.append(grade)
        
        db.add_all(grades)
        await db.commit()
        
        logger.info(f"Submitted {len(grades)} grades for assessment {assessment_record.name}")
        return grades
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Failed to submit grades: {str(e)}")
        raise ValidationError("Failed to submit grades")


# =====================================================
# DASHBOARD OPERATIONS
# =====================================================

async def get_academic_dashboard(
    db: AsyncSession,
    school_id: UUID,
    academic_year_id: UUID
) -> AcademicDashboard:
    """Get academic dashboard data"""
    # Get basic counts
    subjects_count = await db.execute(
        select(func.count(Subject.id)).where(
            and_(Subject.school_id == school_id, Subject.is_active == True)
        )
    )
    
    assessments_stats = await db.execute(
        select(
            func.count(Assessment.id).label('total'),
            func.sum(func.case([(Assessment.status == 'completed', 1)], else_=0)).label('completed'),
            func.sum(func.case([(Assessment.status == 'published', 1)], else_=0)).label('pending')
        ).where(
            and_(
                Assessment.school_id == school_id,
                Assessment.academic_year_id == academic_year_id
            )
        )
    )
    
    # Get attendance rate
    attendance_stats = await get_attendance_stats(db, school_id)
    
    # Get recent grades (placeholder)
    recent_grades = []
    
    # Get upcoming events (placeholder)
    upcoming_events = []
    
    # Get trends (placeholder)
    attendance_trend = []
    grade_distribution = []
    subject_performance = []
    
    stats = assessments_stats.first()
    
    return AcademicDashboard(
        school_id=school_id,
        academic_year_id=academic_year_id,
        total_subjects=subjects_count.scalar(),
        total_classes=0,  # TODO: Get from SIS module
        total_teachers=0,  # TODO: Get from SIS module
        total_students=0,  # TODO: Get from SIS module
        average_attendance_rate=attendance_stats.attendance_rate,
        total_assessments=stats.total if stats.total else 0,
        completed_assessments=stats.completed if stats.completed else 0,
        pending_assessments=stats.pending if stats.pending else 0,
        recent_grades=recent_grades,
        upcoming_events=upcoming_events,
        attendance_trend=attendance_trend,
        grade_distribution=grade_distribution,
        subject_performance=subject_performance
    )


async def get_teacher_dashboard(
    db: AsyncSession,
    teacher_id: UUID,
    school_id: UUID,
    academic_year_id: UUID
) -> TeacherDashboard:
    """Get teacher dashboard data"""
    # Get teacher's classes and subjects
    teacher_subjects = await db.execute(
        select(func.count(func.distinct(Timetable.subject_id))).where(
            and_(
                Timetable.teacher_id == teacher_id,
                Timetable.school_id == school_id,
                Timetable.academic_year_id == academic_year_id,
                Timetable.is_active == True
            )
        )
    )
    
    teacher_classes = await db.execute(
        select(func.count(func.distinct(Timetable.class_id))).where(
            and_(
                Timetable.teacher_id == teacher_id,
                Timetable.school_id == school_id,
                Timetable.academic_year_id == academic_year_id,
                Timetable.is_active == True
            )
        )
    )
    
    # Get pending assessments
    pending_assessments = await db.execute(
        select(func.count(Assessment.id)).where(
            and_(
                Assessment.teacher_id == teacher_id,
                Assessment.school_id == school_id,
                Assessment.academic_year_id == academic_year_id,
                Assessment.status == 'published'
            )
        )
    )
    
    return TeacherDashboard(
        teacher_id=teacher_id,
        school_id=school_id,
        academic_year_id=academic_year_id,
        total_classes=teacher_classes.scalar(),
        total_subjects=teacher_subjects.scalar(),
        total_students=0,  # TODO: Calculate from enrolled students
        my_attendance_rate=Decimal(0),  # TODO: Calculate teacher attendance
        pending_assessments=pending_assessments.scalar(),
        recent_lesson_plans=[],
        upcoming_sessions=[],
        grade_summary=[]
    )