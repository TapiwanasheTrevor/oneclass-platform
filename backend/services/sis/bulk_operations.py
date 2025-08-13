# =====================================================
# SIS Module - Bulk Import/Export Operations
# File: backend/services/sis/bulk_operations.py
# =====================================================

import csv
import json
import io
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime
from uuid import UUID
import logging
from sqlalchemy.orm import Session
from sqlalchemy import select

from .schemas import (
    StudentCreate,
    Gender,
    HomeLanguage,
    BloodType,
    EmergencyContact,
    ZimbabweAddress,
    MedicalCondition,
    Allergy
)
from .crud import StudentCRUD
from .zimbabwe_validators import ZimbabweValidator
from shared.models.sis import Student

logger = logging.getLogger(__name__)

class BulkOperationError(Exception):
    """Base exception for bulk operations"""
    pass

class BulkImportService:
    """Service for bulk importing students from CSV/Excel files"""
    
    # Column mappings for import
    REQUIRED_COLUMNS = [
        'first_name', 'last_name', 'date_of_birth', 'gender', 'grade_level'
    ]
    
    OPTIONAL_COLUMNS = [
        'middle_name', 'preferred_name', 'nationality', 'home_language',
        'religion', 'tribe', 'mobile_number', 'email',
        'national_id', 'birth_certificate', 'passport_number',
        'residential_street', 'residential_suburb', 'residential_city', 'residential_province',
        'blood_type', 'medical_aid_provider', 'medical_aid_number',
        'previous_school', 'transfer_reason', 'transport_needs',
        'parent1_name', 'parent1_phone', 'parent1_email', 'parent1_relationship',
        'parent2_name', 'parent2_phone', 'parent2_email', 'parent2_relationship',
        'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship'
    ]
    
    @staticmethod
    async def import_from_csv(
        db: Session,
        file_content: bytes,
        school_id: UUID,
        created_by_user_id: UUID,
        validate_only: bool = False
    ) -> Dict[str, Any]:
        """
        Import students from CSV file
        Returns: Dict with results including successful imports, errors, and warnings
        """
        try:
            # Parse CSV
            csv_file = io.StringIO(file_content.decode('utf-8'))
            reader = csv.DictReader(csv_file)
            
            results = {
                'total_rows': 0,
                'successful': 0,
                'failed': 0,
                'errors': [],
                'warnings': [],
                'imported_students': []
            }
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                results['total_rows'] += 1
                
                try:
                    # Validate and process row
                    student_data = await BulkImportService._process_csv_row(
                        row, row_num, school_id
                    )
                    
                    if validate_only:
                        results['warnings'].append({
                            'row': row_num,
                            'message': 'Validation passed',
                            'student': f"{row.get('first_name')} {row.get('last_name')}"
                        })
                    else:
                        # Create student
                        student = await StudentCRUD.create_student_full_workflow(
                            db, student_data, school_id, created_by_user_id
                        )
                        
                        results['successful'] += 1
                        results['imported_students'].append({
                            'id': str(student.id),
                            'student_number': student.student_number,
                            'name': f"{student.first_name} {student.last_name}"
                        })
                        
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({
                        'row': row_num,
                        'error': str(e),
                        'student': f"{row.get('first_name', 'Unknown')} {row.get('last_name', 'Unknown')}"
                    })
                    
                    if not validate_only:
                        # Continue with next row on error
                        continue
            
            if not validate_only:
                await db.commit()
                logger.info(f"Bulk import completed: {results['successful']} students imported")
            
            return results
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Bulk import failed: {str(e)}")
            raise BulkOperationError(f"Import failed: {str(e)}")
    
    @staticmethod
    async def import_from_excel(
        db: Session,
        file_content: bytes,
        school_id: UUID,
        created_by_user_id: UUID,
        sheet_name: Optional[str] = None,
        validate_only: bool = False
    ) -> Dict[str, Any]:
        """Import students from Excel file"""
        try:
            # Read Excel file
            excel_file = io.BytesIO(file_content)
            df = pd.read_excel(excel_file, sheet_name=sheet_name or 0)
            
            # Convert to CSV format and process
            csv_content = df.to_csv(index=False).encode('utf-8')
            
            return await BulkImportService.import_from_csv(
                db, csv_content, school_id, created_by_user_id, validate_only
            )
            
        except Exception as e:
            logger.error(f"Excel import failed: {str(e)}")
            raise BulkOperationError(f"Excel import failed: {str(e)}")
    
    @staticmethod
    async def _process_csv_row(
        row: Dict[str, str],
        row_num: int,
        school_id: UUID
    ) -> StudentCreate:
        """Process and validate a CSV row"""
        
        # Check required fields
        for field in BulkImportService.REQUIRED_COLUMNS:
            if not row.get(field):
                raise ValueError(f"Missing required field: {field}")
        
        # Parse date of birth
        try:
            dob_str = row['date_of_birth'].strip()
            # Try multiple date formats
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']:
                try:
                    dob = datetime.strptime(dob_str, fmt).date()
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Invalid date format: {dob_str}")
        except Exception as e:
            raise ValueError(f"Invalid date of birth: {str(e)}")
        
        # Validate and format phone numbers
        mobile_number = None
        if row.get('mobile_number'):
            valid, formatted = ZimbabweValidator.validate_phone_number(row['mobile_number'])
            if valid:
                mobile_number = formatted
            else:
                logger.warning(f"Row {row_num}: Invalid mobile number: {row['mobile_number']}")
        
        # Process address
        residential_address = ZimbabweAddress(
            street=row.get('residential_street', 'Not Provided'),
            suburb=row.get('residential_suburb', 'Not Provided'),
            city=row.get('residential_city', 'Harare'),
            province=row.get('residential_province', 'Harare')
        )
        
        # Process emergency contacts
        emergency_contacts = []
        
        # Parent 1 as emergency contact
        if row.get('parent1_name') and row.get('parent1_phone'):
            valid_phone, formatted_phone = ZimbabweValidator.validate_phone_number(
                row['parent1_phone']
            )
            if valid_phone:
                emergency_contacts.append(EmergencyContact(
                    name=row['parent1_name'],
                    relationship=row.get('parent1_relationship', 'Parent'),
                    phone=formatted_phone,
                    is_primary=True,
                    can_pickup=True
                ))
        
        # Parent 2 as emergency contact
        if row.get('parent2_name') and row.get('parent2_phone'):
            valid_phone, formatted_phone = ZimbabweValidator.validate_phone_number(
                row['parent2_phone']
            )
            if valid_phone:
                emergency_contacts.append(EmergencyContact(
                    name=row['parent2_name'],
                    relationship=row.get('parent2_relationship', 'Parent'),
                    phone=formatted_phone,
                    is_primary=len(emergency_contacts) == 0,
                    can_pickup=True
                ))
        
        # Additional emergency contact
        if row.get('emergency_contact_name') and row.get('emergency_contact_phone'):
            valid_phone, formatted_phone = ZimbabweValidator.validate_phone_number(
                row['emergency_contact_phone']
            )
            if valid_phone:
                emergency_contacts.append(EmergencyContact(
                    name=row['emergency_contact_name'],
                    relationship=row.get('emergency_contact_relationship', 'Emergency Contact'),
                    phone=formatted_phone,
                    is_primary=len(emergency_contacts) == 0,
                    can_pickup=False
                ))
        
        # Ensure at least 2 emergency contacts (requirement)
        if len(emergency_contacts) < 2:
            # Add a default school contact
            emergency_contacts.append(EmergencyContact(
                name="School Office",
                relationship="School",
                phone="+263242123456",  # Default school number
                is_primary=len(emergency_contacts) == 0,
                can_pickup=False
            ))
        
        # Process medical information
        medical_conditions = []
        allergies = []
        
        # Parse medical conditions if provided in a specific column
        if row.get('medical_conditions'):
            conditions = row['medical_conditions'].split(';')
            for condition in conditions:
                if condition.strip():
                    medical_conditions.append(MedicalCondition(
                        condition=condition.strip(),
                        severity="Moderate",
                        notes="Imported from bulk upload"
                    ))
        
        # Parse allergies if provided
        if row.get('allergies'):
            allergy_list = row['allergies'].split(';')
            for allergy in allergy_list:
                if allergy.strip():
                    allergies.append(Allergy(
                        allergen=allergy.strip(),
                        reaction="Unknown",
                        severity="Moderate",
                        epipen_required=False
                    ))
        
        # Create StudentCreate object
        student_data = StudentCreate(
            first_name=row['first_name'].strip().title(),
            middle_name=row.get('middle_name', '').strip().title() or None,
            last_name=row['last_name'].strip().title(),
            preferred_name=row.get('preferred_name', '').strip() or None,
            date_of_birth=dob,
            gender=Gender(row['gender'].strip().title()),
            nationality=row.get('nationality', 'Zimbabwean').strip(),
            home_language=HomeLanguage(row['home_language'].strip().title()) if row.get('home_language') else None,
            religion=row.get('religion', '').strip() or None,
            tribe=row.get('tribe', '').strip() or None,
            mobile_number=mobile_number,
            email=row.get('email', '').strip() or None,
            residential_address=residential_address,
            current_grade_level=int(row['grade_level']),
            enrollment_date=date.today(),
            previous_school_name=row.get('previous_school', '').strip() or None,
            transfer_reason=row.get('transfer_reason', '').strip() or None,
            blood_type=BloodType(row['blood_type'].strip().upper()) if row.get('blood_type') else None,
            medical_conditions=medical_conditions,
            allergies=allergies,
            medical_aid_provider=row.get('medical_aid_provider', '').strip() or None,
            medical_aid_number=row.get('medical_aid_number', '').strip() or None,
            transport_needs=row.get('transport_needs', '').strip() or None,
            emergency_contacts=emergency_contacts
        )
        
        return student_data
    
    @staticmethod
    def generate_import_template() -> bytes:
        """Generate a CSV template for bulk import"""
        headers = BulkImportService.REQUIRED_COLUMNS + BulkImportService.OPTIONAL_COLUMNS
        
        # Add sample data
        sample_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'middle_name': 'James',
            'date_of_birth': '2010-05-15',
            'gender': 'Male',
            'grade_level': '5',
            'nationality': 'Zimbabwean',
            'home_language': 'English',
            'religion': 'Christian',
            'mobile_number': '0771234567',
            'email': 'john.doe@example.com',
            'residential_street': '123 Main Street',
            'residential_suburb': 'Borrowdale',
            'residential_city': 'Harare',
            'residential_province': 'Harare',
            'blood_type': 'O+',
            'medical_aid_provider': 'PSMAS',
            'medical_aid_number': '123456789',
            'parent1_name': 'Jane Doe',
            'parent1_phone': '0772345678',
            'parent1_email': 'jane.doe@example.com',
            'parent1_relationship': 'Mother',
            'parent2_name': 'James Doe',
            'parent2_phone': '0773456789',
            'parent2_email': 'james.doe@example.com',
            'parent2_relationship': 'Father'
        }
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        
        # Write sample row
        writer.writerow(sample_data)
        
        # Add a few empty rows for user to fill
        for _ in range(5):
            writer.writerow({col: '' for col in headers})
        
        return output.getvalue().encode('utf-8')


