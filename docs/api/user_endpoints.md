# OneClass Platform: User Management API Documentation

## Overview

The User Management API provides comprehensive functionality for managing users in the OneClass multi-tenant platform. All endpoints support the new consolidated `PlatformUser` model with multi-school membership capabilities.

## Base URL
```
https://api.oneclass.ac.zw/api/v1/users
```

## Authentication

All endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## User Model Structure

### PlatformUser Response
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "platform_role": "teacher",
  "status": "active",
  "primary_school_id": "550e8400-e29b-41d4-a716-446655440001",
  "school_memberships": [
    {
      "school_id": "550e8400-e29b-41d4-a716-446655440001",
      "school_name": "Springfield Primary School",
      "school_subdomain": "springfield-primary",
      "role": "teacher",
      "permissions": ["students.read", "attendance.mark", "grades.enter"],
      "joined_date": "2024-01-15T10:30:00Z",
      "status": "active",
      "employee_id": "EMP001",
      "department": "Mathematics"
    }
  ],
  "profile": {
    "phone_number": "+263771234567",
    "profile_image_url": "https://cdn.oneclass.ac.zw/profiles/john-doe.jpg",
    "preferred_language": "en",
    "timezone": "Africa/Harare"
  },
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-07-18T14:22:00Z"
}
```

### Platform Roles
- `super_admin` - Platform administrator
- `school_admin` - School administrator  
- `registrar` - School registrar
- `teacher` - Teaching staff
- `parent` - Parent/guardian
- `student` - Student
- `staff` - Non-teaching staff

### School Roles
- `principal` - School principal
- `deputy_principal` - Deputy principal
- `academic_head` - Academic head
- `department_head` - Department head
- `teacher` - Teacher
- `form_teacher` - Form teacher
- `registrar` - School registrar
- `bursar` - Financial officer
- `librarian` - Librarian
- `it_support` - IT support staff
- `security` - Security staff
- `parent` - Parent/guardian
- `student` - Student

## Endpoints

### 1. User Management

#### Create User
```http
POST /users
```

**Request Body:**
```json
{
  "email": "jane.smith@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "platform_role": "teacher",
  "school_id": "550e8400-e29b-41d4-a716-446655440001",
  "school_role": "teacher",
  "profile": {
    "phone_number": "+263771234568",
    "preferred_language": "en",
    "timezone": "Africa/Harare"
  },
  "permissions": ["students.read", "attendance.mark"]
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "email": "jane.smith@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "full_name": "Jane Smith",
  "platform_role": "teacher",
  "status": "active",
  "school_memberships": [
    {
      "school_id": "550e8400-e29b-41d4-a716-446655440001",
      "school_name": "Springfield Primary School",
      "role": "teacher",
      "permissions": ["students.read", "attendance.mark"],
      "joined_date": "2024-07-18T14:22:00Z",
      "status": "active"
    }
  ],
  "created_at": "2024-07-18T14:22:00Z"
}
```

**Permissions Required:** `users.create` in the target school

---

#### Get User
```http
GET /users/{user_id}
```

**Path Parameters:**
- `user_id` (UUID) - The user's unique identifier

**Response:** [PlatformUser Response](#platformuser-response)

**Permissions Required:** `users.read` in the school or own user data

---

#### Update User
```http
PUT /users/{user_id}
```

**Path Parameters:**
- `user_id` (UUID) - The user's unique identifier

**Request Body:**
```json
{
  "first_name": "Jane Updated",
  "last_name": "Smith Updated",
  "profile": {
    "phone_number": "+263771234569",
    "timezone": "Africa/Harare"
  }
}
```

**Response:** [PlatformUser Response](#platformuser-response)

**Permissions Required:** `users.update` in the school or own user data

---

#### List Users
```http
GET /users
```

**Query Parameters:**
- `school_id` (UUID, optional) - Filter by school
- `role` (string, optional) - Filter by school role
- `status` (string, optional) - Filter by user status
- `search` (string, optional) - Search by name or email
- `limit` (integer, optional, default: 50) - Number of results
- `offset` (integer, optional, default: 0) - Pagination offset

**Response:**
```json
{
  "users": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "john.doe@example.com",
      "full_name": "John Doe",
      "platform_role": "teacher",
      "school_role": "teacher",
      "status": "active",
      "joined_date": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

**Permissions Required:** `users.read` in the school

---

#### Delete User
```http
DELETE /users/{user_id}
```

**Path Parameters:**
- `user_id` (UUID) - The user's unique identifier

**Response:**
```json
{
  "message": "User deleted successfully"
}
```

**Permissions Required:** `users.delete` in the school

---

### 2. Role-Specific User Creation

#### Create Teacher
```http
POST /users/teachers
```

**Request Body:**
```json
{
  "email": "teacher@example.com",
  "first_name": "Sarah",
  "last_name": "Johnson",
  "employee_id": "EMP002",
  "department": "Science",
  "subjects": ["Physics", "Chemistry"],
  "profile": {
    "phone_number": "+263771234570"
  }
}
```

**Permissions Required:** `staff.create`

---

#### Create Student
```http
POST /users/students
```

**Request Body:**
```json
{
  "email": "student@example.com",
  "first_name": "Michael",
  "last_name": "Brown",
  "student_id": "STU001",
  "current_grade": "Grade 7",
  "admission_date": "2024-01-15",
  "profile": {
    "date_of_birth": "2010-05-15",
    "gender": "male"
  }
}
```

**Permissions Required:** `students.create`

---

#### Create Parent
```http
POST /users/parents
```

**Request Body:**
```json
{
  "email": "parent@example.com",
  "first_name": "David",
  "last_name": "Wilson",
  "children_ids": ["550e8400-e29b-41d4-a716-446655440003"],
  "relationship": "father",
  "profile": {
    "phone_number": "+263771234571",
    "emergency_contact_name": "Mary Wilson",
    "emergency_contact_phone": "+263771234572"
  }
}
```

**Permissions Required:** `parents.create`

---

#### Create Staff
```http
POST /users/staff
```

**Request Body:**
```json
{
  "email": "staff@example.com",
  "first_name": "Lisa",
  "last_name": "Davis",
  "employee_id": "EMP003",
  "department": "Administration",
  "position": "Secretary",
  "contract_type": "permanent",
  "hire_date": "2024-01-15"
}
```

**Permissions Required:** `staff.create`

---

### 3. School Membership Management

#### Add School Membership
```http
POST /users/{user_id}/schools
```

**Path Parameters:**
- `user_id` (UUID) - The user's unique identifier

**Request Body:**
```json
{
  "school_id": "550e8400-e29b-41d4-a716-446655440004",
  "role": "teacher",
  "permissions": ["students.read", "attendance.mark"],
  "start_date": "2024-07-18"
}
```

**Response:**
```json
{
  "school_id": "550e8400-e29b-41d4-a716-446655440004",
  "school_name": "Oak Valley Secondary",
  "school_subdomain": "oak-valley-secondary",
  "role": "teacher",
  "permissions": ["students.read", "attendance.mark"],
  "joined_date": "2024-07-18T14:22:00Z",
  "status": "active"
}
```

**Permissions Required:** `users.update` and `school.manage_members`

---

#### Update School Membership
```http
PUT /users/{user_id}/schools/{school_id}
```

**Request Body:**
```json
{
  "role": "department_head",
  "permissions": ["students.read", "students.update", "staff.read"],
  "department": "Mathematics"
}
```

**Permissions Required:** `users.update` and `school.manage_members`

---

#### Remove School Membership
```http
DELETE /users/{user_id}/schools/{school_id}
```

**Response:**
```json
{
  "message": "School membership removed successfully"
}
```

**Permissions Required:** `users.update` and `school.manage_members`

---

### 4. User Profile Management

#### Get User Profile
```http
GET /users/{user_id}/profile
```

**Response:**
```json
{
  "phone_number": "+263771234567",
  "profile_image_url": "https://cdn.oneclass.ac.zw/profiles/john-doe.jpg",
  "date_of_birth": "1985-03-20",
  "gender": "male",
  "address": "123 Main Street, Harare",
  "emergency_contact_name": "Jane Doe",
  "emergency_contact_phone": "+263771234568",
  "bio": "Experienced mathematics teacher",
  "preferred_language": "en",
  "timezone": "Africa/Harare",
  "notification_preferences": {
    "email_notifications": true,
    "sms_notifications": true,
    "push_notifications": true,
    "marketing_emails": false
  }
}
```

**Permissions Required:** `users.read` or own profile

---

#### Update User Profile
```http
PUT /users/{user_id}/profile
```

**Request Body:**
```json
{
  "phone_number": "+263771234569",
  "address": "456 Oak Avenue, Harare",
  "bio": "Senior mathematics teacher with 10 years experience",
  "notification_preferences": {
    "email_notifications": true,
    "sms_notifications": false
  }
}
```

**Permissions Required:** `users.update` or own profile

---

### 5. User Search and Filtering

#### Search Users
```http
GET /users/search
```

**Query Parameters:**
- `q` (string, required) - Search query (name, email)
- `school_id` (UUID, optional) - Limit search to specific school
- `roles` (array, optional) - Filter by roles
- `limit` (integer, optional, default: 50) - Number of results

**Response:**
```json
{
  "users": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "john.doe@example.com",
      "full_name": "John Doe",
      "platform_role": "teacher",
      "school_role": "teacher",
      "profile_image_url": "https://cdn.oneclass.ac.zw/profiles/john-doe.jpg"
    }
  ],
  "total": 1,
  "query": "john"
}
```

---

#### Get School Users
```http
GET /schools/{school_id}/users
```

**Query Parameters:**
- `roles` (array, optional) - Filter by school roles
- `status` (string, optional) - Filter by status
- `department` (string, optional) - Filter by department
- `limit` (integer, optional, default: 100) - Number of results
- `offset` (integer, optional, default: 0) - Pagination offset

**Response:**
```json
{
  "users": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "john.doe@example.com",
      "full_name": "John Doe",
      "school_role": "teacher",
      "department": "Mathematics",
      "employee_id": "EMP001",
      "joined_date": "2024-01-15T10:30:00Z",
      "status": "active"
    }
  ],
  "total": 1,
  "school_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

**Permissions Required:** `users.read` in the school

---

### 6. User Invitations

#### Create User Invitation
```http
POST /users/invitations
```

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "role": "teacher",
  "school_id": "550e8400-e29b-41d4-a716-446655440001",
  "permissions": ["students.read", "attendance.mark"],
  "message": "Welcome to Springfield Primary School!",
  "expires_in_days": 7
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440005",
  "email": "newuser@example.com",
  "role": "teacher",
  "school_id": "550e8400-e29b-41d4-a716-446655440001",
  "invitation_token": "inv_1234567890abcdef",
  "invitation_url": "https://app.oneclass.ac.zw/accept-invitation?token=inv_1234567890abcdef",
  "status": "pending",
  "expires_at": "2024-07-25T14:22:00Z",
  "created_at": "2024-07-18T14:22:00Z"
}
```

**Permissions Required:** `users.invite`

---

#### List User Invitations
```http
GET /users/invitations
```

**Query Parameters:**
- `status` (string, optional) - Filter by invitation status

**Response:**
```json
{
  "invitations": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440005",
      "email": "newuser@example.com",
      "role": "teacher",
      "status": "pending",
      "expires_at": "2024-07-25T14:22:00Z",
      "created_at": "2024-07-18T14:22:00Z"
    }
  ],
  "total": 1
}
```

---

#### Accept User Invitation
```http
POST /users/invitations/accept
```

**Request Body:**
```json
{
  "token": "inv_1234567890abcdef",
  "first_name": "Alice",
  "last_name": "Cooper",
  "password": "securepassword123",
  "profile": {
    "phone_number": "+263771234573",
    "preferred_language": "en"
  }
}
```

**Response:** [PlatformUser Response](#platformuser-response)

---

### 7. Bulk Operations

#### Bulk Import Users
```http
POST /users/bulk-import
```

**Request Body:** `multipart/form-data`
- `file` (file) - CSV or Excel file with user data
- `import_type` (string) - "csv" or "excel"
- `default_role` (string, optional) - Default role for users
- `send_invitations` (boolean, optional) - Send invitation emails

**Response:**
```json
{
  "import_id": "550e8400-e29b-41d4-a716-446655440006",
  "total_records": 50,
  "successful_imports": 48,
  "failed_imports": 2,
  "errors": [
    {
      "row": 15,
      "email": "invalid-email",
      "error": "Invalid email format"
    },
    {
      "row": 23,
      "email": "duplicate@example.com",
      "error": "User already exists"
    }
  ],
  "status": "completed",
  "created_at": "2024-07-18T14:22:00Z"
}
```

**Permissions Required:** `users.bulk_import`

---

### 8. User Analytics

#### Get User Statistics
```http
GET /users/statistics
```

**Query Parameters:**
- `school_id` (UUID, optional) - Filter by school
- `date_from` (date, optional) - Start date for analytics
- `date_to` (date, optional) - End date for analytics

**Response:**
```json
{
  "total_users": 1250,
  "active_users": 1180,
  "inactive_users": 70,
  "users_by_role": {
    "student": 1000,
    "teacher": 80,
    "parent": 150,
    "staff": 20
  },
  "new_users_this_month": 25,
  "login_activity": {
    "daily_active_users": 450,
    "weekly_active_users": 890,
    "monthly_active_users": 1100
  },
  "school_distribution": [
    {
      "school_id": "550e8400-e29b-41d4-a716-446655440001",
      "school_name": "Springfield Primary",
      "user_count": 350
    }
  ]
}
```

**Permissions Required:** `analytics.view` or `super_admin`

---

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  },
  "timestamp": "2024-07-18T14:22:00Z",
  "request_id": "req_1234567890"
}
```

### Common Error Codes
- `VALIDATION_ERROR` (400) - Request validation failed
- `UNAUTHORIZED` (401) - Authentication required
- `FORBIDDEN` (403) - Insufficient permissions
- `NOT_FOUND` (404) - Resource not found
- `CONFLICT` (409) - Resource already exists
- `RATE_LIMITED` (429) - Too many requests
- `INTERNAL_ERROR` (500) - Server error

## Rate Limiting

- **Standard endpoints**: 100 requests per minute per user
- **Search endpoints**: 50 requests per minute per user
- **Bulk operations**: 10 requests per minute per user
- **Authentication**: 20 requests per minute per IP

## Pagination

All list endpoints support pagination:

**Request:**
```http
GET /users?limit=25&offset=50
```

**Response Headers:**
```
X-Total-Count: 1250
X-Page-Count: 50
X-Current-Page: 3
X-Per-Page: 25
```

## Performance

### Response Times (95th percentile)
- **User retrieval**: <50ms (cached), <200ms (uncached)
- **User search**: <100ms
- **Bulk operations**: <30 seconds for 1000 records
- **List operations**: <150ms for 100 records

### Caching
- **User context**: Cached for 5 minutes
- **School memberships**: Cached for 15 minutes
- **Search results**: Cached for 2 minutes

## Examples

### Complete User Creation Flow
```javascript
// 1. Create user
const newUser = await fetch('/api/v1/users', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'teacher@school.com',
    first_name: 'Sarah',
    last_name: 'Johnson',
    platform_role: 'teacher',
    school_role: 'teacher',
    profile: {
      phone_number: '+263771234567'
    }
  })
});

// 2. Add to additional school
await fetch(`/api/v1/users/${newUser.id}/schools`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    school_id: 'secondary-school-uuid',
    role: 'substitute_teacher'
  })
});

// 3. Update profile
await fetch(`/api/v1/users/${newUser.id}/profile`, {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    bio: 'Experienced mathematics teacher',
    notification_preferences: {
      email_notifications: true,
      sms_notifications: false
    }
  })
});
```

### School User Management
```javascript
// Get all teachers in a school
const teachers = await fetch('/api/v1/schools/school-uuid/users?roles=teacher,department_head', {
  headers: { 'Authorization': `Bearer ${token}` }
});

// Search for users across platform
const searchResults = await fetch('/api/v1/users/search?q=john&limit=10', {
  headers: { 'Authorization': `Bearer ${token}` }
});

// Get user statistics
const stats = await fetch('/api/v1/users/statistics?school_id=school-uuid', {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

This API provides comprehensive user management capabilities while maintaining security, performance, and scalability for the OneClass multi-tenant platform.