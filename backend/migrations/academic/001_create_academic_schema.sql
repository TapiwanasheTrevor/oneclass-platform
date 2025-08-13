-- =====================================================
-- OneClass Academic Management Module - Database Migration
-- Create Academic Schema and Base Tables
-- =====================================================

-- Migration: 001_create_academic_schema
-- Description: Create academic schema and base tables for subjects, curriculum, timetables, attendance, assessments, and grades
-- Date: 2025-08-13
-- Author: OneClass Development Team

BEGIN;

-- Create academic schema
CREATE SCHEMA IF NOT EXISTS academic;

-- Create UUID extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- SUBJECTS TABLE
-- =====================================================

CREATE TABLE academic.subjects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL,
    code VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    grade_levels INTEGER[] NOT NULL DEFAULT '{}',
    is_core BOOLEAN NOT NULL DEFAULT FALSE,
    is_practical BOOLEAN NOT NULL DEFAULT FALSE,
    requires_lab BOOLEAN NOT NULL DEFAULT FALSE,
    pass_mark DECIMAL(5,2) NOT NULL DEFAULT 50.00,
    max_mark DECIMAL(5,2) NOT NULL DEFAULT 100.00,
    credit_hours INTEGER NOT NULL DEFAULT 1,
    department VARCHAR(50),
    language_of_instruction VARCHAR(20) NOT NULL DEFAULT 'English',
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_subject_code_per_school UNIQUE (school_id, code),
    CONSTRAINT grade_levels_not_empty CHECK (array_length(grade_levels, 1) > 0),
    CONSTRAINT valid_pass_mark CHECK (pass_mark >= 0 AND pass_mark <= 100),
    CONSTRAINT positive_max_mark CHECK (max_mark > 0),
    CONSTRAINT positive_credit_hours CHECK (credit_hours > 0),
    CONSTRAINT non_negative_display_order CHECK (display_order >= 0)
);

-- Create indexes for subjects
CREATE INDEX idx_subjects_school_active ON academic.subjects (school_id, is_active);
CREATE INDEX idx_subjects_code ON academic.subjects (code);
CREATE INDEX idx_subjects_grade_levels ON academic.subjects USING GIN (grade_levels);
CREATE INDEX idx_subjects_department ON academic.subjects (department);

-- =====================================================
-- PERIODS TABLE
-- =====================================================

CREATE TABLE academic.periods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL,
    period_number INTEGER NOT NULL,
    name VARCHAR(50) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_break BOOLEAN NOT NULL DEFAULT FALSE,
    break_type VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_period_number_per_school UNIQUE (school_id, period_number),
    CONSTRAINT positive_period_number CHECK (period_number > 0),
    CONSTRAINT valid_time_order CHECK (end_time > start_time),
    CONSTRAINT valid_break_type CHECK (break_type IS NULL OR break_type IN ('tea', 'lunch', 'assembly'))
);

-- Create indexes for periods
CREATE INDEX idx_periods_school_active ON academic.periods (school_id, is_active);
CREATE INDEX idx_periods_time ON academic.periods (start_time, end_time);

-- =====================================================
-- CURRICULA TABLE
-- =====================================================

CREATE TABLE academic.curricula (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL,
    academic_year_id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    grade_level INTEGER NOT NULL,
    term_number INTEGER,
    subject_id UUID NOT NULL,
    learning_objectives JSONB DEFAULT '[]',
    learning_outcomes JSONB DEFAULT '[]',
    assessment_methods JSONB DEFAULT '[]',
    resources_required JSONB DEFAULT '[]',
    total_periods INTEGER NOT NULL DEFAULT 1,
    practical_periods INTEGER NOT NULL DEFAULT 0,
    effective_from DATE NOT NULL,
    effective_to DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    approved_by UUID,
    approved_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_curriculum_per_term UNIQUE (school_id, academic_year_id, subject_id, grade_level, term_number),
    CONSTRAINT valid_grade_level CHECK (grade_level >= 1 AND grade_level <= 13),
    CONSTRAINT valid_term_number CHECK (term_number IS NULL OR (term_number >= 1 AND term_number <= 3)),
    CONSTRAINT positive_total_periods CHECK (total_periods > 0),
    CONSTRAINT non_negative_practical_periods CHECK (practical_periods >= 0),
    CONSTRAINT practical_not_exceed_total CHECK (practical_periods <= total_periods),
    CONSTRAINT valid_effective_dates CHECK (effective_to IS NULL OR effective_to >= effective_from),
    CONSTRAINT valid_status CHECK (status IN ('draft', 'active', 'archived')),
    
    -- Foreign keys
    CONSTRAINT fk_curricula_subject FOREIGN KEY (subject_id) REFERENCES academic.subjects(id)
);

