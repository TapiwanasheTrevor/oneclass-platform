# =====================================================
# Authentication Service Routes
# Complete authentication system with login, logout, session management
# File: backend/services/auth/routes.py
# =====================================================

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
import logging
from uuid import uuid4

from shared.database import get_async_session
from shared.models.platform_user import (
    PlatformUser,
    UserSession,
    SchoolMembership,
    MembershipStatus,
    UserStatus,
)
from shared.auth import db_manager
from .schemas import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    SwitchSchoolRequest,
    UserRegistrationRequest,
    PasswordResetRequest,
    OnboardingCompleteRequest,
    UserContextResponse,
)
from .services import AuthService
from .utils import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()
logger = logging.getLogger(__name__)

# Initialize auth service
auth_service = AuthService()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def get_current_tenant_info(request: Request) -> Optional[Dict[str, Any]]:
    """
    Extract tenant information from request for login context
    Returns a dictionary with school_id and other tenant information if available
    """
    try:
        # Try to get school context from headers (injected by frontend middleware)
        school_id = request.headers.get("X-School-ID")
        school_name = request.headers.get("X-School-Name")
        subdomain = request.headers.get("X-School-Subdomain")

        if school_id and school_name:
            return {
                "school_id": school_id,
                "school_name": school_name,
                "subdomain": subdomain,
            }

        # Fallback: try to extract from subdomain in host header
        host = request.headers.get("host", "")

        # Extract subdomain from host
        if host and not host.startswith(("localhost", "127.0.0.1")):
            clean_host = host.split(":")[0]
            parts = clean_host.split(".")
            if len(parts) >= 3 and parts[0] != "www":
                subdomain = parts[0]

                # Look up the school information from the database
                if subdomain:
                    try:
                        # Use the same database session as the login function
                        async with db_manager.get_connection() as db_conn:
                            query = """
                                SELECT id, name, subdomain, subscription_tier
                                FROM platform.schools 
                                WHERE subdomain = $1 AND is_active = true
                            """

                            result = await db_conn.fetchrow(query, subdomain.lower())

                            if result:
                                return {
                                    "school_id": str(result["id"]),
                                    "school_name": result["name"],
                                    "subdomain": result["subdomain"],
                                    "subscription_tier": result["subscription_tier"]
                                    or "basic",
                                }
                    except Exception as e:
                        logger.warning(
                            f"Error looking up school by subdomain: {str(e)}"
                        )
                        # Continue with login even if school lookup fails

        return None
    except Exception as e:
        logger.warning(f"Error extracting tenant info: {str(e)}")
        return None


