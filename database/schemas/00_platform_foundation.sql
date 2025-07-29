-- =====================================================
-- Platform Foundation Schema
-- Required foundation for OneClass Platform multitenancy
-- File: database/schemas/00_platform_foundation.sql
-- =====================================================

-- Create the platform schema
CREATE SCHEMA IF NOT EXISTS platform;

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- BASIC PLATFORM TABLES (Foundation for SIS)
-- =====================================================

-- Schools table (basic version required by SIS)
CREATE TABLE IF NOT EXISTS platform.schools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    school_type VARCHAR(50) NOT NULL DEFAULT 'primary' CHECK (school_type IN ('primary', 'secondary', 'combined')),
    registration_number VARCHAR(100) UNIQUE,
    
    -- Contact Information
    email VARCHAR(255),
    phone VARCHAR(20),
    website VARCHAR(255),
    
    -- Address
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    province VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'Zimbabwe',
    
    -- Status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    
    -- System Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT school_name_not_empty CHECK (LENGTH(TRIM(name)) > 0)
);

-- Users table (basic version required by SIS)
CREATE TABLE IF NOT EXISTS platform.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES platform.schools(id) ON DELETE CASCADE,
    
    -- Authentication
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255), -- Will be managed by Supabase
    
    -- Personal Information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    
    -- Contact Information
    phone VARCHAR(20),
    mobile VARCHAR(20),
    
    -- System Information
    role VARCHAR(50) NOT NULL CHECK (role IN ('super_admin', 'school_admin', 'registrar', 'teacher', 'parent', 'student')),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Preferences
    preferred_language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'Africa/Harare',
    
    -- Authentication tracking
    last_login TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,
    
    -- System Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT email_valid CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT name_not_empty CHECK (LENGTH(TRIM(first_name)) > 0 AND LENGTH(TRIM(last_name)) > 0)
);

-- =====================================================
-- ACADEMIC STRUCTURE (Required by SIS)
-- =====================================================

-- Create academic schema for classes and years
CREATE SCHEMA IF NOT EXISTS academic;

-- Academic years table
CREATE TABLE IF NOT EXISTS academic.academic_years (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES platform.schools(id) ON DELETE CASCADE,
    
    -- Year Information
    year_name VARCHAR(50) NOT NULL, -- e.g., "2024", "2024-2025"
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    
    -- Status
    is_current BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'planned')),
    
    -- System Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(school_id, year_name),
    CONSTRAINT valid_year_dates CHECK (end_date > start_date),
    CONSTRAINT single_current_year_per_school UNIQUE(school_id, is_current) WHERE is_current = TRUE
);

-- Classes table
CREATE TABLE IF NOT EXISTS academic.classes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES platform.schools(id) ON DELETE CASCADE,
    academic_year_id UUID NOT NULL REFERENCES academic.academic_years(id) ON DELETE CASCADE,
    
    -- Class Information
    class_name VARCHAR(100) NOT NULL, -- e.g., "Grade 1A", "Form 4 Blue"
    grade_level INTEGER NOT NULL CHECK (grade_level BETWEEN 1 AND 13),
    section VARCHAR(10), -- A, B, C, etc.
    
    -- Capacity and Staffing
    max_students INTEGER DEFAULT 40,
    current_students INTEGER DEFAULT 0,
    class_teacher_id UUID REFERENCES platform.users(id),
    
    -- Status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    
    -- System Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(school_id, academic_year_id, class_name),
    CONSTRAINT current_students_within_max CHECK (current_students <= max_students)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Schools indexes
CREATE INDEX IF NOT EXISTS idx_schools_status ON platform.schools(status);
CREATE INDEX IF NOT EXISTS idx_schools_type ON platform.schools(school_type);
CREATE INDEX IF NOT EXISTS idx_schools_name ON platform.schools(name);

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_school_id ON platform.users(school_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON platform.users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON platform.users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON platform.users(is_active);

-- Academic years indexes
CREATE INDEX IF NOT EXISTS idx_academic_years_school_id ON academic.academic_years(school_id);
CREATE INDEX IF NOT EXISTS idx_academic_years_current ON academic.academic_years(is_current);

-- Classes indexes
CREATE INDEX IF NOT EXISTS idx_classes_school_id ON academic.classes(school_id);
CREATE INDEX IF NOT EXISTS idx_classes_academic_year ON academic.classes(academic_year_id);
CREATE INDEX IF NOT EXISTS idx_classes_grade_level ON academic.classes(grade_level);
CREATE INDEX IF NOT EXISTS idx_classes_teacher ON academic.classes(class_teacher_id);

-- =====================================================
-- UTILITY FUNCTIONS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update triggers to platform tables
CREATE TRIGGER update_schools_updated_at BEFORE UPDATE ON platform.schools FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON platform.users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_academic_years_updated_at BEFORE UPDATE ON academic.academic_years FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_classes_updated_at BEFORE UPDATE ON academic.classes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- SAMPLE DATA FOR DEVELOPMENT
-- =====================================================

-- Insert sample school
INSERT INTO platform.schools (name, school_type, registration_number, email, phone, city, province, country)
VALUES (
    'Demo Primary School',
    'primary',
    'DPS001',
    'admin@demoprimary.edu.zw',
    '+263-4-123456',
    'Harare',
    'Harare',
    'Zimbabwe'
) ON CONFLICT (registration_number) DO NOTHING;

-- Insert sample admin user
INSERT INTO platform.users (school_id, email, first_name, last_name, role)
SELECT 
    s.id,
    'admin@demoprimary.edu.zw',
    'System',
    'Administrator',
    'school_admin'
FROM platform.schools s 
WHERE s.registration_number = 'DPS001'
ON CONFLICT (email) DO NOTHING;

-- Insert current academic year
INSERT INTO academic.academic_years (school_id, year_name, start_date, end_date, is_current)
SELECT 
    s.id,
    '2024',
    '2024-01-15',
    '2024-12-15',
    TRUE
FROM platform.schools s 
WHERE s.registration_number = 'DPS001'
ON CONFLICT (school_id, year_name) DO NOTHING;

-- Insert sample classes
INSERT INTO academic.classes (school_id, academic_year_id, class_name, grade_level, section, max_students)
SELECT 
    s.id,
    ay.id,
    'Grade ' || g.grade_level || COALESCE(g.section, ''),
    g.grade_level,
    g.section,
    40
FROM platform.schools s
CROSS JOIN academic.academic_years ay
CROSS JOIN (
    VALUES 
        (1, 'A'), (1, 'B'), (1, 'C'),
        (2, 'A'), (2, 'B'),
        (3, 'A'), (3, 'B'),
        (4, 'A'), (4, 'B'),
        (5, 'A'), (5, 'B'),
        (6, 'A'), (6, 'B'),
        (7, 'A'), (7, 'B')
) AS g(grade_level, section)
WHERE s.registration_number = 'DPS001'
AND ay.year_name = '2024'
ON CONFLICT (school_id, academic_year_id, class_name) DO NOTHING;

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON SCHEMA platform IS 'Platform foundation schema - contains schools, users, and core system tables';
COMMENT ON SCHEMA academic IS 'Academic structure schema - contains academic years, classes, and curriculum structure';

COMMENT ON TABLE platform.schools IS 'Schools in the system - each school is a tenant';
COMMENT ON TABLE platform.users IS 'All users in the system - scoped to their school';
COMMENT ON TABLE academic.academic_years IS 'Academic years for each school';
COMMENT ON TABLE academic.classes IS 'Classes within each academic year';