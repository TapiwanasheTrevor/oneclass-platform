"""
OneClass Platform Database Models
All models organized by functional area, single Base from shared.database
"""

# Platform models
from .platform import School, SchoolConfiguration, SchoolDomain, SchoolFeatureUsage

# User models (consolidated)
from .platform_user import (
    PlatformUser,
    PlatformUser as User,          # alias
    PlatformUser as UnifiedUser,   # alias
    SchoolMembership,
    UserInvitation,
    UserInvitation as SchoolInvitation,  # alias
    UserSession,
    # Enums
    GlobalRole,
    GlobalRole as PlatformRole,    # alias
    SchoolRole,
    MembershipStatus,
    UserStatus,
    # Pydantic models
    ContactInformation,
    PersonalProfile,
    UserPreferences,
    ClerkIntegration,
    UserProfile,
)

# Academic models
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

# Finance models (re-exported from services/finance/models.py where authoritative)
from .finance import (
    FeeStructure,
    StudentFeeAssignment,
    Invoice,
    Payment,
    FinancialReport,
    Budget,
    Expense,
)

# SIS models
from .sis import (
    Student,
    Enrollment,
    AttendanceRecord,
    DisciplinaryRecord,
    MedicalRecord,
    StudentNote,
)

__all__ = [
    # Platform
    "School", "SchoolConfiguration", "SchoolDomain", "SchoolFeatureUsage",
    # Users
    "PlatformUser", "User", "UnifiedUser",
    "SchoolMembership", "UserInvitation", "SchoolInvitation", "UserSession",
    "GlobalRole", "PlatformRole", "SchoolRole", "MembershipStatus", "UserStatus",
    "ContactInformation", "PersonalProfile", "UserPreferences",
    "ClerkIntegration", "UserProfile",
    # Academic
    "Subject", "AcademicYear", "Term", "Class", "Assessment",
    "Grade", "Timetable", "Lesson", "Curriculum",
    # Finance
    "FeeStructure", "StudentFeeAssignment", "Invoice", "Payment",
    "FinancialReport", "Budget", "Expense",
    # SIS
    "Student", "Enrollment", "AttendanceRecord",
    "DisciplinaryRecord", "MedicalRecord", "StudentNote",
]
