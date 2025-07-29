# =====================================================
# User Context Cache for Performance Optimization
# Redis-based caching to reduce database queries
# File: backend/shared/cache/user_context_cache.py
# =====================================================

import json
import redis
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta
import asyncio
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class UserContextCache:
    """
    Redis-based caching system for user context data
    Implements multi-layer caching strategy for optimal performance
    """
    
    def __init__(self, redis_client: redis.Redis, default_ttl: int = 300):
        """
        Initialize cache with Redis client
        
        Args:
            redis_client: Redis client instance
            default_ttl: Default TTL in seconds (5 minutes)
        """
        self.redis = redis_client
        self.default_ttl = default_ttl
        
        # Different TTL values for different data types
        self.ttl_config = {
            'user_context': 300,       # 5 minutes - user data changes frequently
            'school_info': 900,        # 15 minutes - school data changes less often
            'clerk_validation': 300,   # 5 minutes - auth tokens have their own expiry
            'subdomain_mapping': 1800, # 30 minutes - subdomains rarely change
            'permissions': 600,        # 10 minutes - permission changes need quick propagation
            'features': 1800,          # 30 minutes - feature flags change rarely
            'minimal_context': 120     # 2 minutes - minimal context for performance
        }
    
    def _get_cache_key(self, key_type: str, identifier: str, suffix: str = "") -> str:
        """Generate standardized cache key"""
        base_key = f"oneclass:{key_type}:{identifier}"
        return f"{base_key}:{suffix}" if suffix else base_key
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache with error handling"""
        try:
            cached_data = await self.redis.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
        return None
    
    async def set(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set data in cache with error handling"""
        try:
            ttl = ttl or self.default_ttl
            await self.redis.setex(key, ttl, json.dumps(data, default=str))
            return True
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete data from cache"""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete multiple keys matching pattern"""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    # User Context Caching
    
    async def get_user_context(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get cached user context"""
        key = self._get_cache_key("user_context", str(user_id))
        return await self.get(key)
    
    async def set_user_context(self, user_id: UUID, context: Dict[str, Any]) -> bool:
        """Cache user context"""
        key = self._get_cache_key("user_context", str(user_id))
        return await self.set(key, context, self.ttl_config['user_context'])
    
    async def invalidate_user_context(self, user_id: UUID) -> bool:
        """Invalidate user context cache"""
        key = self._get_cache_key("user_context", str(user_id))
        return await self.delete(key)
    
    # Minimal Context Caching (for performance-critical operations)
    
    async def get_minimal_context(self, user_id: UUID, school_id: Optional[UUID] = None) -> Optional[Dict[str, Any]]:
        """Get cached minimal user context"""
        suffix = str(school_id) if school_id else "none"
        key = self._get_cache_key("minimal_context", str(user_id), suffix)
        return await self.get(key)
    
    async def set_minimal_context(self, user_id: UUID, context: Dict[str, Any], school_id: Optional[UUID] = None) -> bool:
        """Cache minimal user context"""
        suffix = str(school_id) if school_id else "none"
        key = self._get_cache_key("minimal_context", str(user_id), suffix)
        return await self.set(key, context, self.ttl_config['minimal_context'])
    
    # School Information Caching
    
    async def get_school_info(self, school_id: UUID) -> Optional[Dict[str, Any]]:
        """Get cached school information"""
        key = self._get_cache_key("school_info", str(school_id))
        return await self.get(key)
    
    async def set_school_info(self, school_id: UUID, school_info: Dict[str, Any]) -> bool:
        """Cache school information"""
        key = self._get_cache_key("school_info", str(school_id))
        return await self.set(key, school_info, self.ttl_config['school_info'])
    
    async def invalidate_school_info(self, school_id: UUID) -> bool:
        """Invalidate school info cache"""
        key = self._get_cache_key("school_info", str(school_id))
        return await self.delete(key)
    
    # Clerk Integration Caching
    
    async def get_clerk_user(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached Clerk user validation"""
        key = self._get_cache_key("clerk_user", session_id)
        return await self.get(key)
    
    async def set_clerk_user(self, session_id: str, user_data: Dict[str, Any]) -> bool:
        """Cache Clerk user validation"""
        key = self._get_cache_key("clerk_user", session_id)
        return await self.set(key, user_data, self.ttl_config['clerk_validation'])
    
    async def get_user_by_clerk_id(self, clerk_id: str) -> Optional[UUID]:
        """Get platform user ID from Clerk ID"""
        key = self._get_cache_key("clerk_to_user", clerk_id)
        cached = await self.get(key)
        return UUID(cached['user_id']) if cached else None
    
    async def set_user_by_clerk_id(self, clerk_id: str, user_id: UUID) -> bool:
        """Cache Clerk ID to platform user ID mapping"""
        key = self._get_cache_key("clerk_to_user", clerk_id)
        return await self.set(key, {'user_id': str(user_id)}, 600)  # 10 minutes
    
    # Subdomain and School Mapping
    
    async def get_school_by_subdomain(self, subdomain: str) -> Optional[UUID]:
        """Get school ID from subdomain"""
        key = self._get_cache_key("subdomain_to_school", subdomain)
        cached = await self.get(key)
        return UUID(cached['school_id']) if cached else None
    
    async def set_school_by_subdomain(self, subdomain: str, school_id: UUID) -> bool:
        """Cache subdomain to school ID mapping"""
        key = self._get_cache_key("subdomain_to_school", subdomain)
        return await self.set(
            key, 
            {'school_id': str(school_id)}, 
            self.ttl_config['subdomain_mapping']
        )
    
    # Permission and Feature Caching
    
    async def get_user_permissions(self, user_id: UUID, school_id: UUID) -> Optional[List[str]]:
        """Get cached user permissions for specific school"""
        key = self._get_cache_key("permissions", f"{user_id}:{school_id}")
        cached = await self.get(key)
        return cached['permissions'] if cached else None
    
    async def set_user_permissions(self, user_id: UUID, school_id: UUID, permissions: List[str]) -> bool:
        """Cache user permissions for specific school"""
        key = self._get_cache_key("permissions", f"{user_id}:{school_id}")
        return await self.set(
            key, 
            {'permissions': permissions}, 
            self.ttl_config['permissions']
        )
    
    async def get_school_features(self, school_id: UUID) -> Optional[List[str]]:
        """Get cached school features"""
        key = self._get_cache_key("school_features", str(school_id))
        cached = await self.get(key)
        return cached['features'] if cached else None
    
    async def set_school_features(self, school_id: UUID, features: List[str]) -> bool:
        """Cache school features"""
        key = self._get_cache_key("school_features", str(school_id))
        return await self.set(
            key, 
            {'features': features}, 
            self.ttl_config['features']
        )
    
    # Bulk Operations for Performance
    
    async def get_school_users_summary(self, school_id: UUID, roles: Optional[List[str]] = None, 
                                     limit: int = 100, offset: int = 0) -> Optional[List[Dict[str, Any]]]:
        """Get cached school users summary"""
        role_key = ":".join(sorted(roles)) if roles else "all"
        key = self._get_cache_key("school_users", f"{school_id}:{role_key}:{limit}:{offset}")
        cached = await self.get(key)
        return cached['users'] if cached else None
    
    async def set_school_users_summary(self, school_id: UUID, users: List[Dict[str, Any]], 
                                     roles: Optional[List[str]] = None, limit: int = 100, offset: int = 0) -> bool:
        """Cache school users summary"""
        role_key = ":".join(sorted(roles)) if roles else "all"
        key = self._get_cache_key("school_users", f"{school_id}:{role_key}:{limit}:{offset}")
        return await self.set(key, {'users': users}, 300)  # 5 minutes for bulk data
    
    # Cache Invalidation Helpers
    
    async def invalidate_user_all(self, user_id: UUID) -> int:
        """Invalidate all cache entries for a user"""
        pattern = self._get_cache_key("*", str(user_id)) + "*"
        return await self.delete_pattern(pattern)
    
    async def invalidate_school_all(self, school_id: UUID) -> int:
        """Invalidate all cache entries for a school"""
        pattern = self._get_cache_key("*", str(school_id)) + "*"
        return await self.delete_pattern(pattern)
    
    async def invalidate_user_school(self, user_id: UUID, school_id: UUID) -> int:
        """Invalidate cache entries for user-school relationship"""
        patterns = [
            self._get_cache_key("user_context", str(user_id)),
            self._get_cache_key("minimal_context", str(user_id), str(school_id)),
            self._get_cache_key("permissions", f"{user_id}:{school_id}"),
        ]
        
        deleted_count = 0
        for pattern in patterns:
            if await self.delete(pattern):
                deleted_count += 1
        
        return deleted_count
    
    # Health Check and Statistics
    
    async def health_check(self) -> Dict[str, Any]:
        """Check cache health and return statistics"""
        try:
            # Test basic connectivity
            await self.redis.ping()
            
            # Get some basic stats
            info = await self.redis.info()
            memory_usage = info.get('used_memory_human', 'unknown')
            connected_clients = info.get('connected_clients', 0)
            
            # Count our keys
            our_keys = await self.redis.keys("oneclass:*")
            key_count = len(our_keys) if our_keys else 0
            
            return {
                'status': 'healthy',
                'memory_usage': memory_usage,
                'connected_clients': connected_clients,
                'our_key_count': key_count,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get detailed cache statistics"""
        stats = {
            'user_contexts': 0,
            'minimal_contexts': 0,
            'school_info': 0,
            'clerk_data': 0,
            'permissions': 0,
            'subdomain_mappings': 0,
            'school_users': 0,
            'total_keys': 0
        }
        
        try:
            # Count different types of keys
            for key_type in stats.keys():
                if key_type == 'total_keys':
                    continue
                    
                pattern = f"oneclass:{key_type.replace('_', '_')}:*"
                keys = await self.redis.keys(pattern)
                stats[key_type] = len(keys) if keys else 0
            
            # Total count
            all_keys = await self.redis.keys("oneclass:*")
            stats['total_keys'] = len(all_keys) if all_keys else 0
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
        
        return stats


def cache_result(cache_key_func, ttl: int = 300):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Generate cache key
            cache_key = cache_key_func(*args, **kwargs)
            
            # Try to get from cache
            if hasattr(self, 'cache'):
                cached_result = await self.cache.get(cache_key)
                if cached_result:
                    return cached_result
            
            # Execute function
            result = await func(self, *args, **kwargs)
            
            # Cache the result
            if hasattr(self, 'cache') and result is not None:
                await self.cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator