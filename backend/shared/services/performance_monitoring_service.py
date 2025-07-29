# =====================================================
# Performance Monitoring and Optimization Service
# Comprehensive monitoring for the OneClass platform user system
# File: backend/shared/services/performance_monitoring_service.py
# =====================================================

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
from uuid import UUID
import json

# Metrics collection
from collections import defaultdict, deque
import psutil
import redis

# Our imports
from shared.cache.user_context_cache import UserContextCache
from shared.services.optimized_user_service import OptimizedUserService

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics to collect"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""


@dataclass
class PerformanceAlert:
    """Performance alert"""
    name: str
    severity: AlertSeverity
    message: str
    metric_value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False


@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hit_rate: float
    miss_rate: float
    total_requests: int
    total_hits: int
    total_misses: int
    avg_response_time_ms: float
    memory_usage_mb: float
    key_count: int


@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    active_connections: int
    idle_connections: int
    total_queries: int
    avg_query_time_ms: float
    slow_queries: int
    connection_pool_usage: float


@dataclass
class UserSystemMetrics:
    """User system specific metrics"""
    active_users: int
    user_context_requests_per_minute: float
    avg_user_context_resolution_time_ms: float
    school_membership_queries_per_minute: float
    authentication_requests_per_minute: float
    failed_authentications_per_minute: float


