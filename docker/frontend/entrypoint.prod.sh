#!/bin/sh
# =================================================
# Production Entrypoint Script for React Frontend
# =================================================

set -e  # Exit on any error

echo "🚀 Starting React frontend in production mode..."

# Function to validate environment
validate_environment() {
    echo "⚡ Validating environment..."
    
    # Check if build files exist
    if [ ! -f "/usr/share/nginx/html/index.html" ]; then
        echo "❌ Build files not found!"
        exit 1
    fi
    
    echo "✅ Build files validated"
}

# Function to setup nginx directories
setup_nginx() {
    echo "📁 Setting up Nginx directories..."
    
    # Create cache directory
    mkdir -p /var/cache/nginx/api
    chown -R www-data:www-data /var/cache/nginx
    
    # Create log directories  
    mkdir -p /var/log/nginx
    chown -R www-data:www-data /var/log/nginx
    
    # Create run directory for PID
    mkdir -p /var/run
    chown -R www-data:www-data /var/run
    
    echo "✅ Nginx directories configured"
}

# Function to test nginx configuration
test_nginx_config() {
    echo "🔍 Testing Nginx configuration..."
    
    nginx -t
    if [ $? -eq 0 ]; then
        echo "✅ Nginx configuration is valid"
    else
        echo "❌ Nginx configuration is invalid"
        exit 1
    fi
}

# Function to optimize static files
optimize_static_files() {
    echo "⚡ Optimizing static files..."
    
    # Compress static files if not already compressed
    find /usr/share/nginx/html -type f \( -name "*.js" -o -name "*.css" \) -exec gzip -k {} \;
    
    echo "✅ Static files optimized"
}

# Function to set proper permissions
set_permissions() {
    echo "🔒 Setting file permissions..."
    
    # Set ownership for web files
    chown -R www-data:www-data /usr/share/nginx/html
    
    # Set permissions for web files
    find /usr/share/nginx/html -type d -exec chmod 755 {} \;
    find /usr/share/nginx/html -type f -exec chmod 644 {} \;
    
    echo "✅ Permissions configured"
}

# Function to inject runtime environment variables
inject_runtime_config() {
    echo "⚙️  Injecting runtime configuration..."
    
    # Create runtime configuration file
    cat > /usr/share/nginx/html/config.js << EOF
window._env_ = {
    API_URL: '${API_URL:-/api}',
    APP_ENV: '${APP_ENV:-production}',
    VERSION: '${APP_VERSION:-1.0.0}',
    BUILD_DATE: '$(date -u +"%Y-%m-%dT%H:%M:%SZ")'
};
EOF
    
    echo "✅ Runtime configuration injected"
}

# Function to create health check endpoint
create_health_endpoint() {
    echo "❤️  Creating health check endpoint..."
    
    cat > /usr/share/nginx/html/health << EOF
{
    "status": "healthy",
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "service": "cantina-tita-frontend",
    "version": "${APP_VERSION:-1.0.0}"
}
EOF
    
    echo "✅ Health check endpoint created"
}

# Function to start nginx with proper signal handling
start_nginx() {
    echo "🌐 Starting Nginx server..."
    echo "================================================"
    echo "✅ Frontend server ready"
    echo "📱 Application URL: http://localhost:80"
    echo "❤️  Health check: http://localhost:80/health"
    echo "================================================"
    
    # Start nginx in foreground mode
    exec nginx -g "daemon off;"
}

# Handle shutdown gracefully
trap 'echo "🛑 Received shutdown signal, stopping gracefully..."; nginx -s quit; exit 0' TERM INT

# Main startup sequence
main() {
    echo "🎯 Frontend production startup sequence initiated"
    echo "================================================"
    
    # Validate environment
    validate_environment
    
    # Setup nginx
    setup_nginx
    
    # Test configuration
    test_nginx_config
    
    # Optimize files
    optimize_static_files
    
    # Set permissions
    set_permissions
    
    # Runtime configuration
    inject_runtime_config
    
    # Health endpoint
    create_health_endpoint
    
    echo "================================================"
    echo "✅ Frontend startup sequence completed"
    
    # Start the server
    start_nginx
}

# Run main function
main "$@"