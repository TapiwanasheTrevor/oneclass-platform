# =====================================================
# Finance Module - CRUD Operations
# File: backend/services/finance/crud.py
# =====================================================

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
import asyncpg
from fastapi import HTTPException
import logging

from shared.auth import EnhancedUser
from shared.database import get_database_connection
from .schemas import (
    FeeCategoryCreate, FeeCategoryUpdate, FeeCategoryResponse,
    FeeStructureCreate, FeeStructureUpdate, FeeStructureResponse,
    FeeItemCreate, FeeItemUpdate, FeeItemResponse,
    StudentFeeAssignmentCreate, StudentFeeAssignmentUpdate, StudentFeeAssignmentResponse,
    InvoiceCreate, InvoiceUpdate, InvoiceResponse,
    PaymentMethodCreate, PaymentMethodUpdate, PaymentMethodResponse,
    PaymentCreate, PaymentUpdate, PaymentResponse,
    PaymentAllocationCreate, PaymentAllocationResponse,
    BulkInvoiceGenerationRequest, BulkInvoiceGenerationResponse,
    FinancialSummaryResponse, FinanceDashboardResponse,
    InvoiceSearchFilters, PaymentSearchFilters
)

logger = logging.getLogger(__name__)

# =====================================================
# FEE CATEGORY CRUD
# =====================================================

