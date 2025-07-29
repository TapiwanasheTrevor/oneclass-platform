# OneClass Platform API Documentation

## 🚀 API Overview

The OneClass Platform provides a comprehensive REST API built with **FastAPI** for managing multi-tenant school operations. The API follows modern design principles with automatic documentation, request/response validation, and async performance.

### **Base Information**
- **Base URL**: `http://localhost:8000` (development)
- **Production URL**: `https://api.oneclass.ac.zw`
- **API Version**: v1
- **Documentation**: `/docs` (Swagger UI)
- **OpenAPI Schema**: `/openapi.json`

### **Architecture Pattern**
- **API Gateway**: Centralized routing with tenant middleware
- **Modular Services**: Platform, SIS, Academic, Finance, Analytics
- **Tenant Isolation**: Request-level context injection
- **Async/Await**: High-performance async operations

## 🔐 Authentication & Authorization

### **Authentication Methods**
```http
# Bearer Token Authentication
Authorization: Bearer <jwt_token>

# Tenant Context Headers (injected by frontend middleware)
X-School-ID: <school_uuid>
X-School-Name: <school_name>
X-School-Subdomain: <subdomain>
X-School-Tier: <subscription_tier>
```

### **User Roles & Permissions**
| Role | Description | Permissions |
|------|-------------|-------------|
| `platform_admin` | Platform administrator | All platform operations |
| `admin` | School administrator | Full school management |
| `staff` | Teaching staff | Academic & student data |
| `student` | Student user | Own records access |
| `parent` | Parent/Guardian | Children's records access |

## 🏗️ API Gateway Endpoints

### **Health & Status**

#### **GET** `/health`
System health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "oneclass-platform",
  "version": "1.0.0",
  "timestamp": "2025-07-18T06:52:14.443246",
  "database": "connected"
}
```

#### **GET** `/api/v1/status`
API Gateway status with tenant context.

**Response:**
```json
{
  "status": "operational",
  "service": "oneclass-platform-api", 
  "version": "1.0.0",
  "timestamp": "2025-07-18T06:52:14.443246",
  "tenant": {
    "school_id": "uuid",
    "school_name": "School Name",
    "subscription_tier": "basic",
    "enabled_modules": ["sis", "finance"]
  },
  "user": {
    "user_id": "uuid",
    "role": "admin",
    "authenticated": true
  }
}
```

### **Tenant Information**

#### **GET** `/api/v1/tenant/info`
Get current tenant context information.

**Headers:**
```http
X-School-ID: <school_uuid>
X-School-Subdomain: <subdomain>
```

**Response:**
```json
{
  "school_id": "64a4f80e-37fa-4657-bc15-b7fc07639ea3",
  "school_name": "Test Primary School", 
  "subdomain": "test",
  "subscription_tier": "basic",
  "enabled_modules": ["student_information_system", "basic_reports"],
  "timestamp": "2025-07-18T06:52:14.443246"
}
```

#### **GET** `/api/v1/modules/available`
Get available modules for current tenant.

**Response:**
```json
{
  "school_id": "uuid",
  "subscription_tier": "basic",
  "modules": {
    "student_information_system": {
      "name": "Student Information System",
      "description": "Student enrollment, records, and management",
      "tier_required": "basic",
      "status": "enabled",
      "accessible": true,
      "routes": ["/api/v1/sis/*"]
    },
    "advanced_reporting": {
      "name": "Advanced Analytics & Reporting",
      "description": "Detailed insights and custom reports",
      "tier_required": "professional",
      "status": "disabled",
      "accessible": false,
      "upgrade_required": true
    }
  },
  "total_enabled": 2,
  "total_available": 7
}
```

## 🏫 Platform Management API

### **School Management**

#### **POST** `/api/v1/platform/schools`
Create a new school with admin user and configuration.

**Request Body:**
```json
{
  "name": "Sunrise Primary School",
  "type": "primary",
  "contact": {
    "email": "admin@sunrise.co.zw",
    "phone": "+263771234567", 
    "website": "www.sunrise.co.zw"
  },
  "address": {
    "line1": "123 Main Street",
    "line2": "Optional line 2",
    "city": "Harare",
    "province": "harare",
    "postal_code": "12345"
  },
  "established_year": 2000,
  "student_count_range": "201-500",
  "subscription_tier": "basic",
  "configuration": {
    "academic_year": "2024",
    "term_structure": "3-terms",
    "grade_structure": "primary",
    "timezone": "Africa/Harare",
    "language": "en",
    "currency": "USD"
  },
  "admin_user": {
    "first_name": "John",
    "last_name": "Doe", 
    "email": "john.doe@sunrise.co.zw",
    "phone": "+263771234567"
  }
}
```

**Response:**
```json
{
  "id": "64a4f80e-37fa-4657-bc15-b7fc07639ea3",
  "name": "Sunrise Primary School",
  "subdomain": "sunrise",
  "type": "primary",
  "status": "active",
  "subscription_tier": "basic", 
  "is_active": true,
  "created_at": "2025-07-18T06:52:42.450760",
  "admin_user": {
    "id": "136ff7c3-09a9-45ad-b029-2ed0f6e4aced",
    "email": "john.doe@sunrise.co.zw",
    "name": "John Doe"
  }
}
```

**Validation Rules:**
- `name`: Minimum 3 characters
- `type`: Must be one of: `primary`, `secondary`, `combined`, `college`
- `subscription_tier`: Must be one of: `basic`, `professional`, `enterprise`
- `email`: Valid email format
- `subdomain`: Auto-generated, unique across platform

#### **GET** `/api/v1/platform/schools/by-subdomain/{subdomain}`
Get school information by subdomain (public endpoint).

**Parameters:**
- `subdomain` (string): School subdomain

**Response:**
```json
{
  "id": "64a4f80e-37fa-4657-bc15-b7fc07639ea3",
  "name": "Test Primary School",
  "subdomain": "test",
  "is_active": true,
  "subscription_tier": "basic",
  "custom_domain": null,
  "enabled_modules": ["student_information_system", "basic_reports"],
  "branding": {
    "primary_color": "#2563eb",
    "theme": "light"
  }
}
```

#### **GET** `/api/v1/platform/schools/{school_id}`
Get specific school information (requires admin access).

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "id": "64a4f80e-37fa-4657-bc15-b7fc07639ea3",
  "name": "Test Primary School",
  "subdomain": "test",
  "status": "active",
  "subscription_tier": "basic",
  "email": "admin@test.co.zw",
  "phone": "+263771234567",
  "school_type": "primary",
  "is_active": true,
  "created_at": "2025-07-18T06:52:42.450760",
  "configuration": {
    "contact": {...},
    "address": {...},
    "academic": {...},
    "branding": {...}
  }
}
```

