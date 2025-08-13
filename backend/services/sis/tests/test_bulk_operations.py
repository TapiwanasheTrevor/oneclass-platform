# =====================================================
# SIS Module - Bulk Operations Tests
# File: backend/services/sis/tests/test_bulk_operations.py
# =====================================================

import pytest
import asyncio
import io
import csv
from datetime import date
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock

from ..bulk_operations import BulkImportService, BulkExportService, BulkOperationError
from ..schemas import StudentCreate
from shared.models.sis import Student

class TestBulkImportService:
    """Test class for bulk import functionality"""
    
    @pytest.fixture
    def sample_csv_data(self):
        """Create sample CSV data for testing"""
        csv_data = [
            ['first_name', 'last_name', 'date_of_birth', 'gender', 'grade_level', 'parent1_name', 'parent1_phone'],
            ['John', 'Mukamuri', '2010-05-15', 'Male', '5', 'Mary Mukamuri', '+263771234567'],
            ['Jane', 'Chikwava', '2011-03-20', 'Female', '4', 'Grace Chikwava', '+263772345678'],
            ['Peter', 'Ncube', '2009-08-10', 'Male', '6', 'Sarah Ncube', '+263773456789']
        ]
        
        output = io.StringIO()
        writer = csv.writer(output)
        for row in csv_data:
            writer.writerow(row)
        
        return output.getvalue().encode('utf-8')
    
    @pytest.fixture
    def invalid_csv_data(self):
        """Create invalid CSV data for testing"""
        csv_data = [
            ['first_name', 'last_name', 'date_of_birth', 'gender', 'grade_level'],
            ['', 'Mukamuri', '2010-05-15', 'Male', '5'],  # Missing first name
            ['Jane', 'Chikwava', 'invalid-date', 'Female', '4'],  # Invalid date
            ['Peter', 'Ncube', '2009-08-10', 'Invalid', '6']  # Invalid gender
        ]
        
        output = io.StringIO()
        writer = csv.writer(output)
        for row in csv_data:
            writer.writerow(row)
        
        return output.getvalue().encode('utf-8')
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session"""
        session = Mock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session
    
    @pytest.mark.asyncio
    async def test_import_from_csv_success(self, sample_csv_data, mock_db_session):
        """Test successful CSV import"""
        school_id = uuid4()
        created_by = uuid4()
        
        with patch.object(BulkImportService, '_process_csv_row') as mock_process_row, \
             patch('backend.services.sis.crud.StudentCRUD.create_student_full_workflow') as mock_create_student:
            
            # Mock successful row processing
            mock_student_data = Mock(spec=StudentCreate)
            mock_process_row.return_value = mock_student_data
            
            # Mock successful student creation
            mock_student = Mock(spec=Student)
            mock_student.id = uuid4()
            mock_student.student_number = "2024-0001"
            mock_student.first_name = "John"
            mock_student.last_name = "Mukamuri"
            mock_create_student.return_value = mock_student
            
            # Execute import
            results = await BulkImportService.import_from_csv(
                mock_db_session, sample_csv_data, school_id, created_by, validate_only=False
            )
            
            # Verify results
            assert results['total_rows'] == 3
            assert results['successful'] == 3
            assert results['failed'] == 0
            assert len(results['imported_students']) == 3
            assert len(results['errors']) == 0
            
            # Verify mock calls
            assert mock_process_row.call_count == 3
            assert mock_create_student.call_count == 3
    
    @pytest.mark.asyncio
    async def test_import_from_csv_validation_only(self, sample_csv_data, mock_db_session):
        """Test CSV import in validation-only mode"""
        school_id = uuid4()
        created_by = uuid4()
        
        with patch.object(BulkImportService, '_process_csv_row') as mock_process_row:
            mock_student_data = Mock(spec=StudentCreate)
            mock_process_row.return_value = mock_student_data
            
            results = await BulkImportService.import_from_csv(
                mock_db_session, sample_csv_data, school_id, created_by, validate_only=True
            )
            
            # Should validate but not create students
            assert results['total_rows'] == 3
            assert results['successful'] == 0  # No actual creation
            assert len(results['warnings']) == 3  # Validation warnings
            assert len(results['imported_students']) == 0
    
    @pytest.mark.asyncio
    async def test_import_from_csv_with_errors(self, invalid_csv_data, mock_db_session):
        """Test CSV import with validation errors"""
        school_id = uuid4()
        created_by = uuid4()
        
        with patch.object(BulkImportService, '_process_csv_row', side_effect=ValueError("Invalid data")):
            results = await BulkImportService.import_from_csv(
                mock_db_session, invalid_csv_data, school_id, created_by, validate_only=False
            )
            
            # All rows should fail
            assert results['total_rows'] == 3
            assert results['successful'] == 0
            assert results['failed'] == 3
            assert len(results['errors']) == 3
    
    @pytest.mark.asyncio
    async def test_process_csv_row_valid_data(self):
        """Test processing of valid CSV row"""
        school_id = uuid4()
        row = {
            'first_name': 'John',
            'last_name': 'Mukamuri',
            'date_of_birth': '2010-05-15',
            'gender': 'Male',
            'grade_level': '5',
            'nationality': 'Zimbabwean',
            'home_language': 'Shona',
            'residential_street': '123 Main St',
            'residential_suburb': 'Borrowdale',
            'residential_city': 'Harare',
            'residential_province': 'Harare',
            'parent1_name': 'Mary Mukamuri',
            'parent1_phone': '+263771234567',
            'parent1_relationship': 'Mother',
            'parent2_name': 'James Mukamuri',
            'parent2_phone': '+263772345678',
            'parent2_relationship': 'Father'
        }
        
        result = await BulkImportService._process_csv_row(row, 2, school_id)
        
        # Verify student data
        assert result.first_name == 'John'
        assert result.last_name == 'Mukamuri'
        assert result.date_of_birth == date(2010, 5, 15)
        assert result.gender.value == 'Male'
        assert result.current_grade_level == 5
        assert len(result.emergency_contacts) >= 2  # At least parents
    
    @pytest.mark.asyncio
    async def test_process_csv_row_missing_required_field(self):
        """Test processing CSV row with missing required field"""
        school_id = uuid4()
        row = {
            'last_name': 'Mukamuri',  # Missing first_name
            'date_of_birth': '2010-05-15',
            'gender': 'Male',
            'grade_level': '5'
        }
        
        with pytest.raises(ValueError, match="Missing required field"):
            await BulkImportService._process_csv_row(row, 2, school_id)
    
    @pytest.mark.asyncio
    async def test_process_csv_row_invalid_date(self):
        """Test processing CSV row with invalid date"""
        school_id = uuid4()
        row = {
            'first_name': 'John',
            'last_name': 'Mukamuri',
            'date_of_birth': 'invalid-date',
            'gender': 'Male',
            'grade_level': '5'
        }
        
        with pytest.raises(ValueError, match="Invalid date"):
            await BulkImportService._process_csv_row(row, 2, school_id)
    
    def test_generate_import_template(self):
        """Test import template generation"""
        template_data = BulkImportService.generate_import_template()
        
        # Decode and parse CSV
        template_str = template_data.decode('utf-8')
        lines = template_str.strip().split('\n')
        
        # Check header
        header = lines[0].split(',')
        assert 'first_name' in header
        assert 'last_name' in header
        assert 'date_of_birth' in header
        assert 'gender' in header
        assert 'grade_level' in header
        
        # Check sample data exists
        assert len(lines) > 1  # Header + sample + empty rows

class TestBulkExportService:
    """Test class for bulk export functionality"""
    
    @pytest.fixture
    def sample_students(self):
        """Create sample student data for testing"""
        students = []
        for i in range(3):
            student = Mock(spec=Student)
            student.id = uuid4()
            student.student_number = f"2024-000{i+1}"
            student.first_name = f"Student{i+1}"
            student.last_name = f"Test{i+1}"
            student.gender = "Male" if i % 2 == 0 else "Female"
            student.current_grade_level = 5 + i
            student.status = "active"
            student.enrollment_date = date(2024, 1, 15)
            student.middle_name = None
            student.date_of_birth = date(2010, 1, 15)
            student.nationality = "Zimbabwean"
            student.home_language = "English"
            student.mobile_number = f"+26377123456{i}"
            student.email = f"student{i+1}@test.com"
            student.blood_type = "O+"
            student.medical_aid_provider = "PSMAS"
            student.medical_aid_number = f"12345{i}"
            student.residential_address = {"street": "Test St", "city": "Harare"}
            student.transport_needs = "Bus"
            students.append(student)
        return students
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session"""
        return Mock()
    
    @pytest.mark.asyncio
    async def test_export_to_csv_basic(self, sample_students, mock_db_session):
        """Test basic CSV export without sensitive data"""
        school_id = uuid4()
        
        # Mock database query
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = sample_students
        mock_db_session.execute.return_value = mock_result
        
        csv_data = await BulkExportService.export_to_csv(
            mock_db_session, school_id, filters=None, include_sensitive=False
        )
        
        # Parse CSV data
        csv_str = csv_data.decode('utf-8')
        lines = csv_str.strip().split('\n')
        
        # Check header
        header = lines[0].split(',')
        assert 'student_number' in header
        assert 'first_name' in header
        assert 'last_name' in header
        assert 'gender' in header
        assert 'grade_level' in header
        
        # Sensitive fields should not be included
        assert 'mobile_number' not in header
        assert 'email' not in header
        
        # Check data rows
        assert len(lines) == 4  # Header + 3 students
    
    @pytest.mark.asyncio
    async def test_export_to_csv_with_sensitive_data(self, sample_students, mock_db_session):
        """Test CSV export including sensitive data"""
        school_id = uuid4()
        
        # Mock database query  
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = sample_students
        mock_db_session.execute.return_value = mock_result
        
        csv_data = await BulkExportService.export_to_csv(
            mock_db_session, school_id, filters=None, include_sensitive=True
        )
        
        # Parse CSV data
        csv_str = csv_data.decode('utf-8')
        lines = csv_str.strip().split('\n')
        
        # Check header includes sensitive fields
        header = lines[0].split(',')
        assert 'mobile_number' in header
        assert 'email' in header
        assert 'medical_aid_provider' in header
    
    @pytest.mark.asyncio
    async def test_export_to_csv_with_filters(self, sample_students, mock_db_session):
        """Test CSV export with filters applied"""
        school_id = uuid4()
        filters = {'grade_level': 5, 'status': 'active'}
        
        # Mock database query
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_students[0]]  # Filtered result
        mock_db_session.execute.return_value = mock_result
        
        csv_data = await BulkExportService.export_to_csv(
            mock_db_session, school_id, filters=filters, include_sensitive=False
        )
        
        # Should have fewer results due to filtering
        csv_str = csv_data.decode('utf-8')
        lines = csv_str.strip().split('\n')
        assert len(lines) == 2  # Header + 1 filtered student
    
    @pytest.mark.asyncio
    async def test_export_to_excel(self, sample_students, mock_db_session):
        """Test Excel export functionality"""
        school_id = uuid4()
        
        # Mock the CSV export method
        sample_csv = "student_number,first_name,last_name\n2024-0001,John,Doe\n"
        
        with patch.object(BulkExportService, 'export_to_csv', return_value=sample_csv.encode('utf-8')):
            excel_data = await BulkExportService.export_to_excel(
                mock_db_session, school_id, filters=None, include_sensitive=False
            )
            
            # Should return binary Excel data
            assert isinstance(excel_data, bytes)
            assert len(excel_data) > 0
    
    @pytest.mark.asyncio
    async def test_export_class_list_csv(self, sample_students, mock_db_session):
        """Test class list export in CSV format"""
        class_id = uuid4()
        
        # Mock database query for class students
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = sample_students
        mock_db_session.execute.return_value = mock_result
        
        csv_data = await BulkExportService.export_class_list(
            mock_db_session, class_id, format='csv'
        )
        
        # Parse CSV data
        csv_str = csv_data.decode('utf-8')
        lines = csv_str.strip().split('\n')
        
        # Check format: number, student number, name, gender, date of birth
        header = lines[0].split(',')
        assert header[0] == '#'
        assert 'Student Number' in header
        assert 'Name' in header
        assert 'Gender' in header
        
        # Check student rows
        assert len(lines) == 4  # Header + 3 students

