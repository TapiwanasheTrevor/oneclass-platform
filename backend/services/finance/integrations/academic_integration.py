"""
Finance-Academic Integration Module
Links academic structures (grades, classes, terms) with financial operations
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
# FINANCE-ACADEMIC INTEGRATION MANAGER
# =====================================================

class FinanceAcademicIntegration:
    """
    Integration layer between Finance and Academic modules
    Handles grade-based fee structures, class-based billing, and term-based invoicing
    """
    
    def __init__(self, db: AsyncSession, school_id: UUID):
        self.db = db
        self.school_id = school_id
        self.finance_manager = ZimbabweFinanceManager(db, school_id)
    
    # =====================================================
    # GRADE-BASED FEE MANAGEMENT
    # =====================================================
    
    async def create_grade_based_fee_structure(
        self,
        academic_year: str,
        grade_configurations: List[Dict[str, Any]],
        base_currency: Currency = Currency.USD
    ) -> Dict[str, Any]:
        """
        Create fee structures based on academic grade levels
        
        Args:
            academic_year: The academic year (e.g., "2024")
            grade_configurations: List of grade configs with custom fees
            base_currency: Primary currency for fees
        
        Example grade_configurations:
        [
            {
                "grade_levels": [1, 2, 3, 4],  # Primary grades 1-4
                "fee_multiplier": 1.0,
                "special_fees": {"computer_lab": 25.00}
            },
            {
                "grade_levels": [8, 9, 10, 11],  # O-Level grades
                "fee_multiplier": 1.5,
                "special_fees": {"laboratory": 75.00, "examination": 150.00}
            }
        ]
        """
        
        try:
            created_structures = []
            
            for config in grade_configurations:
                grade_levels = config["grade_levels"]
                fee_multiplier = config.get("fee_multiplier", 1.0)
                special_fees = config.get("special_fees", {})
                
                # Determine grade category
                min_grade = min(grade_levels)
                max_grade = max(grade_levels)
                
                if max_grade <= 7:
                    category = "Primary"
                elif min_grade >= 8 and max_grade <= 11:
                    category = "O-Level"
                elif min_grade >= 12:
                    category = "A-Level"
                else:
                    category = "Mixed"
                
                structure_name = f"{category} Fees {academic_year}"
                
                # Create base fee structure using Zimbabwe manager
                result = await self.finance_manager.create_zimbabwe_fee_structure(
                    name=structure_name,
                    academic_year=academic_year,
                    grade_levels=grade_levels,
                    currency=base_currency
                )
                
                # Apply grade-specific modifications
                if fee_multiplier != 1.0 or special_fees:
                    await self._customize_fee_structure(
                        UUID(result["fee_structure_id"]),
                        fee_multiplier,
                        special_fees
                    )
                
                result["grade_category"] = category
                result["affected_grades"] = grade_levels
                created_structures.append(result)
            
            logger.info(f"Created {len(created_structures)} grade-based fee structures for {academic_year}")
            
            return {
                "success": True,
                "academic_year": academic_year,
                "structures_created": len(created_structures),
                "fee_structures": created_structures
            }
            
        except Exception as e:
            logger.error(f"Error creating grade-based fee structures: {e}")
            raise
    
    async def _customize_fee_structure(
        self,
        fee_structure_id: UUID,
        fee_multiplier: float,
        special_fees: Dict[str, float]
    ) -> None:
        """Apply customizations to a fee structure"""
        
        # Get fee structure items
        items_result = await self.db.execute(
            select(FeeStructureItem).where(
                FeeStructureItem.fee_structure_id == fee_structure_id
            )
        )
        items = items_result.scalars().all()
        
        for item in items:
            # Apply multiplier to base fees
            if fee_multiplier != 1.0:
                item.amount = item.amount * Decimal(str(fee_multiplier))
            
            # Override with special fees if specified
            fee_key = item.fee_type.lower().replace("_", "").replace(" ", "")
            for special_key, special_amount in special_fees.items():
                if special_key.lower().replace("_", "").replace(" ", "") in fee_key:
                    item.amount = Decimal(str(special_amount))
                    break
        
        await self.db.commit()
    
    # =====================================================
    # CLASS-BASED BILLING INTEGRATION
    # =====================================================
    
    async def generate_class_invoices(
        self,
        class_id: UUID,
        term_number: int,
        academic_year: str,
        fee_structure_id: Optional[UUID] = None,
        due_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Generate invoices for all students in a specific class
        
        Args:
            class_id: The class/group identifier
            term_number: Zimbabwe term (1, 2, or 3)
            academic_year: Academic year
            fee_structure_id: Specific fee structure (auto-detect if None)
            due_date: Custom due date (auto-calculate if None)
        """
        
        try:
            # Get class information and enrolled students
            class_info = await self._get_class_students(class_id)
            
            if not class_info or not class_info.get("students"):
                raise ValueError(f"No students found in class {class_id}")
            
            students = class_info["students"]
            grade_level = class_info.get("grade_level")
            
            # Auto-detect fee structure if not provided
            if not fee_structure_id:
                fee_structure_id = await self._find_fee_structure_for_grade(
                    grade_level, academic_year
                )
            
            if not fee_structure_id:
                raise ValueError(f"No fee structure found for grade {grade_level}")
            
            # Generate invoices for all students in the class
            generated_invoices = []
            failed_students = []
            
            for student in students:
                try:
                    invoice_result = await self.finance_manager.generate_zimbabwe_invoice(
                        student_id=UUID(student["student_id"]),
                        fee_structure_id=fee_structure_id,
                        term_number=term_number,
                        academic_year=academic_year,
                        due_date=due_date
                    )
                    generated_invoices.append({
                        **invoice_result,
                        "student_name": student.get("name", "Unknown"),
                        "student_number": student.get("student_number")
                    })
                    
                except Exception as e:
                    failed_students.append({
                        "student_id": student["student_id"],
                        "student_name": student.get("name", "Unknown"),
                        "error": str(e)
                    })
                    logger.warning(f"Failed to generate invoice for student {student['student_id']}: {e}")
            
            # Create summary
            total_amount = sum(float(inv["total_amount"]) for inv in generated_invoices)
            
            logger.info(f"Generated {len(generated_invoices)} invoices for class {class_id}, term {term_number}")
            
            return {
                "success": True,
                "class_id": str(class_id),
                "term_number": term_number,
                "academic_year": academic_year,
                "summary": {
                    "total_students": len(students),
                    "invoices_generated": len(generated_invoices),
                    "failed_invoices": len(failed_students),
                    "total_invoiced_amount": total_amount,
                    "success_rate": len(generated_invoices) / len(students) * 100
                },
                "invoices": generated_invoices,
                "failed_students": failed_students
            }
            
        except Exception as e:
            logger.error(f"Error generating class invoices: {e}")
            raise
    
    async def _get_class_students(self, class_id: UUID) -> Dict[str, Any]:
        """Get class information and enrolled students"""
        
        # This would normally query the Academic module's database
        # For now, return mock data structure
        return {
            "class_id": str(class_id),
            "class_name": "Grade 8A",
            "grade_level": 8,
            "students": [
                {
                    "student_id": "550e8400-e29b-41d4-a716-446655440001",
                    "name": "Chipo Mazimba",
                    "student_number": "STU-2024-001"
                },
                {
                    "student_id": "550e8400-e29b-41d4-a716-446655440002", 
                    "name": "Tadiwa Ndlovu",
                    "student_number": "STU-2024-002"
                }
            ]
        }
    
    async def _find_fee_structure_for_grade(
        self,
        grade_level: int,
        academic_year: str
    ) -> Optional[UUID]:
        """Find appropriate fee structure for a grade level"""
        
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
    
    # =====================================================
    # ACADEMIC TERM INTEGRATION
    # =====================================================
    
    async def generate_term_invoices_by_grade(
        self,
        academic_year: str,
        term_number: int,
        grade_levels: List[int],
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Generate term invoices for specific grade levels
        Processes in batches for performance
        
        Args:
            academic_year: Academic year
            term_number: Zimbabwe term (1, 2, or 3)
            grade_levels: List of grade levels to process
            batch_size: Number of students to process per batch
        """
        
        try:
            total_processed = 0
            total_generated = 0
            total_failed = 0
            processing_summary = []
            
            for grade_level in grade_levels:
                # Get students for this grade level
                students = await self._get_students_by_grade(grade_level)
                
                if not students:
                    logger.info(f"No students found for grade {grade_level}")
                    continue
                
                # Find fee structure for this grade
                fee_structure_id = await self._find_fee_structure_for_grade(
                    grade_level, academic_year
                )
                
                if not fee_structure_id:
                    logger.warning(f"No fee structure found for grade {grade_level}")
                    continue
                
                # Process students in batches
                generated_count = 0
                failed_count = 0
                
                for i in range(0, len(students), batch_size):
                    batch = students[i:i + batch_size]
                    batch_results = await self._process_student_batch(
                        batch, fee_structure_id, term_number, academic_year
                    )
                    
                    generated_count += batch_results["generated"]
                    failed_count += batch_results["failed"]
                    total_processed += len(batch)
                
                total_generated += generated_count
                total_failed += failed_count
                
                processing_summary.append({
                    "grade_level": grade_level,
                    "students_found": len(students),
                    "invoices_generated": generated_count,
                    "invoices_failed": failed_count,
                    "success_rate": (generated_count / len(students) * 100) if students else 0
                })
                
                logger.info(f"Grade {grade_level}: {generated_count}/{len(students)} invoices generated")
            
            logger.info(f"Term invoice generation complete: {total_generated}/{total_processed} successful")
            
            return {
                "success": True,
                "academic_year": academic_year,
                "term_number": term_number,
                "summary": {
                    "grades_processed": len(grade_levels),
                    "total_students": total_processed,
                    "invoices_generated": total_generated,
                    "invoices_failed": total_failed,
                    "overall_success_rate": (total_generated / total_processed * 100) if total_processed > 0 else 0
                },
                "grade_breakdown": processing_summary
            }
            
        except Exception as e:
            logger.error(f"Error generating term invoices by grade: {e}")
            raise
    
    async def _get_students_by_grade(self, grade_level: int) -> List[Dict[str, Any]]:
        """Get all students for a specific grade level"""
        
        # This would normally query the SIS/Student module
        # For now, return mock data
        mock_students = []
        
        # Generate different numbers of students per grade for testing
        student_counts = {1: 25, 2: 23, 3: 27, 4: 24, 5: 26, 6: 22, 7: 28,
                         8: 30, 9: 32, 10: 35, 11: 33, 12: 28, 13: 25}
        
        count = student_counts.get(grade_level, 25)
        
        for i in range(count):
            mock_students.append({
                "student_id": f"550e8400-e29b-41d4-a716-{grade_level:02d}{i:08d}",
                "name": f"Student {i+1} Grade {grade_level}",
                "student_number": f"STU-{grade_level:02d}-{i+1:03d}",
                "grade_level": grade_level
            })
        
        return mock_students
    
    async def _process_student_batch(
        self,
        students: List[Dict[str, Any]],
        fee_structure_id: UUID,
        term_number: int,
        academic_year: str
    ) -> Dict[str, int]:
        """Process a batch of students for invoice generation"""
        
        generated = 0
        failed = 0
        
        for student in students:
            try:
                await self.finance_manager.generate_zimbabwe_invoice(
                    student_id=UUID(student["student_id"]),
                    fee_structure_id=fee_structure_id,
                    term_number=term_number,
                    academic_year=academic_year
                )
                generated += 1
                
            except Exception as e:
                failed += 1
                logger.debug(f"Failed to generate invoice for {student['student_id']}: {e}")
        
        return {"generated": generated, "failed": failed}
    
    # =====================================================
    # ACADEMIC CALENDAR INTEGRATION
    # =====================================================
    
    async def sync_with_academic_calendar(
        self,
        academic_year: str
    ) -> Dict[str, Any]:
        """
        Sync financial periods with academic calendar
        Creates financial periods that align with academic terms
        """
        
        try:
            # Get academic calendar for the year
            calendar_data = await self._get_academic_calendar(academic_year)
            
            created_periods = []
            
            for term_info in calendar_data["terms"]:
                # Create financial period for each term
                period = FinancialPeriod(
                    school_id=self.school_id,
                    period_name=f"Term {term_info['term_number']} {academic_year}",
                    academic_year=academic_year,
                    term_number=term_info["term_number"],
                    start_date=term_info["start_date"],
                    end_date=term_info["end_date"],
                    invoice_due_date=term_info.get("fee_due_date"),
                    late_fee_start_date=term_info.get("fee_due_date") + timedelta(days=14),
                    is_active=True
                )
                
                self.db.add(period)
                created_periods.append({
                    "term_number": term_info["term_number"],
                    "start_date": term_info["start_date"].isoformat(),
                    "end_date": term_info["end_date"].isoformat(),
                    "due_date": term_info.get("fee_due_date").isoformat() if term_info.get("fee_due_date") else None
                })
            
            await self.db.commit()
            
            logger.info(f"Synced financial periods with academic calendar for {academic_year}")
            
            return {
                "success": True,
                "academic_year": academic_year,
                "periods_created": len(created_periods),
                "financial_periods": created_periods
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error syncing with academic calendar: {e}")
            raise
    
    async def _get_academic_calendar(self, academic_year: str) -> Dict[str, Any]:
        """Get academic calendar data"""
        
        # This would normally query the Academic module
        # For now, return Zimbabwe's typical academic calendar
        year = int(academic_year)
        
        return {
            "academic_year": academic_year,
            "terms": [
                {
                    "term_number": 1,
                    "start_date": date(year, 1, 15),
                    "end_date": date(year, 4, 15),
                    "fee_due_date": date(year, 2, 15)
                },
                {
                    "term_number": 2,
                    "start_date": date(year, 5, 1),
                    "end_date": date(year, 8, 15),
                    "fee_due_date": date(year, 6, 15)
                },
                {
                    "term_number": 3,
                    "start_date": date(year, 9, 1),
                    "end_date": date(year, 12, 15),
                    "fee_due_date": date(year, 10, 15)
                }
            ]
        }
    
    # =====================================================
    # REPORTING AND ANALYTICS
    # =====================================================
    
    async def generate_academic_finance_report(
        self,
        academic_year: str,
        include_class_breakdown: bool = True,
        include_grade_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive finance report with academic context
        
        Args:
            academic_year: Academic year to report on
            include_class_breakdown: Include per-class financial data
            include_grade_analysis: Include grade-level analysis
        """
        
        try:
            # Get base financial report
            base_report = await self.finance_manager.generate_zimbabwe_financial_report(
                academic_year=academic_year
            )
            
            # Add academic context
            academic_data = {}
            
            if include_grade_analysis:
                academic_data["grade_analysis"] = await self._analyze_by_grade(academic_year)
            
            if include_class_breakdown:
                academic_data["class_breakdown"] = await self._analyze_by_class(academic_year)
            
            # Add term progression analysis
            academic_data["term_progression"] = await self._analyze_term_progression(academic_year)
            
            # Combine reports
            comprehensive_report = {
                **base_report,
                "academic_integration": academic_data,
                "report_type": "comprehensive_academic_finance",
                "generated_by": "finance_academic_integration"
            }
            
            logger.info(f"Generated comprehensive academic finance report for {academic_year}")
            
            return comprehensive_report
            
        except Exception as e:
            logger.error(f"Error generating academic finance report: {e}")
            raise
    
    async def _analyze_by_grade(self, academic_year: str) -> Dict[str, Any]:
        """Analyze financial performance by grade level"""
        
        # Mock analysis - would normally query actual data
        return {
            "primary_grades": {
                "grades": "1-7",
                "total_students": 185,
                "total_invoiced": 55500.00,
                "total_collected": 47175.00,
                "collection_rate": 85.0,
                "average_per_student": 300.00
            },
            "o_level_grades": {
                "grades": "8-11", 
                "total_students": 130,
                "total_invoiced": 78000.00,
                "total_collected": 62400.00,
                "collection_rate": 80.0,
                "average_per_student": 600.00
            },
            "a_level_grades": {
                "grades": "12-13",
                "total_students": 53,
                "total_invoiced": 42400.00,
                "total_collected": 38160.00,
                "collection_rate": 90.0,
                "average_per_student": 800.00
            }
        }
    
    async def _analyze_by_class(self, academic_year: str) -> List[Dict[str, Any]]:
        """Analyze financial performance by class"""
        
        # Mock analysis - would normally query actual class data
        return [
            {
                "class_name": "Grade 8A",
                "grade_level": 8,
                "student_count": 32,
                "total_invoiced": 19200.00,
                "total_collected": 15360.00,
                "collection_rate": 80.0,
                "outstanding_amount": 3840.00
            },
            {
                "class_name": "Grade 10B",
                "grade_level": 10,
                "student_count": 28,
                "total_invoiced": 16800.00,
                "total_collected": 14280.00,
                "collection_rate": 85.0,
                "outstanding_amount": 2520.00
            }
        ]
    
    async def _analyze_term_progression(self, academic_year: str) -> Dict[str, Any]:
        """Analyze collection patterns across terms"""
        
        return {
            "term_1": {
                "invoices_generated": 368,
                "amount_invoiced": 110400.00,
                "amount_collected": 93840.00,
                "collection_rate": 85.0,
                "days_to_collect_avg": 18
            },
            "term_2": {
                "invoices_generated": 368,
                "amount_invoiced": 110400.00,
                "amount_collected": 88320.00,
                "collection_rate": 80.0,
                "days_to_collect_avg": 22
            },
            "term_3": {
                "invoices_generated": 368,
                "amount_invoiced": 110400.00,
                "amount_collected": 98856.00,
                "collection_rate": 89.5,
                "days_to_collect_avg": 15,
                "note": "Higher collection rate due to year-end parent meetings"
            }
        }