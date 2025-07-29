-- =====================================================
-- Consolidated Platform User System Schema
-- Replaces legacy user models with unified structure
-- File: database/schemas/07_platform_users.sql
-- =====================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create the consolidated platform users table
CREATE TABLE IF NOT EXISTS platform.platform_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Core Identity
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    
    -- Platform-level information
    platform_role VARCHAR(50) NOT NULL DEFAULT 'student',
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    
    -- Multi-school support
    primary_school_id UUID REFERENCES platform.schools(id),
    
    -- Extended profile (JSON)
    profile JSONB DEFAULT '{}',
    
    -- Authentication integration (JSON)
    clerk_integration JSONB DEFAULT '{}',
    
    -- System metadata
    feature_flags JSONB DEFAULT '{}',
    user_preferences JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    
    -- Indexes
    CONSTRAINT chk_platform_role CHECK (platform_role IN (
        'super_admin', 'school_admin', 'registrar', 'teacher', 
        'parent', 'student', 'staff'
    )),
    CONSTRAINT chk_status CHECK (status IN (
        'active', 'inactive', 'suspended', 'pending_verification', 'archived'
    ))
);

-- Create school memberships table for multi-school support
CREATE TABLE IF NOT EXISTS platform.school_memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- User and school relationship
    user_id UUID NOT NULL REFERENCES platform.platform_users(id) ON DELETE CASCADE,
    school_id UUID NOT NULL REFERENCES platform.schools(id) ON DELETE CASCADE,
    
    -- School context
    school_name VARCHAR(255) NOT NULL,
    school_subdomain VARCHAR(50) NOT NULL,
    
    -- Role and permissions
    role VARCHAR(50) NOT NULL,
    permissions JSONB DEFAULT '[]',
    joined_date TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    
    -- Student-specific fields
    student_id VARCHAR(50),
    current_grade VARCHAR(20),
    admission_date TIMESTAMP WITH TIME ZONE,
    graduation_date TIMESTAMP WITH TIME ZONE,
    
    -- Staff-specific fields
    employee_id VARCHAR(50),
    department VARCHAR(100),
    hire_date TIMESTAMP WITH TIME ZONE,
    contract_type VARCHAR(50),
    
    -- Parent-specific fields
    children_ids JSONB DEFAULT '[]',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_membership_role CHECK (role IN (
        'principal', 'deputy_principal', 'academic_head', 'department_head',
        'teacher', 'form_teacher', 'registrar', 'bursar', 'librarian',
        'it_support', 'security', 'parent', 'student'
    )),
    CONSTRAINT chk_membership_status CHECK (status IN (
        'active', 'inactive', 'suspended', 'pending_verification', 'archived'
    )),
    CONSTRAINT chk_contract_type CHECK (contract_type IS NULL OR contract_type IN (
        'permanent', 'temporary', 'contract'
    )),
    
    -- Unique constraint to prevent duplicate memberships
    UNIQUE(user_id, school_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_platform_users_email ON platform.platform_users(email);
CREATE INDEX IF NOT EXISTS idx_platform_users_status ON platform.platform_users(status);
CREATE INDEX IF NOT EXISTS idx_platform_users_platform_role ON platform.platform_users(platform_role);
CREATE INDEX IF NOT EXISTS idx_platform_users_primary_school ON platform.platform_users(primary_school_id);
CREATE INDEX IF NOT EXISTS idx_platform_users_clerk_id ON platform.platform_users USING GIN ((clerk_integration->>'clerk_user_id'));

CREATE INDEX IF NOT EXISTS idx_school_memberships_user_id ON platform.school_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_school_memberships_school_id ON platform.school_memberships(school_id);
CREATE INDEX IF NOT EXISTS idx_school_memberships_role ON platform.school_memberships(role);
CREATE INDEX IF NOT EXISTS idx_school_memberships_status ON platform.school_memberships(status);
CREATE INDEX IF NOT EXISTS idx_school_memberships_student_id ON platform.school_memberships(student_id);
CREATE INDEX IF NOT EXISTS idx_school_memberships_employee_id ON platform.school_memberships(employee_id);

-- Create function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_platform_users_updated_at
    BEFORE UPDATE ON platform.platform_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_school_memberships_updated_at
    BEFORE UPDATE ON platform.school_memberships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create migration tracking table for data migration
CREATE TABLE IF NOT EXISTS platform.user_migration_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legacy_user_id UUID NOT NULL,
    new_user_id UUID NOT NULL REFERENCES platform.platform_users(id),
    migration_type VARCHAR(50) NOT NULL, -- 'legacy_to_platform', 'enhanced_to_platform'
    migrated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    batch_number INTEGER,
    migration_metadata JSONB DEFAULT '{}',
    
    -- Indexes
    UNIQUE(legacy_user_id, migration_type)
);

