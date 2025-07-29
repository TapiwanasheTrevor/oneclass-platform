# =====================================================
# Enhanced File Storage with Complete School Isolation
# Implements multitenancy enhancement plan requirements
# File: backend/shared/file_storage.py
# =====================================================

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    # For testing without boto3
    boto3 = None
    class ClientError(Exception):
        pass
from typing import Optional, Dict, Any, List
from uuid import UUID
import os
import logging
from datetime import datetime, timedelta
from fastapi import UploadFile, HTTPException, status
import mimetypes
from pathlib import Path

logger = logging.getLogger(__name__)

class SchoolFileStorage:
    """
    School-isolated file storage system with S3 backend.
    Provides complete isolation between schools with proper access control.
    """
    
    def __init__(self):
        if boto3:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
        else:
            self.s3_client = None
        self.bucket_name = os.getenv('AWS_S3_BUCKET', 'oneclass-files')
        self.cdn_base_url = os.getenv('CDN_BASE_URL', '')
        
        # Local storage fallback for development
        self.use_local_storage = os.getenv('USE_LOCAL_STORAGE', 'true').lower() == 'true'
        self.local_storage_path = os.getenv('LOCAL_STORAGE_PATH', './storage')
        
        if self.use_local_storage:
            # Create local storage directory
            os.makedirs(self.local_storage_path, exist_ok=True)
            logger.info(f"Using local file storage at: {self.local_storage_path}")
    
    def _get_school_prefix(self, school_id: UUID) -> str:
        """Get S3 prefix for school isolation"""
        return f"schools/{school_id}"
    
    def _get_file_path(self, school_id: UUID, category: str, file_name: str) -> str:
        """Generate full file path with proper isolation"""
        school_prefix = self._get_school_prefix(school_id)
        timestamp = datetime.now().strftime('%Y/%m')
        return f"{school_prefix}/{category}/{timestamp}/{file_name}"
    
    def _get_local_file_path(self, file_path: str) -> str:
        """Get local file system path"""
        return os.path.join(self.local_storage_path, file_path)
    
    def _validate_file_type(self, file: UploadFile, allowed_types: List[str]) -> bool:
        """Validate file type against allowed types"""
        if not allowed_types:
            return True
        
        file_ext = file.filename.split('.')[-1].lower() if file.filename else ''
        return file_ext in allowed_types
    
    def _validate_file_size(self, file: UploadFile, max_size_mb: int) -> bool:
        """Validate file size"""
        if not file.size:
            return True
        return file.size <= max_size_mb * 1024 * 1024
    
    def _generate_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename with timestamp"""
        if not original_filename:
            original_filename = "untitled"
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name_parts = original_filename.rsplit('.', 1)
        
        if len(name_parts) == 2:
            name, ext = name_parts
            return f"{timestamp}_{name}.{ext}"
        else:
            return f"{timestamp}_{original_filename}"
    
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
            if not self._validate_file_type(file, allowed_types):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type not allowed. Allowed: {', '.join(allowed_types or [])}"
                )
            
            # Validate file size
            if not self._validate_file_size(file, max_size_mb):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File too large. Maximum size: {max_size_mb}MB"
                )
            
            # Generate unique file name
            unique_filename = self._generate_unique_filename(file.filename)
            
            # Build file path with school isolation
            if subfolder:
                file_path = self._get_file_path(school_id, f"{category}/{subfolder}", unique_filename)
            else:
                file_path = self._get_file_path(school_id, category, unique_filename)
            
            # Read file content
            file_content = await file.read()
            
            # Determine content type
            content_type = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
            
            file_url = ""
            
            if self.use_local_storage:
                # Local storage implementation
                local_file_path = self._get_local_file_path(file_path)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                
                # Write file
                with open(local_file_path, 'wb') as f:
                    f.write(file_content)
                
                file_url = f"/api/v1/files/{file_path}"
                
            else:
                # S3 storage implementation
                upload_response = self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=file_path,
                    Body=file_content,
                    ContentType=content_type,
                    Metadata={
                        'school_id': str(school_id),
                        'category': category,
                        'original_filename': file.filename or 'untitled',
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
                'file_size': len(file_content),
                'file_type': content_type,
                'original_filename': file.filename,
                'upload_timestamp': datetime.now().isoformat()
            }
            
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="File upload failed"
            )
        except Exception as e:
            logger.error(f"File upload error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="File upload failed"
            )
    
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
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot delete file from another school"
                )
            
            if self.use_local_storage:
                # Local storage implementation
                local_file_path = self._get_local_file_path(file_path)
                
                if os.path.exists(local_file_path):
                    os.remove(local_file_path)
                    
                    # Remove empty directories
                    try:
                        os.rmdir(os.path.dirname(local_file_path))
                    except OSError:
                        pass  # Directory not empty
                        
            else:
                # S3 storage implementation
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
    
    async def get_file_url(
        self,
        file_path: str,
        school_id: UUID,
        expiration: int = 3600
    ) -> str:
        """
        Generate secure file access URL.
        Verifies school ownership before generating URL.
        """
        try:
            # Verify file belongs to school
            school_prefix = self._get_school_prefix(school_id)
            if not file_path.startswith(school_prefix):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot access file from another school"
                )
            
            if self.use_local_storage:
                # For local storage, return the API endpoint
                return f"/api/v1/files/{file_path}"
            else:
                # Generate presigned URL for S3
                presigned_url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': file_path},
                    ExpiresIn=expiration
                )
                return presigned_url
                
        except ClientError as e:
            logger.error(f"File URL generation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate file access URL"
            )
    
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
            
            files = []
            
            if self.use_local_storage:
                # Local storage implementation
                local_prefix_path = self._get_local_file_path(prefix)
                
                if os.path.exists(local_prefix_path):
                    for root, dirs, file_names in os.walk(local_prefix_path):
                        for file_name in file_names:
                            file_path = os.path.join(root, file_name)
                            relative_path = os.path.relpath(file_path, self.local_storage_path)
                            
                            stat = os.stat(file_path)
                            files.append({
                                'file_path': relative_path.replace(os.sep, '/'),
                                'file_size': stat.st_size,
                                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                'file_url': f"/api/v1/files/{relative_path.replace(os.sep, '/')}"
                            })
                            
                            if len(files) >= limit:
                                break
                        
                        if len(files) >= limit:
                            break
            else:
                # S3 storage implementation
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix,
                    MaxKeys=limit
                )
                
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
        except Exception as e:
            logger.error(f"List files error: {e}")
            return []
    
    async def get_school_storage_usage(self, school_id: UUID) -> Dict[str, Any]:
        """
        Get storage usage statistics for a school.
        """
        try:
            school_prefix = self._get_school_prefix(school_id)
            
            total_size = 0
            file_count = 0
            category_usage = {}
            
            if self.use_local_storage:
                # Local storage implementation
                local_prefix_path = self._get_local_file_path(school_prefix)
                
                if os.path.exists(local_prefix_path):
                    for root, dirs, file_names in os.walk(local_prefix_path):
                        for file_name in file_names:
                            file_path = os.path.join(root, file_name)
                            size = os.path.getsize(file_path)
                            total_size += size
                            file_count += 1
                            
                            # Extract category from path
                            relative_path = os.path.relpath(file_path, local_prefix_path)
                            path_parts = relative_path.split(os.sep)
                            if len(path_parts) > 0:
                                category = path_parts[0]
                                category_usage[category] = category_usage.get(category, 0) + size
            else:
                # S3 storage implementation
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=school_prefix
                )
                
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
        except Exception as e:
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

async def upload_report_document(
    file: UploadFile,
    school_id: UUID,
    report_type: str
) -> Dict[str, Any]:
    """Upload report document"""
    return await file_storage.upload_file(
        file=file,
        school_id=school_id,
        category="reports",
        subfolder=report_type,
        allowed_types=['pdf', 'xlsx', 'csv'],
        max_size_mb=50
    )

# Additional convenience functions for SIS module compatibility
async def upload_file_to_s3(
    file: UploadFile,
    school_id: UUID,
    category: str = "documents",
    subfolder: str = ""
) -> Dict[str, Any]:
    """Upload file to S3 (compatibility function)"""
    return await file_storage.upload_file(
        file=file,
        school_id=school_id,
        category=category,
        subfolder=subfolder
    )

def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
    """Validate file type based on extension"""
    if not filename:
        return False

    file_extension = filename.lower().split('.')[-1]
    return file_extension in [ext.lower() for ext in allowed_types]