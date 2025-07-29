# 1Class User System Consolidation
# Multi-Tenant SaaS Architecture for Zimbabwe Schools

"""
SINGLE SOURCE OF TRUTH USER MODEL
This consolidates all user models into one comprehensive system
that handles multi-tenancy, school context, and Clerk integration
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID, uuid4

# ============================================================================
# CORE USER ENUMS & TYPES
# ============================================================================

class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive" 
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    ARCHIVED = "archived"

class PlatformRole(str, Enum):
    """Platform-wide roles (across all schools)"""
    SUPER_ADMIN = "super_admin"          # 1Class platform administrators
    PLATFORM_SUPPORT = "platform_support"  # 1Class support team
    CUSTOMER_SUCCESS = "customer_success"   # Account managers
    MIGRATION_SPECIALIST = "migration_specialist"  # Care package team
    PARTNER = "partner"                   # Integration partners
    USER = "user"                        # Regular school users

class SchoolRole(str, Enum):
    """School-specific roles (within a school)"""
    SCHOOL_ADMIN = "school_admin"        # School owner/principal
    DEPUTY_ADMIN = "deputy_admin"        # Deputy head, bursar
    ACADEMIC_HEAD = "academic_head"      # Director of studies
    TEACHER = "teacher"                  # Teaching staff
    LIBRARIAN = "librarian"              # Library staff
    ACCOUNTANT = "accountant"            # Financial staff
    SECRETARY = "secretary"              # Administrative staff
    PARENT = "parent"                    # Parent/guardian
    STUDENT = "student"                  # Student account
    SUPPORT_STAFF = "support_staff"      # Other support roles

class PermissionScope(str, Enum):
    """Permission scopes for granular access control"""
    PLATFORM = "platform"               # Platform-wide permissions
    SCHOOL = "school"                   # School-wide permissions
    CLASS = "class"                     # Class-specific permissions
    STUDENT = "student"                 # Individual student permissions

# ============================================================================
# UNIFIED USER MODEL
# ============================================================================

class UserProfile(BaseModel):
    """Extended user profile information"""
    title: Optional[str] = None          # Mr, Mrs, Dr, Prof
    middle_name: Optional[str] = None
    preferred_name: Optional[str] = None
    phone_number: Optional[str] = None
    phone_number_verified: bool = False
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: str = "Zimbabwe"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    profile_image_url: Optional[str] = None
    bio: Optional[str] = None
    
    # Professional information (for staff)
    employee_id: Optional[str] = None
    department: Optional[str] = None
    subject_specialization: Optional[List[str]] = None
    qualifications: Optional[List[str]] = None
    years_of_experience: Optional[int] = None
    
    # Student-specific information
    student_id: Optional[str] = None
    grade_level: Optional[str] = None
    admission_date: Optional[datetime] = None
    parent_ids: Optional[List[UUID]] = None

class SchoolMembership(BaseModel):
    """User's membership in a specific school"""
    school_id: UUID
    school_name: str                     # Cached for quick access
    school_subdomain: str               # e.g., "stmarys" for stmarys.oneclass.ac.zw
    role: SchoolRole
    status: UserStatus = UserStatus.ACTIVE
    joined_date: datetime = Field(default_factory=datetime.utcnow)
    left_date: Optional[datetime] = None
    
    # Role-specific data
    classes_assigned: Optional[List[str]] = None  # For teachers
    subjects_taught: Optional[List[str]] = None   # For teachers
    grade_level: Optional[str] = None             # For students
    is_primary_contact: bool = False              # For parents
    permissions: List[str] = []                   # Specific permissions
    
    # Metadata
    invited_by: Optional[UUID] = None
    invitation_accepted_date: Optional[datetime] = None
    notes: Optional[str] = None

