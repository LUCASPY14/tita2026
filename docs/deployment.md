# Deployment Guide

## Despliegue en Producción

### Requisitos Previos

- Servidor Linux (Ubuntu 20.04+)
- Python 3.11+
- Node.js 18+
- SQL Server 2025
- Nginx
- Domain name (opcional)

### 1. Preparar el Servidor

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y python3-pip python3-venv nginx git curl gnupg2 unixodbc-dev
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt update
sudo ACCEPT_EULA=Y apt install -y msodbcsql18 mssql-tools18

# Instalar Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2. Configurar SQL Server

```bash
# Crear base de datos titadb
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'secure_password_here' -Q "IF DB_ID('titadb') IS NULL CREATE DATABASE [titadb]" -C
```

### 3. Clonar y Configurar Backend

```bash
# Clonar repositorio
cd /var/www
sudo git clone <repository_url> cantina_tita
cd cantina_tita/backend

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
pip install gunicorn

# Configurar variables de entorno
sudo nano .env
```

Agregar en `.env`:
```
DEBUG=False
SECRET_KEY=generate_a_secure_secret_key_here
DB_ENGINE=mssql
DB_NAME=titadb
DB_USER=sa
DB_PASSWORD=secure_password_here
DB_HOST=localhost
DB_PORT=1433
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

```bash
# Ejecutar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Recolectar archivos estáticos
python manage.py collectstatic --no-input
```

### 4. Configurar Gunicorn

```bash
# Crear archivo de servicio
sudo nano /etc/systemd/system/gunicorn.service
```

Contenido:
```ini
[Unit]
Description=gunicorn daemon for cantina_tita
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/cantina_tita/backend
Environment="PATH=/var/www/cantina_tita/backend/venv/bin"
ExecStart=/var/www/cantina_tita/backend/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/var/www/cantina_tita/backend/gunicorn.sock \
          backend.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Iniciar y habilitar servicio
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

### 5. Configurar Frontend

```bash
cd /var/www/cantina_tita/frontend

# Instalar dependencias
npm install

# Configurar variables de entorno
nano .env.production
```

Contenido de `.env.production`:
```
VITE_API_URL=https://yourdomain.com/api/v1
VITE_APP_NAME=Cantina Tita
```

```bash
# Build para producción
npm run build
```

### 6. Configurar Nginx

```bash
sudo nano /etc/nginx/sites-available/cantina_tita
```

Contenido:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Frontend
    location / {
        root /var/www/cantina_tita/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        include proxy_params;
        proxy_pass http://unix:/var/www/cantina_tita/backend/gunicorn.sock;
    }

    # Django Admin
    location /admin/ {
        include proxy_params;
        proxy_pass http://unix:/var/www/cantina_tita/backend/gunicorn.sock;
    }

    # Static files
    location /static/ {
        alias /var/www/cantina_tita/backend/static/;
    }

    # Media files
    location /media/ {
        alias /var/www/cantina_tita/backend/media/;
    }

    # Seguridad
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    client_max_body_size 10M;
}
```

```bash
# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/cantina_tita /etc/nginx/sites-enabled/

# Verificar configuración
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

### 7. Configurar SSL (Opcional pero Recomendado)

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Verificar renovación automática
sudo certbot renew --dry-run
```

## Despliegue con Docker

### Usando Docker Compose

```bash
# Clonar repositorio
git clone <repository_url> cantina_tita
cd cantina_tita

# Configurar variables de entorno
cp .env.example .env
nano .env

# Iniciar servicios
docker-compose -f docker/docker-compose.yml up -d

# Ejecutar migraciones
docker-compose exec backend python manage.py migrate

# Crear superusuario
docker-compose exec backend python manage.py createsuperuser

# Ver logs
docker-compose logs -f
```

## Mantenimiento

### Actualizar Aplicación

```bash
cd /var/www/cantina_tita

# Backend
git pull origin main
cd backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --no-input
sudo systemctl restart gunicorn

# Frontend
cd ../frontend
npm install
npm run build
```

### Backup Automático

Agregar a crontab:
```bash
# Editar crontab
crontab -e

# Backup diario a las 2 AM
0 2 * * * /var/www/cantina_tita/backend/venv/bin/python /var/www/cantina_tita/backend/scripts/backup_db.py
```

### Monitoreo de Logs

```bash
# Logs de Gunicorn
sudo journalctl -u gunicorn -f

# Logs de Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Troubleshooting

### Error 502 Bad Gateway
```bash
# Verificar Gunicorn
sudo systemctl status gunicorn
sudo systemctl restart gunicorn

# Verificar socket
ls -la /var/www/cantina_tita/backend/gunicorn.sock
```

### Error de permisos
```bash
sudo chown -R www-data:www-data /var/www/cantina_tita
sudo chmod -R 755 /var/www/cantina_tita
```

### Base de datos no responde
```bash
sudo systemctl status mssql-server
sudo systemctl restart mssql-server
```

## Seguridad Adicional

### Firewall (UFW)

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### Fail2Ban

```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Actualizaciones de Seguridad

```bash
# Configurar actualizaciones automáticas
sudo apt install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```
