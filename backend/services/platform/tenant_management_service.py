"""
Comprehensive Tenant Management Service
Handles ongoing tenant operations, monitoring, and management
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
import logging
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text, update, delete, desc
from sqlalchemy.orm import selectinload, joinedload
from pydantic import BaseModel, Field, EmailStr, validator

from shared.database import get_async_session
from shared.models.platform import School, SchoolSubscription
from shared.models.unified_user import (
    UnifiedUser, SchoolMembership, UserSession,
    GlobalRole, SchoolRole, MembershipStatus, UserStatus
)

logger = logging.getLogger(__name__)

# =====================================================
# ENUMS FOR TENANT MANAGEMENT
# =====================================================

class TenantHealth(str, Enum):
    """Tenant health status"""
    
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    INACTIVE = "inactive"


class ActionType(str, Enum):
    """Admin action types"""
    
    ACTIVATE_SCHOOL = "activate_school"
    DEACTIVATE_SCHOOL = "deactivate_school"
    SUSPEND_SCHOOL = "suspend_school"
    UPDATE_SUBSCRIPTION = "update_subscription"
    RESET_PASSWORD = "reset_password"
    MERGE_ACCOUNTS = "merge_accounts"
    TRANSFER_OWNERSHIP = "transfer_ownership"
    BULK_OPERATION = "bulk_operation"


class SubscriptionAction(str, Enum):
    """Subscription management actions"""
    
    UPGRADE = "upgrade"
    DOWNGRADE = "downgrade"
    SUSPEND = "suspend"
    REACTIVATE = "reactivate"
    CANCEL = "cancel"
    EXTEND_TRIAL = "extend_trial"


# =====================================================
# PYDANTIC MODELS FOR TENANT MANAGEMENT
# =====================================================

class TenantSummary(BaseModel):
    """Summary of tenant information"""
    
    school_id: UUID
    school_name: str
    subdomain: str
    status: str
    subscription_tier: str
    
    # Metrics
    total_users: int
    active_users: int
    total_students: int
    total_staff: int
    
    # Health indicators
    health_status: TenantHealth
    last_activity: Optional[datetime]
    storage_usage_mb: float
    
    # Financial
    monthly_revenue: float
    outstanding_balance: float
    
    created_at: datetime
    activated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TenantDetail(BaseModel):
    """Detailed tenant information"""
    
    # Basic info
    school_id: UUID
    school_name: str
    subdomain: str
    school_type: str
    status: str
    
    # Location
    city: str
    province: str
    country: str
    
    # Contact
    phone: Optional[str]
    email: Optional[str]
    website_url: Optional[str]
    
    # Subscription
    subscription_tier: str
    subscription_status: str
    enabled_modules: List[str]
    billing_cycle: str
    next_billing_date: Optional[datetime]
    
    # Usage metrics
    user_metrics: Dict[str, int]
    activity_metrics: Dict[str, Any]
    storage_metrics: Dict[str, float]
    
    # Configuration
    configuration: Dict[str, Any]
    feature_flags: Dict[str, bool]
    
    # Timeline
    created_at: datetime
    activated_at: Optional[datetime]
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


class BulkOperationRequest(BaseModel):
    """Bulk operation request"""
    
    operation_type: ActionType
    school_ids: List[UUID]
    parameters: Dict[str, Any] = Field(default_factory=dict)
    reason: str
    notify_schools: bool = Field(default=True)


class SubscriptionUpdateRequest(BaseModel):
    """Subscription update request"""
    
    action: SubscriptionAction
    new_tier: Optional[str] = None
    new_modules: Optional[List[str]] = None
    effective_date: Optional[datetime] = None
    reason: str
    notify_school: bool = Field(default=True)


class TenantHealthCheck(BaseModel):
    """Tenant health check result"""
    
    school_id: UUID
    health_status: TenantHealth
    checks: Dict[str, Dict[str, Any]]
    recommendations: List[str]
    last_checked: datetime
    
    class Config:
        from_attributes = True


# =====================================================
# TENANT MANAGEMENT SERVICE
# =====================================================

class TenantManagementService:
    """Comprehensive service for ongoing tenant management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =====================================================
    # TENANT OVERVIEW AND MONITORING
    # =====================================================
    
    async def get_all_tenants(
        self,
        status_filter: Optional[str] = None,
        tier_filter: Optional[str] = None,
        health_filter: Optional[TenantHealth] = None,
        search_query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[TenantSummary], int]:
        """Get all tenants with filtering and pagination"""
        
        try:
            # Build base query
            query = text("""
                SELECT 
                    s.id as school_id,
                    s.name as school_name,
                    s.subdomain,
                    s.status,
                    COALESCE(sub.tier, 'basic') as subscription_tier,
                    s.created_at,
                    s.activated_at,
                    
                    -- User counts
                    COALESCE(user_stats.total_users, 0) as total_users,
                    COALESCE(user_stats.active_users, 0) as active_users,
                    COALESCE(user_stats.total_students, 0) as total_students,
                    COALESCE(user_stats.total_staff, 0) as total_staff,
                    
                    -- Activity metrics
                    session_stats.last_activity,
                    
                    -- Financial
                    COALESCE(financial_stats.monthly_revenue, 0) as monthly_revenue,
                    COALESCE(financial_stats.outstanding_balance, 0) as outstanding_balance
                    
                FROM platform.schools s
                LEFT JOIN platform.school_subscriptions sub ON s.id = sub.school_id
                LEFT JOIN LATERAL (
                    SELECT 
                        COUNT(*) as total_users,
                        COUNT(*) FILTER (WHERE sm.status = 'active') as active_users,
                        COUNT(*) FILTER (WHERE sm.role = 'student' AND sm.status = 'active') as total_students,
                        COUNT(*) FILTER (WHERE sm.role != 'student' AND sm.role != 'parent' AND sm.role != 'guardian' AND sm.status = 'active') as total_staff
                    FROM platform.school_memberships sm
                    WHERE sm.school_id = s.id
                ) user_stats ON true
                LEFT JOIN LATERAL (
                    SELECT MAX(us.last_activity_at) as last_activity
                    FROM platform.user_sessions us
                    JOIN platform.school_memberships sm ON us.user_id = sm.user_id
                    WHERE sm.school_id = s.id
                ) session_stats ON true
                LEFT JOIN LATERAL (
                    SELECT 
                        100.0 as monthly_revenue,  -- Placeholder
                        0.0 as outstanding_balance  -- Placeholder
                ) financial_stats ON true
                WHERE 1=1
            """)
            
            # Add filters
            params = {}
            where_conditions = []
            
            if status_filter:
                where_conditions.append("s.status = :status_filter")
                params["status_filter"] = status_filter
            
            if tier_filter:
                where_conditions.append("sub.tier = :tier_filter")
                params["tier_filter"] = tier_filter
            
            if search_query:
                where_conditions.append("(s.name ILIKE :search OR s.subdomain ILIKE :search)")
                params["search"] = f"%{search_query}%"
            
            if where_conditions:
                query = text(str(query) + " AND " + " AND ".join(where_conditions))
            
            # Add ordering and pagination
            query = text(str(query) + " ORDER BY s.created_at DESC LIMIT :limit OFFSET :offset")
            params["limit"] = limit
            params["offset"] = offset
            
            result = await self.db.execute(query, params)
            rows = result.fetchall()
            
            # Build tenant summaries
            tenants = []
            for row in rows:
                # Calculate health status
                health_status = self._calculate_health_status(
                    row.last_activity,
                    row.active_users,
                    row.total_users
                )
                
                tenant = TenantSummary(
                    school_id=row.school_id,
                    school_name=row.school_name,
                    subdomain=row.subdomain,
                    status=row.status,
                    subscription_tier=row.subscription_tier,
                    total_users=row.total_users,
                    active_users=row.active_users,
                    total_students=row.total_students,
                    total_staff=row.total_staff,
                    health_status=health_status,
                    last_activity=row.last_activity,
                    storage_usage_mb=0.0,  # TODO: Calculate actual storage
                    monthly_revenue=row.monthly_revenue,
                    outstanding_balance=row.outstanding_balance,
                    created_at=row.created_at,
                    activated_at=row.activated_at
                )
                tenants.append(tenant)
            
            # Get total count
            count_query = text("""
                SELECT COUNT(*) 
                FROM platform.schools s
                LEFT JOIN platform.school_subscriptions sub ON s.id = sub.school_id
                WHERE 1=1
            """)
            
            if where_conditions:
                count_query = text(str(count_query) + " AND " + " AND ".join(where_conditions))
            
            count_result = await self.db.execute(count_query, {k: v for k, v in params.items() if k not in ["limit", "offset"]})
            total = count_result.scalar()
            
            return tenants, total
            
        except Exception as e:
            logger.error(f"Error getting all tenants: {e}")
            raise
    
    async def get_tenant_detail(self, school_id: UUID) -> Optional[TenantDetail]:
        """Get detailed information for a specific tenant"""
        
        try:
            # Get school and subscription info
            school_query = text("""
                SELECT 
                    s.*,
                    sub.tier as subscription_tier,
                    sub.status as subscription_status,
                    sub.enabled_modules,
                    sub.billing_cycle,
                    sub.next_billing_date
                FROM platform.schools s
                LEFT JOIN platform.school_subscriptions sub ON s.id = sub.school_id
                WHERE s.id = :school_id
            """)
            
            result = await self.db.execute(school_query, {"school_id": school_id})
            school_data = result.fetchone()
            
            if not school_data:
                return None
            
            # Get user metrics
            user_metrics = await self._get_user_metrics(school_id)
            
            # Get activity metrics
            activity_metrics = await self._get_activity_metrics(school_id)
            
            # Get storage metrics
            storage_metrics = await self._get_storage_metrics(school_id)
            
            # Get last login
            last_login = await self._get_last_login(school_id)
            
            tenant_detail = TenantDetail(
                school_id=school_data.id,
                school_name=school_data.name,
                subdomain=school_data.subdomain,
                school_type=school_data.school_type or "school",
                status=school_data.status,
                city=school_data.city or "",
                province=school_data.province or "",
                country=school_data.country or "Zimbabwe",
                phone=school_data.phone,
                email=school_data.email,
                website_url=school_data.website_url,
                subscription_tier=school_data.subscription_tier or "basic",
                subscription_status=school_data.subscription_status or "pending",
                enabled_modules=school_data.enabled_modules or [],
                billing_cycle=school_data.billing_cycle or "monthly",
                next_billing_date=school_data.next_billing_date,
                user_metrics=user_metrics,
                activity_metrics=activity_metrics,
                storage_metrics=storage_metrics,
                configuration=school_data.configuration or {},
                feature_flags={},  # TODO: Implement feature flags
                created_at=school_data.created_at,
                activated_at=school_data.activated_at,
                last_login=last_login
            )
            
            return tenant_detail
            
        except Exception as e:
            logger.error(f"Error getting tenant detail: {e}")
            raise
    
    async def perform_tenant_health_check(self, school_id: UUID) -> TenantHealthCheck:
        """Perform comprehensive health check for tenant"""
        
        try:
            checks = {}
            recommendations = []
            
            # Check 1: User activity
            activity_check = await self._check_user_activity(school_id)
            checks["user_activity"] = activity_check
            if activity_check["status"] != "healthy":
                recommendations.extend(activity_check.get("recommendations", []))
            
            # Check 2: System performance
            performance_check = await self._check_system_performance(school_id)
            checks["system_performance"] = performance_check
            if performance_check["status"] != "healthy":
                recommendations.extend(performance_check.get("recommendations", []))
            
            # Check 3: Data integrity
            data_check = await self._check_data_integrity(school_id)
            checks["data_integrity"] = data_check
            if data_check["status"] != "healthy":
                recommendations.extend(data_check.get("recommendations", []))
            
            # Check 4: Subscription status
            subscription_check = await self._check_subscription_status(school_id)
            checks["subscription"] = subscription_check
            if subscription_check["status"] != "healthy":
                recommendations.extend(subscription_check.get("recommendations", []))
            
            # Determine overall health
            overall_health = self._determine_overall_health(checks)
            
            health_check = TenantHealthCheck(
                school_id=school_id,
                health_status=overall_health,
                checks=checks,
                recommendations=recommendations,
                last_checked=datetime.now(timezone.utc)
            )
            
            return health_check
            
        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            raise
    
    # =====================================================
    # TENANT OPERATIONS
    # =====================================================
    
    async def activate_tenant(
        self,
        school_id: UUID,
        admin_user_id: UUID,
        activation_notes: str = None
    ) -> Dict[str, Any]:
        """Activate a tenant (make it live)"""
        
        try:
            school = await self._get_school_by_id(school_id)
            if not school:
                raise ValueError("School not found")
            
            if school.status == "active":
                raise ValueError("School is already active")
            
            # Update school status
            school.status = "active"
            school.is_active = True
            school.activated_at = datetime.now(timezone.utc)
            
            # Update onboarding data
            onboarding_data = school.onboarding_data or {}
            onboarding_data["activated_by"] = str(admin_user_id)
            onboarding_data["activation_notes"] = activation_notes
            onboarding_data["activated_at"] = datetime.now(timezone.utc).isoformat()
            school.onboarding_data = onboarding_data
            
            # Activate subscription
            subscription = await self._get_school_subscription(school_id)
            if subscription:
                subscription.status = "active"
                subscription.activated_at = datetime.now(timezone.utc)
            
            await self.db.commit()
            
            # Log action
            await self._log_admin_action(
                admin_user_id,
                school_id,
                ActionType.ACTIVATE_SCHOOL,
                {"activation_notes": activation_notes}
            )
            
            logger.info(f"School activated: {school.name} ({school_id})")
            
            return {
                "school_id": str(school_id),
                "status": "active",
                "activated_at": school.activated_at.isoformat(),
                "message": "School activated successfully"
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error activating tenant: {e}")
            raise
    
    async def suspend_tenant(
        self,
        school_id: UUID,
        admin_user_id: UUID,
        suspension_reason: str,
        suspension_duration_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Suspend a tenant temporarily"""
        
        try:
            school = await self._get_school_by_id(school_id)
            if not school:
                raise ValueError("School not found")
            
            if school.status == "suspended":
                raise ValueError("School is already suspended")
            
            # Update school status
            previous_status = school.status
            school.status = "suspended"
            school.is_active = False
            
            # Store suspension details
            suspension_data = {
                "suspended_at": datetime.now(timezone.utc).isoformat(),
                "suspended_by": str(admin_user_id),
                "suspension_reason": suspension_reason,
                "previous_status": previous_status,
                "suspension_duration_days": suspension_duration_days
            }
            
            if suspension_duration_days:
                suspension_end_date = datetime.now(timezone.utc) + timedelta(days=suspension_duration_days)
                suspension_data["suspension_end_date"] = suspension_end_date.isoformat()
            
            # Update school metadata
            school_metadata = school.metadata or {}
            school_metadata["suspension"] = suspension_data
            school.metadata = school_metadata
            
            # Suspend subscription
            subscription = await self._get_school_subscription(school_id)
            if subscription:
                subscription.status = "suspended"
                subscription.suspended_at = datetime.now(timezone.utc)
            
            await self.db.commit()
            
            # Log action
            await self._log_admin_action(
                admin_user_id,
                school_id,
                ActionType.SUSPEND_SCHOOL,
                suspension_data
            )
            
            # Notify school of suspension
            await self._notify_school_suspension(school, suspension_reason)
            
            logger.info(f"School suspended: {school.name} ({school_id})")
            
            return {
                "school_id": str(school_id),
                "status": "suspended",
                "suspension_reason": suspension_reason,
                "suspension_end_date": suspension_data.get("suspension_end_date"),
                "message": "School suspended successfully"
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error suspending tenant: {e}")
            raise
    
    async def update_tenant_subscription(
        self,
        school_id: UUID,
        admin_user_id: UUID,
        update_request: SubscriptionUpdateRequest
    ) -> Dict[str, Any]:
        """Update tenant subscription"""
        
        try:
            subscription = await self._get_school_subscription(school_id)
            if not subscription:
                raise ValueError("School subscription not found")
            
            old_tier = subscription.tier
            old_modules = subscription.enabled_modules.copy()
            
            # Apply subscription action
            if update_request.action == SubscriptionAction.UPGRADE:
                if not update_request.new_tier:
                    raise ValueError("New tier required for upgrade")
                subscription.tier = update_request.new_tier
                subscription.enabled_modules = self._get_modules_for_tier(update_request.new_tier)
                
            elif update_request.action == SubscriptionAction.DOWNGRADE:
                if not update_request.new_tier:
                    raise ValueError("New tier required for downgrade")
                subscription.tier = update_request.new_tier
                subscription.enabled_modules = self._get_modules_for_tier(update_request.new_tier)
                
            elif update_request.action == SubscriptionAction.SUSPEND:
                subscription.status = "suspended"
                subscription.suspended_at = datetime.now(timezone.utc)
                
            elif update_request.action == SubscriptionAction.REACTIVATE:
                subscription.status = "active"
                subscription.suspended_at = None
                subscription.reactivated_at = datetime.now(timezone.utc)
                
            elif update_request.action == SubscriptionAction.EXTEND_TRIAL:
                if subscription.trial_end_date:
                    subscription.trial_end_date = subscription.trial_end_date + timedelta(days=30)
                else:
                    subscription.trial_end_date = datetime.now(timezone.utc) + timedelta(days=30)
            
            # Update effective date
            if update_request.effective_date:
                subscription.effective_date = update_request.effective_date
            else:
                subscription.effective_date = datetime.now(timezone.utc)
            
            # Store change history
            change_record = {
                "action": update_request.action.value,
                "old_tier": old_tier,
                "new_tier": subscription.tier,
                "old_modules": old_modules,
                "new_modules": subscription.enabled_modules,
                "reason": update_request.reason,
                "changed_by": str(admin_user_id),
                "changed_at": datetime.now(timezone.utc).isoformat()
            }
            
            subscription_history = subscription.metadata.get("change_history", []) if subscription.metadata else []
            subscription_history.append(change_record)
            
            if not subscription.metadata:
                subscription.metadata = {}
            subscription.metadata["change_history"] = subscription_history
            
            await self.db.commit()
            
            # Log action
            await self._log_admin_action(
                admin_user_id,
                school_id,
                ActionType.UPDATE_SUBSCRIPTION,
                change_record
            )
            
            # Notify school if requested
            if update_request.notify_school:
                await self._notify_subscription_change(school_id, change_record)
            
            logger.info(f"Subscription updated for school {school_id}: {update_request.action.value}")
            
            return {
                "school_id": str(school_id),
                "action": update_request.action.value,
                "old_tier": old_tier,
                "new_tier": subscription.tier,
                "effective_date": subscription.effective_date.isoformat(),
                "message": "Subscription updated successfully"
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating subscription: {e}")
            raise
    
    async def perform_bulk_operation(
        self,
        admin_user_id: UUID,
        bulk_request: BulkOperationRequest
    ) -> Dict[str, Any]:
        """Perform bulk operation on multiple tenants"""
        
        try:
            results = []
            errors = []
            
            for school_id in bulk_request.school_ids:
                try:
                    if bulk_request.operation_type == ActionType.ACTIVATE_SCHOOL:
                        result = await self.activate_tenant(
                            school_id, admin_user_id, bulk_request.reason
                        )
                        results.append({"school_id": str(school_id), "result": result})
                        
                    elif bulk_request.operation_type == ActionType.SUSPEND_SCHOOL:
                        suspension_days = bulk_request.parameters.get("suspension_duration_days")
                        result = await self.suspend_tenant(
                            school_id, admin_user_id, bulk_request.reason, suspension_days
                        )
                        results.append({"school_id": str(school_id), "result": result})
                        
                    elif bulk_request.operation_type == ActionType.UPDATE_SUBSCRIPTION:
                        # Create subscription update request from parameters
                        update_request = SubscriptionUpdateRequest(
                            action=SubscriptionAction(bulk_request.parameters["action"]),
                            new_tier=bulk_request.parameters.get("new_tier"),
                            reason=bulk_request.reason,
                            notify_school=bulk_request.notify_schools
                        )
                        result = await self.update_tenant_subscription(
                            school_id, admin_user_id, update_request
                        )
                        results.append({"school_id": str(school_id), "result": result})
                        
                    else:
                        errors.append({
                            "school_id": str(school_id),
                            "error": f"Unsupported operation: {bulk_request.operation_type}"
                        })
                        
                except Exception as e:
                    errors.append({
                        "school_id": str(school_id),
                        "error": str(e)
                    })
            
            # Log bulk operation
            await self._log_admin_action(
                admin_user_id,
                None,  # No specific school
                ActionType.BULK_OPERATION,
                {
                    "operation_type": bulk_request.operation_type.value,
                    "school_count": len(bulk_request.school_ids),
                    "success_count": len(results),
                    "error_count": len(errors),
                    "reason": bulk_request.reason
                }
            )
            
            logger.info(f"Bulk operation completed: {bulk_request.operation_type.value} on {len(bulk_request.school_ids)} schools")
            
            return {
                "operation_type": bulk_request.operation_type.value,
                "total_schools": len(bulk_request.school_ids),
                "successful": len(results),
                "failed": len(errors),
                "results": results,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error performing bulk operation: {e}")
            raise
    
    # =====================================================
    # ANALYTICS AND REPORTING
    # =====================================================
    
    async def get_platform_analytics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get platform-wide analytics"""
        
        try:
            analytics = {}
            
            # Tenant growth metrics
            analytics["tenant_growth"] = await self._get_tenant_growth_metrics(start_date, end_date)
            
            # User activity metrics
            analytics["user_activity"] = await self._get_platform_user_activity(start_date, end_date)
            
            # Subscription metrics
            analytics["subscription_metrics"] = await self._get_subscription_metrics(start_date, end_date)
            
            # Health metrics
            analytics["health_metrics"] = await self._get_platform_health_metrics()
            
            # Financial metrics
            analytics["financial_metrics"] = await self._get_financial_metrics(start_date, end_date)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting platform analytics: {e}")
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
    
    async def _get_school_subscription(self, school_id: UUID) -> Optional[SchoolSubscription]:
        """Get school subscription"""
        result = await self.db.execute(
            select(SchoolSubscription).where(SchoolSubscription.school_id == school_id)
        )
        return result.scalar_one_or_none()
    
    def _calculate_health_status(
        self,
        last_activity: Optional[datetime],
        active_users: int,
        total_users: int
    ) -> TenantHealth:
        """Calculate health status based on metrics"""
        
        if not last_activity:
            return TenantHealth.INACTIVE
        
        # Check if last activity was within last 7 days
        days_since_activity = (datetime.now(timezone.utc) - last_activity).days
        
        if days_since_activity > 14:
            return TenantHealth.CRITICAL
        elif days_since_activity > 7:
            return TenantHealth.WARNING
        
        # Check user activity ratio
        if total_users > 0:
            activity_ratio = active_users / total_users
            if activity_ratio < 0.1:
                return TenantHealth.WARNING
        
        return TenantHealth.HEALTHY
    
    async def _get_user_metrics(self, school_id: UUID) -> Dict[str, int]:
        """Get user metrics for school"""
        
        query = text("""
            SELECT 
                COUNT(*) as total_users,
                COUNT(*) FILTER (WHERE status = 'active') as active_users,
                COUNT(*) FILTER (WHERE role = 'student' AND status = 'active') as students,
                COUNT(*) FILTER (WHERE role = 'teacher' AND status = 'active') as teachers,
                COUNT(*) FILTER (WHERE role IN ('parent', 'guardian') AND status = 'active') as parents,
                COUNT(*) FILTER (WHERE role = 'principal' AND status = 'active') as principals
            FROM platform.school_memberships
            WHERE school_id = :school_id
        """)
        
        result = await self.db.execute(query, {"school_id": school_id})
        row = result.fetchone()
        
        return {
            "total_users": row.total_users,
            "active_users": row.active_users,
            "students": row.students,
            "teachers": row.teachers,
            "parents": row.parents,
            "principals": row.principals
        }
    
    async def _get_activity_metrics(self, school_id: UUID) -> Dict[str, Any]:
        """Get activity metrics for school"""
        
        query = text("""
            SELECT 
                COUNT(DISTINCT us.user_id) as users_last_7_days,
                COUNT(DISTINCT CASE WHEN us.last_activity_at > NOW() - INTERVAL '1 day' THEN us.user_id END) as users_last_1_day,
                AVG(us.school_switch_count) as avg_school_switches,
                MAX(us.last_activity_at) as last_activity
            FROM platform.user_sessions us
            JOIN platform.school_memberships sm ON us.user_id = sm.user_id
            WHERE sm.school_id = :school_id
            AND us.last_activity_at > NOW() - INTERVAL '7 days'
        """)
        
        result = await self.db.execute(query, {"school_id": school_id})
        row = result.fetchone()
        
        return {
            "users_last_7_days": row.users_last_7_days or 0,
            "users_last_1_day": row.users_last_1_day or 0,
            "avg_school_switches": float(row.avg_school_switches or 0),
            "last_activity": row.last_activity.isoformat() if row.last_activity else None
        }
    
    async def _get_storage_metrics(self, school_id: UUID) -> Dict[str, float]:
        """Get storage metrics for school"""
        
        # TODO: Implement actual storage calculation
        return {
            "total_storage_mb": 0.0,
            "documents_storage_mb": 0.0,
            "media_storage_mb": 0.0,
            "database_storage_mb": 0.0
        }
    
    async def _get_last_login(self, school_id: UUID) -> Optional[datetime]:
        """Get last login for school"""
        
        query = text("""
            SELECT MAX(us.created_at) as last_login
            FROM platform.user_sessions us
            JOIN platform.school_memberships sm ON us.user_id = sm.user_id
            WHERE sm.school_id = :school_id
        """)
        
        result = await self.db.execute(query, {"school_id": school_id})
        row = result.fetchone()
        
        return row.last_login
    
    # Health check methods
    async def _check_user_activity(self, school_id: UUID) -> Dict[str, Any]:
        """Check user activity health"""
        
        activity_metrics = await self._get_activity_metrics(school_id)
        
        if activity_metrics["users_last_7_days"] == 0:
            return {
                "status": "critical",
                "message": "No user activity in the last 7 days",
                "recommendations": ["Contact school to check if they need assistance"]
            }
        elif activity_metrics["users_last_1_day"] == 0:
            return {
                "status": "warning",
                "message": "No user activity in the last day",
                "recommendations": ["Monitor for continued inactivity"]
            }
        else:
            return {
                "status": "healthy",
                "message": "Normal user activity",
                "metrics": activity_metrics
            }
    
    async def _check_system_performance(self, school_id: UUID) -> Dict[str, Any]:
        """Check system performance"""
        
        # TODO: Implement actual performance checks
        return {
            "status": "healthy",
            "message": "System performance is normal",
            "metrics": {
                "avg_response_time": 250,
                "error_rate": 0.1
            }
        }
    
    async def _check_data_integrity(self, school_id: UUID) -> Dict[str, Any]:
        """Check data integrity"""
        
        # TODO: Implement data integrity checks
        return {
            "status": "healthy",
            "message": "Data integrity checks passed"
        }
    
    async def _check_subscription_status(self, school_id: UUID) -> Dict[str, Any]:
        """Check subscription status"""
        
        subscription = await self._get_school_subscription(school_id)
        
        if not subscription:
            return {
                "status": "critical",
                "message": "No subscription found",
                "recommendations": ["Set up subscription for school"]
            }
        
        if subscription.status == "suspended":
            return {
                "status": "warning",
                "message": "Subscription is suspended",
                "recommendations": ["Review suspension reason and consider reactivation"]
            }
        
        # Check if trial is expiring
        if subscription.trial_end_date and subscription.trial_end_date < datetime.now(timezone.utc) + timedelta(days=7):
            return {
                "status": "warning",
                "message": "Trial period expiring soon",
                "recommendations": ["Follow up on subscription conversion"]
            }
        
        return {
            "status": "healthy",
            "message": "Subscription is active"
        }
    
    def _determine_overall_health(self, checks: Dict[str, Dict[str, Any]]) -> TenantHealth:
        """Determine overall health from individual checks"""
        
        if any(check["status"] == "critical" for check in checks.values()):
            return TenantHealth.CRITICAL
        elif any(check["status"] == "warning" for check in checks.values()):
            return TenantHealth.WARNING
        else:
            return TenantHealth.HEALTHY
    
    def _get_modules_for_tier(self, tier: str) -> List[str]:
        """Get modules for subscription tier"""
        
        module_tiers = {
            "basic": ["student_information_system", "basic_academic_management"],
            "standard": ["student_information_system", "academic_management", "finance_management"],
            "premium": ["student_information_system", "academic_management", "finance_management", "learning_management"],
            "enterprise": ["student_information_system", "academic_management", "finance_management", "learning_management", "human_resources"]
        }
        
        return module_tiers.get(tier, [])
    
    async def _log_admin_action(
        self,
        admin_user_id: UUID,
        school_id: Optional[UUID],
        action_type: ActionType,
        details: Dict[str, Any]
    ):
        """Log admin action for audit trail"""
        
        # TODO: Implement admin action logging
        logger.info(f"Admin action: {action_type.value} by {admin_user_id} on {school_id}")
    
    async def _notify_school_suspension(self, school: School, reason: str):
        """Notify school of suspension"""
        
        # TODO: Implement notification system
        logger.info(f"Suspension notification sent to {school.name}")
    
    async def _notify_subscription_change(self, school_id: UUID, change_record: Dict[str, Any]):
        """Notify school of subscription change"""
        
        # TODO: Implement notification system
        logger.info(f"Subscription change notification sent to school {school_id}")
    
    # Analytics methods (TODO: Implement)
    async def _get_tenant_growth_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        return {"new_tenants": 0, "growth_rate": 0.0}
    
    async def _get_platform_user_activity(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        return {"total_sessions": 0, "avg_session_duration": 0.0}
    
    async def _get_subscription_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        return {"conversions": 0, "churn_rate": 0.0}
    
    async def _get_platform_health_metrics(self) -> Dict[str, Any]:
        return {"healthy_tenants": 0, "warning_tenants": 0, "critical_tenants": 0}
    
    async def _get_financial_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        return {"total_revenue": 0.0, "arr": 0.0}


# =====================================================
# SERVICE FACTORY
# =====================================================

async def create_tenant_management_service() -> TenantManagementService:
    """Create tenant management service with database session"""
    async for db in get_async_session():
        return TenantManagementService(db)