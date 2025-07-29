"""
Academic-Finance Integration Service
Integration layer between Academic Management and Finance & Billing
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import selectinload, joinedload
from decimal import Decimal
import logging

from ..academic.models import Subject, Assessment, AttendanceSession
from ..finance.models import FeeCategory, Invoice, Payment, StudentAccount
from ..finance.schemas import PaymentStatus, InvoiceStatus
from core.exceptions import NotFoundError, ValidationError, InsufficientFundsError

logger = logging.getLogger(__name__)

class AcademicFinanceIntegration:
    """Integration service for Academic Management and Finance"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =====================================================
    # FEE-BASED ACCESS CONTROL
    # =====================================================
    
    async def check_student_subject_access(
        self,
        student_id: UUID,
        subject_id: UUID,
        school_id: UUID,
        academic_year_id: UUID
    ) -> Dict[str, Any]:
        """Check if student has paid required fees to access subject"""
        try:
            # Get subject details
            subject_query = select(Subject).where(
                and_(
                    Subject.id == subject_id,
                    Subject.school_id == school_id,
                    Subject.is_active == True
                )
            )
            subject_result = await self.db.execute(subject_query)
            subject = subject_result.scalar_one_or_none()
            
            if not subject:
                raise NotFoundError("Subject not found")
            
            # Get student account
            account_query = select(StudentAccount).where(
                and_(
                    StudentAccount.student_id == student_id,
                    StudentAccount.school_id == school_id,
                    StudentAccount.academic_year_id == academic_year_id
                )
            )
            account_result = await self.db.execute(account_query)
            account = account_result.scalar_one_or_none()
            
            if not account:
                return {
                    'has_access': False,
                    'reason': 'No student account found',
                    'outstanding_balance': 0,
                    'required_fees': []
                }
            
            # Check for subject-specific fees
            subject_fees_query = select(FeeCategory).where(
                and_(
                    FeeCategory.school_id == school_id,
                    FeeCategory.academic_year_id == academic_year_id,
                    FeeCategory.is_active == True,
                    or_(
                        FeeCategory.name.ilike(f'%{subject.name}%'),
                        FeeCategory.description.ilike(f'%{subject.name}%'),
                        and_(
                            subject.is_practical == True,
                            or_(
                                FeeCategory.name.ilike('%practical%'),
                                FeeCategory.name.ilike('%lab%')
                            )
                        )
                    )
                )
            )
            subject_fees_result = await self.db.execute(subject_fees_query)
            subject_fees = subject_fees_result.scalars().all()
            
            # Check payment status for subject-specific fees
            outstanding_fees = []
            total_outstanding = Decimal('0.00')
            
            for fee in subject_fees:
                # Check if there's an unpaid invoice for this fee
                invoice_query = select(Invoice).where(
                    and_(
                        Invoice.student_id == student_id,
                        Invoice.school_id == school_id,
                        Invoice.fee_category_id == fee.id,
                        Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.OVERDUE]),
                        Invoice.is_active == True
                    )
                )
                invoice_result = await self.db.execute(invoice_query)
                unpaid_invoice = invoice_result.scalar_one_or_none()
                
                if unpaid_invoice:
                    outstanding_fees.append({
                        'fee_category_id': str(fee.id),
                        'fee_name': fee.name,
                        'amount': float(unpaid_invoice.amount),
                        'due_date': unpaid_invoice.due_date.isoformat() if unpaid_invoice.due_date else None,
                        'invoice_id': str(unpaid_invoice.id)
                    })
                    total_outstanding += unpaid_invoice.amount
            
            # Check general tuition status
            tuition_query = select(Invoice).where(
                and_(
                    Invoice.student_id == student_id,
                    Invoice.school_id == school_id,
                    Invoice.academic_year_id == academic_year_id,
                    Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.OVERDUE]),
                    Invoice.is_active == True
                )
            ).join(FeeCategory).where(
                FeeCategory.name.ilike('%tuition%')
            )
            tuition_result = await self.db.execute(tuition_query)
            tuition_invoices = tuition_result.scalars().all()
            
            # Add tuition fees to outstanding
            for invoice in tuition_invoices:
                if invoice.fee_category_id not in [fee['fee_category_id'] for fee in outstanding_fees]:
                    fee_category_query = select(FeeCategory).where(FeeCategory.id == invoice.fee_category_id)
                    fee_category_result = await self.db.execute(fee_category_query)
                    fee_category = fee_category_result.scalar_one_or_none()
                    
                    outstanding_fees.append({
                        'fee_category_id': str(invoice.fee_category_id),
                        'fee_name': fee_category.name if fee_category else 'Tuition',
                        'amount': float(invoice.amount),
                        'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
                        'invoice_id': str(invoice.id)
                    })
                    total_outstanding += invoice.amount
            
            # Determine access based on school policy
            # For now, we'll allow access if no subject-specific fees are outstanding
            subject_specific_outstanding = [fee for fee in outstanding_fees if fee['fee_category_id'] in [str(f.id) for f in subject_fees]]
            has_access = len(subject_specific_outstanding) == 0
            
            # If subject requires lab/practical and there are outstanding lab fees, deny access
            if subject.requires_lab or subject.is_practical:
                lab_fees_outstanding = any(
                    'lab' in fee['fee_name'].lower() or 'practical' in fee['fee_name'].lower()
                    for fee in outstanding_fees
                )
                if lab_fees_outstanding:
                    has_access = False
            
            return {
                'has_access': has_access,
                'reason': 'Outstanding subject-specific fees' if not has_access and subject_specific_outstanding else '',
                'outstanding_balance': float(total_outstanding),
                'required_fees': outstanding_fees,
                'subject_fees': [
                    {
                        'fee_category_id': str(fee.id),
                        'fee_name': fee.name,
                        'amount': float(fee.amount),
                        'description': fee.description
                    }
                    for fee in subject_fees
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to check student subject access: {str(e)}")
            return {
                'has_access': False,
                'reason': 'Error checking access',
                'outstanding_balance': 0,
                'required_fees': []
            }
    
    async def check_student_assessment_access(
        self,
        student_id: UUID,
        assessment_id: UUID,
        school_id: UUID
    ) -> Dict[str, Any]:
        """Check if student can take assessment based on payment status"""
        try:
            # Get assessment details
            assessment_query = select(Assessment).where(
                and_(
                    Assessment.id == assessment_id,
                    Assessment.school_id == school_id,
                    Assessment.is_active == True
                )
            ).options(selectinload(Assessment.subject))
            
            assessment_result = await self.db.execute(assessment_query)
            assessment = assessment_result.scalar_one_or_none()
            
            if not assessment:
                raise NotFoundError("Assessment not found")
            
            # Check subject access
            subject_access = await self.check_student_subject_access(
                student_id, assessment.subject_id, school_id, assessment.academic_year_id
            )
            
            # Additional check for examination fees
            exam_fees_query = select(FeeCategory).where(
                and_(
                    FeeCategory.school_id == school_id,
                    FeeCategory.academic_year_id == assessment.academic_year_id,
                    FeeCategory.is_active == True,
                    or_(
                        FeeCategory.name.ilike('%exam%'),
                        FeeCategory.name.ilike('%assessment%'),
                        and_(
                            assessment.assessment_type == 'exam',
                            FeeCategory.name.ilike('%examination%')
                        )
                    )
                )
            )
            exam_fees_result = await self.db.execute(exam_fees_query)
            exam_fees = exam_fees_result.scalars().all()
            
            # Check for unpaid exam fees
            exam_fees_outstanding = []
            for fee in exam_fees:
                invoice_query = select(Invoice).where(
                    and_(
                        Invoice.student_id == student_id,
                        Invoice.school_id == school_id,
                        Invoice.fee_category_id == fee.id,
                        Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.OVERDUE]),
                        Invoice.is_active == True
                    )
                )
                invoice_result = await self.db.execute(invoice_query)
                unpaid_invoice = invoice_result.scalar_one_or_none()
                
                if unpaid_invoice:
                    exam_fees_outstanding.append({
                        'fee_category_id': str(fee.id),
                        'fee_name': fee.name,
                        'amount': float(unpaid_invoice.amount),
                        'invoice_id': str(unpaid_invoice.id)
                    })
            
            # Determine access
            has_access = subject_access['has_access'] and len(exam_fees_outstanding) == 0
            
            return {
                'has_access': has_access,
                'assessment_name': assessment.name,
                'subject_name': assessment.subject.name if assessment.subject else '',
                'subject_access': subject_access,
                'exam_fees_outstanding': exam_fees_outstanding,
                'total_outstanding': subject_access['outstanding_balance'] + sum(fee['amount'] for fee in exam_fees_outstanding)
            }
            
        except Exception as e:
            logger.error(f"Failed to check student assessment access: {str(e)}")
            return {
                'has_access': False,
                'reason': 'Error checking assessment access'
            }
    
    # =====================================================
    # AUTOMATIC BILLING INTEGRATION
    # =====================================================
    
    async def generate_subject_enrollment_invoice(
        self,
        student_id: UUID,
        subject_id: UUID,
        school_id: UUID,
        academic_year_id: UUID,
        created_by: UUID
    ) -> Optional[Dict[str, Any]]:
        """Generate invoice for subject-specific fees when student enrolls"""
        try:
            # Get subject details
            subject_query = select(Subject).where(
                and_(
                    Subject.id == subject_id,
                    Subject.school_id == school_id,
                    Subject.is_active == True
                )
            )
            subject_result = await self.db.execute(subject_query)
            subject = subject_result.scalar_one_or_none()
            
            if not subject:
                return None
            
            # Find relevant fee categories
            fee_categories = []
            
            # Subject-specific fees
            subject_fees_query = select(FeeCategory).where(
                and_(
                    FeeCategory.school_id == school_id,
                    FeeCategory.academic_year_id == academic_year_id,
                    FeeCategory.is_active == True,
                    or_(
                        FeeCategory.name.ilike(f'%{subject.name}%'),
                        FeeCategory.description.ilike(f'%{subject.name}%')
                    )
                )
            )
            subject_fees_result = await self.db.execute(subject_fees_query)
            fee_categories.extend(subject_fees_result.scalars().all())
            
            # Lab/Practical fees if applicable
            if subject.requires_lab or subject.is_practical:
                lab_fees_query = select(FeeCategory).where(
                    and_(
                        FeeCategory.school_id == school_id,
                        FeeCategory.academic_year_id == academic_year_id,
                        FeeCategory.is_active == True,
                        or_(
                            FeeCategory.name.ilike('%lab%'),
                            FeeCategory.name.ilike('%practical%')
                        )
                    )
                )
                lab_fees_result = await self.db.execute(lab_fees_query)
                fee_categories.extend(lab_fees_result.scalars().all())
            
            if not fee_categories:
                return None
            
            # Create invoices for each fee category
            invoices_created = []
            for fee_category in fee_categories:
                # Check if invoice already exists
                existing_invoice_query = select(Invoice).where(
                    and_(
                        Invoice.student_id == student_id,
                        Invoice.school_id == school_id,
                        Invoice.fee_category_id == fee_category.id,
                        Invoice.academic_year_id == academic_year_id,
                        Invoice.is_active == True
                    )
                )
                existing_result = await self.db.execute(existing_invoice_query)
                if existing_result.scalar_one_or_none():
                    continue  # Invoice already exists
                
                # Create new invoice
                invoice = Invoice(
                    student_id=student_id,
                    school_id=school_id,
                    academic_year_id=academic_year_id,
                    fee_category_id=fee_category.id,
                    amount=fee_category.amount,
                    due_date=datetime.utcnow().date(),  # Due immediately
                    description=f"{fee_category.name} for {subject.name}",
                    status=InvoiceStatus.PENDING,
                    created_by=created_by,
                    updated_by=created_by
                )
                
                self.db.add(invoice)
                await self.db.flush()  # Get the ID
                
                invoices_created.append({
                    'invoice_id': str(invoice.id),
                    'fee_category_name': fee_category.name,
                    'amount': float(fee_category.amount),
                    'due_date': invoice.due_date.isoformat(),
                    'description': invoice.description
                })
            
            await self.db.commit()
            
            return {
                'student_id': str(student_id),
                'subject_id': str(subject_id),
                'subject_name': subject.name,
                'invoices_created': invoices_created,
                'total_amount': sum(inv['amount'] for inv in invoices_created)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate subject enrollment invoice: {str(e)}")
            await self.db.rollback()
            return None
    
    async def process_resource_usage_billing(
        self,
        student_id: UUID,
        resource_type: str,
        resource_id: UUID,
        usage_amount: Decimal,
        school_id: UUID,
        academic_year_id: UUID,
        created_by: UUID
    ) -> Optional[Dict[str, Any]]:
        """Process billing for resource usage (lab materials, equipment, etc.)"""
        try:
            # Find resource-based fee category
            resource_fee_query = select(FeeCategory).where(
                and_(
                    FeeCategory.school_id == school_id,
                    FeeCategory.academic_year_id == academic_year_id,
                    FeeCategory.is_active == True,
                    or_(
                        FeeCategory.name.ilike(f'%{resource_type}%'),
                        FeeCategory.description.ilike(f'%{resource_type}%')
                    )
                )
            )
            resource_fee_result = await self.db.execute(resource_fee_query)
            resource_fee = resource_fee_result.scalar_one_or_none()
            
            if not resource_fee:
                # Create default resource fee category
                resource_fee = FeeCategory(
                    school_id=school_id,
                    academic_year_id=academic_year_id,
                    name=f"{resource_type.title()} Usage",
                    description=f"Usage-based billing for {resource_type}",
                    amount=Decimal('1.00'),  # Per unit cost
                    fee_type='variable',
                    is_mandatory=False,
                    created_by=created_by,
                    updated_by=created_by
                )
                self.db.add(resource_fee)
                await self.db.flush()
            
            # Calculate total cost
            total_cost = resource_fee.amount * usage_amount
            
            # Create invoice
            invoice = Invoice(
                student_id=student_id,
                school_id=school_id,
                academic_year_id=academic_year_id,
                fee_category_id=resource_fee.id,
                amount=total_cost,
                due_date=datetime.utcnow().date(),
                description=f"{resource_type.title()} usage: {usage_amount} units",
                status=InvoiceStatus.PENDING,
                metadata={
                    'resource_type': resource_type,
                    'resource_id': str(resource_id),
                    'usage_amount': float(usage_amount),
                    'unit_cost': float(resource_fee.amount)
                },
                created_by=created_by,
                updated_by=created_by
            )
            
            self.db.add(invoice)
            await self.db.commit()
            
            return {
                'invoice_id': str(invoice.id),
                'resource_type': resource_type,
                'usage_amount': float(usage_amount),
                'unit_cost': float(resource_fee.amount),
                'total_cost': float(total_cost),
                'due_date': invoice.due_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to process resource usage billing: {str(e)}")
            await self.db.rollback()
            return None
    
    # =====================================================
    # FINANCIAL REPORTING INTEGRATION
    # =====================================================
    
    async def get_academic_financial_summary(
        self,
        school_id: UUID,
        academic_year_id: UUID,
        term_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get financial summary related to academic activities"""
        try:
            # Get academic-related fee categories
            academic_fees_query = select(FeeCategory).where(
                and_(
                    FeeCategory.school_id == school_id,
                    FeeCategory.academic_year_id == academic_year_id,
                    FeeCategory.is_active == True,
                    or_(
                        FeeCategory.name.ilike('%tuition%'),
                        FeeCategory.name.ilike('%exam%'),
                        FeeCategory.name.ilike('%lab%'),
                        FeeCategory.name.ilike('%practical%'),
                        FeeCategory.name.ilike('%resource%')
                    )
                )
            )
            academic_fees_result = await self.db.execute(academic_fees_query)
            academic_fees = academic_fees_result.scalars().all()
            
            fee_category_ids = [fee.id for fee in academic_fees]
            
            # Get invoices for academic fees
            invoices_query = select(
                func.count(Invoice.id).label('total_invoices'),
                func.sum(Invoice.amount).label('total_invoiced'),
                func.sum(func.case([(Invoice.status == InvoiceStatus.PAID, Invoice.amount)], else_=0)).label('total_paid'),
                func.sum(func.case([(Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.OVERDUE]), Invoice.amount)], else_=0)).label('total_outstanding')
            ).where(
                and_(
                    Invoice.school_id == school_id,
                    Invoice.academic_year_id == academic_year_id,
                    Invoice.fee_category_id.in_(fee_category_ids),
                    Invoice.is_active == True
                )
            )
            invoices_result = await self.db.execute(invoices_query)
            invoices_stats = invoices_result.first()
            
            # Get payments for academic fees
            payments_query = select(
                func.count(Payment.id).label('total_payments'),
                func.sum(Payment.amount).label('total_payment_amount')
            ).select_from(
                Payment.join(Invoice)
            ).where(
                and_(
                    Invoice.school_id == school_id,
                    Invoice.academic_year_id == academic_year_id,
                    Invoice.fee_category_id.in_(fee_category_ids),
                    Payment.status == PaymentStatus.COMPLETED
                )
            )
            payments_result = await self.db.execute(payments_query)
            payments_stats = payments_result.first()
            
            # Breakdown by fee category
            fee_breakdown = []
            for fee in academic_fees:
                fee_invoices_query = select(
                    func.count(Invoice.id).label('count'),
                    func.sum(Invoice.amount).label('total'),
                    func.sum(func.case([(Invoice.status == InvoiceStatus.PAID, Invoice.amount)], else_=0)).label('paid')
                ).where(
                    and_(
                        Invoice.school_id == school_id,
                        Invoice.fee_category_id == fee.id,
                        Invoice.is_active == True
                    )
                )
                fee_result = await self.db.execute(fee_invoices_query)
                fee_stats = fee_result.first()
                
                fee_breakdown.append({
                    'fee_category_id': str(fee.id),
                    'fee_name': fee.name,
                    'fee_type': fee.fee_type,
                    'total_invoices': fee_stats.count or 0,
                    'total_amount': float(fee_stats.total or 0),
                    'paid_amount': float(fee_stats.paid or 0),
                    'outstanding_amount': float((fee_stats.total or 0) - (fee_stats.paid or 0))
                })
            
            return {
                'school_id': str(school_id),
                'academic_year_id': str(academic_year_id),
                'term_number': term_number,
                'summary': {
                    'total_invoices': invoices_stats.total_invoices or 0,
                    'total_invoiced': float(invoices_stats.total_invoiced or 0),
                    'total_paid': float(invoices_stats.total_paid or 0),
                    'total_outstanding': float(invoices_stats.total_outstanding or 0),
                    'collection_rate': float((invoices_stats.total_paid or 0) / (invoices_stats.total_invoiced or 1) * 100),
                    'total_payments': payments_stats.total_payments or 0,
                    'total_payment_amount': float(payments_stats.total_payment_amount or 0)
                },
                'fee_breakdown': fee_breakdown,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get academic financial summary: {str(e)}")
            return {
                'summary': {
                    'total_invoices': 0,
                    'total_invoiced': 0,
                    'total_paid': 0,
                    'total_outstanding': 0,
                    'collection_rate': 0
                },
                'fee_breakdown': []
            }
    
    # =====================================================
    # PAYMENT STATUS INTEGRATION
    # =====================================================
    
    async def get_students_with_payment_restrictions(
        self,
        class_id: UUID,
        school_id: UUID,
        academic_year_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get students who have academic restrictions due to unpaid fees"""
        try:
            # Get students with outstanding invoices
            students_query = select(
                Invoice.student_id,
                func.sum(Invoice.amount).label('total_outstanding'),
                func.count(Invoice.id).label('outstanding_invoices')
            ).select_from(
                Invoice.join(StudentAccount, StudentAccount.student_id == Invoice.student_id)
            ).where(
                and_(
                    Invoice.school_id == school_id,
                    Invoice.academic_year_id == academic_year_id,
                    Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.OVERDUE]),
                    Invoice.is_active == True,
                    StudentAccount.class_id == class_id
                )
            ).group_by(Invoice.student_id)
            
            students_result = await self.db.execute(students_query)
            students_data = students_result.all()
            
            restricted_students = []
            for student_data in students_data:
                # Check if restrictions apply (e.g., outstanding amount > threshold)
                if student_data.total_outstanding > Decimal('100.00'):  # Configurable threshold
                    
                    # Get specific restriction details
                    restrictions = []
                    
                    # Check for exam fee restrictions
                    exam_fees_query = select(Invoice).join(FeeCategory).where(
                        and_(
                            Invoice.student_id == student_data.student_id,
                            Invoice.school_id == school_id,
                            Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.OVERDUE]),
                            FeeCategory.name.ilike('%exam%')
                        )
                    )
                    exam_fees_result = await self.db.execute(exam_fees_query)
                    if exam_fees_result.scalar_one_or_none():
                        restrictions.append('assessment_access')
                    
                    # Check for lab fee restrictions
                    lab_fees_query = select(Invoice).join(FeeCategory).where(
                        and_(
                            Invoice.student_id == student_data.student_id,
                            Invoice.school_id == school_id,
                            Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.OVERDUE]),
                            or_(
                                FeeCategory.name.ilike('%lab%'),
                                FeeCategory.name.ilike('%practical%')
                            )
                        )
                    )
                    lab_fees_result = await self.db.execute(lab_fees_query)
                    if lab_fees_result.scalar_one_or_none():
                        restrictions.append('practical_access')
                    
                    # Check for general tuition restrictions
                    tuition_fees_query = select(Invoice).join(FeeCategory).where(
                        and_(
                            Invoice.student_id == student_data.student_id,
                            Invoice.school_id == school_id,
                            Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.OVERDUE]),
                            FeeCategory.name.ilike('%tuition%')
                        )
                    )
                    tuition_fees_result = await self.db.execute(tuition_fees_query)
                    if tuition_fees_result.scalar_one_or_none():
                        restrictions.append('class_access')
                    
                    restricted_students.append({
                        'student_id': str(student_data.student_id),
                        'total_outstanding': float(student_data.total_outstanding),
                        'outstanding_invoices': student_data.outstanding_invoices,
                        'restrictions': restrictions,
                        'restriction_level': 'high' if student_data.total_outstanding > Decimal('500.00') else 'medium'
                    })
            
            return restricted_students
            
        except Exception as e:
            logger.error(f"Failed to get students with payment restrictions: {str(e)}")
            return []


# Utility functions for common integration tasks
async def get_academic_finance_integration(db: AsyncSession) -> AcademicFinanceIntegration:
    """Factory function to create AcademicFinanceIntegration instance"""
    return AcademicFinanceIntegration(db)


async def validate_student_academic_access(
    db: AsyncSession,
    student_id: UUID,
    subject_id: UUID,
    school_id: UUID,
    academic_year_id: UUID
) -> bool:
    """Quick validation for student academic access based on payment status"""
    integration = AcademicFinanceIntegration(db)
    access_info = await integration.check_student_subject_access(
        student_id, subject_id, school_id, academic_year_id
    )
    return access_info['has_access']


async def create_academic_invoice_on_enrollment(
    db: AsyncSession,
    student_id: UUID,
    subject_id: UUID,
    school_id: UUID,
    academic_year_id: UUID,
    created_by: UUID
) -> Optional[str]:
    """Create invoice when student enrolls in a subject"""
    integration = AcademicFinanceIntegration(db)
    result = await integration.generate_subject_enrollment_invoice(
        student_id, subject_id, school_id, academic_year_id, created_by
    )
    return result['invoices_created'][0]['invoice_id'] if result and result['invoices_created'] else None