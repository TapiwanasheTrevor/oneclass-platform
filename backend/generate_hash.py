#!/usr/bin/env python3
"""
Simple script to generate password hash for testing
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from services.auth.utils import hash_password
    
    password = "test12345"
    hashed = hash_password(password)
    print(f"Password: {password}")
    print(f"Hash: {hashed}")
    
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback to direct bcrypt
    import bcrypt
    password = "test12345"
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    print(f"Password: {password}")
    print(f"Hash: {hashed.decode('utf-8')}")
