-- =====================================================
-- Academic Management Module Database Schema
-- File: database/schemas/02_academic.sql
-- Module: Academic Management (Module 02)
-- Version: 1.0
-- =====================================================

-- Drop existing schema if it exists (for development)
DROP SCHEMA IF EXISTS academic CASCADE;

-- Create academic schema
CREATE SCHEMA IF NOT EXISTS academic;

-- Set search path to include academic schema
SET search_path TO academic, public;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- SUBJECTS AND CURRICULUM MANAGEMENT
-- =====================================================

-- Subject definitions with Zimbabwe Education Ministry codes
CREATE TABLE academic.subjects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL,
    code VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    grade_levels INTEGER[] NOT NULL DEFAULT '{}',
    is_core BOOLEAN NOT NULL DEFAULT false,
    is_practical BOOLEAN NOT NULL DEFAULT false,
    requires_lab BOOLEAN NOT NULL DEFAULT false,
    pass_mark DECIMAL(5,2) NOT NULL DEFAULT 50.00,
    max_mark DECIMAL(5,2) NOT NULL DEFAULT 100.00,
    credit_hours INTEGER NOT NULL DEFAULT 1,
    department VARCHAR(50),
    language_of_instruction VARCHAR(20) NOT NULL DEFAULT 'English',
    is_active BOOLEAN NOT NULL DEFAULT true,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL,
    updated_by UUID,
    
    -- Constraints
    CONSTRAINT fk_subjects_school FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE,
    CONSTRAINT fk_subjects_created_by FOREIGN KEY (created_by) REFERENCES public.users(id),
    CONSTRAINT fk_subjects_updated_by FOREIGN KEY (updated_by) REFERENCES public.users(id),
    CONSTRAINT unique_subject_code_per_school UNIQUE (school_id, code),
    CONSTRAINT check_grade_levels CHECK (array_length(grade_levels, 1) > 0),
    CONSTRAINT check_pass_mark CHECK (pass_mark >= 0 AND pass_mark <= max_mark),
    CONSTRAINT check_max_mark CHECK (max_mark > 0),
    CONSTRAINT check_credit_hours CHECK (credit_hours > 0)
);

-- Curriculum management
CREATE TABLE academic.curricula (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    grade_level INTEGER NOT NULL,
    academic_year_id UUID NOT NULL,
    term_number INTEGER,
    subject_id UUID NOT NULL,
    learning_objectives TEXT[],
    learning_outcomes TEXT[],
    assessment_methods TEXT[],
    resources_required TEXT[],
    total_periods INTEGER NOT NULL DEFAULT 1,
    practical_periods INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    approved_by UUID,
    approved_at TIMESTAMP WITH TIME ZONE,
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL,
    updated_by UUID,
    
    -- Constraints
    CONSTRAINT fk_curricula_school FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE,
    CONSTRAINT fk_curricula_academic_year FOREIGN KEY (academic_year_id) REFERENCES public.academic_years(id),
    CONSTRAINT fk_curricula_subject FOREIGN KEY (subject_id) REFERENCES academic.subjects(id),
    CONSTRAINT fk_curricula_created_by FOREIGN KEY (created_by) REFERENCES public.users(id),
    CONSTRAINT fk_curricula_updated_by FOREIGN KEY (updated_by) REFERENCES public.users(id),
    CONSTRAINT fk_curricula_approved_by FOREIGN KEY (approved_by) REFERENCES public.users(id),
    CONSTRAINT check_grade_level CHECK (grade_level >= 1 AND grade_level <= 13),
    CONSTRAINT check_term_number CHECK (term_number IN (1, 2, 3)),
    CONSTRAINT check_total_periods CHECK (total_periods > 0),
    CONSTRAINT check_practical_periods CHECK (practical_periods >= 0 AND practical_periods <= total_periods),
    CONSTRAINT check_status CHECK (status IN ('draft', 'active', 'archived')),
    CONSTRAINT check_effective_dates CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

-- =====================================================
-- TIMETABLE AND SCHEDULING
-- =====================================================

-- Class periods definition
CREATE TABLE academic.periods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL,
    period_number INTEGER NOT NULL,
    name VARCHAR(50) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_break BOOLEAN NOT NULL DEFAULT false,
    break_type VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL,
    updated_by UUID,
    
    -- Constraints
    CONSTRAINT fk_periods_school FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE,
    CONSTRAINT fk_periods_created_by FOREIGN KEY (created_by) REFERENCES public.users(id),
    CONSTRAINT fk_periods_updated_by FOREIGN KEY (updated_by) REFERENCES public.users(id),
    CONSTRAINT unique_period_number_per_school UNIQUE (school_id, period_number),
    CONSTRAINT check_period_number CHECK (period_number > 0),
    CONSTRAINT check_time_order CHECK (end_time > start_time),
    CONSTRAINT check_break_type CHECK (break_type IS NULL OR break_type IN ('tea', 'lunch', 'assembly'))
);