class PerformanceMonitoringService:
    """
    Comprehensive performance monitoring service for the user system
    Collects metrics, generates alerts, and provides optimization insights
    """
    
    def __init__(self, cache: UserContextCache, user_service: OptimizedUserService, redis_client: redis.Redis):
        self.cache = cache
        self.user_service = user_service
        self.redis = redis_client
        
        # Metrics storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.alerts: List[PerformanceAlert] = []
        
        # Configuration
        self.collection_interval = 30  # seconds
        self.alert_thresholds = {
            "user_context_resolution_time": 100,  # ms
            "cache_hit_rate": 0.8,  # 80%
            "database_query_time": 50,  # ms
            "memory_usage": 80,  # percent
            "error_rate": 0.01,  # 1%
        }
        
        # Monitoring state
        self.monitoring_active = False
        self.start_time = datetime.utcnow()
        
        # Request tracking
        self.request_times: deque = deque(maxlen=1000)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.operation_counts: Dict[str, int] = defaultdict(int)
    
    async def start_monitoring(self):
        """Start performance monitoring"""
        self.monitoring_active = True
        self.start_time = datetime.utcnow()
        logger.info("Performance monitoring started")
        
        # Start background monitoring tasks
        asyncio.create_task(self._collect_metrics_loop())
        asyncio.create_task(self._check_alerts_loop())
    
    async def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        logger.info("Performance monitoring stopped")
    
    # Metrics Collection
    
    async def _collect_metrics_loop(self):
        """Background task to collect metrics periodically"""
        while self.monitoring_active:
            try:
                await self._collect_all_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_all_metrics(self):
        """Collect all performance metrics"""
        timestamp = datetime.utcnow()
        
        # Collect cache metrics
        cache_metrics = await self._collect_cache_metrics()
        self._record_metric("cache_hit_rate", cache_metrics.hit_rate, MetricType.GAUGE, timestamp)
        self._record_metric("cache_memory_usage", cache_metrics.memory_usage_mb, MetricType.GAUGE, timestamp)
        self._record_metric("cache_key_count", cache_metrics.key_count, MetricType.GAUGE, timestamp)
        
        # Collect database metrics
        db_metrics = await self._collect_database_metrics()
        self._record_metric("db_active_connections", db_metrics.active_connections, MetricType.GAUGE, timestamp)
        self._record_metric("db_avg_query_time", db_metrics.avg_query_time_ms, MetricType.GAUGE, timestamp)
        self._record_metric("db_slow_queries", db_metrics.slow_queries, MetricType.COUNTER, timestamp)
        
        # Collect user system metrics
        user_metrics = await self._collect_user_system_metrics()
        self._record_metric("active_users", user_metrics.active_users, MetricType.GAUGE, timestamp)
        self._record_metric("user_context_resolution_time", user_metrics.avg_user_context_resolution_time_ms, MetricType.GAUGE, timestamp)
        self._record_metric("auth_requests_per_minute", user_metrics.authentication_requests_per_minute, MetricType.GAUGE, timestamp)
        
        # Collect system metrics
        system_metrics = await self._collect_system_metrics()
        self._record_metric("cpu_usage", system_metrics["cpu_percent"], MetricType.GAUGE, timestamp)
        self._record_metric("memory_usage", system_metrics["memory_percent"], MetricType.GAUGE, timestamp)
        self._record_metric("disk_usage", system_metrics["disk_percent"], MetricType.GAUGE, timestamp)
    
    async def _collect_cache_metrics(self) -> CacheMetrics:
        """Collect cache performance metrics"""
        try:
            cache_stats = await self.cache.get_cache_stats()
            cache_health = await self.cache.health_check()
            
            # Calculate hit rate from Redis info
            redis_info = await self.redis.info()
            hits = redis_info.get('keyspace_hits', 0)
            misses = redis_info.get('keyspace_misses', 0)
            total_requests = hits + misses
            hit_rate = hits / total_requests if total_requests > 0 else 0
            
            # Get memory usage
            memory_usage_bytes = redis_info.get('used_memory', 0)
            memory_usage_mb = memory_usage_bytes / (1024 * 1024)
            
            return CacheMetrics(
                hit_rate=hit_rate,
                miss_rate=1 - hit_rate,
                total_requests=total_requests,
                total_hits=hits,
                total_misses=misses,
                avg_response_time_ms=0,  # Would need to track this separately
                memory_usage_mb=memory_usage_mb,
                key_count=cache_stats.get('total_keys', 0)
            )
        except Exception as e:
            logger.warning(f"Error collecting cache metrics: {e}")
            return CacheMetrics(0, 1, 0, 0, 0, 0, 0, 0)
    
    async def _collect_database_metrics(self) -> DatabaseMetrics:
        """Collect database performance metrics"""
        try:
            # This would integrate with your database monitoring
            # For now, return placeholder metrics
            return DatabaseMetrics(
                active_connections=10,
                idle_connections=5,
                total_queries=1000,
                avg_query_time_ms=25,
                slow_queries=2,
                connection_pool_usage=0.6
            )
        except Exception as e:
            logger.warning(f"Error collecting database metrics: {e}")
            return DatabaseMetrics(0, 0, 0, 0, 0, 0)
    
    async def _collect_user_system_metrics(self) -> UserSystemMetrics:
        """Collect user system specific metrics"""
        try:
            # Get user service performance stats
            performance_stats = await self.user_service.get_performance_stats()
            
            # Calculate rates from recent activity
            current_time = time.time()
            recent_requests = [
                t for t in self.request_times 
                if current_time - t < 60  # Last minute
            ]
            
            return UserSystemMetrics(
                active_users=0,  # Would need to track this
                user_context_requests_per_minute=len(recent_requests),
                avg_user_context_resolution_time_ms=sum(self.request_times) / len(self.request_times) if self.request_times else 0,
                school_membership_queries_per_minute=0,  # Would track this
                authentication_requests_per_minute=0,  # Would track this
                failed_authentications_per_minute=0  # Would track this
            )
        except Exception as e:
            logger.warning(f"Error collecting user system metrics: {e}")
            return UserSystemMetrics(0, 0, 0, 0, 0, 0)
    
    async def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect system resource metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "disk_free_gb": disk.free / (1024 * 1024 * 1024)
            }
        except Exception as e:
            logger.warning(f"Error collecting system metrics: {e}")
            return {"cpu_percent": 0, "memory_percent": 0, "disk_percent": 0}
    
    def _record_metric(self, name: str, value: float, metric_type: MetricType, timestamp: datetime, labels: Optional[Dict[str, str]] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=timestamp,
            labels=labels or {}
        )
        
        self.metrics[name].append(metric)
        
        # Store in Redis for persistence
        try:
            key = f"oneclass:metrics:{name}:{int(timestamp.timestamp())}"
            self.redis.setex(key, 3600, json.dumps({
                "value": value,
                "type": metric_type.value,
                "labels": labels or {}
            }))
        except Exception as e:
            logger.warning(f"Error storing metric to Redis: {e}")
    
    # Alert System
    
    async def _check_alerts_loop(self):
        """Background task to check for alert conditions"""
        while self.monitoring_active:
            try:
                await self._check_alert_conditions()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error checking alerts: {e}")
                await asyncio.sleep(60)
    
    async def _check_alert_conditions(self):
        """Check all alert conditions"""
        current_time = datetime.utcnow()
        
        # Check cache hit rate
        if "cache_hit_rate" in self.metrics:
            recent_hit_rates = [m.value for m in list(self.metrics["cache_hit_rate"])[-5:]]
            if recent_hit_rates:
                avg_hit_rate = sum(recent_hit_rates) / len(recent_hit_rates)
                if avg_hit_rate < self.alert_thresholds["cache_hit_rate"]:
                    await self._create_alert(
                        "low_cache_hit_rate",
                        AlertSeverity.WARNING,
                        f"Cache hit rate is {avg_hit_rate:.2%}, below threshold of {self.alert_thresholds['cache_hit_rate']:.2%}",
                        avg_hit_rate,
                        self.alert_thresholds["cache_hit_rate"]
                    )
        
        # Check user context resolution time
        if "user_context_resolution_time" in self.metrics:
            recent_times = [m.value for m in list(self.metrics["user_context_resolution_time"])[-5:]]
            if recent_times:
                avg_time = sum(recent_times) / len(recent_times)
                if avg_time > self.alert_thresholds["user_context_resolution_time"]:
                    await self._create_alert(
                        "slow_user_context_resolution",
                        AlertSeverity.WARNING,
                        f"User context resolution time is {avg_time:.1f}ms, above threshold of {self.alert_thresholds['user_context_resolution_time']}ms",
                        avg_time,
                        self.alert_thresholds["user_context_resolution_time"]
                    )
        
        # Check memory usage
        if "memory_usage" in self.metrics:
            recent_memory = [m.value for m in list(self.metrics["memory_usage"])[-3:]]
            if recent_memory:
                avg_memory = sum(recent_memory) / len(recent_memory)
                if avg_memory > self.alert_thresholds["memory_usage"]:
                    severity = AlertSeverity.CRITICAL if avg_memory > 90 else AlertSeverity.WARNING
                    await self._create_alert(
                        "high_memory_usage",
                        severity,
                        f"Memory usage is {avg_memory:.1f}%, above threshold of {self.alert_thresholds['memory_usage']}%",
                        avg_memory,
                        self.alert_thresholds["memory_usage"]
                    )
    
    async def _create_alert(self, name: str, severity: AlertSeverity, message: str, value: float, threshold: float):
        """Create a new performance alert"""
        # Check if we already have an active alert for this condition
        existing_alert = next(
            (alert for alert in self.alerts 
             if alert.name == name and not alert.resolved),
            None
        )
        
        if not existing_alert:
            alert = PerformanceAlert(
                name=name,
                severity=severity,
                message=message,
                metric_value=value,
                threshold=threshold,
                timestamp=datetime.utcnow()
            )
            
            self.alerts.append(alert)
            logger.warning(f"Performance alert: {message}")
            
            # Store alert in Redis
            try:
                alert_key = f"oneclass:alerts:{name}:{int(alert.timestamp.timestamp())}"
                self.redis.setex(alert_key, 86400, json.dumps({
                    "severity": severity.value,
                    "message": message,
                    "value": value,
                    "threshold": threshold
                }))
            except Exception as e:
                logger.warning(f"Error storing alert to Redis: {e}")
    
    # Performance Tracking Decorators
    
    def track_operation(self, operation_name: str):
        """Decorator to track operation performance"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = await func(*args, **kwargs)
                    self.operation_counts[operation_name] += 1
                    return result
                except Exception as e:
                    self.error_counts[f"{operation_name}_error"] += 1
                    raise
                finally:
                    duration = (time.time() - start_time) * 1000  # Convert to ms
                    self.request_times.append(duration)
                    
                    # Record operation timing
                    self._record_metric(
                        f"operation_{operation_name}_duration",
                        duration,
                        MetricType.TIMER,
                        datetime.utcnow(),
                        {"operation": operation_name}
                    )
            
            return wrapper
        return decorator
    
    @asynccontextmanager
    async def track_request(self, request_type: str):
        """Context manager to track request performance"""
        start_time = time.time()
        
        try:
            yield
            self.operation_counts[request_type] += 1
        except Exception as e:
            self.error_counts[f"{request_type}_error"] += 1
            raise
        finally:
            duration = (time.time() - start_time) * 1000
            self.request_times.append(duration)
            
            self._record_metric(
                f"request_{request_type}_duration",
                duration,
                MetricType.TIMER,
                datetime.utcnow(),
                {"request_type": request_type}
            )
    
    # Reporting and Analytics
    
    async def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        report = {
            "report_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            },
            "cache_performance": await self._get_cache_performance_summary(start_time, end_time),
            "user_system_performance": await self._get_user_system_summary(start_time, end_time),
            "system_resources": await self._get_system_resources_summary(start_time, end_time),
            "alerts": await self._get_alerts_summary(start_time, end_time),
            "recommendations": await self._get_optimization_recommendations()
        }
        
        return report
    
    async def _get_cache_performance_summary(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get cache performance summary"""
        cache_metrics = [
            m for m in self.metrics.get("cache_hit_rate", [])
            if start_time <= m.timestamp <= end_time
        ]
        
        if not cache_metrics:
            return {"hit_rate": 0, "avg_hit_rate": 0, "samples": 0}
        
        hit_rates = [m.value for m in cache_metrics]
        return {
            "current_hit_rate": hit_rates[-1] if hit_rates else 0,
            "avg_hit_rate": sum(hit_rates) / len(hit_rates),
            "min_hit_rate": min(hit_rates),
            "max_hit_rate": max(hit_rates),
            "samples": len(hit_rates)
        }
    
    async def _get_user_system_summary(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get user system performance summary"""
        response_time_metrics = [
            m for m in self.metrics.get("user_context_resolution_time", [])
            if start_time <= m.timestamp <= end_time
        ]
        
        if not response_time_metrics:
            return {"avg_response_time": 0, "samples": 0}
        
        response_times = [m.value for m in response_time_metrics]
        return {
            "avg_response_time_ms": sum(response_times) / len(response_times),
            "min_response_time_ms": min(response_times),
            "max_response_time_ms": max(response_times),
            "p95_response_time_ms": sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0,
            "total_operations": sum(self.operation_counts.values()),
            "total_errors": sum(self.error_counts.values()),
            "error_rate": sum(self.error_counts.values()) / sum(self.operation_counts.values()) if sum(self.operation_counts.values()) > 0 else 0,
            "samples": len(response_times)
        }
    
    async def _get_system_resources_summary(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get system resources summary"""
        cpu_metrics = [
            m for m in self.metrics.get("cpu_usage", [])
            if start_time <= m.timestamp <= end_time
        ]
        
        memory_metrics = [
            m for m in self.metrics.get("memory_usage", [])
            if start_time <= m.timestamp <= end_time
        ]
        
        return {
            "cpu": {
                "avg_usage": sum(m.value for m in cpu_metrics) / len(cpu_metrics) if cpu_metrics else 0,
                "max_usage": max(m.value for m in cpu_metrics) if cpu_metrics else 0
            },
            "memory": {
                "avg_usage": sum(m.value for m in memory_metrics) / len(memory_metrics) if memory_metrics else 0,
                "max_usage": max(m.value for m in memory_metrics) if memory_metrics else 0
            }
        }
    
    async def _get_alerts_summary(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get alerts summary"""
        period_alerts = [
            alert for alert in self.alerts
            if start_time <= alert.timestamp <= end_time
        ]
        
        return {
            "total_alerts": len(period_alerts),
            "by_severity": {
                severity.value: len([a for a in period_alerts if a.severity == severity])
                for severity in AlertSeverity
            },
            "active_alerts": len([a for a in period_alerts if not a.resolved]),
            "resolved_alerts": len([a for a in period_alerts if a.resolved])
        }
    
    async def _get_optimization_recommendations(self) -> List[str]:
        """Get optimization recommendations based on current metrics"""
        recommendations = []
        
        # Check cache hit rate
        if "cache_hit_rate" in self.metrics:
            recent_hit_rates = [m.value for m in list(self.metrics["cache_hit_rate"])[-5:]]
            if recent_hit_rates and sum(recent_hit_rates) / len(recent_hit_rates) < 0.8:
                recommendations.append("Consider increasing cache TTL values or warming critical cache keys")
        
        # Check response times
        if "user_context_resolution_time" in self.metrics:
            recent_times = [m.value for m in list(self.metrics["user_context_resolution_time"])[-5:]]
            if recent_times and sum(recent_times) / len(recent_times) > 50:
                recommendations.append("Consider optimizing database queries or increasing cache usage")
        
        # Check memory usage
        if "memory_usage" in self.metrics:
            recent_memory = [m.value for m in list(self.metrics["memory_usage"])[-3:]]
            if recent_memory and sum(recent_memory) / len(recent_memory) > 70:
                recommendations.append("Consider increasing server memory or optimizing memory usage")
        
        if not recommendations:
            recommendations.append("System performance is within acceptable ranges")
        
        return recommendations
    
    # Health Check
    
    async def health_check(self) -> Dict[str, Any]:
        """Get overall system health status"""
        cache_health = await self.cache.health_check()
        
        # Get recent performance metrics
        recent_alerts = [
            alert for alert in self.alerts
            if not alert.resolved and 
            (datetime.utcnow() - alert.timestamp) < timedelta(hours=1)
        ]
        
        critical_alerts = [a for a in recent_alerts if a.severity == AlertSeverity.CRITICAL]
        warning_alerts = [a for a in recent_alerts if a.severity == AlertSeverity.WARNING]
        
        # Determine overall health
        if critical_alerts:
            health_status = "critical"
        elif warning_alerts:
            health_status = "warning"
        else:
            health_status = "healthy"
        
        return {
            "status": health_status,
            "monitoring_active": self.monitoring_active,
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "cache_health": cache_health,
            "active_alerts": len(recent_alerts),
            "critical_alerts": len(critical_alerts),
            "warning_alerts": len(warning_alerts),
            "timestamp": datetime.utcnow().isoformat()
        }