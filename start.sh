#!/usr/bin/env bash
set -e

echo "Starting Canvas Studio..."

docker compose up -d postgres

echo "Waiting for Postgres..."
until docker compose exec -T postgres pg_isready -U coinswarm -d canvas_studio >/dev/null 2>&1; do
  sleep 1
done
echo "Postgres ready."

cd server && uvicorn main:app --host 0.0.0.0 --port 5174 --reload &
SERVER_PID=$!

cd .. && npm run dev &
VITE_PID=$!

trap "kill $SERVER_PID $VITE_PID 2>/dev/null" EXIT
wait