-- Weekly timetable structure
CREATE TABLE academic.timetables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL,
    class_id UUID NOT NULL,
    academic_year_id UUID NOT NULL,
    term_number INTEGER NOT NULL,
    subject_id UUID NOT NULL,
    teacher_id UUID NOT NULL,
    period_id UUID NOT NULL,
    day_of_week INTEGER NOT NULL,
    room_number VARCHAR(20),
    is_double_period BOOLEAN NOT NULL DEFAULT false,
    is_practical BOOLEAN NOT NULL DEFAULT false,
    week_pattern VARCHAR(10) NOT NULL DEFAULT 'all',
    effective_from DATE NOT NULL,
    effective_to DATE,
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL,
    updated_by UUID,
    
    -- Constraints
    CONSTRAINT fk_timetables_school FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE,
    CONSTRAINT fk_timetables_class FOREIGN KEY (class_id) REFERENCES public.classes(id),
    CONSTRAINT fk_timetables_academic_year FOREIGN KEY (academic_year_id) REFERENCES public.academic_years(id),
    CONSTRAINT fk_timetables_subject FOREIGN KEY (subject_id) REFERENCES academic.subjects(id),
    CONSTRAINT fk_timetables_teacher FOREIGN KEY (teacher_id) REFERENCES public.users(id),
    CONSTRAINT fk_timetables_period FOREIGN KEY (period_id) REFERENCES academic.periods(id),
    CONSTRAINT fk_timetables_created_by FOREIGN KEY (created_by) REFERENCES public.users(id),
    CONSTRAINT fk_timetables_updated_by FOREIGN KEY (updated_by) REFERENCES public.users(id),
    CONSTRAINT check_day_of_week CHECK (day_of_week >= 1 AND day_of_week <= 7),
    CONSTRAINT check_term_number CHECK (term_number IN (1, 2, 3)),
    CONSTRAINT check_week_pattern CHECK (week_pattern IN ('all', 'odd', 'even')),
    CONSTRAINT check_effective_dates CHECK (effective_to IS NULL OR effective_to >= effective_from),
    CONSTRAINT unique_timetable_slot UNIQUE (school_id, class_id, period_id, day_of_week, effective_from)
);

-- =====================================================
-- ATTENDANCE MANAGEMENT
-- =====================================================

-- Attendance sessions for each timetable slot
CREATE TABLE academic.attendance_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL,
    timetable_id UUID NOT NULL,
    session_date DATE NOT NULL,
    period_id UUID NOT NULL,
    teacher_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    class_id UUID NOT NULL,
    session_type VARCHAR(20) NOT NULL DEFAULT 'regular',
    session_status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    attendance_marked BOOLEAN NOT NULL DEFAULT false,
    marked_by UUID,
    marked_at TIMESTAMP WITH TIME ZONE,
    total_students INTEGER NOT NULL DEFAULT 0,
    present_students INTEGER NOT NULL DEFAULT 0,
    absent_students INTEGER NOT NULL DEFAULT 0,
    late_students INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL,
    updated_by UUID,
    
    -- Constraints
    CONSTRAINT fk_attendance_sessions_school FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE,
    CONSTRAINT fk_attendance_sessions_timetable FOREIGN KEY (timetable_id) REFERENCES academic.timetables(id),
    CONSTRAINT fk_attendance_sessions_period FOREIGN KEY (period_id) REFERENCES academic.periods(id),
    CONSTRAINT fk_attendance_sessions_teacher FOREIGN KEY (teacher_id) REFERENCES public.users(id),
    CONSTRAINT fk_attendance_sessions_subject FOREIGN KEY (subject_id) REFERENCES academic.subjects(id),
    CONSTRAINT fk_attendance_sessions_class FOREIGN KEY (class_id) REFERENCES public.classes(id),
    CONSTRAINT fk_attendance_sessions_marked_by FOREIGN KEY (marked_by) REFERENCES public.users(id),
    CONSTRAINT fk_attendance_sessions_created_by FOREIGN KEY (created_by) REFERENCES public.users(id),
    CONSTRAINT fk_attendance_sessions_updated_by FOREIGN KEY (updated_by) REFERENCES public.users(id),
    CONSTRAINT check_session_type CHECK (session_type IN ('regular', 'makeup', 'extra', 'exam')),
    CONSTRAINT check_session_status CHECK (session_status IN ('scheduled', 'completed', 'cancelled', 'postponed')),
    CONSTRAINT check_attendance_totals CHECK (present_students + absent_students + late_students <= total_students),
    CONSTRAINT unique_session_per_timetable_date UNIQUE (school_id, timetable_id, session_date)
);

