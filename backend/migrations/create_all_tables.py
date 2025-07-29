#!/usr/bin/env python3
"""
OneClass Platform Database Migration Script
Creates all database schemas and tables for the complete platform
"""
import os
import sys
import asyncio
import asyncpg
import logging
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection settings
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://user:password@localhost:5432/oneclass"
)

async def create_database_connection():
    """Create database connection"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        logger.info("Connected to database successfully")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

async def create_schemas(conn):
    """Create all required database schemas"""
    schemas = ['platform', 'sis', 'academic', 'finance', 'analytics']
    
    for schema in schemas:
        try:
            await conn.execute(f'CREATE SCHEMA IF NOT EXISTS {schema}')
            logger.info(f"Schema '{schema}' created/verified")
        except Exception as e:
            logger.error(f"Failed to create schema '{schema}': {e}")
            raise

async def create_platform_tables(conn):
    """Create platform schema tables"""
    logger.info("Creating platform tables...")
    
    # Schools table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS platform.schools (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_name VARCHAR(255) NOT NULL,
            school_type VARCHAR(50) NOT NULL DEFAULT 'primary',
            subdomain VARCHAR(100) UNIQUE NOT NULL,
            domain_name VARCHAR(255),
            school_code VARCHAR(20) UNIQUE,
            registration_number VARCHAR(50),
            email VARCHAR(255),
            phone VARCHAR(20),
            address TEXT,
            city VARCHAR(100),
            province VARCHAR(100),
            postal_code VARCHAR(20),
            country VARCHAR(100) DEFAULT 'Zimbabwe',
            ministry_registration_number VARCHAR(100),
            license_number VARCHAR(100),
            principal_name VARCHAR(255),
            principal_email VARCHAR(255),
            principal_phone VARCHAR(20),
            subscription_tier VARCHAR(20) DEFAULT 'starter',
            subscription_status VARCHAR(20) DEFAULT 'trial',
            trial_end_date DATE,
            subscription_start_date DATE,
            subscription_end_date DATE,
            enabled_modules JSONB DEFAULT '[]',
            school_settings JSONB DEFAULT '{}',
            branding_settings JSONB DEFAULT '{}',
            is_active BOOLEAN DEFAULT true,
            onboarding_completed BOOLEAN DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    
    # Users table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS platform.users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID REFERENCES platform.schools(id) ON DELETE CASCADE,
            clerk_user_id VARCHAR(255) UNIQUE,
            email VARCHAR(255) UNIQUE NOT NULL,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            phone VARCHAR(20),
            role VARCHAR(50) NOT NULL,
            permissions JSONB DEFAULT '{}',
            profile_photo_url VARCHAR(500),
            last_login_at TIMESTAMP WITH TIME ZONE,
            is_active BOOLEAN DEFAULT true,
            email_verified BOOLEAN DEFAULT false,
            phone_verified BOOLEAN DEFAULT false,
            two_factor_enabled BOOLEAN DEFAULT false,
            timezone VARCHAR(50) DEFAULT 'Africa/Harare',
            language VARCHAR(10) DEFAULT 'en',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    
    # School configurations table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS platform.school_configurations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID REFERENCES platform.schools(id) ON DELETE CASCADE UNIQUE,
            academic_year_start_month INTEGER DEFAULT 1,
            academic_year_end_month INTEGER DEFAULT 12,
            default_currency VARCHAR(10) DEFAULT 'USD',
            timezone VARCHAR(50) DEFAULT 'Africa/Harare',
            language VARCHAR(10) DEFAULT 'en',
            date_format VARCHAR(20) DEFAULT 'DD/MM/YYYY',
            time_format VARCHAR(10) DEFAULT '24h',
            week_start_day INTEGER DEFAULT 1,
            grading_system VARCHAR(20) DEFAULT 'percentage',
            passing_grade DECIMAL(5,2) DEFAULT 50.00,
            attendance_tracking_enabled BOOLEAN DEFAULT true,
            parent_portal_enabled BOOLEAN DEFAULT true,
            student_portal_enabled BOOLEAN DEFAULT true,
            mobile_app_enabled BOOLEAN DEFAULT true,
            sms_notifications_enabled BOOLEAN DEFAULT false,
            email_notifications_enabled BOOLEAN DEFAULT true,
            backup_frequency VARCHAR(20) DEFAULT 'daily',
            data_retention_months INTEGER DEFAULT 60,
            ministry_reporting_enabled BOOLEAN DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    
    # School domains table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS platform.school_domains (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID REFERENCES platform.schools(id) ON DELETE CASCADE,
            domain_name VARCHAR(255) NOT NULL,
            domain_type VARCHAR(20) DEFAULT 'subdomain',
            is_primary BOOLEAN DEFAULT false,
            is_verified BOOLEAN DEFAULT false,
            verification_token VARCHAR(255),
            verification_method VARCHAR(50),
            verified_at TIMESTAMP WITH TIME ZONE,
            ssl_enabled BOOLEAN DEFAULT true,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(domain_name)
        )
    """)
    
    # School feature usage table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS platform.school_feature_usage (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID REFERENCES platform.schools(id) ON DELETE CASCADE,
            user_id UUID REFERENCES platform.users(id) ON DELETE SET NULL,
            feature_name VARCHAR(100) NOT NULL,
            usage_type VARCHAR(50) DEFAULT 'access',
            usage_count INTEGER DEFAULT 1,
            usage_date DATE NOT NULL,
            session_id VARCHAR(255),
            ip_address INET,
            user_agent TEXT,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_feature_usage_school_date ON platform.school_feature_usage(school_id, usage_date);
        CREATE INDEX IF NOT EXISTS idx_feature_usage_school_feature_date ON platform.school_feature_usage(school_id, feature_name, usage_date);
    """)
    
    logger.info("Platform tables created successfully")

async def create_sis_tables(conn):
    """Create Student Information System tables"""
    logger.info("Creating SIS tables...")
    
    # Students table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS sis.students (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            student_number VARCHAR(50) NOT NULL,
            national_id VARCHAR(50),
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            middle_name VARCHAR(100),
            date_of_birth DATE NOT NULL,
            gender VARCHAR(10) NOT NULL,
            email VARCHAR(255),
            phone VARCHAR(20),
            address TEXT,
            city VARCHAR(100),
            province VARCHAR(100),
            postal_code VARCHAR(20),
            current_class_id UUID,
            current_grade_level VARCHAR(20),
            admission_date DATE NOT NULL,
            graduation_date DATE,
            enrollment_status VARCHAR(20) DEFAULT 'active',
            is_active BOOLEAN DEFAULT true,
            primary_guardian_id UUID,
            secondary_guardian_id UUID,
            emergency_contact JSONB DEFAULT '{}',
            medical_conditions JSONB DEFAULT '[]',
            allergies JSONB DEFAULT '[]',
            medications JSONB DEFAULT '[]',
            emergency_medical_info TEXT,
            religion VARCHAR(50),
            nationality VARCHAR(50),
            language_spoken VARCHAR(50),
            previous_school VARCHAR(255),
            student_metadata JSONB DEFAULT '{}',
            profile_photo_url VARCHAR(500),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            deleted_at TIMESTAMP WITH TIME ZONE
        );
        
        CREATE INDEX IF NOT EXISTS idx_students_school_id ON sis.students(school_id);
        CREATE INDEX IF NOT EXISTS idx_students_student_number ON sis.students(student_number);
        CREATE INDEX IF NOT EXISTS idx_students_enrollment_status ON sis.students(enrollment_status);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_students_school_student_number ON sis.students(school_id, student_number);
    """)
    
    # Enrollments table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS sis.enrollments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            student_id UUID REFERENCES sis.students(id) ON DELETE CASCADE,
            academic_year_id UUID NOT NULL,
            class_id UUID NOT NULL,
            enrollment_date DATE NOT NULL,
            enrollment_type VARCHAR(20) DEFAULT 'new',
            enrollment_status VARCHAR(20) DEFAULT 'active',
            previous_school VARCHAR(255),
            previous_grade VARCHAR(20),
            transfer_reason TEXT,
            documents_submitted JSONB DEFAULT '[]',
            documents_verified BOOLEAN DEFAULT false,
            verified_by UUID,
            verification_date TIMESTAMP WITH TIME ZONE,
            exit_date DATE,
            exit_reason VARCHAR(100),
            exit_destination VARCHAR(255),
            enrolled_by UUID NOT NULL,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_enrollments_school_id ON sis.enrollments(school_id);
        CREATE INDEX IF NOT EXISTS idx_enrollments_student_id ON sis.enrollments(student_id);
        CREATE INDEX IF NOT EXISTS idx_enrollments_status ON sis.enrollments(enrollment_status);
    """)
    
    # Attendance records table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS sis.attendance_records (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            student_id UUID REFERENCES sis.students(id) ON DELETE CASCADE,
            attendance_date DATE NOT NULL,
            class_id UUID NOT NULL,
            academic_year_id UUID,
            term_id UUID,
            status VARCHAR(20) NOT NULL,
            check_in_time TIME,
            check_out_time TIME,
            absence_reason VARCHAR(100),
            is_excused BOOLEAN DEFAULT false,
            excuse_note TEXT,
            medical_certificate BOOLEAN DEFAULT false,
            period_attendance JSONB DEFAULT '{}',
            recorded_by UUID NOT NULL,
            recording_method VARCHAR(20) DEFAULT 'manual',
            parent_notified BOOLEAN DEFAULT false,
            notification_sent_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(student_id),
            INDEX(attendance_date),
            INDEX(status),
            UNIQUE(student_id, attendance_date, class_id)
        )
    """)
    
    # Disciplinary records table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS sis.disciplinary_records (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            student_id UUID REFERENCES sis.students(id) ON DELETE CASCADE,
            incident_date DATE NOT NULL,
            incident_type VARCHAR(50) NOT NULL,
            severity_level VARCHAR(20) DEFAULT 'minor',
            description TEXT NOT NULL,
            location VARCHAR(100),
            reported_by UUID NOT NULL,
            witnesses JSONB DEFAULT '[]',
            other_students_involved JSONB DEFAULT '[]',
            action_taken VARCHAR(100),
            action_details TEXT,
            action_date DATE,
            action_by UUID,
            follow_up_required BOOLEAN DEFAULT false,
            follow_up_date DATE,
            follow_up_notes TEXT,
            follow_up_by UUID,
            parent_contacted BOOLEAN DEFAULT false,
            parent_contact_date TIMESTAMP WITH TIME ZONE,
            parent_contact_method VARCHAR(20),
            parent_response TEXT,
            resolution_status VARCHAR(20) DEFAULT 'open',
            resolution_date DATE,
            resolution_notes TEXT,
            attachments JSONB DEFAULT '[]',
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(student_id),
            INDEX(incident_type),
            INDEX(severity_level)
        )
    """)
    
    # Medical records table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS sis.medical_records (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            student_id UUID REFERENCES sis.students(id) ON DELETE CASCADE,
            record_date DATE NOT NULL,
            record_type VARCHAR(50) NOT NULL,
            description TEXT NOT NULL,
            symptoms JSONB DEFAULT '[]',
            diagnosis TEXT,
            treatment TEXT,
            medical_professional VARCHAR(255),
            medical_facility VARCHAR(255),
            prescribed_medications JSONB DEFAULT '[]',
            medication_instructions TEXT,
            follow_up_required BOOLEAN DEFAULT false,
            follow_up_date DATE,
            follow_up_instructions TEXT,
            activity_restrictions JSONB DEFAULT '[]',
            dietary_restrictions JSONB DEFAULT '[]',
            emergency_action_plan TEXT,
            requires_emergency_medication BOOLEAN DEFAULT false,
            emergency_medication_details JSONB DEFAULT '{}',
            parent_notified BOOLEAN DEFAULT false,
            notification_date TIMESTAMP WITH TIME ZONE,
            confidential BOOLEAN DEFAULT true,
            access_level VARCHAR(20) DEFAULT 'medical_staff',
            recorded_by UUID NOT NULL,
            medical_documents JSONB DEFAULT '[]',
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(student_id),
            INDEX(record_type)
        )
    """)
    
    # Student notes table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS sis.student_notes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            student_id UUID REFERENCES sis.students(id) ON DELETE CASCADE,
            note_type VARCHAR(50) NOT NULL,
            title VARCHAR(255),
            content TEXT NOT NULL,
            priority VARCHAR(20) DEFAULT 'normal',
            visibility VARCHAR(20) DEFAULT 'staff',
            shared_with JSONB DEFAULT '[]',
            requires_follow_up BOOLEAN DEFAULT false,
            follow_up_date DATE,
            follow_up_assigned_to UUID,
            tags JSONB DEFAULT '[]',
            created_by UUID NOT NULL,
            is_active BOOLEAN DEFAULT true,
            is_archived BOOLEAN DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(student_id),
            INDEX(note_type),
            INDEX(created_by)
        )
    """)
    
    logger.info("SIS tables created successfully")

async def create_academic_tables(conn):
    """Create academic management tables"""
    logger.info("Creating academic tables...")
    
    # Subjects table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS academic.subjects (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            subject_name VARCHAR(255) NOT NULL,
            subject_code VARCHAR(20),
            description TEXT,
            department VARCHAR(100),
            credits INTEGER DEFAULT 1,
            is_core_subject BOOLEAN DEFAULT false,
            grade_levels JSONB DEFAULT '[]',
            prerequisites JSONB DEFAULT '[]',
            subject_type VARCHAR(50) DEFAULT 'academic',
            color_code VARCHAR(7) DEFAULT '#3b82f6',
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(subject_code),
            UNIQUE(school_id, subject_code)
        )
    """)
    
    # Academic years table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS academic.academic_years (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            year_name VARCHAR(100) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            is_current BOOLEAN DEFAULT false,
            status VARCHAR(20) DEFAULT 'planning',
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(is_current),
            UNIQUE(school_id, year_name)
        )
    """)
    
    # Terms table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS academic.terms (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            academic_year_id UUID REFERENCES academic.academic_years(id) ON DELETE CASCADE,
            term_name VARCHAR(100) NOT NULL,
            term_number INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            is_current BOOLEAN DEFAULT false,
            status VARCHAR(20) DEFAULT 'planning',
            holidays JSONB DEFAULT '[]',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(academic_year_id),
            INDEX(is_current),
            UNIQUE(school_id, academic_year_id, term_number)
        )
    """)
    
    # Classes table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS academic.classes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            class_name VARCHAR(100) NOT NULL,
            grade_level VARCHAR(20) NOT NULL,
            section VARCHAR(10),
            academic_year_id UUID REFERENCES academic.academic_years(id) ON DELETE CASCADE,
            class_teacher_id UUID,
            assistant_teacher_id UUID,
            room_number VARCHAR(50),
            max_capacity INTEGER DEFAULT 30,
            current_enrollment INTEGER DEFAULT 0,
            subjects JSONB DEFAULT '[]',
            timetable_id UUID,
            class_metadata JSONB DEFAULT '{}',
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(grade_level),
            INDEX(academic_year_id),
            UNIQUE(school_id, academic_year_id, class_name)
        )
    """)
    
    # Assessments table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS academic.assessments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            subject_id UUID REFERENCES academic.subjects(id) ON DELETE CASCADE,
            class_id UUID REFERENCES academic.classes(id) ON DELETE CASCADE,
            term_id UUID REFERENCES academic.terms(id) ON DELETE CASCADE,
            assessment_name VARCHAR(255) NOT NULL,
            assessment_type VARCHAR(50) NOT NULL,
            description TEXT,
            total_marks DECIMAL(10,2) NOT NULL,
            passing_marks DECIMAL(10,2),
            weightage DECIMAL(5,2) DEFAULT 100.00,
            assessment_date DATE,
            due_date DATE,
            duration_minutes INTEGER,
            instructions TEXT,
            rubric JSONB DEFAULT '{}',
            is_published BOOLEAN DEFAULT false,
            created_by UUID NOT NULL,
            graded_by UUID,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(subject_id),
            INDEX(class_id),
            INDEX(term_id),
            INDEX(assessment_type)
        )
    """)
    
    # Grades table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS academic.grades (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            student_id UUID NOT NULL,
            assessment_id UUID REFERENCES academic.assessments(id) ON DELETE CASCADE,
            subject_id UUID REFERENCES academic.subjects(id) ON DELETE CASCADE,
            class_id UUID REFERENCES academic.classes(id) ON DELETE CASCADE,
            term_id UUID REFERENCES academic.terms(id) ON DELETE CASCADE,
            marks_obtained DECIMAL(10,2),
            total_marks DECIMAL(10,2) NOT NULL,
            percentage DECIMAL(5,2),
            grade_letter VARCHAR(5),
            grade_points DECIMAL(4,2),
            remarks TEXT,
            is_absent BOOLEAN DEFAULT false,
            submission_date TIMESTAMP WITH TIME ZONE,
            graded_date TIMESTAMP WITH TIME ZONE,
            graded_by UUID NOT NULL,
            is_published BOOLEAN DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(student_id),
            INDEX(assessment_id),
            INDEX(subject_id),
            UNIQUE(student_id, assessment_id)
        )
    """)
    
    # Timetables table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS academic.timetables (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            class_id UUID REFERENCES academic.classes(id) ON DELETE CASCADE,
            academic_year_id UUID REFERENCES academic.academic_years(id) ON DELETE CASCADE,
            term_id UUID REFERENCES academic.terms(id) ON DELETE CASCADE,
            timetable_name VARCHAR(255) NOT NULL,
            effective_date DATE NOT NULL,
            schedule JSONB NOT NULL,
            is_active BOOLEAN DEFAULT true,
            created_by UUID NOT NULL,
            approved_by UUID,
            approval_date TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(class_id),
            INDEX(academic_year_id),
            INDEX(is_active)
        )
    """)
    
    # Lessons table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS academic.lessons (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            subject_id UUID REFERENCES academic.subjects(id) ON DELETE CASCADE,
            class_id UUID REFERENCES academic.classes(id) ON DELETE CASCADE,
            teacher_id UUID NOT NULL,
            lesson_title VARCHAR(255) NOT NULL,
            lesson_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            lesson_plan TEXT,
            learning_objectives JSONB DEFAULT '[]',
            resources_needed JSONB DEFAULT '[]',
            lesson_type VARCHAR(50) DEFAULT 'regular',
            attendance_taken BOOLEAN DEFAULT false,
            lesson_notes TEXT,
            homework_assigned TEXT,
            status VARCHAR(20) DEFAULT 'scheduled',
            room_number VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(subject_id),
            INDEX(class_id),
            INDEX(teacher_id),
            INDEX(lesson_date)
        )
    """)
    
    # Curriculum table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS academic.curriculum (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            curriculum_name VARCHAR(255) NOT NULL,
            curriculum_code VARCHAR(20),
            grade_level VARCHAR(20) NOT NULL,
            subject_id UUID REFERENCES academic.subjects(id) ON DELETE CASCADE,
            academic_year_id UUID REFERENCES academic.academic_years(id) ON DELETE CASCADE,
            learning_standards JSONB DEFAULT '[]',
            topics JSONB DEFAULT '[]',
            assessment_criteria JSONB DEFAULT '[]',
            resources JSONB DEFAULT '[]',
            pacing_guide JSONB DEFAULT '{}',
            ministry_approved BOOLEAN DEFAULT false,
            approval_date DATE,
            created_by UUID NOT NULL,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(subject_id),
            INDEX(grade_level),
            INDEX(academic_year_id)
        )
    """)
    
    logger.info("Academic tables created successfully")