class ClerkIntegration(BaseModel):
    """Clerk authentication provider integration"""
    clerk_user_id: str                   # Clerk's unique user ID
    clerk_session_id: Optional[str] = None
    external_accounts: Optional[List[Dict[str, Any]]] = None  # Google, etc.
    last_sign_in_at: Optional[datetime] = None
    sign_up_source: Optional[str] = None  # Direct, invitation, etc.
    verification_status: Dict[str, bool] = {}  # Email, phone verification

class PlatformUser(BaseModel):
    """
    SINGLE, COMPREHENSIVE USER MODEL
    This replaces all other user models and serves as the single source of truth
    """
    # Core Identity
    id: UUID = Field(default_factory=uuid4)
    email: EmailStr
    first_name: str
    last_name: str
    
    # Platform-level information
    platform_role: PlatformRole = PlatformRole.USER
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_active_at: Optional[datetime] = None
    
    # Extended profile
    profile: UserProfile = Field(default_factory=UserProfile)
    
    # Multi-tenant school memberships
    school_memberships: List[SchoolMembership] = []
    primary_school_id: Optional[UUID] = None  # Default school context
    
    # Authentication integration
    clerk_integration: Optional[ClerkIntegration] = None
    
    # Platform-level permissions and features
    platform_permissions: List[str] = []
    feature_flags: Dict[str, bool] = {}
    preferences: Dict[str, Any] = {}
    
    # Audit trail
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    archived_at: Optional[datetime] = None
    archived_by: Optional[UUID] = None
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def display_name(self) -> str:
        """Get user's display name (preferred name or full name)"""
        if self.profile.preferred_name:
            return self.profile.preferred_name
        return self.full_name
    
    def get_school_membership(self, school_id: UUID) -> Optional[SchoolMembership]:
        """Get user's membership for a specific school"""
        for membership in self.school_memberships:
            if membership.school_id == school_id:
                return membership
        return None
    
    def get_school_role(self, school_id: UUID) -> Optional[SchoolRole]:
        """Get user's role in a specific school"""
        membership = self.get_school_membership(school_id)
        return membership.role if membership else None
    
    def has_school_access(self, school_id: UUID) -> bool:
        """Check if user has access to a specific school"""
        membership = self.get_school_membership(school_id)
        return membership is not None and membership.status == UserStatus.ACTIVE
    
    def is_school_admin(self, school_id: UUID) -> bool:
        """Check if user is admin of a specific school"""
        role = self.get_school_role(school_id)
        return role in [SchoolRole.SCHOOL_ADMIN, SchoolRole.DEPUTY_ADMIN]
    
    def is_platform_admin(self) -> bool:
        """Check if user has platform-level admin access"""
        return self.platform_role in [PlatformRole.SUPER_ADMIN, PlatformRole.PLATFORM_SUPPORT]

# ============================================================================
# USER MANAGEMENT SERVICES
# ============================================================================

