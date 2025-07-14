#!/bin/bash

# Start all services for development
echo "🚀 Starting GreekSTT Research Platform - All Services"

# Start infrastructure first
echo "📦 Starting infrastructure services..."
docker-compose up -d db redis pgadmin mailhog

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
docker-compose exec -T db pg_isready -U postgres

# Start backend service
echo "🔧 Starting backend service..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d backend

# Start AI service (check if GPU is available)
if command -v nvidia-smi &> /dev/null; then
    echo "🚀 Starting AI service with GPU support..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d ai-gpu
else
    echo "💻 Starting AI service with CPU only..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d ai-cpu
fi

echo "✅ All services started!"
echo ""
echo "🌐 Service URLs:"
echo "   Frontend (Angular): http://localhost:4200 (start manually with: npm run dev:frontend)"
echo "   Backend API: http://localhost:5001"
echo "   AI Service: http://localhost:8000"
echo "   PgAdmin: http://localhost:5050 (admin@greekstt.research/admin)"
echo "   MailHog: http://localhost:8025"
echo ""
echo "🔧 Debug Ports:"
echo "   Backend Debugpy: localhost:5678"
echo "   AI Service Debugpy: localhost:5679"
echo ""
echo "📊 Check status with: docker-compose ps"
echo "📋 View logs with: docker-compose logs -f [service_name]"