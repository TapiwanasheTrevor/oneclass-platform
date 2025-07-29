# =====================================================
# Invitation Service Routes
# Complete invitation system for user onboarding
# File: backend/services/invitations/routes.py
# =====================================================

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import logging

from shared.database import get_async_session
from shared.models.platform_user import PlatformUser, UserInvitation, SchoolMembership
from shared.models.platform import School
from shared.auth import get_current_active_user
from .schemas import (
    CreateInvitationRequest,
    InvitationResponse,
    InvitationDetailResponse,
    BulkInvitationRequest,
    InvitationAcceptRequest,
    InvitationListResponse,
)
from .services import InvitationService
from services.auth.utils import create_invitation_token, verify_invitation_token

router = APIRouter(prefix="/api/v1/invitations", tags=["invitations"])
logger = logging.getLogger(__name__)

invitation_service = InvitationService()


@router.post("/create", response_model=InvitationResponse)
async def create_invitation(
    invitation_data: CreateInvitationRequest,
    background_tasks: BackgroundTasks,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Create a new user invitation
    Can invite new users or add existing users to schools
    """
    try:
        # Verify current user has permission to invite to this school
        if not await invitation_service.can_invite_to_school(
            db, current_user.id, invitation_data.school_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to invite users to this school",
            )

        # Check if user already exists
        existing_user_query = select(PlatformUserDB).where(
            PlatformUserDB.email == invitation_data.email.lower()
        )
        existing_result = await db.execute(existing_user_query)
        existing_user = existing_result.scalar_one_or_none()

        invitation_type = "existing_user" if existing_user else "new_user"

        # Check if user already has membership to this school
        if existing_user:
            existing_membership_query = select(SchoolMembershipDB).where(
                and_(
                    SchoolMembershipDB.user_id == existing_user.id,
                    SchoolMembershipDB.school_id == invitation_data.school_id,
                )
            )
            existing_membership_result = await db.execute(existing_membership_query)
            existing_membership = existing_membership_result.scalar_one_or_none()

            if existing_membership and existing_membership.status == "active":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User already has active membership to this school",
                )

        # Get school details
        school_query = select(School).where(School.id == invitation_data.school_id)
        school_result = await db.execute(school_query)
        school = school_result.scalar_one_or_none()

        if not school:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="School not found"
            )

        # Create invitation token
        token_data = {
            "invitation_id": str(uuid4()),
            "email": invitation_data.email.lower(),
            "school_id": str(invitation_data.school_id),
            "invited_by": str(current_user.id),
            "invitation_type": invitation_type,
        }

        invitation_token = create_invitation_token(token_data, expires_days=7)

        # Create invitation record
        invitation = UserInvitationDB(
            id=UUID(token_data["invitation_id"]),
            email=invitation_data.email.lower(),
            school_id=invitation_data.school_id,
            invited_role=invitation_data.platform_role.value,
            school_role=invitation_data.school_role.value,
            inviter_id=current_user.id,
            existing_user_id=existing_user.id if existing_user else None,
            invitation_token=invitation_token,
            status="pending",
            invitation_type=invitation_type,
            expires_at=datetime.utcnow() + timedelta(days=7),
            additional_context={
                "department": invitation_data.department,
                "employee_id": invitation_data.employee_id,
                "student_id": invitation_data.student_id,
                "subjects": invitation_data.teaching_subjects,
                "classes": invitation_data.assigned_classes,
                "personal_message": invitation_data.personal_message,
            },
            created_at=datetime.utcnow(),
        )

        db.add(invitation)
        await db.commit()

        # Send invitation email in background
        background_tasks.add_task(
            invitation_service.send_invitation_email, invitation, school, current_user
        )

        logger.info(f"Created invitation for {invitation_data.email} to {school.name}")

        return InvitationResponse(
            id=str(invitation.id),
            email=invitation.email,
            school_id=str(invitation.school_id),
            school_name=school.name,
            status=invitation.status,
            invitation_token=invitation_token,
            expires_at=invitation.expires_at.isoformat(),
            invitation_type=invitation.invitation_type,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating invitation: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create invitation",
        )


@router.post("/bulk", response_model=List[InvitationResponse])
async def create_bulk_invitations(
    bulk_data: BulkInvitationRequest,
    background_tasks: BackgroundTasks,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Create multiple invitations at once
    Useful for importing class lists or staff groups
    """
    try:
        # Verify permission to invite to this school
        if not await invitation_service.can_invite_to_school(
            db, current_user.id, bulk_data.school_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to invite users to this school",
            )

        invitations = []
        errors = []

        for invitation_data in bulk_data.invitations:
            try:
                # Create individual invitation
                individual_request = CreateInvitationRequest(
                    email=invitation_data.email,
                    school_id=bulk_data.school_id,
                    platform_role=invitation_data.platform_role,
                    school_role=invitation_data.school_role,
                    department=invitation_data.department,
                    employee_id=invitation_data.employee_id,
                    student_id=invitation_data.student_id,
                    teaching_subjects=invitation_data.teaching_subjects,
                    assigned_classes=invitation_data.assigned_classes,
                )

                invitation = await create_invitation(
                    individual_request, background_tasks, current_user, db
                )
                invitations.append(invitation)

            except Exception as e:
                errors.append({"email": invitation_data.email, "error": str(e)})
                continue

        if errors:
            logger.warning(f"Bulk invitation had {len(errors)} errors: {errors}")

        return invitations

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bulk invitations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bulk invitations",
        )


