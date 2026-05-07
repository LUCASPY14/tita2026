# 🐳 Configuración Docker - Cantina TITA

Este documento complementa la [Guía de Docker](../DOCKER_SETUP.md) con detalles técnicos de la arquitectura.

## 📦 Servicios

### 1. **SQL Server** (`db`)
- **Imagen**: `mcr.microsoft.com/mssql/server:2025-latest`
- **Puerto**: 1433
- **Credenciales**: `sa` / ver `.env.docker`
- **Volumen**: `mssql_data` (persistente)
- **Health Check**: TCP port 1433 cada 5s

### 2. **Django Backend** (`backend`)
- **Build**: `docker/backend/Dockerfile`
- **Puerto**: 8000
- **Desarrollo**: `python manage.py runserver`
- **Producción**: Gunicorn 4 workers, timeout 120s
- **Volúmenes**:
  - Código: `./backend:/app` (bind mount)
  - Static: `static_files` (volumen compartido)
  - Media: `media_files` (volumen compartido)

### 3. **Frontend React** (`frontend`)
- **Build**: `docker/frontend/Dockerfile`
- **Puerto**: 3000
- **Desarrollo**: `npm run dev` (Vite HMR)
- **Producción**: Build estático servido por Nginx

### 4. **Nginx** (`nginx`)
- **Imagen**: `nginx:alpine`
- **Puerto**: 80
- **Configuración**: `docker/nginx/nginx.conf`
- **Función**: Reverse proxy, servir archivos estáticos

## 🗂️ Estructura de Archivos

```
tita2026/
├── docker/
│   ├── backend/
│   │   ├── Dockerfile              # Imagen backend (desarrollo)
│   │   ├── Dockerfile.prod         # Multi-stage producción
│   │   └── entrypoint.prod.sh      # Script de inicio producción
│   ├── frontend/
│   │   ├── Dockerfile              # Imagen frontend (desarrollo)
│   │   ├── Dockerfile.prod         # Multi-stage producción
│   │   ├── entrypoint.prod.sh      # Script de inicio producción
│   │   ├── default.prod.conf       # Config Nginx SPA + caché API
│   │   ├── nginx.prod.conf         # Config Nginx global
│   │   └── security-headers.conf   # CSP, HSTS, X-Frame-Options
│   ├── nginx/
│   │   ├── nginx.conf              # Config global desarrollo
│   │   └── default.conf            # Config del sitio desarrollo
│   └── docker-compose.yml          # Orquestación interna
├── docker-compose.yml              # Orquestación principal
├── docker-compose.prod.yml         # Orquestación producción
├── .env.docker.example             # Plantilla de variables de entorno
├── start-docker.ps1                # Script de inicio rápido (Windows)
└── stop-docker.ps1                 # Script de detención (Windows)
```

## 🔄 Flujo de Datos

```
Cliente (Browser/App)
    ↓
Nginx:80 (Reverse Proxy)
    ↓
├── Backend:8000 (Django + Gunicorn)
│       ↓
│   SQL Server:1433 (Datos persistentes)
└── Frontend:3000 (React — solo en desarrollo)
```

## 🌐 Red Docker

- **Nombre**: `cantina-network`
- **Driver**: `bridge`
- **Aislamiento**: Los contenedores se comunican por nombres de servicio

## 💾 Volúmenes Persistentes

| Volumen | Contenido | Persistencia |
|---------|-----------|--------------|
| `mssql_data` | Base de datos SQL Server | ✅ Sobrevive a `docker-compose down` |
| `static_files` | CSS, JS, imágenes estáticas | ✅ Sobrevive a `docker-compose down` |
| `media_files` | Uploads de usuarios | ✅ Sobrevive a `docker-compose down` |

**Nota**: Se eliminan con `docker-compose down -v`

## ⚙️ Variables de Entorno