CREATE INDEX IF NOT EXISTS idx_migration_tracking_legacy_user ON platform.user_migration_tracking(legacy_user_id);
CREATE INDEX IF NOT EXISTS idx_migration_tracking_new_user ON platform.user_migration_tracking(new_user_id);
CREATE INDEX IF NOT EXISTS idx_migration_tracking_batch ON platform.user_migration_tracking(batch_number);

-- Row Level Security (RLS) Policies
ALTER TABLE platform.platform_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform.school_memberships ENABLE ROW LEVEL SECURITY;

-- Policy for platform users - users can see their own data
CREATE POLICY platform_users_own_data ON platform.platform_users
    FOR ALL USING (
        -- User can access their own data
        id = current_user_id()
        -- Super admins can access all data
        OR current_user_platform_role() = 'super_admin'
        -- School admins can access users in their schools
        OR EXISTS (
            SELECT 1 FROM platform.school_memberships sm
            WHERE sm.user_id = platform.platform_users.id
            AND sm.school_id IN (
                SELECT school_id FROM platform.school_memberships
                WHERE user_id = current_user_id()
                AND role IN ('principal', 'deputy_principal', 'school_admin')
            )
        )
    );

-- Policy for school memberships - members can see school data
CREATE POLICY school_memberships_access ON platform.school_memberships
    FOR ALL USING (
        -- User can see their own memberships
        user_id = current_user_id()
        -- Super admins can see all memberships
        OR current_user_platform_role() = 'super_admin'
        -- School staff can see memberships in their schools
        OR school_id IN (
            SELECT school_id FROM platform.school_memberships
            WHERE user_id = current_user_id()
            AND role IN ('principal', 'deputy_principal', 'school_admin', 'registrar')
        )
    );

-- Helper functions for RLS policies
CREATE OR REPLACE FUNCTION current_user_id()
RETURNS UUID AS $$
BEGIN
    -- This should be set by the application when establishing database connections
    -- For now, return a default value - this will be properly implemented with JWT context
    RETURN COALESCE(current_setting('app.current_user_id', true)::UUID, '00000000-0000-0000-0000-000000000000'::UUID);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION current_user_platform_role()
RETURNS TEXT AS $$
BEGIN
    -- This should be set by the application when establishing database connections
    RETURN COALESCE(current_setting('app.current_user_role', true), 'student');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create views for common queries
CREATE OR REPLACE VIEW platform.user_school_summary AS
SELECT 
    u.id,
    u.email,
    u.first_name,
    u.last_name,
    u.platform_role,
    u.status,
    u.primary_school_id,
    u.created_at,
    u.last_login,
    COUNT(sm.id) as school_count,
    ARRAY_AGG(
        json_build_object(
            'school_id', sm.school_id,
            'school_name', sm.school_name,
            'school_subdomain', sm.school_subdomain,
            'role', sm.role,
            'status', sm.status,
            'joined_date', sm.joined_date
        )
    ) FILTER (WHERE sm.id IS NOT NULL) as school_memberships
FROM platform.platform_users u
LEFT JOIN platform.school_memberships sm ON u.id = sm.user_id
GROUP BY u.id, u.email, u.first_name, u.last_name, u.platform_role, u.status, u.primary_school_id, u.created_at, u.last_login;

