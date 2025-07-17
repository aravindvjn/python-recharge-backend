#!/bin/bash

# Recharge Backend Deployment Script
# Deploys Django app with Supervisor, Gunicorn, Nginx, and optional SSL with Certbot

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root. Please run as a regular user with sudo privileges."
    fi
}

# Check if user has sudo privileges
check_sudo() {
    if ! sudo -n true 2>/dev/null; then
        error "This script requires sudo privileges. Please ensure your user can run sudo commands."
    fi
}

# Update system packages
update_system() {
    log "Updating system packages..."
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y software-properties-common curl wget git
}

# Install Python and dependencies
install_python() {
    log "Installing Python and dependencies..."
    sudo apt install -y python3 python3-pip python3-venv python3-dev
    sudo apt install -y build-essential libssl-dev libffi-dev
    
    # Install UV package manager
    if ! command -v uv &> /dev/null; then
        log "Installing UV package manager..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.cargo/env
    fi
}

# Install and configure PostgreSQL
install_postgresql() {
    log "Installing PostgreSQL..."
    sudo apt install -y postgresql postgresql-contrib postgresql-server-dev-all
    
    # Start and enable PostgreSQL
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    
    # Get database configuration from user
    read -p "Enter database name [recharge_backend]: " DB_NAME
    DB_NAME=${DB_NAME:-recharge_backend}
    
    read -p "Enter database username [recharge_user]: " DB_USER
    DB_USER=${DB_USER:-recharge_user}
    
    read -s -p "Enter database password: " DB_PASSWORD
    echo
    
    if [[ -z "$DB_PASSWORD" ]]; then
        error "Database password cannot be empty"
    fi
    
    # Create database and user
    log "Creating PostgreSQL database and user..."
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
    sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;"
    
    log "PostgreSQL setup completed successfully"
}

# Install Nginx
install_nginx() {
    log "Installing Nginx..."
    sudo apt install -y nginx
    sudo systemctl start nginx
    sudo systemctl enable nginx
}

# Install Supervisor
install_supervisor() {
    log "Installing Supervisor..."
    sudo apt install -y supervisor
    sudo systemctl start supervisor
    sudo systemctl enable supervisor
}

# Install Certbot for SSL
install_certbot() {
    log "Installing Certbot for SSL certificates..."
    sudo apt install -y certbot python3-certbot-nginx
}

# Get project configuration
get_project_config() {
    log "Getting project configuration..."
    
    # Get current directory as project path
    PROJECT_PATH=$(pwd)
    PROJECT_NAME=$(basename "$PROJECT_PATH")
    
    read -p "Enter domain name (e.g., example.com) [localhost]: " DOMAIN_NAME
    DOMAIN_NAME=${DOMAIN_NAME:-localhost}
    
    read -p "Enter project user [$USER]: " PROJECT_USER
    PROJECT_USER=${PROJECT_USER:-$USER}
    
    read -p "Use PostgreSQL database? (y/n) [y]: " USE_POSTGRES
    USE_POSTGRES=${USE_POSTGRES:-y}
    
    read -p "Setup SSL certificate with Certbot? (y/n) [n]: " SETUP_SSL
    SETUP_SSL=${SETUP_SSL:-n}
    
    # Generate secret key
    SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
    
    info "Project Configuration:"
    info "- Project Path: $PROJECT_PATH"
    info "- Project Name: $PROJECT_NAME"
    info "- Domain: $DOMAIN_NAME"
    info "- User: $PROJECT_USER"
    info "- PostgreSQL: $USE_POSTGRES"
    info "- SSL: $SETUP_SSL"
}

# Setup virtual environment and install dependencies
setup_virtualenv() {
    log "Setting up virtual environment..."
    
    cd "$PROJECT_PATH"
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
    else
        error "requirements.txt not found in project directory"
    fi
    
    # Install additional production dependencies
    pip install gunicorn psycopg2-binary
}

