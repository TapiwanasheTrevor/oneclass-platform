-- =====================================================
-- Module 9: Student Information System (SIS) 
-- Complete Database Schema
-- File: database/schemas/09_sis.sql
-- =====================================================

-- Create the SIS schema
CREATE SCHEMA IF NOT EXISTS sis;

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- CORE STUDENT INFORMATION
-- =====================================================

-- Main students table with comprehensive student data
CREATE TABLE sis.students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES platform.schools(id) ON DELETE CASCADE,
    user_id UUID UNIQUE REFERENCES platform.users(id) ON DELETE SET NULL,
    
    -- Basic Identification
    student_number VARCHAR(20) NOT NULL,
    zimsec_number VARCHAR(15) UNIQUE, -- National exam registration
    barcode VARCHAR(50) UNIQUE, -- For ID cards/library systems
    
    -- Personal Information
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    preferred_name VARCHAR(100),
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10) NOT NULL CHECK (gender IN ('Male', 'Female', 'Other')),
    
    -- Cultural and Language Information
    nationality VARCHAR(100) DEFAULT 'Zimbabwean',
    home_language VARCHAR(50) CHECK (home_language IN ('English', 'Shona', 'Ndebele', 'Tonga', 'Kalanga', 'Nambya', 'Other')),
    religion VARCHAR(100),
    tribe VARCHAR(100),
    
    -- Contact Information
    mobile_number VARCHAR(20),
    email VARCHAR(255),
    
    -- Physical Characteristics (for ID purposes)
    height_cm INTEGER,
    weight_kg DECIMAL(5,2),
    blood_type VARCHAR(5) CHECK (blood_type IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
    identifying_marks TEXT,
    
    -- Address Information (JSONB for flexibility)
    residential_address JSONB NOT NULL, -- {"street", "suburb", "city", "province", "postal_code"}
    postal_address JSONB, -- Can be different from residential
    
    -- Academic Information
    current_grade_level INTEGER CHECK (current_grade_level BETWEEN 1 AND 13),
    current_class_id UUID REFERENCES academic.classes(id),
    enrollment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    expected_graduation_date DATE,
    
    -- Status and Behavior Tracking
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'transferred', 'graduated', 'expelled', 'deceased')),
    disciplinary_points INTEGER DEFAULT 0 CHECK (disciplinary_points >= 0),
    merit_points INTEGER DEFAULT 0 CHECK (merit_points >= 0),
    
    -- Medical Information (Encrypted for privacy)
    medical_conditions_encrypted TEXT, -- Encrypted JSONB
    allergies_encrypted TEXT, -- Encrypted JSONB
    medications_encrypted TEXT, -- Encrypted JSONB
    medical_aid_provider VARCHAR(100),
    medical_aid_number VARCHAR(50),
    
    -- Emergency Contacts (Encrypted for privacy)
    emergency_contacts_encrypted TEXT NOT NULL, -- Encrypted JSONB - minimum 2 contacts required
    
    -- Special Needs and Accommodations
    special_needs JSONB, -- Learning disabilities, physical limitations, etc.
    dietary_requirements TEXT,
    transport_needs VARCHAR(100), -- 'bus', 'walking', 'private', 'boarding'
    
    -- Media and Documentation
    profile_photo_url TEXT,
    birth_certificate_url TEXT,
    passport_photo_url TEXT,
    other_documents JSONB, -- Array of document objects
    
    -- Previous School Information
    previous_school_name VARCHAR(255),
    previous_school_address TEXT,
    transfer_reason TEXT,
    transfer_documents JSONB,
    
    -- System Fields
    created_by UUID NOT NULL REFERENCES platform.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE, -- Soft delete for audit purposes
    
    -- Constraints
    CONSTRAINT valid_date_of_birth CHECK (date_of_birth <= CURRENT_DATE - INTERVAL '3 years'),
    CONSTRAINT valid_enrollment_date CHECK (enrollment_date >= date_of_birth + INTERVAL '3 years'),
    CONSTRAINT unique_student_per_school UNIQUE(school_id, student_number),
    CONSTRAINT valid_grade_for_age CHECK (
        (EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM date_of_birth) - 3) >= current_grade_level OR
        current_grade_level IS NULL
    )
);