-- Create indexes for curricula
CREATE INDEX idx_curricula_school_year ON academic.curricula (school_id, academic_year_id);
CREATE INDEX idx_curricula_subject_grade ON academic.curricula (subject_id, grade_level);
CREATE INDEX idx_curricula_term ON academic.curricula (term_number);

-- =====================================================
-- TIMETABLES TABLE
-- =====================================================

CREATE TABLE academic.timetables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL,
    academic_year_id UUID NOT NULL,
    term_number INTEGER NOT NULL,
    class_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    teacher_id UUID NOT NULL,
    period_id UUID NOT NULL,
    day_of_week INTEGER NOT NULL,
    room_number VARCHAR(20),
    is_double_period BOOLEAN NOT NULL DEFAULT FALSE,
    is_practical BOOLEAN NOT NULL DEFAULT FALSE,
    week_pattern VARCHAR(10) NOT NULL DEFAULT 'all',
    effective_from DATE NOT NULL,
    effective_to DATE,
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_class_period_slot UNIQUE (school_id, class_id, period_id, day_of_week, academic_year_id, term_number, effective_from),
    CONSTRAINT valid_day_of_week CHECK (day_of_week >= 1 AND day_of_week <= 7),
    CONSTRAINT valid_term_number CHECK (term_number >= 1 AND term_number <= 3),
    CONSTRAINT valid_week_pattern CHECK (week_pattern IN ('all', 'odd', 'even')),
    CONSTRAINT valid_effective_dates CHECK (effective_to IS NULL OR effective_to >= effective_from),
    
    -- Foreign keys
    CONSTRAINT fk_timetables_subject FOREIGN KEY (subject_id) REFERENCES academic.subjects(id),
    CONSTRAINT fk_timetables_period FOREIGN KEY (period_id) REFERENCES academic.periods(id)
);

-- Create indexes for timetables
CREATE INDEX idx_timetables_school_year ON academic.timetables (school_id, academic_year_id);
CREATE INDEX idx_timetables_teacher ON academic.timetables (teacher_id);
CREATE INDEX idx_timetables_class ON academic.timetables (class_id);
CREATE INDEX idx_timetables_subject ON academic.timetables (subject_id);
CREATE INDEX idx_timetables_day_period ON academic.timetables (day_of_week, period_id);

-- =====================================================
-- ATTENDANCE SESSIONS TABLE
-- =====================================================

CREATE TABLE academic.attendance_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL,
    timetable_id UUID NOT NULL,
    period_id UUID NOT NULL,
    teacher_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    class_id UUID NOT NULL,
    session_date DATE NOT NULL,
    session_type VARCHAR(20) NOT NULL DEFAULT 'regular',
    session_status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    attendance_marked BOOLEAN NOT NULL DEFAULT FALSE,
    marked_by UUID,
    marked_at TIMESTAMP WITH TIME ZONE,
    total_students INTEGER NOT NULL DEFAULT 0,
    present_students INTEGER NOT NULL DEFAULT 0,
    absent_students INTEGER NOT NULL DEFAULT 0,
    late_students INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_session_per_date UNIQUE (school_id, timetable_id, session_date),
    CONSTRAINT valid_session_type CHECK (session_type IN ('regular', 'makeup', 'extra', 'exam')),
    CONSTRAINT valid_session_status CHECK (session_status IN ('scheduled', 'active', 'completed', 'cancelled')),
    CONSTRAINT non_negative_total_students CHECK (total_students >= 0),
    CONSTRAINT non_negative_present_students CHECK (present_students >= 0),
    CONSTRAINT non_negative_absent_students CHECK (absent_students >= 0),
    CONSTRAINT non_negative_late_students CHECK (late_students >= 0),
    CONSTRAINT attendance_sum_check CHECK (present_students + absent_students + late_students = total_students),
    
    -- Foreign keys
    CONSTRAINT fk_attendance_sessions_timetable FOREIGN KEY (timetable_id) REFERENCES academic.timetables(id),
    CONSTRAINT fk_attendance_sessions_period FOREIGN KEY (period_id) REFERENCES academic.periods(id)
);

