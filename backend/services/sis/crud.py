# =====================================================
# SIS Module - CRUD Operations
# File: backend/services/sis/crud.py
# =====================================================

from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_, or_, func, text
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import date, datetime
import json
import logging

from shared.models.sis import (
    Student,
    AttendanceRecord,
    DisciplinaryRecord as DisciplinaryIncident,
    MedicalRecord as HealthRecord,
)
from shared.models.platform_user import PlatformUser as User
from .models import StudentGuardian, StudentAcademicHistory, StudentDocument
from .schemas import (
    StudentCreate,
    StudentUpdate,
    StudentSearchFilters,
    GuardianRelationshipCreate,
    DisciplinaryIncidentCreate,
    AttendanceRecordCreate,
    HealthRecordCreate,
    StudentDocumentCreate,
)

# User is already imported from shared.models.platform_user above
from shared.database import get_db_session
from shared.encryption import encrypt_sensitive_data, decrypt_sensitive_data

logger = logging.getLogger(__name__)

# =====================================================
# CUSTOM EXCEPTIONS
# =====================================================


class SISException(Exception):
    """Base exception for SIS operations"""

    pass


class StudentNotFoundError(SISException):
    """Student not found"""

    pass


class DuplicateStudentError(SISException):
    """Student with similar details already exists"""

    pass


class ClassCapacityExceededError(SISException):
    """Class is at full capacity"""

    pass


class InsufficientPermissionsError(SISException):
    """User doesn't have required permissions"""

    pass


class InvalidDataError(SISException):
    """Invalid data provided"""

    pass


# =====================================================
# STUDENT CRUD OPERATIONS
# =====================================================


