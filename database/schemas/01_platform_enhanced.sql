-- =====================================================
-- Enhanced Platform Schema for Full Multitenancy
-- Implements the multitenancy enhancement plan requirements
-- File: database/schemas/01_platform_enhanced.sql
-- =====================================================

-- School configuration and branding
CREATE TABLE IF NOT EXISTS platform.school_configurations (
    school_id UUID PRIMARY KEY REFERENCES platform.schools(id) ON DELETE CASCADE,
    
    -- Branding Configuration
    logo_url TEXT,
    favicon_url TEXT,
    primary_color VARCHAR(7) DEFAULT '#1e40af', -- Hex color
    secondary_color VARCHAR(7) DEFAULT '#10b981',
    accent_color VARCHAR(7) DEFAULT '#f59e0b',
    font_family VARCHAR(100) DEFAULT 'Inter',
    
    -- School Identity
    motto TEXT,
    vision_statement TEXT,
    mission_statement TEXT,
    established_year INTEGER,
    school_website TEXT,
    
    -- Contact Information
    official_email VARCHAR(255),
    official_phone VARCHAR(20),
    postal_address JSONB,
    
    -- Regional Settings
    timezone VARCHAR(50) DEFAULT 'Africa/Harare',
    academic_calendar_type VARCHAR(20) DEFAULT 'zimbabwe', -- 'zimbabwe', 'british', 'american'
    language_primary VARCHAR(10) DEFAULT 'en',
    language_secondary VARCHAR(10), -- 'sn' for Shona, 'nd' for Ndebele
    currency VARCHAR(3) DEFAULT 'USD',
    date_format VARCHAR(20) DEFAULT 'DD/MM/YYYY',
    
    -- Feature Toggles per School
    features_enabled JSONB DEFAULT '{
        "attendance_tracking": true,
        "disciplinary_system": true,
        "health_records": true,
        "finance_module": true,
        "parent_portal": true,
        "ministry_reporting": false,
        "ai_assistance": false,
        "bulk_sms": false,
        "whatsapp_integration": false
    }'::jsonb,
    
    -- Custom Fields Configuration
    custom_student_fields JSONB DEFAULT '[]'::jsonb,
    custom_parent_fields JSONB DEFAULT '[]'::jsonb,
    
    -- Academic Structure
    grading_system JSONB DEFAULT '{
        "type": "percentage",
        "scale": {"A": "80-100", "B": "70-79", "C": "60-69", "D": "50-59", "E": "40-49", "F": "0-39"},
        "pass_mark": 50
    }'::jsonb,
    
    -- Notification Preferences
    notification_settings JSONB DEFAULT '{
        "email_enabled": true,
        "sms_enabled": false,
        "whatsapp_enabled": false,
        "push_enabled": true,
        "parent_absence_alert": true,
        "disciplinary_auto_notify": true
    }'::jsonb,
    
    -- System Configuration
    student_id_format VARCHAR(50) DEFAULT 'YYYY-NNNN',
    max_students_per_class INTEGER DEFAULT 40,
    academic_year_start_month INTEGER DEFAULT 1, -- January = 1
    terms_per_year INTEGER DEFAULT 3,
    
    -- Subscription and Limits
    subscription_tier VARCHAR(20) DEFAULT 'basic', -- 'trial', 'basic', 'premium', 'enterprise'
    max_students INTEGER DEFAULT 500,
    max_staff INTEGER DEFAULT 50,
    storage_limit_gb INTEGER DEFAULT 10,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- School domains for subdomain support (future)
CREATE TABLE IF NOT EXISTS platform.school_domains (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES platform.schools(id) ON DELETE CASCADE,
    domain VARCHAR(255) UNIQUE NOT NULL, -- e.g., 'harare-high.1class.app'
    is_primary BOOLEAN DEFAULT FALSE,
    is_custom BOOLEAN DEFAULT FALSE, -- true for custom domains like 'portal.hararehigh.edu.zw'
    ssl_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_primary_domain_per_school UNIQUE(school_id, is_primary) WHERE is_primary = true
);

-- Feature usage tracking for analytics
CREATE TABLE IF NOT EXISTS platform.school_feature_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES platform.schools(id) ON DELETE CASCADE,
    feature_name VARCHAR(100) NOT NULL,
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_school_feature UNIQUE(school_id, feature_name)
);

-- Enhanced user table to include school context
ALTER TABLE platform.users ADD COLUMN IF NOT EXISTS school_role_context JSONB DEFAULT '{}'::jsonb;
ALTER TABLE platform.users ADD COLUMN IF NOT EXISTS last_school_switch TIMESTAMP WITH TIME ZONE;

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_school_configurations_tier ON platform.school_configurations(subscription_tier);
CREATE INDEX IF NOT EXISTS idx_school_domains_domain ON platform.school_domains(domain);
CREATE INDEX IF NOT EXISTS idx_feature_usage_school_feature ON platform.school_feature_usage(school_id, feature_name);

-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================

-- Enable RLS on enhanced tables
ALTER TABLE platform.school_configurations ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform.school_domains ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform.school_feature_usage ENABLE ROW LEVEL SECURITY;

-- Create authentication function (placeholder - will be replaced with Supabase)
CREATE OR REPLACE FUNCTION auth.uid() RETURNS UUID AS $$
BEGIN
    -- This is a placeholder function
    -- In production, this will be handled by Supabase
    RETURN CURRENT_SETTING('app.current_user_id', true)::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create role for authenticated users
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated_user') THEN
        CREATE ROLE authenticated_user;
    END IF;
