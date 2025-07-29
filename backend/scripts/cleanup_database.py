#!/usr/bin/env python3
"""
OneClass Platform Database Cleanup Script
This script consolidates user tables and removes orphaned content safely
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text, inspect
from shared.database import get_async_session


class DatabaseCleanup:
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        async for session in get_async_session():
            self.session = session
            return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def check_table_exists(self, schema: str, table: str) -> bool:
        """Check if a table exists"""
        query = text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = :schema AND table_name = :table
            )
        """)
        result = await self.session.execute(query, {"schema": schema, "table": table})
        return result.scalar()

    async def get_table_count(self, schema: str, table: str) -> int:
        """Get record count for a table"""
        if not await self.check_table_exists(schema, table):
            return 0
        
        query = text(f"SELECT COUNT(*) FROM {schema}.{table}")
        result = await self.session.execute(query)
        return result.scalar()

    async def get_table_columns(self, schema: str, table: str) -> List[str]:
        """Get column names for a table"""
        query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = :schema AND table_name = :table
            ORDER BY ordinal_position
        """)
        result = await self.session.execute(query, {"schema": schema, "table": table})
        return [row[0] for row in result.fetchall()]

    async def backup_table(self, schema: str, table: str) -> bool:
        """Create a backup of a table"""
        try:
            backup_name = f"{table}_backup_{int(asyncio.get_event_loop().time())}"
            query = text(f"CREATE TABLE {schema}.{backup_name} AS SELECT * FROM {schema}.{table}")
            await self.session.execute(query)
            await self.session.commit()
            print(f"✅ Created backup: {schema}.{backup_name}")
            return True
        except Exception as e:
            print(f"❌ Failed to backup {schema}.{table}: {e}")
            return False

    async def analyze_user_tables(self):
        """Analyze the current state of user tables"""
        print("🔍 Analyzing user tables...")
        print("=" * 50)
        
        # Check which tables exist
        users_exists = await self.check_table_exists("platform", "users")
        platform_users_exists = await self.check_table_exists("platform", "platform_users")
        
        print(f"📊 platform.users exists: {users_exists}")
        print(f"📊 platform.platform_users exists: {platform_users_exists}")
        
        if users_exists:
            users_count = await self.get_table_count("platform", "users")
            print(f"📊 platform.users record count: {users_count}")
            
            users_columns = await self.get_table_columns("platform", "users")
            print(f"📊 platform.users columns: {', '.join(users_columns)}")
        
        if platform_users_exists:
            platform_users_count = await self.get_table_count("platform", "platform_users")
            print(f"📊 platform.platform_users record count: {platform_users_count}")
            
            platform_users_columns = await self.get_table_columns("platform", "platform_users")
            print(f"📊 platform.platform_users columns: {', '.join(platform_users_columns)}")
        
        return users_exists, platform_users_exists

    async def check_target_user(self):
        """Check the target user's current state"""
        print("\n🎯 Checking target user...")
        print("=" * 50)
        
        email = "maposhere@palmsprings.oneclass.ac.zw"
        
        # Check in platform.users
        if await self.check_table_exists("platform", "users"):
            query = text("""
                SELECT id, email, first_name, last_name, 
                       COALESCE(platform_role, role) as role, 
                       COALESCE(status, CASE WHEN is_active THEN 'active' ELSE 'inactive' END) as status
                FROM platform.users 
                WHERE email = :email
            """)
            result = await self.session.execute(query, {"email": email})
            user = result.fetchone()
            
            if user:
                print(f"👤 Found in platform.users:")
                print(f"   📧 Email: {user.email}")
                print(f"   👤 Name: {user.first_name} {user.last_name}")
                print(f"   🔑 Role: {user.role}")
                print(f"   📊 Status: {user.status}")
            else:
                print(f"❌ User not found in platform.users")
        
        # Check in platform.platform_users
        if await self.check_table_exists("platform", "platform_users"):
            query = text("""
                SELECT id, email, first_name, last_name, platform_role, status
                FROM platform.platform_users 
                WHERE email = :email
            """)
            result = await self.session.execute(query, {"email": email})
            user = result.fetchone()
            
            if user:
                print(f"👤 Found in platform.platform_users:")
                print(f"   📧 Email: {user.email}")
                print(f"   👤 Name: {user.first_name} {user.last_name}")
                print(f"   🔑 Platform Role: {user.platform_role}")
                print(f"   📊 Status: {user.status}")
            else:
                print(f"❌ User not found in platform.platform_users")

    async def consolidate_tables(self):
        """Consolidate platform_users into users table"""
        print("\n🔧 Consolidating user tables...")
        print("=" * 50)
        
        users_exists = await self.check_table_exists("platform", "users")
        platform_users_exists = await self.check_table_exists("platform", "platform_users")
        
        if not users_exists and not platform_users_exists:
            print("❌ No user tables found!")
            return False
        
        # If only platform_users exists, rename it to users
        if platform_users_exists and not users_exists:
            print("📝 Renaming platform.platform_users to platform.users...")
            query = text("ALTER TABLE platform.platform_users RENAME TO users")
            await self.session.execute(query)
            await self.session.commit()
            print("✅ Renamed platform.platform_users to platform.users")
            return True
        
        # If both exist, we need to merge them
        if users_exists and platform_users_exists:
            print("🔄 Both tables exist, merging data...")
            
            # First, backup both tables
            await self.backup_table("platform", "users")
            await self.backup_table("platform", "platform_users")
            
            # Add missing columns to users table
            await self.add_missing_columns()
            
            # Migrate unique data from platform_users to users
            await self.migrate_platform_users_data()
            
            # Drop platform_users table
            query = text("DROP TABLE platform.platform_users CASCADE")
            await self.session.execute(query)
            await self.session.commit()
            print("✅ Dropped platform.platform_users table")
            
            return True
        
        # If only users exists, just add missing columns
        if users_exists and not platform_users_exists:
            print("📝 Adding missing columns to platform.users...")
            await self.add_missing_columns()
            return True

    async def add_missing_columns(self):
        """Add missing columns to platform.users table"""
        print("📝 Adding missing columns...")
        
        # Check and add platform_role column
        columns = await self.get_table_columns("platform", "users")
        
        if "platform_role" not in columns:
            print("   Adding platform_role column...")
            query = text("ALTER TABLE platform.users ADD COLUMN platform_role VARCHAR(50) DEFAULT 'student'")
            await self.session.execute(query)
            
            # Copy role to platform_role
            query = text("UPDATE platform.users SET platform_role = role WHERE role IS NOT NULL")
            await self.session.execute(query)
        
        if "status" not in columns:
            print("   Adding status column...")
            query = text("ALTER TABLE platform.users ADD COLUMN status VARCHAR(50) DEFAULT 'active'")
            await self.session.execute(query)
            
            # Set status based on is_active
            query = text("""
                UPDATE platform.users 
                SET status = CASE WHEN is_active = true THEN 'active' ELSE 'inactive' END
            """)
            await self.session.execute(query)
        
        if "profile" not in columns:
            print("   Adding profile column...")
            query = text("ALTER TABLE platform.users ADD COLUMN profile JSONB DEFAULT '{}'")
            await self.session.execute(query)
        
        if "feature_flags" not in columns:
            print("   Adding feature_flags column...")
            query = text("ALTER TABLE platform.users ADD COLUMN feature_flags JSONB DEFAULT '{}'")
            await self.session.execute(query)
        
        if "user_preferences" not in columns:
            print("   Adding user_preferences column...")
            query = text("ALTER TABLE platform.users ADD COLUMN user_preferences JSONB DEFAULT '{}'")
            await self.session.execute(query)
        
        if "primary_school_id" not in columns:
            print("   Adding primary_school_id column...")
            query = text("ALTER TABLE platform.users ADD COLUMN primary_school_id UUID")
            await self.session.execute(query)
            
            # Set primary_school_id to school_id for existing users
            query = text("UPDATE platform.users SET primary_school_id = school_id WHERE school_id IS NOT NULL")
            await self.session.execute(query)
        
        if "last_login" not in columns:
            print("   Adding last_login column...")
            query = text("ALTER TABLE platform.users ADD COLUMN last_login TIMESTAMP WITH TIME ZONE")
            await self.session.execute(query)
        
        await self.session.commit()
        print("✅ Added missing columns")

    async def migrate_platform_users_data(self):
        """Migrate unique data from platform_users to users"""
        print("🔄 Migrating data from platform.platform_users...")
        
        query = text("""
            INSERT INTO platform.users (
                id, email, first_name, last_name, platform_role, status,
                profile, feature_flags, user_preferences, primary_school_id,
                created_at, updated_at, last_login, school_id
            )
            SELECT 
                pu.id, pu.email, pu.first_name, pu.last_name, pu.platform_role, pu.status,
                pu.profile, pu.feature_flags, pu.user_preferences, pu.primary_school_id,
                pu.created_at, pu.updated_at, pu.last_login, pu.primary_school_id
            FROM platform.platform_users pu
            LEFT JOIN platform.users u ON pu.email = u.email
            WHERE u.email IS NULL
        """)
        
        result = await self.session.execute(query)
        await self.session.commit()
        print(f"✅ Migrated {result.rowcount} unique records")

    async def fix_super_admin_user(self):
        """Fix the super admin user role"""
        print("\n🎯 Fixing super admin user...")
        print("=" * 50)
        
        email = "maposhere@palmsprings.oneclass.ac.zw"
        
        query = text("""
            UPDATE platform.users 
            SET platform_role = 'super_admin', 
                status = 'active',
                updated_at = NOW()
            WHERE email = :email
        """)
        
        result = await self.session.execute(query, {"email": email})
        await self.session.commit()
        
        if result.rowcount > 0:
            print(f"✅ Updated user {email} to super_admin")
            
            # Verify the change
            query = text("""
                SELECT email, first_name, last_name, platform_role, status
                FROM platform.users 
                WHERE email = :email
            """)
            result = await self.session.execute(query, {"email": email})
            user = result.fetchone()
            
            if user:
                print(f"✅ Verified: {user.first_name} {user.last_name} is now {user.platform_role}")
        else:
            print(f"❌ User {email} not found or not updated")

    async def add_constraints(self):
        """Add proper constraints to the users table"""
        print("\n🔒 Adding constraints...")
        print("=" * 50)
        
        try:
            # Drop old constraints if they exist
            await self.session.execute(text("ALTER TABLE platform.users DROP CONSTRAINT IF EXISTS users_role_check"))
            await self.session.execute(text("ALTER TABLE platform.users DROP CONSTRAINT IF EXISTS chk_platform_role"))
            await self.session.execute(text("ALTER TABLE platform.users DROP CONSTRAINT IF EXISTS chk_status"))
            
            # Add new constraints
            query = text("""
                ALTER TABLE platform.users ADD CONSTRAINT chk_platform_role 
                CHECK (platform_role IN ('super_admin', 'school_admin', 'registrar', 'teacher', 'parent', 'student', 'staff'))
            """)
            await self.session.execute(query)
            
            query = text("""
                ALTER TABLE platform.users ADD CONSTRAINT chk_status 
                CHECK (status IN ('active', 'inactive', 'suspended', 'pending_verification', 'archived'))
            """)
            await self.session.execute(query)
            
            await self.session.commit()
            print("✅ Added constraints")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not add constraints: {e}")

    async def verify_cleanup(self):
        """Verify the cleanup was successful"""
        print("\n✅ Verification...")
        print("=" * 50)
        
        # Check final table state
        users_count = await self.get_table_count("platform", "users")
        print(f"📊 Final platform.users count: {users_count}")
        
        # Check if platform_users still exists
        platform_users_exists = await self.check_table_exists("platform", "platform_users")
        print(f"📊 platform.platform_users exists: {platform_users_exists}")
        
        # Check super admin users
        query = text("""
            SELECT email, first_name, last_name, platform_role, status
            FROM platform.users 
            WHERE platform_role = 'super_admin'
        """)
        result = await self.session.execute(query)
        super_admins = result.fetchall()
        
        print(f"👑 Super admin users ({len(super_admins)}):")
        for admin in super_admins:
            print(f"   📧 {admin.email} - {admin.first_name} {admin.last_name} ({admin.status})")


async def main():
    """Main cleanup function"""
    print("🧹 OneClass Platform Database Cleanup")
    print("=" * 50)
    
    try:
        async with DatabaseCleanup() as cleanup:
            # Step 1: Analyze current state
            await cleanup.analyze_user_tables()
            
            # Step 2: Check target user
            await cleanup.check_target_user()
            
            # Step 3: Consolidate tables
            await cleanup.consolidate_tables()
            
            # Step 4: Fix super admin user
            await cleanup.fix_super_admin_user()
            
            # Step 5: Add constraints
            await cleanup.add_constraints()
            
            # Step 6: Verify cleanup
            await cleanup.verify_cleanup()
            
            print("\n🎉 Database cleanup completed successfully!")
            print("💡 Please restart the backend server to apply changes.")
            
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
