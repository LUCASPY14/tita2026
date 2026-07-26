# Runbook de Operación — Cantina Tita

**Para:** Encargado de administración o técnico de guardia  
**Última revisión:** Junio 2026

---

## 1. Reiniciar servicios (arranque normal)

```powershell
# Desde D:\tita2026\ como Administrador

# 1. Verificar que PostgreSQL esté activo
Get-Service -Name "postgresql-x64-*" | Select-Object Name, Status

# 2. Iniciar Redis (se ejecuta en WSL2)
.\scripts\start_redis.ps1

# 3. Levantar todos los contenedores Docker
docker compose up -d

# 4. Verificar que todo está OK
curl http://localhost/api/health/
# Esperado: {"status": "ok", "checks": {"db": "ok", "redis": "ok", "celery": "..."}}
```

Si algún servicio individual falla:

```powershell
# Reiniciar solo el backend
docker compose restart backend

# Ver logs del backend en vivo
docker compose logs -f backend

# Reiniciar todos los contenedores
docker compose restart
```

---

## 2. Si Bancard no funciona (pagos rechazados en el portal)

El sistema tiene un **circuit breaker** que se activa si Bancard falla 5 veces seguidas.  
Mientras el circuit breaker está abierto, los padres ven:  
*"La integración de pagos no está disponible temporalmente"*

### Paso 1 — Verificar si es un problema de Bancard o nuestro

```powershell
# Ver los últimos errores del backend
docker compose logs --tail=50 backend | Select-String "bancard"
```

- Si ves `CircuitBreaker: abierto` o `BancardTimeout` → es transitorio, esperar **60 segundos** y el circuit breaker se recupera solo.
- Si ves `BANCARD_PUBLIC_KEY no configurado` → es un problema de configuración (ver paso 2).
- Si Bancard está caído (http 502/503 desde su lado) → avisar a los padres que reintenten en 30 minutos.

### Paso 2 — Si el circuit breaker no se recupera

```powershell
# Reiniciar el backend (limpia el estado en memoria del circuit breaker)
docker compose restart backend

# Verificar la configuración de claves Bancard en el .env
Select-String "BANCARD" backend\.env.production
```

Las variables que deben estar configuradas:
- `BANCARD_PUBLIC_KEY` — clave pública de Bancard (no vacía)
- `BANCARD_PRIVATE_KEY` — clave privada de Bancard (no vacía)
- `BANCARD_SANDBOX` — debe ser `False` en producción
- `BANCARD_RETURN_URL` — URL accesible desde internet

### Paso 3 — Si los pagos siguen fallando

Contactar a Bancard: **+595 21 xxx xxxx** o soporte@bancard.com.py  
Pedir el `shop_process_id` del pago fallido (visible en los logs) para el reporte.

---

## 3. Si el sistema está caído (pantalla en blanco en los cajeros)

```powershell
# 1. Verificar estado de contenedores
docker compose ps

# 2. Si están caídos, revisar logs
docker compose logs --tail=100 backend
docker compose logs --tail=100 frontend

# 3. Reiniciar todo
docker compose down
.\scripts\start_redis.ps1
docker compose up -d

# 4. Esperar 30 segundos y verificar
Start-Sleep 30
curl http://localhost/api/health/ready/
```

Si PostgreSQL no responde:

```powershell
# Verificar servicio de base de datos
Get-Service -Name "postgresql-x64-*"

# Reiniciar el servicio (requiere permisos de administrador)
Restart-Service -Name "postgresql-x64-16"
```

---

## 4. Restaurar backup de base de datos

> **Atención:** Este procedimiento reemplaza TODOS los datos actuales con los del backup.  
> Confirmar con la dirección antes de continuar.

```powershell
# Ver backups disponibles
Get-ChildItem C:\backups\cantina\ | Sort-Object LastWriteTime -Descending | Select-Object -First 5

# Restaurar el backup más reciente (reemplazar la fecha)
.\restore_cantina.ps1 -BackupFile "C:\backups\cantina\cantina_20260622_0200.dump"

# Reiniciar servicios después de la restauración
docker compose restart backend celery
```

