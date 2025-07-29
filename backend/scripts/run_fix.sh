#!/bin/bash

# Script to fix super admin role for the user
# This script will update the user's platform_role to 'super_admin'

echo "🔧 OneClass Platform - Super Admin Role Fix"
echo "==========================================="

# Change to the backend directory
cd "$(dirname "$0")/.."

# Check if the user exists and list all users first
echo "📋 Listing all users in the platform..."
python scripts/fix_super_admin.py list

echo ""
echo "🔧 Fixing super admin role for maposhere@palmsprings.oneclass.ac.zw..."
python scripts/fix_super_admin.py fix maposhere@palmsprings.oneclass.ac.zw

echo ""
echo "✅ Role fix completed!"
echo "💡 The user should now be able to log in as a super admin and access the admin dashboard."
echo "🔄 Please restart the backend server and try logging in again."
