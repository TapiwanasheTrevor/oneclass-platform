-- =====================================================
-- Module 10: Finance & Billing System
-- Complete Database Schema
-- File: database/schemas/10_finance.sql
-- =====================================================

-- Create the finance schema
CREATE SCHEMA IF NOT EXISTS finance;

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- FEE STRUCTURE MANAGEMENT
-- =====================================================

-- Fee categories and types
CREATE TABLE finance.fee_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES platform.schools(id) ON DELETE CASCADE,
    
    -- Category Information
    name VARCHAR(100) NOT NULL, -- 'Tuition', 'Transport', 'Meals', 'Sports', 'Activities'
    description TEXT,
    code VARCHAR(20) NOT NULL, -- 'TUI', 'TRP', 'MEL', 'SPT', 'ACT'
    
    -- Configuration
    is_mandatory BOOLEAN DEFAULT TRUE,
    is_refundable BOOLEAN DEFAULT FALSE,
    allows_partial_payment BOOLEAN DEFAULT TRUE,
    
    -- Display Settings
    display_order INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- System Fields
    created_by UUID NOT NULL REFERENCES platform.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_fee_category_code UNIQUE(school_id, code),
    CONSTRAINT unique_fee_category_name UNIQUE(school_id, name)
);

-- Fee structures - templates for different fee types
CREATE TABLE finance.fee_structures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES platform.schools(id) ON DELETE CASCADE,
    
    -- Structure Information
    name VARCHAR(200) NOT NULL, -- 'Form 1 2024 Fees', 'Grade 7 Transport 2024'
    description TEXT,
    academic_year_id UUID NOT NULL REFERENCES platform.academic_years(id),
    
    -- Applicability
    grade_levels INTEGER[] NOT NULL, -- [1,2,3] for Forms 1-3
    class_ids UUID[], -- Optional: specific classes
    is_default BOOLEAN DEFAULT FALSE, -- Default for new students
    
    -- Timing
    applicable_from DATE NOT NULL DEFAULT CURRENT_DATE,
    applicable_to DATE,
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'inactive', 'archived')),
    
    -- Approval
    approved_by UUID REFERENCES platform.users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    
    -- System Fields
    created_by UUID NOT NULL REFERENCES platform.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_applicable_dates CHECK (applicable_to IS NULL OR applicable_to > applicable_from),
    CONSTRAINT unique_fee_structure_name UNIQUE(school_id, name, academic_year_id)
);

-- Individual fee items within structures
CREATE TABLE finance.fee_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fee_structure_id UUID NOT NULL REFERENCES finance.fee_structures(id) ON DELETE CASCADE,
    fee_category_id UUID NOT NULL REFERENCES finance.fee_categories(id),
    
    -- Item Details
    name VARCHAR(200) NOT NULL, -- 'Tuition Fee - Form 1', 'Transport - Zone A'
    description TEXT,
    
    -- Pricing
    base_amount DECIMAL(12,2) NOT NULL CHECK (base_amount >= 0),
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Frequency and Timing
    frequency VARCHAR(20) NOT NULL DEFAULT 'term' CHECK (frequency IN ('term', 'annual', 'monthly', 'quarterly', 'one_time')),
    due_date_offset_days INTEGER DEFAULT 0, -- Days from term start
    
    -- Payment Rules
    allows_installments BOOLEAN DEFAULT FALSE,
    max_installments INTEGER DEFAULT 1,
    installment_interval_days INTEGER DEFAULT 30,
    
    -- Penalties
    late_fee_amount DECIMAL(12,2) DEFAULT 0.00,
    late_fee_grace_days INTEGER DEFAULT 7,
    daily_penalty_rate DECIMAL(5,4) DEFAULT 0.0000, -- 0.01% per day
    
    -- System Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_installment_config CHECK (
        (allows_installments = FALSE AND max_installments <= 1) OR
        (allows_installments = TRUE AND max_installments > 1)
    ),
    CONSTRAINT unique_fee_item_name UNIQUE(fee_structure_id, name)
);

