"""
Comprehensive Tenant Onboarding and Configuration Service
Handles school registration, verification, configuration, and subscription management
"""

import hashlib
import secrets
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
import logging
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text, update, delete, insert
from sqlalchemy.orm import selectinload, joinedload
from pydantic import BaseModel, Field, EmailStr, validator, root_validator

from shared.database import get_async_session
from shared.models.platform import School, SchoolSubscription
from shared.models.unified_user import (
    UnifiedUser, SchoolMembership, SchoolInvitation,
    GlobalRole, SchoolRole, MembershipStatus, UserStatus
)

logger = logging.getLogger(__name__)

# =====================================================
# ENUMS FOR ONBOARDING STAGES
# =====================================================

class OnboardingStage(str, Enum):
    """School onboarding stages"""
    
    INITIAL_REGISTRATION = "initial_registration"     # Basic school info submitted
    EMAIL_VERIFICATION = "email_verification"        # Waiting for email verification
    DOCUMENT_VERIFICATION = "document_verification"  # Uploading and verifying documents
    SUBSCRIPTION_SETUP = "subscription_setup"        # Setting up subscription plan
    ADMIN_SETUP = "admin_setup"                     # Creating admin accounts
    MODULE_CONFIGURATION = "module_configuration"    # Configuring enabled modules
    CUSTOMIZATION = "customization"                  # School branding and settings
    FINAL_REVIEW = "final_review"                    # Final review by platform admin
    COMPLETED = "completed"                          # Onboarding complete
    REJECTED = "rejected"                            # Application rejected


class VerificationStatus(str, Enum):
    """Document verification status"""
    
    PENDING = "pending"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ADDITIONAL_INFO_REQUIRED = "additional_info_required"


class SubscriptionTier(str, Enum):
    """Subscription tiers with per-student pricing"""
    
    STARTER = "starter"           # $3.50 per student/month - 50-300 students
    PROFESSIONAL = "professional" # $5.50 per student/month - 200-800 students
    ENTERPRISE = "enterprise"     # $8.00 per student/month - 500+ students


# =====================================================
# PYDANTIC MODELS FOR ONBOARDING
# =====================================================

class MigrationServicePackage(str, Enum):
    """Available migration service packages"""
    
    NONE = "none"                           # No migration services needed
    BASIC = "basic"                         # Basic data import assistance ($500)
    STANDARD = "standard"                   # Standard migration package ($1500)
    PREMIUM = "premium"                     # Premium migration package ($2500)
    ENTERPRISE = "enterprise"               # Full enterprise migration ($5000+)


class MigrationRequirements(BaseModel):
    """Migration service requirements"""
    
    # Service package selection
    package: MigrationServicePackage = MigrationServicePackage.NONE
    
    # Current system information
    current_system: Optional[str] = Field(None, description="Name of current school management system")
    current_system_version: Optional[str] = Field(None, description="Version of current system")
    data_sources: List[str] = Field(default_factory=list, description="List of data sources (Excel, databases, etc.)")
    
    # Data scope
    student_records_count: Optional[int] = Field(None, description="Approximate number of student records")
    staff_records_count: Optional[int] = Field(None, description="Approximate number of staff records")
    financial_data_years: Optional[int] = Field(None, ge=0, le=10, description="Years of financial data to migrate")
    academic_data_years: Optional[int] = Field(None, ge=0, le=10, description="Years of academic data to migrate")
    
    # Timeline preferences
    urgent_migration: bool = Field(False, description="Urgent migration required (additional $1000)")
    preferred_completion_weeks: Optional[int] = Field(None, ge=2, le=26, description="Preferred completion timeline")
    
    # Additional services
    onsite_training: bool = Field(False, description="Onsite training required ($800)")
    weekend_work: bool = Field(False, description="Weekend work acceptable ($500)")
    data_cleanup: bool = Field(True, description="Data cleanup and validation required")
    custom_reports_setup: bool = Field(False, description="Custom reports setup required")
    
    # Special requirements
    special_requirements: Optional[str] = Field(None, max_length=2000, description="Special migration requirements")
    compliance_requirements: List[str] = Field(default_factory=list, description="Specific compliance requirements")