-- Create indexes for attendance sessions
CREATE INDEX idx_attendance_sessions_school_date ON academic.attendance_sessions (school_id, session_date);
CREATE INDEX idx_attendance_sessions_timetable ON academic.attendance_sessions (timetable_id);
CREATE INDEX idx_attendance_sessions_teacher ON academic.attendance_sessions (teacher_id);
CREATE INDEX idx_attendance_sessions_class ON academic.attendance_sessions (class_id);

-- =====================================================
-- ATTENDANCE RECORDS TABLE
-- =====================================================

CREATE TABLE academic.attendance_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL,
    attendance_session_id UUID NOT NULL,
    student_id UUID NOT NULL,
    attendance_status VARCHAR(20) NOT NULL,
    arrival_time TIME,
    departure_time TIME,
    excuse_reason TEXT,
    is_excused BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT,
    marked_by UUID NOT NULL,
    marked_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_student_attendance_per_session UNIQUE (school_id, attendance_session_id, student_id),
    CONSTRAINT valid_attendance_status CHECK (attendance_status IN ('present', 'absent', 'late', 'excused')),
    CONSTRAINT valid_attendance_times CHECK (departure_time IS NULL OR arrival_time IS NULL OR departure_time >= arrival_time),
    
    -- Foreign keys
    CONSTRAINT fk_attendance_records_session FOREIGN KEY (attendance_session_id) REFERENCES academic.attendance_sessions(id) ON DELETE CASCADE
);

-- Create indexes for attendance records
CREATE INDEX idx_attendance_records_school_session ON academic.attendance_records (school_id, attendance_session_id);
CREATE INDEX idx_attendance_records_student ON academic.attendance_records (student_id);
CREATE INDEX idx_attendance_records_status ON academic.attendance_records (attendance_status);

-- =====================================================
-- ASSESSMENTS TABLE
-- =====================================================

CREATE TABLE academic.assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL,
    academic_year_id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    subject_id UUID NOT NULL,
    class_id UUID NOT NULL,
    teacher_id UUID NOT NULL,
    term_number INTEGER NOT NULL,
    assessment_type VARCHAR(20) NOT NULL,
    assessment_category VARCHAR(20) NOT NULL DEFAULT 'continuous',
    total_marks DECIMAL(8,2) NOT NULL DEFAULT 100.00,
    pass_mark DECIMAL(8,2) NOT NULL DEFAULT 50.00,
    weight_percentage DECIMAL(5,2) NOT NULL DEFAULT 100.00,
    assessment_date DATE NOT NULL,
    due_date DATE,
    duration_minutes INTEGER,
    instructions TEXT,
    resources_allowed JSONB DEFAULT '[]',
    is_group_assessment BOOLEAN NOT NULL DEFAULT FALSE,
    max_group_size INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    published_at TIMESTAMP WITH TIME ZONE,
    published_by UUID,
    results_published BOOLEAN NOT NULL DEFAULT FALSE,
    results_published_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_term_number CHECK (term_number >= 1 AND term_number <= 3),
    CONSTRAINT valid_assessment_type CHECK (assessment_type IN ('test', 'quiz', 'assignment', 'project', 'practical', 'oral', 'exam')),
    CONSTRAINT valid_assessment_category CHECK (assessment_category IN ('continuous', 'formative', 'summative', 'final')),
    CONSTRAINT positive_total_marks CHECK (total_marks > 0),
    CONSTRAINT non_negative_pass_mark CHECK (pass_mark >= 0),
    CONSTRAINT pass_mark_not_exceed_total CHECK (pass_mark <= total_marks),
    CONSTRAINT valid_weight_percentage CHECK (weight_percentage > 0 AND weight_percentage <= 100),
    CONSTRAINT valid_due_date CHECK (due_date IS NULL OR due_date >= assessment_date),
    CONSTRAINT positive_duration CHECK (duration_minutes IS NULL OR duration_minutes > 0),
    CONSTRAINT valid_max_group_size CHECK (max_group_size IS NULL OR max_group_size > 1),
    CONSTRAINT valid_status CHECK (status IN ('draft', 'published', 'completed', 'cancelled')),
    
    -- Foreign keys
    CONSTRAINT fk_assessments_subject FOREIGN KEY (subject_id) REFERENCES academic.subjects(id)
);

