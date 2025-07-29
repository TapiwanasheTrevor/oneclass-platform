-- =====================================================
-- Platform Schema Migration
-- Creates the complete platform schema for multi-tenant OneClass Platform
-- =====================================================

-- Create platform schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS platform;

-- Drop existing tables in correct order (respecting foreign keys)
DROP TABLE IF EXISTS platform.school_feature_usage CASCADE;
DROP TABLE IF EXISTS platform.school_domains CASCADE;
DROP TABLE IF EXISTS platform.school_configurations CASCADE;
DROP TABLE IF EXISTS platform.users CASCADE;
DROP TABLE IF EXISTS platform.schools CASCADE;

-- Create Schools table
CREATE TABLE platform.schools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    subscription_tier VARCHAR(20) DEFAULT 'basic' CHECK (subscription_tier IN ('trial', 'basic', 'professional', 'enterprise')),
    
    -- Contact information
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    
    -- School details
    school_type VARCHAR(50), -- primary, secondary, combined, technical
    establishment_year INTEGER,
    student_capacity INTEGER,
    
    -- Configuration (JSON field)
    configuration JSONB DEFAULT '{}',
    
    -- Flags
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on subdomain for fast lookups
CREATE INDEX idx_schools_subdomain ON platform.schools(subdomain);
CREATE INDEX idx_schools_status ON platform.schools(status);
CREATE INDEX idx_schools_active ON platform.schools(is_active);

-- Create Users table
CREATE TABLE platform.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES platform.schools(id) ON DELETE CASCADE,
    
    -- Basic information
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    
    -- Authentication
    clerk_user_id VARCHAR(255) UNIQUE,
    role VARCHAR(50) DEFAULT 'student' CHECK (role IN ('platform_admin', 'admin', 'teacher', 'student', 'parent', 'staff')),
    
    -- User metadata
    user_metadata JSONB DEFAULT '{}',
    preferences JSONB DEFAULT '{}',
    
    -- Flags
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Create indexes for users
CREATE INDEX idx_users_school_id ON platform.users(school_id);
CREATE INDEX idx_users_email ON platform.users(email);
CREATE INDEX idx_users_clerk_id ON platform.users(clerk_user_id);
CREATE INDEX idx_users_role ON platform.users(role);

-- Create School Configurations table
CREATE TABLE platform.school_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL UNIQUE REFERENCES platform.schools(id) ON DELETE CASCADE,
    
    -- Branding
    logo_url VARCHAR(500),
    favicon_url VARCHAR(500),
    primary_color VARCHAR(7) DEFAULT '#2563eb',
    secondary_color VARCHAR(7) DEFAULT '#64748b',
    background_color VARCHAR(7) DEFAULT '#ffffff',
    font_family VARCHAR(100) DEFAULT 'Inter',
    theme VARCHAR(20) DEFAULT 'light' CHECK (theme IN ('light', 'dark')),
    
    -- Feature configuration
    enabled_modules JSONB DEFAULT '[]',
    feature_flags JSONB DEFAULT '{}',
    integrations JSONB DEFAULT '{}',
    
    -- Academic settings
    academic_year_start VARCHAR(10), -- MM-DD format
    term_system VARCHAR(20) DEFAULT 'three_term' CHECK (term_system IN ('three_term', 'semester', 'quarter')),
    grade_system VARCHAR(20) DEFAULT 'zimbabwe' CHECK (grade_system IN ('zimbabwe', 'cambridge', 'ib')),
    
    -- Localization
    timezone VARCHAR(50) DEFAULT 'Africa/Harare',
    language VARCHAR(10) DEFAULT 'en',
    currency VARCHAR(3) DEFAULT 'ZWL',
    
    -- Contact and social
    website_url VARCHAR(500),
    social_links JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create School Domains table
