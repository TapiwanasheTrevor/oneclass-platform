# 1Class User System: Migration & Performance Solutions
# Addressing Migration Complexity & Performance Concerns

from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID
import asyncio
from functools import lru_cache
import redis
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload, joinedload

# ============================================================================
# PERFORMANCE OPTIMIZATIONS
# ============================================================================

class UserContextCache:
    """Redis-based caching for user context to avoid repeated database queries"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.cache_ttl = 300  # 5 minutes
        self.school_cache_ttl = 900  # 15 minutes for school data
    
    def _get_user_cache_key(self, user_id: UUID) -> str:
        return f"user_context:{user_id}"
    
    def _get_school_cache_key(self, school_id: UUID) -> str:
        return f"school_info:{school_id}"
    
    async def get_user_context(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get cached user context"""
        cache_key = self._get_user_cache_key(user_id)
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        return None
    
    async def set_user_context(self, user_id: UUID, context: Dict[str, Any]):
        """Cache user context"""
        cache_key = self._get_user_cache_key(user_id)
        await self.redis.setex(
            cache_key, 
            self.cache_ttl, 
            json.dumps(context, default=str)
        )
    
    async def invalidate_user_context(self, user_id: UUID):
        """Invalidate user context cache"""
        cache_key = self._get_user_cache_key(user_id)
        await self.redis.delete(cache_key)
    
    async def get_school_info(self, school_id: UUID) -> Optional[Dict[str, Any]]:
        """Get cached school information"""
        cache_key = self._get_school_cache_key(school_id)
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        return None
    
    async def set_school_info(self, school_id: UUID, school_info: Dict[str, Any]):
        """Cache school information"""
        cache_key = self._get_school_cache_key(school_id)
        await self.redis.setex(
            cache_key,
            self.school_cache_ttl,
            json.dumps(school_info, default=str)
        )

