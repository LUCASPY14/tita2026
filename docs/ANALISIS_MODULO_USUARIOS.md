# ANÁLISIS DEL MÓDULO USUARIOS - ESTADO ACTUAL

**Fecha de análisis:** 1 de marzo de 2026  
**Módulo:** `apps/usuarios`  
**Estado general:** 🔴 **IMPLEMENTACIÓN BÁSICA - FALTAN REGLAS DE NEGOCIO**

---

## 📊 RESUMEN EJECUTIVO

| Componente | Estado | Completitud | Observaciones |
|------------|--------|-------------|---------------|
| **Modelos** | ✅ Completo | 100% | 17 modelos definidos |
| **Serializers** | 🟡 Básico | 30% | Solo CRUD básico |
| **Views** | 🟡 Básico | 20% | Solo ViewSets CRUD |
| **Tests** | 🔴 Falta | 0% | **NO HAY TESTS** |
| **Lógica de Negocio** | 🔴 Falta | 10% | Sin implementar |
| **Seguridad** | 🔴 Falta | 5% | 2FA no implementado |
| **Auditoría** | 🔴 Falta | 0% | Sin signals/hooks |

---

## ✅ LO QUE ESTÁ IMPLEMENTADO

### 1. Modelos de Base de Datos (17 modelos)

#### 👥 Gestión de Empleados
```python
✅ Empleados
   - campos: nombre, apellido, usuario, contrasena_hash
   - fecha_ingreso, fecha_baja
   - activo (boolean)
   - relación con Roles

✅ Roles  
   - nombre_rol, descripcion
   - activo

✅ PerfilesUsuario
   - Configuración de UI (tema, idioma, timezone)
   - Preferencias de notificaciones
   - Dashboard personalizado (JSON)
   - OneToOne con Empleados
```

#### 🔐 Seguridad y Autenticación
```python
✅ Autenticacion2Fa
   - secret_key, backup_codes
   - habilitado, fecha_activacion
   - unique_together (usuario, tipo_usuario)

✅ Intentos2Fa
   - Tracking de intentos (exitosos/fallidos)
   - IP, geolocalización (ciudad, pais)
   - codigo_ingresado, tipo_codigo

✅ IntentosLogin
   - Historial de intentos de login
   - IP, geolocalización
   - motivo_fallo

✅ SesionesActivas
   - Control de sesiones múltiples
   - session_key, user_agent
   - ultima_actividad, activa

✅ RenovacionesSesion
   - Log de renovaciones de tokens
   - session_key_anterior/nuevo

✅ PatronesAcceso
   - Detección de patrones habituales
   - horario_inicio, horario_fin
   - dias_semana, frecuencia_accesos
   - es_habitual (flag)

✅ BloqueosCuenta
   - Gestión de bloqueos
   - motivo, fecha_bloqueo, fecha_desbloqueo
   - bloqueado_por, activo
```

#### 🌐 Usuarios Portal Web
```python
✅ UsuariosPortal
   - email, password_hash
   - email_verificado
   - OneToOne con Clientes

✅ UsuariosWebClientes  
   - usuario, contrasena_hash
   - OneToOne con Clientes (alternativo)

✅ TokensRecuperacion
   - token único (64 chars)
   - fecha_expiracion, usado
   - Para recuperación de contraseña

✅ TokensVerificacion
   - token, tipo
   - Para verificación de email, etc.
```

#### 📝 Auditoría
```python
✅ AuditoriaEmpleados
   - campo_modificado, valor_anterior, valor_nuevo
   - fecha_cambio, ip_origen

✅ AuditoriaOperaciones
   - operacion, tabla_afectada, id_registro
   - datos_anteriores, datos_nuevos (JSON)
   - ip_address, user_agent, geolocalización
   - resultado, mensaje_error

✅ AuditoriaUsuariosWeb
   - Similar a AuditoriaEmpleados para usuarios web
```

### 2. Endpoints API REST (CRUD Básico)

```http
✅ GET/POST/PUT/DELETE /api/v1/roles/
   - Filtros: activo
   - Búsqueda: nombre_rol

✅ GET/POST/PUT/DELETE /api/v1/empleados/
   - Filtros: activo, id_rol
   - Búsqueda: nombre, apellido, usuario, email
   - Ordenamiento: apellido, nombre

✅ GET/POST/PUT/DELETE /api/v1/perfiles-usuario/
   - Filtros: id_empleado

✅ GET/POST/PUT/DELETE /api/v1/usuarios-portal/
   - Filtros: activo, id_cliente
   - Búsqueda: email
```

