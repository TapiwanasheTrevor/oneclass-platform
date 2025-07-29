"""
Academic-SIS Integration Service
Integration layer between Academic Management and Student Information System
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload, joinedload
import logging

from ..academic.models import Subject, Assessment, Grade, AttendanceSession, AttendanceRecord
from ..academic.schemas import StudentPerformance, AttendanceStats
from ..sis.models import Student, Class, Enrollment, Guardian
from ..sis.schemas import StudentWithDetails, ClassWithStudents
from core.exceptions import NotFoundError, ValidationError
from core.utils import calculate_age

logger = logging.getLogger(__name__)

class AcademicSISIntegration:
    """Integration service for Academic Management and SIS"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =====================================================
    # STUDENT DATA INTEGRATION
    # =====================================================
    
    async def get_class_students_for_academic(
        self,
        class_id: UUID,
        school_id: UUID,
        academic_year_id: UUID
    ) -> List[StudentWithDetails]:
        """Get all students in a class for academic operations"""
        try:
            # Get active enrollments for the class
            query = select(Student).join(
                Enrollment,
                and_(
                    Enrollment.student_id == Student.id,
                    Enrollment.class_id == class_id,
                    Enrollment.academic_year_id == academic_year_id,
                    Enrollment.status == 'active',
                    Enrollment.is_active == True
                )
            ).where(
                and_(
                    Student.school_id == school_id,
                    Student.is_active == True
                )
            ).options(
                selectinload(Student.guardians),
                selectinload(Student.enrollments)
            ).order_by(Student.first_name, Student.last_name)
            
            result = await self.db.execute(query)
            students = result.scalars().all()
            
            # Convert to StudentWithDetails
            student_details = []
            for student in students:
                # Get current enrollment
                current_enrollment = next(
                    (e for e in student.enrollments 
                     if e.class_id == class_id and e.academic_year_id == academic_year_id),
                    None
                )
                
                student_detail = StudentWithDetails(
                    id=student.id,
                    school_id=student.school_id,
                    student_number=student.student_number,
                    first_name=student.first_name,
                    last_name=student.last_name,
                    middle_names=student.middle_names,
                    preferred_name=student.preferred_name,
                    date_of_birth=student.date_of_birth,
                    gender=student.gender,
                    nationality=student.nationality,
                    national_id=student.national_id,
                    birth_certificate_number=student.birth_certificate_number,
                    phone_number=student.phone_number,
                    email_address=student.email_address,
                    physical_address=student.physical_address,
                    emergency_contact_name=student.emergency_contact_name,
                    emergency_contact_phone=student.emergency_contact_phone,
                    medical_conditions=student.medical_conditions,
                    dietary_requirements=student.dietary_requirements,
                    transport_method=student.transport_method,
                    previous_school=student.previous_school,
                    enrollment_date=current_enrollment.enrollment_date if current_enrollment else None,
                    grade_level=current_enrollment.grade_level if current_enrollment else None,
                    class_id=class_id,
                    guardians=[],  # Will be populated separately if needed
                    is_active=student.is_active,
                    created_at=student.created_at,
                    updated_at=student.updated_at
                )
                student_details.append(student_detail)
            
            logger.info(f"Retrieved {len(student_details)} students for class {class_id}")
            return student_details
            
        except Exception as e:
            logger.error(f"Failed to get class students: {str(e)}")
            raise ValidationError("Failed to retrieve class students")
    
    async def get_student_academic_performance(
        self,
        student_id: UUID,
        school_id: UUID,
        academic_year_id: UUID,
        term_number: Optional[int] = None
    ) -> StudentPerformance:
        """Get comprehensive academic performance for a student"""
        try:
            # Get student details
            student_query = select(Student).where(
                and_(
                    Student.id == student_id,
                    Student.school_id == school_id,
                    Student.is_active == True
                )
            ).options(selectinload(Student.enrollments))
            
            student_result = await self.db.execute(student_query)
            student = student_result.scalar_one_or_none()
            
            if not student:
                raise NotFoundError("Student not found")
            
            # Get current enrollment
            current_enrollment = next(
                (e for e in student.enrollments 
                 if e.academic_year_id == academic_year_id and e.status == 'active'),
                None
            )
            
            if not current_enrollment:
                raise NotFoundError("Student not enrolled for this academic year")
            
            # Get class details
            class_query = select(Class).where(Class.id == current_enrollment.class_id)
            class_result = await self.db.execute(class_query)
            class_obj = class_result.scalar_one_or_none()
            
            # Get student grades
            grades_query = select(Grade).join(
                Assessment,
                Assessment.id == Grade.assessment_id
            ).where(
                and_(
                    Grade.student_id == student_id,
                    Grade.school_id == school_id,
                    Assessment.academic_year_id == academic_year_id,
                    Assessment.is_active == True,
                    *([Assessment.term_number == term_number] if term_number else [])
                )
            ).options(joinedload(Grade.assessment))
            
            grades_result = await self.db.execute(grades_query)
            grades = grades_result.scalars().all()
            
            # Calculate overall average
            valid_grades = [g for g in grades if g.percentage_score is not None and not g.is_absent]
            overall_average = 0
            if valid_grades:
                total_weighted_score = sum(
                    g.percentage_score * g.assessment.weight_percentage 
                    for g in valid_grades
                )
                total_weight = sum(g.assessment.weight_percentage for g in valid_grades)
                overall_average = total_weighted_score / total_weight if total_weight > 0 else 0
            
            # Get attendance rate
            attendance_stats = await self.get_student_attendance_stats(
                student_id, school_id, academic_year_id, term_number
            )
            
            # Group grades by subject
            subject_grades = {}
            for grade in grades:
                subject_id = grade.assessment.subject_id
                if subject_id not in subject_grades:
                    subject_grades[subject_id] = {
                        'subject_id': str(subject_id),
                        'subject_name': '',  # Will be populated from subject data
                        'grades': [],
                        'average': 0,
                        'latest_grade': None
                    }
                
                subject_grades[subject_id]['grades'].append({
                    'assessment_name': grade.assessment.name,
                    'assessment_type': grade.assessment.assessment_type,
                    'percentage_score': grade.percentage_score,
                    'letter_grade': grade.letter_grade,
                    'assessment_date': grade.assessment.assessment_date.isoformat() if grade.assessment.assessment_date else None,
                    'feedback': grade.feedback
                })
            
            # Calculate subject averages
            for subject_data in subject_grades.values():
                valid_subject_grades = [g for g in subject_data['grades'] if g['percentage_score'] is not None]
                if valid_subject_grades:
                    subject_data['average'] = sum(g['percentage_score'] for g in valid_subject_grades) / len(valid_subject_grades)
                    subject_data['latest_grade'] = max(valid_subject_grades, key=lambda x: x['assessment_date'] or '1900-01-01')
            
            # Recent assessments
            recent_assessments = [
                {
                    'assessment_name': grade.assessment.name,
                    'subject_name': '',  # Will be populated
                    'assessment_type': grade.assessment.assessment_type,
                    'percentage_score': grade.percentage_score,
                    'letter_grade': grade.letter_grade,
                    'assessment_date': grade.assessment.assessment_date.isoformat() if grade.assessment.assessment_date else None
                }
                for grade in sorted(grades, key=lambda x: x.assessment.assessment_date or date.min, reverse=True)[:5]
                if grade.percentage_score is not None
            ]
            
            # Identify strengths and areas for improvement
            strengths = []
            areas_for_improvement = []
            
            for subject_data in subject_grades.values():
                if subject_data['average'] >= 80:
                    strengths.append(f"Excellent performance in {subject_data['subject_name']}")
                elif subject_data['average'] >= 70:
                    strengths.append(f"Good performance in {subject_data['subject_name']}")
                elif subject_data['average'] < 50:
                    areas_for_improvement.append(f"Needs improvement in {subject_data['subject_name']}")
            
            if attendance_stats.attendance_rate >= 95:
                strengths.append("Excellent attendance record")
            elif attendance_stats.attendance_rate < 80:
                areas_for_improvement.append("Poor attendance affecting academic performance")
            
            return StudentPerformance(
                student_id=str(student_id),
                student_name=f"{student.first_name} {student.last_name}",
                grade_level=current_enrollment.grade_level,
                class_name=class_obj.name if class_obj else '',
                overall_average=round(overall_average, 2),
                attendance_rate=attendance_stats.attendance_rate,
                subject_grades=list(subject_grades.values()),
                recent_assessments=recent_assessments,
                strengths=strengths,
                areas_for_improvement=areas_for_improvement
            )
            
        except Exception as e:
            logger.error(f"Failed to get student academic performance: {str(e)}")
            raise ValidationError("Failed to retrieve student performance data")
    
    async def get_student_attendance_stats(
        self,
        student_id: UUID,
        school_id: UUID,
        academic_year_id: UUID,
        term_number: Optional[int] = None
    ) -> AttendanceStats:
        """Get attendance statistics for a student"""
        try:
            # Base query for attendance records
            query = select(
                func.count(AttendanceRecord.id).label('total_sessions'),
                func.sum(func.case([(AttendanceRecord.attendance_status == 'present', 1)], else_=0)).label('present'),
                func.sum(func.case([(AttendanceRecord.attendance_status == 'absent', 1)], else_=0)).label('absent'),
                func.sum(func.case([(AttendanceRecord.attendance_status == 'late', 1)], else_=0)).label('late')
            ).select_from(
                AttendanceRecord.join(AttendanceSession)
            ).where(
                and_(
                    AttendanceRecord.student_id == student_id,
                    AttendanceRecord.school_id == school_id,
                    *([AttendanceSession.term_number == term_number] if term_number else [])
                )
            )
            
            result = await self.db.execute(query)
            stats = result.first()
            
            total_sessions = stats.total_sessions or 0
            present_sessions = stats.present or 0
            absent_sessions = stats.absent or 0
            late_sessions = stats.late or 0
            
            attendance_rate = 0
            if total_sessions > 0:
                attendance_rate = ((present_sessions + late_sessions) / total_sessions) * 100
            
            return AttendanceStats(
                total_students=1,  # Single student
                present_students=present_sessions,
                absent_students=absent_sessions,
                late_students=late_sessions,
                attendance_rate=round(attendance_rate, 2)
            )
            
        except Exception as e:
            logger.error(f"Failed to get student attendance stats: {str(e)}")
            return AttendanceStats(
                total_students=0,
                present_students=0,
                absent_students=0,
                late_students=0,
                attendance_rate=0
            )
    
    # =====================================================
    # CLASS MANAGEMENT INTEGRATION
    # =====================================================
    
    async def get_class_academic_summary(
        self,
        class_id: UUID,
        school_id: UUID,
        academic_year_id: UUID,
        term_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get comprehensive academic summary for a class"""
        try:
            # Get class details
            class_query = select(Class).where(
                and_(
                    Class.id == class_id,
                    Class.school_id == school_id,
                    Class.is_active == True
                )
            )
            class_result = await self.db.execute(class_query)
            class_obj = class_result.scalar_one_or_none()
            
            if not class_obj:
                raise NotFoundError("Class not found")
            
            # Get enrolled students count
            students_query = select(func.count(Enrollment.id)).where(
                and_(
                    Enrollment.class_id == class_id,
                    Enrollment.academic_year_id == academic_year_id,
                    Enrollment.status == 'active'
                )
            )
            students_result = await self.db.execute(students_query)
            total_students = students_result.scalar() or 0
            
            # Get assessments for this class
            assessments_query = select(
                func.count(Assessment.id).label('total_assessments'),
                func.sum(func.case([(Assessment.status == 'completed', 1)], else_=0)).label('completed_assessments')
            ).where(
                and_(
                    Assessment.class_id == class_id,
                    Assessment.school_id == school_id,
                    Assessment.academic_year_id == academic_year_id,
                    Assessment.is_active == True,
                    *([Assessment.term_number == term_number] if term_number else [])
                )
            )
            assessments_result = await self.db.execute(assessments_query)
            assessments_stats = assessments_result.first()
            
            # Get average performance
            grades_query = select(
                func.avg(Grade.percentage_score).label('class_average'),
                func.count(Grade.id).label('total_grades')
            ).select_from(
                Grade.join(Assessment)
            ).where(
                and_(
                    Assessment.class_id == class_id,
                    Assessment.school_id == school_id,
                    Assessment.academic_year_id == academic_year_id,
                    Grade.percentage_score.isnot(None),
                    Grade.is_absent == False,
                    *([Assessment.term_number == term_number] if term_number else [])
                )
            )
            grades_result = await self.db.execute(grades_query)
            grades_stats = grades_result.first()
            
            # Get attendance statistics
            attendance_query = select(
                func.count(AttendanceRecord.id).label('total_attendance_records'),
                func.sum(func.case([(AttendanceRecord.attendance_status.in_(['present', 'late']), 1)], else_=0)).label('present_records')
            ).select_from(
                AttendanceRecord.join(AttendanceSession)
            ).where(
                and_(
                    AttendanceSession.class_id == class_id,
                    AttendanceRecord.school_id == school_id,
                    *([AttendanceSession.term_number == term_number] if term_number else [])
                )
            )
            attendance_result = await self.db.execute(attendance_query)
            attendance_stats = attendance_result.first()
            
            # Calculate attendance rate
            attendance_rate = 0
            if attendance_stats.total_attendance_records and attendance_stats.total_attendance_records > 0:
                attendance_rate = (attendance_stats.present_records / attendance_stats.total_attendance_records) * 100
            
            return {
                'class_id': str(class_id),
                'class_name': class_obj.name,
                'grade_level': class_obj.grade_level,
                'total_students': total_students,
                'total_assessments': assessments_stats.total_assessments or 0,
                'completed_assessments': assessments_stats.completed_assessments or 0,
                'class_average': round(grades_stats.class_average or 0, 2),
                'total_grades': grades_stats.total_grades or 0,
                'attendance_rate': round(attendance_rate, 2),
                'teacher_id': class_obj.teacher_id,
                'academic_year_id': str(academic_year_id),
                'term_number': term_number
            }
            
        except Exception as e:
            logger.error(f"Failed to get class academic summary: {str(e)}")
            raise ValidationError("Failed to retrieve class academic summary")
    
    # =====================================================
    # PARENT/GUARDIAN INTEGRATION
    # =====================================================
    
    async def get_student_guardians_for_notifications(
        self,
        student_id: UUID,
        school_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get guardian information for academic notifications"""
        try:
            query = select(Guardian).join(
                Student.guardians.property.secondaryjoin
            ).where(
                and_(
                    Student.id == student_id,
                    Student.school_id == school_id,
                    Guardian.is_active == True,
                    Guardian.notification_preferences.op('->>')('academic_updates').astext == 'true'
                )
            )
            
            result = await self.db.execute(query)
            guardians = result.scalars().all()
            
            guardian_list = []
            for guardian in guardians:
                guardian_data = {
                    'id': str(guardian.id),
                    'name': f"{guardian.first_name} {guardian.last_name}",
                    'relationship': guardian.relationship,
                    'phone_number': guardian.phone_number,
                    'email_address': guardian.email_address,
                    'preferred_contact_method': guardian.preferred_contact_method,
                    'notification_preferences': guardian.notification_preferences
                }
                guardian_list.append(guardian_data)
            
            return guardian_list
            
        except Exception as e:
            logger.error(f"Failed to get student guardians: {str(e)}")
            return []
    
    # =====================================================
    # ENROLLMENT VALIDATION
    # =====================================================
    
    async def validate_student_enrollment_for_academic(
        self,
        student_id: UUID,
        class_id: UUID,
        subject_id: UUID,
        academic_year_id: UUID
    ) -> bool:
        """Validate if student is properly enrolled for academic operations"""
        try:
            # Check active enrollment
            enrollment_query = select(Enrollment).where(
                and_(
                    Enrollment.student_id == student_id,
                    Enrollment.class_id == class_id,
                    Enrollment.academic_year_id == academic_year_id,
                    Enrollment.status == 'active',
                    Enrollment.is_active == True
                )
            )
            
            result = await self.db.execute(enrollment_query)
            enrollment = result.scalar_one_or_none()
            
            if not enrollment:
                return False
            
            # Check if subject is available for the student's grade level
            subject_query = select(Subject).where(
                and_(
                    Subject.id == subject_id,
                    Subject.grade_levels.any(enrollment.grade_level),
                    Subject.is_active == True
                )
            )
            
            subject_result = await self.db.execute(subject_query)
            subject = subject_result.scalar_one_or_none()
            
            return subject is not None
            
        except Exception as e:
            logger.error(f"Failed to validate student enrollment: {str(e)}")
            return False
    
    async def get_student_enrollment_details(
        self,
        student_id: UUID,
        academic_year_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get detailed enrollment information for a student"""
        try:
            query = select(Enrollment).where(
                and_(
                    Enrollment.student_id == student_id,
                    Enrollment.academic_year_id == academic_year_id,
                    Enrollment.status == 'active'
                )
            ).options(
                joinedload(Enrollment.student),
                joinedload(Enrollment.class_obj)
            )
            
            result = await self.db.execute(query)
            enrollment = result.scalar_one_or_none()
            
            if not enrollment:
                return None
            
            return {
                'enrollment_id': str(enrollment.id),
                'student_id': str(enrollment.student_id),
                'class_id': str(enrollment.class_id),
                'grade_level': enrollment.grade_level,
                'enrollment_date': enrollment.enrollment_date.isoformat(),
                'status': enrollment.status,
                'student_name': f"{enrollment.student.first_name} {enrollment.student.last_name}",
                'class_name': enrollment.class_obj.name if enrollment.class_obj else '',
                'academic_year_id': str(enrollment.academic_year_id)
            }
            
        except Exception as e:
            logger.error(f"Failed to get student enrollment details: {str(e)}")
            return None


# Utility functions for common integration tasks
async def get_academic_sis_integration(db: AsyncSession) -> AcademicSISIntegration:
    """Factory function to create AcademicSISIntegration instance"""
    return AcademicSISIntegration(db)


async def sync_class_enrollment_with_academic(
    db: AsyncSession,
    class_id: UUID,
    academic_year_id: UUID,
    school_id: UUID
) -> Dict[str, Any]:
    """Sync class enrollment data with academic operations"""
    integration = AcademicSISIntegration(db)
    
    # Get class students for academic operations
    students = await integration.get_class_students_for_academic(
        class_id, school_id, academic_year_id
    )
    
    # Get class academic summary
    summary = await integration.get_class_academic_summary(
        class_id, school_id, academic_year_id
    )
    
    return {
        'students': students,
        'summary': summary,
        'sync_timestamp': datetime.utcnow().isoformat()
    }