-- Student attendance records
CREATE TABLE academic.attendance_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL,
    attendance_session_id UUID NOT NULL,
    student_id UUID NOT NULL,
    attendance_status VARCHAR(20) NOT NULL DEFAULT 'present',
    arrival_time TIME,
    departure_time TIME,
    excuse_reason TEXT,
    is_excused BOOLEAN NOT NULL DEFAULT false,
    marked_by UUID NOT NULL,
    marked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL,
    updated_by UUID,
    
    -- Constraints
    CONSTRAINT fk_attendance_records_school FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE,
    CONSTRAINT fk_attendance_records_session FOREIGN KEY (attendance_session_id) REFERENCES academic.attendance_sessions(id),
    CONSTRAINT fk_attendance_records_student FOREIGN KEY (student_id) REFERENCES public.students(id),
    CONSTRAINT fk_attendance_records_marked_by FOREIGN KEY (marked_by) REFERENCES public.users(id),
    CONSTRAINT fk_attendance_records_created_by FOREIGN KEY (created_by) REFERENCES public.users(id),
    CONSTRAINT fk_attendance_records_updated_by FOREIGN KEY (updated_by) REFERENCES public.users(id),
    CONSTRAINT check_attendance_status CHECK (attendance_status IN ('present', 'absent', 'late', 'excused')),
    CONSTRAINT check_arrival_departure CHECK (departure_time IS NULL OR arrival_time IS NULL OR departure_time >= arrival_time),
    CONSTRAINT unique_student_session_attendance UNIQUE (school_id, attendance_session_id, student_id)
);

-- =====================================================
-- ASSESSMENT AND GRADING
-- =====================================================

-- Assessment types and definitions
CREATE TABLE academic.assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    subject_id UUID NOT NULL,
    class_id UUID NOT NULL,
    teacher_id UUID NOT NULL,
    academic_year_id UUID NOT NULL,
    term_number INTEGER NOT NULL,
    assessment_type VARCHAR(50) NOT NULL,
    assessment_category VARCHAR(50) NOT NULL DEFAULT 'continuous',
    total_marks DECIMAL(8,2) NOT NULL DEFAULT 100.00,
    pass_mark DECIMAL(8,2) NOT NULL DEFAULT 50.00,
    weight_percentage DECIMAL(5,2) NOT NULL DEFAULT 100.00,
    assessment_date DATE NOT NULL,
    due_date DATE,
    duration_minutes INTEGER,
    instructions TEXT,
    resources_allowed TEXT[],
    is_group_assessment BOOLEAN NOT NULL DEFAULT false,
    max_group_size INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    published_at TIMESTAMP WITH TIME ZONE,
    published_by UUID,
    results_published BOOLEAN NOT NULL DEFAULT false,
    results_published_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL,
    updated_by UUID,
    
    -- Constraints
    CONSTRAINT fk_assessments_school FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE,
    CONSTRAINT fk_assessments_subject FOREIGN KEY (subject_id) REFERENCES academic.subjects(id),
    CONSTRAINT fk_assessments_class FOREIGN KEY (class_id) REFERENCES public.classes(id),
    CONSTRAINT fk_assessments_teacher FOREIGN KEY (teacher_id) REFERENCES public.users(id),
    CONSTRAINT fk_assessments_academic_year FOREIGN KEY (academic_year_id) REFERENCES public.academic_years(id),
    CONSTRAINT fk_assessments_published_by FOREIGN KEY (published_by) REFERENCES public.users(id),
    CONSTRAINT fk_assessments_created_by FOREIGN KEY (created_by) REFERENCES public.users(id),
    CONSTRAINT fk_assessments_updated_by FOREIGN KEY (updated_by) REFERENCES public.users(id),
    CONSTRAINT check_term_number CHECK (term_number IN (1, 2, 3)),
    CONSTRAINT check_assessment_type CHECK (assessment_type IN ('test', 'quiz', 'assignment', 'project', 'practical', 'oral', 'exam')),
    CONSTRAINT check_assessment_category CHECK (assessment_category IN ('continuous', 'formative', 'summative', 'final')),
    CONSTRAINT check_total_marks CHECK (total_marks > 0),
    CONSTRAINT check_pass_mark CHECK (pass_mark >= 0 AND pass_mark <= total_marks),
    CONSTRAINT check_weight_percentage CHECK (weight_percentage > 0 AND weight_percentage <= 100),
    CONSTRAINT check_duration CHECK (duration_minutes IS NULL OR duration_minutes > 0),
    CONSTRAINT check_group_size CHECK (max_group_size IS NULL OR max_group_size > 1),
    CONSTRAINT check_status CHECK (status IN ('draft', 'published', 'completed', 'cancelled')),
    CONSTRAINT check_dates CHECK (due_date IS NULL OR due_date >= assessment_date)
);

