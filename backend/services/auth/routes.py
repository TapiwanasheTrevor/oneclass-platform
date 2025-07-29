# =====================================================
# Authentication Service Routes
# Complete authentication system with login, logout, session management
# File: backend/services/auth/routes.py
# =====================================================

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import bcrypt
import jwt
import logging
from uuid import uuid4

from shared.database import get_async_session
from shared.models.platform_user import (
    PlatformUser,
    UserSession,
    SchoolMembership,
)
from shared.models.platform import School
from shared.middleware.tenant_middleware import get_tenant_context, TenantContext
from shared.auth import db_manager
from .schemas import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
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
                PlatformUser.is_active.is_(True),
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
                SchoolMembership.status == "active",
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
                (m for m in memberships if m.school_id == tenant_info["school_id"]),
                None,
            )
            if school_membership:
                current_school_membership = school_membership
                primary_school_id = tenant_info["school_id"]

        if not current_school_membership and memberships:
            # Use primary school or first available
            primary_membership = next(
                (m for m in memberships if m.school_id == user.primary_school_id),
                memberships[0],
            )
            current_school_membership = primary_membership
            primary_school_id = primary_membership.school_id

        # Create session
        session_id = str(uuid4())
        refresh_token = str(uuid4())  # Generate refresh token
        session = UserSession(
            user_id=user.id,
            session_id=session_id,
            refresh_token=refresh_token,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", ""),
            expires_at=datetime.utcnow() + timedelta(days=30),  # 30 day expiry
            is_active=True,
        )

        db.add(session)

        # Update user last login
        user.last_login = datetime.utcnow()

        # Generate tokens
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "session_id": str(session_id),
                "school_id": str(primary_school_id) if primary_school_id else None,
                "platform_role": user.platform_role,
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

        # Set secure HTTP-only cookie for refresh token
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=7 * 24 * 60 * 60,  # 7 days
            httponly=True,
            secure=True,
            samesite="strict",
        )

        # Prepare user data with school memberships
        user_data = {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "platform_role": user.platform_role,
            "status": user.status,
            "primary_school_id": (
                str(user.primary_school_id) if user.primary_school_id else None
            ),
            "profile": user.user_metadata or {},
            "feature_flags": {},
            "user_preferences": user.preferences or {},
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "school_memberships": [],
        }

        # Add school membership details
        for membership in memberships:
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
                        "role": membership.school_role,
                        "permissions": membership.permissions,
                        "joined_date": membership.joined_date.isoformat(),
                        "status": membership.status,
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
                        "children_ids": [
                            str(child_id)
                            for child_id in (membership.children_ids or [])
                        ],
                    }
                )

        logger.info(f"Successful login for {user.email} from {request.client.host}")

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=3600,  # 1 hour
            refresh_token=refresh_token,
            user=user_data,
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
                UserSession.user_id == user_id,
                UserSession.is_active == True,
            )
        )
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired"
            )

        # Update session activity
        session.last_activity = datetime.utcnow()

        # Get user with memberships
        user = await auth_service.get_user_with_context(db, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        await db.commit()

        return UserContextResponse(**user)

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
                UserSession.id == session_id,
                UserSession.user_id == user_id,
                UserSession.refresh_token == refresh_token,
                UserSession.is_active == True,
            )
        )
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        # Get user for token data
        user_query = select(PlatformUser).where(PlatformUser.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        # Create new access token
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "session_id": session_id,
                "school_id": session.school_id,
                "platform_role": user.platform_role,
            }
        )

        # Update session activity
        session.last_activity = datetime.utcnow()
        await db.commit()

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 3600,
        }

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

        if session_id:
            # Deactivate session
            session_query = select(UserSession).where(UserSession.id == session_id)
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()

            if session:
                session.is_active = False
                session.ended_at = datetime.utcnow()

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
    school_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Switch user's current school context
    """
    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        session_id = payload.get("session_id")

        # Verify user has access to the school
        membership_query = select(SchoolMembership).where(
            and_(
                SchoolMembership.user_id == user_id,
                SchoolMembership.school_id == school_id,
                SchoolMembership.status == "active",
            )
        )
        membership_result = await db.execute(membership_query)
        membership = membership_result.scalar_one_or_none()

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this school",
            )

        # Update session's current school
        if session_id:
            session_query = select(UserSession).where(UserSession.id == session_id)
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()

            if session:
                session.school_id = school_id
                session.last_activity = datetime.utcnow()

        await db.commit()

        # Get updated user context
        user_context = await auth_service.get_user_with_context(db, user_id)

        return {
            "message": "School context switched successfully",
            "current_school_id": school_id,
            "user": user_context,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"School switch error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to switch school context",
        )