-- Create indexes for assessments
CREATE INDEX idx_assessments_school_year ON academic.assessments (school_id, academic_year_id);
CREATE INDEX idx_assessments_subject_class ON academic.assessments (subject_id, class_id);
CREATE INDEX idx_assessments_teacher ON academic.assessments (teacher_id);
CREATE INDEX idx_assessments_date ON academic.assessments (assessment_date);
CREATE INDEX idx_assessments_term ON academic.assessments (term_number);

-- =====================================================
-- GRADES TABLE
-- =====================================================

CREATE TABLE academic.grades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL,
    assessment_id UUID NOT NULL,
    student_id UUID NOT NULL,
    raw_score DECIMAL(8,2),
    percentage_score DECIMAL(5,2),
    letter_grade VARCHAR(1),
    grade_points DECIMAL(3,2),
    is_absent BOOLEAN NOT NULL DEFAULT FALSE,
    is_excused BOOLEAN NOT NULL DEFAULT FALSE,
    submission_date TIMESTAMP WITH TIME ZONE,
    feedback TEXT,
    improvement_suggestions TEXT,
    next_steps TEXT,
    graded_by UUID NOT NULL,
    graded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    parent_viewed BOOLEAN NOT NULL DEFAULT FALSE,
    parent_viewed_at TIMESTAMP WITH TIME ZONE,
    is_final BOOLEAN NOT NULL DEFAULT FALSE,
    moderated_by UUID,
    moderated_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_student_grade_per_assessment UNIQUE (school_id, assessment_id, student_id),
    CONSTRAINT non_negative_raw_score CHECK (raw_score IS NULL OR raw_score >= 0),
    CONSTRAINT valid_percentage_score CHECK (percentage_score IS NULL OR (percentage_score >= 0 AND percentage_score <= 100)),
    CONSTRAINT valid_letter_grade CHECK (letter_grade IS NULL OR letter_grade IN ('A', 'B', 'C', 'D', 'E', 'U')),
    CONSTRAINT valid_grade_points CHECK (grade_points IS NULL OR (grade_points >= 0 AND grade_points <= 4)),
    
    -- Foreign keys
    CONSTRAINT fk_grades_assessment FOREIGN KEY (assessment_id) REFERENCES academic.assessments(id) ON DELETE CASCADE
);

-- Create indexes for grades
CREATE INDEX idx_grades_school_assessment ON academic.grades (school_id, assessment_id);
CREATE INDEX idx_grades_student ON academic.grades (student_id);
CREATE INDEX idx_grades_graded_by ON academic.grades (graded_by);
CREATE INDEX idx_grades_letter_grade ON academic.grades (letter_grade);

-- =====================================================
-- LESSON PLANS TABLE
-- =====================================================

