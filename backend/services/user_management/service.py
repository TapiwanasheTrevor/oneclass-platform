"""
User Management Service
Core service for role-based user creation and management within schools
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status, Depends
import bcrypt
import uuid

from shared.database import get_db
from shared.models.platform import School
from shared.models.platform_user import PlatformUser as User
from shared.auth import get_current_active_user
from shared.utils.email import send_email
from shared.utils.notifications import send_notification
from shared.models.platform_user import UserInvitation
from .models import UserRole, UserProfile, BulkUserImport
from .schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserSearchFilter,
    UserListResponse,
    UserInvitationCreate,
    UserInvitationResponse,
    UserInvitationAccept,
    BulkUserImportCreate,
    BulkUserRecord,
    BulkUserImportResponse,
    UserRoleCreate,
    UserRoleUpdate,
    UserRoleResponse,
    UserProfileUpdate,
    UserProfileResponse,
)


class UserManagementService:
    """Service for managing users within schools"""

    def __init__(self, db: Session):
        self.db = db

    # User creation and management
    async def create_user(
        self, school_id: str, user_data: UserCreate, created_by: str
    ) -> UserResponse:
        """Create a new user within a school"""

        # Check if user already exists
        existing_user = (
            self.db.query(User)
            .filter(and_(User.email == user_data.email, User.school_id == school_id))
            .first()
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists in this school",
            )

        # Create user
        user = User(
            id=uuid.uuid4(),
            school_id=school_id,
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            role=user_data.role,
            user_metadata=user_data.role_metadata or {},
            is_active=True,
            is_verified=False,
        )

        # Set password if provided
        if user_data.password:
            user.password_hash = bcrypt.hashpw(
                user_data.password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

        self.db.add(user)
        self.db.flush()

        # Create user profile
        profile = UserProfile(
            user_id=user.id,
            school_id=school_id,
            department=user_data.department,
            position=user_data.position,
            employee_id=user_data.employee_id,
            student_id=user_data.student_id,
            grade_level=user_data.grade_level,
        )

        self.db.add(profile)

        # Send invitation if requested
        if user_data.send_invitation:
            await self._send_user_invitation(user, created_by)

        self.db.commit()

        return UserResponse.from_orm(user)

    async def update_user(
        self, user_id: str, school_id: str, user_data: UserUpdate
    ) -> UserResponse:
        """Update an existing user"""

        user = (
            self.db.query(User)
            .filter(and_(User.id == user_id, User.school_id == school_id))
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Update user fields
        for field, value in user_data.dict(exclude_unset=True).items():
            if hasattr(user, field):
                setattr(user, field, value)

        # Update profile if exists
        if user.profile:
            profile_fields = [
                "department",
                "position",
                "employee_id",
                "student_id",
                "grade_level",
            ]
            for field in profile_fields:
                if hasattr(user_data, field) and getattr(user_data, field) is not None:
                    setattr(user.profile, field, getattr(user_data, field))

        self.db.commit()

        return UserResponse.from_orm(user)

    async def get_user(self, user_id: str, school_id: str) -> UserResponse:
        """Get a specific user"""

        user = (
            self.db.query(User)
            .filter(and_(User.id == user_id, User.school_id == school_id))
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return UserResponse.from_orm(user)

    async def list_users(
        self, school_id: str, filters: UserSearchFilter
    ) -> UserListResponse:
        """List users with filtering and pagination"""

        query = self.db.query(User).filter(User.school_id == school_id)

        # Apply filters
        if filters.query:
            search_term = f"%{filters.query}%"
            query = query.filter(
                or_(
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.email.ilike(search_term),
                )
            )

        if filters.role:
            query = query.filter(User.role == filters.role)

        if filters.is_active is not None:
            query = query.filter(User.is_active == filters.is_active)

        if filters.is_verified is not None:
            query = query.filter(User.is_verified == filters.is_verified)

        if filters.created_after:
            query = query.filter(User.created_at >= filters.created_after)

        if filters.created_before:
            query = query.filter(User.created_at <= filters.created_before)

        # Join with profile for department filtering
        if filters.department:
            query = query.join(UserProfile).filter(
                UserProfile.department == filters.department
            )

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (filters.page - 1) * filters.page_size
        users = query.offset(offset).limit(filters.page_size).all()

        return UserListResponse(
            users=[UserResponse.from_orm(user) for user in users],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=(total + filters.page_size - 1) // filters.page_size,
        )

    async def delete_user(self, user_id: str, school_id: str) -> bool:
        """Soft delete a user"""

        user = (
            self.db.query(User)
            .filter(and_(User.id == user_id, User.school_id == school_id))
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Soft delete by deactivating
        user.is_active = False
        self.db.commit()

        return True

    # User invitation management
    async def create_invitation(
        self, school_id: str, invitation_data: UserInvitationCreate, invited_by: str
    ) -> UserInvitationResponse:
        """Create a user invitation"""

        # Check if user already exists
        existing_user = (
            self.db.query(User)
            .filter(
                and_(User.email == invitation_data.email, User.school_id == school_id)
            )
            .first()
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        # Check for existing pending invitation
        existing_invitation = (
            self.db.query(UserInvitation)
            .filter(
                and_(
                    UserInvitation.email == invitation_data.email,
                    UserInvitation.school_id == school_id,
                    UserInvitation.status == "pending",
                )
            )
            .first()
        )

        if existing_invitation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pending invitation already exists for this email",
            )

        # Create invitation
        invitation = UserInvitation(
            id=uuid.uuid4(),
            school_id=school_id,
            email=invitation_data.email,
            role=invitation_data.role,
            invited_by=invited_by,
            invitation_token=secrets.token_urlsafe(32),
            first_name=invitation_data.first_name,
            last_name=invitation_data.last_name,
            phone=invitation_data.phone,
            department=invitation_data.department,
            position=invitation_data.position,
            role_metadata=invitation_data.role_metadata or {},
            permissions=invitation_data.permissions or [],
            expires_at=datetime.utcnow()
            + timedelta(days=invitation_data.expires_in_days),
        )

        self.db.add(invitation)
        self.db.commit()

        # Send invitation email
        await self._send_invitation_email(invitation)

        return UserInvitationResponse.from_orm(invitation)

    async def accept_invitation(
        self, token: str, acceptance_data: UserInvitationAccept
    ) -> UserResponse:
        """Accept a user invitation"""

        invitation = (
            self.db.query(UserInvitation)
            .filter(UserInvitation.invitation_token == token)
            .first()
        )

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invitation token"
            )

        if invitation.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation has already been processed",
            )

        if invitation.is_expired:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation has expired"
            )

        # Create user
        user = User(
            id=uuid.uuid4(),
            school_id=invitation.school_id,
            email=invitation.email,
            first_name=acceptance_data.first_name or invitation.first_name,
            last_name=acceptance_data.last_name or invitation.last_name,
            phone=acceptance_data.phone,
            role=invitation.role,
            user_metadata=invitation.role_metadata,
            is_active=True,
            is_verified=True,
        )

        # Set password
        user.password_hash = bcrypt.hashpw(
            acceptance_data.password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        self.db.add(user)
        self.db.flush()

        # Create user profile
        profile = UserProfile(
            user_id=user.id,
            school_id=invitation.school_id,
            department=invitation.department,
            position=invitation.position,
            **acceptance_data.profile_data,
        )

        self.db.add(profile)

        # Update invitation status
        invitation.status = "accepted"
        invitation.accepted_at = datetime.utcnow()

        self.db.commit()

        return UserResponse.from_orm(user)

    async def list_invitations(
        self, school_id: str, status: Optional[str] = None
    ) -> List[UserInvitationResponse]:
        """List user invitations"""

        query = self.db.query(UserInvitation).filter(
            UserInvitation.school_id == school_id
        )

        if status:
            query = query.filter(UserInvitation.status == status)

        invitations = query.order_by(UserInvitation.created_at.desc()).all()

        return [UserInvitationResponse.from_orm(inv) for inv in invitations]

    async def cancel_invitation(self, invitation_id: str, school_id: str) -> bool:
        """Cancel a user invitation"""

        invitation = (
            self.db.query(UserInvitation)
            .filter(
                and_(
                    UserInvitation.id == invitation_id,
                    UserInvitation.school_id == school_id,
                )
            )
            .first()
        )

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
            )

        invitation.status = "cancelled"
        self.db.commit()

        return True

    # Role management
    async def create_role(
        self, school_id: str, role_data: UserRoleCreate, created_by: str
    ) -> UserRoleResponse:
        """Create a custom user role"""

        # Check if role already exists
        existing_role = (
            self.db.query(UserRole)
            .filter(
                and_(
                    UserRole.school_id == school_id,
                    UserRole.role_name == role_data.role_name,
                )
            )
            .first()
        )

        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role with this name already exists",
            )

        role = UserRole(
            id=uuid.uuid4(),
            school_id=school_id,
            role_name=role_data.role_name,
            display_name=role_data.display_name,
            description=role_data.description,
            permissions=role_data.permissions,
            inherited_roles=role_data.inherited_roles,
            parent_role_id=role_data.parent_role_id,
            created_by=created_by,
        )

        self.db.add(role)
        self.db.commit()

        return UserRoleResponse.from_orm(role)

    async def list_roles(self, school_id: str) -> List[UserRoleResponse]:
        """List all roles for a school"""

        roles = (
            self.db.query(UserRole)
            .filter(UserRole.school_id == school_id)
            .order_by(UserRole.level, UserRole.role_name)
            .all()
        )

        return [UserRoleResponse.from_orm(role) for role in roles]

    # Profile management
    async def update_profile(
        self, user_id: str, school_id: str, profile_data: UserProfileUpdate
    ) -> UserProfileResponse:
        """Update user profile"""

        profile = (
            self.db.query(UserProfile)
            .filter(
                and_(UserProfile.user_id == user_id, UserProfile.school_id == school_id)
            )
            .first()
        )

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
            )

        # Update profile fields
        for field, value in profile_data.dict(exclude_unset=True).items():
            if hasattr(profile, field):
                setattr(profile, field, value)

        # Calculate completion percentage
        profile.completion_percentage = self._calculate_profile_completion(profile)
        profile.profile_completed = profile.completion_percentage >= 80

        self.db.commit()

        return UserProfileResponse.from_orm(profile)

    # Bulk operations
    async def bulk_import_users(
        self,
        school_id: str,
        user_records: List[BulkUserRecord],
        import_data: BulkUserImportCreate,
        imported_by: str,
    ) -> BulkUserImportResponse:
        """Bulk import users from records"""

        # Create import record
        bulk_import = BulkUserImport(
            id=uuid.uuid4(),
            school_id=school_id,
            imported_by=imported_by,
            import_type=import_data.import_type,
            total_records=len(user_records),
            status="processing",
            started_at=datetime.utcnow(),
        )

        self.db.add(bulk_import)
        self.db.flush()

        successful_imports = 0
        failed_imports = 0
        error_log = []

        for i, record in enumerate(user_records):
            try:
                # Create user
                user_create = UserCreate(
                    email=record.email,
                    first_name=record.first_name,
                    last_name=record.last_name,
                    role=record.role or import_data.default_role,
                    phone=record.phone,
                    department=record.department,
                    position=record.position,
                    employee_id=record.employee_id,
                    student_id=record.student_id,
                    grade_level=record.grade_level,
                    send_invitation=import_data.send_invitations,
                )

                await self.create_user(school_id, user_create, imported_by)
                successful_imports += 1

            except Exception as e:
                failed_imports += 1
                error_log.append({"row": i + 1, "email": record.email, "error": str(e)})

        # Update import record
        bulk_import.successful_imports = successful_imports
        bulk_import.failed_imports = failed_imports
        bulk_import.error_log = error_log
        bulk_import.status = "completed"
        bulk_import.completed_at = datetime.utcnow()

        self.db.commit()

        return BulkUserImportResponse.from_orm(bulk_import)

    # Helper methods
    async def _send_invitation_email(self, invitation: UserInvitation):
        """Send invitation email to user"""

        school = self.db.query(School).filter(School.id == invitation.school_id).first()

        inviter = self.db.query(User).filter(User.id == invitation.invited_by).first()

        # Email content
        subject = f"Invitation to join {school.name}"
        template = "user_invitation"
        context = {
            "invitation": invitation,
            "school": school,
            "inviter": inviter,
            "accept_url": f"https://{school.subdomain}.oneclass.ac.zw/accept-invitation/{invitation.invitation_token}",
        }

        await send_email(
            to_email=invitation.email,
            subject=subject,
            template=template,
            context=context,
        )

    async def _send_user_invitation(self, user: User, created_by: str):
        """Send welcome email to newly created user"""

        school = self.db.query(School).filter(School.id == user.school_id).first()

        subject = f"Welcome to {school.name}"
        template = "user_welcome"
        context = {
            "user": user,
            "school": school,
            "login_url": f"https://{school.subdomain}.oneclass.ac.zw/login",
        }

        await send_email(
            to_email=user.email, subject=subject, template=template, context=context
        )

    def _calculate_profile_completion(self, profile: UserProfile) -> int:
        """Calculate profile completion percentage"""

        total_fields = 0
        completed_fields = 0

        # Basic fields
        fields = [
            "address",
            "emergency_contact_name",
            "emergency_contact_phone",
            "emergency_contact_relationship",
        ]

        # Role-specific fields
        if profile.user.role in ["teacher", "staff"]:
            fields.extend(["department", "position", "hire_date"])
        elif profile.user.role == "student":
            fields.extend(["grade_level", "enrollment_date"])

        total_fields = len(fields)

        for field in fields:
            if getattr(profile, field) is not None:
                completed_fields += 1

        return int((completed_fields / total_fields) * 100) if total_fields > 0 else 0


# Service factory
def get_user_management_service(db: Session = Depends(get_db)) -> UserManagementService:
    """Get user management service instance"""
    return UserManagementService(db)
