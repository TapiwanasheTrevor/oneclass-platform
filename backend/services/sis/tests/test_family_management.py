# =====================================================
# SIS Module - Family Management Tests
# File: backend/services/sis/tests/test_family_management.py
# =====================================================

import pytest
import asyncio
from datetime import date, datetime
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock

from ..family_crud import FamilyCRUD, EnhancedGuardianCRUD, EmergencyContactCRUD, FamilyManagementError
from ..family_models import (
    FamilyGroup, StudentGuardianRelationship, EmergencyContact,
    RelationshipType, ContactMethod, FinancialResponsibilityType
)
from ..family_schemas import (
    GuardianRelationshipCreateEnhanced, EmergencyContactCreate
)
from shared.models.sis import Student
from shared.models.platform_user import PlatformUser as User

class TestFamilyCRUD:
    """Test class for family group management"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session"""
        session = Mock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session
    
    @pytest.mark.asyncio
    async def test_create_family_group_success(self, mock_db_session):
        """Test successful family group creation"""
        family_name = "Mukamuri Family"
        primary_contact_id = uuid4()
        school_id = uuid4()
        created_by = uuid4()
        
        with patch.object(FamilyCRUD, '_generate_family_code', return_value="FAM0001") as mock_gen_code:
            # Mock the family group creation
            mock_family = Mock(spec=FamilyGroup)
            mock_family.id = uuid4()
            mock_family.family_code = "FAM0001"
            mock_family.family_name = family_name
            
            # Since we can't mock the constructor directly, we'll patch the add method
            def mock_add(obj):
                obj.id = mock_family.id
                obj.family_code = mock_family.family_code
            
            mock_db_session.add.side_effect = mock_add
            mock_db_session.refresh.side_effect = lambda obj: setattr(obj, 'id', mock_family.id)
            
            result = await FamilyCRUD.create_family_group(
                mock_db_session, family_name, primary_contact_id, school_id, created_by
            )
            
            # Verify family code generation was called
            mock_gen_code.assert_called_once_with(mock_db_session, school_id)
            
            # Verify database operations
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_family_group_database_error(self, mock_db_session):
        """Test family group creation with database error"""
        family_name = "Test Family"
        primary_contact_id = uuid4()
        school_id = uuid4()
        created_by = uuid4()
        
        # Mock database error
        mock_db_session.commit.side_effect = Exception("Database error")
        
        with patch.object(FamilyCRUD, '_generate_family_code', return_value="FAM0001"):
            with pytest.raises(FamilyManagementError):
                await FamilyCRUD.create_family_group(
                    mock_db_session, family_name, primary_contact_id, school_id, created_by
                )
            
            # Verify rollback was called
            mock_db_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_student_to_family_success(self, mock_db_session):
        """Test successfully adding student to family"""
        student_id = uuid4()
        family_group_id = uuid4()
        
        # Mock no existing membership
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        with patch.object(FamilyCRUD, '_update_family_student_count') as mock_update_count:
            mock_membership = Mock()
            mock_membership.id = uuid4()
            
            def mock_add(obj):
                obj.id = mock_membership.id
            
            mock_db_session.add.side_effect = mock_add
            
            result = await FamilyCRUD.add_student_to_family(
                mock_db_session, student_id, family_group_id
            )
            
            # Verify student count update was called
            mock_update_count.assert_called_once_with(mock_db_session, family_group_id)
            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_student_to_family_already_exists(self, mock_db_session):
        """Test adding student to family when already exists"""
        student_id = uuid4()
        family_group_id = uuid4()
        
        # Mock existing membership
        mock_existing = Mock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_existing
        mock_db_session.execute.return_value = mock_result
        
        with pytest.raises(FamilyManagementError, match="already belongs"):
            await FamilyCRUD.add_student_to_family(
                mock_db_session, student_id, family_group_id
            )
    
    @pytest.mark.asyncio
    async def test_get_family_students(self, mock_db_session):
        """Test retrieving students in a family"""
        family_group_id = uuid4()
        
        # Mock students
        mock_students = [Mock(spec=Student) for _ in range(3)]
        for i, student in enumerate(mock_students):
            student.id = uuid4()
            student.first_name = f"Student{i+1}"
            student.last_name = f"Test{i+1}"
            student.date_of_birth = date(2010, 1, i+1)
        
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_students
        mock_db_session.execute.return_value = mock_result
        
        result = await FamilyCRUD.get_family_students(mock_db_session, family_group_id)
        
        assert len(result) == 3
        assert all(isinstance(s, Mock) for s in result)
    
    @pytest.mark.asyncio
    async def test_generate_family_code(self, mock_db_session):
        """Test family code generation"""
        school_id = uuid4()
        
        # Mock database query result
        mock_result = Mock()
        mock_result.scalar.return_value = 5  # Next sequence number
        mock_db_session.execute.return_value = mock_result
        
        result = await FamilyCRUD._generate_family_code(mock_db_session, school_id)
        
        assert result == "FAM0005"