class SchoolRegistrationRequest(BaseModel):
    """Initial school registration request"""
    
    # Basic school information
    school_name: str = Field(..., min_length=2, max_length=200)
    subdomain: str = Field(..., min_length=2, max_length=50)
    school_type: str = Field(..., description="primary, secondary, combined, college")
    
    # Location information
    physical_address: str = Field(..., min_length=10)
    city: str = Field(..., min_length=2, max_length=100)
    province: str = Field(..., min_length=2, max_length=100)
    postal_code: Optional[str] = None
    country: str = Field(default="Zimbabwe", max_length=100)
    
    # Contact information
    principal_name: str = Field(..., min_length=2, max_length=200)
    principal_email: EmailStr
    principal_phone: str = Field(..., min_length=10, max_length=20)
    school_phone: Optional[str] = None
    school_email: Optional[EmailStr] = None
    website_url: Optional[str] = None
    
    # Registration details
    ministry_registration_number: str = Field(..., min_length=3)
    student_capacity: int = Field(..., ge=10, le=10000)
    current_student_count: int = Field(..., ge=0)
    staff_count: int = Field(..., ge=1)
    
    # Subscription preference
    preferred_subscription_tier: SubscriptionTier = SubscriptionTier.PROFESSIONAL
    
    # Migration Services Requirements
    migration_requirements: MigrationRequirements = Field(default_factory=MigrationRequirements, description="Migration service requirements")
    
    # Terms and conditions
    terms_accepted: bool = Field(..., description="Must accept terms and conditions")
    privacy_policy_accepted: bool = Field(..., description="Must accept privacy policy")
    
    @validator('subdomain')
    def validate_subdomain(cls, v):
        import re
        if not re.match(r'^[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$', v):
            raise ValueError('Invalid subdomain format')
        
        # Check reserved subdomains
        reserved = {
            'www', 'api', 'admin', 'app', 'mail', 'ftp', 'blog', 'shop',
            'support', 'help', 'docs', 'status', 'cdn', 'assets', 'static'
        }
        if v.lower() in reserved:
            raise ValueError('Subdomain is reserved')
        
        return v.lower()
    
    @validator('principal_phone', 'school_phone')
    def validate_zimbabwe_phone(cls, v):
        if v and not (v.startswith('+263') or v.startswith('07') or v.startswith('08')):
            raise ValueError('Phone number must be valid Zimbabwe format')
        return v
    
    @root_validator
    def validate_terms(cls, values):
        if not values.get('terms_accepted') or not values.get('privacy_policy_accepted'):
            raise ValueError('Must accept terms and conditions and privacy policy')
        return values


class DocumentUploadRequest(BaseModel):
    """Document upload for verification"""
    
    document_type: str = Field(..., description="registration_certificate, license, etc.")
    file_url: str = Field(..., description="URL to uploaded document")
    file_name: str = Field(..., min_length=1)
    file_size: int = Field(..., ge=1)
    mime_type: str = Field(..., min_length=1)
    description: Optional[str] = None


class SchoolConfigurationUpdate(BaseModel):
    """School configuration updates"""
    
    # Branding
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    
    # Academic settings
    academic_year_start_month: int = Field(default=1, ge=1, le=12)
    academic_year_end_month: int = Field(default=12, ge=1, le=12)
    terms_per_year: int = Field(default=3, ge=1, le=4)
    
    # Communication settings
    sms_enabled: bool = Field(default=True)
    email_notifications_enabled: bool = Field(default=True)
    parent_portal_enabled: bool = Field(default=True)
    
    # Module configurations
    enabled_modules: List[str] = Field(default_factory=list)
    module_settings: Dict[str, Any] = Field(default_factory=dict)


class OnboardingProgressResponse(BaseModel):
    """Onboarding progress response"""
    
    school_id: UUID
    school_name: str
    subdomain: str
    current_stage: OnboardingStage
    completion_percentage: float
    
    # Stage statuses
    stages: Dict[str, Dict[str, Any]]
    
    # Next steps
    next_steps: List[str]
    required_actions: List[str]
    
    # Timeline
    created_at: datetime
    estimated_completion: Optional[datetime]
    
    class Config:
        from_attributes = True


# =====================================================
# TENANT ONBOARDING SERVICE
# =====================================================

