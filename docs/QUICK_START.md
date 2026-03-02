# ⚡ Quick Start - Módulo de Usuarios

## 🚀 Inicio Rápido (5 minutos)

### 1. Verificar Instalación ✅

```bash
# Ya completado ✅
pip install pyotp bcrypt django-ratelimit qrcode
python manage.py migrate usuarios
python manage.py init_usuarios
```

**Resultado**: Sistema inicializado con 41 permisos, 5 roles y usuario admin.

---

### 2. Probar Login

```bash
# Iniciar servidor
python manage.py runserver
```

#### Login con cURL:
```bash
curl -X POST http://localhost:8000/api/v1/usuarios/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "usuario": "admin",
    "password": "Admin123!@#"
  }'
```

#### Respuesta Esperada:
```json
{
  "success": true,
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "empleado": {
    "id_empleado": 1,
    "nombre": "Administrador",
    "usuario": "admin",
    "rol": "Administrador"
  }
}
```

---

### 3. Obtener Perfil

```bash
# Guardar el access token
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

curl -X GET http://localhost:8000/api/v1/usuarios/auth/perfil/ \
  -H "Authorization: Bearer $TOKEN"
```

---

### 4. Habilitar 2FA

```bash
curl -X POST http://localhost:8000/api/v1/usuarios/2fa/habilitar/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Respuesta**:
```json
{
  "success": true,
  "secret_key": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,iVBORw0KG...",
  "backup_codes": [
    "1234-5678",
    "9012-3456",
    ...
  ],
  "provisioning_uri": "otpauth://totp/CantinatTita:admin?secret=JBSWY3..."
}
```

1. Escanear QR code con Google Authenticator
2. Guardar backup codes en lugar seguro
3. Verificar código 2FA

---

### 5. Verificar 2FA

```bash
# Obtener código de tu app Authenticator (ej: 123456)
curl -X POST http://localhost:8000/api/v1/usuarios/2fa/verificar/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "codigo": "123456"
  }'
```

---

### 6. Cambiar Password

```bash
curl -X POST http://localhost:8000/api/v1/usuarios/auth/cambiar_password/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "password_actual": "Admin123!@#",
    "password_nueva": "NuevaPassword123!@#"
  }'
```

---

### 7. Ver Sesiones Activas

```bash
curl -X GET http://localhost:8000/api/v1/usuarios/sesiones/activas/ \
  -H "Authorization: Bearer $TOKEN"
```

---

### 8. Ejecutar Cleanup Manual

```bash
# Ver qué se limpiaría (dry-run)
python manage.py cleanup_usuarios --dry-run --verbose

# Ejecutar limpieza real
python manage.py cleanup_usuarios
```

---

## 📱 Usando Postman

### 1. Importar Collection

Crear archivo `Usuarios.postman_collection.json`:

```json
{
  "info": {
    "name": "Cantina Tita - Usuarios",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Auth",
      "item": [
        {
          "name": "Login",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"usuario\": \"admin\",\n  \"password\": \"Admin123!@#\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/api/v1/usuarios/auth/login/",
              "host": ["{{base_url}}"],
              "path": ["api", "v1", "usuarios", "auth", "login/"]
            }
          }
        },
        {
          "name": "Perfil",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{access_token}}",
                "type": "text"
              }
            ],
            "url": {
              "raw": "{{base_url}}/api/v1/usuarios/auth/perfil/",
              "host": ["{{base_url}}"],
              "path": ["api", "v1", "usuarios", "auth", "perfil/"]
            }
          }
        }
      ]
    },
    {
      "name": "2FA",
      "item": [
        {
          "name": "Habilitar 2FA",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{access_token}}",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/api/v1/usuarios/2fa/habilitar/",
              "host": ["{{base_url}}"],
              "path": ["api", "v1", "usuarios", "2fa", "habilitar/"]
            }
          }
        }
      ]
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000",
      "type": "string"
    },
    {
      "key": "access_token",
      "value": "",
      "type": "string"
    }
  ]
}
```

### 2. Configurar Environment

Variables:
- `base_url`: `http://localhost:8000`
- `access_token`: (se actualiza después del login)

---

## 🧪 Ejecutar Tests

