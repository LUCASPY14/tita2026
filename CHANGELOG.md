# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).
El versionado sigue [Semantic Versioning](https://semver.org/lang/es/).

---

## [1.0.0] — 2026-07-15

Primera versión estable del sistema de gestión de Cantina Tita.

### POS — ModoRecreo
- Punto de venta full-screen para 5 PCs cajeros, instalable como PWA
- Cobro con tarjeta RFID prepago, efectivo y tarjeta de crédito/débito (Bancard vPOS)
- Listas de precios diferenciadas (alumnos, docentes, funcionarios)
- Soporte de tarjetas para docentes y funcionarios
- Cola offline: las ventas se encolan cuando no hay red y se sincronizan al reconectarse
- Sesión única forzada por cajero (máx. 1 sesión concurrente)

### Módulo de almuerzos — Comedor
- Planes de almuerzo, suscripciones por alumno y menú diario configurable
- Registro de consumo en comedor con identificación por RFID
- Cuentas mensuales por alumno con cierre y cobro automático vía Celery
- Pago de cuota mensual desde el portal de padres con Bancard
- Gestión de alérgenos y restricciones alimentarias por alumno

### Portal de padres
- Accesible desde internet; instalable como PWA en Android
- Recarga de saldo prepago con tarjeta de crédito/débito (Bancard)
- Historial de consumos, saldo actual y movimientos de la cuenta
- Pago de cuentas de almuerzo mensuales
- Descarga de facturas y comprobantes
- Notificaciones push en el navegador

### Módulo de compras
- Registro de compras a proveedores con detalle de productos y precios
- Cuentas corrientes de proveedores con aplicación de pagos y notas de crédito
- Órdenes de compra con seguimiento de estado y recepción
- Carga rápida de productos por código de barras
- Sincronización automática de costos hacia el módulo de inventario (Celery)
- Alertas automáticas de órdenes pendientes y pagos vencidos

### Módulo de inventario
- Control de stock con movimientos de entrada/salida
- Lotes con fechas de vencimiento y alertas automáticas
- Ajustes de inventario con motivo y auditoría
- Resumen diario de stock generado automáticamente a las 23:55

### Módulo de contabilidad
- Cajas por cajero con apertura, movimientos y cierre manual o automático
- Conciliación de pagos con Bancard
- Generación de facturas y gestión de datos de empresa
- Cierre automático de cajas por Celery si no se cierra manualmente

### Notificaciones
- Push en tiempo real por WebSocket (Django Channels + Redis)
- Email transaccional vía Resend (anymail)
- WhatsApp via WAHA (self-hosted) con fallback automático a email
- Preferencias de notificación por usuario
- Plantillas de email configurables desde el admin

### Seguridad y usuarios
- Autenticación custom con email, RBAC con 6 roles (ADMIN, SUPERVISOR, CAJERO, COBRADOR, COCINA, CLIENTE_WEB)
- 2FA TOTP configurable por usuario
- Límite de sesiones concurrentes por rol (1 sesión para cajeros, cobradores y cocina)
- Rate limiting en Nginx y en la API (throttling por tipo de endpoint)
- Auditoría completa de operaciones e intentos de login en `/auditoria`
- Bloqueo automático de cuenta tras intentos fallidos de login
- Tokens JWT con rotación y blacklist

### Infraestructura y operaciones
- Stack: Django 5.2 LTS + Daphne ASGI + Celery 5.6 + Redis 7 + PostgreSQL 15
- Frontend: React 19 + TypeScript 6 + Vite 8 + Tailwind CSS 4
- 9 servicios Docker Compose (frontend, backend, redis, celery, celery-beat, prometheus, pushgateway, grafana, waha)
- 20 tareas Celery periódicas con alertas por email en las 4 críticas
- Particionamiento de tablas de alto volumen (`movimientos`, `ventas`) por año
- Backup automático cifrado con GPG a las 02:00 via Task Scheduler de Windows
- Soporte para subir backups cifrados a almacenamiento en la nube
- WAL archiving de PostgreSQL configurado
- Ambiente de staging en el mismo servidor (puerto 8080)
- Scripts de setup: PostgreSQL, firewall Windows, TLS self-signed para LAN, rotación de secrets
- Deploy automatizado con `deploy.ps1` (7 pasos, health checks, rollback)

### Monitoring y observabilidad
- Prometheus + Grafana con dashboard de negocio preconfigurado (`cantina.json`)
- Alertas configuradas en `cantina_alerts.yaml`
- Sentry integrado en backend (Django + Celery) y frontend (React)
- Métricas de Celery enviadas al PushGateway en cada ejecución
- Load tests k6 en CI los lunes (job `k6.yml`)

### CI/CD
- GitHub Actions: tests backend (pytest, cobertura ≥ 80%), tests frontend (vitest), E2E Playwright en Chromium y Firefox, build de producción
- Cobertura subida a Codecov en cada push
- Load tests k6 programados semanalmente
- Cobertura total backend: **88.2%** · 1.302 tests

---

## [Unreleased]

### En progreso
- Tests de `almuerzos/tasks.py` (cobertura actual 55% → objetivo 80%)
- Tests de `compras/views.py` (cobertura actual 66% → objetivo 80%)
- Tests de `notificaciones/consumers.py` (cobertura actual 67% → objetivo 80%)

### Planeado
- UI de configuración de WhatsApp en Configuración (tab TabWhatsApp)
- Reportes descargables Excel/PDF: balance de clientes, cierre mensual almuerzos, resumen de compras
- `scripts/smoke-test.ps1` para validación post-deploy
- Load tests k6 realistas para el pico del recreo (5 cajeros × 20 min)
- Validación de PWA en los 5 PCs cajeros en hardware real

[1.0.0]: https://github.com/cantina-tita/tita2026/releases/tag/v1.0.0
[Unreleased]: https://github.com/cantina-tita/tita2026/compare/v1.0.0...HEAD