#### **GET** `/api/v1/platform/schools`
List all schools (platform admin only).

**Headers:**
```http
Authorization: Bearer <jwt_token>
X-User-Role: platform_admin
```

**Response:**
```json
[
  {
    "id": "64a4f80e-37fa-4657-bc15-b7fc07639ea3",
    "name": "Test Primary School",
    "subdomain": "test",
    "status": "active",
    "created_at": "2025-07-18T06:52:42.450760"
  },
  {
    "id": "7fb489d8-df31-4ba4-98c3-00082203ca8d", 
    "name": "Sunrise Academy",
    "subdomain": "sunrise2",
    "status": "active",
    "created_at": "2025-07-18T06:53:49.779777"
  }
]
```

## 📊 Analytics & Reporting API

### **Dashboard Analytics**

#### **GET** `/api/v1/analytics/dashboard`
Get comprehensive dashboard analytics for the school.

**Headers:**
```http
X-School-ID: <school_uuid>
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "overview": {
    "total_students": 245,
    "total_staff": 18,
    "total_classes": 12,
    "average_attendance": 94.5
  },
  "recent_trends": {
    "student_growth": 12,
    "attendance_trend": "improving",
    "academic_performance": "stable"
  },
  "financial_summary": {
    "monthly_revenue": 15420.50,
    "outstanding_fees": 3240.75,
    "collection_rate": 89.2
  },
  "quick_stats": {
    "present_today": 231,
    "absent_today": 14,
    "new_enrollments_this_month": 5,
    "upcoming_events": 3
  }
}
```

### **Student Analytics**

#### **GET** `/api/v1/analytics/students`
Get student-related analytics and insights.

**Query Parameters:**
- `date_range` (optional): `7d`, `30d`, `90d`, `1y`
- `grade_level` (optional): Filter by grade
- `class_id` (optional): Filter by class