-- Student fee assignments - link students to fee structures
CREATE TABLE finance.student_fee_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES sis.students(id) ON DELETE CASCADE,
    fee_structure_id UUID NOT NULL REFERENCES finance.fee_structures(id) ON DELETE CASCADE,
    
    -- Assignment Details
    assigned_date DATE NOT NULL DEFAULT CURRENT_DATE,
    effective_from DATE NOT NULL,
    effective_to DATE,
    
    -- Adjustments
    discount_percentage DECIMAL(5,2) DEFAULT 0.00 CHECK (discount_percentage BETWEEN 0 AND 100),
    discount_amount DECIMAL(12,2) DEFAULT 0.00,
    discount_reason TEXT,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'cancelled')),
    
    -- System Fields
    assigned_by UUID NOT NULL REFERENCES platform.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_student_fee_assignment UNIQUE(student_id, fee_structure_id),
    CONSTRAINT valid_effective_dates CHECK (effective_to IS NULL OR effective_to > effective_from),
    CONSTRAINT valid_discount CHECK (discount_percentage >= 0 AND discount_amount >= 0)
);

-- =====================================================
-- INVOICE MANAGEMENT
-- =====================================================

-- Main invoices table
CREATE TABLE finance.invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES platform.schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES sis.students(id) ON DELETE CASCADE,
    
    -- Invoice Information
    invoice_number VARCHAR(50) NOT NULL,
    invoice_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL,
    
    -- Academic Period
    academic_year_id UUID NOT NULL REFERENCES platform.academic_years(id),
    term_id UUID REFERENCES platform.terms(id),
    
    -- Financial Details
    subtotal DECIMAL(12,2) NOT NULL CHECK (subtotal >= 0),
    discount_amount DECIMAL(12,2) DEFAULT 0.00 CHECK (discount_amount >= 0),
    tax_amount DECIMAL(12,2) DEFAULT 0.00 CHECK (tax_amount >= 0),
    total_amount DECIMAL(12,2) NOT NULL CHECK (total_amount >= 0),
    
    -- Payment Status
    paid_amount DECIMAL(12,2) DEFAULT 0.00 CHECK (paid_amount >= 0),
    outstanding_amount DECIMAL(12,2) NOT NULL CHECK (outstanding_amount >= 0),
    payment_status VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'partial', 'paid', 'overdue', 'cancelled')),
    
    -- Late Fees
    late_fee_amount DECIMAL(12,2) DEFAULT 0.00 CHECK (late_fee_amount >= 0),
    penalty_amount DECIMAL(12,2) DEFAULT 0.00 CHECK (penalty_amount >= 0),
    
    -- Currency
    currency VARCHAR(3) DEFAULT 'USD',
    exchange_rate DECIMAL(10,4) DEFAULT 1.0000,
    
    -- Communication
    sent_to_parent BOOLEAN DEFAULT FALSE,
    sent_date TIMESTAMP WITH TIME ZONE,
    reminder_count INTEGER DEFAULT 0,
    last_reminder_date TIMESTAMP WITH TIME ZONE,
    
    -- Status and Notes
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'paid', 'overdue', 'cancelled', 'refunded')),
    notes TEXT,
    
    -- System Fields
    created_by UUID NOT NULL REFERENCES platform.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_invoice_number UNIQUE(school_id, invoice_number),
    CONSTRAINT valid_due_date CHECK (due_date >= invoice_date),
    CONSTRAINT valid_amounts CHECK (
        total_amount = subtotal - discount_amount + tax_amount AND
        outstanding_amount = total_amount - paid_amount + late_fee_amount + penalty_amount
    )
);

