#!/bin/bash
set -e

echo "🚀 Starting Memory MCP Server..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
while ! nc -z $DB_HOST $DB_PORT; do
  echo "PostgreSQL is not ready yet, waiting..."
  sleep 2
done
echo "✅ PostgreSQL is ready!"

# Wait for Qdrant to be ready
echo "⏳ Waiting for Qdrant to be ready..."
while ! nc -z $QDRANT_HOST $QDRANT_PORT; do
  echo "Qdrant is not ready yet, waiting..."
  sleep 2
done
echo "✅ Qdrant is ready!"

# Run database migrations (skip for Celery workers)
if [ "$SKIP_MIGRATIONS" != "true" ]; then
    echo "🔄 Running database migrations..."
    cd /app
    uv run alembic upgrade head
    echo "✅ Database migrations completed!"
else
    echo "⏭️ Skipping database migrations (SKIP_MIGRATIONS=true)"
fi

# Start the application
echo "🚀 Starting the application..."
exec "$@" 