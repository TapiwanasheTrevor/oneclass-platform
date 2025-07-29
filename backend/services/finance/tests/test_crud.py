"""
Unit tests for Finance CRUD operations
Tests database operations for fee structures, invoices, and payments
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.services.finance.crud import (
    create_fee_category,
    get_fee_category,
    get_fee_categories,
    update_fee_category,
    delete_fee_category,
    create_fee_structure,
    get_fee_structure,
    get_fee_structures,
    create_fee_item,
    get_fee_items,
    create_invoice,
    get_invoice,
    get_invoices,
    create_payment,
    get_payment,
    get_payments,
    allocate_payment
)
from backend.services.finance.schemas import (
    FeeCategoryCreate,
    FeeStructureCreate,
    FeeItemCreate,
    InvoiceCreate,
    PaymentCreate,
    PaymentStatus,
    FeeFrequency
)


@pytest.fixture
def school_id():
    """Test school ID"""
    return str(uuid4())


@pytest.fixture
def user_id():
    """Test user ID"""
    return str(uuid4())


@pytest.fixture
def academic_year_id():
    """Test academic year ID"""
    return str(uuid4())


@pytest.fixture
def student_id():
    """Test student ID"""
    return str(uuid4())


class TestFeeCategoryCRUD:
    """Test fee category CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_fee_category(self, db_session: AsyncSession, school_id: str, user_id: str):
        """Test creating a fee category"""
        category_data = FeeCategoryCreate(
            name="Tuition Fees",
            code="TUITION",
            description="Regular tuition fees",
            is_mandatory=True,
            is_refundable=False,
            allows_partial_payment=True,
            display_order=1
        )
        
        category = await create_fee_category(
            db_session, 
            category_data, 
            school_id=school_id,
            created_by=user_id
        )
        
        assert category.id is not None
        assert category.name == "Tuition Fees"
        assert category.code == "TUITION"
        assert category.is_mandatory is True
        assert category.school_id == school_id
    
    @pytest.mark.asyncio
    async def test_get_fee_category(self, db_session: AsyncSession, school_id: str, user_id: str):
        """Test retrieving a fee category"""
        # Create category
        category_data = FeeCategoryCreate(
            name="Sports Fees",
            code="SPORTS",
            is_mandatory=False
        )
        created = await create_fee_category(
            db_session, 
            category_data, 
            school_id=school_id,
            created_by=user_id
        )
        
        # Retrieve category
        retrieved = await get_fee_category(db_session, created.id, school_id=school_id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Sports Fees"
        assert retrieved.code == "SPORTS"
    
    @pytest.mark.asyncio
    async def test_get_fee_categories(self, db_session: AsyncSession, school_id: str, user_id: str):
        """Test retrieving multiple fee categories"""
        # Create multiple categories
        categories = []
        for i in range(3):
            category_data = FeeCategoryCreate(
                name=f"Category {i}",
                code=f"CAT{i}",
                display_order=i
            )
            category = await create_fee_category(
                db_session, 
                category_data, 
                school_id=school_id,
                created_by=user_id
            )
            categories.append(category)
        
        # Retrieve all categories
        retrieved = await get_fee_categories(db_session, school_id=school_id)
        
        assert len(retrieved) == 3
        assert all(cat.school_id == school_id for cat in retrieved)
        # Check ordering
        assert retrieved[0].display_order < retrieved[1].display_order
    
    @pytest.mark.asyncio
    async def test_update_fee_category(self, db_session: AsyncSession, school_id: str, user_id: str):
        """Test updating a fee category"""
        # Create category
        category_data = FeeCategoryCreate(
            name="Old Name",
            code="OLD",
            is_mandatory=True
        )
        category = await create_fee_category(
            db_session, 
            category_data, 
            school_id=school_id,
            created_by=user_id
        )
        
        # Update category
        update_data = {"name": "New Name", "is_mandatory": False}
        updated = await update_fee_category(
            db_session, 
            category.id, 
            update_data,
            school_id=school_id,
            updated_by=user_id
        )
        
        assert updated.name == "New Name"
        assert updated.is_mandatory is False
        assert updated.code == "OLD"  # Unchanged
    
    @pytest.mark.asyncio
    async def test_delete_fee_category(self, db_session: AsyncSession, school_id: str, user_id: str):
        """Test deleting a fee category"""
        # Create category
        category_data = FeeCategoryCreate(
            name="To Delete",
            code="DELETE"
        )
        category = await create_fee_category(
            db_session, 
            category_data, 
            school_id=school_id,
            created_by=user_id
        )
        
        # Delete category
        success = await delete_fee_category(
            db_session, 
            category.id, 
            school_id=school_id
        )
        
        assert success is True
        
        # Verify deletion
        retrieved = await get_fee_category(db_session, category.id, school_id=school_id)
        assert retrieved is None


class TestFeeStructureCRUD:
    """Test fee structure CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_fee_structure(
        self, 
        db_session: AsyncSession, 
        school_id: str, 
        user_id: str,
        academic_year_id: str
    ):
        """Test creating a fee structure"""
        structure_data = FeeStructureCreate(
            name="Grade 1 Fee Structure",
            description="Fee structure for Grade 1 students",
            academic_year_id=academic_year_id,
            grade_levels=[1],
            is_default=True,
            applicable_from=date.today(),
            status="active"
        )
        
        structure = await create_fee_structure(
            db_session,
            structure_data,
            school_id=school_id,
            created_by=user_id
        )
        
        assert structure.id is not None
        assert structure.name == "Grade 1 Fee Structure"
        assert structure.academic_year_id == academic_year_id
        assert 1 in structure.grade_levels
        assert structure.is_default is True
        assert structure.status == "active"
    
    @pytest.mark.asyncio
    async def test_get_fee_structures_by_grade(
        self, 
        db_session: AsyncSession, 
        school_id: str, 
        user_id: str,
        academic_year_id: str
    ):
        """Test retrieving fee structures by grade level"""
        # Create structures for different grades
        for grade in [1, 2, 3]:
            structure_data = FeeStructureCreate(
                name=f"Grade {grade} Structure",
                academic_year_id=academic_year_id,
                grade_levels=[grade],
                applicable_from=date.today(),
                status="active"
            )
            await create_fee_structure(
                db_session,
                structure_data,
                school_id=school_id,
                created_by=user_id
            )
        
        # Get structures for grade 2
        structures = await get_fee_structures(
            db_session,
            school_id=school_id,
            academic_year_id=academic_year_id,
            grade_level=2
        )
        
        assert len(structures) == 1
        assert structures[0].name == "Grade 2 Structure"
        assert 2 in structures[0].grade_levels


class TestFeeItemCRUD:
    """Test fee item CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_fee_item(
        self, 
        db_session: AsyncSession, 
        school_id: str, 
        user_id: str,
        academic_year_id: str
    ):
        """Test creating fee items"""
        # First create a fee category and structure
        category_data = FeeCategoryCreate(
            name="Tuition",
            code="TUITION"
        )
        category = await create_fee_category(
            db_session, 
            category_data, 
            school_id=school_id,
            created_by=user_id
        )
        
        structure_data = FeeStructureCreate(
            name="Test Structure",
            academic_year_id=academic_year_id,
            grade_levels=[1],
            applicable_from=date.today()
        )
        structure = await create_fee_structure(
            db_session,
            structure_data,
            school_id=school_id,
            created_by=user_id
        )
        
        # Create fee item
        item_data = FeeItemCreate(
            fee_structure_id=structure.id,
            fee_category_id=category.id,
            name="Term 1 Tuition",
            description="Tuition fees for Term 1",
            base_amount=Decimal("500.00"),
            currency="USD",
            frequency=FeeFrequency.TERM,
            allows_installments=True,
            max_installments=3,
            late_fee_amount=Decimal("10.00")
        )
        
        item = await create_fee_item(
            db_session,
            item_data,
            school_id=school_id,
            created_by=user_id
        )
        
        assert item.id is not None
        assert item.name == "Term 1 Tuition"
        assert item.base_amount == Decimal("500.00")
        assert item.frequency == FeeFrequency.TERM
        assert item.allows_installments is True
        assert item.max_installments == 3


class TestInvoiceCRUD:
    """Test invoice CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_invoice(
        self,
        db_session: AsyncSession,
        school_id: str,
        user_id: str,
        student_id: str,
        academic_year_id: str
    ):
        """Test creating an invoice"""
        invoice_data = InvoiceCreate(
            student_id=student_id,
            academic_year_id=academic_year_id,
            due_date=date.today() + timedelta(days=30),
            currency="USD",
            line_items=[
                {
                    "description": "Tuition Fees",
                    "quantity": 1,
                    "unit_price": Decimal("500.00"),
                    "discount_amount": Decimal("0.00")
                },
                {
                    "description": "Sports Fees",
                    "quantity": 1,
                    "unit_price": Decimal("50.00"),
                    "discount_amount": Decimal("5.00")
                }
            ]
        )
        
        invoice = await create_invoice(
            db_session,
            invoice_data,
            school_id=school_id,
            created_by=user_id
        )
        
        assert invoice.id is not None
        assert invoice.student_id == student_id
        assert invoice.invoice_number is not None
        assert invoice.subtotal == Decimal("550.00")
        assert invoice.discount_amount == Decimal("5.00")
        assert invoice.total_amount == Decimal("545.00")
        assert invoice.payment_status == "pending"
        assert len(invoice.line_items) == 2
    
    @pytest.mark.asyncio
    async def test_get_invoices_by_status(
        self,
        db_session: AsyncSession,
        school_id: str,
        user_id: str,
        student_id: str,
        academic_year_id: str
    ):
        """Test filtering invoices by payment status"""
        # Create invoices with different statuses
        statuses = ["pending", "paid", "overdue"]
        for status in statuses:
            invoice_data = InvoiceCreate(
                student_id=student_id,
                academic_year_id=academic_year_id,
                due_date=date.today() + timedelta(days=30),
                currency="USD",
                payment_status=status,
                line_items=[{
                    "description": f"{status} Invoice",
                    "quantity": 1,
                    "unit_price": Decimal("100.00")
                }]
            )
            await create_invoice(
                db_session,
                invoice_data,
                school_id=school_id,
                created_by=user_id
            )
        
        # Get only pending invoices
        pending_invoices = await get_invoices(
            db_session,
            school_id=school_id,
            payment_status="pending"
        )
        
        assert len(pending_invoices) == 1
        assert pending_invoices[0].payment_status == "pending"


class TestPaymentCRUD:
    """Test payment CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_payment(
        self,
        db_session: AsyncSession,
        school_id: str,
        user_id: str,
        student_id: str
    ):
        """Test creating a payment"""
        payment_data = PaymentCreate(
            student_id=student_id,
            amount=Decimal("545.00"),
            currency="USD",
            payment_method_id=str(uuid4()),
            payer_name="John Parent",
            payer_email="john@example.com",
            payer_phone="+263771234567",
            transaction_id="PAY123456",
            notes="Payment for Term 1 fees"
        )
        
        payment = await create_payment(
            db_session,
            payment_data,
            school_id=school_id,
            created_by=user_id
        )
        
        assert payment.id is not None
        assert payment.payment_reference is not None
        assert payment.student_id == student_id
        assert payment.amount == Decimal("545.00")
        assert payment.status == PaymentStatus.PENDING
        assert payment.payer_phone == "+263771234567"
    
    @pytest.mark.asyncio
    async def test_allocate_payment_to_invoice(
        self,
        db_session: AsyncSession,
        school_id: str,
        user_id: str,
        student_id: str,
        academic_year_id: str
    ):
        """Test allocating a payment to an invoice"""
        # Create an invoice
        invoice_data = InvoiceCreate(
            student_id=student_id,
            academic_year_id=academic_year_id,
            due_date=date.today() + timedelta(days=30),
            currency="USD",
            line_items=[{
                "description": "Test Fee",
                "quantity": 1,
                "unit_price": Decimal("200.00")
            }]
        )
        invoice = await create_invoice(
            db_session,
            invoice_data,
            school_id=school_id,
            created_by=user_id
        )
        
        # Create a payment
        payment_data = PaymentCreate(
            student_id=student_id,
            amount=Decimal("200.00"),
            currency="USD",
            payment_method_id=str(uuid4()),
            status=PaymentStatus.COMPLETED
        )
        payment = await create_payment(
            db_session,
            payment_data,
            school_id=school_id,
            created_by=user_id
        )
        
        # Allocate payment to invoice
        allocation = await allocate_payment(
            db_session,
            payment_id=payment.id,
            invoice_id=invoice.id,
            amount=Decimal("200.00"),
            school_id=school_id,
            created_by=user_id
        )
        
        assert allocation is not None
        assert allocation.payment_id == payment.id
        assert allocation.invoice_id == invoice.id
        assert allocation.amount == Decimal("200.00")
        
        # Check invoice is now paid
        updated_invoice = await get_invoice(db_session, invoice.id, school_id=school_id)
        assert updated_invoice.paid_amount == Decimal("200.00")
        assert updated_invoice.payment_status == "paid"
    
    @pytest.mark.asyncio
    async def test_partial_payment_allocation(
        self,
        db_session: AsyncSession,
        school_id: str,
        user_id: str,
        student_id: str,
        academic_year_id: str
    ):
        """Test partial payment allocation"""
        # Create an invoice for 500
        invoice_data = InvoiceCreate(
            student_id=student_id,
            academic_year_id=academic_year_id,
            due_date=date.today() + timedelta(days=30),
            currency="USD",
            line_items=[{
                "description": "Large Fee",
                "quantity": 1,
                "unit_price": Decimal("500.00")
            }]
        )
        invoice = await create_invoice(
            db_session,
            invoice_data,
            school_id=school_id,
            created_by=user_id
        )
        
        # Create a partial payment of 200
        payment_data = PaymentCreate(
            student_id=student_id,
            amount=Decimal("200.00"),
            currency="USD",
            payment_method_id=str(uuid4()),
            status=PaymentStatus.COMPLETED
        )
        payment = await create_payment(
            db_session,
            payment_data,
            school_id=school_id,
            created_by=user_id
        )
        
        # Allocate payment
        await allocate_payment(
            db_session,
            payment_id=payment.id,
            invoice_id=invoice.id,
            amount=Decimal("200.00"),
            school_id=school_id,
            created_by=user_id
        )
        
        # Check invoice is partially paid
        updated_invoice = await get_invoice(db_session, invoice.id, school_id=school_id)
        assert updated_invoice.paid_amount == Decimal("200.00")
        assert updated_invoice.outstanding_amount == Decimal("300.00")
        assert updated_invoice.payment_status == "partial"


@pytest.mark.asyncio
async def test_multitenancy_isolation(
    db_session: AsyncSession,
    user_id: str
):
    """Test that data is properly isolated between schools"""
    school1_id = str(uuid4())
    school2_id = str(uuid4())
    
    # Create categories for different schools
    category1_data = FeeCategoryCreate(
        name="School 1 Category",
        code="S1CAT"
    )
    category1 = await create_fee_category(
        db_session,
        category1_data,
        school_id=school1_id,
        created_by=user_id
    )
    
    category2_data = FeeCategoryCreate(
        name="School 2 Category",
        code="S2CAT"
    )
    category2 = await create_fee_category(
        db_session,
        category2_data,
        school_id=school2_id,
        created_by=user_id
    )
    
    # Try to access school1's category with school2's ID
    retrieved = await get_fee_category(
        db_session,
        category1.id,
        school_id=school2_id
    )
    assert retrieved is None  # Should not be accessible
    
    # Each school should only see their own categories
    school1_categories = await get_fee_categories(db_session, school_id=school1_id)
    school2_categories = await get_fee_categories(db_session, school_id=school2_id)
    
    assert len(school1_categories) == 1
    assert len(school2_categories) == 1
    assert school1_categories[0].name == "School 1 Category"
    assert school2_categories[0].name == "School 2 Category"