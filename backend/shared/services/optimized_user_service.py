# =====================================================
# Optimized User Service for High Performance Operations
# Performance-optimized service with caching and efficient queries
# File: backend/shared/services/optimized_user_service.py
# =====================================================

import asyncio
import json
import logging
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from dataclasses import dataclass

# Database imports
import asyncpg
from sqlalchemy import select, and_, or_, func, distinct
from sqlalchemy.orm import selectinload, joinedload, Session
from sqlalchemy.ext.asyncio import AsyncSession

# Models
from shared.models.platform_user import (
    PlatformUser,
    SchoolMembership,
    UserProfile,
    ClerkIntegration,
    PlatformRole,
    SchoolRole,
    UserStatus,
)
from shared.cache.user_context_cache import UserContextCache

logger = logging.getLogger(__name__)


@dataclass
class MinimalUserContext:
    """Lightweight user context for performance-critical operations"""

    user_id: UUID
    email: str
    full_name: str
    platform_role: PlatformRole
    school_role: Optional[SchoolRole] = None
    school_id: Optional[UUID] = None
    permissions: List[str] = None
    is_active: bool = True

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []


@dataclass
class UserSummary:
    """Summary view of user for lists and bulk operations"""

    id: UUID
    email: str
    full_name: str
    platform_role: PlatformRole
    school_role: Optional[SchoolRole] = None
    joined_date: Optional[datetime] = None
    phone_number: Optional[str] = None
    profile_image_url: Optional[str] = None
    status: UserStatus = UserStatus.ACTIVE