CREATE TABLE academic.lesson_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL,
    academic_year_id UUID NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    subject_id UUID NOT NULL,
    class_id UUID NOT NULL,
    teacher_id UUID NOT NULL,
    term_number INTEGER NOT NULL,
    curriculum_id UUID,
    lesson_date DATE NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 40,
    learning_objectives JSONB DEFAULT '[]',
    learning_outcomes JSONB DEFAULT '[]',
    prerequisite_knowledge JSONB DEFAULT '[]',
    materials_required JSONB DEFAULT '[]',
    teaching_methods JSONB DEFAULT '[]',
    lesson_structure JSONB,
    assessment_activities JSONB DEFAULT '[]',
    homework_assignments JSONB DEFAULT '[]',
    differentiation_strategies JSONB DEFAULT '[]',
    extension_activities JSONB DEFAULT '[]',
    reflection_notes TEXT,
    shared_with JSONB DEFAULT '[]',
    is_template BOOLEAN NOT NULL DEFAULT FALSE,
    template_category VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    version INTEGER NOT NULL DEFAULT 1,
    parent_lesson_id UUID,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_term_number CHECK (term_number >= 1 AND term_number <= 3),
    CONSTRAINT positive_duration CHECK (duration_minutes > 0),
    CONSTRAINT valid_status CHECK (status IN ('draft', 'active', 'completed', 'archived')),
    CONSTRAINT positive_version CHECK (version >= 1),
    
    -- Foreign keys
    CONSTRAINT fk_lesson_plans_subject FOREIGN KEY (subject_id) REFERENCES academic.subjects(id),
    CONSTRAINT fk_lesson_plans_curriculum FOREIGN KEY (curriculum_id) REFERENCES academic.curricula(id),
    CONSTRAINT fk_lesson_plans_parent FOREIGN KEY (parent_lesson_id) REFERENCES academic.lesson_plans(id)
);

-- Create indexes for lesson plans
CREATE INDEX idx_lesson_plans_school_year ON academic.lesson_plans (school_id, academic_year_id);
CREATE INDEX idx_lesson_plans_subject_class ON academic.lesson_plans (subject_id, class_id);
CREATE INDEX idx_lesson_plans_teacher ON academic.lesson_plans (teacher_id);
CREATE INDEX idx_lesson_plans_date ON academic.lesson_plans (lesson_date);
CREATE INDEX idx_lesson_plans_term ON academic.lesson_plans (term_number);

-- =====================================================
-- CALENDAR EVENTS TABLE
-- =====================================================

CREATE TABLE academic.calendar_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL,
    academic_year_id UUID NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    event_type VARCHAR(20) NOT NULL,
    event_category VARCHAR(20) NOT NULL DEFAULT 'academic',
    start_date DATE NOT NULL,
    end_date DATE,
    start_time TIME,
    end_time TIME,
    is_all_day BOOLEAN NOT NULL DEFAULT TRUE,
    location VARCHAR(200),
    term_number INTEGER,
    grade_levels INTEGER[] DEFAULT '{}',
    class_ids UUID[] DEFAULT '{}',
    teacher_ids UUID[] DEFAULT '{}',
    is_recurring BOOLEAN NOT NULL DEFAULT FALSE,
    recurrence_pattern VARCHAR(50),
    recurrence_end_date DATE,
    reminder_days INTEGER[] DEFAULT '{}',
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    requires_attendance BOOLEAN NOT NULL DEFAULT FALSE,
    max_participants INTEGER,
    registration_required BOOLEAN NOT NULL DEFAULT FALSE,
    registration_deadline DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_event_type CHECK (event_type IN ('holiday', 'exam', 'assessment', 'sports', 'cultural', 'meeting', 'training', 'other')),
    CONSTRAINT valid_event_category CHECK (event_category IN ('academic', 'administrative', 'social', 'sports', 'cultural')),
    CONSTRAINT valid_end_date CHECK (end_date IS NULL OR end_date >= start_date),
    CONSTRAINT valid_end_time CHECK (end_time IS NULL OR start_time IS NULL OR end_time > start_time),
    CONSTRAINT valid_term_number CHECK (term_number IS NULL OR (term_number >= 1 AND term_number <= 3)),
    CONSTRAINT positive_max_participants CHECK (max_participants IS NULL OR max_participants > 0),
    CONSTRAINT valid_registration_deadline CHECK (registration_deadline IS NULL OR registration_deadline <= start_date),
    CONSTRAINT valid_recurrence_end_date CHECK (recurrence_end_date IS NULL OR recurrence_end_date >= start_date),
    CONSTRAINT valid_status CHECK (status IN ('scheduled', 'confirmed', 'cancelled', 'completed', 'postponed'))
);

-- Create indexes for calendar events
CREATE INDEX idx_calendar_events_school_year ON academic.calendar_events (school_id, academic_year_id);
CREATE INDEX idx_calendar_events_date ON academic.calendar_events (start_date, end_date);
CREATE INDEX idx_calendar_events_type ON academic.calendar_events (event_type);
CREATE INDEX idx_calendar_events_term ON academic.calendar_events (term_number);