-- =====================================================
-- GUARDIAN/PARENT RELATIONSHIPS
-- =====================================================

CREATE TABLE sis.student_guardians (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES sis.students(id) ON DELETE CASCADE,
    guardian_user_id UUID NOT NULL REFERENCES platform.users(id) ON DELETE CASCADE,
    
    -- Relationship Details
    relationship VARCHAR(50) NOT NULL, -- 'Father', 'Mother', 'Guardian', 'Grandmother', etc.
    is_primary_contact BOOLEAN DEFAULT FALSE,
    is_emergency_contact BOOLEAN DEFAULT TRUE,
    contact_priority INTEGER DEFAULT 1, -- 1 = primary, 2 = secondary, etc.
    
    -- Permissions and Responsibilities
    has_pickup_permission BOOLEAN DEFAULT TRUE,
    has_academic_access BOOLEAN DEFAULT TRUE,
    has_financial_responsibility BOOLEAN DEFAULT TRUE,
    financial_responsibility_percentage DECIMAL(5,2) DEFAULT 100.00,
    
    -- Contact Information (can override user account details)
    preferred_contact_method VARCHAR(20) DEFAULT 'sms' CHECK (preferred_contact_method IN ('email', 'sms', 'whatsapp', 'call')),
    alternative_phone VARCHAR(20),
    work_phone VARCHAR(20),
    work_address TEXT,
    
    -- Employment Information
    employer VARCHAR(255),
    job_title VARCHAR(100),
    monthly_income_range VARCHAR(50), -- '0-500', '500-1000', '1000-2000', etc.
    
    -- Legal Information
    legal_guardian_documents JSONB, -- Court orders, adoption papers, etc.
    parental_rights_status VARCHAR(50) DEFAULT 'full' CHECK (parental_rights_status IN ('full', 'limited', 'supervised', 'none')),
    
    -- System Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(student_id, guardian_user_id),
    CONSTRAINT valid_financial_percentage CHECK (financial_responsibility_percentage BETWEEN 0 AND 100),
    CONSTRAINT valid_contact_priority CHECK (contact_priority BETWEEN 1 AND 10)
);

-- =====================================================
-- ACADEMIC PROGRESSION TRACKING
-- =====================================================

CREATE TABLE sis.student_academic_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES sis.students(id) ON DELETE CASCADE,
    academic_year_id UUID NOT NULL REFERENCES academic.academic_years(id),
    
    -- Academic Performance
    grade_level INTEGER NOT NULL,
    class_id UUID REFERENCES academic.classes(id),
    
    -- Term Performance
    term_1_average DECIMAL(5,2) CHECK (term_1_average BETWEEN 0 AND 100),
    term_1_position INTEGER,
    term_1_out_of INTEGER,
    
    term_2_average DECIMAL(5,2) CHECK (term_2_average BETWEEN 0 AND 100),
    term_2_position INTEGER,
    term_2_out_of INTEGER,
    
    term_3_average DECIMAL(5,2) CHECK (term_3_average BETWEEN 0 AND 100),
    term_3_position INTEGER,
    term_3_out_of INTEGER,
    
    -- Annual Summary
    annual_average DECIMAL(5,2) CHECK (annual_average BETWEEN 0 AND 100),
    annual_position INTEGER,
    annual_out_of INTEGER,
    
    -- Progression Decision
    promotion_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (promotion_status IN ('promoted', 'repeated', 'conditional', 'transferred', 'graduated')),
    promotion_conditions TEXT, -- If conditional promotion
    
    -- Attendance Summary
    total_school_days INTEGER,
    days_present INTEGER,
    days_absent INTEGER,
    attendance_percentage DECIMAL(5,2),
    
    -- Comments and Notes
    teacher_comments TEXT,
    headmaster_comments TEXT,
    parent_comments TEXT,
    
    -- System Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(student_id, academic_year_id),
    CONSTRAINT valid_attendance CHECK (days_present + days_absent <= total_school_days),
    CONSTRAINT valid_position CHECK (
        (term_1_position IS NULL OR term_1_position <= term_1_out_of) AND
        (term_2_position IS NULL OR term_2_position <= term_2_out_of) AND
        (term_3_position IS NULL OR term_3_position <= term_3_out_of) AND
        (annual_position IS NULL OR annual_position <= annual_out_of)
    )
);

