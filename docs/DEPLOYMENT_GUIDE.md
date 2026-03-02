# 🚀 Guía de Deployment - Módulo de Usuarios

## 📋 Tabla de Contenidos
1. [Pre-requisitos](#pre-requisitos)
2. [Configuración de Producción](#configuración-de-producción)
3. [Deployment en Servidor](#deployment-en-servidor)
4. [Docker Deployment](#docker-deployment)
5. [Cron Jobs](#cron-jobs)
6. [Monitoreo y Logs](#monitoreo-y-logs)
7. [Backup y Recuperación](#backup-y-recuperación)
8. [Security Checklist](#security-checklist)

---

## 🔧 Pre-requisitos

### Requisitos del Sistema
- Python 3.10+
- PostgreSQL 13+ / MySQL 8+ / MariaDB 10.5+
- Nginx / Apache
- SSL/TLS Certificate
- RAM:  mínimo (4GB+ recomendado)
- Disco: 10GB disponible mínimo

### Dependencias Python
```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuración de Producción

### 1. Variables de Entorno (.env.production)

```bash
# Django Settings
SECRET_KEY=tu_secret_key_super_segura_de_50_caracteres_minimo
DEBUG=False
ALLOWED_HOSTS=cantinatita.com,www.cantinatita.com,api.cantinatita.com
CORS_ALLOWED_ORIGINS=https://cantinatita.com,https://www.cantinatita.com

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=dbcantinatita
DB_USER=cantina_user
DB_PASSWORD=password_muy_segura
DB_HOST=localhost
DB_PORT=5432

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@cantinatita.com
EMAIL_HOST_PASSWORD=app_password_de_gmail
DEFAULT_FROM_EMAIL=Cantina Tita <noreply@cantinatita.com>

# Frontend URL
FRONTEND_URL=https://cantinatita.com

# JWT Settings
ACCESS_TOKEN_LIFETIME_MINUTES=60
REFRESH_TOKEN_LIFETIME_DAYS=7

# Rate Limiting
RATELIMIT_ENABLE=True
```

### 2. Generar SECRET_KEY Segura

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Configuración de settings/production.py

```python
from .base import *
from decouple import config

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', cast=int),
        'OPTIONS': {
            'charset': 'utf8mb4',
        }
    }
}

# Security Settings
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Static and Media files
STATIC_ROOT = '/var/www/cantinatita/static/'
MEDIA_ROOT = '/var/www/cantinatita/media/'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/cantinatita/django.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/cantinatita/security.log',
            'maxBytes': 1024 * 1024 * 15,
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps.usuarios': {
            'handlers': ['file', 'security_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

---

## 🖥️ Deployment en Servidor (Ubuntu/Debian)

### 1. Actualizar Sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Instalar Dependencias

```bash
# Python y herramientas
sudo apt install python3.10 python3.10-venv python3-pip nginx supervisor -y

# Base de datos (PostgreSQL)
sudo apt install postgresql postgresql-contrib -y

# O para MySQL
sudo apt install mysql-server -y
```

### 3. Crear Usuario y Base de Datos

#### PostgreSQL:
```bash
sudo -u postgres psql

CREATE DATABASE dbcantinatita;
CREATE USER cantina_user WITH PASSWORD 'password_segura';
GRANT ALL PRIVILEGES ON DATABASE dbcantinatita TO cantina_user;
ALTER USER cantina_user CREATEDB;  # Para tests
\q
```

#### MySQL:
```bash
sudo mysql

CREATE DATABASE dbcantinatita CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'cantina_user'@'localhost' IDENTIFIED BY 'password_segura';
GRANT ALL PRIVILEGES ON dbcantinatita.* TO 'cantina_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 4. Clonar Proyecto y Configurar

```bash
# Crear directorio
sudo mkdir -p /var/www/cantinatita
sudo chown -R $USER:$USER /var/www/cantinatita

# Clonar proyecto
cd /var/www
git clone <repository_url> cantinatita
cd cantinatita/backend

# Crear entorno virtual
python3.10 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

### 5. Configurar Variables de Entorno

```bash
cp .env.example .env.production
nano .env.production
# Configurar todas las variables
```

### 6. Ejecutar Migraciones

```bash
export DJANGO_SETTINGS_MODULE=backend.settings.production
python manage.py migrate
python manage.py collectstatic --noinput
```

### 7. Inicializar Sistema

```bash
python manage.py init_usuarios
```

### 8. Configurar Gunicorn

Crear `/etc/supervisor/conf.d/cantinatita.conf`:

```ini
[program:cantinatita]
command=/var/www/cantinatita/backend/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:8000 backend.wsgi:application
directory=/var/www/cantinatita/backend
user=www-data
group=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/cantinatita/gunicorn.log
environment=DJANGO_SETTINGS_MODULE="backend.settings.production",LANG="en_US.UTF-8",LC_ALL="en_US.UTF-8"
```

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start cantinatita
```

### 9. Configurar Nginx

Crear `/etc/nginx/sites-available/cantinatita`:

```nginx
upstream cantinatita_backend {
    server 127.0.0.1:8000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name cantinatita.com www.cantinatita.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name cantinatita.com www.cantinatita.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/cantinatita.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cantinatita.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logging
    access_log /var/log/nginx/cantinatita_access.log;
    error_log /var/log/nginx/cantinatita_error.log;

    # Client body size
    client_max_body_size 10M;

    # Static files
    location /static/ {
        alias /var/www/cantinatita/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /var/www/cantinatita/media/;
        expires 7d;
    }

    # API
    location /api/ {
        proxy_pass http://cantinatita_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Admin
    location /admin/ {
        proxy_pass http://cantinatita_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Rate limiting for admin
        limit_req zone=admin_limit burst=5 nodelay;
    }
}

# Rate limiting zones
http {
    limit_req_zone $binary_remote_addr zone=admin_limit:10m rate=1r/s;
}
```

```bash
sudo ln -s /etc/nginx/sites-available/cantinatita /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 10. Instalar SSL con Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d cantinatita.com -d www.cantinatita.com
```

---

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=backend.settings.production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Create log directories
RUN mkdir -p /var/log/cantinatita

# Run gunicorn
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:8000", "backend.wsgi:application"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: dbcantinatita
      POSTGRES_USER: cantina_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  backend:
    build: ./backend
    command: gunicorn --workers 4 --bind 0.0.0.0:8000 backend.wsgi:application
    volumes:
      - ./backend:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env.production
    depends_on:
      - db
      - redis
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/var/www/static
      - media_volume:/var/www/media
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    restart: unless-stopped

  certbot:
    image: certbot/certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

### Deployment con Docker

```bash
# Build y levantar servicios
docker-compose up -d --build

# Ejecutar migraciones
docker-compose exec backend python manage.py migrate

# Crear superusuario
docker-compose exec backend python manage.py init_usuarios

# Ver logs
docker-compose logs -f backend
```

---

## ⏰ Cron Jobs

### Configurar Crontab

```bash
crontab -e
```

### Jobs Recomendados

```cron
# Limpieza de sesiones y tokens (diario a las 2:00 AM)
0 2 * * * cd /var/www/cantinatita/backend && /var/www/cantinatita/backend/venv/bin/python manage.py cleanup_usuarios >> /var/log/cantinatita/cleanup.log 2>&1

# Backup de base de datos (diario a las 3:00 AM)
0 3 * * * /usr/bin/pg_dump -U cantina_user dbcantinatita > /backups/db_$(date +\%Y\%m\%d_\%H\%M\%S).sql

# Rotación de logs (semanal, domingos a las 4:00 AM)
0 4 * * 0 find /var/log/cantinatita/ -name "*.log" -mtime +30 -delete

# Renovación de certificados SSL (mensual)
0 0 1 * * certbot renew --quiet
```

### Script de Backup Automatizado

Crear `/usr/local/bin/backup_cantinatita.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/backups/cantinatita"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="dbcantinatita"
DB_USER="cantina_user"

# Crear directorio de backup
mkdir -p $BACKUP_DIR

# Backup de base de datos
pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup de archivos media
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/cantinatita/media/

# Mantener solo los últimos 30 días
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +30 -delete

echo "Backup completado: $DATE"
```

```bash
chmod +x /usr/local/bin/backup_cantinatita.sh
```

---

## 📊 Monitoreo y Logs

### Estructura de Logs

```
/var/log/cantinatita/
├── django.log          # Logs generales de Django
├── security.log        # Logs de seguridad
├── gunicorn.log        # Logs de Gunicorn
├── email.log           # Logs de envío de emails
└── cleanup.log         # Logs de tareas de limpieza
```

### Monitoreo con Supervisor

```bash
# Ver status
sudo supervisorctl status

# Reiniciar aplicación
sudo supervisorctl restart cantinatita

# Ver logs en tiempo real
sudo supervisorctl tail -f cantinatita
```

### Monitoreo de Performance

Instalar y configurar herramientas:
- **Sentry** para error tracking
- **New Relic** para APM
- **Prometheus + Grafana** para métricas

---

## 🔒 Security Checklist

### Pre-Deployment

- [ ] `DEBUG = False` en producción
- [ ] `SECRET_KEY` única y segura (50+ caracteres)
- [ ] `ALLOWED_HOSTS` configurado correctamente
- [ ] `CORS_ALLOWED_ORIGINS` restringido
- [ ] SSL/TLS certificate instalado
- [ ] Todas las security headers configuradas
- [ ] Database passwords seguros
- [ ] `.env` en `.gitignore`
- [ ] Email credentials seguros (App Password)
- [ ] Rate limiting habilitado

### Post-Deployment

- [ ] Cambiar password del admin por defecto
- [ ] Habilitar 2FA para cuenta admin
- [ ] Revisar permisos de archivos/directorios
- [ ] Configurar firewall (UFW/iptables)
- [ ] Monitoreo de logs configurado
- [ ] Backup automatizado funcionando
- [ ] Tests de penetración básicos
- [ ] Revisar vulnerabilidades con `python manage.py check --deploy`

### Comandos de Verificación

```bash
# Check de deployment
python manage.py check --deploy

# Verificar configuración de seguridad
python manage.py check --tag security

# Auditoría de dependencias
pip-audit
```

---

## 🚨 Troubleshooting

### Error 502 Bad Gateway
```bash
# Verificar que Gunicorn está corriendo
sudo supervisorctl status

# Ver logs
sudo tail -f /var/log/cantinatita/gunicorn.log
```

### Error de permisos
```bash
# Ajustar permisos
sudo chown -R www-data:www-data /var/www/cantinatita
sudo chmod -R 755 /var/www/cantinatita
```

### Email no funciona
```bash
# Verificar configuración
python manage.py shell
from django.core.mail import send_mail
send_mail('Test', 'Test', 'from@example.com', ['to@example.com'])
```

---

## 📚 Recursos Adicionales

- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Best Practices](https://www.nginx.com/blog/nginx-best-practices/)
- [Let's Encrypt](https://letsencrypt.org/)

---

**✅ Una vez completado este checklist, tu aplicación estará lista para producción con seguridad de nivel empresarial.**
