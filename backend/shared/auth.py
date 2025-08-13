# =====================================================
# Enhanced Authentication with Full School Context
# Implements multitenancy enhancement plan requirements
# File: backend/shared/auth.py
# =====================================================

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import json
import os
import logging
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Add UserSession model for middleware compatibility
class UserSession(BaseModel):
    """User session model for middleware compatibility"""
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
    # For testing without jwt
    jwt = None
    class PyJWTError(Exception):
        pass

try:
    import asyncpg
except ImportError:
    # For testing without asyncpg
    asyncpg = None
from contextlib import asynccontextmanager
from shared.database import get_current_school_id

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/oneclass")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = "HS256"

# Security scheme
security = HTTPBearer()

# Enhanced user models removed - now using consolidated PlatformUser model
# See: backend/shared/models/platform_user.py

# Import the new consolidated model
from shared.models.platform_user import PlatformUser, PlatformRole, SchoolRole, UserStatus
    

# Database connection manager
class DatabaseManager:
    def __init__(self):
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection pool"""
        self.pool = await asyncpg.create_pool(DATABASE_URL)
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        if not self.pool:
            await self.initialize()
        
        async with self.pool.acquire() as connection:
            # Apply tenant RLS GUC for this connection if available
            school_id = get_current_school_id()
            if school_id:
                try:
                    await connection.execute("SET app.current_school_id = $1", school_id)
                except Exception:
                    # Do not fail request on context set failure
                    pass
            try:
                yield connection
            finally:
                # Reset GUC to avoid leaks between requests
                try:
                    await connection.execute("RESET app.current_school_id")
                except Exception:
                    pass

# Global database manager instance
db_manager = DatabaseManager()

async def get_database_connection():
    """Dependency to get database connection"""
    async with db_manager.get_connection() as conn:
        yield conn

def create_access_token(user_id: str, school_id: str) -> str:
    """Create JWT access token"""
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
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
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

async def get_current_active_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> PlatformUser:
    """
    Get current user with full context using the consolidated PlatformUser model.
    This is the main authentication dependency.
    """
    # Validate JWT token
    token_data = await validate_token(credentials.credentials)
    user_id = token_data.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get user with all school memberships
    async with db_manager.get_connection() as conn:
        # Get basic user data
        user_query = """
            SELECT 
                id, email, first_name, last_name, platform_role, status,
                primary_school_id, profile, clerk_integration, feature_flags,
                user_preferences, created_at, updated_at, last_login
            FROM platform.platform_users
            WHERE id = $1 AND status = 'active'
        """
        
        user_result = await conn.fetchrow(user_query, UUID(user_id))
        
        if not user_result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Get all school memberships
        memberships_query = """
            SELECT 
                sm.school_id, sm.school_name, sm.school_subdomain, sm.role,
                sm.permissions, sm.joined_date, sm.status, sm.student_id,
                sm.current_grade, sm.admission_date, sm.graduation_date,
                sm.employee_id, sm.department, sm.hire_date, sm.contract_type,
                sm.children_ids
            FROM platform.school_memberships sm
            WHERE sm.user_id = $1 AND sm.status = 'active'
        """
        
        memberships_result = await conn.fetch(memberships_query, UUID(user_id))
        
        # Build school memberships
        from shared.models.platform_user import SchoolMembership
        school_memberships = []
        for membership_row in memberships_result:
            membership = SchoolMembership(
                school_id=membership_row["school_id"],
                school_name=membership_row["school_name"],
                school_subdomain=membership_row["school_subdomain"],
                role=SchoolRole(membership_row["role"]),
                permissions=membership_row["permissions"] or [],
                joined_date=membership_row["joined_date"],
                status=UserStatus(membership_row["status"]),
                student_id=membership_row["student_id"],
                current_grade=membership_row["current_grade"],
                admission_date=membership_row["admission_date"],
                graduation_date=membership_row["graduation_date"],
                employee_id=membership_row["employee_id"],
                department=membership_row["department"],
                hire_date=membership_row["hire_date"],
                contract_type=membership_row["contract_type"],
                children_ids=membership_row["children_ids"] or []
            )
            school_memberships.append(membership)
        
        # Parse profile and other JSON fields
        from shared.models.platform_user import UserProfile, ClerkIntegration
        profile = None
        if user_result["profile"]:
            profile = UserProfile.parse_obj(user_result["profile"])
        
        clerk_integration = None
        if user_result["clerk_integration"]:
            clerk_integration = ClerkIntegration.parse_obj(user_result["clerk_integration"])
        
        # Create and return PlatformUser
        return PlatformUser(
            id=user_result["id"],
            email=user_result["email"],
            first_name=user_result["first_name"],
            last_name=user_result["last_name"],
            platform_role=PlatformRole(user_result["platform_role"]),
            status=UserStatus(user_result["status"]),
            school_memberships=school_memberships,
            primary_school_id=user_result["primary_school_id"],
            profile=profile,
            clerk_integration=clerk_integration,
            created_at=user_result["created_at"],
            updated_at=user_result["updated_at"],
            last_login=user_result["last_login"],
            feature_flags=user_result["feature_flags"] or {},
            user_preferences=user_result["user_preferences"] or {}
        )

async def get_user_permissions(role: str, school_id: UUID) -> List[str]:
    """Get user permissions based on role and school configuration"""
    base_permissions = {
        "super_admin": ["*"],  # All permissions
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
        "parent": [
            "children.read", "payments.make", "communications.receive"
        ],
        "student": [
            "profile.read", "assignments.view", "grades.view"
        ]
    }
    
    return base_permissions.get(role, [])

async def get_available_features(subscription_tier: str) -> List[str]:
    """Get available features based on subscription tier"""
    feature_tiers = {
        "trial": [
            "student_management", "basic_attendance", "parent_communication"
        ],
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
            "ai_assistance", "custom_integrations", "priority_support", "migration_services"
        ]
    }
    
    return feature_tiers.get(subscription_tier, feature_tiers["trial"])

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if "*" not in current_user.permissions and permission not in current_user.permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_feature(feature_name: str):
    """Decorator to require feature availability"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not current_user.can_access_feature(feature_name):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Feature not available: {feature_name}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# User authentication endpoints
