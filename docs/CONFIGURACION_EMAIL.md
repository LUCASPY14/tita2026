# Guía de Configuración de Email (SMTP)

## 📧 Configuración de Email para Recuperación de Contraseñas

El módulo de usuarios requiere envío de emails para:
- ✉️ Recuperación de contraseñas
- ✉️ Verificación de email
- ✉️ Notificaciones de seguridad (opcional)

---

## 🔧 Configuración Básica

### 1. Agregar Variables de Entorno

Crear archivo `.env` en la raíz del proyecto (backend/):

```bash
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@cantinatita.com
EMAIL_HOST_PASSWORD=tu_password_de_aplicacion
DEFAULT_FROM_EMAIL=Cantina Tita <noreply@cantinatita.com>
```

### 2. Instalar python-decouple (si no está instalado)

```bash
pip install python-decouple
```

### 3. Actualizar settings/base.py

```python
from decouple import config

# Configuración de Email
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@cantinatita.com')

# Para desarrollo: usar console backend
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

---

## 📮 Proveedores de Email Soportados

### Gmail

#### Configuración:
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tucorreo@gmail.com
EMAIL_HOST_PASSWORD=tu_password_de_aplicacion
```

#### Obtener Password de Aplicación:
1. Ir a [Google Account Security](https://myaccount.google.com/security)
2. Habilitar verificación en 2 pasos
3. Ir a "App passwords" (Contraseñas de aplicación)
4. Generar nueva password para "Mail"
5. Usar esa password en `EMAIL_HOST_PASSWORD`

**⚠️ Importante**: No usar tu password de Gmail directamente, usar "App Password"

---

### SendGrid

#### Configuración:
```bash
EMAIL_BACKEND=sendgrid_backend.SendgridBackend
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxx
```

#### Instalación:
```bash
pip install django-sendgrid-v5
```

#### settings.py:
```python
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = config('SENDGRID_API_KEY')
```

---

### Mailgun

#### Configuración:
```bash
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_HOST_USER=postmaster@tudominio.mailgun.org
EMAIL_HOST_PASSWORD=tu_api_key
```

---

### SMTP Personalizado (cPanel, Plesk, etc.)

```bash
EMAIL_HOST=mail.tudominio.com
EMAIL_PORT=465  # o 587 para TLS
EMAIL_USE_SSL=True  # Para puerto 465
EMAIL_USE_TLS=False  # Para puerto 465
EMAIL_HOST_USER=noreply@tudominio.com
EMAIL_HOST_PASSWORD=tu_password
```

---

## 🧪 Pruebas de Configuración

### Probar Envío de Email Desde Shell

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail

send_mail(
    'Test Email',
    'Este es un email de prueba desde Django.',
    'noreply@cantinatita.com',
    ['destinatario@example.com'],
    fail_silently=False,
)
```

### Probar Recuperación de Contraseña

```bash
curl -X POST http://localhost:8000/api/v1/usuarios/password/solicitar/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@cantinatita.com"
  }'
```

---

## 📝 Templates de Email

### Crear Templates Personalizados

Estructura recomendada:
```
backend/
  templates/
    email/
      password_recovery.html
      password_recovery.txt
      email_verification.html
      email_verification.txt
      2fa_enabled.html
```

### Ejemplo: password_recovery.html

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Recuperación de Contraseña - Cantina Tita</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2563eb;">Recuperación de Contraseña</h2>
        
        <p>Hola {{ empleado.nombre }},</p>
        
        <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta.</p>
        
        <p>Para restablecer tu contraseña, haz clic en el siguiente enlace:</p>
        
        <p style="text-align: center; margin: 30px 0;">
            <a href="{{ reset_url }}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">
                Restablecer Contraseña
            </a>
        </p>
        
        <p>O copia y pega este enlace en tu navegador:</p>
        <p style="background-color: #f3f4f6; padding: 10px; word-break: break-all;">{{ reset_url }}</p>
        
        <p><strong>Este enlace expirará en 2 horas.</strong></p>
        
        <p>Si no solicitaste este cambio, puedes ignorar este email. Tu contraseña permanecerá sin cambios.</p>
        
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
        
        <p style="font-size: 0.875rem; color: #6b7280;">
            Este es un email automático de Cantina Tita. Por favor no respondas a este mensaje.
        </p>
    </div>
</body>
</html>
```

### Actualizar PasswordRecoveryService

