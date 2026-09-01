#!/bin/bash
# scripts/start.sh — Local development start script for SCREEN
# Run: bash scripts/start.sh
# Note: make this executable with: chmod +x scripts/start.sh
set -e

echo "Checking screen_postgres container health..."
until [ "$(docker inspect -f '{{.State.Health.Status}}' screen_postgres 2>/dev/null)" = "healthy" ]; do
  echo "  Waiting for screen_postgres to be healthy..."
  sleep 2
done
echo "screen_postgres is healthy."

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting SCREEN API on port 8001..."
uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
