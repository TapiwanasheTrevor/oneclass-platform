"""
Academic Management Module - API Documentation
Comprehensive OpenAPI/Swagger documentation for Academic Management APIs
"""

from typing import Dict, Any, List

# OpenAPI tags for organizing endpoints
ACADEMIC_TAGS = [
    {
        "name": "subjects",
        "description": "Subject management operations for curriculum and course definitions",
        "externalDocs": {
            "description": "Zimbabwe Curriculum Framework",
            "url": "https://mopse.gov.zw/curriculum"
        }
    },
    {
        "name": "assessments", 
        "description": "Assessment and examination management for student evaluation",
        "externalDocs": {
            "description": "ZIMSEC Assessment Guidelines",
            "url": "https://zimsec.co.zw/assessment-guidelines"
        }
    },
    {
        "name": "grades",
        "description": "Grade calculation and management using Zimbabwe A-U grading scale",
        "externalDocs": {
            "description": "Zimbabwe Grading System",
            "url": "https://mopse.gov.zw/grading-system"
        }
    },
    {
        "name": "attendance",
        "description": "Student attendance tracking and reporting for academic compliance",
        "externalDocs": {
            "description": "Zimbabwe School Attendance Policy",
            "url": "https://mopse.gov.zw/attendance-policy"
        }
    },
    {
        "name": "timetables",
        "description": "Academic timetable and scheduling management",
        "externalDocs": {
            "description": "Zimbabwe School Calendar",
            "url": "https://mopse.gov.zw/school-calendar"
        }
    },
    {
        "name": "analytics",
        "description": "Academic performance analytics and reporting dashboards",
        "externalDocs": {
            "description": "Education Analytics Guide",
            "url": "https://docs.oneclass.ac.zw/analytics"
        }
    },
    {
        "name": "zimbabwe",
        "description": "Zimbabwe education system specific endpoints and utilities",
        "externalDocs": {
            "description": "Zimbabwe Education Act",
            "url": "https://mopse.gov.zw/education-act"
        }
    }
]

