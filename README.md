# Cantina Tita 2026

Sistema de gestión para cantina escolar: POS de recreo (modo cajero), comedor con suscripciones de almuerzo, portal de padres con recargas vía Bancard, y backoffice administrativo.

## Stack

| Capa | Tecnología |
|------|-----------|
| Base de datos | PostgreSQL 16 (contenedor Docker, volumen `postgres_data`) |
| Backend | Python 3.11 · Django 5.2 LTS (soporte hasta abril 2028) · DRF 3.17 · Daphne ASGI |
| Cola de tareas | Celery 5.6 + Redis 7 (broker y cache, en WSL2) |
| WebSockets | Django Channels 4.2 |
| Frontend | React 19 · TypeScript 6 · Vite 8 · Tailwind CSS 4 |
| Estado | Zustand 5 |
| PWA | `vite-plugin-pwa` + service worker custom (`frontend/public/sw.js`) |
| CI/CD | GitHub Actions (`.github/workflows/ci.yml`) |
| Contenedores | Docker Compose — PostgreSQL corre **dentro** del compose |
| Monitoring | Prometheus (`:9090`) + Grafana (`:3000`) |
| Errores | Sentry (backend + frontend) |

## Setup de desarrollo

### 1. PostgreSQL (Docker)

```powershell
# PostgreSQL 16 corre en el contenedor 'postgres' del compose.
# Datos persistidos en el volumen Docker 'postgres_data'.
# Puerto 5432 expuesto en 127.0.0.1 (para pytest local y herramientas de DB).
docker compose up -d postgres
```

### 2. Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Variables de entorno
copy .env.example .env   # completar SECRET_KEY, DB_PASSWORD

# Migraciones y datos base
python manage.py migrate
python manage.py seed_negocio    # cajas, medios de pago, listas de precio, etc.
python manage.py seed_uat        # datos de prueba UAT (opcional)

# Servidor de desarrollo (HTTP + WebSocket)
python manage.py runserver
# o con Daphne (ASGI completo):
# daphne backend.asgi:application
```

### 3. Redis + Celery (necesario para WebSockets y tareas en background)

```powershell
# Redis corre en WSL2:
.\scripts\start_redis.ps1

# Worker de tareas (terminal separada):
.\scripts\start_celery.ps1

# Scheduler de tareas periódicas (terminal separada):
celery -A backend beat -l INFO
```

### 4. Frontend

```powershell
cd frontend
npm install
npm run dev    # dev server en http://localhost:5173
```

## Comandos frecuentes

### Backend

```bash
# Tests con cobertura (mínimo 95%, forzado por CI)
pytest --cov=apps --cov-report=term-missing -q

# Tests de una app específica
pytest apps/ventas/tests/ -v

# Usuarios de demo
python manage.py create_demo_users

# Limpieza manual
python manage.py limpiar_tokens          # tokens JWT expirados
python manage.py limpiar_audit_logs      # audit logs > 365 días (también Celery día 1/mes)

# Particiones anuales de DB (ya automatizado vía Celery el 1 de diciembre)
python manage.py create_year_partition 2027
```

### Frontend

```bash
npm run dev          # servidor de desarrollo
npm run build        # build de producción
npm run test:run     # unit tests (Vitest, una pasada)
npm run coverage     # cobertura de tests
npm run test:e2e     # Playwright E2E (requiere dev server corriendo)
npm run lint         # ESLint + TypeScript check
```

## Arquitectura de despliegue

```
LAN escolar (7 PCs)
├── 1 PC Admin      → http://servidor/           (gestión general, backoffice)
├── 1 PC Comedor    → http://servidor/comedor     (registro de almuerzos)
└── 5 PCs Cajeros   → http://servidor/modo-recreo (POS instalado como PWA)

