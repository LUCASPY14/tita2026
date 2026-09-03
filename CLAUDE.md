# Cantina Tita 2026 — Guía de desarrollo

## Stack

| Capa | Tecnología |
|------|-----------|
| Base de datos | PostgreSQL 16 (contenedor Docker, volumen `postgres_data`) |
| Backend | Python 3.11 · Django 5.2 LTS (soporte hasta abril 2028) · DRF 3.17 · Daphne ASGI |
| Cola de tareas | Celery 5.6 + Redis 7 (broker y cache) |
| WebSockets | Django Channels 4.2 |
| Frontend | React 19 · TypeScript 6 · Vite 8 · Tailwind CSS 4 |
| Estado | Zustand 5 |
| PWA | `vite-plugin-pwa` + service worker custom (`frontend/public/sw.js`) |
| CI/CD | GitHub Actions (`.github/workflows/ci.yml`) |
| Contenedores | Docker Compose — PostgreSQL corre **dentro** del compose |
| Monitoring | Prometheus + Grafana (`:9090`, `:3000`) |
| Errores | Sentry (backend + frontend) |

## Setup de desarrollo

### PostgreSQL (Docker)
```
# PostgreSQL 16 corre en el contenedor 'postgres' del compose.
# Datos persistidos en volumen Docker 'postgres_data'.
# Puerto 5432 expuesto en 127.0.0.1 (para pytest local y herramientas de DB).
#
# Migración inicial desde nativo (una sola vez):
#   pg_dump -U app_cantina cantina_tita > cantina_backup.sql
#   docker compose up -d postgres
#   docker compose exec -T postgres psql -U app_cantina cantina_tita < cantina_backup.sql
#   Stop-Service postgresql-x64-16 ; Set-Service postgresql-x64-16 -StartupType Disabled
```

### Backend
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Configuración
copy .env.example .env    # completar DB_PASSWORD, SECRET_KEY, etc.

# Migraciones y datos iniciales
python manage.py migrate
python manage.py seed_negocio      # datos base (cajas, medios de pago, etc.)
python manage.py seed_uat          # datos de prueba UAT

# Servidor de desarrollo (HTTP + WebSocket)
python manage.py runserver         # o daphne backend.asgi:application
```

### Redis (necesario para Channels y Celery)
```powershell
# Redis corre en WSL2 — arrancar con:
.\scripts\start_redis.ps1

# Workers Celery (en terminales separadas):
.\scripts\start_celery.ps1         # worker
# celery -A backend beat -l INFO   # scheduler de tareas periódicas
```

### Frontend
```powershell
cd frontend
npm install
npm run dev     # dev server en http://localhost:5173
```

### Con Docker (producción local)
```powershell
# Copiar y completar variables de producción:
copy backend\.env.production.example backend\.env.production

docker compose build
docker compose run --rm backend python manage.py migrate
docker compose up -d

# Verificar:
curl http://localhost/api/health/
```

## Comandos frecuentes

### Backend
```bash
# Tests con cobertura
pytest --cov=apps --cov-report=term-missing -q

# Tests de una sola app
pytest apps/ventas/tests/ -v

# Admin
python manage.py create_demo_users   # usuarios de demo
python manage.py limpiar_tokens      # tokens expirados
python manage.py limpiar_audit_logs  # audit logs viejos

# Particiones anuales de DB
python manage.py create_year_partition 2027
```

### Frontend
```bash
npm run dev          # desarrollo
npm run build        # build de producción
npm run test:run     # unit tests (una vez)
npm run coverage     # cobertura
npm run test:e2e     # Playwright E2E (requiere dev server corriendo)
npm run lint         # ESLint + TypeScript check
```

### Deploy a producción
```powershell
# Desde D:\tita2026\ como Administrador:
.\deploy.ps1

# Flags útiles:
.\deploy.ps1 -SkipBuild        # reusar imágenes existentes
.\deploy.ps1 -SkipMigrations   # hot-fix sin cambios de schema
```

### Backup de base de datos
```powershell
# Primera vez (registra tarea programada Windows 02:00):
# Las credenciales DB se leen de backend\.env.production en cada backup.
.\scripts\setup_backup_task.ps1
# Con cifrado GPG opcional:
.\scripts\setup_backup_task.ps1 -GpgRecipient "admin@cantinatita.com"

# Backup manual:
.\backup_cantina.ps1

# Restaurar:
.\restore_cantina.ps1 -BackupFile "C:\backups\cantina\cantina_20260616_0200.dump"
```

## Arquitectura de despliegue

```
LAN escolar (7 PCs)
├── 1 PC Admin      → http://localhost/  (gestión general)
├── 1 PC Comedor    → http://localhost/comedor  (registro almuerzos)
└── 5 PCs Cajeros   → http://localhost/modo-recreo  (POS, instalado como PWA)

