#!/bin/bash

# OneClass Platform Development Stop Script
# This script stops the development environment

set -e

echo "🛑 Stopping OneClass Platform Development Environment..."
echo "=================================================="

# Stop all services
docker-compose down

echo "✅ All services stopped"
echo ""
echo "💡 Your local PostgreSQL database is still running"
echo "   Use 'brew services stop postgresql' to stop it if needed"
echo ""