class TestEnhancedGuardianCRUD:
    """Test class for enhanced guardian relationship management"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session"""
        session = Mock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session
    
    @pytest.fixture
    def guardian_relationship_data(self):
        """Create test guardian relationship data"""
        return {
            'relationship_type': RelationshipType.MOTHER,
            'is_biological': True,
            'is_legal_guardian': True,
            'is_primary_contact': True,
            'is_emergency_contact': True,
            'contact_priority': 1,
            'preferred_contact_method': ContactMethod.SMS,
            'has_pickup_permission': True,
            'has_academic_access': True,
            'has_medical_access': True,
            'has_financial_responsibility': True,
            'financial_responsibility_type': FinancialResponsibilityType.FULL,
            'financial_responsibility_percentage': 100.0,
            'receive_academic_reports': True,
            'receive_financial_notices': True,
            'student_lives_with': True
        }
    
    @pytest.mark.asyncio
    async def test_create_comprehensive_guardian_relationship_success(
        self, mock_db_session, guardian_relationship_data
    ):
        """Test successful comprehensive guardian relationship creation"""
        student_id = uuid4()
        guardian_user_id = uuid4()
        created_by = uuid4()
        
        # Mock student exists
        mock_student = Mock(spec=Student)
        mock_student.id = student_id
        
        # Mock guardian user exists
        mock_guardian = Mock(spec=User)
        mock_guardian.id = guardian_user_id
        
        # Mock no existing relationship
        mock_db_session.execute.side_effect = [
            Mock(scalar_one_or_none=Mock(return_value=mock_student)),  # Student query
            Mock(scalar_one_or_none=Mock(return_value=mock_guardian)),  # Guardian query
            Mock(scalar_one_or_none=Mock(return_value=None))  # Existing relationship query
        ]
        
        with patch.object(EnhancedGuardianCRUD, '_ensure_single_primary_contact') as mock_ensure_primary:
            mock_relationship = Mock(spec=StudentGuardianRelationship)
            mock_relationship.id = uuid4()
            
            def mock_add(obj):
                obj.id = mock_relationship.id
            
            mock_db_session.add.side_effect = mock_add
            
            result = await EnhancedGuardianCRUD.create_comprehensive_guardian_relationship(
                mock_db_session, student_id, guardian_user_id, 
                guardian_relationship_data, created_by
            )
            
            # Verify primary contact logic was called
            mock_ensure_primary.assert_called_once_with(
                mock_db_session, student_id, guardian_user_id
            )
            
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_guardian_relationship_student_not_found(
        self, mock_db_session, guardian_relationship_data
    ):
        """Test guardian relationship creation when student not found"""
        student_id = uuid4()
        guardian_user_id = uuid4()
        created_by = uuid4()
        
        # Mock student not found
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        with pytest.raises(FamilyManagementError, match="Student .* not found"):
            await EnhancedGuardianCRUD.create_comprehensive_guardian_relationship(
                mock_db_session, student_id, guardian_user_id,
                guardian_relationship_data, created_by
            )
    
    @pytest.mark.asyncio
    async def test_create_guardian_relationship_already_exists(
        self, mock_db_session, guardian_relationship_data
    ):
        """Test guardian relationship creation when relationship already exists"""
        student_id = uuid4()
        guardian_user_id = uuid4()
        created_by = uuid4()
        
        # Mock student and guardian exist, but relationship already exists
        mock_student = Mock(spec=Student)
        mock_guardian = Mock(spec=User)
        mock_existing_relationship = Mock(spec=StudentGuardianRelationship)
        
        mock_db_session.execute.side_effect = [
            Mock(scalar_one_or_none=Mock(return_value=mock_student)),
            Mock(scalar_one_or_none=Mock(return_value=mock_guardian)),
            Mock(scalar_one_or_none=Mock(return_value=mock_existing_relationship))
        ]
        
        with pytest.raises(FamilyManagementError, match="already exists"):
            await EnhancedGuardianCRUD.create_comprehensive_guardian_relationship(
                mock_db_session, student_id, guardian_user_id,
                guardian_relationship_data, created_by
            )
    
    @pytest.mark.asyncio
    async def test_get_student_guardians_comprehensive(self, mock_db_session):
        """Test retrieving comprehensive guardian information"""
        student_id = uuid4()
        
        # Mock guardian relationships
        mock_relationships = [Mock(spec=StudentGuardianRelationship) for _ in range(2)]
        for i, rel in enumerate(mock_relationships):
            rel.id = uuid4()
            rel.guardian_user_id = uuid4()
            rel.relationship_type = RelationshipType.MOTHER if i == 0 else RelationshipType.FATHER
            rel.is_primary_contact = i == 0
            rel.contact_priority = i + 1
        
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_relationships
        mock_db_session.execute.return_value = mock_result
        
        result = await EnhancedGuardianCRUD.get_student_guardians_comprehensive(
            mock_db_session, student_id
        )
        
        assert len(result) == 2
        # Should be ordered by primary contact first, then priority
        assert result[0].is_primary_contact is True
    
    @pytest.mark.asyncio
    async def test_get_guardian_students(self, mock_db_session):
        """Test retrieving students for a guardian"""
        guardian_user_id = uuid4()
        school_id = uuid4()
        
        # Mock student-relationship pairs
        mock_data = []
        for i in range(2):
            student = Mock(spec=Student)
            student.id = uuid4()
            student.first_name = f"Student{i+1}"
            student.last_name = "Test"
            student.school_id = school_id
            
            relationship = Mock(spec=StudentGuardianRelationship)
            relationship.id = uuid4()
            relationship.student_id = student.id
            relationship.guardian_user_id = guardian_user_id
            
            mock_data.append((student, relationship))
        
        mock_result = Mock()
        mock_result.all.return_value = mock_data
        mock_db_session.execute.return_value = mock_result
        
        result = await EnhancedGuardianCRUD.get_guardian_students(
            mock_db_session, guardian_user_id, school_id
        )
        
        assert len(result) == 2
        assert all(len(pair) == 2 for pair in result)  # Each should be (student, relationship) tuple
    
    @pytest.mark.asyncio
    async def test_update_guardian_relationship_success(self, mock_db_session):
        """Test successful guardian relationship update"""
        relationship_id = uuid4()
        updated_by = uuid4()
        update_data = {
            'contact_priority': 2,
            'preferred_contact_method': ContactMethod.EMAIL,
            'has_pickup_permission': False
        }
        
        # Mock existing relationship
        mock_relationship = Mock(spec=StudentGuardianRelationship)
        mock_relationship.id = relationship_id
        mock_relationship.student_id = uuid4()
        mock_relationship.guardian_user_id = uuid4()
        mock_relationship.contact_priority = 1
        mock_relationship.preferred_contact_method = ContactMethod.SMS
        mock_relationship.has_pickup_permission = True
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_relationship
        mock_db_session.execute.return_value = mock_result
        
        result = await EnhancedGuardianCRUD.update_guardian_relationship(
            mock_db_session, relationship_id, update_data, updated_by
        )
        
        # Verify fields were updated
        assert mock_relationship.contact_priority == 2
        assert mock_relationship.preferred_contact_method == ContactMethod.EMAIL
        assert mock_relationship.has_pickup_permission is False
        
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ensure_single_primary_contact(self, mock_db_session):
        """Test ensuring only one primary contact exists"""
        student_id = uuid4()
        new_primary_guardian_id = uuid4()
        
        await EnhancedGuardianCRUD._ensure_single_primary_contact(
            mock_db_session, student_id, new_primary_guardian_id
        )
        
        # Should execute update query to set other guardians as non-primary
        mock_db_session.execute.assert_called_once()

