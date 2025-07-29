"""
Migration Services API Routes
Professional data migration and care package management endpoints
"""
from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from shared.database import get_db
from shared.auth import get_current_active_user
from shared.models.platform_user import PlatformUser, PlatformRole
from shared.models.migration_services import (
    CarePackageCreate, CarePackageUpdate, CarePackageResponse,
    CarePackageOrderCreate, CarePackageOrderUpdate, CarePackageOrderResponse,
    MigrationTaskCreate, MigrationTaskUpdate, MigrationTaskResponse,
    DataSourceCreate, DataSourceUpdate, DataSourceResponse,
    CommunicationLogCreate, CommunicationLogResponse,
    PaymentCreate, PaymentUpdate, PaymentResponse,
    MilestoneCreate, MilestoneUpdate, MilestoneResponse,
    TeamPerformanceCreate, TeamPerformanceUpdate, TeamPerformanceResponse,
    MigrationServicesDashboard, OrderFilters, OrderAnalytics,
    OrderStatus, PaymentStatus, TaskStatus
)
from services.migration_services.service import MigrationServicesService

router = APIRouter(prefix="/api/v1/migration-services", tags=["Migration Services"])


# Care Package Management
@router.get("/care-packages", response_model=List[CarePackageResponse])
async def get_care_packages(
    active_only: bool = Query(True, description="Only return active packages"),
    db: Session = Depends(get_db)
):
    """Get all available care packages"""
    service = MigrationServicesService(db)
    return await service.get_care_packages(active_only=active_only)


@router.get("/care-packages/{package_id}", response_model=CarePackageResponse)
async def get_care_package(
    package_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific care package"""
    service = MigrationServicesService(db)
    package = await service.get_care_package(package_id)
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Care package not found"
        )
    
    return package


@router.post("/care-packages", response_model=CarePackageResponse)
async def create_care_package(
    package_data: CarePackageCreate,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new care package (Super admin only)"""
    # Verify super admin permissions
    if current_user.platform_role != PlatformRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform administrators can create care packages"
        )
    
    service = MigrationServicesService(db)
    return await service.create_care_package(package_data)


@router.put("/care-packages/{package_id}", response_model=CarePackageResponse)
async def update_care_package(
    package_id: UUID,
    package_data: CarePackageUpdate,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a care package (Super admin only)"""
    # Verify super admin permissions
    if current_user.platform_role != PlatformRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform administrators can update care packages"
        )
    
    service = MigrationServicesService(db)
    package = await service.update_care_package(package_id, package_data)
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Care package not found"
        )
    
    return package


# Care Package Order Management
@router.post("/orders", response_model=CarePackageOrderResponse)
async def create_care_package_order(
    order_data: CarePackageOrderCreate,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new care package order"""
    # Verify user can create orders for this school
    if current_user.platform_role != PlatformRole.SUPER_ADMIN and current_user.primary_school_id != order_data.school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create orders for your own school"
        )
    
    service = MigrationServicesService(db)
    return await service.create_care_package_order(order_data, current_user.id)


