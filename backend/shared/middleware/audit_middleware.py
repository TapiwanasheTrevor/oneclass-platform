"""
Audit Middleware for Automatic Action Logging
Captures all HTTP requests and creates comprehensive audit logs
"""

import time
import uuid
import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, insert

from ..models.audit_log import (
    AuditLog, ActionCategory, ActionType, RiskLevel, ComplianceCategory,
    ActionContext, ActionDetails, SecurityMetadata
)
from ..models.unified_user import UnifiedUser, SchoolRole
from ..database import get_async_session
import logging

logger = logging.getLogger(__name__)

# =====================================================
# AUDIT CONFIGURATION
# =====================================================

class AuditConfig:
    """Configuration for audit logging behavior"""
    
    # Actions that should be logged
    LOG_READ_OPERATIONS = False  # Usually too noisy
    LOG_AUTHENTICATION = True
    LOG_AUTHORIZATION = True
    LOG_DATA_CHANGES = True
    LOG_FINANCIAL_OPERATIONS = True
    LOG_ADMINISTRATIVE_ACTIONS = True
    LOG_SECURITY_EVENTS = True
    
    # Risk level mappings
    HIGH_RISK_ACTIONS = {
        "delete", "bulk_delete", "password_reset", "permission_grant", 
        "permission_revoke", "payment_processed", "data_export", 
        "configuration_update", "user_create"
    }
    
    CRITICAL_RISK_ACTIONS = {
        "bulk_delete", "data_breach_attempt", "suspicious_activity",
        "backup", "restore", "settings_change", "financial_adjustment"
    }
    
    # Compliance mappings
    DATA_PROTECTION_ACTIONS = {
        "student_create", "student_update", "student_delete", "data_export",
        "privacy_settings_change", "consent_management"
    }
    
    FINANCIAL_COMPLIANCE_ACTIONS = {
        "payment_processed", "invoice_generated", "fee_adjustment",
        "financial_report_generated", "payment_method_change"
    }
    
    ACADEMIC_COMPLIANCE_ACTIONS = {
        "grade_update", "attendance_update", "academic_record_change",
        "transcript_generated", "certificate_issued"
    }


# =====================================================
# AUDIT MIDDLEWARE CLASS
# =====================================================

