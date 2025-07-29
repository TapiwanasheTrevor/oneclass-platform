# =====================================================
# Authentication Service Layer
# Business logic for user authentication and management
# File: backend/services/auth/services.py
# =====================================================

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4, UUID
import logging

from shared.models.platform_user import (
    PlatformUser,
    SchoolMembership,
    UserProfile,
    UserStatus,
)
from shared.models.platform import School
from shared.models.platform_user import PlatformRole, SchoolRole
from .schemas import OnboardingCompleteRequest, UserContextResponse
from .utils import hash_password

logger = logging.getLogger(__name__)


class AuthService:
    """Service class for authentication and user management operations"""

    async def create_user(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        platform_role: PlatformRole = PlatformRole.STUDENT,
        **kwargs,
    ) -> PlatformUser:
        """Create a new user account"""

        # Hash password
        password_hash = hash_password(password)

        # Create user profile
        profile = UserProfile(
            phone_number=kwargs.get("phone"),
            preferred_language=kwargs.get("preferred_language", "en"),
            timezone=kwargs.get("timezone", "Africa/Harare"),
            notification_preferences=kwargs.get(
                "notification_preferences",
                {
                    "email_notifications": True,
                    "sms_notifications": True,
                    "push_notifications": True,
                    "marketing_emails": False,
                },
            ),
        )

        # Create user
        user = PlatformUser(
            id=uuid4(),
            email=email.lower(),
            password_hash=password_hash,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            platform_role=platform_role,
            status=UserStatus.ACTIVE,
            profile=profile,
            feature_flags=kwargs.get("feature_flags", {}),
            user_preferences=kwargs.get("user_preferences", {}),
            created_at=datetime.utcnow(),
        )

        db.add(user)
        await db.flush()  # Get the user ID

        logger.info(f"Created new user: {email}")
        return user

    async def create_user_from_onboarding(
        self, db: AsyncSession, onboarding_data: OnboardingCompleteRequest
    ) -> PlatformUser:
        """Create user from onboarding data"""

        if not onboarding_data.password:
            raise ValueError("Password required for new user")

        # Create user profile
        profile = UserProfile(
            phone_number=onboarding_data.phone,
            date_of_birth=onboarding_data.date_of_birth,
            gender=onboarding_data.gender,
            address=onboarding_data.address,
            emergency_contact_name=onboarding_data.emergency_contact_name,
            emergency_contact_phone=onboarding_data.emergency_contact_phone,
            preferred_language=onboarding_data.preferred_language,
            timezone=onboarding_data.timezone,
            notification_preferences=onboarding_data.notification_preferences,
        )

        # Create user
        user = PlatformUser(
            id=uuid4(),
            email=onboarding_data.email,
            password_hash=hash_password(onboarding_data.password),
            first_name=onboarding_data.first_name,
            last_name=onboarding_data.last_name,
            platform_role=onboarding_data.primary_role,
            status=UserStatus.ACTIVE,
            profile=profile,
            feature_flags={},
            user_preferences={},
            created_at=datetime.utcnow(),
        )

        db.add(user)
        await db.flush()

        # Add school memberships
        for membership_data in onboarding_data.school_memberships:
            await self.add_school_membership(db, user, membership_data)

        # Set primary school
        if onboarding_data.school_memberships:
            user.primary_school_id = UUID(
                onboarding_data.school_memberships[0].school_id
            )

        logger.info(f"Created user from onboarding: {onboarding_data.email}")
        return user

    async def update_user_from_onboarding(
        self,
        db: AsyncSession,
        user: PlatformUser,
        onboarding_data: OnboardingCompleteRequest,
    ) -> PlatformUser:
        """Update existing user with onboarding data"""

        # Update user profile
        if not user.profile:
            user.profile = UserProfile()

        user.profile.phone_number = onboarding_data.phone or user.profile.phone_number
        user.profile.date_of_birth = (
            onboarding_data.date_of_birth or user.profile.date_of_birth
        )
        user.profile.gender = onboarding_data.gender or user.profile.gender
        user.profile.address = onboarding_data.address or user.profile.address
        user.profile.emergency_contact_name = (
            onboarding_data.emergency_contact_name
            or user.profile.emergency_contact_name
        )
        user.profile.emergency_contact_phone = (
            onboarding_data.emergency_contact_phone
            or user.profile.emergency_contact_phone
        )
        user.profile.preferred_language = onboarding_data.preferred_language
        user.profile.timezone = onboarding_data.timezone
        user.profile.notification_preferences.update(
            onboarding_data.notification_preferences
        )

        # Add new school memberships
        for membership_data in onboarding_data.school_memberships:
            # Check if membership already exists
            existing_query = select(SchoolMembership).where(
                and_(
                    SchoolMembership.user_id == user.id,
                    SchoolMembership.school_id == membership_data.school_id,
                )
            )
            existing_result = await db.execute(existing_query)
            existing_membership = existing_result.scalar_one_or_none()

            if not existing_membership:
                await self.add_school_membership(db, user, membership_data)

        logger.info(f"Updated user from onboarding: {user.email}")
        return user

    async def add_school_membership(
        self, db: AsyncSession, user: PlatformUser, membership_data
    ) -> SchoolMembership:
        """Add school membership to user"""

        # Verify school exists
        school_query = select(School).where(School.id == membership_data.school_id)
        school_result = await db.execute(school_query)
        school = school_result.scalar_one_or_none()

        if not school:
            raise ValueError(f"School not found: {membership_data.school_id}")

        # Get default permissions for role
        permissions = self.get_default_permissions_for_role(membership_data.role)

        # Create membership
        membership = SchoolMembership(
            id=uuid4(),
            user_id=user.id,
            school_id=UUID(membership_data.school_id),
            role=membership_data.role,
            permissions=permissions,
            status=UserStatus.ACTIVE,
            joined_date=datetime.utcnow(),
            department=membership_data.department,
            employee_id=membership_data.employee_id,
            student_id=membership_data.student_id,
            current_grade=membership_data.current_grade,
            children_ids=membership_data.children_ids or [],
        )

        db.add(membership)

        logger.info(
            f"Added school membership: {user.email} -> {school.name} as {membership_data.role}"
        )
        return membership

    def get_default_permissions_for_role(self, role: SchoolRole) -> List[str]:
        """Get default permissions for a school role"""

        role_permissions = {
            SchoolRole.PRINCIPAL: ["*"],
            SchoolRole.DEPUTY_PRINCIPAL: [
                "users.manage",
                "academics.manage",
                "reports.view",
                "finance.view",
                "settings.manage",
            ],
            SchoolRole.ACADEMIC_HEAD: [
                "academics.manage",
                "reports.view",
                "students.manage",
                "teachers.view",
                "curriculum.manage",
            ],
            SchoolRole.DEPARTMENT_HEAD: [
                "academics.view",
                "students.manage",
                "reports.view",
                "teachers.view",
                "curriculum.view",
            ],
            SchoolRole.TEACHER: [
                "students.view",
                "academics.view",
                "attendance.manage",
                "grades.manage",
                "communication.send",
            ],
            SchoolRole.FORM_TEACHER: [
                "students.manage",
                "academics.view",
                "attendance.manage",
                "grades.manage",
                "communication.send",
                "discipline.manage",
            ],
            SchoolRole.REGISTRAR: [
                "students.manage",
                "documents.manage",
                "reports.view",
                "enrollment.manage",
                "records.manage",
            ],
            SchoolRole.BURSAR: [
                "finance.manage",
                "payments.process",
                "reports.financial",
                "invoices.manage",
                "fees.manage",
            ],
            SchoolRole.LIBRARIAN: [
                "library.manage",
                "resources.manage",
                "students.view",
                "books.manage",
                "circulation.manage",
            ],
            SchoolRole.IT_SUPPORT: [
                "system.support",
                "users.support",
                "technical.manage",
                "backups.manage",
                "security.view",
            ],
            SchoolRole.SECURITY: [
                "security.manage",
                "access.control",
                "visitors.manage",
                "incidents.report",
                "surveillance.view",
            ],
            SchoolRole.PARENT: [
                "students.view",
                "payments.view",
                "communication.receive",
                "reports.view",
                "events.view",
            ],
            SchoolRole.STUDENT: [
                "academics.view",
                "assignments.submit",
                "resources.access",
                "grades.view",
                "events.view",
            ],
        }

        return role_permissions.get(role, ["basic.access"])

    async def get_user_with_context(
        self, db: AsyncSession, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get user with full context including school memberships"""

        # Get user with related data
        query = (
            select(PlatformUser)
            .options(
                selectinload(PlatformUser.school_memberships),
            )
            .where(PlatformUser.id == user_id)
        )

        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return None

        # Build user context
        user_data = {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "platform_role": user.platform_role.value if hasattr(user.platform_role, 'value') else str(user.platform_role),
            "status": user.status.value if hasattr(user.status, 'value') else str(user.status),
            "primary_school_id": (
                str(user.primary_school_id) if user.primary_school_id else None
            ),
            "profile": user.profile if user.profile else {
                "phone_number": None,
                "preferred_language": "en",
                "timezone": "Africa/Harare",
                "notification_preferences": {
                    "email_notifications": True,
                    "sms_notifications": True,
                    "push_notifications": True,
                    "marketing_emails": False,
                },
            },
            "feature_flags": user.feature_flags,
            "user_preferences": user.user_preferences,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "school_memberships": [],
        }

        # Add school membership details
        for membership in user.school_memberships:
            if membership.status == UserStatus.ACTIVE:
                # Get school details
                school_query = select(School).where(School.id == membership.school_id)
                school_result = await db.execute(school_query)
                school = school_result.scalar_one_or_none()

                if school:
                    user_data["school_memberships"].append(
                        {
                            "school_id": str(membership.school_id),
                            "school_name": school.name,
                            "school_subdomain": school.subdomain,
                            "role": membership.role.value,
                            "permissions": membership.permissions,
                            "joined_date": membership.joined_date.isoformat(),
                            "status": membership.status.value,
                            "student_id": membership.student_id,
                            "current_grade": membership.current_grade,
                            "admission_date": (
                                membership.admission_date.isoformat()
                                if membership.admission_date
                                else None
                            ),
                            "graduation_date": (
                                membership.graduation_date.isoformat()
                                if membership.graduation_date
                                else None
                            ),
                            "employee_id": membership.employee_id,
                            "department": membership.department,
                            "hire_date": (
                                membership.hire_date.isoformat()
                                if membership.hire_date
                                else None
                            ),
                            "contract_type": membership.contract_type,
                            "children_ids": membership.children_ids or [],
                        }
                    )

        return user_data

    async def verify_user_school_access(
        self, db: AsyncSession, user_id: str, school_id: str
    ) -> Optional[SchoolMembership]:
        """Verify user has access to a school"""

        query = select(SchoolMembership).where(
            and_(
                SchoolMembership.user_id == user_id,
                SchoolMembership.school_id == school_id,
                SchoolMembership.status == UserStatus.ACTIVE,
            )
        )

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_permissions(
        self, db: AsyncSession, user_id: str, school_id: Optional[str] = None
    ) -> List[str]:
        """Get user's permissions for a specific school or platform-wide"""

        user_query = select(PlatformUser).where(PlatformUser.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            return []

        # Super admin has all permissions
        if user.platform_role == PlatformRole.SUPER_ADMIN:
            return ["*"]

        permissions = []

        if school_id:
            # Get school-specific permissions
            membership = await self.verify_user_school_access(db, user_id, school_id)
            if membership:
                permissions.extend(membership.permissions)
        else:
            # Get all permissions across all schools
            memberships_query = select(SchoolMembership).where(
                and_(
                    SchoolMembership.user_id == user_id,
                    SchoolMembership.status == UserStatus.ACTIVE,
                )
            )
            memberships_result = await db.execute(memberships_query)
            memberships = memberships_result.scalars().all()

            for membership in memberships:
                permissions.extend(membership.permissions)

        return list(set(permissions))  # Remove duplicates
