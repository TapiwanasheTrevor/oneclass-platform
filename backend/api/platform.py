"""
Platform Management API
Handles school creation, user management, and platform administration
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Optional
import re
import logging
import uuid
import json
from datetime import datetime

from shared.database import get_db
from shared.models.platform import School, SchoolConfiguration
from shared.models.platform_user import PlatformUser as User
from shared.middleware.tenant_middleware import get_user_session, UserSession

logger = logging.getLogger(__name__)

# Create platform router
platform_router = APIRouter(prefix="/platform", tags=["Platform Management"])


# Pydantic models for request/response
class SchoolContactInfo(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    website: Optional[str] = None


class SchoolAddress(BaseModel):
    line1: str
    line2: Optional[str] = None
    city: str
    province: str
    postal_code: Optional[str] = None


class AdminUser(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None


class SchoolConfiguration(BaseModel):
    academic_year: Optional[str] = None
    term_structure: Optional[str] = None
    grade_structure: Optional[str] = None
    timezone: Optional[str] = "Africa/Harare"
    language: Optional[str] = "en"
    currency: Optional[str] = "USD"


class CreateSchoolRequest(BaseModel):
    name: str
    type: str  # primary, secondary, combined, college
    contact: SchoolContactInfo
    address: SchoolAddress
    established_year: Optional[int] = None
    student_count_range: Optional[str] = None
    subscription_tier: str = "basic"
    configuration: Optional[SchoolConfiguration] = None
    admin_user: AdminUser

    @validator("name")
    def validate_name(cls, v):
        if len(v.strip()) < 3:
            raise ValueError("School name must be at least 3 characters long")
        return v.strip()

    @validator("type")
    def validate_type(cls, v):
        valid_types = ["primary", "secondary", "combined", "college"]
        if v not in valid_types:
            raise ValueError(f"School type must be one of: {valid_types}")
        return v

    @validator("subscription_tier")
    def validate_tier(cls, v):
        valid_tiers = ["basic", "professional", "enterprise"]
        if v not in valid_tiers:
            raise ValueError(f"Subscription tier must be one of: {valid_tiers}")
        return v


class SchoolResponse(BaseModel):
    id: str
    name: str
    subdomain: str
    type: str
    status: str
    subscription_tier: str
    is_active: bool
    created_at: str
    admin_user: Dict[str, str]


def generate_subdomain(school_name: str, db: Session) -> str:
    """Generate a unique subdomain from school name"""
    # Clean the school name
    clean_name = re.sub(r"[^a-zA-Z0-9\s]", "", school_name.lower())
    clean_name = re.sub(r"\s+", "-", clean_name.strip())

    # Remove common words
    common_words = [
        "school",
        "college",
        "university",
        "primary",
        "secondary",
        "high",
        "academy",
    ]
    words = clean_name.split("-")
    filtered_words = [
        word for word in words if word not in common_words and len(word) > 1
    ]

    # Create base subdomain
    base_subdomain = "-".join(filtered_words[:3])  # Use first 3 meaningful words

    if not base_subdomain:
        base_subdomain = "school"

    # Ensure it's between 3-30 characters
    if len(base_subdomain) < 3:
        base_subdomain = f"{base_subdomain}-sch"
    elif len(base_subdomain) > 30:
        base_subdomain = base_subdomain[:30]

    # Check uniqueness and add suffix if needed
    subdomain = base_subdomain
    counter = 1

    while True:
        existing = db.execute(
            text("SELECT id FROM platform.schools WHERE subdomain = :subdomain"),
            {"subdomain": subdomain},
        ).fetchone()

        if not existing:
            break

        counter += 1
        subdomain = f"{base_subdomain}{counter}"

        # Prevent infinite loops
        if counter > 999:
            subdomain = f"{base_subdomain}-{uuid.uuid4().hex[:6]}"
            break

    return subdomain


def get_enabled_modules_for_tier(tier: str) -> List[str]:
    """Get default enabled modules for subscription tier"""
    module_tiers = {
        "basic": ["student_information_system", "basic_reports"],
        "professional": [
            "student_information_system",
            "finance_management",
            "academic_management",
            "basic_reports",
            "communication_hub",
            "parent_portal",
        ],
        "enterprise": [
            "student_information_system",
            "finance_management",
            "academic_management",
            "advanced_reporting",
            "communication_hub",
            "parent_portal",
            "api_access",
        ],
    }

    return module_tiers.get(tier, module_tiers["basic"])


@platform_router.post("/schools", response_model=SchoolResponse)
async def create_school(request: CreateSchoolRequest, db: Session = Depends(get_db)):
    """Create a new school and admin user"""
    try:
        # Generate unique subdomain
        subdomain = generate_subdomain(request.name, db)

        # Get enabled modules for tier
        enabled_modules = get_enabled_modules_for_tier(request.subscription_tier)

        # Create school record
        school_data = {
            "id": uuid.uuid4(),
            "name": request.name,
            "subdomain": subdomain,
            "status": "active",
            "subscription_tier": request.subscription_tier,
            "email": request.contact.email,
            "phone": request.contact.phone,
            "school_type": request.type,
            "establishment_year": request.established_year,
            "is_active": True,
            "is_verified": False,
            "configuration": {
                "contact": request.contact.dict(),
                "address": request.address.dict(),
                "academic": (
                    request.configuration.dict() if request.configuration else {}
                ),
                "branding": {
                    "primary_color": "#2563eb",
                    "secondary_color": "#64748b",
                    "theme": "light",
                },
                "features": {"enabled_modules": enabled_modules},
            },
        }

        # Insert school
        db.execute(
            text(
                """
                INSERT INTO platform.schools 
                (id, name, subdomain, status, subscription_tier, email, phone, 
                 school_type, is_active, configuration)
                VALUES 
                (:id, :name, :subdomain, :status, :subscription_tier, :email, :phone,
                 :school_type, :is_active, :configuration)
            """
            ),
            {
                "id": school_data["id"],
                "name": school_data["name"],
                "subdomain": subdomain,
                "status": "active",
                "subscription_tier": school_data["subscription_tier"],
                "email": school_data["email"],
                "phone": school_data["phone"],
                "school_type": school_data["school_type"],
                "is_active": school_data["is_active"],
                "configuration": json.dumps(school_data["configuration"]),
            },
        )

        # Create admin user
        admin_user_data = {
            "id": uuid.uuid4(),
            "school_id": school_data["id"],
            "email": request.admin_user.email,
            "first_name": request.admin_user.first_name,
            "last_name": request.admin_user.last_name,
            "phone": request.admin_user.phone,
            "role": "admin",
            "is_active": True,
            "is_verified": False,
            "user_metadata": {
                "onboarding_completed": True,
                "created_via": "school_onboarding",
            },
        }

        db.execute(
            text(
                """
                INSERT INTO platform.users 
                (id, school_id, email, first_name, last_name, phone, role, is_active)
                VALUES 
                (:id, :school_id, :email, :first_name, :last_name, :phone, :role, :is_active)
            """
            ),
            {
                "id": admin_user_data["id"],
                "school_id": admin_user_data["school_id"],
                "email": admin_user_data["email"],
                "first_name": admin_user_data["first_name"],
                "last_name": admin_user_data["last_name"],
                "phone": admin_user_data["phone"],
                "role": admin_user_data["role"],
                "is_active": admin_user_data["is_active"],
            },
        )

        # Create school configuration record
        config_data = {
            "id": uuid.uuid4(),
            "school_id": school_data["id"],
            "currency": (
                request.configuration.currency if request.configuration else "USD"
            ),
            "timezone": (
                request.configuration.timezone
                if request.configuration
                else "Africa/Harare"
            ),
            "language": (
                request.configuration.language if request.configuration else "en"
            ),
            "enabled_modules": json.dumps(enabled_modules),
        }

        db.execute(
            text(
                """
                INSERT INTO platform.school_configurations 
                (id, school_id, currency, timezone, language, enabled_modules)
                VALUES 
                (:id, :school_id, :currency, :timezone, :language, :enabled_modules)
            """
            ),
            config_data,
        )

        # Commit transaction
        db.commit()

        logger.info(f"School created successfully: {school_data['name']} ({subdomain})")

        return SchoolResponse(
            id=str(school_data["id"]),
            name=school_data["name"],
            subdomain=subdomain,
            type=school_data["school_type"],
            status="active",
            subscription_tier=school_data["subscription_tier"],
            is_active=school_data["is_active"],
            created_at=datetime.utcnow().isoformat(),
            admin_user={
                "id": str(admin_user_data["id"]),
                "email": admin_user_data["email"],
                "name": f"{admin_user_data['first_name']} {admin_user_data['last_name']}",
            },
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create school: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "school_creation_failed",
                "message": "Failed to create school. Please try again.",
                "details": str(e) if logger.level <= logging.DEBUG else None,
            },
        )


@platform_router.get("/schools/{school_id}")
async def get_school(
    school_id: str,
    db: Session = Depends(get_db),
    user_session: UserSession = Depends(get_user_session),
):
    """Get school information"""
    # Check if user is platform admin or belongs to the school
    if user_session.role != "platform_admin" and user_session.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    school = db.execute(
        text("SELECT * FROM platform.schools WHERE id = :school_id"),
        {"school_id": school_id},
    ).fetchone()

    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="School not found"
        )

    return dict(school)


@platform_router.get("/schools/by-subdomain/{subdomain}")
async def get_school_by_subdomain(subdomain: str, db: Session = Depends(get_db)):
    """Get school information by subdomain (public endpoint for middleware)"""
    school = db.execute(
        text(
            """
            SELECT s.*, sc.enabled_modules, sc.primary_color, sc.theme
            FROM platform.schools s
            LEFT JOIN platform.school_configurations sc ON s.id = sc.school_id
            WHERE s.subdomain = :subdomain AND s.is_active = true
        """
        ),
        {"subdomain": subdomain},
    ).fetchone()

    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="School not found"
        )

    return {
        "id": str(school.id),
        "name": school.name,
        "subdomain": school.subdomain,
        "is_active": school.is_active,
        "subscription_tier": school.subscription_tier,
        "custom_domain": None,  # TODO: Implement custom domains
        "enabled_modules": school.enabled_modules or [],
        "branding": {"primary_color": school.primary_color, "theme": school.theme},
    }


@platform_router.get("/schools")
async def list_schools(
    db: Session = Depends(get_db), user_session: UserSession = Depends(get_user_session)
):
    """List all schools (platform admin only)"""
    if user_session.role != "platform_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admin access required",
        )

    schools = db.execute(
        text("SELECT * FROM platform.schools ORDER BY created_at DESC")
    ).fetchall()

    return [dict(school) for school in schools]
