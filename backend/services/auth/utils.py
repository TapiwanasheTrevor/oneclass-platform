# =====================================================
# Authentication Utilities
# Helper functions for password hashing, JWT tokens, etc.
# File: backend/services/auth/utils.py
# =====================================================

import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
from uuid import uuid4

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except (ValueError, TypeError):
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "jti": str(uuid4())  # JWT ID for tracking
    })
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": str(uuid4())
    })
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("type") != token_type:
            raise jwt.InvalidTokenError(f"Invalid token type. Expected {token_type}")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise jwt.ExpiredSignatureError("Token has expired")
    except jwt.InvalidTokenError:
        raise jwt.InvalidTokenError("Invalid token")

def decode_token_without_verification(token: str) -> Optional[Dict[str, Any]]:
    """Decode token without verifying signature (for debugging)"""
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except Exception:
        return None

def generate_reset_token() -> str:
    """Generate a secure password reset token"""
    return str(uuid4())

def create_invitation_token(data: Dict[str, Any], expires_days: int = 7) -> str:
    """Create a JWT token for invitations"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=expires_days)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "invitation",
        "jti": str(uuid4())
    })
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_invitation_token(token: str) -> Dict[str, Any]:
    """Verify and decode an invitation token"""
    return verify_token(token, token_type="invitation")

def extract_user_id_from_token(token: str) -> Optional[str]:
    """Extract user ID from token without full verification"""
    try:
        payload = decode_token_without_verification(token)
        return payload.get("sub") if payload else None
    except Exception:
        return None

def is_token_expired(token: str) -> bool:
    """Check if token is expired without raising exception"""
    try:
        payload = decode_token_without_verification(token)
        if not payload:
            return True
        
        exp = payload.get("exp")
        if not exp:
            return True
            
        return datetime.fromtimestamp(exp) < datetime.utcnow()
    except Exception:
        return True

def get_token_expiry(token: str) -> Optional[datetime]:
    """Get token expiry datetime"""
    try:
        payload = decode_token_without_verification(token)
        if not payload:
            return None
            
        exp = payload.get("exp")
        return datetime.fromtimestamp(exp) if exp else None
    except Exception:
        return None

def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength and return feedback"""
    issues = []
    score = 0
    
    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")
    else:
        score += 1
    
    if not any(c.isupper() for c in password):
        issues.append("Password must contain at least one uppercase letter")
    else:
        score += 1
    
    if not any(c.islower() for c in password):
        issues.append("Password must contain at least one lowercase letter")
    else:
        score += 1
    
    if not any(c.isdigit() for c in password):
        issues.append("Password must contain at least one number")
    else:
        score += 1
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        issues.append("Password must contain at least one special character")
    else:
        score += 1
    
    strength_levels = {
        0: "Very Weak",
        1: "Weak", 
        2: "Fair",
        3: "Good",
        4: "Strong",
        5: "Very Strong"
    }
    
    return {
        "is_valid": len(issues) == 0,
        "score": score,
        "strength": strength_levels[score],
        "issues": issues
    }

def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))