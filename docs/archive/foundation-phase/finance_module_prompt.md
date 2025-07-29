# Claude Code Prompt: Finance & Billing Module Implementation

## 🎯 **Project Context**

You are building **Module 10 (Finance & Billing)** for the 1Class educational platform. This is the second major module after our gold standard SIS (Student Information System) module.

## 📁 **Reference Files to Study First**

**CRITICAL**: Before starting, examine these files to understand established patterns:

### **Database Patterns**
- `database/schemas/09_sis.sql` - Study the table structure, RLS policies, indexes, and utility functions
- `database/schemas/01_platform_enhanced.sql` - Review school configuration and multitenancy setup

### **Backend Patterns**  
- `backend/services/sis/schemas.py` - Pydantic models, validation patterns, Zimbabwe-specific validation
- `backend/services/sis/crud.py` - CRUD operations, business logic, audit trails, error handling
- `backend/services/sis/main.py` - FastAPI endpoints, authentication, permissions, background tasks
- `backend/shared/auth.py` - Enhanced authentication with school context
- `backend/shared/file_storage.py` - School-isolated file storage patterns

### **Quality Standards**
- **Database**: Multi-tenant RLS, encrypted sensitive data, comprehensive constraints, performance indexes
- **API**: Role-based permissions, comprehensive validation, audit logging, Zimbabwe-specific business rules
- **Frontend**: Multi-step forms, real-time validation, offline sync, responsive design

---

## 🏗️ **Module 10: Finance & Billing Specifications**

### **Core Functionality Required**

#### **1. Fee Management System**
- **Fee Structures**: Create flexible fee structures per grade/term/year
- **Fee Categories**: Tuition, transport, meals, sports, activities, penalties
- **Dynamic Pricing**: Early bird discounts, sibling discounts, scholarship adjustments
- **Recurring Fees**: Automatic generation per term/month

#### **2. Invoice & Billing System**
- **Smart Invoice Generation**: Automatic based on fee structures and student enrollment
- **Multi-Currency Support**: USD primary, ZWL secondary, other currencies
- **Payment Plans**: Full payment, installments, custom payment schedules
- **Bulk Operations**: Mass invoice generation, bulk adjustments

#### **3. Payment Processing**
- **Zimbabwe Payment Gateways**: 
  - Paynow (EcoCash, OneMoney, Zimswitch, Visa/Mastercard)
  - Direct bank integration capabilities
  - Cash payment recording
  - Payment voucher systems
- **Payment Reconciliation**: Automatic matching of payments to invoices
- **Partial Payments**: Support for installment payments
- **Refund Management**: Process refunds and credits

#### **4. Financial Reporting & Analytics**
- **School Finance Dashboard**: Revenue, collections, outstanding balances
- **Parent Financial Portal**: Payment history, outstanding balances, payment options
- **Advanced Reports**: Cash flow, collection rates, revenue forecasting
- **Export Capabilities**: PDF statements, CSV reports, accounting system integration

#### **5. Zimbabwe-Specific Features**
- **Local Currency Support**: Handle ZWL inflation and currency conversion
- **Mobile Money Integration**: EcoCash, OneMoney with USSD fallback
- **Government Integration**: Prepare for ZIMRA tax reporting requirements
- **Local Banking**: Support for major Zimbabwean banks (CBZ, Steward, FBC, etc.)

---

## 🗄️ **Database Schema Requirements**

### **Tables to Create (in `finance` schema)**

```sql
-- Use this as your starting structure, following SIS patterns exactly

CREATE SCHEMA IF NOT EXISTS finance;

-- Key tables needed:
finance.fee_structures        -- Templates for different fee types
finance.fee_items            -- Individual fee components  
finance.student_fee_assignments  -- Link students to fee structures
finance.invoices             -- Generated invoices for students
finance.invoice_line_items   -- Detailed breakdown of invoice charges
finance.payments             -- All payment records
finance.payment_methods      -- Available payment options
finance.payment_reconciliation -- Match payments to invoices
finance.refunds              -- Refund and credit records
finance.financial_reports    -- Cached report data
finance.fee_adjustments      -- Discounts, scholarships, penalties
finance.payment_plans        -- Custom payment schedules
```

### **Critical Requirements**
- **Multi-tenant isolation**: Every table must have `school_id` with RLS policies
- **Audit trails**: Full logging of all financial transactions
- **Data encryption**: Sensitive payment data must be encrypted
- **Performance**: Indexes for reporting and payment lookup
- **Constraints**: Business rule enforcement at database level
- **Currency handling**: Proper decimal precision for money fields

---

## 🚀 **API Endpoints Required**

### **Fee Management APIs**
```
POST   /api/v1/finance/fee-structures
GET    /api/v1/finance/fee-structures
PUT    /api/v1/finance/fee-structures/{id}
DELETE /api/v1/finance/fee-structures/{id}

POST   /api/v1/finance/fee-structures/{id}/assign-students
GET    /api/v1/finance/students/{id}/fee-assignments
```