Servidor (1 PC dedicado)
├── Cloudflare Tunnel   (servicio nativo Windows, cloudflared.exe)
├── Docker Desktop
│   ├── postgres        (PostgreSQL 16, volumen postgres_data)
│   ├── frontend        (Nginx + React SPA, puerto 80)
│   ├── backend         (Django + Daphne, puerto interno 8000)
│   ├── redis           (broker + cache, puerto interno 6379)
│   ├── celery          (worker)
│   ├── celery-beat     (scheduler)
│   ├── waha            (WhatsApp self-hosted, 127.0.0.1:3001)
│   ├── prometheus      (métricas, 127.0.0.1:9090)
│   └── grafana         (dashboards, 127.0.0.1:3000)
└── Backups             (D:\produccion_tita\backups\cantina\, tarea programada 02:00)
```

Portal de padres (`/portal/*`) accesible desde internet via Bancard para recargas.

## Aplicaciones Django (apps/)

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

| Rol | Acceso |
|-----|--------|
| `ADMIN` | Todo |
| `SUPERVISOR` | Gestión sin configuración |
| `CAJERO` | POS (ModoRecreo), carga de saldo — máx. **1 sesión** |
| `COBRADOR` | Cobros, reportes — máx. **1 sesión** |
| `COCINA` | Comedor, menú diario — máx. **1 sesión** |
| `CLIENTE_WEB` | Solo portal de padres (`/portal/*`) |

El límite de sesiones concurrentes se aplica automáticamente al hacer login
(`apps/usuarios/views.py:_registrar_sesion`).

## Tareas Celery periódicas (21 activas)

| Tarea | Cuándo | Crítica |
|-------|--------|---------|
| `expirar_recargas_pendientes` | Diario 02:00 | No |
| `crear_particion_anio_siguiente` | 1 dic 04:00 | No |
| `generar_alertas_saldo_bajo` | Diario 08:00 | No |
| `limpiar_notificaciones_antiguas` | Domingos 03:00 | No |
| `enviar_emails_pendientes` | Cada 15 min | No |
| `procesar_solicitudes_pendientes` | Cada 15 min | No |
| `alertar_stock_minimo` | Diario 07:00 | No |
| `generar_resumen_diario_stock` | Diario 23:55 | No |
| `generar_resumen_diario_ventas` | Diario 23:50 | No |
| `cerrar_cuentas_mes_anterior` | Día 1 de mes 05:00 | **Sí** |
| `generar_cuentas_mensuales` | Día 1 de mes 06:00 | **Sí** |
| `avisar_deuda_almuerzo` | Viernes 08:00 | No |
| `alertar_saldo_almuerzo_negativo` | Diario 09:45 | No |
| `limpiar_audit_logs` | Día 1 de mes 01:00 | No |
| `refrescar_mv_balance_cliente` | Cada 15 min | No |
| `alertar_ordenes_compra_pendientes` | Diario 09:30 | No |
| `alertar_compras_pendientes_pago` | Diario 10:00 | No |
| `sincronizar_costos_desde_compras` | Diario 01:30 | No |
| `alertar_saldo_negativo_prolongado` | Diario 09:15 | No |
| `resumen_mensual_deuda_clientes` | Día 5 de mes 08:30 | No |
| `recordar_facturacion_mensual_pendiente` | Día 5 de mes 08:45 | No |

Las tareas críticas envían email a `ADMINS` si fallan (configurado en `celery_app.py`). `generar_resumen_diario_ventas` y `generar_resumen_diario_stock` solo escriben logs y tienen `autoretry_for=(Exception,)` — no están en `_CRITICAL_TASKS`.

> `cerrar_cajas_automatico` está desactivada en el beat (`celery_app.py:104`); el cierre de caja es manual.

## Convenciones importantes

### API
- Todas las rutas bajo `/api/v1/`
- Autenticación: JWT Bearer token (`Authorization: Bearer <access>`)
- El portal de padres usa el mismo JWT pero con rol `CLIENTE_WEB`
- Paginación: `{ results, count, next, previous }` en todos los listados

### Frontend
- Rutas del portal: `/portal/*` — layout separado (`PortalLayout.tsx`)
- Rutas del sistema interno: todo lo demás bajo `AppLayout.tsx`
- `ModoRecreo` es el único componente fuera del `AppLayout` (full-screen POS)
- Service Worker activo solo en producción (`injectRegister: null` en vite.config.ts)
- i18n en `src/i18n/es.json` — agregar toda cadena nueva aquí

### Tests
- Backend: cobertura mínima 95% forzada por CI (`--cov-fail-under=95`)
- E2E Playwright: usar patrón LIFO para mocks — registrar catch-all primero, específicos después
- Tests backend: usar `Model.objects.create()` con datos explícitos; no usar fixtures de Django para datos complejos
- Tests que dependan de fechas: usar `freezegun` (`@freeze_time`) con una fecha fija; nunca `date.today()` sin freeze

### Base de datos
- Tablas de alto volumen (`movimientos`, `ventas`) usan particionamiento por año
- PostgreSQL corre en Docker (contenedor `postgres`, volumen `postgres_data`) — backup via `docker exec pg_dump`
- No usar `datetime.now()` en modelos — siempre `django.utils.timezone.now()` (aware)

## Variables de entorno

Hay dos archivos de entorno:
- `backend/.env.production` — variables del backend Django (secretos, DB, Redis, Bancard, etc.)
- `D:\tita2026\.env` — variables para docker-compose (build args + `DB_PASSWORD`, `GRAFANA_PASSWORD`, `WAHA_API_KEY`)

Ver `backend/.env.production.example` para la lista completa con descripción.
Variables mínimas para desarrollo: `SECRET_KEY`, `DB_*`.
Variables para portal de padres con Bancard: `BANCARD_*`, `PORTAL_FRONTEND_URL`.

### Notas de configuración Docker
- `ALLOWED_HOSTS` debe incluir `backend` (nombre del servicio) para que Prometheus scrapee `/metrics`
- `REDIS_URL=redis://redis:6379/1` — DB 1 para Django/Celery; DB 0 libre
- `WAHA_API_KEY` debe estar en `.env` raíz Y en `backend/.env.production` como `EVOLUTION_API_KEY`
- Puertos de monitoring solo en `127.0.0.1` (prometheus:9090, grafana:3000, waha:3001)
