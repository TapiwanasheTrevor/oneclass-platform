"""
Academic Management CRUD Tests
Comprehensive unit tests for academic management CRUD operations
"""

import pytest
import pytest_asyncio
from datetime import datetime, date, time
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ..crud import (
    create_subject, get_subject, get_subjects, update_subject, delete_subject,
    create_curriculum, get_curriculum, get_curricula,
    create_period, create_timetable_entry,
    create_attendance_session, mark_bulk_attendance, get_attendance_stats,
    create_assessment, submit_bulk_grades,
    get_academic_dashboard, get_teacher_dashboard
)
from ..schemas import (
    SubjectCreate, SubjectUpdate, CurriculumCreate,
    PeriodCreate, TimetableCreate, AttendanceSessionCreate,
    AttendanceRecordCreate, BulkAttendanceCreate,
    AssessmentCreate, GradeCreate, BulkGradeCreate,
    GradingScale, AttendanceStatus, AssessmentType, AssessmentCategory,
    TermNumber, SessionType
)
from core.exceptions import NotFoundError, ValidationError, DuplicateError


class TestSubjectCRUD:
    """Test suite for Subject CRUD operations"""

    @pytest_asyncio.fixture
    async def sample_subject_data(self):
        """Sample subject data for testing"""
        return SubjectCreate(
            code="MATH101",
            name="Mathematics",
            description="Basic mathematics course",
            grade_levels=[10, 11, 12],
            is_core=True,
            is_practical=False,
            requires_lab=False,
            pass_mark=Decimal("50.00"),
            max_mark=Decimal("100.00"),
            credit_hours=3,
            department="Mathematics",
            language_of_instruction="English",
            display_order=1
        )

    async def test_create_subject_success(self, db_session: AsyncSession, school_id: str, user_id: str, sample_subject_data: SubjectCreate):
        """Test successful subject creation"""
        subject = await create_subject(
            db=db_session,
            subject_data=sample_subject_data,
            school_id=school_id,
            created_by=user_id
        )
        
        assert subject.id is not None
        assert subject.school_id == school_id
        assert subject.code == "MATH101"
        assert subject.name == "Mathematics"
        assert subject.grade_levels == [10, 11, 12]
        assert subject.is_core is True
        assert subject.is_active is True
        assert subject.created_by == user_id

    async def test_create_subject_duplicate_code(self, db_session: AsyncSession, school_id: str, user_id: str, sample_subject_data: SubjectCreate):
        """Test subject creation with duplicate code"""
        # Create first subject
        await create_subject(
            db=db_session,
            subject_data=sample_subject_data,
            school_id=school_id,
            created_by=user_id
        )
        
        # Try to create second subject with same code
        with pytest.raises(DuplicateError):
            await create_subject(
                db=db_session,
                subject_data=sample_subject_data,
                school_id=school_id,
                created_by=user_id
            )

    async def test_create_subject_invalid_grade_levels(self, db_session: AsyncSession, school_id: str, user_id: str):
        """Test subject creation with invalid grade levels"""
        invalid_subject_data = SubjectCreate(
            code="INVALID",
            name="Invalid Subject",
            grade_levels=[0, 14],  # Invalid grade levels
            is_core=False
        )
        
        with pytest.raises(ValidationError):
            await create_subject(
                db=db_session,
                subject_data=invalid_subject_data,
                school_id=school_id,
                created_by=user_id
            )

    async def test_get_subject_success(self, db_session: AsyncSession, school_id: str, user_id: str, sample_subject_data: SubjectCreate):
        """Test successful subject retrieval"""
        created_subject = await create_subject(
            db=db_session,
            subject_data=sample_subject_data,
            school_id=school_id,
            created_by=user_id
        )
        
        retrieved_subject = await get_subject(
            db=db_session,
            subject_id=created_subject.id,
            school_id=school_id
        )
        
        assert retrieved_subject is not None
        assert retrieved_subject.id == created_subject.id
        assert retrieved_subject.code == "MATH101"

    async def test_get_subject_not_found(self, db_session: AsyncSession, school_id: str):
        """Test subject retrieval with non-existent ID"""
        non_existent_id = uuid4()
        subject = await get_subject(
            db=db_session,
            subject_id=non_existent_id,
            school_id=school_id
        )
        
        assert subject is None

    async def test_get_subjects_with_filters(self, db_session: AsyncSession, school_id: str, user_id: str):
        """Test subject listing with filters"""
        # Create multiple subjects
        subjects_data = [
            SubjectCreate(code="MATH", name="Mathematics", grade_levels=[10, 11], is_core=True, department="Mathematics"),
            SubjectCreate(code="ENG", name="English", grade_levels=[10, 11, 12], is_core=True, department="Languages"),
            SubjectCreate(code="ART", name="Art", grade_levels=[10], is_core=False, department="Arts")
        ]
        
        for subject_data in subjects_data:
            await create_subject(
                db=db_session,
                subject_data=subject_data,
                school_id=school_id,
                created_by=user_id
            )
        
        # Test filter by grade level
        subjects, total = await get_subjects(
            db=db_session,
            school_id=school_id,
            grade_level=10
        )
        assert len(subjects) == 3  # All subjects have grade 10
        
        # Test filter by core subjects
        subjects, total = await get_subjects(
            db=db_session,
            school_id=school_id,
            is_core=True
        )
        assert len(subjects) == 2  # Math and English are core
        
        # Test filter by department
        subjects, total = await get_subjects(
            db=db_session,
            school_id=school_id,
            department="Mathematics"
        )
        assert len(subjects) == 1  # Only Math in Mathematics department

    async def test_update_subject_success(self, db_session: AsyncSession, school_id: str, user_id: str, sample_subject_data: SubjectCreate):
        """Test successful subject update"""
        created_subject = await create_subject(
            db=db_session,
            subject_data=sample_subject_data,
            school_id=school_id,
            created_by=user_id
        )
        
        update_data = SubjectUpdate(
            name="Advanced Mathematics",
            description="Advanced mathematics course",
            grade_levels=[11, 12],
            is_practical=True
        )
        
        updated_subject = await update_subject(
            db=db_session,
            subject_id=created_subject.id,
            subject_data=update_data,
            school_id=school_id,
            updated_by=user_id
        )
        
        assert updated_subject.name == "Advanced Mathematics"
        assert updated_subject.grade_levels == [11, 12]
        assert updated_subject.is_practical is True
        assert updated_subject.updated_by == user_id

    async def test_delete_subject_success(self, db_session: AsyncSession, school_id: str, user_id: str, sample_subject_data: SubjectCreate):
        """Test successful subject deletion (soft delete)"""
        created_subject = await create_subject(
            db=db_session,
            subject_data=sample_subject_data,
            school_id=school_id,
            created_by=user_id
        )
        
        result = await delete_subject(
            db=db_session,
            subject_id=created_subject.id,
            school_id=school_id,
            deleted_by=user_id
        )
        
        assert result is True
        
        # Verify subject is soft deleted
        deleted_subject = await get_subject(
            db=db_session,
            subject_id=created_subject.id,
            school_id=school_id
        )
        assert deleted_subject is None  # Should not be returned in normal queries


