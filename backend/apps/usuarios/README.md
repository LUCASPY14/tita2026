# Módulo Usuarios

## Descripción general

El módulo **Usuarios** es el sistema de autenticación y autorización central de Cantina Tita. Provee:

- Autenticación por **email + contraseña** con JWT (SimpleJWT)
- **RBAC** con 6 roles predefinidos
- **2FA TOTP** implementado sin dependencias externas (RFC 6238)
- **Límite de sesiones concurrentes** por rol
- **Auditoría** completa de operaciones y cambios
- Portal web de padres (`CLIENTE_WEB`) con endpoints propios

---

## Modelos (8 modelos principales)

| Modelo | Tabla DB | Propósito |
|--------|----------|-----------|
| `Usuario` | `usuarios` | Cuenta de autenticación unificada (AbstractBaseUser) |
| `Empleado` | `empleados` | Datos de personal — solo legado; autenticación en `Usuario` |
| `Rol` | `roles` | Roles legacy del sistema (compatibilidad) |
| `PerfilUsuario` | `perfiles_usuario` | Preferencias: tema, idioma, notificaciones, dashboard |
| `Autenticacion2FA` | `autenticacion_2fa` | Secreto TOTP + backup codes (8 códigos de emergencia) |
| `SesionActiva` | `sesiones_activas` | Sesiones activas con IP, user-agent y última actividad |
| `IntentoLogin` | `intentos_login` | Log de intentos (exitosos y fallidos) con IP |
| `BloqueoCuenta` | `bloqueos_cuenta` | Bloqueos manuales o automáticos con motivo y responsable |

### Modelos de auditoría

| Modelo | Tabla | Registra |
|--------|-------|---------|
| `AuditoriaEmpleado` | `auditoria_empleados` | Cambios campo a campo en datos de personal |
| `AuditoriaOperacion` | `auditoria_operaciones` | Operaciones del sistema con datos antes/después |
| `AuditoriaUsuarioWeb` | `auditoria_usuarios_web` | Cambios en usuarios del portal |

---

## Roles y accesos

```
ADMIN        → Acceso total al sistema, incluyendo configuración
SUPERVISOR   → Gestión operativa sin acceso a configuración del sistema
CAJERO       → POS (ModoRecreo), carga de saldo — máx. 1 sesión concurrente
COBRADOR     → Cobros, reportes — máx. 1 sesión concurrente
COCINA       → Módulo Comedor, menú diario — máx. 1 sesión concurrente
CLIENTE_WEB  → Solo portal de padres (/portal/*), acceso via Bancard
```

### Restricción de sesiones concurrentes

Los roles `CAJERO`, `COBRADOR` y `COCINA` solo pueden tener **1 sesión activa** al mismo tiempo. Al hacer login, si ya existe una sesión activa para ese usuario, el sistema la cierra antes de crear la nueva. La lógica está en `views.py:_registrar_sesion`.

### Escalada de privilegios bloqueada

`Usuario.save()` valida que `is_superuser=True` solo sea compatible con `rol=ADMIN`. Cualquier intento de elevar privilegios sin el rol correcto levanta `ValueError`.

---

## Autenticación — Flujo JWT

```
POST /api/token/                   → { access, refresh } + datos del usuario en el payload
POST /api/token/refresh/           → { access }  (dado refresh válido)
POST /api/token/verify/            → 200 si el token es válido
POST /api/v1/usuarios/logout/      → Invalida el refresh token en blacklist
```

El `CustomTokenObtainPairView` extiende SimpleJWT para incluir en el payload:
- `rol`, `nombre`, `apellido`, `email`, `requiere_2fa`

Si el usuario tiene 2FA habilitado, la respuesta JWT incluye `requiere_2fa: true` y el frontend debe solicitar el código TOTP antes de aceptar el token como válido (flujo en dos pasos con `/api/v1/usuarios/2fa/login/`).

---

## 2FA TOTP (RFC 6238)

El TOTP está implementado sin dependencias externas en `views.py`. Usa SHA-1, paso de 30 segundos y tolerancia de ±1 ventana.

### Flujo de configuración

