# =====================================================
# WebSocket Manager for Real-time Progress Tracking
# Manages WebSocket connections and real-time events
# File: backend/services/realtime/websocket_manager.py
# =====================================================

import asyncio
import json
import uuid
import logging
from typing import Dict, List, Set, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict

from fastapi import WebSocket, WebSocketDisconnect
from .schemas import (
    RealTimeEvent, ConnectionInfo, EventType, ProgressUpdate,
    SubscriptionRequest, ProgressSummary
)
from .progress_tracker import ProgressTracker

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections for real-time progress tracking"""
    
    def __init__(self, progress_tracker: ProgressTracker):
        # Connection management
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_info: Dict[str, ConnectionInfo] = {}
        
        # User and school mappings
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)  # user_id -> connection_ids
        self.school_connections: Dict[str, Set[str]] = defaultdict(set)  # school_id -> connection_ids
        
        # Subscription management
        self.operation_subscribers: Dict[str, Set[str]] = defaultdict(set)  # operation_id -> connection_ids
        self.event_subscribers: Dict[EventType, Set[str]] = defaultdict(set)  # event_type -> connection_ids
        
        # Progress tracker integration
        self.progress_tracker = progress_tracker
        
        # Configuration
        self.heartbeat_interval = 30  # seconds
        self.connection_timeout = 300  # 5 minutes
        self.max_connections_per_user = 5
        
        # Background tasks
        self.background_tasks: List[asyncio.Task] = []
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        loop = asyncio.get_event_loop()
        
        # Heartbeat task
        self.background_tasks.append(
            loop.create_task(self._heartbeat_loop())
        )
        
        # Connection cleanup task
        self.background_tasks.append(
            loop.create_task(self._cleanup_stale_connections())
        )
    
    async def connect_user(
        self,
        websocket: WebSocket,
        user_id: str,
        school_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """Connect a user WebSocket"""
        
        # Accept connection
        await websocket.accept()
        
        # Generate connection ID
        connection_id = str(uuid.uuid4())
        
        # Check connection limits
        if len(self.user_connections[user_id]) >= self.max_connections_per_user:
            # Disconnect oldest connection
            oldest_connection = min(
                self.user_connections[user_id],
                key=lambda cid: self.connection_info[cid].connected_at
            )
            await self.disconnect(oldest_connection)
        
        # Store connection
        self.active_connections[connection_id] = websocket
        
        # Create connection info
        connection_info = ConnectionInfo(
            connection_id=connection_id,
            user_id=user_id,
            school_id=school_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.connection_info[connection_id] = connection_info
        
        # Update mappings
        self.user_connections[user_id].add(connection_id)
        if school_id:
            self.school_connections[school_id].add(connection_id)
        
        # Subscribe to progress tracker
        self.progress_tracker.subscribe_to_all(
            lambda progress: asyncio.create_task(self._handle_progress_update(progress))
        )
        
        # Send connection established event
        await self._send_to_connection(connection_id, RealTimeEvent(
            event_type=EventType.CONNECTION_ESTABLISHED,
            user_id=user_id,
            data={
                "connection_id": connection_id,
                "server_time": datetime.utcnow().isoformat(),
                "message": "Connected to OneClass real-time service"
            }
        ))
        
        # Send current progress summary
        await self._send_progress_summary(connection_id, user_id)
        
        logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Disconnect a WebSocket connection"""
        
        if connection_id not in self.active_connections:
            return
        
        try:
            # Get connection info
            conn_info = self.connection_info[connection_id]
            
            # Close WebSocket
            websocket = self.active_connections[connection_id]
            await websocket.close()
            
            # Remove from mappings
            self.user_connections[conn_info.user_id].discard(connection_id)
            if conn_info.school_id:
                self.school_connections[conn_info.school_id].discard(connection_id)
            
            # Remove from subscriptions
            for operation_id in conn_info.subscriptions:
                self.operation_subscribers[operation_id].discard(connection_id)
            
            # Clean up
            del self.active_connections[connection_id]
            del self.connection_info[connection_id]
            
            logger.info(f"WebSocket disconnected: {connection_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket {connection_id}: {str(e)}")
    
    async def handle_message(self, connection_id: str, message: str):
        """Handle incoming WebSocket message"""
        
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "subscribe":
                await self._handle_subscription(connection_id, data)
            elif message_type == "unsubscribe":
                await self._handle_unsubscription(connection_id, data)
            elif message_type == "ping":
                await self._handle_ping(connection_id)
            elif message_type == "get_progress":
                await self._handle_progress_request(connection_id, data)
            else:
                logger.warning(f"Unknown message type from {connection_id}: {message_type}")
        
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from {connection_id}: {message}")
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {str(e)}")
    
    async def _handle_subscription(self, connection_id: str, data: Dict[str, Any]):
        """Handle subscription request"""
        
        try:
            operation_ids = data.get("operation_ids", [])
            event_types = data.get("event_types", list(EventType))
            
            conn_info = self.connection_info[connection_id]
            
            # Subscribe to operations
            for operation_id in operation_ids:
                self.operation_subscribers[operation_id].add(connection_id)
                conn_info.subscriptions.append(operation_id)
            
            # Subscribe to event types
            for event_type in event_types:
                if isinstance(event_type, str):
                    event_type = EventType(event_type)
                self.event_subscribers[event_type].add(connection_id)
            
            # Send confirmation
            await self._send_to_connection(connection_id, RealTimeEvent(
                event_type=EventType.STATUS_CHANGE,
                data={
                    "subscribed_operations": operation_ids,
                    "subscribed_events": [et.value for et in event_types],
                    "message": "Subscription successful"
                }
            ))
            
        except Exception as e:
            logger.error(f"Error handling subscription for {connection_id}: {str(e)}")
    
    async def _handle_unsubscription(self, connection_id: str, data: Dict[str, Any]):
        """Handle unsubscription request"""
        
        try:
            operation_ids = data.get("operation_ids", [])
            
            conn_info = self.connection_info[connection_id]
            
            # Unsubscribe from operations
            for operation_id in operation_ids:
                self.operation_subscribers[operation_id].discard(connection_id)
                if operation_id in conn_info.subscriptions:
                    conn_info.subscriptions.remove(operation_id)
            
            # Send confirmation
            await self._send_to_connection(connection_id, RealTimeEvent(
                event_type=EventType.STATUS_CHANGE,
                data={
                    "unsubscribed_operations": operation_ids,
                    "message": "Unsubscription successful"
                }
            ))
            
        except Exception as e:
            logger.error(f"Error handling unsubscription for {connection_id}: {str(e)}")
    
    async def _handle_ping(self, connection_id: str):
        """Handle ping message"""
        
        # Update last seen
        if connection_id in self.connection_info:
            self.connection_info[connection_id].last_seen = datetime.utcnow()
        
        # Send pong
        await self._send_to_connection(connection_id, RealTimeEvent(
            event_type=EventType.HEARTBEAT,
            data={"message": "pong", "server_time": datetime.utcnow().isoformat()}
        ))
    
    async def _handle_progress_request(self, connection_id: str, data: Dict[str, Any]):
        """Handle progress information request"""
        
        try:
            operation_id = data.get("operation_id")
            
            if operation_id:
                # Get specific operation progress
                progress = self.progress_tracker.get_operation_progress(operation_id)
                bulk_progress = self.progress_tracker.get_bulk_operation_progress(operation_id)
                
                await self._send_to_connection(connection_id, RealTimeEvent(
                    event_type=EventType.PROGRESS_UPDATE,
                    operation_id=operation_id,
                    data={
                        "progress": progress.dict() if progress else None,
                        "bulk_progress": bulk_progress.dict() if bulk_progress else None
                    }
                ))
            else:
                # Send progress summary
                conn_info = self.connection_info[connection_id]
                await self._send_progress_summary(connection_id, conn_info.user_id)
        
        except Exception as e:
            logger.error(f"Error handling progress request for {connection_id}: {str(e)}")
    
    async def _handle_progress_update(self, progress: ProgressUpdate):
        """Handle progress update from progress tracker"""
        
        # Create real-time event
        event = RealTimeEvent(
            event_type=EventType.PROGRESS_UPDATE,
            operation_id=progress.operation_id,
            user_id=progress.user_id,
            school_id=progress.school_id,
            data=progress.dict()
        )
        
        # Send to operation subscribers
        connection_ids = self.operation_subscribers.get(progress.operation_id, set())
        
        # Also send to user's connections
        if progress.user_id:
            connection_ids.update(self.user_connections.get(str(progress.user_id), set()))
        
        # Send to school connections if applicable
        if progress.school_id:
            connection_ids.update(self.school_connections.get(str(progress.school_id), set()))
        
        # Send to all relevant connections
        await self._broadcast_to_connections(list(connection_ids), event)
    
    async def broadcast_event(
        self,
        event: RealTimeEvent,
        target_users: Optional[List[str]] = None,
        target_schools: Optional[List[str]] = None,
        operation_id: Optional[str] = None
    ):
        """Broadcast event to specific targets"""
        
        connection_ids = set()
        
        # Target specific users
        if target_users:
            for user_id in target_users:
                connection_ids.update(self.user_connections.get(user_id, set()))
        
        # Target specific schools
        if target_schools:
            for school_id in target_schools:
                connection_ids.update(self.school_connections.get(school_id, set()))
        
        # Target operation subscribers
        if operation_id:
            connection_ids.update(self.operation_subscribers.get(operation_id, set()))
        
        # Broadcast globally if no specific targets
        if event.broadcast and not (target_users or target_schools or operation_id):
            connection_ids.update(self.active_connections.keys())
        
        await self._broadcast_to_connections(list(connection_ids), event)
    
    async def _send_progress_summary(self, connection_id: str, user_id: str):
        """Send progress summary to connection"""
        
        try:
            # Get user operations
            user_operations = self.progress_tracker.get_user_operations(uuid.UUID(user_id))
            
            # Separate active and completed
            active_operations = [op for op in user_operations if op.status.value in ['pending', 'in_progress']]
            recent_completed = [op for op in user_operations if op.status.value in ['completed', 'failed', 'cancelled']]
            
            summary = ProgressSummary(
                user_id=user_id,
                active_operations=active_operations,
                recent_completed=recent_completed[:10],  # Last 10 completed
                total_active=len(active_operations),
                total_completed_today=len(recent_completed)
            )
            
            await self._send_to_connection(connection_id, RealTimeEvent(
                event_type=EventType.PROGRESS_UPDATE,
                user_id=user_id,
                data={"summary": summary.dict()}
            ))
            
        except Exception as e:
            logger.error(f"Error sending progress summary to {connection_id}: {str(e)}")
    
    async def _send_to_connection(self, connection_id: str, event: RealTimeEvent):
        """Send event to specific connection"""
        
        if connection_id not in self.active_connections:
            return
        
        try:
            websocket = self.active_connections[connection_id]
            await websocket.send_text(event.json())
            
        except WebSocketDisconnect:
            await self.disconnect(connection_id)
        except Exception as e:
            logger.error(f"Error sending to connection {connection_id}: {str(e)}")
            await self.disconnect(connection_id)
    
    async def _broadcast_to_connections(self, connection_ids: List[str], event: RealTimeEvent):
        """Broadcast event to multiple connections"""
        
        if not connection_ids:
            return
        
        # Send to all connections concurrently
        tasks = [
            self._send_to_connection(connection_id, event)
            for connection_id in connection_ids
            if connection_id in self.active_connections
        ]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat to all connections"""
        
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                if not self.active_connections:
                    continue
                
                # Create heartbeat event
                heartbeat_event = RealTimeEvent(
                    event_type=EventType.HEARTBEAT,
                    data={
                        "server_time": datetime.utcnow().isoformat(),
                        "active_connections": len(self.active_connections)
                    }
                )
                
                # Send to all connections
                connection_ids = list(self.active_connections.keys())
                await self._broadcast_to_connections(connection_ids, heartbeat_event)
                
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {str(e)}")
    
    async def _cleanup_stale_connections(self):
        """Clean up stale connections periodically"""
        
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                cutoff_time = datetime.utcnow() - timedelta(seconds=self.connection_timeout)
                stale_connections = []
                
                for connection_id, conn_info in self.connection_info.items():
                    if conn_info.last_seen < cutoff_time:
                        stale_connections.append(connection_id)
                
                # Disconnect stale connections
                for connection_id in stale_connections:
                    await self.disconnect(connection_id)
                
                if stale_connections:
                    logger.info(f"Cleaned up {len(stale_connections)} stale connections")
                
            except Exception as e:
                logger.error(f"Error in connection cleanup: {str(e)}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        
        active_users = len(self.user_connections)
        active_schools = len(self.school_connections)
        total_subscriptions = sum(len(subs) for subs in self.operation_subscribers.values())
        
        return {
            "total_connections": len(self.active_connections),
            "active_users": active_users,
            "active_schools": active_schools,
            "total_subscriptions": total_subscriptions,
            "connections_by_user": {
                user_id: len(connections) 
                for user_id, connections in self.user_connections.items()
            },
            "uptime": (datetime.utcnow() - min(
                conn.connected_at for conn in self.connection_info.values()
            )).total_seconds() if self.connection_info else 0
        }
    
    async def shutdown(self):
        """Gracefully shutdown WebSocket manager"""
        
        logger.info("Shutting down WebSocket manager...")
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Disconnect all connections
        connection_ids = list(self.active_connections.keys())
        for connection_id in connection_ids:
            await self.disconnect(connection_id)
        
        logger.info("WebSocket manager shutdown complete")