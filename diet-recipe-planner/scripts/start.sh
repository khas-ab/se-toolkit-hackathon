#!/bin/bash
# Development startup script for Diet Recipe Planner
# Usage: ./scripts/start.sh
#
# This script:
# 1. Starts PostgreSQL, backend, and frontend via docker-compose
# 2. Seeds the database with 30 recipes
# 3. Optionally starts the Telegram bot

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "🍽️  Diet Recipe Planner — Starting..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "✅ Created .env — please edit it and add your API keys if needed."
    echo ""
fi

# Start all services (support both v1 and v2 syntax)
echo "🚀 Starting Docker services..."
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    docker compose up -d
else
    docker-compose up -d
fi

echo ""
echo "⏳ Waiting for backend to be ready..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend did not start in time. Check logs: docker compose logs backend"
        exit 1
    fi
    sleep 2
done

# Seed the database
echo ""
echo "🌱 Seeding database with recipes..."
docker compose exec -T backend python seed_recipes.py || echo "⚠️  Seed may have failed (recipes might already exist)"

echo ""
echo "✅ All services started!"
echo ""
echo "📱 Frontend:  http://localhost:5173"
echo "🔌 Backend:   http://localhost:8000"
echo "📖 API Docs:  http://localhost:8000/docs"
echo ""
echo "To start the Telegram bot:"
echo "  docker compose exec backend python telegram_bot.py"
echo ""
echo "To stop all services:"
echo "  docker compose down"
