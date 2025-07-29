"""
Domain Management API Routes
FastAPI routes for domain management
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db_session
from shared.auth import get_current_user, require_permissions
from shared.models.platform import 
from shared.models.platform_user import PlatformUserDB as User
from shared.exceptions import (
    ValidationError,
    NotFoundError,
    ConflictError,
    ExternalServiceError
)
from .service import DomainManagementService
from .schemas import (
    DomainCreate,
    DomainUpdate,
    DomainResponse,
    EmailAddressCreate,
    EmailAddressUpdate,
    EmailAddressResponse,
    SSLCertificateCreate,
    SSLCertificateResponse,
    DomainVerificationCreate,
    DomainVerificationResponse,
    DomainValidationRequest,
    DomainValidationResponse,
    DomainStatsResponse,
    BulkEmailCreateRequest,
    BulkEmailCreateResponse
)

router = APIRouter(prefix="/domains", tags=["Domain Management"])


@router.post("/", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
async def create_domain(
    domain_data: DomainCreate,
    current_user: User = Depends(get_current_user),
    service: DomainManagementService = Depends()
):
    """Create a new domain for a school"""
    try:
        # Check if user has permission to create domains for this school
        await require_permissions(current_user, "domain:create", domain_data.school_id)
        
        return await service.create_domain(domain_data, str(current_user.id))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{domain_id}", response_model=DomainResponse)
async def get_domain(
    domain_id: str,
    current_user: User = Depends(get_current_user),
    service: DomainManagementService = Depends()
):
    """Get domain by ID"""
    try:
        domain = await service.get_domain(domain_id)
        
        # Check if user has permission to view this domain
        await require_permissions(current_user, "domain:read", domain.school_id)
        
        return domain
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/subdomain/{subdomain}", response_model=DomainResponse)
async def get_domain_by_subdomain(
    subdomain: str,
    current_user: User = Depends(get_current_user),
    service: DomainManagementService = Depends()
):
    """Get domain by subdomain"""
    try:
        domain = await service.get_domain_by_subdomain(subdomain)
        
        # Check if user has permission to view this domain
        await require_permissions(current_user, "domain:read", domain.school_id)
        
        return domain
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/school/{school_id}", response_model=DomainResponse)
async def get_school_domain(
    school_id: str,
    current_user: User = Depends(get_current_user),
    service: DomainManagementService = Depends()
):
    """Get domain for a school"""
    try:
        # Check if user has permission to view this school's domain
        await require_permissions(current_user, "domain:read", school_id)
        
        return await service.get_school_domain(school_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{domain_id}", response_model=DomainResponse)
async def update_domain(
    domain_id: str,
    domain_data: DomainUpdate,
    current_user: User = Depends(get_current_user),
    service: DomainManagementService = Depends()
):
    """Update domain"""
    try:
        # Get domain to check permissions
        domain = await service.get_domain(domain_id)
        await require_permissions(current_user, "domain:update", domain.school_id)
        
        return await service.update_domain(domain_id, domain_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_domain(
    domain_id: str,
    current_user: User = Depends(get_current_user),
    service: DomainManagementService = Depends()
):
    """Delete domain"""
    try:
        # Get domain to check permissions
        domain = await service.get_domain(domain_id)
        await require_permissions(current_user, "domain:delete", domain.school_id)
        
        await service.delete_domain(domain_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/validate", response_model=DomainValidationResponse)
async def validate_domain(
    validation_data: DomainValidationRequest,
    current_user: User = Depends(get_current_user),
    service: DomainManagementService = Depends()
):
    """Validate domain availability and format"""
    try:
        return await service.validate_domain(
            validation_data.subdomain,
            validation_data.custom_domain
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{domain_id}/verify", response_model=dict)
async def verify_domain(
    domain_id: str,
    current_user: User = Depends(get_current_user),
    service: DomainManagementService = Depends()
):
    """Verify domain ownership"""
    try:
        # Get domain to check permissions
        domain = await service.get_domain(domain_id)
        await require_permissions(current_user, "domain:verify", domain.school_id)
        
        verified = await service.verify_domain(domain_id)
        
        return {
            "verified": verified,
            "message": "Domain verified successfully" if verified else "Domain verification failed"
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{domain_id}/stats", response_model=DomainStatsResponse)
async def get_domain_stats(
    domain_id: str,
    current_user: User = Depends(get_current_user),
    service: DomainManagementService = Depends()
):
    """Get domain statistics"""
    try:
        # Get domain to check permissions
        domain = await service.get_domain(domain_id)
        await require_permissions(current_user, "domain:read", domain.school_id)
        
        return await service.get_domain_stats(domain_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Email Address Management Routes

@router.post("/{domain_id}/emails", response_model=EmailAddressResponse, status_code=status.HTTP_201_CREATED)
async def create_email_address(
    domain_id: str,
    email_data: EmailAddressCreate,
    current_user: User = Depends(get_current_user),
    service: DomainManagementService = Depends()
):
    """Create email address for domain"""
    try:
        # Get domain to check permissions
        domain = await service.get_domain(domain_id)
        await require_permissions(current_user, "email:create", domain.school_id)
        
        # Set domain_id
        email_data.domain_id = domain_id
        
        return await service.create_email_address(email_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{domain_id}/emails", response_model=List[EmailAddressResponse])
async def get_domain_emails(
    domain_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    service: DomainManagementService = Depends()
):
    """Get email addresses for domain"""
    try:
        # Get domain to check permissions
        domain = await service.get_domain(domain_id)
        await require_permissions(current_user, "email:read", domain.school_id)
        
        return await service.get_domain_emails(domain_id, skip, limit)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/emails/{email_id}", response_model=EmailAddressResponse)
async def update_email_address(
    email_id: str,
    email_data: EmailAddressUpdate,
    current_user: User = Depends(get_current_user),
    service: DomainManagementService = Depends()
):
    """Update email address"""
    try:
        # This would need implementation in service
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/emails/{email_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_email_address(
    email_id: str,
    current_user: User = Depends(get_current_user),
    service: DomainManagementService = Depends()
):
    """Delete email address"""
    try:
        # This would need implementation in service
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{domain_id}/emails/bulk", response_model=BulkEmailCreateResponse)
async def bulk_create_email_addresses(
    domain_id: str,
    bulk_request: BulkEmailCreateRequest,
    current_user: User = Depends(get_current_user),
    service: DomainManagementService = Depends()
):
    """Bulk create email addresses"""
    try:
        # Get domain to check permissions
        domain = await service.get_domain(domain_id)
        await require_permissions(current_user, "email:create", domain.school_id)
        
        # This would need implementation in service
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# SSL Certificate Management Routes

@router.get("/{domain_id}/ssl", response_model=List[SSLCertificateResponse])
async def get_domain_ssl_certificates(
    domain_id: str,
    current_user: User = Depends(get_current_user),
    service: DomainManagementService = Depends()
):
    """Get SSL certificates for domain"""
    try:
        # Get domain to check permissions
        domain = await service.get_domain(domain_id)
        await require_permissions(current_user, "ssl:read", domain.school_id)
        
        # This would need implementation in service
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{domain_id}/ssl", response_model=SSLCertificateResponse, status_code=status.HTTP_201_CREATED)
async def create_ssl_certificate(
    domain_id: str,
    ssl_data: SSLCertificateCreate,
    current_user: User = Depends(get_current_user),
    service: DomainManagementService = Depends()
):
    """Create SSL certificate for domain"""
    try:
        # Get domain to check permissions
        domain = await service.get_domain(domain_id)
        await require_permissions(current_user, "ssl:create", domain.school_id)
        
        # This would need implementation in service
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{domain_id}/ssl/renew", response_model=dict)
async def renew_ssl_certificate(
    domain_id: str,
    current_user: User = Depends(get_current_user),
    service: DomainManagementService = Depends()
):
    """Renew SSL certificate for domain"""
    try:
        # Get domain to check permissions
        domain = await service.get_domain(domain_id)
        await require_permissions(current_user, "ssl:renew", domain.school_id)
        
        # This would need implementation in service
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Domain Verification Routes

@router.get("/{domain_id}/verification", response_model=List[DomainVerificationResponse])
async def get_domain_verifications(
    domain_id: str,
    current_user: User = Depends(get_current_user),
    service: DomainManagementService = Depends()
):
    """Get domain verification records"""
    try:
        # Get domain to check permissions
        domain = await service.get_domain(domain_id)
        await require_permissions(current_user, "domain:read", domain.school_id)
        
        # This would need implementation in service
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{domain_id}/verification", response_model=DomainVerificationResponse, status_code=status.HTTP_201_CREATED)
async def create_domain_verification(
    domain_id: str,
    verification_data: DomainVerificationCreate,
    current_user: User = Depends(get_current_user),
    service: DomainManagementService = Depends()
):
    """Create domain verification record"""
    try:
        # Get domain to check permissions
        domain = await service.get_domain(domain_id)
        await require_permissions(current_user, "domain:verify", domain.school_id)
        
        # This would need implementation in service
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))