class UserService:
    """Centralized user management service"""
    
    @staticmethod
    async def create_user_from_clerk(
        clerk_user_data: Dict[str, Any],
        school_context: Optional[Dict[str, Any]] = None
    ) -> PlatformUser:
        """Create a new user from Clerk signup data"""
        
        # Extract basic info from Clerk
        email = clerk_user_data.get("email_addresses", [{}])[0].get("email_address")
        first_name = clerk_user_data.get("first_name", "")
        last_name = clerk_user_data.get("last_name", "")
        clerk_user_id = clerk_user_data.get("id")
        
        # Create user profile
        profile = UserProfile()
        if clerk_user_data.get("phone_numbers"):
            profile.phone_number = clerk_user_data["phone_numbers"][0].get("phone_number")
        
        # Create Clerk integration
        clerk_integration = ClerkIntegration(
            clerk_user_id=clerk_user_id,
            external_accounts=clerk_user_data.get("external_accounts", []),
            sign_up_source=school_context.get("source") if school_context else "direct"
        )
        
        # Create base user
        user = PlatformUser(
            email=email,
            first_name=first_name,
            last_name=last_name,
            profile=profile,
            clerk_integration=clerk_integration
        )
        
        # Add school membership if signing up via school subdomain
        if school_context:
            school_membership = SchoolMembership(
                school_id=UUID(school_context["school_id"]),
                school_name=school_context["school_name"],
                school_subdomain=school_context["subdomain"],
                role=SchoolRole(school_context.get("default_role", "teacher")),
                invitation_accepted_date=datetime.utcnow()
            )
            user.school_memberships.append(school_membership)
            user.primary_school_id = school_membership.school_id
        
        return user
    
    @staticmethod
    async def add_school_membership(
        user_id: UUID,
        school_id: UUID,
        role: SchoolRole,
        invited_by: UUID,
        permissions: Optional[List[str]] = None
    ) -> SchoolMembership:
        """Add user to a school with specific role"""
        
        # Get school information (would come from school service)
        school_info = await get_school_info(school_id)  # This would be implemented
        
        membership = SchoolMembership(
            school_id=school_id,
            school_name=school_info["name"],
            school_subdomain=school_info["subdomain"],
            role=role,
            invited_by=invited_by,
            permissions=permissions or []
        )
        
        return membership
    
    @staticmethod
    async def remove_school_membership(user_id: UUID, school_id: UUID) -> bool:
        """Remove user from a school"""
        # Implementation would update user's school_memberships
        # Set left_date and status to INACTIVE
        pass
    
    @staticmethod
    async def get_user_by_clerk_id(clerk_user_id: str) -> Optional[PlatformUser]:
        """Get user by Clerk user ID"""
        # Implementation would query database
        pass
    
    @staticmethod
    async def get_users_by_school(
        school_id: UUID,
        role: Optional[SchoolRole] = None,
        status: UserStatus = UserStatus.ACTIVE
    ) -> List[PlatformUser]:
        """Get all users for a specific school"""
        # Implementation would query database
        pass

# ============================================================================
# AUTHENTICATION & CONTEXT MIDDLEWARE
# ============================================================================

class SchoolContext(BaseModel):
    """Current school context for a user session"""
    school_id: UUID
    school_name: str
    subdomain: str
    user_role: SchoolRole
    user_permissions: List[str]
    school_settings: Dict[str, Any]
    branding: Dict[str, Any]

class UserContext(BaseModel):
    """Complete user context for current session"""
    user: PlatformUser
    current_school: Optional[SchoolContext] = None
    available_schools: List[SchoolContext] = []
    platform_permissions: List[str] = []

async def get_user_context(
    clerk_session_id: str,
    subdomain: Optional[str] = None
) -> Optional[UserContext]:
    """
    Get complete user context from Clerk session
    This replaces the EnhancedUser approach with a more structured system
    """
    
    # 1. Validate Clerk session and get user
    clerk_user = await validate_clerk_session(clerk_session_id)
    if not clerk_user:
        return None
    
    # 2. Get platform user
    platform_user = await UserService.get_user_by_clerk_id(clerk_user["id"])
    if not platform_user:
        return None
    
    # 3. Determine current school context
    current_school = None
    if subdomain:
        # User accessed via school subdomain
        for membership in platform_user.school_memberships:
            if membership.school_subdomain == subdomain and membership.status == UserStatus.ACTIVE:
                school_info = await get_school_info(membership.school_id)
                current_school = SchoolContext(
                    school_id=membership.school_id,
                    school_name=membership.school_name,
                    subdomain=membership.school_subdomain,
                    user_role=membership.role,
                    user_permissions=membership.permissions,
                    school_settings=school_info.get("settings", {}),
                    branding=school_info.get("branding", {})
                )
                break
    
    # 4. Build available schools list
    available_schools = []
    for membership in platform_user.school_memberships:
        if membership.status == UserStatus.ACTIVE:
            school_info = await get_school_info(membership.school_id)
            school_context = SchoolContext(
                school_id=membership.school_id,
                school_name=membership.school_name,
                subdomain=membership.school_subdomain,
                user_role=membership.role,
                user_permissions=membership.permissions,
                school_settings=school_info.get("settings", {}),
                branding=school_info.get("branding", {})
            )
            available_schools.append(school_context)
    
    return UserContext(
        user=platform_user,
        current_school=current_school,
        available_schools=available_schools,
        platform_permissions=platform_user.platform_permissions
    )

