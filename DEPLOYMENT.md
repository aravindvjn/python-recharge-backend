# Recharge Backend Deployment Guide

This guide explains how to deploy the Recharge Backend application to a production server using the automated deployment script.

## 🚀 Quick Deployment

### Prerequisites
- Ubuntu 20.04 LTS or later
- A user account with sudo privileges (not root)
- Domain name pointing to your server (optional, for SSL)
- At least 2GB RAM and 20GB storage

### One-Command Deployment
```bash
# Clone the repository
git clone <your-repo-url>
cd callCenter

# Run the deployment script
./deploy.sh
```

## 📋 Deployment Process

The deployment script will guide you through the following interactive setup:

### 1. **Project Configuration**
- Domain name (e.g., api.yourcompany.com)
- Project user (defaults to current user)
- Database choice (PostgreSQL or SQLite)
- SSL certificate setup (yes/no)

### 2. **Database Setup**
**PostgreSQL (Recommended for Production):**
- Database name: `recharge_backend`
- Username: `recharge_user`
- Password: (you'll be prompted)

**SQLite (Development/Testing):**
- Uses local SQLite file
- No additional configuration needed

### 3. **SSL Certificate**
If you choose SSL setup:
- Automatic certificate generation with Let's Encrypt
- Auto-renewal configuration
- HTTPS redirect setup

## 🏗️ What Gets Installed

### **System Components**
- **Python 3** with pip and venv
- **UV Package Manager** for fast dependency management
- **PostgreSQL** (if selected)
- **Nginx** as reverse proxy and static file server
- **Supervisor** for process management
- **Certbot** for SSL certificate management
- **UFW Firewall** with proper rules

### **Application Setup**
- **Virtual Environment** with all dependencies
- **Gunicorn** WSGI server with optimized configuration
- **Production Settings** with security hardening
- **Static Files** collection and serving
- **Database Migrations** and superuser creation

### **Monitoring & Maintenance**
- **Health Monitoring** script running every 5 minutes
- **Daily Backups** of database and media files
- **Log Rotation** and management
- **Process Monitoring** with automatic restart

## 🔧 Post-Deployment Management

### **Service Management**
```bash
# Check application status
sudo supervisorctl status recharge_backend

# Restart application
sudo supervisorctl restart recharge_backend

# View application logs
tail -f /path/to/project/logs/supervisor.log

# Check Nginx status
sudo systemctl status nginx

# Restart Nginx
sudo systemctl restart nginx
```

### **Database Management**
```bash
# Run migrations (if needed)
cd /path/to/project
source venv/bin/activate
DJANGO_SETTINGS_MODULE=config.production_settings python manage.py migrate

# Create additional superuser
DJANGO_SETTINGS_MODULE=config.production_settings python manage.py createsuperuser

# Backup database manually
./backup.sh
```

### **SSL Certificate Management**
```bash
# Check certificate status
sudo certbot certificates

# Renew certificates manually
sudo certbot renew

# Test auto-renewal
sudo certbot renew --dry-run
```

## 📁 Important File Locations

### **Application Files**
- **Project Directory**: `/path/to/your/project/`
- **Virtual Environment**: `/path/to/project/venv/`
- **Static Files**: `/path/to/project/staticfiles/`
- **Media Files**: `/path/to/project/media/`
- **Logs**: `/path/to/project/logs/`

### **Configuration Files**
- **Production Settings**: `config/production_settings.py`
- **Gunicorn Config**: `gunicorn_config.py`
- **Supervisor Config**: `/etc/supervisor/conf.d/recharge_backend.conf`
- **Nginx Config**: `/etc/nginx/sites-available/recharge_backend`

### **Scripts**
- **Deployment**: `deploy.sh`
- **Backup**: `backup.sh`
- **Monitoring**: `monitor.sh`

## 🌐 Accessing Your Application

After successful deployment:

### **Web Interfaces**
- **Main Application**: `https://yourdomain.com` or `http://yourdomain.com`
- **API Documentation**: `https://yourdomain.com/swagger/`
- **Admin Panel**: `https://yourdomain.com/admin/`
- **ReDoc Documentation**: `https://yourdomain.com/redoc/`

### **Default Admin Credentials**
The deployment script will prompt you to create a superuser account.

## 🔒 Security Features

The deployment automatically configures:

### **Firewall Rules**
- SSH access (port 22)
- HTTP access (port 80)
- HTTPS access (port 443)
- All other ports blocked by default

### **Security Headers**
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- X-Content-Type-Options: nosniff
- HSTS headers (with SSL)
- Content Security Policy

### **Application Security**
- DEBUG = False in production
- Secret key generation
- Secure database configuration
- Static file serving optimization

## 📊 Monitoring & Logs

### **Application Logs**
```bash
# Supervisor logs (application output)
tail -f /path/to/project/logs/supervisor.log

# Django application logs
tail -f /path/to/project/logs/django.log

# Gunicorn access logs
tail -f /path/to/project/logs/gunicorn_access.log

# Gunicorn error logs
tail -f /path/to/project/logs/gunicorn_error.log
```

### **System Logs**
```bash
# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# System monitoring logs
sudo tail -f /var/log/recharge_backend_monitor.log
```

### **Health Monitoring**
The monitoring script checks:
- ✅ Gunicorn process status
- ✅ Nginx service status
- ✅ Disk space usage (warns at 90%)
- ✅ Memory usage (warns at 90%)
- ✅ Automatic service restart if needed

## 💾 Backup & Recovery

### **Automated Backups**
- **Daily backups** at 2:00 AM
- **Database backups** (PostgreSQL dump or SQLite copy)
- **Media file backups** (compressed tar.gz)
- **Retention**: 7 days (automatic cleanup)

### **Manual Backup**
```bash
# Run backup script manually
./backup.sh

# View backup files
ls -la /home/username/backups/
```

### **Recovery Process**
```bash
# Restore database (PostgreSQL)
psql -U recharge_user -h localhost recharge_backend < backup_file.sql

# Restore database (SQLite)
cp backup_file.sqlite3 db.sqlite3

# Restore media files
tar -xzf media_backup_timestamp.tar.gz
```

## 🚨 Troubleshooting

### **Common Issues**

#### **Application Not Starting**
```bash
# Check supervisor status
sudo supervisorctl status

# View error logs
tail -f /path/to/project/logs/supervisor.log

# Restart application
sudo supervisorctl restart recharge_backend
```

#### **502 Bad Gateway Error**
```bash
# Check if Gunicorn is running
ps aux | grep gunicorn

# Check Nginx configuration
sudo nginx -t

# Restart services
sudo supervisorctl restart recharge_backend
sudo systemctl restart nginx
```

#### **SSL Certificate Issues**
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew --force-renewal

# Check Nginx SSL configuration
sudo nginx -t
```

#### **Database Connection Issues**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
sudo -u postgres psql -c "\\l"

# Check database credentials in settings
cat config/production_settings.py
```

### **Performance Optimization**
```bash
# Increase Gunicorn workers (edit gunicorn_config.py)
workers = multiprocessing.cpu_count() * 2 + 1

# Enable Nginx gzip compression (already configured)
# Monitor resource usage
htop
df -h
free -h
```

## 🔄 Updates & Maintenance

### **Application Updates**
```bash
# Pull latest code
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements-prod.txt

# Run migrations
DJANGO_SETTINGS_MODULE=config.production_settings python manage.py migrate

# Collect static files
DJANGO_SETTINGS_MODULE=config.production_settings python manage.py collectstatic --noinput

# Restart application
sudo supervisorctl restart recharge_backend
```

### **System Updates**
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Restart services if needed
sudo systemctl restart nginx
sudo supervisorctl restart recharge_backend
```

## 📞 Support

If you encounter any issues during deployment:

1. **Check the logs** first (locations listed above)
2. **Verify all services** are running
3. **Test configuration files** for syntax errors
4. **Review firewall rules** if experiencing connectivity issues
5. **Check DNS settings** for domain-related problems

For additional support, refer to the main project documentation or create an issue in the repository.

---

**🎉 Congratulations! Your Recharge Backend is now deployed and ready for production use!**