"""
User Management Routes
FastAPI routes for role-based user creation and management within schools
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
import csv
import json
import io

from shared.database import get_db
from shared.auth import get_current_active_user
from shared.middleware.tenant_middleware import get_tenant_context, TenantContext
from shared.models.platform_user import PlatformUser, PlatformRole, SchoolRole
# Temporarily comment out fast middleware imports due to dependency issues
# from shared.middleware.fast_user_context_middleware import get_current_user_fast, require_role, require_school_role
from .service import UserManagementService, get_user_management_service
from .schemas import (
    UserCreate, UserUpdate, UserResponse, UserSearchFilter, UserListResponse,
    UserInvitationCreate, UserInvitationResponse, UserInvitationAccept,
    BulkUserImportCreate, BulkUserRecord, BulkUserImportResponse,
    UserRoleCreate, UserRoleUpdate, UserRoleResponse,
    UserProfileUpdate, UserProfileResponse,
    TeacherCreate, StudentCreate, ParentCreate, StaffCreate
)

router = APIRouter(prefix="/users", tags=["User Management"])


# User CRUD operations
@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: PlatformUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
    service: UserManagementService = Depends(get_user_management_service)
):
    """Create a new user within the school"""
    
    # Check permission using new model
    if not current_user.has_permission_in_school("users.create", tenant_context.school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create users"
        )
    
    return await service.create_user(
        school_id=tenant_context.school_id,
        user_data=user_data,
        created_by=current_user.id
    )


@router.get("/", response_model=UserListResponse)
async def list_users(
    filters: UserSearchFilter = Depends(),
    current_user: PlatformUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
    service: UserManagementService = Depends(get_user_management_service)
):
    """List users with filtering and pagination"""
    
    # Check permission using new model
    if not current_user.has_permission_in_school("users.read", tenant_context.school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view users"
        )
    
    return await service.list_users(
        school_id=tenant_context.school_id,
        filters=filters
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: PlatformUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
    service: UserManagementService = Depends(get_user_management_service)
):
    """Get a specific user"""
    
    # Check permission
    if not current_user.has_permission_in_school("users.read", tenant_context.school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view users"
        )
    
    return await service.get_user(
        user_id=user_id,
        school_id=tenant_context.school_id
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: PlatformUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
    service: UserManagementService = Depends(get_user_management_service)
):
    """Update an existing user"""
    
    # Check permission
    if not current_user.has_permission_in_school("users.update", tenant_context.school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update users"
        )
    
    return await service.update_user(
        user_id=user_id,
        school_id=tenant_context.school_id,
        user_data=user_data
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: PlatformUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
    service: UserManagementService = Depends(get_user_management_service)
):
    """Delete a user (soft delete)"""
    
    # Check permission
    if not current_user.has_permission_in_school("users.delete", tenant_context.school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete users"
        )
    
    await service.delete_user(
        user_id=user_id,
        school_id=tenant_context.school_id
    )
    
    return {"message": "User deleted successfully"}


# Role-specific user creation
@router.post("/teachers", response_model=UserResponse)
async def create_teacher(
    teacher_data: TeacherCreate,
    current_user: PlatformUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
    service: UserManagementService = Depends(get_user_management_service)
):
    """Create a new teacher"""
    
    # Check permission
    if not current_user.has_permission_in_school("staff.create", tenant_context.school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create teachers"
        )
    
    # Convert to UserCreate
    user_data = UserCreate(**teacher_data.dict())
    
    return await service.create_user(
        school_id=tenant_context.school_id,
        user_data=user_data,
        created_by=current_user.id
    )


@router.post("/students", response_model=UserResponse)
async def create_student(
    student_data: StudentCreate,
    current_user: PlatformUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
    service: UserManagementService = Depends(get_user_management_service)
):
    """Create a new student"""
    
    # Check permission
    if not current_user.has_permission_in_school("students.create", tenant_context.school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create students"
        )
    
    # Convert to UserCreate
    user_data = UserCreate(**student_data.dict())
    
    return await service.create_user(
        school_id=tenant_context.school_id,
        user_data=user_data,
        created_by=current_user.id
    )


@router.post("/parents", response_model=UserResponse)
async def create_parent(
    parent_data: ParentCreate,
    current_user: PlatformUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
    service: UserManagementService = Depends(get_user_management_service)
):
    """Create a new parent"""
    
    # Check permission
    if not current_user.has_permission_in_school("parents.create", tenant_context.school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create parents"
        )
    
    # Convert to UserCreate
    user_data = UserCreate(**parent_data.dict(exclude={"children_ids", "relationship"}))
    
    return await service.create_user(
        school_id=tenant_context.school_id,
        user_data=user_data,
        created_by=current_user.id
    )


@router.post("/staff", response_model=UserResponse)
async def create_staff(
    staff_data: StaffCreate,
    current_user: PlatformUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
    service: UserManagementService = Depends(get_user_management_service)
):
    """Create a new staff member"""
    
    # Check permission
    if not current_user.has_permission_in_school("staff.create", tenant_context.school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create staff"
        )
    
    # Convert to UserCreate
    user_data = UserCreate(**staff_data.dict())
    
    return await service.create_user(
        school_id=tenant_context.school_id,
        user_data=user_data,
        created_by=current_user.id
    )


# User invitation management
@router.post("/invitations", response_model=UserInvitationResponse)
async def create_invitation(
    invitation_data: UserInvitationCreate,
    current_user: PlatformUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
    service: UserManagementService = Depends(get_user_management_service)
):
    """Create a user invitation"""
    
    # Check permission
    if not current_user.has_permission_in_school("users.invite", tenant_context.school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to invite users"
        )
    
    return await service.create_invitation(
        school_id=tenant_context.school_id,
        invitation_data=invitation_data,
        invited_by=current_user.id
    )


@router.get("/invitations", response_model=List[UserInvitationResponse])
async def list_invitations(
    status: Optional[str] = None,
    current_user: PlatformUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
    service: UserManagementService = Depends(get_user_management_service)
):
    """List user invitations"""
    
    # Check permission
    if not current_user.has_permission_in_school("users.read", tenant_context.school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view invitations"
        )
    
    return await service.list_invitations(
        school_id=tenant_context.school_id,
        status=status
    )


@router.post("/invitations/{invitation_id}/cancel")
async def cancel_invitation(
    invitation_id: str,
    current_user: PlatformUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
    service: UserManagementService = Depends(get_user_management_service)
):
    """Cancel a user invitation"""
    
    # Check permission
    if not current_user.has_permission_in_school("users.invite", tenant_context.school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to cancel invitations"
        )
    
    await service.cancel_invitation(
        invitation_id=invitation_id,
        school_id=tenant_context.school_id
    )
    
    return {"message": "Invitation cancelled successfully"}


# Public invitation acceptance endpoint
@router.post("/invitations/accept", response_model=UserResponse)
async def accept_invitation(
    acceptance_data: UserInvitationAccept,
    service: UserManagementService = Depends(get_user_management_service)
):
    """Accept a user invitation (public endpoint)"""
    
    return await service.accept_invitation(
        token=acceptance_data.token,
        acceptance_data=acceptance_data
    )


# Bulk user operations
@router.post("/bulk-import", response_model=BulkUserImportResponse)
async def bulk_import_users(
    file: UploadFile = File(...),
    import_type: str = Form(...),
    default_role: str = Form("student"),
    send_invitations: bool = Form(True),
    current_user: PlatformUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
    service: UserManagementService = Depends(get_user_management_service)
):
    """Bulk import users from CSV or Excel file"""
    
    # Check permission
    if not current_user.has_permission_in_school("users.bulk_import", tenant_context.school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to bulk import users"
        )
    
    # Process file
    try:
        contents = await file.read()
        
        if import_type == "csv":
            user_records = await _process_csv_file(contents)
        elif import_type == "excel":
            user_records = await _process_excel_file(contents)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type"
            )
        
        # Create import data
        import_data = BulkUserImportCreate(
            import_type=import_type,
            default_role=default_role,
            send_invitations=send_invitations
        )
        
        return await service.bulk_import_users(
            school_id=tenant_context.school_id,
            user_records=user_records,
            import_data=import_data,
            imported_by=current_user.id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing file: {str(e)}"
        )


# User role management
@router.post("/roles", response_model=UserRoleResponse)
async def create_role(
    role_data: UserRoleCreate,
    current_user: PlatformUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
    service: UserManagementService = Depends(get_user_management_service)
):
    """Create a custom user role"""
    
    # Check permission
    if not current_user.has_permission_in_school("roles.create", tenant_context.school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create roles"
        )
    
    return await service.create_role(
        school_id=tenant_context.school_id,
        role_data=role_data,
        created_by=current_user.id
    )


@router.get("/roles", response_model=List[UserRoleResponse])
async def list_roles(
    current_user: PlatformUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
    service: UserManagementService = Depends(get_user_management_service)
):
    """List all roles for the school"""
    
    # Check permission
    if not current_user.has_permission_in_school("roles.read", tenant_context.school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view roles"
        )
    
    return await service.list_roles(
        school_id=tenant_context.school_id
    )


# User profile management
@router.put("/{user_id}/profile", response_model=UserProfileResponse)
async def update_user_profile(
    user_id: str,
    profile_data: UserProfileUpdate,
    current_user: PlatformUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
    service: UserManagementService = Depends(get_user_management_service)
):
    """Update user profile"""
    
    # Check permission (users can update their own profile)
    if user_id != str(current_user.id) and not current_user.has_permission_in_school("users.update", tenant_context.school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update user profile"
        )
    
    return await service.update_profile(
        user_id=user_id,
        school_id=tenant_context.school_id,
        profile_data=profile_data
    )


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    current_user: PlatformUser = Depends(get_current_active_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
    service: UserManagementService = Depends(get_user_management_service)
):
    """Get user profile"""
    
    # Check permission (users can view their own profile)
    if user_id != str(current_user.id) and not current_user.has_permission_in_school("users.read", tenant_context.school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view user profile"
        )
    
    user = await service.get_user(
        user_id=user_id,
        school_id=tenant_context.school_id
    )
    
    return user.profile


# Helper functions
async def _process_csv_file(contents: bytes) -> List[BulkUserRecord]:
    """Process CSV file and return user records"""
    
    csv_data = contents.decode('utf-8')
    reader = csv.DictReader(io.StringIO(csv_data))
    
    user_records = []
    for row in reader:
        try:
            record = BulkUserRecord(
                email=row.get('email'),
                first_name=row.get('first_name'),
                last_name=row.get('last_name'),
                role=row.get('role'),
                phone=row.get('phone'),
                department=row.get('department'),
                position=row.get('position'),
                employee_id=row.get('employee_id'),
                student_id=row.get('student_id'),
                grade_level=row.get('grade_level')
            )
            user_records.append(record)
        except Exception as e:
            continue  # Skip invalid rows
    
    return user_records


async def _process_excel_file(contents: bytes) -> List[BulkUserRecord]:
    """Process Excel file and return user records"""
    
    # This would require openpyxl or similar library
    # For now, return empty list
    return []