class TestCurriculumCRUD:
    """Test suite for Curriculum CRUD operations"""

    @pytest_asyncio.fixture
    async def sample_curriculum_data(self, subject_id: str, academic_year_id: str):
        """Sample curriculum data for testing"""
        return CurriculumCreate(
            academic_year_id=academic_year_id,
            name="Grade 10 Mathematics Curriculum",
            description="Comprehensive mathematics curriculum for grade 10",
            grade_level=10,
            term_number=TermNumber.TERM_1,
            subject_id=subject_id,
            learning_objectives=["Understand algebra", "Master geometry"],
            learning_outcomes=["Solve algebraic equations", "Calculate areas"],
            assessment_methods=["Tests", "Assignments"],
            resources_required=["Textbook", "Calculator"],
            total_periods=40,
            practical_periods=10,
            effective_from=date(2024, 1, 15)
        )

    async def test_create_curriculum_success(self, db_session: AsyncSession, school_id: str, user_id: str, subject_id: str, sample_curriculum_data: CurriculumCreate):
        """Test successful curriculum creation"""
        curriculum = await create_curriculum(
            db=db_session,
            curriculum_data=sample_curriculum_data,
            school_id=school_id,
            created_by=user_id
        )
        
        assert curriculum.id is not None
        assert curriculum.school_id == school_id
        assert curriculum.name == "Grade 10 Mathematics Curriculum"
        assert curriculum.grade_level == 10
        assert curriculum.term_number == TermNumber.TERM_1
        assert curriculum.total_periods == 40
        assert curriculum.practical_periods == 10
        assert curriculum.is_active is True

    async def test_create_curriculum_invalid_subject(self, db_session: AsyncSession, school_id: str, user_id: str, academic_year_id: str):
        """Test curriculum creation with invalid subject"""
        invalid_curriculum_data = CurriculumCreate(
            academic_year_id=academic_year_id,
            name="Invalid Curriculum",
            grade_level=10,
            subject_id=str(uuid4()),  # Non-existent subject
            effective_from=date(2024, 1, 15)
        )
        
        with pytest.raises(NotFoundError):
            await create_curriculum(
                db=db_session,
                curriculum_data=invalid_curriculum_data,
                school_id=school_id,
                created_by=user_id
            )

    async def test_get_curricula_with_filters(self, db_session: AsyncSession, school_id: str, user_id: str, subject_id: str, academic_year_id: str):
        """Test curricula listing with filters"""
        # Create multiple curricula
        curricula_data = [
            CurriculumCreate(
                academic_year_id=academic_year_id,
                name="Grade 10 Term 1",
                grade_level=10,
                term_number=TermNumber.TERM_1,
                subject_id=subject_id,
                effective_from=date(2024, 1, 15)
            ),
            CurriculumCreate(
                academic_year_id=academic_year_id,
                name="Grade 10 Term 2",
                grade_level=10,
                term_number=TermNumber.TERM_2,
                subject_id=subject_id,
                effective_from=date(2024, 5, 1)
            ),
            CurriculumCreate(
                academic_year_id=academic_year_id,
                name="Grade 11 Term 1",
                grade_level=11,
                term_number=TermNumber.TERM_1,
                subject_id=subject_id,
                effective_from=date(2024, 1, 15)
            )
        ]
        
        for curriculum_data in curricula_data:
            await create_curriculum(
                db=db_session,
                curriculum_data=curriculum_data,
                school_id=school_id,
                created_by=user_id
            )
        
        # Test filter by grade level
        curricula, total = await get_curricula(
            db=db_session,
            school_id=school_id,
            grade_level=10
        )
        assert len(curricula) == 2  # Two Grade 10 curricula
        
        # Test filter by term
        curricula, total = await get_curricula(
            db=db_session,
            school_id=school_id,
            term_number=TermNumber.TERM_1
        )
        assert len(curricula) == 2  # Two Term 1 curricula