-- Invoice line items - detailed breakdown
CREATE TABLE finance.invoice_line_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID NOT NULL REFERENCES finance.invoices(id) ON DELETE CASCADE,
    fee_item_id UUID NOT NULL REFERENCES finance.fee_items(id),
    
    -- Item Details
    description VARCHAR(500) NOT NULL,
    quantity DECIMAL(10,2) DEFAULT 1.00 CHECK (quantity > 0),
    unit_price DECIMAL(12,2) NOT NULL CHECK (unit_price >= 0),
    
    -- Calculations
    discount_percentage DECIMAL(5,2) DEFAULT 0.00 CHECK (discount_percentage BETWEEN 0 AND 100),
    discount_amount DECIMAL(12,2) DEFAULT 0.00 CHECK (discount_amount >= 0),
    line_total DECIMAL(12,2) NOT NULL CHECK (line_total >= 0),
    
    -- System Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_line_calculation CHECK (
        line_total = (quantity * unit_price) - discount_amount
    )
);

-- =====================================================
-- PAYMENT PROCESSING
-- =====================================================

-- Payment methods available
CREATE TABLE finance.payment_methods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES platform.schools(id) ON DELETE CASCADE,
    
    -- Method Information
    name VARCHAR(100) NOT NULL, -- 'Cash', 'EcoCash', 'Bank Transfer', 'Paynow'
    code VARCHAR(20) NOT NULL, -- 'CASH', 'ECOCASH', 'BANK', 'PAYNOW'
    type VARCHAR(20) NOT NULL CHECK (type IN ('cash', 'mobile_money', 'bank_transfer', 'online', 'card')),
    
    -- Configuration
    is_active BOOLEAN DEFAULT TRUE,
    requires_reference BOOLEAN DEFAULT FALSE,
    supports_partial_payment BOOLEAN DEFAULT TRUE,
    
    -- Integration Settings
    gateway_config JSONB, -- API keys, endpoints, etc. (encrypted)
    
    -- Fees
    transaction_fee_percentage DECIMAL(5,2) DEFAULT 0.00,
    transaction_fee_fixed DECIMAL(12,2) DEFAULT 0.00,
    
    -- Display
    display_order INTEGER DEFAULT 1,
    icon_url TEXT,
    
    -- System Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_payment_method_code UNIQUE(school_id, code),
    CONSTRAINT unique_payment_method_name UNIQUE(school_id, name)
);

-- Main payments table
CREATE TABLE finance.payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES platform.schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES sis.students(id) ON DELETE CASCADE,
    
    -- Payment Information
    payment_reference VARCHAR(100) NOT NULL,
    payment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    payment_method_id UUID NOT NULL REFERENCES finance.payment_methods(id),
    
    -- Amount Details
    amount DECIMAL(12,2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(3) DEFAULT 'USD',
    exchange_rate DECIMAL(10,4) DEFAULT 1.0000,
    
    -- Transaction Details
    transaction_id VARCHAR(200), -- External gateway transaction ID
    gateway_reference VARCHAR(200), -- Paynow poll URL or similar
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled', 'refunded')),
    
    -- Gateway Response
    gateway_response JSONB, -- Full response from payment gateway
    failure_reason TEXT,
    
    -- Payer Information
    payer_name VARCHAR(200),
    payer_email VARCHAR(255),
    payer_phone VARCHAR(20),
    
    -- Reconciliation
    reconciled BOOLEAN DEFAULT FALSE,
    reconciled_at TIMESTAMP WITH TIME ZONE,
    reconciled_by UUID REFERENCES platform.users(id),
    
    -- Notes
    notes TEXT,
    
    -- System Fields
    created_by UUID REFERENCES platform.users(id), -- NULL for online payments
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_payment_reference UNIQUE(school_id, payment_reference)
);

-- Payment allocations - link payments to invoices
CREATE TABLE finance.payment_allocations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payment_id UUID NOT NULL REFERENCES finance.payments(id) ON DELETE CASCADE,
    invoice_id UUID NOT NULL REFERENCES finance.invoices(id) ON DELETE CASCADE,
    
    -- Allocation Details
    allocated_amount DECIMAL(12,2) NOT NULL CHECK (allocated_amount > 0),
    allocation_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- System Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(payment_id, invoice_id)
);

