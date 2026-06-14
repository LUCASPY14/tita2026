# Cantina Tita — Guía de Despliegue v1

Guía paso a paso para poner en producción el sistema en el servidor HP Mini con Windows 11.

## Requisitos previos

| Componente | Versión mínima | Notas |
|---|---|---|
| Docker Desktop (Windows) | 4.30+ | Con WSL2 backend activado |
| PostgreSQL | 15+ | Instalado nativo en Windows |
| Python | 3.11+ | Solo para tareas de administración fuera de Docker |
| Git | 2.40+ | Para clonar y desplegar |

---

## 1. Clonar el repositorio

```powershell
git clone https://github.com/tu-org/cantina-tita.git D:\tita2026
cd D:\tita2026
```

---

## 2. Configurar variables de entorno

### 2.1 Copiar la plantilla

```powershell
Copy-Item .env.example backend\.env.production
```

### 2.2 Editar `backend\.env.production`

Abrir el archivo y completar **todos** los valores marcados:

```ini
# ── Django ────────────────────────────────────────────────────────────────────
SECRET_KEY=<generar con: python -c "import secrets; print(secrets.token_urlsafe(50))">
DEBUG=False
ALLOWED_HOSTS=192.168.1.100,localhost          # IP del servidor en la LAN

# ── Base de datos (PostgreSQL nativo en Windows) ──────────────────────────────
DB_NAME=cantina_tita
DB_USER=cantina_user
DB_PASSWORD=<contraseña segura>
DB_HOST=host.docker.internal                   # Docker → PostgreSQL Windows
DB_PORT=5432

# ── Redis (contenedor Docker) ─────────────────────────────────────────────────
REDIS_URL=redis://redis:6379/1
USE_REDIS_CACHE=True
USE_REDIS_CHANNELS=True

# ── Celery ────────────────────────────────────────────────────────────────────
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# ── Email SMTP ────────────────────────────────────────────────────────────────
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=cantina@ejemplo.com
EMAIL_HOST_PASSWORD=<contraseña de aplicación Gmail>
DEFAULT_FROM_EMAIL=Cantina Tita <cantina@ejemplo.com>

# ── Admins (alertas de tareas críticas) ──────────────────────────────────────
ADMINS=Admin:admin@ejemplo.com

# ── CORS (orígenes permitidos para el frontend) ───────────────────────────────
CORS_ALLOWED_ORIGINS=http://192.168.1.100
CSRF_TRUSTED_ORIGINS=http://192.168.1.100

# ── Grafana ───────────────────────────────────────────────────────────────────
GRAFANA_PASSWORD=<contraseña segura>

# ── Sentry (opcional pero recomendado) ────────────────────────────────────────
SENTRY_DSN=https://xxxx@oxxxxxx.ingest.sentry.io/yyyyyyy
SENTRY_ENVIRONMENT=production
SENTRY_RELEASE=                                # se puede dejar vacío; usar GIT_COMMIT_SHA
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.05

# ── Portal de padres ──────────────────────────────────────────────────────────
PORTAL_FRONTEND_URL=http://192.168.1.100
```

> **Seguridad**: el archivo `.env.production` contiene secretos. Nunca lo commitees. Está en `.gitignore`.

---

## 3. Crear la base de datos PostgreSQL

En Windows, abrir **psql** como administrador y ejecutar:

```sql
CREATE USER cantina_user WITH PASSWORD 'contraseña_segura';
CREATE DATABASE cantina_tita OWNER cantina_user;
GRANT ALL PRIVILEGES ON DATABASE cantina_tita TO cantina_user;
```

Permitir conexiones desde Docker en `pg_hba.conf` (normalmente en `C:\Program Files\PostgreSQL\15\data\pg_hba.conf`):

```
host    cantina_tita    cantina_user    172.17.0.0/16    scram-sha-256
```

Reiniciar PostgreSQL después del cambio:

```powershell
Restart-Service postgresql-x64-15
```

---

## 4. Build de imágenes Docker

```powershell
cd D:\tita2026
docker compose build --no-cache
```

El build tarda ~3-5 minutos la primera vez. Las siguientes veces usa caché.

---

## 5. Migraciones de base de datos

```powershell
docker compose run --rm backend python manage.py migrate
```

Verificar que todas las migraciones se apliquen sin errores. Si alguna falla, revisar la conexión a PostgreSQL:

```powershell
docker compose run --rm backend python manage.py dbshell
```

---

## 6. Crear superusuario administrador

```powershell
docker compose run --rm backend python manage.py createsuperuser
```

Ingresar: nombre de usuario, email y contraseña cuando se solicite.

---

## 7. Configurar particionado de tablas históricas (primera vez)

Las tablas `core_movimientotarjeta` y `usuarios_auditoriaoperacion` usan particionado por año en PostgreSQL. El script debe ejecutarse **una sola vez** al hacer el primer deploy.

```powershell
# Desde Windows, conectarse a PostgreSQL y ejecutar el script SQL:
& "C:\Program Files\PostgreSQL\15\bin\psql.exe" -U cantina_user -d cantina_tita -f D:\tita2026\scripts\setup_partitions.sql
```

Una vez particionadas, crear las particiones del año actual y siguiente:

```powershell
docker compose run --rm backend python manage.py create_year_partition --year 2026
docker compose run --rm backend python manage.py create_year_partition --year 2027
```

> **Automatización**: Celery Beat crea automáticamente la partición del año siguiente cada 1 de diciembre a las 04:00. Si el deploy ocurre en otro momento y falta algún año, crear la partición manualmente con el comando anterior.

Para verificar que las particiones existen:

