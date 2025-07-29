# =====================================================
# User Management Service
# Complete business logic for user CRUD operations
# File: backend/services/users/services.py
# =====================================================

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text, delete, update
from sqlalchemy.orm import selectinload, joinedload
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import logging
import json

from shared.models.platform_user import (
    PlatformUserDB, SchoolMembershipDB, UserSessionDB,
    PlatformRole, SchoolRole, UserStatus
)
from shared.models.platform import School
from services.auth.utils import hash_password, generate_secure_token
from .schemas import (
    UserCreateRequest, UserUpdateRequest, UserSearchRequest, UserResponse,
    UserListItem, UserStatistics, UserBulkOperationRequest, BulkOperation,
    UserProfileUpdateRequest, SchoolMembershipUpdateRequest, UserFilterBy
)

logger = logging.getLogger(__name__)

class UserManagementService:
    """Service for comprehensive user management operations"""
    
    def __init__(self):
        self.default_permissions = {
            SchoolRole.PRINCIPAL: ['*'],
            SchoolRole.DEPUTY_PRINCIPAL: [
                'users.manage', 'academics.manage', 'reports.view', 
                'finance.view', 'settings.manage'
            ],
            SchoolRole.TEACHER: [
                'students.view', 'academics.view', 'attendance.manage',
                'grades.manage', 'communication.send'
            ],
            SchoolRole.STUDENT: [
                'academics.view', 'assignments.submit', 'resources.access',
                'grades.view', 'events.view'
            ],
            SchoolRole.PARENT: [
                'students.view', 'payments.view', 'communication.receive',
                'reports.view', 'events.view'
            ]
        }
    
    async def create_user(
        self,
        db: AsyncSession,
        user_data: UserCreateRequest,
        created_by: UUID
    ) -> PlatformUserDB:
        """Create a new user with optional school memberships"""
        
        try:
            # Check if email already exists
            existing_query = select(PlatformUserDB).where(
                PlatformUserDB.email == user_data.email.lower()
            )
            existing_result = await db.execute(existing_query)
            existing_user = existing_result.scalar_one_or_none()
            
            if existing_user:
                raise ValueError(f"User with email {user_data.email} already exists")
            
            # Create profile data
            profile_data = {
                "phone_number": user_data.phone,
                "date_of_birth": user_data.date_of_birth.isoformat() if user_data.date_of_birth else None,
                "gender": user_data.gender,
                "address": user_data.address,
                "emergency_contact_name": user_data.emergency_contact_name,
                "emergency_contact_phone": user_data.emergency_contact_phone,
                "preferred_language": "en",
                "timezone": "Africa/Harare",
                "notification_preferences": {
                    "email_notifications": True,
                    "sms_notifications": True,
                    "push_notifications": True,
                    "marketing_emails": False
                }
            }
            
            # Create user
            user = PlatformUserDB(
                id=uuid4(),
                email=user_data.email.lower(),
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                platform_role=user_data.platform_role.value,
                status=UserStatus.ACTIVE.value,
                primary_school_id=user_data.primary_school_id,
                profile=profile_data,
                feature_flags={},
                user_preferences={},
                created_at=datetime.utcnow()
            )
            
            db.add(user)
            await db.flush()  # Get user ID
            
            # Create school memberships
            for membership_data in user_data.school_memberships:
                membership = SchoolMembershipDB(
                    id=uuid4(),
                    user_id=user.id,
                    school_id=UUID(membership_data['school_id']),
                    school_name=membership_data.get('school_name', ''),
                    school_subdomain=membership_data.get('school_subdomain', ''),
                    role=membership_data['role'],
                    permissions=self.default_permissions.get(
                        SchoolRole(membership_data['role']), []
                    ),
                    status=UserStatus.ACTIVE.value,
                    joined_date=datetime.utcnow(),
                    department=membership_data.get('department'),
                    employee_id=membership_data.get('employee_id'),
                    student_id=membership_data.get('student_id'),
                    current_grade=membership_data.get('current_grade')
                )
                db.add(membership)
            
            await db.commit()
            
            # Log user creation
            await self._log_user_action(
                db, user.id, "user_created", 
                f"User created by {created_by}", created_by
            )
            
            logger.info(f"User created: {user.email} by {created_by}")
            return user
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    async def get_user_by_id(
        self,
        db: AsyncSession,
        user_id: UUID,
        include_memberships: bool = True
    ) -> Optional[PlatformUserDB]:
        """Get user by ID with optional school memberships"""
        
        query = select(PlatformUserDB).where(PlatformUserDB.id == user_id)
        
        if include_memberships:
            query = query.options(selectinload(PlatformUserDB.school_memberships))
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_by_email(
        self,
        db: AsyncSession,
        email: str,
        include_memberships: bool = True
    ) -> Optional[PlatformUserDB]:
        """Get user by email with optional school memberships"""
        
        query = select(PlatformUserDB).where(
            PlatformUserDB.email == email.lower()
        )
        
        if include_memberships:
            query = query.options(selectinload(PlatformUserDB.school_memberships))
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        user_data: UserUpdateRequest,
        updated_by: UUID
    ) -> PlatformUserDB:
        """Update user information"""
        
        try:
            # Get existing user
            user = await self.get_user_by_id(db, user_id, include_memberships=False)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Store old values for audit
            old_values = {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "platform_role": user.platform_role,
                "status": user.status,
                "primary_school_id": str(user.primary_school_id) if user.primary_school_id else None
            }
            
            # Update basic fields
            if user_data.first_name is not None:
                user.first_name = user_data.first_name
            if user_data.last_name is not None:
                user.last_name = user_data.last_name
            if user_data.platform_role is not None:
                user.platform_role = user_data.platform_role.value
            if user_data.status is not None:
                user.status = user_data.status.value
            if user_data.primary_school_id is not None:
                user.primary_school_id = user_data.primary_school_id
            
            # Update profile
            if any([
                user_data.phone, user_data.date_of_birth, user_data.gender,
                user_data.address, user_data.emergency_contact_name,
                user_data.emergency_contact_phone, user_data.preferred_language,
                user_data.timezone, user_data.notification_preferences
            ]):
                profile = user.profile or {}
                
                if user_data.phone is not None:
                    profile['phone_number'] = user_data.phone
                if user_data.date_of_birth is not None:
                    profile['date_of_birth'] = user_data.date_of_birth.isoformat()
                if user_data.gender is not None:
                    profile['gender'] = user_data.gender
                if user_data.address is not None:
                    profile['address'] = user_data.address
                if user_data.emergency_contact_name is not None:
                    profile['emergency_contact_name'] = user_data.emergency_contact_name
                if user_data.emergency_contact_phone is not None:
                    profile['emergency_contact_phone'] = user_data.emergency_contact_phone
                if user_data.preferred_language is not None:
                    profile['preferred_language'] = user_data.preferred_language
                if user_data.timezone is not None:
                    profile['timezone'] = user_data.timezone
                if user_data.notification_preferences is not None:
                    profile['notification_preferences'] = user_data.notification_preferences
                
                user.profile = profile
            
            # Update preferences and flags
            if user_data.feature_flags is not None:
                user.feature_flags = user_data.feature_flags
            if user_data.user_preferences is not None:
                user.user_preferences = user_data.user_preferences
            
            user.updated_at = datetime.utcnow()
            
            await db.commit()
            
            # Log user update
            new_values = {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "platform_role": user.platform_role,
                "status": user.status,
                "primary_school_id": str(user.primary_school_id) if user.primary_school_id else None
            }
            
            await self._log_user_action(
                db, user.id, "user_updated",
                f"User updated by {updated_by}",
                updated_by, old_values=old_values, new_values=new_values
            )
            
            logger.info(f"User updated: {user.email} by {updated_by}")
            return user
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating user {user_id}: {str(e)}")
            raise
    
    async def delete_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        deleted_by: UUID,
        permanent: bool = False
    ) -> bool:
        """Delete user (soft delete by default)"""
        
        try:
            user = await self.get_user_by_id(db, user_id, include_memberships=False)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            if permanent:
                # Permanent deletion - remove all data
                # First delete school memberships
                membership_delete = delete(SchoolMembershipDB).where(
                    SchoolMembershipDB.user_id == user_id
                )
                await db.execute(membership_delete)
                
                # Delete user sessions
                session_delete = delete(UserSessionDB).where(
                    UserSessionDB.user_id == user_id
                )
                await db.execute(session_delete)
                
                # Delete user
                user_delete = delete(PlatformUserDB).where(
                    PlatformUserDB.id == user_id
                )
                await db.execute(user_delete)
                
                action = "user_permanently_deleted"
            else:
                # Soft delete - mark as archived
                user.status = UserStatus.ARCHIVED.value
                user.updated_at = datetime.utcnow()
                
                # Deactivate all sessions
                session_update = update(UserSessionDB).where(
                    UserSessionDB.user_id == user_id
                ).values(is_active=False)
                await db.execute(session_update)
                
                action = "user_deleted"
            
            await db.commit()
            
            # Log deletion
            await self._log_user_action(
                db, user_id, action,
                f"User deleted by {deleted_by} (permanent: {permanent})",
                deleted_by
            )
            
            logger.info(f"User deleted: {user.email} by {deleted_by} (permanent: {permanent})")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            raise
    
    async def search_users(
        self,
        db: AsyncSession,
        search_params: UserSearchRequest
    ) -> Tuple[List[PlatformUserDB], int]:
        """Search users with filters and pagination"""
        
        # Base query
        query = select(PlatformUserDB)
        count_query = select(func.count(PlatformUserDB.id))
        
        # Apply filters
        filters = []
        
        # Text search
        if search_params.query:
            search_term = f"%{search_params.query.lower()}%"
            filters.append(
                or_(
                    func.lower(PlatformUserDB.first_name).like(search_term),
                    func.lower(PlatformUserDB.last_name).like(search_term),
                    func.lower(PlatformUserDB.email).like(search_term)
                )
            )
        
        # Platform role filter
        if search_params.platform_role:
            filters.append(PlatformUserDB.platform_role == search_params.platform_role.value)
        
        # Status filter
        if search_params.status != UserFilterBy.ALL:
            status_mapping = {
                UserFilterBy.ACTIVE: UserStatus.ACTIVE.value,
                UserFilterBy.INACTIVE: UserStatus.INACTIVE.value,
                UserFilterBy.PENDING: UserStatus.PENDING_VERIFICATION.value,
                UserFilterBy.SUSPENDED: UserStatus.SUSPENDED.value
            }
            filters.append(PlatformUserDB.status == status_mapping[search_params.status])
        
        # Date filters
        if search_params.created_after:
            filters.append(PlatformUserDB.created_at >= search_params.created_after)
        if search_params.created_before:
            filters.append(PlatformUserDB.created_at <= search_params.created_before)
        if search_params.last_login_after:
            filters.append(PlatformUserDB.last_login >= search_params.last_login_after)
        if search_params.last_login_before:
            filters.append(PlatformUserDB.last_login <= search_params.last_login_before)
        
        # School-specific filters
        if search_params.school_id:
            # Join with school memberships
            query = query.join(SchoolMembershipDB).where(
                SchoolMembershipDB.school_id == search_params.school_id
            )
            count_query = count_query.join(SchoolMembershipDB).where(
                SchoolMembershipDB.school_id == search_params.school_id
            )
            
            if search_params.school_role:
                filters.append(SchoolMembershipDB.role == search_params.school_role.value)
            if search_params.department:
                filters.append(SchoolMembershipDB.department.ilike(f"%{search_params.department}%"))
            if search_params.grade:
                filters.append(SchoolMembershipDB.current_grade.ilike(f"%{search_params.grade}%"))
        
        # Apply all filters
        if filters:
            filter_condition = and_(*filters)
            query = query.where(filter_condition)
            count_query = count_query.where(filter_condition)
        
        # Get total count
        count_result = await db.execute(count_query)
        total_count = count_result.scalar()
        
        # Apply sorting
        sort_column = getattr(PlatformUserDB, search_params.sort_by.value)
        if search_params.sort_desc:
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        query = query.offset(search_params.offset).limit(search_params.limit)
        
        # Execute query
        result = await db.execute(query)
        users = result.scalars().all()
        
        return users, total_count
    
    async def bulk_operation(
        self,
        db: AsyncSession,
        operation_data: UserBulkOperationRequest,
        performed_by: UUID
    ) -> Dict[str, Any]:
        """Perform bulk operations on users"""
        
        try:
            results = {
                'successful': [],
                'failed': [],
                'total_processed': len(operation_data.user_ids)
            }
            
            for user_id in operation_data.user_ids:
                try:
                    user = await self.get_user_by_id(db, user_id, include_memberships=False)
                    if not user:
                        results['failed'].append({
                            'user_id': str(user_id),
                            'error': 'User not found'
                        })
                        continue
                    
                    # Perform operation
                    if operation_data.operation == BulkOperation.ACTIVATE:
                        user.status = UserStatus.ACTIVE.value
                        action = "bulk_activated"
                    
                    elif operation_data.operation == BulkOperation.DEACTIVATE:
                        user.status = UserStatus.INACTIVE.value
                        action = "bulk_deactivated"
                    
                    elif operation_data.operation == BulkOperation.SUSPEND:
                        user.status = UserStatus.SUSPENDED.value
                        action = "bulk_suspended"
                    
                    elif operation_data.operation == BulkOperation.DELETE:
                        user.status = UserStatus.ARCHIVED.value
                        action = "bulk_deleted"
                    
                    elif operation_data.operation == BulkOperation.UPDATE_ROLE:
                        if operation_data.new_role:
                            user.platform_role = operation_data.new_role.value
                            action = "bulk_role_updated"
                        else:
                            results['failed'].append({
                                'user_id': str(user_id),
                                'error': 'New role required for role update'
                            })
                            continue
                    
                    user.updated_at = datetime.utcnow()
                    
                    # Log action
                    await self._log_user_action(
                        db, user.id, action,
                        f"{action} by {performed_by}: {operation_data.reason or 'No reason provided'}",
                        performed_by
                    )
                    
                    results['successful'].append({
                        'user_id': str(user_id),
                        'email': user.email,
                        'operation': operation_data.operation.value
                    })
                    
                except Exception as e:
                    results['failed'].append({
                        'user_id': str(user_id),
                        'error': str(e)
                    })
            
            await db.commit()
            
            logger.info(f"Bulk operation {operation_data.operation} completed by {performed_by}: "
                       f"{len(results['successful'])} successful, {len(results['failed'])} failed")
            
            return results
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error in bulk operation: {str(e)}")
            raise
    
    async def get_user_statistics(
        self,
        db: AsyncSession,
        school_id: Optional[UUID] = None
    ) -> UserStatistics:
        """Get user statistics for dashboard"""
        
        # Base query
        base_query = select(PlatformUserDB)
        
        if school_id:
            base_query = base_query.join(SchoolMembershipDB).where(
                SchoolMembershipDB.school_id == school_id
            )
        
        # Total users
        total_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
        total_users = total_result.scalar()
        
        # Users by status
        status_counts = {}
        for status in UserStatus:
            status_query = base_query.where(PlatformUserDB.status == status.value)
            count_result = await db.execute(select(func.count()).select_from(status_query.subquery()))
            status_counts[status.value] = count_result.scalar()
        
        # Users by role
        role_counts = {}
        for role in PlatformRole:
            role_query = base_query.where(PlatformUserDB.platform_role == role.value)
            count_result = await db.execute(select(func.count()).select_from(role_query.subquery()))
            role_counts[role.value] = count_result.scalar()
        
        # Recent activity
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        new_users_query = base_query.where(PlatformUserDB.created_at >= thirty_days_ago)
        new_users_result = await db.execute(select(func.count()).select_from(new_users_query.subquery()))
        new_users_last_30_days = new_users_result.scalar()
        
        active_users_query = base_query.where(PlatformUserDB.last_login >= seven_days_ago)
        active_users_result = await db.execute(select(func.count()).select_from(active_users_query.subquery()))
        active_users_last_7_days = active_users_result.scalar()
        
        never_logged_in_query = base_query.where(PlatformUserDB.last_login.is_(None))
        never_logged_in_result = await db.execute(select(func.count()).select_from(never_logged_in_query.subquery()))
        users_never_logged_in = never_logged_in_result.scalar()
        
        return UserStatistics(
            total_users=total_users,
            active_users=status_counts.get(UserStatus.ACTIVE.value, 0),
            inactive_users=status_counts.get(UserStatus.INACTIVE.value, 0),
            pending_users=status_counts.get(UserStatus.PENDING_VERIFICATION.value, 0),
            suspended_users=status_counts.get(UserStatus.SUSPENDED.value, 0),
            users_by_role=role_counts,
            users_by_school={},  # TODO: Implement school counts
            new_users_last_30_days=new_users_last_30_days,
            active_users_last_7_days=active_users_last_7_days,
            users_never_logged_in=users_never_logged_in,
            users_with_complete_profiles=0,  # TODO: Implement profile completion logic
            average_profile_completion=0.0
        )
    
    async def _log_user_action(
        self,
        db: AsyncSession,
        user_id: UUID,
        action: str,
        description: str,
        performed_by: UUID,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None
    ):
        """Log user management action for audit trail"""
        
        # TODO: Implement audit logging table
        # For now, just log to application logs
        log_entry = {
            'user_id': str(user_id),
            'action': action,
            'description': description,
            'performed_by': str(performed_by),
            'timestamp': datetime.utcnow().isoformat(),
            'old_values': old_values,
            'new_values': new_values
        }
        
        logger.info(f"User action logged: {json.dumps(log_entry)}")
    
    def _calculate_profile_completion(self, user: PlatformUserDB) -> float:
        """Calculate profile completion percentage"""
        
        if not user.profile:
            return 0.0
        
        total_fields = 10
        completed_fields = 0
        
        profile = user.profile
        
        # Required basic info (already have first_name, last_name, email)
        completed_fields += 3
        
        # Optional profile fields
        if profile.get('phone_number'):
            completed_fields += 1
        if profile.get('date_of_birth'):
            completed_fields += 1
        if profile.get('gender'):
            completed_fields += 1
        if profile.get('address'):
            completed_fields += 1
        if profile.get('emergency_contact_name'):
            completed_fields += 1
        if profile.get('emergency_contact_phone'):
            completed_fields += 1
        if profile.get('profile_image_url'):
            completed_fields += 1
        
        return (completed_fields / total_fields) * 100