@router.get("/{token}", response_model=InvitationDetailResponse)
async def get_invitation_details(
    token: str, db: AsyncSession = Depends(get_async_session)
):
    """
    Get invitation details by token
    Used by invitation handler to display invitation info
    """
    try:
        # Verify and decode token
        try:
            token_data = verify_invitation_token(token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired invitation link",
            )

        # Get invitation from database
        invitation_query = select(UserInvitation).where(
            UserInvitation.invitation_token == token
        )
        invitation_result = await db.execute(invitation_query)
        invitation = invitation_result.scalar_one_or_none()

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
            )

        # Check if invitation is expired
        if invitation.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation has expired"
            )

        # Check if invitation is already used
        if invitation.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invitation already {invitation.status}",
            )

        # Get school details
        school_query = select(School).where(School.id == invitation.school_id)
        school_result = await db.execute(school_query)
        school = school_result.scalar_one_or_none()

        # Get inviter details
        inviter_query = select(PlatformUser).where(
            PlatformUser.id == invitation.inviter_id
        )
        inviter_result = await db.execute(inviter_query)
        inviter = inviter_result.scalar_one_or_none()

        # Check if user already exists
        existing_user_id = None
        if invitation.invitation_type == "existing_user":
            existing_user_query = select(PlatformUser).where(
                PlatformUser.email == invitation.email
            )
            existing_result = await db.execute(existing_user_query)
            existing_user = existing_result.scalar_one_or_none()
            if existing_user:
                existing_user_id = str(existing_user.id)

        return InvitationDetailResponse(
            id=str(invitation.id),
            email=invitation.email,
            school_id=str(invitation.school_id),
            school_name=school.name if school else "Unknown School",
            school_subdomain=school.subdomain if school else "",
            invited_role=invitation.invited_role,
            school_role=invitation.school_role,
            inviter_name=inviter.full_name if inviter else "Unknown",
            inviter_role=str(inviter.platform_role) if inviter else "unknown",
            created_at=invitation.created_at.isoformat(),
            expires_at=invitation.expires_at.isoformat(),
            status=invitation.status,
            invitation_type=invitation.invitation_type,
            existing_user_id=existing_user_id,
            additional_context=invitation.additional_context or {},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting invitation details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get invitation details",
        )