-- =====================================================
-- REFUNDS AND CREDITS
-- =====================================================

CREATE TABLE finance.refunds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES platform.schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES sis.students(id) ON DELETE CASCADE,
    
    -- Refund Information
    refund_reference VARCHAR(100) NOT NULL,
    refund_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Original Payment
    original_payment_id UUID REFERENCES finance.payments(id),
    
    -- Refund Details
    refund_amount DECIMAL(12,2) NOT NULL CHECK (refund_amount > 0),
    refund_reason TEXT NOT NULL,
    refund_type VARCHAR(20) NOT NULL CHECK (refund_type IN ('payment_reversal', 'overpayment', 'withdrawal', 'adjustment')),
    
    -- Processing
    refund_method VARCHAR(50) NOT NULL, -- 'bank_transfer', 'cash', 'credit_note'
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP WITH TIME ZONE,
    processed_by UUID REFERENCES platform.users(id),
    
    -- Approval
    approved_by UUID REFERENCES platform.users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'processed', 'cancelled')),
    
    -- System Fields
    created_by UUID NOT NULL REFERENCES platform.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_refund_reference UNIQUE(school_id, refund_reference)
);

-- =====================================================
-- PAYMENT PLANS AND INSTALLMENTS
-- =====================================================

CREATE TABLE finance.payment_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES sis.students(id) ON DELETE CASCADE,
    invoice_id UUID NOT NULL REFERENCES finance.invoices(id) ON DELETE CASCADE,
    
    -- Plan Information
    plan_name VARCHAR(200) NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL CHECK (total_amount > 0),
    
    -- Schedule
    number_of_installments INTEGER NOT NULL CHECK (number_of_installments > 0),
    installment_amount DECIMAL(12,2) NOT NULL CHECK (installment_amount > 0),
    first_installment_date DATE NOT NULL,
    installment_frequency VARCHAR(20) DEFAULT 'monthly' CHECK (installment_frequency IN ('weekly', 'monthly', 'quarterly')),
    
    -- Status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'defaulted', 'cancelled')),
    
    -- Approval
    approved_by UUID REFERENCES platform.users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    
    -- System Fields
    created_by UUID NOT NULL REFERENCES platform.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_payment_plan_per_invoice UNIQUE(invoice_id)
);

-- Individual installments
CREATE TABLE finance.installments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payment_plan_id UUID NOT NULL REFERENCES finance.payment_plans(id) ON DELETE CASCADE,
    
    -- Installment Information
    installment_number INTEGER NOT NULL,
    due_date DATE NOT NULL,
    amount DECIMAL(12,2) NOT NULL CHECK (amount > 0),
    
    -- Payment Status
    paid_amount DECIMAL(12,2) DEFAULT 0.00 CHECK (paid_amount >= 0),
    outstanding_amount DECIMAL(12,2) NOT NULL CHECK (outstanding_amount >= 0),
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'overdue', 'defaulted')),
    paid_date DATE,
    
    -- Late Fees
    late_fee_amount DECIMAL(12,2) DEFAULT 0.00 CHECK (late_fee_amount >= 0),
    
    -- System Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_installment_number UNIQUE(payment_plan_id, installment_number),
    CONSTRAINT valid_installment_amounts CHECK (outstanding_amount = amount - paid_amount + late_fee_amount)
);

-- =====================================================
-- FINANCIAL REPORTING
-- =====================================================