-- Student grades and assessment results
CREATE TABLE academic.grades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL,
    assessment_id UUID NOT NULL,
    student_id UUID NOT NULL,
    raw_score DECIMAL(8,2),
    percentage_score DECIMAL(5,2),
    letter_grade VARCHAR(5),
    grade_points DECIMAL(4,2),
    is_absent BOOLEAN NOT NULL DEFAULT false,
    is_excused BOOLEAN NOT NULL DEFAULT false,
    submission_date TIMESTAMP WITH TIME ZONE,
    graded_by UUID NOT NULL,
    graded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    feedback TEXT,
    improvement_suggestions TEXT,
    next_steps TEXT,
    parent_viewed BOOLEAN NOT NULL DEFAULT false,
    parent_viewed_at TIMESTAMP WITH TIME ZONE,
    is_final BOOLEAN NOT NULL DEFAULT false,
    moderated_by UUID,
    moderated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL,
    updated_by UUID,
    
    -- Constraints
    CONSTRAINT fk_grades_school FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE,
    CONSTRAINT fk_grades_assessment FOREIGN KEY (assessment_id) REFERENCES academic.assessments(id),
    CONSTRAINT fk_grades_student FOREIGN KEY (student_id) REFERENCES public.students(id),
    CONSTRAINT fk_grades_graded_by FOREIGN KEY (graded_by) REFERENCES public.users(id),
    CONSTRAINT fk_grades_moderated_by FOREIGN KEY (moderated_by) REFERENCES public.users(id),
    CONSTRAINT fk_grades_created_by FOREIGN KEY (created_by) REFERENCES public.users(id),
    CONSTRAINT fk_grades_updated_by FOREIGN KEY (updated_by) REFERENCES public.users(id),
    CONSTRAINT check_percentage_score CHECK (percentage_score IS NULL OR (percentage_score >= 0 AND percentage_score <= 100)),
    CONSTRAINT check_letter_grade CHECK (letter_grade IS NULL OR letter_grade IN ('A', 'B', 'C', 'D', 'E', 'U')),
    CONSTRAINT check_grade_points CHECK (grade_points IS NULL OR (grade_points >= 0 AND grade_points <= 4)),
    CONSTRAINT unique_student_assessment_grade UNIQUE (school_id, assessment_id, student_id)
);

-- =====================================================
-- LESSON PLANNING
-- =====================================================

-- Lesson plans
CREATE TABLE academic.lesson_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    subject_id UUID NOT NULL,
    class_id UUID NOT NULL,
    teacher_id UUID NOT NULL,
    academic_year_id UUID NOT NULL,
    term_number INTEGER NOT NULL,
    curriculum_id UUID,
    lesson_date DATE NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 40,
    learning_objectives TEXT[],
    learning_outcomes TEXT[],
    prerequisite_knowledge TEXT[],
    materials_required TEXT[],
    teaching_methods TEXT[],
    lesson_structure JSONB,
    assessment_activities TEXT[],
    homework_assignments TEXT[],
    differentiation_strategies TEXT[],
    extension_activities TEXT[],
    reflection_notes TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    shared_with UUID[],
    is_template BOOLEAN NOT NULL DEFAULT false,
    template_category VARCHAR(50),
    version INTEGER NOT NULL DEFAULT 1,
    parent_lesson_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL,
    updated_by UUID,
    
    -- Constraints
    CONSTRAINT fk_lesson_plans_school FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE,
    CONSTRAINT fk_lesson_plans_subject FOREIGN KEY (subject_id) REFERENCES academic.subjects(id),
    CONSTRAINT fk_lesson_plans_class FOREIGN KEY (class_id) REFERENCES public.classes(id),
    CONSTRAINT fk_lesson_plans_teacher FOREIGN KEY (teacher_id) REFERENCES public.users(id),
    CONSTRAINT fk_lesson_plans_academic_year FOREIGN KEY (academic_year_id) REFERENCES public.academic_years(id),
    CONSTRAINT fk_lesson_plans_curriculum FOREIGN KEY (curriculum_id) REFERENCES academic.curricula(id),
    CONSTRAINT fk_lesson_plans_parent FOREIGN KEY (parent_lesson_id) REFERENCES academic.lesson_plans(id),
    CONSTRAINT fk_lesson_plans_created_by FOREIGN KEY (created_by) REFERENCES public.users(id),
    CONSTRAINT fk_lesson_plans_updated_by FOREIGN KEY (updated_by) REFERENCES public.users(id),
    CONSTRAINT check_term_number CHECK (term_number IN (1, 2, 3)),
    CONSTRAINT check_duration CHECK (duration_minutes > 0),
    CONSTRAINT check_status CHECK (status IN ('draft', 'active', 'completed', 'archived')),
    CONSTRAINT check_version CHECK (version > 0)
);

-- =====================================================
-- ACADEMIC CALENDAR
-- =====================================================

