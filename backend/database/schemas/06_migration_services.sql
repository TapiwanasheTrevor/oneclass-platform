-- Migration Services Schema
-- Professional data migration and care package management system
-- Version: 1.0
-- Created: 2025-07-18

-- Create migration services schema
CREATE SCHEMA IF NOT EXISTS migration_services;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Care Package Definitions
CREATE TABLE migration_services.care_packages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL, -- 'Foundation', 'Growth', 'Enterprise'
    price_usd DECIMAL(10,2) NOT NULL,
    price_zwl DECIMAL(15,2) NOT NULL, -- Updated with exchange rate
    max_students INTEGER,
    max_historical_years INTEGER,
    features JSONB NOT NULL,
    inclusions TEXT[],
    exclusions TEXT[],
    estimated_duration_days INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Care Package Orders
CREATE TABLE migration_services.care_package_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_number VARCHAR(20) UNIQUE NOT NULL, -- CP-2025-001
    school_id UUID NOT NULL REFERENCES platform.schools(id),
    care_package_id UUID NOT NULL REFERENCES migration_services.care_packages(id),
    
    -- Order Details
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    requested_start_date DATE,
    estimated_completion_date DATE,
    actual_completion_date DATE,
    
    -- Status Management
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'approved', 'in_progress', 'data_migration', 'system_setup',
        'training', 'testing', 'go_live', 'completed', 'cancelled'
    )),
    
    -- Pricing & Payment
    package_price DECIMAL(10,2) NOT NULL,
    additional_costs DECIMAL(10,2) DEFAULT 0,
    total_price DECIMAL(10,2) GENERATED ALWAYS AS (package_price + additional_costs) STORED,
    currency VARCHAR(3) DEFAULT 'USD',
    payment_option VARCHAR(20) DEFAULT 'split' CHECK (payment_option IN (
        'full_upfront', 'split', 'extended'
    )),
    payment_status VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN (
        'pending', 'deposit_paid', 'fully_paid', 'refunded'
    )),
    
    -- Team Assignment
    assigned_migration_manager UUID REFERENCES platform.users(id),
    assigned_technical_lead UUID REFERENCES platform.users(id),
    assigned_data_specialist UUID REFERENCES platform.users(id),
    assigned_training_specialist UUID REFERENCES platform.users(id),
    
    -- Requirements & Customization
    student_count INTEGER,
    current_system_type VARCHAR(50), -- 'excel', 'paper', 'legacy_software'
    data_sources_description TEXT,
    special_requirements TEXT,
    custom_integrations_needed TEXT[],
    
    -- Additional Options
    urgent_migration BOOLEAN DEFAULT FALSE,
    onsite_training BOOLEAN DEFAULT FALSE,
    weekend_work BOOLEAN DEFAULT FALSE,
    
    -- Progress Tracking
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage BETWEEN 0 AND 100),
    estimated_hours INTEGER,
    actual_hours INTEGER DEFAULT 0,
    
    -- Communication
    primary_contact_name VARCHAR(100),
    primary_contact_email VARCHAR(255),
    primary_contact_phone VARCHAR(20),
    secondary_contact_name VARCHAR(100),
    secondary_contact_email VARCHAR(255),
    
    -- Notes & Documentation
    initial_assessment_notes TEXT,
    completion_notes TEXT,
    customer_feedback TEXT,
    internal_notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Migration Project Tasks
CREATE TABLE migration_services.migration_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    care_package_order_id UUID NOT NULL REFERENCES migration_services.care_package_orders(id),
    phase VARCHAR(30) NOT NULL, -- 'discovery', 'data_extraction', 'system_setup', etc.
    task_name VARCHAR(255) NOT NULL,
    description TEXT,
    assigned_to UUID REFERENCES platform.users(id),
    
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN (
        'pending', 'in_progress', 'blocked', 'review', 'completed', 'skipped'
    )),
    priority VARCHAR(10) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2) DEFAULT 0,
    
    due_date DATE,
    completion_date DATE,
    
    -- Dependencies
    depends_on UUID REFERENCES migration_services.migration_tasks(id),
    blocking_reason TEXT,
    
    -- Documentation
    task_notes TEXT,
    completion_notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Data Sources & Files
