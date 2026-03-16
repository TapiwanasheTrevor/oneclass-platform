"""
Backward-compatibility re-exports.
All models consolidated into platform_user.py.
"""

from .platform_user import (
    PlatformUser as UnifiedUser,
    SchoolMembership,
    UserSession,
    UserInvitation as SchoolInvitation,
    GlobalRole,
    SchoolRole,
    MembershipStatus,
    UserStatus,
    ContactInformation,
    PersonalProfile,
    UserPreferences,
    ClerkIntegration,
)
