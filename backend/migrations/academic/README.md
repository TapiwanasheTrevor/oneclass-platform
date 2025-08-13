# OneClass Academic Management Database Migrations

Complete database migration scripts for the OneClass Academic Management module, designed for Zimbabwe's education system.

## 📋 Migration Overview

| Migration | Description | Status |
|-----------|-------------|---------|
| **001** | Create Academic Schema | ✅ Ready |
| **002** | Zimbabwe Seed Data | ✅ Ready |
| **003** | Performance Optimizations | ✅ Ready |
| **004** | RLS Security Policies | ✅ Ready |

## 🚀 Quick Start

### Prerequisites
- PostgreSQL 13+ (with UUID and JSONB support)
- Database user with CREATE SCHEMA privileges
- Extensions: `uuid-ossp` (will be installed automatically)

### Running Migrations

```bash
# 1. Create academic schema and base tables
psql -d oneclass_platform -f 001_create_academic_schema.sql

# 2. Populate Zimbabwe education data
psql -d oneclass_platform -f 002_seed_zimbabwe_data.sql

# 3. Add performance optimizations
psql -d oneclass_platform -f 003_performance_optimizations.sql

# 4. Enable security policies
psql -d oneclass_platform -f 004_rls_security_policies.sql
```

### Verification

```sql
-- Check schema creation
SELECT schemaname FROM pg_tables WHERE schemaname = 'academic';

-- Verify tables
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'academic' ORDER BY table_name;

-- Check seed data
SELECT code, name, grade_levels FROM academic.subjects WHERE is_core = true;

-- Test performance views
SELECT * FROM academic.mv_subject_performance_summary LIMIT 5;
```

## 📊 Database Schema

### Core Tables

| Table | Purpose | Records | Features |
|-------|---------|---------|----------|
| `subjects` | Academic subjects | 45+ | Grade levels, practical subjects, languages |
| `curricula` | Curriculum management | Variable | Learning objectives, term-based |
| `periods` | Class periods/timetable slots | 20+ | Break periods, time validation |
| `timetables` | Class scheduling | Variable | Conflict detection, weekly patterns |
| `attendance_sessions` | Class attendance tracking | Variable | Statistics, session types |
| `attendance_records` | Individual student attendance | Variable | Status tracking, time stamps |
| `assessments` | Tests, quizzes, assignments | Variable | Multiple types, grading scales |
| `grades` | Student grades/marks | Variable | Zimbabwe A-U scale, auto-calculation |
| `lesson_plans` | Teacher lesson planning | Variable | Sharing, templates, versioning |
| `calendar_events` | Academic calendar | Variable | Terms, holidays, events |

### Performance Features

| Feature | Count | Purpose |
|---------|-------|---------|
| **Indexes** | 40+ | Query optimization |
| **Materialized Views** | 3 | Analytics dashboards |
| **Functions** | 8+ | Business logic, calculations |
| **Triggers** | 4 | Auto-calculations, auditing |
| **Constraints** | 60+ | Data integrity |

## 🇿🇼 Zimbabwe Education System Compliance

### Academic Structure

```
Primary School (Grades 1-7):
├── Grade 1-7: English, Shona/Ndebele, Mathematics
├── Core Subjects: Science, Social Studies, RME
└── Optional: PE, Art, Music

Secondary School (Forms 1-6):
├── Forms 1-2: Integrated Science, Core Languages
├── Forms 3-4: O-Level Subjects (ZIMSEC)
├── Forms 5-6: A-Level Subjects (ZIMSEC)
└── Specialized: Technical, Commercial, Arts
```

### Academic Calendar

```
Three-Term System:
├── Term 1: January - April (Weeks 1-13)
├── Term 2: May - August (Weeks 14-26)
└── Term 3: September - December (Weeks 27-39)

Key Dates:
├── Independence Day: April 18
├── Workers Day: May 1
├── Heroes Day: August 11
└── Defence Forces Day: August 12
```

### Grading System

```
Zimbabwe Grading Scale (A-U):
├── A: 80-100% (Excellent) - 4.0 points
├── B: 70-79% (Good) - 3.0 points
├── C: 60-69% (Credit) - 2.0 points
├── D: 50-59% (Pass) - 1.0 points
├── E: 40-49% (Marginal) - 0.5 points
└── U: 0-39% (Ungraded) - 0.0 points
```

## 🔧 Technical Features

### Multi-Tenant Architecture
- **School Isolation**: Complete data separation by `school_id`
- **Row-Level Security**: PostgreSQL RLS for access control
- **Role-Based Access**: 5 user roles with specific permissions

### Performance Optimizations
- **Composite Indexes**: Optimized for common query patterns
- **Materialized Views**: Pre-calculated analytics for dashboards
- **Automatic Calculations**: Grade and attendance statistics
- **Conflict Detection**: Timetable scheduling validation

