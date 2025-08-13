"""
Audit Service for OneClass Platform
Provides comprehensive audit logging and reporting capabilities
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, insert, update, delete, and_, or_, func, desc, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..shared.models.audit_log import (
    AuditLog, AuditLogSummary, ActionCategory, ActionType, RiskLevel, 
    ComplianceCategory, ActionContext, ActionDetails, SecurityMetadata
)
from ..shared.models.unified_user import UnifiedUser, SchoolMembership, SchoolRole
from ..shared.database import get_async_session

import logging
import json
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# =====================================================
# AUDIT SERVICE SCHEMAS
# =====================================================

class AuditLogRequest(BaseModel):
    """Request model for creating audit logs"""
    
    school_id: str
    user_id: str
    action_category: ActionCategory
    action_type: ActionType
    action_description: str
    risk_level: RiskLevel = RiskLevel.LOW
    
    # Optional context
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    
    # Detailed information
    action_context: Optional[Dict[str, Any]] = None
    action_details: Optional[Dict[str, Any]] = None
    security_metadata: Optional[Dict[str, Any]] = None
    
    # Results
    success: str = "success"
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    
    # Additional metadata
    correlation_id: Optional[str] = None
    parent_log_id: Optional[str] = None
    batch_id: Optional[str] = None
    compliance_categories: List[ComplianceCategory] = Field(default_factory=list)


class AuditLogFilter(BaseModel):
    """Filter model for audit log queries"""
    
    school_id: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    action_category: Optional[ActionCategory] = None
    action_type: Optional[ActionType] = None
    risk_level: Optional[RiskLevel] = None
    resource_type: Optional[str] = None
    
    # Time filters
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # Compliance filters
    compliance_categories: List[ComplianceCategory] = Field(default_factory=list)
    
    # Status filters
    success: Optional[str] = None
    archived: Optional[str] = "active"
    
    # Pagination
    limit: int = 50
    offset: int = 0
    
    # Sorting
    sort_by: str = "timestamp"
    sort_order: str = "desc"


class AuditReportRequest(BaseModel):
    """Request model for generating audit reports"""
    
    school_id: str
    report_type: str  # daily, weekly, monthly, custom
    start_date: datetime
    end_date: datetime
    
    # Filters
    include_categories: List[ActionCategory] = Field(default_factory=list)
    include_users: List[str] = Field(default_factory=list)
    risk_levels: List[RiskLevel] = Field(default_factory=list)
    
    # Report options
    include_summaries: bool = True
    include_details: bool = False
    include_compliance: bool = True
    format: str = "json"  # json, csv, pdf


# =====================================================
# MAIN AUDIT SERVICE
# =====================================================

class AuditService:
    """Comprehensive audit logging and reporting service"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # =====================================================
    # AUDIT LOG CREATION
    # =====================================================
    
    async def create_audit_log(self, request: AuditLogRequest) -> AuditLog:
        """Create a comprehensive audit log entry"""
        
        try:
            # Get user information
            user_info = await self._get_user_info(request.user_id, request.school_id)
            if not user_info:
                raise ValueError(f"User {request.user_id} not found or not associated with school {request.school_id}")
            
            # Get school information
            school_info = await self._get_school_info(request.school_id)
            if not school_info:
                raise ValueError(f"School {request.school_id} not found")
            
            # Determine retention policy
            retention_until = self._calculate_retention_date(
                request.action_category, 
                request.compliance_categories
            )
            
            # Create audit log entry
            audit_log = AuditLog(
                timestamp=datetime.now(timezone.utc),
                school_id=request.school_id,
                school_name=school_info["name"],
                user_id=user_info["user_id"],
                user_email=user_info["email"],
                user_full_name=user_info["full_name"],
                user_role=user_info["role"],
                action_category=request.action_category.value,
                action_type=request.action_type.value,
                action_description=request.action_description,
                risk_level=request.risk_level.value,
                compliance_categories=[cat.value for cat in request.compliance_categories],
                resource_type=request.resource_type,
                resource_id=request.resource_id,
                resource_name=request.resource_name,
                action_context=request.action_context or {},
                action_details=request.action_details or {},
                security_metadata=request.security_metadata or {},
                success=request.success,
                error_message=request.error_message,
                duration_ms=request.duration_ms,
                correlation_id=request.correlation_id,
                parent_log_id=request.parent_log_id,
                batch_id=request.batch_id,
                retention_until=retention_until
            )
            
            # Save to database
            self.session.add(audit_log)
            await self.session.commit()
            
            # Trigger async processing for high-risk events
            if request.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                asyncio.create_task(self._process_high_risk_event(audit_log))
            
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            await self.session.rollback()
            raise
    
    async def create_bulk_audit_logs(self, requests: List[AuditLogRequest]) -> List[AuditLog]:
        """Create multiple audit log entries efficiently"""
        
        try:
            audit_logs = []
            
            for request in requests:
                # Get cached user/school info to avoid repeated queries
                user_info = await self._get_user_info(request.user_id, request.school_id)
                school_info = await self._get_school_info(request.school_id)
                
                if not user_info or not school_info:
                    continue  # Skip invalid entries
                
                retention_until = self._calculate_retention_date(
                    request.action_category, 
                    request.compliance_categories
                )
                
                audit_log = AuditLog(
                    timestamp=datetime.now(timezone.utc),
                    school_id=request.school_id,
                    school_name=school_info["name"],
                    user_id=user_info["user_id"],
                    user_email=user_info["email"],
                    user_full_name=user_info["full_name"],
                    user_role=user_info["role"],
                    action_category=request.action_category.value,
                    action_type=request.action_type.value,
                    action_description=request.action_description,
                    risk_level=request.risk_level.value,
                    compliance_categories=[cat.value for cat in request.compliance_categories],
                    resource_type=request.resource_type,
                    resource_id=request.resource_id,
                    resource_name=request.resource_name,
                    action_context=request.action_context or {},
                    action_details=request.action_details or {},
                    security_metadata=request.security_metadata or {},
                    success=request.success,
                    error_message=request.error_message,
                    duration_ms=request.duration_ms,
                    correlation_id=request.correlation_id,
                    parent_log_id=request.parent_log_id,
                    batch_id=request.batch_id,
                    retention_until=retention_until
                )
                
                audit_logs.append(audit_log)
            
            # Bulk insert
            self.session.add_all(audit_logs)
            await self.session.commit()
            
            return audit_logs
            
        except Exception as e:
            logger.error(f"Failed to create bulk audit logs: {str(e)}")
            await self.session.rollback()
            raise
    
    # =====================================================
    # AUDIT LOG QUERIES
    # =====================================================
    
    async def get_audit_logs(self, filter_params: AuditLogFilter) -> Dict[str, Any]:
        """Get audit logs with comprehensive filtering"""
        
        try:
            # Build base query
            query = select(AuditLog).options(
                selectinload(AuditLog.user)
            )
            
            # Apply filters
            conditions = []
            
            if filter_params.school_id:
                conditions.append(AuditLog.school_id == filter_params.school_id)
            
            if filter_params.user_id:
                conditions.append(AuditLog.user_id == filter_params.user_id)
            
            if filter_params.user_email:
                conditions.append(AuditLog.user_email.ilike(f"%{filter_params.user_email}%"))
            
            if filter_params.action_category:
                conditions.append(AuditLog.action_category == filter_params.action_category.value)
            
            if filter_params.action_type:
                conditions.append(AuditLog.action_type == filter_params.action_type.value)
            
            if filter_params.risk_level:
                conditions.append(AuditLog.risk_level == filter_params.risk_level.value)
            
            if filter_params.resource_type:
                conditions.append(AuditLog.resource_type == filter_params.resource_type)
            
            if filter_params.start_date:
                conditions.append(AuditLog.timestamp >= filter_params.start_date)
            
            if filter_params.end_date:
                conditions.append(AuditLog.timestamp <= filter_params.end_date)
            
            if filter_params.compliance_categories:
                compliance_values = [cat.value for cat in filter_params.compliance_categories]
                conditions.append(AuditLog.compliance_categories.op('&&')(compliance_values))
            
            if filter_params.success:
                conditions.append(AuditLog.success == filter_params.success)
            
            if filter_params.archived:
                conditions.append(AuditLog.archived == filter_params.archived)
            
            # Apply conditions
            if conditions:
                query = query.where(and_(*conditions))
            
            # Apply sorting
            if filter_params.sort_order.lower() == "desc":
                query = query.order_by(desc(getattr(AuditLog, filter_params.sort_by)))
            else:
                query = query.order_by(getattr(AuditLog, filter_params.sort_by))
            
            # Get total count
            count_query = select(func.count(AuditLog.id))
            if conditions:
                count_query = count_query.where(and_(*conditions))
            
            total_count_result = await self.session.execute(count_query)
            total_count = total_count_result.scalar()
            
            # Apply pagination
            query = query.offset(filter_params.offset).limit(filter_params.limit)
            
            # Execute query
            result = await self.session.execute(query)
            audit_logs = result.scalars().all()
            
            return {
                "audit_logs": [self._serialize_audit_log(log) for log in audit_logs],
                "total_count": total_count,
                "limit": filter_params.limit,
                "offset": filter_params.offset,
                "has_more": (filter_params.offset + filter_params.limit) < total_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get audit logs: {str(e)}")
            raise
    
    async def get_audit_log_by_id(self, log_id: str) -> Optional[AuditLog]:
        """Get specific audit log by ID"""
        
        try:
            query = select(AuditLog).options(
                selectinload(AuditLog.user)
            ).where(AuditLog.id == log_id)
            
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get audit log {log_id}: {str(e)}")
            return None
    
    async def get_user_activity_summary(self, user_id: str, school_id: str, days: int = 30) -> Dict[str, Any]:
        """Get activity summary for a specific user"""
        
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Activity count by category
            category_query = select(
                AuditLog.action_category,
                func.count(AuditLog.id).label('count')
            ).where(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.school_id == school_id,
                    AuditLog.timestamp >= start_date
                )
            ).group_by(AuditLog.action_category)
            
            category_result = await self.session.execute(category_query)
            category_stats = {row.action_category: row.count for row in category_result}
            
            # Risk level distribution
            risk_query = select(
                AuditLog.risk_level,
                func.count(AuditLog.id).label('count')
            ).where(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.school_id == school_id,
                    AuditLog.timestamp >= start_date
                )
            ).group_by(AuditLog.risk_level)
            
            risk_result = await self.session.execute(risk_query)
            risk_stats = {row.risk_level: row.count for row in risk_result}
            
            # Recent high-risk activities
            high_risk_query = select(AuditLog).where(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.school_id == school_id,
                    AuditLog.risk_level.in_(['high', 'critical']),
                    AuditLog.timestamp >= start_date
                )
            ).order_by(desc(AuditLog.timestamp)).limit(10)
            
            high_risk_result = await self.session.execute(high_risk_query)
            high_risk_activities = [
                self._serialize_audit_log(log) for log in high_risk_result.scalars()
            ]
            
            return {
                "user_id": user_id,
                "school_id": school_id,
                "period_days": days,
                "category_stats": category_stats,
                "risk_stats": risk_stats,
                "total_activities": sum(category_stats.values()),
                "high_risk_activities": high_risk_activities
            }
            
        except Exception as e:
            logger.error(f"Failed to get user activity summary: {str(e)}")
            raise
    
    # =====================================================
    # AUDIT REPORTING
    # =====================================================
    
    async def generate_audit_report(self, request: AuditReportRequest) -> Dict[str, Any]:
        """Generate comprehensive audit report"""
        
        try:
            report = {
                "school_id": request.school_id,
                "report_type": request.report_type,
                "period": {
                    "start_date": request.start_date.isoformat(),
                    "end_date": request.end_date.isoformat(),
                },
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Base conditions
            conditions = [
                AuditLog.school_id == request.school_id,
                AuditLog.timestamp >= request.start_date,
                AuditLog.timestamp <= request.end_date
            ]
            
            # Apply filters
            if request.include_categories:
                category_values = [cat.value for cat in request.include_categories]
                conditions.append(AuditLog.action_category.in_(category_values))
            
            if request.include_users:
                conditions.append(AuditLog.user_id.in_(request.include_users))
            
            if request.risk_levels:
                risk_values = [level.value for level in request.risk_levels]
                conditions.append(AuditLog.risk_level.in_(risk_values))
            
            # Summary statistics
            if request.include_summaries:
                report["summaries"] = await self._generate_report_summaries(conditions)
            
            # Detailed activities
            if request.include_details:
                report["details"] = await self._generate_report_details(conditions)
            
            # Compliance report
            if request.include_compliance:
                report["compliance"] = await self._generate_compliance_report(conditions)
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate audit report: {str(e)}")
            raise
    
    async def _generate_report_summaries(self, conditions: List) -> Dict[str, Any]:
        """Generate summary statistics for report"""
        
        # Total activities
        total_query = select(func.count(AuditLog.id)).where(and_(*conditions))
        total_result = await self.session.execute(total_query)
        total_activities = total_result.scalar()
        
        # Activities by category
        category_query = select(
            AuditLog.action_category,
            func.count(AuditLog.id).label('count')
        ).where(and_(*conditions)).group_by(AuditLog.action_category)
        
        category_result = await self.session.execute(category_query)
        category_breakdown = {row.action_category: row.count for row in category_result}
        
        # Risk level distribution
        risk_query = select(
            AuditLog.risk_level,
            func.count(AuditLog.id).label('count')
        ).where(and_(*conditions)).group_by(AuditLog.risk_level)
        
        risk_result = await self.session.execute(risk_query)
        risk_distribution = {row.risk_level: row.count for row in risk_result}
        
        # Success rate
        success_query = select(
            AuditLog.success,
            func.count(AuditLog.id).label('count')
        ).where(and_(*conditions)).group_by(AuditLog.success)
        
        success_result = await self.session.execute(success_query)
        success_breakdown = {row.success: row.count for row in success_result}
        
        # Most active users
        user_query = select(
            AuditLog.user_email,
            AuditLog.user_full_name,
            func.count(AuditLog.id).label('count')
        ).where(and_(*conditions)).group_by(
            AuditLog.user_email, AuditLog.user_full_name
        ).order_by(desc('count')).limit(10)
        
        user_result = await self.session.execute(user_query)
        top_users = [
            {
                "email": row.user_email,
                "name": row.user_full_name,
                "activity_count": row.count
            }
            for row in user_result
        ]
        
        return {
            "total_activities": total_activities,
            "category_breakdown": category_breakdown,
            "risk_distribution": risk_distribution,
            "success_breakdown": success_breakdown,
            "top_users": top_users
        }
    
    async def _generate_report_details(self, conditions: List) -> List[Dict[str, Any]]:
        """Generate detailed activity list for report"""
        
        query = select(AuditLog).where(and_(*conditions)).order_by(
            desc(AuditLog.timestamp)
        ).limit(1000)  # Limit to prevent huge reports
        
        result = await self.session.execute(query)
        activities = [self._serialize_audit_log(log) for log in result.scalars()]
        
        return activities
    
    async def _generate_compliance_report(self, conditions: List) -> Dict[str, Any]:
        """Generate compliance-focused report section"""
        
        # Compliance activities
        compliance_conditions = conditions + [
            func.array_length(AuditLog.compliance_categories, 1) > 0
        ]
        
        compliance_query = select(
            func.unnest(AuditLog.compliance_categories).label('category'),
            func.count().label('count')
        ).where(and_(*compliance_conditions)).group_by('category')
        
        compliance_result = await self.session.execute(compliance_query)
        compliance_breakdown = {row.category: row.count for row in compliance_result}
        
        # High-risk compliance events
        high_risk_compliance_query = select(AuditLog).where(
            and_(
                *compliance_conditions,
                AuditLog.risk_level.in_(['high', 'critical'])
            )
        ).order_by(desc(AuditLog.timestamp)).limit(50)
        
        high_risk_result = await self.session.execute(high_risk_compliance_query)
        high_risk_events = [
            self._serialize_audit_log(log) for log in high_risk_result.scalars()
        ]
        
        return {
            "compliance_breakdown": compliance_breakdown,
            "high_risk_events": high_risk_events,
            "total_compliance_activities": sum(compliance_breakdown.values())
        }
    
    # =====================================================
    # HELPER METHODS
    # =====================================================
    
    async def _get_user_info(self, user_id: str, school_id: str) -> Optional[Dict[str, Any]]:
        """Get user information with school context"""
        
        try:
            query = select(
                UnifiedUser,
                SchoolMembership
            ).join(
                SchoolMembership, UnifiedUser.id == SchoolMembership.user_id
            ).where(
                and_(
                    UnifiedUser.id == user_id,
                    SchoolMembership.school_id == school_id,
                    SchoolMembership.status == "active"
                )
            )
            
            result = await self.session.execute(query)
            row = result.first()
            
            if not row:
                return None
            
            user, membership = row
            
            return {
                "user_id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": membership.role
            }
            
        except Exception as e:
            logger.error(f"Failed to get user info: {str(e)}")
            return None
    
    async def _get_school_info(self, school_id: str) -> Optional[Dict[str, Any]]:
        """Get school information"""
        
        # This would typically query a schools table
        # For now, returning mock data
        return {
            "id": school_id,
            "name": "Unknown School"
        }
    
    def _calculate_retention_date(
        self, 
        action_category: ActionCategory, 
        compliance_categories: List[ComplianceCategory]
    ) -> Optional[datetime]:
        """Calculate retention date based on compliance requirements"""
        
        # Default retention periods (in years)
        retention_periods = {
            ComplianceCategory.FINANCIAL_RECORD: 7,
            ComplianceCategory.ACADEMIC_RECORD: 5,
            ComplianceCategory.DATA_PROTECTION: 3,
            ComplianceCategory.EMPLOYMENT_RECORD: 5,
            ComplianceCategory.MINISTRY_REPORTING: 10,
            ComplianceCategory.SAFETY_COMPLIANCE: 7
        }
        
        # Find maximum retention period
        max_retention = 0
        for category in compliance_categories:
            period = retention_periods.get(category, 1)
            max_retention = max(max_retention, period)
        
        # Category-specific retention
        if action_category in [ActionCategory.FINANCIAL_OPERATIONS, ActionCategory.PAYMENT_PROCESSING]:
            max_retention = max(max_retention, 7)
        elif action_category in [ActionCategory.STUDENT_MANAGEMENT, ActionCategory.ACADEMIC_RECORDS]:
            max_retention = max(max_retention, 5)
        elif action_category == ActionCategory.SECURITY_EVENTS:
            max_retention = max(max_retention, 3)
        
        if max_retention > 0:
            return datetime.now(timezone.utc) + timedelta(days=max_retention * 365)
        
        return None
    
    async def _process_high_risk_event(self, audit_log: AuditLog):
        """Process high-risk events with additional security measures"""
        
        try:
            # Log security alert
            logger.warning(
                f"High-risk event detected: {audit_log.action_type} by {audit_log.user_email} "
                f"in {audit_log.school_name} (Risk: {audit_log.risk_level})"
            )
            
            # Additional processing could include:
            # - Send notifications to administrators
            # - Trigger security workflows
            # - Update risk scores
            # - Log to security systems
            
        except Exception as e:
            logger.error(f"Failed to process high-risk event: {str(e)}")
    
    def _serialize_audit_log(self, audit_log: AuditLog) -> Dict[str, Any]:
        """Serialize audit log for API responses"""
        
        return {
            "id": str(audit_log.id),
            "timestamp": audit_log.timestamp.isoformat(),
            "school_id": str(audit_log.school_id),
            "school_name": audit_log.school_name,
            "user": {
                "id": str(audit_log.user_id),
                "email": audit_log.user_email,
                "full_name": audit_log.user_full_name,
                "role": audit_log.user_role
            },
            "action": {
                "category": audit_log.action_category,
                "type": audit_log.action_type,
                "description": audit_log.action_description
            },
            "risk_level": audit_log.risk_level,
            "compliance_categories": audit_log.compliance_categories or [],
            "resource": {
                "type": audit_log.resource_type,
                "id": audit_log.resource_id,
                "name": audit_log.resource_name
            },
            "context": audit_log.action_context or {},
            "details": audit_log.action_details or {},
            "security": audit_log.security_metadata or {},
            "success": audit_log.success,
            "error_message": audit_log.error_message,
            "duration_ms": audit_log.duration_ms,
            "correlation_id": audit_log.correlation_id
        }


# =====================================================
# AUDIT SERVICE FACTORY
# =====================================================

async def get_audit_service() -> AuditService:
    """Get audit service instance"""
    async with get_async_session() as session:
        return AuditService(session)