-- Cached financial summaries for performance
CREATE TABLE finance.financial_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES platform.schools(id) ON DELETE CASCADE,
    
    -- Summary Period
    summary_date DATE NOT NULL,
    summary_type VARCHAR(20) NOT NULL CHECK (summary_type IN ('daily', 'weekly', 'monthly', 'quarterly', 'annual')),
    academic_year_id UUID REFERENCES platform.academic_years(id),
    
    -- Revenue Metrics
    total_invoiced DECIMAL(12,2) DEFAULT 0.00,
    total_collected DECIMAL(12,2) DEFAULT 0.00,
    total_outstanding DECIMAL(12,2) DEFAULT 0.00,
    total_overdue DECIMAL(12,2) DEFAULT 0.00,
    
    -- Collection Metrics
    collection_rate DECIMAL(5,2) DEFAULT 0.00,
    average_payment_time_days INTEGER DEFAULT 0,
    
    -- Student Metrics
    students_with_outstanding INTEGER DEFAULT 0,
    students_fully_paid INTEGER DEFAULT 0,
    
    -- System Fields
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_financial_summary UNIQUE(school_id, summary_date, summary_type)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Fee structures and items
CREATE INDEX idx_fee_structures_school_year ON finance.fee_structures(school_id, academic_year_id);
CREATE INDEX idx_fee_structures_status ON finance.fee_structures(status);
CREATE INDEX idx_fee_items_structure ON finance.fee_items(fee_structure_id);
CREATE INDEX idx_fee_items_category ON finance.fee_items(fee_category_id);

-- Student assignments
CREATE INDEX idx_student_assignments_student ON finance.student_fee_assignments(student_id);
CREATE INDEX idx_student_assignments_structure ON finance.student_fee_assignments(fee_structure_id);
CREATE INDEX idx_student_assignments_status ON finance.student_fee_assignments(status);

-- Invoices
CREATE INDEX idx_invoices_school_id ON finance.invoices(school_id);
CREATE INDEX idx_invoices_student_id ON finance.invoices(student_id);
CREATE INDEX idx_invoices_invoice_number ON finance.invoices(invoice_number);
CREATE INDEX idx_invoices_due_date ON finance.invoices(due_date);
CREATE INDEX idx_invoices_payment_status ON finance.invoices(payment_status);
CREATE INDEX idx_invoices_academic_year ON finance.invoices(academic_year_id);
CREATE INDEX idx_invoices_outstanding ON finance.invoices(outstanding_amount) WHERE outstanding_amount > 0;

-- Invoice line items
CREATE INDEX idx_invoice_line_items_invoice ON finance.invoice_line_items(invoice_id);
CREATE INDEX idx_invoice_line_items_fee_item ON finance.invoice_line_items(fee_item_id);

-- Payments
CREATE INDEX idx_payments_school_id ON finance.payments(school_id);
CREATE INDEX idx_payments_student_id ON finance.payments(student_id);
CREATE INDEX idx_payments_reference ON finance.payments(payment_reference);
CREATE INDEX idx_payments_date ON finance.payments(payment_date);
CREATE INDEX idx_payments_status ON finance.payments(status);
CREATE INDEX idx_payments_method ON finance.payments(payment_method_id);
CREATE INDEX idx_payments_transaction_id ON finance.payments(transaction_id) WHERE transaction_id IS NOT NULL;

-- Payment allocations
CREATE INDEX idx_payment_allocations_payment ON finance.payment_allocations(payment_id);
CREATE INDEX idx_payment_allocations_invoice ON finance.payment_allocations(invoice_id);

-- Payment plans
CREATE INDEX idx_payment_plans_student ON finance.payment_plans(student_id);
CREATE INDEX idx_payment_plans_invoice ON finance.payment_plans(invoice_id);
CREATE INDEX idx_payment_plans_status ON finance.payment_plans(status);

-- Installments
CREATE INDEX idx_installments_plan ON finance.installments(payment_plan_id);
CREATE INDEX idx_installments_due_date ON finance.installments(due_date);
CREATE INDEX idx_installments_status ON finance.installments(status);

-- Financial summaries
CREATE INDEX idx_financial_summaries_school_date ON finance.financial_summaries(school_id, summary_date);
CREATE INDEX idx_financial_summaries_type ON finance.financial_summaries(summary_type);

-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE finance.fee_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.fee_structures ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.fee_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.student_fee_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.invoice_line_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.payment_methods ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.payment_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.refunds ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.payment_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.installments ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.financial_summaries ENABLE ROW LEVEL SECURITY;