@router.options("/login")
async def login_options():
    """Handle OPTIONS requests for login endpoint"""
    return {}


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Authenticate user and create session
    Supports both email/password and school-specific login
    """
    try:
        # Debug logging
        logger.info(
            f"Login attempt with data: email={login_data.email}, password_length={len(login_data.password) if hasattr(login_data, 'password') else 'NO_PASSWORD'}"
        )
        # Get tenant info if available
        tenant_info = await get_current_tenant_info(request)

        # Find user by email
        query = select(PlatformUser).where(
            and_(
                PlatformUser.email == login_data.email.lower(),
                PlatformUser.status == UserStatus.ACTIVE.value,
            )
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Check if user has a password hash
        if not user.password_hash:
            logger.warning(f"User {user.email} has no password hash set")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account setup incomplete. Please contact your administrator.",
            )

        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            # Log failed attempt
            logger.warning(
                f"Failed login attempt for {login_data.email} from {request.client.host}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Get user's school memberships
        memberships_query = select(SchoolMembership).where(
            and_(
                SchoolMembership.user_id == user.id,
                SchoolMembership.status == MembershipStatus.ACTIVE.value,
            )
        )
        memberships_result = await db.execute(memberships_query)
        memberships = memberships_result.scalars().all()

        # Determine primary school context
        primary_school_id = user.primary_school_id
        current_school_membership = None

        if tenant_info and tenant_info.get("school_id"):
            # Check if user has access to this school
            school_membership = next(
                (
                    m
                    for m in memberships
                    if str(m.school_id) == str(tenant_info["school_id"])
                ),
                None,
            )
            if school_membership:
                current_school_membership = school_membership
                primary_school_id = school_membership.school_id

        if not current_school_membership and memberships:
            # Use primary school or first available
            primary_membership = next(
                (m for m in memberships if m.school_id == primary_school_id),
                memberships[0],
            )
            current_school_membership = primary_membership
            primary_school_id = primary_membership.school_id

        # Create session
        session_id = str(uuid4())
        session = UserSession(
            user_id=user.id,
            session_id=session_id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", ""),
            current_school_id=(
                auth_service._coerce_uuid(primary_school_id)
                if primary_school_id
                else None
            ),
            available_school_ids=[str(m.school_id) for m in memberships],
            last_activity_at=_utcnow(),
            expires_at=_utcnow() + timedelta(days=30),  # 30 day expiry
            is_active=True,
        )

        db.add(session)

        # Update user last login
        user.last_login_at = _utcnow()
        user.last_activity_at = _utcnow()
        user.login_count = (user.login_count or 0) + 1
        user.failed_login_attempts = 0

        # Generate tokens
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "session_id": session_id,
                "school_id": (
                    str(session.current_school_id) if session.current_school_id else None
                ),
                "platform_role": user.global_role,
                "school_role": (
                    current_school_membership.school_role
                    if current_school_membership
                    else None
                ),
            }
        )

        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "session_id": str(session_id)}
        )

        # Store refresh token in session
        session.refresh_token = refresh_token

        await db.commit()
        user_data = await auth_service.get_user_with_context(
            db,
            str(user.id),
            str(session.current_school_id) if session.current_school_id else None,
        )

        # Set secure HTTP-only cookie for refresh token
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=7 * 24 * 60 * 60,  # 7 days
            httponly=True,
            secure=True,
            samesite="strict",
        )

        logger.info(f"Successful login for {user.email} from {request.client.host}")

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=3600,  # 1 hour
            refresh_token=refresh_token,
            user=user_data or {},
        )

    except HTTPException:
        raise
    except RequestValidationError:
        # Let FastAPI handle validation errors
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        )


@router.get("/me", response_model=UserContextResponse)
async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get current user with full context including school memberships
    """
    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        session_id = payload.get("session_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        # Verify session is still active
        session_query = select(UserSession).where(
            and_(
                UserSession.session_id == session_id,
                UserSession.user_id == auth_service._coerce_uuid(user_id),
                UserSession.is_active.is_(True),
            )
        )
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired"
            )

        # Update session activity
        session.last_activity_at = _utcnow()

        # Get user with memberships
        user = await auth_service.get_user_with_context(
            db,
            user_id,
            (
                str(session.current_school_id)
                if session.current_school_id
                else payload.get("school_id")
            ),
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        await db.commit()

        return UserContextResponse(**user)

    except HTTPException:
        raise
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user context",
        )


@router.post("/refresh")
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Refresh access token using refresh token
    """
    try:
        # Get refresh token from request or cookie
        refresh_token = refresh_data.refresh_token or request.cookies.get(
            "refresh_token"
        )

        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token required",
            )

        # Verify refresh token
        payload = verify_token(refresh_token, token_type="refresh")
        user_id = payload.get("sub")
        session_id = payload.get("session_id")

        # Verify session exists and refresh token matches
        session_query = select(UserSession).where(
            and_(
                UserSession.session_id == session_id,
                UserSession.user_id == auth_service._coerce_uuid(user_id),
                UserSession.refresh_token == refresh_token,
                UserSession.is_active.is_(True),
            )
        )
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if not session or session.is_expired:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        # Get user for token data
        user_query = select(PlatformUser).where(
            and_(
                PlatformUser.id == auth_service._coerce_uuid(user_id),
                PlatformUser.status == UserStatus.ACTIVE.value,
            )
        )
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        current_membership = None
        if session.current_school_id:
            current_membership = await auth_service.verify_user_school_access(
                db,
                user_id,
                str(session.current_school_id),
            )

        # Create new access token
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "session_id": session_id,
                "school_id": (
                    str(session.current_school_id) if session.current_school_id else None
                ),
                "platform_role": user.global_role,
                "school_role": (
                    current_membership.school_role if current_membership else None
                ),
            }
        )

        # Update session activity
        session.last_activity_at = _utcnow()
        await db.commit()

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 3600,
        }

    except HTTPException:
        raise
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        )


@router.post("/logout")
async def logout(
    response: Response,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Logout user and invalidate session
    """
    try:
        # Verify token to get session info
        payload = verify_token(credentials.credentials)
        session_id = payload.get("session_id")
        user_id = payload.get("sub")

        if session_id and user_id:
            # Deactivate session
            session_query = select(UserSession).where(
                and_(
                    UserSession.session_id == session_id,
                    UserSession.user_id == auth_service._coerce_uuid(user_id),
                )
            )
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()

            if session:
                session.is_active = False
                session.last_activity_at = _utcnow()

        # Clear refresh token cookie
        response.delete_cookie(
            key="refresh_token", httponly=True, secure=True, samesite="strict"
        )

        await db.commit()

        return {"message": "Successfully logged out"}

    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        # Still return success even if session cleanup fails
        response.delete_cookie("refresh_token")
        return {"message": "Logged out"}


