"""
API Documentation Schemas
Pydantic models for API documentation service
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class DocumentationFormat(str, Enum):
    """Supported documentation formats"""
    JSON = "json"
    YAML = "yaml"
    POSTMAN = "postman"
    MARKDOWN = "markdown"


class DocumentationStatus(str, Enum):
    """Documentation generation status"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentationConfigUpdate(BaseModel):
    """Configuration update for documentation generation"""
    title: Optional[str] = Field(None, description="API title")
    version: Optional[str] = Field(None, description="API version")
    description: Optional[str] = Field(None, description="API description")
    base_url: Optional[str] = Field(None, description="Base URL for API")
    contact_info: Optional[Dict[str, str]] = Field(None, description="Contact information")
    license_info: Optional[Dict[str, str]] = Field(None, description="License information")
    
    @validator('version')
    def validate_version(cls, v):
        if v and not v.replace('.', '').replace('-', '').isalnum():
            raise ValueError('Version must contain only alphanumeric characters, dots, and hyphens')
        return v


class DocumentationGenerationRequest(BaseModel):
    """Request for documentation generation"""
    format: DocumentationFormat = Field(..., description="Output format")
    include_examples: bool = Field(True, description="Include example responses")
    include_schemas: bool = Field(True, description="Include component schemas")
    include_security: bool = Field(True, description="Include security schemes")
    tags_filter: Optional[List[str]] = Field(None, description="Filter by specific tags")
    paths_filter: Optional[List[str]] = Field(None, description="Filter by specific paths")


class DocumentationGenerationResponse(BaseModel):
    """Response for documentation generation"""
    success: bool = Field(..., description="Generation success status")
    message: str = Field(..., description="Status message")
    format: DocumentationFormat = Field(..., description="Generated format")
    file_path: Optional[str] = Field(None, description="Path to generated file")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    generated_by: str = Field(..., description="User who generated the documentation")
    timestamp: datetime = Field(..., description="Generation timestamp")
    download_url: Optional[str] = Field(None, description="Download URL for the file")


class DocumentationStats(BaseModel):
    """API documentation statistics"""
    total_endpoints: int = Field(..., description="Total number of endpoints")
    methods_distribution: Dict[str, int] = Field(..., description="HTTP methods distribution")
    tags_distribution: Dict[str, int] = Field(..., description="Tags distribution")
    components: Dict[str, int] = Field(..., description="Component counts")
    api_info: Dict[str, Any] = Field(..., description="API information")
    generated_at: datetime = Field(..., description="Statistics generation timestamp")


class DocumentationHealth(BaseModel):
    """Documentation service health status"""
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    endpoints_documented: int = Field(..., description="Number of documented endpoints")
    available_formats: List[str] = Field(..., description="Available documentation formats")
    last_updated: str = Field(..., description="Last update timestamp")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class DocumentationExportRequest(BaseModel):
    """Request for documentation export"""
    format: DocumentationFormat = Field(..., description="Export format")
    include_metadata: bool = Field(True, description="Include metadata in export")
    compress: bool = Field(False, description="Compress the exported file")


class DocumentationExportResponse(BaseModel):
    """Response for documentation export"""
    filename: str = Field(..., description="Exported filename")
    content: str = Field(..., description="File content")
    content_type: str = Field(..., description="MIME content type")
    size: int = Field(..., description="File size in bytes")
    exported_by: str = Field(..., description="User who exported the documentation")
    timestamp: datetime = Field(..., description="Export timestamp")


class OpenAPIInfo(BaseModel):
    """OpenAPI info section"""
    title: str = Field(..., description="API title")
    version: str = Field(..., description="API version")
    description: str = Field(..., description="API description")
    terms_of_service: Optional[str] = Field(None, description="Terms of service URL")
    contact: Optional[Dict[str, str]] = Field(None, description="Contact information")
    license: Optional[Dict[str, str]] = Field(None, description="License information")


class OpenAPIServer(BaseModel):
    """OpenAPI server configuration"""
    url: str = Field(..., description="Server URL")
    description: str = Field(..., description="Server description")
    variables: Optional[Dict[str, Any]] = Field(None, description="Server variables")


class OpenAPITag(BaseModel):
    """OpenAPI tag definition"""
    name: str = Field(..., description="Tag name")
    description: str = Field(..., description="Tag description")
    external_docs: Optional[Dict[str, str]] = Field(None, description="External documentation")


class OpenAPISecurityScheme(BaseModel):
    """OpenAPI security scheme"""
    type: str = Field(..., description="Security scheme type")
    scheme: Optional[str] = Field(None, description="Security scheme")
    bearer_format: Optional[str] = Field(None, description="Bearer token format")
    description: Optional[str] = Field(None, description="Security scheme description")
    name: Optional[str] = Field(None, description="Security scheme name")
    in_location: Optional[str] = Field(None, alias="in", description="Location of the security parameter")
    flows: Optional[Dict[str, Any]] = Field(None, description="OAuth2 flows")


