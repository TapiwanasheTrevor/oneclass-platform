"""
Tenant Onboarding API Routes
Handles complete school registration and onboarding workflow
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import logging

from shared.database import get_async_session
from shared.auth import get_current_active_user, verify_platform_admin_access
from shared.models.platform_user import PlatformUser
from ..tenant_onboarding_service import (
    TenantOnboardingService,
    SchoolRegistrationRequest,
    DocumentUploadRequest, 
    SchoolConfigurationUpdate,
    OnboardingProgressResponse,
    OnboardingStage,
    SubscriptionTier
)

router = APIRouter(prefix="/api/v1/platform/onboarding", tags=["tenant-onboarding"])
logger = logging.getLogger(__name__)


# =====================================================
# PUBLIC ONBOARDING ROUTES
# =====================================================

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_school(
    registration_data: SchoolRegistrationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Register a new school and initiate onboarding process
    This is a public endpoint that doesn't require authentication
    """
    try:
        service = TenantOnboardingService(db)
        
        result = await service.register_school(registration_data)
        
        # Add background task for additional processing
        background_tasks.add_task(
            _process_registration_background,
            result["school_id"],
            registration_data.principal_email
        )
        
        logger.info(f"School registration initiated: {registration_data.school_name}")
        
        return {
            "success": True,
            "message": "School registration submitted successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error registering school: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register school"
        )


@router.post("/verify-email/{school_id}")
async def verify_email(
    school_id: UUID,
    verification_token: str,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Verify principal's email address
    Public endpoint accessed via email link
    """
    try:
        service = TenantOnboardingService(db)
        
        result = await service.verify_email(school_id, verification_token)
        
        logger.info(f"Email verified for school: {school_id}")
        
        return {
            "success": True,
            "message": "Email verified successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error verifying email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email"
        )


@router.get("/progress/{school_id}", response_model=OnboardingProgressResponse)
async def get_onboarding_progress(
    school_id: UUID,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get onboarding progress for a school
    Public endpoint for tracking progress
    """
    try:
        service = TenantOnboardingService(db)
        
        progress = await service.get_onboarding_progress(school_id)
        
        return progress
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting onboarding progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get onboarding progress"
        )


# =====================================================
# DOCUMENT VERIFICATION ROUTES
# =====================================================

