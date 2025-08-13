# =====================================================
# SIS Module - Student CRUD Tests
# File: backend/services/sis/tests/test_student_crud.py
# =====================================================

import pytest
import asyncio
from datetime import date, datetime
from uuid import uuid4, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import Mock, patch

from services.sis.crud import StudentCRUD
from services.sis.schemas import StudentCreate, StudentUpdate, Gender, HomeLanguage, BloodType
from services.sis.zimbabwe_validators import ZimbabweValidator

# Test data fixtures
@pytest.fixture
def valid_student_data():
    """Create valid student data for testing"""
    return StudentCreate(
        first_name="Tanaka",
        last_name="Mukamuri",
        date_of_birth=date(2010, 5, 15),
        gender=Gender.MALE,
        nationality="Zimbabwean",
        home_language=HomeLanguage.SHONA,
        current_grade_level=5,
        residential_address={
            "street": "123 Borrowdale Road",
            "suburb": "Borrowdale",
            "city": "Harare",
            "province": "Harare"
        },
        emergency_contacts=[
            {
                "name": "Mary Mukamuri",
                "relationship": "Mother",
                "phone": "+263771234567",
                "is_primary": True,
                "can_pickup": True
            },
            {
                "name": "John Mukamuri", 
                "relationship": "Father",
                "phone": "+263772345678",
                "is_primary": False,
                "can_pickup": True
            }
        ]
    )

@pytest.fixture
def mock_user():
    """Create mock user for testing"""
    user = Mock(spec=User)
    user.id = uuid4()
    user.school_id = uuid4()
    user.role = "school_admin"
    return user

@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    return Mock(spec=AsyncSession)

