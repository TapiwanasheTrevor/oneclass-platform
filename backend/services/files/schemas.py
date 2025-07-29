# =====================================================
# File Service Schemas
# Pydantic models for file upload requests and responses
# File: backend/services/files/schemas.py
# =====================================================

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from enum import Enum

class FileType(str, Enum):
    """Supported file types"""
    IMAGE = "image"
    CSV = "csv"
    EXCEL = "excel" 
    PDF = "pdf"
    DOCUMENT = "document"

class UploadPurpose(str, Enum):
    """File upload purposes"""
    PROFILE_IMAGE = "profile_image"
    SCHOOL_LOGO = "school_logo"
    BULK_IMPORT = "bulk_import"
    DOCUMENT = "document"
    ATTACHMENT = "attachment"

class FileMetadata(BaseModel):
    """File metadata information"""
    filename: str
    file_size: int
    content_type: str
    file_type: FileType
    upload_purpose: UploadPurpose
    
    # File processing info
    is_processed: bool = False
    processing_status: str = "pending"  # pending, processing, completed, failed
    processing_errors: List[str] = Field(default_factory=list)
    
    # Storage info
    storage_path: str
    public_url: Optional[str] = None
    
    # Security
    is_public: bool = False
    access_permissions: List[str] = Field(default_factory=list)
    
    # Metadata
    uploaded_by: UUID
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    school_id: Optional[UUID] = None
    
    # File-specific metadata
    image_metadata: Optional[Dict[str, Any]] = None
    csv_metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }

class FileUploadRequest(BaseModel):
    """File upload request"""
    upload_purpose: UploadPurpose
    school_id: Optional[UUID] = None
    is_public: bool = False
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class FileUploadResponse(BaseModel):
    """File upload response"""
    file_id: str
    filename: str
    file_size: int
    content_type: str
    file_type: FileType
    upload_purpose: UploadPurpose
    storage_path: str
    public_url: Optional[str] = None
    processing_status: str
    uploaded_at: str

class BulkImportFileRequest(BaseModel):
    """Bulk import file upload request"""
    school_id: UUID
    import_type: str  # users, students, staff
    file_format: str  # csv, excel
    has_header: bool = True
    delimiter: str = ","  # For CSV files
    mapping: Optional[Dict[str, str]] = None  # Column mapping
    dry_run: bool = False  # Validate only, don't import

class BulkImportProgress(BaseModel):
    """Bulk import progress tracking"""
    import_id: str
    status: str  # uploading, processing, validating, importing, completed, failed
    total_records: int
    processed_records: int
    successful_records: int
    failed_records: int
    progress_percentage: float
    errors: List[Dict[str, str]]
    warnings: List[Dict[str, str]]
    estimated_completion: Optional[datetime] = None
    
class BulkImportResponse(BaseModel):
    """Bulk import response"""
    import_id: str
    file_id: str
    status: str
    total_records: int
    validation_results: Optional[Dict[str, Any]] = None
    preview_data: Optional[List[Dict[str, Any]]] = None
    mapping_suggestions: Optional[Dict[str, str]] = None
    processing_started_at: str

class FileListRequest(BaseModel):
    """File list request with filters"""
    school_id: Optional[UUID] = None
    file_type: Optional[FileType] = None
    upload_purpose: Optional[UploadPurpose] = None
    uploaded_by: Optional[UUID] = None
    is_public: Optional[bool] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    search: Optional[str] = None

class FileListResponse(BaseModel):
    """File list response"""
    files: List[FileMetadata]
    total: int
    limit: int
    offset: int

class ImageResizeRequest(BaseModel):
    """Image resize request"""
    width: Optional[int] = None
    height: Optional[int] = None
    max_width: Optional[int] = None
    max_height: Optional[int] = None
    quality: int = Field(default=85, ge=1, le=100)
    format: Optional[str] = None  # jpeg, png, webp

class ImageResizeResponse(BaseModel):
    """Image resize response"""
    resized_file_id: str
    original_file_id: str
    width: int
    height: int
    file_size: int
    public_url: Optional[str] = None

class FileDownloadRequest(BaseModel):
    """File download request"""
    file_id: UUID
    download_as_attachment: bool = False
    thumbnail: bool = False  # For images
    
class FileDeleteRequest(BaseModel):
    """File deletion request"""
    file_ids: List[UUID]
    permanent: bool = False  # Soft delete by default

class FileShareRequest(BaseModel):
    """File sharing request"""
    file_id: UUID
    share_with: List[UUID]  # User IDs
    permissions: List[str] = Field(default_factory=lambda: ["view"])  # view, download, edit
    expires_at: Optional[datetime] = None
    message: Optional[str] = None

class FileShareResponse(BaseModel):
    """File sharing response"""
    share_id: str
    file_id: str
    shared_with: List[str]
    permissions: List[str]
    share_url: str
    expires_at: Optional[str] = None

class StorageQuotaInfo(BaseModel):
    """Storage quota information"""
    school_id: UUID
    total_quota: int  # bytes
    used_space: int   # bytes
    available_space: int  # bytes
    file_count: int
    quota_percentage: float
    files_by_type: Dict[str, int]
    storage_warnings: List[str] = Field(default_factory=list)

class FileValidationResult(BaseModel):
    """File validation result"""
    is_valid: bool
    file_type: Optional[FileType] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BulkImportMapping(BaseModel):
    """Column mapping for bulk imports"""
    source_column: str
    target_field: str
    data_type: str  # string, integer, date, email, etc.
    required: bool = False
    default_value: Optional[str] = None
    validation_rules: List[str] = Field(default_factory=list)

class BulkImportTemplate(BaseModel):
    """Template for bulk imports"""
    import_type: str
    template_name: str
    required_columns: List[str]
    optional_columns: List[str]
    column_descriptions: Dict[str, str]
    example_data: List[Dict[str, str]]
    validation_rules: Dict[str, List[str]]

class ProcessingJobStatus(BaseModel):
    """File processing job status"""
    job_id: str
    file_id: str
    job_type: str  # resize, convert, import, etc.
    status: str   # queued, processing, completed, failed
    progress: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None