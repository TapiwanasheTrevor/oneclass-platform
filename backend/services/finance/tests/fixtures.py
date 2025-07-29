"""
Test fixtures and mock data for Finance module tests
Provides consistent test data across all test files
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4
from typing import Dict, List, Any

from backend.services.finance.schemas import (
    FeeCategoryCreate,
    FeeStructureCreate,
    FeeItemCreate,
    InvoiceCreate,
    PaymentCreate,
    PaymentStatus,
    FeeFrequency,
    PaynowPaymentRequest,
    PaynowPaymentResponse,
    PaynowStatusResponse
)


# School and User Fixtures
@pytest.fixture
def school_id() -> str:
    """Test school ID"""
    return "school-12345678-1234-1234-1234-123456789012"


@pytest.fixture
def user_id() -> str:
    """Test user ID"""
    return "user-87654321-4321-4321-4321-210987654321"


@pytest.fixture
def admin_user_id() -> str:
    """Test admin user ID"""
    return "admin-11111111-1111-1111-1111-111111111111"


@pytest.fixture
def teacher_user_id() -> str:
    """Test teacher user ID"""
    return "teacher-22222222-2222-2222-2222-222222222222"


@pytest.fixture
def academic_year_id() -> str:
    """Test academic year ID"""
    return "ay-2025-33333333-3333-3333-3333-333333333333"


@pytest.fixture
def term_id() -> str:
    """Test term ID"""
    return "term-44444444-4444-4444-4444-444444444444"


@pytest.fixture
def student_id() -> str:
    """Test student ID"""
    return "student-55555555-5555-5555-5555-555555555555"


@pytest.fixture
def class_id() -> str:
    """Test class ID"""
    return "class-66666666-6666-6666-6666-666666666666"


# Fee Category Fixtures
@pytest.fixture
def fee_category_data() -> Dict[str, Any]:
    """Standard fee category data"""
    return {
        "name": "Tuition Fees",
        "code": "TUITION",
        "description": "Regular tuition fees for academic instruction",
        "is_mandatory": True,
        "is_refundable": False,
        "allows_partial_payment": True,
        "display_order": 1,
        "is_active": True
    }


@pytest.fixture
def fee_category_create(fee_category_data: Dict[str, Any]) -> FeeCategoryCreate:
    """Fee category create schema"""
    return FeeCategoryCreate(**fee_category_data)


@pytest.fixture
def multiple_fee_categories() -> List[Dict[str, Any]]:
    """Multiple fee categories for testing"""
    return [
        {
            "name": "Tuition Fees",
            "code": "TUITION",
            "description": "Regular tuition fees",
            "is_mandatory": True,
            "is_refundable": False,
            "allows_partial_payment": True,
            "display_order": 1
        },
        {
            "name": "Sports Fees",
            "code": "SPORTS",
            "description": "Sports and extracurricular activities",
            "is_mandatory": False,
            "is_refundable": True,
            "allows_partial_payment": False,
            "display_order": 2
        },
        {
            "name": "Laboratory Fees",
            "code": "LAB",
            "description": "Science laboratory usage",
            "is_mandatory": True,
            "is_refundable": False,
            "allows_partial_payment": True,
            "display_order": 3
        },
        {
            "name": "Library Fees",
            "code": "LIBRARY",
            "description": "Library membership and resources",
            "is_mandatory": False,
            "is_refundable": True,
            "allows_partial_payment": False,
            "display_order": 4
        }
    ]


# Fee Structure Fixtures
@pytest.fixture
def fee_structure_data(academic_year_id: str) -> Dict[str, Any]:
    """Standard fee structure data"""
    return {
        "name": "Form 1 Fee Structure 2025",
        "description": "Standard fee structure for Form 1 students",
        "academic_year_id": academic_year_id,
        "grade_levels": [1],
        "class_ids": None,
        "is_default": True,
        "applicable_from": date.today(),
        "applicable_to": date.today() + timedelta(days=365),
        "status": "active"
    }


@pytest.fixture
def fee_structure_create(fee_structure_data: Dict[str, Any]) -> FeeStructureCreate:
    """Fee structure create schema"""
    return FeeStructureCreate(**fee_structure_data)


@pytest.fixture
def multiple_fee_structures(academic_year_id: str) -> List[Dict[str, Any]]:
    """Multiple fee structures for different grades"""
    return [
        {
            "name": "Form 1 Fee Structure 2025",
            "description": "Standard fees for Form 1",
            "academic_year_id": academic_year_id,
            "grade_levels": [1],
            "is_default": True,
            "applicable_from": date.today(),
            "status": "active"
        },
        {
            "name": "Form 2 Fee Structure 2025",
            "description": "Standard fees for Form 2",
            "academic_year_id": academic_year_id,
            "grade_levels": [2],
            "is_default": True,
            "applicable_from": date.today(),
            "status": "active"
        },
        {
            "name": "Form 3-4 Fee Structure 2025",
            "description": "Standard fees for Form 3-4",
            "academic_year_id": academic_year_id,
            "grade_levels": [3, 4],
            "is_default": True,
            "applicable_from": date.today(),
            "status": "active"
        }
    ]


# Fee Item Fixtures
@pytest.fixture
def fee_item_data() -> Dict[str, Any]:
    """Standard fee item data"""
    return {
        "name": "Term 1 Tuition",
        "description": "Tuition fees for Term 1",
        "base_amount": Decimal("500.00"),
        "currency": "USD",
        "frequency": FeeFrequency.TERM,
        "allows_installments": True,
        "max_installments": 3,
        "late_fee_amount": Decimal("10.00"),
        "is_active": True
    }


@pytest.fixture
def fee_item_create(
    fee_item_data: Dict[str, Any],
    fee_structure_id: str,
    fee_category_id: str
) -> FeeItemCreate:
    """Fee item create schema"""
    return FeeItemCreate(
        fee_structure_id=fee_structure_id,
        fee_category_id=fee_category_id,
        **fee_item_data
    )


@pytest.fixture
def multiple_fee_items() -> List[Dict[str, Any]]:
    """Multiple fee items for testing"""
    return [
        {
            "name": "Term 1 Tuition",
            "description": "Tuition fees for Term 1",
            "base_amount": Decimal("500.00"),
            "currency": "USD",
            "frequency": FeeFrequency.TERM,
            "allows_installments": True,
            "max_installments": 3,
            "late_fee_amount": Decimal("10.00")
        },
        {
            "name": "Annual Sports Fee",
            "description": "Sports and activities for the year",
            "base_amount": Decimal("100.00"),
            "currency": "USD",
            "frequency": FeeFrequency.ANNUAL,
            "allows_installments": False,
            "max_installments": 1,
            "late_fee_amount": Decimal("5.00")
        },
        {
            "name": "Monthly Lab Fee",
            "description": "Laboratory usage fee",
            "base_amount": Decimal("50.00"),
            "currency": "USD",
            "frequency": FeeFrequency.MONTHLY,
            "allows_installments": False,
            "max_installments": 1,
            "late_fee_amount": Decimal("2.00")
        }
    ]


# Invoice Fixtures
@pytest.fixture
def invoice_data(student_id: str, academic_year_id: str) -> Dict[str, Any]:
    """Standard invoice data"""
    return {
        "student_id": student_id,
        "academic_year_id": academic_year_id,
        "term_id": None,
        "due_date": date.today() + timedelta(days=30),
        "currency": "USD",
        "notes": "Term 1 fees for student",
        "line_items": [
            {
                "description": "Tuition Fees",
                "quantity": 1,
                "unit_price": Decimal("500.00"),
                "discount_amount": Decimal("0.00")
            },
            {
                "description": "Sports Fees",
                "quantity": 1,
                "unit_price": Decimal("100.00"),
                "discount_amount": Decimal("10.00")
            }
        ]
    }


@pytest.fixture
def invoice_create(invoice_data: Dict[str, Any]) -> InvoiceCreate:
    """Invoice create schema"""
    return InvoiceCreate(**invoice_data)


@pytest.fixture
def multiple_invoices(academic_year_id: str) -> List[Dict[str, Any]]:
    """Multiple invoices with different statuses"""
    return [
        {
            "student_id": str(uuid4()),
            "student_name": "John Smith",
            "student_number": "STU-001",
            "academic_year_id": academic_year_id,
            "invoice_number": "INV-2025-001",
            "due_date": date.today() + timedelta(days=30),
            "total_amount": Decimal("500.00"),
            "paid_amount": Decimal("200.00"),
            "outstanding_amount": Decimal("300.00"),
            "payment_status": "partial",
            "status": "sent",
            "currency": "USD"
        },
        {
            "student_id": str(uuid4()),
            "student_name": "Jane Doe",
            "student_number": "STU-002",
            "academic_year_id": academic_year_id,
            "invoice_number": "INV-2025-002",
            "due_date": date.today() - timedelta(days=10),
            "total_amount": Decimal("750.00"),
            "paid_amount": Decimal("0.00"),
            "outstanding_amount": Decimal("750.00"),
            "payment_status": "overdue",
            "status": "sent",
            "currency": "USD"
        },
        {
            "student_id": str(uuid4()),
            "student_name": "Mike Johnson",
            "student_number": "STU-003",
            "academic_year_id": academic_year_id,
            "invoice_number": "INV-2025-003",
            "due_date": date.today() + timedelta(days=15),
            "total_amount": Decimal("600.00"),
            "paid_amount": Decimal("600.00"),
            "outstanding_amount": Decimal("0.00"),
            "payment_status": "paid",
            "status": "paid",
            "currency": "USD"
        }
    ]


# Payment Fixtures
@pytest.fixture
def payment_data(student_id: str) -> Dict[str, Any]:
    """Standard payment data"""
    return {
        "student_id": student_id,
        "amount": Decimal("500.00"),
        "currency": "USD",
        "payment_method_id": str(uuid4()),
        "payer_name": "John Parent",
        "payer_email": "parent@example.com",
        "payer_phone": "+263771234567",
        "transaction_id": "TXN-123456789",
        "notes": "Payment for Term 1 fees",
        "reconciled": False
    }


@pytest.fixture
def payment_create(payment_data: Dict[str, Any]) -> PaymentCreate:
    """Payment create schema"""
    return PaymentCreate(**payment_data)


@pytest.fixture
def multiple_payments(student_id: str) -> List[Dict[str, Any]]:
    """Multiple payments with different statuses"""
    return [
        {
            "student_id": student_id,
            "payment_reference": "PAY-2025-001",
            "amount": Decimal("500.00"),
            "currency": "USD",
            "payment_method_id": str(uuid4()),
            "payer_name": "John Parent",
            "payer_email": "parent@example.com",
            "payer_phone": "+263771234567",
            "transaction_id": "ECOCASH-123456",
            "status": PaymentStatus.COMPLETED,
            "payment_date": date.today(),
            "reconciled": False
        },
        {
            "student_id": student_id,
            "payment_reference": "PAY-2025-002",
            "amount": Decimal("200.00"),
            "currency": "USD",
            "payment_method_id": str(uuid4()),
            "payer_name": "Jane Parent",
            "payer_email": "jane@example.com",
            "payer_phone": "+263772345678",
            "transaction_id": "BANK-789012",
            "status": PaymentStatus.PENDING,
            "payment_date": date.today(),
            "reconciled": False
        },
        {
            "student_id": student_id,
            "payment_reference": "PAY-2025-003",
            "amount": Decimal("100.00"),
            "currency": "USD",
            "payment_method_id": str(uuid4()),
            "payer_name": "Mike Parent",
            "payer_email": "mike@example.com",
            "payer_phone": "+263773456789",
            "transaction_id": "CASH-345678",
            "status": PaymentStatus.FAILED,
            "payment_date": date.today(),
            "reconciled": False
        }
    ]


# Payment Method Fixtures
@pytest.fixture
def payment_methods() -> List[Dict[str, Any]]:
    """Standard payment methods"""
    return [
        {
            "id": str(uuid4()),
            "name": "EcoCash",
            "code": "ECOCASH",
            "type": "mobile_money",
            "is_active": True,
            "requires_reference": True,
            "supports_partial_payment": True,
            "transaction_fee_percentage": Decimal("1.5"),
            "transaction_fee_fixed": Decimal("0.00"),
            "display_order": 1
        },
        {
            "id": str(uuid4()),
            "name": "OneMoney",
            "code": "ONEMONEY",
            "type": "mobile_money",
            "is_active": True,
            "requires_reference": True,
            "supports_partial_payment": True,
            "transaction_fee_percentage": Decimal("1.5"),
            "transaction_fee_fixed": Decimal("0.00"),
            "display_order": 2
        },
        {
            "id": str(uuid4()),
            "name": "Bank Transfer",
            "code": "BANK",
            "type": "bank_transfer",
            "is_active": True,
            "requires_reference": True,
            "supports_partial_payment": True,
            "transaction_fee_percentage": Decimal("0.0"),
            "transaction_fee_fixed": Decimal("0.00"),
            "display_order": 3
        },
        {
            "id": str(uuid4()),
            "name": "Cash",
            "code": "CASH",
            "type": "cash",
            "is_active": True,
            "requires_reference": False,
            "supports_partial_payment": True,
            "transaction_fee_percentage": Decimal("0.0"),
            "transaction_fee_fixed": Decimal("0.00"),
            "display_order": 4
        }
    ]


# Paynow Integration Fixtures
@pytest.fixture
def paynow_payment_request(student_id: str) -> PaynowPaymentRequest:
    """Paynow payment request data"""
    return PaynowPaymentRequest(
        student_id=student_id,
        invoice_ids=[str(uuid4())],
        amount=Decimal("250.00"),
        payer_email="parent@example.com",
        payer_phone="+263771234567"
    )


@pytest.fixture
def paynow_success_response() -> PaynowPaymentResponse:
    """Successful Paynow payment response"""
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
def paynow_error_response() -> PaynowPaymentResponse:
    """Error Paynow payment response"""
    return PaynowPaymentResponse(
        payment_id="PAY-ERROR",
        paynow_reference="",
        poll_url="",
        redirect_url="",
        status="error",
        success=False,
        hash_valid=False,
        error="Invalid email address"
    )


@pytest.fixture
def paynow_status_paid() -> PaynowStatusResponse:
    """Paynow status response - paid"""
    return PaynowStatusResponse(
        status="Paid",
        amount=Decimal("250.00"),
        paynow_reference="PR-789012",
        poll_url="https://paynow.co.zw/interface/poll/?guid=123",
        hash_valid=True
    )


@pytest.fixture
def paynow_status_pending() -> PaynowStatusResponse:
    """Paynow status response - pending"""
    return PaynowStatusResponse(
        status="Awaiting Delivery",
        amount=Decimal("250.00"),
        paynow_reference="PR-789012",
        poll_url="https://paynow.co.zw/interface/poll/?guid=123",
        hash_valid=True
    )


# Dashboard Data Fixtures
@pytest.fixture
def finance_dashboard_data(academic_year_id: str) -> Dict[str, Any]:
    """Finance dashboard data"""
    return {
        "school_id": "school-123",
        "academic_year_id": academic_year_id,
        "current_term_invoiced": Decimal("150000.00"),
        "current_term_collected": Decimal("120000.00"),
        "current_term_outstanding": Decimal("30000.00"),
        "current_term_collection_rate": 80.0,
        "year_to_date_invoiced": Decimal("450000.00"),
        "year_to_date_collected": Decimal("360000.00"),
        "year_to_date_outstanding": Decimal("90000.00"),
        "year_to_date_collection_rate": 80.0,
        "recent_payments": [
            {
                "id": str(uuid4()),
                "student_name": "John Smith",
                "amount": Decimal("500.00"),
                "payment_date": date.today().isoformat(),
                "status": "completed",
                "payment_method": {"name": "EcoCash"}
            },
            {
                "id": str(uuid4()),
                "student_name": "Jane Doe",
                "amount": Decimal("750.00"),
                "payment_date": (date.today() - timedelta(days=1)).isoformat(),
                "status": "completed",
                "payment_method": {"name": "Bank Transfer"}
            }
        ],
        "overdue_invoices_count": 5,
        "pending_payments_count": 3,
        "monthly_collection_trend": [
            {
                "month": "2025-01",
                "expected": Decimal("100000.00"),
                "collected": Decimal("85000.00"),
                "rate": 85.0
            },
            {
                "month": "2025-02",
                "expected": Decimal("120000.00"),
                "collected": Decimal("96000.00"),
                "rate": 80.0
            },
            {
                "month": "2025-03",
                "expected": Decimal("110000.00"),
                "collected": Decimal("99000.00"),
                "rate": 90.0
            }
        ],
        "payment_method_breakdown": [
            {
                "method": "EcoCash",
                "amount": Decimal("50000.00"),
                "count": 100,
                "percentage": 41.7
            },
            {
                "method": "Bank Transfer",
                "amount": Decimal("40000.00"),
                "count": 80,
                "percentage": 33.3
            },
            {
                "method": "Cash",
                "amount": Decimal("30000.00"),
                "count": 60,
                "percentage": 25.0
            }
        ],
        "fee_category_breakdown": [
            {
                "category": "Tuition",
                "amount": Decimal("80000.00"),
                "percentage": 66.7
            },
            {
                "category": "Sports",
                "amount": Decimal("25000.00"),
                "percentage": 20.8
            },
            {
                "category": "Laboratory",
                "amount": Decimal("15000.00"),
                "percentage": 12.5
            }
        ]
    }


# Validation Test Data
@pytest.fixture
def invalid_phone_numbers() -> List[str]:
    """Invalid phone numbers for validation testing"""
    return [
        "1234567890",  # No country code
        "+1234567890",  # Wrong country code
        "+263712345",  # Too short
        "+2637123456789",  # Too long
        "+263abc1234567",  # Contains letters
        "263771234567",  # Missing +
        "+263 77 123 4567",  # Contains spaces
        "+263-77-123-4567",  # Contains hyphens
    ]


@pytest.fixture
def valid_phone_numbers() -> List[str]:
    """Valid Zimbabwe phone numbers"""
    return [
        "+263771234567",  # EcoCash
        "+263712345678",  # NetOne
        "+263782345678",  # Telecel
        "+263773456789",  # EcoCash
        "+263714567890",  # NetOne
    ]


@pytest.fixture
def invalid_currencies() -> List[str]:
    """Invalid currencies for validation testing"""
    return [
        "EUR",  # Not supported
        "GBP",  # Not supported
        "JPY",  # Not supported
        "CAD",  # Not supported
        "AUD",  # Not supported
        "ZAR",  # Not supported
    ]


@pytest.fixture
def valid_currencies() -> List[str]:
    """Valid currencies"""
    return [
        "USD",  # US Dollar
        "ZWL",  # Zimbabwe Dollar
    ]


# Bulk Operation Fixtures
@pytest.fixture
def bulk_invoice_data(academic_year_id: str) -> Dict[str, Any]:
    """Bulk invoice generation data"""
    return {
        "fee_structure_id": str(uuid4()),
        "due_date": (date.today() + timedelta(days=30)).isoformat(),
        "academic_year_id": academic_year_id,
        "term_id": str(uuid4()),
        "grade_levels": [1, 2, 3],
        "notes": "Bulk generated invoices for Term 1"
    }


@pytest.fixture
def bulk_invoice_result() -> Dict[str, Any]:
    """Bulk invoice generation result"""
    return {
        "total_invoices_generated": 75,
        "total_students_processed": 75,
        "total_amount": Decimal("37500.00"),
        "failed_students": [],
        "invoice_ids": [str(uuid4()) for _ in range(75)]
    }


# Error Scenarios
@pytest.fixture
def payment_errors() -> List[Dict[str, Any]]:
    """Common payment error scenarios"""
    return [
        {
            "error_type": "insufficient_funds",
            "message": "Insufficient funds in account",
            "paynow_status": "Failed",
            "should_retry": True
        },
        {
            "error_type": "invalid_phone",
            "message": "Invalid phone number format",
            "paynow_status": "Error",
            "should_retry": False
        },
        {
            "error_type": "network_error",
            "message": "Network connection failed",
            "paynow_status": "Error",
            "should_retry": True
        },
        {
            "error_type": "merchant_error",
            "message": "Merchant account suspended",
            "paynow_status": "Error",
            "should_retry": False
        }
    ]


# Performance Test Data
@pytest.fixture
def large_dataset() -> Dict[str, Any]:
    """Large dataset for performance testing"""
    return {
        "invoices_count": 1000,
        "payments_count": 500,
        "students_count": 300,
        "bulk_operations": 50
    }


# Integration Test Data
@pytest.fixture
def integration_test_school() -> Dict[str, Any]:
    """Complete school data for integration testing"""
    return {
        "school_id": "integration-school-123",
        "name": "Integration Test School",
        "academic_years": [
            {
                "id": "ay-2025",
                "name": "2025 Academic Year",
                "start_date": "2025-01-01",
                "end_date": "2025-12-31"
            }
        ],
        "students": [
            {
                "id": "student-001",
                "name": "John Smith",
                "grade": 1,
                "class": "1A"
            },
            {
                "id": "student-002", 
                "name": "Jane Doe",
                "grade": 2,
                "class": "2B"
            }
        ],
        "fee_structures": [
            {
                "id": "fs-001",
                "name": "Form 1 Fees",
                "grade_levels": [1],
                "total_amount": Decimal("500.00")
            },
            {
                "id": "fs-002",
                "name": "Form 2 Fees", 
                "grade_levels": [2],
                "total_amount": Decimal("600.00")
            }
        ]
    }