class TenantOnboardingService:
    """Comprehensive service for tenant onboarding and configuration"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =====================================================
    # INITIAL REGISTRATION
    # =====================================================
    
    async def register_school(self, registration_data: SchoolRegistrationRequest) -> Dict[str, Any]:
        """Register new school and start onboarding process"""
        
        try:
            # Validate subdomain availability
            if not await self._is_subdomain_available(registration_data.subdomain):
                raise ValueError(f"Subdomain '{registration_data.subdomain}' is already taken")
            
            # Validate principal email uniqueness
            if await self._is_principal_email_taken(registration_data.principal_email):
                raise ValueError(f"Principal email '{registration_data.principal_email}' is already registered")
            
            # Create school record
            school = School(
                id=uuid4(),
                name=registration_data.school_name,
                subdomain=registration_data.subdomain,
                school_type=registration_data.school_type,
                status="pending_verification",
                is_active=False,
                
                # Location
                physical_address=registration_data.physical_address,
                city=registration_data.city,
                province=registration_data.province,
                postal_code=registration_data.postal_code,
                country=registration_data.country,
                
                # Contact info
                phone=registration_data.school_phone or registration_data.principal_phone,
                email=registration_data.school_email or registration_data.principal_email,
                website_url=registration_data.website_url,
                
                # Registration details
                ministry_registration_number=registration_data.ministry_registration_number,
                student_capacity=registration_data.student_capacity,
                current_student_count=registration_data.current_student_count,
                staff_count=registration_data.staff_count,
                
                # Metadata
                onboarding_data={
                    "stage": OnboardingStage.EMAIL_VERIFICATION.value,
                    "registration_data": registration_data.dict(),
                    "verification_token": self._generate_verification_token(),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "principal_info": {
                        "name": registration_data.principal_name,
                        "email": registration_data.principal_email,
                        "phone": registration_data.principal_phone
                    },
                    "migration_requirements": registration_data.migration_requirements.dict(),
                    "requires_migration_services": registration_data.migration_requirements.package != MigrationServicePackage.NONE
                },
                
                created_at=datetime.now(timezone.utc)
            )
            
            self.db.add(school)
            await self.db.flush()
            
            # Create initial subscription record
            subscription = SchoolSubscription(
                id=uuid4(),
                school_id=school.id,
                tier=registration_data.preferred_subscription_tier.value,
                status="pending",
                
                # Default module access based on tier
                enabled_modules=self._get_default_modules_for_tier(registration_data.preferred_subscription_tier),
                
                # Trial period
                trial_start_date=datetime.now(timezone.utc),
                trial_end_date=datetime.now(timezone.utc) + timedelta(days=30),
                
                metadata={
                    "onboarding_tier": registration_data.preferred_subscription_tier.value,
                    "trial_requested": True
                },
                
                created_at=datetime.now(timezone.utc)
            )
            
            self.db.add(subscription)
            await self.db.commit()
            
            # Send verification email
            await self._send_verification_email(school)
            
            logger.info(f"School registration initiated: {school.name} ({school.id})")
            
            return {
                "school_id": str(school.id),
                "subdomain": school.subdomain,
                "verification_required": True,
                "verification_email_sent": True,
                "onboarding_stage": OnboardingStage.EMAIL_VERIFICATION.value,
                "trial_period_days": 30
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error registering school: {e}")
            raise
    
    async def verify_email(self, school_id: UUID, verification_token: str) -> Dict[str, Any]:
        """Verify principal's email address"""
        
        try:
            school = await self._get_school_by_id(school_id)
            if not school:
                raise ValueError("School not found")
            
            onboarding_data = school.onboarding_data or {}
            stored_token = onboarding_data.get("verification_token")
            
            if not stored_token or stored_token != verification_token:
                raise ValueError("Invalid verification token")
            
            # Update onboarding stage
            onboarding_data["stage"] = OnboardingStage.DOCUMENT_VERIFICATION.value
            onboarding_data["email_verified_at"] = datetime.now(timezone.utc).isoformat()
            onboarding_data["verification_token"] = None  # Clear token
            
            school.onboarding_data = onboarding_data
            school.status = "email_verified"
            
            await self.db.commit()
            
            logger.info(f"Email verified for school: {school.name} ({school.id})")
            
            return {
                "school_id": str(school.id),
                "email_verified": True,
                "next_stage": OnboardingStage.DOCUMENT_VERIFICATION.value,
                "required_documents": self._get_required_documents()
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error verifying email: {e}")
            raise
    
    # =====================================================
    # DOCUMENT VERIFICATION
    # =====================================================
    
    async def upload_verification_document(
        self,
        school_id: UUID,
        document_data: DocumentUploadRequest
    ) -> Dict[str, Any]:
        """Upload document for verification"""
        
        try:
            school = await self._get_school_by_id(school_id)
            if not school:
                raise ValueError("School not found")
            
            onboarding_data = school.onboarding_data or {}
            
            if onboarding_data.get("stage") != OnboardingStage.DOCUMENT_VERIFICATION.value:
                raise ValueError("School is not in document verification stage")
            
            # Add document to verification list
            documents = onboarding_data.get("verification_documents", [])
            
            document_record = {
                "id": str(uuid4()),
                "type": document_data.document_type,
                "file_url": document_data.file_url,
                "file_name": document_data.file_name,
                "file_size": document_data.file_size,
                "mime_type": document_data.mime_type,
                "description": document_data.description,
                "status": VerificationStatus.SUBMITTED.value,
                "uploaded_at": datetime.now(timezone.utc).isoformat()
            }
            
            documents.append(document_record)
            onboarding_data["verification_documents"] = documents
            
            # Check if all required documents are uploaded
            required_docs = self._get_required_documents()
            uploaded_types = {doc["type"] for doc in documents}
            
            if all(req_doc in uploaded_types for req_doc in required_docs):
                onboarding_data["all_documents_uploaded"] = True
                onboarding_data["ready_for_review"] = True
                
                # Notify admin for review
                await self._notify_admin_for_document_review(school)
            
            school.onboarding_data = onboarding_data
            await self.db.commit()
            
            logger.info(f"Document uploaded for school {school.name}: {document_data.document_type}")
            
            return {
                "document_id": document_record["id"],
                "status": "uploaded",
                "all_required_uploaded": onboarding_data.get("all_documents_uploaded", False),
                "ready_for_review": onboarding_data.get("ready_for_review", False)
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error uploading verification document: {e}")
            raise
    
    async def review_documents(
        self,
        school_id: UUID,
        reviewer_id: UUID,
        review_decision: str,
        review_notes: str = None
    ) -> Dict[str, Any]:
        """Review submitted documents (admin only)"""
        
        try:
            school = await self._get_school_by_id(school_id)
            if not school:
                raise ValueError("School not found")
            
            onboarding_data = school.onboarding_data or {}
            
            if review_decision == "approved":
                onboarding_data["stage"] = OnboardingStage.SUBSCRIPTION_SETUP.value
                onboarding_data["documents_approved_at"] = datetime.now(timezone.utc).isoformat()
                school.status = "documents_approved"
                
                # Generate subscription setup link
                setup_token = self._generate_setup_token()
                onboarding_data["subscription_setup_token"] = setup_token
                
                # Send approval email
                await self._send_approval_email(school, setup_token)
                
            elif review_decision == "rejected":
                onboarding_data["stage"] = OnboardingStage.REJECTED.value
                onboarding_data["rejection_reason"] = review_notes
                school.status = "rejected"
                
                # Send rejection email
                await self._send_rejection_email(school, review_notes)
                
            else:
                onboarding_data["additional_info_required"] = True
                onboarding_data["additional_info_notes"] = review_notes
                
                # Send request for additional information
                await self._send_additional_info_request_email(school, review_notes)
            
            # Record review
            onboarding_data["document_review"] = {
                "reviewer_id": str(reviewer_id),
                "decision": review_decision,
                "notes": review_notes,
                "reviewed_at": datetime.now(timezone.utc).isoformat()
            }
            
            school.onboarding_data = onboarding_data
            await self.db.commit()
            
            logger.info(f"Documents reviewed for school {school.name}: {review_decision}")
            
            return {
                "school_id": str(school.id),
                "review_decision": review_decision,
                "next_stage": onboarding_data.get("stage"),
                "setup_token": onboarding_data.get("subscription_setup_token")
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error reviewing documents: {e}")
            raise
    
    # =====================================================
    # SUBSCRIPTION SETUP
    # =====================================================
    
    async def setup_subscription(
        self,
        school_id: UUID,
        setup_token: str,
        subscription_tier: SubscriptionTier,
        payment_method: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Set up subscription and payment"""
        
        try:
            school = await self._get_school_by_id(school_id)
            if not school:
                raise ValueError("School not found")
            
            onboarding_data = school.onboarding_data or {}
            
            # Validate setup token
            if onboarding_data.get("subscription_setup_token") != setup_token:
                raise ValueError("Invalid setup token")
            
            if onboarding_data.get("stage") != OnboardingStage.SUBSCRIPTION_SETUP.value:
                raise ValueError("School is not in subscription setup stage")
            
            # Update subscription
            subscription_query = select(SchoolSubscription).where(
                SchoolSubscription.school_id == school_id
            )
            result = await self.db.execute(subscription_query)
            subscription = result.scalar_one_or_none()
            
            if subscription:
                subscription.tier = subscription_tier.value
                subscription.status = "active"
                subscription.enabled_modules = self._get_default_modules_for_tier(subscription_tier)
                subscription.billing_start_date = datetime.now(timezone.utc)
                subscription.next_billing_date = datetime.now(timezone.utc) + timedelta(days=30)
                subscription.payment_method = payment_method
            
            # Update onboarding stage
            onboarding_data["stage"] = OnboardingStage.ADMIN_SETUP.value
            onboarding_data["subscription_configured_at"] = datetime.now(timezone.utc).isoformat()
            onboarding_data["subscription_tier"] = subscription_tier.value
            onboarding_data["subscription_setup_token"] = None  # Clear token
            
            # Generate admin setup credentials
            admin_setup_data = await self._generate_admin_setup_credentials(school)
            onboarding_data["admin_setup"] = admin_setup_data
            
            school.onboarding_data = onboarding_data
            school.status = "subscription_active"
            
            await self.db.commit()
            
            # Send admin setup instructions
            await self._send_admin_setup_email(school, admin_setup_data)
            
            logger.info(f"Subscription configured for school {school.name}: {subscription_tier.value}")
            
            return {
                "school_id": str(school.id),
                "subscription_tier": subscription_tier.value,
                "next_stage": OnboardingStage.ADMIN_SETUP.value,
                "admin_setup_url": admin_setup_data["setup_url"],
                "trial_days_remaining": 30
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error setting up subscription: {e}")
            raise
    
    # =====================================================
    # ADMIN SETUP
    # =====================================================
    
    async def setup_principal_account(
        self,
        school_id: UUID,
        setup_token: str,
        principal_password: str,
        additional_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Set up principal user account"""
        
        try:
            school = await self._get_school_by_id(school_id)
            if not school:
                raise ValueError("School not found")
            
            onboarding_data = school.onboarding_data or {}
            admin_setup = onboarding_data.get("admin_setup", {})
            
            # Validate setup token
            if admin_setup.get("setup_token") != setup_token:
                raise ValueError("Invalid admin setup token")
            
            if onboarding_data.get("stage") != OnboardingStage.ADMIN_SETUP.value:
                raise ValueError("School is not in admin setup stage")
            
            # Create principal user account
            principal_info = onboarding_data["principal_info"]
            
            principal_user = UnifiedUser(
                id=uuid4(),
                email=principal_info["email"],
                first_name=principal_info["name"].split()[0],
                last_name=" ".join(principal_info["name"].split()[1:]) if len(principal_info["name"].split()) > 1 else "",
                global_role=GlobalRole.SYSTEM_USER.value,
                status=UserStatus.ACTIVE.value,
                is_email_verified=True,
                password_hash=self._hash_password(principal_password),
                
                contact_information={
                    "primary_phone": principal_info["phone"],
                    "address_line1": school.physical_address,
                    "city": school.city,
                    "state_province": school.province,
                    "country": school.country
                },
                
                personal_profile=additional_info or {},
                
                created_at=datetime.now(timezone.utc)
            )
            
            self.db.add(principal_user)
            await self.db.flush()
            
            # Create school membership for principal
            principal_membership = SchoolMembership(
                id=uuid4(),
                user_id=principal_user.id,
                school_id=school.id,
                school_name=school.name,
                school_subdomain=school.subdomain,
                school_region=school.province,
                role=SchoolRole.PRINCIPAL.value,
                status=MembershipStatus.ACTIVE.value,
                
                # Employment details
                employee_id="PRIN001",
                department="Administration",
                position="Principal",
                hire_date=datetime.now(timezone.utc),
                contract_type="permanent",
                employment_status="active",
                
                permissions=[
                    "school_admin", "user_management", "academic_management",
                    "finance_management", "staff_management", "student_management"
                ],
                
                role_metadata={
                    "is_founder": True,
                    "setup_during_onboarding": True
                },
                
                joined_date=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc)
            )
            
            self.db.add(principal_membership)
            
            # Update onboarding stage
            onboarding_data["stage"] = OnboardingStage.MODULE_CONFIGURATION.value
            onboarding_data["principal_account_created_at"] = datetime.now(timezone.utc).isoformat()
            onboarding_data["principal_user_id"] = str(principal_user.id)
            onboarding_data["admin_setup"]["completed"] = True
            
            school.onboarding_data = onboarding_data
            school.principal_user_id = principal_user.id
            
            await self.db.commit()
            
            logger.info(f"Principal account created for school {school.name}: {principal_user.email}")
            
            return {
                "school_id": str(school.id),
                "principal_user_id": str(principal_user.id),
                "next_stage": OnboardingStage.MODULE_CONFIGURATION.value,
                "account_created": True
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error setting up principal account: {e}")
            raise
    
    # =====================================================
    # MODULE CONFIGURATION
    # =====================================================
    
    async def configure_school_modules(
        self,
        school_id: UUID,
        module_configuration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Configure school modules and settings"""
        
        try:
            school = await self._get_school_by_id(school_id)
            if not school:
                raise ValueError("School not found")
            
            onboarding_data = school.onboarding_data or {}
            
            if onboarding_data.get("stage") != OnboardingStage.MODULE_CONFIGURATION.value:
                raise ValueError("School is not in module configuration stage")
            
            # Update subscription with module configuration
            subscription_query = select(SchoolSubscription).where(
                SchoolSubscription.school_id == school_id
            )
            result = await self.db.execute(subscription_query)
            subscription = result.scalar_one_or_none()
            
            if subscription:
                # Validate requested modules against subscription tier
                allowed_modules = self._get_allowed_modules_for_tier(SubscriptionTier(subscription.tier))
                requested_modules = module_configuration.get("enabled_modules", [])
                
                valid_modules = [mod for mod in requested_modules if mod in allowed_modules]
                subscription.enabled_modules = valid_modules
                subscription.module_settings = module_configuration.get("module_settings", {})
            
            # Update onboarding stage
            onboarding_data["stage"] = OnboardingStage.CUSTOMIZATION.value
            onboarding_data["modules_configured_at"] = datetime.now(timezone.utc).isoformat()
            onboarding_data["module_configuration"] = module_configuration
            
            school.onboarding_data = onboarding_data
            
            await self.db.commit()
            
            logger.info(f"Modules configured for school {school.name}")
            
            return {
                "school_id": str(school.id),
                "configured_modules": valid_modules,
                "next_stage": OnboardingStage.CUSTOMIZATION.value,
                "modules_configured": True
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error configuring school modules: {e}")
            raise
    
    # =====================================================
    # SCHOOL CUSTOMIZATION
    # =====================================================
    
    async def update_school_configuration(
        self,
        school_id: UUID,
        config_data: SchoolConfigurationUpdate
    ) -> Dict[str, Any]:
        """Update school configuration and branding"""
        
        try:
            school = await self._get_school_by_id(school_id)
            if not school:
                raise ValueError("School not found")
            
            onboarding_data = school.onboarding_data or {}
            
            # Update school with configuration
            if config_data.logo_url:
                school.logo_url = config_data.logo_url
            
            # Store configuration in school metadata
            school_config = school.configuration or {}
            
            school_config.update({
                "branding": {
                    "primary_color": config_data.primary_color,
                    "secondary_color": config_data.secondary_color,
                    "logo_url": config_data.logo_url
                },
                "academic": {
                    "year_start_month": config_data.academic_year_start_month,
                    "year_end_month": config_data.academic_year_end_month,
                    "terms_per_year": config_data.terms_per_year
                },
                "communication": {
                    "sms_enabled": config_data.sms_enabled,
                    "email_notifications_enabled": config_data.email_notifications_enabled,
                    "parent_portal_enabled": config_data.parent_portal_enabled
                }
            })
            
            school.configuration = school_config
            
            # Update onboarding stage
            if onboarding_data.get("stage") == OnboardingStage.CUSTOMIZATION.value:
                onboarding_data["stage"] = OnboardingStage.FINAL_REVIEW.value
                onboarding_data["customization_completed_at"] = datetime.now(timezone.utc).isoformat()
                
                # Notify admin for final review
                await self._notify_admin_for_final_review(school)
            
            school.onboarding_data = onboarding_data
            
            await self.db.commit()
            
            logger.info(f"School configuration updated: {school.name}")
            
            return {
                "school_id": str(school.id),
                "configuration_updated": True,
                "next_stage": onboarding_data.get("stage"),
                "ready_for_final_review": onboarding_data.get("stage") == OnboardingStage.FINAL_REVIEW.value
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating school configuration: {e}")
            raise
    
    # =====================================================
    # FINAL APPROVAL
    # =====================================================
    
    async def complete_onboarding(
        self,
        school_id: UUID,
        reviewer_id: UUID,
        approval_notes: str = None
    ) -> Dict[str, Any]:
        """Complete school onboarding process (admin only)"""
        
        try:
            school = await self._get_school_by_id(school_id)
            if not school:
                raise ValueError("School not found")
            
            onboarding_data = school.onboarding_data or {}
            
            if onboarding_data.get("stage") != OnboardingStage.FINAL_REVIEW.value:
                raise ValueError("School is not ready for final approval")
            
            # Activate school
            school.status = "active"
            school.is_active = True
            school.activated_at = datetime.now(timezone.utc)
            
            # Complete onboarding
            onboarding_data["stage"] = OnboardingStage.COMPLETED.value
            onboarding_data["completed_at"] = datetime.now(timezone.utc).isoformat()
            onboarding_data["approved_by"] = str(reviewer_id)
            onboarding_data["approval_notes"] = approval_notes
            
            school.onboarding_data = onboarding_data
            
            # Activate subscription
            subscription_query = select(SchoolSubscription).where(
                SchoolSubscription.school_id == school_id
            )
            result = await self.db.execute(subscription_query)
            subscription = result.scalar_one_or_none()
            
            if subscription:
                subscription.status = "active"
                subscription.activated_at = datetime.now(timezone.utc)
            
            await self.db.commit()
            
            # Send welcome email
            await self._send_welcome_email(school)
            
            # Set up initial tenant data
            await self._initialize_tenant_data(school)
            
            logger.info(f"Onboarding completed for school: {school.name} ({school.id})")
            
            return {
                "school_id": str(school.id),
                "onboarding_completed": True,
                "school_activated": True,
                "subdomain_active": f"https://{school.subdomain}.oneclass.ac.zw",
                "welcome_email_sent": True
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error completing onboarding: {e}")
            raise
    
    # =====================================================
    # PROGRESS TRACKING
    # =====================================================
    
    async def get_onboarding_progress(self, school_id: UUID) -> OnboardingProgressResponse:
        """Get detailed onboarding progress"""
        
        try:
            school = await self._get_school_by_id(school_id)
            if not school:
                raise ValueError("School not found")
            
            onboarding_data = school.onboarding_data or {}
            current_stage = OnboardingStage(onboarding_data.get("stage", "initial_registration"))
            
            # Calculate progress percentage
            stage_weights = {
                OnboardingStage.INITIAL_REGISTRATION: 10,
                OnboardingStage.EMAIL_VERIFICATION: 20,
                OnboardingStage.DOCUMENT_VERIFICATION: 35,
                OnboardingStage.SUBSCRIPTION_SETUP: 50,
                OnboardingStage.ADMIN_SETUP: 65,
                OnboardingStage.MODULE_CONFIGURATION: 80,
                OnboardingStage.CUSTOMIZATION: 90,
                OnboardingStage.FINAL_REVIEW: 95,
                OnboardingStage.COMPLETED: 100
            }
            
            completion_percentage = stage_weights.get(current_stage, 0)
            
            # Build stage status details
            stages = {}
            for stage in OnboardingStage:
                stages[stage.value] = self._get_stage_status(stage, onboarding_data)
            
            # Get next steps and required actions
            next_steps, required_actions = self._get_next_steps(current_stage, onboarding_data)
            
            # Estimate completion time
            estimated_completion = self._estimate_completion_time(current_stage)
            
            return OnboardingProgressResponse(
                school_id=school.id,
                school_name=school.name,
                subdomain=school.subdomain,
                current_stage=current_stage,
                completion_percentage=completion_percentage,
                stages=stages,
                next_steps=next_steps,
                required_actions=required_actions,
                created_at=school.created_at,
                estimated_completion=estimated_completion
            )
            
        except Exception as e:
            logger.error(f"Error getting onboarding progress: {e}")
            raise
    
    # =====================================================
    # UTILITY METHODS
    # =====================================================
    
    async def _get_school_by_id(self, school_id: UUID) -> Optional[School]:
        """Get school by ID"""
        result = await self.db.execute(
            select(School).where(School.id == school_id)
        )
        return result.scalar_one_or_none()
    
    async def _is_subdomain_available(self, subdomain: str) -> bool:
        """Check if subdomain is available"""
        result = await self.db.execute(
            select(func.count(School.id)).where(School.subdomain == subdomain)
        )
        count = result.scalar()
        return count == 0
    
    async def _is_principal_email_taken(self, email: str) -> bool:
        """Check if principal email is already registered"""
        result = await self.db.execute(
            select(func.count(UnifiedUser.id)).where(UnifiedUser.email == email.lower())
        )
        count = result.scalar()
        return count > 0
    
    def _generate_verification_token(self) -> str:
        """Generate email verification token"""
        return secrets.token_urlsafe(32)
    
    def _generate_setup_token(self) -> str:
        """Generate setup token"""
        return secrets.token_urlsafe(32)
    
    def _get_default_modules_for_tier(self, tier: SubscriptionTier) -> List[str]:
        """Get default modules for subscription tier"""
        module_tiers = {
            SubscriptionTier.STARTER: [
                "student_information_system",
                "basic_academic_management",
                "parent_communication_portal",
                "basic_financial_management",
                "staff_management"
            ],
            SubscriptionTier.PROFESSIONAL: [
                "student_information_system",
                "advanced_academic_management",
                "parent_communication_portal",
                "basic_financial_management",
                "staff_management",
                "payment_gateway_integration",
                "advanced_reporting_analytics",
                "library_management_system"
            ],
            SubscriptionTier.ENTERPRISE: [
                "student_information_system",
                "advanced_academic_management",
                "parent_communication_portal",
                "basic_financial_management",
                "staff_management",
                "payment_gateway_integration",
                "advanced_reporting_analytics",
                "library_management_system",
                "advanced_analytics_forecasting",
                "multi_campus_support",
                "government_compliance_reporting",
                "learning_management_system"
            ]
        }
        return module_tiers.get(tier, [])
    
    def _get_allowed_modules_for_tier(self, tier: SubscriptionTier) -> List[str]:
        """Get allowed modules for subscription tier"""
        return self._get_default_modules_for_tier(tier)
    
    def _calculate_subscription_pricing(self, tier: SubscriptionTier, student_count: int) -> Dict[str, Any]:
        """Calculate subscription pricing based on tier and student count"""
        pricing_per_student = {
            SubscriptionTier.STARTER: 3.50,
            SubscriptionTier.PROFESSIONAL: 5.50,
            SubscriptionTier.ENTERPRISE: 8.00
        }
        
        price_per_student = pricing_per_student.get(tier, 3.50)
        monthly_total = price_per_student * student_count
        annual_total = monthly_total * 12 * 0.9  # 10% discount for annual
        
        return {
            "tier": tier.value,
            "price_per_student_monthly": price_per_student,
            "student_count": student_count,
            "monthly_total": monthly_total,
            "annual_total": annual_total,
            "annual_savings": monthly_total * 12 - annual_total
        }
    
    def _get_required_documents(self) -> List[str]:
        """Get list of required documents for verification"""
        return [
            "ministry_registration_certificate",
            "school_license",
            "principal_identification",
            "proof_of_address"
        ]
    
    async def _generate_admin_setup_credentials(self, school: School) -> Dict[str, Any]:
        """Generate admin setup credentials"""
        setup_token = self._generate_setup_token()
        
        return {
            "setup_token": setup_token,
            "setup_url": f"https://{school.subdomain}.oneclass.ac.zw/setup/{setup_token}",
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        }
    
    def _get_stage_status(self, stage: OnboardingStage, onboarding_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get status for specific onboarding stage"""
        current_stage = OnboardingStage(onboarding_data.get("stage", "initial_registration"))
        
        # Determine if stage is completed, current, or pending
        stage_order = list(OnboardingStage)
        current_index = stage_order.index(current_stage)
        stage_index = stage_order.index(stage)
        
        if stage_index < current_index:
            status = "completed"
        elif stage_index == current_index:
            status = "current"
        else:
            status = "pending"
        
        # Add stage-specific details
        details = {}
        if stage == OnboardingStage.EMAIL_VERIFICATION:
            details["email_verified"] = onboarding_data.get("email_verified_at") is not None
        elif stage == OnboardingStage.DOCUMENT_VERIFICATION:
            docs = onboarding_data.get("verification_documents", [])
            details["documents_uploaded"] = len(docs)
            details["all_required_uploaded"] = onboarding_data.get("all_documents_uploaded", False)
        elif stage == OnboardingStage.SUBSCRIPTION_SETUP:
            details["subscription_tier"] = onboarding_data.get("subscription_tier")
        elif stage == OnboardingStage.ADMIN_SETUP:
            details["principal_account_created"] = onboarding_data.get("principal_user_id") is not None
        
        return {
            "status": status,
            "details": details
        }
    
    def _get_next_steps(self, current_stage: OnboardingStage, onboarding_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Get next steps and required actions"""
        next_steps = []
        required_actions = []
        
        if current_stage == OnboardingStage.EMAIL_VERIFICATION:
            required_actions.append("Check your email and click the verification link")
            next_steps.append("Verify your email address to proceed with document upload")
            
        elif current_stage == OnboardingStage.DOCUMENT_VERIFICATION:
            required_docs = self._get_required_documents()
            uploaded_docs = [doc["type"] for doc in onboarding_data.get("verification_documents", [])]
            missing_docs = [doc for doc in required_docs if doc not in uploaded_docs]
            
            if missing_docs:
                for doc in missing_docs:
                    required_actions.append(f"Upload {doc.replace('_', ' ').title()}")
            else:
                next_steps.append("Documents under review by platform administrators")
                
        elif current_stage == OnboardingStage.SUBSCRIPTION_SETUP:
            required_actions.append("Complete subscription setup and payment configuration")
            next_steps.append("Set up your subscription plan and billing information")
            
        elif current_stage == OnboardingStage.ADMIN_SETUP:
            required_actions.append("Create your principal account using the setup link sent to your email")
            next_steps.append("Set up administrator accounts and school leadership team")
            
        elif current_stage == OnboardingStage.MODULE_CONFIGURATION:
            required_actions.append("Configure enabled modules and features for your school")
            next_steps.append("Customize modules based on your school's needs")
            
        elif current_stage == OnboardingStage.CUSTOMIZATION:
            required_actions.append("Complete school branding and configuration settings")
            next_steps.append("Add school logo, colors, and academic calendar settings")
            
        elif current_stage == OnboardingStage.FINAL_REVIEW:
            next_steps.append("Platform administrators are conducting final review")
            next_steps.append("You will be notified once your school is approved and activated")
        
        return next_steps, required_actions
    
    def _estimate_completion_time(self, current_stage: OnboardingStage) -> Optional[datetime]:
        """Estimate completion time based on current stage"""
        stage_durations = {
            OnboardingStage.EMAIL_VERIFICATION: 1,      # 1 day
            OnboardingStage.DOCUMENT_VERIFICATION: 3,    # 3 days
            OnboardingStage.SUBSCRIPTION_SETUP: 1,       # 1 day
            OnboardingStage.ADMIN_SETUP: 1,              # 1 day
            OnboardingStage.MODULE_CONFIGURATION: 2,     # 2 days
            OnboardingStage.CUSTOMIZATION: 1,            # 1 day
            OnboardingStage.FINAL_REVIEW: 2,             # 2 days (admin review)
        }
        
        stage_order = list(OnboardingStage)
        current_index = stage_order.index(current_stage)
        
        total_days = 0
        for i in range(current_index, len(stage_order) - 1):  # Exclude COMPLETED stage
            stage = stage_order[i]
            total_days += stage_durations.get(stage, 1)
        
        if total_days > 0:
            return datetime.now(timezone.utc) + timedelta(days=total_days)
        
        return None
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # =====================================================
    # EMAIL NOTIFICATION METHODS
    # =====================================================
    
    async def _send_verification_email(self, school: School):
        """Send email verification email"""
        # TODO: Implement email sending
        logger.info(f"Verification email sent to {school.onboarding_data['principal_info']['email']}")
    
    async def _send_approval_email(self, school: School, setup_token: str):
        """Send document approval email"""
        # TODO: Implement email sending
        logger.info(f"Approval email sent to {school.onboarding_data['principal_info']['email']}")
    
    async def _send_rejection_email(self, school: School, reason: str):
        """Send document rejection email"""
        # TODO: Implement email sending
        logger.info(f"Rejection email sent to {school.onboarding_data['principal_info']['email']}")
    
    async def _send_additional_info_request_email(self, school: School, notes: str):
        """Send additional information request email"""
        # TODO: Implement email sending
        logger.info(f"Additional info request sent to {school.onboarding_data['principal_info']['email']}")
    
    async def _send_admin_setup_email(self, school: School, admin_setup_data: Dict[str, Any]):
        """Send admin setup instructions email"""
        # TODO: Implement email sending
        logger.info(f"Admin setup email sent to {school.onboarding_data['principal_info']['email']}")
    
    async def _send_welcome_email(self, school: School):
        """Send welcome email after onboarding completion"""
        # TODO: Implement email sending
        logger.info(f"Welcome email sent to {school.onboarding_data['principal_info']['email']}")
    
    async def _notify_admin_for_document_review(self, school: School):
        """Notify platform admin for document review"""
        # TODO: Implement admin notification
        logger.info(f"Admin notified for document review: {school.name}")
    
    async def _notify_admin_for_final_review(self, school: School):
        """Notify platform admin for final review"""
        # TODO: Implement admin notification
        logger.info(f"Admin notified for final review: {school.name}")
    
    async def _initialize_tenant_data(self, school: School):
        """Initialize tenant-specific data after activation"""
        # TODO: Create initial academic years, terms, default settings, etc.
        logger.info(f"Tenant data initialized for school: {school.name}")


# =====================================================
# SERVICE FACTORY
# =====================================================

async def create_tenant_onboarding_service() -> TenantOnboardingService:
    """Create tenant onboarding service with database session"""
    async for db in get_async_session():
        return TenantOnboardingService(db)