END
$$;

-- School configurations access policy
CREATE POLICY school_config_access ON platform.school_configurations
FOR ALL TO authenticated_user
USING (school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid()));

-- School domains access policy
CREATE POLICY school_domains_access ON platform.school_domains
FOR ALL TO authenticated_user
USING (school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid()));

-- Feature usage access policy
CREATE POLICY feature_usage_access ON platform.school_feature_usage
FOR ALL TO authenticated_user
USING (school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid()));

-- =====================================================
-- UTILITY FUNCTIONS
-- =====================================================

-- Function to get school configuration
CREATE OR REPLACE FUNCTION platform.get_school_config(p_school_id UUID)
RETURNS JSONB AS $$
DECLARE
    config_data JSONB;
BEGIN
    SELECT row_to_json(sc.*)::jsonb INTO config_data
    FROM platform.school_configurations sc
    WHERE sc.school_id = p_school_id;
    
    RETURN COALESCE(config_data, '{}'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- Function to track feature usage
CREATE OR REPLACE FUNCTION platform.track_feature_usage(p_school_id UUID, p_feature_name VARCHAR(100))
RETURNS VOID AS $$
BEGIN
    INSERT INTO platform.school_feature_usage (school_id, feature_name, usage_count, last_used_at)
    VALUES (p_school_id, p_feature_name, 1, NOW())
    ON CONFLICT (school_id, feature_name) 
    DO UPDATE SET 
        usage_count = school_feature_usage.usage_count + 1,
        last_used_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Function to check if school has feature enabled
CREATE OR REPLACE FUNCTION platform.has_feature_enabled(p_school_id UUID, p_feature_name VARCHAR(100))
RETURNS BOOLEAN AS $$
DECLARE
    feature_enabled BOOLEAN;
BEGIN
    SELECT COALESCE((features_enabled->p_feature_name)::boolean, false)
    INTO feature_enabled
    FROM platform.school_configurations
    WHERE school_id = p_school_id;
    
    RETURN COALESCE(feature_enabled, false);
END;
$$ LANGUAGE plpgsql;

-- Function to get school subscription limits
CREATE OR REPLACE FUNCTION platform.get_school_limits(p_school_id UUID)
RETURNS JSONB AS $$
DECLARE
    limits JSONB;
BEGIN
    SELECT jsonb_build_object(
        'max_students', max_students,
        'max_staff', max_staff,
        'storage_limit_gb', storage_limit_gb,
        'subscription_tier', subscription_tier
    ) INTO limits
    FROM platform.school_configurations
    WHERE school_id = p_school_id;
    
    RETURN COALESCE(limits, '{
        "max_students": 500,
        "max_staff": 50,
        "storage_limit_gb": 10,
        "subscription_tier": "basic"
    }'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- Trigger to create default configuration for new schools
CREATE OR REPLACE FUNCTION platform.create_default_school_config()
RETURNS TRIGGER AS $$
BEGIN
    -- Create default configuration
    INSERT INTO platform.school_configurations (school_id)
    VALUES (NEW.id);
    
    -- Create default domain
    INSERT INTO platform.school_domains (school_id, domain, is_primary)
    VALUES (NEW.id, LOWER(REPLACE(NEW.name, ' ', '-')) || '.1class.app', true);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_create_school_config
AFTER INSERT ON platform.schools
FOR EACH ROW EXECUTE FUNCTION platform.create_default_school_config();

-- Apply update triggers to new tables
CREATE TRIGGER update_school_configurations_updated_at 
    BEFORE UPDATE ON platform.school_configurations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- SEED DATA FOR DEVELOPMENT
-- =====================================================

-- Create default configuration for existing schools
INSERT INTO platform.school_configurations (school_id)
SELECT id FROM platform.schools 
WHERE id NOT IN (SELECT school_id FROM platform.school_configurations);

-- Create default domains for existing schools
INSERT INTO platform.school_domains (school_id, domain, is_primary)
SELECT 
    s.id,
    LOWER(REPLACE(s.name, ' ', '-')) || '.1class.app',
    true
FROM platform.schools s
WHERE s.id NOT IN (SELECT school_id FROM platform.school_domains WHERE is_primary = true);

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON TABLE platform.school_configurations IS 'School-specific configuration, branding, and feature toggles';
COMMENT ON TABLE platform.school_domains IS 'Domain configuration for school subdomains and custom domains';
COMMENT ON TABLE platform.school_feature_usage IS 'Tracks usage of features for analytics and billing';

COMMENT ON COLUMN platform.school_configurations.features_enabled IS 'JSONB object with feature names as keys and boolean values';
COMMENT ON COLUMN platform.school_configurations.grading_system IS 'School-specific grading configuration';
COMMENT ON COLUMN platform.school_configurations.notification_settings IS 'School notification preferences';
COMMENT ON COLUMN platform.school_configurations.subscription_tier IS 'Subscription level: trial, basic, premium, enterprise';

COMMENT ON FUNCTION platform.get_school_config(UUID) IS 'Returns full school configuration as JSONB';
COMMENT ON FUNCTION platform.track_feature_usage(UUID, VARCHAR) IS 'Increments usage counter for a feature';
COMMENT ON FUNCTION platform.has_feature_enabled(UUID, VARCHAR) IS 'Checks if a feature is enabled for a school';
COMMENT ON FUNCTION platform.get_school_limits(UUID) IS 'Returns subscription limits for a school';