El backup automático corre cada día a las **02:00** via Windows Task Scheduler.  
Los archivos se guardan en `C:\backups\cantina\` con formato `cantina_YYYYMMDD_HHMM.dump`.

---

## 5. Backup manual (antes de una actualización)

```powershell
# Crear backup ahora mismo
.\backup_cantina.ps1

# Verificar que se creó
Get-ChildItem C:\backups\cantina\ | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

---

## 6. Actualizar el sistema (deploy)

```powershell
# Desde D:\tita2026\ como Administrador
.\deploy.ps1

# Si hay cambios urgentes sin modificar la base de datos:
.\deploy.ps1 -SkipMigrations
```

El deploy tarda entre 2 y 5 minutos. Durante ese tiempo el sistema puede mostrar  
errores temporales a los usuarios.

---

## 7. Ver cuántos cajeros están conectados

```powershell
# Logs de sesiones activas (últimas 20 líneas)
docker compose logs --tail=20 backend | Select-String "SesionActiva|login"
```

O desde el panel de administración:  
`http://localhost/admin/` → Usuarios → Sesiones activas

---

## 8. Si un cajero no puede iniciar sesión

1. Verificar que el usuario existe en `http://localhost/admin/` → Usuarios
2. Verificar que `is_active = True`
3. Si el cajero ya tenía una sesión abierta en otra PC, el sistema la cierra automáticamente al reiniciar sesión — es comportamiento esperado
4. Si olvidó su contraseña, resetearla desde el admin: Usuarios → Cambiar contraseña

---

## 9. PWA en PCs cajeros — instalación y mantenimiento

> Los 5 PCs cajeros usan **ModoRecreo** instalado como PWA (Progressive Web App) en Chrome.
> La PWA funciona sin conexión: las ventas se guardan en IndexedDB y se sincronizan al reconectar.

### 9.1 Instalación inicial (hacer en cada PC cajero)

**Prerrequisitos:**
- Chrome 90 o superior instalado
- PC conectada a la LAN de la cantina (puede hacer ping al servidor)
- El servidor (`docker compose up -d`) debe estar corriendo

**Pasos:**

```powershell
# Desde el servidor, ejecutar este script en cada PC cajero
# (o copiarlo a la PC cajero y ejecutarlo localmente)
.\scripts\install-pwa-cajero.ps1
```

El script verifica los prerrequisitos y abre Chrome guiando la instalación.
Si el servidor no es `localhost` (la PC cajero accede por IP):

```powershell
.\scripts\install-pwa-cajero.ps1 -ServidorUrl http://192.168.1.100
```

**Instalación manual** (si el script no está disponible):
1. Abrir Chrome → `http://localhost/modo-recreo`
2. Esperar que cargue; buscar el ícono de instalación (□↑) en la barra de direcciones
3. Clic en ese ícono → **Instalar**
4. La app abre como ventana independiente
5. Anclar el ícono "Cantina" a la Barra de tareas

### 9.2 Verificar que la PWA está correctamente instalada

```powershell
.\scripts\install-pwa-cajero.ps1 -SoloValidar
```

Verifica: Chrome versión, health del servidor, SW accesible, manifest válido, íconos OK.

### 9.3 Configurar inicio automático con Windows

Para que la PWA arranque sola cuando el PC cajero enciende:

```powershell
# Primero instalar la PWA (9.1), luego ejecutar:
.\scripts\install-pwa-cajero.ps1 -ConfigurarInicio
```

El script copia el acceso directo de Chrome App a la carpeta de Inicio de Windows (`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`).

### 9.4 Actualizar la PWA después de un deploy

El Service Worker se actualiza automáticamente: Chrome verifica `sw.js` en cada navegación.
Si un cajero no recibe la actualización:

```powershell
# En Chrome de la PC cajero, abrir la consola (F12) y ejecutar:
# navigator.serviceWorker.getRegistration().then(r => r.update())
# O directamente: ir a chrome://serviceworker-internals/ → Unregister → recargar
```

