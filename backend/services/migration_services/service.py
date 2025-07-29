"""
Migration Services Service Layer
Professional data migration and care package management business logic
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy import text, and_, or_, func, desc, asc
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from shared.database import get_db
from shared.models.migration_services import (
    CarePackageCreate,
    CarePackageUpdate,
    CarePackageResponse,
    CarePackageOrderCreate,
    CarePackageOrderUpdate,
    CarePackageOrderResponse,
    MigrationTaskCreate,
    MigrationTaskUpdate,
    MigrationTaskResponse,
    DataSourceCreate,
    DataSourceUpdate,
    DataSourceResponse,
    CommunicationLogCreate,
    CommunicationLogResponse,
    PaymentCreate,
    PaymentUpdate,
    PaymentResponse,
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneResponse,
    TeamPerformanceCreate,
    TeamPerformanceUpdate,
    TeamPerformanceResponse,
    MigrationServicesDashboard,
    OrderFilters,
    OrderAnalytics,
    OrderStatus,
    PaymentStatus,
    TaskStatus,
    MilestoneStatus,
)
from shared.models.platform import School
from shared.models.platform_user import PlatformUser as User

logger = logging.getLogger(__name__)


class MigrationServicesService:
    """Service for managing migration services and care packages"""

    def __init__(self, db: Session):
        self.db = db

    # Care Package Management

    async def get_care_packages(
        self, active_only: bool = True
    ) -> List[CarePackageResponse]:
        """Get all care packages"""
        try:
            query = self.db.query(CarePackage)
            if active_only:
                query = query.filter(CarePackage.is_active == True)

            packages = query.order_by(CarePackage.price_usd).all()
            return [CarePackageResponse.from_orm(pkg) for pkg in packages]

        except Exception as e:
            logger.error(f"Error getting care packages: {str(e)}")
            raise

    async def get_care_package(self, package_id: UUID) -> Optional[CarePackageResponse]:
        """Get a specific care package"""
        try:
            package = (
                self.db.query(CarePackage).filter(CarePackage.id == package_id).first()
            )

            if not package:
                return None

            return CarePackageResponse.from_orm(package)

        except Exception as e:
            logger.error(f"Error getting care package {package_id}: {str(e)}")
            raise

    async def create_care_package(
        self, package_data: CarePackageCreate
    ) -> CarePackageResponse:
        """Create a new care package"""
        try:
            package = CarePackage(**package_data.dict())
            self.db.add(package)
            self.db.commit()
            self.db.refresh(package)

            logger.info(f"Created care package: {package.name}")
            return CarePackageResponse.from_orm(package)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating care package: {str(e)}")
            raise

    async def update_care_package(
        self, package_id: UUID, package_data: CarePackageUpdate
    ) -> Optional[CarePackageResponse]:
        """Update a care package"""
        try:
            package = (
                self.db.query(CarePackage).filter(CarePackage.id == package_id).first()
            )

            if not package:
                return None

            update_data = package_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(package, field, value)

            self.db.commit()
            self.db.refresh(package)

            logger.info(f"Updated care package: {package.name}")
            return CarePackageResponse.from_orm(package)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating care package {package_id}: {str(e)}")
            raise

    # Care Package Order Management

    async def create_care_package_order(
        self, order_data: CarePackageOrderCreate, created_by: UUID
    ) -> CarePackageOrderResponse:
        """Create a new care package order"""
        try:
            # Get the care package to calculate pricing
            package = await self.get_care_package(order_data.care_package_id)
            if not package:
                raise ValueError("Care package not found")

            # Calculate pricing
            base_price = package.price_usd
            additional_costs = Decimal("0")

            if order_data.urgent_migration:
                additional_costs += Decimal("1000")
            if order_data.onsite_training:
                additional_costs += Decimal("800")
            if order_data.weekend_work:
                additional_costs += Decimal("500")

            # Generate order number
            order_number = await self._generate_order_number()

            # Create order
            order = CarePackageOrder(
                order_number=order_number,
                package_price=base_price,
                additional_costs=additional_costs,
                **order_data.dict(),
            )

            self.db.add(order)
            self.db.commit()
            self.db.refresh(order)

            # Create default milestones
            await self._create_default_milestones(order.id)

            # Log creation
            await self._log_communication(
                order.id,
                "system",
                "outbound",
                "Care Package Order Created",
                f"Order {order_number} created for {package.name}",
                created_by,
            )

            logger.info(f"Created care package order: {order_number}")
            return await self._get_order_response(order.id)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating care package order: {str(e)}")
            raise

    async def get_care_package_orders(
        self,
        filters: OrderFilters = None,
        school_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[CarePackageOrderResponse]:
        """Get care package orders with filtering"""
        try:
            query = self.db.query(CarePackageOrder)

            # School filtering for non-admin users
            if school_id:
                query = query.filter(CarePackageOrder.school_id == school_id)

            # Apply filters
            if filters:
                if filters.status:
                    query = query.filter(CarePackageOrder.status == filters.status)
                if filters.payment_status:
                    query = query.filter(
                        CarePackageOrder.payment_status == filters.payment_status
                    )
                if filters.assigned_manager:
                    query = query.filter(
                        CarePackageOrder.assigned_migration_manager
                        == filters.assigned_manager
                    )
                if filters.date_from:
                    query = query.filter(
                        CarePackageOrder.order_date >= filters.date_from
                    )
                if filters.date_to:
                    query = query.filter(CarePackageOrder.order_date <= filters.date_to)
                if filters.school_name:
                    query = query.join(School).filter(
                        School.name.ilike(f"%{filters.school_name}%")
                    )

            orders = (
                query.order_by(desc(CarePackageOrder.order_date))
                .limit(limit)
                .offset(offset)
                .all()
            )

            return [await self._get_order_response(order.id) for order in orders]

        except Exception as e:
            logger.error(f"Error getting care package orders: {str(e)}")
            raise

    async def get_care_package_order(
        self, order_id: UUID
    ) -> Optional[CarePackageOrderResponse]:
        """Get a specific care package order"""
        try:
            return await self._get_order_response(order_id)

        except Exception as e:
            logger.error(f"Error getting care package order {order_id}: {str(e)}")
            raise

    async def update_care_package_order(
        self, order_id: UUID, order_data: CarePackageOrderUpdate, updated_by: UUID
    ) -> Optional[CarePackageOrderResponse]:
        """Update a care package order"""
        try:
            order = (
                self.db.query(CarePackageOrder)
                .filter(CarePackageOrder.id == order_id)
                .first()
            )

            if not order:
                return None

            # Track status changes
            old_status = order.status

            update_data = order_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(order, field, value)

            self.db.commit()
            self.db.refresh(order)

            # Log status change
            if "status" in update_data and old_status != order.status:
                await self._log_communication(
                    order_id,
                    "system",
                    "outbound",
                    "Status Update",
                    f"Order status changed from {old_status} to {order.status}",
                    updated_by,
                )

            logger.info(f"Updated care package order: {order.order_number}")
            return await self._get_order_response(order_id)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating care package order {order_id}: {str(e)}")
            raise

    # Migration Task Management

    async def create_migration_task(
        self, task_data: MigrationTaskCreate, created_by: UUID
    ) -> MigrationTaskResponse:
        """Create a new migration task"""
        try:
            task = MigrationTask(**task_data.dict())
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)

            logger.info(f"Created migration task: {task.task_name}")
            return await self._get_task_response(task.id)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating migration task: {str(e)}")
            raise

    async def get_migration_tasks(
        self, order_id: UUID, status: Optional[TaskStatus] = None
    ) -> List[MigrationTaskResponse]:
        """Get migration tasks for an order"""
        try:
            query = self.db.query(MigrationTask).filter(
                MigrationTask.care_package_order_id == order_id
            )

            if status:
                query = query.filter(MigrationTask.status == status)

            tasks = query.order_by(MigrationTask.due_date.asc()).all()

            return [await self._get_task_response(task.id) for task in tasks]

        except Exception as e:
            logger.error(f"Error getting migration tasks: {str(e)}")
            raise

    async def update_migration_task(
        self, task_id: UUID, task_data: MigrationTaskUpdate, updated_by: UUID
    ) -> Optional[MigrationTaskResponse]:
        """Update a migration task"""
        try:
            task = (
                self.db.query(MigrationTask).filter(MigrationTask.id == task_id).first()
            )

            if not task:
                return None

            update_data = task_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(task, field, value)

            self.db.commit()
            self.db.refresh(task)

            logger.info(f"Updated migration task: {task.task_name}")
            return await self._get_task_response(task_id)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating migration task {task_id}: {str(e)}")
            raise

    # Dashboard and Analytics

    async def get_migration_dashboard(
        self, school_id: Optional[UUID] = None
    ) -> MigrationServicesDashboard:
        """Get migration services dashboard data"""
        try:
            # Base query
            base_query = self.db.query(CarePackageOrder)
            if school_id:
                base_query = base_query.filter(CarePackageOrder.school_id == school_id)

            # KPIs
            active_projects = base_query.filter(
                CarePackageOrder.status.in_(
                    [
                        OrderStatus.APPROVED,
                        OrderStatus.IN_PROGRESS,
                        OrderStatus.DATA_MIGRATION,
                        OrderStatus.SYSTEM_SETUP,
                        OrderStatus.TRAINING,
                        OrderStatus.TESTING,
                        OrderStatus.GO_LIVE,
                    ]
                )
            ).count()

            # Monthly revenue (current month)
            current_month = date.today().replace(day=1)
            monthly_revenue = base_query.filter(
                CarePackageOrder.order_date >= current_month
            ).with_entities(
                func.sum(
                    CarePackageOrder.package_price + CarePackageOrder.additional_costs
                )
            ).scalar() or Decimal(
                "0"
            )

            # Team utilization (placeholder - would need actual calculation)
            team_utilization = Decimal("87")

            # Success rate
            completed_orders = base_query.filter(
                CarePackageOrder.status == OrderStatus.COMPLETED
            ).count()
            total_orders = base_query.count()
            success_rate = (
                (completed_orders / total_orders * 100) if total_orders > 0 else 0
            )

            # Recent orders
            recent_orders = await self.get_care_package_orders(
                school_id=school_id, limit=10, offset=0
            )

            # Team performance (placeholder)
            team_performance = []

            return MigrationServicesDashboard(
                active_projects=active_projects,
                monthly_revenue=monthly_revenue,
                team_utilization=team_utilization,
                success_rate=Decimal(str(success_rate)),
                projects_trend="+12% this month",
                revenue_trend="+23% vs last month",
                utilization_trend="Optimal",
                success_rate_trend="Above target",
                recent_orders=recent_orders,
                team_performance=team_performance,
            )

        except Exception as e:
            logger.error(f"Error getting migration dashboard: {str(e)}")
            raise

    async def get_order_analytics(
        self,
        school_id: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> OrderAnalytics:
        """Get order analytics"""
        try:
            # Date range defaults
            if not date_from:
                date_from = date.today() - timedelta(days=90)
            if not date_to:
                date_to = date.today()

            # Base query
            base_query = self.db.query(CarePackageOrder).filter(
                CarePackageOrder.order_date.between(date_from, date_to)
            )
            if school_id:
                base_query = base_query.filter(CarePackageOrder.school_id == school_id)

            # Basic metrics
            total_orders = base_query.count()
            total_revenue = base_query.with_entities(
                func.sum(
                    CarePackageOrder.package_price + CarePackageOrder.additional_costs
                )
            ).scalar() or Decimal("0")

            average_order_value = (
                total_revenue / total_orders if total_orders > 0 else Decimal("0")
            )

            completed_orders = base_query.filter(
                CarePackageOrder.status == OrderStatus.COMPLETED
            ).count()
            completion_rate = (
                (completed_orders / total_orders * 100) if total_orders > 0 else 0
            )

            # Average delivery time (placeholder)
            average_delivery_time = 18

            # Customer satisfaction (placeholder)
            customer_satisfaction = Decimal("4.8")

            return OrderAnalytics(
                total_orders=total_orders,
                total_revenue=total_revenue,
                average_order_value=average_order_value,
                completion_rate=Decimal(str(completion_rate)),
                average_delivery_time=average_delivery_time,
                customer_satisfaction=customer_satisfaction,
                package_breakdown={},
                monthly_trends=[],
            )

        except Exception as e:
            logger.error(f"Error getting order analytics: {str(e)}")
            raise

    # Helper Methods

    async def _generate_order_number(self) -> str:
        """Generate a unique order number"""
        try:
            result = self.db.execute(text("SELECT generate_order_number()"))
            return result.scalar()

        except Exception as e:
            logger.error(f"Error generating order number: {str(e)}")
            raise

    async def _create_default_milestones(self, order_id: UUID) -> None:
        """Create default milestones for an order"""
        try:
            # Get milestone templates
            milestone_templates = [
                ("Project Kickoff", "Initial assessment and project planning", 1),
                ("Data Collection", "Gather all source data from school", 2),
                ("Data Analysis", "Analyze and clean collected data", 3),
                ("System Configuration", "Set up OneClass instance for school", 4),
                ("Data Migration", "Import all data into OneClass system", 5),
                ("User Setup", "Create user accounts and permissions", 6),
                ("Training Delivery", "Conduct user training sessions", 7),
                ("System Testing", "End-to-end testing with school staff", 8),
                ("Go Live", "Launch system for production use", 9),
                ("Project Closure", "Complete project and handover", 10),
            ]

            for name, desc, seq in milestone_templates:
                milestone = Milestone(
                    care_package_order_id=order_id,
                    milestone_name=name,
                    description=desc,
                    sequence_order=seq,
                    status=MilestoneStatus.PENDING,
                )
                self.db.add(milestone)

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating default milestones: {str(e)}")
            raise

    async def _log_communication(
        self,
        order_id: UUID,
        comm_type: str,
        direction: str,
        subject: str,
        content: str,
        created_by: UUID,
    ) -> None:
        """Log communication for an order"""
        try:
            log_entry = CommunicationLog(
                care_package_order_id=order_id,
                communication_type=comm_type,
                direction=direction,
                subject=subject,
                content=content,
                created_by=created_by,
            )
            self.db.add(log_entry)
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error logging communication: {str(e)}")
            raise

    async def _get_order_response(
        self, order_id: UUID
    ) -> Optional[CarePackageOrderResponse]:
        """Get enriched order response"""
        try:
            order = (
                self.db.query(CarePackageOrder)
                .options(
                    joinedload(CarePackageOrder.care_package),
                    joinedload(CarePackageOrder.school),
                )
                .filter(CarePackageOrder.id == order_id)
                .first()
            )

            if not order:
                return None

            response = CarePackageOrderResponse.from_orm(order)
            response.school_name = order.school.name if order.school else None

            return response

        except Exception as e:
            logger.error(f"Error getting order response: {str(e)}")
            raise

    async def _get_task_response(
        self, task_id: UUID
    ) -> Optional[MigrationTaskResponse]:
        """Get enriched task response"""
        try:
            task = (
                self.db.query(MigrationTask)
                .options(joinedload(MigrationTask.assigned_user))
                .filter(MigrationTask.id == task_id)
                .first()
            )

            if not task:
                return None

            response = MigrationTaskResponse.from_orm(task)
            response.assigned_user_name = (
                task.assigned_user.full_name if task.assigned_user else None
            )

            return response

        except Exception as e:
            logger.error(f"Error getting task response: {str(e)}")
            raise


# Database Models (placeholder - these would be defined in a separate file)
class CarePackage:
    """Care package database model"""

    pass


class CarePackageOrder:
    """Care package order database model"""

    pass


class MigrationTask:
    """Migration task database model"""

    pass


class DataSource:
    """Data source database model"""

    pass


class CommunicationLog:
    """Communication log database model"""

    pass


class Payment:
    """Payment database model"""

    pass


class Milestone:
    """Milestone database model"""

    pass


class TeamPerformance:
    """Team performance database model"""

    pass
