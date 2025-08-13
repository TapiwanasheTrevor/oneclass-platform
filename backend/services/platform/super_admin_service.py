"""
Super Admin Service for OneClass Platform Staff
Comprehensive management dashboard for school registrations, migration services, and platform operations
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Union
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select, and_, or_, func, desc, asc, text, update, delete
from pydantic import BaseModel, Field, EmailStr

from shared.database import get_async_session
from shared.models.platform import School, SchoolSubscription
from shared.models.unified_user import UnifiedUser, SchoolMembership, GlobalRole, SchoolRole
from .tenant_onboarding_service import OnboardingStage, VerificationStatus, MigrationServicePackage

import logging

logger = logging.getLogger(__name__)

# =====================================================
# SUPER ADMIN MODELS AND ENUMS
# =====================================================

class SchoolStatus(str, Enum):
    """School status for admin filtering"""
    
    ALL = "all"
    PENDING_VERIFICATION = "pending_verification"
    EMAIL_VERIFIED = "email_verified" 
    DOCUMENTS_SUBMITTED = "documents_submitted"
    DOCUMENTS_APPROVED = "documents_approved"
    SUBSCRIPTION_ACTIVE = "subscription_active"
    ACTIVE = "active"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class MigrationServiceStatus(str, Enum):
    """Migration service status"""
    
    REQUESTED = "requested"
    QUOTED = "quoted"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    DATA_MIGRATION = "data_migration"
    TESTING = "testing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SuperAdminSchoolFilter(BaseModel):
    """Filter model for school listings"""
    
    # Basic filters
    status: Optional[SchoolStatus] = None
    school_type: Optional[str] = None
    province: Optional[str] = None
    subscription_tier: Optional[str] = None
    
    # Migration services
    migration_package: Optional[MigrationServicePackage] = None
    migration_status: Optional[MigrationServiceStatus] = None
    
    # Date filters
    registered_after: Optional[datetime] = None
    registered_before: Optional[datetime] = None
    
    # Search
    search_query: Optional[str] = None
    
    # Pagination
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0)
    
    # Sorting
    sort_by: str = Field("created_at", regex="^(created_at|school_name|status|subscription_tier)$")
    sort_order: str = Field("desc", regex="^(asc|desc)$")


class SchoolRegistrationSummary(BaseModel):
    """Summary of school registration for admin view"""
    
    # Basic information
    school_id: str
    school_name: str
    subdomain: str
    school_type: str
    status: str
    
    # Location
    city: str
    province: str
    
    # Contact
    principal_name: str
    principal_email: str
    principal_phone: str
    
    # Registration details
    student_count: int
    staff_count: int
    ministry_registration_number: str
    
    # Onboarding progress
    onboarding_stage: str
    completion_percentage: float
    
    # Subscription
    subscription_tier: str
    subscription_status: str
    
    # Migration services
    migration_package: Optional[str] = None
    migration_status: Optional[str] = None
    migration_estimated_cost: Optional[Decimal] = None
    
    # Timeline
    registered_at: datetime
    last_activity: Optional[datetime] = None
    estimated_activation: Optional[datetime] = None
    
    # Admin notes
    admin_notes: Optional[str] = None
    assigned_reviewer: Optional[str] = None


class MigrationServiceRequest(BaseModel):
    """Migration service request details"""
    
    school_id: str
    school_name: str
    package: str
    status: str
    
    # Requirements
    current_system: Optional[str] = None
    data_sources: List[str] = []
    student_records_count: Optional[int] = None
    staff_records_count: Optional[int] = None
    financial_data_years: Optional[int] = None
    academic_data_years: Optional[int] = None
    
    # Services
    urgent_migration: bool = False
    onsite_training: bool = False
    weekend_work: bool = False
    
    # Costing
    base_cost: Decimal
    additional_costs: Decimal
    total_estimated_cost: Decimal
    
    # Timeline
    requested_at: datetime
    preferred_completion_weeks: Optional[int] = None
    estimated_start_date: Optional[datetime] = None
    estimated_completion_date: Optional[datetime] = None
    
    # Assignment
    assigned_manager: Optional[str] = None
    assigned_team: List[str] = []
    
    # Special requirements
    special_requirements: Optional[str] = None
    compliance_requirements: List[str] = []


class PlatformMetrics(BaseModel):
    """Overall platform metrics for super admin dashboard"""
    
    # School metrics
    total_schools: int
    active_schools: int
    pending_registrations: int
    registrations_this_month: int
    
    # Onboarding metrics
    schools_by_stage: Dict[str, int]
    average_onboarding_days: float
    onboarding_completion_rate: float
    
    # Migration services metrics  
    migration_requests_pending: int
    migration_projects_active: int
    migration_revenue_this_month: Decimal
    migration_completion_rate: float
    
    # Subscription metrics
    subscription_distribution: Dict[str, int]
    monthly_recurring_revenue: Decimal
    churn_rate: float
    
    # Geographic distribution
    schools_by_province: Dict[str, int]
    
    # Performance metrics
    avg_system_uptime: float
    avg_response_time_ms: float
    
    # Support metrics
    support_tickets_open: int
    avg_resolution_time_hours: float


class SuperAdminAction(BaseModel):
    """Actions that super admin can take"""
    
    action_type: str
    school_id: str
    notes: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# =====================================================
# SUPER ADMIN SERVICE
# =====================================================

class SuperAdminService:
    """Comprehensive super admin service for OneClass platform management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =====================================================
    # SCHOOL REGISTRATION MANAGEMENT
    # =====================================================
    
    async def get_school_registrations(self, filter_params: SuperAdminSchoolFilter) -> Dict[str, Any]:
        """Get school registrations with comprehensive filtering"""
        
        try:
            # Build base query
            query = select(School).options(
                selectinload(School.subscription),
                selectinload(School.principal_user)
            )
            
            # Apply filters
            conditions = []
            
            if filter_params.status and filter_params.status != SchoolStatus.ALL:
                conditions.append(School.status == filter_params.status.value)
            
            if filter_params.school_type:
                conditions.append(School.school_type == filter_params.school_type)
            
            if filter_params.province:
                conditions.append(School.province == filter_params.province)
            
            if filter_params.registered_after:
                conditions.append(School.created_at >= filter_params.registered_after)
            
            if filter_params.registered_before:
                conditions.append(School.created_at <= filter_params.registered_before)
            
            # Search functionality
            if filter_params.search_query:
                search_term = f"%{filter_params.search_query}%"
                conditions.append(
                    or_(
                        School.name.ilike(search_term),
                        School.subdomain.ilike(search_term),
                        School.city.ilike(search_term),
                        School.ministry_registration_number.ilike(search_term)
                    )
                )
            
            # Migration service filters
            if filter_params.migration_package or filter_params.migration_status:
                # This would require filtering based on onboarding_data JSON
                if filter_params.migration_package:
                    conditions.append(
                        School.onboarding_data['migration_requirements']['package'].astext == filter_params.migration_package.value
                    )
            
            # Apply conditions
            if conditions:
                query = query.where(and_(*conditions))
            
            # Apply sorting
            sort_field = getattr(School, filter_params.sort_by, School.created_at)
            if filter_params.sort_order.lower() == "desc":
                query = query.order_by(desc(sort_field))
            else:
                query = query.order_by(asc(sort_field))
            
            # Get total count
            count_query = select(func.count(School.id))
            if conditions:
                count_query = count_query.where(and_(*conditions))
            
            total_count_result = await self.db.execute(count_query)
            total_count = total_count_result.scalar()
            
            # Apply pagination
            query = query.offset(filter_params.offset).limit(filter_params.limit)
            
            # Execute query
            result = await self.db.execute(query)
            schools = result.scalars().all()
            
            # Convert to summary format
            school_summaries = []
            for school in schools:
                summary = await self._create_school_summary(school)
                school_summaries.append(summary)
            
            return {
                "schools": school_summaries,
                "total_count": total_count,
                "limit": filter_params.limit,
                "offset": filter_params.offset,
                "has_more": (filter_params.offset + filter_params.limit) < total_count
            }
            
        except Exception as e:
            logger.error(f"Error getting school registrations: {str(e)}")
            raise
    
    async def get_school_details(self, school_id: UUID) -> Dict[str, Any]:
        """Get comprehensive school details for admin review"""
        
        try:
            # Get school with all relationships
            query = select(School).options(
                selectinload(School.subscription),
                selectinload(School.principal_user),
                selectinload(School.school_memberships).selectinload(SchoolMembership.user)
            ).where(School.id == school_id)
            
            result = await self.db.execute(query)
            school = result.scalar_one_or_none()
            
            if not school:
                return None
            
            onboarding_data = school.onboarding_data or {}
            
            # Build comprehensive details
            details = {
                "basic_info": {
                    "id": str(school.id),
                    "name": school.name,
                    "subdomain": school.subdomain,
                    "type": school.school_type,
                    "status": school.status,
                    "is_active": school.is_active,
                    "ministry_registration": school.ministry_registration_number,
                    "created_at": school.created_at.isoformat()
                },
                
                "location": {
                    "address": school.physical_address,
                    "city": school.city,
                    "province": school.province,
                    "postal_code": school.postal_code,
                    "country": school.country
                },
                
                "contact": {
                    "phone": school.phone,
                    "email": school.email,
                    "website": school.website_url
                },
                
                "capacity": {
                    "student_capacity": school.student_capacity,
                    "current_student_count": school.current_student_count,
                    "staff_count": school.staff_count
                },
                
                "onboarding": {
                    "stage": onboarding_data.get("stage"),
                    "progress": await self._calculate_onboarding_progress(onboarding_data.get("stage")),
                    "registration_data": onboarding_data.get("registration_data", {}),
                    "verification_documents": onboarding_data.get("verification_documents", []),
                    "document_review": onboarding_data.get("document_review"),
                    "principal_info": onboarding_data.get("principal_info", {})
                },
                
                "subscription": None,
                "migration_services": None,
                "team_members": [],
                "admin_notes": school.admin_notes if hasattr(school, 'admin_notes') else None
            }
            
            # Add subscription details
            if school.subscription:
                details["subscription"] = {
                    "tier": school.subscription.tier,
                    "status": school.subscription.status,
                    "trial_start": school.subscription.trial_start_date.isoformat() if school.subscription.trial_start_date else None,
                    "trial_end": school.subscription.trial_end_date.isoformat() if school.subscription.trial_end_date else None,
                    "billing_start": school.subscription.billing_start_date.isoformat() if school.subscription.billing_start_date else None,
                    "enabled_modules": school.subscription.enabled_modules or [],
                    "monthly_cost": self._calculate_monthly_cost(school.subscription.tier, school.current_student_count)
                }
            
            # Add migration service details
            migration_reqs = onboarding_data.get("registration_data", {}).get("migration_requirements")
            if migration_reqs and migration_reqs.get("package") != "none":
                details["migration_services"] = await self._get_migration_service_details(school, migration_reqs)
            
            # Add team members
            if school.school_memberships:
                for membership in school.school_memberships:
                    if membership.user and membership.is_staff:
                        details["team_members"].append({
                            "user_id": str(membership.user.id),
                            "name": membership.user.full_name,
                            "email": membership.user.email,
                            "role": membership.role,
                            "joined_date": membership.joined_date.isoformat() if membership.joined_date else None
                        })
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting school details: {str(e)}")
            raise
    
    async def approve_school_registration(
        self, 
        school_id: UUID, 
        admin_id: UUID, 
        approval_notes: str = None
    ) -> Dict[str, Any]:
        """Approve school registration and move to next stage"""
        
        try:
            school = await self._get_school_by_id(school_id)
            if not school:
                raise ValueError("School not found")
            
            onboarding_data = school.onboarding_data or {}
            current_stage = onboarding_data.get("stage")
            
            if current_stage == OnboardingStage.DOCUMENT_VERIFICATION.value:
                # Approve documents and move to subscription setup
                onboarding_data["stage"] = OnboardingStage.SUBSCRIPTION_SETUP.value
                onboarding_data["documents_approved_at"] = datetime.now(timezone.utc).isoformat()
                onboarding_data["approved_by"] = str(admin_id)
                onboarding_data["approval_notes"] = approval_notes
                
                school.status = "documents_approved"
                
                # Generate subscription setup token
                setup_token = self._generate_setup_token()
                onboarding_data["subscription_setup_token"] = setup_token
                
                # TODO: Send approval email with setup link
                
            elif current_stage == OnboardingStage.FINAL_REVIEW.value:
                # Complete onboarding
                school.status = "active"
                school.is_active = True
                school.activated_at = datetime.now(timezone.utc)
                
                onboarding_data["stage"] = OnboardingStage.COMPLETED.value
                onboarding_data["completed_at"] = datetime.now(timezone.utc).isoformat()
                onboarding_data["final_approved_by"] = str(admin_id)
                onboarding_data["final_approval_notes"] = approval_notes
                
                # Activate subscription
                if school.subscription:
                    school.subscription.status = "active"
                    school.subscription.activated_at = datetime.now(timezone.utc)
                
                # TODO: Send welcome email and initialize tenant data
            
            school.onboarding_data = onboarding_data
            await self.db.commit()
            
            logger.info(f"School approved by admin {admin_id}: {school.name}")
            
            return {
                "school_id": str(school.id),
                "approved": True,
                "new_stage": onboarding_data.get("stage"),
                "setup_token": onboarding_data.get("subscription_setup_token")
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error approving school registration: {str(e)}")
            raise
    
    async def reject_school_registration(
        self,
        school_id: UUID,
        admin_id: UUID,
        rejection_reason: str
    ) -> Dict[str, Any]:
        """Reject school registration"""
        
        try:
            school = await self._get_school_by_id(school_id)
            if not school:
                raise ValueError("School not found")
            
            onboarding_data = school.onboarding_data or {}
            
            # Update to rejected status
            school.status = "rejected"
            onboarding_data["stage"] = OnboardingStage.REJECTED.value
            onboarding_data["rejected_at"] = datetime.now(timezone.utc).isoformat()
            onboarding_data["rejected_by"] = str(admin_id)
            onboarding_data["rejection_reason"] = rejection_reason
            
            school.onboarding_data = onboarding_data
            await self.db.commit()
            
            # TODO: Send rejection email
            
            logger.info(f"School rejected by admin {admin_id}: {school.name}")
            
            return {
                "school_id": str(school.id),
                "rejected": True,
                "reason": rejection_reason
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error rejecting school registration: {str(e)}")
            raise
    
    # =====================================================
    # MIGRATION SERVICES MANAGEMENT
    # =====================================================
    
    async def get_migration_requests(self, status_filter: Optional[MigrationServiceStatus] = None) -> List[MigrationServiceRequest]:
        """Get all migration service requests"""
        
        try:
            # Query schools with migration service requirements
            query = select(School).where(
                School.onboarding_data['registration_data']['migration_requirements']['package'].astext != 'none'
            )
            
            if status_filter:
                query = query.where(
                    School.onboarding_data['migration_requirements']['status'].astext == status_filter.value
                )
            
            result = await self.db.execute(query)
            schools = result.scalars().all()
            
            migration_requests = []
            for school in schools:
                onboarding_data = school.onboarding_data or {}
                registration_data = onboarding_data.get("registration_data", {})
                migration_reqs = registration_data.get("migration_requirements", {})
                
                if migration_reqs.get("package") != "none":
                    request_data = await self._create_migration_service_request(school, migration_reqs)
                    migration_requests.append(request_data)
            
            return migration_requests
            
        except Exception as e:
            logger.error(f"Error getting migration requests: {str(e)}")
            raise
    
    async def update_migration_service_status(
        self,
        school_id: UUID,
        new_status: MigrationServiceStatus,
        admin_id: UUID,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update migration service status"""
        
        try:
            school = await self._get_school_by_id(school_id)
            if not school:
                raise ValueError("School not found")
            
            onboarding_data = school.onboarding_data or {}
            
            # Initialize migration tracking if not exists
            if "migration_service" not in onboarding_data:
                onboarding_data["migration_service"] = {}
            
            # Update migration service status
            onboarding_data["migration_service"]["status"] = new_status.value
            onboarding_data["migration_service"]["last_updated"] = datetime.now(timezone.utc).isoformat()
            onboarding_data["migration_service"]["updated_by"] = str(admin_id)
            
            if notes:
                if "status_history" not in onboarding_data["migration_service"]:
                    onboarding_data["migration_service"]["status_history"] = []
                
                onboarding_data["migration_service"]["status_history"].append({
                    "status": new_status.value,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "admin_id": str(admin_id),
                    "notes": notes
                })
            
            school.onboarding_data = onboarding_data
            await self.db.commit()
            
            logger.info(f"Migration service status updated for {school.name}: {new_status.value}")
            
            return {
                "school_id": str(school.id),
                "migration_status": new_status.value,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating migration service status: {str(e)}")
            raise
    
    async def assign_migration_manager(
        self,
        school_id: UUID,
        manager_id: UUID,
        admin_id: UUID
    ) -> Dict[str, Any]:
        """Assign migration manager to school"""
        
        try:
            school = await self._get_school_by_id(school_id)
            if not school:
                raise ValueError("School not found")
            
            # Get manager details
            manager_query = select(UnifiedUser).where(UnifiedUser.id == manager_id)
            manager_result = await self.db.execute(manager_query)
            manager = manager_result.scalar_one_or_none()
            
            if not manager:
                raise ValueError("Manager not found")
            
            onboarding_data = school.onboarding_data or {}
            
            # Initialize migration service if not exists
            if "migration_service" not in onboarding_data:
                onboarding_data["migration_service"] = {}
            
            # Assign manager
            onboarding_data["migration_service"]["assigned_manager_id"] = str(manager_id)
            onboarding_data["migration_service"]["assigned_manager_name"] = manager.full_name
            onboarding_data["migration_service"]["assigned_manager_email"] = manager.email
            onboarding_data["migration_service"]["assigned_at"] = datetime.now(timezone.utc).isoformat()
            onboarding_data["migration_service"]["assigned_by"] = str(admin_id)
            
            school.onboarding_data = onboarding_data
            await self.db.commit()
            
            logger.info(f"Migration manager assigned to {school.name}: {manager.full_name}")
            
            return {
                "school_id": str(school.id),
                "assigned_manager": {
                    "id": str(manager_id),
                    "name": manager.full_name,
                    "email": manager.email
                }
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error assigning migration manager: {str(e)}")
            raise
    
    # =====================================================
    # PLATFORM METRICS AND ANALYTICS
    # =====================================================
    
    async def get_platform_metrics(self) -> PlatformMetrics:
        """Get comprehensive platform metrics for super admin dashboard"""
        
        try:
            # Basic school counts
            total_schools_query = select(func.count(School.id))
            active_schools_query = select(func.count(School.id)).where(School.is_active == True)
            pending_query = select(func.count(School.id)).where(School.status.in_([
                "pending_verification", "email_verified", "documents_submitted"
            ]))
            
            total_schools = await self._execute_count_query(total_schools_query)
            active_schools = await self._execute_count_query(active_schools_query)
            pending_registrations = await self._execute_count_query(pending_query)
            
            # This month registrations
            start_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_registrations_query = select(func.count(School.id)).where(
                School.created_at >= start_of_month
            )
            registrations_this_month = await self._execute_count_query(month_registrations_query)
            
            # Schools by onboarding stage
            stages_query = select(
                func.json_extract(School.onboarding_data, '$.stage').label('stage'),
                func.count(School.id).label('count')
            ).group_by('stage')
            
            stages_result = await self.db.execute(stages_query)
            schools_by_stage = {row.stage or "initial": row.count for row in stages_result}
            
            # Migration service metrics
            migration_requests_query = select(func.count(School.id)).where(
                func.json_extract(School.onboarding_data, '$.registration_data.migration_requirements.package') != 'none'
            )
            migration_requests_total = await self._execute_count_query(migration_requests_query)
            
            # Subscription distribution
            subscription_query = select(
                SchoolSubscription.tier,
                func.count(SchoolSubscription.id).label('count')
            ).group_by(SchoolSubscription.tier)
            
            subscription_result = await self.db.execute(subscription_query)
            subscription_distribution = {row.tier: row.count for row in subscription_result}
            
            # Calculate MRR (Monthly Recurring Revenue)
            mrr = await self._calculate_monthly_recurring_revenue()
            
            # Geographic distribution
            provinces_query = select(
                School.province,
                func.count(School.id).label('count')
            ).group_by(School.province)
            
            provinces_result = await self.db.execute(provinces_query)
            schools_by_province = {row.province or "Unknown": row.count for row in provinces_result}
            
            return PlatformMetrics(
                total_schools=total_schools,
                active_schools=active_schools,
                pending_registrations=pending_registrations,
                registrations_this_month=registrations_this_month,
                
                schools_by_stage=schools_by_stage,
                average_onboarding_days=await self._calculate_avg_onboarding_days(),
                onboarding_completion_rate=await self._calculate_onboarding_completion_rate(),
                
                migration_requests_pending=migration_requests_total,
                migration_projects_active=0,  # Would need proper migration project tracking
                migration_revenue_this_month=Decimal("0"),  # Would calculate from completed migrations
                migration_completion_rate=0.85,  # Placeholder
                
                subscription_distribution=subscription_distribution,
                monthly_recurring_revenue=mrr,
                churn_rate=0.02,  # Placeholder - would need proper calculation
                
                schools_by_province=schools_by_province,
                
                avg_system_uptime=99.95,  # Placeholder - would get from monitoring
                avg_response_time_ms=150,  # Placeholder - would get from monitoring
                
                support_tickets_open=12,  # Placeholder - would get from support system
                avg_resolution_time_hours=4.2  # Placeholder - would get from support system
            )
            
        except Exception as e:
            logger.error(f"Error getting platform metrics: {str(e)}")
            raise
    
    async def get_school_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get school analytics for specified period"""
        
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Registration trends
            daily_registrations_query = text("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM schools 
                WHERE created_at >= :start_date
                GROUP BY DATE(created_at)
                ORDER BY date
            """)
            
            daily_result = await self.db.execute(daily_registrations_query, {"start_date": start_date})
            daily_registrations = [
                {"date": row.date.isoformat(), "count": row.count}
                for row in daily_result
            ]
            
            # Conversion funnel
            funnel_data = await self._calculate_conversion_funnel(start_date)
            
            # Top performing regions
            regional_query = select(
                School.province,
                func.count(School.id).label('registrations'),
                func.count(School.id).filter(School.is_active == True).label('active')
            ).where(
                School.created_at >= start_date
            ).group_by(School.province).order_by(desc('registrations')).limit(10)
            
            regional_result = await self.db.execute(regional_query)
            top_regions = [
                {
                    "province": row.province,
                    "registrations": row.registrations,
                    "active": row.active,
                    "conversion_rate": (row.active / row.registrations * 100) if row.registrations > 0 else 0
                }
                for row in regional_result
            ]
            
            return {
                "period_days": days,
                "daily_registrations": daily_registrations,
                "conversion_funnel": funnel_data,
                "top_regions": top_regions,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting school analytics: {str(e)}")
            raise
    
    # =====================================================
    # HELPER METHODS
    # =====================================================
    
    async def _get_school_by_id(self, school_id: UUID) -> Optional[School]:
        """Get school by ID"""
        result = await self.db.execute(
            select(School).where(School.id == school_id)
        )
        return result.scalar_one_or_none()
    
    async def _create_school_summary(self, school: School) -> SchoolRegistrationSummary:
        """Create school registration summary from school object"""
        
        onboarding_data = school.onboarding_data or {}
        registration_data = onboarding_data.get("registration_data", {})
        principal_info = onboarding_data.get("principal_info", {})
        
        # Get migration service info
        migration_reqs = registration_data.get("migration_requirements", {})
        migration_package = migration_reqs.get("package") if migration_reqs.get("package") != "none" else None
        migration_cost = None
        
        if migration_package:
            migration_cost = await self._calculate_migration_cost(migration_reqs)
        
        return SchoolRegistrationSummary(
            school_id=str(school.id),
            school_name=school.name,
            subdomain=school.subdomain,
            school_type=school.school_type,
            status=school.status,
            
            city=school.city,
            province=school.province,
            
            principal_name=principal_info.get("name", "Unknown"),
            principal_email=principal_info.get("email", school.email or ""),
            principal_phone=principal_info.get("phone", school.phone or ""),
            
            student_count=school.current_student_count,
            staff_count=school.staff_count,
            ministry_registration_number=school.ministry_registration_number,
            
            onboarding_stage=onboarding_data.get("stage", "initial_registration"),
            completion_percentage=await self._calculate_onboarding_progress(onboarding_data.get("stage")),
            
            subscription_tier=school.subscription.tier if school.subscription else "unknown",
            subscription_status=school.subscription.status if school.subscription else "pending",
            
            migration_package=migration_package,
            migration_status=onboarding_data.get("migration_service", {}).get("status"),
            migration_estimated_cost=migration_cost,
            
            registered_at=school.created_at,
            last_activity=school.updated_at if hasattr(school, 'updated_at') else None,
            estimated_activation=await self._estimate_activation_date(onboarding_data.get("stage"))
        )
    
    async def _calculate_onboarding_progress(self, stage: str) -> float:
        """Calculate onboarding progress percentage"""
        stage_weights = {
            "initial_registration": 10,
            "email_verification": 20,
            "document_verification": 35,
            "subscription_setup": 50,
            "admin_setup": 65,
            "module_configuration": 80,
            "customization": 90,
            "final_review": 95,
            "completed": 100
        }
        return stage_weights.get(stage, 0)
    
    async def _calculate_migration_cost(self, migration_reqs: Dict[str, Any]) -> Decimal:
        """Calculate estimated migration cost"""
        package_costs = {
            "basic": Decimal("500"),
            "standard": Decimal("1500"),
            "premium": Decimal("2500"),
            "enterprise": Decimal("5000")
        }
        
        base_cost = package_costs.get(migration_reqs.get("package", "basic"), Decimal("500"))
        additional_cost = Decimal("0")
        
        if migration_reqs.get("urgent_migration"):
            additional_cost += Decimal("1000")
        if migration_reqs.get("onsite_training"):
            additional_cost += Decimal("800")
        if migration_reqs.get("weekend_work"):
            additional_cost += Decimal("500")
        
        return base_cost + additional_cost
    
    async def _estimate_activation_date(self, current_stage: str) -> Optional[datetime]:
        """Estimate when school will be activated"""
        stage_durations = {
            "email_verification": 1,
            "document_verification": 3,
            "subscription_setup": 1,
            "admin_setup": 1,
            "module_configuration": 2,
            "customization": 1,
            "final_review": 2,
        }
        
        remaining_days = stage_durations.get(current_stage, 0)
        
        # Add subsequent stage durations
        stages_order = [
            "email_verification", "document_verification", "subscription_setup",
            "admin_setup", "module_configuration", "customization", "final_review"
        ]
        
        if current_stage in stages_order:
            current_index = stages_order.index(current_stage)
            for i in range(current_index + 1, len(stages_order)):
                remaining_days += stage_durations.get(stages_order[i], 1)
        
        if remaining_days > 0:
            return datetime.now(timezone.utc) + timedelta(days=remaining_days)
        
        return None
    
    async def _execute_count_query(self, query) -> int:
        """Execute count query and return result"""
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def _calculate_monthly_recurring_revenue(self) -> Decimal:
        """Calculate total MRR from active subscriptions"""
        try:
            # This would need the actual subscription pricing calculation
            # For now, return a placeholder
            return Decimal("25000.00")
        except:
            return Decimal("0.00")
    
    async def _calculate_avg_onboarding_days(self) -> float:
        """Calculate average onboarding completion time"""
        try:
            # This would need to query completed onboardings and calculate average
            return 8.5  # Placeholder
        except:
            return 0.0
    
    async def _calculate_onboarding_completion_rate(self) -> float:
        """Calculate onboarding completion rate"""
        try:
            total_query = select(func.count(School.id))
            completed_query = select(func.count(School.id)).where(School.is_active == True)
            
            total = await self._execute_count_query(total_query)
            completed = await self._execute_count_query(completed_query)
            
            return (completed / total * 100) if total > 0 else 0.0
        except:
            return 0.0
    
    async def _calculate_conversion_funnel(self, start_date: datetime) -> Dict[str, Any]:
        """Calculate conversion funnel metrics"""
        try:
            stages = [
                "initial_registration",
                "email_verification", 
                "document_verification",
                "subscription_setup",
                "completed"
            ]
            
            funnel_data = {}
            for stage in stages:
                count_query = select(func.count(School.id)).where(
                    and_(
                        School.created_at >= start_date,
                        func.json_extract(School.onboarding_data, '$.stage') == stage
                    )
                )
                count = await self._execute_count_query(count_query)
                funnel_data[stage] = count
            
            return funnel_data
        except:
            return {}
    
    async def _get_migration_service_details(self, school: School, migration_reqs: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed migration service information"""
        
        estimated_cost = await self._calculate_migration_cost(migration_reqs)
        
        return {
            "package": migration_reqs.get("package"),
            "current_system": migration_reqs.get("current_system"),
            "data_sources": migration_reqs.get("data_sources", []),
            "estimated_cost": estimated_cost,
            "urgent_migration": migration_reqs.get("urgent_migration", False),
            "onsite_training": migration_reqs.get("onsite_training", False),
            "special_requirements": migration_reqs.get("special_requirements")
        }
    
    async def _create_migration_service_request(self, school: School, migration_reqs: Dict[str, Any]) -> MigrationServiceRequest:
        """Create migration service request object"""
        
        base_cost = await self._calculate_migration_cost(migration_reqs)
        additional_costs = Decimal("0")
        
        if migration_reqs.get("urgent_migration"):
            additional_costs += Decimal("1000")
        if migration_reqs.get("onsite_training"):
            additional_costs += Decimal("800")
        if migration_reqs.get("weekend_work"):
            additional_costs += Decimal("500")
        
        onboarding_data = school.onboarding_data or {}
        migration_service = onboarding_data.get("migration_service", {})
        
        return MigrationServiceRequest(
            school_id=str(school.id),
            school_name=school.name,
            package=migration_reqs.get("package", "basic"),
            status=migration_service.get("status", MigrationServiceStatus.REQUESTED.value),
            
            current_system=migration_reqs.get("current_system"),
            data_sources=migration_reqs.get("data_sources", []),
            student_records_count=migration_reqs.get("student_records_count"),
            staff_records_count=migration_reqs.get("staff_records_count"),
            financial_data_years=migration_reqs.get("financial_data_years"),
            academic_data_years=migration_reqs.get("academic_data_years"),
            
            urgent_migration=migration_reqs.get("urgent_migration", False),
            onsite_training=migration_reqs.get("onsite_training", False),
            weekend_work=migration_reqs.get("weekend_work", False),
            
            base_cost=base_cost - additional_costs,
            additional_costs=additional_costs,
            total_estimated_cost=base_cost,
            
            requested_at=school.created_at,
            preferred_completion_weeks=migration_reqs.get("preferred_completion_weeks"),
            
            assigned_manager=migration_service.get("assigned_manager_name"),
            special_requirements=migration_reqs.get("special_requirements"),
            compliance_requirements=migration_reqs.get("compliance_requirements", [])
        )
    
    def _calculate_monthly_cost(self, tier: str, student_count: int) -> Decimal:
        """Calculate monthly subscription cost"""
        pricing = {
            "starter": Decimal("3.50"),
            "professional": Decimal("5.50"),  
            "enterprise": Decimal("8.00")
        }
        
        price_per_student = pricing.get(tier.lower(), Decimal("5.50"))
        return price_per_student * student_count
    
    def _generate_setup_token(self) -> str:
        """Generate setup token"""
        import secrets
        return secrets.token_urlsafe(32)


# =====================================================
# SERVICE FACTORY
# =====================================================

async def get_super_admin_service() -> SuperAdminService:
    """Get super admin service instance"""
    async with get_async_session() as session:
        return SuperAdminService(session)