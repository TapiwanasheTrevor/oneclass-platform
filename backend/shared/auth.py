# =====================================================
# Authentication Layer
# Clerk = identity provider, this module = school context resolver
# File: backend/shared/auth.py
# =====================================================

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import os
import logging
from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Pydantic session model for middleware compatibility
class UserSessionData(BaseModel):
    """Lightweight user session for middleware"""
    user_id: str
    role: str
    permissions: List[str] = []
    features: List[str] = []
    school_id: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


try:
    import jwt
    from jwt.exceptions import PyJWTError
except ImportError:
    jwt = None
    class PyJWTError(Exception):
        pass

try:
    import asyncpg
except ImportError:
    asyncpg = None

from contextlib import asynccontextmanager
from shared.database import get_current_school_id

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/oneclass")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = "HS256"

# Security scheme
security = HTTPBearer()

# Import consolidated model
from shared.models.platform_user import (
    PlatformUser, GlobalRole, SchoolRole, UserStatus,
    SchoolMembership, UserSession
)


# =====================================================
# DATABASE CONNECTION
# =====================================================

class DatabaseManager:
    def __init__(self):
        self.pool = None

    async def initialize(self):
        self.pool = await asyncpg.create_pool(DATABASE_URL)

    async def close(self):
        if self.pool:
            await self.pool.close()

    @asynccontextmanager
    async def get_connection(self):
        if not self.pool:
            await self.initialize()
        async with self.pool.acquire() as connection:
            school_id = get_current_school_id()
            if school_id:
                try:
                    await connection.execute("SET app.current_school_id = $1", school_id)
                except Exception:
                    pass
            try:
                yield connection
            finally:
                try:
                    await connection.execute("RESET app.current_school_id")
                except Exception:
                    pass


db_manager = DatabaseManager()


async def get_database_connection():
    async with db_manager.get_connection() as conn:
        yield conn


# =====================================================
# TOKEN MANAGEMENT
# =====================================================