class OptimizedUserService:
    """Performance-optimized user service with caching and efficient queries"""
    
    def __init__(self, db_session, cache: UserContextCache):
        self.db = db_session
        self.cache = cache
    
    async def get_user_with_schools(self, user_id: UUID) -> Optional['PlatformUser']:
        """
        Get user with all school memberships in a single optimized query
        Uses eager loading to avoid N+1 query problems
        """
        
        # Try cache first
        cached_context = await self.cache.get_user_context(user_id)
        if cached_context:
            return PlatformUser.parse_obj(cached_context['user'])
        
        # Single query with eager loading
        query = (
            select(PlatformUser)
            .options(
                selectinload(PlatformUser.school_memberships),
                joinedload(PlatformUser.profile)
            )
            .where(PlatformUser.id == user_id)
        )
        
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            # Cache the result
            user_dict = user.dict()
            await self.cache.set_user_context(user_id, {'user': user_dict})
        
        return user
    
    async def get_minimal_user_context(
        self, 
        user_id: UUID, 
        school_id: Optional[UUID] = None
    ) -> Optional['MinimalUserContext']:
        """
        Get minimal user context for performance-critical operations
        Only loads essential data, not full user profile
        """
        
        cache_key = f"minimal_context:{user_id}:{school_id or 'none'}"
        cached = await self.cache.redis.get(cache_key)
        
        if cached:
            return MinimalUserContext.parse_raw(cached)
        
        # Minimal query - only essential fields
        query = (
            select(
                PlatformUser.id,
                PlatformUser.email,
                PlatformUser.first_name,
                PlatformUser.last_name,
                PlatformUser.platform_role,
                PlatformUser.status
            )
            .where(PlatformUser.id == user_id)
        )
        
        if school_id:
            # Add school membership info
            query = query.join(SchoolMembership).add_columns(
                SchoolMembership.school_id,
                SchoolMembership.role,
                SchoolMembership.permissions
            ).where(SchoolMembership.school_id == school_id)
        
        result = await self.db.execute(query)
        row = result.first()
        
        if row:
            context = MinimalUserContext(
                user_id=row.id,
                email=row.email,
                full_name=f"{row.first_name} {row.last_name}",
                platform_role=row.platform_role,
                school_role=getattr(row, 'role', None),
                school_id=school_id,
                permissions=getattr(row, 'permissions', [])
            )
            
            # Cache for 2 minutes (shorter for minimal context)
            await self.cache.redis.setex(cache_key, 120, context.json())
            return context
        
        return None
    
    async def bulk_get_school_users(
        self, 
        school_id: UUID, 
        roles: Optional[List[SchoolRole]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List['UserSummary']:
        """
        Efficiently get multiple users for a school with pagination
        Returns summary objects, not full user profiles
        """
        
        cache_key = f"school_users:{school_id}:{':'.join(roles or [])}:{limit}:{offset}"
        cached = await self.cache.redis.get(cache_key)
        
        if cached:
            return [UserSummary.parse_obj(user) for user in json.loads(cached)]
        
        # Efficient query with specific fields only
        query = (
            select(
                PlatformUser.id,
                PlatformUser.email,
                PlatformUser.first_name,
                PlatformUser.last_name,
                PlatformUser.status,
                SchoolMembership.role,
                SchoolMembership.joined_date,
                UserProfile.phone_number,
                UserProfile.profile_image_url
            )
            .join(SchoolMembership)
            .join(UserProfile, isouter=True)
            .where(
                and_(
                    SchoolMembership.school_id == school_id,
                    SchoolMembership.status == UserStatus.ACTIVE
                )
            )
            .limit(limit)
            .offset(offset)
        )
        
        if roles:
            query = query.where(SchoolMembership.role.in_(roles))
        
        result = await self.db.execute(query)
        users = []
        
        for row in result:
            user_summary = UserSummary(
                id=row.id,
                email=row.email,
                full_name=f"{row.first_name} {row.last_name}",
                school_role=row.role,
                joined_date=row.joined_date,
                phone_number=row.phone_number,
                profile_image_url=row.profile_image_url
            )
            users.append(user_summary)
        
        # Cache for 5 minutes
        users_dict = [user.dict() for user in users]
        await self.cache.redis.setex(cache_key, 300, json.dumps(users_dict, default=str))
        
        return users

class MinimalUserContext(BaseModel):
    """Lightweight user context for performance-critical operations"""
    user_id: UUID
    email: str
    full_name: str
    platform_role: PlatformRole
    school_role: Optional[SchoolRole] = None
    school_id: Optional[UUID] = None
    permissions: List[str] = []

class UserSummary(BaseModel):
    """Summary view of user for lists and bulk operations"""
    id: UUID
    email: str
    full_name: str
    school_role: SchoolRole
    joined_date: datetime
    phone_number: Optional[str] = None
    profile_image_url: Optional[str] = None

# ============================================================================
# MIGRATION STRATEGY - ZERO DOWNTIME
# ============================================================================

class UserMigrationService:
    """Handles migration from old user models to new consolidated model"""
    
    def __init__(self, db_session, cache: UserContextCache):
        self.db = db_session
        self.cache = cache
        self.batch_size = 100
    
    async def analyze_existing_data(self) -> Dict[str, Any]:
        """Analyze existing user data to plan migration"""
        
        analysis = {
            "legacy_users_count": 0,
            "enhanced_users_count": 0,
            "duplicate_emails": [],
            "missing_data": [],
            "school_assignments": {},
            "data_quality_issues": []
        }
        
        # Count legacy users
        legacy_count_query = select(func.count(LegacyUser.id))
        result = await self.db.execute(legacy_count_query)
        analysis["legacy_users_count"] = result.scalar()
        
        # Count enhanced users
        enhanced_count_query = select(func.count(EnhancedUser.id))
        result = await self.db.execute(enhanced_count_query)
        analysis["enhanced_users_count"] = result.scalar()
        
        # Find duplicate emails
        duplicate_emails_query = (
            select(LegacyUser.email, func.count(LegacyUser.email))
            .group_by(LegacyUser.email)
            .having(func.count(LegacyUser.email) > 1)
        )
        result = await self.db.execute(duplicate_emails_query)
        analysis["duplicate_emails"] = [row.email for row in result]
        
        # Analyze school assignments
        school_assignments_query = (
            select(EnhancedUser.school_id, func.count(EnhancedUser.user_id))
            .group_by(EnhancedUser.school_id)
        )
        result = await self.db.execute(school_assignments_query)
        analysis["school_assignments"] = {
            str(row.school_id): row.count for row in result
        }
        
        return analysis
    
    async def create_migration_plan(self) -> Dict[str, Any]:
        """Create detailed migration execution plan"""
        
        analysis = await self.analyze_existing_data()
        
        plan = {
            "total_users": analysis["legacy_users_count"],
            "batches": math.ceil(analysis["legacy_users_count"] / self.batch_size),
            "estimated_duration_minutes": math.ceil(analysis["legacy_users_count"] / 50),  # ~50 users/minute
            "pre_migration_steps": [
                "Create backup of existing user tables",
                "Validate data integrity",
                "Create new PlatformUser table",
                "Setup migration tracking table"
            ],
            "migration_steps": [
                "Migrate users in batches",
                "Create school memberships",
                "Validate migrated data",
                "Update foreign key references"
            ],
            "post_migration_steps": [
                "Run data validation queries",
                "Update application code",
                "Clear all caches",
                "Monitor for issues"
            ],
            "rollback_plan": [
                "Restore from backup",
                "Revert application code",
                "Clear caches"
            ]
        }
        
        return plan
    
    async def migrate_users_batch(self, batch_number: int) -> Dict[str, Any]:
        """Migrate a batch of users"""
        
        offset = batch_number * self.batch_size
        
        # Get batch of legacy users with their enhanced data
        query = (
            select(LegacyUser)
            .outerjoin(EnhancedUser, LegacyUser.id == EnhancedUser.user_id)
            .limit(self.batch_size)
            .offset(offset)
        )
        
        result = await self.db.execute(query)
        legacy_users = result.scalars().all()
        
        migrated_count = 0
        errors = []
        
        for legacy_user in legacy_users:
            try:
                # Create new consolidated user
                new_user = await self._convert_legacy_user(legacy_user)
                
                # Save to database
                self.db.add(new_user)
                await self.db.flush()  # Get the ID without committing
                
                # Track migration
                migration_record = MigrationTracking(
                    legacy_user_id=legacy_user.id,
                    new_user_id=new_user.id,
                    migrated_at=datetime.utcnow(),
                    batch_number=batch_number
                )
                self.db.add(migration_record)
                
                migrated_count += 1
                
            except Exception as e:
                errors.append({
                    "user_id": legacy_user.id,
                    "email": legacy_user.email,
                    "error": str(e)
                })
        
        # Commit the batch
        await self.db.commit()
        
        return {
            "batch_number": batch_number,
            "migrated_count": migrated_count,
            "errors": errors,
            "success_rate": migrated_count / len(legacy_users) if legacy_users else 0
        }
    
    async def _convert_legacy_user(self, legacy_user) -> PlatformUser:
        """Convert legacy user to new PlatformUser model"""
        
        # Get enhanced user data if it exists
        enhanced_query = (
            select(EnhancedUser)
            .where(EnhancedUser.user_id == legacy_user.id)
        )
        result = await self.db.execute(enhanced_query)
        enhanced_user = result.scalar_one_or_none()
        
        # Create profile
        profile = UserProfile()
        if enhanced_user:
            profile.phone_number = enhanced_user.phone_number
            profile.profile_image_url = enhanced_user.profile_image_url
            # ... map other enhanced fields
        
        # Create new user
        new_user = PlatformUser(
            id=legacy_user.id,  # Keep same ID for referential integrity
            email=legacy_user.email,
            first_name=legacy_user.first_name,
            last_name=legacy_user.last_name,
            platform_role=PlatformRole(legacy_user.role),
            status=UserStatus(legacy_user.status),
            created_at=legacy_user.created_at,
            profile=profile
        )
        
        # Add school membership if enhanced user has school context
        if enhanced_user and enhanced_user.school_id:
            school_membership = SchoolMembership(
                school_id=enhanced_user.school_id,
                school_name=enhanced_user.school_name,
                school_subdomain=enhanced_user.school_subdomain,
                role=SchoolRole(enhanced_user.school_role),
                joined_date=enhanced_user.created_at,
                permissions=enhanced_user.permissions or []
            )
            new_user.school_memberships.append(school_membership)
            new_user.primary_school_id = enhanced_user.school_id
        
        return new_user
    
    async def run_full_migration(self) -> Dict[str, Any]:
        """Execute complete migration process"""
        
        start_time = datetime.utcnow()
        
        # Create migration plan
        plan = await self.create_migration_plan()
        
        # Execute migration in batches
        results = []
        total_migrated = 0
        total_errors = 0
        
        for batch_num in range(plan["batches"]):
            print(f"Migrating batch {batch_num + 1}/{plan['batches']}...")
            
            batch_result = await self.migrate_users_batch(batch_num)
            results.append(batch_result)
            
            total_migrated += batch_result["migrated_count"]
            total_errors += len(batch_result["errors"])
            
            # Brief pause between batches to avoid overwhelming the database
            await asyncio.sleep(0.1)
        
        # Validation phase
        validation_result = await self._validate_migration()
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        return {
            "migration_completed": True,
            "start_time": start_time,
            "end_time": end_time,
            "duration_seconds": duration,
            "total_users_migrated": total_migrated,
            "total_errors": total_errors,
            "success_rate": total_migrated / (total_migrated + total_errors) if (total_migrated + total_errors) > 0 else 0,
            "batch_results": results,
            "validation": validation_result
        }
    
    async def _validate_migration(self) -> Dict[str, Any]:
        """Validate migration completed successfully"""
        
        # Count migrated users
        new_users_count_query = select(func.count(PlatformUser.id))
        result = await self.db.execute(new_users_count_query)
        new_users_count = result.scalar()
        
        # Count original users
        legacy_users_count_query = select(func.count(LegacyUser.id))
        result = await self.db.execute(legacy_users_count_query)
        legacy_users_count = result.scalar()
        
        # Check for data integrity issues
        integrity_issues = []
        
        # Check for missing school memberships
        missing_memberships_query = (
            select(PlatformUser.id)
            .outerjoin(SchoolMembership, PlatformUser.id == SchoolMembership.user_id)
            .where(
                and_(
                    PlatformUser.primary_school_id.isnot(None),
                    SchoolMembership.user_id.is_(None)
                )
            )
        )
        result = await self.db.execute(missing_memberships_query)
        missing_memberships = result.scalars().all()
        
        if missing_memberships:
            integrity_issues.append(f"Users with primary_school_id but no membership: {len(missing_memberships)}")
        
        return {
            "new_users_count": new_users_count,
            "legacy_users_count": legacy_users_count,
            "count_match": new_users_count == legacy_users_count,
            "integrity_issues": integrity_issues,
            "validation_passed": len(integrity_issues) == 0 and new_users_count == legacy_users_count
        }

# ============================================================================
# OPTIMIZED MIDDLEWARE
# ============================================================================

class FastUserContextMiddleware:
    """High-performance middleware for user context resolution"""
    
    def __init__(self, cache: UserContextCache, user_service: OptimizedUserService):
        self.cache = cache
        self.user_service = user_service
    
    async def get_user_context(
        self, 
        clerk_session_id: str, 
        subdomain: Optional[str] = None,
        minimal: bool = False
    ) -> Optional[UserContext]:
        """
        Get user context with performance optimizations
        
        Args:
            clerk_session_id: Clerk session identifier
            subdomain: School subdomain for context
            minimal: If True, returns lightweight context for better performance
        """
        
        # Step 1: Validate Clerk session (cached)
        clerk_user = await self._get_cached_clerk_user(clerk_session_id)
        if not clerk_user:
            return None
        
        # Step 2: Get platform user ID from Clerk ID (cached)
        user_id = await self._get_user_id_by_clerk_id(clerk_user["id"])
        if not user_id:
            return None
        
        # Step 3: Return minimal context for performance-critical operations
        if minimal:
            minimal_context = await self.user_service.get_minimal_user_context(
                user_id, 
                await self._get_school_id_by_subdomain(subdomain) if subdomain else None
            )
            return minimal_context
        
        # Step 4: Get full user context (cached)
        return await self._get_full_user_context(user_id, subdomain)
    
    @lru_cache(maxsize=1000)
    async def _get_cached_clerk_user(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Cache Clerk user validation for 5 minutes"""
        # Implementation would validate with Clerk API
        pass
    
    async def _get_user_id_by_clerk_id(self, clerk_id: str) -> Optional[UUID]:
        """Get platform user ID from Clerk ID with caching"""
        cache_key = f"clerk_to_user:{clerk_id}"
        cached_id = await self.cache.redis.get(cache_key)
        
        if cached_id:
            return UUID(cached_id)
        
        # Query database
        query = select(PlatformUser.id).where(
            PlatformUser.clerk_integration['clerk_user_id'].astext == clerk_id
        )
        result = await self.user_service.db.execute(query)
        user_id = result.scalar_one_or_none()
        
        if user_id:
            # Cache for 10 minutes
            await self.cache.redis.setex(cache_key, 600, str(user_id))
        
        return user_id
    
    async def _get_school_id_by_subdomain(self, subdomain: str) -> Optional[UUID]:
        """Get school ID from subdomain with caching"""
        cache_key = f"subdomain_to_school:{subdomain}"
        cached_id = await self.cache.redis.get(cache_key)
        
        if cached_id:
            return UUID(cached_id)
        
        # Query database
        query = select(School.id).where(School.subdomain == subdomain)
        result = await self.user_service.db.execute(query)
        school_id = result.scalar_one_or_none()
        
        if school_id:
            # Cache for 30 minutes (subdomains rarely change)
            await self.cache.redis.setex(cache_key, 1800, str(school_id))
        
        return school_id

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

# Example: High-performance user context resolution
async def get_current_user_fast(request: Request):
    """Fast user context resolution for API endpoints"""
    
    subdomain = extract_subdomain(request)
    session_id = extract_clerk_session(request)
    
    # Use minimal context for better performance
    context = await fast_middleware.get_user_context(
        session_id, 
        subdomain, 
        minimal=True  # Only load essential data
    )
    
    return context

# Example: Efficient bulk operations
async def get_school_teachers(school_id: UUID):
    """Efficiently get all teachers for a school"""
    
    teachers = await optimized_user_service.bulk_get_school_users(
        school_id=school_id,
        roles=[SchoolRole.TEACHER, SchoolRole.ACADEMIC_HEAD],
        limit=100
    )
    
    return teachers

# Example: Migration execution
async def run_migration():
    """Execute user migration with progress tracking"""
    
    migration_service = UserMigrationService(db_session, cache)
    
    # Analyze current data
    analysis = await migration_service.analyze_existing_data()
    print(f"Migration analysis: {analysis}")
    
    # Create migration plan
    plan = await migration_service.create_migration_plan()
    print(f"Migration plan: {plan}")
    
    # Execute migration
    result = await migration_service.run_full_migration()
    print(f"Migration completed: {result}")
    
    return result