# Enhanced schema examples for documentation
SCHEMA_EXAMPLES = {
    "Subject": {
        "summary": "Mathematics Subject Example",
        "description": "A complete subject definition for mathematics in the Zimbabwe curriculum",
        "value": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "code": "MATH",
            "name": "Mathematics",
            "description": "Core mathematics curriculum covering algebra, geometry, statistics and calculus",
            "department": "Sciences",
            "grade_level": 10,
            "is_core": True,
            "credit_hours": 5,
            "prerequisites": ["Basic Mathematics"],
            "curriculum_framework": "Cambridge IGCSE",
            "assessment_methods": ["Continuous Assessment", "End of Term Exam"],
            "school_id": "123e4567-e89b-12d3-a456-426614174000",
            "created_at": "2024-08-13T10:00:00Z",
            "updated_at": "2024-08-13T10:00:00Z",
            "created_by": "teacher-001",
            "is_active": True
        }
    },
    "Assessment": {
        "summary": "Term 1 Mathematics Test",
        "description": "Mid-term assessment for Form 4 Mathematics",
        "value": {
            "id": "660e8400-e29b-41d4-a716-446655440001",
            "name": "Term 1 Mathematics Test",
            "description": "Comprehensive test covering algebra and geometry topics",
            "subject_id": "550e8400-e29b-41d4-a716-446655440000",
            "class_id": "770e8400-e29b-41d4-a716-446655440002",
            "teacher_id": "880e8400-e29b-41d4-a716-446655440003",
            "assessment_type": "test",
            "term_number": 1,
            "total_marks": 100,
            "pass_mark": 50,
            "assessment_date": "2024-03-15",
            "due_date": "2024-03-20",
            "instructions": "Answer all questions. Show all working.",
            "grading_scale": "zimbabwe_au",
            "school_id": "123e4567-e89b-12d3-a456-426614174000",
            "created_at": "2024-08-13T10:00:00Z",
            "is_published": True
        }
    },
    "Grade": {
        "summary": "Student Grade Record",
        "description": "Individual student grade for an assessment",
        "value": {
            "id": "990e8400-e29b-41d4-a716-446655440004",
            "assessment_id": "660e8400-e29b-41d4-a716-446655440001",
            "student_id": "aaa0e8400-e29b-41d4-a716-446655440005",
            "marks_obtained": 85,
            "total_marks": 100,
            "percentage": 85.0,
            "letter_grade": "A",
            "grade_points": 4.0,
            "comments": "Excellent work. Strong understanding of algebraic concepts.",
            "graded_by": "teacher-001",
            "graded_at": "2024-03-16T14:30:00Z",
            "is_published": True,
            "school_id": "123e4567-e89b-12d3-a456-426614174000"
        }
    },
    "AttendanceSession": {
        "summary": "Mathematics Class Session",
        "description": "Attendance session for a mathematics class",
        "value": {
            "id": "bbb0e8400-e29b-41d4-a716-446655440006",
            "subject_id": "550e8400-e29b-41d4-a716-446655440000",
            "class_id": "770e8400-e29b-41d4-a716-446655440002",
            "teacher_id": "880e8400-e29b-41d4-a716-446655440003",
            "session_date": "2024-08-13",
            "period_number": 3,
            "lesson_topic": "Quadratic Equations",
            "session_type": "regular",
            "total_students": 30,
            "students_present": 28,
            "students_absent": 2,
            "attendance_marked_at": "2024-08-13T09:45:00Z",
            "school_id": "123e4567-e89b-12d3-a456-426614174000"
        }
    },
    "ZimbabweGradeLevels": {
        "summary": "Zimbabwe Education Grade Levels",
        "description": "Complete grade level structure for Zimbabwe education system",
        "value": {
            "primary": [
                {"value": 1, "label": "Grade 1", "description": "Primary - Age 6-7", "curriculum": "Primary Curriculum"},
                {"value": 2, "label": "Grade 2", "description": "Primary - Age 7-8", "curriculum": "Primary Curriculum"},
                {"value": 3, "label": "Grade 3", "description": "Primary - Age 8-9", "curriculum": "Primary Curriculum"},
                {"value": 4, "label": "Grade 4", "description": "Primary - Age 9-10", "curriculum": "Primary Curriculum"},
                {"value": 5, "label": "Grade 5", "description": "Primary - Age 10-11", "curriculum": "Primary Curriculum"},
                {"value": 6, "label": "Grade 6", "description": "Primary - Age 11-12", "curriculum": "Primary Curriculum"},
                {"value": 7, "label": "Grade 7", "description": "Primary - Age 12-13", "curriculum": "Primary Curriculum"}
            ],
            "secondary": [
                {"value": 8, "label": "Form 1", "description": "Secondary - Age 13-14", "curriculum": "Zimbabwe Junior Certificate"},
                {"value": 9, "label": "Form 2", "description": "Secondary - Age 14-15", "curriculum": "Zimbabwe Junior Certificate"},
                {"value": 10, "label": "Form 3", "description": "O-Level - Age 15-16", "curriculum": "ZIMSEC O-Level"},
                {"value": 11, "label": "Form 4", "description": "O-Level - Age 16-17", "curriculum": "ZIMSEC O-Level"},
                {"value": 12, "label": "Form 5", "description": "A-Level - Age 17-18", "curriculum": "ZIMSEC A-Level"},
                {"value": 13, "label": "Form 6", "description": "A-Level - Age 18-19", "curriculum": "ZIMSEC A-Level"}
            ]
        }
    },
    "ZimbabweTerms": {
        "summary": "Zimbabwe Academic Terms",
        "description": "Three-term academic year structure used in Zimbabwe schools",
        "value": {
            "academic_year": "2024",
            "terms": [
                {
                    "number": 1,
                    "name": "Term 1",
                    "description": "January - April",
                    "start_date": "2024-01-15",
                    "end_date": "2024-04-18",
                    "total_weeks": 13,
                    "holidays": ["Easter Holiday"]
                },
                {
                    "number": 2, 
                    "name": "Term 2",
                    "description": "May - August",
                    "start_date": "2024-05-06",
                    "end_date": "2024-08-22",
                    "total_weeks": 15,
                    "holidays": ["Independence Day", "Heroes Day"]
                },
                {
                    "number": 3,
                    "name": "Term 3", 
                    "description": "September - December",
                    "start_date": "2024-09-09",
                    "end_date": "2024-12-05",
                    "total_weeks": 12,
                    "holidays": ["Unity Day", "Christmas Holiday"]
                }
            ]
        }
    },
    "ErrorResponse": {
        "summary": "Standard Error Response",
        "description": "Standardized error response format for all Academic Management API errors",
        "value": {
            "error": "SUBJECT_NOT_FOUND",
            "message": "Subject not found: PHYSICS",
            "details": {
                "subject_id": None,
                "subject_code": "PHYSICS",
                "suggestion": "Check if the subject exists and you have permission to access it"
            },
            "module": "academic_management",
            "request_id": "req-12345678",
            "timestamp": "2024-08-13T10:15:30Z"
        }
    }
}

