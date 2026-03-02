# 🔐 Módulo de Usuarios - Documentación Completa

## 📋 Tabla de Contenido

1. [Introducción](#introducción)
2. [Características](#características)
3. [Arquitectura](#arquitectura)
4. [Instalación](#instalación)
5. [API Endpoints](#api-endpoints)
6. [Guía de Uso](#guía-de-uso)
7. [Seguridad](#seguridad)
8. [Tests](#tests)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Introducción

El módulo de usuarios de **Cantina Tita** implementa un sistema de autenticación y autorización empresarial con las mejores prácticas de seguridad de la industria.

### Características Principales

✅ **Autenticación JWT** con tokens de acceso y refresco  
✅ **Autenticación de Dos Factores (2FA)** compatible con Google Authenticator  
✅ **Gestión de Sesiones** con detección de patrones sospechosos  
✅ **Sistema de Permisos Granulares** basado en roles  
✅ **Recuperación de Contraseñas** con tokens seguros  
✅ **Auditoría Automática** de todas las operaciones  
✅ **Rate Limiting** para prevenir ataques de fuerza bruta  
✅ **Validación de Contraseñas Fuertes** (8+ caracteres, mayúsculas, números, símbolos)  

---

## 🏗️ Arquitectura

### Componentes del Sistema

```
apps/usuarios/
├── services/
│   ├── auth_service.py              # Autenticación JWT, login, logout
│   ├── two_factor_service.py        # 2FA con TOTP
│   ├── session_service.py           # Gestión de sesiones activas
│   └── password_recovery_service.py # Recuperación de contraseñas
├── models.py                        # 17 modelos de base de datos
├── permissions.py                   # Sistema de permisos granulares
├── signals.py                       # Auditoría automática con signals
├── middleware.py                    # Captura de contexto para auditoría
├── views.py                         # API endpoints REST
├── urls.py                          # Configuración de rutas
└── serializers.py                   # Serializadores DRF
```

### Modelos de Base de Datos

| Modelo | Descripción |
|--------|-------------|
| `Empleados` | Usuarios del sistema (staff) |
| `Roles` | Roles de usuario |
| `Permisos` | Permisos granulares del sistema |
| `RolesPermisos` | Relación roles-permisos |
| `PerfilesUsuario` | Preferencias de usuario |
| `Autenticacion2Fa` | Configuración 2FA |
| `Intentos2Fa` | Registro de intentos 2FA |
| `IntentosLogin` | Registro de intentos de login |
| `SesionesActivas` | Sesiones activas del sistema |
| `RenovacionesSesion` | Historial de renovaciones de sesión |
| `PatronesAcceso` | Patrones de acceso habituales |
| `BloqueosCuenta` | Bloqueos de cuenta |
| `TokensVerificacion` | Tokens para recuperación y verificación |
| `AuditoriaEmpleados` | Auditoría de cambios en empleados |
| `AuditoriaOperaciones` | Auditoría general de operaciones |
| `UsuariosPortal` | Usuarios del portal (clientes) |
| `UsuariosWebClientes` | Usuarios web de clientes |

---

## 🚀 Instalación

### 1. Dependencias

El módulo requiere las siguientes dependencias (ya instaladas):

```txt
Django==6.0.2
djangorestframework==3.16.1
djangorestframework-simplejwt==5.4.0
pyotp==2.9.0           # 2FA TOTP
bcrypt==5.0.0          # Hashing seguro de contraseñas
django-ratelimit==4.1.0 # Protección contra fuerza bruta
qrcode==8.2            # Generación de QR codes para 2FA
```

### 2. Configuración

**settings/base.py:**
```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'rest_framework_simplejwt',
    'django_ratelimit',
    'apps.usuarios',
]

MIDDLEWARE = [
    # ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.usuarios.middleware.AuditContextMiddleware',  # ⬅️ Middleware de auditoría
]

# Configuración JWT
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

### 3. Migraciones

```bash
python manage.py makemigrations usuarios
python manage.py migrate usuarios
```

### 4. Inicializar Permisos

```bash
# Desde Python shell o crear un management command
python manage.py shell

>>> from apps.usuarios.permissions import PermissionService
>>> PermissionService.inicializar_permisos()
{'permisos_creados': 35, 'permisos_existentes': 0, 'total': 35}
```

---

## 📡 API Endpoints

### 🔑 Autenticación

#### **POST** `/api/v1/usuarios/auth/login/`

Login con usuario y contraseña.

**Request:**
```json
{
  "usuario": "admin",
  "password": "Admin123!@#"
}
```

**Response (sin 2FA):**
```json
{
  "success": true,
  "requiere_2fa": false,
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  },
  "empleado": {
    "id": 1,
    "usuario": "admin",
    "nombre": "Juan",
    "apellido": "Pérez",
    "email": "admin@cantinatita.com",
    "rol": "Administrador",
    "id_rol": 1
  },
  "mensaje": "Login exitoso",
  "codigo": "LOGIN_EXITOSO"
}
```

**Response (con 2FA habilitado):**
```json
{
  "success": true,
  "requiere_2fa": true,
  "mensaje": "Por favor, ingrese su código 2FA",
  "token_temporal": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Errores Posibles:**
- `401 Unauthorized`: Credenciales inválidas
- `403 Forbidden`: Cuenta bloqueada
- `429 Too Many Requests`: Demasiados intentos (rate limit: 5/minuto por IP)

---

#### **POST** `/api/v1/usuarios/auth/logout/`

Cierra la sesión actual.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "success": true,
  "mensaje": "Logout exitoso"
}
```

---

#### **POST** `/api/v1/usuarios/auth/cambiar_password/`

Cambia la contraseña del usuario actual.

**Request:**
```json
{
  "password_actual": "OldPass123!",
  "password_nueva": "NewPass456@"
}
```

**Response:**
```json
{
  "success": true,
  "mensaje": "Contraseña cambiada exitosamente. Por favor, vuelva a iniciar sesión."
}
```

**Validaciones de Contraseña:**
- Mínimo 8 caracteres
- Al menos 1 mayúscula
- Al menos 1 minúscula
- Al menos 1 número
- Al menos 1 carácter especial (!@#$%^&*...)

---

#### **GET** `/api/v1/usuarios/auth/perfil/`

Obtiene información del usuario autenticado.

**Response:**
```json
{
  "empleado": {
    "id": 1,
    "usuario": "admin",
    "nombre": "Juan",
    "apellido": "Pérez",
    "email": "admin@cantinatita.com",
    "rol": {
      "id": 1,
      "nombre_rol": "Administrador"
    }
  },
  "permisos": [
    "admin.acceso_total",
    "ventas.ver",
    "ventas.crear",
    "inventario.ajustar",
    "..."
  ],
  "stats_2fa": {
    "habilitado": true,
    "fecha_activacion": "2026-03-01T10:00:00Z",
    "total_intentos": 150,
    "intentos_exitosos": 148,
    "intentos_fallidos": 2,
    "backup_codes_restantes": 8,
    "ultimo_uso": "2026-03-01T14:30:00Z"
  }
}
```

---

### 🔐 Autenticación de Dos Factores (2FA)

#### **POST** `/api/v1/usuarios/2fa/habilitar/`

Habilita 2FA para el usuario actual.

**Response:**
```json
{
  "success": true,
  "secret_key": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "backup_codes": [
    "A1B2-C3D4",
    "E5F6-G7H8",
    "I9J0-K1L2",
    "M3N4-O5P6",
    "Q7R8-S9T0",
    "U1V2-W3X4",
    "Y5Z6-A7B8",
    "C9D0-E1F2",
    "G3H4-I5J6",
    "K7L8-M9N0"
  ],
  "provisioning_uri": "otpauth://totp/Cantina%20Tita:admin@cantinatita.com?secret=JBSWY3DPEHPK3PXP&issuer=Cantina%20Tita",
  "mensaje": "2FA habilitado exitosamente. Guarde los códigos de respaldo en un lugar seguro."
}
```

**Uso del QR Code:**
1. Escanear con Google Authenticator / Authy / Microsoft Authenticator
2. Guardar los códigos de respaldo en lugar seguro
3. Verificar con un código en el siguiente endpoint

---

#### **POST** `/api/v1/usuarios/2fa/verificar/`

Verifica un código 2FA (6 dígitos o código de respaldo).

**Request:**
```json
{
  "codigo": "123456"
}
```

**Response (código válido):**
```json
{
  "success": true,
  "mensaje": "Código 2FA verificado correctamente",
  "tipo_codigo": "totp"
}
```

**Response (código de respaldo):**
```json
{
  "success": true,
  "mensaje": "Código de respaldo verificado. ADVERTENCIA: Este código ya no puede usarse nuevamente.",
  "tipo_codigo": "backup"
}
```

**Errores:**
- Código inválido: `{"success": false, "mensaje": "Código 2FA inválido. Intentos restantes: 2"}`
- Demasiados intentos: `429 Too Many Requests` (rate limit: 10/minuto por usuario)

---

#### **POST** `/api/v1/usuarios/2fa/deshabilitar/`

Deshabilita 2FA para el usuario actual.

**Response:**
```json
{
  "success": true,
  "mensaje": "2FA deshabilitado exitosamente"
}
```

---

#### **POST** `/api/v1/usuarios/2fa/regenerar_backup_codes/`

Regenera los códigos de respaldo (invalida los anteriores).

**Response:**
```json
{
  "success": true,
  "backup_codes": [
    "X1Y2-Z3A4",
    "B5C6-D7E8",
    "..."
  ],
  "mensaje": "Códigos de respaldo regenerados exitosamente. Los códigos anteriores ya no son válidos."
}
```

---

### 🖥️ Gestión de Sesiones

#### **GET** `/api/v1/usuarios/sesiones/activas/`

Lista todas las sesiones activas del usuario.

**Response:**
```json
{
  "sesiones": [
    {
      "id": 1,
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
      "fecha_inicio": "2026-03-01T10:00:00Z",
      "fecha_ultima_actividad": "2026-03-01T14:30:00Z",
      "fecha_expiracion": "2026-03-02T10:00:00Z",
      "tiempo_inactivo_minutos": 15,
      "es_sesion_actual": false
    },
    {
      "id": 2,
      "ip_address": "192.168.1.150",
      "user_agent": "PostmanRuntime/7.32.3",
      "fecha_inicio": "2026-03-01T12:00:00Z",
      "fecha_ultima_actividad": "2026-03-01T14:45:00Z",
      "fecha_expiracion": "2026-03-02T12:00:00Z",
      "tiempo_inactivo_minutos": 0,
      "es_sesion_actual": true
    }
  ],
  "total": 2
}
```

---

#### **POST** `/api/v1/usuarios/sesiones/cerrar/`

Cierra una sesión específica.

**Request:**
```json
{
  "session_key": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

#### **POST** `/api/v1/usuarios/sesiones/cerrar_todas/`

Cierra todas las sesiones excepto la actual.

**Response:**
```json
{
  "success": true,
  "sesiones_cerradas": 3,
  "mensaje": "3 sesión(es) cerrada(s) exitosamente"
}
```

---

### 🔄 Recuperación de Contraseñas

#### **POST** `/api/v1/usuarios/password/solicitar/`

Solicita un token de recuperación de contraseña.

**Request:**
```json
{
  "email": "usuario@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "mensaje": "Si el email existe, recibirá instrucciones para recuperar su contraseña"
}
```

**Nota:** Por seguridad, siempre retorna success=true aunque el email no exista.

**Rate Limit:** 3 solicitudes por hora por IP.

---

#### **POST** `/api/v1/usuarios/password/validar_token/`

Valida un token de recuperación.

**Request:**
```json
{
  "token": "a1b2c3d4e5f6..."
}
```

**Response:**
```json
{
  "valido": true,
  "mensaje": "Token válido"
}
```

---

#### **POST** `/api/v1/usuarios/password/restablecer/`

Restablece la contraseña usando el token.

**Request:**
```json
{
  "token": "a1b2c3d4e5f6...",
  "nueva_password": "NewSecurePass123!@#"
}
```

**Response:**
```json
{
  "success": true,
  "mensaje": "Contraseña restablecida exitosamente. Por favor, inicie sesión con su nueva contraseña."
}
```

**Nota:** Invalida todas las sesiones activas del usuario por seguridad.

---

### 🛡️ Sistema de Permisos

#### **GET** `/api/v1/usuarios/permisos/listar/`

Lista todos los permisos del sistema.

**Requiere:** Permiso `admin.acceso_total`

**Response:**
```json
{
  "permisos": [
    {
      "id": 1,
      "codigo_permiso": "ventas.ver",
      "nombre": "Ver ventas",
      "modulo": "ventas",
      "descripcion": null
    },
    {
      "id": 2,
      "codigo_permiso": "ventas.crear",
      "nombre": "Crear ventas",
      "modulo": "ventas",
      "descripcion": null
    }
  ],
  "permisos_por_modulo": {
    "ventas": [...],
    "inventario": [...],
    "usuarios": [...]
  },
  "total": 35
}
```

---

#### **POST** `/api/v1/usuarios/permisos/inicializar/`

Inicializa todos los permisos predefinidos del sistema.

**Requiere:** Permiso `admin.acceso_total`

**Response:**
```json
{
  "permisos_creados": 35,
  "permisos_existentes": 0,
  "total": 35
}
```

**Permisos Predefinidos:**

| Módulo | Permisos |
|--------|----------|
| **Usuarios** | `usuarios.ver`, `usuarios.crear`, `usuarios.editar`, `usuarios.eliminar`, `usuarios.administrar_roles`, `usuarios.ver_auditoria` |
| **Ventas** | `ventas.ver`, `ventas.crear`, `ventas.editar`, `ventas.anular`, `ventas.ver_reportes`, `ventas.aplicar_descuentos` |
| **Compras** | `compras.ver`, `compras.crear`, `compras.editar`, `compras.aprobar`, `compras.anular` |
| **Inventario** | `inventario.ver`, `inventario.ajustar`, `inventario.transferir`, `inventario.ver_valorizado` |
| **Productos** | `productos.ver`, `productos.crear`, `productos.editar`, `productos.eliminar`, `productos.gestionar_precios` |
| **Clientes** | `clientes.ver`, `clientes.crear`, `clientes.editar`, `clientes.eliminar`, `clientes.ver_creditos` |
| **Reportes** | `reportes.ventas`, `reportes.inventario`, `reportes.financieros`, `reportes.auditoria` |
| **Configuración** | `configuracion.ver`, `configuracion.editar`, `configuracion.gestionar_impuestos` |
| **Admin** | `admin.acceso_total`, `admin.gestionar_backups`, `admin.ver_logs` |

---

#### **POST** `/api/v1/usuarios/permisos/asignar_a_rol/`

Asigna un permiso a un rol.

**Request:**
```json
{
  "id_rol": 2,
  "codigo_permiso": "ventas.crear"
}
```

**Response:**
```json
{
  "success": true,
  "mensaje": "Permiso ventas.crear asignado al rol Vendedor"
}
```

---

### 👥 CRUD de Empleados

#### **GET** `/api/v1/usuarios/empleados/`

Lista empleados con filtros y búsqueda.

**Query Parameters:**
- `activo=true|false` - Filtrar por estado
- `id_rol=1` - Filtrar por rol
- `search=juan` - Buscar en nombre, apellido, usuario, email
- `ordering=apellido,-nombre` - Ordenar

**Response:**
```json
{
  "count": 15,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "usuario": "admin",
      "nombre": "Juan",
      "apellido": "Pérez",
      "email": "admin@cantinatita.com",
      "activo": true,
      "rol": {
        "id": 1,
        "nombre_rol": "Administrador"
      }
    }
  ]
}
```

---

#### **POST** `/api/v1/usuarios/empleados/`

Crea un nuevo empleado.

**Request:**
```json
{
  "nombre": "María",
  "apellido": "González",
  "usuario": "maria.gonzalez",
  "email": "maria@cantinatita.com",
  "password": "SecurePass123!@#",
  "id_rol": 2
}
```

**Response:**
```json
{
  "success": true,
  "empleado": {
    "id": 5,
    "usuario": "maria.gonzalez",
    "nombre": "María",
    "apellido": "González",
    "email": "maria@cantinatita.com",
    "activo": true,
    "rol": {
      "id": 2,
      "nombre_rol": "Vendedor"
    }
  },
  "mensaje": "Empleado creado exitosamente"
}
```

---

## 🔒 Seguridad

### Características de Seguridad Implementadas

#### 1. **Hashing de Contraseñas**
- Algoritmo: **bcrypt** con 12 rounds de salt
- Contraseñas nunca se almacenan en texto plano
- Imposible recuperar contraseña original

#### 2. **Validación de Contraseñas Fuertes**
```python
Requisitos:
- Mínimo 8 caracteres
- Al menos 1 mayúscula
- Al menos 1 minúscula  
- Al menos 1 número
- Al menos 1 símbolo especial (!@#$%^&*...)
```

#### 3. **Rate Limiting**
```python
- Login: 5 intentos / minuto por IP
- Recuperación de contraseña: 3 intentos / hora por IP
- Verificación 2FA: 10 intentos / minuto por usuario
```

#### 4. **Bloqueo de Cuenta**
- Después de 5 intentos fallidos de login
- Bloqueo temporal de 30 minutos
- Auditoría completa del bloqueo

#### 5. **Tokens Seguros**
```python
- Recuperación de contraseña: 2 horas de validez
- Generados con secrets.token_hex(32) (64 caracteres hex)
- Almacenados como hash SHA-256
- Máximo 5 solicitudes por día por usuario
```

#### 6. **JWT Tokens**
```python
- Access token: 1 hora de validez
- Refresh token: 7 días de validez
- Rotación automática al renovar
- Blacklist después de rotación
```

#### 7. **2FA (TOTP)**
```python
- Compatible con Google Authenticator, Authy, etc.
- 10 códigos de respaldo
- Códigos de 6 dígitos con ventana de 30 segundos
- Registro de todos los intentos
```

#### 8. **Auditoría Completa**
```python
Todas las operaciones registran:
- ¿Quién? (id_empleado)
- ¿Qué? (operación)
- ¿Cuándo? (timestamp)
- ¿Dónde? (IP address)
- ¿Qué cambió? (datos_anteriores + datos_nuevos)
```

#### 9. **Detección de Patrones Sospechosos**
```python
El sistema detecta:
- Acceso desde IP no habitual
- Acceso en horario inusual
- Acceso en día atípico
- Múltiples sesiones simultáneas
- Cambios repentinos de ubicación
```

---

## 🧪 Tests

### Ejecutar Tests

```bash
# Todos los tests del módulo
python manage.py test apps.usuarios

# Tests específicos
python manage.py test apps.usuarios.tests.TestAuthenticationService
python manage.py test apps.usuarios.tests.TestTwoFactorAuth
python manage.py test apps.usuarios.tests.TestPermissions
```

### Coverage Esperado

- **Servicios de Autenticación:** 95%+
- **2FA:** 90%+
- **Permisos:** 95%+
- **Sesiones:** 85%+
- **Recuperación de Contraseña:** 90%+
- **Auditoría:** 80%+

---

## ⚡ Mejores Prácticas

### 1. **Flujo de Login Completo con 2FA**

```python
# Paso 1: Login inicial
POST /api/v1/usuarios/auth/login/
{
  "usuario": "admin",
  "password": "Admin123!@#"
}

# Respuesta si tiene 2FA habilitado:
{
  "success": true,
  "requiere_2fa": true,
  "token_temporal": "..."
}

# Paso 2: Verificar código 2FA
POST /api/v1/usuarios/2fa/verificar/
Headers: Authorization: Bearer <token_temporal>
{
  "codigo": "123456"
}

# Respuesta:
{
  "success": true,
  "mensaje": "Código 2FA verificado correctamente"
}

# Paso 3: Obtener tokens finales (re-login automático)
# El sistema automáticamente actualiza los tokens después de verificar 2FA
```

### 2. **Renovación de Tokens**

```python
POST /api/v1/usuarios/auth/token/refresh/
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

# Respuesta:
{
  "access": "nuevo_access_token...",
  "refresh": "nuevo_refresh_token..."  # Token rotado
}
```

### 3. **Verificar Permisos en el Frontend**

```javascript
// Después del login, guardar permisos
const permisos = response.data.empleado.permisos;
localStorage.setItem('permisos', JSON.stringify(permisos));

// Verificar permiso
function tienePermiso(codigo) {
  const permisos = JSON.parse(localStorage.getItem('permisos') || '[]');
  return permisos.includes(codigo) || permisos.includes('admin.acceso_total');
}

// Uso
if (tienePermiso('ventas.crear')) {
  // Mostrar botón "Crear Venta"
}
```

---

## 🐛 Troubleshooting

### Problema: "Token inválido o expirado"

**Solución:**
1. Verificar que el token no haya expirado (access: 1h, refresh: 7d)
2. Renovar usando el refresh token
3. Si el refresh también expiró, hacer login nuevamente

### Problema: "Cuenta bloqueada"

**Solución:**
1. Esperar 30 minutos (bloqueo temporal automático)
2. O contactar a un administrador para desbloqueo manual
3. Verificar en `BloqueosCuenta` tabla

### Problema: "Código 2FA siempre inválido"

**Solución:**
1. Verificar que la hora del servidor esté sincronizada (NTP)
2. El código 2FA depende del tiempo (TOTP)
3. Usar código de respaldo si es necesario
4. Regenerar secret key si el problema persiste

### Problema: "Middleware de auditoría no captura empleado actual"

**Solución:**
1. Verificar que `AuditContextMiddleware` esté en MIDDLEWARE
2. Debe estar DESPUÉS de `AuthenticationMiddleware`
3. Verificar que el usuario esté autenticado con JWT

---

## 📊 Estadísticas y Monitoreo

### Consultas Útiles

```python
# Total de intentos fallidos hoy
from django.utils import timezone
from datetime import timedelta

hoy_inicio = timezone.now().replace(hour=0, minute=0, second=0)
intentos_fallidos = IntentosLogin.objects.filter(
    exitoso=False,
    fecha_intento__gte=hoy_inicio
).count()

# Sesiones activas por usuario
from django.db.models import Count

sesiones_por_usuario = SesionesActivas.objects.filter(
    activa=True
).values('id_empleado__nombre', 'id_empleado__apellido').annotate(
    total=Count('id')
).order_by('-total')

# Empleados con 2FA habilitado
empleados_con_2fa = Autenticacion2Fa.objects.filter(
    habilitado=True,
    tipo_usuario='empleado'
).count()

total_empleados = Empleados.objects.filter(activo=True).count()
porcentaje_2fa = (empleados_con_2fa / total_empleados * 100)
```

---

## 🚀 Roadmap Futuro

- [ ] **Autenticación con proveedores externos** (OAuth2: Google, Microsoft)
- [ ] **Biometría** (WebAuthn API)
- [ ] **Análisis de riesgo con Machine Learning** para detectar accesos sospechosos
- [ ] **Notificaciones por email/SMS** para eventos de seguridad
- [ ] **Dashboard de seguridad** con métricas en tiempo real
- [ ] **Sign in como otro usuario** para administradores (con auditoría completa)
- [ ] **RBAC más granular** con permisos a nivel de objeto

---

## 📝 Licencia

Copyright © 2026 Cantina Tita. Todos los derechos reservados.

---

## 👥 Soporte

Para soporte técnico o reportar bugs, contactar a:
- **Email:** soporte@cantinatita.com
- **Slack:** #cantina-tita-dev
- **Github Issues:** https://github.com/cantinatita/backend/issues