-- School isolation policies
CREATE POLICY finance_school_isolation_fee_categories ON finance.fee_categories
FOR ALL TO authenticated_user
USING (school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid()));

CREATE POLICY finance_school_isolation_fee_structures ON finance.fee_structures
FOR ALL TO authenticated_user
USING (school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid()));

CREATE POLICY finance_school_isolation_invoices ON finance.invoices
FOR ALL TO authenticated_user
USING (school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid()));

CREATE POLICY finance_school_isolation_payments ON finance.payments
FOR ALL TO authenticated_user
USING (school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid()));

CREATE POLICY finance_school_isolation_refunds ON finance.refunds
FOR ALL TO authenticated_user
USING (school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid()));

CREATE POLICY finance_school_isolation_payment_methods ON finance.payment_methods
FOR ALL TO authenticated_user
USING (school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid()));

CREATE POLICY finance_school_isolation_summaries ON finance.financial_summaries
FOR ALL TO authenticated_user
USING (school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid()));

-- Student-specific policies for guardians
CREATE POLICY finance_guardian_access_invoices ON finance.invoices
FOR SELECT TO authenticated_user
USING (
    student_id IN (
        SELECT student_id FROM sis.student_guardians 
        WHERE guardian_user_id = auth.uid()
    )
);

CREATE POLICY finance_guardian_access_payments ON finance.payments
FOR SELECT TO authenticated_user
USING (
    student_id IN (
        SELECT student_id FROM sis.student_guardians 
        WHERE guardian_user_id = auth.uid()
    )
);

-- Fee items access through structure
CREATE POLICY finance_fee_items_access ON finance.fee_items
FOR ALL TO authenticated_user
USING (
    fee_structure_id IN (
        SELECT id FROM finance.fee_structures 
        WHERE school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid())
    )
);

-- Student assignments access
CREATE POLICY finance_student_assignments_access ON finance.student_fee_assignments
FOR ALL TO authenticated_user
USING (
    student_id IN (
        SELECT id FROM sis.students 
        WHERE school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid())
    )
);

-- Invoice line items access
CREATE POLICY finance_invoice_line_items_access ON finance.invoice_line_items
FOR ALL TO authenticated_user
USING (
    invoice_id IN (
        SELECT id FROM finance.invoices 
        WHERE school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid())
    )
);

-- Payment allocations access
CREATE POLICY finance_payment_allocations_access ON finance.payment_allocations
FOR ALL TO authenticated_user
USING (
    payment_id IN (
        SELECT id FROM finance.payments 
        WHERE school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid())
    )
);

-- Payment plans access
CREATE POLICY finance_payment_plans_access ON finance.payment_plans
FOR ALL TO authenticated_user
USING (
    student_id IN (
        SELECT id FROM sis.students 
        WHERE school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid())
    )
);

-- Installments access
CREATE POLICY finance_installments_access ON finance.installments
FOR ALL TO authenticated_user
USING (
    payment_plan_id IN (
        SELECT id FROM finance.payment_plans 
        WHERE student_id IN (
            SELECT id FROM sis.students 
            WHERE school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid())
        )
    )
);

-- =====================================================
-- UTILITY FUNCTIONS
-- =====================================================

-- Generate invoice number
CREATE OR REPLACE FUNCTION finance.generate_invoice_number(p_school_id UUID, p_year INTEGER DEFAULT NULL)
RETURNS VARCHAR(50) AS $$
DECLARE
    v_year INTEGER;
    v_next_sequence INTEGER;
    v_invoice_number VARCHAR(50);
BEGIN
    v_year := COALESCE(p_year, EXTRACT(YEAR FROM CURRENT_DATE));
    
    -- Get the next sequence number for this year and school
    SELECT COALESCE(MAX(CAST(SUBSTRING(invoice_number FROM '[0-9]+$') AS INTEGER)), 0) + 1
    INTO v_next_sequence
    FROM finance.invoices 
    WHERE school_id = p_school_id 
    AND invoice_number LIKE 'INV-' || v_year::text || '-%';
    
    -- Format: INV-YYYY-NNNNN (e.g., INV-2024-00001)
    v_invoice_number := 'INV-' || v_year::text || '-' || LPAD(v_next_sequence::text, 5, '0');
    
    RETURN v_invoice_number;
