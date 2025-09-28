#!/bin/bash

# Production deployment script for Movie Recommendation API
# This script handles the deployment process including migrations,
# static files collection, and service restarts

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/var/www/movie_api"
VENV_DIR="$PROJECT_DIR/venv"
GIT_REPO="https://github.com/your-username/movie-recommendation-api.git"
SERVICE_NAME="movie_api"
CELERY_SERVICE="movie_api_celery"
NGINX_SERVICE="nginx"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking system requirements..."
    
    # Check if running as root or with sudo
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root or with sudo"
        exit 1
    fi
    
    # Check if git is installed
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed. Please install git first."
        exit 1
    fi
    
    # Check if python3 is installed
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 is not installed. Please install Python3 first."
        exit 1
    fi
    
    # Check if pip is installed
    if ! command -v pip3 &> /dev/null; then
        log_error "Pip3 is not installed. Please install pip3 first."
        exit 1
    fi
}

setup_project() {
    log_info "Setting up project directory..."
    
    # Create project directory if it doesn't exist
    if [ ! -d "$PROJECT_DIR" ]; then
        mkdir -p "$PROJECT_DIR"
        log_info "Created project directory: $PROJECT_DIR"
    fi
    
    cd "$PROJECT_DIR"
    
    # Clone or update repository
    if [ ! -d ".git" ]; then
        log_info "Cloning repository..."
        git clone "$GIT_REPO" .
    else
        log_info "Updating repository..."
        git fetch origin
        git reset --hard origin/main
    fi
}

setup_virtualenv() {
    log_info "Setting up virtual environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        log_info "Created virtual environment: $VENV_DIR"
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    log_info "Installing Python dependencies..."
    pip install -r requirements.txt
}

setup_environment() {
    log_info "Setting up environment variables..."
    
    # Copy environment file if it doesn't exist
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_warn "Copied .env.example to .env. Please update the values."
        else
            log_error ".env.example file not found. Please create .env file manually."
            exit 1
        fi
    fi
    
    # Check if required environment variables are set
    source .env
    
    if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your-secret-key-here" ]; then
        log_error "SECRET_KEY is not set in .env file"
        exit 1
    fi
    
    if [ -z "$TMDB_API_KEY" ] || [ "$TMDB_API_KEY" = "your-tmdb-api-key-here" ]; then
        log_warn "TMDB_API_KEY is not set in .env file. Some features may not work."
    fi
}

run_migrations() {
    log_info "Running database migrations..."
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Run migrations
    python manage.py migrate
    
    # Create superuser if it doesn't exist
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin@movieapi.com', 'admin123')
    print('Superuser created')
else:
    print('Superuser already exists')
"
}

collect_static() {
    log_info "Collecting static files..."
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Collect static files
    python manage.py collectstatic --noinput
}

setup_services() {
    log_info "Setting up systemd services..."
    
    # Create gunicorn service file
    cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=Movie API Gunicorn daemon
Requires=$SERVICE_NAME.socket
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$VENV_DIR/bin/gunicorn --access-logfile - --workers 3 --bind unix:$PROJECT_DIR/movie_api.sock movie_api.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

    # Create gunicorn socket file
    cat > "/etc/systemd/system/$SERVICE_NAME.socket" << EOF
[Unit]
Description=Movie API gunicorn socket

[Socket]
ListenStream=$PROJECT_DIR/movie_api.sock

[Install]
WantedBy=sockets.target
EOF

    # Create celery service file
    cat > "/etc/systemd/system/$CELERY_SERVICE.service" << EOF
[Unit]
Description=Movie API Celery Worker
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$VENV_DIR/bin/celery -A movie_api worker --loglevel=info --detach
ExecStop=$VENV_DIR/bin/celery -A movie_api control shutdown
ExecReload=$VENV_DIR/bin/celery -A movie_api control reload
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

    # Set proper permissions
    chown -R www-data:www-data "$PROJECT_DIR"
    chmod -R 755 "$PROJECT_DIR"
    
    # Reload systemd and enable services
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME.socket"
    systemctl enable "$SERVICE_NAME.service"
    systemctl enable "$CELERY_SERVICE.service"
}

restart_services() {
    log_info "Restarting services..."
    
    # Restart services
    systemctl restart "$SERVICE_NAME.socket"
    systemctl restart "$SERVICE_NAME.service"
    systemctl restart "$CELERY_SERVICE.service"
    
    # Restart nginx if it's running
    if systemctl is-active --quiet nginx; then
        systemctl restart nginx
    fi
    
    # Check service status
    log_info "Service status:"
    systemctl status "$SERVICE_NAME.service" --no-pager -l
    systemctl status "$CELERY_SERVICE.service" --no-pager -l
}

run_tests() {
    log_info "Running tests..."
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Run tests
    python manage.py test
}

show_status() {
    log_info "Deployment completed successfully!"
    echo
    echo "Services status:"
    systemctl status "$SERVICE_NAME.service" --no-pager -l
    echo
    systemctl status "$CELERY_SERVICE.service" --no-pager -l
    echo
    log_info "Next steps:"
    echo "1. Configure your web server (nginx/apache) to proxy to the socket"
    echo "2. Set up SSL certificates"
    echo "3. Configure firewall rules"
    echo "4. Set up monitoring and logging"
    echo "5. Configure backup procedures"
}

# Main deployment process
main() {
    log_info "Starting Movie API deployment..."
    
    check_requirements
    setup_project
    setup_virtualenv
    setup_environment
    run_migrations
    collect_static
    setup_services
    restart_services
    
    # Run tests if requested
    if [ "$1" = "--test" ]; then
        run_tests
    fi
    
    show_status
}

# Run main function
main "$@"