# Response examples for different scenarios
RESPONSE_EXAMPLES = {
    "subjects_list_success": {
        "summary": "Successful subjects list",
        "description": "Example of successful paginated subjects response",
        "value": {
            "items": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "code": "MATH",
                    "name": "Mathematics",
                    "department": "Sciences",
                    "grade_level": 10,
                    "is_core": True
                }
            ],
            "total_count": 15,
            "page": 1,
            "page_size": 20,
            "total_pages": 1,
            "has_next": False,
            "has_prev": False
        }
    },
    "assessment_created": {
        "summary": "Assessment created successfully",
        "description": "Response when assessment is successfully created",
        "value": {
            "id": "660e8400-e29b-41d4-a716-446655440001",
            "name": "Term 1 Mathematics Test",
            "subject_id": "550e8400-e29b-41d4-a716-446655440000",
            "assessment_type": "test",
            "term_number": 1,
            "total_marks": 100,
            "created_at": "2024-08-13T10:00:00Z"
        }
    },
    "grade_submission_success": {
        "summary": "Bulk grades submitted",
        "description": "Response when bulk grades are successfully submitted",
        "value": {
            "message": "Grades submitted successfully",
            "grades_submitted": 25,
            "grades_updated": 3,
            "processing_time": "0.245s",
            "timestamp": "2024-08-13T10:00:00Z"
        }
    },
    "attendance_marked": {
        "summary": "Attendance marked successfully", 
        "description": "Response when bulk attendance is successfully marked",
        "value": {
            "message": "Attendance marked successfully",
            "records_processed": 30,
            "students_present": 28,
            "students_absent": 2,
            "session_id": "bbb0e8400-e29b-41d4-a716-446655440006"
        }
    }
}

# Error response examples
ERROR_EXAMPLES = {
    "validation_error": {
        "summary": "Validation Error",
        "description": "Invalid input data provided",
        "value": {
            "error": "ACADEMIC_VALIDATION_ERROR",
            "message": "Invalid grade level: 15. Must be between 1-13 for Zimbabwe education system.",
            "details": {
                "field": "grade_level",
                "invalid_value": "15",
                "valid_range": "1-13",
                "zimbabwe_grades": "Grades 1-7 (Primary), Forms 1-6 (Secondary)"
            },
            "module": "academic_management"
        }
    },
    "permission_error": {
        "summary": "Permission Denied",
        "description": "Insufficient permissions to perform action",
        "value": {
            "error": "ACADEMIC_PERMISSION_ERROR",
            "message": "Insufficient permissions to create subjects. Required: academic.subject.create",
            "details": {
                "required_permission": "academic.subject.create",
                "user_role": "student"
            },
            "module": "academic_management"
        }
    },
    "resource_not_found": {
        "summary": "Resource Not Found",
        "description": "Requested resource does not exist",
        "value": {
            "error": "SUBJECT_NOT_FOUND", 
            "message": "Subject not found: PHYSICS",
            "details": {
                "subject_id": None,
                "subject_code": "PHYSICS",
                "suggestion": "Check if the subject exists and you have permission to access it"
            },
            "module": "academic_management"
        }
    },
    "business_logic_error": {
        "summary": "Business Logic Violation",
        "description": "Operation violates business rules",
        "value": {
            "error": "DUPLICATE_SUBJECT_CODE",
            "message": "Subject with code 'MATH' already exists in Harare Primary School",
            "details": {
                "subject_code": "MATH",
                "school": "Harare Primary School",
                "suggestion": "Use a different subject code or update the existing subject"
            },
            "module": "academic_management"
        }
    }
}

