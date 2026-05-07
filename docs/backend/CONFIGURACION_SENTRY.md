# Configuración de Sentry para Monitoreo de Errores

## 🎯 Objetivo

Sentry es una plataforma de monitoreo de errores que te ayudará a:
- Detectar errores en producción en tiempo real
- Recibir notificaciones inmediatas de fallos críticos
- Rastrear el rendimiento de la aplicación
- Identificar problemas antes de que afecten a los usuarios

## 📋 Paso 1: Crear Cuenta en Sentry

1. Visita [https://sentry.io/signup/](https://sentry.io/signup/)
2. Crea una cuenta gratuita (plan Developer - 5,000 errores/mes)
3. Crea un nuevo proyecto:
   - Plataforma: **Django**
   - Nombre del proyecto: `cantina-tita-backend`
   - Equipo: Personal o crea uno nuevo

## 🔑 Paso 2: Obtener el DSN

Después de crear el proyecto, Sentry te mostrará tu **DSN (Data Source Name)**:

```
https://abc123def456@o123456.ingest.sentry.io/7890123
```

**Guarda este DSN**, lo necesitarás en el siguiente paso.

## ⚙️ Paso 3: Configurar Variables de Entorno

Edita tu archivo `.env.production` (o crea uno basado en `.env.production.example`):

```bash
# Sentry Configuration
SENTRY_DSN=https://abc123def456@o123456.ingest.sentry.io/7890123
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### Parámetros:

- **SENTRY_DSN**: La URL que obtuviste de Sentry (OBLIGATORIO)
- **SENTRY_ENVIRONMENT**: `production`, `staging`, `development` (opcional, default: `production`)
- **SENTRY_TRACES_SAMPLE_RATE**: Porcentaje de transacciones a monitorear (0.0 a 1.0)
  - `1.0` = 100% de transacciones (alto consumo, solo para debugging)
  - `0.1` = 10% de transacciones (RECOMENDADO para producción)
  - `0.01` = 1% de transacciones (para aplicaciones de alto tráfico)

## 📦 Paso 4: Instalar Dependencias

```powershell
cd D:\tita2026\cantina_tita\backend
pip install -r requirements.txt
```

Esto instalará:
- `sentry-sdk==2.22.0` - SDK de Sentry
- `django-redis==5.4.0` - Redis para caching (opcional)

## 🔧 Configuración Automática

El archivo `backend/settings/production.py` ya está configurado para usar Sentry:

```python
# Sentry Integration (si SENTRY_DSN está configurado)
if os.environ.get("SENTRY_DSN"):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration

    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_DSN"),
        integrations=[
            DjangoIntegration(),
            RedisIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        send_default_pii=False,  # No enviar información personal
        environment=os.environ.get("SENTRY_ENVIRONMENT", "production"),
    )
```

### Integraciones Incluidas:

✅ **DjangoIntegration**: Captura errores de Django, middlewares, views
✅ **RedisIntegration**: Monitorea operaciones de Redis/Celery
✅ **CeleryIntegration**: Rastrea tareas de Celery y errores async

## 🧪 Paso 5: Probar la Configuración

### Opción A: Endpoint de Prueba (Recomendado)

Crea una vista temporal para probar Sentry:

```python
# backend/apps/core/views.py
from django.http import HttpResponse

def test_sentry(request):
    """Vista temporal para probar Sentry - ELIMINAR en producción"""
    division_by_zero = 1 / 0  # Esto generará un error
    return HttpResponse("No deberías ver esto")
```

Agrega la URL:

```python
# backend/cantina_tita/urls.py
urlpatterns = [
    # ... otras URLs
    path('test-sentry/', test_sentry),  # TEMPORAL
]
```

Accede a `https://tu-dominio.com/test-sentry/` y deberías ver el error en Sentry.

### Opción B: Probar desde el Shell

```powershell
cd D:\tita2026\cantina_tita\backend
python manage.py shell --settings=cantina_tita.settings.production
```

Dentro del shell:

```python
from sentry_sdk import capture_message, capture_exception

# Enviar un mensaje de prueba
capture_message("Sentry está configurado correctamente! 🎉", level="info")

# Enviar un error de prueba
try:
    1 / 0
except Exception as e:
    capture_exception(e)
```

Ve a tu dashboard de Sentry en [https://sentry.io/](https://sentry.io/) y verifica que aparezcan los eventos.

## 📊 Paso 6: Verificar en Dashboard de Sentry

1. Ingresa a [https://sentry.io/](https://sentry.io/)
2. Selecciona tu proyecto `cantina-tita-backend`
3. Deberías ver:
   - **Issues**: Listado de errores capturados
   - **Performance**: Transacciones y métricas de rendimiento
   - **Releases**: Versiones desplegadas (opcional)

## 🔔 Paso 7: Configurar Alertas

1. En el dashboard de Sentry, ve a **Settings** → **Alerts**
2. Crea una nueva alerta:
   - **Tipo**: Issue Alert
   - **Condición**: Cuando un nuevo issue es detectado
   - **Acción**: Enviar notificación a tu email/Slack

### Alertas Recomendadas:

```
1. Error Crítico Detectado
   - Condición: Nuevo issue con nivel "error" o "fatal"
   - Acción: Email inmediato + Slack (si está configurado)

2. Alto Volumen de Errores
   - Condición: Más de 10 eventos del mismo issue en 1 hora
   - Acción: Email + notificación en Sentry

3. Error en Endpoint Crítico
   - Condición: Error en /api/ventas/ o /api/auth/
   - Acción: Email inmediato + SMS (plan pago)
```

## 📈 Monitoreo de Performance

Sentry también te permite monitorear el rendimiento de tu aplicación:

### Ver Transacciones Lentas:

1. Ve a **Performance** en tu dashboard
2. Filtra por:
   - **Transaction**: Nombre de endpoint (ej: `POST /api/ventas/`)
   - **Duration**: Transacciones que tardaron más de 1 segundo

### Endpoints Críticos a Monitorear:

```
✅ POST /api/auth/login/         (Autenticación)
✅ POST /api/ventas/             (Registro de ventas)
✅ GET  /api/productos/          (Listado de productos)
✅ POST /api/clientes/           (Registro de clientes)
✅ GET  /api/turnos/actual/      (Turno actual)
```

## 🚨 Buenas Prácticas

### ✅ DO:
- ✅ Mantener `send_default_pii=False` para no enviar datos personales
- ✅ Usar `traces_sample_rate=0.1` (10%) en producción
- ✅ Configurar alertas para errores críticos
- ✅ Revisar el dashboard de Sentry diariamente
- ✅ Usar `capture_message()` para logs importantes

### ❌ DON'T:
- ❌ NO enviar `SENTRY_DSN` a repositorios públicos
- ❌ NO usar `traces_sample_rate=1.0` en producción (alto consumo)
- ❌ NO ignorar errores sin investigar la causa raíz
- ❌ NO enviar información sensible (contraseñas, tokens) a Sentry

## 📝 Uso Avanzado

### Capturar Contexto Adicional:

```python
from sentry_sdk import set_context, set_tag, set_user

# Agregar información del usuario (sin PII)
set_user({"id": usuario.id_empleado, "username": usuario.usuario})

# Agregar tags personalizados
set_tag("tipo_venta", "credito")
set_tag("caja_id", caja.id_caja)

# Agregar contexto
set_context("venta", {
    "id_venta": venta.id_venta,
    "monto_total": float(venta.monto_total),
    "id_cliente": venta.id_cliente_id,
})
```

### Breadcrumbs (Rastro de Eventos):

```python
from sentry_sdk import add_breadcrumb

add_breadcrumb(
    category="auth",
    message="Usuario intentó iniciar sesión",
    level="info",
    data={"username": usuario.usuario}
)
```

## 🔄 Integración con CI/CD

Si usas GitHub Actions o GitLab CI, puedes enviar releases a Sentry:

```yaml
# .github/workflows/deploy.yml
- name: Create Sentry Release
  run: |
    sentry-cli releases new ${{ github.sha }}
    sentry-cli releases set-commits ${{ github.sha }} --auto
    sentry-cli releases finalize ${{ github.sha }}
  env:
    SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
    SENTRY_ORG: tu-organizacion
    SENTRY_PROJECT: cantina-tita-backend
```

## 📞 Recursos Adicionales

- 📖 Documentación oficial: [https://docs.sentry.io/platforms/python/guides/django/](https://docs.sentry.io/platforms/python/guides/django/)
- 💬 Soporte de Sentry: [https://forum.sentry.io/](https://forum.sentry.io/)
- 🎓 Guía de mejores prácticas: [https://docs.sentry.io/product/best-practices/](https://docs.sentry.io/product/best-practices/)

## ✅ Checklist de Implementación

- [ ] Crear cuenta en Sentry.io
- [ ] Crear proyecto Django en Sentry
- [ ] Copiar DSN de Sentry
- [ ] Agregar SENTRY_DSN a `.env.production`
- [ ] Instalar dependencias: `pip install -r requirements.txt`
- [ ] Probar Sentry con endpoint de prueba
- [ ] Verificar eventos en dashboard de Sentry
- [ ] Configurar alertas por email/Slack
- [ ] Documentar el DSN en gestor de secretos (Azure Key Vault, AWS Secrets Manager, etc.)
- [ ] Eliminar endpoint de prueba

---

**Estado**: ✅ Configurado en `production.py` - Solo falta agregar `SENTRY_DSN` al `.env.production`