@router.post("/documents/{school_id}/upload")
async def upload_verification_document(
    school_id: UUID,
    document_type: str,
    file: UploadFile = File(...),
    description: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Upload verification document for school
    Requires file upload and document metadata
    """
    try:
        # Validate file type
        allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only PDF and image files are allowed."
            )
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 10MB limit"
            )
        
        # TODO: Upload file to storage service (S3, GCS, etc.)
        # For now, simulate file upload
        file_url = f"https://storage.oneclass.ac.zw/documents/{school_id}/{file.filename}"
        
        service = TenantOnboardingService(db)
        
        document_data = DocumentUploadRequest(
            document_type=document_type,
            file_url=file_url,
            file_name=file.filename,
            file_size=len(file_content),
            mime_type=file.content_type,
            description=description
        )
        
        result = await service.upload_verification_document(school_id, document_data)
        
        logger.info(f"Document uploaded for school {school_id}: {document_type}")
        
        return {
            "success": True,
            "message": "Document uploaded successfully",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )


# =====================================================
# SUBSCRIPTION SETUP ROUTES
# =====================================================

@router.post("/subscription/{school_id}/setup")
async def setup_subscription(
    school_id: UUID,
    setup_token: str,
    subscription_tier: SubscriptionTier,
    payment_method: Dict[str, Any],
    db: AsyncSession = Depends(get_async_session)
):
    """
    Set up subscription and payment method
    Requires valid setup token from email
    """
    try:
        service = TenantOnboardingService(db)
        
        result = await service.setup_subscription(
            school_id, setup_token, subscription_tier, payment_method
        )
        
        logger.info(f"Subscription configured for school {school_id}: {subscription_tier.value}")
        
        return {
            "success": True,
            "message": "Subscription configured successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error setting up subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set up subscription"
        )


# =====================================================
# ADMIN SETUP ROUTES  
# =====================================================

@router.post("/admin/{school_id}/setup")
async def setup_principal_account(
    school_id: UUID,
    setup_token: str,
    principal_password: str,
    additional_info: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Set up principal user account
    Requires valid setup token from email
    """
    try:
        # Validate password strength
        if len(principal_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )
        
        service = TenantOnboardingService(db)
        
        result = await service.setup_principal_account(
            school_id, setup_token, principal_password, additional_info
        )
        
        logger.info(f"Principal account created for school {school_id}")
        
        return {
            "success": True,
            "message": "Principal account created successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error setting up principal account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set up principal account"
        )


# =====================================================
# CONFIGURATION ROUTES
# =====================================================

@router.post("/modules/{school_id}/configure")
async def configure_school_modules(
    school_id: UUID,
    module_configuration: Dict[str, Any],
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Configure school modules and settings
    Requires authenticated user with school access
    """
    try:
        # Verify user has access to this school
        if not await _verify_school_access(db, current_user.id, school_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to configure this school"
            )
        
        service = TenantOnboardingService(db)
        
        result = await service.configure_school_modules(school_id, module_configuration)
        
        logger.info(f"Modules configured for school {school_id}")
        
        return {
            "success": True,
            "message": "Modules configured successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error configuring modules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to configure modules"
        )


@router.put("/configuration/{school_id}")
async def update_school_configuration(
    school_id: UUID,
    config_data: SchoolConfigurationUpdate,
    current_user: PlatformUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Update school configuration and branding
    Requires authenticated user with school access
    """
    try:
        # Verify user has access to this school
        if not await _verify_school_access(db, current_user.id, school_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to configure this school"
            )
        
        service = TenantOnboardingService(db)
        
        result = await service.update_school_configuration(school_id, config_data)
        
        logger.info(f"Configuration updated for school {school_id}")
        
        return {
            "success": True,
            "message": "School configuration updated successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update configuration"
        )


# =====================================================
# ADMIN REVIEW ROUTES
# =====================================================

@router.post("/review/{school_id}/documents")
async def review_documents(
    school_id: UUID,
    review_decision: str,
    review_notes: Optional[str] = None,
    current_user: PlatformUser = Depends(verify_platform_admin_access),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Review submitted documents (platform admin only)
    """
    try:
        if review_decision not in ["approved", "rejected", "additional_info_required"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid review decision"
            )
        
        service = TenantOnboardingService(db)
        
        result = await service.review_documents(
            school_id, current_user.id, review_decision, review_notes
        )
        
        logger.info(f"Documents reviewed for school {school_id}: {review_decision}")
        
        return {
            "success": True,
            "message": f"Documents {review_decision} successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error reviewing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to review documents"
        )


@router.post("/complete/{school_id}")
async def complete_onboarding(
    school_id: UUID,
    approval_notes: Optional[str] = None,
    current_user: PlatformUser = Depends(verify_platform_admin_access),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Complete school onboarding process (platform admin only)
    """
    try:
        service = TenantOnboardingService(db)
        
        result = await service.complete_onboarding(
            school_id, current_user.id, approval_notes
        )
        
        logger.info(f"Onboarding completed for school {school_id}")
        
        return {
            "success": True,
            "message": "School onboarding completed successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error completing onboarding: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete onboarding"
        )


# =====================================================
# ADMIN MANAGEMENT ROUTES
# =====================================================

@router.get("/admin/pending")
async def get_pending_onboardings(
    stage: Optional[OnboardingStage] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: PlatformUser = Depends(verify_platform_admin_access),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get list of schools pending onboarding review (platform admin only)
    """
    try:
        # Build query for schools in onboarding
        query = """
            SELECT 
                s.id,
                s.name,
                s.subdomain,
                s.status,
                s.onboarding_data->>'stage' as stage,
                s.created_at,
                s.onboarding_data->'principal_info'->>'email' as principal_email
            FROM platform.schools s
            WHERE s.status != 'active'
        """
        
        params = {}
        
        if stage:
            query += " AND s.onboarding_data->>'stage' = :stage"
            params["stage"] = stage.value
        
        query += " ORDER BY s.created_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset
        
        result = await db.execute(query, params)
        schools = result.fetchall()
        
        # Get total count
        count_query = """
            SELECT COUNT(*) 
            FROM platform.schools s
            WHERE s.status != 'active'
        """
        
        if stage:
            count_query += " AND s.onboarding_data->>'stage' = :stage"
        
        count_result = await db.execute(count_query, params)
        total = count_result.scalar()
        
        school_list = []
        for school in schools:
            school_list.append({
                "id": str(school.id),
                "name": school.name,
                "subdomain": school.subdomain,
                "status": school.status,
                "stage": school.stage,
                "principal_email": school.principal_email,
                "created_at": school.created_at.isoformat()
            })
        
        return {
            "schools": school_list,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error getting pending onboardings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pending onboardings"
        )


@router.get("/admin/stats")
async def get_onboarding_stats(
    current_user: PlatformUser = Depends(verify_platform_admin_access),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get onboarding statistics (platform admin only)
    """
    try:
        stats_query = """
            SELECT 
                s.onboarding_data->>'stage' as stage,
                COUNT(*) as count
            FROM platform.schools s
            WHERE s.status != 'active'
            GROUP BY s.onboarding_data->>'stage'
        """
        
        result = await db.execute(stats_query)
        stage_stats = {row.stage: row.count for row in result}
        
        # Get total counts
        total_query = """
            SELECT 
                COUNT(*) FILTER (WHERE status = 'active') as active_schools,
                COUNT(*) FILTER (WHERE status != 'active') as pending_schools,
                COUNT(*) as total_schools
            FROM platform.schools
        """
        
        total_result = await db.execute(total_query)
        totals = total_result.fetchone()
        
        return {
            "stage_breakdown": stage_stats,
            "totals": {
                "active_schools": totals.active_schools,
                "pending_schools": totals.pending_schools,
                "total_schools": totals.total_schools
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting onboarding stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get onboarding statistics"
        )


# =====================================================
# UTILITY FUNCTIONS
# =====================================================

async def _verify_school_access(db: AsyncSession, user_id: UUID, school_id: UUID) -> bool:
    """Verify user has access to school"""
    # Check if user is platform admin
    user_query = select(PlatformUser).where(PlatformUser.id == user_id)
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    if user and user.platform_role in ["platform_admin", "super_admin"]:
        return True
    
    # Check if user has school membership
    membership_query = """
        SELECT COUNT(*) 
        FROM platform.school_memberships 
        WHERE user_id = :user_id AND school_id = :school_id AND status = 'active'
    """
    
    result = await db.execute(membership_query, {"user_id": user_id, "school_id": school_id})
    count = result.scalar()
    
    return count > 0


async def _process_registration_background(school_id: str, principal_email: str):
    """Background task to process registration"""
    # TODO: Additional processing like:
    # - Send welcome email
    # - Create audit log entry
    # - Notify administrators
    # - Set up monitoring
    logger.info(f"Background processing completed for school {school_id}")


# =====================================================
# HEALTH CHECK
# =====================================================

@router.get("/health")
async def health_check():
    """Health check for onboarding service"""
    return {
        "status": "healthy",
        "service": "tenant-onboarding",
        "timestamp": datetime.utcnow().isoformat()
    }