class TestTimetableCRUD:
    """Test suite for Timetable CRUD operations"""

    @pytest_asyncio.fixture
    async def sample_period_data(self):
        """Sample period data for testing"""
        return PeriodCreate(
            period_number=1,
            name="Period 1",
            start_time=time(8, 0),
            end_time=time(8, 40),
            is_break=False
        )

    @pytest_asyncio.fixture
    async def sample_timetable_data(self, academic_year_id: str, class_id: str, subject_id: str, teacher_id: str, period_id: str):
        """Sample timetable data for testing"""
        return TimetableCreate(
            academic_year_id=academic_year_id,
            term_number=TermNumber.TERM_1,
            class_id=class_id,
            subject_id=subject_id,
            teacher_id=teacher_id,
            period_id=period_id,
            day_of_week=1,  # Monday
            room_number="Room 101",
            is_double_period=False,
            is_practical=False,
            week_pattern="all",
            effective_from=date(2024, 1, 15)
        )

    async def test_create_period_success(self, db_session: AsyncSession, school_id: str, user_id: str, sample_period_data: PeriodCreate):
        """Test successful period creation"""
        period = await create_period(
            db=db_session,
            period_data=sample_period_data,
            school_id=school_id,
            created_by=user_id
        )
        
        assert period.id is not None
        assert period.school_id == school_id
        assert period.period_number == 1
        assert period.name == "Period 1"
        assert period.start_time == time(8, 0)
        assert period.end_time == time(8, 40)
        assert period.is_break is False

    async def test_create_period_duplicate_number(self, db_session: AsyncSession, school_id: str, user_id: str, sample_period_data: PeriodCreate):
        """Test period creation with duplicate number"""
        # Create first period
        await create_period(
            db=db_session,
            period_data=sample_period_data,
            school_id=school_id,
            created_by=user_id
        )
        
        # Try to create second period with same number
        with pytest.raises(DuplicateError):
            await create_period(
                db=db_session,
                period_data=sample_period_data,
                school_id=school_id,
                created_by=user_id
            )

    async def test_create_period_invalid_time_order(self, db_session: AsyncSession, school_id: str, user_id: str):
        """Test period creation with invalid time order"""
        invalid_period_data = PeriodCreate(
            period_number=2,
            name="Invalid Period",
            start_time=time(9, 0),
            end_time=time(8, 0),  # End time before start time
            is_break=False
        )
        
        with pytest.raises(ValidationError):
            await create_period(
                db=db_session,
                period_data=invalid_period_data,
                school_id=school_id,
                created_by=user_id
            )

    async def test_create_timetable_entry_success(self, db_session: AsyncSession, school_id: str, user_id: str, sample_timetable_data: TimetableCreate):
        """Test successful timetable entry creation"""
        timetable = await create_timetable_entry(
            db=db_session,
            timetable_data=sample_timetable_data,
            school_id=school_id,
            created_by=user_id
        )
        
        assert timetable.id is not None
        assert timetable.school_id == school_id
        assert timetable.class_id == sample_timetable_data.class_id
        assert timetable.subject_id == sample_timetable_data.subject_id
        assert timetable.teacher_id == sample_timetable_data.teacher_id
        assert timetable.day_of_week == 1
        assert timetable.room_number == "Room 101"


