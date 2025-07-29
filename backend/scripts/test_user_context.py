#!/usr/bin/env python3
"""
Test script to verify user context and school associations
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from shared.database import get_async_session
from shared.models.platform_user import PlatformUser, SchoolMembership


async def test_user_context():
    """Test user context and school associations"""
    user_id = '00435818-c9cc-4562-83ab-bc5d31e11ea2'
    
    async for db in get_async_session():
        try:
            print("🔍 Testing User Context and School Associations")
            print("=" * 60)
            
            # Get user with school memberships
            query = (
                select(PlatformUser)
                .where(PlatformUser.id == user_id)
            )
            result = await db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User {user_id} not found")
                return
            
            print(f"👤 User: {user.first_name} {user.last_name}")
            print(f"📧 Email: {user.email}")
            print(f"🔑 Platform Role: {user.role}")
            print(f"🏫 Primary School ID: {user.primary_school_id}")
            print(f"📊 Status: {user.is_active}")
            
            # Get school memberships
            memberships_query = select(SchoolMembership).where(
                SchoolMembership.user_id == user_id
            )
            memberships_result = await db.execute(memberships_query)
            memberships = memberships_result.scalars().all()
            
            print(f"\n🏫 School Memberships ({len(memberships)}):")
            print("-" * 40)
            
            for membership in memberships:
                print(f"🏫 School: {membership.school_name}")
                print(f"   📍 School ID: {membership.school_id}")
                print(f"   🔑 Role: {membership.role}")
                print(f"   📊 Status: {membership.status}")
                print(f"   📅 Joined: {membership.joined_date}")
                print(f"   🏢 Department: {membership.department}")
                print("-" * 40)
            
            # Test JWT token generation logic
            print(f"\n🔐 JWT Token Generation Test:")
            print("-" * 40)
            
            primary_school_id = user.primary_school_id
            current_school_membership = None
            
            if memberships:
                # Use primary school or first available
                primary_membership = next(
                    (m for m in memberships if m.school_id == user.primary_school_id),
                    memberships[0],
                )
                current_school_membership = primary_membership
                primary_school_id = primary_membership.school_id
                
                print(f"✅ Primary School ID: {primary_school_id}")
                print(f"✅ Current School Membership: {current_school_membership.school_name}")
                print(f"✅ School Role: {current_school_membership.role}")
            else:
                print(f"❌ No school memberships found")
            
            # Simulate JWT payload
            jwt_payload = {
                "sub": str(user.id),
                "email": user.email,
                "school_id": str(primary_school_id) if primary_school_id else None,
                "platform_role": user.role,
                "school_role": (
                    current_school_membership.role
                    if current_school_membership
                    else None
                ),
            }
            
            print(f"\n🎯 Expected JWT Payload:")
            print("-" * 40)
            for key, value in jwt_payload.items():
                print(f"   {key}: {value}")
            
            # Check if this matches what we expect
            expected_school_id = 'b87f4d8b-2667-4c72-9ad7-e260281cdfdc'
            if jwt_payload['school_id'] == expected_school_id:
                print(f"\n✅ SUCCESS: JWT payload will contain correct school_id")
                print(f"✅ User should be able to access Palm Springs Jnr School")
            else:
                print(f"\n❌ ISSUE: JWT payload school_id mismatch")
                print(f"   Expected: {expected_school_id}")
                print(f"   Got: {jwt_payload['school_id']}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        break


if __name__ == "__main__":
    asyncio.run(test_user_context())
