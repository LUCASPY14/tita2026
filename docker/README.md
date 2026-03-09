# 🐳 Configuración Docker - Cantina TITA

Este documento complementa la [Guía de Docker](../DOCKER_SETUP.md) con detalles técnicos de la arquitectura.

## 📦 Servicios

### 1. **PostgreSQL** (`db`)
- **Imagen**: `postgres:15-alpine`
- **Puerto**: 5432
- **Credenciales**: Ver `.env.docker`
- **Volumen**: `postgres_data` (persistente)
- **Health Check**: Verifica conexión cada 10s

### 2. **Redis** (`redis`)
- **Imagen**: `redis:7-alpine`
- **Puerto**: 6379
- **Password**: Configurado en `.env.docker`
- **Uso**: Cache, sesiones, Celery broker
- **Volumen**: `redis_data` (persistente)

### 3. **Django Backend** (`backend`)
- **Build**: `docker/backend/Dockerfile`
- **Puerto**: 8000
- **Workers Gunicorn**: 4
- **Timeout**: 120s
- **Volúmenes**:
  - Código: `./backend:/app` (bind mount)
  - Static: `static_files` (volumen compartido)
  - Media: `media_files` (volumen compartido)

### 4. **Celery Worker** (`celery_worker`)
- **Base**: Mismo Dockerfile que backend
- **Concurrency**: 2 workers
- **Uso**: Tareas asíncronas (emails, reportes, cálculos)

### 5. **Celery Beat** (`celery_beat`)
- **Base**: Mismo Dockerfile que backend
- **Scheduler**: Django Celery Beat (DB-backed)
- **Uso**: Tareas programadas (cierres diarios, alertas)

### 6. **Nginx** (`nginx`)
- **Imagen**: `nginx:alpine`
- **Puerto**: 80 (HTTP), 443 (HTTPS)
- **Configuración**: `docker/nginx/default.conf`
- **Función**: Reverse proxy, servir archivos estáticos

## 🗂️ Estructura de Archivos

```
cantina_tita/
├── docker/
│   ├── backend/
│   │   ├── Dockerfile              # Imagen backend
│   │   ├── Dockerfile.prod         # Producción
│   │   └── entrypoint.prod.sh      # Script de inicio
│   ├── nginx/
│   │   ├── nginx.conf              # Config global
│   │   └── default.conf            # Config del sitio
│   ├── postgres/
│   │   └── init.sql                # Script de inicialización
│   └── docker-compose.yml          # Orquestación (legacy)
├── docker-compose.yml              # Orquestación principal
├── .env.docker                     # Variables de entorno
├── .env.docker.example             # Plantilla de ejemplo
├── DOCKER_SETUP.md                 # Guía de usuario
├── start-docker.ps1                # Script de inicio rápido
└── stop-docker.ps1                 # Script de detención
```

## 🔄 Flujo de Datos

```
Cliente (Browser/App)
    ↓
Nginx:80 (Reverse Proxy)
    ↓
Backend:8000 (Django + Gunicorn)
    ↓
├── PostgreSQL:5432 (Datos persistentes)
├── Redis:6379 (Cache + Sesiones)
└── Celery (Workers + Beat)
```

## 🌐 Red Docker

- **Nombre**: `cantina-network`
- **Driver**: `bridge`
- **Subnet**: `172.25.0.0/16`
- **Aislamiento**: Los contenedores se comunican por nombres de servicio

## 💾 Volúmenes Persistentes

| Volumen | Contenido | Persistencia |
|---------|-----------|--------------|
| `postgres_data` | Base de datos | ✅ Sobrevive a `docker-compose down` |
| `redis_data` | Cache y datos Redis | ✅ Sobrevive a `docker-compose down` |
| `static_files` | CSS, JS, imágenes estáticas | ✅ Sobrevive a `docker-compose down` |
| `media_files` | Uploads de usuarios | ✅ Sobrevive a `docker-compose down` |

