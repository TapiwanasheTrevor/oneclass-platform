# =====================================================
# SIS Module - Simple Validator Tests (Standalone)
# File: backend/services/sis/tests/test_validators_simple.py
# =====================================================

import re
from typing import Tuple, Optional
from datetime import date

# Inline validators for testing (copied from zimbabwe_validators.py)
class ZimbabweValidatorSimple:
    """Simple validators for Zimbabwe-specific data formats"""
    
    @staticmethod
    def validate_national_id(national_id: str) -> Tuple[bool, Optional[str]]:
        """Validate Zimbabwe National ID format"""
        if not national_id:
            return True, None
            
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
    def validate_phone_number(phone: str) -> Tuple[bool, Optional[str]]:
        """Validate Zimbabwe phone number"""
        if not phone:
            return True, None
            
        # Remove all spaces, hyphens, and parentheses
        phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Check for international format
        if phone.startswith('+263'):
            phone = phone[4:]
            if len(phone) == 9 and phone[0] in '7':  # Mobile
                return True, f"+263{phone}"
        elif phone.startswith('0'):
            if len(phone) == 10 and phone[1] in '7':  # Mobile
                return True, f"+263{phone[1:]}"
        
        return False, "Invalid Zimbabwe phone number. Use format: 0712345678 or +263712345678"
    
    @staticmethod
    def calculate_age_from_id(national_id: str) -> Optional[int]:
        """Calculate age from National ID"""
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

# Test classes
class TestZimbabweValidatorsSimple:
    """Test Zimbabwe-specific validators (standalone)"""
    
    def test_validate_national_id_valid(self):
        """Test valid National ID validation"""
        valid_id = "63-123456-K-23"
        is_valid, formatted = ZimbabweValidatorSimple.validate_national_id(valid_id)
        
        assert is_valid is True
        assert formatted == "63-123456-K-23"
    
    def test_validate_national_id_valid_without_hyphens(self):
        """Test valid National ID without hyphens"""
        valid_id = "63123456K23"
        is_valid, formatted = ZimbabweValidatorSimple.validate_national_id(valid_id)
        
        assert is_valid is True
        assert formatted == "63-123456-K-23"
    
    def test_validate_national_id_invalid_format(self):
        """Test invalid National ID format"""
        invalid_id = "123-456-789"
        is_valid, error = ZimbabweValidatorSimple.validate_national_id(invalid_id)
        
        assert is_valid is False
        assert "Invalid National ID format" in error
    
    def test_validate_national_id_invalid_province(self):
        """Test invalid province code in National ID"""
        invalid_id = "99-123456-K-23"  # Invalid province code
        is_valid, error = ZimbabweValidatorSimple.validate_national_id(invalid_id)
        
        assert is_valid is False
        assert "Invalid province code" in error
    
    def test_validate_national_id_empty(self):
        """Test empty National ID (should be valid as optional)"""
        is_valid, result = ZimbabweValidatorSimple.validate_national_id("")
        
        assert is_valid is True
        assert result is None
    
    def test_validate_phone_number_valid_international(self):
        """Test valid Zimbabwe mobile number (international format)"""
        valid_phone = "+263771234567"
        is_valid, formatted = ZimbabweValidatorSimple.validate_phone_number(valid_phone)
        
        assert is_valid is True
        assert formatted == "+263771234567"
    
    def test_validate_phone_number_valid_local(self):
        """Test valid local format phone number"""
        local_phone = "0771234567"
        is_valid, formatted = ZimbabweValidatorSimple.validate_phone_number(local_phone)
        
        assert is_valid is True
        assert formatted == "+263771234567"
    
    def test_validate_phone_number_with_spaces(self):
        """Test phone number with spaces"""
        phone_with_spaces = "077 123 4567"
        is_valid, formatted = ZimbabweValidatorSimple.validate_phone_number(phone_with_spaces)
        
        assert is_valid is True
        assert formatted == "+263771234567"
    
    def test_validate_phone_number_invalid(self):
        """Test invalid phone number"""
        invalid_phone = "123456"
        is_valid, error = ZimbabweValidatorSimple.validate_phone_number(invalid_phone)
        
        assert is_valid is False
        assert "Invalid Zimbabwe phone number" in error
    
    def test_validate_phone_number_empty(self):
        """Test empty phone number (should be valid as optional)"""
        is_valid, result = ZimbabweValidatorSimple.validate_phone_number("")
        
        assert is_valid is True
        assert result is None
    
    def test_calculate_age_from_id_1995(self):
        """Test age calculation from National ID (born 1995)"""
        # ID for someone born 15 May 1995
        national_id = "63-950515-K-23"
        age = ZimbabweValidatorSimple.calculate_age_from_id(national_id)
        
        # Age should be approximately 28-29 (depending on current date)
        assert age is not None
        assert 25 <= age <= 35  # Reasonable range
    
    def test_calculate_age_from_id_2005(self):
        """Test age calculation from National ID (born 2005)"""
        # ID for someone born 10 March 2005
        national_id = "63-050310-A-45"
        age = ZimbabweValidatorSimple.calculate_age_from_id(national_id)
        
        # Age should be approximately 18-19
        assert age is not None
        assert 15 <= age <= 25  # Reasonable range
    
    def test_calculate_age_from_id_invalid(self):
        """Test age calculation with invalid ID"""
        invalid_id = "invalid-id"
        age = ZimbabweValidatorSimple.calculate_age_from_id(invalid_id)
        
        assert age is None

class TestDataValidationScenarios:
    """Test realistic data validation scenarios"""
    
    def test_student_registration_data_valid(self):
        """Test complete student registration data validation"""
        student_data = {
            "national_id": "63-050515-K-23",
            "parent_phone": "0771234567",
            "emergency_phone": "+263772345678"
        }
        
        # Validate national ID
        id_valid, formatted_id = ZimbabweValidatorSimple.validate_national_id(student_data["national_id"])
        assert id_valid is True
        assert formatted_id == "63-050515-K-23"
        
        # Calculate age
        age = ZimbabweValidatorSimple.calculate_age_from_id(formatted_id)
        assert age is not None
        assert 10 <= age <= 25  # School age range
        
        # Validate parent phone
        parent_valid, parent_formatted = ZimbabweValidatorSimple.validate_phone_number(student_data["parent_phone"])
        assert parent_valid is True
        assert parent_formatted == "+263771234567"
        
        # Validate emergency phone
        emergency_valid, emergency_formatted = ZimbabweValidatorSimple.validate_phone_number(student_data["emergency_phone"])
        assert emergency_valid is True
        assert emergency_formatted == "+263772345678"
    
    def test_student_registration_data_invalid(self):
        """Test student registration with invalid data"""
        student_data = {
            "national_id": "99-123456-X-99",  # Invalid province
            "parent_phone": "123456",  # Invalid phone
            "emergency_phone": ""  # Empty (should be valid)
        }
        
        # Validate national ID (should fail)
        id_valid, id_error = ZimbabweValidatorSimple.validate_national_id(student_data["national_id"])
        assert id_valid is False
        assert "Invalid province code" in id_error
        
        # Validate parent phone (should fail)
        parent_valid, parent_error = ZimbabweValidatorSimple.validate_phone_number(student_data["parent_phone"])
        assert parent_valid is False
        assert "Invalid Zimbabwe phone number" in parent_error
        
        # Validate emergency phone (should pass as empty is allowed)
        emergency_valid, emergency_result = ZimbabweValidatorSimple.validate_phone_number(student_data["emergency_phone"])
        assert emergency_valid is True
        assert emergency_result is None

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])