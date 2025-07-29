"""
Public school routes for tenant discovery
These endpoints don't require authentication and are used for subdomain resolution
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import List, Optional
from pydantic import BaseModel

from shared.database import get_async_session

router = APIRouter(prefix="/schools", tags=["public-schools"])


class PublicSchoolInfo(BaseModel):
    """Public school information for tenant discovery"""
    id: str
    name: str
    subdomain: str
    type: str
    status: str
    logo_url: Optional[str] = None


class SchoolSubdomainInfo(BaseModel):
    """School information for subdomain resolution"""
    subdomain: str
    schoolName: str
    schoolId: str
    type: str
    status: str
    logo_url: Optional[str] = None


@router.get("/public", response_model=List[PublicSchoolInfo])
async def get_public_schools(
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get list of public schools for the school selector
    Only returns basic information for schools that allow public discovery
    """
    try:
        query = text("""
            SELECT 
                id,
                name,
                subdomain,
                school_type as type,
                status,
                logo_url
            FROM platform.schools 
            WHERE status = 'active'
            AND allow_public_discovery = true
            ORDER BY name
        """)
        
        result = await db.execute(query)
        schools = result.fetchall()
        
        return [
            PublicSchoolInfo(
                id=str(school.id),
                name=school.name,
                subdomain=school.subdomain,
                type=school.type or 'school',
                status=school.status,
                logo_url=school.logo_url
            )
            for school in schools
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch public schools: {str(e)}"
        )


@router.get("/by-subdomain/{subdomain}", response_model=SchoolSubdomainInfo)
async def get_school_by_subdomain(
    subdomain: str,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get school information by subdomain for tenant resolution
    This is used by the frontend to determine which school the user is accessing
    """
    try:
        # Validate subdomain format
        if not subdomain or len(subdomain) < 2 or len(subdomain) > 63:
            raise HTTPException(
                status_code=400,
                detail="Invalid subdomain format"
            )
        
        # Query school by subdomain
        query = text("""
            SELECT 
                id,
                name,
                subdomain,
                school_type as type,
                status,
                logo_url
            FROM platform.schools 
            WHERE subdomain = :subdomain
            AND status IN ('active', 'setup')
        """)
        
        result = await db.execute(query, {"subdomain": subdomain})
        school = result.fetchone()
        
        if not school:
            raise HTTPException(
                status_code=404,
                detail=f"School not found for subdomain: {subdomain}"
            )
        
        return {
            "subdomain": school.subdomain,
            "schoolName": school.name,
            "schoolId": str(school.id),
            "type": school.type or 'school',
            "status": school.status,
            "logo_url": school.logo_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch school by subdomain: {str(e)}"
        )


@router.get("/subdomain-check/{subdomain}")
async def check_subdomain_availability(
    subdomain: str,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Check if a subdomain is available for registration
    Used during school onboarding
    """
    try:
        # Validate subdomain format
        import re
        subdomain_pattern = r'^[a-z0-9]([a-z0-9-]{1,61}[a-z0-9])?$'
        if not re.match(subdomain_pattern, subdomain):
            return {
                "available": False,
                "reason": "Invalid subdomain format. Use only lowercase letters, numbers, and hyphens."
            }
        
        # Check if subdomain is reserved
        reserved_subdomains = {
            'www', 'api', 'admin', 'app', 'mail', 'ftp', 'blog', 'shop',
            'support', 'help', 'docs', 'status', 'cdn', 'assets', 'static',
            'media', 'images', 'files', 'download', 'upload', 'secure',
            'ssl', 'vpn', 'test', 'staging', 'dev', 'demo', 'beta'
        }
        
        if subdomain.lower() in reserved_subdomains:
            return {
                "available": False,
                "reason": "This subdomain is reserved for system use."
            }
        
        # Check if subdomain exists in database
        query = text("""
            SELECT COUNT(*) as count
            FROM platform.schools 
            WHERE subdomain = :subdomain
        """)
        
        result = await db.execute(query, {"subdomain": subdomain})
        count = result.scalar()
        
        if count > 0:
            return {
                "available": False,
                "reason": "This subdomain is already taken."
            }
        
        return {
            "available": True,
            "reason": "Subdomain is available."
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check subdomain availability: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for public school services"""
    return {
        "status": "healthy",
        "service": "public-schools",
        "timestamp": "2025-01-28T12:00:00Z"
    }