Forma más rápida en el PC cajero:
1. Abrir la PWA
2. Menú de Chrome (⋮) → `Más herramientas` → `Herramientas para desarrolladores`
3. Pestaña **Application** → **Service Workers** → clic en **Update**
4. Recargar la app

### 9.5 Reinstalar la PWA (si hay problemas)

```powershell
# 1. Desinstalar la PWA actual desde Chrome:
#    chrome://apps/ → clic derecho en "Cantina" → "Desinstalar"
# 2. Limpiar el Service Worker:
#    chrome://serviceworker-internals/ → Unregister del sw.js de localhost
# 3. Limpiar caché y datos del sitio:
#    chrome://settings/siteData → buscar "localhost" → Eliminar
# 4. Reinstalar:
.\scripts\install-pwa-cajero.ps1
```

### 9.6 Comportamiento offline del ModoRecreo

| Situación | Comportamiento |
|-----------|---------------|
| Sin conexión al servidor | El cajero ve el banner "Sin conexión — ventas se guardan offline" |
| Ventas realizadas offline | Se encolan en IndexedDB del browser |
| Al reconectar | Las ventas pendientes se sincronizan automáticamente (BackgroundSync) |
| Catálogo de productos | Disponible offline (StaleWhileRevalidate) |
| Consulta de saldo de tarjeta | Muestra último saldo cacheado si no hay red |

Si las ventas offline no se sincronizan al reconectar, forzar sync manualmente:
1. Abrir la PWA → F12 → Application → Background Sync
2. Clic en **Push** en la fila `sync-ventas`

### 9.7 Checklist de 5 PCs cajeros

| PC | Ubicación | Chrome ≥90 | PWA instalada | Inicio automático | Verificado |
|----|-----------|:----------:|:-------------:|:-----------------:|:----------:|
| Cajero 1 | Puesto 1 | ☐ | ☐ | ☐ | ☐ |
| Cajero 2 | Puesto 2 | ☐ | ☐ | ☐ | ☐ |
| Cajero 3 | Puesto 3 | ☐ | ☐ | ☐ | ☐ |
| Cajero 4 | Puesto 4 | ☐ | ☐ | ☐ | ☐ |
| Cajero 5 | Puesto 5 | ☐ | ☐ | ☐ | ☐ |

---

## Contactos de emergencia

| Situación | Contacto |
|-----------|----------|
| Sistema caído, no se puede resolver | Administrador del sistema |
| Problema de pagos Bancard | Soporte Bancard |
| Base de datos corrupta | DBA / Proveedor de hosting |

---

## Verificación rápida de estado

```powershell
# Un solo comando para ver todo:
docker compose ps ; curl http://localhost/api/health/
```

---

## Hoja de ruta de infraestructura — v2.0

### PostgreSQL nativo → contenedor (recomendado para v2.0)

PostgreSQL corre actualmente como servicio nativo en Windows. Las limitaciones son:
- Las actualizaciones de Windows Update pueden interrumpir el servicio sin aviso
- No hay aislamiento de recursos (RAM/CPU compartida con el OS)
- La migración de versión mayor es manual

**Camino de migración recomendado:**
1. Activar WAL archiving primero (`scripts/setup_wal_archiving.ps1`)
2. Agregar a `docker-compose.yml`:
   ```yaml
   postgres:
     image: postgres:15
     volumes:
       - postgres_data:/var/lib/postgresql/data
     environment:
       POSTGRES_DB: cantina_tita
       POSTGRES_USER: app_cantina
       POSTGRES_PASSWORD: ${DB_PASSWORD}
     ports:
       - "5432:5432"
   ```
3. Migrar los datos con `pg_dump` / `pg_restore`
4. Actualizar `DB_HOST` en `.env.production` de `host.docker.internal` a `postgres`
5. Eliminar la dependencia `extra_hosts: host.docker.internal` de backend/celery

No realizar este cambio en pleno año lectivo. Planificar para vacaciones de julio o enero.
