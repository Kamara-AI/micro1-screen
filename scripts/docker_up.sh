#!/bin/bash
# scripts/docker_up.sh — Bring up SCREEN infrastructure (postgres first, then API)
# Run: bash scripts/docker_up.sh
# Note: make this executable with: chmod +x scripts/docker_up.sh
set -e

docker compose up -d screen_postgres
echo "Waiting for PostgreSQL..."
until docker exec screen_postgres pg_isready -U screen_user -d screen_db; do
  sleep 1
done
echo "PostgreSQL ready. Running migrations..."
poetry run alembic upgrade head
echo "Starting API..."
docker compose up -d screen_api
echo "SCREEN is running at http://localhost:8001"
echo "API docs at http://localhost:8001/docs"