```bash
# Todos los tests (121 tests)
python manage.py test apps.usuarios.tests --noinput

# Solo tests de autenticación (43 tests)
python manage.py test apps.usuarios.tests.test_auth_service

# Solo tests de 2FA (29 tests)
python manage.py test apps.usuarios.tests.test_two_factor_service

# Ver cobertura detallada
python manage.py test apps.usuarios.tests -v 2
```

---

## 📊 Verificar Estado del Sistema

### Ver Permisos

```bash
python manage.py shell
```

```python
from apps.usuarios.models import Permisos
print(f"Permisos creados: {Permisos.objects.count()}")
Permisos.objects.values_list('codigo_permiso', flat=True)
```

### Ver Roles

```python
from apps.usuarios.models import Roles, RolesPermisos
for rol in Roles.objects.all():
    permisos_count = RolesPermisos.objects.filter(id_rol=rol).count()
    print(f"{rol.nombre_rol}: {permisos_count} permisos")
```

### Ver Empleados

```python
from apps.usuarios.models import Empleados
print(f"Empleados activos: {Empleados.objects.filter(activo=True).count()}")
for emp in Empleados.objects.all():
    print(f"- {emp.usuario} ({emp.nombre}) - {emp.id_rol.nombre_rol}")
```

---

## ⚙️ Configuración Rápida de Email (Opcional)

### Gmail (5 minutos)

1. **Crear App Password**:
   - Ir a https://myaccount.google.com/security
   - Habilitar 2FA
   - Generar "App password"

2. **Configurar .env**:
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tuemail@gmail.com
EMAIL_HOST_PASSWORD=xxxx_xxxx_xxxx_xxxx
DEFAULT_FROM_EMAIL=Cantina Tita <tuemail@gmail.com>
```

3. **Probar**:
```python
python manage.py shell

from django.core.mail import send_mail
send_mail(
    'Test',
    'Email de prueba',
    'tuemail@gmail.com',
    ['destinatario@example.com']
)
```

---

## 📋 Checklist de Verificación

### Sistema Inicializado ✅
- [ ] Migraciones aplicadas
- [ ] 41 permisos creados
- [ ] 5 roles creados
- [ ] Usuario admin creado
- [ ] Login funciona
- [ ] 2FA funciona
- [ ] Tests pasan

### Próximos Pasos
- [ ] Cambiar password del admin
- [ ] Configurar email SMTP (opcional)
- [ ] Configurar cron job de cleanup
- [ ] Crear más usuarios
- [ ] Integrar con frontend

---

## 🆘 Troubleshooting Rápido

### Login falla
```bash
# Verificar usuario existe
python manage.py shell
from apps.usuarios.models import Empleados
Empleados.objects.filter(usuario='admin').first()
```

### 2FA no funciona
```bash
# Verificar pyotp instalado
pip show pyotp

# Verificar código es actual (30s window)
# Usar código de backup si falla TOTP
```

### Tests fallan
```bash
# Limpiar base de datos de tests
python manage.py test --noinput

# Ver detalles del error
python manage.py test apps.usuarios.tests -v 2
```

---

## 📚 Documentación Completa

- **API**: [MODULO_USUARIOS_COMPLETO.md](MODULO_USUARIOS_COMPLETO.md)
- **Implementación**: [IMPLEMENTACION_FINAL.md](IMPLEMENTACION_FINAL.md)
- **Email**: [CONFIGURACION_EMAIL.md](CONFIGURACION_EMAIL.md)
- **Deployment**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

## 💡 Ejemplos de Uso Comunes

### Crear Nuevo Empleado

```bash
curl -X POST http://localhost:8000/api/v1/usuarios/empleados/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan",
    "apellido": "Pérez",
    "usuario": "jperez",
    "email": "jperez@cantinatita.com",
    "password": "Password123!@#",
    "id_rol": 3
  }'
```

### Asignar Permiso a Rol

```bash
curl -X POST http://localhost:8000/api/v1/usuarios/permisos/asignar_a_rol/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id_rol": 3,
    "codigo_permiso": "ventas.crear"
  }'
```

### Solicitar Recuperación de Password

```bash
curl -X POST http://localhost:8000/api/v1/usuarios/password/solicitar/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@cantinatita.com"
  }'
```

---

**🎉 ¡Sistema listo para usar! Comienza con el login y explora las funcionalidades.**
