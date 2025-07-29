#!/bin/bash

# OneClass Platform Development Reset Script
# This script resets the development environment

set -e

echo "🔄 Resetting OneClass Platform Development Environment..."
echo "=================================================="

# Stop all services
echo "🛑 Stopping services..."
docker-compose down

# Remove containers and volumes
echo "🗑️  Removing containers and volumes..."
docker-compose down -v --remove-orphans

# Remove images
echo "🗑️  Removing images..."
docker-compose down --rmi local

# Rebuild and start
echo "🔧 Rebuilding services..."
docker-compose build --no-cache

echo "✅ Development environment reset complete"
echo ""
echo "💡 To start again, run: ./scripts/start-dev.sh"
echo ""