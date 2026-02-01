#!/bin/bash
# SmartParlay Quick Start Script
# This script sets up the development environment and runs basic tests

set -e  # Exit on any error

echo "🎯 SmartParlay - Quick Start"
echo "=============================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker found: $(docker --version)"
echo "✅ Docker Compose found: $(docker-compose --version)"
echo ""

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    cp backend/.env.example backend/.env
    echo "📝 Please edit backend/.env with your API keys"
    echo "   See docs/API_KEYS_GUIDE.md for instructions"
    echo ""
    read -p "Press Enter to continue after adding API keys..."
fi

# Start services
echo "🚀 Starting services with Docker Compose..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check health
echo ""
echo "🏥 Checking service health..."

if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend API is healthy"
else
    echo "❌ Backend API not responding. Check logs:"
    echo "   docker-compose logs backend"
    exit 1
fi

# Seed Data
echo ""
echo "🌱 Seeding database..."
echo "   - Seeding 32 NFL Teams"
docker-compose exec -T backend python -m scripts.seed_nfl
echo "   - Seeding Sample Players & Correlations"
docker-compose exec -T backend python -m scripts.seed_db

# Run simulation benchmark
echo ""
echo "🧪 Running JAX Copula simulation benchmark..."
echo "   (First run will take ~2s for JIT compilation)"
docker-compose exec -T backend python -m app.services.copula.simulation

# Check regime detection
echo ""
echo "🎮 Testing game regime detection..."
docker-compose exec -T backend python -m app.services.copula.regime

echo ""
echo "=============================="
echo "✅ SmartParlay is ready!"
echo ""
echo "🌐 Access points:"
echo "   - Backend API:      http://localhost:8000"
echo "   - API Docs:         http://localhost:8000/docs"
echo "   - Health Check:     http://localhost:8000/health"
echo "   - Prometheus:       http://localhost:9090"
echo "   - Grafana:          http://localhost:3001"
echo ""
echo "📚 Next steps:"
echo "   1. Explore API docs: http://localhost:8000/docs"
echo "   2. Get API keys: cat docs/API_KEYS_GUIDE.md"
echo "   3. Read project summary: cat PROJECT_SUMMARY.md"
echo ""
echo "🛠️  Useful commands:"
echo "   - View logs:        docker-compose logs -f backend"
echo "   - Stop services:    docker-compose down"
echo "   - Restart:          docker-compose restart backend"
echo "   - Shell access:     docker-compose exec backend bash"
echo ""
echo "Happy betting! 🎲"
