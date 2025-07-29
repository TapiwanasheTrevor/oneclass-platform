# OneClass Platform Database Schema Documentation

## 🏗️ Architecture Overview

The OneClass Platform uses a **multi-schema PostgreSQL database** designed for multi-tenant SaaS architecture with strict data isolation between schools.

### **Schema Organization**
```
oneclass_db/
├── platform/          # Platform-wide data (schools, users, configs)
├── sis/               # Student Information System
├── academic/          # Academic management (curriculum, assessments)
├── finance/           # Financial management (fees, payments)
└── analytics/         # Reporting and analytics data
```

## 🔐 Multi-Tenant Architecture

### **Tenant Isolation Strategy**
- **Row Level Security (RLS)**: Database-level filtering by `school_id`
- **Schema Separation**: Logical separation of concerns
- **Subdomain Routing**: Each school gets unique subdomain
- **API Gateway**: Request-level tenant context injection

### **Access Patterns**
```sql
-- Every tenant-specific query includes school_id filtering
SELECT * FROM sis.students WHERE school_id = $1;
SELECT * FROM academic.subjects WHERE school_id = $1;
SELECT * FROM finance.invoices WHERE school_id = $1;
```

## 📊 Core Schema Definitions

### **Platform Schema** (`platform`)

#### **Schools Table**
```sql
CREATE TABLE platform.schools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'trial')),
    subscription_tier VARCHAR(20) DEFAULT 'basic' CHECK (subscription_tier IN ('basic', 'professional', 'enterprise')),
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    school_type VARCHAR(20) CHECK (school_type IN ('primary', 'secondary', 'combined', 'college')),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    configuration JSONB DEFAULT '{}',
    
    -- Indexes for performance
    INDEX idx_schools_subdomain (subdomain),
    INDEX idx_schools_status (status),
    INDEX idx_schools_tier (subscription_tier)
);
```

#### **Users Table**
```sql
CREATE TABLE platform.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES platform.schools(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'staff', 'student', 'parent', 'platform_admin')),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_metadata JSONB DEFAULT '{}',
    
    -- Indexes
    INDEX idx_users_school_id (school_id),
    INDEX idx_users_email (email),
    INDEX idx_users_role (role),
    
    -- RLS Policy
    CONSTRAINT users_school_isolation CHECK (school_id IS NOT NULL)
);
```

#### **School Configurations Table**
```sql
CREATE TABLE platform.school_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES platform.schools(id) ON DELETE CASCADE,
    currency VARCHAR(3) DEFAULT 'USD',
    timezone VARCHAR(50) DEFAULT 'Africa/Harare',
    language VARCHAR(5) DEFAULT 'en',
    enabled_modules JSONB DEFAULT '[]',
    primary_color VARCHAR(7) DEFAULT '#2563eb',
    theme VARCHAR(10) DEFAULT 'light',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint
    UNIQUE(school_id)
);
```

### **Student Information System Schema** (`sis`)

#### **Students Table**
```sql
CREATE TABLE sis.students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL,
    student_number VARCHAR(50) UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10) CHECK (gender IN ('male', 'female', 'other')),
    address JSONB,
    guardian_info JSONB,
    medical_info JSONB,
    enrollment_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'graduated', 'transferred')),
    class_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_students_school_id (school_id),
    INDEX idx_students_number (student_number),
    INDEX idx_students_status (status),
    INDEX idx_students_class (class_id)
);
```

#### **Enrollment Table**
```sql
CREATE TABLE sis.enrollment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL,
    student_id UUID NOT NULL,
    academic_year VARCHAR(10) NOT NULL,
    grade_level VARCHAR(20) NOT NULL,
    class_id UUID,
    enrollment_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Composite unique constraint
    UNIQUE(student_id, academic_year),
    
    -- Indexes
    INDEX idx_enrollment_school_id (school_id),
    INDEX idx_enrollment_student (student_id),
    INDEX idx_enrollment_year (academic_year)
);
```

#### **Attendance Records Table**
```sql
CREATE TABLE sis.attendance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL,
    student_id UUID NOT NULL,
    date DATE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('present', 'absent', 'late', 'excused')),
    notes TEXT,
    recorded_by UUID,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Composite unique constraint
    UNIQUE(student_id, date),
    
    -- Indexes
    INDEX idx_attendance_school_id (school_id),
    INDEX idx_attendance_student (student_id),
    INDEX idx_attendance_date (date),
    INDEX idx_attendance_status (status)
);
```

### **Academic Schema** (`academic`)

#### **Subjects Table**
```sql
CREATE TABLE academic.subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20),
    description TEXT,
    grade_levels JSONB DEFAULT '[]',
    is_core BOOLEAN DEFAULT false,
    credits INTEGER DEFAULT 1,
    department VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint per school
    UNIQUE(school_id, code),
    
    -- Indexes
    INDEX idx_subjects_school_id (school_id),
    INDEX idx_subjects_name (name),
    INDEX idx_subjects_department (department)
);
```