END;
$$ LANGUAGE plpgsql;

-- Generate payment reference
CREATE OR REPLACE FUNCTION finance.generate_payment_reference(p_school_id UUID)
RETURNS VARCHAR(100) AS $$
DECLARE
    v_timestamp VARCHAR(20);
    v_school_code VARCHAR(10);
    v_random VARCHAR(10);
    v_reference VARCHAR(100);
BEGIN
    -- Get timestamp
    v_timestamp := TO_CHAR(NOW(), 'YYYYMMDDHH24MISS');
    
    -- Get school code (first 3 chars of school name)
    SELECT UPPER(LEFT(name, 3)) INTO v_school_code
    FROM platform.schools 
    WHERE id = p_school_id;
    
    -- Generate random string
    v_random := UPPER(LEFT(md5(random()::text), 4));
    
    -- Format: PAY-SCH-20240717143022-A1B2
    v_reference := 'PAY-' || v_school_code || '-' || v_timestamp || '-' || v_random;
    
    RETURN v_reference;
END;
$$ LANGUAGE plpgsql;

-- Calculate outstanding amount for invoice
CREATE OR REPLACE FUNCTION finance.calculate_outstanding_amount(p_invoice_id UUID)
RETURNS DECIMAL(12,2) AS $$
DECLARE
    v_total_amount DECIMAL(12,2);
    v_paid_amount DECIMAL(12,2);
    v_late_fees DECIMAL(12,2);
    v_penalties DECIMAL(12,2);
    v_outstanding DECIMAL(12,2);
BEGIN
    SELECT 
        i.total_amount,
        i.late_fee_amount,
        i.penalty_amount,
        COALESCE(SUM(pa.allocated_amount), 0)
    INTO v_total_amount, v_late_fees, v_penalties, v_paid_amount
    FROM finance.invoices i
    LEFT JOIN finance.payment_allocations pa ON i.id = pa.invoice_id
    LEFT JOIN finance.payments p ON pa.payment_id = p.id AND p.status = 'completed'
    WHERE i.id = p_invoice_id
    GROUP BY i.id, i.total_amount, i.late_fee_amount, i.penalty_amount;
    
    v_outstanding := v_total_amount - v_paid_amount + v_late_fees + v_penalties;
    
    RETURN GREATEST(v_outstanding, 0);
END;
$$ LANGUAGE plpgsql;

-- Update invoice payment status
CREATE OR REPLACE FUNCTION finance.update_invoice_payment_status(p_invoice_id UUID)
RETURNS VOID AS $$
DECLARE
    v_outstanding DECIMAL(12,2);
    v_new_status VARCHAR(20);
    v_due_date DATE;
BEGIN
    -- Calculate outstanding amount
    v_outstanding := finance.calculate_outstanding_amount(p_invoice_id);
    
    -- Get due date
    SELECT due_date INTO v_due_date
    FROM finance.invoices
    WHERE id = p_invoice_id;
    
    -- Determine new status
    IF v_outstanding = 0 THEN
        v_new_status := 'paid';
    ELSIF v_outstanding > 0 AND v_due_date < CURRENT_DATE THEN
        v_new_status := 'overdue';
    ELSIF v_outstanding > 0 THEN
        SELECT 
            CASE 
                WHEN paid_amount > 0 THEN 'partial'
                ELSE 'pending'
            END
        INTO v_new_status
        FROM finance.invoices
        WHERE id = p_invoice_id;
    END IF;
    
    -- Update invoice
    UPDATE finance.invoices
    SET 
        outstanding_amount = v_outstanding,
        payment_status = v_new_status,
        updated_at = NOW()
    WHERE id = p_invoice_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =====================================================

