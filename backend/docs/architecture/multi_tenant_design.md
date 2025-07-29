# OneClass Multi-Tenant Architecture Design

## Overview
OneClass needs to support:
- **Multi-School Users**: One user can have different roles in different schools
- **School Context Switching**: Users can switch between schools they have access to
- **School Groups**: Super admins can manage multiple schools
- **Context-Aware Permissions**: Permissions based on current school context

## Database Schema Design

### 1. Core User Table
```sql
-- Single user identity across the platform
platform.users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    
    -- Global platform role (only for platform-level access)
    platform_role VARCHAR(50) DEFAULT 'user', -- 'super_admin', 'platform_admin', 'user'
    
    -- Profile and preferences
    profile JSONB DEFAULT '{}',
    preferences JSONB DEFAULT '{}',
    
    -- Status
    status VARCHAR(50) DEFAULT 'active',
    is_verified BOOLEAN DEFAULT false,
    
    -- Authentication
    password_hash VARCHAR(255),
    clerk_user_id VARCHAR(255) UNIQUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);
```

### 2. School Memberships (Context-Based Roles)
```sql
-- User roles and permissions within specific schools
platform.school_memberships (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES platform.users(id) ON DELETE CASCADE,
    school_id UUID REFERENCES platform.schools(id) ON DELETE CASCADE,
    
    -- School context info
    school_name VARCHAR(255) NOT NULL,
    school_subdomain VARCHAR(50) NOT NULL,
    
    -- Role within this school
    role VARCHAR(50) NOT NULL, -- 'principal', 'teacher', 'parent', 'student', etc.
    
    -- Specific permissions for this role in this school
    permissions JSONB DEFAULT '[]',
    
    -- Role-specific data
    department VARCHAR(100), -- For staff
    employee_id VARCHAR(50), -- For staff
    student_id VARCHAR(50), -- For students
    current_grade VARCHAR(20), -- For students
    children_ids JSONB DEFAULT '[]', -- For parents
    
    -- Membership status
    status VARCHAR(50) DEFAULT 'active',
    joined_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    left_date TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, school_id)
);
```

### 3. School Groups (For Multi-School Management)
```sql
-- Groups of schools managed by the same organization
platform.school_groups (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Group admin
    owner_user_id UUID REFERENCES platform.users(id),
    
    -- Group settings
    settings JSONB DEFAULT '{}',
    
    -- Status
    status VARCHAR(50) DEFAULT 'active',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Schools belonging to groups
platform.school_group_memberships (
    id UUID PRIMARY KEY,
    group_id UUID REFERENCES platform.school_groups(id) ON DELETE CASCADE,
    school_id UUID REFERENCES platform.schools(id) ON DELETE CASCADE,
    
    -- When school joined the group
    joined_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(group_id, school_id)
);

-- Users who can manage school groups
platform.school_group_admins (
    id UUID PRIMARY KEY,
    group_id UUID REFERENCES platform.school_groups(id) ON DELETE CASCADE,
    user_id UUID REFERENCES platform.users(id) ON DELETE CASCADE,
    
    -- Admin level permissions
    permissions JSONB DEFAULT '[]',
    
    -- Status
    status VARCHAR(50) DEFAULT 'active',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(group_id, user_id)
);
```

### 4. User Sessions (Context-Aware)
```sql
-- User sessions with current school context
platform.user_sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES platform.users(id) ON DELETE CASCADE,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Current school context
    current_school_id UUID REFERENCES platform.schools(id),
    current_role VARCHAR(50), -- Current role in current school
    
    -- Session data
    refresh_token VARCHAR(500) UNIQUE NOT NULL,
    ip_address VARCHAR(50),
    user_agent TEXT,
    device_info JSONB DEFAULT '{}',
    
    -- Session status
    is_active BOOLEAN DEFAULT true,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);
```

## API Design

### 1. Authentication with Context
```typescript
// JWT Token Structure
interface JWTPayload {
    sub: string; // user_id
    email: string;
    session_id: string;
    
    // Platform level
    platform_role: 'super_admin' | 'platform_admin' | 'user';
    
    // Current school context
    current_school_id?: string;
    current_school_role?: string;
    current_school_permissions?: string[];
    
    // Available schools
    available_schools: Array<{
        school_id: string;
        school_name: string;
        role: string;
        permissions: string[];
    }>;
    
    exp: number;
    iat: number;
}
```

### 2. School Context Switching
```typescript
// Switch school context
POST /api/v1/auth/switch-school
{
    "school_id": "uuid",
    "role": "teacher" // if user has multiple roles in same school
}

// Response: New JWT token with updated context
{
    "access_token": "new_jwt_token",
    "current_school": {
        "school_id": "uuid",
        "school_name": "School Name",
        "role": "teacher",
        "permissions": ["manage_classes", "view_students"]
    }
}
```

### 3. Multi-School Management
```typescript
// Get schools user can access
GET /api/v1/auth/schools

// Get school groups user can manage
GET /api/v1/school-groups

// Create new school in group
POST /api/v1/school-groups/{group_id}/schools
```

## Frontend Implementation

### 1. School Context Provider
```typescript
interface SchoolContext {
    currentSchool: School | null;
    availableSchools: School[];
    currentRole: string | null;
    permissions: string[];
    switchSchool: (schoolId: string, role?: string) => Promise<void>;
}

export const SchoolContextProvider = ({ children }) => {
    // Implementation
};
```

### 2. School Switcher Component
```typescript
export const SchoolSwitcher = () => {
    const { currentSchool, availableSchools, switchSchool } = useSchoolContext();
    
    return (
        <Select onValueChange={(schoolId) => switchSchool(schoolId)}>
            {availableSchools.map(school => (
                <SelectItem key={school.id} value={school.id}>
                    {school.name} ({school.role})
                </SelectItem>
            ))}
        </Select>
    );
};
```

## Migration Strategy

### Phase 1: Update Database Schema
1. Add school_groups tables
2. Update user_sessions to include current_school_id
3. Ensure school_memberships supports multiple roles per user

### Phase 2: Update Authentication System
1. Modify JWT token generation to include school context
2. Add school switching endpoint
3. Update middleware to handle school context

### Phase 3: Update Frontend
1. Add SchoolContextProvider
2. Add SchoolSwitcher component
3. Update all API calls to be context-aware

### Phase 4: Multi-School Admin Features
1. School group management UI
2. Cross-school reporting
3. Bulk operations across schools

## Benefits

1. **Flexibility**: Users can have different roles in different schools
2. **Scalability**: Supports large organizations with multiple schools
3. **Security**: Context-aware permissions
4. **User Experience**: Seamless school switching
5. **Business Model**: Supports various organizational structures
