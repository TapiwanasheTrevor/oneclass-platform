#!/bin/bash
set -e

echo "🚀 Starting OneClass Platform - Local Development Mode"
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Check if local PostgreSQL is running
if ! nc -z localhost 5432 > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not running on localhost:5432"
    echo "Please start your local PostgreSQL instance first."
    exit 1
fi

# Start Docker services (Redis, MailHog, Backend only)
echo "🐳 Starting backend services..."
docker-compose up -d redis mailhog backend

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 10

# Check if frontend dependencies are installed
cd frontend
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install --legacy-peer-deps
fi

# Start frontend locally
echo "🌐 Starting frontend locally..."
echo "Frontend will run on: http://localhost:3001"
echo "Backend API: http://localhost:8000"
echo "MailHog: http://localhost:8025"
echo ""
echo "To stop backend services: docker-compose down"
echo ""

# Start frontend in the foreground
npm run dev