class StudentCRUD:

    @staticmethod
    async def create_student_full_workflow(
        db: Session,
        student_data: StudentCreate,
        school_id: UUID,
        created_by_user_id: UUID,
    ) -> Student:
        """
        Complete student creation workflow with all validations and related data.
        This is the main entry point for student registration.
        """
        try:
            # 1. Validate class capacity if class is specified
            if student_data.current_class_id:
                await StudentCRUD._validate_class_capacity(
                    db, student_data.current_class_id
                )

            # 2. Check for potential duplicate students
            await StudentCRUD._check_duplicate_student(db, student_data, school_id)

            # 3. Generate student number
            student_number = await StudentCRUD._generate_student_number(db, school_id)

            # 4. Encrypt sensitive data
            encrypted_medical = await StudentCRUD._encrypt_medical_data(
                student_data.medical_conditions, student_data.allergies
            )
            encrypted_emergency_contacts = (
                await StudentCRUD._encrypt_emergency_contacts(
                    student_data.emergency_contacts
                )
            )

            # 5. Create student record
            student = Student(
                school_id=school_id,
                student_number=student_number,
                first_name=student_data.first_name,
                middle_name=student_data.middle_name,
                last_name=student_data.last_name,
                preferred_name=student_data.preferred_name,
                date_of_birth=student_data.date_of_birth,
                gender=student_data.gender.value,
                nationality=student_data.nationality,
                home_language=(
                    student_data.home_language.value
                    if student_data.home_language
                    else None
                ),
                religion=student_data.religion,
                mobile_number=student_data.mobile_number,
                email=student_data.email,
                residential_address=student_data.residential_address.dict(),
                postal_address=(
                    student_data.postal_address.dict()
                    if student_data.postal_address
                    else None
                ),
                current_grade_level=student_data.current_grade_level,
                current_class_id=student_data.current_class_id,
                enrollment_date=student_data.enrollment_date,
                blood_type=(
                    student_data.blood_type.value if student_data.blood_type else None
                ),
                medical_aid_provider=student_data.medical_aid_provider,
                medical_aid_number=student_data.medical_aid_number,
                medical_conditions_encrypted=encrypted_medical,
                emergency_contacts_encrypted=encrypted_emergency_contacts,
                special_needs=student_data.special_needs,
                dietary_requirements=student_data.dietary_requirements,
                transport_needs=student_data.transport_needs,
                identifying_marks=student_data.identifying_marks,
                previous_school_name=student_data.previous_school_name,
                transfer_reason=student_data.transfer_reason,
                created_by=created_by_user_id,
            )

            db.add(student)
            await db.flush()  # Get the student ID

            # 6. Create initial academic history record
            await StudentCRUD._create_initial_academic_history(
                db, student.id, school_id
            )

            # 7. Log the creation activity
            await StudentCRUD._log_student_activity(
                db,
                student.id,
                created_by_user_id,
                "student_created",
                {
                    "student_number": student_number,
                    "grade": student_data.current_grade_level,
                },
            )

            await db.commit()
            await db.refresh(student)

            logger.info(
                f"Student created successfully: {student_number} for school {school_id}"
            )
            return student

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating student: {str(e)}")
            raise

    @staticmethod
    async def get_student_by_id_with_permission_check(
        db: Session, user: User, student_id: UUID
    ) -> Optional[Student]:
        """
        Get student by ID with proper permission checking based on user role.
        """
        query = select(Student).where(Student.id == student_id)

        # Apply role-based filtering
        if user.role == "student":
            # Students can only see their own record
            query = query.where(Student.user_id == user.id)
        elif user.role == "parent":
            # Parents can only see their children
            query = query.where(
                Student.id.in_(
                    select(StudentGuardian.student_id).where(
                        StudentGuardian.guardian_user_id == user.id
                    )
                )
            )
        elif user.role in ["teacher", "school_admin", "registrar"]:
            # Staff can see students in their school
            query = query.where(Student.school_id == user.school_id)
        else:
            # Ministry officials, super admins have broader access
            pass

        result = await db.execute(query)
        student = result.scalar_one_or_none()

        if student:
            # Decrypt sensitive data if user has permission
            if await StudentCRUD._user_can_view_sensitive_data(user, student):
                await StudentCRUD._decrypt_student_sensitive_data(student)

        return student

    @staticmethod
    async def get_students(
        db: Session,
        user: User,
        grade_id: Optional[UUID] = None,
        class_id: Optional[UUID] = None,
        status: Optional[str] = None,
        search_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Student]:
        """
        Get students with filtering and role-based access control.
        """
        query = select(Student)

        # Apply role-based filtering
        if user.role in ["teacher", "school_admin", "registrar"]:
            query = query.where(Student.school_id == user.school_id)
        elif user.role == "parent":
            # Parents can only see their children
            query = query.where(
                Student.id.in_(
                    select(StudentGuardian.student_id).where(
                        StudentGuardian.guardian_user_id == user.id
                    )
                )
            )
        elif user.role == "student":
            # Students see empty list (should use /me endpoint)
            return []

        # Apply filters
        if class_id:
            query = query.where(Student.current_class_id == class_id)
        if status:
            query = query.where(Student.status == status)
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.where(
                or_(
                    Student.first_name.ilike(search_pattern),
                    Student.last_name.ilike(search_pattern),
                    Student.student_number.ilike(search_pattern),
                    func.concat(Student.first_name, " ", Student.last_name).ilike(
                        search_pattern
                    ),
                )
            )

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Order by last name, first name
        query = query.order_by(Student.last_name, Student.first_name)

        result = await db.execute(query)
        students = result.scalars().all()

        return list(students)

    @staticmethod
    async def update_student(
        db: Session,
        student_id: UUID,
        student_update: StudentUpdate,
        updated_by_user_id: UUID,
    ) -> Student:
        """
        Update student information with validation and audit trail.
        """
        try:
            # Get existing student
            result = await db.execute(select(Student).where(Student.id == student_id))
            student = result.scalar_one_or_none()

            if not student:
                raise StudentNotFoundError(f"Student with ID {student_id} not found")

            # Track changes for audit
            changes = {}

            # Update basic fields
            for field, value in student_update.dict(exclude_unset=True).items():
                if field in ["emergency_contacts", "medical_conditions", "allergies"]:
                    continue  # Handle these separately

                old_value = getattr(student, field, None)
                if old_value != value:
                    changes[field] = {"from": old_value, "to": value}
                    setattr(student, field, value)

            # Handle emergency contacts update
            if student_update.emergency_contacts:
                encrypted_contacts = await StudentCRUD._encrypt_emergency_contacts(
                    student_update.emergency_contacts
                )
                student.emergency_contacts_encrypted = encrypted_contacts
                changes["emergency_contacts"] = "updated"

            # Handle medical data update
            if student_update.medical_conditions or student_update.allergies:
                encrypted_medical = await StudentCRUD._encrypt_medical_data(
                    student_update.medical_conditions or [],
                    student_update.allergies or [],
                )
                student.medical_conditions_encrypted = encrypted_medical
                changes["medical_data"] = "updated"

            # Update timestamp
            student.updated_at = datetime.utcnow()

            # Log the update
            if changes:
                await StudentCRUD._log_student_activity(
                    db, student_id, updated_by_user_id, "student_updated", changes
                )

            await db.commit()
            await db.refresh(student)

            logger.info(f"Student {student.student_number} updated successfully")
            return student

        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating student {student_id}: {str(e)}")
            raise

    @staticmethod
    async def delete_student(
        db: Session,
        student_id: UUID,
        deleted_by_user_id: UUID,
        soft_delete: bool = True,
    ) -> bool:
        """
        Delete student (soft delete by default for audit purposes).
        """
        try:
            result = await db.execute(select(Student).where(Student.id == student_id))
            student = result.scalar_one_or_none()

            if not student:
                raise StudentNotFoundError(f"Student with ID {student_id} not found")

            if soft_delete:
                # Soft delete - mark as deleted but keep record
                student.status = "transferred"  # or create a "deleted" status
                student.deleted_at = datetime.utcnow()
                student.updated_at = datetime.utcnow()

                await StudentCRUD._log_student_activity(
                    db,
                    student_id,
                    deleted_by_user_id,
                    "student_soft_deleted",
                    {"reason": "administrative_deletion"},
                )
            else:
                # Hard delete - remove from database
                await db.delete(student)

                await StudentCRUD._log_student_activity(
                    db,
                    student_id,
                    deleted_by_user_id,
                    "student_hard_deleted",
                    {"student_number": student.student_number},
                )

            await db.commit()
            logger.info(f"Student {student.student_number} deleted successfully")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting student {student_id}: {str(e)}")
            raise

    # =====================================================
    # HELPER METHODS
    # =====================================================

    @staticmethod
    async def _validate_class_capacity(db: Session, class_id: UUID):
        """Validate that class has capacity for new student."""
        # Query class capacity and current enrollment
        query = text(
            """
            SELECT c.max_capacity, COUNT(s.id) as current_enrollment
            FROM academic.classes c
            LEFT JOIN sis.students s ON s.current_class_id = c.id AND s.status = 'active'
            WHERE c.id = :class_id
            GROUP BY c.max_capacity
        """
        )

        result = await db.execute(query, {"class_id": class_id})
        row = result.fetchone()

        if not row:
            raise InvalidDataError(f"Class {class_id} not found")

        max_capacity, current_enrollment = row
        if max_capacity and current_enrollment >= max_capacity:
            raise ClassCapacityExceededError(
                f"Class is at full capacity ({current_enrollment}/{max_capacity})"
            )

    @staticmethod
    async def _check_duplicate_student(
        db: Session, student_data: StudentCreate, school_id: UUID
    ):
        """Check for potential duplicate students."""
        # Check for students with same name and date of birth
        query = select(Student).where(
            and_(
                Student.school_id == school_id,
                Student.first_name.ilike(student_data.first_name),
                Student.last_name.ilike(student_data.last_name),
                Student.date_of_birth == student_data.date_of_birth,
                Student.status != "transferred",
            )
        )

        result = await db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            raise DuplicateStudentError(
                f"Student with similar details already exists: {existing.student_number}"
            )

    @staticmethod
    async def _generate_student_number(db: Session, school_id: UUID) -> str:
        """Generate unique student number for the school."""
        current_year = datetime.now().year

        # Get the next sequence number for this year and school
        query = text(
            """
            SELECT COALESCE(MAX(CAST(SUBSTRING(student_number FROM '[0-9]+) AS INTEGER)), 0) + 1
            FROM sis.students 
            WHERE school_id = :school_id 
            AND student_number LIKE :year_prefix
        """
        )

        result = await db.execute(
            query, {"school_id": school_id, "year_prefix": f"{current_year}-%"}
        )
        next_sequence = result.scalar()

        # Format: YYYY-NNNN (e.g., 2024-0001)
        return f"{current_year}-{next_sequence:04d}"

    @staticmethod
    async def _encrypt_medical_data(
        medical_conditions: List[Any], allergies: List[Any]
    ) -> str:
        """Encrypt medical conditions and allergies."""
        medical_data = {
            "conditions": [
                condition.dict() if hasattr(condition, "dict") else condition
                for condition in medical_conditions
            ],
            "allergies": [
                allergy.dict() if hasattr(allergy, "dict") else allergy
                for allergy in allergies
            ],
        }
        return encrypt_sensitive_data(medical_data)

    @staticmethod
    async def _encrypt_emergency_contacts(emergency_contacts: List[Any]) -> str:
        """Encrypt emergency contact information."""
        contacts_data = [
            contact.dict() if hasattr(contact, "dict") else contact
            for contact in emergency_contacts
        ]
        return encrypt_sensitive_data(contacts_data)

    @staticmethod
    async def _decrypt_student_sensitive_data(student: Student):
        """Decrypt sensitive data for authorized users."""
        if student.medical_conditions_encrypted:
            try:
                medical_data = decrypt_sensitive_data(
                    student.medical_conditions_encrypted
                )
                student.decrypted_medical_conditions = medical_data.get(
                    "conditions", []
                )
                student.decrypted_allergies = medical_data.get("allergies", [])
            except Exception as e:
                logger.warning(
                    f"Failed to decrypt medical data for student {student.id}: {str(e)}"
                )

        if student.emergency_contacts_encrypted:
            try:
                student.decrypted_emergency_contacts = decrypt_sensitive_data(
                    student.emergency_contacts_encrypted
                )
            except Exception as e:
                logger.warning(
                    f"Failed to decrypt emergency contacts for student {student.id}: {str(e)}"
                )

    @staticmethod
    async def _user_can_view_sensitive_data(user: User, student: Student) -> bool:
        """Check if user can view sensitive medical/emergency contact data."""
        if user.role in ["school_admin", "nurse"]:
            return True
        if user.role == "parent":
            # Check if user is a guardian of this student
            # This would require a database query in real implementation
            return True  # Simplified for now
        return False

    @staticmethod
    async def _create_initial_academic_history(
        db: Session, student_id: UUID, school_id: UUID
    ):
        """Create initial academic history record for new student."""
        # Get current academic year
        query = text(
            """
            SELECT id FROM academic.academic_years 
            WHERE school_id = :school_id AND is_current = true
        """
        )
        result = await db.execute(query, {"school_id": school_id})
        academic_year_id = result.scalar()

        if academic_year_id:
            history = StudentAcademicHistory(
                student_id=student_id,
                academic_year_id=academic_year_id,
                grade_level=1,  # Will be updated based on student's current grade
                promotion_status="pending",
            )
            db.add(history)

    @staticmethod
    async def _log_student_activity(
        db: Session,
        student_id: UUID,
        user_id: UUID,
        action: str,
        details: Dict[str, Any],
    ):
        """Log student-related activities for audit trail."""
        # This would insert into an audit log table
        # Implementation depends on your audit system
        logger.info(
            f"Student activity: {action} for {student_id} by {user_id}, details: {details}"
        )