-- =====================================================
-- DISCIPLINARY MANAGEMENT
-- =====================================================

CREATE TABLE sis.disciplinary_incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES sis.students(id) ON DELETE CASCADE,
    
    -- Incident Details
    incident_date DATE NOT NULL,
    incident_time TIME,
    incident_type VARCHAR(100) NOT NULL, -- 'Lateness', 'Uniform violation', 'Fighting', 'Insubordination', etc.
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('minor', 'moderate', 'serious', 'severe')),
    
    -- Description and Evidence
    description TEXT NOT NULL,
    location VARCHAR(100), -- Where incident occurred
    witnesses TEXT, -- Names of witnesses
    evidence_urls JSONB, -- Photos, videos, documents
    
    -- Action Taken
    action_taken TEXT NOT NULL,
    points_deducted INTEGER DEFAULT 0 CHECK (points_deducted >= 0),
    suspension_days INTEGER DEFAULT 0 CHECK (suspension_days >= 0),
    detention_hours INTEGER DEFAULT 0 CHECK (detention_hours >= 0),
    
    -- Follow-up Requirements
    counseling_required BOOLEAN DEFAULT FALSE,
    parent_meeting_required BOOLEAN DEFAULT FALSE,
    behavioral_contract_required BOOLEAN DEFAULT FALSE,
    
    -- Communication
    parent_notified BOOLEAN DEFAULT FALSE,
    parent_notification_date TIMESTAMP WITH TIME ZONE,
    parent_notification_method VARCHAR(20), -- 'email', 'sms', 'call', 'letter'
    parent_response TEXT,
    
    -- Staff Involved
    reported_by UUID NOT NULL REFERENCES platform.users(id),
    investigated_by UUID REFERENCES platform.users(id),
    approved_by UUID REFERENCES platform.users(id), -- For serious incidents
    
    -- Status and Follow-up
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'under_investigation', 'resolved', 'appealed')),
    resolution_date DATE,
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_date DATE,
    follow_up_notes TEXT,
    
    -- System Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT incident_date_not_future CHECK (incident_date <= CURRENT_DATE),
    CONSTRAINT resolution_after_incident CHECK (resolution_date IS NULL OR resolution_date >= incident_date)
);

-- =====================================================
-- HEALTH AND MEDICAL RECORDS
-- =====================================================

CREATE TABLE sis.health_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES sis.students(id) ON DELETE CASCADE,
    
    -- Medical Event Details
    record_type VARCHAR(50) NOT NULL CHECK (record_type IN ('checkup', 'illness', 'injury', 'vaccination', 'screening', 'medication_change')),
    record_date DATE NOT NULL,
    recorded_by VARCHAR(100), -- Nurse, doctor name
    
    -- Health Information
    symptoms TEXT,
    diagnosis TEXT,
    treatment_given TEXT,
    medications_administered JSONB, -- [{"name": "Paracetamol", "dosage": "500mg", "time": "14:30"}]
    
    -- Vital Signs
    temperature_celsius DECIMAL(4,1),
    blood_pressure VARCHAR(10), -- "120/80"
    pulse_rate INTEGER,
    weight_kg DECIMAL(5,2),
    height_cm INTEGER,
    
    -- Follow-up and Recommendations
    recommendations TEXT,
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_date DATE,
    parent_contacted BOOLEAN DEFAULT FALSE,
    sent_home BOOLEAN DEFAULT FALSE,
    
    -- Emergency Response
    emergency_contact_called VARCHAR(100),
    emergency_action_taken TEXT,
    hospital_referral BOOLEAN DEFAULT FALSE,
    hospital_name VARCHAR(255),
    
    -- Documentation
    medical_certificate_url TEXT,
    other_documents JSONB,
    
    -- System Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_temperature CHECK (temperature_celsius IS NULL OR temperature_celsius BETWEEN 30 AND 45),
    CONSTRAINT valid_pulse CHECK (pulse_rate IS NULL OR pulse_rate BETWEEN 40 AND 200)
);