async def authenticate_user(email: str, password: str) -> Optional[PlatformUser]:
    """Authenticate user with email and password"""
    # In production, this would integrate with Clerk or similar
    # For now, this is a placeholder implementation
    
    async with db_manager.get_connection() as conn:
        query = """
            SELECT id, primary_school_id, email, first_name, last_name, platform_role, status
            FROM platform.platform_users
            WHERE email = $1 AND status = 'active'
        """
        
        result = await conn.fetchrow(query, email)
        
        if not result:
            return None
        
        # In production, verify password hash here
        # For now, we'll skip password verification
        
        # Create token and return user
        token = create_access_token(
            str(result["id"]), 
            str(result["primary_school_id"]) if result["primary_school_id"] else ""
        )
        
        # Get full user context (this would normally be done in get_current_active_user)
        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        return await get_current_active_user(credentials)

# Initialize database on startup
async def init_auth_system():
    """Initialize authentication system"""
    await db_manager.initialize()

# Cleanup on shutdown
async def cleanup_auth_system():
    """Cleanup authentication system"""
    await db_manager.close()

# Add verify_token function for middleware compatibility
async def verify_token(token: str) -> Optional[UserSession]:
    """Verify JWT token and return user session (middleware compatibility)"""
    try:
        if not token:
            return None
        
        # Validate token
        token_data = await validate_token(token)
        user_id = token_data.get("sub")
        school_id = token_data.get("school_id")
        
        if not user_id:
            return None
        
        # Get user details from database
        async with db_manager.get_connection() as conn:
            query = """
                SELECT u.id, u.email, u.first_name, u.last_name, u.platform_role,
                       u.primary_school_id
                FROM platform.platform_users u
                WHERE u.id = $1 AND u.status = 'active'
            """
            
            result = await conn.fetchrow(query, UUID(user_id))
            
            if not result:
                return None
            
            # Get school membership for primary school if exists
            permissions = []
            primary_school_id = result["primary_school_id"]
            
            if primary_school_id:
                membership_query = """
                    SELECT role, permissions
                    FROM platform.school_memberships
                    WHERE user_id = $1 AND school_id = $2 AND status = 'active'
                """
                membership_result = await conn.fetchrow(membership_query, UUID(user_id), primary_school_id)
                if membership_result:
                    permissions = membership_result["permissions"] or []
                
                # Get features based on school subscription
                subscription_tier = await get_school_subscription_tier(primary_school_id)
                features = await get_available_features(subscription_tier)
            else:
                features = []
            
            return UserSession(
                user_id=str(result["id"]),
                role=result["platform_role"],
                permissions=permissions,
                features=features,
                school_id=str(primary_school_id) if primary_school_id else None,
                email=result["email"],
                first_name=result["first_name"],
                last_name=result["last_name"],
                issued_at=datetime.fromtimestamp(token_data.get("iat", 0)) if token_data.get("iat") else None,
                expires_at=datetime.fromtimestamp(token_data.get("exp", 0)) if token_data.get("exp") else None
            )
            
    except Exception as e:
        return None