# =====================================================
# GUARDIAN RELATIONSHIP CRUD
# =====================================================


class GuardianCRUD:

    @staticmethod
    async def create_guardian_relationship(
        db: Session,
        student_id: UUID,
        guardian_data: GuardianRelationshipCreate,
        created_by_user_id: UUID,
    ) -> StudentGuardian:
        """Create guardian-student relationship."""
        try:
            # Validate that student exists
            result = await db.execute(select(Student).where(Student.id == student_id))
            student = result.scalar_one_or_none()
            if not student:
                raise StudentNotFoundError(f"Student {student_id} not found")

            # Check if relationship already exists
            existing_query = select(StudentGuardian).where(
                and_(
                    StudentGuardian.student_id == student_id,
                    StudentGuardian.guardian_user_id == guardian_data.guardian_user_id,
                )
            )
            result = await db.execute(existing_query)
            if result.scalar_one_or_none():
                raise InvalidDataError("Guardian relationship already exists")

            # Handle primary contact logic
            if guardian_data.is_primary_contact:
                # Ensure only one primary contact
                await GuardianCRUD._ensure_single_primary_contact(db, student_id)

            relationship = StudentGuardian(
                student_id=student_id,
                guardian_user_id=guardian_data.guardian_user_id,
                relationship=guardian_data.relationship,
                is_primary_contact=guardian_data.is_primary_contact,
                is_emergency_contact=guardian_data.is_emergency_contact,
                contact_priority=guardian_data.contact_priority,
                has_pickup_permission=guardian_data.has_pickup_permission,
                has_academic_access=guardian_data.has_academic_access,
                has_financial_responsibility=guardian_data.has_financial_responsibility,
                financial_responsibility_percentage=guardian_data.financial_responsibility_percentage,
                preferred_contact_method=guardian_data.preferred_contact_method.value,
                alternative_phone=guardian_data.alternative_phone,
                work_phone=guardian_data.work_phone,
                employer=guardian_data.employer,
                job_title=guardian_data.job_title,
            )

            db.add(relationship)
            await db.commit()
            await db.refresh(relationship)

            logger.info(
                f"Guardian relationship created: {guardian_data.guardian_user_id} -> {student_id}"
            )
            return relationship

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating guardian relationship: {str(e)}")
            raise

    @staticmethod
    async def get_student_guardians(
        db: Session, student_id: UUID
    ) -> List[StudentGuardian]:
        """Get all guardians for a student."""
        query = (
            select(StudentGuardian)
            .where(StudentGuardian.student_id == student_id)
            .order_by(StudentGuardian.contact_priority)
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def _ensure_single_primary_contact(db: Session, student_id: UUID):
        """Ensure only one primary contact exists for a student."""
        update_query = (
            update(StudentGuardian)
            .where(StudentGuardian.student_id == student_id)
            .values(is_primary_contact=False)
        )

        await db.execute(update_query)


# =====================================================
# DISCIPLINARY CRUD
# =====================================================


class DisciplinaryCRUD:

    @staticmethod
    async def create_incident(
        db: Session,
        incident_data: DisciplinaryIncidentCreate,
        reported_by_user_id: UUID,
    ) -> DisciplinaryIncident:
        """Create a disciplinary incident."""
        try:
            incident = DisciplinaryIncident(
                student_id=incident_data.student_id,
                incident_date=incident_data.incident_date,
                incident_time=incident_data.incident_time,
                incident_type=incident_data.incident_type,
                severity=incident_data.severity.value,
                description=incident_data.description,
                location=incident_data.location,
                witnesses=incident_data.witnesses,
                action_taken=incident_data.action_taken,
                points_deducted=incident_data.points_deducted,
                suspension_days=incident_data.suspension_days,
                detention_hours=incident_data.detention_hours,
                counseling_required=incident_data.counseling_required,
                parent_meeting_required=incident_data.parent_meeting_required,
                behavioral_contract_required=incident_data.behavioral_contract_required,
                reported_by=reported_by_user_id,
            )

            db.add(incident)

            # Update student's disciplinary points
            if incident_data.points_deducted > 0:
                await DisciplinaryCRUD._update_student_disciplinary_points(
                    db, incident_data.student_id, incident_data.points_deducted
                )

            await db.commit()
            await db.refresh(incident)

            logger.info(
                f"Disciplinary incident created for student {incident_data.student_id}"
            )
            return incident

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating disciplinary incident: {str(e)}")
            raise

    @staticmethod
    async def _update_student_disciplinary_points(
        db: Session, student_id: UUID, points_to_add: int
    ):
        """Update student's disciplinary points total."""
        update_query = (
            update(Student)
            .where(Student.id == student_id)
            .values(disciplinary_points=Student.disciplinary_points + points_to_add)
        )

        await db.execute(update_query)


# =====================================================
# ATTENDANCE CRUD
# =====================================================


class AttendanceCRUD:

    @staticmethod
    async def mark_attendance(
        db: Session, attendance_data: AttendanceRecordCreate, marked_by_user_id: UUID
    ) -> AttendanceRecord:
        """Mark student attendance."""
        try:
            # Check if attendance already marked for this date/period
            existing_query = select(AttendanceRecord).where(
                and_(
                    AttendanceRecord.student_id == attendance_data.student_id,
                    AttendanceRecord.attendance_date == attendance_data.attendance_date,
                    AttendanceRecord.period == attendance_data.period,
                )
            )
            result = await db.execute(existing_query)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing record
                for field, value in attendance_data.dict(exclude_unset=True).items():
                    setattr(existing, field, value)
                existing.marked_by = marked_by_user_id
                existing.updated_at = datetime.utcnow()

                await db.commit()
                await db.refresh(existing)
                return existing
            else:
                # Create new record
                attendance = AttendanceRecord(
                    student_id=attendance_data.student_id,
                    attendance_date=attendance_data.attendance_date,
                    period=attendance_data.period,
                    status=attendance_data.status.value,
                    arrival_time=attendance_data.arrival_time,
                    departure_time=attendance_data.departure_time,
                    absence_reason=attendance_data.absence_reason,
                    excuse_provided=attendance_data.excuse_provided,
                    notes=attendance_data.notes,
                    marked_by=marked_by_user_id,
                )

                db.add(attendance)
                await db.commit()
                await db.refresh(attendance)

                logger.info(
                    f"Attendance marked for student {attendance_data.student_id}"
                )
                return attendance

        except Exception as e:
            await db.rollback()
            logger.error(f"Error marking attendance: {str(e)}")
            raise

    @staticmethod
    async def get_student_attendance(
        db: Session,
        student_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[AttendanceRecord]:
        """Get attendance records for a student."""
        query = select(AttendanceRecord).where(
            AttendanceRecord.student_id == student_id
        )

        if start_date:
            query = query.where(AttendanceRecord.attendance_date >= start_date)
        if end_date:
            query = query.where(AttendanceRecord.attendance_date <= end_date)

        query = query.order_by(AttendanceRecord.attendance_date.desc())

        result = await db.execute(query)
        return list(result.scalars().all())


# =====================================================
# HEALTH RECORD CRUD
# =====================================================


class HealthRecordCRUD:

    @staticmethod
    async def create_health_record(
        db: Session, health_data: HealthRecordCreate, created_by_user_id: UUID
    ) -> HealthRecord:
        """Create a health record for a student."""
        try:
            health_record = HealthRecord(
                student_id=health_data.student_id,
                record_type=health_data.record_type,
                record_date=health_data.record_date,
                recorded_by=health_data.recorded_by,
                symptoms=health_data.symptoms,
                diagnosis=health_data.diagnosis,
                treatment_given=health_data.treatment_given,
                temperature_celsius=health_data.temperature_celsius,
                blood_pressure=health_data.blood_pressure,
                pulse_rate=health_data.pulse_rate,
                weight_kg=health_data.weight_kg,
                height_cm=health_data.height_cm,
                recommendations=health_data.recommendations,
                follow_up_required=health_data.follow_up_required,
                follow_up_date=health_data.follow_up_date,
                parent_contacted=health_data.parent_contacted,
                sent_home=health_data.sent_home,
            )

            db.add(health_record)
            await db.commit()
            await db.refresh(health_record)

            logger.info(f"Health record created for student {health_data.student_id}")
            return health_record

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating health record: {str(e)}")
            raise


# =====================================================
# DOCUMENT CRUD
# =====================================================


class DocumentCRUD:

    @staticmethod
    async def upload_student_document(
        db: Session, document_data: StudentDocumentCreate, uploaded_by_user_id: UUID
    ) -> StudentDocument:
        """Upload a document for a student."""
        try:
            document = StudentDocument(
                student_id=document_data.student_id,
                document_type=document_data.document_type.value,
                document_name=document_data.document_name,
                file_url=document_data.file_url,
                file_size_bytes=document_data.file_size_bytes,
                file_format=document_data.file_format,
                is_confidential=document_data.is_confidential,
                access_level=document_data.access_level,
                description=document_data.description,
                expiry_date=document_data.expiry_date,
                uploaded_by=uploaded_by_user_id,
            )

            db.add(document)
            await db.commit()
            await db.refresh(document)

            logger.info(f"Document uploaded for student {document_data.student_id}")
            return document

        except Exception as e:
            await db.rollback()
            logger.error(f"Error uploading document: {str(e)}")
            raise
