# =====================================================
# Real-time Progress Tracking Routes
# WebSocket and HTTP endpoints for progress tracking
# File: backend/services/realtime/routes.py
# =====================================================

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import logging
import json

from shared.database import get_async_session
from shared.models.platform_user import PlatformUser
from shared.auth import get_current_active_user, get_websocket_user
from .websocket_manager import WebSocketManager
from .progress_tracker import ProgressTracker
from .schemas import (
    ProgressUpdate, BulkOperationProgress, RealTimeEvent, ProgressFilter,
    OperationType, ProgressStatus, ProgressSummary, SystemMetrics,
    PerformanceMetrics, AlertConfig, EventType
)

router = APIRouter(prefix="/api/v1/realtime", tags=["realtime"])
logger = logging.getLogger(__name__)

# Initialize services
progress_tracker = ProgressTracker()
websocket_manager = WebSocketManager(progress_tracker)

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time progress tracking
    
    Usage:
    - Connect: ws://localhost:8000/api/v1/realtime/ws?token=<jwt_token>
    - Send: {"type": "subscribe", "operation_ids": ["uuid1", "uuid2"]}
    - Send: {"type": "ping"}
    - Receive: {"event_type": "progress_update", "data": {...}}
    """
    
    connection_id = None
    
    try:
        # Authenticate user via token
        user = await get_websocket_user(token)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Extract connection metadata
        client_host = websocket.client.host if websocket.client else None
        user_agent = websocket.headers.get("user-agent")
        
        # Connect user
        connection_id = await websocket_manager.connect_user(
            websocket=websocket,
            user_id=str(user.id),
            school_id=str(user.school_memberships[0].school_id) if user.school_memberships else None,
            ip_address=client_host,
            user_agent=user_agent
        )
        
        # Handle messages
        while True:
            try:
                message = await websocket.receive_text()
                await websocket_manager.handle_message(connection_id, message)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {str(e)}")
                # Send error to client
                await websocket.send_text(json.dumps({
                    "event_type": "error",
                    "message": "Error processing message",
                    "timestamp": datetime.utcnow().isoformat()
                }))
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
    finally:
        if connection_id:
            await websocket_manager.disconnect(connection_id)

@router.post("/operations", response_model=dict)
async def create_operation(
    operation_type: OperationType,
    total_items: int = 0,
    school_id: Optional[UUID] = None,
    metadata: Optional[Dict[str, Any]] = None,
    current_user: PlatformUser = Depends(get_current_active_user)
):
    """Create a new operation for progress tracking"""
    
    try:
        operation_id = await progress_tracker.create_operation(
            operation_type=operation_type,
            user_id=current_user.id,
            total_items=total_items,
            school_id=school_id,
            metadata=metadata or {}
        )
        
        return {
            "operation_id": operation_id,
            "message": "Operation created successfully",
            "status": "pending"
        }
        
    except Exception as e:
        logger.error(f"Error creating operation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create operation: {str(e)}"
        )

@router.post("/operations/bulk", response_model=dict)
async def create_bulk_operation(
    operation_type: OperationType,
    total_items: int,
    batch_size: int = 100,
    school_id: Optional[UUID] = None,
    metadata: Optional[Dict[str, Any]] = None,
    current_user: PlatformUser = Depends(get_current_active_user)
):
    """Create a new bulk operation for progress tracking"""
    
    try:
        # Validate inputs
        if total_items <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Total items must be greater than 0"
            )
        
        if batch_size <= 0 or batch_size > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size must be between 1 and 1000"
            )
        
        operation_id = await progress_tracker.create_bulk_operation(
            operation_type=operation_type,
            user_id=current_user.id,
            total_items=total_items,
            batch_size=batch_size,
            school_id=school_id,
            metadata=metadata or {}
        )
        
        total_batches = (total_items + batch_size - 1) // batch_size
        
        return {
            "operation_id": operation_id,
            "message": "Bulk operation created successfully",
            "status": "pending",
            "total_items": total_items,
            "total_batches": total_batches,
            "batch_size": batch_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bulk operation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bulk operation: {str(e)}"
        )

@router.get("/operations/{operation_id}", response_model=dict)
async def get_operation_progress(
    operation_id: str,
    current_user: PlatformUser = Depends(get_current_active_user)
):
    """Get current progress for an operation"""
    
    try:
        # Get regular progress
        progress = progress_tracker.get_operation_progress(operation_id)
        
        # Get bulk progress if available
        bulk_progress = progress_tracker.get_bulk_operation_progress(operation_id)
        
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Operation not found"
            )
        
        # Check permission
        if (progress.user_id != current_user.id and 
            current_user.platform_role not in ['super_admin', 'school_admin']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view this operation"
            )
        
        result = {
            "operation_id": operation_id,
            "progress": progress.dict(),
        }
        
        if bulk_progress:
            result["bulk_progress"] = bulk_progress.dict()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting operation progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get operation progress"
        )

@router.put("/operations/{operation_id}/progress")
async def update_operation_progress(
    operation_id: str,
    progress_percentage: Optional[float] = None,
    current_step: Optional[int] = None,
    current_task: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    current_user: PlatformUser = Depends(get_current_active_user)
):
    """Update operation progress"""
    
    try:
        # Check if operation exists and user has permission
        progress = progress_tracker.get_operation_progress(operation_id)
        
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Operation not found"
            )
        
        if (progress.user_id != current_user.id and 
            current_user.platform_role not in ['super_admin']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update this operation"
            )
        
        # Update progress
        success = await progress_tracker.update_progress(
            operation_id=operation_id,
            progress_percentage=progress_percentage,
            current_step=current_step,
            current_task=current_task,
            metadata=metadata
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update progress"
            )
        
        return {"message": "Progress updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update progress"
        )

@router.put("/operations/{operation_id}/complete")
async def complete_operation(
    operation_id: str,
    success: bool = True,
    result_data: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    current_user: PlatformUser = Depends(get_current_active_user)
):
    """Mark operation as completed"""
    
    try:
        # Check if operation exists and user has permission
        progress = progress_tracker.get_operation_progress(operation_id)
        
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Operation not found"
            )
        
        if (progress.user_id != current_user.id and 
            current_user.platform_role not in ['super_admin']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to complete this operation"
            )
        
        # Complete operation
        completed = await progress_tracker.complete_operation(
            operation_id=operation_id,
            success=success,
            result_data=result_data,
            error_message=error_message
        )
        
        if not completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to complete operation"
            )
        
        return {
            "message": "Operation completed successfully",
            "success": success
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing operation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete operation"
        )

@router.delete("/operations/{operation_id}/cancel")
async def cancel_operation(
    operation_id: str,
    current_user: PlatformUser = Depends(get_current_active_user)
):
    """Cancel an active operation"""
    
    try:
        # Check if operation exists and user has permission
        progress = progress_tracker.get_operation_progress(operation_id)
        
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Operation not found"
            )
        
        if (progress.user_id != current_user.id and 
            current_user.platform_role not in ['super_admin']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to cancel this operation"
            )
        
        # Cancel operation
        cancelled = await progress_tracker.cancel_operation(operation_id)
        
        if not cancelled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Operation cannot be cancelled"
            )
        
        return {"message": "Operation cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling operation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel operation"
        )

@router.get("/operations", response_model=List[dict])
async def list_operations(
    status_filter: Optional[ProgressStatus] = None,
    operation_type: Optional[OperationType] = None,
    school_id: Optional[UUID] = None,
    limit: int = Query(50, ge=1, le=100),
    current_user: PlatformUser = Depends(get_current_active_user)
):
    """List operations for current user or school"""
    
    try:
        operations = []
        
        # Get user operations
        user_operations = progress_tracker.get_user_operations(current_user.id)
        operations.extend(user_operations)
        
        # Add school operations if user has permission
        if (school_id and current_user.platform_role in ['super_admin', 'school_admin']):
            school_operations = progress_tracker.get_school_operations(school_id)
            operations.extend(school_operations)
        
        # Apply filters
        if status_filter:
            operations = [op for op in operations if op.status == status_filter]
        
        if operation_type:
            operations = [op for op in operations if op.operation_type == operation_type]
        
        # Limit results
        operations = operations[:limit]
        
        # Convert to dict format
        result = []
        for op in operations:
            op_dict = op.dict()
            
            # Add bulk progress if available
            bulk_progress = progress_tracker.get_bulk_operation_progress(op.operation_id)
            if bulk_progress:
                op_dict["bulk_progress"] = bulk_progress.dict()
            
            result.append(op_dict)
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing operations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list operations"
        )

@router.get("/summary", response_model=dict)
async def get_progress_summary(
    current_user: PlatformUser = Depends(get_current_active_user)
):
    """Get progress summary for current user"""
    
    try:
        # Get user operations
        user_operations = progress_tracker.get_user_operations(current_user.id)
        
        # Separate by status
        active_operations = [op for op in user_operations if op.status.value in ['pending', 'in_progress']]
        completed_operations = [op for op in user_operations if op.status.value in ['completed', 'failed', 'cancelled']]
        
        # Create summary
        summary = {
            "user_id": str(current_user.id),
            "active_operations": [op.dict() for op in active_operations],
            "recent_completed": [op.dict() for op in completed_operations[:10]],
            "total_active": len(active_operations),
            "total_completed_today": len(completed_operations),
            "by_type": {},
            "by_status": {}
        }
        
        # Group by type and status
        all_operations = user_operations
        for op in all_operations:
            # By type
            op_type = op.operation_type.value
            summary["by_type"][op_type] = summary["by_type"].get(op_type, 0) + 1
            
            # By status
            op_status = op.status.value
            summary["by_status"][op_status] = summary["by_status"].get(op_status, 0) + 1
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting progress summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get progress summary"
        )

@router.get("/metrics", response_model=dict)
async def get_performance_metrics(
    operation_type: Optional[OperationType] = None,
    current_user: PlatformUser = Depends(get_current_active_user)
):
    """Get performance metrics"""
    
    try:
        # Check permissions
        if current_user.platform_role not in ['super_admin', 'school_admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for metrics"
            )
        
        metrics = progress_tracker.get_performance_metrics(operation_type)
        
        # Convert to serializable format
        result = {}
        for op_type, metric in metrics.items():
            if metric:
                result[op_type.value] = metric.dict()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get performance metrics"
        )

@router.get("/system/stats", response_model=dict)
async def get_system_stats(
    current_user: PlatformUser = Depends(get_current_active_user)
):
    """Get system-wide statistics"""
    
    try:
        # Check permissions
        if current_user.platform_role not in ['super_admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for system stats"
            )
        
        # Get progress tracker stats
        progress_stats = progress_tracker.get_system_stats()
        
        # Get WebSocket stats
        websocket_stats = websocket_manager.get_connection_stats()
        
        return {
            "progress_tracking": progress_stats,
            "websocket_connections": websocket_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system statistics"
        )

@router.post("/broadcast")
async def broadcast_event(
    event_type: EventType,
    message: str,
    target_users: Optional[List[UUID]] = None,
    target_schools: Optional[List[UUID]] = None,
    operation_id: Optional[str] = None,
    broadcast_all: bool = False,
    data: Optional[Dict[str, Any]] = None,
    current_user: PlatformUser = Depends(get_current_active_user)
):
    """Broadcast event to connected users"""
    
    try:
        # Check permissions
        if current_user.platform_role not in ['super_admin', 'school_admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to broadcast events"
            )
        
        # Create event
        event = RealTimeEvent(
            event_type=event_type,
            message=message,
            user_id=current_user.id,
            operation_id=operation_id,
            data=data or {},
            broadcast=broadcast_all
        )
        
        # Convert UUIDs to strings
        target_user_strs = [str(uid) for uid in target_users] if target_users else None
        target_school_strs = [str(sid) for sid in target_schools] if target_schools else None
        
        # Broadcast event
        await websocket_manager.broadcast_event(
            event=event,
            target_users=target_user_strs,
            target_schools=target_school_strs,
            operation_id=operation_id
        )
        
        return {"message": "Event broadcasted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error broadcasting event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to broadcast event"
        )

@router.get("/health")
async def get_service_health():
    """Get real-time service health status"""
    
    try:
        # Get basic health metrics
        progress_stats = progress_tracker.get_system_stats()
        websocket_stats = websocket_manager.get_connection_stats()
        
        # Determine health status
        health_status = "healthy"
        issues = []
        
        if progress_stats["active_operations"] > 1000:
            health_status = "warning"
            issues.append("High number of active operations")
        
        if websocket_stats["total_connections"] > 500:
            health_status = "warning"
            issues.append("High number of WebSocket connections")
        
        return {
            "status": health_status,
            "timestamp": datetime.utcnow().isoformat(),
            "progress_tracker": {
                "active_operations": progress_stats["active_operations"],
                "completed_operations": progress_stats["completed_operations"]
            },
            "websocket_manager": {
                "total_connections": websocket_stats["total_connections"],
                "active_users": websocket_stats["active_users"]
            },
            "issues": issues
        }
        
    except Exception as e:
        logger.error(f"Error getting service health: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }