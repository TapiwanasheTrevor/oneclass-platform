"""
SIS Service Models
Re-exports models from shared.models.sis for service-specific use
"""

# Import all SIS models from shared location
from shared.models.sis import (
    Student,
    Enrollment,
    AttendanceRecord,
    DisciplinaryRecord,
    MedicalRecord,
    StudentNote,
)

# Import related models that SIS service might need
from shared.models.platform_user import PlatformUser as User
from shared.models.academic import Class, Subject, AcademicYear, Term

# Re-export for backward compatibility
__all__ = [
    "Student",
    "Enrollment",
    "AttendanceRecord",
    "DisciplinaryRecord",
    "MedicalRecord",
    "StudentNote",
    "User",
    "Class",
    "Subject",
    "AcademicYear",
    "Term",
]

# Aliases for backward compatibility
StudentGuardian = User  # Guardian is a type of user
StudentAcademicHistory = Enrollment  # Academic history is tracked through enrollments
DisciplinaryIncident = DisciplinaryRecord  # Alternative name
HealthRecord = MedicalRecord  # Alternative name
StudentDocument = StudentNote  # Documents can be stored as notes
