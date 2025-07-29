# =====================================================
# File Management Service
# Business logic for file operations and management
# File: backend/services/files/services.py
# =====================================================

import os
import uuid
import aiofiles
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List, BinaryIO, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
import logging
from PIL import Image
import magic
import mimetypes

from shared.models.platform_user import PlatformUserDB
from shared.models.platform import School
from .schemas import (
    FileMetadata, FileType, UploadPurpose, FileValidationResult,
    StorageQuotaInfo, ImageResizeRequest, BulkImportFileRequest
)

logger = logging.getLogger(__name__)

class FileService:
    """Service for file management operations"""
    
    def __init__(self):
        self.base_upload_path = Path(os.getenv("UPLOAD_PATH", "/tmp/uploads"))
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default
        self.allowed_extensions = {
            FileType.IMAGE: ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
            FileType.CSV: ['.csv'],
            FileType.EXCEL: ['.xlsx', '.xls'],
            FileType.PDF: ['.pdf'],
            FileType.DOCUMENT: ['.doc', '.docx', '.txt', '.rtf']
        }
        
        # Create upload directories
        self.base_upload_path.mkdir(parents=True, exist_ok=True)
        for purpose in UploadPurpose:
            (self.base_upload_path / purpose.value).mkdir(exist_ok=True)
    
    def validate_file(self, filename: str, content: bytes, upload_purpose: UploadPurpose) -> FileValidationResult:
        """Validate uploaded file"""
        errors = []
        warnings = []
        metadata = {}
        
        # Check file size
        if len(content) > self.max_file_size:
            errors.append(f"File size {len(content)} exceeds maximum {self.max_file_size} bytes")
        
        # Get file extension
        file_ext = Path(filename).suffix.lower()
        
        # Detect file type using magic
        try:
            file_mime = magic.from_buffer(content, mime=True)
            metadata['detected_mime_type'] = file_mime
        except Exception as e:
            warnings.append(f"Could not detect file type: {str(e)}")
            file_mime = mimetypes.guess_type(filename)[0]
        
        # Determine file type
        detected_file_type = self._get_file_type_from_mime(file_mime)
        
        if not detected_file_type:
            errors.append(f"Unsupported file type: {file_mime}")
            return FileValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                metadata=metadata
            )
        
        # Check allowed extensions for file type
        if file_ext not in self.allowed_extensions.get(detected_file_type, []):
            errors.append(f"File extension {file_ext} not allowed for {detected_file_type}")
        
        # Validate based on upload purpose
        purpose_validation = self._validate_for_purpose(
            detected_file_type, upload_purpose, content
        )
        errors.extend(purpose_validation.get('errors', []))
        warnings.extend(purpose_validation.get('warnings', []))
        metadata.update(purpose_validation.get('metadata', {}))
        
        # Special validation for images
        if detected_file_type == FileType.IMAGE:
            image_validation = self._validate_image(content)
            errors.extend(image_validation.get('errors', []))
            warnings.extend(image_validation.get('warnings', []))
            metadata.update(image_validation.get('metadata', {}))
        
        return FileValidationResult(
            is_valid=len(errors) == 0,
            file_type=detected_file_type,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )
    
    def _get_file_type_from_mime(self, mime_type: str) -> Optional[FileType]:
        """Get FileType from MIME type"""
        mime_mappings = {
            'image/': FileType.IMAGE,
            'text/csv': FileType.CSV,
            'application/vnd.ms-excel': FileType.EXCEL,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': FileType.EXCEL,
            'application/pdf': FileType.PDF,
            'application/msword': FileType.DOCUMENT,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': FileType.DOCUMENT,
            'text/plain': FileType.DOCUMENT,
            'text/rtf': FileType.DOCUMENT
        }
        
        for mime_prefix, file_type in mime_mappings.items():
            if mime_type.startswith(mime_prefix):
                return file_type
        
        return None
    
    def _validate_for_purpose(self, file_type: FileType, purpose: UploadPurpose, content: bytes) -> Dict[str, Any]:
        """Validate file for specific upload purpose"""
        errors = []
        warnings = []
        metadata = {}
        
        purpose_requirements = {
            UploadPurpose.PROFILE_IMAGE: [FileType.IMAGE],
            UploadPurpose.SCHOOL_LOGO: [FileType.IMAGE],
            UploadPurpose.BULK_IMPORT: [FileType.CSV, FileType.EXCEL],
            UploadPurpose.DOCUMENT: [FileType.PDF, FileType.DOCUMENT],
            UploadPurpose.ATTACHMENT: [FileType.IMAGE, FileType.PDF, FileType.DOCUMENT]
        }
        
        allowed_types = purpose_requirements.get(purpose, [])
        if file_type not in allowed_types:
            errors.append(f"File type {file_type} not allowed for {purpose}")
        
        # Size limits based on purpose
        size_limits = {
            UploadPurpose.PROFILE_IMAGE: 2 * 1024 * 1024,  # 2MB
            UploadPurpose.SCHOOL_LOGO: 1 * 1024 * 1024,    # 1MB
            UploadPurpose.BULK_IMPORT: 50 * 1024 * 1024,   # 50MB
            UploadPurpose.DOCUMENT: 25 * 1024 * 1024,      # 25MB
            UploadPurpose.ATTACHMENT: 10 * 1024 * 1024     # 10MB
        }
        
        max_size = size_limits.get(purpose, self.max_file_size)
        if len(content) > max_size:
            errors.append(f"File size exceeds {max_size} bytes limit for {purpose}")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'metadata': metadata
        }
    
    def _validate_image(self, content: bytes) -> Dict[str, Any]:
        """Validate image-specific requirements"""
        errors = []
        warnings = []
        metadata = {}
        
        try:
            from io import BytesIO
            image = Image.open(BytesIO(content))
            
            metadata['image_width'] = image.width
            metadata['image_height'] = image.height
            metadata['image_format'] = image.format
            metadata['image_mode'] = image.mode
            
            # Check dimensions
            max_dimensions = (4096, 4096)  # 4K max
            if image.width > max_dimensions[0] or image.height > max_dimensions[1]:
                warnings.append(f"Image dimensions {image.width}x{image.height} exceed recommended {max_dimensions}")
            
            # Check if image needs optimization
            if len(content) > 1024 * 1024:  # 1MB
                warnings.append("Large image file - consider optimizing")
            
        except Exception as e:
            errors.append(f"Invalid image file: {str(e)}")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'metadata': metadata
        }
    
    async def save_file(
        self,
        filename: str,
        content: bytes,
        upload_purpose: UploadPurpose,
        uploaded_by: uuid.UUID,
        school_id: Optional[uuid.UUID] = None,
        is_public: bool = False
    ) -> FileMetadata:
        """Save file to storage and return metadata"""
        
        # Generate unique filename
        file_id = uuid.uuid4()
        file_ext = Path(filename).suffix.lower()
        safe_filename = f"{file_id}{file_ext}"
        
        # Create storage path
        storage_dir = self.base_upload_path / upload_purpose.value
        if school_id:
            storage_dir = storage_dir / str(school_id)
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        storage_path = storage_dir / safe_filename
        
        # Calculate file hash
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Save file
        async with aiofiles.open(storage_path, 'wb') as f:
            await f.write(content)
        
        # Generate public URL if needed
        public_url = None
        if is_public:
            public_url = f"/api/v1/files/{file_id}/download"
        
        # Detect file type
        validation = self.validate_file(filename, content, upload_purpose)
        
        # Create metadata
        metadata = FileMetadata(
            filename=filename,
            file_size=len(content),
            content_type=mimetypes.guess_type(filename)[0] or 'application/octet-stream',
            file_type=validation.file_type or FileType.DOCUMENT,
            upload_purpose=upload_purpose,
            storage_path=str(storage_path),
            public_url=public_url,
            uploaded_by=uploaded_by,
            school_id=school_id,
            is_public=is_public,
            image_metadata=validation.metadata if validation.file_type == FileType.IMAGE else None,
            csv_metadata=validation.metadata if validation.file_type == FileType.CSV else None
        )
        
        logger.info(f"File saved: {filename} -> {storage_path}")
        return metadata
    
    async def resize_image(
        self,
        file_metadata: FileMetadata,
        resize_request: ImageResizeRequest
    ) -> FileMetadata:
        """Resize an image and return new file metadata"""
        
        if file_metadata.file_type != FileType.IMAGE:
            raise ValueError("Can only resize image files")
        
        # Load original image
        image = Image.open(file_metadata.storage_path)
        
        # Calculate new dimensions
        original_width, original_height = image.size
        new_width, new_height = self._calculate_resize_dimensions(
            original_width, original_height, resize_request
        )
        
        # Resize image
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save resized image
        file_id = uuid.uuid4()
        original_path = Path(file_metadata.storage_path)
        resized_filename = f"{file_id}_resized{original_path.suffix}"
        resized_path = original_path.parent / resized_filename
        
        # Save with quality setting
        save_kwargs = {}
        if resize_request.format:
            resized_path = resized_path.with_suffix(f".{resize_request.format}")
        if resize_request.quality and resized_path.suffix.lower() in ['.jpg', '.jpeg']:
            save_kwargs['quality'] = resize_request.quality
            save_kwargs['optimize'] = True
        
        resized_image.save(resized_path, **save_kwargs)
        
        # Get file size
        file_size = resized_path.stat().st_size
        
        # Create new metadata
        resized_metadata = FileMetadata(
            filename=f"resized_{file_metadata.filename}",
            file_size=file_size,
            content_type=file_metadata.content_type,
            file_type=FileType.IMAGE,
            upload_purpose=file_metadata.upload_purpose,
            storage_path=str(resized_path),
            public_url=f"/api/v1/files/{file_id}/download" if file_metadata.is_public else None,
            uploaded_by=file_metadata.uploaded_by,
            school_id=file_metadata.school_id,
            is_public=file_metadata.is_public,
            image_metadata={
                'image_width': new_width,
                'image_height': new_height,
                'image_format': resized_image.format,
                'image_mode': resized_image.mode,
                'original_file_id': str(file_metadata.uploaded_by)  # Using uploaded_by as file_id placeholder
            }
        )
        
        logger.info(f"Image resized: {original_width}x{original_height} -> {new_width}x{new_height}")
        return resized_metadata
    
    def _calculate_resize_dimensions(
        self,
        original_width: int,
        original_height: int,
        resize_request: ImageResizeRequest
    ) -> Tuple[int, int]:
        """Calculate new dimensions for image resize"""
        
        # Direct width/height specified
        if resize_request.width and resize_request.height:
            return resize_request.width, resize_request.height
        
        # Maintain aspect ratio with one dimension
        aspect_ratio = original_width / original_height
        
        if resize_request.width:
            return resize_request.width, int(resize_request.width / aspect_ratio)
        
        if resize_request.height:
            return int(resize_request.height * aspect_ratio), resize_request.height
        
        # Max dimensions - scale down if needed
        new_width, new_height = original_width, original_height
        
        if resize_request.max_width and new_width > resize_request.max_width:
            new_height = int(new_height * (resize_request.max_width / new_width))
            new_width = resize_request.max_width
        
        if resize_request.max_height and new_height > resize_request.max_height:
            new_width = int(new_width * (resize_request.max_height / new_height))
            new_height = resize_request.max_height
        
        return new_width, new_height
    
    async def get_storage_quota_info(
        self,
        db: AsyncSession,
        school_id: uuid.UUID
    ) -> StorageQuotaInfo:
        """Get storage quota information for a school"""
        
        # This would typically query a database table for file records
        # For now, calculate from filesystem
        school_upload_path = self.base_upload_path / "bulk_import" / str(school_id)
        
        total_quota = 1024 * 1024 * 1024  # 1GB default
        used_space = 0
        file_count = 0
        files_by_type = {}
        
        if school_upload_path.exists():
            for file_path in school_upload_path.rglob("*"):
                if file_path.is_file():
                    file_count += 1
                    file_size = file_path.stat().st_size
                    used_space += file_size
                    
                    # Count by file type
                    ext = file_path.suffix.lower()
                    files_by_type[ext] = files_by_type.get(ext, 0) + 1
        
        available_space = total_quota - used_space
        quota_percentage = (used_space / total_quota) * 100
        
        warnings = []
        if quota_percentage > 90:
            warnings.append("Storage quota almost full")
        elif quota_percentage > 75:
            warnings.append("Storage quota usage high")
        
        return StorageQuotaInfo(
            school_id=school_id,
            total_quota=total_quota,
            used_space=used_space,
            available_space=available_space,
            file_count=file_count,
            quota_percentage=quota_percentage,
            files_by_type=files_by_type,
            storage_warnings=warnings
        )
    
    async def delete_file(self, file_path: str, permanent: bool = False) -> bool:
        """Delete a file from storage"""
        try:
            file_path_obj = Path(file_path)
            
            if permanent:
                # Permanently delete
                if file_path_obj.exists():
                    file_path_obj.unlink()
                    logger.info(f"File permanently deleted: {file_path}")
                    return True
            else:
                # Soft delete - move to trash
                trash_dir = self.base_upload_path / ".trash"
                trash_dir.mkdir(exist_ok=True)
                
                if file_path_obj.exists():
                    trash_path = trash_dir / f"{uuid.uuid4()}_{file_path_obj.name}"
                    file_path_obj.rename(trash_path)
                    logger.info(f"File moved to trash: {file_path} -> {trash_path}")
                    return True
            
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return False
        
        return False
    
    def generate_secure_url(
        self,
        file_id: uuid.UUID,
        expires_in: timedelta = timedelta(hours=1)
    ) -> str:
        """Generate a secure, time-limited URL for file access"""
        import hmac
        import base64
        
        expires_at = int((datetime.utcnow() + expires_in).timestamp())
        secret_key = os.getenv("FILE_ACCESS_SECRET", "change-this-secret")
        
        # Create signature
        message = f"{file_id}:{expires_at}"
        signature = hmac.new(
            secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).decode()
        
        return f"/api/v1/files/{file_id}/download?expires={expires_at}&signature={signature_b64}"