class TestBulkOperationsIntegration:
    """Integration tests for bulk operations"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_import_export_cycle(self):
        """Test complete import and export cycle"""
        # This would test importing students and then exporting them
        # to verify data integrity
        pytest.skip("Integration test - requires database setup")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_large_file_import(self):
        """Test importing large CSV files (1000+ students)"""
        pytest.skip("Integration test - requires performance setup")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_import_operations(self):
        """Test multiple simultaneous import operations"""
        pytest.skip("Integration test - requires concurrency setup")

class TestBulkOperationsErrorHandling:
    """Test error handling in bulk operations"""
    
    @pytest.mark.asyncio
    async def test_import_file_encoding_error(self, mock_db_session):
        """Test handling of file encoding errors"""
        # Create invalid UTF-8 data
        invalid_data = b'\xff\xfe\x00\x01'
        school_id = uuid4()
        created_by = uuid4()
        
        with pytest.raises(BulkOperationError):
            await BulkImportService.import_from_csv(
                mock_db_session, invalid_data, school_id, created_by
            )
    
    @pytest.mark.asyncio
    async def test_import_database_error_rollback(self, mock_db_session):
        """Test database error handling and rollback"""
        sample_csv = "first_name,last_name,date_of_birth,gender,grade_level\nJohn,Doe,2010-01-01,Male,5\n"
        school_id = uuid4()
        created_by = uuid4()
        
        # Mock database error
        mock_db_session.commit = AsyncMock(side_effect=Exception("Database error"))
        mock_db_session.rollback = AsyncMock()
        
        with patch.object(BulkImportService, '_process_csv_row'), \
             patch('backend.services.sis.crud.StudentCRUD.create_student_full_workflow'):
            
            with pytest.raises(BulkOperationError):
                await BulkImportService.import_from_csv(
                    mock_db_session, sample_csv.encode('utf-8'), school_id, created_by
                )
            
            # Verify rollback was called
            mock_db_session.rollback.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])