"""
OneClass Platform Database Models
Contains all database models organized by functional area
"""

# Import all models for easy access
from .platform import School, SchoolConfiguration, SchoolDomain, SchoolFeatureUsage
from .platform_user import (
    PlatformUser as User,
    SchoolMembership,
    UserInvitation,
    UserSession,
)
from .academic import (
    Subject,
    AcademicYear,
    Term,
    Class,
    Assessment,
    Grade,
    Timetable,
    Lesson,
    Curriculum,
)
from .finance import (
    FeeStructure,
    StudentFeeAssignment,
    Invoice,
    Payment,
    FinancialReport,
    Budget,
    Expense,
)
from .sis import (
    Student,
    Enrollment,
    AttendanceRecord,
    DisciplinaryRecord,
    MedicalRecord,
    StudentNote,
)

__all__ = [
    # Platform models
    "School",
    "User",
    "SchoolConfiguration",
    "SchoolDomain",
    "SchoolFeatureUsage",
    "SchoolMembership",
    "UserInvitation",
    "UserSession",
    # Academic models
    "Subject",
    "AcademicYear",
    "Term",
    "Class",
    "Assessment",
    "Grade",
    "Timetable",
    "Lesson",
    "Curriculum",
    # Finance models
    "FeeStructure",
    "StudentFeeAssignment",
    "Invoice",
    "Payment",
    "FinancialReport",
    "Budget",
    "Expense",
    # SIS models
    "Student",
    "Enrollment",
    "AttendanceRecord",
    "DisciplinaryRecord",
    "MedicalRecord",
    "StudentNote",
]
