# =====================================================
# File Management Service Module
# Handle file uploads, storage, and processing
# File: backend/services/files/__init__.py
# =====================================================

from .routes import router
from .services import FileService
from .upload_handler import FileUploadHandler
from .bulk_processor import BulkImportProcessor
from .schemas import FileUploadResponse, BulkImportResponse, FileMetadata

__all__ = [
    "router",
    "FileService",
    "FileUploadHandler", 
    "BulkImportProcessor",
    "FileUploadResponse",
    "BulkImportResponse",
    "FileMetadata"
]