Servidor (1 PC dedicado)
├── Cloudflare Tunnel   (servicio nativo Windows, cloudflared.exe)
├── Docker Desktop
│   ├── postgres        (PostgreSQL 16, volumen postgres_data)
│   ├── frontend        (Nginx + React SPA, puerto 80)
│   ├── backend         (Django + Daphne, puerto interno 8000)
│   ├── redis           (broker + cache, puerto interno 6379)
│   ├── celery          (worker)
│   ├── celery-beat     (scheduler de tareas periódicas)
│   ├── waha            (WhatsApp self-hosted, 127.0.0.1:3001)
│   ├── prometheus      (métricas, 127.0.0.1:9090)
│   └── grafana         (dashboards, 127.0.0.1:3000)
└── Backups             (D:\produccion_tita\backups\cantina\, tarea programada 02:00)
```

El portal de padres (`/portal/*`) es accesible desde internet para recargas vía Bancard vPOS.

## Deploy a producción

```powershell
# Desde D:\tita2026\ como Administrador:
.\deploy.ps1

# Flags útiles:
.\deploy.ps1 -SkipBuild        # reusar imágenes Docker existentes
.\deploy.ps1 -SkipMigrations   # hot-fix sin cambios de schema
```

El script realiza en orden: `docker compose build` → migraciones → `docker compose up -d` → health check.

## Backup de base de datos

```powershell
# Registrar tarea programada Windows (02:00 diario) — solo la primera vez.
# Las credenciales DB se leen de backend\.env.production en cada backup.
.\scripts\setup_backup_task.ps1
# Con cifrado GPG opcional:
.\scripts\setup_backup_task.ps1 -GpgRecipient "admin@cantinatita.com"

# Backup manual:
.\backup_cantina.ps1

# Restaurar:
.\restore_cantina.ps1 -BackupFile "C:\backups\cantina\cantina_20260616_0200.dump"
```

Los backups rotan automáticamente (30 días por defecto). El script también sube a la nube si `rclone` está configurado (ver `scripts/backup_nube.ps1`).

## Aplicaciones Django

| App | Responsabilidad |
|-----|----------------|
| `usuarios` | Auth custom (email), roles RBAC, 2FA TOTP, sesiones, auditoría |
| `clientes` | Padres, hijos, grados, cuentas corrientes |
| `core` | Tarjetas RFID, saldo, movimientos, medios de pago, Bancard vPOS |
| `productos` | Catálogo, categorías, precios por lista, impuestos |
| `ventas` | Ventas POS, notas de crédito, condiciones |
| `almuerzos` | Planes, suscripciones, menú diario, cuentas mensuales, alérgenos |
| `compras` | Proveedores, órdenes de compra, cuentas corrientes |
| `inventario` | Stock, movimientos, alertas, lotes, vencimientos |
| `contabilidad` | Caja, cierre de caja, conciliación, facturas |
| `notificaciones` | Push (WebSocket), email, plantillas |

## Roles de usuario

| Rol | Acceso | Sesiones máx. |
|-----|--------|--------------|
| `ADMIN` | Todo | ilimitadas |
| `SUPERVISOR` | Gestión sin configuración | ilimitadas |
| `CAJERO` | POS ModoRecreo, carga de saldo | 1 |
| `COBRADOR` | Cobros, reportes | 1 |
| `COCINA` | Comedor, menú diario | 1 |
| `CLIENTE_WEB` | Solo portal de padres (`/portal/*`) | ilimitadas |

## API

- Base URL: `/api/v1/`
- Autenticación: JWT Bearer (`Authorization: Bearer <access>`)
- Paginación: `{ count, results, next, previous }` en todos los listados
- Documentación interactiva: `/api/docs/` (Swagger UI, disponible en desarrollo)

## Variables de entorno

Hay dos archivos de entorno:

- `backend/.env.production` — variables del backend Django (secretos, DB, Redis, Bancard, etc.)
- `D:\tita2026\.env` — variables para docker-compose (build args + `DB_PASSWORD`, `GRAFANA_PASSWORD`, `WAHA_API_KEY`)

Ver `backend/.env.production.example` para la lista completa con descripción.

Variables mínimas para desarrollo:

```env
SECRET_KEY=django-insecure-...
DB_NAME=cantina_tita
DB_USER=postgres
DB_PASSWORD=...
DB_HOST=localhost
DB_PORT=5432
```

Variables adicionales para el portal de padres (Bancard):

```env
BANCARD_PUBLIC_KEY=...
BANCARD_PRIVATE_KEY=...
BANCARD_BASE_URL=https://vpos.infonet.com.py
PORTAL_FRONTEND_URL=https://cantina.edu.py
```