**Response:**
```json
{
  "enrollment_stats": {
    "total_enrolled": 245,
    "by_grade": {
      "Grade 1": 45,
      "Grade 2": 42,
      "Grade 3": 38
    },
    "by_gender": {
      "male": 128,
      "female": 117
    }
  },
  "attendance_analytics": {
    "overall_rate": 94.5,
    "trend": "improving",
    "by_grade": {
      "Grade 1": 96.2,
      "Grade 2": 94.8,
      "Grade 3": 92.1
    }
  },
  "performance_insights": {
    "average_scores": {
      "Mathematics": 78.5,
      "English": 82.1,
      "Science": 76.8
    },
    "improvement_areas": ["Mathematics", "Science"],
    "top_performers": 15
  }
}
```

### **Financial Analytics**

#### **GET** `/api/v1/analytics/finance`
Get financial analytics and reporting data.

**Response:**
```json
{
  "revenue_analytics": {
    "total_revenue": 45620.75,
    "monthly_breakdown": {
      "January": 15420.50,
      "February": 14850.25,
      "March": 15350.00
    },
    "by_fee_type": {
      "tuition": 38500.00,
      "activities": 4120.75,
      "transport": 3000.00
    }
  },
  "collection_metrics": {
    "collection_rate": 89.2,
    "outstanding_amount": 3240.75,
    "overdue_invoices": 12,
    "payment_methods": {
      "bank_transfer": 65.4,
      "mobile_money": 28.1,
      "cash": 6.5
    }
  },
  "predictions": {
    "next_month_revenue": 15800.00,
    "collection_forecast": 91.5,
    "risk_students": 8
  }
}
```

## 🔍 Error Handling

### **Standard Error Response Format**
```json
{
  "error": "error_code",
  "message": "Human readable error message",
  "details": "Additional error details (development only)",
  "request_id": "req_12345",
  "timestamp": "2025-07-18T06:52:14.443246"
}
```

### **HTTP Status Codes**
| Code | Meaning | Usage |
|------|---------|--------|
| `200` | OK | Successful request |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid request data |
| `401` | Unauthorized | Authentication required |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource not found |
| `422` | Validation Error | Request validation failed |
| `500` | Internal Error | Server error |

### **Common Error Examples**

#### **Validation Error (422)**
```json
{
  "error": "validation_error",
  "message": "Request validation failed",
  "details": {
    "field_errors": [
      {
        "field": "email",
        "message": "Invalid email format"
      },
      {
        "field": "subscription_tier", 
        "message": "Must be one of: basic, professional, enterprise"
      }
    ]
  }
}
```

#### **Tenant Not Found (404)**
```json
{
  "error": "tenant_not_found",
  "message": "School not found for subdomain",
  "details": "Subdomain 'invalid-school' does not exist"
}
```

#### **Module Access Denied (403)**
```json
{
  "error": "module_not_available",
  "message": "The requested module is not available in your subscription",
  "subscription_tier": "basic",
  "required_tier": "professional"
}
```

## 🚀 Rate Limiting

### **Rate Limits by Endpoint Type**
| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Authentication | 5 requests | 1 minute |
| School Creation | 10 requests | 1 hour |
| General API | 1000 requests | 1 hour |
| Analytics | 100 requests | 1 minute |

### **Rate Limit Headers**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 998
X-RateLimit-Reset: 1642694400
```

## 📈 API Versioning

### **Version Strategy**
- **URL Versioning**: `/api/v1/`
- **Backward Compatibility**: Previous versions supported
- **Deprecation Notice**: 6 months advance notice
- **Migration Guides**: Provided for major version changes

### **Version History**
| Version | Release Date | Status | Notes |
|---------|--------------|--------|-------|
| v1.0.0 | 2025-07-18 | Current | Initial release with multi-tenant support |

## 🔧 Development Tools

### **API Testing**
```bash
# Test school creation
curl -X POST http://localhost:8000/api/v1/platform/schools \
  -H "Content-Type: application/json" \
  -d @school_creation_payload.json

# Test tenant lookup  
curl http://localhost:8000/api/v1/platform/schools/by-subdomain/test

# Test analytics endpoint
curl http://localhost:8000/api/v1/analytics/dashboard \
  -H "X-School-ID: 64a4f80e-37fa-4657-bc15-b7fc07639ea3"
```

### **SDK & Libraries**
- **Python SDK**: Coming soon
- **JavaScript SDK**: Coming soon
- **Postman Collection**: Available in `/docs/postman/`

---

**API Status**: ✅ **Production Ready**  
**Documentation Version**: 1.0.0  
**Last Updated**: July 18, 2025