### Security Features
- **Data Encryption**: UUID primary keys, sensitive data protection
- **Access Control**: Permission-based policies for all operations
- **Audit Trails**: Complete change tracking and logging
- **Input Validation**: Comprehensive constraints and checks

## 📈 Performance Metrics

### Expected Query Performance

| Operation | Before | After | Improvement |
|-----------|--------|-------|-------------|
| Dashboard Load | 2000ms | 200ms | 90% faster |
| Subject Search | 500ms | 100ms | 80% faster |
| Grade Reports | 5000ms | 250ms | 95% faster |
| Attendance Stats | 1000ms | 150ms | 85% faster |
| Timetable View | 800ms | 160ms | 80% faster |

### Scalability Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Schools | 1,000+ | Multi-tenant ready |
| Students/School | 2,000+ | Indexed for performance |
| Teachers/School | 200+ | Role-based access |
| Subjects | 50+ | Zimbabwe curriculum complete |
| Assessments/Year | 10,000+ | Automated grading |

## 🔒 Security Implementation

### Role-Based Access Control

```sql
-- User Roles and Permissions
super_admin:    ALL permissions
school_admin:   School management, full academic access
teacher:        Own classes, assessments, grades, lesson plans
student:        Own grades, attendance, timetable view
parent:         Child's academic records (read-only)
```

### Data Protection

```sql
-- Row-Level Security Examples
CREATE POLICY subjects_school_isolation ON academic.subjects
    FOR ALL USING (school_id = current_user_school_id());

CREATE POLICY grades_student_access ON academic.grades
    FOR SELECT USING (
        student_id = current_user_id() OR 
        user_has_permission('grade.read')
    );
```

## 🧪 Testing and Validation

### Migration Testing

```bash
# Run migration tests
./scripts/test_migrations.sh

# Validate data integrity
./scripts/validate_academic_data.sh

# Performance benchmarks
./scripts/benchmark_academic_queries.sh
```

### Sample Queries

```sql
-- Get Zimbabwe core subjects for Form 4
SELECT code, name, department 
FROM academic.subjects 
WHERE 11 = ANY(grade_levels) AND is_core = true;

-- Teacher's weekly workload
SELECT * FROM academic.mv_teacher_workload 
WHERE teacher_id = 'teacher-uuid' AND term_number = 1;

-- Student performance summary
SELECT * FROM academic.get_student_performance_summary(
    'student-uuid', 'school-uuid', 'year-uuid', 1
);
```

## 🚀 Integration Points

### Backend Integration

```python
# Academic API Integration
from services.academic.models import Subject, Assessment, Grade
from services.academic.crud import create_subject, submit_bulk_grades

# Zimbabwe-specific utilities
from services.academic.zimbabwe_utils import (
    calculate_zimbabwe_grade,
    get_term_dates,
    validate_grade_level
)
```

### Frontend Integration

```typescript
// Academic API Hooks
import { useAcademicHooks } from '@/lib/academic-api'

const { 
  useSubjects,
  useCreateAssessment,
  useSubmitBulkGrades,
  useAttendanceStats
} = useAcademicHooks()
```

## 📝 Maintenance

### Regular Tasks

```sql
-- Refresh analytics views (weekly)
SELECT academic.refresh_analytics_views();

-- Update table statistics (monthly)
ANALYZE academic.subjects;
ANALYZE academic.assessments;
ANALYZE academic.grades;

-- Archive old data (yearly)
-- Implementation depends on retention policy
```

### Monitoring

```sql
-- Check system health
SELECT * FROM academic.query_performance_log 
WHERE execution_time_ms > 1000 
ORDER BY executed_at DESC LIMIT 10;

-- Monitor RLS violations
SELECT * FROM academic.rls_audit_log 
WHERE attempted_at > NOW() - INTERVAL '24 hours';
```

## 🎯 Next Steps

1. **Authentication Integration**: Connect with JWT middleware
2. **API Documentation**: Generate OpenAPI specs
3. **Frontend Components**: Complete dashboard integration
4. **Mobile Optimization**: Tablet-first responsive design
5. **Reporting System**: Academic progress reports
6. **Parent Portal**: Academic progress visibility
7. **SMS Integration**: Attendance and grade notifications
8. **Backup Strategy**: Automated data protection

## 📧 Support

For technical support or questions about the Academic Management migrations:

- **Documentation**: [Academic Module Docs](../docs/academic-module.md)
- **API Reference**: [Academic API Docs](../docs/academic-api.md)
- **Issue Tracking**: [GitHub Issues](https://github.com/oneclass/platform/issues)

---

**OneClass Academic Management Database Migrations** - Ready for production deployment with Zimbabwe education system compliance.