-- Create view for school membership details
CREATE OR REPLACE VIEW platform.school_user_details AS
SELECT 
    sm.id as membership_id,
    sm.user_id,
    sm.school_id,
    sm.school_name,
    sm.school_subdomain,
    sm.role as school_role,
    sm.status as membership_status,
    sm.joined_date,
    
    -- User details
    u.email,
    u.first_name,
    u.last_name,
    u.platform_role,
    u.status as user_status,
    u.created_at as user_created_at,
    u.last_login,
    
    -- Role-specific details
    sm.student_id,
    sm.current_grade,
    sm.admission_date,
    sm.graduation_date,
    sm.employee_id,
    sm.department,
    sm.hire_date,
    sm.contract_type,
    sm.children_ids,
    
    -- Profile data
    u.profile->>'phone_number' as phone_number,
    u.profile->>'profile_image_url' as profile_image_url,
    u.profile->>'date_of_birth' as date_of_birth,
    u.profile->>'gender' as gender,
    u.profile->>'address' as address
    
FROM platform.school_memberships sm
JOIN platform.platform_users u ON sm.user_id = u.id;

-- Grant permissions to application role
GRANT SELECT, INSERT, UPDATE, DELETE ON platform.platform_users TO oneclass_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON platform.school_memberships TO oneclass_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON platform.user_migration_tracking TO oneclass_app;
GRANT SELECT ON platform.user_school_summary TO oneclass_app;
GRANT SELECT ON platform.school_user_details TO oneclass_app;

-- Comments for documentation
COMMENT ON TABLE platform.platform_users IS 'Consolidated user model supporting multi-tenant, multi-school membership';
COMMENT ON TABLE platform.school_memberships IS 'User memberships in schools with role-specific data';
COMMENT ON TABLE platform.user_migration_tracking IS 'Tracks migration from legacy user models to consolidated model';

COMMENT ON COLUMN platform.platform_users.platform_role IS 'Platform-level role determining global permissions';
COMMENT ON COLUMN platform.platform_users.primary_school_id IS 'Users primary school for default context';
COMMENT ON COLUMN platform.platform_users.profile IS 'Extended user profile data as JSON';
COMMENT ON COLUMN platform.platform_users.clerk_integration IS 'Clerk authentication integration data';

COMMENT ON COLUMN platform.school_memberships.role IS 'School-specific role determining permissions within the school';
COMMENT ON COLUMN platform.school_memberships.permissions IS 'Array of specific permissions granted to user in this school';
COMMENT ON COLUMN platform.school_memberships.children_ids IS 'For parent users, IDs of their children (students)';

-- Create function to validate primary school membership
CREATE OR REPLACE FUNCTION validate_primary_school_membership()
RETURNS TRIGGER AS $$
BEGIN
    -- If primary_school_id is set, ensure user has membership in that school
    IF NEW.primary_school_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1 FROM platform.school_memberships 
            WHERE user_id = NEW.id 
            AND school_id = NEW.primary_school_id 
            AND status = 'active'
        ) THEN
            RAISE EXCEPTION 'User must have active membership in primary school';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to validate primary school membership
CREATE TRIGGER validate_primary_school_membership_trigger
    BEFORE INSERT OR UPDATE ON platform.platform_users
    FOR EACH ROW EXECUTE FUNCTION validate_primary_school_membership();

-- Create function to automatically set primary school
CREATE OR REPLACE FUNCTION auto_set_primary_school()
RETURNS TRIGGER AS $$
DECLARE
    user_record RECORD;
BEGIN
    -- If this is the first school membership and user has no primary school, set it
    SELECT * INTO user_record FROM platform.platform_users WHERE id = NEW.user_id;
    
    IF user_record.primary_school_id IS NULL THEN
        UPDATE platform.platform_users 
        SET primary_school_id = NEW.school_id 
        WHERE id = NEW.user_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-set primary school
CREATE TRIGGER auto_set_primary_school_trigger
    AFTER INSERT ON platform.school_memberships
    FOR EACH ROW EXECUTE FUNCTION auto_set_primary_school();