async def create_finance_tables(conn):
    """Create finance management tables"""
    logger.info("Creating finance tables...")
    
    # Fee structures table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS finance.fee_structures (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            structure_name VARCHAR(255) NOT NULL,
            grade_level VARCHAR(20) NOT NULL,
            academic_year_id UUID NOT NULL,
            fee_categories JSONB NOT NULL,
            total_amount DECIMAL(12,2) NOT NULL,
            payment_schedule JSONB DEFAULT '[]',
            late_fee_policy JSONB DEFAULT '{}',
            discount_policy JSONB DEFAULT '{}',
            currency VARCHAR(10) DEFAULT 'USD',
            is_active BOOLEAN DEFAULT true,
            effective_date DATE NOT NULL,
            created_by UUID NOT NULL,
            approved_by UUID,
            approval_date TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(grade_level),
            INDEX(academic_year_id),
            UNIQUE(school_id, academic_year_id, grade_level, structure_name)
        )
    """)
    
    # Student fee assignments table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS finance.student_fee_assignments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            student_id UUID NOT NULL,
            fee_structure_id UUID REFERENCES finance.fee_structures(id) ON DELETE CASCADE,
            academic_year_id UUID NOT NULL,
            assigned_amount DECIMAL(12,2) NOT NULL,
            discount_amount DECIMAL(12,2) DEFAULT 0.00,
            final_amount DECIMAL(12,2) NOT NULL,
            discount_reason TEXT,
            special_arrangements JSONB DEFAULT '{}',
            assigned_by UUID NOT NULL,
            assigned_date DATE NOT NULL,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(student_id),
            INDEX(fee_structure_id),
            INDEX(academic_year_id),
            UNIQUE(student_id, academic_year_id)
        )
    """)
    
    # Invoices table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS finance.invoices (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            student_id UUID NOT NULL,
            invoice_number VARCHAR(50) UNIQUE NOT NULL,
            academic_year_id UUID NOT NULL,
            term_id UUID,
            invoice_date DATE NOT NULL,
            due_date DATE NOT NULL,
            invoice_items JSONB NOT NULL,
            subtotal DECIMAL(12,2) NOT NULL,
            discount_amount DECIMAL(12,2) DEFAULT 0.00,
            tax_amount DECIMAL(12,2) DEFAULT 0.00,
            total_amount DECIMAL(12,2) NOT NULL,
            amount_paid DECIMAL(12,2) DEFAULT 0.00,
            balance_due DECIMAL(12,2) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            payment_terms TEXT,
            notes TEXT,
            late_fee_applied DECIMAL(12,2) DEFAULT 0.00,
            currency VARCHAR(10) DEFAULT 'USD',
            generated_by UUID NOT NULL,
            sent_date TIMESTAMP WITH TIME ZONE,
            last_reminder_date DATE,
            reminder_count INTEGER DEFAULT 0,
            is_cancelled BOOLEAN DEFAULT false,
            cancelled_reason TEXT,
            cancelled_by UUID,
            cancelled_date TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(student_id),
            INDEX(invoice_number),
            INDEX(status),
            INDEX(due_date)
        )
    """)
    
    # Payments table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS finance.payments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            student_id UUID NOT NULL,
            invoice_id UUID REFERENCES finance.invoices(id) ON DELETE CASCADE,
            payment_reference VARCHAR(100) UNIQUE NOT NULL,
            payment_date DATE NOT NULL,
            amount DECIMAL(12,2) NOT NULL,
            payment_method VARCHAR(50) NOT NULL,
            payment_details JSONB DEFAULT '{}',
            transaction_id VARCHAR(100),
            gateway_response JSONB DEFAULT '{}',
            status VARCHAR(20) DEFAULT 'pending',
            processed_by UUID,
            processing_fee DECIMAL(12,2) DEFAULT 0.00,
            net_amount DECIMAL(12,2) NOT NULL,
            currency VARCHAR(10) DEFAULT 'USD',
            receipt_number VARCHAR(50),
            receipt_generated BOOLEAN DEFAULT false,
            notes TEXT,
            refund_amount DECIMAL(12,2) DEFAULT 0.00,
            refund_reason TEXT,
            refunded_by UUID,
            refund_date TIMESTAMP WITH TIME ZONE,
            reconciled BOOLEAN DEFAULT false,
            reconciliation_date TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(student_id),
            INDEX(invoice_id),
            INDEX(payment_reference),
            INDEX(status),
            INDEX(payment_date)
        )
    """)
    
    # Financial reports table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS finance.financial_reports (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            report_name VARCHAR(255) NOT NULL,
            report_type VARCHAR(50) NOT NULL,
            period_start DATE NOT NULL,
            period_end DATE NOT NULL,
            report_data JSONB NOT NULL,
            total_revenue DECIMAL(12,2) DEFAULT 0.00,
            total_expenses DECIMAL(12,2) DEFAULT 0.00,
            net_income DECIMAL(12,2) DEFAULT 0.00,
            generated_by UUID NOT NULL,
            generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            file_url VARCHAR(500),
            is_published BOOLEAN DEFAULT false,
            published_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(report_type),
            INDEX(period_start, period_end)
        )
    """)
    
    # Budgets table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS finance.budgets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            budget_name VARCHAR(255) NOT NULL,
            academic_year_id UUID NOT NULL,
            budget_type VARCHAR(50) DEFAULT 'annual',
            total_budget DECIMAL(12,2) NOT NULL,
            budget_categories JSONB NOT NULL,
            approval_workflow JSONB DEFAULT '[]',
            status VARCHAR(20) DEFAULT 'draft',
            approved_by UUID,
            approval_date TIMESTAMP WITH TIME ZONE,
            effective_date DATE NOT NULL,
            end_date DATE NOT NULL,
            created_by UUID NOT NULL,
            notes TEXT,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(academic_year_id),
            INDEX(status)
        )
    """)
    
    # Expenses table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS finance.expenses (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            expense_number VARCHAR(50) UNIQUE NOT NULL,
            expense_category VARCHAR(100) NOT NULL,
            subcategory VARCHAR(100),
            description TEXT NOT NULL,
            amount DECIMAL(12,2) NOT NULL,
            expense_date DATE NOT NULL,
            vendor_name VARCHAR(255),
            vendor_contact JSONB DEFAULT '{}',
            payment_method VARCHAR(50),
            reference_number VARCHAR(100),
            receipt_url VARCHAR(500),
            budget_id UUID REFERENCES finance.budgets(id) ON DELETE SET NULL,
            approved_by UUID,
            approval_date TIMESTAMP WITH TIME ZONE,
            status VARCHAR(20) DEFAULT 'pending',
            reimbursable BOOLEAN DEFAULT false,
            reimbursed BOOLEAN DEFAULT false,
            reimbursement_date TIMESTAMP WITH TIME ZONE,
            tax_deductible BOOLEAN DEFAULT false,
            currency VARCHAR(10) DEFAULT 'USD',
            exchange_rate DECIMAL(10,4) DEFAULT 1.0000,
            local_amount DECIMAL(12,2),
            created_by UUID NOT NULL,
            notes TEXT,
            tags JSONB DEFAULT '[]',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(expense_category),
            INDEX(expense_date),
            INDEX(status),
            INDEX(budget_id)
        )
    """)
    
    logger.info("Finance tables created successfully")

async def create_analytics_tables(conn):
    """Create analytics tables"""
    logger.info("Creating analytics tables...")
    
    # Analytics snapshots table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS analytics.snapshots (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            snapshot_date DATE NOT NULL,
            snapshot_type VARCHAR(50) NOT NULL,
            data JSONB NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(snapshot_date),
            INDEX(snapshot_type),
            UNIQUE(school_id, snapshot_date, snapshot_type)
        )
    """)
    
    # Report templates table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS analytics.report_templates (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            template_name VARCHAR(255) NOT NULL,
            template_type VARCHAR(50) NOT NULL,
            configuration JSONB NOT NULL,
            is_system_template BOOLEAN DEFAULT false,
            created_by UUID,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(template_type)
        )
    """)
    
    # Report executions table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS analytics.report_executions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            template_id UUID REFERENCES analytics.report_templates(id) ON DELETE CASCADE,
            executed_by UUID NOT NULL,
            execution_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            parameters JSONB DEFAULT '{}',
            status VARCHAR(20) DEFAULT 'pending',
            result_data JSONB,
            file_url VARCHAR(500),
            error_message TEXT,
            execution_time_ms INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX(school_id),
            INDEX(template_id),
            INDEX(executed_by),
            INDEX(status)
        )
    """)
    
    logger.info("Analytics tables created successfully")

