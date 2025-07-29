-- =====================================================
-- Analytics Schema Migration
-- Creates analytics and reporting tables for OneClass Platform
-- =====================================================

-- Create analytics schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS analytics;

-- Drop existing tables in correct order
DROP TABLE IF EXISTS analytics.report_executions CASCADE;
DROP TABLE IF EXISTS analytics.report_templates CASCADE;
DROP TABLE IF EXISTS analytics.analytics_snapshots CASCADE;

-- Create Analytics Snapshots table
CREATE TABLE analytics.analytics_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL,
    
    -- Snapshot metadata
    snapshot_type VARCHAR(20) NOT NULL CHECK (snapshot_type IN ('daily', 'weekly', 'monthly', 'yearly')),
    snapshot_date TIMESTAMP WITH TIME ZONE NOT NULL,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Student metrics
    total_students INTEGER DEFAULT 0,
    active_students INTEGER DEFAULT 0,
    new_enrollments INTEGER DEFAULT 0,
    withdrawals INTEGER DEFAULT 0,
    
    -- Academic metrics
    average_attendance_rate DECIMAL(5,2) DEFAULT 0.0,
    total_classes_held INTEGER DEFAULT 0,
    average_grade DECIMAL(5,2) DEFAULT 0.0,
    pass_rate DECIMAL(5,2) DEFAULT 0.0,
    
    -- Financial metrics
    total_fees_collected DECIMAL(12,2) DEFAULT 0.0,
    outstanding_fees DECIMAL(12,2) DEFAULT 0.0,
    fee_collection_rate DECIMAL(5,2) DEFAULT 0.0,
    
    -- Staff metrics
    total_staff INTEGER DEFAULT 0,
    teacher_student_ratio DECIMAL(5,2) DEFAULT 0.0,
    
    -- System usage metrics
    total_logins INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    
    -- Additional data (JSON)
    metrics_data JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for analytics snapshots
CREATE INDEX idx_analytics_snapshots_school_id ON analytics.analytics_snapshots(school_id);
CREATE INDEX idx_analytics_snapshots_date ON analytics.analytics_snapshots(snapshot_date);
CREATE INDEX idx_analytics_snapshots_type ON analytics.analytics_snapshots(snapshot_type);
CREATE UNIQUE INDEX idx_analytics_snapshots_unique ON analytics.analytics_snapshots(school_id, snapshot_type, snapshot_date);

-- Create Report Templates table
CREATE TABLE analytics.report_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL,
    
    -- Template metadata
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL CHECK (category IN ('academic', 'financial', 'administrative', 'analytics', 'custom')),
    
    -- Template configuration
    report_type VARCHAR(50) NOT NULL CHECK (report_type IN ('table', 'chart', 'dashboard', 'pdf')),
    data_sources JSONB NOT NULL,
    filters JSONB DEFAULT '{}',
    columns JSONB DEFAULT '[]',
    charts JSONB DEFAULT '[]',
    
    -- Access control
    created_by UUID NOT NULL,
    is_public BOOLEAN DEFAULT false,
    allowed_roles JSONB DEFAULT '[]',
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for report templates
CREATE INDEX idx_report_templates_school_id ON analytics.report_templates(school_id);
CREATE INDEX idx_report_templates_category ON analytics.report_templates(category);
CREATE INDEX idx_report_templates_created_by ON analytics.report_templates(created_by);
CREATE INDEX idx_report_templates_public ON analytics.report_templates(is_public);

-- Create Report Executions table
CREATE TABLE analytics.report_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL,
    template_id UUID NOT NULL REFERENCES analytics.report_templates(id) ON DELETE CASCADE,
    
    -- Execution metadata
    executed_by UUID NOT NULL,
    execution_date TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Parameters and filters used
    parameters JSONB DEFAULT '{}',
    filters_applied JSONB DEFAULT '{}',
    
    -- Execution results
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    execution_time_ms INTEGER,
    row_count INTEGER,
    file_path VARCHAR(500),
    
    -- Error handling
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for report executions
CREATE INDEX idx_report_executions_school_id ON analytics.report_executions(school_id);
CREATE INDEX idx_report_executions_template_id ON analytics.report_executions(template_id);
CREATE INDEX idx_report_executions_executed_by ON analytics.report_executions(executed_by);
CREATE INDEX idx_report_executions_date ON analytics.report_executions(execution_date);
CREATE INDEX idx_report_executions_status ON analytics.report_executions(status);

-- Create updated_at trigger for analytics tables
CREATE TRIGGER update_analytics_snapshots_updated_at 
    BEFORE UPDATE ON analytics.analytics_snapshots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_report_templates_updated_at 
    BEFORE UPDATE ON analytics.report_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample analytics snapshots
INSERT INTO analytics.analytics_snapshots (
    school_id, snapshot_type, snapshot_date, period_start, period_end,
    total_students, active_students, new_enrollments, withdrawals,
    average_attendance_rate, average_grade, pass_rate,
    total_fees_collected, outstanding_fees, fee_collection_rate,
    total_staff, teacher_student_ratio, total_logins, active_users
) VALUES 
-- Demo High School snapshots
('550e8400-e29b-41d4-a716-446655440001', 'monthly', '2024-01-01', '2024-01-01', '2024-01-31',
 450, 425, 25, 5, 87.5, 78.2, 82.5, 125000.00, 15000.00, 89.3, 35, 12.8, 1250, 380),