class TestEmergencyContactCRUD:
    """Test class for emergency contact management"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session"""
        session = Mock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session
    
    @pytest.fixture
    def emergency_contact_data(self):
        """Create test emergency contact data"""
        return {
            'full_name': 'Jane Doe',
            'relationship_to_student': 'Aunt',
            'primary_phone': '+263771234567',
            'secondary_phone': '+263772345678',
            'email': 'jane.doe@example.com',
            'priority_order': 3,
            'available_24_7': True,
            'can_pickup_student': True,
            'can_authorize_medical_treatment': False,
            'medical_knowledge': 'Student has asthma',
            'languages_spoken': 'English, Shona'
        }
    
    @pytest.mark.asyncio
    async def test_create_emergency_contact_success(self, mock_db_session, emergency_contact_data):
        """Test successful emergency contact creation"""
        student_id = uuid4()
        created_by = uuid4()
        
        with patch.object(EmergencyContactCRUD, '_validate_priority_order') as mock_validate:
            mock_contact = Mock(spec=EmergencyContact)
            mock_contact.id = uuid4()
            
            def mock_add(obj):
                obj.id = mock_contact.id
            
            mock_db_session.add.side_effect = mock_add
            
            result = await EmergencyContactCRUD.create_emergency_contact(
                mock_db_session, student_id, emergency_contact_data, created_by
            )
            
            # Verify priority validation was called
            mock_validate.assert_called_once_with(
                mock_db_session, student_id, emergency_contact_data['priority_order']
            )
            
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_student_emergency_contacts(self, mock_db_session):
        """Test retrieving emergency contacts for student"""
        student_id = uuid4()
        
        # Mock emergency contacts
        mock_contacts = [Mock(spec=EmergencyContact) for _ in range(3)]
        for i, contact in enumerate(mock_contacts):
            contact.id = uuid4()
            contact.student_id = student_id
            contact.full_name = f"Contact {i+1}"
            contact.priority_order = i + 1
            contact.is_active = True
        
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_contacts
        mock_db_session.execute.return_value = mock_result
        
        result = await EmergencyContactCRUD.get_student_emergency_contacts(
            mock_db_session, student_id
        )
        
        assert len(result) == 3
        # Should be ordered by priority
        assert all(c.priority_order == i + 1 for i, c in enumerate(result))
    
    @pytest.mark.asyncio
    async def test_validate_priority_order_conflict(self, mock_db_session):
        """Test priority order validation with conflicts"""
        student_id = uuid4()
        new_priority = 1
        
        # Mock existing contact with same priority
        mock_existing = Mock(spec=EmergencyContact)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_existing
        mock_db_session.execute.return_value = mock_result
        
        await EmergencyContactCRUD._validate_priority_order(
            mock_db_session, student_id, new_priority
        )
        
        # Should execute update to shift existing contacts
        assert mock_db_session.execute.call_count == 2  # Query + Update

class TestFamilyManagementIntegration:
    """Integration tests for family management system"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_family_setup_workflow(self):
        """Test complete family setup including all relationships"""
        # This would test creating a family, adding students, guardians, and emergency contacts
        pytest.skip("Integration test - requires database setup")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_family_data_consistency(self):
        """Test data consistency across family relationships"""
        pytest.skip("Integration test - requires database setup")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_guardian_permissions_enforcement(self):
        """Test guardian permission enforcement in various scenarios"""
        pytest.skip("Integration test - requires permission system setup")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])