### 3. Serializers (4 básicos)

```python
✅ RolesSerializer - campos básicos
✅ EmpleadosSerializer 
   - rol_nombre (read_only)
   - contrasena_hash (write_only)
✅ PerfilesUsuarioSerializer
   - empleado_nombre (read_only)
✅ UsuariosPortalSerializer
   - cliente_nombre (read_only)
   - password_hash (write_only)
```

---

## 🔴 LO QUE FALTA IMPLEMENTAR

### 1. Lógica de Autenticación y Seguridad (CRÍTICO)

#### ❌ Login y Autenticación
```python
FALTA:
- Endpoint /api/v1/auth/login/
- Validación de credenciales (bcrypt/hash)
- Generación de JWT tokens
- Refresh token mechanism
- Logout endpoint
- Registro de IntentosLogin automático
```

#### ❌ Autenticación 2FA
```python
FALTA:
- Endpoint para activar 2FA
  POST /api/v1/auth/2fa/activate/
  - Generar secret_key (TOTP)
  - Generar backup_codes
  - Retornar QR code

- Endpoint para verificar 2FA
  POST /api/v1/auth/2fa/verify/
  - Validar código TOTP
  - Validar backup code
  - Registrar en Intentos2Fa

- Endpoint para desactivar 2FA
  POST /api/v1/auth/2fa/deactivate/

- Endpoint para regenerar backup codes
  POST /api/v1/auth/2fa/regenerate-backup/
```

#### ❌ Gestión de Sesiones
```python
FALTA:
- Signal para crear SesionesActivas en login
- Signal para actualizar ultima_actividad
- Endpoint para listar sesiones activas
  GET /api/v1/auth/sessions/
- Endpoint para cerrar sesión específica
  DELETE /api/v1/auth/sessions/{id}/
- Endpoint para cerrar todas las sesiones
  POST /api/v1/auth/sessions/close-all/
- Task periódica para limpiar sesiones expiradas
```

#### ❌ Recuperación de Contraseña
```python
FALTA:
- Endpoint solicitar recuperación
  POST /api/v1/auth/password-reset/request/
  - Generar token único
  - Enviar email con link
  - Grabar en TokensRecuperacion

- Endpoint validar token
  GET /api/v1/auth/password-reset/validate/{token}/

- Endpoint resetear contraseña
  POST /api/v1/auth/password-reset/confirm/
  - Validar token
  - Cambiar password_hash
  - Marcar token como usado
```

#### ❌ Bloqueo de Cuentas
```python
FALTA:
- Signal para bloquear después de N intentos fallidos
- Endpoint para desbloquear manualmente
  POST /api/v1/usuarios/{id}/unlock/
- Endpoint para listar cuentas bloqueadas
  GET /api/v1/usuarios/blocked/
- Notificación automática al bloquear
```

### 2. Reglas de Negocio NO Implementadas

#### ❌ Validaciones de Empleados
```python
FALTA:
- Validar unicidad de 'usuario'
- Validar formato de email
- Validar que fecha_ingreso <= hoy
- Validar que si activo=False, debe tener fecha_baja
- No permitir eliminar empleados con ventas/operaciones asociadas
```

#### ❌ Validaciones de Roles
```python
FALTA:
- No permitir eliminar roles con empleados asignados
- No permitir desactivar rol 'Admin' si solo hay 1 admin
```

#### ❌ Validaciones de PerfilesUsuario
```python
FALTA:
- Validar formato JSON de dashboard_config
- Valores por defecto al crear empleado
- Validar timezone válido
- Validar idioma soportado
```

#### ❌ Patrones de Acceso
```python
FALTA:
- Task periódica para analizar IntentosLogin
- Detectar patrones (horarios, IPs frecuentes)
- Actualizar PatronesAcceso automáticamente
- Alertar acceso desde IP/horario inusual
```

### 3. Auditoría Automática (CRÍTICO)

