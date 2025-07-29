-- =====================================================
-- OneClass Platform Database Cleanup Script
-- This script consolidates user tables and removes orphaned content
-- =====================================================

-- Step 1: Backup existing data before cleanup
-- Create backup tables
CREATE TABLE IF NOT EXISTS platform.users_backup AS 
SELECT * FROM platform.users;

CREATE TABLE IF NOT EXISTS platform.platform_users_backup AS 
SELECT * FROM platform.platform_users;

-- Step 2: Check what data exists in both tables
SELECT 'platform.users' as table_name, count(*) as record_count FROM platform.users
UNION ALL
SELECT 'platform.platform_users' as table_name, count(*) as record_count FROM platform.platform_users;

-- Step 3: Show the structure differences
\d platform.users
\d platform.platform_users

-- Step 4: Migrate data from platform_users to users (if needed)
-- First, let's see if there's any data in platform_users that's not in users
SELECT 
    'Data in platform_users but not in users:' as status,
    count(*) as count
FROM platform.platform_users pu
LEFT JOIN platform.users u ON pu.email = u.email
WHERE u.email IS NULL;

-- Step 5: Update the users table structure to match what we need
-- Add missing columns to platform.users if they don't exist
DO $$
BEGIN
    -- Add platform_role column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'platform' 
                   AND table_name = 'users' 
                   AND column_name = 'platform_role') THEN
        ALTER TABLE platform.users ADD COLUMN platform_role VARCHAR(50) DEFAULT 'student';
        
        -- Update existing role values to platform_role
        UPDATE platform.users SET platform_role = role;
    END IF;
    
    -- Add status column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'platform' 
                   AND table_name = 'users' 
                   AND column_name = 'status') THEN
        ALTER TABLE platform.users ADD COLUMN status VARCHAR(50) DEFAULT 'active';
        
        -- Set status based on is_active
        UPDATE platform.users SET status = CASE 
            WHEN is_active = true THEN 'active' 
            ELSE 'inactive' 
        END;
    END IF;
    
    -- Add profile JSONB column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'platform' 
                   AND table_name = 'users' 
                   AND column_name = 'profile') THEN
        ALTER TABLE platform.users ADD COLUMN profile JSONB DEFAULT '{}';
    END IF;
    
    -- Add feature_flags JSONB column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'platform' 
                   AND table_name = 'users' 
                   AND column_name = 'feature_flags') THEN
        ALTER TABLE platform.users ADD COLUMN feature_flags JSONB DEFAULT '{}';
    END IF;
    
    -- Add user_preferences JSONB column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'platform' 
                   AND table_name = 'users' 
                   AND column_name = 'user_preferences') THEN
        ALTER TABLE platform.users ADD COLUMN user_preferences JSONB DEFAULT '{}';
        
        -- Migrate existing preferences if they exist
        UPDATE platform.users SET user_preferences = preferences WHERE preferences IS NOT NULL;
    END IF;
    
    -- Add primary_school_id if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'platform' 
                   AND table_name = 'users' 
                   AND column_name = 'primary_school_id') THEN
        ALTER TABLE platform.users ADD COLUMN primary_school_id UUID;
        
        -- Set primary_school_id to school_id for existing users
        UPDATE platform.users SET primary_school_id = school_id;
    END IF;
    
    -- Add last_login column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'platform' 
                   AND table_name = 'users' 
                   AND column_name = 'last_login') THEN
        ALTER TABLE platform.users ADD COLUMN last_login TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;

-- Step 6: Update constraints on platform.users
-- Drop old role constraint if it exists
ALTER TABLE platform.users DROP CONSTRAINT IF EXISTS users_role_check;

-- Add new platform_role constraint
ALTER TABLE platform.users DROP CONSTRAINT IF EXISTS chk_platform_role;
ALTER TABLE platform.users ADD CONSTRAINT chk_platform_role 
CHECK (platform_role IN ('super_admin', 'school_admin', 'registrar', 'teacher', 'parent', 'student', 'staff'));

-- Add status constraint
ALTER TABLE platform.users DROP CONSTRAINT IF EXISTS chk_status;
ALTER TABLE platform.users ADD CONSTRAINT chk_status 
CHECK (status IN ('active', 'inactive', 'suspended', 'pending_verification', 'archived'));

-- Step 7: Migrate any unique data from platform_users to users
INSERT INTO platform.users (
    id, email, first_name, last_name, platform_role, status, 
    profile, feature_flags, user_preferences, primary_school_id,
    created_at, updated_at, last_login
)
SELECT 
    pu.id, pu.email, pu.first_name, pu.last_name, pu.platform_role, pu.status,
    pu.profile, pu.feature_flags, pu.user_preferences, pu.primary_school_id,
    pu.created_at, pu.updated_at, pu.last_login
FROM platform.platform_users pu
LEFT JOIN platform.users u ON pu.email = u.email
WHERE u.email IS NULL;

-- Step 8: Fix the specific user role issue
UPDATE platform.users 
SET platform_role = 'super_admin', 
    status = 'active',
    updated_at = NOW()
WHERE email = 'maposhere@palmsprings.oneclass.ac.zw';

-- Step 9: Drop orphaned tables and constraints
-- Drop platform_users table (after backing up)
DROP TABLE IF EXISTS platform.platform_users CASCADE;

-- Drop school_memberships table if it exists and is not being used
-- (We'll keep this for now as it might be needed for multi-school support)

-- Step 10: Clean up unused schema files references
-- Remove any triggers or functions that reference the old table

-- Step 11: Update any foreign key references
-- Check for any tables that reference platform.platform_users
SELECT 
    tc.table_schema, 
    tc.table_name, 
    kcu.column_name,
    ccu.table_schema AS foreign_table_schema,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND ccu.table_name = 'platform_users';

-- Step 12: Verify the cleanup
SELECT 'Final verification:' as status;
SELECT 'platform.users' as table_name, count(*) as record_count FROM platform.users;

-- Show the user we're trying to fix
SELECT id, email, first_name, last_name, platform_role, status, created_at 
FROM platform.users 
WHERE email = 'maposhere@palmsprings.oneclass.ac.zw';

-- Show all super_admin users
SELECT id, email, first_name, last_name, platform_role, status 
FROM platform.users 
WHERE platform_role = 'super_admin';

COMMIT;
