#!/bin/sh

set -e

echo "=== LATECME Production Entrypoint ==="

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
while ! nc -z $DJANGO_DB_HOST $DJANGO_DB_PORT; do
    sleep 1
done
echo "PostgreSQL is available"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if DJANGO_SUPERUSER_* env vars are set
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser --noinput || echo "Superuser already exists"
fi

echo "=== Entrypoint complete, starting application ==="

exec "$@"