-- =====================================================
-- ATTENDANCE TRACKING
-- =====================================================

CREATE TABLE sis.attendance_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES sis.students(id) ON DELETE CASCADE,
    
    -- Date and Time Information
    attendance_date DATE NOT NULL,
    period VARCHAR(20) NOT NULL, -- 'morning', 'afternoon', 'period_1', 'period_2', etc.
    
    -- Attendance Status
    status VARCHAR(20) NOT NULL CHECK (status IN ('present', 'absent', 'late', 'excused', 'sick', 'suspended')),
    arrival_time TIME,
    departure_time TIME,
    
    -- Absence Details
    absence_reason VARCHAR(100),
    excuse_provided BOOLEAN DEFAULT FALSE,
    excuse_document_url TEXT,
    parent_notified BOOLEAN DEFAULT FALSE,
    
    -- Staff Information
    marked_by UUID NOT NULL REFERENCES platform.users(id),
    verified_by UUID REFERENCES platform.users(id), -- For disputed attendance
    
    -- Notes
    notes TEXT,
    
    -- System Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(student_id, attendance_date, period),
    CONSTRAINT attendance_date_not_future CHECK (attendance_date <= CURRENT_DATE)
);

-- =====================================================
-- STUDENT DOCUMENTS AND FILES
-- =====================================================

CREATE TABLE sis.student_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES sis.students(id) ON DELETE CASCADE,
    
    -- Document Information
    document_type VARCHAR(50) NOT NULL CHECK (document_type IN (
        'birth_certificate', 'passport', 'national_id', 'medical_certificate', 
        'previous_school_report', 'immunization_record', 'court_order',
        'recommendation_letter', 'other'
    )),
    document_name VARCHAR(255) NOT NULL,
    file_url TEXT NOT NULL,
    file_size_bytes BIGINT,
    file_format VARCHAR(10), -- 'pdf', 'jpg', 'png', etc.
    
    -- Document Status
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by UUID REFERENCES platform.users(id),
    verification_date TIMESTAMP WITH TIME ZONE,
    expiry_date DATE, -- For documents that expire
    
    -- Access Control
    is_confidential BOOLEAN DEFAULT FALSE,
    access_level VARCHAR(20) DEFAULT 'school' CHECK (access_level IN ('student', 'guardian', 'teacher', 'admin', 'school')),
    
    -- Metadata
    description TEXT,
    tags JSONB, -- ["important", "legal", "medical"]
    
    -- System Fields
    uploaded_by UUID NOT NULL REFERENCES platform.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Students table indexes
CREATE INDEX idx_students_school_id ON sis.students(school_id);
CREATE INDEX idx_students_student_number ON sis.students(student_number);
CREATE INDEX idx_students_zimsec_number ON sis.students(zimsec_number) WHERE zimsec_number IS NOT NULL;
CREATE INDEX idx_students_current_grade ON sis.students(current_grade_level);
CREATE INDEX idx_students_current_class ON sis.students(current_class_id) WHERE current_class_id IS NOT NULL;
CREATE INDEX idx_students_status ON sis.students(status);
CREATE INDEX idx_students_enrollment_date ON sis.students(enrollment_date);

-- Full-text search for student names
CREATE INDEX idx_students_name_search ON sis.students 
USING gin(to_tsvector('english', first_name || ' ' || COALESCE(middle_name, '') || ' ' || last_name));

-- Guardian relationships indexes
CREATE INDEX idx_student_guardians_student_id ON sis.student_guardians(student_id);
CREATE INDEX idx_student_guardians_guardian_id ON sis.student_guardians(guardian_user_id);
CREATE INDEX idx_student_guardians_primary ON sis.student_guardians(student_id, is_primary_contact);

-- Academic history indexes
CREATE INDEX idx_academic_history_student_year ON sis.student_academic_history(student_id, academic_year_id);
CREATE INDEX idx_academic_history_year ON sis.student_academic_history(academic_year_id);

