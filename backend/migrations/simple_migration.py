#!/usr/bin/env python3
"""
Simple OneClass Platform Database Migration Script
Creates all database schemas and core tables
"""
import os
import sys
import asyncio
import asyncpg
import logging

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection settings
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:123Bubblegums@localhost:5432/oneclass"
)

async def main():
    """Main migration function"""
    logger.info("Starting simple database migration...")
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        logger.info("Connected to database successfully")
        
        # Create schemas
        schemas = ['platform', 'sis', 'academic', 'finance', 'analytics']
        for schema in schemas:
            await conn.execute(f'CREATE SCHEMA IF NOT EXISTS {schema}')
            logger.info(f"Schema '{schema}' created/verified")
        
        # Create a simple test to ensure our updated analytics queries work
        # Students table (simplified)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sis.students (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                school_id UUID NOT NULL,
                student_number VARCHAR(50) NOT NULL,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                admission_date DATE NOT NULL,
                enrollment_status VARCHAR(20) DEFAULT 'active',
                is_active BOOLEAN DEFAULT true,
                deleted_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Attendance records table (simplified)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sis.attendance_records (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                school_id UUID NOT NULL,
                student_id UUID NOT NULL,
                attendance_date DATE NOT NULL,
                status VARCHAR(20) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Academic tables (simplified)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS academic.subjects (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                school_id UUID NOT NULL,
                subject_name VARCHAR(255) NOT NULL,
                subject_code VARCHAR(20),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS academic.assessments (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                school_id UUID NOT NULL,
                subject_id UUID NOT NULL,
                assessment_name VARCHAR(255) NOT NULL,
                assessment_type VARCHAR(50) NOT NULL,
                total_marks DECIMAL(10,2) NOT NULL,
                assessment_date DATE,
                is_published BOOLEAN DEFAULT false,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS academic.grades (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                school_id UUID NOT NULL,
                student_id UUID NOT NULL,
                assessment_id UUID NOT NULL,
                subject_id UUID NOT NULL,
                marks_obtained DECIMAL(10,2),
                total_marks DECIMAL(10,2) NOT NULL,
                percentage DECIMAL(5,2),
                is_published BOOLEAN DEFAULT false,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Finance tables (simplified)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS finance.invoices (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                school_id UUID NOT NULL,
                student_id UUID NOT NULL,
                invoice_number VARCHAR(50) UNIQUE NOT NULL,
                invoice_date DATE NOT NULL,
                total_amount DECIMAL(12,2) NOT NULL,
                amount_paid DECIMAL(12,2) DEFAULT 0.00,
                balance_due DECIMAL(12,2) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                is_cancelled BOOLEAN DEFAULT false,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS finance.payments (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                school_id UUID NOT NULL,
                student_id UUID NOT NULL,
                invoice_id UUID NOT NULL,
                payment_reference VARCHAR(100) UNIQUE NOT NULL,
                payment_date DATE NOT NULL,
                amount DECIMAL(12,2) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Platform feature usage table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS platform.school_feature_usage (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                school_id UUID NOT NULL,
                user_id UUID,
                feature_name VARCHAR(100) NOT NULL,
                usage_type VARCHAR(50) DEFAULT 'access',
                usage_count INTEGER DEFAULT 1,
                usage_date DATE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Platform users table  
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS platform.users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                school_id UUID NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                role VARCHAR(50) NOT NULL,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Create basic indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_students_school_id ON sis.students(school_id)",
            "CREATE INDEX IF NOT EXISTS idx_attendance_school_id ON sis.attendance_records(school_id)",
            "CREATE INDEX IF NOT EXISTS idx_attendance_student_id ON sis.attendance_records(student_id)",
            "CREATE INDEX IF NOT EXISTS idx_attendance_date ON sis.attendance_records(attendance_date)",
            "CREATE INDEX IF NOT EXISTS idx_grades_school_id ON academic.grades(school_id)",
            "CREATE INDEX IF NOT EXISTS idx_grades_student_id ON academic.grades(student_id)",
            "CREATE INDEX IF NOT EXISTS idx_grades_assessment_id ON academic.grades(assessment_id)",
            "CREATE INDEX IF NOT EXISTS idx_invoices_school_id ON finance.invoices(school_id)",
            "CREATE INDEX IF NOT EXISTS idx_payments_school_id ON finance.payments(school_id)",
            "CREATE INDEX IF NOT EXISTS idx_feature_usage_school_id ON platform.school_feature_usage(school_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_school_id ON platform.users(school_id)"
        ]
        
        for index_sql in indexes:
            await conn.execute(index_sql)
        
        logger.info("Database migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())