```sql
SELECT tablename FROM pg_tables
WHERE tablename LIKE 'core_movimientotarjeta_%'
   OR tablename LIKE 'usuarios_auditoriaoperacion_%'
ORDER BY tablename;
```

---

## 8. Cargar datos iniciales (seed)

```powershell
# Datos del negocio: categorías, configuración, tipos de tarjeta, etc.
docker compose run --rm backend python manage.py seed_negocio

# (Opcional) Datos de ejemplo para desarrollo/staging:
# docker compose run --rm backend python manage.py seed_demo
```

El comando `seed_negocio` es idempotente — se puede correr más de una vez sin duplicar datos.

---

## 9. Recolectar archivos estáticos

```powershell
docker compose run --rm backend python manage.py collectstatic --noinput
```

Los archivos se copian a `staticfiles/` y el contenedor `frontend` (Nginx) los sirve.

---

## 10. Levantar todos los servicios

```powershell
docker compose up -d
```

Verificar que todos los contenedores estén `healthy`:

```powershell
docker compose ps
```

Salida esperada:

```
NAME                STATUS
tita2026-frontend-1     Up (healthy)
tita2026-backend-1      Up (healthy)
tita2026-redis-1        Up
tita2026-celery-1       Up
tita2026-celery-beat-1  Up
tita2026-prometheus-1   Up
tita2026-grafana-1      Up
```

---

## 11. Verificar el despliegue

### Healthcheck de la API

```powershell
Invoke-WebRequest http://localhost/api/health/ | Select-Object StatusCode, Content
```

Respuesta esperada: `{"status": "ok", "database": "ok", "redis": "ok"}`

### Admin Django

Abrir `http://192.168.1.100/admin/` en el navegador. Login con el superusuario creado en paso 6.

### Panel de monitoreo

| Servicio | URL | Credenciales |
|---|---|---|
| Grafana | `http://192.168.1.100:3000` | admin / (GRAFANA_PASSWORD del .env) |
| Prometheus | `http://192.168.1.100:9090` | sin autenticación |
| API docs | `http://192.168.1.100/api/docs/` | sin autenticación |

---

## 12. Configurar inicio automático con Windows

Para que Docker Compose arranque solo cuando se reinicie el servidor:

1. Verificar que Docker Desktop esté configurado para iniciar con Windows (Settings → General → "Start Docker Desktop when you sign in")
2. Crear una tarea programada para `docker compose up -d`:

```powershell
$action = New-ScheduledTaskAction -Execute "docker" -Argument "compose -f D:\tita2026\docker-compose.yml up -d" -WorkingDirectory "D:\tita2026"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
Register-ScheduledTask -TaskName "CantinaDockerCompose" -Action $action -Trigger $trigger -Principal $principal
```

---

## 13. Acceso desde las PCs cajeras (LAN)

Las 5 PCs cajeras (ModoRecreo) acceden via navegador Chrome:

```
http://192.168.1.100/
```

Reemplazar `192.168.1.100` por la IP real del servidor HP Mini en la LAN local.

> Para saber la IP del servidor: `ipconfig` en el servidor → buscar la tarjeta de red LAN.

---

## Operaciones habituales

### Ver logs en tiempo real

```powershell
# Todos los servicios
docker compose logs -f

# Solo backend
docker compose logs -f backend

# Solo Celery worker
docker compose logs -f celery
```

### Aplicar migraciones nuevas tras un deploy

```powershell
git pull
docker compose build backend celery celery-beat
docker compose run --rm backend python manage.py migrate
docker compose up -d
```

### Reiniciar un servicio

```powershell
docker compose restart backend
docker compose restart celery
```

### Verificar tareas Celery

```powershell
# Estado del worker
docker compose exec celery celery -A backend inspect active

# Tareas programadas (Beat)
docker compose exec celery-beat celery -A backend inspect scheduled
```

### Backup de la base de datos

```powershell
$fecha = Get-Date -Format "yyyyMMdd_HHmm"
& "C:\Program Files\PostgreSQL\15\bin\pg_dump.exe" -U cantina_user -Fc cantina_tita > "D:\backups\cantina_$fecha.dump"
```

Restaurar:

```powershell
& "C:\Program Files\PostgreSQL\15\bin\pg_restore.exe" -U cantina_user -d cantina_tita "D:\backups\cantina_20260610_0800.dump"
```

---

## Solución de problemas frecuentes

### Backend no puede conectarse a PostgreSQL

```powershell
# Verificar que PostgreSQL escucha en 0.0.0.0 o en la IP del host
# En postgresql.conf:
#   listen_addresses = '*'
# En pg_hba.conf agregar la línea del paso 3.
# Reiniciar el servicio de PostgreSQL.
```

### Celery worker no procesa tareas

```powershell
docker compose logs celery
# Verificar que REDIS_URL apunte al contenedor 'redis', no a localhost.
# Verificar que DJANGO_SETTINGS_MODULE=backend.settings.production
```

### Sentry no recibe eventos

Verificar que `SENTRY_DSN` esté configurado en `.env.production` y que el servidor tenga acceso a Internet (`sentry.io`). Forzar un evento de prueba:

```powershell
docker compose exec backend python -c "import sentry_sdk; sentry_sdk.capture_message('test desde produccion')"
```

### Grafana no muestra datos

1. Verificar que Prometheus esté corriendo: `http://192.168.1.100:9090/targets`
2. Todos los targets deben aparecer en estado `UP`
3. Si el target `backend` aparece `DOWN`, verificar que el backend exponga `/metrics` (requiere `django-prometheus` instalado)