# Create production environment file
create_production_settings() {
    log "Creating production environment configuration..."
    
    # Create production .env file
    cat > "$PROJECT_PATH/.env.production" << EOF
# Recharge Backend Production Configuration
# Generated automatically by deployment script

# Django Core Settings
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=$DOMAIN_NAME,www.$DOMAIN_NAME,localhost,127.0.0.1

EOF

    if [[ "$USE_POSTGRES" == "y" ]]; then
        cat >> "$PROJECT_PATH/.env.production" << EOF
# Database Configuration (PostgreSQL)
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432

EOF
    fi

    cat >> "$PROJECT_PATH/.env.production" << EOF
# JWT Settings
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# OTP Settings
OTP_EXPIRY_MINUTES=5

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Security Settings
SECURE_SSL_REDIRECT=$([[ "$SETUP_SSL" == "y" ]] && echo "True" || echo "False")
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
EOF

    # Create symlink for production
    ln -sf "$PROJECT_PATH/.env.production" "$PROJECT_PATH/.env"
    
    # Create logs directory
    mkdir -p "$PROJECT_PATH/logs"
    
    log "Production environment configuration created successfully"
    log "Note: Update .env.production with your email credentials for production use"
}

# Run Django migrations and collect static files
setup_django() {
    log "Setting up Django..."
    
    cd "$PROJECT_PATH"
    source venv/bin/activate
    
    # Set Django settings module
    export DJANGO_SETTINGS_MODULE=config.production_settings
    
    # Run migrations
    log "Running Django migrations..."
    python manage.py migrate
    
    # Collect static files
    log "Collecting static files..."
    python manage.py collectstatic --noinput
    
    # Create superuser prompt
    read -p "Create Django superuser? (y/n) [y]: " CREATE_SUPERUSER
    CREATE_SUPERUSER=${CREATE_SUPERUSER:-y}
    
    if [[ "$CREATE_SUPERUSER" == "y" ]]; then
        log "Creating Django superuser..."
        python manage.py createsuperuser
    fi
}

# Create Gunicorn configuration
create_gunicorn_config() {
    log "Creating Gunicorn configuration..."
    
    cat > "$PROJECT_PATH/gunicorn_config.py" << EOF
# Gunicorn configuration file
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 5
preload_app = True
daemon = False
user = "$PROJECT_USER"
group = "$PROJECT_USER"
raw_env = [
    'DJANGO_SETTINGS_MODULE=config.production_settings',
]

# Logging
accesslog = "$PROJECT_PATH/logs/gunicorn_access.log"
errorlog = "$PROJECT_PATH/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'recharge_backend'

# Server mechanics
pidfile = "$PROJECT_PATH/logs/gunicorn.pid"
EOF

    log "Gunicorn configuration created"
}

# Create Supervisor configuration
create_supervisor_config() {
    log "Creating Supervisor configuration..."
    
    sudo tee /etc/supervisor/conf.d/recharge_backend.conf > /dev/null << EOF
[program:recharge_backend]
command=$PROJECT_PATH/venv/bin/gunicorn config.wsgi:application -c $PROJECT_PATH/gunicorn_config.py
directory=$PROJECT_PATH
user=$PROJECT_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=$PROJECT_PATH/logs/supervisor.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=3
environment=DJANGO_SETTINGS_MODULE=config.production_settings
EOF

    # Update supervisor
    sudo supervisorctl reread
    sudo supervisorctl update
    sudo supervisorctl start recharge_backend
    
    log "Supervisor configuration created and service started"
}

# Create Nginx configuration
create_nginx_config() {
    log "Creating Nginx configuration..."
    
    sudo tee /etc/nginx/sites-available/recharge_backend > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /static/ {
        alias $PROJECT_PATH/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias $PROJECT_PATH/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Health check endpoint
    location /health/ {
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }
}
EOF

    # Enable site
    sudo ln -sf /etc/nginx/sites-available/recharge_backend /etc/nginx/sites-enabled/
    
    # Remove default site if it exists
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test Nginx configuration
    sudo nginx -t
    
    # Restart Nginx
    sudo systemctl restart nginx
    
    log "Nginx configuration created and service restarted"
}