### **Invoice Management APIs**
```
POST   /api/v1/finance/invoices/generate-bulk
GET    /api/v1/finance/invoices
GET    /api/v1/finance/invoices/{id}
PUT    /api/v1/finance/invoices/{id}
POST   /api/v1/finance/invoices/{id}/send-notification

GET    /api/v1/finance/students/{id}/invoices
GET    /api/v1/finance/parents/my-invoices
```

### **Payment Processing APIs**
```
POST   /api/v1/finance/payments/initiate-paynow
POST   /api/v1/finance/payments/record-cash
GET    /api/v1/finance/payments/{id}/status
POST   /api/v1/finance/payments/webhook/paynow

GET    /api/v1/finance/students/{id}/payment-history
POST   /api/v1/finance/payments/{id}/refund
```

### **Reporting APIs**
```
GET    /api/v1/finance/dashboard/school-overview
GET    /api/v1/finance/reports/collection-summary
GET    /api/v1/finance/reports/outstanding-balances
POST   /api/v1/finance/reports/generate-custom

GET    /api/v1/finance/statements/{student_id}/pdf
GET    /api/v1/finance/receipts/{payment_id}/pdf
```

---

## 💻 **Frontend Components Required**

### **Admin Components**
```typescript
// Fee structure management
FeeStructureForm.tsx         // Create/edit fee structures
FeeStructureList.tsx         // List all fee structures  
StudentFeeAssignment.tsx     // Assign fees to students

// Invoice management  
InvoiceGeneration.tsx        // Bulk invoice generation
InvoiceList.tsx             // View all invoices
InvoiceDetails.tsx          // Individual invoice details

// Payment processing
PaymentRecording.tsx        // Record cash/bank payments
PaymentReconciliation.tsx   // Match payments to invoices
RefundProcessing.tsx        // Process refunds

// Financial reporting
FinanceDashboard.tsx        // School finance overview
CollectionReports.tsx       // Payment collection analysis
FinancialStatements.tsx     // Detailed financial reports
```

### **Parent Components**
```typescript
// Parent payment portal
ParentPaymentDashboard.tsx  // Overview of all children's fees
InvoicePaymentForm.tsx      // Make payments via Paynow
PaymentHistory.tsx          // View payment history
PaymentPlanSetup.tsx        // Setup payment plans

// Payment processing
PaynowPaymentFlow.tsx       // Complete payment flow
MobileMoneyPayment.tsx      // EcoCash/OneMoney integration
PaymentConfirmation.tsx     // Payment success/failure
```

### **Student Components**
```typescript
// Student financial view
StudentFinancialOverview.tsx // View own fee status
PaymentStatusCard.tsx       // Quick payment status
FeeBreakdown.tsx           // Detailed fee breakdown
```

---

## 🇿🇼 **Zimbabwe Integration Requirements**

### **Paynow Payment Integration**
```python
# Exact implementation pattern needed
class PaynowIntegration:
    async def initiate_payment(self, amount: float, email: str, student_id: str) -> dict
    async def check_payment_status(self, poll_url: str) -> dict  
    async def process_webhook(self, webhook_data: dict) -> bool
    async def handle_payment_result(self, payment_id: str, status: str) -> dict
```

### **Mobile Money Support**
- **EcoCash**: Full integration with transaction verification
- **OneMoney**: Direct API integration where possible
- **USSD Fallback**: Instructions for manual USSD payments
- **Transaction Tracking**: Full audit trail for all mobile payments

### **Local Banking Integration**
- **RTGS Support**: Real-time gross settlement integration prep
- **Bank Transfer Recording**: Manual bank transfer confirmation
- **Bulk Payment Processing**: Handle large payment uploads
- **Reconciliation Tools**: Match bank statements to payments

---

## 📊 **Business Logic Requirements**

### **Fee Calculation Engine**
```python
# Must implement sophisticated fee calculation
def calculate_student_fees(
    student_id: UUID,
    academic_year_id: UUID,
    term_id: Optional[UUID] = None,
    apply_discounts: bool = True
) -> FeeCalculationResult:
    # 1. Get base fee structure for student's grade
    # 2. Apply school-specific adjustments
    # 3. Calculate sibling discounts
    # 4. Apply scholarship adjustments  
    # 5. Add penalty fees if applicable
    # 6. Handle early payment discounts
    # 7. Return detailed breakdown
```

### **Payment Allocation Logic**
```python
# Intelligent payment allocation to multiple invoices
def allocate_payment(
    payment_amount: Decimal,
    student_invoices: List[Invoice],
    allocation_strategy: str = "oldest_first"
) -> PaymentAllocation:
    # 1. Sort invoices by strategy (oldest_first, highest_first, etc.)
    # 2. Allocate payment across invoices
    # 3. Handle partial payments
    # 4. Update invoice statuses
    # 5. Generate allocation report
```

### **Outstanding Balance Management**
```python
# Track and manage outstanding balances
def update_student_balance(student_id: UUID) -> StudentFinancialSummary:
    # 1. Calculate total invoiced amount
    # 2. Sum all payments received
    # 3. Calculate outstanding balance
    # 4. Determine overdue amounts
    # 5. Apply late payment penalties
    # 6. Update student financial status
```

