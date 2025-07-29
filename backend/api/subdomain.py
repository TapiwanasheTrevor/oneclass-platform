"""
Subdomain API Routes
Public endpoints for school resolution and subdomain validation
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime
import re
import logging

from shared.auth import db_manager
from shared.models.platform import School

logger = logging.getLogger(__name__)

# Create subdomain router (public endpoints)
subdomain_router = APIRouter(prefix="/api/v1/schools", tags=["Subdomain Resolution"])

class SubdomainValidationRequest(BaseModel):
    subdomain: str
    
    @validator('subdomain')
    def validate_subdomain(cls, v):
        # Subdomain validation rules
        if not v or len(v) < 3 or len(v) > 20:
            raise ValueError('Subdomain must be between 3 and 20 characters')
        
        if not re.match(r'^[a-z0-9-]+$', v.lower()):
            raise ValueError('Subdomain can only contain lowercase letters, numbers, and hyphens')
        
        if v.startswith('-') or v.endswith('-'):
            raise ValueError('Subdomain cannot start or end with a hyphen')
        
        # Reserved subdomains
        reserved = {
            'www', 'api', 'admin', 'app', 'mail', 'ftp', 'blog', 'shop', 
            'support', 'help', 'docs', 'status', 'cdn', 'assets', 'static',
            'platform', 'system', 'root', 'test', 'staging', 'prod', 'demo'
        }
        
        if v.lower() in reserved:
            raise ValueError('This subdomain is reserved and cannot be used')
        
        return v.lower()

class SubdomainSuggestionRequest(BaseModel):
    preferred_name: str
    school_name: Optional[str] = None

class SchoolInfo(BaseModel):
    id: str
    name: str
    subdomain: str
    status: str
    subscription_tier: str
    configuration: dict

@subdomain_router.get("/by-subdomain/{subdomain}")
async def get_school_by_subdomain(subdomain: str):
    """Get school information by subdomain"""
    try:
        # Validate subdomain format
        validation_request = SubdomainValidationRequest(subdomain=subdomain)
        clean_subdomain = validation_request.subdomain
        
        # Query school by subdomain
        async with db_manager.get_connection() as db:
            query = """
                SELECT id, name, subdomain, status, subscription_tier, is_active
                FROM platform.schools 
                WHERE subdomain = $1 AND is_active = true
            """
            
            school = await db.fetchrow(query, clean_subdomain)
        
        if not school:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "school_not_found",
                    "message": f"No active school found with subdomain '{subdomain}'",
                    "subdomain": subdomain
                }
            )
        
        # Check school status
        if school["status"] == "suspended":
            return JSONResponse(
                status_code=200,
                content={
                    "school": {
                        "id": str(school["id"]),
                        "name": school["name"],
                        "subdomain": school["subdomain"],
                        "status": school["status"],
                        "message": "School account is currently suspended"
                    },
                    "redirect": "/suspended"
                }
            )
        
        if school["status"] == "inactive":
            return JSONResponse(
                status_code=200,
                content={
                    "school": {
                        "id": str(school["id"]),
                        "name": school["name"],
                        "subdomain": school["subdomain"],
                        "status": school["status"],
                        "message": "School account is inactive"
                    },
                    "redirect": "/suspended?reason=inactive"
                }
            )
        
        # Return school information
        school_config = {
            "branding": {
                "primary_color": "#2563eb",
                "secondary_color": "#64748b",
                "logo_url": None,
                "favicon_url": None,
                "theme": "light"
            },
            "features": {
                "enabled_modules": [
                    "student_information_system",
                    "finance_management", 
                    "academic_management"
                ]
            },
            "settings": {
                "timezone": "Africa/Harare",
                "language": "en",
                "currency": "ZWL"
            }
        }
        
        return {
            "school": {
                "id": str(school["id"]),
                "name": school["name"],
                "subdomain": school["subdomain"],
                "status": school["status"],
                "subscription_tier": school["subscription_tier"],
                "configuration": school_config
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_subdomain",
                "message": str(e),
                "subdomain": subdomain
            }
        )
    except Exception as e:
        logger.error(f"Error resolving subdomain {subdomain}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "subdomain_resolution_error",
                "message": "Failed to resolve school subdomain"
            }
        )

@subdomain_router.post("/validate-subdomain")
async def validate_subdomain(request: SubdomainValidationRequest):
    """Validate if subdomain is available"""
    try:
        subdomain = request.subdomain
        
        # Check if subdomain is already taken
        async with db_manager.get_connection() as db:
            query = "SELECT id FROM platform.schools WHERE subdomain = $1"
            existing_school = await db.fetchval(query, subdomain)
        
        if existing_school:
            return {
                "available": False,
                "subdomain": subdomain,
                "reason": "already_taken",
                "message": f"Subdomain '{subdomain}' is already in use"
            }
        
        return {
            "available": True,
            "subdomain": subdomain,
            "message": f"Subdomain '{subdomain}' is available"
        }
        
    except ValueError as e:
        return {
            "available": False,
            "subdomain": request.subdomain,
            "reason": "invalid_format",
            "message": str(e)
        }
    except Exception as e:
        logger.error(f"Error validating subdomain: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "validation_error",
                "message": "Failed to validate subdomain"
            }
        )

@subdomain_router.post("/suggest-subdomains")
async def suggest_subdomains(request: SubdomainSuggestionRequest):
    """Suggest available subdomains based on school name"""
    try:
        base_name = request.preferred_name.lower()
        school_name = request.school_name or request.preferred_name
        
        # Clean and normalize the name
        clean_name = re.sub(r'[^a-z0-9\s]', '', base_name)
        clean_name = re.sub(r'\s+', '', clean_name)
        
        # Generate suggestions
        suggestions = []
        
        # Primary suggestion
        if len(clean_name) >= 3:
            suggestions.append(clean_name[:15])
        
        # Add variations
        words = school_name.lower().split()
        if len(words) > 1:
            # Acronym
            acronym = ''.join(word[0] for word in words if word)
            if len(acronym) >= 3:
                suggestions.append(acronym)
            
            # First word + abbreviation
            if len(words[0]) >= 3:
                suggestions.append(words[0][:10])
                suggestions.append(f"{words[0][:8]}sch")
                suggestions.append(f"{words[0][:8]}school")
        
        # Add numerical suffixes
        base_suggestions = suggestions.copy()
        for base in base_suggestions[:3]:  # Only for first 3 suggestions
            for i in range(1, 6):
                suggestions.append(f"{base}{i}")
        
        # Add location-based suffixes
        zimbabwe_cities = ['harare', 'bulawayo', 'mutare', 'gweru', 'kwekwe']
        for base in base_suggestions[:2]:  # Only for first 2 suggestions
            for city in zimbabwe_cities[:3]:
                suggestions.append(f"{base}{city[:3]}")
        
        # Remove duplicates and invalid suggestions
        unique_suggestions = []
        seen = set()
        
        for suggestion in suggestions:
            if suggestion not in seen and len(suggestion) >= 3 and len(suggestion) <= 20:
                try:
                    # Validate format
                    SubdomainValidationRequest(subdomain=suggestion)
                    unique_suggestions.append(suggestion)
                    seen.add(suggestion)
                    if len(unique_suggestions) >= 10:  # Limit to 10 suggestions
                        break
                except ValueError:
                    continue
        
        # Check availability for each suggestion
        available_suggestions = []
        async with db_manager.get_connection() as db:
            for suggestion in unique_suggestions:
                query = "SELECT id FROM platform.schools WHERE subdomain = $1"
                existing = await db.fetchval(query, suggestion)
                if not existing:
                    available_suggestions.append({
                        "subdomain": suggestion,
                        "available": True,
                        "score": 100 - (len(unique_suggestions) - unique_suggestions.index(suggestion)) * 10
                    })
        
        return {
            "query": request.preferred_name,
            "suggestions": available_suggestions[:8],  # Return top 8
            "total_checked": len(unique_suggestions),
            "available_count": len(available_suggestions)
        }
        
    except Exception as e:
        logger.error(f"Error generating subdomain suggestions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "suggestion_error",
                "message": "Failed to generate subdomain suggestions"
            }
        )