# Setup SSL with Certbot
setup_ssl() {
    if [[ "$SETUP_SSL" == "y" ]] && [[ "$DOMAIN_NAME" != "localhost" ]]; then
        log "Setting up SSL certificate with Certbot..."
        
        # Check if domain resolves
        if ! nslookup "$DOMAIN_NAME" > /dev/null 2>&1; then
            warn "Domain $DOMAIN_NAME does not resolve. Make sure DNS is configured correctly."
            read -p "Continue with SSL setup? (y/n) [n]: " CONTINUE_SSL
            CONTINUE_SSL=${CONTINUE_SSL:-n}
            
            if [[ "$CONTINUE_SSL" != "y" ]]; then
                warn "Skipping SSL setup"
                return
            fi
        fi
        
        # Get SSL certificate
        sudo certbot --nginx -d "$DOMAIN_NAME" -d "www.$DOMAIN_NAME" --non-interactive --agree-tos --email "admin@$DOMAIN_NAME" || {
            warn "SSL certificate generation failed. You can run it manually later with:"
            warn "sudo certbot --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME"
        }
        
        # Setup auto-renewal
        sudo systemctl enable certbot.timer
        sudo systemctl start certbot.timer
        
        log "SSL certificate setup completed"
    else
        info "Skipping SSL setup"
    fi
}

# Setup firewall
setup_firewall() {
    log "Configuring firewall..."
    
    # Install UFW if not installed
    sudo apt install -y ufw
    
    # Reset UFW to defaults
    sudo ufw --force reset
    
    # Default policies
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH (be careful with this)
    sudo ufw allow ssh
    
    # Allow HTTP and HTTPS
    sudo ufw allow 'Nginx Full'
    
    # Enable firewall
    sudo ufw --force enable
    
    log "Firewall configured successfully"
}

# Create systemd service for monitoring
create_monitoring_service() {
    log "Creating monitoring service..."
    
    cat > "$PROJECT_PATH/monitor.sh" << 'EOF'
#!/bin/bash
# Simple monitoring script for Recharge Backend

LOG_FILE="/var/log/recharge_backend_monitor.log"

log_message() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Check if Gunicorn is running
if ! pgrep -f "gunicorn.*recharge_backend" > /dev/null; then
    log_message "ERROR: Gunicorn process not found. Attempting restart..."
    sudo supervisorctl restart recharge_backend
fi

# Check if Nginx is running
if ! systemctl is-active --quiet nginx; then
    log_message "ERROR: Nginx is not running. Attempting restart..."
    sudo systemctl restart nginx
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    log_message "WARNING: Disk usage is ${DISK_USAGE}%"
fi

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.2f", $3/$2 * 100.0)}' | cut -d. -f1)
if [ "$MEMORY_USAGE" -gt 90 ]; then
    log_message "WARNING: Memory usage is ${MEMORY_USAGE}%"
fi

log_message "Health check completed successfully"
EOF

    chmod +x "$PROJECT_PATH/monitor.sh"
    
    # Add to crontab for the user
    (crontab -l 2>/dev/null; echo "*/5 * * * * $PROJECT_PATH/monitor.sh") | crontab -
    
    log "Monitoring service created"
}

# Final setup and information
final_setup() {
    log "Running final setup..."
    
    # Set proper permissions
    sudo chown -R "$PROJECT_USER:$PROJECT_USER" "$PROJECT_PATH"
    chmod -R 755 "$PROJECT_PATH"
    
    # Create backup script
    cat > "$PROJECT_PATH/backup.sh" << EOF
#!/bin/bash
# Backup script for Recharge Backend

BACKUP_DIR="/home/$PROJECT_USER/backups"
TIMESTAMP=\$(date +%Y%m%d_%H%M%S)

mkdir -p "\$BACKUP_DIR"

# Backup database
EOF

    if [[ "$USE_POSTGRES" == "y" ]]; then
        cat >> "$PROJECT_PATH/backup.sh" << EOF
pg_dump -U $DB_USER -h localhost $DB_NAME > "\$BACKUP_DIR/db_backup_\$TIMESTAMP.sql"
EOF
    else
        cat >> "$PROJECT_PATH/backup.sh" << EOF
cp "$PROJECT_PATH/db.sqlite3" "\$BACKUP_DIR/db_backup_\$TIMESTAMP.sqlite3"
EOF
    fi

    cat >> "$PROJECT_PATH/backup.sh" << EOF

# Backup media files
tar -czf "\$BACKUP_DIR/media_backup_\$TIMESTAMP.tar.gz" -C "$PROJECT_PATH" media/

# Keep only last 7 days of backups
find "\$BACKUP_DIR" -name "*backup_*" -mtime +7 -delete

echo "Backup completed: \$TIMESTAMP"
EOF

    chmod +x "$PROJECT_PATH/backup.sh"
    
    # Add daily backup to crontab
    (crontab -l 2>/dev/null; echo "0 2 * * * $PROJECT_PATH/backup.sh") | crontab -
    
    log "Final setup completed"
}

