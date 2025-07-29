"""
Encryption Utility Module
Handles data encryption and decryption for sensitive information
"""

import os
import base64
import logging
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

# Encryption configuration
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
ENCRYPTION_SALT = os.getenv("ENCRYPTION_SALT", "oneclass-platform-salt").encode()

class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self):
        self.fernet = self._get_fernet()
    
    def _get_fernet(self) -> Fernet:
        """Get Fernet encryption instance"""
        if ENCRYPTION_KEY:
            # Use provided key
            key = ENCRYPTION_KEY.encode()
        else:
            # Generate key from default password (for development only)
            password = b"oneclass-default-password"
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=ENCRYPTION_SALT,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
        
        return Fernet(key)
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt string data"""
        try:
            if not data:
                return ""
            
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        
        except Exception as e:
            logger.error(f"Failed to encrypt data: {str(e)}")
            return data  # Return original data if encryption fails
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        try:
            if not encrypted_data:
                return ""
            
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        
        except Exception as e:
            logger.error(f"Failed to decrypt data: {str(e)}")
            return encrypted_data  # Return original data if decryption fails
    
    def encrypt_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt dictionary values"""
        encrypted_dict = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                encrypted_dict[key] = self.encrypt_data(value)
            elif isinstance(value, dict):
                encrypted_dict[key] = self.encrypt_dict(value)
            else:
                encrypted_dict[key] = value
        
        return encrypted_dict
    
    def decrypt_dict(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt dictionary values"""
        decrypted_dict = {}
        
        for key, value in encrypted_data.items():
            if isinstance(value, str):
                decrypted_dict[key] = self.decrypt_data(value)
            elif isinstance(value, dict):
                decrypted_dict[key] = self.decrypt_dict(value)
            else:
                decrypted_dict[key] = value
        
        return decrypted_dict

# Global encryption service instance
encryption_service = EncryptionService()

# Convenience functions
def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data using the global service"""
    return encryption_service.encrypt_data(data)

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data using the global service"""
    return encryption_service.decrypt_data(encrypted_data)

def encrypt_medical_data(medical_data: Dict[str, Any]) -> Dict[str, Any]:
    """Encrypt medical data dictionary"""
    return encryption_service.encrypt_dict(medical_data)

def decrypt_medical_data(encrypted_medical_data: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt medical data dictionary"""
    return encryption_service.decrypt_dict(encrypted_medical_data)

def encrypt_emergency_contacts(contacts: Dict[str, Any]) -> Dict[str, Any]:
    """Encrypt emergency contact information"""
    return encryption_service.encrypt_dict(contacts)

def decrypt_emergency_contacts(encrypted_contacts: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt emergency contact information"""
    return encryption_service.decrypt_dict(encrypted_contacts)

def encrypt_personal_data(personal_data: Dict[str, Any]) -> Dict[str, Any]:
    """Encrypt personal data (addresses, phone numbers, etc.)"""
    sensitive_fields = [
        'phone', 'address', 'emergency_contact_phone', 
        'parent_phone', 'guardian_phone', 'home_address'
    ]
    
    encrypted_data = personal_data.copy()
    
    for field in sensitive_fields:
        if field in encrypted_data and encrypted_data[field]:
            encrypted_data[field] = encrypt_sensitive_data(str(encrypted_data[field]))
    
    return encrypted_data

def decrypt_personal_data(encrypted_personal_data: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt personal data"""
    sensitive_fields = [
        'phone', 'address', 'emergency_contact_phone', 
        'parent_phone', 'guardian_phone', 'home_address'
    ]
    
    decrypted_data = encrypted_personal_data.copy()
    
    for field in sensitive_fields:
        if field in decrypted_data and decrypted_data[field]:
            decrypted_data[field] = decrypt_sensitive_data(str(decrypted_data[field]))
    
    return decrypted_data