class AuditMiddleware:
    """Middleware for comprehensive audit logging"""
    
    def __init__(self, app):
        self.app = app
        self.config = AuditConfig()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Skip audit for certain paths
        if self._should_skip_audit(request.url.path):
            await self.app(scope, receive, send)
            return
        
        # Capture request start time
        start_time = time.time()
        correlation_id = str(uuid.uuid4())
        
        # Store correlation ID in request state
        request.state.correlation_id = correlation_id
        request.state.audit_start_time = start_time
        
        # Extract request context
        context = await self._extract_request_context(request)
        
        # Create a custom send function to capture response
        response_status = None
        response_body = None
        
        async def audit_send(message):
            nonlocal response_status, response_body
            if message["type"] == "http.response.start":
                response_status = message["status"]
            elif message["type"] == "http.response.body":
                if message.get("body"):
                    response_body = message["body"]
            await send(message)
        
        try:
            # Process request
            await self.app(scope, receive, audit_send)
            
            # Log successful request
            await self._log_request_completion(
                request, context, correlation_id, start_time, 
                response_status, response_body, None
            )
            
        except Exception as e:
            # Log failed request
            await self._log_request_completion(
                request, context, correlation_id, start_time,
                500, None, str(e)
            )
            raise
    
    def _should_skip_audit(self, path: str) -> bool:
        """Determine if path should be skipped from audit logging"""
        skip_paths = [
            "/health", "/metrics", "/docs", "/openapi.json",
            "/static/", "/_next/", "/favicon.ico"
        ]
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    async def _extract_request_context(self, request: Request) -> ActionContext:
        """Extract context information from request"""
        
        # Get IP address (handle proxy headers)
        ip_address = request.headers.get("x-forwarded-for")
        if ip_address:
            ip_address = ip_address.split(",")[0].strip()
        else:
            ip_address = request.client.host if request.client else None
        
        return ActionContext(
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            api_endpoint=str(request.url),
            http_method=request.method,
            request_id=request.state.correlation_id
        )
    
    async def _log_request_completion(
        self,
        request: Request,
        context: ActionContext,
        correlation_id: str,
        start_time: float,
        response_status: Optional[int],
        response_body: Optional[bytes],
        error_message: Optional[str]
    ):
        """Log completed request with all context"""
        
        try:
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Extract user information from request
            user_info = await self._extract_user_info(request)
            if not user_info:
                return  # Skip logging if no user context
            
            # Determine action details
            action_category, action_type, description = self._classify_action(request)
            
            if not self._should_log_action(action_type):
                return  # Skip if action type shouldn't be logged
            
            # Determine risk level
            risk_level = self._determine_risk_level(action_type, request, response_status)
            
            # Extract resource information
            resource_info = self._extract_resource_info(request, response_body)
            
            # Determine compliance categories
            compliance_categories = self._determine_compliance_categories(action_type, resource_info)
            
            # Create action details
            action_details = ActionDetails(
                resource_type=resource_info.get("type"),
                resource_id=resource_info.get("id"),
                resource_name=resource_info.get("name"),
                reason=request.headers.get("x-audit-reason"),
                notes=request.headers.get("x-audit-notes")
            )
            
            # Create security metadata
            security_metadata = SecurityMetadata(
                compliance_categories=compliance_categories,
                automated_risk_score=self._calculate_risk_score(action_type, risk_level, user_info),
                risk_factors=self._identify_risk_factors(request, user_info, duration_ms)
            )
            
            # Create audit log entry
            audit_log = AuditLog(
                timestamp=datetime.now(timezone.utc),
                school_id=user_info["school_id"],
                school_name=user_info["school_name"],
                user_id=user_info["user_id"],
                user_email=user_info["email"],
                user_full_name=user_info["full_name"],
                user_role=user_info["role"],
                action_category=action_category.value,
                action_type=action_type.value,
                action_description=description,
                risk_level=risk_level.value,
                compliance_categories=[cat.value for cat in compliance_categories],
                resource_type=resource_info.get("type"),
                resource_id=resource_info.get("id"),
                resource_name=resource_info.get("name"),
                action_context=context.dict(),
                action_details=action_details.dict(),
                security_metadata=security_metadata.dict(),
                success="success" if not error_message and response_status < 400 else "failure",
                error_message=error_message,
                duration_ms=duration_ms,
                correlation_id=correlation_id
            )
            
            # Save to database (fire and forget to avoid blocking)
            asyncio.create_task(self._save_audit_log(audit_log))
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
    
    async def _extract_user_info(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract user information from request"""
        
        try:
            # Get user from request state (set by auth middleware)
            user = getattr(request.state, "user", None)
            school = getattr(request.state, "current_school", None)
            
            if not user or not school:
                return None
            
            return {
                "user_id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": getattr(request.state, "user_role", "unknown"),
                "school_id": school.id,
                "school_name": school.name
            }
        except Exception:
            return None
    
    def _classify_action(self, request: Request) -> tuple:
        """Classify request into action category, type, and description"""
        
        method = request.method.upper()
        path = request.url.path.lower()
        
        # Authentication actions
        if "/auth/" in path or "/login" in path or "/logout" in path:
            if "login" in path:
                return ActionCategory.AUTHENTICATION, ActionType.LOGIN, f"User login attempt"
            elif "logout" in path:
                return ActionCategory.AUTHENTICATION, ActionType.LOGOUT, f"User logout"
            else:
                return ActionCategory.AUTHENTICATION, ActionType.UPDATE, f"Authentication action"
        
        # Student management
        if "/students" in path:
            if method == "POST":
                return ActionCategory.STUDENT_MANAGEMENT, ActionType.CREATE, "Student created"
            elif method == "PUT" or method == "PATCH":
                return ActionCategory.STUDENT_MANAGEMENT, ActionType.UPDATE, "Student updated"
            elif method == "DELETE":
                return ActionCategory.STUDENT_MANAGEMENT, ActionType.DELETE, "Student deleted"
            else:
                return ActionCategory.STUDENT_MANAGEMENT, ActionType.READ, "Student accessed"
        
        # Staff management
        if "/staff" in path or "/teachers" in path:
            if method == "POST":
                return ActionCategory.STAFF_MANAGEMENT, ActionType.CREATE, "Staff member created"
            elif method == "PUT" or method == "PATCH":
                return ActionCategory.STAFF_MANAGEMENT, ActionType.UPDATE, "Staff member updated"
            elif method == "DELETE":
                return ActionCategory.STAFF_MANAGEMENT, ActionType.DELETE, "Staff member deleted"
            else:
                return ActionCategory.STAFF_MANAGEMENT, ActionType.READ, "Staff member accessed"
        
        # Financial operations
        if "/payments" in path or "/finance" in path or "/fees" in path:
            if method == "POST":
                if "payment" in path:
                    return ActionCategory.FINANCIAL_OPERATIONS, ActionType.PAYMENT_PROCESSED, "Payment processed"
                else:
                    return ActionCategory.FINANCIAL_OPERATIONS, ActionType.CREATE, "Financial record created"
            elif method == "PUT" or method == "PATCH":
                return ActionCategory.FINANCIAL_OPERATIONS, ActionType.UPDATE, "Financial record updated"
            elif method == "DELETE":
                return ActionCategory.FINANCIAL_OPERATIONS, ActionType.DELETE, "Financial record deleted"
            else:
                return ActionCategory.FINANCIAL_OPERATIONS, ActionType.READ, "Financial record accessed"
        
        # School configuration
        if "/settings" in path or "/config" in path:
            if method in ["PUT", "PATCH", "POST"]:
                return ActionCategory.SCHOOL_CONFIGURATION, ActionType.SETTINGS_CHANGE, "School settings updated"
            else:
                return ActionCategory.SCHOOL_CONFIGURATION, ActionType.READ, "School settings accessed"
        
        # Data operations
        if "/import" in path:
            return ActionCategory.DATA_IMPORT, ActionType.IMPORT, "Data import operation"
        elif "/export" in path:
            return ActionCategory.DATA_EXPORT, ActionType.EXPORT, "Data export operation"
        elif "/backup" in path:
            return ActionCategory.DATA_BACKUP, ActionType.BACKUP, "Data backup operation"
        
        # Default classification
        if method == "POST":
            return ActionCategory.USER_MANAGEMENT, ActionType.CREATE, f"Resource created via {path}"
        elif method in ["PUT", "PATCH"]:
            return ActionCategory.USER_MANAGEMENT, ActionType.UPDATE, f"Resource updated via {path}"
        elif method == "DELETE":
            return ActionCategory.USER_MANAGEMENT, ActionType.DELETE, f"Resource deleted via {path}"
        else:
            return ActionCategory.USER_MANAGEMENT, ActionType.READ, f"Resource accessed via {path}"
    
    def _should_log_action(self, action_type: ActionType) -> bool:
        """Determine if action should be logged based on configuration"""
        
        if action_type == ActionType.READ and not self.config.LOG_READ_OPERATIONS:
            return False
        
        return True
    
    def _determine_risk_level(
        self, 
        action_type: ActionType, 
        request: Request, 
        response_status: Optional[int]
    ) -> RiskLevel:
        """Determine risk level based on action and context"""
        
        if action_type.value in self.config.CRITICAL_RISK_ACTIONS:
            return RiskLevel.CRITICAL
        elif action_type.value in self.config.HIGH_RISK_ACTIONS:
            return RiskLevel.HIGH
        elif response_status and response_status >= 400:
            return RiskLevel.MEDIUM
        elif request.method.upper() in ["DELETE", "PUT", "PATCH"]:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _extract_resource_info(
        self, 
        request: Request, 
        response_body: Optional[bytes]
    ) -> Dict[str, str]:
        """Extract information about affected resource"""
        
        path_parts = request.url.path.strip("/").split("/")
        
        resource_info = {}
        
        # Try to extract resource type from URL
        if len(path_parts) >= 2:
            resource_info["type"] = path_parts[-2] if path_parts[-1].isdigit() else path_parts[-1]
        
        # Try to extract resource ID from URL
        if len(path_parts) >= 1 and path_parts[-1].isdigit():
            resource_info["id"] = path_parts[-1]
        
        # Try to extract resource name from response body
        if response_body:
            try:
                response_data = json.loads(response_body.decode())
                if isinstance(response_data, dict):
                    resource_info["name"] = (
                        response_data.get("name") or 
                        response_data.get("title") or 
                        response_data.get("full_name") or
                        response_data.get("school_name")
                    )
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
        
        return resource_info
    
    def _determine_compliance_categories(
        self, 
        action_type: ActionType, 
        resource_info: Dict[str, str]
    ) -> List[ComplianceCategory]:
        """Determine which compliance categories apply"""
        
        categories = []
        
        if action_type.value in self.config.DATA_PROTECTION_ACTIONS:
            categories.append(ComplianceCategory.DATA_PROTECTION)
        
        if action_type.value in self.config.FINANCIAL_COMPLIANCE_ACTIONS:
            categories.append(ComplianceCategory.FINANCIAL_RECORD)
        
        if action_type.value in self.config.ACADEMIC_COMPLIANCE_ACTIONS:
            categories.append(ComplianceCategory.ACADEMIC_RECORD)
        
        # Resource-based compliance
        resource_type = resource_info.get("type", "").lower()
        if resource_type in ["students", "student"]:
            categories.append(ComplianceCategory.DATA_PROTECTION)
        elif resource_type in ["payments", "fees", "finance"]:
            categories.append(ComplianceCategory.FINANCIAL_RECORD)
        elif resource_type in ["grades", "assessments", "academic"]:
            categories.append(ComplianceCategory.ACADEMIC_RECORD)
        
        return categories
    
    def _calculate_risk_score(
        self, 
        action_type: ActionType, 
        risk_level: RiskLevel, 
        user_info: Dict[str, Any]
    ) -> float:
        """Calculate automated risk score (0.0 to 1.0)"""
        
        base_score = {
            RiskLevel.LOW: 0.1,
            RiskLevel.MEDIUM: 0.4,
            RiskLevel.HIGH: 0.7,
            RiskLevel.CRITICAL: 0.9
        }.get(risk_level, 0.1)
        
        # Adjust based on user role
        role = user_info.get("role", "").lower()
        if role in ["principal", "school_admin"]:
            base_score *= 0.8  # Admins are expected to perform high-risk actions
        elif role in ["teacher", "staff"]:
            base_score *= 1.0  # Normal risk
        elif role in ["parent", "student"]:
            base_score *= 1.2  # Higher risk for limited-privilege users
        
        return min(1.0, base_score)
    
    def _identify_risk_factors(
        self, 
        request: Request, 
        user_info: Dict[str, Any], 
        duration_ms: int
    ) -> List[str]:
        """Identify specific risk factors for the action"""
        
        risk_factors = []
        
        # Time-based risk factors
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:
            risk_factors.append("unusual_time_of_day")
        
        # Performance risk factors
        if duration_ms > 5000:  # 5 seconds
            risk_factors.append("slow_response_time")
        
        # IP-based risk factors
        ip_address = request.headers.get("x-forwarded-for") or request.client.host
        if ip_address and not ip_address.startswith("192.168.") and not ip_address.startswith("10."):
            risk_factors.append("external_ip_access")
        
        # Role-based risk factors
        role = user_info.get("role", "").lower()
        path = request.url.path.lower()
        if role == "student" and "/admin" in path:
            risk_factors.append("privilege_escalation_attempt")
        elif role == "parent" and "/staff" in path:
            risk_factors.append("unauthorized_access_attempt")
        
        return risk_factors
    
    async def _save_audit_log(self, audit_log: AuditLog):
        """Save audit log to database asynchronously"""
        
        try:
            async with get_async_session() as session:
                session.add(audit_log)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to save audit log: {str(e)}")


# =====================================================
# AUDIT LOGGING UTILITIES
# =====================================================

async def log_security_event(
    session: AsyncSession,
    user_id: str,
    school_id: str,
    event_type: str,
    description: str,
    risk_level: RiskLevel = RiskLevel.HIGH,
    additional_context: Optional[Dict[str, Any]] = None
):
    """Log a security event manually"""
    
    try:
        # Get user info
        user_query = select(UnifiedUser).where(UnifiedUser.id == user_id)
        user_result = await session.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            return
        
        audit_log = AuditLog(
            timestamp=datetime.now(timezone.utc),
            school_id=school_id,
            school_name="Unknown",  # Would need to fetch from school table
            user_id=user.id,
            user_email=user.email,
            user_full_name=user.full_name,
            user_role="unknown",
            action_category=ActionCategory.SECURITY_EVENTS.value,
            action_type=event_type,
            action_description=description,
            risk_level=risk_level.value,
            action_context=(additional_context or {}),
            success="success"
        )
        
        session.add(audit_log)
        await session.commit()
        
    except Exception as e:
        logger.error(f"Failed to log security event: {str(e)}")


def audit_decorator(
    action_category: ActionCategory,
    action_type: ActionType,
    description: str,
    risk_level: RiskLevel = RiskLevel.LOW
):
    """Decorator for manual audit logging of specific functions"""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            correlation_id = str(uuid.uuid4())
            
            try:
                result = await func(*args, **kwargs)
                success = "success"
                error_message = None
            except Exception as e:
                result = None
                success = "failure"
                error_message = str(e)
                raise
            finally:
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Create audit log entry (would need to extract user/school context)
                # This is a simplified version - full implementation would need request context
                logger.info(f"Audit: {action_category.value}.{action_type.value} - {description} - {success} ({duration_ms}ms)")
            
            return result
        
        return wrapper
    return decorator