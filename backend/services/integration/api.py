"""
Integration API Routes
API endpoints for cross-module integration between Academic, SIS, and Finance
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.auth import get_current_user, require_permissions
from core.exceptions import NotFoundError, ValidationError
from core.models import User
from core.pagination import PaginationParams, PaginatedResponse

from .academic_sis_integration import AcademicSISIntegration, get_academic_sis_integration
from .academic_finance_integration import AcademicFinanceIntegration, get_academic_finance_integration
from ..academic.schemas import StudentPerformance, AttendanceStats
from ..sis.schemas import StudentWithDetails

router = APIRouter(prefix="/api/v1/integration", tags=["integration"])

# =====================================================
# ACADEMIC-SIS INTEGRATION ENDPOINTS
# =====================================================

@router.get("/academic/class/{class_id}/students", response_model=List[StudentWithDetails])
async def get_class_students_for_academic(
    class_id: UUID,
    academic_year_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[StudentWithDetails]:
    """Get all students in a class for academic operations"""
    try:
        await require_permissions(current_user, ["academic.class.read", "sis.student.read"])
        
        integration = await get_academic_sis_integration(db)
        students = await integration.get_class_students_for_academic(
            class_id=class_id,
            school_id=current_user.school_id,
            academic_year_id=academic_year_id
        )
        
        return students
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.get("/academic/student/{student_id}/performance", response_model=StudentPerformance)
async def get_student_academic_performance(
    student_id: UUID,
    academic_year_id: UUID = Query(...),
    term_number: Optional[int] = Query(None, ge=1, le=3),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> StudentPerformance:
    """Get comprehensive academic performance for a student"""
    try:
        await require_permissions(current_user, ["academic.student.read", "sis.student.read"])
        
        integration = await get_academic_sis_integration(db)
        performance = await integration.get_student_academic_performance(
            student_id=student_id,
            school_id=current_user.school_id,
            academic_year_id=academic_year_id,
            term_number=term_number
        )
        
        return performance
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.get("/academic/student/{student_id}/attendance", response_model=AttendanceStats)
async def get_student_attendance_stats(
    student_id: UUID,
    academic_year_id: UUID = Query(...),
    term_number: Optional[int] = Query(None, ge=1, le=3),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AttendanceStats:
    """Get attendance statistics for a student"""
    try:
        await require_permissions(current_user, ["academic.attendance.read", "sis.student.read"])
        
        integration = await get_academic_sis_integration(db)
        stats = await integration.get_student_attendance_stats(
            student_id=student_id,
            school_id=current_user.school_id,
            academic_year_id=academic_year_id,
            term_number=term_number
        )
        
        return stats
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )


@router.get("/academic/class/{class_id}/summary")
async def get_class_academic_summary(
    class_id: UUID,
    academic_year_id: UUID = Query(...),
    term_number: Optional[int] = Query(None, ge=1, le=3),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive academic summary for a class"""
    try:
        await require_permissions(current_user, ["academic.class.read", "sis.class.read"])
        
        integration = await get_academic_sis_integration(db)
        summary = await integration.get_class_academic_summary(
            class_id=class_id,
            school_id=current_user.school_id,
            academic_year_id=academic_year_id,
            term_number=term_number
        )
        
        return summary
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.get("/academic/student/{student_id}/guardians")
async def get_student_guardians_for_notifications(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get guardian information for academic notifications"""
    try:
        await require_permissions(current_user, ["sis.guardian.read"])
        
        integration = await get_academic_sis_integration(db)
        guardians = await integration.get_student_guardians_for_notifications(
            student_id=student_id,
            school_id=current_user.school_id
        )
        
        return guardians
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )


# =====================================================
# ACADEMIC-FINANCE INTEGRATION ENDPOINTS
# =====================================================

@router.get("/finance/student/{student_id}/subject/{subject_id}/access")
async def check_student_subject_access(
    student_id: UUID,
    subject_id: UUID,
    academic_year_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Check if student has paid required fees to access subject"""
    try:
        await require_permissions(current_user, ["finance.payment.read", "academic.subject.read"])
        
        integration = await get_academic_finance_integration(db)
        access_info = await integration.check_student_subject_access(
            student_id=student_id,
            subject_id=subject_id,
            school_id=current_user.school_id,
            academic_year_id=academic_year_id
        )
        
        return access_info
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student or subject not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.get("/finance/student/{student_id}/assessment/{assessment_id}/access")
async def check_student_assessment_access(
    student_id: UUID,
    assessment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Check if student can take assessment based on payment status"""
    try:
        await require_permissions(current_user, ["finance.payment.read", "academic.assessment.read"])
        
        integration = await get_academic_finance_integration(db)
        access_info = await integration.check_student_assessment_access(
            student_id=student_id,
            assessment_id=assessment_id,
            school_id=current_user.school_id
        )
        
        return access_info
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student or assessment not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.post("/finance/student/{student_id}/subject/{subject_id}/invoice")
async def generate_subject_enrollment_invoice(
    student_id: UUID,
    subject_id: UUID,
    academic_year_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Generate invoice for subject-specific fees when student enrolls"""
    try:
        await require_permissions(current_user, ["finance.invoice.create", "academic.subject.read"])
        
        integration = await get_academic_finance_integration(db)
        invoice_info = await integration.generate_subject_enrollment_invoice(
            student_id=student_id,
            subject_id=subject_id,
            school_id=current_user.school_id,
            academic_year_id=academic_year_id,
            created_by=current_user.id
        )
        
        if not invoice_info:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="No invoices needed for this subject"
            )
        
        return invoice_info
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student or subject not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.post("/finance/resource-usage")
async def process_resource_usage_billing(
    student_id: UUID,
    resource_type: str,
    resource_id: UUID,
    usage_amount: float,
    academic_year_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Process billing for resource usage (lab materials, equipment, etc.)"""
    try:
        await require_permissions(current_user, ["finance.invoice.create"])
        
        from decimal import Decimal
        integration = await get_academic_finance_integration(db)
        billing_info = await integration.process_resource_usage_billing(
            student_id=student_id,
            resource_type=resource_type,
            resource_id=resource_id,
            usage_amount=Decimal(str(usage_amount)),
            school_id=current_user.school_id,
            academic_year_id=academic_year_id,
            created_by=current_user.id
        )
        
        if not billing_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to process resource usage billing"
            )
        
        return billing_info
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.get("/finance/academic/summary")
async def get_academic_financial_summary(
    academic_year_id: UUID = Query(...),
    term_number: Optional[int] = Query(None, ge=1, le=3),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get financial summary related to academic activities"""
    try:
        await require_permissions(current_user, ["finance.report.read", "academic.report.read"])
        
        integration = await get_academic_finance_integration(db)
        summary = await integration.get_academic_financial_summary(
            school_id=current_user.school_id,
            academic_year_id=academic_year_id,
            term_number=term_number
        )
        
        return summary
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.get("/finance/class/{class_id}/payment-restrictions")
async def get_students_with_payment_restrictions(
    class_id: UUID,
    academic_year_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get students who have academic restrictions due to unpaid fees"""
    try:
        await require_permissions(current_user, ["finance.payment.read", "academic.class.read"])
        
        integration = await get_academic_finance_integration(db)
        restricted_students = await integration.get_students_with_payment_restrictions(
            class_id=class_id,
            school_id=current_user.school_id,
            academic_year_id=academic_year_id
        )
        
        return restricted_students
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


# =====================================================
# CROSS-MODULE VALIDATION ENDPOINTS
# =====================================================

@router.get("/validate/student/{student_id}/enrollment")
async def validate_student_enrollment_for_academic(
    student_id: UUID,
    class_id: UUID = Query(...),
    subject_id: UUID = Query(...),
    academic_year_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, bool]:
    """Validate if student is properly enrolled for academic operations"""
    try:
        await require_permissions(current_user, ["sis.enrollment.read", "academic.subject.read"])
        
        integration = await get_academic_sis_integration(db)
        is_valid = await integration.validate_student_enrollment_for_academic(
            student_id=student_id,
            class_id=class_id,
            subject_id=subject_id,
            academic_year_id=academic_year_id
        )
        
        return {"is_valid": is_valid}
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.get("/validate/student/{student_id}/academic-access")
async def validate_student_academic_access(
    student_id: UUID,
    subject_id: UUID = Query(...),
    academic_year_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, bool]:
    """Quick validation for student academic access based on payment status"""
    try:
        await require_permissions(current_user, ["finance.payment.read", "academic.subject.read"])
        
        from .academic_finance_integration import validate_student_academic_access
        has_access = await validate_student_academic_access(
            db=db,
            student_id=student_id,
            subject_id=subject_id,
            school_id=current_user.school_id,
            academic_year_id=academic_year_id
        )
        
        return {"has_access": has_access}
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


# =====================================================
# BULK OPERATIONS
# =====================================================

@router.post("/sync/class/{class_id}/enrollment-academic")
async def sync_class_enrollment_with_academic(
    class_id: UUID,
    academic_year_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Sync class enrollment data with academic operations"""
    try:
        await require_permissions(current_user, ["sis.enrollment.read", "academic.class.read"])
        
        from .academic_sis_integration import sync_class_enrollment_with_academic
        sync_result = await sync_class_enrollment_with_academic(
            db=db,
            class_id=class_id,
            academic_year_id=academic_year_id,
            school_id=current_user.school_id
        )
        
        return sync_result
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


# =====================================================
# HEALTH CHECK
# =====================================================

@router.get("/health", status_code=status.HTTP_200_OK)
async def integration_health_check():
    """Health check for integration services"""
    return {
        "status": "healthy",
        "service": "integration",
        "modules": ["academic-sis", "academic-finance"],
        "timestamp": datetime.utcnow().isoformat()
    }