"""
Enhanced Tenant Resolution System
Supports dual subdomain patterns with caching and performance optimization
"""

import re
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
from shared.database import get_async_session

logger = logging.getLogger(__name__)

# =====================================================
# TENANT RESOLUTION PATTERNS
# =====================================================

class SubdomainPattern(str, Enum):
    """Supported subdomain patterns"""
    
    # Pattern 1: school.oneclass.ac.zw 
    SCHOOL_ONECLASS = "school_oneclass"
    
    # Pattern 2: oneclass.school.ac.zw
    ONECLASS_SCHOOL = "oneclass_school"
    
    # Development patterns
    LOCALHOST_DEV = "localhost_dev"
    
    # Direct IP access
    IP_ACCESS = "ip_access"


@dataclass
class TenantResolution:
    """Result of tenant resolution"""
    
    school_id: str
    school_name: str
    subdomain: str
    pattern: SubdomainPattern
    subscription_tier: str
    enabled_modules: List[str]
    custom_domain: Optional[str] = None
    is_active: bool = True
    cache_key: Optional[str] = None
    resolved_at: datetime = None
    
    def __post_init__(self):
        if self.resolved_at is None:
            self.resolved_at = datetime.utcnow()


class EnhancedTenantResolver:
    """
    Enhanced tenant resolver supporting multiple subdomain patterns
    with caching and performance optimization
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.cache_ttl = 300  # 5 minutes cache
        self.negative_cache_ttl = 60  # 1 minute for non-existent tenants
        
        # Compile regex patterns for performance
        self.patterns = {
            # Pattern 1: churchill.oneclass.ac.zw
            SubdomainPattern.SCHOOL_ONECLASS: re.compile(
                r'^([a-zA-Z0-9-]+)\.oneclass\.ac\.zw(?::\d+)?$'
            ),
            # Pattern 2: oneclass.churchill.ac.zw  
            SubdomainPattern.ONECLASS_SCHOOL: re.compile(
                r'^oneclass\.([a-zA-Z0-9-]+)\.ac\.zw(?::\d+)?$'
            ),
            # Development: localhost with subdomain header
            SubdomainPattern.LOCALHOST_DEV: re.compile(
                r'^localhost(?::\d+)?$'
            ),
            # IP access
            SubdomainPattern.IP_ACCESS: re.compile(
                r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?$'
            )
        }
        
        # Domain validation patterns
        self.subdomain_validation = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]$')
        
        # Reserved subdomains that cannot be used by schools
        self.reserved_subdomains = {
            'www', 'api', 'admin', 'platform', 'docs', 'help', 'support',
            'mail', 'email', 'ftp', 'ssh', 'vpn', 'cdn', 'static', 'assets',
            'test', 'staging', 'dev', 'demo', 'sandbox', 'app', 'apps',
            'dashboard', 'portal', 'console', 'control', 'manage', 'system'
        }
    
    # =====================================================
    # MAIN RESOLUTION METHODS
    # =====================================================
    
    async def resolve_tenant(
        self, 
        host: str, 
        headers: Dict[str, str] = None,
        force_refresh: bool = False
    ) -> Optional[TenantResolution]:
        """
        Resolve tenant from host and headers with caching
        
        Args:
            host: Host header value
            headers: Additional request headers
            force_refresh: Skip cache and force database lookup
            
        Returns:
            TenantResolution or None if not found
        """
        
        if not host:
            return None
        
        # Generate cache key
        cache_key = self._generate_cache_key(host, headers)
        
        # Check cache first (unless forced refresh)
        if not force_refresh and self.redis_client:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached
        
        # Extract subdomain and pattern
        subdomain, pattern = await self._extract_subdomain_and_pattern(host, headers)
        
        if not subdomain:
            # Cache negative result
            if self.redis_client:
                await self._cache_negative_result(cache_key)
            return None
        
        # Resolve from database
        tenant_resolution = await self._resolve_from_database(subdomain, pattern)
        
        if tenant_resolution:
            tenant_resolution.cache_key = cache_key
            
            # Cache positive result
            if self.redis_client:
                await self._cache_result(cache_key, tenant_resolution)
        else:
            # Cache negative result
            if self.redis_client:
                await self._cache_negative_result(cache_key)
        
        return tenant_resolution
    
    async def _extract_subdomain_and_pattern(
        self, 
        host: str, 
        headers: Dict[str, str] = None
    ) -> Tuple[Optional[str], Optional[SubdomainPattern]]:
        """Extract subdomain and determine pattern"""
        
        host = host.lower().strip()
        headers = headers or {}
        
        # Try each pattern
        for pattern, regex in self.patterns.items():
            match = regex.match(host)
            
            if match:
                if pattern == SubdomainPattern.SCHOOL_ONECLASS:
                    # churchill.oneclass.ac.zw -> churchill
                    subdomain = match.group(1)
                    
                elif pattern == SubdomainPattern.ONECLASS_SCHOOL:
                    # oneclass.churchill.ac.zw -> churchill
                    subdomain = match.group(1)
                    
                elif pattern == SubdomainPattern.LOCALHOST_DEV:
                    # Development mode - check headers or fallback
                    subdomain = await self._get_dev_subdomain(headers)
                    
                elif pattern == SubdomainPattern.IP_ACCESS:
                    # IP access - check headers
                    subdomain = headers.get('x-subdomain') or headers.get('x-school-subdomain')
                
                # Validate subdomain
                if subdomain and self._is_valid_subdomain(subdomain):
                    return subdomain, pattern
        
        return None, None
    
    async def _get_dev_subdomain(self, headers: Dict[str, str]) -> Optional[str]:
        """Get subdomain for development mode"""
        
        # Check headers for development subdomain
        dev_subdomain = (
            headers.get('x-dev-subdomain') or 
            headers.get('x-school-subdomain') or
            headers.get('x-subdomain')
        )
        
        if dev_subdomain:
            return dev_subdomain
        
        # Fallback to default development school
        return 'dev-school'
    
    def _is_valid_subdomain(self, subdomain: str) -> bool:
        """Validate subdomain format and restrictions"""
        
        if not subdomain:
            return False
        
        # Check format
        if not self.subdomain_validation.match(subdomain):
            return False
        
        # Check reserved subdomains
        if subdomain.lower() in self.reserved_subdomains:
            return False
        
        # Length check
        if len(subdomain) < 2 or len(subdomain) > 63:
            return False
        
        return True
    
    # =====================================================
    # DATABASE RESOLUTION
    # =====================================================
    
    async def _resolve_from_database(
        self, 
        subdomain: str, 
        pattern: SubdomainPattern
    ) -> Optional[TenantResolution]:
        """Resolve tenant from database"""
        
        try:
            async for db in get_async_session():
                # Query school by subdomain
                query = text("""
                    SELECT 
                        s.id,
                        s.name,
                        s.subdomain,
                        s.subscription_tier,
                        s.is_active,
                        s.custom_domain,
                        sc.enabled_modules
                    FROM platform.schools s
                    LEFT JOIN platform.school_configurations sc ON s.id = sc.school_id
                    WHERE s.subdomain = :subdomain 
                        AND s.is_active = true
                """)
                
                result = await db.execute(query, {"subdomain": subdomain.lower()})
                row = result.fetchone()
                
                if not row:
                    logger.warning(f"School not found for subdomain: {subdomain}")
                    return None
                
                # Parse enabled modules
                enabled_modules = []
                if row.enabled_modules:
                    if isinstance(row.enabled_modules, str):
                        import json
                        try:
                            enabled_modules = json.loads(row.enabled_modules)
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in enabled_modules for school {row.id}")
                    elif isinstance(row.enabled_modules, list):
                        enabled_modules = row.enabled_modules
                
                # Default modules if none specified
                if not enabled_modules:
                    enabled_modules = [
                        'student_information_system',
                        'finance_management',
                        'academic_management'
                    ]
                
                return TenantResolution(
                    school_id=str(row.id),
                    school_name=row.name,
                    subdomain=row.subdomain,
                    pattern=pattern,
                    subscription_tier=row.subscription_tier or 'basic',
                    enabled_modules=enabled_modules,
                    custom_domain=row.custom_domain,
                    is_active=row.is_active
                )
                
        except Exception as e:
            logger.error(f"Database error resolving tenant {subdomain}: {e}")
            return None
    
    # =====================================================
    # CACHING METHODS
    # =====================================================
    
    def _generate_cache_key(self, host: str, headers: Dict[str, str] = None) -> str:
        """Generate cache key for tenant resolution"""
        
        # Include relevant headers in cache key
        header_keys = ['x-dev-subdomain', 'x-school-subdomain', 'x-subdomain']
        header_values = []
        
        if headers:
            for key in header_keys:
                value = headers.get(key)
                if value:
                    header_values.append(f"{key}:{value}")
        
        cache_input = f"{host}|{'|'.join(header_values)}"
        
        # Generate hash for cache key
        hash_object = hashlib.md5(cache_input.encode())
        return f"tenant_resolution:{hash_object.hexdigest()}"
    
    async def _get_from_cache(self, cache_key: str) -> Optional[TenantResolution]:
        """Get tenant resolution from cache"""
        
        if not self.redis_client:
            return None
        
        try:
            cached_data = await self.redis_client.hgetall(cache_key)
            
            if not cached_data:
                return None
            
            # Check for negative cache
            if cached_data.get(b'negative') == b'true':
                return None
            
            # Reconstruct TenantResolution
            enabled_modules = []
            if cached_data.get(b'enabled_modules'):
                import json
                enabled_modules = json.loads(cached_data[b'enabled_modules'].decode())
            
            return TenantResolution(
                school_id=cached_data[b'school_id'].decode(),
                school_name=cached_data[b'school_name'].decode(),
                subdomain=cached_data[b'subdomain'].decode(),
                pattern=SubdomainPattern(cached_data[b'pattern'].decode()),
                subscription_tier=cached_data[b'subscription_tier'].decode(),
                enabled_modules=enabled_modules,
                custom_domain=cached_data.get(b'custom_domain', b'').decode() or None,
                is_active=cached_data[b'is_active'].decode().lower() == 'true',
                cache_key=cache_key,
                resolved_at=datetime.fromisoformat(cached_data[b'resolved_at'].decode())
            )
            
        except Exception as e:
            logger.warning(f"Cache retrieval error for {cache_key}: {e}")
            return None
    
    async def _cache_result(self, cache_key: str, resolution: TenantResolution):
        """Cache tenant resolution result"""
        
        if not self.redis_client:
            return
        
        try:
            import json
            
            cache_data = {
                'school_id': resolution.school_id,
                'school_name': resolution.school_name,
                'subdomain': resolution.subdomain,
                'pattern': resolution.pattern.value,
                'subscription_tier': resolution.subscription_tier,
                'enabled_modules': json.dumps(resolution.enabled_modules),
                'custom_domain': resolution.custom_domain or '',
                'is_active': str(resolution.is_active).lower(),
                'resolved_at': resolution.resolved_at.isoformat()
            }
            
            await self.redis_client.hset(cache_key, mapping=cache_data)
            await self.redis_client.expire(cache_key, self.cache_ttl)
            
        except Exception as e:
            logger.warning(f"Cache storage error for {cache_key}: {e}")
    
    async def _cache_negative_result(self, cache_key: str):
        """Cache negative result (tenant not found)"""
        
        if not self.redis_client:
            return
        
        try:
            await self.redis_client.hset(cache_key, 'negative', 'true')
            await self.redis_client.expire(cache_key, self.negative_cache_ttl)
            
        except Exception as e:
            logger.warning(f"Negative cache storage error for {cache_key}: {e}")
    
    # =====================================================
    # UTILITY METHODS
    # =====================================================
    
    async def validate_subdomain_availability(self, subdomain: str) -> Dict[str, Any]:
        """
        Validate if a subdomain is available for registration
        
        Args:
            subdomain: Proposed subdomain
            
        Returns:
            Dict with validation results
        """
        
        result = {
            'available': False,
            'valid_format': False,
            'not_reserved': False,
            'not_taken': False,
            'suggestions': []
        }
        
        # Format validation
        result['valid_format'] = self._is_valid_subdomain(subdomain)
        
        if not result['valid_format']:
            result['suggestions'] = await self._generate_subdomain_suggestions(subdomain)
            return result
        
        # Reserved check
        result['not_reserved'] = subdomain.lower() not in self.reserved_subdomains
        
        if not result['not_reserved']:
            result['suggestions'] = await self._generate_subdomain_suggestions(subdomain)
            return result
        
        # Database check
        try:
            async for db in get_async_session():
                query = text("""
                    SELECT COUNT(*) as count
                    FROM platform.schools
                    WHERE subdomain = :subdomain
                """)
                
                result_row = await db.execute(query, {"subdomain": subdomain.lower()})
                count = result_row.fetchone().count
                
                result['not_taken'] = count == 0
                
                if not result['not_taken']:
                    result['suggestions'] = await self._generate_subdomain_suggestions(subdomain)
                else:
                    result['available'] = True
                
        except Exception as e:
            logger.error(f"Error checking subdomain availability: {e}")
        
        return result
    
    async def _generate_subdomain_suggestions(self, base_subdomain: str) -> List[str]:
        """Generate alternative subdomain suggestions"""
        
        suggestions = []
        base = re.sub(r'[^a-zA-Z0-9]', '', base_subdomain.lower())
        
        if len(base) < 2:
            base = 'school'
        
        # Try variations
        variations = [
            f"{base}1", f"{base}2", f"{base}3",
            f"{base}school", f"{base}edu",
            f"the{base}", f"{base}academy"
        ]
        
        for variation in variations:
            if len(suggestions) >= 5:  # Limit suggestions
                break
                
            if self._is_valid_subdomain(variation):
                # Quick check if available
                try:
                    async for db in get_async_session():
                        query = text("""
                            SELECT COUNT(*) as count
                            FROM platform.schools
                            WHERE subdomain = :subdomain
                        """)
                        
                        result = await db.execute(query, {"subdomain": variation})
                        count = result.fetchone().count
                        
                        if count == 0:
                            suggestions.append(variation)
                            
                except Exception:
                    pass  # Skip suggestions that cause errors
        
        return suggestions
    
    async def invalidate_cache(self, subdomain: str = None, school_id: str = None):
        """Invalidate cached tenant resolutions"""
        
        if not self.redis_client:
            return
        
        try:
            if subdomain:
                # Find and delete cache entries for this subdomain
                pattern = f"tenant_resolution:*{subdomain}*"
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
            
            if school_id:
                # More complex - would need to scan all keys and check school_id
                # For now, just log
                logger.info(f"Cache invalidation requested for school_id: {school_id}")
                
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
    
    async def get_tenant_stats(self) -> Dict[str, Any]:
        """Get tenant resolution statistics"""
        
        stats = {
            'total_active_tenants': 0,
            'pattern_distribution': {},
            'subscription_tiers': {},
            'cache_hit_rate': 0.0
        }
        
        try:
            async for db in get_async_session():
                # Total active tenants
                query = text("SELECT COUNT(*) as count FROM platform.schools WHERE is_active = true")
                result = await db.execute(query)
                stats['total_active_tenants'] = result.fetchone().count
                
                # Subscription tier distribution
                query = text("""
                    SELECT subscription_tier, COUNT(*) as count
                    FROM platform.schools
                    WHERE is_active = true
                    GROUP BY subscription_tier
                """)
                result = await db.execute(query)
                for row in result:
                    stats['subscription_tiers'][row.subscription_tier or 'basic'] = row.count
                
                # Pattern distribution would need request log analysis
                stats['pattern_distribution'] = {
                    'school_oneclass': 0,  # Would be populated from logs
                    'oneclass_school': 0,
                    'development': 0,
                    'ip_access': 0
                }
                
        except Exception as e:
            logger.error(f"Error getting tenant stats: {e}")
        
        return stats


# =====================================================
# GLOBAL RESOLVER INSTANCE
# =====================================================

# Create global resolver instance (will be configured in app startup)
tenant_resolver: Optional[EnhancedTenantResolver] = None


async def initialize_tenant_resolver(redis_client: Optional[redis.Redis] = None):
    """Initialize global tenant resolver"""
    global tenant_resolver
    tenant_resolver = EnhancedTenantResolver(redis_client=redis_client)
    logger.info("Enhanced tenant resolver initialized")


def get_tenant_resolver() -> EnhancedTenantResolver:
    """Get global tenant resolver instance"""
    if tenant_resolver is None:
        raise RuntimeError("Tenant resolver not initialized. Call initialize_tenant_resolver() first.")
    return tenant_resolver