CREATE TABLE platform.school_domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES platform.schools(id) ON DELETE CASCADE,
    
    domain VARCHAR(255) UNIQUE NOT NULL,
    subdomain VARCHAR(50) NOT NULL REFERENCES platform.schools(subdomain),
    
    -- SSL/TLS
    ssl_enabled BOOLEAN DEFAULT false,
    ssl_certificate TEXT,
    
    -- Verification
    is_verified BOOLEAN DEFAULT false,
    verification_token VARCHAR(255),
    verification_method VARCHAR(50) CHECK (verification_method IN ('dns', 'file', 'email')),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    verified_at TIMESTAMP WITH TIME ZONE
);

-- Create School Feature Usage table
CREATE TABLE platform.school_feature_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES platform.schools(id) ON DELETE CASCADE,
    
    feature_name VARCHAR(100) NOT NULL,
    module_name VARCHAR(100) NOT NULL,
    usage_type VARCHAR(50) NOT NULL CHECK (usage_type IN ('api_call', 'page_view', 'action', 'storage')),
    
    -- Usage data
    count INTEGER DEFAULT 1,
    usage_metadata JSONB DEFAULT '{}',
    
    -- User context
    user_id UUID REFERENCES platform.users(id),
    user_role VARCHAR(50),
    
    -- Timestamps
    usage_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for feature usage
CREATE INDEX idx_feature_usage_school_id ON platform.school_feature_usage(school_id);
CREATE INDEX idx_feature_usage_date ON platform.school_feature_usage(usage_date);
CREATE INDEX idx_feature_usage_feature ON platform.school_feature_usage(feature_name);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
CREATE TRIGGER update_schools_updated_at BEFORE UPDATE ON platform.schools
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON platform.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_school_configurations_updated_at BEFORE UPDATE ON platform.school_configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_school_domains_updated_at BEFORE UPDATE ON platform.school_domains
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO platform.schools (id, name, subdomain, status, subscription_tier, email, school_type, is_active, is_verified) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'Demo High School', 'demo', 'active', 'professional', 'admin@demo.oneclass.platform', 'secondary', true, true),
('550e8400-e29b-41d4-a716-446655440002', 'Test Primary School', 'testschool', 'active', 'basic', 'admin@test.oneclass.platform', 'primary', true, true),
('550e8400-e29b-41d4-a716-446655440003', 'Enterprise Academy', 'enterprise', 'active', 'enterprise', 'admin@enterprise.oneclass.platform', 'combined', true, true);

-- Insert school configurations
INSERT INTO platform.school_configurations (school_id, enabled_modules, primary_color, secondary_color) VALUES
('550e8400-e29b-41d4-a716-446655440001', '["student_information_system", "finance_management", "academic_management", "advanced_reporting"]', '#2563eb', '#64748b'),
('550e8400-e29b-41d4-a716-446655440002', '["student_information_system", "finance_management", "academic_management"]', '#059669', '#6b7280'),
('550e8400-e29b-41d4-a716-446655440003', '["student_information_system", "finance_management", "academic_management", "advanced_reporting", "communication_hub", "parent_portal", "api_access"]', '#7c3aed', '#374151');

-- Insert sample users
INSERT INTO platform.users (id, school_id, email, first_name, last_name, role, is_active, is_verified) VALUES
('550e8400-e29b-41d4-a716-446655440101', '550e8400-e29b-41d4-a716-446655440001', 'admin@demo.oneclass.platform', 'Demo', 'Admin', 'admin', true, true),
('550e8400-e29b-41d4-a716-446655440102', '550e8400-e29b-41d4-a716-446655440002', 'admin@test.oneclass.platform', 'Test', 'Admin', 'admin', true, true),
('550e8400-e29b-41d4-a716-446655440103', '550e8400-e29b-41d4-a716-446655440003', 'admin@enterprise.oneclass.platform', 'Enterprise', 'Admin', 'admin', true, true);

-- Grant necessary permissions
GRANT USAGE ON SCHEMA platform TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA platform TO PUBLIC;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA platform TO PUBLIC;