('550e8400-e29b-41d4-a716-446655440001', 'monthly', '2024-02-01', '2024-02-01', '2024-02-29',
 465, 440, 20, 5, 89.1, 79.5, 85.2, 130000.00, 12000.00, 91.5, 35, 13.3, 1380, 395),
('550e8400-e29b-41d4-a716-446655440001', 'monthly', '2024-03-01', '2024-03-01', '2024-03-31',
 475, 455, 15, 5, 88.7, 80.1, 86.8, 135000.00, 10000.00, 93.1, 36, 13.2, 1420, 410),

-- Test Primary School snapshots
('550e8400-e29b-41d4-a716-446655440002', 'monthly', '2024-01-01', '2024-01-01', '2024-01-31',
 280, 265, 18, 3, 91.2, 82.5, 88.9, 75000.00, 8000.00, 90.3, 22, 12.7, 850, 240),
('550e8400-e29b-41d4-a716-446655440002', 'monthly', '2024-02-01', '2024-02-01', '2024-02-29',
 290, 275, 12, 2, 92.5, 83.8, 90.1, 78000.00, 6000.00, 92.8, 22, 13.2, 920, 255),
('550e8400-e29b-41d4-a716-446655440002', 'monthly', '2024-03-01', '2024-03-01', '2024-03-31',
 295, 285, 8, 3, 93.1, 84.2, 91.5, 82000.00, 5000.00, 94.2, 23, 12.8, 980, 270),

-- Enterprise Academy snapshots
('550e8400-e29b-41d4-a716-446655440003', 'monthly', '2024-01-01', '2024-01-01', '2024-01-31',
 650, 620, 35, 8, 85.8, 85.2, 89.5, 195000.00, 25000.00, 88.7, 48, 13.5, 1850, 580),
('550e8400-e29b-41d4-a716-446655440003', 'monthly', '2024-02-01', '2024-02-01', '2024-02-29',
 670, 645, 28, 8, 87.2, 86.1, 90.8, 205000.00, 20000.00, 91.1, 49, 13.7, 1950, 610),
('550e8400-e29b-41d4-a716-446655440003', 'monthly', '2024-03-01', '2024-03-01', '2024-03-31',
 685, 665, 22, 7, 88.5, 86.8, 92.2, 215000.00, 18000.00, 92.3, 50, 13.7, 2050, 640);

-- Insert sample report templates
INSERT INTO analytics.report_templates (
    id, school_id, name, description, category, report_type, data_sources, 
    filters, columns, charts, created_by, is_public, allowed_roles
) VALUES 
-- Academic reports
('a1000000-0000-0000-0000-000000000001', '550e8400-e29b-41d4-a716-446655440001',
 'Student Performance Summary', 'Overview of student academic performance by grade and subject',
 'academic', 'table', 
 '[{"source": "sis.students", "joins": ["academic.grades"]}, {"source": "academic.subjects"}]',
 '{"grade_levels": [], "subjects": [], "date_range": {"start": null, "end": null}}',
 '[{"field": "student_name", "title": "Student Name", "type": "text"}, {"field": "grade_level", "title": "Grade", "type": "text"}, {"field": "average_grade", "title": "Average Grade", "type": "percentage"}]',
 '[{"type": "bar", "title": "Grade Distribution", "data_field": "grade_distribution"}]',
 '550e8400-e29b-41d4-a716-446655440101', true, '["admin", "teacher"]'),

-- Financial reports
('a2000000-0000-0000-0000-000000000001', '550e8400-e29b-41d4-a716-446655440001',
 'Fee Collection Report', 'Detailed fee collection analysis with payment tracking',
 'financial', 'dashboard',
 '[{"source": "finance.invoices"}, {"source": "finance.payments"}]',
 '{"payment_status": [], "fee_types": [], "date_range": {"start": null, "end": null}}',
 '[{"field": "invoice_number", "title": "Invoice", "type": "text"}, {"field": "amount", "title": "Amount", "type": "currency"}, {"field": "status", "title": "Status", "type": "text"}]',
 '[{"type": "pie", "title": "Payment Status Distribution"}, {"type": "line", "title": "Collection Trend"}]',
 '550e8400-e29b-41d4-a716-446655440101', true, '["admin", "finance_manager"]'),

-- Analytics reports
('a3000000-0000-0000-0000-000000000001', '550e8400-e29b-41d4-a716-446655440001',
 'School Analytics Dashboard', 'Comprehensive school performance metrics and trends',
 'analytics', 'dashboard',
 '[{"source": "analytics.analytics_snapshots"}, {"source": "platform.school_feature_usage"}]',
 '{"period": "monthly", "metrics": []}',
 '[{"field": "metric_name", "title": "Metric", "type": "text"}, {"field": "current_value", "title": "Current", "type": "number"}, {"field": "trend", "title": "Trend", "type": "text"}]',
 '[{"type": "line", "title": "Student Enrollment Trend"}, {"type": "bar", "title": "Academic Performance"}, {"type": "doughnut", "title": "Fee Collection"}]',
 '550e8400-e29b-41d4-a716-446655440101', true, '["admin"]');

-- Grant necessary permissions
GRANT USAGE ON SCHEMA analytics TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA analytics TO PUBLIC;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA analytics TO PUBLIC;