# OneClass Platform API Documentation

## 🌐 API Overview

The OneClass Platform provides a comprehensive RESTful API that enables developers to integrate with the school management system. The API is designed with multi-tenancy in mind, ensuring complete data isolation between schools while maintaining a consistent interface.

## 🚀 Quick Start

### Base URL
```
Production: https://api.oneclass.ac.zw
Staging: https://staging-api.oneclass.ac.zw
Development: http://localhost:8000
```

### Authentication
All API requests require authentication using Bearer tokens:
```http
Authorization: Bearer <your-access-token>
```

### Content Type
All requests and responses use JSON:
```http
Content-Type: application/json
```

## 📋 API Endpoints Overview

### Authentication Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | User authentication |
| POST | `/api/v1/auth/logout` | User logout |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Get current user profile |

### School Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/schools` | List all schools (admin only) |
| POST | `/api/v1/schools` | Create new school |
| GET | `/api/v1/schools/{id}` | Get school details |
| PUT | `/api/v1/schools/{id}` | Update school information |
| DELETE | `/api/v1/schools/{id}` | Delete school |

### User Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users` | List users in school |
| POST | `/api/v1/users` | Create new user |
| GET | `/api/v1/users/{id}` | Get user details |
| PUT | `/api/v1/users/{id}` | Update user information |
| DELETE | `/api/v1/users/{id}` | Delete user |
| POST | `/api/v1/users/{id}/invite` | Send user invitation |

### Student Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/students` | List students in school |
| POST | `/api/v1/students` | Create new student |
| GET | `/api/v1/students/{id}` | Get student details |
| PUT | `/api/v1/students/{id}` | Update student information |
| DELETE | `/api/v1/students/{id}` | Delete student |
| POST | `/api/v1/students/bulk` | Bulk create students |

### Analytics & Reporting
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/dashboard` | Get dashboard metrics |
| GET | `/api/v1/analytics/students` | Student analytics |
| GET | `/api/v1/analytics/academic` | Academic performance |
| GET | `/api/v1/analytics/financial` | Financial metrics |
| GET | `/api/v1/analytics/reports` | Generate reports |

### Monitoring & Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/monitoring/health` | System health check |
| GET | `/api/v1/monitoring/metrics` | System metrics |
| GET | `/api/v1/monitoring/status` | Service status |

## 🔐 Authentication

### Login Request
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin@harare-primary.oneclass.ac.zw",
  "password": "secure_password"
}
```

### Login Response
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "admin@harare-primary.oneclass.ac.zw",
      "role": "school_admin",
      "school_id": "456e7890-e89b-12d3-a456-426614174001"
    }
  }
}
```

### Mobile Authentication
```http
POST /api/v1/auth/mobile/login
Content-Type: application/json

{
  "username": "teacher@bulawayo-high.oneclass.ac.zw",
  "password": "secure_password",
  "device_id": "device_123456",
  "device_name": "iPhone 14 Pro",
  "device_type": "ios"
}
```

## 🏫 School Management API

### Create School
```http
POST /api/v1/schools
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "name": "Harare Primary School",
  "subdomain": "harare-primary",
  "type": "Primary",
  "address": "123 School Road, Harare",
  "phone": "+263242123456",
  "email": "info@harare-primary.oneclass.ac.zw",
  "principal": "Mrs. Grace Moyo",
  "established": "1995"
}
```

### Response
```json
{
  "success": true,
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Harare Primary School",
    "subdomain": "harare-primary",
    "domain": "harare-primary.oneclass.ac.zw",
    "type": "Primary",
    "address": "123 School Road, Harare",
    "phone": "+263242123456",
    "email": "info@harare-primary.oneclass.ac.zw",
    "principal": "Mrs. Grace Moyo",
    "established": "1995",
    "is_active": true,
    "created_at": "2024-01-18T10:30:00Z",
    "updated_at": "2024-01-18T10:30:00Z"
  }
}
```

## 👥 User Management API

### Create User
```http
POST /api/v1/users
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "email": "teacher@harare-primary.oneclass.ac.zw",
  "username": "sarah.chikwanha",
  "first_name": "Sarah",
  "last_name": "Chikwanha",
  "role": "teacher",
  "department": "Mathematics",
  "phone": "+263777123456",
  "send_invitation": true
}
```

### Response
```json
{
  "success": true,
  "data": {
    "id": "456e7890-e89b-12d3-a456-426614174001",
    "email": "teacher@harare-primary.oneclass.ac.zw",
    "username": "sarah.chikwanha",
    "first_name": "Sarah",
    "last_name": "Chikwanha",
    "role": "teacher",
    "department": "Mathematics",
    "phone": "+263777123456",
    "is_active": true,
    "last_login": null,
    "created_at": "2024-01-18T10:30:00Z",
    "updated_at": "2024-01-18T10:30:00Z"
  }
}
```

