#!/usr/bin/env bash
set -euo pipefail

echo "[1/5] Launching stack..."
docker compose -f infra/docker-compose.yml up -d --build

echo "[2/5] Running migrations..."
docker compose -f infra/docker-compose.yml exec api alembic upgrade head

echo "[3/5] Seeding demo data..."
docker compose -f infra/docker-compose.yml exec api python -m app.seed.seed_demo

echo "[4/5] Upload sample receipt image"
curl -s -F "file=@docs/samples/receipt1.png" http://localhost:8000/api/v1/receipts/upload | jq . || true

echo "[5/5] Analytics summary"
curl -s "http://localhost:8000/api/v1/analytics/summary" | jq . || true

echo "Open API docs: http://localhost:8000/docs"