-- Academic calendar events
CREATE TABLE academic.calendar_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    event_type VARCHAR(50) NOT NULL,
    event_category VARCHAR(50) NOT NULL DEFAULT 'academic',
    start_date DATE NOT NULL,
    end_date DATE,
    start_time TIME,
    end_time TIME,
    is_all_day BOOLEAN NOT NULL DEFAULT true,
    location VARCHAR(200),
    academic_year_id UUID NOT NULL,
    term_number INTEGER,
    grade_levels INTEGER[],
    class_ids UUID[],
    subject_ids UUID[],
    teacher_ids UUID[],
    is_recurring BOOLEAN NOT NULL DEFAULT false,
    recurrence_pattern VARCHAR(50),
    recurrence_end_date DATE,
    reminder_days INTEGER[] DEFAULT '{1, 7}',
    is_public BOOLEAN NOT NULL DEFAULT false,
    requires_attendance BOOLEAN NOT NULL DEFAULT false,
    max_participants INTEGER,
    registration_required BOOLEAN NOT NULL DEFAULT false,
    registration_deadline DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL,
    updated_by UUID,
    
    -- Constraints
    CONSTRAINT fk_calendar_events_school FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE,
    CONSTRAINT fk_calendar_events_academic_year FOREIGN KEY (academic_year_id) REFERENCES public.academic_years(id),
    CONSTRAINT fk_calendar_events_created_by FOREIGN KEY (created_by) REFERENCES public.users(id),
    CONSTRAINT fk_calendar_events_updated_by FOREIGN KEY (updated_by) REFERENCES public.users(id),
    CONSTRAINT check_event_type CHECK (event_type IN ('holiday', 'exam', 'assessment', 'sports', 'cultural', 'meeting', 'training', 'other')),
    CONSTRAINT check_event_category CHECK (event_category IN ('academic', 'administrative', 'social', 'sports', 'cultural')),
    CONSTRAINT check_term_number CHECK (term_number IS NULL OR term_number IN (1, 2, 3)),
    CONSTRAINT check_dates CHECK (end_date IS NULL OR end_date >= start_date),
    CONSTRAINT check_times CHECK (start_time IS NULL OR end_time IS NULL OR end_time >= start_time),
    CONSTRAINT check_recurrence_end CHECK (recurrence_end_date IS NULL OR recurrence_end_date >= start_date),
    CONSTRAINT check_max_participants CHECK (max_participants IS NULL OR max_participants > 0),
    CONSTRAINT check_registration_deadline CHECK (registration_deadline IS NULL OR registration_deadline <= start_date),
    CONSTRAINT check_status CHECK (status IN ('scheduled', 'confirmed', 'cancelled', 'completed', 'postponed'))
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Subjects indexes
CREATE INDEX idx_subjects_school_id ON academic.subjects(school_id);
CREATE INDEX idx_subjects_code ON academic.subjects(code);
CREATE INDEX idx_subjects_grade_levels ON academic.subjects USING GIN(grade_levels);
CREATE INDEX idx_subjects_active ON academic.subjects(is_active) WHERE is_active = true;

-- Curricula indexes
CREATE INDEX idx_curricula_school_id ON academic.curricula(school_id);
CREATE INDEX idx_curricula_subject_id ON academic.curricula(subject_id);
CREATE INDEX idx_curricula_academic_year_id ON academic.curricula(academic_year_id);
CREATE INDEX idx_curricula_grade_level ON academic.curricula(grade_level);
CREATE INDEX idx_curricula_status ON academic.curricula(status);

-- Periods indexes
CREATE INDEX idx_periods_school_id ON academic.periods(school_id);
CREATE INDEX idx_periods_active ON academic.periods(is_active) WHERE is_active = true;

-- Timetables indexes
CREATE INDEX idx_timetables_school_id ON academic.timetables(school_id);
CREATE INDEX idx_timetables_class_id ON academic.timetables(class_id);
CREATE INDEX idx_timetables_teacher_id ON academic.timetables(teacher_id);
CREATE INDEX idx_timetables_subject_id ON academic.timetables(subject_id);
CREATE INDEX idx_timetables_academic_year_id ON academic.timetables(academic_year_id);
CREATE INDEX idx_timetables_day_period ON academic.timetables(day_of_week, period_id);
CREATE INDEX idx_timetables_effective_dates ON academic.timetables(effective_from, effective_to);

-- Attendance sessions indexes
CREATE INDEX idx_attendance_sessions_school_id ON academic.attendance_sessions(school_id);
CREATE INDEX idx_attendance_sessions_class_id ON academic.attendance_sessions(class_id);
CREATE INDEX idx_attendance_sessions_teacher_id ON academic.attendance_sessions(teacher_id);
CREATE INDEX idx_attendance_sessions_date ON academic.attendance_sessions(session_date);
CREATE INDEX idx_attendance_sessions_timetable_id ON academic.attendance_sessions(timetable_id);