# ============================================================================
# MIGRATION STRATEGY
# ============================================================================

class UserModelMigration:
    """Migration utilities to consolidate existing user models"""
    
    @staticmethod
    async def migrate_from_legacy_models():
        """Migrate data from existing User and EnhancedUser models"""
        
        # 1. Get all existing users from platform.py User model
        legacy_users = await get_all_legacy_users()
        
        # 2. Get all enhanced user data from auth.py
        enhanced_user_data = await get_all_enhanced_user_data()
        
        # 3. Consolidate into new PlatformUser model
        for legacy_user in legacy_users:
            enhanced_data = enhanced_user_data.get(legacy_user.id)
            
            # Create new consolidated user
            new_user = PlatformUser(
                id=legacy_user.id,
                email=legacy_user.email,
                first_name=legacy_user.first_name,
                last_name=legacy_user.last_name,
                platform_role=legacy_user.role,
                created_at=legacy_user.created_at,
                # ... migrate other fields
            )
            
            # Add school memberships from enhanced data
            if enhanced_data and enhanced_data.get("school_context"):
                school_context = enhanced_data["school_context"]
                membership = SchoolMembership(
                    school_id=UUID(school_context["school_id"]),
                    school_name=school_context["school_name"],
                    school_subdomain=school_context["subdomain"],
                    role=SchoolRole(school_context["user_role"]),
                    # ... migrate other membership data
                )
                new_user.school_memberships.append(membership)
                new_user.primary_school_id = membership.school_id
            
            # Save consolidated user
            await save_consolidated_user(new_user)
        
        print("User model migration completed successfully!")

# ============================================================================
# API ENDPOINTS EXAMPLE
# ============================================================================

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer

app = FastAPI()
security = HTTPBearer()

async def get_current_user_context(request: Request) -> UserContext:
    """Dependency to get current user context"""
    
    # Extract subdomain from request
    host = request.headers.get("host", "")
    subdomain = None
    if ".oneclass.ac.zw" in host:
        subdomain = host.split(".oneclass.ac.zw")[0]
    
    # Get Clerk session from Authorization header
    auth_header = request.headers.get("authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    clerk_session_id = auth_header.replace("Bearer ", "")
    
    # Get user context
    user_context = await get_user_context(clerk_session_id, subdomain)
    if not user_context:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    return user_context

@app.get("/api/user/me")
async def get_current_user(context: UserContext = Depends(get_current_user_context)):
    """Get current user information"""
    return {
        "user": context.user,
        "current_school": context.current_school,
        "available_schools": context.available_schools
    }

@app.post("/api/user/switch-school/{school_id}")
async def switch_school_context(
    school_id: UUID,
    context: UserContext = Depends(get_current_user_context)
):
    """Switch user's current school context"""
    
    # Check if user has access to requested school
    target_school = None
    for school in context.available_schools:
        if school.school_id == school_id:
            target_school = school
            break
    
    if not target_school:
        raise HTTPException(status_code=403, detail="No access to requested school")
    
    # Return redirect URL to school subdomain
    return {
        "redirect_url": f"https://{target_school.subdomain}.oneclass.ac.zw/dashboard",
        "school_context": target_school
    }

# Helper function placeholders (would be implemented based on your existing services)
async def validate_clerk_session(session_id: str): pass
async def get_school_info(school_id: UUID): pass
async def get_all_legacy_users(): pass
async def get_all_enhanced_user_data(): pass
async def save_consolidated_user(user: PlatformUser): pass