class TestStudentCRUD:
    """Test class for Student CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_student_full_workflow_success(self, mock_db_session, valid_student_data, mock_user):
        """Test successful student creation with full workflow"""
        # Setup
        school_id = mock_user.school_id
        created_by = mock_user.id
        
        # Mock dependencies
        with patch.object(StudentCRUD, '_validate_class_capacity') as mock_validate_capacity, \
             patch.object(StudentCRUD, '_check_duplicate_student') as mock_check_duplicate, \
             patch.object(StudentCRUD, '_generate_student_number', return_value="2024-0001") as mock_gen_number, \
             patch.object(StudentCRUD, '_encrypt_medical_data', return_value="encrypted_medical") as mock_encrypt_medical, \
             patch.object(StudentCRUD, '_encrypt_emergency_contacts', return_value="encrypted_contacts") as mock_encrypt_contacts, \
             patch.object(StudentCRUD, '_create_initial_academic_history') as mock_create_history, \
             patch.object(StudentCRUD, '_log_student_activity') as mock_log_activity:
            
            # Mock database operations
            mock_student = Mock(spec=Student)
            mock_student.id = uuid4()
            mock_student.student_number = "2024-0001"
            
            mock_db_session.add = Mock()
            mock_db_session.flush = Mock()
            mock_db_session.commit = Mock()
            mock_db_session.refresh = Mock()
            
            # Execute
            result = await StudentCRUD.create_student_full_workflow(
                mock_db_session, valid_student_data, school_id, created_by
            )
            
            # Verify workflow steps were called
            mock_check_duplicate.assert_called_once()
            mock_gen_number.assert_called_once_with(mock_db_session, school_id)
            mock_encrypt_medical.assert_called_once()
            mock_encrypt_contacts.assert_called_once()
            mock_create_history.assert_called_once()
            mock_log_activity.assert_called_once()
            
            # Verify database operations
            mock_db_session.add.assert_called_once()
            mock_db_session.flush.assert_called_once()
            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_student_duplicate_check_fails(self, mock_db_session, valid_student_data, mock_user):
        """Test student creation fails when duplicate is found"""
        from ..crud import DuplicateStudentError
        
        school_id = mock_user.school_id
        created_by = mock_user.id
        
        with patch.object(StudentCRUD, '_check_duplicate_student', 
                         side_effect=DuplicateStudentError("Duplicate student found")):
            
            with pytest.raises(DuplicateStudentError):
                await StudentCRUD.create_student_full_workflow(
                    mock_db_session, valid_student_data, school_id, created_by
                )
    
    @pytest.mark.asyncio 
    async def test_get_student_by_id_with_permission_check_admin(self, mock_db_session, mock_user):
        """Test admin can access any student in their school"""
        student_id = uuid4()
        mock_user.role = "school_admin"
        
        # Mock student
        mock_student = Mock(spec=Student)
        mock_student.id = student_id
        mock_student.school_id = mock_user.school_id
        
        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_student
        mock_db_session.execute.return_value = mock_result
        
        with patch.object(StudentCRUD, '_user_can_view_sensitive_data', return_value=True), \
             patch.object(StudentCRUD, '_decrypt_student_sensitive_data') as mock_decrypt:
            
            result = await StudentCRUD.get_student_by_id_with_permission_check(
                mock_db_session, mock_user, student_id
            )
            
            assert result == mock_student
            mock_decrypt.assert_called_once_with(mock_student)
    
    @pytest.mark.asyncio
    async def test_get_student_by_id_parent_access_control(self, mock_db_session, mock_user):
        """Test parent can only access their own children"""
        student_id = uuid4()
        mock_user.role = "parent"
        
        # Mock query execution
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None  # No access
        mock_db_session.execute.return_value = mock_result
        
        result = await StudentCRUD.get_student_by_id_with_permission_check(
            mock_db_session, mock_user, student_id
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_student_success(self, mock_db_session, mock_user):
        """Test successful student update"""
        student_id = uuid4()
        
        # Create update data
        update_data = StudentUpdate(
            first_name="Updated Name",
            email="newemail@example.com",
            mobile_number="+263771111111"
        )
        
        # Mock existing student
        mock_student = Mock(spec=Student)
        mock_student.id = student_id
        mock_student.first_name = "Old Name"
        mock_student.email = "old@example.com"
        mock_student.mobile_number = "+263770000000"
        mock_student.student_number = "2024-0001"
        
        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_student
        mock_db_session.execute.return_value = mock_result
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()
        
        with patch.object(StudentCRUD, '_log_student_activity') as mock_log:
            result = await StudentCRUD.update_student(
                mock_db_session, student_id, update_data, mock_user.id
            )
            
            # Verify fields were updated
            assert mock_student.first_name == "Updated Name"
            assert mock_student.email == "newemail@example.com"
            assert mock_student.mobile_number == "+263771111111"
            
            # Verify audit logging
            mock_log.assert_called_once()
            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_student_not_found(self, mock_db_session, mock_user):
        """Test student update fails when student not found"""
        from ..crud import StudentNotFoundError
        
        student_id = uuid4()
        update_data = StudentUpdate(first_name="New Name")
        
        # Mock student not found
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        with pytest.raises(StudentNotFoundError):
            await StudentCRUD.update_student(
                mock_db_session, student_id, update_data, mock_user.id
            )
    
    @pytest.mark.asyncio
    async def test_delete_student_soft_delete(self, mock_db_session, mock_user):
        """Test soft delete functionality"""
        student_id = uuid4()
        
        # Mock existing student
        mock_student = Mock(spec=Student)
        mock_student.id = student_id
        mock_student.student_number = "2024-0001"
        mock_student.status = "active"
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_student
        mock_db_session.execute.return_value = mock_result
        mock_db_session.commit = Mock()
        
        with patch.object(StudentCRUD, '_log_student_activity') as mock_log:
            result = await StudentCRUD.delete_student(
                mock_db_session, student_id, mock_user.id, soft_delete=True
            )
            
            assert result is True
            assert mock_student.status == "transferred"  # Soft delete status
            assert mock_student.deleted_at is not None
            mock_log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_student_number(self, mock_db_session):
        """Test student number generation"""
        school_id = uuid4()
        
        # Mock database query result
        mock_result = Mock()
        mock_result.scalar.return_value = 5  # Next sequence number
        mock_db_session.execute.return_value = mock_result
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value.year = 2024
            
            result = await StudentCRUD._generate_student_number(mock_db_session, school_id)
            
            assert result == "2024-0005"
    
    @pytest.mark.asyncio
    async def test_check_duplicate_student_found(self, mock_db_session):
        """Test duplicate student detection"""
        from ..crud import DuplicateStudentError
        
        school_id = uuid4()
        student_data = Mock()
        student_data.first_name = "John"
        student_data.last_name = "Doe"
        student_data.date_of_birth = date(2010, 1, 1)
        
        # Mock existing student found
        mock_existing_student = Mock(spec=Student)
        mock_existing_student.student_number = "2024-0001"
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_existing_student
        mock_db_session.execute.return_value = mock_result
        
        with pytest.raises(DuplicateStudentError):
            await StudentCRUD._check_duplicate_student(mock_db_session, student_data, school_id)
    
    @pytest.mark.asyncio
    async def test_check_duplicate_student_not_found(self, mock_db_session):
        """Test no duplicate student found"""
        school_id = uuid4()
        student_data = Mock()
        student_data.first_name = "John"
        student_data.last_name = "Doe" 
        student_data.date_of_birth = date(2010, 1, 1)
        
        # Mock no existing student
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        # Should not raise exception
        await StudentCRUD._check_duplicate_student(mock_db_session, student_data, school_id)

class TestZimbabweValidators:
    """Test Zimbabwe-specific validators"""
    
    def test_validate_national_id_valid(self):
        """Test valid National ID validation"""
        valid_id = "63-123456-K-23"
        is_valid, formatted = ZimbabweValidator.validate_national_id(valid_id)
        
        assert is_valid is True
        assert formatted == "63-123456-K-23"
    
    def test_validate_national_id_invalid_format(self):
        """Test invalid National ID format"""
        invalid_id = "123-456-789"
        is_valid, error = ZimbabweValidator.validate_national_id(invalid_id)
        
        assert is_valid is False
        assert "Invalid National ID format" in error
    
    def test_validate_national_id_invalid_province(self):
        """Test invalid province code in National ID"""
        invalid_id = "99-123456-K-23"  # Invalid province code
        is_valid, error = ZimbabweValidator.validate_national_id(invalid_id)
        
        assert is_valid is False
        assert "Invalid province code" in error
    
    def test_validate_phone_number_valid_mobile(self):
        """Test valid Zimbabwe mobile number"""
        valid_phone = "+263771234567"
        is_valid, formatted = ZimbabweValidator.validate_phone_number(valid_phone)
        
        assert is_valid is True
        assert formatted == "+263771234567"
    
    def test_validate_phone_number_local_format(self):
        """Test local format phone number"""
        local_phone = "0771234567"
        is_valid, formatted = ZimbabweValidator.validate_phone_number(local_phone)
        
        assert is_valid is True
        assert formatted == "+263771234567"
    
    def test_validate_phone_number_invalid(self):
        """Test invalid phone number"""
        invalid_phone = "123456"
        is_valid, error = ZimbabweValidator.validate_phone_number(invalid_phone)
        
        assert is_valid is False
        assert "Invalid Zimbabwe phone number" in error
    
    def test_calculate_age_from_id(self):
        """Test age calculation from National ID"""
        # ID for someone born in 1995
        national_id = "63-950515-K-23"
        age = ZimbabweValidator.calculate_age_from_id(national_id)
        
        # Age should be approximately 28-29 (depending on current date)
        assert age is not None
        assert 25 <= age <= 35  # Reasonable range
    
    def test_validate_grade_level_primary(self):
        """Test grade level validation for primary school"""
        is_valid, error = ZimbabweValidator.validate_grade_level(5, "primary")
        assert is_valid is True
        
        is_valid, error = ZimbabweValidator.validate_grade_level(10, "primary") 
        assert is_valid is False
        assert "Primary school grades are 1-7" in error
    
    def test_validate_grade_level_secondary(self):
        """Test grade level validation for secondary school"""
        is_valid, error = ZimbabweValidator.validate_grade_level(10, "secondary")
        assert is_valid is True
        
        is_valid, error = ZimbabweValidator.validate_grade_level(5, "secondary")
        assert is_valid is False
        assert "Secondary school forms are 8-13" in error

# Integration test fixtures
@pytest.fixture
def integration_test_db():
    """Setup test database for integration tests"""
    # This would set up a real test database
    # For now, return mock
    return Mock()

class TestStudentCRUDIntegration:
    """Integration tests for Student CRUD operations"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio 
    async def test_full_student_lifecycle(self, integration_test_db):
        """Test complete student lifecycle: create, read, update, delete"""
        # This would be a full integration test with real database
        # For now, just mark as placeholder
        pytest.skip("Integration test - requires database setup")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_bulk_student_import(self, integration_test_db):
        """Test bulk import functionality"""
        pytest.skip("Integration test - requires database setup")
    
    @pytest.mark.integration 
    @pytest.mark.asyncio
    async def test_student_search_and_filtering(self, integration_test_db):
        """Test student search and filtering functionality"""
        pytest.skip("Integration test - requires database setup")

# Performance test fixtures
class TestStudentCRUDPerformance:
    """Performance tests for Student CRUD operations"""
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_bulk_student_creation_performance(self):
        """Test performance of bulk student creation"""
        # Test creating 1000 students and measure time
        pytest.skip("Performance test - requires specific setup")
    
    @pytest.mark.slow  
    @pytest.mark.asyncio
    async def test_student_search_performance(self):
        """Test performance of student search with large dataset"""
        pytest.skip("Performance test - requires large dataset")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])