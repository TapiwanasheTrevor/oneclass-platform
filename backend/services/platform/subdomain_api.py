"""Platform Subdomain API
Handles subdomain-based school resolution for multi-tenant routing"""

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any, List
from datetime import datetime
import re

from core.database import get_db
from shared.models.platform import School, SchoolConfiguration, SchoolDomain
from core.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/api/v1/schools", tags=["schools", "subdomain"])

# Subdomain validation regex
SUBDOMAIN_PATTERN = re.compile(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$')

# Reserved subdomains that cannot be used by schools
RESERVED_SUBDOMAINS = {
    'www', 'api', 'admin', 'app', 'mail', 'email', 'ftp', 'smtp', 'pop',
    'imap', 'webmail', 'secure', 'ssl', 'tls', 'cdn', 'static', 'assets',
    'files', 'upload', 'download', 'support', 'help', 'docs', 'blog',
    'news', 'status', 'monitoring', 'health', 'ping', 'test', 'dev',
    'staging', 'prod', 'production', 'platform', 'system', 'root',
    'administrator', 'moderator', 'staff', 'team'
}


class SchoolSubdomainService:
    """Service for handling school subdomain operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_school_by_subdomain(self, subdomain: str) -> Optional[Dict[str, Any]]:
        """Get school information by subdomain"""
        # Validate subdomain format
        if not self._is_valid_subdomain(subdomain):
            raise ValidationError(f"Invalid subdomain format: {subdomain}")
        
        # Query school by subdomain
        query = (
            select(School, SchoolConfiguration)
            .outerjoin(SchoolConfiguration, School.id == SchoolConfiguration.school_id)
            .where(School.subdomain == subdomain.lower())
            .where(School.is_active == True)
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        school, config = row
        
        # Build response
        school_info = {
            "id": str(school.id),
            "name": school.name,
            "subdomain": school.subdomain,
            "is_active": school.is_active,
            "subscription_tier": school.subscription_tier,
            "created_at": school.created_at.isoformat(),
            "timezone": school.timezone,
            "country": school.country,
            "region": school.region,
            "configuration": {}
        }
        
        # Add configuration if available
        if config:
            school_info["configuration"] = {
                "branding": {
                    "logo_url": config.logo_url,
                    "favicon_url": config.favicon_url,
                    "primary_color": config.primary_color,
                    "secondary_color": config.secondary_color,
                    "accent_color": config.accent_color,
                    "font_family": config.font_family
                },
                "contact": {
                    "website": config.website,
                    "phone": config.phone,
                    "email": config.email,
                    "address": config.address
                },
                "academic": {
                    "academic_year_start": config.academic_year_start,
                    "academic_year_end": config.academic_year_end,
                    "grading_system": config.grading_system,
                    "attendance_tracking": config.attendance_tracking
                },
                "finance": {
                    "currency": config.currency,
                    "payment_methods": config.payment_methods,
                    "late_fee_policy": config.late_fee_policy,
                    "invoice_numbering": config.invoice_numbering
                },
                "features": {
                    "enabled_modules": config.enabled_modules,
                    "custom_fields": config.custom_fields,
                    "integrations": config.integrations
                },
                "updated_at": config.updated_at.isoformat() if config.updated_at else None
            }
        
        return school_info
    
    async def validate_subdomain_availability(self, subdomain: str, exclude_school_id: Optional[str] = None) -> Dict[str, Any]:
        """Validate if a subdomain is available for use"""
        subdomain = subdomain.lower().strip()
        
        # Validate format
        if not self._is_valid_subdomain(subdomain):
            return {
                "available": False,
                "reason": "invalid_format",
                "message": "Subdomain must be 3-63 characters long and contain only letters, numbers, and hyphens"
            }
        
        # Check if reserved
        if subdomain in RESERVED_SUBDOMAINS:
            return {
                "available": False,
                "reason": "reserved",
                "message": "This subdomain is reserved and cannot be used"
            }
        
        # Check if already taken
        query = select(School).where(School.subdomain == subdomain)
        if exclude_school_id:
            query = query.where(School.id != exclude_school_id)
        
        result = await self.db.execute(query)
        existing_school = result.scalar_one_or_none()
        
        if existing_school:
            return {
                "available": False,
                "reason": "taken",
                "message": "This subdomain is already in use by another school"
            }
        
        # Check custom domains table
        domain_query = select(SchoolDomain).where(SchoolDomain.subdomain == subdomain)
        if exclude_school_id:
            domain_query = domain_query.where(SchoolDomain.school_id != exclude_school_id)
        
        domain_result = await self.db.execute(domain_query)
        existing_domain = domain_result.scalar_one_or_none()
        
        if existing_domain:
            return {
                "available": False,
                "reason": "taken",
                "message": "This subdomain is already in use"
            }
        
        return {
            "available": True,
            "subdomain": subdomain,
            "message": "Subdomain is available"
        }
    
    async def suggest_subdomains(self, school_name: str, count: int = 5) -> List[str]:
        """Suggest available subdomains based on school name"""
        base_name = self._normalize_school_name(school_name)
        suggestions = []
        
        # Try base name first
        if (await self.validate_subdomain_availability(base_name))["available"]:
            suggestions.append(base_name)
        
        # Try variations
        variations = [
            f"{base_name}school",
            f"{base_name}academy",
            f"{base_name}college",
            f"{base_name}edu",
            f"{base_name}zw",
        ]
        
        # Add numbered variations
        for i in range(2, 20):
            variations.append(f"{base_name}{i}")
        
        for variation in variations:
            if len(suggestions) >= count:
                break
            
            if (await self.validate_subdomain_availability(variation))["available"]:
                suggestions.append(variation)
        
        return suggestions[:count]
    
    def _is_valid_subdomain(self, subdomain: str) -> bool:
        """Validate subdomain format"""
        if not subdomain:
            return False
        
        if len(subdomain) < 3 or len(subdomain) > 63:
            return False
        
        if not SUBDOMAIN_PATTERN.match(subdomain):
            return False
        
        # Cannot start or end with hyphen
        if subdomain.startswith('-') or subdomain.endswith('-'):
            return False
        
        return True
    
    def _normalize_school_name(self, name: str) -> str:
        """Normalize school name for subdomain suggestion"""
        # Remove common words and normalize
        normalized = name.lower()
        
        # Remove common school terms
        terms_to_remove = [
            'school', 'college', 'academy', 'university', 'institute',
            'high', 'primary', 'secondary', 'prep', 'preparatory',
            'the', 'of', 'and', '&', 'for'
        ]
        
        for term in terms_to_remove:
            normalized = normalized.replace(term, '')
        
        # Remove special characters and spaces
        normalized = re.sub(r'[^a-z0-9]', '', normalized)
        
        # Ensure minimum length
        if len(normalized) < 3:
            normalized = f"{normalized}school"[:20]  # Truncate if too long
        
        return normalized[:20]  # Max 20 chars for suggestions


# Dependency injection
async def get_subdomain_service(db: AsyncSession = Depends(get_db)) -> SchoolSubdomainService:
    return SchoolSubdomainService(db)


# API Endpoints
@router.get("/by-subdomain/{subdomain}")
async def get_school_by_subdomain(
    subdomain: str,
    service: SchoolSubdomainService = Depends(get_subdomain_service)
):
    """Get school information by subdomain"""
    school_info = await service.get_school_by_subdomain(subdomain)
    
    if not school_info:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "school_not_found",
                "message": f"No active school found for subdomain: {subdomain}",
                "subdomain": subdomain
            }
        )
    
    return school_info


@router.post("/validate-subdomain")
async def validate_subdomain(
    request: Dict[str, Any],
    service: SchoolSubdomainService = Depends(get_subdomain_service)
):
    """Validate subdomain availability"""
    subdomain = request.get("subdomain")
    exclude_school_id = request.get("exclude_school_id")
    
    if not subdomain:
        raise HTTPException(
            status_code=400,
            detail={"error": "missing_subdomain", "message": "Subdomain is required"}
        )
    
    result = await service.validate_subdomain_availability(subdomain, exclude_school_id)
    return result


@router.post("/suggest-subdomains")
async def suggest_subdomains(
    request: Dict[str, Any],
    service: SchoolSubdomainService = Depends(get_subdomain_service)
):
    """Suggest available subdomains based on school name"""
    school_name = request.get("school_name")
    count = request.get("count", 5)
    
    if not school_name:
        raise HTTPException(
            status_code=400,
            detail={"error": "missing_school_name", "message": "School name is required"}
        )
    
    suggestions = await service.suggest_subdomains(school_name, count)
    
    return {
        "suggestions": suggestions,
        "school_name": school_name,
        "count": len(suggestions)
    }


@router.get("/health")
async def subdomain_health_check():
    """Health check for subdomain service"""
    return {
        "status": "healthy",
        "service": "subdomain-resolution",
        "timestamp": datetime.utcnow().isoformat()
    }
