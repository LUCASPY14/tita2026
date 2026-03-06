#!/bin/bash
# =================================================
# Production Entrypoint Script for Django Backend
# =================================================

set -e  # Exit on any error

echo "🚀 Starting Django backend in production mode..."

# Function to wait for database
wait_for_db() {
    echo "⏳ Waiting for database connection..."
    while ! python -c "
import os
import django
import sys
from django.core.management.base import BaseCommand
from django.db import connections
from django.core.exceptions import ImproperlyConfigured

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.production')
django.setup()

try:
    db_conn = connections['default']
    db_conn.cursor()
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
" 2>/dev/null; do
        echo "🔄 Database is unavailable - retrying in 2 seconds..."
        sleep 2
    done
}

# Function to run database migrations
run_migrations() {
    echo "📦 Running database migrations..."
    python manage.py migrate --noinput --settings=backend.settings.production
    if [ $? -eq 0 ]; then
        echo "✅ Migrations completed successfully"
    else
        echo "❌ Migration failed"
        exit 1
    fi
}

# Function to collect static files
collect_static() {
    echo "📁 Collecting static files..."
    python manage.py collectstatic --noinput --clear --settings=backend.settings.production
    if [ $? -eq 0 ]; then
        echo "✅ Static files collected successfully"
    else
        echo "❌ Static file collection failed"
        exit 1
    fi
}

# Function to create superuser if needed
create_superuser() {
    if [ "$DJANGO_CREATE_SUPERUSER" = "true" ]; then
        echo "👤 Creating superuser..."
        python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$DJANGO_SUPERUSER_EMAIL').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
    print('✅ Superuser created successfully')
else:
    print('ℹ️  Superuser already exists')
"
    fi
}

# Function to validate settings
validate_settings() {
    echo "⚡ Validating Django settings..."
    python manage.py check --settings=backend.settings.production --deploy
    if [ $? -eq 0 ]; then
        echo "✅ Settings validation successful"
    else
        echo "❌ Settings validation failed"
        exit 1
    fi
}

# Function to warm up application
warmup_app() {
    echo "🔥 Warming up application..."
    python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.production')
django.setup()
# Import key modules to warm up
from django.contrib.auth.models import User
from apps.usuarios.models import *
from apps.clientes.models import *
print('✅ Application warmed up successfully')
"
}

# Main startup sequence
main() {
    echo "🎯 Production startup sequence initiated"
    echo "================================================"
    
    # Wait for dependencies
    wait_for_db
    
    # Validate configuration
    validate_settings
    
    # Database setup
    run_migrations
    
    # Static files
    collect_static
    
    # Optional superuser creation
    create_superuser
    
    # Warm up the application
    warmup_app
    
    echo "================================================"
    echo "✅ Production startup sequence completed"
    echo "🚀 Starting Gunicorn server..."
    echo "================================================"
    
    # Execute the main command
    exec "$@"
}

# Handle shutdown gracefully
trap 'echo "🛑 Received shutdown signal, stopping gracefully..."; kill -TERM $PID; wait $PID' TERM INT

# Run main function
main "$@" &
PID=$!
wait $PID