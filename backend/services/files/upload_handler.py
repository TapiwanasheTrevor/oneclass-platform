# =====================================================
# File Upload Handler
# Utilities for handling file uploads and processing
# File: backend/services/files/upload_handler.py
# =====================================================

import asyncio
import aiofiles
import tempfile
import uuid
from pathlib import Path
from typing import BinaryIO, Optional, Dict, Any, List
from datetime import datetime
import logging
from PIL import Image
import io

from .schemas import FileType, UploadPurpose, FileValidationResult

logger = logging.getLogger(__name__)

class FileUploadHandler:
    """Handle file upload processing and validation"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "oneclass_uploads"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Image processing settings
        self.image_quality_settings = {
            UploadPurpose.PROFILE_IMAGE: {
                'max_width': 512,
                'max_height': 512,
                'quality': 85,
                'format': 'JPEG'
            },
            UploadPurpose.SCHOOL_LOGO: {
                'max_width': 256,
                'max_height': 256,
                'quality': 90,
                'format': 'PNG'
            }
        }
    
    async def process_upload(
        self,
        file_content: bytes,
        filename: str,
        upload_purpose: UploadPurpose
    ) -> Dict[str, Any]:
        """Process uploaded file and return processing results"""
        
        result = {
            'success': False,
            'original_size': len(file_content),
            'processed_files': [],
            'errors': [],
            'warnings': []
        }
        
        try:
            # Save original file temporarily
            temp_file_path = await self._save_temp_file(file_content, filename)
            
            result['processed_files'].append({
                'type': 'original',
                'path': str(temp_file_path),
                'size': len(file_content)
            })
            
            # Process based on file type and purpose
            file_ext = Path(filename).suffix.lower()
            
            if upload_purpose in [UploadPurpose.PROFILE_IMAGE, UploadPurpose.SCHOOL_LOGO]:
                image_results = await self._process_image(
                    file_content, filename, upload_purpose
                )
                result['processed_files'].extend(image_results['files'])
                result['warnings'].extend(image_results['warnings'])
            
            elif upload_purpose == UploadPurpose.BULK_IMPORT:
                import_results = await self._process_import_file(
                    file_content, filename
                )
                result['processed_files'].extend(import_results['files'])
                result['warnings'].extend(import_results['warnings'])
            
            result['success'] = True
            
        except Exception as e:
            logger.error(f"Upload processing error: {str(e)}")
            result['errors'].append(str(e))
        
        return result
    
    async def _save_temp_file(self, content: bytes, filename: str) -> Path:
        """Save file content to temporary location"""
        
        temp_id = uuid.uuid4()
        file_ext = Path(filename).suffix
        temp_filename = f"{temp_id}{file_ext}"
        temp_path = self.temp_dir / temp_filename
        
        async with aiofiles.open(temp_path, 'wb') as f:
            await f.write(content)
        
        return temp_path
    
    async def _process_image(
        self,
        content: bytes,
        filename: str,
        upload_purpose: UploadPurpose
    ) -> Dict[str, Any]:
        """Process image uploads with optimization and resizing"""
        
        result = {
            'files': [],
            'warnings': []
        }
        
        try:
            # Load image
            image = Image.open(io.BytesIO(content))
            original_format = image.format
            
            # Get processing settings
            settings = self.image_quality_settings.get(upload_purpose, {})
            
            # Create optimized version
            processed_image = image.copy()
            
            # Resize if needed
            max_width = settings.get('max_width')
            max_height = settings.get('max_height')
            
            if max_width or max_height:
                processed_image = self._resize_image_proportional(
                    processed_image, max_width, max_height
                )
            
            # Convert format if needed
            target_format = settings.get('format', original_format)
            if target_format != original_format:
                if target_format == 'JPEG' and processed_image.mode in ('RGBA', 'LA', 'P'):
                    # Convert to RGB for JPEG
                    background = Image.new('RGB', processed_image.size, (255, 255, 255))
                    background.paste(processed_image, mask=processed_image.split()[-1] if 'A' in processed_image.mode else None)
                    processed_image = background
            
            # Save optimized version
            optimized_path = await self._save_optimized_image(
                processed_image, filename, target_format, settings.get('quality', 85)
            )
            
            result['files'].append({
                'type': 'optimized',
                'path': str(optimized_path),
                'size': optimized_path.stat().st_size,
                'width': processed_image.width,
                'height': processed_image.height,
                'format': target_format
            })
            
            # Create thumbnail for profile images
            if upload_purpose == UploadPurpose.PROFILE_IMAGE:
                thumbnail = self._create_thumbnail(processed_image, 128, 128)
                thumbnail_path = await self._save_optimized_image(
                    thumbnail, f"thumb_{filename}", target_format, 80
                )
                
                result['files'].append({
                    'type': 'thumbnail',
                    'path': str(thumbnail_path),
                    'size': thumbnail_path.stat().st_size,
                    'width': thumbnail.width,
                    'height': thumbnail.height,
                    'format': target_format
                })
            
            # Add warnings for large files
            if len(content) > 1024 * 1024:  # 1MB
                result['warnings'].append("Large image file - optimized version created")
            
        except Exception as e:
            logger.error(f"Image processing error: {str(e)}")
            raise
        
        return result
    
    def _resize_image_proportional(
        self,
        image: Image.Image,
        max_width: Optional[int],
        max_height: Optional[int]
    ) -> Image.Image:
        """Resize image while maintaining aspect ratio"""
        
        original_width, original_height = image.size
        
        # Calculate new dimensions
        if max_width and max_height:
            ratio = min(max_width / original_width, max_height / original_height)
        elif max_width:
            ratio = max_width / original_width
        elif max_height:
            ratio = max_height / original_height
        else:
            return image
        
        # Only resize if image is larger than target
        if ratio < 1:
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return image
    
    def _create_thumbnail(self, image: Image.Image, width: int, height: int) -> Image.Image:
        """Create square thumbnail with cropping"""
        
        # Calculate crop box for center square
        original_width, original_height = image.size
        
        if original_width == original_height:
            # Already square
            cropped = image
        elif original_width > original_height:
            # Landscape - crop width
            left = (original_width - original_height) // 2
            cropped = image.crop((left, 0, left + original_height, original_height))
        else:
            # Portrait - crop height
            top = (original_height - original_width) // 2
            cropped = image.crop((0, top, original_width, top + original_width))
        
        # Resize to target dimensions
        return cropped.resize((width, height), Image.Resampling.LANCZOS)
    
    async def _save_optimized_image(
        self,
        image: Image.Image,
        filename: str,
        format: str,
        quality: int
    ) -> Path:
        """Save optimized image to temporary location"""
        
        temp_id = uuid.uuid4()
        file_ext = f".{format.lower()}" if format.lower() != 'jpeg' else '.jpg'
        temp_filename = f"{temp_id}_opt{file_ext}"
        temp_path = self.temp_dir / temp_filename
        
        # Save with optimization
        save_kwargs = {}
        if format.upper() in ['JPEG', 'JPG']:
            save_kwargs.update({
                'quality': quality,
                'optimize': True,
                'progressive': True
            })
        elif format.upper() == 'PNG':
            save_kwargs.update({
                'optimize': True,
                'compress_level': 6
            })
        
        image.save(temp_path, format=format.upper(), **save_kwargs)
        return temp_path
    
    async def _process_import_file(
        self,
        content: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """Process bulk import files for validation"""
        
        result = {
            'files': [],
            'warnings': []
        }
        
        try:
            # For CSV/Excel files, we mainly validate structure
            file_ext = Path(filename).suffix.lower()
            
            if file_ext == '.csv':
                # Basic CSV validation
                content_str = content.decode('utf-8')
                lines = content_str.split('\n')
                
                if len(lines) < 2:
                    result['warnings'].append("CSV file appears to have no data rows")
                
                # Check for common issues
                first_line = lines[0] if lines else ""
                if ',' not in first_line and ';' not in first_line:
                    result['warnings'].append("CSV file may not be properly delimited")
                
            elif file_ext in ['.xlsx', '.xls']:
                # For Excel files, we'd need to use pandas or openpyxl
                # For now, just basic size check
                if len(content) > 50 * 1024 * 1024:  # 50MB
                    result['warnings'].append("Large Excel file - processing may take time")
            
            result['files'].append({
                'type': 'validated',
                'path': filename,
                'size': len(content),
                'format': file_ext[1:].upper()
            })
            
        except Exception as e:
            logger.error(f"Import file processing error: {str(e)}")
            raise
        
        return result
    
    async def cleanup_temp_files(self, max_age_hours: int = 24):
        """Clean up old temporary files"""
        
        try:
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
            
            for file_path in self.temp_dir.iterdir():
                if file_path.is_file():
                    file_age = file_path.stat().st_mtime
                    if file_age < cutoff_time:
                        file_path.unlink()
                        logger.debug(f"Cleaned up temp file: {file_path}")
            
        except Exception as e:
            logger.error(f"Temp file cleanup error: {str(e)}")
    
    def validate_file_security(self, content: bytes, filename: str) -> List[str]:
        """Perform security validation on uploaded files"""
        
        warnings = []
        
        # Check for suspicious file extensions
        suspicious_extensions = ['.exe', '.bat', '.cmd', '.scr', '.com', '.pif']
        file_ext = Path(filename).suffix.lower()
        
        if file_ext in suspicious_extensions:
            warnings.append(f"Potentially dangerous file extension: {file_ext}")
        
        # Check for embedded executables in content
        executable_signatures = [
            b'MZ',  # Windows executable
            b'PK',  # ZIP/Office documents (could contain macros)
        ]
        
        for signature in executable_signatures:
            if content.startswith(signature):
                if file_ext not in ['.zip', '.xlsx', '.docx', '.pptx']:
                    warnings.append("File contains executable signature")
                break
        
        # Check file size limits
        if len(content) > 100 * 1024 * 1024:  # 100MB
            warnings.append("Very large file - may impact performance")
        
        return warnings
    
    async def scan_for_viruses(self, file_path: str) -> Dict[str, Any]:
        """Scan file for viruses (placeholder for integration with antivirus)"""
        
        # In production, integrate with ClamAV or similar
        return {
            'clean': True,
            'threats_found': [],
            'scan_date': datetime.utcnow().isoformat()
        }