-- Disciplinary incidents indexes
CREATE INDEX idx_disciplinary_student_id ON sis.disciplinary_incidents(student_id);
CREATE INDEX idx_disciplinary_date ON sis.disciplinary_incidents(incident_date);
CREATE INDEX idx_disciplinary_severity ON sis.disciplinary_incidents(severity);
CREATE INDEX idx_disciplinary_status ON sis.disciplinary_incidents(status);

-- Health records indexes
CREATE INDEX idx_health_records_student_id ON sis.health_records(student_id);
CREATE INDEX idx_health_records_date ON sis.health_records(record_date);
CREATE INDEX idx_health_records_type ON sis.health_records(record_type);

-- Attendance records indexes
CREATE INDEX idx_attendance_student_date ON sis.attendance_records(student_id, attendance_date);
CREATE INDEX idx_attendance_date ON sis.attendance_records(attendance_date);
CREATE INDEX idx_attendance_status ON sis.attendance_records(status);

-- Documents indexes
CREATE INDEX idx_documents_student_id ON sis.student_documents(student_id);
CREATE INDEX idx_documents_type ON sis.student_documents(document_type);
CREATE INDEX idx_documents_verified ON sis.student_documents(is_verified);

-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE sis.students ENABLE ROW LEVEL SECURITY;
ALTER TABLE sis.student_guardians ENABLE ROW LEVEL SECURITY;
ALTER TABLE sis.student_academic_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE sis.disciplinary_incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE sis.health_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE sis.attendance_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE sis.student_documents ENABLE ROW LEVEL SECURITY;

-- Students table policies
CREATE POLICY sis_students_school_isolation ON sis.students
FOR ALL TO authenticated_user
USING (school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid()));

CREATE POLICY sis_students_own_record ON sis.students
FOR SELECT TO authenticated_user
USING (
    user_id = auth.uid() OR -- Student can see their own record
    id IN (SELECT student_id FROM sis.student_guardians WHERE guardian_user_id = auth.uid()) -- Parent can see child's record
);

-- Guardian relationships policies
CREATE POLICY sis_guardians_school_isolation ON sis.student_guardians
FOR ALL TO authenticated_user
USING (
    student_id IN (SELECT id FROM sis.students WHERE school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid()))
);

-- Academic history policies
CREATE POLICY sis_academic_history_access ON sis.student_academic_history
FOR ALL TO authenticated_user
USING (
    student_id IN (
        SELECT id FROM sis.students 
        WHERE school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid())
    )
);

-- Disciplinary incidents policies (more restrictive)
CREATE POLICY sis_disciplinary_staff_access ON sis.disciplinary_incidents
FOR ALL TO authenticated_user
USING (
    student_id IN (
        SELECT id FROM sis.students 
        WHERE school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid())
    ) AND (
        (SELECT role FROM platform.users WHERE id = auth.uid()) IN ('school_admin', 'teacher') OR
        student_id IN (SELECT student_id FROM sis.student_guardians WHERE guardian_user_id = auth.uid())
    )
);

-- Health records policies (medical staff and guardians only)
CREATE POLICY sis_health_records_access ON sis.health_records
FOR ALL TO authenticated_user
USING (
    student_id IN (
        SELECT id FROM sis.students 
        WHERE school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid())
    ) AND (
        (SELECT role FROM platform.users WHERE id = auth.uid()) IN ('school_admin', 'nurse', 'teacher') OR
        student_id IN (SELECT student_id FROM sis.student_guardians WHERE guardian_user_id = auth.uid())
    )
);

-- Attendance records policies
CREATE POLICY sis_attendance_access ON sis.attendance_records
FOR ALL TO authenticated_user
USING (
    student_id IN (
        SELECT id FROM sis.students 
        WHERE school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid())
    )
);

-- Documents policies (based on access level)
CREATE POLICY sis_documents_access ON sis.student_documents
FOR ALL TO authenticated_user
USING (
    student_id IN (
        SELECT id FROM sis.students 
        WHERE school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid())
    ) AND (
        access_level = 'school' OR
        (access_level = 'admin' AND (SELECT role FROM platform.users WHERE id = auth.uid()) = 'school_admin') OR
        (access_level = 'guardian' AND student_id IN (SELECT student_id FROM sis.student_guardians WHERE guardian_user_id = auth.uid())) OR
        (access_level = 'student' AND student_id IN (SELECT id FROM sis.students WHERE user_id = auth.uid()))
    )
);

