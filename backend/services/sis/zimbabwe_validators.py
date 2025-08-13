# =====================================================
# SIS Module - Zimbabwe-Specific Validators
# File: backend/services/sis/zimbabwe_validators.py
# =====================================================

import re
from typing import Optional, Tuple
from datetime import date, datetime
from enum import Enum

class ZimbabweIDType(str, Enum):
    NATIONAL_ID = "national_id"
    BIRTH_CERTIFICATE = "birth_certificate"
    PASSPORT = "passport"

class ZimbabweValidator:
    """Validators for Zimbabwe-specific data formats and requirements"""
    
    @staticmethod
    def validate_national_id(national_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Zimbabwe National ID format
        Format: 00-000000-X-00 where X is a letter
        Example: 63-123456-K-23
        """
        if not national_id:
            return True, None  # Optional field
            
        # Remove spaces and convert to uppercase
        national_id = national_id.replace(" ", "").replace("-", "").upper()
        
        # Check basic format: 2 digits + 6 digits + 1 letter + 2 digits
        pattern = r'^[0-9]{2}[0-9]{6}[A-Z][0-9]{2}$'
        
        if not re.match(pattern, national_id):
            return False, "Invalid National ID format. Expected: 00-000000-X-00"
        
        # Validate province code (first 2 digits)
        province_code = int(national_id[:2])
        valid_province_codes = list(range(1, 11)) + list(range(41, 51)) + list(range(61, 71))
        
        if province_code not in valid_province_codes:
            return False, f"Invalid province code: {province_code}"
        
        # Format with hyphens for storage
        formatted_id = f"{national_id[:2]}-{national_id[2:8]}-{national_id[8]}-{national_id[9:]}"
        
        return True, formatted_id
    
    @staticmethod
    def validate_birth_certificate(birth_cert_number: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Zimbabwe Birth Certificate Number
        Format varies but typically: XXXXXX/YY where X is numeric and YY is year
        Example: 123456/23 or B123456
        """
        if not birth_cert_number:
            return True, None
            
        birth_cert_number = birth_cert_number.strip().upper()
        
        # Pattern 1: New format (6 digits / 2 digit year)
        pattern1 = r'^[0-9]{6}/[0-9]{2}$'
        # Pattern 2: Old format (Letter + 6 digits)
        pattern2 = r'^[A-Z][0-9]{6}$'
        # Pattern 3: Alternative format (just numbers)
        pattern3 = r'^[0-9]{7,10}$'
        
        if re.match(pattern1, birth_cert_number):
            return True, birth_cert_number
        elif re.match(pattern2, birth_cert_number):
            return True, birth_cert_number
        elif re.match(pattern3, birth_cert_number):
            return True, birth_cert_number
        else:
            return False, "Invalid Birth Certificate format. Expected formats: 123456/23, B123456, or numeric sequence"
    
    @staticmethod
    def validate_phone_number(phone: str, allow_international: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Validate Zimbabwe phone number
        Formats accepted:
        - Local: 0712345678 (10 digits starting with 0)
        - International: +263712345678 or 263712345678
        - Landline: 024-2123456 or 0242123456
        """
        if not phone:
            return True, None
            
        # Remove all spaces, hyphens, and parentheses
        phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Check for international format
        if phone.startswith('+263'):
            phone = phone[4:]
            if len(phone) == 9 and phone[0] in '7':  # Mobile
                return True, f"+263{phone}"
            elif len(phone) in [9, 10] and phone[0] in '2468':  # Landline
                return True, f"+263{phone}"
        elif phone.startswith('263'):
            phone = phone[3:]
            if len(phone) == 9 and phone[0] in '7':  # Mobile
                return True, f"+263{phone}"
            elif len(phone) in [9, 10] and phone[0] in '2468':  # Landline
                return True, f"+263{phone}"
        elif phone.startswith('0'):
            if len(phone) == 10 and phone[1] in '7':  # Mobile
                return True, f"+263{phone[1:]}"
            elif len(phone) in [10, 11] and phone[1] in '2468':  # Landline
                return True, f"+263{phone[1:]}"
        
        return False, "Invalid Zimbabwe phone number. Use format: 0712345678 or +263712345678"
    
    @staticmethod
    def validate_medical_aid_number(provider: str, number: str) -> Tuple[bool, Optional[str]]:
        """
        Validate medical aid number based on provider
        Common providers: PSMAS, CIMAS, First Mutual, Premier Service
        """
        if not provider or not number:
            return True, None
            
        provider_upper = provider.upper()
        number = number.strip().upper()
        
        # PSMAS format validation
        if 'PSMAS' in provider_upper:
            # PSMAS numbers are typically 9-10 digits
            if re.match(r'^[0-9]{9,10}$', number):
                return True, number
            else:
                return False, "PSMAS number should be 9-10 digits"
        
        # CIMAS format validation
        elif 'CIMAS' in provider_upper:
            # CIMAS uses various formats including alphanumeric
            if re.match(r'^[A-Z0-9]{6,12}$', number):
                return True, number
            else:
                return False, "CIMAS number should be 6-12 alphanumeric characters"
        
        # First Mutual format
        elif 'FIRST MUTUAL' in provider_upper or 'FIRSTMUTUAL' in provider_upper:
            if re.match(r'^[A-Z0-9]{8,15}$', number):
                return True, number
            else:
                return False, "First Mutual number should be 8-15 alphanumeric characters"
        
        # Generic validation for other providers
        else:
            if len(number) >= 5 and len(number) <= 20:
                return True, number
            else:
                return False, "Medical aid number should be between 5-20 characters"
    
    @staticmethod
    def validate_school_registration_number(reg_number: str) -> Tuple[bool, Optional[str]]:
        """
        Validate school registration number (Ministry of Education format)
        Format typically: P123/456 for primary, S123/456 for secondary
        """
        if not reg_number:
            return True, None
            
        reg_number = reg_number.strip().upper()
        
        # Pattern: Letter (P/S/C) followed by numbers and optional slash
        pattern = r'^[PSC][0-9]{3,6}(/[0-9]{1,4})?$'
        
        if re.match(pattern, reg_number):
            return True, reg_number
        else:
            return False, "Invalid school registration. Format: P123/456 (Primary) or S123/456 (Secondary)"
    
    @staticmethod
    def validate_zimsec_candidate_number(candidate_number: str) -> Tuple[bool, Optional[str]]:
        """
        Validate ZIMSEC candidate number
        Format: Centre Number (4 digits) + Candidate Number (4 digits)
        Example: 12340001
        """
        if not candidate_number:
            return True, None
            
        candidate_number = candidate_number.strip()
        
        # Should be 8 digits
        if re.match(r'^[0-9]{8}$', candidate_number):
            # Format as XXXX-XXXX for readability
            formatted = f"{candidate_number[:4]}-{candidate_number[4:]}"
            return True, formatted
        else:
            return False, "ZIMSEC candidate number should be 8 digits (4 for centre, 4 for candidate)"
    
    @staticmethod
    def validate_postal_code(postal_code: str, city: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Zimbabwe postal codes
        Major cities have specific codes
        """
        if not postal_code:
            return True, None
            
        postal_code = postal_code.strip()
        
        # Zimbabwe doesn't have a strict postal code system
        # But some areas have informal codes
        city_codes = {
            'HARARE': ['00263', 'HRE'],
            'BULAWAYO': ['00263', 'BYO'],
            'MUTARE': ['00263', 'MUT'],
            'GWERU': ['00263', 'GWE'],
            'MASVINGO': ['00263', 'MSV'],
            'CHINHOYI': ['00263', 'CHI'],
            'KADOMA': ['00263', 'KAD'],
            'KWEKWE': ['00263', 'KWE'],
            'VICTORIA FALLS': ['00263', 'VFA'],
        }
        
        city_upper = city.upper() if city else ''
        
        # If city is known, validate against known codes
        if city_upper in city_codes:
            if postal_code in city_codes[city_upper] or len(postal_code) <= 10:
                return True, postal_code
        
        # General validation - accept most formats as Zimbabwe doesn't have strict postal codes
        if len(postal_code) <= 10:
            return True, postal_code
        else:
            return False, "Postal code too long (max 10 characters)"
    
    @staticmethod
    def calculate_age_from_id(national_id: str) -> Optional[int]:
        """
        Calculate age from National ID
        The first 6 digits after province code represent date of birth
        """
        try:
            # Remove formatting
            id_clean = national_id.replace("-", "").replace(" ", "")
            
            # Extract date components (digits 2-8 are YYMMDD)
            year_str = id_clean[2:4]
            month_str = id_clean[4:6]
            day_str = id_clean[6:8]
            
            # Determine century (00-30 = 2000s, 31-99 = 1900s)
            year = int(year_str)
            if year <= 30:
                year += 2000
            else:
                year += 1900
            
            birth_date = date(year, int(month_str), int(day_str))
            today = date.today()
            
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return age
        except:
            return None
    
    @staticmethod
    def validate_school_term(term_number: int, year: int) -> Tuple[bool, Optional[str]]:
        """
        Validate school term based on Zimbabwe's three-term system
        Term 1: January - April
        Term 2: May - August  
        Term 3: September - December
        """
        if term_number not in [1, 2, 3]:
            return False, "Invalid term number. Zimbabwe schools have 3 terms (1, 2, or 3)"
        
        current_date = date.today()
        current_month = current_date.month
        
        # Determine current term
        if current_month in [1, 2, 3, 4]:
            current_term = 1
        elif current_month in [5, 6, 7, 8]:
            current_term = 2
        else:
            current_term = 3
        
        # Validate year
        if year < 2020 or year > current_date.year + 1:
            return False, f"Invalid year. Must be between 2020 and {current_date.year + 1}"
        
        return True, f"Term {term_number} of {year}"
    
    @staticmethod
    def validate_grade_level(grade: int, school_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate grade level based on school type
        ECD: -2 to 0 (ECD A, ECD B, Grade 0)
        Primary: 1-7
        Secondary: Form 1-6 (represented as 8-13)
        """
        school_type = school_type.lower() if school_type else ''
        
        if 'ecd' in school_type or 'early' in school_type:
            if grade not in [-2, -1, 0]:
                return False, "ECD grades should be -2 (ECD A), -1 (ECD B), or 0 (Grade 0)"
        elif 'primary' in school_type:
            if grade < 1 or grade > 7:
                return False, "Primary school grades are 1-7"
        elif 'secondary' in school_type or 'high' in school_type:
            if grade < 8 or grade > 13:
                return False, "Secondary school forms are 8-13 (Form 1-6)"
        elif 'combined' in school_type or 'composite' in school_type:
            if grade < -2 or grade > 13:
                return False, "Combined schools support grades from ECD A (-2) to Form 6 (13)"
        else:
            # General validation
            if grade < -2 or grade > 13:
                return False, "Grade level must be between -2 (ECD A) and 13 (Form 6)"
        
        return True, None
    
    @staticmethod
    def format_student_name(first_name: str, middle_name: Optional[str], last_name: str) -> str:
        """
        Format student name according to Zimbabwe conventions
        Typically: SURNAME, First Middle
        """
        # Capitalize properly
        first = first_name.title() if first_name else ""
        middle = middle_name.title() if middle_name else ""
        last = last_name.upper() if last_name else ""
        
        if middle:
            return f"{last}, {first} {middle}"
        else:
            return f"{last}, {first}"
    
    @staticmethod
    def validate_exam_board(exam_board: str) -> Tuple[bool, Optional[str]]:
        """
        Validate examination board
        Main boards: ZIMSEC, Cambridge, IB
        """
        valid_boards = ['ZIMSEC', 'CAMBRIDGE', 'IB', 'HEXCO', 'NAMACO']
        
        board_upper = exam_board.upper() if exam_board else ''
        
        if board_upper in valid_boards:
            return True, board_upper
        else:
            return False, f"Invalid exam board. Valid options: {', '.join(valid_boards)}"