-- Attendance records indexes
CREATE INDEX idx_attendance_records_school_id ON academic.attendance_records(school_id);
CREATE INDEX idx_attendance_records_student_id ON academic.attendance_records(student_id);
CREATE INDEX idx_attendance_records_session_id ON academic.attendance_records(attendance_session_id);
CREATE INDEX idx_attendance_records_status ON academic.attendance_records(attendance_status);
CREATE INDEX idx_attendance_records_marked_at ON academic.attendance_records(marked_at);

-- Assessments indexes
CREATE INDEX idx_assessments_school_id ON academic.assessments(school_id);
CREATE INDEX idx_assessments_subject_id ON academic.assessments(subject_id);
CREATE INDEX idx_assessments_class_id ON academic.assessments(class_id);
CREATE INDEX idx_assessments_teacher_id ON academic.assessments(teacher_id);
CREATE INDEX idx_assessments_academic_year_id ON academic.assessments(academic_year_id);
CREATE INDEX idx_assessments_date ON academic.assessments(assessment_date);
CREATE INDEX idx_assessments_type ON academic.assessments(assessment_type);
CREATE INDEX idx_assessments_status ON academic.assessments(status);

-- Grades indexes
CREATE INDEX idx_grades_school_id ON academic.grades(school_id);
CREATE INDEX idx_grades_assessment_id ON academic.grades(assessment_id);
CREATE INDEX idx_grades_student_id ON academic.grades(student_id);
CREATE INDEX idx_grades_letter_grade ON academic.grades(letter_grade);
CREATE INDEX idx_grades_graded_at ON academic.grades(graded_at);

-- Lesson plans indexes
CREATE INDEX idx_lesson_plans_school_id ON academic.lesson_plans(school_id);
CREATE INDEX idx_lesson_plans_subject_id ON academic.lesson_plans(subject_id);
CREATE INDEX idx_lesson_plans_class_id ON academic.lesson_plans(class_id);
CREATE INDEX idx_lesson_plans_teacher_id ON academic.lesson_plans(teacher_id);
CREATE INDEX idx_lesson_plans_date ON academic.lesson_plans(lesson_date);
CREATE INDEX idx_lesson_plans_status ON academic.lesson_plans(status);
CREATE INDEX idx_lesson_plans_template ON academic.lesson_plans(is_template) WHERE is_template = true;

-- Calendar events indexes
CREATE INDEX idx_calendar_events_school_id ON academic.calendar_events(school_id);
CREATE INDEX idx_calendar_events_academic_year_id ON academic.calendar_events(academic_year_id);
CREATE INDEX idx_calendar_events_dates ON academic.calendar_events(start_date, end_date);
CREATE INDEX idx_calendar_events_type ON academic.calendar_events(event_type);
CREATE INDEX idx_calendar_events_status ON academic.calendar_events(status);
CREATE INDEX idx_calendar_events_grade_levels ON academic.calendar_events USING GIN(grade_levels);

-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
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

-- Create policies for each table
-- Note: These policies assume a current_user_school_id() function exists
-- and users have appropriate role claims

-- Subjects policies
CREATE POLICY subjects_select_policy ON academic.subjects
    FOR SELECT USING (school_id = current_user_school_id());

CREATE POLICY subjects_insert_policy ON academic.subjects
    FOR INSERT WITH CHECK (school_id = current_user_school_id());

CREATE POLICY subjects_update_policy ON academic.subjects
    FOR UPDATE USING (school_id = current_user_school_id())
    WITH CHECK (school_id = current_user_school_id());

CREATE POLICY subjects_delete_policy ON academic.subjects
    FOR DELETE USING (school_id = current_user_school_id());

-- Curricula policies
CREATE POLICY curricula_select_policy ON academic.curricula
    FOR SELECT USING (school_id = current_user_school_id());

CREATE POLICY curricula_insert_policy ON academic.curricula
    FOR INSERT WITH CHECK (school_id = current_user_school_id());

CREATE POLICY curricula_update_policy ON academic.curricula
    FOR UPDATE USING (school_id = current_user_school_id())
    WITH CHECK (school_id = current_user_school_id());

CREATE POLICY curricula_delete_policy ON academic.curricula
    FOR DELETE USING (school_id = current_user_school_id());

-- Periods policies
CREATE POLICY periods_select_policy ON academic.periods
    FOR SELECT USING (school_id = current_user_school_id());

CREATE POLICY periods_insert_policy ON academic.periods
    FOR INSERT WITH CHECK (school_id = current_user_school_id());

CREATE POLICY periods_update_policy ON academic.periods
    FOR UPDATE USING (school_id = current_user_school_id())
    WITH CHECK (school_id = current_user_school_id());

CREATE POLICY periods_delete_policy ON academic.periods
    FOR DELETE USING (school_id = current_user_school_id());

-- Timetables policies
CREATE POLICY timetables_select_policy ON academic.timetables
    FOR SELECT USING (school_id = current_user_school_id());

