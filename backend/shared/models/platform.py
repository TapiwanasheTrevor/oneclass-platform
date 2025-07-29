"""
Platform Models
Database models for platform-level entities (schools, users, configurations)
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class School(Base):
    """School model for multi-tenant setup"""
    __tablename__ = "schools"
    __table_args__ = {"schema": "platform"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    subdomain = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(20), default="active")  # active, inactive, suspended
    subscription_tier = Column(String(20), default="basic")  # basic, professional, enterprise
    
    # Contact information
    email = Column(String(255))
    phone = Column(String(20))
    address = Column(Text)
    
    # School details
    school_type = Column(String(50))  # primary, secondary, combined, technical
    establishment_year = Column(Integer)
    student_capacity = Column(Integer)
    
    # Configuration (JSON field)
    configuration = Column(JSON, default={})
    
    # Flags
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<School(id={self.id}, name='{self.name}', subdomain='{self.subdomain}')>"

# User model removed - now using consolidated PlatformUser model
# See: backend/shared/models/platform_user.py

class SchoolConfiguration(Base):
    """School-specific configuration and branding"""
    __tablename__ = "school_configurations"
    __table_args__ = {"schema": "platform"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    
    # Branding
    logo_url = Column(String(500))
    favicon_url = Column(String(500))
    primary_color = Column(String(7), default="#2563eb")  # Hex color
    secondary_color = Column(String(7), default="#64748b")
    background_color = Column(String(7), default="#ffffff")
    font_family = Column(String(100), default="Inter")
    theme = Column(String(20), default="light")  # light, dark
    
    # Feature configuration
    enabled_modules = Column(JSON, default=[])
    feature_flags = Column(JSON, default={})
    integrations = Column(JSON, default={})
    
    # Academic settings
    academic_year_start = Column(String(10))  # MM-DD format
    term_system = Column(String(20), default="three_term")  # three_term, semester, quarter
    grade_system = Column(String(20), default="zimbabwe")  # zimbabwe, cambridge, ib
    
    # Localization
    timezone = Column(String(50), default="Africa/Harare")
    language = Column(String(10), default="en")
    currency = Column(String(3), default="ZWL")
    
    # Contact and social
    website_url = Column(String(500))
    social_links = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SchoolConfiguration(id={self.id}, school_id={self.school_id})>"

class SchoolDomain(Base):
    """Custom domains for schools"""
    __tablename__ = "school_domains"
    __table_args__ = {"schema": "platform"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    domain = Column(String(255), unique=True, nullable=False)  # custom.domain.com
    subdomain = Column(String(50), nullable=False)  # links to school.subdomain
    
    # SSL/TLS
    ssl_enabled = Column(Boolean, default=False)
    ssl_certificate = Column(Text)  # Certificate data or reference
    
    # Verification
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255))
    verification_method = Column(String(50))  # dns, file, email
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    verified_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<SchoolDomain(id={self.id}, domain='{self.domain}', subdomain='{self.subdomain}')>"

class SchoolFeatureUsage(Base):
    """Track feature usage for analytics and billing"""
    __tablename__ = "school_feature_usage"
    __table_args__ = {"schema": "platform"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    feature_name = Column(String(100), nullable=False)
    module_name = Column(String(100), nullable=False)
    usage_type = Column(String(50), nullable=False)  # api_call, page_view, action, storage
    
    # Usage data
    count = Column(Integer, default=1)
    usage_metadata = Column(JSON, default={})
    
    # User context
    user_id = Column(UUID(as_uuid=True))
    user_role = Column(String(50))
    
    # Timestamps
    usage_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SchoolFeatureUsage(school_id={self.school_id}, feature='{self.feature_name}')>"