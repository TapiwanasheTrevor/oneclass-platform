# Multitenancy Enhancement Plan for Claude Code

## **🎯 Objective: Production-Ready Multitenancy in 8 Weeks**

**Deadline**: Product ready for testing 4 months before school calendar (January 2025)
**Timeline**: 8 weeks for complete multitenancy enhancement
**Current Status**: 85% complete, need final 15% for enterprise-grade deployment

---

## **📋 Phase 1: Core Multitenancy Enhancements (Weeks 1-2)**

### **Task 1.1: Enhanced Platform Schema**

**File**: `database/schemas/00_platform_enhanced.sql`

```sql
-- =====================================================
-- Enhanced Platform Schema for Full Multitenancy
-- Add to existing platform schema
-- =====================================================

-- School configuration and branding
CREATE TABLE platform.school_configurations (
    school_id UUID PRIMARY KEY REFERENCES platform.schools(id) ON DELETE CASCADE,
    
    -- Branding Configuration
    logo_url TEXT,
    favicon_url TEXT,
    primary_color VARCHAR(7) DEFAULT '#1e40af', -- Hex color
    secondary_color VARCHAR(7) DEFAULT '#10b981',
    accent_color VARCHAR(7) DEFAULT '#f59e0b',
    font_family VARCHAR(100) DEFAULT 'Inter',
    
    -- School Identity
    motto TEXT,
    vision_statement TEXT,
    mission_statement TEXT,
    established_year INTEGER,
    school_website TEXT,
    
    -- Contact Information
    official_email VARCHAR(255),
    official_phone VARCHAR(20),
    postal_address JSONB,
    
    -- Regional Settings
    timezone VARCHAR(50) DEFAULT 'Africa/Harare',
    academic_calendar_type VARCHAR(20) DEFAULT 'zimbabwe', -- 'zimbabwe', 'british', 'american'
    language_primary VARCHAR(10) DEFAULT 'en',
    language_secondary VARCHAR(10), -- 'sn' for Shona, 'nd' for Ndebele
    currency VARCHAR(3) DEFAULT 'USD',
    date_format VARCHAR(20) DEFAULT 'DD/MM/YYYY',
    
    -- Feature Toggles per School
    features_enabled JSONB DEFAULT '{
        "attendance_tracking": true,
        "disciplinary_system": true,
        "health_records": true,
        "finance_module": true,
        "parent_portal": true,
        "ministry_reporting": false,
        "ai_assistance": false,
        "bulk_sms": false,
        "whatsapp_integration": false
    }'::jsonb,
    
    -- Custom Fields Configuration
    custom_student_fields JSONB DEFAULT '[]'::jsonb,
    custom_parent_fields JSONB DEFAULT '[]'::jsonb,
    
    -- Academic Structure
    grading_system JSONB DEFAULT '{
        "type": "percentage",
        "scale": {"A": "80-100", "B": "70-79", "C": "60-69", "D": "50-59", "E": "40-49", "F": "0-39"},
        "pass_mark": 50
    }'::jsonb,
    
    -- Notification Preferences
    notification_settings JSONB DEFAULT '{
        "email_enabled": true,
        "sms_enabled": false,
        "whatsapp_enabled": false,
        "push_enabled": true,
        "parent_absence_alert": true,
        "disciplinary_auto_notify": true
    }'::jsonb,
    
    -- System Configuration
    student_id_format VARCHAR(50) DEFAULT 'YYYY-NNNN',
    max_students_per_class INTEGER DEFAULT 40,
    academic_year_start_month INTEGER DEFAULT 1, -- January = 1
    terms_per_year INTEGER DEFAULT 3,
    
    -- Subscription and Limits
    subscription_tier VARCHAR(20) DEFAULT 'basic', -- 'trial', 'basic', 'premium', 'enterprise'
    max_students INTEGER DEFAULT 500,
    max_staff INTEGER DEFAULT 50,
    storage_limit_gb INTEGER DEFAULT 10,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- School domains for subdomain support (future)
CREATE TABLE platform.school_domains (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES platform.schools(id) ON DELETE CASCADE,
    domain VARCHAR(255) UNIQUE NOT NULL, -- e.g., 'harare-high.1class.app'
    is_primary BOOLEAN DEFAULT FALSE,
    is_custom BOOLEAN DEFAULT FALSE, -- true for custom domains like 'portal.hararehigh.edu.zw'
    ssl_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(school_id, is_primary) WHERE is_primary = true
);

-- Feature usage tracking for analytics
CREATE TABLE platform.school_feature_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES platform.schools(id) ON DELETE CASCADE,
    feature_name VARCHAR(100) NOT NULL,
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(school_id, feature_name)
);

-- Enhanced user table to include school context
ALTER TABLE platform.users ADD COLUMN IF NOT EXISTS school_role_context JSONB DEFAULT '{}'::jsonb;
ALTER TABLE platform.users ADD COLUMN IF NOT EXISTS last_school_switch TIMESTAMP WITH TIME ZONE;
ALTER TABLE platform.users ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(10) DEFAULT 'en';

-- Indexes for performance
CREATE INDEX idx_school_configurations_tier ON platform.school_configurations(subscription_tier);
CREATE INDEX idx_school_domains_domain ON platform.school_domains(domain);
CREATE INDEX idx_feature_usage_school_feature ON platform.school_feature_usage(school_id, feature_name);

-- RLS Policies
ALTER TABLE platform.school_configurations ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform.school_domains ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform.school_feature_usage ENABLE ROW LEVEL SECURITY;

CREATE POLICY school_config_access ON platform.school_configurations
FOR ALL TO authenticated_user
USING (school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid()));

CREATE POLICY school_domains_access ON platform.school_domains
FOR ALL TO authenticated_user
USING (school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid()));

-- Utility functions
CREATE OR REPLACE FUNCTION platform.get_school_config(p_school_id UUID)
RETURNS JSONB AS $$
DECLARE
    config_data JSONB;
BEGIN
    SELECT row_to_json(sc.*)::jsonb INTO config_data
    FROM platform.school_configurations sc
    WHERE sc.school_id = p_school_id;
    
    RETURN COALESCE(config_data, '{}'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- Trigger to create default configuration for new schools
CREATE OR REPLACE FUNCTION platform.create_default_school_config()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO platform.school_configurations (school_id)
    VALUES (NEW.id);
    
    INSERT INTO platform.school_domains (school_id, domain, is_primary)
    VALUES (NEW.id, LOWER(REPLACE(NEW.name, ' ', '-')) || '.1class.app', true);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_create_school_config
AFTER INSERT ON platform.schools
FOR EACH ROW EXECUTE FUNCTION platform.create_default_school_config();
```