### List Users with Filtering
```http
GET /api/v1/users?role=teacher&department=Mathematics&page=1&limit=10
Authorization: Bearer <admin-token>
```

### Response
```json
{
  "success": true,
  "data": [
    {
      "id": "456e7890-e89b-12d3-a456-426614174001",
      "email": "teacher@harare-primary.oneclass.ac.zw",
      "username": "sarah.chikwanha",
      "first_name": "Sarah",
      "last_name": "Chikwanha",
      "role": "teacher",
      "department": "Mathematics",
      "is_active": true,
      "last_login": "2024-01-18T09:15:00Z"
    }
  ],
  "meta": {
    "total": 1,
    "page": 1,
    "per_page": 10,
    "total_pages": 1
  }
}
```

## 🎓 Student Management API

### Create Student
```http
POST /api/v1/students
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "student_id": "STU2024001",
  "first_name": "Tendai",
  "last_name": "Mukamuri",
  "email": "tendai.mukamuri@harare-primary.oneclass.ac.zw",
  "date_of_birth": "2010-05-15",
  "grade": "Grade 7",
  "class": "7A",
  "parent_contact": "+263777123456",
  "address": "456 Student Road, Harare",
  "emergency_contact": "+263777654321",
  "medical_info": "No known allergies"
}
```

### Response
```json
{
  "success": true,
  "data": {
    "id": "789e0123-e89b-12d3-a456-426614174002",
    "student_id": "STU2024001",
    "first_name": "Tendai",
    "last_name": "Mukamuri",
    "email": "tendai.mukamuri@harare-primary.oneclass.ac.zw",
    "date_of_birth": "2010-05-15",
    "grade": "Grade 7",
    "class": "7A",
    "parent_contact": "+263777123456",
    "address": "456 Student Road, Harare",
    "emergency_contact": "+263777654321",
    "enrollment_date": "2024-01-18",
    "is_active": true,
    "created_at": "2024-01-18T10:30:00Z",
    "updated_at": "2024-01-18T10:30:00Z"
  }
}
```

### Bulk Create Students
```http
POST /api/v1/students/bulk
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "students": [
    {
      "student_id": "STU2024002",
      "first_name": "Chipo",
      "last_name": "Nyamukapa",
      "email": "chipo.nyamukapa@harare-primary.oneclass.ac.zw",
      "date_of_birth": "2010-03-20",
      "grade": "Grade 7",
      "class": "7A"
    },
    {
      "student_id": "STU2024003",
      "first_name": "Tafadzwa",
      "last_name": "Mwale",
      "email": "tafadzwa.mwale@harare-primary.oneclass.ac.zw",
      "date_of_birth": "2010-07-10",
      "grade": "Grade 7",
      "class": "7B"
    }
  ]
}
```

## 📊 Analytics API

### Dashboard Metrics
```http
GET /api/v1/analytics/dashboard
Authorization: Bearer <admin-token>
```

### Response
```json
{
  "success": true,
  "data": {
    "student_metrics": {
      "total_students": 850,
      "active_students": 820,
      "new_enrollments": 25,
      "enrollment_rate": 96.5
    },
    "academic_metrics": {
      "average_grade": 85.2,
      "pass_rate": 92.3,
      "attendance_rate": 94.7,
      "improvement_rate": 8.5
    },
    "financial_metrics": {
      "total_revenue": 125000.00,
      "collection_rate": 87.5,
      "outstanding_fees": 18750.00,
      "payment_trend": "increasing"
    },
    "system_metrics": {
      "active_users": 145,
      "login_rate": 78.2,
      "feature_adoption": 65.8,
      "system_uptime": 99.9
    }
  }
}
```

### Student Analytics
```http
GET /api/v1/analytics/students?grade=Grade%207&period=monthly
Authorization: Bearer <admin-token>
```

### Response
```json
{
  "success": true,
  "data": {
    "enrollment_trends": [
      {
        "month": "2024-01",
        "enrollments": 25,
        "withdrawals": 3,
        "net_change": 22
      }
    ],
    "performance_metrics": {
      "average_grade": 82.5,
      "grade_distribution": {
        "A": 15,
        "B": 25,
        "C": 30,
        "D": 8,
        "F": 2
      }
    },
    "attendance_metrics": {
      "overall_rate": 94.2,
      "by_class": {
        "7A": 95.1,
        "7B": 93.8,
        "7C": 93.7
      }
    }
  }
}
```

## 📱 Mobile API

### Mobile Login
```http
POST /api/v1/mobile/auth/login
Content-Type: application/json

{
  "username": "student@harare-primary.oneclass.ac.zw",
  "password": "secure_password",
  "device_id": "mobile_device_123",
  "device_name": "iPhone 14",
  "device_type": "ios",
  "app_version": "1.0.0"
}
```