-- Update timestamp trigger function (reuse from SIS)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update triggers to all tables
CREATE TRIGGER update_fee_categories_updated_at BEFORE UPDATE ON finance.fee_categories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_fee_structures_updated_at BEFORE UPDATE ON finance.fee_structures FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_fee_items_updated_at BEFORE UPDATE ON finance.fee_items FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_student_assignments_updated_at BEFORE UPDATE ON finance.student_fee_assignments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_invoices_updated_at BEFORE UPDATE ON finance.invoices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_payment_methods_updated_at BEFORE UPDATE ON finance.payment_methods FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_payments_updated_at BEFORE UPDATE ON finance.payments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_refunds_updated_at BEFORE UPDATE ON finance.refunds FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_payment_plans_updated_at BEFORE UPDATE ON finance.payment_plans FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_installments_updated_at BEFORE UPDATE ON finance.installments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-generate invoice number trigger
CREATE OR REPLACE FUNCTION finance.auto_generate_invoice_number()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.invoice_number IS NULL OR NEW.invoice_number = '' THEN
        NEW.invoice_number := finance.generate_invoice_number(NEW.school_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auto_invoice_number BEFORE INSERT ON finance.invoices FOR EACH ROW EXECUTE FUNCTION finance.auto_generate_invoice_number();

-- Auto-generate payment reference trigger
CREATE OR REPLACE FUNCTION finance.auto_generate_payment_reference()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.payment_reference IS NULL OR NEW.payment_reference = '' THEN
        NEW.payment_reference := finance.generate_payment_reference(NEW.school_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auto_payment_reference BEFORE INSERT ON finance.payments FOR EACH ROW EXECUTE FUNCTION finance.auto_generate_payment_reference();

-- Update invoice status after payment allocation
CREATE OR REPLACE FUNCTION finance.update_invoice_after_payment()
RETURNS TRIGGER AS $$
BEGIN
    -- Update invoice payment status
    PERFORM finance.update_invoice_payment_status(NEW.invoice_id);
    
    -- Update paid amount
    UPDATE finance.invoices
    SET paid_amount = (
        SELECT COALESCE(SUM(pa.allocated_amount), 0)
        FROM finance.payment_allocations pa
        JOIN finance.payments p ON pa.payment_id = p.id
        WHERE pa.invoice_id = NEW.invoice_id
        AND p.status = 'completed'
    )
    WHERE id = NEW.invoice_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_invoice_after_payment AFTER INSERT OR UPDATE ON finance.payment_allocations FOR EACH ROW EXECUTE FUNCTION finance.update_invoice_after_payment();

-- =====================================================
-- COMMENTS AND DOCUMENTATION
-- =====================================================

COMMENT ON SCHEMA finance IS 'Finance & Billing System - Complete schema for fee management, invoicing, and payment processing';
COMMENT ON TABLE finance.fee_categories IS 'Categories for different types of fees (tuition, transport, etc.)';
COMMENT ON TABLE finance.fee_structures IS 'Templates for fee structures by grade/year';
COMMENT ON TABLE finance.fee_items IS 'Individual fee components within structures';
COMMENT ON TABLE finance.student_fee_assignments IS 'Links students to their applicable fee structures';
COMMENT ON TABLE finance.invoices IS 'Generated invoices for student fees';
COMMENT ON TABLE finance.invoice_line_items IS 'Detailed breakdown of invoice charges';
COMMENT ON TABLE finance.payment_methods IS 'Available payment methods for the school';
COMMENT ON TABLE finance.payments IS 'All payment transactions';
COMMENT ON TABLE finance.payment_allocations IS 'Links payments to specific invoices';
COMMENT ON TABLE finance.refunds IS 'Refund and credit transactions';
COMMENT ON TABLE finance.payment_plans IS 'Custom payment schedules for students';
COMMENT ON TABLE finance.installments IS 'Individual installment records';
COMMENT ON TABLE finance.financial_summaries IS 'Cached financial reports for performance';