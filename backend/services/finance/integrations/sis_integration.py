"""
Finance-SIS Integration Module
Links Student Information System with financial operations for comprehensive billing
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload, joinedload

# Finance module imports
from ..models import (
    FeeStructure, FeeStructureItem, Invoice, InvoiceItem, Payment, 
    PaymentMethodConfig, StudentAccount, FinancialPeriod
)
from ..schemas import (
    PaymentStatus, PaymentMethodType, InvoiceStatus, Currency,
    FeeStructureCreate, InvoiceCreate, PaymentCreate
)
from ..zimbabwe_finance import ZimbabweFinanceManager

logger = logging.getLogger(__name__)

# =====================================================
# FINANCE-SIS INTEGRATION MANAGER
# =====================================================

class FinanceSISIntegration:
    """
    Integration layer between Finance and Student Information System
    Handles student billing, family accounts, enrollment-based invoicing, and payment tracking
    """
    
    def __init__(self, db: AsyncSession, school_id: UUID):
        self.db = db
        self.school_id = school_id
        self.finance_manager = ZimbabweFinanceManager(db, school_id)
    
    # =====================================================
    # STUDENT ENROLLMENT BILLING
    # =====================================================
    
    async def create_enrollment_based_invoice(
        self,
        student_id: UUID,
        academic_year: str,
        term_number: int,
        enrollment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create invoice based on student enrollment information
        
        Args:
            student_id: Student identifier
            academic_year: Academic year
            term_number: Term number (1-3 for Zimbabwe)
            enrollment_data: Student enrollment details from SIS
        
        Expected enrollment_data structure:
        {
            "student_number": "STU-2024-001",
            "grade_level": 8,
            "class_id": "uuid",
            "enrollment_date": "2024-01-15",
            "enrollment_status": "active",
            "special_programs": ["sports", "computer_club"],
            "scholarship_percentage": 10.0,
            "family_id": "uuid",
            "guardian_info": {...}
        }
        """
        
        try:
            # Validate enrollment data
            required_fields = ["student_number", "grade_level", "enrollment_status"]
            for field in required_fields:
                if field not in enrollment_data:
                    raise ValueError(f"Missing required enrollment field: {field}")
            
            if enrollment_data["enrollment_status"] != "active":
                raise ValueError("Cannot create invoice for inactive enrollment")
            
            grade_level = enrollment_data["grade_level"]
            student_number = enrollment_data["student_number"]
            
            # Find appropriate fee structure for grade level
            fee_structure_id = await self._find_fee_structure_for_grade(grade_level, academic_year)
            
            if not fee_structure_id:
                raise ValueError(f"No fee structure found for grade {grade_level}")
            
            # Generate base invoice
            base_invoice = await self.finance_manager.generate_zimbabwe_invoice(
                student_id=student_id,
                fee_structure_id=fee_structure_id,
                term_number=term_number,
                academic_year=academic_year
            )
            
            # Apply enrollment-specific adjustments
            adjustments = await self._apply_enrollment_adjustments(
                UUID(base_invoice["invoice_id"]),
                enrollment_data
            )
            
            # Update student account with enrollment info
            await self._update_student_account_with_enrollment(student_id, enrollment_data)
            
            result = {
                **base_invoice,
                "student_number": student_number,
                "grade_level": grade_level,
                "enrollment_adjustments": adjustments,
                "net_amount_after_adjustments": adjustments.get("final_amount", base_invoice["total_amount"])
            }
            
            logger.info(f"Created enrollment-based invoice for student {student_number}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating enrollment-based invoice: {e}")
            raise
    
    async def _apply_enrollment_adjustments(
        self,
        invoice_id: UUID,
        enrollment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply adjustments based on enrollment details"""
        
        # Get invoice
        invoice_result = await self.db.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        invoice = invoice_result.scalar_one()
        
        original_amount = invoice.total_amount
        adjustments = []
        final_amount = original_amount
        
        # Apply scholarship discount
        scholarship_percentage = enrollment_data.get("scholarship_percentage", 0)
        if scholarship_percentage > 0:
            scholarship_discount = original_amount * (Decimal(str(scholarship_percentage)) / 100)
            final_amount -= scholarship_discount
            adjustments.append({
                "type": "scholarship_discount",
                "description": f"Scholarship ({scholarship_percentage}%)",
                "amount": -float(scholarship_discount)
            })
        
        # Apply special program fees
        special_programs = enrollment_data.get("special_programs", [])
        program_fees = {
            "sports": 50.00,
            "computer_club": 75.00,
            "drama_club": 40.00,
            "debate_society": 30.00,
            "music_program": 80.00
        }
        
        for program in special_programs:
            if program in program_fees:
                program_fee = Decimal(str(program_fees[program]))
                final_amount += program_fee
                adjustments.append({
                    "type": "program_fee",
                    "description": f"{program.replace('_', ' ').title()} Program",
                    "amount": float(program_fee)
                })
        
        # Apply sibling discount if applicable
        family_id = enrollment_data.get("family_id")
        if family_id:
            sibling_discount = await self._calculate_sibling_discount(family_id, original_amount)
            if sibling_discount > 0:
                final_amount -= sibling_discount
                adjustments.append({
                    "type": "sibling_discount",
                    "description": "Sibling Discount",
                    "amount": -float(sibling_discount)
                })
        
        # Update invoice with final amount
        invoice.total_amount = final_amount
        invoice.outstanding_amount = final_amount
        
        # Add adjustment details to invoice metadata
        invoice.metadata = {
            "enrollment_adjustments": adjustments,
            "original_amount": float(original_amount),
            "final_amount": float(final_amount)
        }
        
        await self.db.commit()
        
        return {
            "original_amount": float(original_amount),
            "final_amount": float(final_amount),
            "total_adjustments": float(final_amount - original_amount),
            "adjustments": adjustments
        }
    
    # =====================================================
    # FAMILY BILLING INTEGRATION
    # =====================================================
    
    async def generate_family_consolidated_bill(
        self,
        family_id: UUID,
        academic_year: str,
        term_number: int,
        include_payment_plan: bool = True
    ) -> Dict[str, Any]:
        """
        Generate consolidated bill for all students in a family
        
        Args:
            family_id: Family identifier from SIS
            academic_year: Academic year
            term_number: Term number
            include_payment_plan: Include payment plan options
        """
        
        try:
            # Get family information from SIS
            family_info = await self._get_family_information(family_id)
            
            if not family_info or not family_info.get("students"):
                raise ValueError("Family not found or has no enrolled students")
            
            students = family_info["students"]
            consolidated_bill = {
                "family_id": str(family_id),
                "family_name": family_info.get("family_name", "Unknown Family"),
                "guardian_info": family_info.get("guardian_info", {}),
                "academic_year": academic_year,
                "term_number": term_number,
                "generated_date": datetime.now().isoformat(),
                "students": [],
                "summary": {
                    "total_students": len(students),
                    "total_amount": 0.0,
                    "total_outstanding": 0.0,
                    "total_paid": 0.0
                }
            }
            
            total_amount = Decimal('0.00')
            total_outstanding = Decimal('0.00')
            total_paid = Decimal('0.00')
            
            # Process each student
            for student in students:
                try:
                    # Get or create invoice for student
                    student_invoice = await self._get_or_create_student_invoice(
                        UUID(student["student_id"]),
                        academic_year,
                        term_number,
                        student
                    )
                    
                    # Get payment history for student
                    payment_history = await self._get_student_payment_history(
                        UUID(student["student_id"]),
                        academic_year,
                        term_number
                    )
                    
                    student_data = {
                        "student_id": student["student_id"],
                        "student_name": student.get("name", "Unknown"),
                        "student_number": student.get("student_number"),
                        "grade_level": student.get("grade_level"),
                        "invoice": student_invoice,
                        "payments": payment_history,
                        "balance_status": self._determine_balance_status(student_invoice, payment_history)
                    }
                    
                    consolidated_bill["students"].append(student_data)
                    
                    # Update totals
                    invoice_amount = Decimal(str(student_invoice.get("total_amount", 0)))
                    outstanding_amount = Decimal(str(student_invoice.get("outstanding_amount", 0)))
                    paid_amount = invoice_amount - outstanding_amount
                    
                    total_amount += invoice_amount
                    total_outstanding += outstanding_amount
                    total_paid += paid_amount
                    
                except Exception as e:
                    logger.warning(f"Error processing student {student.get('student_id')}: {e}")
                    continue
            
            # Update summary
            consolidated_bill["summary"].update({
                "total_amount": float(total_amount),
                "total_outstanding": float(total_outstanding),
                "total_paid": float(total_paid),
                "collection_rate": float((total_paid / total_amount * 100) if total_amount > 0 else 0)
            })
            
            # Add payment plan options if requested
            if include_payment_plan and total_outstanding > 0:
                consolidated_bill["payment_options"] = await self._generate_family_payment_options(
                    total_outstanding, family_info
                )
            
            # Apply family-level discounts
            family_adjustments = await self._apply_family_discounts(consolidated_bill)
            if family_adjustments:
                consolidated_bill["family_adjustments"] = family_adjustments
            
            logger.info(f"Generated consolidated bill for family {family_id} with {len(students)} students")
            
            return {
                "success": True,
                "data": consolidated_bill
            }
            
        except Exception as e:
            logger.error(f"Error generating family consolidated bill: {e}")
            raise
    
    async def _get_family_information(self, family_id: UUID) -> Dict[str, Any]:
        """Get family information from SIS"""
        
        # Mock family data - in production would query SIS module
        return {
            "family_id": str(family_id),
            "family_name": "The Chimbira Family",
            "guardian_info": {
                "primary_guardian": "Mr. James Chimbira",
                "secondary_guardian": "Mrs. Mary Chimbira",
                "contact_phone": "+263 77 123 4567",
                "contact_email": "james.chimbira@email.com",
                "preferred_payment_method": "EcoCash",
                "billing_address": "123 Borrowdale Road, Harare"
            },
            "family_status": "active",
            "payment_history_score": 8.5,
            "students": [
                {
                    "student_id": "550e8400-e29b-41d4-a716-446655440001",
                    "name": "Tendai Chimbira",
                    "student_number": "STU-2024-001",
                    "grade_level": 10,
                    "enrollment_status": "active"
                },
                {
                    "student_id": "550e8400-e29b-41d4-a716-446655440002",
                    "name": "Grace Chimbira", 
                    "student_number": "STU-2024-002",
                    "grade_level": 7,
                    "enrollment_status": "active"
                }
            ]
        }
    
    # =====================================================
    # BULK STUDENT OPERATIONS
    # =====================================================
    
    async def bulk_create_student_invoices(
        self,
        academic_year: str,
        term_number: int,
        filters: Dict[str, Any] = None,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Bulk create invoices for students based on SIS enrollment data
        
        Args:
            academic_year: Academic year
            term_number: Term number
            filters: Optional filters (grade_level, class_id, enrollment_status, etc.)
            batch_size: Processing batch size
        """
        
        try:
            # Get students from SIS based on filters
            students = await self._get_students_from_sis(filters or {})
            
            if not students:
                return {
                    "success": True,
                    "message": "No students found matching criteria",
                    "data": {
                        "total_students": 0,
                        "invoices_created": 0,
                        "errors": []
                    }
                }
            
            # Process students in batches
            total_students = len(students)
            invoices_created = 0
            errors = []
            processing_summary = []
            
            for i in range(0, total_students, batch_size):
                batch = students[i:i + batch_size]
                batch_result = await self._process_student_invoice_batch(
                    batch, academic_year, term_number
                )
                
                invoices_created += batch_result["created"]
                errors.extend(batch_result["errors"])
                processing_summary.append({
                    "batch_number": i // batch_size + 1,
                    "students_processed": len(batch),
                    "invoices_created": batch_result["created"],
                    "errors_count": len(batch_result["errors"])
                })
            
            success_rate = (invoices_created / total_students * 100) if total_students > 0 else 0
            
            result = {
                "success": True,
                "message": f"Bulk invoice creation completed",
                "data": {
                    "academic_year": academic_year,
                    "term_number": term_number,
                    "total_students": total_students,
                    "invoices_created": invoices_created,
                    "success_rate": success_rate,
                    "errors_count": len(errors),
                    "processing_batches": len(processing_summary),
                    "batch_summary": processing_summary,
                    "errors": errors[:10]  # Return first 10 errors
                }
            }
            
            logger.info(f"Bulk created {invoices_created}/{total_students} student invoices")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in bulk student invoice creation: {e}")
            raise
    
    async def _get_students_from_sis(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get students from SIS based on filters"""
        
        # Mock student data - in production would query SIS module
        all_students = []
        
        # Generate mock students across different grades
        grades_data = {
            1: 28, 2: 26, 3: 30, 4: 27, 5: 29, 6: 25, 7: 32,  # Primary
            8: 35, 9: 33, 10: 38, 11: 31,  # O-Level
            12: 28, 13: 24  # A-Level
        }
        
        student_counter = 1
        for grade, count in grades_data.items():
            # Apply grade level filter if specified
            if "grade_level" in filters and grade != filters["grade_level"]:
                continue
                
            for i in range(count):
                student = {
                    "student_id": f"550e8400-e29b-41d4-{grade:02d}{i:02d}-{student_counter:06d}",
                    "student_number": f"STU-{grade:02d}-{i+1:03d}",
                    "name": f"Student {i+1} Grade {grade}",
                    "grade_level": grade,
                    "class_id": f"class-{grade}-{chr(65 + (i % 3))}",  # A, B, C classes
                    "enrollment_status": "active",
                    "enrollment_date": "2024-01-15",
                    "family_id": f"family-{grade}-{i//2}",  # Siblings share family
                    "special_programs": self._generate_random_programs(grade),
                    "scholarship_percentage": 5.0 if i % 10 == 0 else 0.0  # 10% get scholarship
                }
                all_students.append(student)
                student_counter += 1
        
        # Apply other filters
        filtered_students = all_students
        
        if "enrollment_status" in filters:
            filtered_students = [s for s in filtered_students 
                               if s["enrollment_status"] == filters["enrollment_status"]]
        
        if "class_id" in filters:
            filtered_students = [s for s in filtered_students 
                               if s["class_id"] == filters["class_id"]]
        
        return filtered_students
    
    def _generate_random_programs(self, grade_level: int) -> List[str]:
        """Generate random special programs based on grade level"""
        
        programs = []
        if grade_level >= 8:  # Secondary students more likely to have programs
            import random
            available_programs = ["sports", "computer_club", "drama_club", "debate_society"]
            if random.random() < 0.3:  # 30% chance
                programs.append(random.choice(available_programs))
        
        return programs
    
    # =====================================================
    # STUDENT PAYMENT TRACKING
    # =====================================================
    
    async def track_student_payment_progress(
        self,
        student_id: UUID,
        academic_year: str
    ) -> Dict[str, Any]:
        """
        Track payment progress for a student across all terms
        
        Args:
            student_id: Student identifier
            academic_year: Academic year to track
        """
        
        try:
            # Get student information
            student_info = await self._get_student_information(student_id)
            
            if not student_info:
                raise ValueError("Student not found")
            
            # Get all invoices for student in academic year
            invoices_result = await self.db.execute(
                select(Invoice)
                .where(
                    and_(
                        Invoice.school_id == self.school_id,
                        Invoice.student_id == student_id,
                        Invoice.academic_year == academic_year
                    )
                )
                .order_by(Invoice.term_number)
            )
            invoices = invoices_result.scalars().all()
            
            # Get all payments for student in academic year
            payments_result = await self.db.execute(
                select(Payment)
                .join(Invoice, Payment.invoice_id == Invoice.id)
                .where(
                    and_(
                        Payment.school_id == self.school_id,
                        Payment.student_id == student_id,
                        Invoice.academic_year == academic_year,
                        Payment.status == PaymentStatus.COMPLETED
                    )
                )
                .order_by(Payment.payment_date)
            )
            payments = payments_result.scalars().all()
            
            # Build payment progress tracking
            progress_tracking = {
                "student_info": {
                    "student_id": str(student_id),
                    "name": student_info.get("name", "Unknown"),
                    "student_number": student_info.get("student_number"),
                    "grade_level": student_info.get("grade_level"),
                    "family_id": student_info.get("family_id")
                },
                "academic_year": academic_year,
                "terms": [],
                "summary": {
                    "total_invoiced": 0.0,
                    "total_paid": 0.0,
                    "total_outstanding": 0.0,
                    "payment_count": len(payments),
                    "average_payment_days": 0,
                    "payment_methods_used": set()
                }
            }
            
            total_invoiced = Decimal('0.00')
            total_paid = Decimal('0.00')
            payment_days_total = 0
            
            # Process each term
            for term_num in [1, 2, 3]:
                term_invoices = [inv for inv in invoices if inv.term_number == term_num]
                term_payments = [pay for pay in payments 
                               if any(inv.id == pay.invoice_id for inv in term_invoices)]
                
                term_data = {
                    "term_number": term_num,
                    "invoices": [],
                    "payments": [],
                    "term_total": 0.0,
                    "term_paid": 0.0,
                    "term_outstanding": 0.0,
                    "payment_status": "not_invoiced"
                }
                
                term_total = Decimal('0.00')
                term_paid_amount = Decimal('0.00')
                
                for invoice in term_invoices:
                    invoice_payments = [p for p in term_payments if p.invoice_id == invoice.id]
                    invoice_paid = sum(p.amount for p in invoice_payments)
                    
                    term_data["invoices"].append({
                        "invoice_id": str(invoice.id),
                        "invoice_number": invoice.invoice_number,
                        "issue_date": invoice.issue_date.isoformat(),
                        "due_date": invoice.due_date.isoformat(),
                        "amount": float(invoice.total_amount),
                        "paid": float(invoice_paid),
                        "outstanding": float(invoice.outstanding_amount),
                        "status": invoice.status.value
                    })
                    
                    term_total += invoice.total_amount
                    term_paid_amount += invoice_paid
                
                for payment in term_payments:
                    days_to_pay = self._calculate_payment_days(payment, term_invoices)
                    payment_days_total += days_to_pay
                    
                    term_data["payments"].append({
                        "payment_id": str(payment.id),
                        "payment_date": payment.payment_date.isoformat(),
                        "amount": float(payment.amount),
                        "method": payment.payment_method,
                        "reference": payment.payment_reference,
                        "days_to_pay": days_to_pay
                    })
                    
                    progress_tracking["summary"]["payment_methods_used"].add(payment.payment_method)
                
                # Update term data
                term_data.update({
                    "term_total": float(term_total),
                    "term_paid": float(term_paid_amount),
                    "term_outstanding": float(term_total - term_paid_amount),
                    "payment_status": self._determine_term_payment_status(term_total, term_paid_amount)
                })
                
                total_invoiced += term_total
                total_paid += term_paid_amount
                progress_tracking["terms"].append(term_data)
            
            # Update summary
            progress_tracking["summary"].update({
                "total_invoiced": float(total_invoiced),
                "total_paid": float(total_paid),
                "total_outstanding": float(total_invoiced - total_paid),
                "average_payment_days": payment_days_total // len(payments) if payments else 0,
                "payment_methods_used": list(progress_tracking["summary"]["payment_methods_used"]),
                "collection_rate": float(total_paid / total_invoiced * 100) if total_invoiced > 0 else 0
            })
            
            logger.info(f"Generated payment progress tracking for student {student_info.get('student_number')}")
            
            return {
                "success": True,
                "data": progress_tracking
            }
            
        except Exception as e:
            logger.error(f"Error tracking student payment progress: {e}")
            raise
    
    # =====================================================
    # UTILITY METHODS
    # =====================================================
    
    async def _find_fee_structure_for_grade(
        self, 
        grade_level: int, 
        academic_year: str
    ) -> Optional[UUID]:
        """Find appropriate fee structure for grade level"""
        
        result = await self.db.execute(
            select(FeeStructure).where(
                and_(
                    FeeStructure.school_id == self.school_id,
                    FeeStructure.academic_year == academic_year,
                    FeeStructure.grade_level_min <= grade_level,
                    FeeStructure.grade_level_max >= grade_level,
                    FeeStructure.is_active == True
                )
            ).limit(1)
        )
        
        fee_structure = result.scalar_one_or_none()
        return fee_structure.id if fee_structure else None
    
    async def _calculate_sibling_discount(
        self, 
        family_id: str, 
        base_amount: Decimal
    ) -> Decimal:
        """Calculate sibling discount based on family size"""
        
        # Mock sibling count - would normally query SIS
        sibling_count = 2  # Assume 2 siblings for demo
        
        if sibling_count >= 2:
            return base_amount * Decimal('0.10')  # 10% discount for siblings
        
        return Decimal('0.00')
    
    def _determine_balance_status(
        self, 
        invoice: Dict[str, Any], 
        payments: List[Dict[str, Any]]
    ) -> str:
        """Determine student balance status"""
        
        outstanding = float(invoice.get("outstanding_amount", 0))
        
        if outstanding <= 0:
            return "paid_in_full"
        elif len(payments) > 0:
            return "partially_paid"
        else:
            return "unpaid"
    
    def _determine_term_payment_status(
        self, 
        term_total: Decimal, 
        term_paid: Decimal
    ) -> str:
        """Determine payment status for a term"""
        
        if term_total <= 0:
            return "not_invoiced"
        elif term_paid >= term_total:
            return "paid_in_full"
        elif term_paid > 0:
            return "partially_paid"
        else:
            return "unpaid"