#### ❌ Signals de Auditoría
```python
FALTA:
- Signal post_save para Empleados
  → Grabar en AuditoriaEmpleados

- Signal post_save para UsuariosPortal
  → Grabar en AuditoriaUsuariosWeb

- Signal genérico para operaciones críticas
  → Grabar en AuditoriaOperaciones
  (cambios en ventas, compras, inventario, etc.)
```

### 4. Permisos y Autorización

#### ❌ Sistema de Permisos
```python
FALTA:
- Tabla RolesPermisos (relación M2M)
- Permisos granulares:
  - ver_ventas, crear_ventas, anular_ventas
  - ver_stock, ajustar_stock
  - ver_reportes_financieros
  - gestionar_usuarios
  - etc.

- Middleware para validar permisos por endpoint
- Decoradores @require_permission('ver_ventas')
```

#### ❌ Permissions Classes DRF
```python
FALTA:
- IsAdmin
- IsGerente  
- IsCajero
- CanViewReports
- CanManageInventory
- etc.

Actualmente NO HAY control de permisos en los views
```

### 5. Tests (COMPLETAMENTE FALTANTE)

```python
FALTA TODO:
- tests/test_models.py
  - Crear empleados, validaciones
  - Relaciones OneToOne/ForeignKey
  - Unicidad de usuario/email

- tests/test_auth.py
  - Login exitoso/fallido
  - 2FA activar/verificar
  - Tokens JWT
  - Recuperación de contraseña

- tests/test_sessions.py
  - Crear/listar/cerrar sesiones
  - Múltiples sesiones simultáneas
  - Expiración

- tests/test_permissions.py
  - Validar permisos por rol
  - Acceso denegado sin permisos

- tests/test_audit.py
  - Verificar que se graban auditorías
  - Rastrear cambios

TESTS ACTUALES: 0
```

### 6. Endpoints Faltantes

```python
❌ Autenticación:
POST /api/v1/auth/login/
POST /api/v1/auth/logout/
POST /api/v1/auth/refresh-token/
POST /api/v1/auth/register/ (para portal web)

❌ 2FA:
POST /api/v1/auth/2fa/activate/
POST /api/v1/auth/2fa/verify/
POST /api/v1/auth/2fa/deactivate/
GET  /api/v1/auth/2fa/qr-code/

❌ Sesiones:
GET    /api/v1/auth/sessions/
DELETE /api/v1/auth/sessions/{id}/
POST   /api/v1/auth/sessions/close-all/

❌ Recuperación:
POST /api/v1/auth/password-reset/request/
GET  /api/v1/auth/password-reset/validate/{token}/
POST /api/v1/auth/password-reset/confirm/

❌ Perfil:
GET  /api/v1/auth/me/ (usuario actual)
PUT  /api/v1/auth/me/profile/
PUT  /api/v1/auth/me/password/

❌ Gestión:
GET  /api/v1/usuarios/blocked/
POST /api/v1/usuarios/{id}/unlock/
GET  /api/v1/usuarios/{id}/audit-log/
GET  /api/v1/usuarios/{id}/sessions/
```

---

## 📋 PLAN DE ACCIÓN RECOMENDADO

### Fase 1: SEGURIDAD BÁSICA (Alta Prioridad)
```
1. ✅ Implementar login/logout con JWT
2. ✅ Validaciones de contraseñas (hash bcrypt)
3. ✅ Registro de IntentosLogin automático
4. ✅ Bloqueo automático después de 5 intentos fallidos
5. ✅ Recuperación de contraseña con tokens
6. ✅ Tests básicos de autenticación (20-30 tests)
```

### Fase 2: GESTIÓN DE SESIONES (Media Prioridad)
```
1. ✅ Crear SesionesActivas en login
2. ✅ Actualizar ultima_actividad (middleware)
3. ✅ Endpoints para gestionar sesiones
4. ✅ Task para limpiar sesiones expiradas
5. ✅ Tests de sesiones (10-15 tests)
```

### Fase 3: AUTENTICACIÓN 2FA (Media Prioridad)
```
1. ✅ Implementar TOTP con pyotp
2. ✅ Generación de QR codes
3. ✅ Backup codes
4. ✅ Endpoints completos de 2FA
5. ✅ Tests 2FA (15-20 tests)
```

### Fase 4: PERMISOS Y ROLES (Media Prioridad)
```
1. ✅ Tabla RolesPermisos
2. ✅ Permission classes DRF
3. ✅ Aplicar permisos a todos los ViewSets
4. ✅ Tests de permisos (20-25 tests)
```