async def create_indexes_and_constraints(conn):
    """Create additional indexes and constraints for performance"""
    logger.info("Creating additional indexes and constraints...")
    
    # Create function for updating timestamps
    await conn.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Create triggers for updating timestamps on all tables
    tables_with_updated_at = [
        'platform.schools', 'platform.users', 'platform.school_configurations',
        'platform.school_domains', 'sis.students', 'sis.enrollments', 
        'sis.attendance_records', 'sis.disciplinary_records', 'sis.medical_records',
        'sis.student_notes', 'academic.subjects', 'academic.academic_years',
        'academic.terms', 'academic.classes', 'academic.assessments', 'academic.grades',
        'academic.timetables', 'academic.lessons', 'academic.curriculum',
        'finance.fee_structures', 'finance.student_fee_assignments', 'finance.invoices',
        'finance.payments', 'finance.financial_reports', 'finance.budgets',
        'finance.expenses', 'analytics.report_templates'
    ]
    
    for table in tables_with_updated_at:
        trigger_name = f"update_{table.replace('.', '_')}_updated_at"
        await conn.execute(f"""
            CREATE TRIGGER {trigger_name}
                BEFORE UPDATE ON {table}
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """)
    
    logger.info("Indexes and constraints created successfully")

async def main():
    """Main migration function"""
    logger.info("Starting database migration...")
    
    conn = await create_database_connection()
    
    try:
        # Create schemas
        await create_schemas(conn)
        
        # Create tables in order (respecting foreign key dependencies)
        await create_platform_tables(conn)
        await create_sis_tables(conn)
        await create_academic_tables(conn)
        await create_finance_tables(conn)
        await create_analytics_tables(conn)
        
        # Create indexes and constraints
        await create_indexes_and_constraints(conn)
        
        logger.info("Database migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())