"""
Academic Management Authentication Middleware
Integrates Academic module with platform authentication and RLS system
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
from fastapi import HTTPException, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from shared.auth import get_current_active_user, PlatformUser
from shared.middleware.tenant_middleware import get_tenant_context, TenantContext
from shared.database import get_async_session

import logging

logger = logging.getLogger(__name__)

class AcademicPermissions:
    """Academic module specific permissions"""
    
    # Subject permissions
    SUBJECT_READ = "academic.subject.read"
    SUBJECT_CREATE = "academic.subject.create"
    SUBJECT_UPDATE = "academic.subject.update"
    SUBJECT_DELETE = "academic.subject.delete"
    
    # Curriculum permissions
    CURRICULUM_READ = "academic.curriculum.read"
    CURRICULUM_CREATE = "academic.curriculum.create"
    CURRICULUM_UPDATE = "academic.curriculum.update"
    CURRICULUM_DELETE = "academic.curriculum.delete"
    
    # Timetable permissions
    TIMETABLE_READ = "academic.timetable.read"
    TIMETABLE_CREATE = "academic.timetable.create"
    TIMETABLE_UPDATE = "academic.timetable.update"
    TIMETABLE_DELETE = "academic.timetable.delete"
    
    # Attendance permissions
    ATTENDANCE_READ = "academic.attendance.read"
    ATTENDANCE_CREATE = "academic.attendance.create"
    ATTENDANCE_UPDATE = "academic.attendance.update"
    ATTENDANCE_DELETE = "academic.attendance.delete"
    
    # Assessment permissions
    ASSESSMENT_READ = "academic.assessment.read"
    ASSESSMENT_CREATE = "academic.assessment.create"
    ASSESSMENT_UPDATE = "academic.assessment.update"
    ASSESSMENT_DELETE = "academic.assessment.delete"
    
    # Grade permissions
    GRADE_READ = "academic.grade.read"
    GRADE_CREATE = "academic.grade.create"
    GRADE_UPDATE = "academic.grade.update"
    GRADE_DELETE = "academic.grade.delete"
    
    # Lesson plan permissions
    LESSON_PLAN_READ = "academic.lesson_plan.read"
    LESSON_PLAN_CREATE = "academic.lesson_plan.create"
    LESSON_PLAN_UPDATE = "academic.lesson_plan.update"
    LESSON_PLAN_DELETE = "academic.lesson_plan.delete"
    
    # Calendar permissions
    CALENDAR_READ = "academic.calendar.read"
    CALENDAR_CREATE = "academic.calendar.create"
    CALENDAR_UPDATE = "academic.calendar.update"
    CALENDAR_DELETE = "academic.calendar.delete"
    
    # Class management permissions
    CLASS_READ = "academic.class.read"
    CLASS_CREATE = "academic.class.create"
    CLASS_UPDATE = "academic.class.update"
    CLASS_DELETE = "academic.class.delete"
    CLASS_MANAGE_SUBJECTS = "academic.class.manage_subjects"
    CLASS_MANAGE_ENROLLMENT = "academic.class.manage_enrollment"
    CLASS_BULK_CREATE = "academic.class.bulk_create"
    
    # Dashboard permissions
    DASHBOARD_READ = "academic.dashboard.read"
    ANALYTICS_READ = "academic.analytics.read"

class AcademicAuthContext:
    """Authentication context for Academic module operations"""
    
    def __init__(
        self,
        user: PlatformUser,
        tenant: TenantContext,
        school_id: UUID,
        user_role: str,
        permissions: List[str],
        teacher_id: Optional[UUID] = None,
        student_id: Optional[UUID] = None
    ):
        self.user = user
        self.tenant = tenant
        self.school_id = school_id
        self.user_role = user_role
        self.permissions = permissions
        self.teacher_id = teacher_id
        self.student_id = student_id
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions or "*" in self.permissions
    
    def can_access_all_data(self) -> bool:
        """Check if user can access all school data"""
        return self.user_role in ['super_admin', 'school_admin']
    
    def can_manage_subjects(self) -> bool:
        """Check if user can manage subjects"""
        return self.has_permission(AcademicPermissions.SUBJECT_CREATE)
    
    def can_manage_assessments(self) -> bool:
        """Check if user can create assessments"""
        return self.has_permission(AcademicPermissions.ASSESSMENT_CREATE)
    
    def can_enter_grades(self) -> bool:
        """Check if user can enter grades"""
        return self.has_permission(AcademicPermissions.GRADE_CREATE)
    
    def can_mark_attendance(self) -> bool:
        """Check if user can mark attendance"""
        return self.has_permission(AcademicPermissions.ATTENDANCE_CREATE)
    
    def can_view_analytics(self) -> bool:
        """Check if user can view analytics"""
        return self.has_permission(AcademicPermissions.ANALYTICS_READ)
    
    def can_manage_classes(self) -> bool:
        """Check if user can create classes"""
        return self.has_permission(AcademicPermissions.CLASS_CREATE)
    
    def can_view_classes(self) -> bool:
        """Check if user can view classes"""
        return self.has_permission(AcademicPermissions.CLASS_READ)
    
    def can_manage_class_subjects(self) -> bool:
        """Check if user can assign subjects to classes"""
        return self.has_permission(AcademicPermissions.CLASS_MANAGE_SUBJECTS)
    
    def can_manage_class_enrollment(self) -> bool:
        """Check if user can manage student enrollment in classes"""
        return self.has_permission(AcademicPermissions.CLASS_MANAGE_ENROLLMENT)
    
    def can_bulk_manage_classes(self) -> bool:
        """Check if user can perform bulk class operations"""
        return self.has_permission(AcademicPermissions.CLASS_BULK_CREATE)
    
    def can_manage_calendar(self) -> bool:
        """Check if user can manage calendar events"""
        return self.has_permission(AcademicPermissions.CALENDAR_CREATE)
    
    def can_view_calendar(self) -> bool:
        """Check if user can view calendar events"""
        return self.has_permission(AcademicPermissions.CALENDAR_READ)

async def get_academic_auth_context(
    request: Request,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
) -> AcademicAuthContext:
    """
    Get academic authentication context with full permissions and role mapping
    """
    try:
        # Get tenant context from middleware
        tenant_context = get_tenant_context(request)
        school_id = UUID(tenant_context.school_id)
        
        # Get user's school membership for this school
        school_membership = None
        for membership in current_user.school_memberships:
            if membership.school_id == school_id:
                school_membership = membership
                break
        
        if not school_membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have access to this school"
            )
        
        # Map school role to academic permissions
        user_role = school_membership.role.value
        permissions = await _get_academic_permissions(user_role, school_id, db)
        
        # Get additional context (teacher_id, student_id) if applicable
        teacher_id = None
        student_id = None
        
        if user_role == 'teacher' and school_membership.employee_id:
            teacher_id = UUID(current_user.id)  # Use user ID as teacher ID
        
        if user_role == 'student' and school_membership.student_id:
            student_id = UUID(school_membership.student_id)
        
        # Set up database context for RLS
        await _setup_academic_database_context(db, school_id, current_user.id, user_role)
        
        return AcademicAuthContext(
            user=current_user,
            tenant=tenant_context,
            school_id=school_id,
            user_role=user_role,
            permissions=permissions,
            teacher_id=teacher_id,
            student_id=student_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create academic auth context: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to establish authentication context"
        )

async def _get_academic_permissions(
    role: str, 
    school_id: UUID, 
    db: AsyncSession
) -> List[str]:
    """Get academic permissions based on user role"""
    
    # Define role-based permission sets
    role_permissions = {
        'super_admin': ['*'],  # All permissions
        'school_admin': [
            # Full access to all academic functions
            AcademicPermissions.SUBJECT_READ,
            AcademicPermissions.SUBJECT_CREATE,
            AcademicPermissions.SUBJECT_UPDATE,
            AcademicPermissions.SUBJECT_DELETE,
            AcademicPermissions.CURRICULUM_READ,
            AcademicPermissions.CURRICULUM_CREATE,
            AcademicPermissions.CURRICULUM_UPDATE,
            AcademicPermissions.CURRICULUM_DELETE,
            AcademicPermissions.TIMETABLE_READ,
            AcademicPermissions.TIMETABLE_CREATE,
            AcademicPermissions.TIMETABLE_UPDATE,
            AcademicPermissions.TIMETABLE_DELETE,
            AcademicPermissions.ATTENDANCE_READ,
            AcademicPermissions.ATTENDANCE_CREATE,
            AcademicPermissions.ATTENDANCE_UPDATE,
            AcademicPermissions.ATTENDANCE_DELETE,
            AcademicPermissions.ASSESSMENT_READ,
            AcademicPermissions.ASSESSMENT_CREATE,
            AcademicPermissions.ASSESSMENT_UPDATE,
            AcademicPermissions.ASSESSMENT_DELETE,
            AcademicPermissions.GRADE_READ,
            AcademicPermissions.GRADE_CREATE,
            AcademicPermissions.GRADE_UPDATE,
            AcademicPermissions.GRADE_DELETE,
            AcademicPermissions.LESSON_PLAN_READ,
            AcademicPermissions.LESSON_PLAN_CREATE,
            AcademicPermissions.LESSON_PLAN_UPDATE,
            AcademicPermissions.LESSON_PLAN_DELETE,
            AcademicPermissions.CALENDAR_READ,
            AcademicPermissions.CALENDAR_CREATE,
            AcademicPermissions.CALENDAR_UPDATE,
            AcademicPermissions.CALENDAR_DELETE,
            AcademicPermissions.CLASS_READ,
            AcademicPermissions.CLASS_CREATE,
            AcademicPermissions.CLASS_UPDATE,
            AcademicPermissions.CLASS_DELETE,
            AcademicPermissions.CLASS_MANAGE_SUBJECTS,
            AcademicPermissions.CLASS_MANAGE_ENROLLMENT,
            AcademicPermissions.CLASS_BULK_CREATE,
            AcademicPermissions.DASHBOARD_READ,
            AcademicPermissions.ANALYTICS_READ
        ],
        'teacher': [
            # Teachers can read most things and manage their own classes
            AcademicPermissions.SUBJECT_READ,
            AcademicPermissions.CURRICULUM_READ,
            AcademicPermissions.TIMETABLE_READ,
            AcademicPermissions.ATTENDANCE_READ,
            AcademicPermissions.ATTENDANCE_CREATE,
            AcademicPermissions.ATTENDANCE_UPDATE,
            AcademicPermissions.ASSESSMENT_READ,
            AcademicPermissions.ASSESSMENT_CREATE,
            AcademicPermissions.ASSESSMENT_UPDATE,
            AcademicPermissions.GRADE_READ,
            AcademicPermissions.GRADE_CREATE,
            AcademicPermissions.GRADE_UPDATE,
            AcademicPermissions.LESSON_PLAN_READ,
            AcademicPermissions.LESSON_PLAN_CREATE,
            AcademicPermissions.LESSON_PLAN_UPDATE,
            AcademicPermissions.CLASS_READ,
            AcademicPermissions.CLASS_MANAGE_ENROLLMENT,
            AcademicPermissions.CALENDAR_READ,
            AcademicPermissions.DASHBOARD_READ,
            AcademicPermissions.ANALYTICS_READ
        ],
        'student': [
            # Students can only view their own academic data
            AcademicPermissions.SUBJECT_READ,
            AcademicPermissions.TIMETABLE_READ,
            AcademicPermissions.GRADE_READ,
            AcademicPermissions.CALENDAR_READ
        ],
        'parent': [
            # Parents can view their children's academic data
            AcademicPermissions.SUBJECT_READ,
            AcademicPermissions.TIMETABLE_READ,
            AcademicPermissions.ATTENDANCE_READ,
            AcademicPermissions.GRADE_READ,
            AcademicPermissions.CALENDAR_READ
        ],
        'registrar': [
            # Registrars focus on student information but can view academic data
            AcademicPermissions.SUBJECT_READ,
            AcademicPermissions.TIMETABLE_READ,
            AcademicPermissions.ATTENDANCE_READ,
            AcademicPermissions.GRADE_READ,
            AcademicPermissions.CALENDAR_READ,
            AcademicPermissions.DASHBOARD_READ
        ]
    }
    
    base_permissions = role_permissions.get(role, [])
    
    # TODO: In the future, you could add school-specific permission overrides here
    # by querying the database for custom permission configurations
    
    return base_permissions

async def _setup_academic_database_context(
    db: AsyncSession,
    school_id: UUID,
    user_id: str,
    user_role: str
):
    """Set up database context for Academic module RLS policies"""
    try:
        # Set the RLS context variables that our policies use
        await db.execute(text("SET app.current_school_id = :school_id"), {"school_id": str(school_id)})
        await db.execute(text("SET app.current_user_id = :user_id"), {"user_id": user_id})
        await db.execute(text("SET app.current_user_role = :user_role"), {"user_role": user_role})
        
        # Commit the context setup
        await db.commit()
        
    except Exception as e:
        logger.warning(f"Failed to set up database context: {str(e)}")
        # Don't fail the request if context setup fails
        pass

def require_academic_permission(permission: str):
    """Decorator to require specific academic permission"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract auth context from kwargs or dependencies
            auth_context = None
            for arg in args:
                if isinstance(arg, AcademicAuthContext):
                    auth_context = arg
                    break
            
            if not auth_context:
                # Try to get from kwargs
                auth_context = kwargs.get('auth_context')
            
            if not auth_context:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication context required"
                )
            
            if not auth_context.has_permission(permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "insufficient_permissions",
                        "message": f"Permission required: {permission}",
                        "user_role": auth_context.user_role,
                        "required_permission": permission
                    }
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_academic_feature(feature_name: str):
    """Decorator to require specific academic feature availability"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract auth context from args or kwargs
            auth_context = None
            for arg in args:
                if isinstance(arg, AcademicAuthContext):
                    auth_context = arg
                    break
            
            if not auth_context:
                auth_context = kwargs.get('auth_context')
            
            if not auth_context:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication context required"
                )
            
            # Check if academic management module is enabled
            if 'academic_management' not in auth_context.tenant.enabled_modules:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "module_not_available",
                        "message": "Academic Management module is not available in your subscription",
                        "subscription_tier": auth_context.tenant.subscription_tier,
                        "enabled_modules": auth_context.tenant.enabled_modules
                    }
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Convenience dependency functions for common permission checks
async def require_subject_read(auth_context: AcademicAuthContext = Depends(get_academic_auth_context)):
    """Require subject read permission"""
    if not auth_context.has_permission(AcademicPermissions.SUBJECT_READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subject read permission required"
        )
    return auth_context

async def require_subject_write(auth_context: AcademicAuthContext = Depends(get_academic_auth_context)):
    """Require subject write permission"""
    if not auth_context.has_permission(AcademicPermissions.SUBJECT_CREATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subject write permission required"
        )
    return auth_context

async def require_assessment_write(auth_context: AcademicAuthContext = Depends(get_academic_auth_context)):
    """Require assessment write permission"""
    if not auth_context.has_permission(AcademicPermissions.ASSESSMENT_CREATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Assessment write permission required"
        )
    return auth_context

async def require_grade_write(auth_context: AcademicAuthContext = Depends(get_academic_auth_context)):
    """Require grade write permission"""
    if not auth_context.has_permission(AcademicPermissions.GRADE_CREATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Grade write permission required"
        )
    return auth_context

async def require_attendance_write(auth_context: AcademicAuthContext = Depends(get_academic_auth_context)):
    """Require attendance write permission"""
    if not auth_context.has_permission(AcademicPermissions.ATTENDANCE_CREATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Attendance write permission required"
        )
    return auth_context

async def require_analytics_read(auth_context: AcademicAuthContext = Depends(get_academic_auth_context)):
    """Require analytics read permission"""
    if not auth_context.has_permission(AcademicPermissions.ANALYTICS_READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analytics read permission required"
        )
    return auth_context

# Helper function to check teacher ownership of academic records
async def verify_teacher_ownership(
    teacher_id: UUID,
    auth_context: AcademicAuthContext,
    resource_type: str,
    resource_id: UUID,
    db: AsyncSession
) -> bool:
    """Verify that a teacher owns/can access a specific academic resource"""
    
    # Admins can access everything
    if auth_context.can_access_all_data():
        return True
    
    # Only teachers can use this check
    if auth_context.user_role != 'teacher' or not auth_context.teacher_id:
        return False
    
    # Check ownership based on resource type
    try:
        if resource_type == 'assessment':
            query = text("""
                SELECT COUNT(*) FROM academic.assessments 
                WHERE id = :resource_id AND teacher_id = :teacher_id AND school_id = :school_id
            """)
        elif resource_type == 'attendance_session':
            query = text("""
                SELECT COUNT(*) FROM academic.attendance_sessions 
                WHERE id = :resource_id AND teacher_id = :teacher_id AND school_id = :school_id
            """)
        elif resource_type == 'lesson_plan':
            query = text("""
                SELECT COUNT(*) FROM academic.lesson_plans 
                WHERE id = :resource_id AND teacher_id = :teacher_id AND school_id = :school_id
            """)
        elif resource_type == 'timetable':
            query = text("""
                SELECT COUNT(*) FROM academic.timetables 
                WHERE id = :resource_id AND teacher_id = :teacher_id AND school_id = :school_id
            """)
        else:
            return False
        
        result = await db.execute(query, {
            "resource_id": str(resource_id),
            "teacher_id": str(teacher_id),
            "school_id": str(auth_context.school_id)
        })
        
        count = result.scalar()
        return count > 0
        
    except Exception as e:
        logger.error(f"Error verifying teacher ownership: {str(e)}")
        return False