# Display final information
show_final_info() {
    log "Deployment completed successfully!"
    echo
    echo "=================================="
    echo "🚀 Recharge Backend Deployment Info"
    echo "=================================="
    echo
    echo "📍 Project Details:"
    echo "   - Project Path: $PROJECT_PATH"
    echo "   - Domain: $DOMAIN_NAME"
    echo "   - Database: $([ "$USE_POSTGRES" == "y" ] && echo "PostgreSQL" || echo "SQLite")"
    echo "   - SSL: $([ "$SETUP_SSL" == "y" ] && echo "Enabled" || echo "Disabled")"
    echo
    echo "🌐 URLs:"
    if [[ "$SETUP_SSL" == "y" && "$DOMAIN_NAME" != "localhost" ]]; then
        echo "   - Website: https://$DOMAIN_NAME"
        echo "   - API Docs: https://$DOMAIN_NAME/swagger/"
        echo "   - Admin: https://$DOMAIN_NAME/admin/"
    else
        echo "   - Website: http://$DOMAIN_NAME"
        echo "   - API Docs: http://$DOMAIN_NAME/swagger/"
        echo "   - Admin: http://$DOMAIN_NAME/admin/"
    fi
    echo
    echo "🔧 Management Commands:"
    echo "   - Check status: sudo supervisorctl status recharge_backend"
    echo "   - Restart app: sudo supervisorctl restart recharge_backend"
    echo "   - View logs: tail -f $PROJECT_PATH/logs/supervisor.log"
    echo "   - Nginx status: sudo systemctl status nginx"
    echo "   - SSL renewal: sudo certbot renew --dry-run"
    echo
    echo "📁 Important Files:"
    echo "   - Settings: $PROJECT_PATH/config/production_settings.py"
    echo "   - Gunicorn: $PROJECT_PATH/gunicorn_config.py"
    echo "   - Supervisor: /etc/supervisor/conf.d/recharge_backend.conf"
    echo "   - Nginx: /etc/nginx/sites-available/recharge_backend"
    echo "   - Logs: $PROJECT_PATH/logs/"
    echo
    echo "💾 Backup & Monitoring:"
    echo "   - Backup script: $PROJECT_PATH/backup.sh"
    echo "   - Monitor script: $PROJECT_PATH/monitor.sh"
    echo "   - Log file: /var/log/recharge_backend_monitor.log"
    echo
    if [[ "$USE_POSTGRES" == "y" ]]; then
        echo "🗃️ Database Info:"
        echo "   - Database: $DB_NAME"
        echo "   - Username: $DB_USER"
        echo "   - Host: localhost:5432"
        echo
    fi
    echo "✅ Your Recharge Backend is now live!"
    echo "=================================="
}

# Main deployment function
main() {
    log "Starting Recharge Backend deployment..."
    echo
    
    # Initial checks
    check_root
    check_sudo
    
    # Get configuration
    get_project_config
    
    # Confirm deployment
    echo
    read -p "Proceed with deployment? (y/n): " CONFIRM
    if [[ "$CONFIRM" != "y" ]]; then
        error "Deployment cancelled by user"
    fi
    
    # System setup
    update_system
    install_python
    
    # Database setup
    if [[ "$USE_POSTGRES" == "y" ]]; then
        install_postgresql
    fi
    
    # Web server setup
    install_nginx
    install_supervisor
    
    # SSL setup
    if [[ "$SETUP_SSL" == "y" ]]; then
        install_certbot
    fi
    
    # Application setup
    setup_virtualenv
    create_production_settings
    setup_django
    
    # Service configuration
    create_gunicorn_config
    create_supervisor_config
    create_nginx_config
    
    # Security and monitoring
    setup_ssl
    setup_firewall
    create_monitoring_service
    
    # Final steps
    final_setup
    show_final_info
}

# Run main function
main "$@"