### **Task 1.2: Enhanced Authentication Context**

**File**: `backend/shared/auth.py`

```python
# =====================================================
# Enhanced Authentication with Full School Context
# File: backend/shared/auth.py
# =====================================================

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import json

class SchoolConfiguration(BaseModel):
    """School configuration and branding"""
    school_id: UUID
    logo_url: Optional[str] = None
    primary_color: str = "#1e40af"
    secondary_color: str = "#10b981"
    timezone: str = "Africa/Harare"
    language_primary: str = "en"
    language_secondary: Optional[str] = None
    currency: str = "USD"
    features_enabled: Dict[str, bool]
    subscription_tier: str = "basic"
    max_students: int = 500
    grading_system: Dict[str, Any]
    notification_settings: Dict[str, bool]
    student_id_format: str = "YYYY-NNNN"
    academic_year_start_month: int = 1
    terms_per_year: int = 3

class SchoolDomain(BaseModel):
    """School domain configuration"""
    domain: str
    is_primary: bool
    is_custom: bool

class EnhancedUser(BaseModel):
    """Enhanced user model with full school context"""
    # Core User Data
    id: UUID
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    
    # School Context
    school_id: UUID
    school_name: str
    school_type: str
    school_config: SchoolConfiguration
    school_domains: List[SchoolDomain]
    
    # Permissions and Features
    permissions: List[str]
    available_features: List[str]
    
    # User Preferences
    preferred_language: str = "en"
    timezone: str = "Africa/Harare"
    
    # System Info
    last_login: Optional[datetime] = None
    created_at: datetime
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def can_access_feature(self) -> callable:
        def check_feature(feature_name: str) -> bool:
            return (
                feature_name in self.available_features and
                self.school_config.features_enabled.get(feature_name, False)
            )
        return check_feature
    
    @property
    def is_admin(self) -> bool:
        return self.role in ["school_admin", "super_admin"]
    
    @property
    def can_modify_students(self) -> bool:
        return self.role in ["school_admin", "registrar"]

async def get_current_active_user(token: str = Depends(get_auth_token)) -> EnhancedUser:
    """
    Get current user with full school context and configuration.
    This replaces the basic get_current_active_user function.
    """
    # Validate JWT token with Supabase
    user_data = await validate_supabase_token(token)
    
    # Get full user context with school configuration
    query = """
        SELECT 
            u.*,
            s.name as school_name,
            s.school_type,
            sc.*,
            array_agg(sd.domain) as domains
        FROM platform.users u
        JOIN platform.schools s ON u.school_id = s.id
        LEFT JOIN platform.school_configurations sc ON s.id = sc.school_id
        LEFT JOIN platform.school_domains sd ON s.id = sd.school_id
        WHERE u.id = $1 AND u.is_active = true
        GROUP BY u.id, s.name, s.school_type, sc.school_id
    """
    
    result = await database.fetch_one(query, user_data["id"])
    
    if not result:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    # Build school configuration
    school_config = SchoolConfiguration(
        school_id=result["school_id"],
        logo_url=result["logo_url"],
        primary_color=result["primary_color"],
        secondary_color=result["secondary_color"],
        timezone=result["timezone"],
        language_primary=result["language_primary"],
        language_secondary=result["language_secondary"],
        currency=result["currency"],
        features_enabled=result["features_enabled"],
        subscription_tier=result["subscription_tier"],
        max_students=result["max_students"],
        grading_system=result["grading_system"],
        notification_settings=result["notification_settings"],
        student_id_format=result["student_id_format"],
        academic_year_start_month=result["academic_year_start_month"],
        terms_per_year=result["terms_per_year"]
    )
    
    # Build school domains
    school_domains = [
        SchoolDomain(domain=domain, is_primary=True, is_custom=False)
        for domain in (result["domains"] or [])
    ]
    
    # Get user permissions based on role
    permissions = await get_user_permissions(result["role"], result["school_id"])
    available_features = await get_available_features(result["subscription_tier"])
    
    return EnhancedUser(
        id=result["id"],
        email=result["email"],
        first_name=result["first_name"],
        last_name=result["last_name"],
        role=result["role"],
        is_active=result["is_active"],
        school_id=result["school_id"],
        school_name=result["school_name"],
        school_type=result["school_type"],
        school_config=school_config,
        school_domains=school_domains,
        permissions=permissions,
        available_features=available_features,
        preferred_language=result["preferred_language"],
        timezone=result["timezone"],
        last_login=result["last_login"],
        created_at=result["created_at"]
    )

async def get_user_permissions(role: str, school_id: UUID) -> List[str]:
    """Get user permissions based on role and school configuration"""
    base_permissions = {
        "super_admin": ["*"],  # All permissions
        "school_admin": [
            "students.create", "students.read", "students.update", "students.delete",
            "staff.create", "staff.read", "staff.update", "staff.delete",
            "classes.create", "classes.read", "classes.update", "classes.delete",
            "reports.generate", "settings.update", "finance.manage"
        ],
        "registrar": [
            "students.create", "students.read", "students.update",
            "documents.upload", "documents.verify"
        ],
        "teacher": [
            "students.read", "attendance.mark", "grades.enter",
            "disciplinary.minor", "health.basic"
        ],
        "parent": [
            "children.read", "payments.make", "communications.receive"
        ],
        "student": [
            "profile.read", "assignments.view", "grades.view"
        ]
    }
    
    return base_permissions.get(role, [])

async def get_available_features(subscription_tier: str) -> List[str]:
    """Get available features based on subscription tier"""
    feature_tiers = {
        "trial": [
            "student_management", "basic_attendance", "parent_communication"
        ],
        "basic": [
            "student_management", "attendance_tracking", "basic_reports",
            "parent_portal", "disciplinary_system"
        ],
        "premium": [
            "student_management", "attendance_tracking", "health_records",
            "finance_module", "parent_portal", "disciplinary_system",
            "advanced_reports", "bulk_communication"
        ],
        "enterprise": [
            "student_management", "attendance_tracking", "health_records",
            "finance_module", "parent_portal", "disciplinary_system",
            "advanced_reports", "bulk_communication", "ministry_reporting",
            "ai_assistance", "custom_integrations", "priority_support"
        ]
    }
    
    return feature_tiers.get(subscription_tier, feature_tiers["trial"])

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            if "*" not in current_user.permissions and permission not in current_user.permissions:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Permission required: {permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_feature(feature_name: str):
    """Decorator to require feature availability"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            if not current_user.can_access_feature(feature_name):
                raise HTTPException(
                    status_code=403, 
                    detail=f"Feature not available: {feature_name}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### **Task 1.3: Enhanced File Storage with School Isolation**

**File**: `backend/shared/file_storage.py`

```python
# =====================================================
# Enhanced File Storage with Complete School Isolation
# File: backend/shared/file_storage.py
# =====================================================

