#!/usr/bin/env python3
"""
Script to fix super admin user role assignment
This script will update the user's platform_role to 'super_admin' for the specified email
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, update
from shared.database import get_async_session
from shared.models.platform_user import PlatformUser


async def fix_super_admin_role(email: str):
    """Fix the platform role for a super admin user"""
    
    async for db in get_async_session():
        try:
            # Find the user by email
            query = select(PlatformUser).where(PlatformUser.email == email.lower())
            result = await db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User with email '{email}' not found")
                return False
            
            print(f"📧 Found user: {user.first_name} {user.last_name} ({user.email})")
            print(f"🔍 Current platform_role: {user.platform_role}")
            print(f"🔍 Current status: {user.status}")
            print(f"🔍 Primary school ID: {user.primary_school_id}")
            
            # Update the user's platform role to super_admin
            if user.platform_role != 'super_admin':
                user.platform_role = 'super_admin'
                user.status = 'active'  # Ensure user is active
                
                await db.commit()
                print(f"✅ Updated platform_role to 'super_admin' for {email}")
            else:
                print(f"✅ User already has super_admin role")
            
            # Display updated user info
            await db.refresh(user)
            print(f"🎯 Updated platform_role: {user.platform_role}")
            print(f"🎯 Updated status: {user.status}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating user: {str(e)}")
            await db.rollback()
            return False


async def list_all_users():
    """List all users in the platform"""
    
    async for db in get_async_session():
        try:
            query = select(PlatformUser).order_by(PlatformUser.created_at)
            result = await db.execute(query)
            users = result.scalars().all()
            
            print(f"\n📋 Found {len(users)} users in the platform:")
            print("-" * 80)
            
            for user in users:
                print(f"📧 {user.email}")
                print(f"   👤 Name: {user.first_name} {user.last_name}")
                print(f"   🔑 Platform Role: {user.platform_role}")
                print(f"   📊 Status: {user.status}")
                print(f"   🏫 Primary School ID: {user.primary_school_id}")
                print(f"   📅 Created: {user.created_at}")
                print("-" * 80)
                
        except Exception as e:
            print(f"❌ Error listing users: {str(e)}")


async def create_super_admin(email: str, first_name: str, last_name: str, password: str = None):
    """Create a new super admin user"""
    
    async for db in get_async_session():
        try:
            # Check if user already exists
            query = select(PlatformUser).where(PlatformUser.email == email.lower())
            result = await db.execute(query)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"❌ User with email '{email}' already exists")
                return False
            
            # Create new super admin user
            from services.auth.utils import hash_password
            from uuid import uuid4
            from datetime import datetime
            
            password_hash = hash_password(password) if password else None
            
            new_user = PlatformUser(
                id=uuid4(),
                email=email.lower(),
                first_name=first_name,
                last_name=last_name,
                platform_role='super_admin',
                status='active',
                password_hash=password_hash,
                user_metadata={},
                preferences={},
                created_at=datetime.utcnow(),
            )
            
            db.add(new_user)
            await db.commit()
            
            print(f"✅ Created super admin user: {email}")
            print(f"   👤 Name: {first_name} {last_name}")
            print(f"   🔑 Platform Role: super_admin")
            print(f"   📊 Status: active")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating super admin: {str(e)}")
            await db.rollback()
            return False


async def main():
    """Main function"""
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python fix_super_admin.py list                                    # List all users")
        print("  python fix_super_admin.py fix <email>                            # Fix existing user role")
        print("  python fix_super_admin.py create <email> <first_name> <last_name> [password]  # Create new super admin")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        await list_all_users()
    
    elif command == "fix":
        if len(sys.argv) < 3:
            print("❌ Please provide an email address")
            return
        
        email = sys.argv[2]
        success = await fix_super_admin_role(email)
        
        if success:
            print(f"\n🎉 Successfully updated user role for {email}")
            print("💡 The user should now be able to log in as a super admin")
        else:
            print(f"\n❌ Failed to update user role for {email}")
    
    elif command == "create":
        if len(sys.argv) < 5:
            print("❌ Please provide email, first_name, and last_name")
            return
        
        email = sys.argv[2]
        first_name = sys.argv[3]
        last_name = sys.argv[4]
        password = sys.argv[5] if len(sys.argv) > 5 else "admin123"  # Default password
        
        success = await create_super_admin(email, first_name, last_name, password)
        
        if success:
            print(f"\n🎉 Successfully created super admin user: {email}")
            print(f"🔑 Default password: {password}")
            print("💡 The user can now log in as a super admin")
        else:
            print(f"\n❌ Failed to create super admin user: {email}")
    
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    asyncio.run(main())