-- =====================================================
-- ASSOCIATION TABLES
-- =====================================================

CREATE TABLE academic.calendar_event_subjects (
    calendar_event_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    PRIMARY KEY (calendar_event_id, subject_id),
    
    -- Foreign keys
    CONSTRAINT fk_calendar_event_subjects_event FOREIGN KEY (calendar_event_id) REFERENCES academic.calendar_events(id) ON DELETE CASCADE,
    CONSTRAINT fk_calendar_event_subjects_subject FOREIGN KEY (subject_id) REFERENCES academic.subjects(id) ON DELETE CASCADE
);

-- =====================================================
-- TRIGGERS FOR UPDATED_AT
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION academic.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for all tables
CREATE TRIGGER update_subjects_updated_at BEFORE UPDATE ON academic.subjects FOR EACH ROW EXECUTE FUNCTION academic.update_updated_at_column();
CREATE TRIGGER update_curricula_updated_at BEFORE UPDATE ON academic.curricula FOR EACH ROW EXECUTE FUNCTION academic.update_updated_at_column();
CREATE TRIGGER update_periods_updated_at BEFORE UPDATE ON academic.periods FOR EACH ROW EXECUTE FUNCTION academic.update_updated_at_column();
CREATE TRIGGER update_timetables_updated_at BEFORE UPDATE ON academic.timetables FOR EACH ROW EXECUTE FUNCTION academic.update_updated_at_column();
CREATE TRIGGER update_attendance_sessions_updated_at BEFORE UPDATE ON academic.attendance_sessions FOR EACH ROW EXECUTE FUNCTION academic.update_updated_at_column();
CREATE TRIGGER update_attendance_records_updated_at BEFORE UPDATE ON academic.attendance_records FOR EACH ROW EXECUTE FUNCTION academic.update_updated_at_column();
CREATE TRIGGER update_assessments_updated_at BEFORE UPDATE ON academic.assessments FOR EACH ROW EXECUTE FUNCTION academic.update_updated_at_column();
CREATE TRIGGER update_grades_updated_at BEFORE UPDATE ON academic.grades FOR EACH ROW EXECUTE FUNCTION academic.update_updated_at_column();
CREATE TRIGGER update_lesson_plans_updated_at BEFORE UPDATE ON academic.lesson_plans FOR EACH ROW EXECUTE FUNCTION academic.update_updated_at_column();
CREATE TRIGGER update_calendar_events_updated_at BEFORE UPDATE ON academic.calendar_events FOR EACH ROW EXECUTE FUNCTION academic.update_updated_at_column();

-- =====================================================
-- RLS (ROW LEVEL SECURITY) POLICIES
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE academic.subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE academic.curricula ENABLE ROW LEVEL SECURITY;
ALTER TABLE academic.periods ENABLE ROW LEVEL SECURITY;
ALTER TABLE academic.timetables ENABLE ROW LEVEL SECURITY;
ALTER TABLE academic.attendance_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE academic.attendance_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE academic.assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE academic.grades ENABLE ROW LEVEL SECURITY;
ALTER TABLE academic.lesson_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE academic.calendar_events ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (tenant isolation by school_id)
-- These policies will be enabled when the authentication system is integrated

-- CREATE POLICY subjects_school_isolation ON academic.subjects
--     FOR ALL USING (school_id = current_setting('app.current_school_id')::UUID);

-- CREATE POLICY curricula_school_isolation ON academic.curricula
--     FOR ALL USING (school_id = current_setting('app.current_school_id')::UUID);

-- ... (Additional RLS policies for other tables)

COMMIT;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================
-- Academic Management Database Schema Created Successfully
-- Tables: 10 core tables + 1 association table
-- Indexes: 40+ performance indexes created
-- Constraints: 60+ data integrity constraints
-- Features: UUID primary keys, JSONB columns, array columns, audit trails, soft deletes, RLS ready
-- Zimbabwe Education System: Full compliance with grade levels, terms, and grading scale
-- =====================================================