import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any, List
from uuid import UUID
import os
import logging
from datetime import datetime, timedelta
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)

class SchoolFileStorage:
    """
    School-isolated file storage system with S3 backend.
    Provides complete isolation between schools with proper access control.
    """
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('AWS_S3_BUCKET')
        self.cdn_base_url = os.getenv('CDN_BASE_URL', '')
    
    def _get_school_prefix(self, school_id: UUID) -> str:
        """Get S3 prefix for school isolation"""
        return f"schools/{school_id}"
    
    def _get_file_path(self, school_id: UUID, category: str, file_name: str) -> str:
        """Generate full S3 file path with proper isolation"""
        school_prefix = self._get_school_prefix(school_id)
        timestamp = datetime.now().strftime('%Y/%m')
        return f"{school_prefix}/{category}/{timestamp}/{file_name}"
    
    async def upload_file(
        self,
        file: UploadFile,
        school_id: UUID,
        category: str,
        subfolder: str = "",
        allowed_types: Optional[List[str]] = None,
        max_size_mb: int = 10
    ) -> Dict[str, Any]:
        """
        Upload file with school isolation and validation.
        
        Args:
            file: The uploaded file
            school_id: School ID for isolation
            category: File category (documents, photos, reports, etc.)
            subfolder: Optional subfolder within category
            allowed_types: List of allowed file extensions
            max_size_mb: Maximum file size in MB
            
        Returns:
            Dict with file URL, size, type, and metadata
        """
        try:
            # Validate file type
            if allowed_types:
                file_ext = file.filename.split('.')[-1].lower() if file.filename else ''
                if file_ext not in allowed_types:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"File type not allowed. Allowed: {', '.join(allowed_types)}"
                    )
            
            # Validate file size
            if file.size > max_size_mb * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size: {max_size_mb}MB"
                )
            
            # Generate unique file name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{file.filename}"
            
            # Build file path with school isolation
            if subfolder:
                file_path = self._get_file_path(school_id, f"{category}/{subfolder}", unique_filename)
            else:
                file_path = self._get_file_path(school_id, category, unique_filename)
            
            # Upload to S3
            file_content = await file.read()
            
            upload_response = self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_path,
                Body=file_content,
                ContentType=file.content_type,
                Metadata={
                    'school_id': str(school_id),
                    'category': category,
                    'original_filename': file.filename,
                    'uploaded_at': datetime.now().isoformat()
                }
            )
            
            # Generate file URL
            file_url = f"{self.cdn_base_url}/{file_path}" if self.cdn_base_url else \
                      f"https://{self.bucket_name}.s3.amazonaws.com/{file_path}"
            
            logger.info(f"File uploaded successfully: {file_path} for school {school_id}")
            
            return {
                'file_url': file_url,
                'file_path': file_path,
                'file_size': file.size,
                'file_type': file.content_type,
                'original_filename': file.filename,
                'upload_timestamp': datetime.now().isoformat()
            }
            
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            raise HTTPException(status_code=500, detail="File upload failed")
        except Exception as e:
            logger.error(f"File upload error: {e}")
            raise HTTPException(status_code=500, detail="File upload failed")
    
    async def delete_file(self, file_path: str, school_id: UUID) -> bool:
        """
        Delete file with school verification.
        Only allows deletion of files belonging to the specified school.
        """
        try:
            # Verify file belongs to school
            school_prefix = self._get_school_prefix(school_id)
            if not file_path.startswith(school_prefix):
                raise HTTPException(
                    status_code=403,
                    detail="Cannot delete file from another school"
                )
            
            # Delete from S3
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            
            logger.info(f"File deleted: {file_path} for school {school_id}")
            return True
            
        except ClientError as e:
            logger.error(f"S3 delete error: {e}")
            return False
        except Exception as e:
            logger.error(f"File delete error: {e}")
            return False
    
    async def get_presigned_url(
        self,
        file_path: str,
        school_id: UUID,
        expiration: int = 3600
    ) -> str:
        """
        Generate presigned URL for secure file access.
        Verifies school ownership before generating URL.
        """
        try:
            # Verify file belongs to school
            school_prefix = self._get_school_prefix(school_id)
            if not file_path.startswith(school_prefix):
                raise HTTPException(
                    status_code=403,
                    detail="Cannot access file from another school"
                )
            
            # Generate presigned URL
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_path},
                ExpiresIn=expiration
            )
            
            return presigned_url
            
        except ClientError as e:
            logger.error(f"Presigned URL error: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate file access URL")
    
    async def list_school_files(
        self,
        school_id: UUID,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List all files for a school with optional category filtering.
        """
        try:
            school_prefix = self._get_school_prefix(school_id)
            prefix = f"{school_prefix}/{category}" if category else school_prefix
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=limit
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'file_path': obj['Key'],
                    'file_size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'file_url': f"{self.cdn_base_url}/{obj['Key']}" if self.cdn_base_url else \
                              f"https://{self.bucket_name}.s3.amazonaws.com/{obj['Key']}"
                })
            
            return files
            
        except ClientError as e:
            logger.error(f"List files error: {e}")
            return []
    
    async def get_school_storage_usage(self, school_id: UUID) -> Dict[str, Any]:
        """
        Get storage usage statistics for a school.
        """
        try:
            school_prefix = self._get_school_prefix(school_id)
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=school_prefix
            )
            
            total_size = 0
            file_count = 0
            category_usage = {}
            
            for obj in response.get('Contents', []):
                total_size += obj['Size']
                file_count += 1
                
                # Extract category from path
                path_parts = obj['Key'].split('/')
                if len(path_parts) > 2:
                    category = path_parts[2]
                    category_usage[category] = category_usage.get(category, 0) + obj['Size']
            
            return {
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_count': file_count,
                'category_breakdown': category_usage
            }
            
        except ClientError as e:
            logger.error(f"Storage usage error: {e}")
            return {'total_size_bytes': 0, 'total_size_mb': 0, 'file_count': 0}

# Global instance
file_storage = SchoolFileStorage()

# Convenience functions for common file types
async def upload_student_document(
    file: UploadFile,
    school_id: UUID,
    student_id: UUID
) -> Dict[str, Any]:
    """Upload student document with proper categorization"""
    return await file_storage.upload_file(
        file=file,
        school_id=school_id,
        category="students",
        subfolder=f"{student_id}/documents",
        allowed_types=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'],
        max_size_mb=10
    )

async def upload_student_photo(
    file: UploadFile,
    school_id: UUID,
    student_id: UUID
) -> Dict[str, Any]:
    """Upload student profile photo"""
    return await file_storage.upload_file(
        file=file,
        school_id=school_id,
        category="students",
        subfolder=f"{student_id}/photos",
        allowed_types=['jpg', 'jpeg', 'png'],
        max_size_mb=5
    )

async def upload_school_logo(
    file: UploadFile,
    school_id: UUID
) -> Dict[str, Any]:
    """Upload school logo/branding"""
    return await file_storage.upload_file(
        file=file,
        school_id=school_id,
        category="branding",
        subfolder="logos",
        allowed_types=['jpg', 'jpeg', 'png', 'svg'],
        max_size_mb=2
    )
```

---

## **📋 Phase 2: Frontend School Context (Weeks 3-4)**

### **Task 2.1: School Context Hook**

**File**: `frontend/src/hooks/useSchoolContext.ts`

```typescript
// =====================================================
// School Context Hook for Frontend Multitenancy
// File: frontend/src/hooks/useSchoolContext.ts
// =====================================================

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from './useAuth';
import { api } from '@/lib/api';

interface SchoolConfiguration {
  school_id: string;
  logo_url?: string;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  font_family: string;
  motto?: string;
  vision_statement?: string;
  mission_statement?: string;
  timezone: string;
  language_primary: string;
  language_secondary?: string;
  currency: string;
  date_format: string;
  features_enabled: Record<string, boolean>;
  subscription_tier: string;
  max_students: number;
  grading_system: Record<string, any>;
  notification_settings: Record<string, boolean>;
  student_id_format: string;
  academic_year_start_month: number;
  terms_per_year: number;
}

interface SchoolDomain {
  domain: string;
  is_primary: boolean;
  is_custom: boolean;
}

interface SchoolContext {
  school: {
    id: string;
    name: string;
    type: string;
    config: SchoolConfiguration;
    domains: SchoolDomain[];
  };
  branding: {
    logo_url?: string;
    primary_color: string;
    secondary_color: string;
    accent_color: string;
    font_family: string;
  };
  features: Record<string, boolean>;
  subscription: {
    tier: string;
    limits: {
      max_students: number;
      max_staff: number;
      storage_limit_gb: number;
    };
  };
  academic: {
    year_start_month: number;
    terms_per_year: number;
    grading_system: Record<string, any>;
  };
  regional: {
    timezone: string;
    currency: string;
    date_format: string;
    primary_language: string;
    secondary_language?: string;
  };
  // Utility functions
  hasFeature: (feature: string) => boolean;
  canAccess: (permission: string) => boolean;
  formatCurrency: (amount: number) => string;
  formatDate: (date: Date) => string;
  getGradeDisplay: (grade: number) => string;
}

export function useSchoolContext(): SchoolContext | null {
  const { user } = useAuth();
  
  const { data: schoolData } = useQuery({
    queryKey: ['school-context', user?.school_id],
    queryFn: async () => {
      if (!user?.school_id) return null;
      
      const response = await api.get(`/schools/${user.school_id}/context`);
      return response.data;
    },
    enabled: !!user?.school_id,
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 30 * 60 * 1000, // 30 minutes
  });

  if (!schoolData || !user) return null;

  return {
    school: {
      id: schoolData.id,
      name: schoolData.name,
      type: schoolData.type,
      config: schoolData.config,
      domains: schoolData.domains
    },
    branding: {
      logo_url: schoolData.config.logo_url,
      primary_color: schoolData.config.primary_color,
      secondary_color: schoolData.config.secondary_color,
      accent_color: schoolData.config.accent_color,
      font_family: schoolData.config.font_family
    },
    features: schoolData.config.features_enabled,
    subscription: {
      tier: schoolData.config.subscription_tier,
      limits: {
        max_students: schoolData.config.max_students,
        max_staff: 50, // This would come from config
        storage_limit_gb: 10 // This would come from config
      }
    },
    academic: {
      year_start_month: schoolData.config.academic_year_start_month,
      terms_per_year: schoolData.config.terms_per_year,
      grading_system: schoolData.config.grading_system
    },
    regional: {
      timezone: schoolData.config.timezone,
      currency: schoolData.config.currency,
      date_format: schoolData.config.date_format,
      primary_language: schoolData.config.language_primary,
      secondary_language: schoolData.config.language_secondary
    },
    hasFeature: (feature: string) => {
      return schoolData.config.features_enabled[feature] === true &&
             user.available_features.includes(feature);
    },
    canAccess: (permission: string) => {
      return user.permissions.includes('*') || user.permissions.includes(permission);
    },
    formatCurrency: (amount: number) => {
      const currency = schoolData.config.currency;
      return new Intl.NumberFormat('en-ZW', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2
      }).format(amount);
    },
    formatDate: (date: Date) => {
      const format = schoolData.config.date_format;
      const locale = schoolData.config.language_primary === 'en' ? 'en-ZW' : 'en-US';
      
      if (format === 'DD/MM/YYYY') {
        return date.toLocaleDateString(locale, {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric'
        });
      }
      
      return date.toLocaleDateString(locale);
    },
    getGradeDisplay: (grade: number) => {
      if (grade <= 7) return `Grade ${grade}`;
      if (grade === 12) return `Form 5 (Lower 6)`;
      if (grade === 13) return `Form 6 (Upper 6)`;
      return `Form ${grade - 6}`;
    }
  };
}

// Hook for feature-gated components
export function useFeatureAccess(feature: string) {
  const schoolContext = useSchoolContext();
  
  return {
    hasAccess: schoolContext?.hasFeature(feature) ?? false,
    tier: schoolContext?.subscription.tier ?? 'trial',
    upgradeRequired: !schoolContext?.hasFeature(feature)
  };
}

// Hook for permission-gated components
export function usePermissionAccess(permission: string) {
  const schoolContext = useSchoolContext();
  
  return {
    hasAccess: schoolContext?.canAccess(permission) ?? false,
    userRole: schoolContext?.school ? 'unknown' : 'guest'
  };
}
```

### **Task 2.2: School Theming Provider**

**File**: `frontend/src/components/providers/SchoolThemeProvider.tsx`

```typescript
// =====================================================
// School Theme Provider for Dynamic Branding
// File: frontend/src/components/providers/SchoolThemeProvider.tsx
// =====================================================

import React, { createContext, useContext, useEffect } from 'react';
import { useSchoolContext } from '@/hooks/useSchoolContext';

interface ThemeContextValue {
  primaryColor: string;
  secondaryColor: string;
  accentColor: string;
  fontFamily: string;
  logoUrl?: string;
  applyTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

interface SchoolThemeProviderProps {
  children: React.ReactNode;
}

export function SchoolThemeProvider({ children }: SchoolThemeProviderProps) {
  const schoolContext = useSchoolContext();

  const themeValue: ThemeContextValue = {
    primaryColor: schoolContext?.branding.primary_color ?? '#1e40af',
    secondaryColor: schoolContext?.branding.secondary_color ?? '#10b981',
    accentColor: schoolContext?.branding.accent_color ?? '#f59e0b',
    fontFamily: schoolContext?.branding.font_family ?? 'Inter',
    logoUrl: schoolContext?.branding.logo_url,
    applyTheme: () => {
      if (!schoolContext) return;

      const root = document.documentElement;
      
      // Apply CSS custom properties for dynamic theming
      root.style.setProperty('--color-primary', schoolContext.branding.primary_color);
      root.style.setProperty('--color-secondary', schoolContext.branding.secondary_color);
      root.style.setProperty('--color-accent', schoolContext.branding.accent_color);
      root.style.setProperty('--font-primary', schoolContext.branding.font_family);
      
      // Update favicon if available
      if (schoolContext.branding.logo_url) {
        const favicon = document.querySelector('link[rel="icon"]') as HTMLLinkElement;
        if (favicon) {
          favicon.href = schoolContext.branding.logo_url;
        }
      }
      
      // Update page title with school name
      document.title = `1Class - ${schoolContext.school.name}`;
    }
  };

  // Apply theme on mount and when school context changes
  useEffect(() => {
    themeValue.applyTheme();
  }, [schoolContext?.school.id]);

  return (
    <ThemeContext.Provider value={themeValue}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useSchoolTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useSchoolTheme must be used within SchoolThemeProvider');
  }
  return context;
}

// Component for displaying school logo
export function SchoolLogo({ className, fallback }: { className?: string; fallback?: React.ReactNode }) {
  const { logoUrl } = useSchoolTheme();
  const schoolContext = useSchoolContext();
  
  if (logoUrl) {
    return (
      <img
        src={logoUrl}
        alt={`${schoolContext?.school.name} logo`}
        className={className}
        onError={(e) => {
          // Hide image on error and show fallback
          (e.target as HTMLImageElement).style.display = 'none';
        }}
      />
    );
  }
  
  if (fallback) {
    return <>{fallback}</>;
  }
  
  // Default fallback - school initials
  const initials = schoolContext?.school.name
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 3) ?? '1C';
  
  return (
    <div className={`flex items-center justify-center bg-primary text-primary-foreground font-bold ${className}`}>
      {initials}
    </div>
  );
}
```

---

## **⏰ Timeline Summary**

### **Week 1-2: Core Infrastructure** ✅
- Enhanced database schema with school configuration
- Enhanced authentication with full school context  
- School-isolated file storage system

### **Week 3-4: Frontend Integration** 🔄
- School context hooks and providers
- Dynamic theming and branding
- Feature-gated components

### **Week 5-6: Testing & Optimization** 📋
- Multi-school testing environment
- Performance optimization
- Security audit

### **Week 7-8: Production Deployment** 🚀
- Production infrastructure setup
- School onboarding system
- Monitoring and analytics

**Result**: Enterprise-grade multitenancy ready for 500+ schools with complete isolation, branding, and feature management! 🏆