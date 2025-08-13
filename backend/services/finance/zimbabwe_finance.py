"""
Finance Management Module - Zimbabwe-Specific Business Logic
Enhanced financial operations for Zimbabwe schools with local payment integration
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
import logging
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload

from .models import (
    FeeStructure, FeeStructureItem, Invoice, InvoiceItem, Payment, 
    PaymentMethodConfig, StudentAccount, FinancialPeriod
)
from .schemas import (
    PaymentStatus, PaymentMethodType, InvoiceStatus, Currency,
    FeeStructureCreate, InvoiceCreate, PaymentCreate,
    PaynowPaymentRequest, EcocashPaymentRequest, PaymentGatewayResponse
)

logger = logging.getLogger(__name__)

# =====================================================
# ZIMBABWE EDUCATION FINANCE SYSTEM
# =====================================================

class ZimbabweFinanceManager:
    """
    Zimbabwe-specific finance management with local payment integration
    Handles fee structures, invoicing, and payments for Zimbabwe schools
    """
    
    def __init__(self, db: AsyncSession, school_id: UUID):
        self.db = db
        self.school_id = school_id
    
    # =====================================================
    # FEE STRUCTURE MANAGEMENT
    # =====================================================
    
    async def create_zimbabwe_fee_structure(
        self,
        name: str,
        academic_year: str,
        grade_levels: List[int],
        currency: Currency = Currency.USD
    ) -> Dict[str, Any]:
        """Create a comprehensive fee structure for Zimbabwe schools"""
        
        try:
            # Validate Zimbabwe grade levels (1-13)
            for level in grade_levels:
                if level < 1 or level > 13:
                    raise ValueError(f"Invalid Zimbabwe grade level: {level}")
            
            # Create base fee structure
            fee_structure = FeeStructure(
                school_id=self.school_id,
                name=name,
                academic_year=academic_year,
                grade_level_min=min(grade_levels),
                grade_level_max=max(grade_levels),
                currency=currency,
                effective_from=date.today(),
                is_per_term=True,  # Zimbabwe uses term-based fees
                allow_installments=True,
                installment_count=3,  # 3 terms per year
                late_fee_percentage=Decimal('2.5'),  # 2.5% late fee
                grace_period_days=14,  # 2 weeks grace period
                early_payment_discount_percentage=Decimal('5.0'),  # 5% early payment discount
                early_payment_days=30,  # Pay 30 days early for discount
                sibling_discount_percentage=Decimal('10.0'),  # 10% sibling discount
            )
            
            self.db.add(fee_structure)
            await self.db.flush()
            
            # Add standard Zimbabwe fee items
            zimbabwe_fees = await self._create_standard_zimbabwe_fees(fee_structure.id, grade_levels, currency)
            
            await self.db.commit()
            
            logger.info(f"Created Zimbabwe fee structure '{name}' for grades {grade_levels}")
            
            return {
                "fee_structure_id": str(fee_structure.id),
                "name": name,
                "grade_levels": grade_levels,
                "currency": currency,
                "fee_items_created": len(zimbabwe_fees),
                "total_annual_fee": sum(item["amount"] for item in zimbabwe_fees)
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating Zimbabwe fee structure: {e}")
            raise
    
    async def _create_standard_zimbabwe_fees(
        self, 
        fee_structure_id: UUID, 
        grade_levels: List[int], 
        currency: Currency
    ) -> List[Dict[str, Any]]:
        """Create standard fee items for Zimbabwe schools"""
        
        # Define Zimbabwe-specific fee amounts based on grade level
        fee_items = []
        
        # Determine if primary or secondary
        is_primary = any(level <= 7 for level in grade_levels)
        is_secondary = any(level >= 8 for level in grade_levels)
        
        # Base fees in USD (most common in Zimbabwe)
        if currency == Currency.USD:
            if is_primary:
                base_tuition = Decimal('150.00')  # Per term
                registration_fee = Decimal('50.00')
                examination_fee = Decimal('25.00')
                sports_fee = Decimal('20.00')
                library_fee = Decimal('15.00')
            else:  # Secondary
                base_tuition = Decimal('300.00')  # Per term
                registration_fee = Decimal('100.00')
                examination_fee = Decimal('75.00')  # O/A Level exams
                sports_fee = Decimal('40.00')
                library_fee = Decimal('30.00')
        else:
            # Placeholder for other currencies - would normally be converted
            base_tuition = Decimal('150.00')
            registration_fee = Decimal('50.00')
            examination_fee = Decimal('25.00')
            sports_fee = Decimal('20.00')
            library_fee = Decimal('15.00')
        
        # Standard fee items
        standard_fees = [
            {
                "name": "Tuition Fee",
                "fee_type": "tuition",
                "amount": base_tuition,
                "term_number": None,  # Applies to all terms
                "is_mandatory": True,
                "category": "Academic"
            },
            {
                "name": "Registration Fee",
                "fee_type": "registration", 
                "amount": registration_fee,
                "term_number": 1,  # First term only
                "is_mandatory": True,
                "category": "Administrative"
            },
            {
                "name": "Examination Fee",
                "fee_type": "examination",
                "amount": examination_fee,
                "term_number": None,  # All terms for continuous assessment
                "is_mandatory": True,
                "category": "Academic"
            },
            {
                "name": "Sports & Recreation",
                "fee_type": "sports",
                "amount": sports_fee,
                "term_number": None,
                "is_mandatory": False,
                "category": "Activities"
            },
            {
                "name": "Library Fee",
                "fee_type": "library",
                "amount": library_fee,
                "term_number": None,
                "is_mandatory": True,
                "category": "Academic"
            }
        ]
        
        # Add grade-specific fees
        if any(level >= 10 for level in grade_levels):  # O-Level and above
            standard_fees.append({
                "name": "Laboratory Fee",
                "fee_type": "technology",
                "amount": Decimal('60.00') if currency == Currency.USD else Decimal('40.00'),
                "term_number": None,
                "is_mandatory": True,
                "category": "Academic"
            })
        
        if any(level >= 12 for level in grade_levels):  # A-Level
            standard_fees.append({
                "name": "A-Level Preparation",
                "fee_type": "examination",
                "amount": Decimal('120.00') if currency == Currency.USD else Decimal('80.00'),
                "term_number": None,
                "is_mandatory": True,
                "category": "Academic"
            })
        
        # Create fee structure items
        for i, fee_data in enumerate(standard_fees):
            fee_item = FeeStructureItem(
                fee_structure_id=fee_structure_id,
                fee_type=fee_data["fee_type"],
                name=fee_data["name"],
                amount=fee_data["amount"],
                term_number=fee_data["term_number"],
                is_mandatory=fee_data["is_mandatory"],
                allow_partial_payment=True,
                category=fee_data["category"],
                display_order=i + 1
            )
            self.db.add(fee_item)
            fee_items.append(fee_data)
        
        return fee_items
    
    # =====================================================
    # ZIMBABWE INVOICE GENERATION
    # =====================================================
    
    async def generate_zimbabwe_invoice(
        self,
        student_id: UUID,
        fee_structure_id: UUID,
        term_number: int,
        academic_year: str,
        due_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Generate an invoice for a Zimbabwe student with term-specific fees"""
        
        try:
            # Validate term number (Zimbabwe has 3 terms)
            if term_number not in [1, 2, 3]:
                raise ValueError("Zimbabwe schools have 3 terms (1, 2, 3)")
            
            # Get fee structure
            fee_structure_result = await self.db.execute(
                select(FeeStructure)
                .options(selectinload(FeeStructure.fee_items))
                .where(
                    and_(
                        FeeStructure.id == fee_structure_id,
                        FeeStructure.school_id == self.school_id,
                        FeeStructure.is_active == True
                    )
                )
            )
            fee_structure = fee_structure_result.scalar_one_or_none()
            
            if not fee_structure:
                raise ValueError("Fee structure not found or inactive")
            
            # Calculate due date if not provided
            if not due_date:
                due_date = self._calculate_zimbabwe_due_date(term_number, academic_year)
            
            # Generate unique invoice number
            invoice_number = await self._generate_invoice_number(academic_year, term_number)
            
            # Create invoice
            invoice = Invoice(
                school_id=self.school_id,
                student_id=student_id,
                fee_structure_id=fee_structure_id,
                invoice_number=invoice_number,
                academic_year=academic_year,
                term_number=term_number,
                issue_date=date.today(),
                due_date=due_date,
                currency=fee_structure.currency,
                status=InvoiceStatus.DRAFT
            )
            
            self.db.add(invoice)
            await self.db.flush()
            
            # Add invoice items for this term
            total_amount = Decimal('0.00')
            line_number = 1
            
            for fee_item in fee_structure.fee_items:
                # Include fee if it applies to all terms or this specific term
                if fee_item.term_number is None or fee_item.term_number == term_number:
                    
                    # Calculate item total (considering installments for annual fees)
                    item_amount = fee_item.amount
                    if fee_item.term_number is None and fee_structure.is_per_term:
                        # This is an annual fee, divide by number of terms
                        item_amount = fee_item.amount / 3
                    
                    invoice_item = InvoiceItem(
                        invoice_id=invoice.id,
                        fee_structure_item_id=fee_item.id,
                        fee_type=fee_item.fee_type,
                        name=fee_item.name,
                        description=fee_item.description,
                        quantity=Decimal('1.00'),
                        unit_price=item_amount,
                        total_price=item_amount,
                        term_number=term_number,
                        category=fee_item.category,
                        line_number=line_number
                    )
                    
                    self.db.add(invoice_item)
                    total_amount += item_amount
                    line_number += 1
            
            # Update invoice totals
            invoice.subtotal_amount = total_amount
            invoice.total_amount = total_amount
            invoice.outstanding_amount = total_amount
            
            await self.db.commit()
            
            # Update student account
            await self._update_student_account(student_id, invoice_amount=total_amount)
            
            logger.info(f"Generated Zimbabwe invoice {invoice_number} for student {student_id}, term {term_number}")
            
            return {
                "invoice_id": str(invoice.id),
                "invoice_number": invoice_number,
                "student_id": str(student_id),
                "term_number": term_number,
                "total_amount": float(total_amount),
                "currency": fee_structure.currency,
                "due_date": due_date.isoformat(),
                "items_count": line_number - 1
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error generating Zimbabwe invoice: {e}")
            raise
    
    def _calculate_zimbabwe_due_date(self, term_number: int, academic_year: str) -> date:
        """Calculate due date based on Zimbabwe school calendar"""
        year = int(academic_year)
        
        # Zimbabwe school terms and typical due dates
        if term_number == 1:  # Term 1: Jan-Apr
            return date(year, 2, 15)  # Due mid-February
        elif term_number == 2:  # Term 2: May-Aug  
            return date(year, 6, 15)  # Due mid-June
        else:  # Term 3: Sep-Dec
            return date(year, 10, 15)  # Due mid-October
    
    async def _generate_invoice_number(self, academic_year: str, term_number: int) -> str:
        """Generate unique invoice number for Zimbabwe format"""
        
        # Get count of invoices for this term
        count_result = await self.db.execute(
            select(func.count(Invoice.id))
            .where(
                and_(
                    Invoice.school_id == self.school_id,
                    Invoice.academic_year == academic_year,
                    Invoice.term_number == term_number
                )
            )
        )
        count = count_result.scalar() + 1
        
        # Format: ZW-2024-T1-0001
        return f"ZW-{academic_year}-T{term_number}-{count:04d}"
    
    # =====================================================
    # ZIMBABWE PAYMENT PROCESSING
    # =====================================================
    
    async def process_zimbabwe_payment(
        self,
        invoice_id: UUID,
        amount: Decimal,
        payment_method: str,
        payer_info: Dict[str, Any],
        external_reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process payment using Zimbabwe payment methods"""
        
        try:
            # Get invoice
            invoice_result = await self.db.execute(
                select(Invoice).where(
                    and_(
                        Invoice.id == invoice_id,
                        Invoice.school_id == self.school_id
                    )
                )
            )
            invoice = invoice_result.scalar_one_or_none()
            
            if not invoice:
                raise ValueError("Invoice not found")
            
            if invoice.outstanding_amount <= 0:
                raise ValueError("Invoice already fully paid")
            
            if amount > invoice.outstanding_amount:
                raise ValueError("Payment amount exceeds outstanding balance")
            
            # Generate payment reference
            payment_reference = await self._generate_payment_reference()
            
            # Get payment method config
            payment_config = await self._get_payment_method_config(payment_method)
            
            # Calculate transaction fee
            transaction_fee = await self._calculate_transaction_fee(amount, payment_config)
            net_amount = amount - transaction_fee
            
            # Create payment record
            payment = Payment(
                school_id=self.school_id,
                student_id=invoice.student_id,
                invoice_id=invoice_id,
                payment_reference=payment_reference,
                external_reference=external_reference,
                amount=amount,
                currency=invoice.currency,
                transaction_fee=transaction_fee,
                net_amount=net_amount,
                payment_method=payment_method,
                payment_date=datetime.now(),
                status=PaymentStatus.PENDING,
                payer_name=payer_info.get('name'),
                payer_email=payer_info.get('email'),
                payer_phone=payer_info.get('phone')
            )
            
            self.db.add(payment)
            await self.db.flush()
            
            # Process payment based on method
            gateway_response = await self._process_payment_gateway(payment, payment_method, payer_info)
            
            # Update payment with gateway response
            payment.gateway_response = gateway_response
            payment.transaction_id = gateway_response.get('transaction_id')
            
            if gateway_response.get('success'):
                payment.status = PaymentStatus.COMPLETED
                payment.processed_date = datetime.now()
                
                # Update invoice
                invoice.paid_amount += amount
                invoice.outstanding_amount -= amount
                
                if invoice.outstanding_amount <= 0:
                    invoice.status = InvoiceStatus.PAID
                else:
                    invoice.status = InvoiceStatus.PARTIALLY_PAID
                
                # Update student account
                await self._update_student_account(invoice.student_id, payment_amount=amount)
                
            else:
                payment.status = PaymentStatus.FAILED
            
            await self.db.commit()
            
            logger.info(f"Processed Zimbabwe payment {payment_reference} for ${amount}")
            
            return {
                "payment_id": str(payment.id),
                "payment_reference": payment_reference,
                "amount": float(amount),
                "transaction_fee": float(transaction_fee),
                "net_amount": float(net_amount),
                "status": payment.status,
                "gateway_response": gateway_response
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error processing Zimbabwe payment: {e}")
            raise
    
    async def _generate_payment_reference(self) -> str:
        """Generate unique payment reference"""
        
        # Get today's payment count
        today = date.today()
        count_result = await self.db.execute(
            select(func.count(Payment.id))
            .where(
                and_(
                    Payment.school_id == self.school_id,
                    func.date(Payment.payment_date) == today
                )
            )
        )
        count = count_result.scalar() + 1
        
        # Format: PAY-YYYYMMDD-0001
        return f"PAY-{today.strftime('%Y%m%d')}-{count:04d}"
    
    async def _get_payment_method_config(self, payment_method: str) -> Dict[str, Any]:
        """Get payment method configuration"""
        
        config_result = await self.db.execute(
            select(PaymentMethodConfig).where(
                and_(
                    PaymentMethodConfig.school_id == self.school_id,
                    PaymentMethodConfig.payment_method == payment_method,
                    PaymentMethodConfig.is_active == True
                )
            )
        )
        config = config_result.scalar_one_or_none()
        
        if not config:
            # Return default config
            return {
                "transaction_fee_percentage": Decimal('0.00'),
                "transaction_fee_fixed": Decimal('0.00')
            }
        
        return {
            "transaction_fee_percentage": config.transaction_fee_percentage,
            "transaction_fee_fixed": config.transaction_fee_fixed,
            "gateway_config": config.gateway_config or {}
        }
    
    async def _calculate_transaction_fee(self, amount: Decimal, config: Dict[str, Any]) -> Decimal:
        """Calculate transaction fee for payment"""
        
        percentage_fee = amount * (config["transaction_fee_percentage"] / 100)
        fixed_fee = config["transaction_fee_fixed"]
        
        return percentage_fee + fixed_fee
    
    async def _process_payment_gateway(
        self, 
        payment: Payment, 
        payment_method: str, 
        payer_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process payment through appropriate gateway"""
        
        # This would integrate with actual payment gateways
        # For now, return success for demonstration
        
        if payment_method == "cash":
            return {
                "success": True,
                "transaction_id": f"CASH-{payment.payment_reference}",
                "message": "Cash payment recorded",
                "gateway": "internal"
            }
        elif payment_method == "ecocash":
            # Would integrate with EcoCash API
            return {
                "success": True,
                "transaction_id": f"ECO-{payment.payment_reference}",
                "message": "EcoCash payment processed",
                "gateway": "ecocash"
            }
        elif payment_method == "paynow":
            # Would integrate with Paynow API
            return {
                "success": True,
                "transaction_id": f"PAY-{payment.payment_reference}",
                "message": "Paynow payment processed",
                "gateway": "paynow"
            }
        else:
            return {
                "success": False,
                "message": f"Unknown payment method: {payment_method}",
                "gateway": "unknown"
            }
    
    # =====================================================
    # STUDENT ACCOUNT MANAGEMENT
    # =====================================================
    
    async def _update_student_account(
        self, 
        student_id: UUID, 
        invoice_amount: Optional[Decimal] = None,
        payment_amount: Optional[Decimal] = None
    ) -> None:
        """Update student account balances"""
        
        # Get or create student account
        account_result = await self.db.execute(
            select(StudentAccount).where(
                and_(
                    StudentAccount.school_id == self.school_id,
                    StudentAccount.student_id == student_id
                )
            )
        )
        account = account_result.scalar_one_or_none()
        
        if not account:
            account = StudentAccount(
                school_id=self.school_id,
                student_id=student_id,
                account_number=await self._generate_account_number(student_id)
            )
            self.db.add(account)
        
        # Update balances
        if invoice_amount:
            account.total_invoiced += invoice_amount
            account.total_outstanding += invoice_amount
            account.current_balance -= invoice_amount  # Negative balance = amount owed
            account.last_invoice_date = datetime.now()
        
        if payment_amount:
            account.total_paid += payment_amount
            account.total_outstanding -= payment_amount
            account.current_balance += payment_amount
            account.last_payment_date = datetime.now()
    
    async def _generate_account_number(self, student_id: UUID) -> str:
        """Generate unique account number for student"""
        
        # Simple format: ACC-{last 8 chars of student UUID}
        return f"ACC-{str(student_id)[-8:].upper()}"
    
    # =====================================================
    # ZIMBABWE FINANCIAL REPORTING
    # =====================================================
    
    async def generate_zimbabwe_financial_report(
        self,
        academic_year: str,
        term_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive financial report for Zimbabwe schools"""
        
        try:
            # Base query filters
            filters = [
                Invoice.school_id == self.school_id,
                Invoice.academic_year == academic_year
            ]
            
            if term_number:
                filters.append(Invoice.term_number == term_number)
            
            # Get invoice statistics
            invoice_stats = await self.db.execute(
                select(
                    func.count(Invoice.id).label('total_invoices'),
                    func.sum(Invoice.total_amount).label('total_invoiced'),
                    func.sum(Invoice.paid_amount).label('total_paid'),
                    func.sum(Invoice.outstanding_amount).label('total_outstanding'),
                    func.count(func.distinct(Invoice.student_id)).label('students_with_invoices')
                )
                .where(and_(*filters))
            )
            stats = invoice_stats.first()
            
            # Get payment method breakdown
            payment_methods = await self.db.execute(
                select(
                    Payment.payment_method,
                    func.count(Payment.id).label('payment_count'),
                    func.sum(Payment.amount).label('total_amount')
                )
                .join(Invoice, Payment.invoice_id == Invoice.id)
                .where(
                    and_(
                        Payment.school_id == self.school_id,
                        Payment.status == PaymentStatus.COMPLETED,
                        Invoice.academic_year == academic_year,
                        *([Invoice.term_number == term_number] if term_number else [])
                    )
                )
                .group_by(Payment.payment_method)
            )
            
            # Get overdue invoices
            overdue_invoices = await self.db.execute(
                select(func.count(Invoice.id), func.sum(Invoice.outstanding_amount))
                .where(
                    and_(
                        *filters,
                        Invoice.due_date < date.today(),
                        Invoice.outstanding_amount > 0
                    )
                )
            )
            overdue_stats = overdue_invoices.first()
            
            # Calculate collection rate
            total_invoiced = stats.total_invoiced or Decimal('0.00')
            total_paid = stats.total_paid or Decimal('0.00')
            collection_rate = (total_paid / total_invoiced * 100) if total_invoiced > 0 else Decimal('0.00')
            
            report = {
                "period": f"{academic_year}" + (f" - Term {term_number}" if term_number else ""),
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_invoices": stats.total_invoices or 0,
                    "total_invoiced": float(total_invoiced),
                    "total_paid": float(total_paid),
                    "total_outstanding": float(stats.total_outstanding or Decimal('0.00')),
                    "collection_rate": float(collection_rate),
                    "students_with_invoices": stats.students_with_invoices or 0,
                    "overdue_invoices": overdue_stats[0] or 0,
                    "overdue_amount": float(overdue_stats[1] or Decimal('0.00'))
                },
                "payment_methods": [
                    {
                        "method": row.payment_method,
                        "payment_count": row.payment_count,
                        "total_amount": float(row.total_amount)
                    }
                    for row in payment_methods
                ],
                "currency": "USD"  # Primary currency for Zimbabwe schools
            }
            
            logger.info(f"Generated Zimbabwe financial report for {academic_year}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating Zimbabwe financial report: {e}")
            raise