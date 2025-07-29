#!/bin/bash

# OneClass Platform Development Startup Script
# This script starts the development environment using Docker Compose

set -e

echo "🚀 Starting OneClass Platform Development Environment..."
echo "=================================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Check if PostgreSQL is running locally
if ! nc -z localhost 5432 >/dev/null 2>&1; then
    echo "❌ PostgreSQL is not running on localhost:5432"
    echo "Please start your local PostgreSQL instance first."
    exit 1
fi

# Start services
echo "🔧 Starting Docker services..."
docker-compose up -d redis mailhog

echo "📦 Building and starting backend..."
docker-compose up --build -d backend

echo "🌐 Building and starting frontend..."
docker-compose up --build -d frontend

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check Redis
if docker-compose exec redis redis-cli ping >/dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is not responding"
fi

# Check Backend
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ Backend is running"
else
    echo "❌ Backend is not responding"
fi

# Check Frontend
if curl -s http://localhost:3000 >/dev/null 2>&1; then
    echo "✅ Frontend is running"
else
    echo "❌ Frontend is not responding"
fi

echo ""
echo "🎉 Development environment is ready!"
echo "=================================================="
echo "📱 Frontend:     http://localhost:3000"
echo "🔧 Backend API:  http://localhost:8000"
echo "📧 MailHog:      http://localhost:8025"
echo "💾 Redis:        localhost:6379"
echo "🗄️  PostgreSQL:   localhost:5432 (local)"
echo ""
echo "📋 Useful commands:"
echo "  View logs:     docker-compose logs -f"
echo "  Stop services: docker-compose down"
echo "  Restart:       docker-compose restart"
echo ""
echo "🔍 To test the SIS module:"
echo "  curl http://localhost:8000/api/v1/sis/health"
echo ""