"""
Unified User Service
Manages users with multi-school memberships and cross-school functionality
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text, update, delete
from sqlalchemy.orm import selectinload, joinedload
from pydantic import BaseModel, Field, EmailStr, validator

from shared.database import get_async_session
from shared.models.unified_user import (
    UnifiedUser, SchoolMembership, UserSession, SchoolInvitation,
    GlobalRole, SchoolRole, MembershipStatus, UserStatus,
    ContactInformation, PersonalProfile, UserPreferences
)

logger = logging.getLogger(__name__)

# =====================================================
# PYDANTIC MODELS FOR SERVICE
# =====================================================

class UserCreate(BaseModel):
    """Model for creating a new user"""
    
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    password: Optional[str] = Field(None, min_length=8)
    global_role: GlobalRole = GlobalRole.SYSTEM_USER
    
    # Optional profile information
    contact_information: Optional[ContactInformation] = None
    personal_profile: Optional[PersonalProfile] = None
    user_preferences: Optional[UserPreferences] = None
    
    @validator('email')
    def validate_email(cls, v):
        return v.lower().strip()


class SchoolMembershipCreate(BaseModel):
    """Model for creating school membership"""
    
    school_id: UUID
    role: SchoolRole
    
    # Role-specific fields
    employee_id: Optional[str] = None
    student_id: Optional[str] = None
    registration_number: Optional[str] = None
    
    # Academic information
    current_grade: Optional[str] = None
    current_class: Optional[str] = None
    admission_date: Optional[datetime] = None
    
    # Employment information
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: Optional[datetime] = None
    contract_type: Optional[str] = None
    
    # Family relationships
    children_ids: Optional[List[str]] = Field(default_factory=list)
    relationship_type: Optional[str] = None
    
    # Additional data
    permissions: Optional[List[str]] = Field(default_factory=list)
    role_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    membership_notes: Optional[str] = None


class SchoolSwitchRequest(BaseModel):
    """Model for school switching request"""
    
    target_school_id: UUID
    reason: Optional[str] = None


class UserResponse(BaseModel):
    """Response model for user data"""
    
    id: UUID
    email: str
    first_name: str
    last_name: str
    full_name: str
    display_name: Optional[str]
    global_role: str
    status: str
    is_email_verified: bool
    created_at: datetime
    updated_at: datetime
    
    # School memberships
    school_memberships: List[Dict[str, Any]] = Field(default_factory=list)
    active_memberships_count: int = 0
    
    class Config:
        from_attributes = True


# =====================================================
# UNIFIED USER SERVICE
# =====================================================

class UnifiedUserService:
    """Service for managing unified users with multi-school support"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =====================================================
    # USER MANAGEMENT
    # =====================================================
    
    async def create_user(self, user_data: UserCreate) -> UnifiedUser:
        """Create a new unified user"""
        
        try:
            # Check if user already exists
            existing_user = await self._get_user_by_email(user_data.email)
            if existing_user:
                raise ValueError(f"User with email {user_data.email} already exists")
            
            # Create user
            user = UnifiedUser(
                email=user_data.email,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                global_role=user_data.global_role.value,
                status=UserStatus.PENDING_VERIFICATION.value if user_data.password else UserStatus.ACTIVE.value
            )
            
            # Set password if provided
            if user_data.password:
                user.password_hash = self._hash_password(user_data.password)
            
            # Set profile data
            if user_data.contact_information:
                user.contact_information = user_data.contact_information.dict()
            if user_data.personal_profile:
                user.personal_profile = user_data.personal_profile.dict()
            if user_data.user_preferences:
                user.user_preferences = user_data.user_preferences.dict()
            
            self.db.add(user)
            await self.db.flush()
            
            logger.info(f"Created unified user: {user.email} ({user.id})")
            
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating user: {e}")
            raise
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[UnifiedUser]:
        """Get user by ID with school memberships"""
        
        try:
            result = await self.db.execute(
                select(UnifiedUser)
                .options(selectinload(UnifiedUser.school_memberships))
                .where(UnifiedUser.id == user_id)
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[UnifiedUser]:
        """Get user by email with school memberships"""
        
        try:
            result = await self.db.execute(
                select(UnifiedUser)
                .options(selectinload(UnifiedUser.school_memberships))
                .where(UnifiedUser.email == email.lower().strip())
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    async def update_user_profile(
        self, 
        user_id: UUID, 
        profile_data: Dict[str, Any]
    ) -> Optional[UnifiedUser]:
        """Update user profile information"""
        
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return None
            
            # Update basic fields
            for field in ['first_name', 'last_name', 'display_name']:
                if field in profile_data:
                    setattr(user, field, profile_data[field])
            
            # Update JSON fields
            if 'contact_information' in profile_data:
                user.contact_information = profile_data['contact_information']
            if 'personal_profile' in profile_data:
                user.personal_profile = profile_data['personal_profile']
            if 'user_preferences' in profile_data:
                user.user_preferences = profile_data['user_preferences']
            
            user.updated_at = datetime.now(timezone.utc)
            
            await self.db.commit()
            
            logger.info(f"Updated user profile: {user.email}")
            
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating user profile: {e}")
            raise
    
    # =====================================================
    # SCHOOL MEMBERSHIP MANAGEMENT
    # =====================================================
    
    async def add_school_membership(
        self,
        user_id: UUID,
        membership_data: SchoolMembershipCreate
    ) -> SchoolMembership:
        """Add school membership for user"""
        
        try:
            # Check if user exists
            user = await self.get_user_by_id(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Check if membership already exists
            existing_membership = await self._get_school_membership(
                user_id, membership_data.school_id
            )
            if existing_membership:
                raise ValueError(f"User already has membership in school {membership_data.school_id}")
            
            # Get school information
            school_info = await self._get_school_info(membership_data.school_id)
            if not school_info:
                raise ValueError(f"School {membership_data.school_id} not found")
            
            # Create membership
            membership = SchoolMembership(
                user_id=user_id,
                school_id=membership_data.school_id,
                school_name=school_info.name,
                school_subdomain=school_info.subdomain,
                school_region=getattr(school_info, 'region', None),
                role=membership_data.role.value,
                status=MembershipStatus.ACTIVE.value,
                permissions=membership_data.permissions or [],
                
                # Role-specific fields
                employee_id=membership_data.employee_id,
                student_id=membership_data.student_id,
                registration_number=membership_data.registration_number,
                
                # Academic information
                current_grade=membership_data.current_grade,
                current_class=membership_data.current_class,
                admission_date=membership_data.admission_date,
                
                # Employment information
                department=membership_data.department,
                position=membership_data.position,
                hire_date=membership_data.hire_date,
                contract_type=membership_data.contract_type,
                
                # Family relationships
                children_ids=membership_data.children_ids or [],
                relationship_type=membership_data.relationship_type,
                
                # Additional data
                role_metadata=membership_data.role_metadata or {},
                membership_notes=membership_data.membership_notes,
                
                joined_date=datetime.now(timezone.utc)
            )
            
            self.db.add(membership)
            await self.db.flush()
            
            logger.info(f"Added school membership: User {user_id} -> School {membership_data.school_id} as {membership_data.role.value}")
            
            return membership
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error adding school membership: {e}")
            raise
    
    async def update_school_membership(
        self,
        user_id: UUID,
        school_id: UUID,
        updates: Dict[str, Any]
    ) -> Optional[SchoolMembership]:
        """Update school membership"""
        
        try:
            membership = await self._get_school_membership(user_id, school_id)
            if not membership:
                return None
            
            # Update allowed fields
            updatable_fields = [
                'role', 'status', 'permissions', 'current_grade', 'current_class',
                'department', 'position', 'contract_type', 'employment_status',
                'children_ids', 'relationship_type', 'role_metadata', 'membership_notes'
            ]
            
            for field in updatable_fields:
                if field in updates:
                    setattr(membership, field, updates[field])
            
            membership.updated_at = datetime.now(timezone.utc)
            
            await self.db.commit()
            
            logger.info(f"Updated school membership: User {user_id} in School {school_id}")
            
            return membership
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating school membership: {e}")
            raise
    
    async def remove_school_membership(
        self,
        user_id: UUID,
        school_id: UUID,
        reason: str = None
    ) -> bool:
        """Remove school membership (soft delete)"""
        
        try:
            membership = await self._get_school_membership(user_id, school_id)
            if not membership:
                return False
            
            # Soft delete by updating status
            membership.status = MembershipStatus.ARCHIVED.value
            membership.left_date = datetime.now(timezone.utc)
            if reason:
                membership.membership_notes = f"Archived: {reason}"
            
            await self.db.commit()
            
            logger.info(f"Archived school membership: User {user_id} from School {school_id}")
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error removing school membership: {e}")
            return False
    
    async def get_user_school_memberships(
        self,
        user_id: UUID,
        active_only: bool = True
    ) -> List[SchoolMembership]:
        """Get all school memberships for user"""
        
        try:
            query = select(SchoolMembership).where(SchoolMembership.user_id == user_id)
            
            if active_only:
                query = query.where(SchoolMembership.status == MembershipStatus.ACTIVE.value)
            
            query = query.order_by(SchoolMembership.school_name)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting user school memberships: {e}")
            return []
    
    # =====================================================
    # SCHOOL SWITCHING
    # =====================================================
    
    async def switch_user_school_context(
        self,
        user_id: UUID,
        session_id: str,
        target_school_id: UUID,
        reason: str = None
    ) -> Dict[str, Any]:
        """Switch user's school context in session"""
        
        try:
            # Get user and verify they have access to target school
            user = await self.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            
            if not user.has_school_access(str(target_school_id)):
                raise ValueError("User does not have access to target school")
            
            # Get user session
            session = await self._get_user_session(session_id)
            if not session or session.user_id != user_id:
                raise ValueError("Invalid session")
            
            # Get target membership
            target_membership = user.get_school_membership(str(target_school_id))
            if not target_membership:
                raise ValueError("Target school membership not found")
            
            # Update session
            old_school_id = session.current_school_id
            session.switch_school(str(target_school_id))
            session.last_activity_at = datetime.now(timezone.utc)
            
            await self.db.commit()
            
            logger.info(f"User {user_id} switched from school {old_school_id} to {target_school_id}")
            
            return {
                "success": True,
                "old_school_id": str(old_school_id) if old_school_id else None,
                "new_school_id": str(target_school_id),
                "new_school_name": target_membership.school_name,
                "new_role": target_membership.role,
                "switch_count": session.school_switch_count
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error switching school context: {e}")
            raise
    
    async def get_user_available_schools(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Get schools available for user to switch to"""
        
        memberships = await self.get_user_school_memberships(user_id, active_only=True)
        
        available_schools = []
        for membership in memberships:
            available_schools.append({
                "school_id": str(membership.school_id),
                "school_name": membership.school_name,
                "school_subdomain": membership.school_subdomain,
                "role": membership.role,
                "permissions": membership.permissions,
                "is_student": membership.is_student,
                "is_staff": membership.is_staff,
                "is_parent_guardian": membership.is_parent_guardian,
                "children_count": membership.get_children_count()
            })
        
        return available_schools
    
    # =====================================================
    # STUDENT RECORD PORTABILITY
    # =====================================================
    
    async def prepare_student_transfer(
        self,
        student_user_id: UUID,
        from_school_id: UUID,
        to_school_id: UUID
    ) -> Dict[str, Any]:
        """Prepare student record for transfer between schools"""
        
        try:
            # Get student user and membership
            user = await self.get_user_by_id(student_user_id)
            if not user:
                raise ValueError("Student user not found")
            
            student_membership = user.get_school_membership(str(from_school_id))
            if not student_membership or not student_membership.is_student:
                raise ValueError("Student membership not found in source school")
            
            # Get comprehensive student record
            student_record = await self._compile_student_record(
                student_user_id, from_school_id
            )
            
            # Create transfer package
            transfer_package = {
                "transfer_id": str(uuid4()),
                "student_info": {
                    "user_id": str(student_user_id),
                    "student_id": student_membership.student_id,
                    "registration_number": student_membership.registration_number,
                    "full_name": user.full_name,
                    "email": user.email,
                    "contact_information": user.contact_information,
                    "personal_profile": user.personal_profile
                },
                "academic_record": student_record.get("academic", {}),
                "financial_record": student_record.get("financial", {}),
                "health_record": student_record.get("health", {}),
                "disciplinary_record": student_record.get("disciplinary", {}),
                "from_school": {
                    "school_id": str(from_school_id),
                    "school_name": student_membership.school_name,
                    "current_grade": student_membership.current_grade,
                    "graduation_date": student_membership.graduation_date
                },
                "to_school": {
                    "school_id": str(to_school_id)
                },
                "transfer_date": datetime.now(timezone.utc).isoformat(),
                "status": "prepared"
            }
            
            logger.info(f"Prepared student transfer: {student_user_id} from {from_school_id} to {to_school_id}")
            
            return transfer_package
            
        except Exception as e:
            logger.error(f"Error preparing student transfer: {e}")
            raise
    
    async def execute_student_transfer(
        self,
        transfer_package: Dict[str, Any],
        target_grade: str,
        target_class: str = None
    ) -> SchoolMembership:
        """Execute student transfer using transfer package"""
        
        try:
            student_user_id = UUID(transfer_package["student_info"]["user_id"])
            from_school_id = UUID(transfer_package["from_school"]["school_id"])
            to_school_id = UUID(transfer_package["to_school"]["school_id"])
            
            # Update old membership status
            old_membership = await self._get_school_membership(student_user_id, from_school_id)
            if old_membership:
                old_membership.status = MembershipStatus.TRANSFERRED.value
                old_membership.left_date = datetime.now(timezone.utc)
                old_membership.membership_notes = f"Transferred to school {to_school_id}"
            
            # Create new membership
            new_membership_data = SchoolMembershipCreate(
                school_id=to_school_id,
                role=SchoolRole.STUDENT,
                current_grade=target_grade,
                current_class=target_class,
                admission_date=datetime.now(timezone.utc),
                role_metadata={
                    "transferred_from": str(from_school_id),
                    "transfer_date": datetime.now(timezone.utc).isoformat(),
                    "previous_grade": transfer_package["from_school"]["current_grade"],
                    "transfer_package_id": transfer_package["transfer_id"]
                }
            )
            
            new_membership = await self.add_school_membership(
                student_user_id, new_membership_data
            )
            
            # Import academic and other records (would involve other services)
            await self._import_student_records(to_school_id, transfer_package)
            
            await self.db.commit()
            
            logger.info(f"Executed student transfer: {student_user_id} to school {to_school_id}")
            
            return new_membership
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error executing student transfer: {e}")
            raise
    
    # =====================================================
    # UTILITY METHODS
    # =====================================================
    
    async def _get_user_by_email(self, email: str) -> Optional[UnifiedUser]:
        """Internal method to get user by email"""
        result = await self.db.execute(
            select(UnifiedUser).where(UnifiedUser.email == email.lower().strip())
        )
        return result.scalar_one_or_none()
    
    async def _get_school_membership(
        self,
        user_id: UUID,
        school_id: UUID
    ) -> Optional[SchoolMembership]:
        """Get school membership by user and school ID"""
        
        result = await self.db.execute(
            select(SchoolMembership).where(
                and_(
                    SchoolMembership.user_id == user_id,
                    SchoolMembership.school_id == school_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def _get_school_info(self, school_id: UUID):
        """Get basic school information"""
        
        query = text("""
            SELECT id, name, subdomain, region, is_active
            FROM platform.schools
            WHERE id = :school_id
        """)
        
        result = await self.db.execute(query, {"school_id": school_id})
        return result.fetchone()
    
    async def _get_user_session(self, session_id: str) -> Optional[UserSession]:
        """Get user session by session ID"""
        
        result = await self.db.execute(
            select(UserSession).where(UserSession.session_id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def _compile_student_record(
        self,
        student_user_id: UUID,
        school_id: UUID
    ) -> Dict[str, Any]:
        """Compile comprehensive student record for transfer"""
        
        # This would integrate with other modules to get complete record
        # For now, return placeholder structure
        return {
            "academic": {
                "grades": [],
                "attendance": {},
                "subjects": [],
                "assessments": []
            },
            "financial": {
                "fee_history": [],
                "payment_history": [],
                "outstanding_balances": []
            },
            "health": {
                "medical_records": [],
                "immunizations": [],
                "emergency_contacts": []
            },
            "disciplinary": {
                "incidents": [],
                "commendations": []
            }
        }
    
    async def _import_student_records(
        self,
        school_id: UUID,
        transfer_package: Dict[str, Any]
    ):
        """Import student records into new school"""
        
        # This would integrate with other modules to import records
        # For now, just log the operation
        logger.info(f"Importing student records for transfer {transfer_package['transfer_id']} to school {school_id}")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


# =====================================================
# SERVICE FACTORY
# =====================================================

async def create_unified_user_service() -> UnifiedUserService:
    """Create unified user service with database session"""
    
    async for db in get_async_session():
        return UnifiedUserService(db)