#### **Academic Years Table**
```sql
CREATE TABLE academic.academic_years (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL,
    year VARCHAR(10) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT false,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint
    UNIQUE(school_id, year),
    
    -- Indexes
    INDEX idx_academic_years_school_id (school_id),
    INDEX idx_academic_years_current (is_current)
);
```

#### **Assessments Table**
```sql
CREATE TABLE academic.assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) CHECK (type IN ('exam', 'test', 'assignment', 'project', 'quiz')),
    total_marks INTEGER NOT NULL,
    date_conducted DATE,
    grade_level VARCHAR(20),
    academic_year VARCHAR(10),
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_assessments_school_id (school_id),
    INDEX idx_assessments_subject (subject_id),
    INDEX idx_assessments_type (type),
    INDEX idx_assessments_date (date_conducted)
);
```

### **Finance Schema** (`finance`)

#### **Fee Structures Table**
```sql
CREATE TABLE finance.fee_structures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    grade_level VARCHAR(20),
    academic_year VARCHAR(10) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    payment_frequency VARCHAR(20) CHECK (payment_frequency IN ('once', 'monthly', 'termly', 'annually')),
    due_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_fee_structures_school_id (school_id),
    INDEX idx_fee_structures_grade (grade_level),
    INDEX idx_fee_structures_year (academic_year)
);
```

#### **Invoices Table**
```sql
CREATE TABLE finance.invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL,
    student_id UUID NOT NULL,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    due_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'overdue', 'cancelled')),
    items JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_invoices_school_id (school_id),
    INDEX idx_invoices_student (student_id),
    INDEX idx_invoices_number (invoice_number),
    INDEX idx_invoices_status (status),
    INDEX idx_invoices_due_date (due_date)
);
```

### **Analytics Schema** (`analytics`)

#### **Reports Table**
```sql
CREATE TABLE analytics.reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,
    generated_by UUID,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    
    -- Indexes
    INDEX idx_reports_school_id (school_id),
    INDEX idx_reports_type (type),
    INDEX idx_reports_generated_at (generated_at)
);
```

## 🔐 Row Level Security (RLS) Implementation

### **RLS Policies**
```sql
-- Enable RLS on all tenant-specific tables
ALTER TABLE sis.students ENABLE ROW LEVEL SECURITY;
ALTER TABLE academic.subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.invoices ENABLE ROW LEVEL SECURITY;

-- Create policies for school-based access
CREATE POLICY school_isolation_policy ON sis.students
    FOR ALL TO authenticated
    USING (school_id = current_setting('app.current_school_id')::UUID);

CREATE POLICY school_isolation_policy ON academic.subjects
    FOR ALL TO authenticated  
    USING (school_id = current_setting('app.current_school_id')::UUID);

CREATE POLICY school_isolation_policy ON finance.invoices
    FOR ALL TO authenticated
    USING (school_id = current_setting('app.current_school_id')::UUID);
```

## 📈 Performance Optimizations

### **Indexing Strategy**
- **Primary Keys**: UUID with gen_random_uuid()
- **Foreign Keys**: Indexed for join performance
- **School ID**: Indexed on all tenant tables
- **Composite Indexes**: For common query patterns

### **Query Patterns**
```sql
-- Optimized queries with proper indexing
SELECT * FROM sis.students 
WHERE school_id = $1 AND status = 'active'
ORDER BY last_name, first_name;

SELECT * FROM finance.invoices 
WHERE school_id = $1 AND status = 'pending' 
AND due_date <= CURRENT_DATE;
```

## 🔄 Migration Strategy

### **Version Control**
- **Sequential migrations**: Numbered migration files
- **Rollback support**: Down migrations for each change
- **Environment-specific**: Dev, staging, production migrations

### **Migration Files**
```
migrations/
├── 001_create_platform_schema.sql
├── 002_create_sis_schema.sql  
├── 003_create_academic_schema.sql
├── 004_create_finance_schema.sql
├── 005_create_analytics_schema.sql
└── 006_enable_rls_policies.sql
```

## 🎯 Data Validation Rules

### **Business Rules Enforced at DB Level**
- **Email uniqueness**: Across platform
- **Subdomain uniqueness**: Platform-wide
- **Student numbers**: Unique per school
- **Enrollment**: One active enrollment per student per year
- **Invoice numbers**: Globally unique

### **Check Constraints**
- **Status enums**: Predefined valid values
- **School types**: Limited to valid education levels  
- **Subscription tiers**: Basic, Professional, Enterprise
- **User roles**: Admin, Staff, Student, Parent

## 🚀 Scalability Considerations

### **Horizontal Scaling**
- **Sharding strategy**: By school_id for large deployments
- **Read replicas**: For analytics and reporting
- **Connection pooling**: For high concurrency

### **Data Archival**
- **Historical data**: Archive old academic years
- **Audit logs**: Separate audit schema
- **Retention policies**: Configurable data retention

---

**Schema Status**: ✅ **Production Ready**  
**Last Updated**: July 18, 2025  
**Version**: 1.0.0