class TestAttendanceCRUD:
    """Test suite for Attendance CRUD operations"""

    @pytest_asyncio.fixture
    async def sample_attendance_session_data(self, timetable_id: str):
        """Sample attendance session data for testing"""
        return AttendanceSessionCreate(
            timetable_id=timetable_id,
            session_date=date(2024, 3, 15),
            session_type=SessionType.REGULAR,
            notes="Regular class session"
        )

    async def test_create_attendance_session_success(self, db_session: AsyncSession, school_id: str, user_id: str, sample_attendance_session_data: AttendanceSessionCreate):
        """Test successful attendance session creation"""
        session = await create_attendance_session(
            db=db_session,
            session_data=sample_attendance_session_data,
            school_id=school_id,
            created_by=user_id
        )
        
        assert session.id is not None
        assert session.school_id == school_id
        assert session.timetable_id == sample_attendance_session_data.timetable_id
        assert session.session_date == date(2024, 3, 15)
        assert session.session_type == SessionType.REGULAR
        assert session.attendance_marked is False

    async def test_mark_bulk_attendance_success(self, db_session: AsyncSession, school_id: str, user_id: str, attendance_session_id: str, student_ids: list):
        """Test successful bulk attendance marking"""
        attendance_records = [
            AttendanceRecordCreate(
                student_id=student_ids[0],
                attendance_status=AttendanceStatus.PRESENT,
                arrival_time=time(8, 0)
            ),
            AttendanceRecordCreate(
                student_id=student_ids[1],
                attendance_status=AttendanceStatus.LATE,
                arrival_time=time(8, 15)
            ),
            AttendanceRecordCreate(
                student_id=student_ids[2],
                attendance_status=AttendanceStatus.ABSENT,
                is_excused=True,
                excuse_reason="Sick"
            )
        ]
        
        bulk_attendance = BulkAttendanceCreate(
            attendance_session_id=attendance_session_id,
            attendance_records=attendance_records
        )
        
        records = await mark_bulk_attendance(
            db=db_session,
            attendance_data=bulk_attendance,
            school_id=school_id,
            marked_by=user_id
        )
        
        assert len(records) == 3
        assert records[0].attendance_status == AttendanceStatus.PRESENT
        assert records[1].attendance_status == AttendanceStatus.LATE
        assert records[2].attendance_status == AttendanceStatus.ABSENT
        assert records[2].is_excused is True

    async def test_get_attendance_stats_success(self, db_session: AsyncSession, school_id: str, class_id: str):
        """Test attendance statistics calculation"""
        stats = await get_attendance_stats(
            db=db_session,
            school_id=school_id,
            class_id=class_id,
            start_date=date(2024, 3, 1),
            end_date=date(2024, 3, 31)
        )
        
        assert isinstance(stats.total_students, int)
        assert isinstance(stats.present_students, int)
        assert isinstance(stats.absent_students, int)
        assert isinstance(stats.late_students, int)
        assert isinstance(stats.attendance_rate, (int, float))
        assert 0 <= stats.attendance_rate <= 100