def create_access_token(user_id: str, school_id: str) -> str:
    """Create JWT access token with school context"""
    payload = {
        "sub": user_id,
        "school_id": school_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def validate_token(token: str) -> Dict[str, Any]:
    """Validate JWT token and return payload"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


# =====================================================
# USER RESOLUTION
# =====================================================

async def get_current_active_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> PlatformUser:
    """
    Main auth dependency: resolve JWT → PlatformUser with school memberships.
    Queries platform.users (the consolidated table).
    """
    token_data = await validate_token(credentials.credentials)
    user_id = token_data.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    async with db_manager.get_connection() as conn:
        # Query the consolidated users table
        user_row = await conn.fetchrow(
            """
            SELECT id, email, first_name, last_name, display_name,
                   global_role, status, primary_school_id,
                   clerk_user_id, contact_information, personal_profile,
                   user_preferences, last_login_at, created_at, updated_at
            FROM platform.users
            WHERE id = $1 AND status = 'active'
            """,
            UUID(user_id)
        )

        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Get all active school memberships
        membership_rows = await conn.fetch(
            """
            SELECT school_id, school_name, school_subdomain, role,
                   permissions, joined_date, status, student_id,
                   current_grade, admission_date, graduation_date,
                   employee_id, department, hire_date, contract_type,
                   children_ids, school_region, position
            FROM platform.school_memberships
            WHERE user_id = $1 AND status = 'active'
            """,
            UUID(user_id)
        )

        # Build response — return as a simple dict that routes can serialize
        memberships = []
        for m in membership_rows:
            memberships.append({
                "school_id": str(m["school_id"]),
                "school_name": m["school_name"],
                "school_subdomain": m["school_subdomain"],
                "role": m["role"],
                "permissions": m["permissions"] or [],
                "joined_date": m["joined_date"].isoformat() if m["joined_date"] else None,
                "status": m["status"],
                "student_id": m["student_id"],
                "current_grade": m["current_grade"],
                "admission_date": m["admission_date"].isoformat() if m["admission_date"] else None,
                "graduation_date": m["graduation_date"].isoformat() if m["graduation_date"] else None,
                "employee_id": m["employee_id"],
                "department": m["department"],
                "hire_date": m["hire_date"].isoformat() if m["hire_date"] else None,
                "contract_type": m["contract_type"],
                "children_ids": [str(c) for c in (m["children_ids"] or [])],
            })

        # Derive school_id from token context or primary
        token_school_id = token_data.get("school_id")
        effective_school_id = token_school_id or (
            str(user_row["primary_school_id"]) if user_row["primary_school_id"] else None
        )

        # Collect permissions from the active school membership
        active_permissions = []
        if effective_school_id:
            for m in memberships:
                if m["school_id"] == effective_school_id:
                    active_permissions = m.get("permissions", [])
                    break

        # Build a lightweight user object
        user = type('UserContext', (), {
            'id': user_row["id"],
            'email': user_row["email"],
            'first_name': user_row["first_name"],
            'last_name': user_row["last_name"],
            'full_name': f"{user_row['first_name']} {user_row['last_name']}",
            'global_role': user_row["global_role"],
            'platform_role': user_row["global_role"],
            'role': user_row["global_role"],
            'status': user_row["status"],
            'school_id': UUID(effective_school_id) if effective_school_id else user_row["primary_school_id"],
            'primary_school_id': user_row["primary_school_id"],
            'clerk_user_id': user_row["clerk_user_id"],
            'school_memberships': memberships,
            'contact_information': user_row["contact_information"] or {},
            'personal_profile': user_row["personal_profile"] or {},
            'user_preferences': user_row["user_preferences"] or {},
            'last_login_at': user_row["last_login_at"],
            'created_at': user_row["created_at"],
            'updated_at': user_row["updated_at"],
            'is_platform_admin': user_row["global_role"] in [
                GlobalRole.SUPER_ADMIN.value, GlobalRole.PLATFORM_ADMIN.value
            ],
            'permissions': active_permissions,
            'can_access_feature': lambda self, f: True,
        })()

        return user


# Alias for backward compat
get_current_user = get_current_active_user


async def require_super_admin(
    current_user = Depends(get_current_user)
):
    """Require super admin or platform admin"""
    if current_user.global_role not in [
        GlobalRole.SUPER_ADMIN.value, GlobalRole.PLATFORM_ADMIN.value
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin permissions required"
        )
    return current_user


async def get_current_school_context(
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current school context for the user"""
    return {
        "school_id": str(current_user.primary_school_id) if current_user.primary_school_id else None,
        "user_role": current_user.global_role,
    }


# =====================================================
# PERMISSIONS & FEATURES
# =====================================================

async def get_user_permissions(role: str, school_id: UUID) -> List[str]:
    """Get permissions based on role"""
    base_permissions = {
        "super_admin": ["*"],
        "platform_admin": ["*"],
        "school_admin": [
            "students.create", "students.read", "students.update", "students.delete",
            "staff.create", "staff.read", "staff.update", "staff.delete",
            "classes.create", "classes.read", "classes.update", "classes.delete",
            "reports.generate", "settings.update", "finance.manage"
        ],
        "registrar": [
            "students.create", "students.read", "students.update",
            "documents.upload", "documents.verify"
        ],
        "teacher": [
            "students.read", "attendance.mark", "grades.enter",
            "disciplinary.minor", "health.basic"
        ],
        "parent": ["children.read", "payments.make", "communications.receive"],
        "student": ["profile.read", "assignments.view", "grades.view"],
    }
    return base_permissions.get(role, [])


async def get_available_features(subscription_tier: str) -> List[str]:
    """Get features based on subscription tier"""
    tiers = {
        "trial": ["student_management", "basic_attendance", "parent_communication"],
        "basic": [
            "student_management", "attendance_tracking", "basic_reports",
            "parent_portal", "disciplinary_system", "migration_services"
        ],
        "premium": [
            "student_management", "attendance_tracking", "health_records",
            "finance_module", "parent_portal", "disciplinary_system",
            "advanced_reports", "bulk_communication", "migration_services"
        ],
        "enterprise": [
            "student_management", "attendance_tracking", "health_records",
            "finance_module", "parent_portal", "disciplinary_system",
            "advanced_reports", "bulk_communication", "ministry_reporting",
            "ai_assistance", "custom_integrations", "priority_support",
            "migration_services"
        ],
    }
    return tiers.get(subscription_tier, tiers["trial"])


def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        from functools import wraps
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            # Super admin / platform admin bypass
            if getattr(current_user, 'platform_role', None) in [
                GlobalRole.SUPER_ADMIN.value, GlobalRole.PLATFORM_ADMIN.value,
                'super_admin', 'platform_admin'
            ]:
                return await func(*args, **kwargs)
            user_perms = getattr(current_user, 'permissions', []) or []
            if "*" not in user_perms and permission not in user_perms:
                # Check dot-prefix match (e.g. "finance.read" matches "finance.*")
                module = permission.split('.')[0] if '.' in permission else None
                if not module or f"{module}.*" not in user_perms:
                    raise HTTPException(status_code=403, detail=f"Permission required: {permission}")
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# =====================================================
# MIDDLEWARE TOKEN VERIFICATION
# =====================================================

async def verify_token(token: str) -> Optional[UserSessionData]:
    """Verify JWT and return lightweight session data for middleware"""
    try:
        if not token:
            return None

        token_data = await validate_token(token)
        user_id = token_data.get("sub")
        school_id = token_data.get("school_id")
        if not user_id:
            return None

        async with db_manager.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, email, first_name, last_name, global_role, primary_school_id
                FROM platform.users
                WHERE id = $1 AND status = 'active'
                """,
                UUID(user_id)
            )
            if not row:
                return None

            primary_school_id = row["primary_school_id"]
            permissions = []
            features = []

            if primary_school_id:
                membership = await conn.fetchrow(
                    """
                    SELECT role, permissions
                    FROM platform.school_memberships
                    WHERE user_id = $1 AND school_id = $2 AND status = 'active'
                    """,
                    UUID(user_id), primary_school_id
                )
                if membership:
                    permissions = membership["permissions"] or []

                tier = await conn.fetchval(
                    "SELECT subscription_tier FROM platform.schools WHERE id = $1",
                    primary_school_id
                )
                features = await get_available_features(tier or "basic")

            return UserSessionData(
                user_id=str(row["id"]),
                role=row["global_role"],
                permissions=permissions,
                features=features,
                school_id=str(primary_school_id) if primary_school_id else None,
                email=row["email"],
                first_name=row["first_name"],
                last_name=row["last_name"],
                issued_at=datetime.fromtimestamp(token_data.get("iat", 0)) if token_data.get("iat") else None,
                expires_at=datetime.fromtimestamp(token_data.get("exp", 0)) if token_data.get("exp") else None,
            )
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        return None


async def get_school_subscription_tier(school_id: UUID) -> str:
    async with db_manager.get_connection() as conn:
        return await conn.fetchval(
            "SELECT subscription_tier FROM platform.schools WHERE id = $1",
            school_id
        ) or "basic"


# =====================================================
# WEBSOCKET AUTH
# =====================================================

async def get_websocket_user(token: Optional[str]):
    """Authenticate user from WebSocket token"""
    if not token:
        return None
    try:
        token_data = await validate_token(token)
        user_id = token_data.get("sub")
        if not user_id:
            return None

        async with db_manager.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, email, first_name, last_name, global_role,
                       primary_school_id, created_at
                FROM platform.users
                WHERE id = $1 AND status = 'active'
                """,
                UUID(user_id)
            )
            if not row:
                return None

            return type('WSUser', (), {
                'id': row["id"],
                'email': row["email"],
                'first_name': row["first_name"],
                'last_name': row["last_name"],
                'global_role': row["global_role"],
                'platform_role': row["global_role"],
                'primary_school_id': row["primary_school_id"],
            })()

    except Exception as e:
        logger.error(f"WebSocket auth error: {e}")
        return None


# =====================================================
# LIFECYCLE
# =====================================================

def require_feature(feature: str):
    """Decorator to require a specific feature enabled for the school"""
    def decorator(func):
        from functools import wraps
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                return await func(*args, **kwargs)
            # Super admin bypasses feature checks
            if getattr(current_user, 'platform_role', None) in [
                GlobalRole.SUPER_ADMIN.value, GlobalRole.PLATFORM_ADMIN.value,
                'super_admin', 'platform_admin'
            ]:
                return await func(*args, **kwargs)
            # Check if the school's subscription includes this feature
            school_id = getattr(current_user, 'school_id', None) or getattr(current_user, 'primary_school_id', None)
            if school_id:
                tier = await get_school_subscription_tier(school_id)
                available = await get_available_features(tier)
                if feature not in available:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Feature '{feature}' not available on your subscription plan"
                    )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Type alias — Finance and other services import this as the user dependency type
EnhancedUser = type(None)  # duck-typed; actual object comes from get_current_active_user


async def init_auth_system():
    await db_manager.initialize()

async def cleanup_auth_system():
    await db_manager.close()
