#!/bin/sh
set -e

echo "Waiting for database to be ready..."
MAX_RETRIES=10
RETRY=0
until python -c "import psycopg2; conn = psycopg2.connect('${DATABASE_URL_SYNC}'); conn.close(); print('DB ready')" 2>/dev/null; do
  RETRY=$((RETRY + 1))
  if [ $RETRY -ge $MAX_RETRIES ]; then
    echo "Database not available after $MAX_RETRIES retries, exiting."
    exit 1
  fi
  echo "DB not ready, retrying in 3s... ($RETRY/$MAX_RETRIES)"
  sleep 3
done

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting FastAPI server..."
exec uvicorn main:app --reload --host 0.0.0.0 --port 8000
