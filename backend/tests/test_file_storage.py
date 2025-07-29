"""
Tests for School-Isolated File Storage System
"""
import pytest
import os
import tempfile
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi import UploadFile, HTTPException
from io import BytesIO

# Mock boto3 before importing file_storage
import sys
from unittest.mock import MagicMock

# Create a proper mock for ClientError that inherits from Exception
class MockClientError(Exception):
    pass

mock_botocore_exceptions = MagicMock()
mock_botocore_exceptions.ClientError = MockClientError

sys.modules['boto3'] = MagicMock()
sys.modules['botocore'] = MagicMock()
sys.modules['botocore.exceptions'] = mock_botocore_exceptions

from shared.file_storage import (
    SchoolFileStorage,
    file_storage,
    upload_student_document,
    upload_student_photo,
    upload_school_logo,
    upload_report_document
)


class TestSchoolFileStorage:
    """Test SchoolFileStorage class"""
    
    @pytest.fixture
    def storage(self):
        """Create storage instance with local storage"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = SchoolFileStorage()
            storage.use_local_storage = True
            storage.local_storage_path = temp_dir
            yield storage
    
    @pytest.fixture
    def mock_file(self):
        """Create mock upload file"""
        file_content = b"Test file content"
        file = Mock(spec=UploadFile)
        file.filename = "test_document.pdf"
        file.content_type = "application/pdf"
        file.size = len(file_content)
        file.read = AsyncMock(return_value=file_content)
        return file
    
    def test_get_school_prefix(self, storage):
        """Test school prefix generation"""
        school_id = uuid4()
        prefix = storage._get_school_prefix(school_id)
        assert prefix == f"schools/{school_id}"
    
    def test_get_file_path(self, storage):
        """Test file path generation"""
        school_id = uuid4()
        category = "documents"
        filename = "test.pdf"
        
        with patch('shared.file_storage.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '2024/01'
            
            path = storage._get_file_path(school_id, category, filename)
            expected = f"schools/{school_id}/documents/2024/01/test.pdf"
            assert path == expected
    
    def test_validate_file_type_success(self, storage):
        """Test successful file type validation"""
        file = Mock()
        file.filename = "document.pdf"
        
        assert storage._validate_file_type(file, ["pdf", "doc"]) is True
        assert storage._validate_file_type(file, None) is True  # No restrictions
    
    def test_validate_file_type_failure(self, storage):
        """Test failed file type validation"""
        file = Mock()
        file.filename = "image.exe"
        
        assert storage._validate_file_type(file, ["pdf", "doc"]) is False
    
    def test_validate_file_size_success(self, storage):
        """Test successful file size validation"""
        file = Mock()
        file.size = 5 * 1024 * 1024  # 5MB
        
        assert storage._validate_file_size(file, 10) is True
    
    def test_validate_file_size_failure(self, storage):
        """Test failed file size validation"""
        file = Mock()
        file.size = 15 * 1024 * 1024  # 15MB
        
        assert storage._validate_file_size(file, 10) is False
    
    def test_generate_unique_filename(self, storage):
        """Test unique filename generation"""
        with patch('shared.file_storage.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20240101_120000'
            
            # Test with extension
            filename = storage._generate_unique_filename("document.pdf")
            assert filename == "20240101_120000_document.pdf"
            
            # Test without extension
            filename = storage._generate_unique_filename("document")
            assert filename == "20240101_120000_document"
            
            # Test with empty filename
            filename = storage._generate_unique_filename("")
            assert filename == "20240101_120000_untitled"
    
    @pytest.mark.asyncio
    async def test_upload_file_local_storage(self, storage, mock_file):
        """Test file upload to local storage"""
        school_id = uuid4()
        
        result = await storage.upload_file(
            file=mock_file,
            school_id=school_id,
            category="documents",
            allowed_types=["pdf"],
            max_size_mb=10
        )
        
        assert "file_url" in result
        assert "file_path" in result
        assert result["file_size"] == 17  # len(b"Test file content")
        assert result["file_type"] == "application/pdf"
        assert result["original_filename"] == "test_document.pdf"
        
        # Verify file was written
        local_path = storage._get_local_file_path(result["file_path"])
        assert os.path.exists(local_path)
        
        with open(local_path, 'rb') as f:
            assert f.read() == b"Test file content"
    
    @pytest.mark.asyncio
    async def test_upload_file_validation_errors(self, storage):
        """Test file upload validation errors"""
        school_id = uuid4()
        
        # Test invalid file type
        invalid_type_file = Mock(spec=UploadFile)
        invalid_type_file.filename = "virus.exe"
        invalid_type_file.size = 1024
        invalid_type_file.read = AsyncMock(return_value=b"fake content")
        
        with pytest.raises(HTTPException) as exc_info:
            await storage.upload_file(
                file=invalid_type_file,
                school_id=school_id,
                category="documents",
                allowed_types=["pdf", "doc"]
            )
        
        assert exc_info.value.status_code == 400
        assert "File type not allowed" in exc_info.value.detail
        
        # Test file too large
        large_file = Mock(spec=UploadFile)
        large_file.filename = "large.pdf"
        large_file.size = 20 * 1024 * 1024  # 20MB
        large_file.read = AsyncMock(return_value=b"fake content")
        
        with pytest.raises(HTTPException) as exc_info:
            await storage.upload_file(
                file=large_file,
                school_id=school_id,
                category="documents",
                max_size_mb=10
            )
        
        assert exc_info.value.status_code == 400
        assert "File too large" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_upload_file_s3_storage(self):
        """Test file upload to S3 storage"""
        storage = SchoolFileStorage()
        storage.use_local_storage = False
        storage.bucket_name = "test-bucket"
        storage.cdn_base_url = "https://cdn.example.com"
        
        # Mock S3 client
        mock_s3_response = {"ETag": '"abc123"'}
        storage.s3_client = Mock()
        storage.s3_client.put_object = Mock(return_value=mock_s3_response)
        
        # Create test file
        file = Mock(spec=UploadFile)
        file.filename = "test.pdf"
        file.content_type = "application/pdf"
        file.size = 1024
        file.read = AsyncMock(return_value=b"test content")
        
        school_id = uuid4()
        
        result = await storage.upload_file(
            file=file,
            school_id=school_id,
            category="documents"
        )
        
        assert result["file_url"].startswith("https://cdn.example.com")
        assert "file_path" in result
        
        # Verify S3 client was called correctly
        storage.s3_client.put_object.assert_called_once()
        call_args = storage.s3_client.put_object.call_args[1]
        assert call_args["Bucket"] == "test-bucket"
        assert call_args["Body"] == b"test content"
        assert call_args["ContentType"] == "application/pdf"
    
    @pytest.mark.asyncio
    async def test_delete_file_local_storage(self, storage):
        """Test file deletion from local storage"""
        school_id = uuid4()
        file_path = f"schools/{school_id}/documents/test.pdf"
        
        # Create the file
        local_path = storage._get_local_file_path(file_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'w') as f:
            f.write("test content")
        
        assert os.path.exists(local_path)
        
        # Delete the file
        result = await storage.delete_file(file_path, school_id)
        
        assert result is True
        assert not os.path.exists(local_path)
    
    @pytest.mark.asyncio
    async def test_delete_file_wrong_school(self, storage):
        """Test file deletion with wrong school ID"""
        school_id = uuid4()
        wrong_school_id = uuid4()
        file_path = f"schools/{school_id}/documents/test.pdf"
        
        try:
            await storage.delete_file(file_path, wrong_school_id)
            assert False, "Should have raised HTTPException"
        except HTTPException as exc:
            assert exc.status_code == 403
            assert "Cannot delete file from another school" in exc.detail
    
    @pytest.mark.asyncio
    async def test_get_file_url_local_storage(self, storage):
        """Test file URL generation for local storage"""
        school_id = uuid4()
        file_path = f"schools/{school_id}/documents/test.pdf"
        
        url = await storage.get_file_url(file_path, school_id)
        
        assert url == f"/api/v1/files/{file_path}"
    
    @pytest.mark.asyncio
    async def test_get_file_url_wrong_school(self, storage):
        """Test file URL generation with wrong school ID"""
        school_id = uuid4()
        wrong_school_id = uuid4()
        file_path = f"schools/{school_id}/documents/test.pdf"
        
        try:
            await storage.get_file_url(file_path, wrong_school_id)
            assert False, "Should have raised HTTPException"
        except HTTPException as exc:
            assert exc.status_code == 403
            assert "Cannot access file from another school" in exc.detail
    
    @pytest.mark.asyncio
    async def test_list_school_files_local_storage(self, storage):
        """Test listing school files from local storage"""
        school_id = uuid4()
        
        # Create some test files
        files = [
            f"schools/{school_id}/documents/file1.pdf",
            f"schools/{school_id}/documents/file2.pdf",
            f"schools/{school_id}/photos/photo1.jpg"
        ]
        
        for file_path in files:
            local_path = storage._get_local_file_path(file_path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'w') as f:
                f.write("test content")
        
        # List all files
        result = await storage.list_school_files(school_id)
        
        assert len(result) == 3
        assert all("file_path" in item for item in result)
        assert all("file_size" in item for item in result)
        assert all("last_modified" in item for item in result)
        assert all("file_url" in item for item in result)
        
        # List files by category
        result = await storage.list_school_files(school_id, category="documents")
        
        assert len(result) == 2
        assert all("documents" in item["file_path"] for item in result)
    
    @pytest.mark.asyncio
    async def test_get_school_storage_usage(self, storage):
        """Test storage usage calculation"""
        school_id = uuid4()
        
        # Create test files with known sizes
        files = [
            (f"schools/{school_id}/documents/file1.pdf", b"a" * 1000),
            (f"schools/{school_id}/documents/file2.pdf", b"b" * 2000),
            (f"schools/{school_id}/photos/photo1.jpg", b"c" * 3000)
        ]
        
        for file_path, content in files:
            local_path = storage._get_local_file_path(file_path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(content)
        
        usage = await storage.get_school_storage_usage(school_id)
        
        assert usage["total_size_bytes"] == 6000
        assert usage["total_size_mb"] == round(6000 / (1024 * 1024), 2)
        assert usage["file_count"] == 3
        assert "category_breakdown" in usage
        assert usage["category_breakdown"]["documents"] == 3000
        assert usage["category_breakdown"]["photos"] == 3000


class TestConvenienceFunctions:
    """Test convenience upload functions"""
    
    @pytest.mark.asyncio
    async def test_upload_student_document(self):
        """Test student document upload"""
        with patch('shared.file_storage.file_storage.upload_file') as mock_upload:
            mock_upload.return_value = {"file_url": "test_url"}
            
            file = Mock(spec=UploadFile)
            school_id = uuid4()
            student_id = uuid4()
            
            result = await upload_student_document(file, school_id, student_id)
            
            mock_upload.assert_called_once_with(
                file=file,
                school_id=school_id,
                category="students",
                subfolder=f"{student_id}/documents",
                allowed_types=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'],
                max_size_mb=10
            )
            assert result == {"file_url": "test_url"}
    
    @pytest.mark.asyncio
    async def test_upload_student_photo(self):
        """Test student photo upload"""
        with patch('shared.file_storage.file_storage.upload_file') as mock_upload:
            mock_upload.return_value = {"file_url": "test_url"}
            
            file = Mock(spec=UploadFile)
            school_id = uuid4()
            student_id = uuid4()
            
            result = await upload_student_photo(file, school_id, student_id)
            
            mock_upload.assert_called_once_with(
                file=file,
                school_id=school_id,
                category="students",
                subfolder=f"{student_id}/photos",
                allowed_types=['jpg', 'jpeg', 'png'],
                max_size_mb=5
            )
    
    @pytest.mark.asyncio
    async def test_upload_school_logo(self):
        """Test school logo upload"""
        with patch('shared.file_storage.file_storage.upload_file') as mock_upload:
            mock_upload.return_value = {"file_url": "test_url"}
            
            file = Mock(spec=UploadFile)
            school_id = uuid4()
            
            result = await upload_school_logo(file, school_id)
            
            mock_upload.assert_called_once_with(
                file=file,
                school_id=school_id,
                category="branding",
                subfolder="logos",
                allowed_types=['jpg', 'jpeg', 'png', 'svg'],
                max_size_mb=2
            )
    
    @pytest.mark.asyncio
    async def test_upload_report_document(self):
        """Test report document upload"""
        with patch('shared.file_storage.file_storage.upload_file') as mock_upload:
            mock_upload.return_value = {"file_url": "test_url"}
            
            file = Mock(spec=UploadFile)
            school_id = uuid4()
            report_type = "financial"
            
            result = await upload_report_document(file, school_id, report_type)
            
            mock_upload.assert_called_once_with(
                file=file,
                school_id=school_id,
                category="reports",
                subfolder=report_type,
                allowed_types=['pdf', 'xlsx', 'csv'],
                max_size_mb=50
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])