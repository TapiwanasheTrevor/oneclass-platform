#!/bin/bash

# OneClass Platform Database Cleanup Script
# This script consolidates user tables and fixes the super admin role

echo "🧹 OneClass Platform Database Cleanup"
echo "====================================="

# Change to the backend directory
cd "$(dirname "$0")/.."

echo "📋 Step 1: Analyzing current database state..."
python scripts/cleanup_database.py

echo ""
echo "✅ Database cleanup completed!"
echo ""
echo "🔄 Next steps:"
echo "1. Restart the backend server: python main.py"
echo "2. Clear browser cache/localStorage"
echo "3. Try logging in again with maposhere@palmsprings.oneclass.ac.zw"
echo ""
echo "💡 The user should now be recognized as super_admin and see the admin dashboard."
