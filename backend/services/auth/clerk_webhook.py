"""
Clerk Webhook Handler
Syncs Clerk user events to PlatformUser in our database.

Clerk handles: sign-up, sign-in, social auth, MFA, email verification
We handle: school memberships, roles, permissions, school context

Webhook events:
- user.created → Create PlatformUser record
- user.updated → Sync profile changes
- user.deleted → Deactivate PlatformUser
- session.created → Track login activity
"""

import json
import logging
import os
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from shared.database import get_async_session
from shared.models.platform_user import (
    PlatformUser, GlobalRole, UserStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

CLERK_WEBHOOK_SECRET = os.getenv("CLERK_WEBHOOK_SECRET", "")


async def verify_clerk_webhook(request: Request) -> dict:
    """
    Verify Clerk webhook signature using svix.
    Returns the parsed event payload if valid.
    """
    body = await request.body()

    if not CLERK_WEBHOOK_SECRET:
        # Dev mode: skip verification, just parse
        logger.warning("CLERK_WEBHOOK_SECRET not set — skipping signature verification")
        return json.loads(body)

    try:
        from svix.webhooks import Webhook

        svix_id = request.headers.get("svix-id", "")
        svix_timestamp = request.headers.get("svix-timestamp", "")
        svix_signature = request.headers.get("svix-signature", "")

        if not all([svix_id, svix_timestamp, svix_signature]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing svix headers"
            )

        wh = Webhook(CLERK_WEBHOOK_SECRET)
        payload = wh.verify(
            body.decode("utf-8"),
            {
                "svix-id": svix_id,
                "svix-timestamp": svix_timestamp,
                "svix-signature": svix_signature,
            }
        )
        return payload

    except Exception as e:
        logger.error(f"Webhook verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )


@router.post("/clerk")
async def handle_clerk_webhook(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Handle Clerk webhook events.
    Syncs user data from Clerk into our PlatformUser table.
    """
    event = await verify_clerk_webhook(request)

    event_type = event.get("type", "")
    data = event.get("data", {})

    logger.info(f"Clerk webhook received: {event_type}")

    try:
        if event_type == "user.created":
            await _handle_user_created(db, data)
        elif event_type == "user.updated":
            await _handle_user_updated(db, data)
        elif event_type == "user.deleted":
            await _handle_user_deleted(db, data)
        elif event_type == "session.created":
            await _handle_session_created(db, data)
        else:
            logger.debug(f"Unhandled webhook event: {event_type}")

        await db.commit()
        return {"status": "ok", "event": event_type}

    except Exception as e:
        await db.rollback()
        logger.error(f"Webhook handler error for {event_type}: {e}")
        # Return 200 to prevent Clerk from retrying — log the error
        return {"status": "error", "event": event_type, "message": str(e)}


async def _handle_user_created(db: AsyncSession, data: dict):
    """
    Clerk user.created → Create PlatformUser.
    The user has just signed up via Clerk (email, Google, etc.)
    They won't have any school memberships yet — those come later
    during onboarding or invitation acceptance.
    """
    clerk_user_id = data.get("id")
    if not clerk_user_id:
        return

    # Check if user already exists (idempotency)
    existing = await db.execute(
        select(PlatformUser).where(PlatformUser.clerk_user_id == clerk_user_id)
    )
    if existing.scalar_one_or_none():
        logger.info(f"User already exists for clerk_id={clerk_user_id}")
        return

    # Extract user info from Clerk data
    email = _get_primary_email(data)
    if not email:
        logger.warning(f"No email found for clerk user {clerk_user_id}")
        return

    # Check if a user with this email already exists (e.g., invited before signup)
    email_check = await db.execute(
        select(PlatformUser).where(PlatformUser.email == email.lower())
    )
    existing_by_email = email_check.scalar_one_or_none()

    if existing_by_email:
        # Link existing user to Clerk
        existing_by_email.clerk_user_id = clerk_user_id
        existing_by_email.is_email_verified = True
        existing_by_email.last_login_at = datetime.now(timezone.utc)
        if data.get("first_name"):
            existing_by_email.first_name = data["first_name"]
        if data.get("last_name"):
            existing_by_email.last_name = data["last_name"]
        if data.get("image_url"):
            profile = existing_by_email.personal_profile or {}
            profile["profile_image_url"] = data["image_url"]
            existing_by_email.personal_profile = profile
        logger.info(f"Linked existing user {email} to Clerk {clerk_user_id}")
        return

    # Create new user
    user = PlatformUser(
        id=uuid4(),
        email=email.lower(),
        first_name=data.get("first_name", ""),
        last_name=data.get("last_name", ""),
        clerk_user_id=clerk_user_id,
        global_role=GlobalRole.SYSTEM_USER.value,
        status=UserStatus.ACTIVE.value,
        is_email_verified=True,
        personal_profile={
            "profile_image_url": data.get("image_url"),
        },
        contact_information={
            "primary_phone": _get_primary_phone(data),
        },
        last_login_at=datetime.now(timezone.utc),
        login_count=1,
    )

    db.add(user)
    logger.info(f"Created PlatformUser for {email} (clerk_id={clerk_user_id})")


async def _handle_user_updated(db: AsyncSession, data: dict):
    """Sync profile updates from Clerk"""
    clerk_user_id = data.get("id")
    if not clerk_user_id:
        return

    result = await db.execute(
        select(PlatformUser).where(PlatformUser.clerk_user_id == clerk_user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        # User doesn't exist in our system yet — create them
        await _handle_user_created(db, data)
        return

    # Sync basic info
    if data.get("first_name"):
        user.first_name = data["first_name"]
    if data.get("last_name"):
        user.last_name = data["last_name"]

    # Sync email if changed
    new_email = _get_primary_email(data)
    if new_email and new_email.lower() != user.email:
        user.email = new_email.lower()

    # Sync profile image
    if data.get("image_url"):
        profile = user.personal_profile or {}
        profile["profile_image_url"] = data["image_url"]
        user.personal_profile = profile

    logger.info(f"Updated PlatformUser from Clerk: {user.email}")


async def _handle_user_deleted(db: AsyncSession, data: dict):
    """Deactivate user when deleted from Clerk"""
    clerk_user_id = data.get("id")
    if not clerk_user_id:
        return

    result = await db.execute(
        select(PlatformUser).where(PlatformUser.clerk_user_id == clerk_user_id)
    )
    user = result.scalar_one_or_none()
    if user:
        user.status = UserStatus.ARCHIVED.value
        logger.info(f"Archived PlatformUser {user.email} (Clerk user deleted)")


async def _handle_session_created(db: AsyncSession, data: dict):
    """Track login activity"""
    user_id = data.get("user_id")
    if not user_id:
        return

    result = await db.execute(
        select(PlatformUser).where(PlatformUser.clerk_user_id == user_id)
    )
    user = result.scalar_one_or_none()
    if user:
        user.last_login_at = datetime.now(timezone.utc)
        user.login_count = (user.login_count or 0) + 1


# =====================================================
# HELPERS
# =====================================================

def _get_primary_email(data: dict) -> str | None:
    """Extract primary email from Clerk user data"""
    email_addresses = data.get("email_addresses", [])
    for addr in email_addresses:
        if addr.get("id") == data.get("primary_email_address_id"):
            return addr.get("email_address")
    if email_addresses:
        return email_addresses[0].get("email_address")
    return None


def _get_primary_phone(data: dict) -> str | None:
    """Extract primary phone from Clerk user data"""
    phone_numbers = data.get("phone_numbers", [])
    for phone in phone_numbers:
        if phone.get("id") == data.get("primary_phone_number_id"):
            return phone.get("phone_number")
    if phone_numbers:
        return phone_numbers[0].get("phone_number")
    return None