CREATE TABLE migration_services.data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    care_package_order_id UUID NOT NULL REFERENCES migration_services.care_package_orders(id),
    source_name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- 'excel', 'csv', 'database', 'paper', 'api'
    file_path TEXT,
    file_size BIGINT,
    record_count INTEGER,
    
    status VARCHAR(20) DEFAULT 'received' CHECK (status IN (
        'received', 'analyzed', 'cleaned', 'validated', 'imported', 'verified'
    )),
    
    -- Analysis Results
    data_quality_score INTEGER CHECK (data_quality_score BETWEEN 0 AND 100),
    issues_found TEXT[],
    cleaning_notes TEXT,
    
    processed_at TIMESTAMP WITH TIME ZONE,
    processed_by UUID REFERENCES platform.users(id),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Communication Log
CREATE TABLE migration_services.communication_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    care_package_order_id UUID NOT NULL REFERENCES migration_services.care_package_orders(id),
    communication_type VARCHAR(20) NOT NULL, -- 'email', 'phone', 'meeting', 'system'
    direction VARCHAR(10) NOT NULL, -- 'inbound', 'outbound'
    subject VARCHAR(255),
    content TEXT,
    participants TEXT[], -- Array of email addresses or names
    
    -- Metadata
    created_by UUID REFERENCES platform.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Payment Tracking
CREATE TABLE migration_services.payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    care_package_order_id UUID NOT NULL REFERENCES migration_services.care_package_orders(id),
    payment_type VARCHAR(20) NOT NULL, -- 'deposit', 'milestone', 'final', 'refund'
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    
    payment_method VARCHAR(20), -- 'bank_transfer', 'ecocash', 'cash', 'cheque'
    reference_number VARCHAR(100),
    
    due_date DATE,
    paid_date DATE,
    
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN (
        'pending', 'paid', 'overdue', 'cancelled', 'refunded'
    )),
    
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Migration Milestones
CREATE TABLE migration_services.milestones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    care_package_order_id UUID NOT NULL REFERENCES migration_services.care_package_orders(id),
    milestone_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Sequencing
    sequence_order INTEGER NOT NULL,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN (
        'pending', 'in_progress', 'completed', 'skipped'
    )),
    
    -- Timeline
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    
    -- Deliverables
    deliverables TEXT[],
    acceptance_criteria TEXT[],
    
    -- Notes
    completion_notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Team Performance Metrics
CREATE TABLE migration_services.team_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES platform.users(id),
    month_year DATE NOT NULL, -- First day of month
    
    -- Project Metrics
    projects_assigned INTEGER DEFAULT 0,
    projects_completed INTEGER DEFAULT 0,
    projects_delayed INTEGER DEFAULT 0,
    
    -- Time Metrics
    billable_hours DECIMAL(6,2) DEFAULT 0,
    utilization_percentage DECIMAL(5,2) DEFAULT 0,
    
    -- Quality Metrics
    customer_satisfaction_avg DECIMAL(3,2) DEFAULT 0,
    on_time_delivery_rate DECIMAL(5,2) DEFAULT 0,
    
    -- Performance Rating
    overall_rating DECIMAL(3,2) DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, month_year)
);

-- Create indexes for performance
CREATE INDEX idx_care_package_orders_school_id ON migration_services.care_package_orders(school_id);
CREATE INDEX idx_care_package_orders_status ON migration_services.care_package_orders(status);
CREATE INDEX idx_care_package_orders_order_date ON migration_services.care_package_orders(order_date);
CREATE INDEX idx_care_package_orders_assigned_manager ON migration_services.care_package_orders(assigned_migration_manager);

CREATE INDEX idx_migration_tasks_order_id ON migration_services.migration_tasks(care_package_order_id);
CREATE INDEX idx_migration_tasks_status ON migration_services.migration_tasks(status);
CREATE INDEX idx_migration_tasks_assigned_to ON migration_services.migration_tasks(assigned_to);

CREATE INDEX idx_data_sources_order_id ON migration_services.data_sources(care_package_order_id);
CREATE INDEX idx_data_sources_status ON migration_services.data_sources(status);

CREATE INDEX idx_communication_log_order_id ON migration_services.communication_log(care_package_order_id);
CREATE INDEX idx_communication_log_type ON migration_services.communication_log(communication_type);

CREATE INDEX idx_payments_order_id ON migration_services.payments(care_package_order_id);
CREATE INDEX idx_payments_status ON migration_services.payments(status);

CREATE INDEX idx_milestones_order_id ON migration_services.milestones(care_package_order_id);
CREATE INDEX idx_milestones_status ON migration_services.milestones(status);

