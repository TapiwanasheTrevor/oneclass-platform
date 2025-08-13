# =====================================================
# SIS Module - Family Relationship CRUD Operations
# File: backend/services/sis/family_crud.py
# =====================================================

from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_, or_, func, text
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import date, datetime
import logging

from .family_models import (
    StudentGuardianRelationship,
    FamilyGroup,
    StudentFamilyMembership,
    GuardianFamilyMembership,
    EmergencyContact,
    RelationshipType,
    ContactMethod,
    FinancialResponsibilityType
)
from shared.models.platform_user import PlatformUser as User
from shared.models.sis import Student
from .schemas import GuardianRelationshipCreate, GuardianRelationshipUpdate

logger = logging.getLogger(__name__)

class FamilyManagementError(Exception):
    """Base exception for family management operations"""
    pass

class FamilyCRUD:
    """CRUD operations for family management"""
    
    @staticmethod
    async def create_family_group(
        db: Session,
        family_name: str,
        primary_contact_user_id: UUID,
        school_id: UUID,
        created_by_user_id: UUID,
        family_details: Optional[Dict[str, Any]] = None
    ) -> FamilyGroup:
        """Create a new family group"""
        try:
            # Generate unique family code
            family_code = await FamilyCRUD._generate_family_code(db, school_id)
            
            family_group = FamilyGroup(
                school_id=school_id,
                family_name=family_name,
                family_code=family_code,
                primary_contact_user_id=primary_contact_user_id,
                created_by=created_by_user_id,
                **family_details or {}
            )
            
            db.add(family_group)
            await db.commit()
            await db.refresh(family_group)
            
            logger.info(f"Family group created: {family_code} - {family_name}")
            return family_group
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating family group: {str(e)}")
            raise FamilyManagementError(f"Failed to create family group: {str(e)}")
    
    @staticmethod
    async def add_student_to_family(
        db: Session,
        student_id: UUID,
        family_group_id: UUID,
        relationship_details: Optional[Dict[str, Any]] = None
    ) -> StudentFamilyMembership:
        """Add a student to a family group"""
        try:
            # Check if student already belongs to this family
            existing_query = select(StudentFamilyMembership).where(
                and_(
                    StudentFamilyMembership.student_id == student_id,
                    StudentFamilyMembership.family_group_id == family_group_id,
                    StudentFamilyMembership.is_active == True
                )
            )
            result = await db.execute(existing_query)
            if result.scalar_one_or_none():
                raise FamilyManagementError("Student already belongs to this family group")
            
            membership = StudentFamilyMembership(
                student_id=student_id,
                family_group_id=family_group_id,
                **relationship_details or {}
            )
            
            db.add(membership)
            
            # Update family group student count
            await FamilyCRUD._update_family_student_count(db, family_group_id)
            
            await db.commit()
            await db.refresh(membership)
            
            logger.info(f"Student {student_id} added to family {family_group_id}")
            return membership
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error adding student to family: {str(e)}")
            raise
    
    @staticmethod
    async def add_guardian_to_family(
        db: Session,
        guardian_user_id: UUID,
        family_group_id: UUID,
        role_details: Optional[Dict[str, Any]] = None
    ) -> GuardianFamilyMembership:
        """Add a guardian to a family group"""
        try:
            # Check if guardian already belongs to this family
            existing_query = select(GuardianFamilyMembership).where(
                and_(
                    GuardianFamilyMembership.guardian_user_id == guardian_user_id,
                    GuardianFamilyMembership.family_group_id == family_group_id,
                    GuardianFamilyMembership.is_active == True
                )
            )
            result = await db.execute(existing_query)
            if result.scalar_one_or_none():
                raise FamilyManagementError("Guardian already belongs to this family group")
            
            membership = GuardianFamilyMembership(
                guardian_user_id=guardian_user_id,
                family_group_id=family_group_id,
                **role_details or {}
            )
            
            db.add(membership)
            await db.commit()
            await db.refresh(membership)
            
            logger.info(f"Guardian {guardian_user_id} added to family {family_group_id}")
            return membership
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error adding guardian to family: {str(e)}")
            raise
    
    @staticmethod
    async def get_family_students(
        db: Session,
        family_group_id: UUID
    ) -> List[Student]:
        """Get all students in a family group"""
        query = select(Student).join(
            StudentFamilyMembership,
            Student.id == StudentFamilyMembership.student_id
        ).where(
            and_(
                StudentFamilyMembership.family_group_id == family_group_id,
                StudentFamilyMembership.is_active == True
            )
        ).order_by(Student.date_of_birth.desc())  # Eldest first
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_student_families(
        db: Session,
        student_id: UUID
    ) -> List[FamilyGroup]:
        """Get all family groups a student belongs to"""
        query = select(FamilyGroup).join(
            StudentFamilyMembership,
            FamilyGroup.id == StudentFamilyMembership.family_group_id
        ).where(
            and_(
                StudentFamilyMembership.student_id == student_id,
                StudentFamilyMembership.is_active == True,
                FamilyGroup.is_active == True
            )
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def _generate_family_code(db: Session, school_id: UUID) -> str:
        """Generate unique family code for the school"""
        # Get the next sequence number for this school
        query = text("""
            SELECT COALESCE(MAX(CAST(SUBSTRING(family_code FROM '[0-9]+$') AS INTEGER)), 0) + 1
            FROM sis.family_groups 
            WHERE school_id = :school_id 
            AND family_code ~ '^FAM[0-9]+$'
        """)
        
        result = await db.execute(query, {"school_id": school_id})
        next_sequence = result.scalar()
        
        # Format: FAM + 4-digit number (e.g., FAM0001)
        return f"FAM{next_sequence:04d}"
    
    @staticmethod
    async def _update_family_student_count(db: Session, family_group_id: UUID):
        """Update the student count for a family group"""
        count_query = select(func.count(StudentFamilyMembership.id)).where(
            and_(
                StudentFamilyMembership.family_group_id == family_group_id,
                StudentFamilyMembership.is_active == True
            )
        )
        result = await db.execute(count_query)
        student_count = result.scalar()
        
        update_query = update(FamilyGroup).where(
            FamilyGroup.id == family_group_id
        ).values(number_of_students=student_count)
        
        await db.execute(update_query)

class EnhancedGuardianCRUD:
    """Enhanced CRUD operations for guardian relationships"""
    
    @staticmethod
    async def create_comprehensive_guardian_relationship(
        db: Session,
        student_id: UUID,
        guardian_user_id: UUID,
        relationship_data: Dict[str, Any],
        created_by_user_id: UUID
    ) -> StudentGuardianRelationship:
        """Create a comprehensive guardian-student relationship"""
        try:
            # Validate that student exists
            student_query = select(Student).where(Student.id == student_id)
            result = await db.execute(student_query)
            student = result.scalar_one_or_none()
            if not student:
                raise FamilyManagementError(f"Student {student_id} not found")
            
            # Validate that guardian user exists
            guardian_query = select(User).where(User.id == guardian_user_id)
            result = await db.execute(guardian_query)
            guardian = result.scalar_one_or_none()
            if not guardian:
                raise FamilyManagementError(f"Guardian user {guardian_user_id} not found")
            
            # Check if relationship already exists
            existing_query = select(StudentGuardianRelationship).where(
                and_(
                    StudentGuardianRelationship.student_id == student_id,
                    StudentGuardianRelationship.guardian_user_id == guardian_user_id,
                    StudentGuardianRelationship.is_active == True
                )
            )
            result = await db.execute(existing_query)
            if result.scalar_one_or_none():
                raise FamilyManagementError("Guardian relationship already exists")
            
            # Handle primary contact logic
            if relationship_data.get('is_primary_contact', False):
                await EnhancedGuardianCRUD._ensure_single_primary_contact(
                    db, student_id, guardian_user_id
                )
            
            # Create relationship
            relationship = StudentGuardianRelationship(
                student_id=student_id,
                guardian_user_id=guardian_user_id,
                created_by=created_by_user_id,
                **relationship_data
            )
            
            db.add(relationship)
            await db.commit()
            await db.refresh(relationship)
            
            logger.info(f"Guardian relationship created: {guardian_user_id} -> {student_id}")
            return relationship
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating guardian relationship: {str(e)}")
            raise
    
    @staticmethod
    async def get_student_guardians_comprehensive(
        db: Session,
        student_id: UUID,
        include_inactive: bool = False
    ) -> List[StudentGuardianRelationship]:
        """Get all guardians for a student with comprehensive details"""
        query = select(StudentGuardianRelationship).where(
            StudentGuardianRelationship.student_id == student_id
        )
        
        if not include_inactive:
            query = query.where(StudentGuardianRelationship.is_active == True)
        
        query = query.order_by(
            StudentGuardianRelationship.is_primary_contact.desc(),
            StudentGuardianRelationship.contact_priority.asc()
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_guardian_students(
        db: Session,
        guardian_user_id: UUID,
        school_id: Optional[UUID] = None
    ) -> List[Tuple[Student, StudentGuardianRelationship]]:
        """Get all students for a guardian with relationship details"""
        query = select(Student, StudentGuardianRelationship).join(
            StudentGuardianRelationship,
            Student.id == StudentGuardianRelationship.student_id
        ).where(
            and_(
                StudentGuardianRelationship.guardian_user_id == guardian_user_id,
                StudentGuardianRelationship.is_active == True
            )
        )
        
        if school_id:
            query = query.where(Student.school_id == school_id)
        
        query = query.order_by(Student.last_name, Student.first_name)
        
        result = await db.execute(query)
        return list(result.all())
    
    @staticmethod
    async def update_guardian_relationship(
        db: Session,
        relationship_id: UUID,
        update_data: Dict[str, Any],
        updated_by_user_id: UUID
    ) -> StudentGuardianRelationship:
        """Update guardian relationship"""
        try:
            # Get existing relationship
            query = select(StudentGuardianRelationship).where(
                StudentGuardianRelationship.id == relationship_id
            )
            result = await db.execute(query)
            relationship = result.scalar_one_or_none()
            
            if not relationship:
                raise FamilyManagementError(f"Guardian relationship {relationship_id} not found")
            
            # Handle primary contact updates
            if 'is_primary_contact' in update_data and update_data['is_primary_contact']:
                await EnhancedGuardianCRUD._ensure_single_primary_contact(
                    db, relationship.student_id, relationship.guardian_user_id
                )
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(relationship, field):
                    setattr(relationship, field, value)
            
            relationship.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(relationship)
            
            logger.info(f"Guardian relationship updated: {relationship_id}")
            return relationship
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating guardian relationship: {str(e)}")
            raise
    
    @staticmethod
    async def _ensure_single_primary_contact(
        db: Session,
        student_id: UUID,
        new_primary_guardian_id: UUID
    ):
        """Ensure only one primary contact exists for a student"""
        update_query = update(StudentGuardianRelationship).where(
            and_(
                StudentGuardianRelationship.student_id == student_id,
                StudentGuardianRelationship.guardian_user_id != new_primary_guardian_id
            )
        ).values(is_primary_contact=False)
        
        await db.execute(update_query)

class EmergencyContactCRUD:
    """CRUD operations for emergency contacts"""
    
    @staticmethod
    async def create_emergency_contact(
        db: Session,
        student_id: UUID,
        contact_data: Dict[str, Any],
        created_by_user_id: UUID
    ) -> EmergencyContact:
        """Create an emergency contact for a student"""
        try:
            # Validate priority order
            if 'priority_order' in contact_data:
                await EmergencyContactCRUD._validate_priority_order(
                    db, student_id, contact_data['priority_order']
                )
            
            contact = EmergencyContact(
                student_id=student_id,
                created_by=created_by_user_id,
                **contact_data
            )
            
            db.add(contact)
            await db.commit()
            await db.refresh(contact)
            
            logger.info(f"Emergency contact created for student {student_id}")
            return contact
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating emergency contact: {str(e)}")
            raise
    
    @staticmethod
    async def get_student_emergency_contacts(
        db: Session,
        student_id: UUID,
        active_only: bool = True
    ) -> List[EmergencyContact]:
        """Get emergency contacts for a student"""
        query = select(EmergencyContact).where(
            EmergencyContact.student_id == student_id
        )
        
        if active_only:
            query = query.where(EmergencyContact.is_active == True)
        
        query = query.order_by(EmergencyContact.priority_order.asc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def _validate_priority_order(
        db: Session,
        student_id: UUID,
        new_priority: int
    ):
        """Validate and adjust priority orders for emergency contacts"""
        # Check if priority already exists
        existing_query = select(EmergencyContact).where(
            and_(
                EmergencyContact.student_id == student_id,
                EmergencyContact.priority_order == new_priority,
                EmergencyContact.is_active == True
            )
        )
        result = await db.execute(existing_query)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Shift existing contacts down
            update_query = update(EmergencyContact).where(
                and_(
                    EmergencyContact.student_id == student_id,
                    EmergencyContact.priority_order >= new_priority,
                    EmergencyContact.is_active == True
                )
            ).values(priority_order=EmergencyContact.priority_order + 1)
            
            await db.execute(update_query)