### Mobile User Profile
```http
GET /api/v1/mobile/profile
Authorization: Bearer <mobile-token>
```

### Response
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Tendai Mukamuri",
      "email": "tendai.mukamuri@harare-primary.oneclass.ac.zw",
      "role": "student",
      "avatar_url": "https://cdn.oneclass.ac.zw/avatars/tendai.jpg"
    },
    "student": {
      "student_id": "STU2024001",
      "grade": "Grade 7",
      "class": "7A",
      "academic_year": "2024"
    },
    "school": {
      "name": "Harare Primary School",
      "logo_url": "https://cdn.oneclass.ac.zw/logos/harare-primary.png"
    }
  }
}
```

## 🔍 Monitoring API

### System Health
```http
GET /api/v1/monitoring/health
```

### Response
```json
{
  "status": "healthy",
  "timestamp": "2024-01-18T10:30:00Z",
  "system": {
    "cpu_usage": 25.5,
    "memory_usage": 65.2,
    "disk_usage": 45.8,
    "uptime": 86400
  },
  "database": {
    "connection_count": 15,
    "active_connections": 8,
    "status": "healthy"
  },
  "cache": {
    "hit_ratio": 92.5,
    "memory_usage": 128.5,
    "status": "healthy"
  }
}
```

## 🚨 Error Handling

### Standard Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    }
  },
  "timestamp": "2024-01-18T10:30:00Z",
  "request_id": "req_123456789"
}
```

### Common Error Codes
| Code | Description | HTTP Status |
|------|-------------|-------------|
| `VALIDATION_ERROR` | Request validation failed | 400 |
| `AUTHENTICATION_ERROR` | Authentication failed | 401 |
| `AUTHORIZATION_ERROR` | Insufficient permissions | 403 |
| `NOT_FOUND` | Resource not found | 404 |
| `CONFLICT` | Resource already exists | 409 |
| `RATE_LIMIT_EXCEEDED` | Too many requests | 429 |
| `INTERNAL_ERROR` | Server error | 500 |

## 📝 Request/Response Standards

### Request Headers
```http
Authorization: Bearer <access-token>
Content-Type: application/json
Accept: application/json
X-Client-Version: 1.0.0
X-School-Subdomain: harare-primary
```

### Response Headers
```http
Content-Type: application/json
X-Request-ID: req_123456789
X-Response-Time: 125ms
X-Rate-Limit-Remaining: 999
X-Rate-Limit-Reset: 1640995200
```

### Pagination
```json
{
  "success": true,
  "data": [...],
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 10,
    "total_pages": 10,
    "has_next": true,
    "has_previous": false
  }
}
```

## 🔒 Rate Limiting

### Rate Limits by Tier
| Tier | Requests per Hour | Requests per Minute |
|------|------------------|---------------------|
| Free | 1,000 | 20 |
| Premium | 10,000 | 200 |
| Enterprise | 100,000 | 2,000 |

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## 🛠️ SDK and Tools

### Official SDKs
- **Python**: `pip install oneclass-sdk`
- **JavaScript**: `npm install oneclass-sdk`
- **PHP**: `composer require oneclass/sdk`
- **Mobile**: iOS and Android SDKs available

### Development Tools
- **Postman Collection**: [Download](https://api.oneclass.ac.zw/docs/postman)
- **OpenAPI Spec**: [Download](https://api.oneclass.ac.zw/docs/openapi.json)
- **Interactive Docs**: [Explore](https://api.oneclass.ac.zw/docs)

## 📋 API Versioning

### Version Strategy
The API uses URL versioning:
- **Current Version**: `v1`
- **Base URL**: `https://api.oneclass.ac.zw/api/v1`
- **Deprecation Policy**: 6 months notice before deprecation

### Version Headers
```http
API-Version: v1
```

## 🔄 Webhooks

### Webhook Events
- `student.created`
- `student.updated`
- `student.deleted`
- `user.created`
- `user.updated`
- `grade.updated`
- `attendance.recorded`

### Webhook Payload
```json
{
  "event": "student.created",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "student_id": "STU2024001",
    "first_name": "Tendai",
    "last_name": "Mukamuri",
    "email": "tendai.mukamuri@harare-primary.oneclass.ac.zw"
  },
  "school_id": "456e7890-e89b-12d3-a456-426614174001",
  "timestamp": "2024-01-18T10:30:00Z"
}
```

## 📞 Support

### API Support
- **Email**: api-support@oneclass.ac.zw
- **Documentation**: https://docs.oneclass.ac.zw
- **Status Page**: https://status.oneclass.ac.zw
- **Community**: https://community.oneclass.ac.zw

### Response Times
- **Critical Issues**: 2 hours
- **High Priority**: 24 hours
- **Medium Priority**: 72 hours
- **Low Priority**: 1 week

---

**Last Updated**: 2024-01-18
**API Version**: v1
**Status**: Production Ready