```python
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def enviar_email_recuperacion(empleado, token):
    """Enviar email de recuperación de contraseña"""
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    # Renderizar template HTML
    html_message = render_to_string('email/password_recovery.html', {
        'empleado': empleado,
        'reset_url': reset_url,
        'token': token
    })
    
    # Texto plano fallback
    plain_message = f"""
Hola {empleado.nombre},

Recibimos una solicitud para restablecer la contraseña de tu cuenta.

Para restablecer tu contraseña, copia y pega este enlace en tu navegador:
{reset_url}

Este enlace expirará en 2 horas.

Si no solicitaste este cambio, puedes ignorar este email.

Saludos,
Equipo Cantina Tita
    """.strip()
    
    send_mail(
        subject='Recuperación de Contraseña - Cantina Tita',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[empleado.email],
        html_message=html_message,
        fail_silently=False
    )
```

---

## 🔒 Seguridad

### Variables de Entorno en Producción

**✅ HACER:**
- Usar variables de entorno para credenciales
- Usar servicios de gestión de secretos (AWS Secrets Manager, HashiCorp Vault, etc.)
- Rotar passwords regularmente
- Usar email dedicado para la aplicación (no personal)

**❌ NO HACER:**
- Commitear credenciales en Git
- Usar passwords en código fuente
- Compartir credenciales de email personal

### .gitignore

Asegurar que `.env` está en `.gitignore`:

```bash
# Environment variables
.env
.env.local
.env.production

# Email credentials
*_credentials.json
```

---

## 📊 Monitoreo y Logs

### Configurar Logging para Emails

```python
# settings/base.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_handler': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/email.log',
        },
    },
    'loggers': {
        'django.core.mail': {
            'handlers': ['mail_handler'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### Verificar Logs

```bash
tail -f logs/email.log
```

---

## 🚀 Testing en Desarrollo

### Usar Console Backend (Development)

```python
# settings/development.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Emails se mostrarán en la consola en lugar de enviarse.

### Usar File Backend (Testing)

```python
# settings/test.py
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = 'test_emails/'
```

Emails se guardarán como archivos en `test_emails/`.

---

## 📱 Integración con Frontend

### URL de Frontend en .env

```bash
FRONTEND_URL=https://cantinatita.com
# o en desarrollo:
FRONTEND_URL=http://localhost:3000
```

### Endpoint de Reset Password

Frontend debe implementar ruta:
```
/reset-password?token=XXXXXXXXXX
```

Que llame al endpoint:
```
POST /api/v1/usuarios/password/restablecer/
```

---

## ✅ Checklist de Configuración

- [ ] Variables de entorno configuradas en `.env`
- [ ] `EMAIL_HOST_PASSWORD` con App Password (no password real)
- [ ] `DEFAULT_FROM_EMAIL` configurado
- [ ] `FRONTEND_URL` configurado
- [ ] Templates de email creados
- [ ] Prueba de envío exitosa
- [ ] Logs configurados
- [ ] `.env` en `.gitignore`
- [ ] Documentación para equipo

---

## 🆘 Troubleshooting

### Error: "SMTPAuthenticationError"
- Verificar `EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD`
- Para Gmail: Usar App Password, no password de cuenta
- Verificar que 2FA está habilitado (Gmail)

### Error: "Connection refused"
- Verificar `EMAIL_HOST` y `EMAIL_PORT`
- Verificar firewall no bloquea puerto SMTP
- Probar con telnet: `telnet smtp.gmail.com 587`

### Emails no llegan
- Revisar carpeta de SPAM
- Verificar dominio del remitente
- Revisar logs: `logs/email.log`
- Verificar límites de envío del proveedor

### Error: "TLS/SSL handshake failed"
- Para puerto 587: `EMAIL_USE_TLS=True`, `EMAIL_USE_SSL=False`
- Para puerto 465: `EMAIL_USE_SSL=True`, `EMAIL_USE_TLS=False`

---

## 📚 Recursos Adicionales

- [Django Email Documentation](https://docs.djangoproject.com/en/5.1/topics/email/)
- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)
- [SendGrid Django](https://github.com/sklarsa/django-sendgrid-v5)
- [Email Testing Tools](https://mailtrap.io/)

---

## 💡 Recomendaciones Finales

1. **Desarrollo**: Usar `console` backend
2. **Testing**: Usar `filebased` backend o servicio como Mailtrap
3. **Staging**: Usar SMTP real con dominio de prueba
4. **Producción**: Usar servicio profesional (SendGrid, Mailgun, SES)

5. **Monitoreo**: Configurar alertas para fallos de envío
6. **Límites**: Respetar rate limits del proveedor
7. **Templates**: Mantener diseño responsive
8. **Testing**: Tests automatizados para flujo de emails