class OpenAPIExample(BaseModel):
    """OpenAPI example definition"""
    summary: str = Field(..., description="Example summary")
    description: Optional[str] = Field(None, description="Example description")
    value: Any = Field(..., description="Example value")
    external_value: Optional[str] = Field(None, description="External example URL")


class PostmanCollection(BaseModel):
    """Postman collection structure"""
    info: Dict[str, Any] = Field(..., description="Collection info")
    auth: Optional[Dict[str, Any]] = Field(None, description="Collection authentication")
    variable: List[Dict[str, Any]] = Field(default_factory=list, description="Collection variables")
    item: List[Dict[str, Any]] = Field(default_factory=list, description="Collection items")


class PostmanRequest(BaseModel):
    """Postman request structure"""
    name: str = Field(..., description="Request name")
    description: Optional[str] = Field(None, description="Request description")
    method: str = Field(..., description="HTTP method")
    url: Dict[str, Any] = Field(..., description="Request URL")
    header: List[Dict[str, Any]] = Field(default_factory=list, description="Request headers")
    body: Optional[Dict[str, Any]] = Field(None, description="Request body")
    auth: Optional[Dict[str, Any]] = Field(None, description="Request authentication")


class DocumentationRefreshResponse(BaseModel):
    """Response for documentation refresh"""
    success: bool = Field(..., description="Refresh success status")
    message: str = Field(..., description="Refresh message")
    endpoints_count: int = Field(..., description="Number of endpoints after refresh")
    refreshed_by: str = Field(..., description="User who refreshed the documentation")
    timestamp: datetime = Field(..., description="Refresh timestamp")


class DocumentationCacheInfo(BaseModel):
    """Documentation cache information"""
    cached: bool = Field(..., description="Whether documentation is cached")
    cache_size: int = Field(..., description="Cache size in bytes")
    cache_timestamp: Optional[datetime] = Field(None, description="Cache creation timestamp")
    cache_expires: Optional[datetime] = Field(None, description="Cache expiration timestamp")
    cache_hit_count: int = Field(0, description="Cache hit count")
    cache_miss_count: int = Field(0, description="Cache miss count")


class DocumentationError(BaseModel):
    """Documentation error response"""
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(..., description="Error timestamp")
    endpoint: Optional[str] = Field(None, description="Endpoint where error occurred")


class DocumentationMetrics(BaseModel):
    """Documentation usage metrics"""
    total_requests: int = Field(..., description="Total documentation requests")
    unique_visitors: int = Field(..., description="Unique visitors count")
    popular_endpoints: Dict[str, int] = Field(..., description="Most accessed endpoints")
    format_usage: Dict[str, int] = Field(..., description="Format usage statistics")
    error_rate: float = Field(..., description="Error rate percentage")
    average_response_time: float = Field(..., description="Average response time in milliseconds")
    last_updated: datetime = Field(..., description="Metrics last update time")


class SDKGenerationRequest(BaseModel):
    """Request for SDK generation"""
    language: str = Field(..., description="Programming language for SDK")
    package_name: str = Field(..., description="Package/module name")
    version: str = Field(..., description="SDK version")
    include_examples: bool = Field(True, description="Include usage examples")
    include_tests: bool = Field(True, description="Include test files")
    
    @validator('language')
    def validate_language(cls, v):
        supported_languages = ['python', 'javascript', 'typescript', 'php', 'java', 'csharp', 'go', 'ruby']
        if v.lower() not in supported_languages:
            raise ValueError(f'Language must be one of: {", ".join(supported_languages)}')
        return v.lower()


class SDKGenerationResponse(BaseModel):
    """Response for SDK generation"""
    success: bool = Field(..., description="Generation success status")
    message: str = Field(..., description="Generation message")
    language: str = Field(..., description="Generated SDK language")
    package_name: str = Field(..., description="Package name")
    version: str = Field(..., description="SDK version")
    download_url: str = Field(..., description="SDK download URL")
    file_size: int = Field(..., description="SDK file size in bytes")
    generated_by: str = Field(..., description="User who generated the SDK")
    timestamp: datetime = Field(..., description="Generation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Download URL expiration")


class DocumentationValidationResult(BaseModel):
    """Documentation validation result"""
    valid: bool = Field(..., description="Whether documentation is valid")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    score: float = Field(..., description="Documentation quality score (0-100)")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    validated_at: datetime = Field(..., description="Validation timestamp")
    validator_version: str = Field(..., description="Validator version used")