### Fase 5: AUDITORÍA AUTOMÁTICA (Baja Prioridad)
```
1. ✅ Signals para auditoría de empleados
2. ✅ Signals para auditoría de usuarios web
3. ✅ Signal genérico para operaciones críticas
4. ✅ Endpoint para consultar logs de auditoría
5. ✅ Tests de auditoría (10-15 tests)
```

### Fase 6: ANÁLISIS DE PATRONES (Opcional)
```
1. ✅ Task Celery para analizar patrones
2. ✅ Detección de accesos anómalos
3. ✅ Notificaciones de alerta
4. ✅ Dashboard de seguridad
```

---

## 🎯 COMPARACIÓN: IMPLEMENTADO vs REQUERIDO

| Funcionalidad | Requerido | Implementado | % |
|--------------|-----------|--------------|---|
| Modelos DB | 17 | 17 | 100% ✅ |
| CRUD Básico | 4 ViewSets | 4 ViewSets | 100% ✅ |
| Autenticación | Login, JWT, 2FA | ❌ Nada | 0% 🔴 |
| Sesiones | Gestión completa | ❌ Nada | 0% 🔴 |
| Recuperación Pass | Solicitud, validación, reset | ❌ Nada | 0% 🔴 |
| Permisos | Sistema de permisos por rol | ❌ Nada | 0% 🔴 |
| Auditoría Auto | Signals, logs automáticos | ❌ Nada | 0% 🔴 |
| Validaciones | Reglas de negocio | ❌ Mínimas | 10% 🔴 |
| Tests | 80-100 tests esperados | 0 tests | 0% 🔴 |
| Documentación | API docs, ejemplos | ❌ Falta | 20% 🔴 |

**PROMEDIO GENERAL: 23% de completitud**

---

## 🔧 DEPENDENCIAS NECESARIAS

```txt
# Para implementar todo el módulo usuarios:

# Ya instaladas:
djangorestframework==3.16.1
djangorestframework-simplejwt==5.4.0
django-filter==25.2

# FALTANTES por instalar:
pyotp==2.9.0              # Para TOTP (2FA)
qrcode==7.4.2             # Para generar QR codes
Pillow==12.1.1            # Ya instalado (para QR)
bcrypt==4.1.2             # Para hashing de contraseñas (mejor que default)
django-ratelimit==4.1.0   # Rate limiting para login
celery==5.3.4             # Para tasks periódicas (opcional)
redis==5.0.1              # Para cache y Celery (opcional)
```

---

## 📝 NOTAS IMPORTANTES

1. **Seguridad Crítica**: El módulo de usuarios actualmente **NO TIENE** lógica de autenticación implementada. Cualquier sistema en producción necesita esto **URGENTEMENTE**.

2. **Sin Tests**: Con 0 tests, no hay garantía de que el código básico funcione correctamente.

3. **Sin Permisos**: Todos los endpoints están expuestos sin control de acceso. Esto es un **riesgo de seguridad**.

4. **Auditoría Manual**: No hay signals para auditoría automática. Los cambios críticos no se están registrando.

5. **2FA Preparado**: Los modelos están listos, pero la implementación completa falta.

6. **Patrones de Acceso**: Sistema sofisticado en DB, pero sin lógica para aprovecharlos.

---

## 🚀 SIGUIENTE PASO RECOMENDADO

**OPCIÓN 1: Implementar Seguridad Básica**
```bash
# Tiempo estimado: 2-3 días
1. Login/Logout con JWT (4 horas)
2. Registro de IntentosLogin (2 horas)
3. Validaciones y bloqueos (3 horas)
4. Tests básicos (3 horas)
5. Documentación (1 hora)
```

**OPCIÓN 2: Implementar TODO (Completo)**
```bash
# Tiempo estimado: 2-3 semanas
- Fase 1: Seguridad (3-4 días)
- Fase 2: Sesiones (2-3 días)
- Fase 3: 2FA (2-3 días)
- Fase 4: Permisos (3-4 días)
- Fase 5: Auditoría (2 días)
- Tests completos (3-4 días)
- Documentación (1-2 días)
```

**¿Qué quieres implementar primero?**

---

**Generado**: 1 de marzo de 2026  
**Versión**: 1.0  
**Módulo**: apps/usuarios
