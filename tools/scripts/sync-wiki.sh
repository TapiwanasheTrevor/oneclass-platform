#!/bin/bash

# OneClass Platform Wiki Sync Script
# Syncs local docs/wiki to GitHub Wiki

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WIKI_DIR="$PROJECT_ROOT/docs/wiki"

echo "🔄 OneClass Wiki Sync"
echo "===================="

# Check if wiki directory exists
if [ ! -d "$WIKI_DIR" ]; then
    echo "❌ Wiki directory not found at $WIKI_DIR"
    exit 1
fi

# Check if wiki remote exists
cd "$PROJECT_ROOT"
if ! git remote get-url wiki &>/dev/null; then
    echo "📝 Setting up wiki remote..."
    git remote add wiki https://github.com/TapiwanasheTrevor/oneclass-platform.wiki.git
fi

# Create temporary directory for wiki
TEMP_WIKI=$(mktemp -d)
echo "📁 Cloning wiki to temporary directory..."
git clone https://github.com/TapiwanasheTrevor/oneclass-platform.wiki.git "$TEMP_WIKI" 2>/dev/null || {
    echo "⚠️  Wiki not initialized on GitHub. Please enable wiki in repository settings first."
    rm -rf "$TEMP_WIKI"
    exit 1
}

# Copy wiki files
echo "📋 Copying wiki files..."
cp -r "$WIKI_DIR"/* "$TEMP_WIKI/" 2>/dev/null || true

# Rename README.md to Home.md for GitHub Wiki
if [ -f "$TEMP_WIKI/README.md" ]; then
    mv "$TEMP_WIKI/README.md" "$TEMP_WIKI/Home.md"
fi

# Commit and push changes
cd "$TEMP_WIKI"
git add .
if git diff --staged --quiet; then
    echo "✅ No changes to sync"
else
    COMMIT_MSG="Update wiki: $(date '+%Y-%m-%d %H:%M:%S')"
    git commit -m "$COMMIT_MSG"
    git push origin master
    echo "✅ Wiki synced successfully!"
fi

# Cleanup
rm -rf "$TEMP_WIKI"

echo ""
echo "📚 Wiki available at: https://github.com/TapiwanasheTrevor/oneclass-platform/wiki"
echo "✨ Done!"