### Django Settings
- `DJANGO_SETTINGS_MODULE`: `backend.settings.docker`
- `DEBUG`: `True` (desarrollo) / `False` (producción)
- `SECRET_KEY`: Clave secreta de Django
- `ALLOWED_HOSTS`: Hosts permitidos (separados por coma)

### Database (SQL Server)
- `DB_ENGINE`: `mssql`
- `DB_NAME`: Nombre de la base de datos (`titadb`)
- `DB_USER`: Usuario de SQL Server (`sa` en desarrollo)
- `DB_PASSWORD`: Contraseña de SQL Server
- `DB_HOST`: Hostname del servicio (`db`)
- `DB_PORT`: Puerto de SQL Server (`1433`)

## 🔒 Seguridad

### Desarrollo
- ✅ ALLOWED_HOSTS con wildcard (`*`)
- ✅ DEBUG activado
- ✅ CORS permisivo
- ✅ HTTP sin SSL

### Producción (Recomendaciones)
- ⚠️ Cambiar `SECRET_KEY`
- ⚠️ Cambiar contraseña `MSSQL_SA_PASSWORD`
- ⚠️ `DEBUG=False`
- ⚠️ ALLOWED_HOSTS específico
- ⚠️ Configurar HTTPS con certificados
- ⚠️ Configurar CORS restrictivo
- ⚠️ Usar usuario no-root en contenedores
- ⚠️ Limitar recursos de CPU/memoria

## 📊 Monitoreo

### Health Checks

| Servicio | Check | Intervalo | Timeout |
|----------|-------|-----------|---------|
| `db` | TCP 1433 (`echo > /dev/tcp/localhost/1433`) | 5s | 5s |
| `backend` | `/health/` HTTP 200 | 30s | 10s |

### Logs

```powershell
# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f backend

# Ver últimas 100 líneas
docker-compose logs --tail=100 backend

# Guardar logs a archivo
docker-compose logs > logs.txt
```

## 🚀 Despliegue en Producción

### Opción 1: Docker Compose (Servidor único)

1. Copiar archivos al servidor
2. Configurar variables de entorno en `.env.docker`
3. Ejecutar `docker-compose -f docker-compose.prod.yml up -d`
4. Configurar reverse proxy (Nginx) para HTTPS
5. Configurar backups automáticos con `scripts/sql/setup_sql_backups.sql`

### Opción 2: Kubernetes (Escalable)

1. Convertir `docker-compose.yml` a manifiestos K8s
2. Usar Helm charts para gestión
3. Configurar Ingress para HTTPS
4. Implementar HorizontalPodAutoscaler
5. Configurar PersistentVolumeClaims

### Opción 3: Cloud Providers

- **Azure**: Container Instances + Azure SQL + Azure Container Registry
- **AWS**: ECS + RDS SQL Server + ECR
- **GCP**: Cloud Run + Cloud SQL (SQL Server edition)

## 🔧 Optimizaciones

### Backend
- Aumentar workers de Gunicorn: `--workers 8`
- Usar `--worker-class gevent` para más concurrencia
- Configurar connection pooling con `django-mssql-backend`

### Database (SQL Server)
- Configurar `max server memory` según RAM disponible
- Usar índices columnstore para consultas de reportes
- Habilitar Query Store para monitoreo de rendimiento
- Configurar backups automáticos (FULL diario, LOG cada 15 min)

### Nginx
- Caché de archivos estáticos habilitado (`default.prod.conf`)
- Gzip compresión habilitada (`nginx.prod.conf`)
- Rate limiting configurado: API 10r/s, login 1r/s
- HTTP/2 habilitado en producción

## 📚 Referencias

- [Docker Compose File Reference](https://docs.docker.com/compose/compose-file/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)
- [Gunicorn Settings](https://docs.gunicorn.org/en/stable/settings.html)
- [SQL Server en Docker](https://hub.docker.com/_/microsoft-mssql-server)
- [Nginx Docker](https://hub.docker.com/_/nginx)
