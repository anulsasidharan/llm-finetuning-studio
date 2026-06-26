#!/bin/sh
set -e

echo "[prod] Waiting for database..."
MAX_RETRIES=15
RETRY=0
until python -c "import psycopg2; conn = psycopg2.connect('${DATABASE_URL_SYNC}'); conn.close()" 2>/dev/null; do
  RETRY=$((RETRY + 1))
  if [ $RETRY -ge $MAX_RETRIES ]; then
    echo "[prod] Database unavailable after $MAX_RETRIES retries — aborting."
    exit 1
  fi
  echo "[prod] DB not ready, retrying in 3s... ($RETRY/$MAX_RETRIES)"
  sleep 3
done
echo "[prod] DB ready."

echo "[prod] Running Alembic migrations..."
alembic upgrade head

echo "[prod] Starting FastAPI (4 workers, proxy-aware)..."
exec uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --no-access-log \
  --proxy-headers \
  --forwarded-allow-ips='*'