@router.post("/register", response_model=LoginResponse)
async def register(
    registration_data: UserRegistrationRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Register new user account
    Used for self-registration when enabled
    """
    try:
        # Check if email already exists
        existing_user_query = select(PlatformUser).where(
            PlatformUser.email == registration_data.email.lower()
        )
        existing_result = await db.execute(existing_user_query)
        existing_user = existing_result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create new user
        user = await auth_service.create_user(
            db=db,
            email=registration_data.email.lower(),
            password=registration_data.password,
            first_name=registration_data.first_name,
            last_name=registration_data.last_name,
            platform_role=registration_data.platform_role,
        )

        await db.commit()

        # Automatically log in the new user
        login_request = LoginRequest(
            email=registration_data.email, password=registration_data.password
        )

        return await login(login_request, request, response, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/complete-onboarding")
async def complete_onboarding(
    onboarding_data: OnboardingCompleteRequest,
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Complete user onboarding process
    Can be used for new users or adding school memberships to existing users
    """
    try:
        user = None

        # Check if this is an authenticated user (adding school membership)
        if credentials:
            try:
                payload = verify_token(credentials.credentials)
                user_id = payload.get("sub")

                user_query = select(PlatformUser).where(PlatformUser.id == user_id)
                result = await db.execute(user_query)
                user = result.scalar_one_or_none()
            except:
                pass  # Ignore token errors for onboarding

        if not user:
            # Create new user
            user = await auth_service.create_user_from_onboarding(db, onboarding_data)
        else:
            # Update existing user with onboarding data
            user = await auth_service.update_user_from_onboarding(
                db, user, onboarding_data
            )

        await db.commit()

        # Return success with user context
        user_context = await auth_service.get_user_with_context(db, str(user.id))

        return {"message": "Onboarding completed successfully", "user": user_context}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Onboarding completion error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Onboarding completion failed",
        )


@router.post("/switch-school")
async def switch_school(
    switch_data: SwitchSchoolRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Switch user's current school context and return a fresh access token with updated context.
    """
    try:
        token_data = verify_token(credentials.credentials)
        user_id = token_data.get("sub")
        session_id = token_data.get("session_id")
        school_id = switch_data.school_id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session context missing from token",
            )

        session_query = select(UserSession).where(
            and_(
                UserSession.session_id == session_id,
                UserSession.user_id == auth_service._coerce_uuid(user_id),
                UserSession.is_active.is_(True),
            )
        )
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if not session or session.is_expired:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired",
            )

        membership = await auth_service.verify_user_school_access(db, user_id, school_id)
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this school",
            )

        user_query = select(PlatformUser).where(
            and_(
                PlatformUser.id == auth_service._coerce_uuid(user_id),
                PlatformUser.status == UserStatus.ACTIVE.value,
            )
        )
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        available_school_ids = [str(sid) for sid in (session.available_school_ids or [])]
        if school_id not in available_school_ids:
            available_school_ids.append(school_id)

        session.current_school_id = auth_service._coerce_uuid(school_id)
        session.available_school_ids = available_school_ids
        session.school_switch_count = (session.school_switch_count or 0) + 1
        session.last_school_switch_at = _utcnow()
        session.last_activity_at = _utcnow()

        # Issue new access token scoped to selected school
        new_access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "session_id": session.session_id,
                "school_id": school_id,
                "platform_role": user.global_role,
                "school_role": membership.school_role,
            }
        )

        await db.commit()

        user_context = await auth_service.get_user_with_context(db, user_id, school_id)
        current_school = user_context.get("current_school") if user_context else None

        return {
            "message": "School context switched successfully",
            "access_token": new_access_token,
            "current_school": current_school,
            "user": user_context,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"School switch error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to switch school context",
        )


@router.get("/me/schools")
async def get_my_schools(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get all schools the current user has access to.
    Lightweight endpoint for the school switcher — no full user context needed.
    """
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        memberships_query = select(SchoolMembership).where(
            and_(
                SchoolMembership.user_id == auth_service._coerce_uuid(user_id),
                SchoolMembership.status == MembershipStatus.ACTIVE.value,
            )
        )
        result = await db.execute(memberships_query)
        memberships = result.scalars().all()

        schools = []
        for m in memberships:
            schools.append({
                "school_id": str(m.school_id),
                "school_name": m.school_name,
                "school_subdomain": m.school_subdomain,
                "role": m.role,
                "permissions": m.permissions or [],
                "student_id": m.student_id,
                "employee_id": m.employee_id,
                "department": m.department,
                "current_grade": m.current_grade,
                "children_ids": [str(c) for c in (m.children_ids or [])],
            })

        return {"schools": schools, "count": len(schools)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get schools error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get schools",
        )
