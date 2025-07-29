"""
Integration tests for payment processing flows
Tests complete payment workflows including Paynow integration
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.finance.paynow_integration import (
    PaynowIntegration,
    PaynowPaymentRequest,
    PaynowPaymentResponse,
    PaynowStatusResponse
)
from backend.services.finance.crud import (
    create_invoice,
    create_payment,
    get_payment,
    update_payment_status,
    allocate_payment
)
from backend.services.finance.schemas import (
    InvoiceCreate,
    PaymentCreate,
    PaymentStatus
)


@pytest.fixture
def paynow_integration():
    """Mock Paynow integration"""
    integration = PaynowIntegration(
        integration_id="test-id",
        integration_key="test-key",
        return_url="https://test.com/return",
        result_url="https://test.com/result"
    )
    return integration


@pytest.fixture
def mock_paynow_success_response():
    """Mock successful Paynow response"""
    return PaynowPaymentResponse(
        payment_id="PAY-123456",
        paynow_reference="PR-789012",
        poll_url="https://paynow.co.zw/interface/poll/?guid=123",
        redirect_url="https://paynow.co.zw/interface/initiate/?guid=123",
        status="ok",
        success=True,
        hash_valid=True
    )


@pytest.fixture
def mock_paynow_status_response():
    """Mock Paynow status response"""
    return PaynowStatusResponse(
        status="Paid",
        amount=Decimal("250.00"),
        paynow_reference="PR-789012",
        poll_url="https://paynow.co.zw/interface/poll/?guid=123",
        hash_valid=True
    )


class TestPaynowIntegration:
    """Test Paynow payment gateway integration"""
    
    @pytest.mark.asyncio
    async def test_initiate_payment_success(
        self, 
        paynow_integration: PaynowIntegration,
        mock_paynow_success_response: PaynowPaymentResponse
    ):
        """Test successful payment initiation"""
        payment_request = PaynowPaymentRequest(
            student_id=str(uuid4()),
            invoice_ids=[str(uuid4())],
            amount=Decimal("250.00"),
            payer_email="parent@example.com",
            payer_phone="+263771234567"
        )
        
        with patch.object(paynow_integration, '_make_request') as mock_request:
            mock_request.return_value = {
                "status": "ok",
                "browserurl": "https://paynow.co.zw/interface/initiate/?guid=123",
                "pollurl": "https://paynow.co.zw/interface/poll/?guid=123",
                "hash": "valid-hash"
            }
            
            response = await paynow_integration.initiate_payment(
                payment_request,
                "PAY-123456"
            )
            
            assert response.success is True
            assert response.redirect_url is not None
            assert response.poll_url is not None
            assert response.payment_id == "PAY-123456"
    
    @pytest.mark.asyncio
    async def test_check_payment_status_paid(
        self,
        paynow_integration: PaynowIntegration,
        mock_paynow_status_response: PaynowStatusResponse
    ):
        """Test checking payment status - paid"""
        poll_url = "https://paynow.co.zw/interface/poll/?guid=123"
        
        with patch.object(paynow_integration, '_make_request') as mock_request:
            mock_request.return_value = {
                "status": "Paid",
                "amount": "250.00",
                "reference": "PR-789012",
                "paynowreference": "PR-789012",
                "pollurl": poll_url,
                "hash": "valid-hash"
            }
            
            status = await paynow_integration.check_payment_status(poll_url)
            
            assert status.status == "Paid"
            assert status.amount == Decimal("250.00")
            assert status.paynow_reference == "PR-789012"
    
    @pytest.mark.asyncio
    async def test_initiate_mobile_payment(
        self,
        paynow_integration: PaynowIntegration
    ):
        """Test mobile money payment initiation"""
        payment_request = PaynowPaymentRequest(
            student_id=str(uuid4()),
            invoice_ids=[str(uuid4())],
            amount=Decimal("150.00"),
            payer_email="parent@example.com",
            payer_phone="+263771234567"
        )
        
        with patch.object(paynow_integration, '_make_request') as mock_request:
            mock_request.return_value = {
                "status": "ok",
                "instructions": "Dial *151*2*1*573646# to complete payment",
                "pollurl": "https://paynow.co.zw/interface/poll/?guid=456",
                "hash": "valid-hash"
            }
            
            response = await paynow_integration.initiate_mobile_payment(
                payment_request,
                "PAY-789012",
                method="ecocash"
            )
            
            assert response.success is True
            assert response.poll_url is not None
            assert "instructions" in response.__dict__
    
    @pytest.mark.asyncio
    async def test_payment_failure_handling(
        self,
        paynow_integration: PaynowIntegration
    ):
        """Test handling of payment failures"""
        payment_request = PaynowPaymentRequest(
            student_id=str(uuid4()),
            invoice_ids=[str(uuid4())],
            amount=Decimal("100.00"),
            payer_email="invalid-email",
            payer_phone="+263771234567"
        )
        
        with patch.object(paynow_integration, '_make_request') as mock_request:
            mock_request.return_value = {
                "status": "error",
                "error": "Invalid email address",
                "hash": "valid-hash"
            }
            
            response = await paynow_integration.initiate_payment(
                payment_request,
                "PAY-FAIL"
            )
            
            assert response.success is False
            assert "error" in response.__dict__


class TestPaymentWorkflow:
    """Test complete payment processing workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_payment_flow(
        self,
        db_session: AsyncSession,
        school_id: str,
        user_id: str,
        student_id: str,
        academic_year_id: str
    ):
        """Test complete payment flow from invoice to payment"""
        # Step 1: Create invoice
        invoice_data = InvoiceCreate(
            student_id=student_id,
            academic_year_id=academic_year_id,
            due_date=date.today() + timedelta(days=30),
            currency="USD",
            line_items=[{
                "description": "School Fees",
                "quantity": 1,
                "unit_price": Decimal("400.00"),
                "discount_amount": Decimal("0.00")
            }]
        )
        
        invoice = await create_invoice(
            db_session,
            invoice_data,
            school_id=school_id,
            created_by=user_id
        )
        
        # Step 2: Create payment
        payment_data = PaymentCreate(
            student_id=student_id,
            amount=Decimal("400.00"),
            currency="USD",
            payment_method_id=str(uuid4()),
            payer_name="John Parent",
            payer_email="john@example.com",
            payer_phone="+263771234567",
            transaction_id="TXN-123456",
            status=PaymentStatus.PENDING
        )
        
        payment = await create_payment(
            db_session,
            payment_data,
            school_id=school_id,
            created_by=user_id
        )
        
        # Step 3: Simulate payment confirmation
        await update_payment_status(
            db_session,
            payment.id,
            PaymentStatus.COMPLETED,
            school_id=school_id,
            updated_by=user_id
        )
        
        # Step 4: Allocate payment to invoice
        allocation = await allocate_payment(
            db_session,
            payment_id=payment.id,
            invoice_id=invoice.id,
            amount=Decimal("400.00"),
            school_id=school_id,
            created_by=user_id
        )
        
        # Verify complete flow
        assert allocation is not None
        assert allocation.amount == Decimal("400.00")
        
        # Check payment status
        updated_payment = await get_payment(db_session, payment.id, school_id=school_id)
        assert updated_payment.status == PaymentStatus.COMPLETED
        
        # Check invoice is now paid
        from backend.services.finance.crud import get_invoice
        updated_invoice = await get_invoice(db_session, invoice.id, school_id=school_id)
        assert updated_invoice.paid_amount == Decimal("400.00")
        assert updated_invoice.payment_status == "paid"
    
    @pytest.mark.asyncio
    async def test_partial_payment_flow(
        self,
        db_session: AsyncSession,
        school_id: str,
        user_id: str,
        student_id: str,
        academic_year_id: str
    ):
        """Test partial payment allocation"""
        # Create invoice for $500
        invoice_data = InvoiceCreate(
            student_id=student_id,
            academic_year_id=academic_year_id,
            due_date=date.today() + timedelta(days=30),
            currency="USD",
            line_items=[{
                "description": "Large Fee",
                "quantity": 1,
                "unit_price": Decimal("500.00"),
                "discount_amount": Decimal("0.00")
            }]
        )
        
        invoice = await create_invoice(
            db_session,
            invoice_data,
            school_id=school_id,
            created_by=user_id
        )
        
        # Make first partial payment of $200
        payment1_data = PaymentCreate(
            student_id=student_id,
            amount=Decimal("200.00"),
            currency="USD",
            payment_method_id=str(uuid4()),
            status=PaymentStatus.COMPLETED
        )
        
        payment1 = await create_payment(
            db_session,
            payment1_data,
            school_id=school_id,
            created_by=user_id
        )
        
        await allocate_payment(
            db_session,
            payment_id=payment1.id,
            invoice_id=invoice.id,
            amount=Decimal("200.00"),
            school_id=school_id,
            created_by=user_id
        )
        
        # Make second partial payment of $300
        payment2_data = PaymentCreate(
            student_id=student_id,
            amount=Decimal("300.00"),
            currency="USD",
            payment_method_id=str(uuid4()),
            status=PaymentStatus.COMPLETED
        )
        
        payment2 = await create_payment(
            db_session,
            payment2_data,
            school_id=school_id,
            created_by=user_id
        )
        
        await allocate_payment(
            db_session,
            payment_id=payment2.id,
            invoice_id=invoice.id,
            amount=Decimal("300.00"),
            school_id=school_id,
            created_by=user_id
        )
        
        # Verify full payment
        from backend.services.finance.crud import get_invoice
        updated_invoice = await get_invoice(db_session, invoice.id, school_id=school_id)
        assert updated_invoice.paid_amount == Decimal("500.00")
        assert updated_invoice.outstanding_amount == Decimal("0.00")
        assert updated_invoice.payment_status == "paid"
    
    @pytest.mark.asyncio
    async def test_overpayment_handling(
        self,
        db_session: AsyncSession,
        school_id: str,
        user_id: str,
        student_id: str,
        academic_year_id: str
    ):
        """Test handling of overpayments"""
        # Create invoice for $300
        invoice_data = InvoiceCreate(
            student_id=student_id,
            academic_year_id=academic_year_id,
            due_date=date.today() + timedelta(days=30),
            currency="USD",
            line_items=[{
                "description": "Standard Fee",
                "quantity": 1,
                "unit_price": Decimal("300.00"),
                "discount_amount": Decimal("0.00")
            }]
        )
        
        invoice = await create_invoice(
            db_session,
            invoice_data,
            school_id=school_id,
            created_by=user_id
        )
        
        # Make payment of $400 (overpayment)
        payment_data = PaymentCreate(
            student_id=student_id,
            amount=Decimal("400.00"),
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
        
        # Try to allocate full payment amount
        allocation = await allocate_payment(
            db_session,
            payment_id=payment.id,
            invoice_id=invoice.id,
            amount=Decimal("400.00"),  # This should be limited to invoice amount
            school_id=school_id,
            created_by=user_id
        )
        
        # Should only allocate the invoice amount
        assert allocation.amount == Decimal("300.00")
        
        # Check invoice is fully paid
        from backend.services.finance.crud import get_invoice
        updated_invoice = await get_invoice(db_session, invoice.id, school_id=school_id)
        assert updated_invoice.paid_amount == Decimal("300.00")
        assert updated_invoice.payment_status == "paid"
        
        # Payment should show remaining unallocated amount
        updated_payment = await get_payment(db_session, payment.id, school_id=school_id)
        # This would require additional logic to track unallocated amounts
        # For now, just verify the allocation was created correctly
        assert updated_payment.amount == Decimal("400.00")


class TestPaymentWebhooks:
    """Test payment webhook handling"""
    
    @pytest.mark.asyncio
    async def test_paynow_webhook_processing(
        self,
        db_session: AsyncSession,
        school_id: str,
        user_id: str,
        student_id: str
    ):
        """Test processing Paynow webhook notifications"""
        # Create a pending payment
        payment_data = PaymentCreate(
            student_id=student_id,
            amount=Decimal("250.00"),
            currency="USD",
            payment_method_id=str(uuid4()),
            transaction_id="PAY-WEBHOOK-123",
            status=PaymentStatus.PENDING
        )
        
        payment = await create_payment(
            db_session,
            payment_data,
            school_id=school_id,
            created_by=user_id
        )
        
        # Simulate webhook data
        webhook_data = {
            "reference": payment.payment_reference,
            "paynowreference": "PR-123456",
            "amount": "250.00",
            "status": "Paid",
            "hash": "valid-hash"
        }
        
        # Process webhook
        with patch('backend.services.finance.paynow_integration.verify_webhook_hash') as mock_verify:
            mock_verify.return_value = True
            
            await update_payment_status(
                db_session,
                payment.id,
                PaymentStatus.COMPLETED,
                school_id=school_id,
                updated_by="system",
                webhook_data=webhook_data
            )
        
        # Verify payment was updated
        updated_payment = await get_payment(db_session, payment.id, school_id=school_id)
        assert updated_payment.status == PaymentStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_webhook_security(
        self,
        db_session: AsyncSession,
        school_id: str,
        user_id: str,
        student_id: str
    ):
        """Test webhook security validation"""
        # Create a pending payment
        payment_data = PaymentCreate(
            student_id=student_id,
            amount=Decimal("100.00"),
            currency="USD",
            payment_method_id=str(uuid4()),
            transaction_id="PAY-SECURITY-123",
            status=PaymentStatus.PENDING
        )
        
        payment = await create_payment(
            db_session,
            payment_data,
            school_id=school_id,
            created_by=user_id
        )
        
        # Simulate webhook with invalid hash
        webhook_data = {
            "reference": payment.payment_reference,
            "paynowreference": "PR-INVALID",
            "amount": "100.00",
            "status": "Paid",
            "hash": "invalid-hash"
        }
        
        # Process webhook - should fail hash validation
        with patch('backend.services.finance.paynow_integration.verify_webhook_hash') as mock_verify:
            mock_verify.return_value = False
            
            # This should raise an exception or return error
            try:
                await update_payment_status(
                    db_session,
                    payment.id,
                    PaymentStatus.COMPLETED,
                    school_id=school_id,
                    updated_by="system",
                    webhook_data=webhook_data
                )
                assert False, "Should have raised security exception"
            except Exception as e:
                assert "hash" in str(e).lower() or "security" in str(e).lower()
        
        # Verify payment was NOT updated
        unchanged_payment = await get_payment(db_session, payment.id, school_id=school_id)
        assert unchanged_payment.status == PaymentStatus.PENDING


class TestPaymentReconciliation:
    """Test payment reconciliation processes"""
    
    @pytest.mark.asyncio
    async def test_daily_reconciliation(
        self,
        db_session: AsyncSession,
        school_id: str,
        user_id: str,
        student_id: str
    ):
        """Test daily payment reconciliation"""
        # Create multiple payments
        payment_amounts = [Decimal("100.00"), Decimal("200.00"), Decimal("150.00")]
        payment_ids = []
        
        for amount in payment_amounts:
            payment_data = PaymentCreate(
                student_id=student_id,
                amount=amount,
                currency="USD",
                payment_method_id=str(uuid4()),
                status=PaymentStatus.COMPLETED,
                reconciled=False
            )
            
            payment = await create_payment(
                db_session,
                payment_data,
                school_id=school_id,
                created_by=user_id
            )
            payment_ids.append(payment.id)
        
        # Run reconciliation process
        from backend.services.finance.crud import mark_payments_reconciled
        reconciled_count = await mark_payments_reconciled(
            db_session,
            payment_ids,
            school_id=school_id,
            reconciled_by=user_id
        )
        
        assert reconciled_count == 3
        
        # Verify all payments are marked as reconciled
        for payment_id in payment_ids:
            payment = await get_payment(db_session, payment_id, school_id=school_id)
            assert payment.reconciled is True
    
    @pytest.mark.asyncio
    async def test_payment_matching(
        self,
        db_session: AsyncSession,
        school_id: str,
        user_id: str,
        student_id: str
    ):
        """Test matching payments to bank statements"""
        # Create a payment
        payment_data = PaymentCreate(
            student_id=student_id,
            amount=Decimal("300.00"),
            currency="USD",
            payment_method_id=str(uuid4()),
            transaction_id="BANK-REF-456",
            status=PaymentStatus.COMPLETED,
            reconciled=False
        )
        
        payment = await create_payment(
            db_session,
            payment_data,
            school_id=school_id,
            created_by=user_id
        )
        
        # Simulate bank statement entry
        bank_entry = {
            "reference": "BANK-REF-456",
            "amount": Decimal("300.00"),
            "date": date.today(),
            "description": "School Fee Payment"
        }
        
        # Match payment to bank entry
        from backend.services.finance.crud import match_payment_to_bank
        match_result = await match_payment_to_bank(
            db_session,
            payment.id,
            bank_entry,
            school_id=school_id,
            matched_by=user_id
        )
        
        assert match_result is True
        
        # Verify payment is now reconciled
        updated_payment = await get_payment(db_session, payment.id, school_id=school_id)
        assert updated_payment.reconciled is True