CREATE POLICY timetables_insert_policy ON academic.timetables
    FOR INSERT WITH CHECK (school_id = current_user_school_id());

CREATE POLICY timetables_update_policy ON academic.timetables
    FOR UPDATE USING (school_id = current_user_school_id())
    WITH CHECK (school_id = current_user_school_id());

CREATE POLICY timetables_delete_policy ON academic.timetables
    FOR DELETE USING (school_id = current_user_school_id());

-- Attendance sessions policies
CREATE POLICY attendance_sessions_select_policy ON academic.attendance_sessions
    FOR SELECT USING (school_id = current_user_school_id());

CREATE POLICY attendance_sessions_insert_policy ON academic.attendance_sessions
    FOR INSERT WITH CHECK (school_id = current_user_school_id());

CREATE POLICY attendance_sessions_update_policy ON academic.attendance_sessions
    FOR UPDATE USING (school_id = current_user_school_id())
    WITH CHECK (school_id = current_user_school_id());

CREATE POLICY attendance_sessions_delete_policy ON academic.attendance_sessions
    FOR DELETE USING (school_id = current_user_school_id());

-- Attendance records policies
CREATE POLICY attendance_records_select_policy ON academic.attendance_records
    FOR SELECT USING (school_id = current_user_school_id());

CREATE POLICY attendance_records_insert_policy ON academic.attendance_records
    FOR INSERT WITH CHECK (school_id = current_user_school_id());

CREATE POLICY attendance_records_update_policy ON academic.attendance_records
    FOR UPDATE USING (school_id = current_user_school_id())
    WITH CHECK (school_id = current_user_school_id());

CREATE POLICY attendance_records_delete_policy ON academic.attendance_records
    FOR DELETE USING (school_id = current_user_school_id());

-- Assessments policies
CREATE POLICY assessments_select_policy ON academic.assessments
    FOR SELECT USING (school_id = current_user_school_id());

CREATE POLICY assessments_insert_policy ON academic.assessments
    FOR INSERT WITH CHECK (school_id = current_user_school_id());

CREATE POLICY assessments_update_policy ON academic.assessments
    FOR UPDATE USING (school_id = current_user_school_id())
    WITH CHECK (school_id = current_user_school_id());

CREATE POLICY assessments_delete_policy ON academic.assessments
    FOR DELETE USING (school_id = current_user_school_id());

-- Grades policies
CREATE POLICY grades_select_policy ON academic.grades
    FOR SELECT USING (school_id = current_user_school_id());

CREATE POLICY grades_insert_policy ON academic.grades
    FOR INSERT WITH CHECK (school_id = current_user_school_id());

CREATE POLICY grades_update_policy ON academic.grades
    FOR UPDATE USING (school_id = current_user_school_id())
    WITH CHECK (school_id = current_user_school_id());

CREATE POLICY grades_delete_policy ON academic.grades
    FOR DELETE USING (school_id = current_user_school_id());

-- Lesson plans policies
CREATE POLICY lesson_plans_select_policy ON academic.lesson_plans
    FOR SELECT USING (school_id = current_user_school_id());

CREATE POLICY lesson_plans_insert_policy ON academic.lesson_plans
    FOR INSERT WITH CHECK (school_id = current_user_school_id());

CREATE POLICY lesson_plans_update_policy ON academic.lesson_plans
    FOR UPDATE USING (school_id = current_user_school_id())
    WITH CHECK (school_id = current_user_school_id());

CREATE POLICY lesson_plans_delete_policy ON academic.lesson_plans
    FOR DELETE USING (school_id = current_user_school_id());

-- Calendar events policies
CREATE POLICY calendar_events_select_policy ON academic.calendar_events
    FOR SELECT USING (school_id = current_user_school_id());

CREATE POLICY calendar_events_insert_policy ON academic.calendar_events
    FOR INSERT WITH CHECK (school_id = current_user_school_id());

CREATE POLICY calendar_events_update_policy ON academic.calendar_events
    FOR UPDATE USING (school_id = current_user_school_id())
    WITH CHECK (school_id = current_user_school_id());

CREATE POLICY calendar_events_delete_policy ON academic.calendar_events
    FOR DELETE USING (school_id = current_user_school_id());

-- =====================================================
-- TRIGGERS FOR UPDATED_AT
-- =====================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION academic.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for all tables
CREATE TRIGGER update_subjects_updated_at BEFORE UPDATE ON academic.subjects
    FOR EACH ROW EXECUTE FUNCTION academic.update_updated_at_column();

CREATE TRIGGER update_curricula_updated_at BEFORE UPDATE ON academic.curricula
    FOR EACH ROW EXECUTE FUNCTION academic.update_updated_at_column();

CREATE TRIGGER update_periods_updated_at BEFORE UPDATE ON academic.periods
    FOR EACH ROW EXECUTE FUNCTION academic.update_updated_at_column();

