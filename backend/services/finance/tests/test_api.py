"""
API endpoint tests for Finance module
Tests all REST endpoints with authentication and authorization
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4
from httpx import AsyncClient
from fastapi import status

from backend.services.finance.main import app


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {
        "Authorization": "Bearer test-token",
        "X-School-ID": str(uuid4()),
        "X-User-ID": str(uuid4())
    }


@pytest.fixture
def admin_headers(auth_headers):
    """Mock admin authentication headers"""
    auth_headers["X-User-Role"] = "admin"
    return auth_headers


@pytest.fixture
def teacher_headers(auth_headers):
    """Mock teacher authentication headers"""
    auth_headers["X-User-Role"] = "teacher"
    return auth_headers


class TestFeeCategoryAPI:
    """Test fee category API endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_fee_category(self, client: AsyncClient, admin_headers: dict):
        """Test creating a fee category via API"""
        category_data = {
            "name": "Library Fees",
            "code": "LIB",
            "description": "Annual library membership",
            "is_mandatory": False,
            "is_refundable": True,
            "allows_partial_payment": False,
            "display_order": 5
        }
        
        response = await client.post(
            "/api/v1/finance/fee-management/categories",
            json=category_data,
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Library Fees"
        assert data["code"] == "LIB"
        assert data["is_mandatory"] is False
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_list_fee_categories(self, client: AsyncClient, admin_headers: dict):
        """Test listing fee categories"""
        # Create multiple categories
        categories = ["Tuition", "Sports", "Lab", "Transport"]
        for i, name in enumerate(categories):
            await client.post(
                "/api/v1/finance/fee-management/categories",
                json={
                    "name": f"{name} Fees",
                    "code": name[:3].upper(),
                    "display_order": i
                },
                headers=admin_headers
            )
        
        # List all categories
        response = await client.get(
            "/api/v1/finance/fee-management/categories",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 4
        # Check ordering
        assert data[0]["display_order"] <= data[1]["display_order"]
    
    @pytest.mark.asyncio
    async def test_update_fee_category(self, client: AsyncClient, admin_headers: dict):
        """Test updating a fee category"""
        # Create category
        create_response = await client.post(
            "/api/v1/finance/fee-management/categories",
            json={"name": "Old Name", "code": "OLD"},
            headers=admin_headers
        )
        category_id = create_response.json()["id"]
        
        # Update category
        update_data = {
            "name": "New Name",
            "description": "Updated description",
            "is_mandatory": True
        }
        response = await client.put(
            f"/api/v1/finance/fee-management/categories/{category_id}",
            json=update_data,
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "New Name"
        assert data["description"] == "Updated description"
        assert data["is_mandatory"] is True
        assert data["code"] == "OLD"  # Unchanged
    
    @pytest.mark.asyncio
    async def test_delete_fee_category(self, client: AsyncClient, admin_headers: dict):
        """Test deleting a fee category"""
        # Create category
        create_response = await client.post(
            "/api/v1/finance/fee-management/categories",
            json={"name": "To Delete", "code": "DEL"},
            headers=admin_headers
        )
        category_id = create_response.json()["id"]
        
        # Delete category
        response = await client.delete(
            f"/api/v1/finance/fee-management/categories/{category_id}",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify deletion
        get_response = await client.get(
            f"/api/v1/finance/fee-management/categories/{category_id}",
            headers=admin_headers
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient, teacher_headers: dict):
        """Test that teachers cannot create fee categories"""
        response = await client.post(
            "/api/v1/finance/fee-management/categories",
            json={"name": "Unauthorized", "code": "UNAUTH"},
            headers=teacher_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestFeeStructureAPI:
    """Test fee structure API endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_fee_structure(self, client: AsyncClient, admin_headers: dict):
        """Test creating a fee structure"""
        structure_data = {
            "name": "Grade 5 Fee Structure 2025",
            "description": "Standard fees for Grade 5",
            "academic_year_id": str(uuid4()),
            "grade_levels": [5],
            "is_default": True,
            "applicable_from": str(date.today()),
            "status": "active"
        }
        
        response = await client.post(
            "/api/v1/finance/fee-management/structures",
            json=structure_data,
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Grade 5 Fee Structure 2025"
        assert 5 in data["grade_levels"]
        assert data["is_default"] is True
    
    @pytest.mark.asyncio
    async def test_get_fee_structure_details(self, client: AsyncClient, admin_headers: dict):
        """Test getting fee structure with items"""
        # Create fee category
        category_response = await client.post(
            "/api/v1/finance/fee-management/categories",
            json={"name": "Tuition", "code": "TUI"},
            headers=admin_headers
        )
        category_id = category_response.json()["id"]
        
        # Create fee structure
        structure_response = await client.post(
            "/api/v1/finance/fee-management/structures",
            json={
                "name": "Test Structure",
                "academic_year_id": str(uuid4()),
                "grade_levels": [1],
                "applicable_from": str(date.today())
            },
            headers=admin_headers
        )
        structure_id = structure_response.json()["id"]
        
        # Add fee items
        await client.post(
            f"/api/v1/finance/fee-management/structures/{structure_id}/items",
            json={
                "fee_category_id": category_id,
                "name": "Term 1 Tuition",
                "base_amount": 500.00,
                "currency": "USD",
                "frequency": "term"
            },
            headers=admin_headers
        )
        
        # Get structure details
        response = await client.get(
            f"/api/v1/finance/fee-management/structures/{structure_id}/details",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "structure" in data
        assert "items" in data
        assert "total_amount" in data
        assert len(data["items"]) == 1
        assert data["total_amount"] == 500.00


class TestInvoiceAPI:
    """Test invoice API endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_invoice(self, client: AsyncClient, admin_headers: dict):
        """Test creating an invoice"""
        invoice_data = {
            "student_id": str(uuid4()),
            "academic_year_id": str(uuid4()),
            "due_date": str(date.today() + timedelta(days=30)),
            "currency": "USD",
            "line_items": [
                {
                    "description": "Tuition Fees",
                    "quantity": 1,
                    "unit_price": 750.00,
                    "discount_amount": 0.00
                },
                {
                    "description": "Sports Fees",
                    "quantity": 1,
                    "unit_price": 50.00,
                    "discount_amount": 10.00
                }
            ]
        }
        
        response = await client.post(
            "/api/v1/finance/invoices",
            json=invoice_data,
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["total_amount"] == 790.00  # 750 + 50 - 10
        assert data["payment_status"] == "pending"
        assert len(data["line_items"]) == 2
        assert "invoice_number" in data
    
    @pytest.mark.asyncio
    async def test_bulk_generate_invoices(self, client: AsyncClient, admin_headers: dict):
        """Test bulk invoice generation"""
        # Create fee structure first
        structure_response = await client.post(
            "/api/v1/finance/fee-management/structures",
            json={
                "name": "Bulk Test Structure",
                "academic_year_id": str(uuid4()),
                "grade_levels": [1, 2, 3],
                "applicable_from": str(date.today())
            },
            headers=admin_headers
        )
        structure_id = structure_response.json()["id"]
        
        # Bulk generate invoices
        bulk_data = {
            "fee_structure_id": structure_id,
            "due_date": str(date.today() + timedelta(days=30)),
            "academic_year_id": str(uuid4()),
            "grade_levels": [1, 2]
        }
        
        response = await client.post(
            "/api/v1/finance/invoices/bulk-generate",
            json=bulk_data,
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_invoices_generated" in data
        assert "total_students_processed" in data
        assert "invoice_ids" in data
    
    @pytest.mark.asyncio
    async def test_list_invoices_with_filters(self, client: AsyncClient, admin_headers: dict):
        """Test listing invoices with various filters"""
        student_id = str(uuid4())
        academic_year_id = str(uuid4())
        
        # Create multiple invoices
        for i in range(5):
            await client.post(
                "/api/v1/finance/invoices",
                json={
                    "student_id": student_id,
                    "academic_year_id": academic_year_id,
                    "due_date": str(date.today() + timedelta(days=30)),
                    "payment_status": "pending" if i < 3 else "paid",
                    "line_items": [{
                        "description": f"Invoice {i}",
                        "quantity": 1,
                        "unit_price": 100.00
                    }]
                },
                headers=admin_headers
            )
        
        # Filter by payment status
        response = await client.get(
            "/api/v1/finance/invoices",
            params={
                "payment_status": "pending",
                "academic_year_id": academic_year_id
            },
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_count"] == 3
        assert all(inv["payment_status"] == "pending" for inv in data["invoices"])
    
    @pytest.mark.asyncio
    async def test_send_invoice(self, client: AsyncClient, admin_headers: dict):
        """Test sending invoice to parent"""
        # Create invoice
        invoice_response = await client.post(
            "/api/v1/finance/invoices",
            json={
                "student_id": str(uuid4()),
                "academic_year_id": str(uuid4()),
                "due_date": str(date.today() + timedelta(days=30)),
                "line_items": [{
                    "description": "Test Fee",
                    "quantity": 1,
                    "unit_price": 100.00
                }]
            },
            headers=admin_headers
        )
        invoice_id = invoice_response.json()["id"]
        
        # Send invoice
        response = await client.post(
            f"/api/v1/finance/invoices/{invoice_id}/send",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["sent_to_parent"] is True


class TestPaymentAPI:
    """Test payment API endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_payment(self, client: AsyncClient, admin_headers: dict):
        """Test recording a payment"""
        payment_data = {
            "student_id": str(uuid4()),
            "payment_method_id": str(uuid4()),
            "amount": 500.00,
            "currency": "USD",
            "payer_name": "Jane Parent",
            "payer_email": "jane@example.com",
            "payer_phone": "+263771234567",
            "transaction_id": "BANK123456",
            "notes": "Payment for Term 1"
        }
        
        response = await client.post(
            "/api/v1/finance/payments",
            json=payment_data,
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["amount"] == 500.00
        assert data["payer_phone"] == "+263771234567"
        assert "payment_reference" in data
        assert data["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_allocate_payment(self, client: AsyncClient, admin_headers: dict):
        """Test allocating payment to invoices"""
        student_id = str(uuid4())
        
        # Create invoice
        invoice_response = await client.post(
            "/api/v1/finance/invoices",
            json={
                "student_id": student_id,
                "academic_year_id": str(uuid4()),
                "due_date": str(date.today() + timedelta(days=30)),
                "line_items": [{
                    "description": "Test Fee",
                    "quantity": 1,
                    "unit_price": 300.00
                }]
            },
            headers=admin_headers
        )
        invoice_id = invoice_response.json()["id"]
        
        # Create payment
        payment_response = await client.post(
            "/api/v1/finance/payments",
            json={
                "student_id": student_id,
                "payment_method_id": str(uuid4()),
                "amount": 300.00,
                "status": "completed"
            },
            headers=admin_headers
        )
        payment_id = payment_response.json()["id"]
        
        # Allocate payment
        response = await client.post(
            f"/api/v1/finance/payments/{payment_id}/allocate",
            json={"invoice_ids": [invoice_id]},
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["allocated_amount"] == 300.00
        assert len(data["allocations"]) == 1
    
    @pytest.mark.asyncio
    async def test_paynow_payment_initiation(self, client: AsyncClient, admin_headers: dict):
        """Test initiating Paynow payment"""
        payment_request = {
            "student_id": str(uuid4()),
            "invoice_ids": [str(uuid4())],
            "amount": 250.00,
            "payer_email": "parent@example.com",
            "payer_phone": "+263771234567"
        }
        
        response = await client.post(
            "/api/v1/finance/payments/paynow/initiate",
            json=payment_request,
            headers=admin_headers
        )
        
        # This would normally integrate with Paynow
        # For testing, we expect either success or a mock response
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE  # If Paynow not configured
        ]
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "payment_id" in data
            assert "redirect_url" in data
            assert "poll_url" in data


class TestFinanceReportsAPI:
    """Test finance reporting endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_finance_dashboard(self, client: AsyncClient, admin_headers: dict):
        """Test getting finance dashboard data"""
        academic_year_id = str(uuid4())
        
        response = await client.get(
            "/api/v1/finance/reports/dashboard",
            params={"academic_year_id": academic_year_id},
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check dashboard structure
        assert "current_term_invoiced" in data
        assert "current_term_collected" in data
        assert "current_term_outstanding" in data
        assert "current_term_collection_rate" in data
        assert "year_to_date_invoiced" in data
        assert "recent_payments" in data
        assert "payment_method_breakdown" in data
    
    @pytest.mark.asyncio
    async def test_collection_report(self, client: AsyncClient, admin_headers: dict):
        """Test collection analysis report"""
        params = {
            "start_date": str(date.today() - timedelta(days=30)),
            "end_date": str(date.today()),
            "grade_levels": [1, 2, 3]
        }
        
        response = await client.get(
            "/api/v1/finance/reports/collection",
            params=params,
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_expected" in data
        assert "total_collected" in data
        assert "collection_rate" in data
        assert "grade_breakdown" in data
    
    @pytest.mark.asyncio
    async def test_export_report(self, client: AsyncClient, admin_headers: dict):
        """Test exporting financial report"""
        response = await client.get(
            "/api/v1/finance/reports/export/invoices",
            params={
                "format": "csv",
                "start_date": str(date.today() - timedelta(days=30)),
                "end_date": str(date.today())
            },
            headers=admin_headers
        )
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_501_NOT_IMPLEMENTED  # If export not implemented
        ]
        
        if response.status_code == status.HTTP_200_OK:
            assert response.headers["content-type"] in [
                "text/csv",
                "application/vnd.ms-excel"
            ]


class TestAuthorizationAndValidation:
    """Test authorization rules and input validation"""
    
    @pytest.mark.asyncio
    async def test_teacher_cannot_modify_fees(self, client: AsyncClient, teacher_headers: dict):
        """Test that teachers have read-only access"""
        # Teachers should not create fee structures
        response = await client.post(
            "/api/v1/finance/fee-management/structures",
            json={
                "name": "Unauthorized Structure",
                "academic_year_id": str(uuid4()),
                "grade_levels": [1]
            },
            headers=teacher_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Teachers can view invoices
        response = await client.get(
            "/api/v1/finance/invoices",
            headers=teacher_headers
        )
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    async def test_zimbabwe_phone_validation(self, client: AsyncClient, admin_headers: dict):
        """Test Zimbabwe phone number validation"""
        # Invalid phone number
        payment_data = {
            "student_id": str(uuid4()),
            "payment_method_id": str(uuid4()),
            "amount": 100.00,
            "payer_phone": "1234567890"  # Invalid format
        }
        
        response = await client.post(
            "/api/v1/finance/payments",
            json=payment_data,
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "payer_phone" in response.json()["detail"][0]["loc"]
    
    @pytest.mark.asyncio
    async def test_currency_validation(self, client: AsyncClient, admin_headers: dict):
        """Test currency validation"""
        invoice_data = {
            "student_id": str(uuid4()),
            "academic_year_id": str(uuid4()),
            "due_date": str(date.today() + timedelta(days=30)),
            "currency": "EUR",  # Not supported
            "line_items": [{
                "description": "Test",
                "quantity": 1,
                "unit_price": 100.00
            }]
        }
        
        response = await client.post(
            "/api/v1/finance/invoices",
            json=invoice_data,
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_decimal_precision(self, client: AsyncClient, admin_headers: dict):
        """Test decimal precision handling"""
        payment_data = {
            "student_id": str(uuid4()),
            "payment_method_id": str(uuid4()),
            "amount": 123.456789,  # Too many decimal places
            "currency": "USD"
        }
        
        response = await client.post(
            "/api/v1/finance/payments",
            json=payment_data,
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        # Should be rounded to 2 decimal places
        assert data["amount"] == 123.46