class FeeCategoryCRUD:
    """CRUD operations for fee categories"""
    
    @staticmethod
    async def create_fee_category(category_data: FeeCategoryCreate, current_user: EnhancedUser) -> FeeCategoryResponse:
        """Create a new fee category"""
        try:
            async with get_database_connection() as conn:
                # Check if category code already exists
                existing = await conn.fetchrow(
                    "SELECT id FROM finance.fee_categories WHERE school_id = $1 AND code = $2",
                    current_user.school_id, category_data.code
                )
                if existing:
                    raise HTTPException(status_code=400, detail="Category code already exists")
                
                # Create category
                query = """
                    INSERT INTO finance.fee_categories 
                    (school_id, name, description, code, is_mandatory, is_refundable, 
                     allows_partial_payment, display_order, is_active, created_by)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING *
                """
                row = await conn.fetchrow(
                    query,
                    current_user.school_id,
                    category_data.name,
                    category_data.description,
                    category_data.code,
                    category_data.is_mandatory,
                    category_data.is_refundable,
                    category_data.allows_partial_payment,
                    category_data.display_order,
                    category_data.is_active,
                    current_user.id
                )
                
                logger.info(f"Created fee category {category_data.name} for school {current_user.school_id}")
                return FeeCategoryResponse(**dict(row))
                
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Category name or code already exists")
        except Exception as e:
            logger.error(f"Error creating fee category: {e}")
            raise HTTPException(status_code=500, detail="Failed to create fee category")
    
    @staticmethod
    async def get_fee_categories(school_id: UUID, active_only: bool = True) -> List[FeeCategoryResponse]:
        """Get all fee categories for a school"""
        try:
            async with get_database_connection() as conn:
                query = """
                    SELECT * FROM finance.fee_categories 
                    WHERE school_id = $1
                """
                params = [school_id]
                
                if active_only:
                    query += " AND is_active = TRUE"
                
                query += " ORDER BY display_order, name"
                
                rows = await conn.fetch(query, *params)
                return [FeeCategoryResponse(**dict(row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Error fetching fee categories: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch fee categories")
    
    @staticmethod
    async def get_fee_category_by_id(category_id: UUID, school_id: UUID) -> Optional[FeeCategoryResponse]:
        """Get fee category by ID"""
        try:
            async with get_database_connection() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM finance.fee_categories WHERE id = $1 AND school_id = $2",
                    category_id, school_id
                )
                return FeeCategoryResponse(**dict(row)) if row else None
                
        except Exception as e:
            logger.error(f"Error fetching fee category: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch fee category")
    
    @staticmethod
    async def update_fee_category(category_id: UUID, category_data: FeeCategoryUpdate, school_id: UUID) -> FeeCategoryResponse:
        """Update fee category"""
        try:
            async with get_database_connection() as conn:
                # Build update query dynamically
                update_fields = []
                params = []
                param_count = 1
                
                for field, value in category_data.dict(exclude_unset=True).items():
                    if value is not None:
                        update_fields.append(f"{field} = ${param_count}")
                        params.append(value)
                        param_count += 1
                
                if not update_fields:
                    raise HTTPException(status_code=400, detail="No fields to update")
                
                update_fields.append("updated_at = NOW()")
                
                query = f"""
                    UPDATE finance.fee_categories 
                    SET {', '.join(update_fields)}
                    WHERE id = ${param_count} AND school_id = ${param_count + 1}
                    RETURNING *
                """
                params.extend([category_id, school_id])
                
                row = await conn.fetchrow(query, *params)
                if not row:
                    raise HTTPException(status_code=404, detail="Fee category not found")
                
                logger.info(f"Updated fee category {category_id} for school {school_id}")
                return FeeCategoryResponse(**dict(row))
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating fee category: {e}")
            raise HTTPException(status_code=500, detail="Failed to update fee category")
    
    @staticmethod
    async def delete_fee_category(category_id: UUID, school_id: UUID) -> bool:
        """Delete (deactivate) fee category"""
        try:
            async with get_database_connection() as conn:
                # Check if category is in use
                usage_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM finance.fee_items WHERE fee_category_id = $1",
                    category_id
                )
                
                if usage_count > 0:
                    # Deactivate instead of delete
                    await conn.execute(
                        "UPDATE finance.fee_categories SET is_active = FALSE, updated_at = NOW() WHERE id = $1 AND school_id = $2",
                        category_id, school_id
                    )
                    logger.info(f"Deactivated fee category {category_id} (in use)")
                else:
                    # Safe to delete
                    result = await conn.execute(
                        "DELETE FROM finance.fee_categories WHERE id = $1 AND school_id = $2",
                        category_id, school_id
                    )
                    if result == "DELETE 0":
                        raise HTTPException(status_code=404, detail="Fee category not found")
                    logger.info(f"Deleted fee category {category_id}")
                
                return True
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting fee category: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete fee category")

# =====================================================
# FEE STRUCTURE CRUD
# =====================================================

class FeeStructureCRUD:
    """CRUD operations for fee structures"""
    
    @staticmethod
    async def create_fee_structure(structure_data: FeeStructureCreate, current_user: EnhancedUser) -> FeeStructureResponse:
        """Create a new fee structure"""
        try:
            async with get_database_connection() as conn:
                # Check if structure name already exists for this year
                existing = await conn.fetchrow(
                    "SELECT id FROM finance.fee_structures WHERE school_id = $1 AND name = $2 AND academic_year_id = $3",
                    current_user.school_id, structure_data.name, structure_data.academic_year_id
                )
                if existing:
                    raise HTTPException(status_code=400, detail="Fee structure name already exists for this academic year")
                
                # Create structure
                query = """
                    INSERT INTO finance.fee_structures 
                    (school_id, name, description, academic_year_id, grade_levels, class_ids, 
                     is_default, applicable_from, applicable_to, status, created_by)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    RETURNING *
                """
                row = await conn.fetchrow(
                    query,
                    current_user.school_id,
                    structure_data.name,
                    structure_data.description,
                    structure_data.academic_year_id,
                    structure_data.grade_levels,
                    structure_data.class_ids,
                    structure_data.is_default,
                    structure_data.applicable_from,
                    structure_data.applicable_to,
                    structure_data.status,
                    current_user.id
                )
                
                logger.info(f"Created fee structure {structure_data.name} for school {current_user.school_id}")
                return FeeStructureResponse(**dict(row))
                
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Fee structure name already exists")
        except Exception as e:
            logger.error(f"Error creating fee structure: {e}")
            raise HTTPException(status_code=500, detail="Failed to create fee structure")
    
    @staticmethod
    async def get_fee_structures(school_id: UUID, academic_year_id: Optional[UUID] = None, 
                               status: Optional[str] = None) -> List[FeeStructureResponse]:
        """Get fee structures for a school"""
        try:
            async with get_database_connection() as conn:
                query = """
                    SELECT * FROM finance.fee_structures 
                    WHERE school_id = $1
                """
                params = [school_id]
                param_count = 2
                
                if academic_year_id:
                    query += f" AND academic_year_id = ${param_count}"
                    params.append(academic_year_id)
                    param_count += 1
                
                if status:
                    query += f" AND status = ${param_count}"
                    params.append(status)
                
                query += " ORDER BY created_at DESC"
                
                rows = await conn.fetch(query, *params)
                return [FeeStructureResponse(**dict(row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Error fetching fee structures: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch fee structures")
    
    @staticmethod
    async def get_fee_structure_by_id(structure_id: UUID, school_id: UUID) -> Optional[FeeStructureResponse]:
        """Get fee structure by ID"""
        try:
            async with get_database_connection() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM finance.fee_structures WHERE id = $1 AND school_id = $2",
                    structure_id, school_id
                )
                return FeeStructureResponse(**dict(row)) if row else None
                
        except Exception as e:
            logger.error(f"Error fetching fee structure: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch fee structure")
    
    @staticmethod
    async def get_fee_structure_with_items(structure_id: UUID, school_id: UUID) -> Dict[str, Any]:
        """Get fee structure with all its items"""
        try:
            async with get_database_connection() as conn:
                # Get structure
                structure_row = await conn.fetchrow(
                    "SELECT * FROM finance.fee_structures WHERE id = $1 AND school_id = $2",
                    structure_id, school_id
                )
                if not structure_row:
                    return None
                
                # Get items
                items_query = """
                    SELECT fi.*, fc.name as category_name, fc.code as category_code
                    FROM finance.fee_items fi
                    JOIN finance.fee_categories fc ON fi.fee_category_id = fc.id
                    WHERE fi.fee_structure_id = $1
                    ORDER BY fc.display_order, fi.name
                """
                items_rows = await conn.fetch(items_query, structure_id)
                
                structure = FeeStructureResponse(**dict(structure_row))
                items = [FeeItemResponse(**dict(row)) for row in items_rows]
                
                return {
                    "structure": structure,
                    "items": items,
                    "total_amount": sum(item.base_amount for item in items)
                }
                
        except Exception as e:
            logger.error(f"Error fetching fee structure with items: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch fee structure details")

# =====================================================
# INVOICE CRUD
# =====================================================

class InvoiceCRUD:
    """CRUD operations for invoices"""
    
    @staticmethod
    async def create_invoice(invoice_data: InvoiceCreate, current_user: EnhancedUser) -> InvoiceResponse:
        """Create a new invoice"""
        try:
            async with get_database_connection() as conn:
                async with conn.transaction():
                    # Get fee structure details
                    structure_query = """
                        SELECT fs.*, array_agg(
                            json_build_object(
                                'id', fi.id,
                                'name', fi.name,
                                'base_amount', fi.base_amount,
                                'currency', fi.currency,
                                'fee_category_id', fi.fee_category_id,
                                'category_name', fc.name
                            )
                        ) as items
                        FROM finance.fee_structures fs
                        JOIN finance.fee_items fi ON fs.id = fi.fee_structure_id
                        JOIN finance.fee_categories fc ON fi.fee_category_id = fc.id
                        WHERE fs.id = $1 AND fs.school_id = $2
                        GROUP BY fs.id
                    """
                    structure_row = await conn.fetchrow(structure_query, invoice_data.fee_structure_id, current_user.school_id)
                    if not structure_row:
                        raise HTTPException(status_code=404, detail="Fee structure not found")
                    
                    # Check if student has this fee structure assigned
                    assignment_check = await conn.fetchrow(
                        "SELECT id FROM finance.student_fee_assignments WHERE student_id = $1 AND fee_structure_id = $2 AND status = 'active'",
                        invoice_data.student_id, invoice_data.fee_structure_id
                    )
                    if not assignment_check:
                        raise HTTPException(status_code=400, detail="Student not assigned to this fee structure")
                    
                    # Calculate invoice totals
                    subtotal = sum(Decimal(str(item['base_amount'])) for item in structure_row['items'])
                    discount_amount = Decimal('0.00')  # Apply discounts if any
                    tax_amount = Decimal('0.00')  # Apply taxes if any
                    total_amount = subtotal - discount_amount + tax_amount
                    
                    # Create invoice
                    invoice_query = """
                        INSERT INTO finance.invoices 
                        (school_id, student_id, due_date, academic_year_id, term_id, 
                         subtotal, discount_amount, tax_amount, total_amount, outstanding_amount,
                         currency, exchange_rate, notes, created_by)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                        RETURNING *
                    """
                    invoice_row = await conn.fetchrow(
                        invoice_query,
                        current_user.school_id,
                        invoice_data.student_id,
                        invoice_data.due_date,
                        invoice_data.academic_year_id,
                        invoice_data.term_id,
                        subtotal,
                        discount_amount,
                        tax_amount,
                        total_amount,
                        total_amount,  # outstanding_amount initially equals total_amount
                        invoice_data.currency,
                        invoice_data.exchange_rate,
                        invoice_data.notes,
                        current_user.id
                    )
                    
                    # Create invoice line items
                    for item in structure_row['items']:
                        await conn.execute(
                            """
                            INSERT INTO finance.invoice_line_items 
                            (invoice_id, fee_item_id, description, quantity, unit_price, line_total)
                            VALUES ($1, $2, $3, $4, $5, $6)
                            """,
                            invoice_row['id'],
                            item['id'],
                            item['name'],
                            Decimal('1.00'),
                            Decimal(str(item['base_amount'])),
                            Decimal(str(item['base_amount']))
                        )
                    
                    logger.info(f"Created invoice {invoice_row['invoice_number']} for student {invoice_data.student_id}")
                    return InvoiceResponse(**dict(invoice_row))
                    
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating invoice: {e}")
            raise HTTPException(status_code=500, detail="Failed to create invoice")
    
    @staticmethod
    async def get_invoices(school_id: UUID, filters: Optional[InvoiceSearchFilters] = None, 
                          page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get invoices with filtering and pagination"""
        try:
            async with get_database_connection() as conn:
                # Build query
                base_query = """
                    FROM finance.invoices i
                    JOIN sis.students s ON i.student_id = s.id
                    WHERE i.school_id = $1
                """
                params = [school_id]
                param_count = 2
                
                # Apply filters
                if filters:
                    if filters.student_id:
                        base_query += f" AND i.student_id = ${param_count}"
                        params.append(filters.student_id)
                        param_count += 1
                    
                    if filters.grade_level:
                        base_query += f" AND s.current_grade_level = ${param_count}"
                        params.append(filters.grade_level)
                        param_count += 1
                    
                    if filters.payment_status:
                        base_query += f" AND i.payment_status = ${param_count}"
                        params.append(filters.payment_status)
                        param_count += 1
                    
                    if filters.due_date_from:
                        base_query += f" AND i.due_date >= ${param_count}"
                        params.append(filters.due_date_from)
                        param_count += 1
                    
                    if filters.due_date_to:
                        base_query += f" AND i.due_date <= ${param_count}"
                        params.append(filters.due_date_to)
                        param_count += 1
                
                # Get total count
                count_query = f"SELECT COUNT(*) {base_query}"
                total_count = await conn.fetchval(count_query, *params)
                
                # Get paginated results
                offset = (page - 1) * page_size
                data_query = f"""
                    SELECT i.*, s.first_name, s.last_name, s.student_number
                    {base_query}
                    ORDER BY i.created_at DESC
                    LIMIT ${param_count} OFFSET ${param_count + 1}
                """
                params.extend([page_size, offset])
                
                rows = await conn.fetch(data_query, *params)
                invoices = [InvoiceResponse(**dict(row)) for row in rows]
                
                return {
                    "invoices": invoices,
                    "total_count": total_count,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total_count + page_size - 1) // page_size,
                    "has_next": page * page_size < total_count,
                    "has_previous": page > 1
                }
                
        except Exception as e:
            logger.error(f"Error fetching invoices: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch invoices")
    
    @staticmethod
    async def bulk_generate_invoices(request: BulkInvoiceGenerationRequest, current_user: EnhancedUser) -> BulkInvoiceGenerationResponse:
        """Generate invoices in bulk"""
        try:
            async with get_database_connection() as conn:
                async with conn.transaction():
                    # Get fee structure
                    structure_query = """
                        SELECT fs.*, array_agg(
                            json_build_object(
                                'id', fi.id,
                                'name', fi.name,
                                'base_amount', fi.base_amount,
                                'currency', fi.currency,
                                'fee_category_id', fi.fee_category_id
                            )
                        ) as items
                        FROM finance.fee_structures fs
                        JOIN finance.fee_items fi ON fs.id = fi.fee_structure_id
                        WHERE fs.id = $1 AND fs.school_id = $2
                        GROUP BY fs.id
                    """
                    structure_row = await conn.fetchrow(structure_query, request.fee_structure_id, current_user.school_id)
                    if not structure_row:
                        raise HTTPException(status_code=404, detail="Fee structure not found")
                    
                    # Get eligible students
                    students_query = """
                        SELECT DISTINCT s.id, s.first_name, s.last_name, s.student_number
                        FROM sis.students s
                        JOIN finance.student_fee_assignments sfa ON s.id = sfa.student_id
                        WHERE s.school_id = $1 AND sfa.fee_structure_id = $2 AND sfa.status = 'active'
                    """
                    params = [current_user.school_id, request.fee_structure_id]
                    param_count = 3
                    
                    # Apply student selection criteria
                    if request.student_ids:
                        students_query += f" AND s.id = ANY(${param_count})"
                        params.append(request.student_ids)
                        param_count += 1
                    
                    if request.grade_levels:
                        students_query += f" AND s.current_grade_level = ANY(${param_count})"
                        params.append(request.grade_levels)
                        param_count += 1
                    
                    if request.class_ids:
                        students_query += f" AND s.current_class_id = ANY(${param_count})"
                        params.append(request.class_ids)
                    
                    students = await conn.fetch(students_query, *params)
                    
                    if not students:
                        raise HTTPException(status_code=400, detail="No eligible students found")
                    
                    # Generate invoices
                    invoices_generated = []
                    failed_students = []
                    total_amount = Decimal('0.00')
                    
                    for student in students:
                        try:
                            # Check if invoice already exists
                            existing_invoice = await conn.fetchrow(
                                """
                                SELECT id FROM finance.invoices 
                                WHERE student_id = $1 AND academic_year_id = $2 
                                AND term_id = $3 AND status != 'cancelled'
                                """,
                                student['id'], request.academic_year_id, request.term_id
                            )
                            
                            if existing_invoice:
                                failed_students.append({
                                    "student_id": str(student['id']),
                                    "student_name": f"{student['first_name']} {student['last_name']}",
                                    "reason": "Invoice already exists"
                                })
                                continue
                            
                            # Calculate totals
                            subtotal = sum(Decimal(str(item['base_amount'])) for item in structure_row['items'])
                            invoice_total = subtotal
                            total_amount += invoice_total
                            
                            # Create invoice
                            invoice_row = await conn.fetchrow(
                                """
                                INSERT INTO finance.invoices 
                                (school_id, student_id, due_date, academic_year_id, term_id, 
                                 subtotal, total_amount, outstanding_amount, created_by)
                                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                                RETURNING id
                                """,
                                current_user.school_id,
                                student['id'],
                                request.due_date,
                                request.academic_year_id,
                                request.term_id,
                                subtotal,
                                invoice_total,
                                invoice_total,
                                current_user.id
                            )
                            
                            # Create line items
                            for item in structure_row['items']:
                                await conn.execute(
                                    """
                                    INSERT INTO finance.invoice_line_items 
                                    (invoice_id, fee_item_id, description, quantity, unit_price, line_total)
                                    VALUES ($1, $2, $3, $4, $5, $6)
                                    """,
                                    invoice_row['id'],
                                    item['id'],
                                    item['name'],
                                    Decimal('1.00'),
                                    Decimal(str(item['base_amount'])),
                                    Decimal(str(item['base_amount']))
                                )
                            
                            invoices_generated.append(invoice_row['id'])
                            
                        except Exception as e:
                            logger.error(f"Error generating invoice for student {student['id']}: {e}")
                            failed_students.append({
                                "student_id": str(student['id']),
                                "student_name": f"{student['first_name']} {student['last_name']}",
                                "reason": str(e)
                            })
                    
                    logger.info(f"Generated {len(invoices_generated)} invoices for school {current_user.school_id}")
                    
                    return BulkInvoiceGenerationResponse(
                        total_invoices_generated=len(invoices_generated),
                        total_students_processed=len(students),
                        total_amount=total_amount,
                        failed_students=failed_students,
                        invoice_ids=invoices_generated
                    )
                    
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in bulk invoice generation: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate invoices")

# =====================================================
# PAYMENT CRUD
# =====================================================

class PaymentCRUD:
    """CRUD operations for payments"""
    
    @staticmethod
    async def create_payment(payment_data: PaymentCreate, current_user: EnhancedUser) -> PaymentResponse:
        """Create a new payment"""
        try:
            async with get_database_connection() as conn:
                # Create payment
                query = """
                    INSERT INTO finance.payments 
                    (school_id, student_id, amount, currency, exchange_rate, payment_method_id,
                     transaction_id, gateway_reference, payer_name, payer_email, payer_phone, 
                     notes, created_by)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    RETURNING *
                """
                row = await conn.fetchrow(
                    query,
                    current_user.school_id,
                    payment_data.student_id,
                    payment_data.amount,
                    payment_data.currency,
                    payment_data.exchange_rate,
                    payment_data.payment_method_id,
                    payment_data.transaction_id,
                    payment_data.gateway_reference,
                    payment_data.payer_name,
                    payment_data.payer_email,
                    payment_data.payer_phone,
                    payment_data.notes,
                    current_user.id
                )
                
                logger.info(f"Created payment {row['payment_reference']} for student {payment_data.student_id}")
                return PaymentResponse(**dict(row))
                
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            raise HTTPException(status_code=500, detail="Failed to create payment")
    
    @staticmethod
    async def get_payments(school_id: UUID, filters: Optional[PaymentSearchFilters] = None,
                          page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get payments with filtering and pagination"""
        try:
            async with get_database_connection() as conn:
                # Build query
                base_query = """
                    FROM finance.payments p
                    JOIN sis.students s ON p.student_id = s.id
                    JOIN finance.payment_methods pm ON p.payment_method_id = pm.id
                    WHERE p.school_id = $1
                """
                params = [school_id]
                param_count = 2
                
                # Apply filters
                if filters:
                    if filters.student_id:
                        base_query += f" AND p.student_id = ${param_count}"
                        params.append(filters.student_id)
                        param_count += 1
                    
                    if filters.status:
                        base_query += f" AND p.status = ${param_count}"
                        params.append(filters.status)
                        param_count += 1
                    
                    if filters.payment_method_id:
                        base_query += f" AND p.payment_method_id = ${param_count}"
                        params.append(filters.payment_method_id)
                        param_count += 1
                    
                    if filters.payment_date_from:
                        base_query += f" AND p.payment_date >= ${param_count}"
                        params.append(filters.payment_date_from)
                        param_count += 1
                    
                    if filters.payment_date_to:
                        base_query += f" AND p.payment_date <= ${param_count}"
                        params.append(filters.payment_date_to)
                        param_count += 1
                
                # Get total count
                count_query = f"SELECT COUNT(*) {base_query}"
                total_count = await conn.fetchval(count_query, *params)
                
                # Get paginated results
                offset = (page - 1) * page_size
                data_query = f"""
                    SELECT p.*, s.first_name, s.last_name, s.student_number, pm.name as payment_method_name
                    {base_query}
                    ORDER BY p.created_at DESC
                    LIMIT ${param_count} OFFSET ${param_count + 1}
                """
                params.extend([page_size, offset])
                
                rows = await conn.fetch(data_query, *params)
                payments = [PaymentResponse(**dict(row)) for row in rows]
                
                return {
                    "payments": payments,
                    "total_count": total_count,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total_count + page_size - 1) // page_size,
                    "has_next": page * page_size < total_count,
                    "has_previous": page > 1
                }
                
        except Exception as e:
            logger.error(f"Error fetching payments: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch payments")
    
    @staticmethod
    async def allocate_payment_to_invoices(payment_id: UUID, invoice_ids: List[UUID], 
                                         current_user: EnhancedUser) -> List[PaymentAllocationResponse]:
        """Allocate payment to invoices"""
        try:
            async with get_database_connection() as conn:
                async with conn.transaction():
                    # Get payment details
                    payment = await conn.fetchrow(
                        "SELECT * FROM finance.payments WHERE id = $1 AND school_id = $2 AND status = 'completed'",
                        payment_id, current_user.school_id
                    )
                    if not payment:
                        raise HTTPException(status_code=404, detail="Payment not found or not completed")
                    
                    # Get invoices
                    invoices = await conn.fetch(
                        """
                        SELECT * FROM finance.invoices 
                        WHERE id = ANY($1) AND school_id = $2 AND outstanding_amount > 0
                        ORDER BY due_date ASC
                        """,
                        invoice_ids, current_user.school_id
                    )
                    
                    if not invoices:
                        raise HTTPException(status_code=404, detail="No eligible invoices found")
                    
                    # Check if payment is already allocated
                    existing_allocations = await conn.fetchval(
                        "SELECT COALESCE(SUM(allocated_amount), 0) FROM finance.payment_allocations WHERE payment_id = $1",
                        payment_id
                    )
                    
                    available_amount = payment['amount'] - existing_allocations
                    if available_amount <= 0:
                        raise HTTPException(status_code=400, detail="Payment already fully allocated")
                    
                    # Allocate payment
                    allocations = []
                    remaining_amount = available_amount
                    
                    for invoice in invoices:
                        if remaining_amount <= 0:
                            break
                        
                        allocation_amount = min(remaining_amount, invoice['outstanding_amount'])
                        
                        # Create allocation
                        allocation_row = await conn.fetchrow(
                            """
                            INSERT INTO finance.payment_allocations (payment_id, invoice_id, allocated_amount)
                            VALUES ($1, $2, $3)
                            RETURNING *
                            """,
                            payment_id, invoice['id'], allocation_amount
                        )
                        
                        allocations.append(PaymentAllocationResponse(**dict(allocation_row)))
                        remaining_amount -= allocation_amount
                    
                    logger.info(f"Allocated payment {payment_id} to {len(allocations)} invoices")
                    return allocations
                    
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error allocating payment: {e}")
            raise HTTPException(status_code=500, detail="Failed to allocate payment")

# =====================================================
# FINANCIAL REPORTING
# =====================================================

class FinancialReportingCRUD:
    """CRUD operations for financial reporting"""
    
    @staticmethod
    async def get_finance_dashboard(school_id: UUID, academic_year_id: UUID) -> FinanceDashboardResponse:
        """Get finance dashboard data"""
        try:
            async with get_database_connection() as conn:
                # Current academic year summary
                year_summary = await conn.fetchrow(
                    """
                    SELECT 
                        COALESCE(SUM(total_amount), 0) as year_invoiced,
                        COALESCE(SUM(paid_amount), 0) as year_collected,
                        COALESCE(SUM(outstanding_amount), 0) as year_outstanding,
                        CASE 
                            WHEN SUM(total_amount) > 0 THEN (SUM(paid_amount) / SUM(total_amount)) * 100
                            ELSE 0
                        END as year_collection_rate
                    FROM finance.invoices 
                    WHERE school_id = $1 AND academic_year_id = $2
                    """,
                    school_id, academic_year_id
                )
                
                # Recent payments
                recent_payments = await conn.fetch(
                    """
                    SELECT p.*, s.first_name, s.last_name, pm.name as payment_method_name
                    FROM finance.payments p
                    JOIN sis.students s ON p.student_id = s.id
                    JOIN finance.payment_methods pm ON p.payment_method_id = pm.id
                    WHERE p.school_id = $1 AND p.status = 'completed'
                    ORDER BY p.created_at DESC
                    LIMIT 10
                    """,
                    school_id
                )
                
                # Counts
                overdue_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM finance.invoices WHERE school_id = $1 AND payment_status = 'overdue'",
                    school_id
                )
                
                pending_payments_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM finance.payments WHERE school_id = $1 AND status = 'pending'",
                    school_id
                )
                
                return FinanceDashboardResponse(
                    school_id=school_id,
                    academic_year_id=academic_year_id,
                    current_term_invoiced=year_summary['year_invoiced'],
                    current_term_collected=year_summary['year_collected'],
                    current_term_outstanding=year_summary['year_outstanding'],
                    current_term_collection_rate=year_summary['year_collection_rate'],
                    year_to_date_invoiced=year_summary['year_invoiced'],
                    year_to_date_collected=year_summary['year_collected'],
                    year_to_date_outstanding=year_summary['year_outstanding'],
                    year_to_date_collection_rate=year_summary['year_collection_rate'],
                    recent_payments=[PaymentResponse(**dict(row)) for row in recent_payments],
                    overdue_invoices_count=overdue_count,
                    pending_payments_count=pending_payments_count,
                    monthly_collection_trend=[],  # TODO: Implement trend data
                    payment_method_breakdown=[],  # TODO: Implement breakdown
                    fee_category_breakdown=[]     # TODO: Implement breakdown
                )
                
        except Exception as e:
            logger.error(f"Error fetching finance dashboard: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch finance dashboard")