@router.post("/{token}/accept")
async def accept_invitation(
    token: str,
    accept_data: InvitationAcceptRequest,
    current_user: Optional[PlatformUser] = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Accept an invitation
    Can accept as existing user or complete onboarding as new user
    """
    try:
        # Get invitation details first
        invitation_query = select(UserInvitation).where(
            UserInvitation.invitation_token == token
        )
        invitation_result = await db.execute(invitation_query)
        invitation = invitation_result.scalar_one_or_none()

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
            )

        # Check invitation status
        if invitation.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invitation already {invitation.status}",
            )

        if invitation.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation has expired"
            )

        # Handle based on invitation type
        if invitation.invitation_type == "existing_user":
            # Add school membership to existing user
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required for existing user",
                )

            # Verify this is the invited user
            if current_user.email.lower() != invitation.email.lower():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only accept invitations sent to your email",
                )

            # Add school membership
            await invitation_service.add_school_membership_from_invitation(
                db, current_user, invitation
            )

            # Update invitation status
            invitation.status = "accepted"
            invitation.accepted_at = datetime.utcnow()
            invitation.accepted_by = current_user.id

            await db.commit()

            return {
                "message": "Invitation accepted successfully",
                "action": "school_membership_added",
                "school_id": str(invitation.school_id),
            }

        else:
            # New user - create account through onboarding
            if not accept_data.onboarding_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Onboarding data required for new user",
                )

            # Create user from onboarding data and invitation
            user = await invitation_service.create_user_from_invitation(
                db, invitation, accept_data.onboarding_data
            )

            # Update invitation status
            invitation.status = "accepted"
            invitation.accepted_at = datetime.utcnow()
            invitation.accepted_by = user.id

            await db.commit()

            return {
                "message": "Account created and invitation accepted",
                "action": "user_created",
                "user_id": str(user.id),
                "school_id": str(invitation.school_id),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting invitation: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to accept invitation",
        )


@router.post("/{token}/decline")
async def decline_invitation(
    token: str,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Decline an invitation
    """
    try:
        invitation_query = select(UserInvitation).where(
            UserInvitation.invitation_token == token
        )
        invitation_result = await db.execute(invitation_query)
        invitation = invitation_result.scalar_one_or_none()

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
            )

        if invitation.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invitation already {invitation.status}",
            )

        # Update invitation status
        invitation.status = "declined"
        invitation.declined_at = datetime.utcnow()
        invitation.decline_reason = reason

        await db.commit()

        logger.info(f"Invitation declined for {invitation.email}")

        return {"message": "Invitation declined"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error declining invitation: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decline invitation",
        )


@router.get("/school/{school_id}", response_model=InvitationListResponse)
async def get_school_invitations(
    school_id: UUID,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get invitations for a school
    Only accessible to users with invitation management permissions
    """
    try:
        # Verify permission
        if not await invitation_service.can_view_school_invitations(
            db, current_user.id, school_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view invitations for this school",
            )

        # Build query
        query = select(UserInvitation).where(UserInvitation.school_id == school_id)

        if status:
            query = query.where(UserInvitation.status == status)

        # Add ordering and pagination
        query = (
            query.order_by(UserInvitation.created_at.desc()).offset(offset).limit(limit)
        )

        result = await db.execute(query)
        invitations = result.scalars().all()

        # Get total count
        count_query = select(UserInvitation).where(
            UserInvitation.school_id == school_id
        )
        if status:
            count_query = count_query.where(UserInvitation.status == status)

        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        # Format response
        invitation_list = []
        for invitation in invitations:
            invitation_list.append(
                {
                    "id": str(invitation.id),
                    "email": invitation.email,
                    "invited_role": invitation.invited_role,
                    "school_role": invitation.school_role,
                    "status": invitation.status,
                    "created_at": invitation.created_at.isoformat(),
                    "expires_at": invitation.expires_at.isoformat(),
                    "invitation_type": invitation.invitation_type,
                }
            )

        return InvitationListResponse(
            invitations=invitation_list, total=total, limit=limit, offset=offset
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting school invitations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get school invitations",
        )
