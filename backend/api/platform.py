"""
Platform Management API
Handles school provisioning, discovery, and platform administration
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Optional, Any
import re
import logging
import uuid
import json
from datetime import datetime

from shared.database import get_async_session
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


def _parse_json_field(value: Any, default: Any) -> Any:
    if value is None:
        return default.copy() if isinstance(default, (dict, list)) else default
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed
        except json.JSONDecodeError:
            return default.copy() if isinstance(default, (dict, list)) else default
    return value


def _normalize_enabled_modules(value: Any) -> List[str]:
    modules = _parse_json_field(value, [])
    if isinstance(modules, list):
        return [str(module) for module in modules]
    return []


def _build_school_summary_payload(school_row: Any) -> Dict[str, Any]:
    enabled_modules = _normalize_enabled_modules(getattr(school_row, "enabled_modules", []))
    return {
        "id": str(school_row.id),
        "name": school_row.name,
        "subdomain": school_row.subdomain,
        "is_active": bool(school_row.is_active),
        "subscription_tier": school_row.subscription_tier,
        "custom_domain": None,
        "enabled_modules": enabled_modules,
        "branding": {
            "primary_color": getattr(school_row, "primary_color", None),
            "secondary_color": getattr(school_row, "secondary_color", None),
            "logo_url": getattr(school_row, "logo_url", None),
            "theme": getattr(school_row, "theme", None),
        },
    }


def _build_school_context_payload(school_row: Any) -> Dict[str, Any]:
    school_configuration = _parse_json_field(getattr(school_row, "configuration", None), {})
    branding_config = school_configuration.get("branding", {})
    settings_config = school_configuration.get("settings", {})
    academic_config = school_configuration.get("academic", {})
    feature_config = school_configuration.get("features", {})

    enabled_modules = _normalize_enabled_modules(
        getattr(school_row, "enabled_modules", None)
        or feature_config.get("enabled_modules", [])
    )
    feature_flags = _parse_json_field(getattr(school_row, "feature_flags", None), {})
    features_enabled = {module: True for module in enabled_modules}
    if isinstance(feature_flags, dict):
        for key, value in feature_flags.items():
            features_enabled[str(key)] = bool(value)

    if "finance_management" in features_enabled:
        features_enabled["finance_module"] = True
    if "student_information_system" in features_enabled:
        features_enabled["sis_module"] = True

    term_system = getattr(school_row, "term_system", None) or academic_config.get(
        "term_system", "three_term"
    )
    terms_per_year = {
        "three_term": 3,
        "semester": 2,
        "quarter": 4,
    }.get(term_system, 3)

    academic_year_start = getattr(school_row, "academic_year_start", None) or academic_config.get(
        "academic_year_start", "01-01"
    )
    try:
        academic_year_start_month = int(str(academic_year_start).split("-")[0])
    except (TypeError, ValueError):
        academic_year_start_month = 1

    grading_system = academic_config.get("grading_system")
    if not grading_system:
        grading_system = {
            "system": getattr(school_row, "grade_system", None) or "zimbabwe"
        }

    config = {
        "school_id": str(school_row.id),
        "logo_url": getattr(school_row, "logo_url", None) or branding_config.get("logo_url"),
        "primary_color": getattr(school_row, "primary_color", None) or branding_config.get("primary_color") or "#2563eb",
        "secondary_color": getattr(school_row, "secondary_color", None) or branding_config.get("secondary_color") or "#64748b",
        "accent_color": branding_config.get("accent_color")
        or getattr(school_row, "primary_color", None)
        or "#2563eb",
        "font_family": getattr(school_row, "font_family", None) or branding_config.get("font_family") or "ui-sans-serif",
        "motto": branding_config.get("motto"),
        "vision_statement": school_configuration.get("vision_statement"),
        "mission_statement": school_configuration.get("mission_statement"),
        "timezone": getattr(school_row, "timezone", None) or settings_config.get("timezone") or "Africa/Harare",
        "language_primary": getattr(school_row, "language", None) or settings_config.get("language") or "en",
        "language_secondary": settings_config.get("secondary_language"),
        "currency": getattr(school_row, "currency", None) or settings_config.get("currency") or "USD",
        "date_format": settings_config.get("date_format") or "DD/MM/YYYY",
        "features_enabled": features_enabled,
        "subscription_tier": school_row.subscription_tier,
        "max_students": school_configuration.get("max_students") or getattr(school_row, "student_capacity", None) or 500,
        "grading_system": grading_system,
        "notification_settings": school_configuration.get("notification_settings", {}),
        "student_id_format": school_configuration.get("student_id_format", "AUTO"),
        "academic_year_start_month": academic_year_start_month,
        "terms_per_year": terms_per_year,
    }

    return {
        "id": str(school_row.id),
        "name": school_row.name,
        "subdomain": school_row.subdomain,
        "type": getattr(school_row, "school_type", None) or "school",
        "status": school_row.status,
        "subscription_tier": school_row.subscription_tier,
        "config": config,
        "branding": {
            "logo_url": config["logo_url"],
            "primary_color": config["primary_color"],
            "secondary_color": config["secondary_color"],
            "accent_color": config["accent_color"],
            "font_family": config["font_family"],
        },
        "enabled_modules": enabled_modules,
        "features_enabled": features_enabled,
        "schoolContext": {
            "school_id": str(school_row.id),
            "school_name": school_row.name,
            "school_subdomain": school_row.subdomain,
            "subscription_tier": school_row.subscription_tier,
            "enabled_modules": enabled_modules,
        },
    }


async def generate_subdomain(school_name: str, db: AsyncSession) -> str:
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
        result = await db.execute(
            text("SELECT id FROM platform.schools WHERE subdomain = :subdomain"),
            {"subdomain": subdomain},
        )
        existing = result.first()

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
async def create_school(
    request: CreateSchoolRequest, db: AsyncSession = Depends(get_async_session)
):
    """Create a new school and admin user"""
    try:
        # Generate unique subdomain
        subdomain = await generate_subdomain(request.name, db)

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
        await db.execute(
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

        await db.execute(
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

        await db.execute(
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
        await db.commit()

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
        await db.rollback()
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
    db: AsyncSession = Depends(get_async_session),
    user_session: UserSession = Depends(get_user_session),
):
    """Get school information"""
    # Check if user is platform admin or belongs to the school
    if user_session.role != "platform_admin" and user_session.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    result = await db.execute(
        text("SELECT * FROM platform.schools WHERE id = :school_id"),
        {"school_id": school_id},
    )
    school = result.first()

    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="School not found"
        )

    return dict(school._mapping)


@platform_router.get("/schools/by-subdomain/{subdomain}")
async def get_school_by_subdomain(
    subdomain: str, db: AsyncSession = Depends(get_async_session)
):
    """Get school information by subdomain (public endpoint for middleware)"""
    result = await db.execute(
        text(
            """
            SELECT
                s.*,
                sc.enabled_modules,
                sc.primary_color,
                sc.secondary_color,
                sc.logo_url,
                sc.theme
            FROM platform.schools s
            LEFT JOIN platform.school_configurations sc ON s.id = sc.school_id
            WHERE s.subdomain = :subdomain AND s.is_active = true
        """
        ),
        {"subdomain": subdomain},
    )
    school = result.first()

    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="School not found"
        )

    return _build_school_summary_payload(school)


@platform_router.get("/schools/by-id/{school_id}")
async def get_school_by_id_public(
    school_id: str, db: AsyncSession = Depends(get_async_session)
):
    """Get school information by ID for cross-subdomain navigation."""
    result = await db.execute(
        text(
            """
            SELECT
                s.*,
                sc.enabled_modules,
                sc.primary_color,
                sc.secondary_color,
                sc.logo_url,
                sc.theme
            FROM platform.schools s
            LEFT JOIN platform.school_configurations sc ON s.id = sc.school_id
            WHERE s.id = :school_id AND s.is_active = true
        """
        ),
        {"school_id": school_id},
    )
    school = result.first()

    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="School not found"
        )

    return _build_school_summary_payload(school)


@platform_router.get("/schools/{school_id}/context")
async def get_school_context(
    school_id: str, db: AsyncSession = Depends(get_async_session)
):
    """Get the canonical school context payload used by the frontend."""
    result = await db.execute(
        text(
            """
            SELECT
                s.*,
                sc.logo_url,
                sc.primary_color,
                sc.secondary_color,
                sc.background_color,
                sc.font_family,
                sc.theme,
                sc.enabled_modules,
                sc.feature_flags,
                sc.academic_year_start,
                sc.term_system,
                sc.grade_system,
                sc.timezone,
                sc.language,
                sc.currency
            FROM platform.schools s
            LEFT JOIN platform.school_configurations sc ON s.id = sc.school_id
            WHERE s.id = :school_id AND s.is_active = true
        """
        ),
        {"school_id": school_id},
    )
    school = result.first()

    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="School not found"
        )

    return _build_school_context_payload(school)


@platform_router.get("/schools")
async def list_schools(
    db: AsyncSession = Depends(get_async_session),
    user_session: UserSession = Depends(get_user_session),
):
    """List all schools (platform admin only)"""
    if user_session.role != "platform_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admin access required",
        )

    result = await db.execute(
        text("SELECT * FROM platform.schools ORDER BY created_at DESC")
    )
    schools = result.fetchall()

    return [dict(school._mapping) for school in schools]