CREATE TRIGGER update_timetables_updated_at BEFORE UPDATE ON academic.timetables
    FOR EACH ROW EXECUTE FUNCTION academic.update_updated_at_column();

CREATE TRIGGER update_attendance_sessions_updated_at BEFORE UPDATE ON academic.attendance_sessions
    FOR EACH ROW EXECUTE FUNCTION academic.update_updated_at_column();

CREATE TRIGGER update_attendance_records_updated_at BEFORE UPDATE ON academic.attendance_records
    FOR EACH ROW EXECUTE FUNCTION academic.update_updated_at_column();

CREATE TRIGGER update_assessments_updated_at BEFORE UPDATE ON academic.assessments
    FOR EACH ROW EXECUTE FUNCTION academic.update_updated_at_column();

CREATE TRIGGER update_grades_updated_at BEFORE UPDATE ON academic.grades
    FOR EACH ROW EXECUTE FUNCTION academic.update_updated_at_column();

CREATE TRIGGER update_lesson_plans_updated_at BEFORE UPDATE ON academic.lesson_plans
    FOR EACH ROW EXECUTE FUNCTION academic.update_updated_at_column();

CREATE TRIGGER update_calendar_events_updated_at BEFORE UPDATE ON academic.calendar_events
    FOR EACH ROW EXECUTE FUNCTION academic.update_updated_at_column();

-- =====================================================
-- UTILITY FUNCTIONS
-- =====================================================

-- Function to get student attendance rate
CREATE OR REPLACE FUNCTION academic.get_student_attendance_rate(
    p_student_id UUID,
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL
) RETURNS DECIMAL AS $$
DECLARE
    attendance_rate DECIMAL;
BEGIN
    SELECT 
        CASE 
            WHEN COUNT(*) = 0 THEN 0
            ELSE ROUND(
                (COUNT(*) FILTER (WHERE attendance_status = 'present') * 100.0) / COUNT(*),
                2
            )
        END INTO attendance_rate
    FROM academic.attendance_records ar
    JOIN academic.attendance_sessions ass ON ar.attendance_session_id = ass.id
    WHERE ar.student_id = p_student_id
    AND (p_start_date IS NULL OR ass.session_date >= p_start_date)
    AND (p_end_date IS NULL OR ass.session_date <= p_end_date);
    
    RETURN attendance_rate;
END;
$$ LANGUAGE plpgsql;

-- Function to get class attendance statistics
CREATE OR REPLACE FUNCTION academic.get_class_attendance_stats(
    p_class_id UUID,
    p_session_date DATE
) RETURNS TABLE(
    total_students INTEGER,
    present_students INTEGER,
    absent_students INTEGER,
    late_students INTEGER,
    attendance_rate DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(ar.student_id)::INTEGER as total_students,
        COUNT(ar.student_id) FILTER (WHERE ar.attendance_status = 'present')::INTEGER as present_students,
        COUNT(ar.student_id) FILTER (WHERE ar.attendance_status = 'absent')::INTEGER as absent_students,
        COUNT(ar.student_id) FILTER (WHERE ar.attendance_status = 'late')::INTEGER as late_students,
        CASE 
            WHEN COUNT(ar.student_id) = 0 THEN 0
            ELSE ROUND(
                (COUNT(ar.student_id) FILTER (WHERE ar.attendance_status = 'present') * 100.0) / COUNT(ar.student_id),
                2
            )
        END as attendance_rate
    FROM academic.attendance_records ar
    JOIN academic.attendance_sessions ass ON ar.attendance_session_id = ass.id
    WHERE ass.class_id = p_class_id
    AND ass.session_date = p_session_date;
END;
$$ LANGUAGE plpgsql;

-- Function to get teacher timetable
CREATE OR REPLACE FUNCTION academic.get_teacher_timetable(
    p_teacher_id UUID,
    p_academic_year_id UUID,
    p_term_number INTEGER DEFAULT NULL
) RETURNS TABLE(
    day_of_week INTEGER,
    period_number INTEGER,
    period_name VARCHAR(50),
    start_time TIME,
    end_time TIME,
    subject_name VARCHAR(100),
    class_name VARCHAR(100),
    room_number VARCHAR(20)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.day_of_week,
        p.period_number,
        p.name as period_name,
        p.start_time,
        p.end_time,
        s.name as subject_name,
        c.name as class_name,
        t.room_number
    FROM academic.timetables t
    JOIN academic.periods p ON t.period_id = p.id
    JOIN academic.subjects s ON t.subject_id = s.id
    JOIN public.classes c ON t.class_id = c.id
    WHERE t.teacher_id = p_teacher_id
    AND t.academic_year_id = p_academic_year_id
    AND (p_term_number IS NULL OR t.term_number = p_term_number)
    AND t.is_active = true
    ORDER BY t.day_of_week, p.period_number;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- SCHEMA COMPLETE
-- =====================================================

-- Reset search path
SET search_path TO public;