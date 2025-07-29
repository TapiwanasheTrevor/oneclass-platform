# =====================================================
# Progress Tracker Service
# Core service for tracking and managing operation progress
# File: backend/services/realtime/progress_tracker.py
# =====================================================

import asyncio
import uuid
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque

from .schemas import (
    ProgressUpdate, BulkOperationProgress, ProgressStatus, OperationType,
    OperationLog, PerformanceMetrics, ProgressSnapshot, ErrorDetail
)

# Fix missing UUID import in schemas
import uuid as uuid_module

logger = logging.getLogger(__name__)

class ProgressTracker:
    """Service for tracking and managing operation progress"""
    
    def __init__(self):
        # Core tracking data
        self.active_operations: Dict[str, ProgressUpdate] = {}
        self.bulk_operations: Dict[str, BulkOperationProgress] = {}
        self.completed_operations: Dict[str, ProgressUpdate] = {}
        
        # Performance tracking
        self.operation_logs: Dict[str, List[OperationLog]] = defaultdict(list)
        self.performance_metrics: Dict[OperationType, PerformanceMetrics] = {}
        self.snapshots: Dict[str, List[ProgressSnapshot]] = defaultdict(list)
        
        # Error tracking
        self.operation_errors: Dict[str, List[ErrorDetail]] = defaultdict(list)
        
        # Event subscribers
        self.progress_subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.global_subscribers: List[Callable] = []
        
        # Configuration
        self.max_completed_operations = 1000
        self.max_logs_per_operation = 500
        self.snapshot_interval = 30  # seconds
        self.cleanup_interval = 3600  # 1 hour
        
        # Background tasks
        self.background_tasks: List[asyncio.Task] = []
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        loop = asyncio.get_event_loop()
        
        # Snapshot task
        self.background_tasks.append(
            loop.create_task(self._periodic_snapshots())
        )
        
        # Cleanup task
        self.background_tasks.append(
            loop.create_task(self._periodic_cleanup())
        )
        
        # Performance calculation task
        self.background_tasks.append(
            loop.create_task(self._calculate_performance_metrics())
        )
    
    async def create_operation(
        self,
        operation_type: OperationType,
        user_id: uuid.UUID,
        total_items: int = 0,
        school_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new operation for tracking"""
        
        operation_id = str(uuid.uuid4())
        
        progress = ProgressUpdate(
            operation_id=operation_id,
            operation_type=operation_type,
            status=ProgressStatus.PENDING,
            progress_percentage=0.0,
            current_step=0,
            total_steps=total_items if total_items > 0 else 1,
            started_at=datetime.utcnow(),
            total_items=total_items,
            user_id=user_id,
            school_id=school_id,
            metadata=metadata or {}
        )
        
        self.active_operations[operation_id] = progress
        
        # Log operation creation
        await self._log_operation(operation_id, "info", f"Operation created: {operation_type}")
        
        # Notify subscribers
        await self._notify_progress_update(progress)
        
        logger.info(f"Created operation {operation_id}: {operation_type} for user {user_id}")
        return operation_id
    
    async def create_bulk_operation(
        self,
        operation_type: OperationType,
        user_id: uuid.UUID,
        total_items: int,
        batch_size: int = 100,
        school_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new bulk operation for tracking"""
        
        operation_id = str(uuid.uuid4())
        total_batches = (total_items + batch_size - 1) // batch_size  # Ceiling division
        
        bulk_progress = BulkOperationProgress(
            operation_id=operation_id,
            operation_type=operation_type,
            status=ProgressStatus.PENDING,
            total_batches=total_batches,
            completed_batches=0,
            current_batch=0,
            batch_size=batch_size,
            total_items=total_items,
            processed_items=0,
            successful_items=0,
            failed_items=0,
            progress_percentage=0.0,
            started_at=datetime.utcnow()
        )
        
        self.bulk_operations[operation_id] = bulk_progress
        
        # Also create regular progress entry
        progress = ProgressUpdate(
            operation_id=operation_id,
            operation_type=operation_type,
            status=ProgressStatus.PENDING,
            progress_percentage=0.0,
            current_step=0,
            total_steps=total_items,
            started_at=datetime.utcnow(),
            total_items=total_items,
            user_id=user_id,
            school_id=school_id,
            metadata=metadata or {}
        )
        
        self.active_operations[operation_id] = progress
        
        await self._log_operation(operation_id, "info", 
                                 f"Bulk operation created: {operation_type}, {total_items} items, {total_batches} batches")
        
        await self._notify_progress_update(progress)
        
        logger.info(f"Created bulk operation {operation_id}: {operation_type} for user {user_id}")
        return operation_id
    
    async def update_progress(
        self,
        operation_id: str,
        progress_percentage: Optional[float] = None,
        current_step: Optional[int] = None,
        current_task: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update operation progress"""
        
        if operation_id not in self.active_operations:
            logger.warning(f"Operation {operation_id} not found for progress update")
            return False
        
        progress = self.active_operations[operation_id]
        
        # Update fields
        if progress_percentage is not None:
            progress.progress_percentage = min(100.0, max(0.0, progress_percentage))
        if current_step is not None:
            progress.current_step = current_step
            # Auto-calculate percentage if not provided
            if progress_percentage is None and progress.total_steps > 0:
                progress.progress_percentage = (current_step / progress.total_steps) * 100
        if current_task is not None:
            progress.current_task = current_task
        if metadata:
            progress.metadata.update(metadata)
        
        # Update timing
        elapsed = (datetime.utcnow() - progress.started_at).total_seconds()
        progress.elapsed_time = elapsed
        
        # Estimate completion time
        if progress.progress_percentage > 0:
            total_estimated = elapsed / (progress.progress_percentage / 100)
            remaining_time = total_estimated - elapsed
            progress.estimated_completion = datetime.utcnow() + timedelta(seconds=remaining_time)
        
        # Change status if starting
        if progress.status == ProgressStatus.PENDING:
            progress.status = ProgressStatus.IN_PROGRESS
        
        # Notify subscribers
        await self._notify_progress_update(progress)
        
        return True
    
    async def update_bulk_progress(
        self,
        operation_id: str,
        completed_batches: Optional[int] = None,
        processed_items: Optional[int] = None,
        successful_items: Optional[int] = None,
        failed_items: Optional[int] = None,
        current_batch: Optional[int] = None,
        errors: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Update bulk operation progress"""
        
        if operation_id not in self.bulk_operations:
            logger.warning(f"Bulk operation {operation_id} not found for progress update")
            return False
        
        bulk_progress = self.bulk_operations[operation_id]
        
        # Update fields
        if completed_batches is not None:
            bulk_progress.completed_batches = completed_batches
        if processed_items is not None:
            bulk_progress.processed_items = processed_items
        if successful_items is not None:
            bulk_progress.successful_items = successful_items
        if failed_items is not None:
            bulk_progress.failed_items = failed_items
        if current_batch is not None:
            bulk_progress.current_batch = current_batch
        if errors:
            bulk_progress.errors.extend(errors)
        
        # Calculate progress percentage
        if bulk_progress.total_items > 0:
            bulk_progress.progress_percentage = (bulk_progress.processed_items / bulk_progress.total_items) * 100
        
        # Calculate processing rate
        elapsed = (datetime.utcnow() - bulk_progress.started_at).total_seconds()
        if elapsed > 0:
            bulk_progress.items_per_second = bulk_progress.processed_items / elapsed
            
            # Estimate completion
            if bulk_progress.items_per_second > 0:
                remaining_items = bulk_progress.total_items - bulk_progress.processed_items
                remaining_seconds = remaining_items / bulk_progress.items_per_second
                bulk_progress.estimated_completion = datetime.utcnow() + timedelta(seconds=remaining_seconds)
        
        bulk_progress.last_updated = datetime.utcnow()
        
        # Update corresponding regular progress entry
        if operation_id in self.active_operations:
            await self.update_progress(
                operation_id,
                progress_percentage=bulk_progress.progress_percentage,
                current_step=bulk_progress.processed_items,
                current_task=f"Processing batch {bulk_progress.current_batch + 1}/{bulk_progress.total_batches}"
            )
        
        return True
    
    async def complete_operation(
        self,
        operation_id: str,
        success: bool = True,
        result_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Mark operation as completed"""
        
        if operation_id not in self.active_operations:
            logger.warning(f"Operation {operation_id} not found for completion")
            return False
        
        progress = self.active_operations[operation_id]
        
        # Update status
        progress.status = ProgressStatus.COMPLETED if success else ProgressStatus.FAILED
        progress.progress_percentage = 100.0 if success else progress.progress_percentage
        
        # Update timing
        progress.elapsed_time = (datetime.utcnow() - progress.started_at).total_seconds()
        
        # Add result data
        if result_data:
            progress.metadata.update(result_data)
        
        # Log completion
        log_level = "info" if success else "error"
        log_message = f"Operation completed: {success}"
        if error_message:
            log_message += f" - {error_message}"
        
        await self._log_operation(operation_id, log_level, log_message)
        
        # Update bulk operation if applicable
        if operation_id in self.bulk_operations:
            bulk_progress = self.bulk_operations[operation_id]
            bulk_progress.status = progress.status
            bulk_progress.progress_percentage = 100.0 if success else bulk_progress.progress_percentage
            
            if result_data:
                bulk_progress.results_summary = result_data
        
        # Notify subscribers
        await self._notify_progress_update(progress)
        
        # Move to completed operations
        self.completed_operations[operation_id] = progress
        del self.active_operations[operation_id]
        
        if operation_id in self.bulk_operations:
            del self.bulk_operations[operation_id]
        
        # Clean up old completed operations
        await self._cleanup_completed_operations()
        
        logger.info(f"Operation {operation_id} completed: {success}")
        return True
    
    async def cancel_operation(self, operation_id: str) -> bool:
        """Cancel an active operation"""
        
        if operation_id not in self.active_operations:
            return False
        
        progress = self.active_operations[operation_id]
        progress.status = ProgressStatus.CANCELLED
        
        await self._log_operation(operation_id, "warning", "Operation cancelled")
        await self._notify_progress_update(progress)
        
        # Move to completed
        self.completed_operations[operation_id] = progress
        del self.active_operations[operation_id]
        
        if operation_id in self.bulk_operations:
            del self.bulk_operations[operation_id]
        
        logger.info(f"Operation {operation_id} cancelled")
        return True
    
    async def add_error(
        self,
        operation_id: str,
        error_type: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
        item_index: Optional[int] = None
    ):
        """Add error to operation"""
        
        error = ErrorDetail(
            operation_id=operation_id,
            error_type=error_type,
            error_message=error_message,
            error_details=error_details or {},
            item_index=item_index
        )
        
        self.operation_errors[operation_id].append(error)
        
        # Update operation progress with error count
        if operation_id in self.active_operations:
            progress = self.active_operations[operation_id]
            progress.failed_items += 1
            await self._notify_progress_update(progress)
        
        # Update bulk operation
        if operation_id in self.bulk_operations:
            bulk_progress = self.bulk_operations[operation_id]
            bulk_progress.failed_items += 1
            bulk_progress.errors.append({
                "error_type": error_type,
                "error_message": error_message,
                "item_index": item_index,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        await self._log_operation(operation_id, "error", f"{error_type}: {error_message}")
    
    def get_operation_progress(self, operation_id: str) -> Optional[ProgressUpdate]:
        """Get current progress for an operation"""
        
        # Check active operations first
        if operation_id in self.active_operations:
            return self.active_operations[operation_id]
        
        # Check completed operations
        if operation_id in self.completed_operations:
            return self.completed_operations[operation_id]
        
        return None
    
    def get_bulk_operation_progress(self, operation_id: str) -> Optional[BulkOperationProgress]:
        """Get bulk operation progress"""
        return self.bulk_operations.get(operation_id)
    
    def get_user_operations(self, user_id: uuid.UUID) -> List[ProgressUpdate]:
        """Get all operations for a user"""
        
        user_operations = []
        
        # Active operations
        for progress in self.active_operations.values():
            if progress.user_id == user_id:
                user_operations.append(progress)
        
        # Recent completed operations (last 24 hours)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        for progress in self.completed_operations.values():
            if progress.user_id == user_id and progress.started_at > cutoff:
                user_operations.append(progress)
        
        return sorted(user_operations, key=lambda x: x.started_at, reverse=True)
    
    def get_school_operations(self, school_id: uuid.UUID) -> List[ProgressUpdate]:
        """Get all operations for a school"""
        
        school_operations = []
        
        # Active operations
        for progress in self.active_operations.values():
            if progress.school_id == school_id:
                school_operations.append(progress)
        
        # Recent completed operations
        cutoff = datetime.utcnow() - timedelta(hours=24)
        for progress in self.completed_operations.values():
            if progress.school_id == school_id and progress.started_at > cutoff:
                school_operations.append(progress)
        
        return sorted(school_operations, key=lambda x: x.started_at, reverse=True)
    
    def subscribe_to_operation(self, operation_id: str, callback: Callable):
        """Subscribe to updates for a specific operation"""
        self.progress_subscribers[operation_id].append(callback)
    
    def subscribe_to_all(self, callback: Callable):
        """Subscribe to all progress updates"""
        self.global_subscribers.append(callback)
    
    def unsubscribe(self, operation_id: str, callback: Callable):
        """Unsubscribe from operation updates"""
        if operation_id in self.progress_subscribers:
            try:
                self.progress_subscribers[operation_id].remove(callback)
            except ValueError:
                pass
    
    async def _notify_progress_update(self, progress: ProgressUpdate):
        """Notify all subscribers of progress update"""
        
        # Notify operation-specific subscribers
        for callback in self.progress_subscribers.get(progress.operation_id, []):
            try:
                await callback(progress)
            except Exception as e:
                logger.error(f"Error in progress callback: {str(e)}")
        
        # Notify global subscribers
        for callback in self.global_subscribers:
            try:
                await callback(progress)
            except Exception as e:
                logger.error(f"Error in global progress callback: {str(e)}")
    
    async def _log_operation(self, operation_id: str, level: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Log operation event"""
        
        log_entry = OperationLog(
            operation_id=operation_id,
            timestamp=datetime.utcnow(),
            level=level,
            message=message,
            details=details or {}
        )
        
        self.operation_logs[operation_id].append(log_entry)
        
        # Limit log entries per operation
        if len(self.operation_logs[operation_id]) > self.max_logs_per_operation:
            self.operation_logs[operation_id] = self.operation_logs[operation_id][-self.max_logs_per_operation:]
    
    async def _periodic_snapshots(self):
        """Take periodic snapshots of active operations"""
        
        while True:
            try:
                await asyncio.sleep(self.snapshot_interval)
                
                for operation_id, progress in self.active_operations.items():
                    snapshot = ProgressSnapshot(
                        operation_id=operation_id,
                        snapshot_time=datetime.utcnow(),
                        status=progress.status,
                        progress_percentage=progress.progress_percentage,
                        items_processed=progress.processed_items,
                        items_remaining=max(0, progress.total_items - progress.processed_items),
                        current_rate=progress.processed_items / progress.elapsed_time if progress.elapsed_time > 0 else 0,
                        estimated_completion=progress.estimated_completion
                    )
                    
                    self.snapshots[operation_id].append(snapshot)
                    
                    # Limit snapshots per operation
                    if len(self.snapshots[operation_id]) > 100:
                        self.snapshots[operation_id] = self.snapshots[operation_id][-100:]
                
            except Exception as e:
                logger.error(f"Error in periodic snapshots: {str(e)}")
    
    async def _periodic_cleanup(self):
        """Clean up old data periodically"""
        
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                await self._cleanup_completed_operations()
                await self._cleanup_logs()
                await self._cleanup_snapshots()
                
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {str(e)}")
    
    async def _cleanup_completed_operations(self):
        """Clean up old completed operations"""
        
        if len(self.completed_operations) <= self.max_completed_operations:
            return
        
        # Sort by completion time and keep only the most recent
        sorted_operations = sorted(
            self.completed_operations.items(),
            key=lambda x: x[1].started_at,
            reverse=True
        )
        
        # Keep only the most recent operations
        operations_to_keep = dict(sorted_operations[:self.max_completed_operations])
        operations_to_remove = set(self.completed_operations.keys()) - set(operations_to_keep.keys())
        
        for operation_id in operations_to_remove:
            del self.completed_operations[operation_id]
            if operation_id in self.operation_logs:
                del self.operation_logs[operation_id]
            if operation_id in self.snapshots:
                del self.snapshots[operation_id]
            if operation_id in self.operation_errors:
                del self.operation_errors[operation_id]
        
        logger.info(f"Cleaned up {len(operations_to_remove)} old completed operations")
    
    async def _cleanup_logs(self):
        """Clean up old log entries"""
        
        cutoff_time = datetime.utcnow() - timedelta(days=7)
        
        for operation_id in list(self.operation_logs.keys()):
            original_count = len(self.operation_logs[operation_id])
            self.operation_logs[operation_id] = [
                log for log in self.operation_logs[operation_id]
                if log.timestamp > cutoff_time
            ]
            
            # Remove empty log lists
            if not self.operation_logs[operation_id]:
                del self.operation_logs[operation_id]
    
    async def _cleanup_snapshots(self):
        """Clean up old snapshots"""
        
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        for operation_id in list(self.snapshots.keys()):
            self.snapshots[operation_id] = [
                snapshot for snapshot in self.snapshots[operation_id]
                if snapshot.snapshot_time > cutoff_time
            ]
            
            # Remove empty snapshot lists
            if not self.snapshots[operation_id]:
                del self.snapshots[operation_id]
    
    async def _calculate_performance_metrics(self):
        """Calculate performance metrics for different operation types"""
        
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                # Calculate metrics for each operation type
                for operation_type in OperationType:
                    await self._calculate_operation_type_metrics(operation_type)
                
            except Exception as e:
                logger.error(f"Error calculating performance metrics: {str(e)}")
    
    async def _calculate_operation_type_metrics(self, operation_type: OperationType):
        """Calculate metrics for a specific operation type"""
        
        # Get completed operations of this type from last 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        relevant_operations = [
            op for op in self.completed_operations.values()
            if op.operation_type == operation_type and op.started_at > cutoff_time
        ]
        
        if not relevant_operations:
            return
        
        # Calculate metrics
        durations = [op.elapsed_time for op in relevant_operations if op.elapsed_time > 0]
        success_count = len([op for op in relevant_operations if op.status == ProgressStatus.COMPLETED])
        
        if durations:
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
        else:
            avg_duration = min_duration = max_duration = 0
        
        success_rate = success_count / len(relevant_operations) if relevant_operations else 0
        
        # Calculate throughput (items per second)
        total_items = sum(op.total_items for op in relevant_operations)
        total_time = sum(durations)
        throughput = total_items / total_time if total_time > 0 else 0
        
        metrics = PerformanceMetrics(
            operation_type=operation_type,
            avg_duration=avg_duration,
            min_duration=min_duration,
            max_duration=max_duration,
            success_rate=success_rate,
            throughput=throughput,
            last_24h_count=len(relevant_operations),
            last_24h_success_rate=success_rate
        )
        
        self.performance_metrics[operation_type] = metrics
    
    def get_performance_metrics(self, operation_type: Optional[OperationType] = None) -> Dict[OperationType, PerformanceMetrics]:
        """Get performance metrics"""
        
        if operation_type:
            return {operation_type: self.performance_metrics.get(operation_type)}
        
        return self.performance_metrics.copy()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        
        return {
            "active_operations": len(self.active_operations),
            "completed_operations": len(self.completed_operations),
            "bulk_operations": len(self.bulk_operations),
            "total_subscribers": sum(len(subs) for subs in self.progress_subscribers.values()),
            "global_subscribers": len(self.global_subscribers),
            "operations_by_type": self._count_operations_by_type(),
            "operations_by_status": self._count_operations_by_status(),
            "error_count": sum(len(errors) for errors in self.operation_errors.values())
        }
    
    def _count_operations_by_type(self) -> Dict[str, int]:
        """Count operations by type"""
        
        counts = defaultdict(int)
        
        for op in self.active_operations.values():
            counts[op.operation_type.value] += 1
        
        for op in self.completed_operations.values():
            counts[op.operation_type.value] += 1
        
        return dict(counts)
    
    def _count_operations_by_status(self) -> Dict[str, int]:
        """Count operations by status"""
        
        counts = defaultdict(int)
        
        for op in self.active_operations.values():
            counts[op.status.value] += 1
        
        for op in self.completed_operations.values():
            counts[op.status.value] += 1
        
        return dict(counts)