# =====================================================
# Bulk Import Processor
# Handle CSV/Excel file processing for user imports
# File: backend/services/files/bulk_processor.py
# =====================================================

import csv
import pandas as pd
import uuid
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Generator
from datetime import datetime, timedelta
from pathlib import Path
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.platform_user import (
    PlatformRole,
    SchoolRole,
    PlatformUser,
    SchoolMembership,
)
from shared.models.platform import School
from services.auth.utils import hash_password
from .schemas import BulkImportProgress, BulkImportMapping, BulkImportTemplate

logger = logging.getLogger(__name__)


class BulkImportProcessor:
    """Process bulk import files for user creation"""

    def __init__(self):
        self.supported_formats = ["csv", "xlsx", "xls"]
        self.max_batch_size = 100
        self.progress_cache = {}  # In production, use Redis or database

        # Field mappings for different import types
        self.field_mappings = {
            "users": {
                "required": ["email", "first_name", "last_name", "role"],
                "optional": [
                    "phone",
                    "department",
                    "employee_id",
                    "student_id",
                    "grade",
                    "parent_email",
                ],
                "defaults": {"platform_role": "student", "status": "active"},
            },
            "students": {
                "required": ["email", "first_name", "last_name", "grade"],
                "optional": [
                    "student_id",
                    "parent_email",
                    "parent_phone",
                    "address",
                    "date_of_birth",
                ],
                "defaults": {"platform_role": "student", "school_role": "student"},
            },
            "staff": {
                "required": ["email", "first_name", "last_name", "role", "department"],
                "optional": [
                    "employee_id",
                    "phone",
                    "hire_date",
                    "subjects",
                    "qualifications",
                ],
                "defaults": {"platform_role": "teacher", "school_role": "teacher"},
            },
        }

    async def validate_file(self, file_path: str, import_type: str) -> Dict[str, Any]:
        """Validate import file structure and data"""
        try:
            # Read file to get structure
            df = await self._read_file(file_path)

            validation_result = {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "total_rows": len(df),
                "columns": list(df.columns),
                "preview_data": df.head(5).to_dict("records"),
                "mapping_suggestions": {},
                "data_types": df.dtypes.to_dict(),
            }

            # Check required fields
            field_config = self.field_mappings.get(import_type, {})
            required_fields = field_config.get("required", [])

            # Auto-detect column mappings
            column_mapping = self._auto_detect_mappings(df.columns, required_fields)
            validation_result["mapping_suggestions"] = column_mapping

            # Validate required fields are mappable
            missing_required = []
            for field in required_fields:
                if field not in column_mapping.values():
                    missing_required.append(field)

            if missing_required:
                validation_result["is_valid"] = False
                validation_result["errors"].append(
                    f"Required fields not found or mappable: {missing_required}"
                )

            # Validate data quality
            data_validation = await self._validate_data_quality(
                df, import_type, column_mapping
            )
            validation_result["errors"].extend(data_validation["errors"])
            validation_result["warnings"].extend(data_validation["warnings"])

            if data_validation["errors"]:
                validation_result["is_valid"] = False

            return validation_result

        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            return {
                "is_valid": False,
                "errors": [f"File validation failed: {str(e)}"],
                "warnings": [],
                "total_rows": 0,
                "columns": [],
                "preview_data": [],
                "mapping_suggestions": {},
            }

    async def _read_file(self, file_path: str) -> pd.DataFrame:
        """Read CSV or Excel file into DataFrame"""
        file_ext = Path(file_path).suffix.lower()

        if file_ext == ".csv":
            # Try different encodings and delimiters
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                for delimiter in [",", ";", "\t"]:
                    try:
                        df = pd.read_csv(
                            file_path, encoding=encoding, delimiter=delimiter
                        )
                        if len(df.columns) > 1:  # Successfully parsed
                            return df
                    except:
                        continue

            # Fallback to basic CSV read
            return pd.read_csv(file_path)

        elif file_ext in [".xlsx", ".xls"]:
            return pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")

    def _auto_detect_mappings(
        self, columns: List[str], required_fields: List[str]
    ) -> Dict[str, str]:
        """Auto-detect column to field mappings"""
        mapping = {}

        # Common column name variations
        field_variations = {
            "email": ["email", "email_address", "e-mail", "mail"],
            "first_name": [
                "first_name",
                "firstname",
                "first name",
                "given_name",
                "fname",
            ],
            "last_name": [
                "last_name",
                "lastname",
                "last name",
                "surname",
                "family_name",
                "lname",
            ],
            "phone": ["phone", "phone_number", "mobile", "cell", "telephone"],
            "role": ["role", "position", "job_title", "designation"],
            "department": ["department", "dept", "division", "faculty"],
            "employee_id": ["employee_id", "emp_id", "staff_id", "worker_id"],
            "student_id": [
                "student_id",
                "student_number",
                "registration_number",
                "reg_no",
            ],
            "grade": ["grade", "class", "year", "level", "form"],
            "date_of_birth": ["date_of_birth", "dob", "birth_date", "birthdate"],
            "address": ["address", "home_address", "residential_address"],
            "parent_email": ["parent_email", "guardian_email", "parent_mail"],
            "parent_phone": ["parent_phone", "guardian_phone", "parent_mobile"],
        }

        # Convert columns to lowercase for comparison
        columns_lower = [col.lower().strip() for col in columns]

        for field, variations in field_variations.items():
            for variation in variations:
                if variation.lower() in columns_lower:
                    # Find original column name
                    original_col = columns[columns_lower.index(variation.lower())]
                    mapping[original_col] = field
                    break

        return mapping

    async def _validate_data_quality(
        self, df: pd.DataFrame, import_type: str, mapping: Dict[str, str]
    ) -> Dict[str, List[str]]:
        """Validate data quality in the import file"""
        errors = []
        warnings = []

        # Reverse mapping for easier lookup
        field_to_col = {v: k for k, v in mapping.items()}

        # Email validation
        if "email" in field_to_col:
            email_col = field_to_col["email"]
            if email_col in df.columns:
                # Check for missing emails
                missing_emails = df[email_col].isna().sum()
                if missing_emails > 0:
                    errors.append(f"{missing_emails} rows have missing email addresses")

                # Check for duplicate emails
                duplicates = df[email_col].duplicated().sum()
                if duplicates > 0:
                    warnings.append(f"{duplicates} duplicate email addresses found")

                # Basic email format validation
                email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                invalid_emails = ~df[email_col].str.match(email_pattern, na=False)
                invalid_count = invalid_emails.sum()
                if invalid_count > 0:
                    errors.append(f"{invalid_count} invalid email formats found")

        # Name validation
        for name_field in ["first_name", "last_name"]:
            if name_field in field_to_col:
                name_col = field_to_col[name_field]
                if name_col in df.columns:
                    missing_names = df[name_col].isna().sum()
                    if missing_names > 0:
                        errors.append(f"{missing_names} rows have missing {name_field}")

        # Role validation
        if "role" in field_to_col:
            role_col = field_to_col["role"]
            if role_col in df.columns:
                valid_roles = [role.value for role in SchoolRole]
                invalid_roles = ~df[role_col].isin(valid_roles)
                invalid_count = invalid_roles.sum()
                if invalid_count > 0:
                    warnings.append(f"{invalid_count} rows have unrecognized roles")

        # Grade validation for students
        if import_type == "students" and "grade" in field_to_col:
            grade_col = field_to_col["grade"]
            if grade_col in df.columns:
                missing_grades = df[grade_col].isna().sum()
                if missing_grades > 0:
                    warnings.append(
                        f"{missing_grades} students have missing grade information"
                    )

        return {"errors": errors, "warnings": warnings}

    async def process_import(
        self,
        db: AsyncSession,
        file_path: str,
        school_id: uuid.UUID,
        import_type: str,
        column_mapping: Dict[str, str],
        uploaded_by: uuid.UUID,
        dry_run: bool = False,
    ) -> str:
        """Process bulk import file"""

        import_id = str(uuid.uuid4())

        try:
            # Read file
            df = await self._read_file(file_path)

            # Initialize progress tracking
            progress = BulkImportProgress(
                import_id=import_id,
                status="processing",
                total_records=len(df),
                processed_records=0,
                successful_records=0,
                failed_records=0,
                progress_percentage=0.0,
                errors=[],
                warnings=[],
            )
            self.progress_cache[import_id] = progress

            # Process in batches
            batch_size = min(self.max_batch_size, len(df))
            successful_users = []
            failed_records = []

            for start_idx in range(0, len(df), batch_size):
                end_idx = min(start_idx + batch_size, len(df))
                batch = df.iloc[start_idx:end_idx]

                batch_results = await self._process_batch(
                    db,
                    batch,
                    school_id,
                    import_type,
                    column_mapping,
                    uploaded_by,
                    dry_run,
                )

                successful_users.extend(batch_results["successful"])
                failed_records.extend(batch_results["failed"])

                # Update progress
                progress.processed_records = end_idx
                progress.successful_records = len(successful_users)
                progress.failed_records = len(failed_records)
                progress.progress_percentage = (end_idx / len(df)) * 100
                progress.errors = [
                    {"row": r["row"], "error": r["error"]} for r in failed_records
                ]

                self.progress_cache[import_id] = progress

                # Small delay to prevent overwhelming the database
                await asyncio.sleep(0.1)

            # Finalize
            if not dry_run:
                await db.commit()

            progress.status = "completed"
            progress.estimated_completion = datetime.utcnow()
            self.progress_cache[import_id] = progress

            logger.info(
                f"Import {import_id} completed: {len(successful_users)} successful, {len(failed_records)} failed"
            )

            return import_id

        except Exception as e:
            logger.error(f"Import {import_id} failed: {str(e)}")
            if import_id in self.progress_cache:
                self.progress_cache[import_id].status = "failed"
                self.progress_cache[import_id].errors.append({"error": str(e)})

            await db.rollback()
            raise

    async def _process_batch(
        self,
        db: AsyncSession,
        batch: pd.DataFrame,
        school_id: uuid.UUID,
        import_type: str,
        column_mapping: Dict[str, str],
        uploaded_by: uuid.UUID,
        dry_run: bool,
    ) -> Dict[str, List]:
        """Process a batch of records"""

        successful = []
        failed = []

        # Reverse mapping
        field_to_col = {v: k for k, v in column_mapping.items()}

        for idx, row in batch.iterrows():
            try:
                # Extract user data
                user_data = self._extract_user_data(row, field_to_col, import_type)

                if not dry_run:
                    # Create user
                    user = await self._create_user_from_import(db, user_data, school_id)
                    successful.append(
                        {
                            "row": idx,
                            "email": user_data["email"],
                            "user_id": str(user.id) if user else None,
                        }
                    )
                else:
                    # Just validate
                    successful.append(
                        {
                            "row": idx,
                            "email": user_data["email"],
                            "validation": "passed",
                        }
                    )

            except Exception as e:
                failed.append(
                    {
                        "row": idx,
                        "email": row.get(field_to_col.get("email", ""), "unknown"),
                        "error": str(e),
                    }
                )

        return {"successful": successful, "failed": failed}

    def _extract_user_data(
        self, row: pd.Series, field_mapping: Dict[str, str], import_type: str
    ) -> Dict[str, Any]:
        """Extract user data from a row based on field mapping"""

        user_data = {}

        # Required fields
        for field in ["email", "first_name", "last_name"]:
            if field in field_mapping:
                col_name = field_mapping[field]
                value = row.get(col_name)
                if pd.isna(value) or value == "":
                    raise ValueError(f"Missing required field: {field}")
                user_data[field] = str(value).strip()

        # Optional fields
        optional_fields = [
            "phone",
            "department",
            "employee_id",
            "student_id",
            "grade",
            "parent_email",
            "parent_phone",
            "address",
            "date_of_birth",
        ]

        for field in optional_fields:
            if field in field_mapping:
                col_name = field_mapping[field]
                value = row.get(col_name)
                if not pd.isna(value) and value != "":
                    user_data[field] = str(value).strip()

        # Handle roles
        if "role" in field_mapping:
            role_value = row.get(field_mapping["role"])
            if not pd.isna(role_value):
                user_data["school_role"] = str(role_value).strip()

        # Set defaults based on import type
        defaults = self.field_mappings.get(import_type, {}).get("defaults", {})
        for key, value in defaults.items():
            if key not in user_data:
                user_data[key] = value

        return user_data

    async def _create_user_from_import(
        self, db: AsyncSession, user_data: Dict[str, Any], school_id: uuid.UUID
    ) -> Optional[PlatformUserDB]:
        """Create user from import data"""

        # Check if user already exists
        from sqlalchemy import select

        existing_query = select(PlatformUserDB).where(
            PlatformUserDB.email == user_data["email"].lower()
        )
        result = await db.execute(existing_query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            # Add school membership to existing user
            membership = SchoolMembership(
                id=uuid.uuid4(),
                user_id=existing_user.id,
                school_id=school_id,
                school_name="",  # Will be filled by caller
                school_subdomain="",  # Will be filled by caller
                role=user_data.get("school_role", SchoolRole.STUDENT.value),
                permissions=[],
                status="active",
                joined_date=datetime.utcnow(),
                department=user_data.get("department"),
                employee_id=user_data.get("employee_id"),
                student_id=user_data.get("student_id"),
                current_grade=user_data.get("grade"),
            )
            db.add(membership)
            return existing_user

        # Create new user
        profile_data = {
            "phone_number": user_data.get("phone"),
            "address": user_data.get("address"),
            "emergency_contact_name": user_data.get("parent_email"),
            "emergency_contact_phone": user_data.get("parent_phone"),
        }

        user = PlatformUserDB(
            id=uuid.uuid4(),
            email=user_data["email"].lower(),
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            platform_role=user_data.get("platform_role", PlatformRole.STUDENT.value),
            status="active",
            primary_school_id=school_id,
            profile=profile_data,
            created_at=datetime.utcnow(),
        )

        db.add(user)
        await db.flush()  # Get user ID

        # Create school membership
        membership = SchoolMembership(
            id=uuid.uuid4(),
            user_id=user.id,
            school_id=school_id,
            school_name="",  # Will be filled by caller
            school_subdomain="",  # Will be filled by caller
            role=user_data.get("school_role", SchoolRole.STUDENT.value),
            permissions=[],
            status="active",
            joined_date=datetime.utcnow(),
            department=user_data.get("department"),
            employee_id=user_data.get("employee_id"),
            student_id=user_data.get("student_id"),
            current_grade=user_data.get("grade"),
        )

        db.add(membership)
        return user

    def get_import_progress(self, import_id: str) -> Optional[BulkImportProgress]:
        """Get import progress by ID"""
        return self.progress_cache.get(import_id)

    def get_import_template(self, import_type: str) -> BulkImportTemplate:
        """Get import template for specified type"""

        field_config = self.field_mappings.get(import_type, {})

        templates = {
            "users": {
                "template_name": "General Users Import",
                "description": "Import any type of user (students, teachers, staff)",
                "example_data": [
                    {
                        "email": "john.doe@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "role": "teacher",
                        "department": "Mathematics",
                        "phone": "+263771234567",
                    }
                ],
            },
            "students": {
                "template_name": "Students Import",
                "description": "Import student records with academic information",
                "example_data": [
                    {
                        "email": "student@example.com",
                        "first_name": "Jane",
                        "last_name": "Smith",
                        "grade": "Form 4A",
                        "student_id": "STU001",
                        "parent_email": "parent@example.com",
                    }
                ],
            },
            "staff": {
                "template_name": "Staff Import",
                "description": "Import teaching and non-teaching staff",
                "example_data": [
                    {
                        "email": "teacher@example.com",
                        "first_name": "Bob",
                        "last_name": "Johnson",
                        "role": "teacher",
                        "department": "Science",
                        "employee_id": "EMP001",
                    }
                ],
            },
        }

        template_info = templates.get(import_type, templates["users"])

        return BulkImportTemplate(
            import_type=import_type,
            template_name=template_info["template_name"],
            required_columns=field_config.get("required", []),
            optional_columns=field_config.get("optional", []),
            column_descriptions={
                "email": "User email address (must be unique)",
                "first_name": "User first name",
                "last_name": "User last name",
                "role": "User role in school (teacher, student, etc.)",
                "department": "Department or subject area",
                "phone": "Contact phone number",
                "grade": "Student grade/class (for students)",
                "employee_id": "Employee ID (for staff)",
                "student_id": "Student ID (for students)",
            },
            example_data=template_info["example_data"],
            validation_rules={
                "email": ["required", "unique", "valid_email"],
                "first_name": ["required", "max_length:100"],
                "last_name": ["required", "max_length:100"],
                "role": ["required", "valid_role"],
                "phone": ["valid_phone"],
                "grade": ["required_for_students"],
            },
        )