---

## 🔒 **Security & Compliance Requirements**

### **Financial Data Protection**
- **PCI DSS Compliance**: No storage of card details, secure payment processing
- **Data Encryption**: All payment information encrypted at rest and in transit
- **Audit Trails**: Complete financial transaction logging
- **Access Controls**: Role-based access to financial data
- **Fraud Detection**: Basic fraud detection for unusual payment patterns

### **Zimbabwe Compliance**
- **ZIMRA Integration Prep**: Structure for future tax reporting
- **RBZ Compliance**: Follow Reserve Bank of Zimbabwe payment regulations
- **Data Residency**: Ensure financial data stays within Zimbabwe where required
- **Audit Requirements**: Support for external financial audits

---

## ⚡ **Performance Requirements**

### **Critical Performance Targets**
- **Payment Processing**: <3 seconds for Paynow initiation
- **Report Generation**: <5 seconds for standard reports
- **Dashboard Loading**: <2 seconds for finance dashboard
- **Bulk Operations**: Handle 1000+ invoice generation in <30 seconds
- **Payment Webhook**: <1 second response time

### **Scalability Requirements**
- **Multi-School**: Support 1000+ schools with independent fee structures
- **High Volume**: Handle 10,000+ students per school
- **Concurrent Payments**: Support 100+ simultaneous payment transactions
- **Large Reports**: Generate reports for entire school districts

---

## 🧪 **Testing Requirements**

### **Critical Test Scenarios**
```python
# Payment flow testing
test_paynow_payment_success()
test_paynow_payment_failure() 
test_partial_payment_handling()
test_payment_webhook_processing()

# Business logic testing
test_fee_calculation_accuracy()
test_discount_application()
test_payment_allocation_logic()
test_outstanding_balance_tracking()

# Multi-tenancy testing  
test_school_financial_isolation()
test_payment_security_boundaries()
test_fee_structure_independence()

# Performance testing
test_bulk_invoice_generation()
test_concurrent_payment_processing()
test_large_report_generation()
```

---

## 📋 **Implementation Phases**

### **Phase 1: Core Finance Infrastructure (Week 1)**
1. **Database Schema**: Complete finance schema with all tables
2. **Basic CRUD**: Fee structures, invoices, basic payment recording
3. **Authentication**: Finance-specific permissions and roles
4. **Foundation Tests**: Core functionality testing

### **Phase 2: Payment Integration (Week 2)**  
1. **Paynow Integration**: Complete payment gateway integration
2. **Payment Processing**: Full payment flow with webhooks
3. **Payment Dashboard**: Basic admin payment management
4. **Parent Payment Portal**: Allow parents to make payments

### **Phase 3: Advanced Features (Week 3)**
1. **Financial Reporting**: Comprehensive reporting system
2. **Bulk Operations**: Mass invoice generation and processing
3. **Payment Plans**: Installment and custom payment schedules
4. **Advanced UI**: Complete admin and parent interfaces

### **Phase 4: Zimbabwe Features (Week 4)**
1. **Mobile Money**: EcoCash and OneMoney integration
2. **Local Banking**: Bank transfer and reconciliation tools
3. **Currency Support**: Multi-currency with ZWL handling
4. **Compliance**: ZIMRA prep and audit trail enhancements

---

## ✅ **Success Criteria**

### **Technical Success**
- [ ] Complete database schema following SIS patterns
- [ ] All API endpoints implemented with proper validation
- [ ] Frontend components with responsive design and offline support
- [ ] Paynow integration working end-to-end
- [ ] Multi-tenant isolation verified
- [ ] Performance targets met
- [ ] 90%+ test coverage achieved

### **Business Success**  
- [ ] Schools can create fee structures and generate invoices
- [ ] Parents can make payments via multiple methods
- [ ] Financial reporting provides actionable insights
- [ ] Payment processing is reliable and secure
- [ ] Zimbabwe-specific features work correctly
- [ ] System scales to support multiple schools

### **Quality Success**
- [ ] Code follows established SIS patterns exactly
- [ ] Security measures protect financial data
- [ ] Error handling covers all edge cases
- [ ] Documentation is complete and actionable
- [ ] Integration tests cover all payment flows
- [ ] Performance meets or exceeds requirements

---

## 🎯 **Immediate Next Steps**

1. **Study Reference Files**: Examine SIS implementation patterns thoroughly
2. **Start with Database**: Create complete finance schema following SIS patterns  
3. **Build Core CRUD**: Implement basic fee and invoice management
4. **Add Payment Integration**: Implement Paynow gateway
5. **Create Frontend Components**: Build admin and parent interfaces
6. **Test Everything**: Comprehensive testing at each step

**Remember**: This module must match the quality and consistency of our SIS gold standard while adding sophisticated financial management capabilities for Zimbabwean schools.

Build this module to production quality - it will handle real money for real schools! 💰🏫