class OptimizedUserService:
    """
    Performance-optimized user service with multi-layer caching
    Designed for high-throughput operations with minimal database queries
    """

    def __init__(self, db_session: AsyncSession, cache: UserContextCache):
        """
        Initialize service with database session and cache

        Args:
            db_session: SQLAlchemy async session
            cache: UserContextCache instance
        """
        self.db = db_session
        self.cache = cache
        self.logger = logger

    # Core User Retrieval Methods

    async def get_user_by_id(
        self, user_id: UUID, use_cache: bool = True
    ) -> Optional[PlatformUser]:
        """
        Get user by ID with optional caching

        Args:
            user_id: User's UUID
            use_cache: Whether to use cache (default: True)
        """
        if use_cache:
            # Try cache first
            cached_context = await self.cache.get_user_context(user_id)
            if cached_context:
                try:
                    return PlatformUser.parse_obj(cached_context["user"])
                except Exception as e:
                    self.logger.warning(f"Error parsing cached user {user_id}: {e}")

        # Query database with optimized joins
        query = (
            select(PlatformUserDB)
            .options(selectinload(PlatformUserDB.school_memberships))
            .where(PlatformUserDB.id == user_id)
        )

        result = await self.db.execute(query)
        user_db = result.scalar_one_or_none()

        if not user_db:
            return None

        # Convert to Pydantic model
        user = await self._convert_db_to_pydantic(user_db)

        # Cache the result if using cache
        if use_cache and user:
            await self.cache.set_user_context(user_id, {"user": user.dict()})

        return user

    async def get_user_by_email(
        self, email: str, use_cache: bool = True
    ) -> Optional[PlatformUser]:
        """Get user by email address"""
        query = (
            select(PlatformUserDB)
            .options(selectinload(PlatformUserDB.school_memberships))
            .where(PlatformUserDB.email == email.lower())
        )

        result = await self.db.execute(query)
        user_db = result.scalar_one_or_none()

        if not user_db:
            return None

        user = await self._convert_db_to_pydantic(user_db)

        # Cache by user ID if using cache
        if use_cache and user:
            await self.cache.set_user_context(user.id, {"user": user.dict()})

        return user

    async def get_user_by_clerk_id(
        self, clerk_id: str, use_cache: bool = True
    ) -> Optional[PlatformUser]:
        """Get user by Clerk user ID"""
        if use_cache:
            # Check cache first
            cached_user_id = await self.cache.get_user_by_clerk_id(clerk_id)
            if cached_user_id:
                return await self.get_user_by_id(cached_user_id, use_cache=True)

        # Query database
        query = (
            select(PlatformUserDB)
            .options(selectinload(PlatformUserDB.school_memberships))
            .where(PlatformUserDB.clerk_integration["clerk_user_id"].astext == clerk_id)
        )

        result = await self.db.execute(query)
        user_db = result.scalar_one_or_none()

        if not user_db:
            return None

        user = await self._convert_db_to_pydantic(user_db)

        # Cache both the user and the Clerk ID mapping
        if use_cache and user:
            await self.cache.set_user_context(user.id, {"user": user.dict()})
            await self.cache.set_user_by_clerk_id(clerk_id, user.id)

        return user

    # High-Performance Context Methods

    async def get_minimal_user_context(
        self, user_id: UUID, school_id: Optional[UUID] = None, use_cache: bool = True
    ) -> Optional[MinimalUserContext]:
        """
        Get minimal user context for performance-critical operations
        Only loads essential data, not full user profile
        """
        if use_cache:
            cached = await self.cache.get_minimal_context(user_id, school_id)
            if cached:
                try:
                    return MinimalUserContext(**cached)
                except Exception as e:
                    self.logger.warning(
                        f"Error parsing cached minimal context {user_id}: {e}"
                    )

        # Minimal query - only essential fields
        if school_id:
            # Include school membership info
            query = (
                select(
                    PlatformUserDB.id,
                    PlatformUserDB.email,
                    PlatformUserDB.first_name,
                    PlatformUserDB.last_name,
                    PlatformUserDB.platform_role,
                    PlatformUserDB.status,
                    SchoolMembershipDB.role.label("school_role"),
                    SchoolMembershipDB.permissions,
                )
                .join(
                    SchoolMembershipDB, PlatformUserDB.id == SchoolMembershipDB.user_id
                )
                .where(
                    and_(
                        PlatformUserDB.id == user_id,
                        SchoolMembershipDB.school_id == school_id,
                        SchoolMembershipDB.status == UserStatus.ACTIVE.value,
                    )
                )
            )
        else:
            # Just user data
            query = select(
                PlatformUserDB.id,
                PlatformUserDB.email,
                PlatformUserDB.first_name,
                PlatformUserDB.last_name,
                PlatformUserDB.platform_role,
                PlatformUserDB.status,
            ).where(PlatformUserDB.id == user_id)

        result = await self.db.execute(query)
        row = result.first()

        if not row:
            return None

        context = MinimalUserContext(
            user_id=row.id,
            email=row.email,
            full_name=f"{row.first_name} {row.last_name}",
            platform_role=PlatformRole(row.platform_role),
            school_role=(
                SchoolRole(row.school_role)
                if hasattr(row, "school_role") and row.school_role
                else None
            ),
            school_id=school_id,
            permissions=(
                row.permissions
                if hasattr(row, "permissions") and row.permissions
                else []
            ),
            is_active=row.status == UserStatus.ACTIVE.value,
        )

        # Cache for shorter time (2 minutes for minimal context)
        if use_cache:
            await self.cache.set_minimal_context(user_id, context.__dict__, school_id)

        return context

    # Bulk Operations for Performance

    async def bulk_get_school_users(
        self,
        school_id: UUID,
        roles: Optional[List[SchoolRole]] = None,
        limit: int = 100,
        offset: int = 0,
        use_cache: bool = True,
    ) -> List[UserSummary]:
        """
        Efficiently get multiple users for a school with pagination
        Returns summary objects, not full user profiles
        """
        if use_cache:
            cached_users = await self.cache.get_school_users_summary(
                school_id, [r.value for r in roles] if roles else None, limit, offset
            )
            if cached_users:
                try:
                    return [UserSummary(**user) for user in cached_users]
                except Exception as e:
                    self.logger.warning(
                        f"Error parsing cached school users {school_id}: {e}"
                    )

        # Efficient query with specific fields only
        query = (
            select(
                PlatformUserDB.id,
                PlatformUserDB.email,
                PlatformUserDB.first_name,
                PlatformUserDB.last_name,
                PlatformUserDB.platform_role,
                PlatformUserDB.status,
                SchoolMembershipDB.role,
                SchoolMembershipDB.joined_date,
                PlatformUserDB.profile["phone_number"].astext.label("phone_number"),
                PlatformUserDB.profile["profile_image_url"].astext.label(
                    "profile_image_url"
                ),
            )
            .join(SchoolMembershipDB, PlatformUserDB.id == SchoolMembershipDB.user_id)
            .where(
                and_(
                    SchoolMembershipDB.school_id == school_id,
                    SchoolMembershipDB.status == UserStatus.ACTIVE.value,
                )
            )
            .limit(limit)
            .offset(offset)
        )

        if roles:
            role_values = [role.value for role in roles]
            query = query.where(SchoolMembershipDB.role.in_(role_values))

        result = await self.db.execute(query)
        users = []

        for row in result:
            user_summary = UserSummary(
                id=row.id,
                email=row.email,
                full_name=f"{row.first_name} {row.last_name}",
                platform_role=PlatformRole(row.platform_role),
                school_role=SchoolRole(row.role),
                joined_date=row.joined_date,
                phone_number=row.phone_number,
                profile_image_url=row.profile_image_url,
                status=UserStatus(row.status),
            )
            users.append(user_summary)

        # Cache for 5 minutes
        if use_cache:
            users_dict = [user.__dict__ for user in users]
            await self.cache.set_school_users_summary(
                school_id,
                users_dict,
                [r.value for r in roles] if roles else None,
                limit,
                offset,
            )

        return users

    async def get_school_user_count(
        self, school_id: UUID, role: Optional[SchoolRole] = None
    ) -> int:
        """Get count of users in a school, optionally filtered by role"""
        query = select(func.count(distinct(SchoolMembershipDB.user_id))).where(
            and_(
                SchoolMembershipDB.school_id == school_id,
                SchoolMembershipDB.status == UserStatus.ACTIVE.value,
            )
        )

        if role:
            query = query.where(SchoolMembershipDB.role == role.value)

        result = await self.db.execute(query)
        return result.scalar() or 0

    # School Operations

    async def get_user_schools(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Get all schools a user belongs to"""
        query = select(SchoolMembershipDB).where(
            and_(
                SchoolMembershipDB.user_id == user_id,
                SchoolMembershipDB.status == UserStatus.ACTIVE.value,
            )
        )

        result = await self.db.execute(query)
        memberships = result.scalars().all()

        return [
            {
                "school_id": membership.school_id,
                "school_name": membership.school_name,
                "school_subdomain": membership.school_subdomain,
                "role": membership.role,
                "joined_date": membership.joined_date,
                "permissions": membership.permissions or [],
            }
            for membership in memberships
        ]

    async def check_user_school_access(self, user_id: UUID, school_id: UUID) -> bool:
        """Check if user has access to a specific school"""
        # Check cache first
        cached_permissions = await self.cache.get_user_permissions(user_id, school_id)
        if cached_permissions is not None:
            return len(cached_permissions) > 0

        query = select(SchoolMembershipDB.id).where(
            and_(
                SchoolMembershipDB.user_id == user_id,
                SchoolMembershipDB.school_id == school_id,
                SchoolMembershipDB.status == UserStatus.ACTIVE.value,
            )
        )

        result = await self.db.execute(query)
        has_access = result.scalar() is not None

        # Cache the result
        if has_access:
            membership_query = select(SchoolMembershipDB.permissions).where(
                and_(
                    SchoolMembershipDB.user_id == user_id,
                    SchoolMembershipDB.school_id == school_id,
                    SchoolMembershipDB.status == UserStatus.ACTIVE.value,
                )
            )
            result = await self.db.execute(membership_query)
            permissions = result.scalar() or []
            await self.cache.set_user_permissions(user_id, school_id, permissions)

        return has_access

    # Search and Filter Operations

    async def search_users(
        self,
        query_text: str,
        school_id: Optional[UUID] = None,
        roles: Optional[List[SchoolRole]] = None,
        limit: int = 50,
    ) -> List[UserSummary]:
        """Search users by name or email"""
        search_pattern = f"%{query_text.lower()}%"

        if school_id:
            # Search within school
            query = (
                select(
                    PlatformUserDB.id,
                    PlatformUserDB.email,
                    PlatformUserDB.first_name,
                    PlatformUserDB.last_name,
                    PlatformUserDB.platform_role,
                    PlatformUserDB.status,
                    SchoolMembershipDB.role,
                    SchoolMembershipDB.joined_date,
                )
                .join(
                    SchoolMembershipDB, PlatformUserDB.id == SchoolMembershipDB.user_id
                )
                .where(
                    and_(
                        SchoolMembershipDB.school_id == school_id,
                        SchoolMembershipDB.status == UserStatus.ACTIVE.value,
                        or_(
                            func.lower(PlatformUserDB.first_name).like(search_pattern),
                            func.lower(PlatformUserDB.last_name).like(search_pattern),
                            func.lower(PlatformUserDB.email).like(search_pattern),
                        ),
                    )
                )
            )

            if roles:
                role_values = [role.value for role in roles]
                query = query.where(SchoolMembershipDB.role.in_(role_values))
        else:
            # Search platform-wide
            query = select(
                PlatformUserDB.id,
                PlatformUserDB.email,
                PlatformUserDB.first_name,
                PlatformUserDB.last_name,
                PlatformUserDB.platform_role,
                PlatformUserDB.status,
                PlatformUserDB.created_at,
            ).where(
                and_(
                    PlatformUserDB.status == UserStatus.ACTIVE.value,
                    or_(
                        func.lower(PlatformUserDB.first_name).like(search_pattern),
                        func.lower(PlatformUserDB.last_name).like(search_pattern),
                        func.lower(PlatformUserDB.email).like(search_pattern),
                    ),
                )
            )

        query = query.limit(limit)
        result = await self.db.execute(query)

        users = []
        for row in result:
            user_summary = UserSummary(
                id=row.id,
                email=row.email,
                full_name=f"{row.first_name} {row.last_name}",
                platform_role=PlatformRole(row.platform_role),
                school_role=(
                    SchoolRole(row.role) if hasattr(row, "role") and row.role else None
                ),
                joined_date=(
                    row.joined_date if hasattr(row, "joined_date") else row.created_at
                ),
                status=UserStatus(row.status),
            )
            users.append(user_summary)

        return users

    # Helper Methods

    async def _convert_db_to_pydantic(self, user_db: PlatformUserDB) -> PlatformUser:
        """Convert SQLAlchemy model to Pydantic model"""
        # Parse JSON fields
        profile = None
        if user_db.profile:
            profile = UserProfile.parse_obj(user_db.profile)

        clerk_integration = None
        if user_db.clerk_integration:
            clerk_integration = ClerkIntegration.parse_obj(user_db.clerk_integration)

        # Convert school memberships
        school_memberships = []
        for membership_db in user_db.school_memberships:
            membership = SchoolMembership(
                school_id=membership_db.school_id,
                school_name=membership_db.school_name,
                school_subdomain=membership_db.school_subdomain,
                role=SchoolRole(membership_db.role),
                permissions=membership_db.permissions or [],
                joined_date=membership_db.joined_date,
                status=UserStatus(membership_db.status),
                student_id=membership_db.student_id,
                current_grade=membership_db.current_grade,
                admission_date=membership_db.admission_date,
                graduation_date=membership_db.graduation_date,
                employee_id=membership_db.employee_id,
                department=membership_db.department,
                hire_date=membership_db.hire_date,
                contract_type=membership_db.contract_type,
                children_ids=membership_db.children_ids or [],
            )
            school_memberships.append(membership)

        return PlatformUser(
            id=user_db.id,
            email=user_db.email,
            first_name=user_db.first_name,
            last_name=user_db.last_name,
            platform_role=PlatformRole(user_db.platform_role),
            status=UserStatus(user_db.status),
            school_memberships=school_memberships,
            primary_school_id=user_db.primary_school_id,
            profile=profile,
            clerk_integration=clerk_integration,
            created_at=user_db.created_at,
            updated_at=user_db.updated_at,
            last_login=user_db.last_login,
            feature_flags=user_db.feature_flags or {},
            user_preferences=user_db.user_preferences or {},
        )

    # Cache Management

    async def invalidate_user_cache(self, user_id: UUID) -> None:
        """Invalidate all cache entries for a user"""
        await self.cache.invalidate_user_all(user_id)

    async def invalidate_school_cache(self, school_id: UUID) -> None:
        """Invalidate all cache entries for a school"""
        await self.cache.invalidate_school_all(school_id)

    async def warm_user_cache(self, user_id: UUID) -> None:
        """Pre-warm cache for a user"""
        user = await self.get_user_by_id(user_id, use_cache=False)
        if user:
            await self.cache.set_user_context(user_id, {"user": user.dict()})

    # Health and Performance Monitoring

    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for monitoring"""
        cache_stats = await self.cache.get_cache_stats()
        cache_health = await self.cache.health_check()

        return {
            "cache_stats": cache_stats,
            "cache_health": cache_health,
            "timestamp": datetime.utcnow().isoformat(),
        }