```
GET  /api/v1/usuarios/2fa/estado/       → { habilitado: bool, backup_codes: [...] }
POST /api/v1/usuarios/2fa/configurar/   → Genera secret, devuelve QR URI para el autenticador
POST /api/v1/usuarios/2fa/activar/      → Confirma con primer código válido; habilita 2FA
POST /api/v1/usuarios/2fa/desactivar/   → Deshabilita 2FA (requiere código actual)
POST /api/v1/usuarios/2fa/verificar/    → Verifica un código en sesión activa
POST /api/v1/usuarios/2fa/login/        → Segundo paso del login con código TOTP
```

Los **backup codes** son 8 códigos de 6 caracteres hex (ej: `A3F912`). Se generan al activar 2FA y se consumen de a uno. Si se agotan, el admin debe desactivar y reactivar 2FA.

---

## Recuperación de contraseña

```
POST /api/v1/usuarios/recuperar-password/          → Envía email con token (TTL 24h)
POST /api/v1/usuarios/recuperar-password/confirmar/ → { token, nueva_password }
```

El token usa el `default_token_generator` de Django (hash derivado del estado del usuario, no se persiste en DB). Es válido una sola vez: cambia en cuanto el usuario actualiza su contraseña.

---

## Endpoints de gestión (requieren rol ADMIN)

```
GET/POST   /api/v1/usuarios/usuarios/            → Listar / crear usuarios
GET/PATCH  /api/v1/usuarios/usuarios/{id}/       → Detalle / editar
POST       /api/v1/usuarios/usuarios/{id}/desactivar/   → Baja lógica (is_active=False)

GET/POST   /api/v1/usuarios/empleados/           → Datos de personal
GET/POST   /api/v1/usuarios/roles/               → Puestos de trabajo (catálogo de Empleado.id_rol)

GET/POST   /api/v1/usuarios/perfiles/            → Preferencias de usuario
```

---

## Endpoints del portal de padres (CLIENTE_WEB)

```
GET  /api/v1/usuarios/portal/mi-hijo/               → Datos del hijo y saldo actual
GET  /api/v1/usuarios/portal/historial-consumos/    → Consumos en recreo (paginado)
GET  /api/v1/usuarios/portal/historial-cantina/     → Historial de movimientos
GET  /api/v1/usuarios/portal/mis-facturas/          → Facturas emitidas
```

Todos requieren `rol=CLIENTE_WEB`. El usuario `CLIENTE_WEB` tiene un `OneToOneField` con `clientes.Cliente`, lo que conecta la cuenta del portal con la familia en el sistema interno.

---

## Middleware de sesión

`middleware.py` intercepta cada request autenticado para actualizar `SesionActiva.ultima_actividad`. Sesiones sin actividad por más del tiempo configurado (`SESSION_TIMEOUT_MINUTES`, default 480 min) se marcan como inactivas automáticamente.

---

## Management commands

```bash
python manage.py create_demo_users    # Crea usuarios demo con credenciales predefinidas
python manage.py limpiar_tokens       # Elimina tokens de recuperación expirados o usados
python manage.py limpiar_audit_logs   # Elimina registros de auditoría mayores a N días
```

---

## Seguridad

| Mecanismo | Implementación |
|-----------|---------------|
| Contraseñas | bcrypt via Django (PBKDF2_SHA256 por defecto) |
| JWT | SimpleJWT con blacklist para logout |
| Rate limiting | `LoginRateThrottle` en `/api/token/` (5 intentos/minuto) |
| 2FA | TOTP RFC 6238, sin dependencias externas |
| Intentos login | Registrados en `IntentoLogin` con IP y motivo de fallo |
| Bloqueo | Manual via `BloqueoCuenta` o automático tras N fallos (configurable) |
| Sesiones | Rastradas en `SesionActiva`; límite por rol (CAJERO/COBRADOR/COCINA: 1) |
| is_superuser | Solo compatible con rol ADMIN (validado en `save()`) |

---

## Variables de entorno relevantes

```
SECRET_KEY                 # Firma de JWT y cookies
SIMPLE_JWT_ACCESS_LIFETIME # Duración del access token (default: 1h)
SIMPLE_JWT_REFRESH_LIFETIME # Duración del refresh token (default: 7d)
SESSION_TIMEOUT_MINUTES    # Inactividad antes de cerrar sesión (default: 480)
```

---

## Dependencias entre apps

- `clientes` — `Usuario.cliente` OneToOne para portal de padres
- `notificaciones` — Envío de email en recuperación de contraseña
- `core` — `PagoBancard.cliente` requiere que el usuario tenga cliente asociado