-- =====================================================
-- UTILITY FUNCTIONS
-- =====================================================

-- Function to generate next student number
CREATE OR REPLACE FUNCTION sis.generate_student_number(p_school_id UUID, p_year INTEGER DEFAULT NULL)
RETURNS VARCHAR(20) AS $$
DECLARE
    v_year INTEGER;
    v_next_sequence INTEGER;
    v_student_number VARCHAR(20);
BEGIN
    v_year := COALESCE(p_year, EXTRACT(YEAR FROM CURRENT_DATE));
    
    -- Get the next sequence number for this year and school
    SELECT COALESCE(MAX(CAST(SUBSTRING(student_number FROM '[0-9]+$') AS INTEGER)), 0) + 1
    INTO v_next_sequence
    FROM sis.students 
    WHERE school_id = p_school_id 
    AND student_number LIKE v_year::text || '-%';
    
    -- Format: YYYY-NNNN (e.g., 2024-0001)
    v_student_number := v_year::text || '-' || LPAD(v_next_sequence::text, 4, '0');
    
    RETURN v_student_number;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate age in years
CREATE OR REPLACE FUNCTION sis.calculate_age(p_date_of_birth DATE, p_as_of_date DATE DEFAULT CURRENT_DATE)
RETURNS INTEGER AS $$
BEGIN
    RETURN EXTRACT(YEAR FROM AGE(p_as_of_date, p_date_of_birth));
END;
$$ LANGUAGE plpgsql;

-- Function to encrypt sensitive data
CREATE OR REPLACE FUNCTION sis.encrypt_sensitive_data(p_data JSONB, p_key TEXT DEFAULT 'default_encryption_key')
RETURNS TEXT AS $$
BEGIN
    RETURN encode(pgp_sym_encrypt(p_data::text, p_key), 'base64');
END;
$$ LANGUAGE plpgsql;

-- Function to decrypt sensitive data
CREATE OR REPLACE FUNCTION sis.decrypt_sensitive_data(p_encrypted_data TEXT, p_key TEXT DEFAULT 'default_encryption_key')
RETURNS JSONB AS $$
BEGIN
    RETURN pgp_sym_decrypt(decode(p_encrypted_data, 'base64'), p_key)::JSONB;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =====================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update triggers to all tables
CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON sis.students FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_guardians_updated_at BEFORE UPDATE ON sis.student_guardians FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_academic_history_updated_at BEFORE UPDATE ON sis.student_academic_history FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_disciplinary_updated_at BEFORE UPDATE ON sis.disciplinary_incidents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_health_records_updated_at BEFORE UPDATE ON sis.health_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_attendance_updated_at BEFORE UPDATE ON sis.attendance_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON sis.student_documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-generate student number trigger
CREATE OR REPLACE FUNCTION sis.auto_generate_student_number()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.student_number IS NULL OR NEW.student_number = '' THEN
        NEW.student_number := sis.generate_student_number(NEW.school_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auto_student_number BEFORE INSERT ON sis.students FOR EACH ROW EXECUTE FUNCTION sis.auto_generate_student_number();

-- =====================================================
-- SAMPLE DATA FOR DEVELOPMENT
-- =====================================================

-- Insert sample students (for development/testing only)
-- This section would be in a separate seed file in production

COMMENT ON SCHEMA sis IS 'Student Information System - Complete schema for managing student data, guardians, academic history, discipline, health records, and attendance';
COMMENT ON TABLE sis.students IS 'Core student information with encrypted sensitive data';
COMMENT ON TABLE sis.student_guardians IS 'Parent/guardian relationships and permissions';
COMMENT ON TABLE sis.student_academic_history IS 'Academic performance tracking by year';
COMMENT ON TABLE sis.disciplinary_incidents IS 'Disciplinary actions and behavior management';
COMMENT ON TABLE sis.health_records IS 'Medical events and health monitoring';
COMMENT ON TABLE sis.attendance_records IS 'Daily attendance tracking';
COMMENT ON TABLE sis.student_documents IS 'Document storage with access control';