async def get_school_subscription_tier(school_id: UUID) -> str:
    """Get school subscription tier"""
    async with db_manager.get_connection() as conn:
        query = "SELECT subscription_tier FROM platform.schools WHERE id = $1"
        result = await conn.fetchval(query, school_id)
        return result or "basic"

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> "UnifiedUser":
    """Alias for get_current_active_user for compatibility"""
    from .models.unified_user import UnifiedUser
    
    # This is a simplified version - in production, implement full user lookup
    user = await get_current_active_user(credentials)
    
    # Convert PlatformUser to UnifiedUser for compatibility
    # This is a temporary bridge until unified
    return UnifiedUser(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        global_role=user.platform_role.value if hasattr(user.platform_role, 'value') else str(user.platform_role),
        status="active"
    )


async def require_super_admin(
    current_user: "UnifiedUser" = Depends(get_current_user)
) -> "UnifiedUser":
    """Require super admin permissions"""
    from .models.unified_user import GlobalRole
    
    if not current_user.global_role or current_user.global_role not in [
        GlobalRole.SUPER_ADMIN.value, 
        GlobalRole.PLATFORM_ADMIN.value
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin permissions required"
        )
    
    return current_user


async def get_current_school_context(
    current_user: "UnifiedUser" = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current school context for the user"""
    
    # This is a simplified version - in production would determine current school
    # based on subdomain, user selection, or other context
    return {
        "school_id": "default-school-id",
        "school_name": "Default School",
        "user_role": "principal"  # or actual role
    }


async def get_websocket_user(token: Optional[str]) -> Optional[PlatformUser]:
    """
    Authenticate user from WebSocket token parameter
    Used for WebSocket connections that can't use standard HTTP auth
    """
    if not token:
        return None
    
    try:
        # Validate JWT token
        token_data = await validate_token(token)
        user_id = token_data.get("sub")
        
        if not user_id:
            return None
        
        # Use same logic as get_current_active_user but without HTTP dependencies
        async with db_manager.get_connection() as conn:
            # Get basic user data
            user_query = """
                SELECT 
                    id, email, first_name, last_name, platform_role, status,
                    primary_school_id, profile, clerk_integration, feature_flags,
                    user_preferences, created_at, updated_at, last_login
                FROM platform.platform_users
                WHERE id = $1 AND status = 'active'
            """
            
            user_result = await conn.fetchrow(user_query, UUID(user_id))
            
            if not user_result:
                return None
            
            # Get all school memberships
            memberships_query = """
                SELECT 
                    sm.school_id, sm.school_name, sm.school_subdomain, sm.role,
                    sm.permissions, sm.joined_date, sm.status, sm.student_id,
                    sm.current_grade, sm.admission_date, sm.graduation_date,
                    sm.employee_id, sm.department, sm.hire_date, sm.contract_type,
                    sm.children_ids
                FROM platform.school_memberships sm
                WHERE sm.user_id = $1 AND sm.status = 'active'
            """
            
            memberships_result = await conn.fetch(memberships_query, UUID(user_id))
            
            # Build school memberships
            from shared.models.platform_user import SchoolMembership
            school_memberships = []
            for membership_row in memberships_result:
                membership = SchoolMembership(
                    school_id=membership_row["school_id"],
                    school_name=membership_row["school_name"],
                    school_subdomain=membership_row["school_subdomain"],
                    role=SchoolRole(membership_row["role"]),
                    permissions=membership_row["permissions"] or [],
                    joined_date=membership_row["joined_date"],
                    status=UserStatus(membership_row["status"]),
                    student_id=membership_row["student_id"],
                    current_grade=membership_row["current_grade"],
                    admission_date=membership_row["admission_date"],
                    graduation_date=membership_row["graduation_date"],
                    employee_id=membership_row["employee_id"],
                    department=membership_row["department"],
                    hire_date=membership_row["hire_date"],
                    contract_type=membership_row["contract_type"],
                    children_ids=membership_row["children_ids"] or []
                )
                school_memberships.append(membership)
            
            # Parse profile and other JSON fields
            from shared.models.platform_user import UserProfile, ClerkIntegration
            profile = None
            if user_result["profile"]:
                profile = UserProfile.parse_obj(user_result["profile"])
            
            clerk_integration = None
            if user_result["clerk_integration"]:
                clerk_integration = ClerkIntegration.parse_obj(user_result["clerk_integration"])
            
            # Create and return PlatformUser
            return PlatformUser(
                id=user_result["id"],
                email=user_result["email"],
                first_name=user_result["first_name"],
                last_name=user_result["last_name"],
                platform_role=PlatformRole(user_result["platform_role"]),
                status=UserStatus(user_result["status"]),
                school_memberships=school_memberships,
                primary_school_id=user_result["primary_school_id"],
                profile=profile,
                clerk_integration=clerk_integration,
                created_at=user_result["created_at"],
                updated_at=user_result["updated_at"],
                last_login=user_result["last_login"],
                feature_flags=user_result["feature_flags"] or {},
                user_preferences=user_result["user_preferences"] or {}
            )
            
    except Exception as e:
        logger.error(f"Error authenticating WebSocket user: {str(e)}")
        return None