CREATE INDEX idx_team_performance_user_month ON migration_services.team_performance(user_id, month_year);

-- Create trigger for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_care_packages_updated_at BEFORE UPDATE ON migration_services.care_packages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_care_package_orders_updated_at BEFORE UPDATE ON migration_services.care_package_orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_migration_tasks_updated_at BEFORE UPDATE ON migration_services.migration_tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_milestones_updated_at BEFORE UPDATE ON migration_services.milestones FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_team_performance_updated_at BEFORE UPDATE ON migration_services.team_performance FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default care packages
INSERT INTO migration_services.care_packages (name, price_usd, price_zwl, max_students, max_historical_years, features, inclusions, exclusions, estimated_duration_days) VALUES
(
    'Foundation Package',
    2800.00,
    4480000.00,
    200,
    1,
    '{"student_migration": true, "basic_branding": true, "training_hours": 4, "support_days": 30}',
    ARRAY[
        'Up to 200 current students',
        'Basic parent/guardian contacts',
        'Current year class assignments',
        'School branding setup',
        'Basic fee structure (3 types)',
        '15 staff user accounts',
        '4-hour virtual training',
        '30-day email support'
    ],
    ARRAY[
        'Historical data beyond current year',
        'Financial record migration',
        'Attendance history',
        'Custom integrations'
    ],
    14
),
(
    'Growth Package',
    6500.00,
    10400000.00,
    800,
    3,
    '{"student_migration": true, "financial_migration": true, "training_hours": 12, "support_days": 90, "onsite_training": true}',
    ARRAY[
        'Up to 800 students (3-year history)',
        'Complete academic records',
        'Financial data migration',
        '40 staff user accounts',
        'Payment gateway setup',
        '12-hour role-based training',
        'On-site training option (+$800)',
        '90-day priority support'
    ],
    ARRAY[
        'Government system integration',
        'Multi-campus setup',
        'Alumni database'
    ],
    21
),
(
    'Enterprise Package',
    15000.00,
    24000000.00,
    NULL,
    5,
    '{"unlimited_students": true, "government_integration": true, "multi_campus": true, "training_hours": 24, "support_months": 6, "dedicated_manager": true}',
    ARRAY[
        'Unlimited students (5+ year history)',
        'Government system integration',
        'Multi-campus support',
        'Alumni database integration',
        'Custom API development',
        '24-hour training program',
        'On-site change management',
        '6-month dedicated support'
    ],
    ARRAY[],
    30
);

-- Insert default milestones template
INSERT INTO migration_services.milestones (care_package_order_id, milestone_name, description, sequence_order, deliverables, acceptance_criteria)
SELECT 
    NULL as care_package_order_id, -- Template milestones
    milestone_name,
    description,
    sequence_order,
    deliverables,
    acceptance_criteria
FROM (VALUES
    ('Project Kickoff', 'Initial assessment and project planning', 1, ARRAY['Project plan document', 'Requirements assessment'], ARRAY['Project team assigned', 'Kickoff meeting completed']),
    ('Data Collection', 'Gather all source data from school', 2, ARRAY['Data inventory', 'Data quality assessment'], ARRAY['All data sources identified', 'Data quality report completed']),
    ('Data Analysis', 'Analyze and clean collected data', 3, ARRAY['Cleaned dataset', 'Data mapping document'], ARRAY['Data quality score > 85%', 'Mapping approved by school']),
    ('System Configuration', 'Set up OneClass instance for school', 4, ARRAY['Configured system', 'Branding implementation'], ARRAY['System configured per requirements', 'School branding applied']),
    ('Data Migration', 'Import all data into OneClass system', 5, ARRAY['Migrated data', 'Migration report'], ARRAY['100% critical data migrated', 'Data validation tests passed']),
    ('User Setup', 'Create user accounts and permissions', 6, ARRAY['User accounts', 'Permission matrix'], ARRAY['All staff accounts created', 'Permissions tested']),
    ('Training Delivery', 'Conduct user training sessions', 7, ARRAY['Training materials', 'Training completion certificates'], ARRAY['All users trained', 'Training evaluation > 4.0']),
    ('System Testing', 'End-to-end testing with school staff', 8, ARRAY['Test results', 'Issue resolution'], ARRAY['All critical workflows tested', 'No blocking issues']),
    ('Go Live', 'Launch system for production use', 9, ARRAY['Go-live checklist', 'Support plan'], ARRAY['System live and operational', 'Support team ready']),
    ('Project Closure', 'Complete project and handover', 10, ARRAY['Project completion report', 'Customer satisfaction survey'], ARRAY['All deliverables completed', 'Customer sign-off received'])
) AS milestones(milestone_name, description, sequence_order, deliverables, acceptance_criteria);