class BulkExportService:
    """Service for bulk exporting student data"""
    
    @staticmethod
    async def export_to_csv(
        db: Session,
        school_id: UUID,
        filters: Optional[Dict[str, Any]] = None,
        include_sensitive: bool = False
    ) -> bytes:
        """Export students to CSV format"""
        
        # Build query
        query = select(Student).where(Student.school_id == school_id)
        
        # Apply filters
        if filters:
            if filters.get('grade_level'):
                query = query.where(Student.current_grade_level == filters['grade_level'])
            if filters.get('status'):
                query = query.where(Student.status == filters['status'])
            if filters.get('class_id'):
                query = query.where(Student.current_class_id == filters['class_id'])
        
        # Execute query
        result = await db.execute(query.order_by(Student.last_name, Student.first_name))
        students = result.scalars().all()
        
        # Prepare CSV
        output = io.StringIO()
        
        # Define columns based on sensitivity
        if include_sensitive:
            fieldnames = [
                'student_number', 'first_name', 'middle_name', 'last_name',
                'date_of_birth', 'gender', 'nationality', 'home_language',
                'grade_level', 'status', 'enrollment_date',
                'mobile_number', 'email', 'blood_type',
                'medical_aid_provider', 'medical_aid_number',
                'residential_address', 'transport_needs'
            ]
        else:
            fieldnames = [
                'student_number', 'first_name', 'last_name',
                'gender', 'grade_level', 'status', 'enrollment_date'
            ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write student data
        for student in students:
            row = {
                'student_number': student.student_number,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'gender': student.gender,
                'grade_level': student.current_grade_level,
                'status': student.status,
                'enrollment_date': student.enrollment_date.strftime('%Y-%m-%d')
            }
            
            if include_sensitive:
                row.update({
                    'middle_name': student.middle_name or '',
                    'date_of_birth': student.date_of_birth.strftime('%Y-%m-%d'),
                    'nationality': student.nationality or 'Zimbabwean',
                    'home_language': student.home_language or '',
                    'mobile_number': student.mobile_number or '',
                    'email': student.email or '',
                    'blood_type': student.blood_type or '',
                    'medical_aid_provider': student.medical_aid_provider or '',
                    'medical_aid_number': student.medical_aid_number or '',
                    'residential_address': json.dumps(student.residential_address) if student.residential_address else '',
                    'transport_needs': student.transport_needs or ''
                })
            
            writer.writerow(row)
        
        return output.getvalue().encode('utf-8')
    
    @staticmethod
    async def export_to_excel(
        db: Session,
        school_id: UUID,
        filters: Optional[Dict[str, Any]] = None,
        include_sensitive: bool = False
    ) -> bytes:
        """Export students to Excel format"""
        
        # Get CSV data first
        csv_data = await BulkExportService.export_to_csv(
            db, school_id, filters, include_sensitive
        )
        
        # Convert CSV to DataFrame
        csv_file = io.StringIO(csv_data.decode('utf-8'))
        df = pd.read_csv(csv_file)
        
        # Write to Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Students', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Students']
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[chr(65 + col_idx)].width = min(column_width + 2, 50)
        
        output.seek(0)
        return output.read()
    
    @staticmethod
    async def export_class_list(
        db: Session,
        class_id: UUID,
        format: str = 'pdf'
    ) -> bytes:
        """Export a formatted class list for printing"""
        
        # Query students in the class
        query = select(Student).where(
            Student.current_class_id == class_id,
            Student.status == 'active'
        ).order_by(Student.last_name, Student.first_name)
        
        result = await db.execute(query)
        students = result.scalars().all()
        
        if format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow(['#', 'Student Number', 'Name', 'Gender', 'Date of Birth'])
            
            # Student rows
            for idx, student in enumerate(students, 1):
                name = f"{student.last_name}, {student.first_name}"
                if student.middle_name:
                    name += f" {student.middle_name}"
                
                writer.writerow([
                    idx,
                    student.student_number,
                    name,
                    student.gender,
                    student.date_of_birth.strftime('%d/%m/%Y')
                ])
            
            return output.getvalue().encode('utf-8')
        
        # For PDF format, would need additional library like reportlab
        # Returning CSV for now
        return await BulkExportService.export_class_list(db, class_id, 'csv')