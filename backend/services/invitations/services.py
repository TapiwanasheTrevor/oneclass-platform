# =====================================================
# Invitation Service Layer
# Business logic for invitation management
# File: backend/services/invitations/services.py
# =====================================================

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import logging

from shared.models.platform_user import (
    PlatformUser,
    UserInvitation,
    SchoolMembership,
    UserProfile,
)
from shared.models.platform_user import PlatformRole, SchoolRole, UserStatus
from shared.models.platform import School
from services.auth.schemas import OnboardingCompleteRequest
from services.auth.utils import hash_password
from .email_service import EmailService

logger = logging.getLogger(__name__)


class InvitationService:
    """Service class for invitation management operations"""

    def __init__(self):
        self.email_service = EmailService()

    async def can_invite_to_school(
        self, db: AsyncSession, user_id: UUID, school_id: UUID
    ) -> bool:
        """Check if user can invite others to a school"""

        # Get user
        user_query = select(PlatformUser).where(PlatformUser.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            return False

        # Super admin can invite to any school
        if user.platform_role == PlatformRole.SUPER_ADMIN.value:
            return True

        # Check school membership and permissions
        membership_query = select(SchoolMembership).where(
            and_(
                SchoolMembership.user_id == user_id,
                SchoolMembership.school_id == school_id,
                SchoolMembership.status == UserStatus.ACTIVE.value,
            )
        )
        membership_result = await db.execute(membership_query)
        membership = membership_result.scalar_one_or_none()

        if not membership:
            return False

        # Check if user has invitation permissions
        return (
            membership.role
            in [SchoolRole.PRINCIPAL.value, SchoolRole.DEPUTY_PRINCIPAL.value]
            or "users.invite" in (membership.permissions or [])
            or "*" in (membership.permissions or [])
        )

    async def can_view_school_invitations(
        self, db: AsyncSession, user_id: UUID, school_id: UUID
    ) -> bool:
        """Check if user can view invitations for a school"""

        # Same permissions as inviting for now
        return await self.can_invite_to_school(db, user_id, school_id)

    async def add_school_membership_from_invitation(
        self, db: AsyncSession, user: PlatformUser, invitation: UserInvitation
    ) -> SchoolMembership:
        """Add school membership to existing user from invitation"""

        # Check if membership already exists
        existing_query = select(SchoolMembership).where(
            and_(
                SchoolMembership.user_id == user.id,
                SchoolMembership.school_id == invitation.school_id,
            )
        )
        existing_result = await db.execute(existing_query)
        existing_membership = existing_result.scalar_one_or_none()

        if existing_membership:
            # Reactivate if inactive
            if existing_membership.status != UserStatus.ACTIVE.value:
                existing_membership.status = UserStatus.ACTIVE.value
                existing_membership.role = invitation.school_role.value
                existing_membership.permissions = self.get_default_permissions_for_role(
                    invitation.school_role
                )

                # Update additional context
                if invitation.additional_context:
                    existing_membership.department = invitation.additional_context.get(
                        "department"
                    )
                    existing_membership.employee_id = invitation.additional_context.get(
                        "employee_id"
                    )
                    existing_membership.student_id = invitation.additional_context.get(
                        "student_id"
                    )

                logger.info(f"Reactivated school membership for {user.email}")
                return existing_membership
            else:
                raise ValueError("User already has active membership to this school")

        # Create new membership
        membership = SchoolMembership(
            id=uuid4(),
            user_id=user.id,
            school_id=invitation.school_id,
            school_name="",  # Will be filled by caller
            school_subdomain="",  # Will be filled by caller
            role=invitation.school_role.value,
            permissions=self.get_default_permissions_for_role(invitation.school_role),
            status=UserStatus.ACTIVE.value,
            joined_date=datetime.utcnow(),
        )

        # Add additional context from invitation
        if invitation.additional_context:
            membership.department = invitation.additional_context.get("department")
            membership.employee_id = invitation.additional_context.get("employee_id")
            membership.student_id = invitation.additional_context.get("student_id")

        # Set as primary school if user has no primary school
        if not user.primary_school_id:
            user.primary_school_id = invitation.school_id

        db.add(membership)

        logger.info(
            f"Added school membership for {user.email} to {invitation.school_id}"
        )
        return membership

    async def create_user_from_invitation(
        self,
        db: AsyncSession,
        invitation: UserInvitation,
        onboarding_data: OnboardingCompleteRequest,
    ) -> PlatformUser:
        """Create new user from invitation and onboarding data"""

        # Verify email matches
        if invitation.email.lower() != onboarding_data.email.lower():
            raise ValueError("Email mismatch between invitation and onboarding data")

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

        # Create user profile JSON
        profile_data = {
            "phone_number": onboarding_data.phone,
            "date_of_birth": (
                onboarding_data.date_of_birth.isoformat()
                if onboarding_data.date_of_birth
                else None
            ),
            "gender": onboarding_data.gender,
            "address": onboarding_data.address,
            "emergency_contact_name": onboarding_data.emergency_contact_name,
            "emergency_contact_phone": onboarding_data.emergency_contact_phone,
            "preferred_language": onboarding_data.preferred_language or "en",
            "timezone": onboarding_data.timezone or "Africa/Harare",
            "notification_preferences": onboarding_data.notification_preferences
            or {
                "email_notifications": True,
                "sms_notifications": True,
                "push_notifications": True,
                "marketing_emails": False,
            },
        }

        # Create user DB model
        user = PlatformUser(
            id=uuid4(),
            email=invitation.email,
            first_name=onboarding_data.first_name,
            last_name=onboarding_data.last_name,
            platform_role=invitation.invited_role.value,
            status=UserStatus.ACTIVE.value,
            primary_school_id=invitation.school_id,
            profile=profile_data,
            feature_flags={},
            user_preferences={},
            created_at=datetime.utcnow(),
        )

        db.add(user)
        await db.flush()  # Get user ID

        # Create school membership
        membership = SchoolMembership(
            id=uuid4(),
            user_id=user.id,
            school_id=invitation.school_id,
            school_name="",  # Will be filled by caller
            school_subdomain="",  # Will be filled by caller
            role=invitation.school_role.value,
            permissions=self.get_default_permissions_for_role(invitation.school_role),
            status=UserStatus.ACTIVE.value,
            joined_date=datetime.utcnow(),
        )

        # Add additional context from invitation
        if invitation.additional_context:
            membership.department = invitation.additional_context.get("department")
            membership.employee_id = invitation.additional_context.get("employee_id")
            membership.student_id = invitation.additional_context.get("student_id")

        # Add any additional school memberships from onboarding
        for membership_data in onboarding_data.school_memberships or []:
            if str(membership_data.school_id) != str(invitation.school_id):
                additional_membership = SchoolMembership(
                    id=uuid4(),
                    user_id=user.id,
                    school_id=UUID(membership_data.school_id),
                    school_name="",  # Will be filled by caller
                    school_subdomain="",  # Will be filled by caller
                    role=(
                        membership_data.role.value
                        if hasattr(membership_data.role, "value")
                        else membership_data.role
                    ),
                    permissions=self.get_default_permissions_for_role(
                        membership_data.role
                    ),
                    status=UserStatus.ACTIVE.value,
                    joined_date=datetime.utcnow(),
                    department=membership_data.department,
                    employee_id=membership_data.employee_id,
                    student_id=membership_data.student_id,
                    current_grade=membership_data.current_grade,
                    children_ids=membership_data.children_ids or [],
                )
                db.add(additional_membership)

        db.add(membership)

        logger.info(f"Created user from invitation: {invitation.email}")
        return user

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

    async def send_invitation_email(
        self, invitation: UserInvitation, school: School, inviter: PlatformUser
    ):
        """Send invitation email (background task)"""

        try:
            # Build invitation URL
            invitation_url = f"https://{school.subdomain}.oneclass.ac.zw/invitation/{invitation.invitation_token}"

            # Get role description
            role_description = self.get_role_description(invitation.school_role)

            # Prepare email data
            email_data = {
                "recipient_email": invitation.email,
                "recipient_name": invitation.email.split("@")[0].title(),
                "school_name": school.name,
                "school_subdomain": school.subdomain,
                "inviter_name": inviter.full_name,
                "inviter_role": inviter.platform_role.value.replace("_", " ").title(),
                "invited_role": invitation.school_role.value.replace("_", " ").title(),
                "role_description": role_description,
                "invitation_url": invitation_url,
                "expires_at": invitation.expires_at.strftime("%B %d, %Y"),
                "personal_message": (
                    invitation.additional_context.get("personal_message")
                    if invitation.additional_context
                    else None
                ),
                "invitation_type": invitation.invitation_type,
            }

            # Send email
            await self.email_service.send_invitation_email(email_data)

            logger.info(f"Sent invitation email to {invitation.email}")

        except Exception as e:
            logger.error(
                f"Failed to send invitation email to {invitation.email}: {str(e)}"
            )

    def get_role_description(self, role: SchoolRole) -> str:
        """Get user-friendly description of a school role"""

        descriptions = {
            SchoolRole.PRINCIPAL: "Lead the school and oversee all operations",
            SchoolRole.DEPUTY_PRINCIPAL: "Assist with school leadership and management",
            SchoolRole.ACADEMIC_HEAD: "Manage academic programs and curriculum",
            SchoolRole.DEPARTMENT_HEAD: "Lead your subject department",
            SchoolRole.TEACHER: "Teach classes and manage student progress",
            SchoolRole.FORM_TEACHER: "Teach and provide pastoral care for a specific class",
            SchoolRole.REGISTRAR: "Manage student records and enrollment",
            SchoolRole.BURSAR: "Handle financial operations and fee management",
            SchoolRole.LIBRARIAN: "Manage library resources and services",
            SchoolRole.IT_SUPPORT: "Provide technical support and system maintenance",
            SchoolRole.SECURITY: "Ensure school safety and security",
            SchoolRole.PARENT: "Track your child's academic progress and school activities",
            SchoolRole.STUDENT: "Access your assignments, grades, and school resources",
        }

        return descriptions.get(role, "Access school systems and resources")

    async def get_invitation_statistics(
        self, db: AsyncSession, school_id: Optional[UUID] = None, days: int = 30
    ) -> Dict[str, Any]:
        """Get invitation statistics for analytics"""

        # Build base query
        query = select(UserInvitation)

        if school_id:
            query = query.where(UserInvitation.school_id == school_id)

        # Filter by date range
        start_date = datetime.utcnow() - timedelta(days=days)
        query = query.where(UserInvitation.created_at >= start_date)

        result = await db.execute(query)
        invitations = result.scalars().all()

        # Calculate statistics
        total = len(invitations)
        pending = len([i for i in invitations if i.status == "pending"])
        accepted = len([i for i in invitations if i.status == "accepted"])
        declined = len([i for i in invitations if i.status == "declined"])
        expired = len(
            [
                i
                for i in invitations
                if i.expires_at < datetime.utcnow() and i.status == "pending"
            ]
        )

        acceptance_rate = (accepted / total * 100) if total > 0 else 0

        return {
            "total_sent": total,
            "pending": pending,
            "accepted": accepted,
            "declined": declined,
            "expired": expired,
            "acceptance_rate": round(acceptance_rate, 2),
        }