-- Create function to generate order number
CREATE OR REPLACE FUNCTION generate_order_number()
RETURNS VARCHAR(20) AS $$
DECLARE
    year_part VARCHAR(4);
    sequence_part VARCHAR(3);
    next_sequence INTEGER;
BEGIN
    year_part := EXTRACT(YEAR FROM CURRENT_DATE)::VARCHAR;
    
    SELECT COALESCE(MAX(CAST(SUBSTRING(order_number FROM 9 FOR 3) AS INTEGER)), 0) + 1
    INTO next_sequence
    FROM migration_services.care_package_orders
    WHERE order_number LIKE 'CP-' || year_part || '-%';
    
    sequence_part := LPAD(next_sequence::VARCHAR, 3, '0');
    
    RETURN 'CP-' || year_part || '-' || sequence_part;
END;
$$ LANGUAGE plpgsql;

-- Create RLS policies for multi-tenancy
ALTER TABLE migration_services.care_package_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE migration_services.migration_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE migration_services.data_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE migration_services.communication_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE migration_services.payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE migration_services.milestones ENABLE ROW LEVEL SECURITY;

-- RLS policies (Super admin can see all, schools can only see their own)
CREATE POLICY school_orders_policy ON migration_services.care_package_orders
FOR ALL USING (
    school_id = current_setting('app.current_school_id')::uuid OR
    current_setting('app.user_role') = 'platform_admin'
);

CREATE POLICY order_tasks_policy ON migration_services.migration_tasks
FOR ALL USING (
    EXISTS (
        SELECT 1 FROM migration_services.care_package_orders 
        WHERE id = care_package_order_id 
        AND (school_id = current_setting('app.current_school_id')::uuid OR
             current_setting('app.user_role') = 'platform_admin')
    )
);

CREATE POLICY order_data_sources_policy ON migration_services.data_sources
FOR ALL USING (
    EXISTS (
        SELECT 1 FROM migration_services.care_package_orders 
        WHERE id = care_package_order_id 
        AND (school_id = current_setting('app.current_school_id')::uuid OR
             current_setting('app.user_role') = 'platform_admin')
    )
);

CREATE POLICY order_communication_policy ON migration_services.communication_log
FOR ALL USING (
    EXISTS (
        SELECT 1 FROM migration_services.care_package_orders 
        WHERE id = care_package_order_id 
        AND (school_id = current_setting('app.current_school_id')::uuid OR
             current_setting('app.user_role') = 'platform_admin')
    )
);

CREATE POLICY order_payments_policy ON migration_services.payments
FOR ALL USING (
    EXISTS (
        SELECT 1 FROM migration_services.care_package_orders 
        WHERE id = care_package_order_id 
        AND (school_id = current_setting('app.current_school_id')::uuid OR
             current_setting('app.user_role') = 'platform_admin')
    )
);

CREATE POLICY order_milestones_policy ON migration_services.milestones
FOR ALL USING (
    EXISTS (
        SELECT 1 FROM migration_services.care_package_orders 
        WHERE id = care_package_order_id 
        AND (school_id = current_setting('app.current_school_id')::uuid OR
             current_setting('app.user_role') = 'platform_admin')
    )
);

-- Comments for documentation
COMMENT ON SCHEMA migration_services IS 'Professional migration services and care package management';
COMMENT ON TABLE migration_services.care_packages IS 'Available care package definitions (Foundation, Growth, Enterprise)';
COMMENT ON TABLE migration_services.care_package_orders IS 'School orders for migration services';
COMMENT ON TABLE migration_services.migration_tasks IS 'Individual tasks within migration projects';
COMMENT ON TABLE migration_services.data_sources IS 'Source data files and systems for migration';
COMMENT ON TABLE migration_services.communication_log IS 'All communication history for migration projects';
COMMENT ON TABLE migration_services.payments IS 'Payment tracking for care packages';
COMMENT ON TABLE migration_services.milestones IS 'Project milestones and deliverables';
COMMENT ON TABLE migration_services.team_performance IS 'Team member performance metrics and KPIs';