class TestAssessmentCRUD:
    """Test suite for Assessment CRUD operations"""

    @pytest_asyncio.fixture
    async def sample_assessment_data(self, academic_year_id: str, subject_id: str, class_id: str, teacher_id: str):
        """Sample assessment data for testing"""
        return AssessmentCreate(
            academic_year_id=academic_year_id,
            name="Mid-Term Mathematics Test",
            description="Comprehensive mathematics assessment",
            subject_id=subject_id,
            class_id=class_id,
            teacher_id=teacher_id,
            term_number=TermNumber.TERM_1,
            assessment_type=AssessmentType.TEST,
            assessment_category=AssessmentCategory.CONTINUOUS,
            total_marks=Decimal("100.00"),
            pass_mark=Decimal("50.00"),
            weight_percentage=Decimal("25.00"),
            assessment_date=date(2024, 3, 15),
            duration_minutes=90,
            instructions="Answer all questions",
            resources_allowed=["Calculator", "Formula sheet"],
            is_group_assessment=False
        )

    async def test_create_assessment_success(self, db_session: AsyncSession, school_id: str, user_id: str, sample_assessment_data: AssessmentCreate):
        """Test successful assessment creation"""
        assessment = await create_assessment(
            db=db_session,
            assessment_data=sample_assessment_data,
            school_id=school_id,
            created_by=user_id
        )
        
        assert assessment.id is not None
        assert assessment.school_id == school_id
        assert assessment.name == "Mid-Term Mathematics Test"
        assert assessment.total_marks == Decimal("100.00")
        assert assessment.pass_mark == Decimal("50.00")
        assert assessment.weight_percentage == Decimal("25.00")
        assert assessment.assessment_type == AssessmentType.TEST
        assert assessment.term_number == TermNumber.TERM_1

    async def test_submit_bulk_grades_success(self, db_session: AsyncSession, school_id: str, user_id: str, assessment_id: str, student_ids: list):
        """Test successful bulk grade submission"""
        grades = [
            GradeCreate(
                assessment_id=assessment_id,
                student_id=student_ids[0],
                raw_score=Decimal("85.00"),
                is_absent=False,
                feedback="Excellent work"
            ),
            GradeCreate(
                assessment_id=assessment_id,
                student_id=student_ids[1],
                raw_score=Decimal("72.00"),
                is_absent=False,
                feedback="Good effort"
            ),
            GradeCreate(
                assessment_id=assessment_id,
                student_id=student_ids[2],
                is_absent=True,
                is_excused=True
            )
        ]
        
        bulk_grades = BulkGradeCreate(
            assessment_id=assessment_id,
            grades=grades
        )
        
        submitted_grades = await submit_bulk_grades(
            db=db_session,
            grades_data=bulk_grades,
            school_id=school_id,
            graded_by=user_id
        )
        
        assert len(submitted_grades) == 3
        assert submitted_grades[0].raw_score == Decimal("85.00")
        assert submitted_grades[0].letter_grade == GradingScale.A  # 85% = A grade
        assert submitted_grades[1].raw_score == Decimal("72.00")
        assert submitted_grades[1].letter_grade == GradingScale.B  # 72% = B grade
        assert submitted_grades[2].is_absent is True
        assert submitted_grades[2].is_excused is True


class TestDashboardCRUD:
    """Test suite for Dashboard CRUD operations"""

    async def test_get_academic_dashboard_success(self, db_session: AsyncSession, school_id: str, academic_year_id: str):
        """Test academic dashboard data retrieval"""
        dashboard = await get_academic_dashboard(
            db=db_session,
            school_id=school_id,
            academic_year_id=academic_year_id
        )
        
        assert dashboard.school_id == school_id
        assert dashboard.academic_year_id == academic_year_id
        assert isinstance(dashboard.total_subjects, int)
        assert isinstance(dashboard.total_classes, int)
        assert isinstance(dashboard.total_teachers, int)
        assert isinstance(dashboard.total_students, int)
        assert isinstance(dashboard.average_attendance_rate, (int, float))
        assert isinstance(dashboard.total_assessments, int)
        assert isinstance(dashboard.completed_assessments, int)
        assert isinstance(dashboard.pending_assessments, int)

    async def test_get_teacher_dashboard_success(self, db_session: AsyncSession, school_id: str, teacher_id: str, academic_year_id: str):
        """Test teacher dashboard data retrieval"""
        dashboard = await get_teacher_dashboard(
            db=db_session,
            teacher_id=teacher_id,
            school_id=school_id,
            academic_year_id=academic_year_id
        )
        
        assert dashboard.teacher_id == teacher_id
        assert dashboard.school_id == school_id
        assert dashboard.academic_year_id == academic_year_id
        assert isinstance(dashboard.total_classes, int)
        assert isinstance(dashboard.total_subjects, int)
        assert isinstance(dashboard.total_students, int)
        assert isinstance(dashboard.my_attendance_rate, (int, float))
        assert isinstance(dashboard.pending_assessments, int)