# OpenAPI documentation metadata
OPENAPI_METADATA = {
    "title": "OneClass Academic Management API",
    "description": """
## OneClass Academic Management System API

**Complete Academic Management for Zimbabwe Schools**

This API provides comprehensive academic management functionality specifically designed for Zimbabwe's education system, including:

### 🎓 Core Features
- **Subject Management**: Create and manage curriculum subjects with Zimbabwe framework compliance
- **Assessment Management**: Handle continuous assessments, tests, and examinations
- **Grade Management**: Zimbabwe A-U grading scale with automatic calculations
- **Attendance Tracking**: Student attendance with statistical reporting
- **Timetable Management**: Academic scheduling and period management
- **Analytics & Reporting**: Performance dashboards and academic insights

### 🇿🇼 Zimbabwe Education System Compliance
- **Grade Levels**: Grades 1-7 (Primary), Forms 1-6 (Secondary)
- **Academic Calendar**: 3-term system (Term 1: Jan-Apr, Term 2: May-Aug, Term 3: Sep-Dec)
- **Grading Scale**: Zimbabwe A-U scale (A: 80-100%, B: 70-79%, C: 60-69%, D: 50-59%, E: 40-49%, U: 0-39%)
- **Curriculum Frameworks**: Support for Zimbabwe Junior Certificate, ZIMSEC O-Level, ZIMSEC A-Level
- **Assessment Types**: Continuous assessment, end-of-term exams, practical assessments

### 🔐 Security & Authentication
- **Role-Based Access Control**: Different permissions for administrators, teachers, students, and parents
- **Multi-Tenant Architecture**: Secure school-level data isolation
- **Teacher Ownership**: Teachers can only modify their own assessments and grades
- **Student Privacy**: Students can only view their own academic records

### ⚡ Performance & Reliability
- **Bulk Operations**: Efficient batch processing for grades and attendance
- **Caching**: Response caching for improved performance
- **Error Handling**: Comprehensive error handling with detailed error responses
- **Audit Logging**: Full audit trail for all academic operations

### 📊 Data Management
- **Pagination**: All list endpoints support pagination for efficient data loading
- **Filtering**: Advanced filtering options for subjects, assessments, and grades
- **Search**: Full-text search capabilities across academic entities
- **Export**: Data export functionality for reporting and analytics

### 🚀 Getting Started
1. **Authentication**: Obtain an access token through the auth endpoints
2. **School Context**: All requests require valid school context (via subdomain or JWT)
3. **Permissions**: Ensure your user role has appropriate permissions for desired operations
4. **API Usage**: Use the documented endpoints with proper request/response formats

For detailed implementation guides, see our [Developer Documentation](https://docs.oneclass.ac.zw/).
    """,
    "version": "1.0.0",
    "contact": {
        "name": "OneClass Support",
        "email": "support@oneclass.ac.zw",
        "url": "https://oneclass.ac.zw/support"
    },
    "license": {
        "name": "OneClass Platform License",
        "url": "https://oneclass.ac.zw/license"
    },
    "termsOfService": "https://oneclass.ac.zw/terms",
    "servers": [
        {
            "url": "https://api.oneclass.ac.zw",
            "description": "Production server"
        },
        {
            "url": "https://staging-api.oneclass.ac.zw", 
            "description": "Staging server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        }
    ]
}

# Security schemes for OpenAPI
SECURITY_SCHEMES = {
    "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT Bearer token authentication. Include the token in the Authorization header as 'Bearer {token}'"
    },
    "SchoolContext": {
        "type": "apiKey", 
        "in": "header",
        "name": "X-School-ID",
        "description": "School context identifier. Required for multi-tenant operations."
    }
}

# Common parameter definitions
COMMON_PARAMETERS = {
    "page": {
        "name": "page",
        "in": "query",
        "description": "Page number for pagination (1-based)",
        "required": False,
        "schema": {
            "type": "integer",
            "minimum": 1,
            "default": 1,
            "example": 1
        }
    },
    "page_size": {
        "name": "page_size", 
        "in": "query",
        "description": "Number of items per page (max 100)",
        "required": False,
        "schema": {
            "type": "integer",
            "minimum": 1,
            "maximum": 100,
            "default": 20,
            "example": 20
        }
    },
    "grade_level": {
        "name": "grade_level",
        "in": "query", 
        "description": "Filter by grade level (1-13 for Zimbabwe system)",
        "required": False,
        "schema": {
            "type": "integer",
            "minimum": 1,
            "maximum": 13,
            "example": 10
        }
    },
    "term_number": {
        "name": "term_number",
        "in": "query",
        "description": "Filter by academic term (1, 2, or 3)",
        "required": False,
        "schema": {
            "type": "integer",
            "enum": [1, 2, 3],
            "example": 1
        }
    },
    "search": {
        "name": "search",
        "in": "query",
        "description": "Search query for filtering results",
        "required": False,
        "schema": {
            "type": "string",
            "minLength": 2,
            "maxLength": 100,
            "example": "mathematics"
        }
    }
}

def get_enhanced_openapi_metadata() -> Dict[str, Any]:
    """Get enhanced OpenAPI metadata for Academic Management API"""
    return {
        **OPENAPI_METADATA,
        "tags": ACADEMIC_TAGS,
        "components": {
            "securitySchemes": SECURITY_SCHEMES,
            "parameters": COMMON_PARAMETERS,
            "examples": {
                **SCHEMA_EXAMPLES,
                **RESPONSE_EXAMPLES,
                **ERROR_EXAMPLES
            }
        }
    }