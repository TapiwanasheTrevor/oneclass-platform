#!/bin/bash

echo "🚀 Starting OneClass Platform - Simple Mode"
echo "============================================"

# Just start the backend services that are already configured
echo "🐳 Starting backend services..."
docker-compose -f docker-compose.dev.yml up -d

echo "⏳ Waiting 5 seconds for services to start..."
sleep 5

echo "✅ Backend services started!"
echo ""
echo "📊 Service URLs:"
echo "- Backend API: http://localhost:8000"
echo "- MailHog: http://localhost:8025"
echo "- Redis: localhost:6379"
echo ""
echo "🌐 Now starting frontend..."
echo "Frontend URL: http://localhost:3000"
echo ""
echo "To stop backend services: docker-compose -f docker-compose.dev.yml down"
echo ""

# Change to frontend directory and start
cd frontend && npm run dev