@router.get("/orders", response_model=List[CarePackageOrderResponse])
async def get_care_package_orders(
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    payment_status: Optional[PaymentStatus] = Query(None, description="Filter by payment status"),
    assigned_manager: Optional[UUID] = Query(None, description="Filter by assigned manager"),
    school_name: Optional[str] = Query(None, description="Filter by school name"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    limit: int = Query(50, ge=1, le=100, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset results"),
    current_user: PlatformUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get care package orders with filtering"""
    # Create filters
    filters = OrderFilters(
        status=status,
        payment_status=payment_status,
        assigned_manager=assigned_manager,
        school_name=school_name,
        date_from=date_from,
        date_to=date_to
    )
    
    # School filtering for non-admin users
    school_id = None if current_user.platform_role == PlatformRole.SUPER_ADMIN else current_user.primary_school_id
    
    service = MigrationServicesService(db)
    return await service.get_care_package_orders(filters, school_id, limit, offset)


@router.get("/orders/{order_id}", response_model=CarePackageOrderResponse)
async def get_care_package_order(
    order_id: UUID,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific care package order"""
    service = MigrationServicesService(db)
    order = await service.get_care_package_order(order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Care package order not found"
        )
    
    # Verify access permissions
    if current_user.platform_role != PlatformRole.SUPER_ADMIN and current_user.primary_school_id != order.school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view orders for your own school"
        )
    
    return order


@router.put("/orders/{order_id}", response_model=CarePackageOrderResponse)
async def update_care_package_order(
    order_id: UUID,
    order_data: CarePackageOrderUpdate,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a care package order"""
    # Get existing order to check permissions
    service = MigrationServicesService(db)
    existing_order = await service.get_care_package_order(order_id)
    
    if not existing_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Care package order not found"
        )
    
    # Verify permissions
    if current_user.platform_role != PlatformRole.SUPER_ADMIN and current_user.primary_school_id != existing_order.school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update orders for your own school"
        )
    
    # Super admin can update all fields, schools can only update limited fields
    if current_user.platform_role != PlatformRole.SUPER_ADMIN:
        # Remove admin-only fields
        restricted_fields = [
            "status", "assigned_migration_manager", "assigned_technical_lead",
            "assigned_data_specialist", "assigned_training_specialist",
            "progress_percentage", "payment_status"
        ]
        update_dict = order_data.dict(exclude_unset=True)
        for field in restricted_fields:
            update_dict.pop(field, None)
        order_data = CarePackageOrderUpdate(**update_dict)
    
    return await service.update_care_package_order(order_id, order_data, current_user.id)


# Migration Task Management
@router.post("/orders/{order_id}/tasks", response_model=MigrationTaskResponse)
async def create_migration_task(
    order_id: UUID,
    task_data: MigrationTaskCreate,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new migration task"""
    # Verify super admin or assigned to the order
    if current_user.platform_role != PlatformRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform administrators can create migration tasks"
        )
    
    # Ensure task is for the correct order
    task_data.care_package_order_id = order_id
    
    service = MigrationServicesService(db)
    return await service.create_migration_task(task_data, current_user.id)


@router.get("/orders/{order_id}/tasks", response_model=List[MigrationTaskResponse])
async def get_migration_tasks(
    order_id: UUID,
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    current_user: PlatformUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get migration tasks for an order"""
    # Verify access to order
    service = MigrationServicesService(db)
    order = await service.get_care_package_order(order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Care package order not found"
        )
    
    if current_user.platform_role != PlatformRole.SUPER_ADMIN and current_user.primary_school_id != order.school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view tasks for your own school's orders"
        )
    
    return await service.get_migration_tasks(order_id, status)


@router.put("/tasks/{task_id}", response_model=MigrationTaskResponse)
async def update_migration_task(
    task_id: UUID,
    task_data: MigrationTaskUpdate,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a migration task"""
    # Verify super admin or assigned to the task
    if current_user.platform_role != PlatformRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform administrators can update migration tasks"
        )
    
    service = MigrationServicesService(db)
    task = await service.update_migration_task(task_id, task_data, current_user.id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Migration task not found"
        )
    
    return task


# Dashboard and Analytics
@router.get("/dashboard", response_model=MigrationServicesDashboard)
async def get_migration_dashboard(
    current_user: PlatformUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get migration services dashboard data"""
    # School filtering for non-admin users
    school_id = None if current_user.platform_role == PlatformRole.SUPER_ADMIN else current_user.primary_school_id
    
    service = MigrationServicesService(db)
    return await service.get_migration_dashboard(school_id)


@router.get("/analytics", response_model=OrderAnalytics)
async def get_order_analytics(
    date_from: Optional[date] = Query(None, description="Start date for analytics"),
    date_to: Optional[date] = Query(None, description="End date for analytics"),
    current_user: PlatformUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get order analytics"""
    # School filtering for non-admin users
    school_id = None if current_user.platform_role == PlatformRole.SUPER_ADMIN else current_user.primary_school_id
    
    service = MigrationServicesService(db)
    return await service.get_order_analytics(school_id, date_from, date_to)


# Order Status Management
@router.patch("/orders/{order_id}/status", response_model=CarePackageOrderResponse)
async def update_order_status(
    order_id: UUID,
    status: OrderStatus,
    notes: Optional[str] = None,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update order status (Super admin only)"""
    if current_user.platform_role != PlatformRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform administrators can update order status"
        )
    
    service = MigrationServicesService(db)
    update_data = CarePackageOrderUpdate(status=status)
    if notes:
        update_data.internal_notes = notes
    
    order = await service.update_care_package_order(order_id, update_data, current_user.id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Care package order not found"
        )
    
    return order


# Team Assignment
@router.patch("/orders/{order_id}/assign-team", response_model=CarePackageOrderResponse)
async def assign_team_to_order(
    order_id: UUID,
    migration_manager: Optional[UUID] = None,
    technical_lead: Optional[UUID] = None,
    data_specialist: Optional[UUID] = None,
    training_specialist: Optional[UUID] = None,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Assign team members to an order (Super admin only)"""
    if current_user.platform_role != PlatformRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform administrators can assign team members"
        )
    
    service = MigrationServicesService(db)
    update_data = CarePackageOrderUpdate(
        assigned_migration_manager=migration_manager,
        assigned_technical_lead=technical_lead,
        assigned_data_specialist=data_specialist,
        assigned_training_specialist=training_specialist
    )
    
    order = await service.update_care_package_order(order_id, update_data, current_user.id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Care package order not found"
        )
    
    return order


# Order Progress
@router.patch("/orders/{order_id}/progress", response_model=CarePackageOrderResponse)
async def update_order_progress(
    order_id: UUID,
    progress_percentage: int,
    notes: Optional[str] = None,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update order progress (Super admin only)"""
    if current_user.platform_role != PlatformRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform administrators can update order progress"
        )
    
    if not (0 <= progress_percentage <= 100):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Progress percentage must be between 0 and 100"
        )
    
    service = MigrationServicesService(db)
    update_data = CarePackageOrderUpdate(progress_percentage=progress_percentage)
    if notes:
        update_data.internal_notes = notes
    
    order = await service.update_care_package_order(order_id, update_data, current_user.id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Care package order not found"
        )
    
    return order


# Super Admin Statistics
@router.get("/admin/statistics")
async def get_admin_statistics(
    current_user: PlatformUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get super admin statistics"""
    if current_user.platform_role != PlatformRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform administrators can view admin statistics"
        )
    
    service = MigrationServicesService(db)
    
    # Get comprehensive statistics
    dashboard = await service.get_migration_dashboard()
    analytics = await service.get_order_analytics()
    
    return {
        "dashboard": dashboard,
        "analytics": analytics,
        "timestamp": date.today()
    }


# Order Export
@router.get("/orders/export")
async def export_orders(
    format: str = Query("csv", description="Export format (csv, xlsx)"),
    status: Optional[OrderStatus] = Query(None, description="Filter by status"),
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    current_user: PlatformUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export orders to CSV or Excel (Super admin only)"""
    if current_user.platform_role != PlatformRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform administrators can export orders"
        )
    
    # Implementation would generate and return file
    # For now, return placeholder
    return {"message": "Export functionality to be implemented"}


# Error handlers and validation
@router.get("/validation/order-number/{order_number}")
async def validate_order_number(
    order_number: str,
    db: Session = Depends(get_db)
):
    """Validate if order number exists"""
    service = MigrationServicesService(db)
    # Implementation would check if order number exists
    return {"exists": False, "order_number": order_number}


# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "migration-services"}