**Nota**: Se eliminan con `docker-compose down -v`

## ⚙️ Variables de Entorno

### Django Settings
- `DJANGO_SETTINGS_MODULE`: `backend.settings.docker`
- `DEBUG`: `True` (desarrollo) / `False` (producción)
- `SECRET_KEY`: Clave secreta de Django
- `ALLOWED_HOSTS`: Hosts permitidos (separados por coma)

### Database
- `DB_ENGINE`: Motor de base de datos
- `DB_NAME`: Nombre de la base de datos
- `DB_USER`: Usuario de PostgreSQL
- `DB_PASSWORD`: Contraseña de PostgreSQL
- `DB_HOST`: Hostname del servicio (`db`)
- `DB_PORT`: Puerto de PostgreSQL (`5432`)

### Redis
- `REDIS_HOST`: Hostname del servicio (`redis`)
- `REDIS_PORT`: Puerto de Redis (`6379`)
- `REDIS_PASSWORD`: Contraseña de Redis

### Celery
- `CELERY_BROKER_URL`: URL completa del broker
- `CELERY_RESULT_BACKEND`: URL del backend de resultados

## 🔒 Seguridad

### Desarrollo
- ✅ ALLOWED_HOSTS con wildcard (`*`)
- ✅ DEBUG activado
- ✅ CORS permisivo
- ✅ HTTP sin SSL

### Producción (Recomendaciones)
- ⚠️ Cambiar `SECRET_KEY`
- ⚠️ Cambiar contraseñas de DB y Redis
- ⚠️ `DEBUG=False`
- ⚠️ ALLOWED_HOSTS específico
- ⚠️ Configurar HTTPS con certificados
- ⚠️ Configurar CORS restrictivo
- ⚠️ Usar usuario no-root en contenedores
- ⚠️ Limitar recursos de CPU/memoria
- ⚠️ Configurar secrets con Docker Secrets o Kubernetes

## 📊 Monitoreo

### Health Checks

| Servicio | Endpoint | Intervalo | Timeout |
|----------|----------|-----------|---------|
| `db` | `pg_isready` | 10s | 5s |
| `redis` | `redis-cli ping` | 10s | 3s |
| `backend` | `/health/` | 30s | 10s |

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
3. Ejecutar `docker-compose -f docker-compose.yml up -d`
4. Configurar reverse proxy (Nginx/Caddy) para HTTPS
5. Configurar backups automáticos

### Opción 2: Kubernetes (Escalable)

1. Convertir `docker-compose.yml` a manifiestos K8s
2. Usar Helm charts para gestión
3. Configurar Ingress para HTTPS
4. Implementar HorizontalPodAutoscaler
5. Configurar PersistentVolumeClaims

### Opción 3: Cloud Providers

- **AWS**: ECS + RDS + ElastiCache
- **Azure**: Container Instances + PostgreSQL + Redis Cache
- **GCP**: Cloud Run + Cloud SQL + Memorystore

## 🔧 Optimizaciones

### Backend
- Aumentar workers de Gunicorn: `--workers 8`
- Usar `--worker-class gevent` para más concurrencia
- Configurar connection pooling

### Database
- Configurar `max_connections` en PostgreSQL
- Implementar read replicas
- Configurar índices optimizados

### Cache
- Aumentar memoria de Redis
- Configurar eviction policy: `allkeys-lru`
- Usar Redis Cluster para alta disponibilidad

### Nginx
- Configurar cache de archivos estáticos
- Habilitar gzip compression
- Configurar HTTP/2
- Implementar rate limiting

## 📚 Referencias

- [Docker Compose File Reference](https://docs.docker.com/compose/compose-file/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)
- [Gunicorn Settings](https://docs.gunicorn.org/en/stable/settings.html)
- [PostgreSQL Docker](https://hub.docker.com/_/postgres)
- [Redis Docker](https://hub.docker.com/_/redis)
- [Nginx Docker](https://hub.docker.com/_/nginx)
