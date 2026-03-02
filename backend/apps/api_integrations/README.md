# 📡 API Integrations - Sistema de Integración con APIs Externas

Módulo especializado para la gestión integral de integraciones con APIs externas, webhooks, credenciales multi-ambiente y logging completo de llamadas. Sistema empresarial diseñado para manejar múltiples proveedores de servicios con soporte para REST, SOAP, GraphQL, WebSocket, gRPC, XML-RPC y OData.

---

## 📋 Tabla de Contenidos

1. [Características Principales](#características-principales)
2. [Modelos del Sistema](#modelos-del-sistema)
3. [Validadores (48 total)](#validadores-48-total)
4. [Configuración de Proveedores](#configuración-de-proveedores)
5. [Gestión de Endpoints](#gestión-de-endpoints)
6. [Sistema de Credenciales](#sistema-de-credenciales)
7. [Webhooks](#webhooks)
8. [Logging y Monitoreo](#logging-y-monitoreo)
9. [Casos de Uso](#casos-de-uso)
10. [Tests](#tests)
11. [API Reference](#api-reference)

---

## 🎯 Características Principales

### Gestión Multi-Proveedor
- ✅ Soporte para 7 tipos de servicios API (REST, SOAP, GraphQL, WebSocket, gRPC, XML-RPC, OData)
- ✅ 8 métodos de autenticación (API_KEY, OAuth2, Bearer, Basic, JWT, None, HMAC, Custom)
- ✅ Configuración JSON flexible para cada proveedor
- ✅ Versionado semántico (v1.0.0, 2.1.3, v3)
- ✅ Timeouts configurables (1-300 segundos)
- ✅ Sistema de reintentos (0-10 intentos)

### Endpoints Dinámicos
- ✅ 7 métodos HTTP (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)
- ✅ Validación de paths ( `/api/v1/payments`, `/users/{id}`)
- ✅ Schemas JSON para request/response (hasta 50KB)
- ✅ Caché configurable (0-86400 segundos = 24 horas)
- ✅ Headers y parámetros JSON
- ✅ Autenticación opcional por endpoint

### Webhooks Empresariales
- ✅ Endpoints personalizados con paths únicos
- ✅ Verificación de firma HMAC con secret keys (mínimo 32 caracteres)
- ✅ Headers de verificación configurables (X-Stripe-Signature, Authorization, etc.)
- ✅ Eventos tipados con validación (payment.created, user.signup, etc.)
- ✅ Handlers Python personalizados (apps.api_integrations.handlers.handle_stripe_webhook)
- ✅ UNIQUE constraint por proveedor+path

### Credenciales Multi-Ambiente
- ✅ 4 ambientes (development, staging, production, testing)
- ✅ API Keys, Secrets y Tokens separados
- ✅ Configuración JSON adicional (hasta 20KB)
- ✅ Fechas de expiración
- ✅ UNIQUE constraint por proveedor+ambiente
- ✅ Timestamps de actualización

### Logging Completo
- ✅ **LogsLlamadasApi**: Request completo (método, URL, headers, payload hasta 1MB)
- ✅ **LogsLlamadasApi**: Response completo (status code 100-599, headers, payload, bytes)
- ✅ **LogsLlamadasApi**: Métricas (tiempo en ms, bytes enviados/recibidos hasta 100MB)
- ✅ **LogsLlamadasApi**: Contexto JSON (hasta 10KB), IP origen (IPv4/IPv6)
- ✅ **LogsWebhooks**: Eventos recibidos con payload (hasta 1MB)
- ✅ **LogsWebhooks**: Verificación y procesamiento (verificacion_ok, procesado_ok)
- ✅ **LogsWebhooks**: Tiempo de procesamiento (hasta 60000ms = 1 minuto)

### Validación Avanzada
- ✅ 48 validadores personalizados
- ✅ Validación de URLs (http/https obligatorio)
- ✅ Validación IPv4 e IPv6
- ✅ Validación JSON con límites de tamaño
- ✅ Validación de headers HTTP
- ✅ Validación de paths de funciones Python
- ✅ Tolerancia de ±1 hora para timestamps (clock skew)

---

## 📦 Modelos del Sistema

### 1. ProveedoresApi
**Proveedores de servicios API externos (Stripe, PayPal, Twilio, etc.)**

```python
class ProveedoresApi(models.Model):
    id_proveedor       # AutoField - PK
    nombre             # CharField(100) - "Stripe Payments"
    descripcion        # TextField - Descripción detallada
    tipo_servicio      # CharField(30) - REST/SOAP/GraphQL/WebSocket/gRPC/XML-RPC/OData
    url_base           # CharField(200) - https://api.stripe.com
    version            # CharField(20) - v1.0.0, 2.1.3, v3
    documentacion      # CharField(200, optional) - URL de docs
    tipo_auth          # CharField(20) - API_KEY/OAuth2/Bearer/Basic/JWT/None/HMAC/Custom
    config_auth        # JSONField - {"header": "Authorization", "prefix": "Bearer"}
    timeout            # IntegerField - 1-300 segundos
    max_reintentos     # IntegerField - 0-10
    activo             # BooleanField - True/False
    created_at         # DateTimeField
```

**Características:**
- URLs validadas con protocolo http/https obligatorio
- Versiones semánticas (regex `^v?\d+(\.\d+)*$`)
- config_auth con límite de 10KB serializado
- Timeouts entre 1-300 segundos (5 minutos máximo)
- Reintentos configurables 0-10

**Ejemplo JSON config_auth:**
```json
{
    "header": "Authorization",
    "prefix": "Bearer",
    "additional_headers": {
        "X-API-Version": "2023-03-01"
    },
    "params": {
        "client_id": "app_identifier"
    }
}
```

---

### 2. EndpointsApi
**Endpoints específicos de cada proveedor**

```python
class EndpointsApi(models.Model):
    id_endpoint        # AutoField - PK
    nombre             # CharField(100) - "Create Payment Intent"
    descripcion        # TextField - Descripción funcional
    path               # CharField(200) - /v1/payment_intents
    metodo             # CharField(10) - GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS
    headers            # JSONField - {"Content-Type": "application/json"}
    parametros         # JSONField - Query params o path params
    schema_request     # JSONField - Schema de request (hasta 50KB)
    schema_response    # JSONField - Schema de response (hasta 50KB)
    cache_segundos     # IntegerField - 0-86400 (24 horas)
    requiere_auth      # IntegerField - 0 o 1
    activo             # BooleanField
    id_proveedor       # ForeignKey(ProveedoresApi)
```

**Características:**
- Paths validados: deben empezar con `/`, sin espacios, regex `/[a-zA-Z0-9/_\-{}]*$`
- Métodos HTTP normalizados a mayúsculas (get → GET)
- Headers validados como nombres HTTP válidos
- Schemas JSON con límite de 50KB
- Caché de 0 segundos (sin caché) hasta 24 horas
- requiere_auth: 0 (público) o 1 (autenticado)

**Ejemplo path con parámetros:**
```
/api/v1/customers/{customer_id}/payments/{payment_id}
```

**Ejemplo schema_request:**
```json
{
    "type": "object",
    "required": ["amount", "currency"],
    "properties": {
        "amount": {"type": "number", "minimum": 0},
        "currency": {"type": "string", "enum": ["USD", "EUR", "GBP"]},
        "description": {"type": "string", "maxLength": 500}
    }
}
```

---

### 3. LogsLlamadasApi
**Registro completo de todas las llamadas API (request + response)**

```python
class LogsLlamadasApi(models.Model):
    id_log             # AutoField - PK
    timestamp          # DateTimeField - Momento de la llamada
    metodo             # CharField(10) - GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS
    url                # CharField(500) - URL completa
    headers_req        # JSONField - Headers request
    payload_req        # TextField(optional) - Body request (hasta 1MB)
    status_code        # IntegerField - 100-599
    headers_res        # JSONField - Headers response
    payload_res        # TextField(optional) - Body response (hasta 1MB)
    tiempo_ms          # IntegerField - Tiempo de respuesta en milisegundos (0-3600000)
    bytes_sent         # IntegerField(optional) - Bytes enviados (0-100MB)
    bytes_received     # IntegerField(optional) - Bytes recibidos (0-100MB)
    exitoso            # IntegerField - 0 (error) o 1 (éxito)
    error_msg          # TextField(optional) - Mensaje de error (hasta 5000 chars)
    intento            # IntegerField - Número de intento (1-100)
    ip_origen          # CharField(39, optional) - IPv4 o IPv6
    contexto           # JSONField - Información adicional (hasta 10KB)
    id_endpoint        # ForeignKey(EndpointsApi, optional)
    id_empleado        # ForeignKey(Empleados, optional)
```

**Características:**
- Timestamps con tolerancia de ±1 hora para clock skew
- URLs validadas con formato correcto
- Payloads hasta 1MB (request y response)
- Status codes HTTP válidos (100-599)
- Tiempos en milisegundos hasta 1 hora
- Bytes hasta 100MB
- IP origen: IPv4 (`^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$`) o IPv6 (`^[0-9a-fA-F:]+$`)
- Contexto JSON con límite de 10KB

**Ejemplo contexto JSON:**
```json
{
    "user_action": "create_invoice",
    "session_id": "sess_abc123",
    "trace_id": "trace_xyz789",
    "metadata": {
        "origin": "web_app",
        "version": "2.1.0"
    }
}
```

**Códigos de Status HTTP:**
- 2xx: Éxito (verde en admin)
- 3xx: Redirección (azul claro)
- 4xx: Error del cliente (amarillo)
- 5xx: Error del servidor (rojo)

---

### 4. CredencialesApi
**Credenciales por ambiente para cada proveedor**

```python
class CredencialesApi(models.Model):
    id_credencial      # AutoField - PK
    ambiente           # CharField(20) - development/staging/production/testing
    api_key            # TextField(optional) - Mínimo 10 chars, máximo 5000
    secret             # TextField(optional) - Mínimo 10 chars, máximo 5000
    token              # TextField(optional) - Mínimo 10 chars, máximo 5000 (JWT puede ser largo)
    configuracion      # JSONField - Config adicional (hasta 20KB)
    fecha_expiracion   # DateTimeField(optional) - Fecha futura con tolerancia ±1h
    updated_at         # DateTimeField - Última actualización
    activo             # BooleanField
    id_proveedor       # ForeignKey(ProveedoresApi)
    
    class Meta:
        unique_together = (('id_proveedor', 'ambiente'),)
```

**Características:**
- 4 ambientes: development, staging, production, testing (case-insensitive)
- UNIQUE constraint: no puede haber duplicados de proveedor+ambiente
- api_key, secret, token opcionales pero mínimo 10 caracteres si se proveen
- configuracion JSON hasta 20KB
- Fecha de expiración debe ser futura (validación con tolerancia)
- Badges de ambiente en admin con colores:
  - 🛠️ Development (gris)
  - 🚧 Staging (amarillo)
  - 🔴 Production (rojo)
  - 🧪 Testing (azul)

**Ejemplo configuracion JSON:**
```json
{
    "webhook_secret": "whsec_abc123...",
    "rate_limit": {
        "requests_per_minute": 100,
        "burst": 20
    },
    "endpoints_habilitados": [
        "/v1/payments",
        "/v1/customers",
        "/v1/refunds"
    ],
    "opciones": {
        "retry_on_429": true,
        "timeout_override": 60
    }
}
```

**Admin con campos sensibles colapsados:**
- api_key, secret, token se muestran colapsados por defecto
- Indicadores ✓ / — para verificar presencia sin exponer valores

---

### 5. LogsWebhooks
**Registro de webhooks recibidos de proveedores externos**

```python
class LogsWebhooks(models.Model):
    id_log             # AutoField - PK
    timestamp          # DateTimeField - Momento de recepción
    headers            # JSONField - Headers HTTP recibidos
    payload            # TextField - Payload recibido (REQUERIDO, hasta 1MB)
    evento_tipo        # CharField(100) - payment.created, user.signup, invoice.updated
    verificacion_ok    # IntegerField - 0 (falló) o 1 (pasó)
    procesado_ok       # IntegerField - 0 (error) o 1 (éxito)
    tiempo_proc_ms     # IntegerField(optional) - Tiempo procesamiento 0-60000ms (1 min)
    error_msg          # TextField(optional) - Error si procesado_ok=0 (hasta 5000 chars)
    ip_origen          # CharField(39) - IPv4 o IPv6 REQUERIDO
    user_agent         # TextField(optional) - User-Agent header (hasta 500 chars)
    id_webhook         # ForeignKey(WebhookEndpoints, optional)
```

**Características:**
- Timestamp con tolerancia ±1 hora
- Payload REQUERIDO (no opcional), hasta 1MB
- evento_tipo validado: 3-100 chars, regex `^[a-zA-Z0-9._\-]+$`
- verificacion_ok: verificación de firma HMAC
- procesado_ok: resultado del procesamiento del handler
- Tiempo de procesamiento hasta 1 minuto
- IP origen REQUERIDA (IPv4 o IPv6)
- User-Agent opcional para identificar el cliente

**Ejemplos evento_tipo:**
- `payment.created`
- `payment.updated`
- `payment.succeeded`
- `payment.failed`
- `invoice.created`
- `invoice.paid`
- `customer.created`
- `subscription.created`
- `charge.refunded`
- `user_signup`
- `user.deleted`

**Webhook Flow:**
```
1. Proveedor envía POST → /webhooks/stripe
2. Sistema registra log con timestamp, headers, payload, IP
3. Sistema verifica firma HMAC → verificacion_ok = 1 o 0
4. Sistema ejecuta handler_func → procesado_ok = 1 o 0
5. Registra tiempo_proc_ms y error_msg si falla
```

---

### 6. WebhookEndpoints
**Configuración de endpoints para recibir webhooks**

```python
class WebhookEndpoints(models.Model):
    id_webhook         # AutoField - PK
    nombre             # CharField(100) - "Stripe Payment Events"
    descripcion        # TextField - Descripción funcional
    path               # CharField(200) - /webhooks/stripe
    requiere_verificacion  # IntegerField - 0 o 1
    secret_key         # CharField(255) - MÍNIMO 32 caracteres
    header_verificacion    # CharField(100) - X-Stripe-Signature
    eventos            # JSONField - ["payment.created", "payment.updated"]
    handler_func       # CharField(200) - apps.api_integrations.handlers.handle_stripe
    activo             # BooleanField
    created_at         # DateTimeField
    id_proveedor       # ForeignKey(ProveedoresApi)
    
    class Meta:
        unique_together = (('id_proveedor', 'path'),)
```

**Características:**
- Path validado: empieza con `/`, sin espacios
- UNIQUE constraint: proveedor+path (ej: Stripe no puede tener dos /webhooks/stripe)
- secret_key MÍNIMO 32 caracteres (requisito de seguridad)
- header_verificacion validado como nombre HTTP válido (regex `^[A-Za-z][A-Za-z0-9\-]*$`)
- eventos: JSON array de strings únicos (sin duplicados), cada evento 3-100 chars
- handler_func: path Python válido (regex `^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)+$`)

**Ejemplo eventos JSON:**
```json
[
    "payment.created",
    "payment.updated",
    "payment.succeeded",
    "payment.failed",
    "payment.refunded",
    "invoice.created",
    "invoice.paid",
    "customer.created",
    "customer.updated"
]
```

**Validaciones eventos:**
- ✅ Sin duplicados
- ✅ Cada evento 3-100 caracteres
- ✅ Formato: `^[a-zA-Z0-9._\-]+$`
- ❌ No se permiten espacios, caracteres especiales, tildes

**Ejemplo handler_func:**
```python
# apps/api_integrations/handlers.py
def handle_stripe_webhook(payload, headers, ip_origen):
    """
    Handler para webhooks de Stripe
    
    Args:
        payload (str): JSON payload del webhook
        headers (dict): Headers HTTP recibidos
        ip_origen (str): IP del remitente
        
    Returns:
        dict: {"success": True/False, "message": "..."}
    """
    import json
    data = json.loads(payload)
    
    evento_tipo = data.get('type')
    
    if evento_tipo == 'payment.succeeded':
        # Procesar pago exitoso
        payment_id = data['data']['object']['id']
        # ... lógica de negocio ...
        return {"success": True, "message": f"Payment {payment_id} processed"}
    
    # ... otros eventos ...
    
    return {"success": False, "message": f"Event {evento_tipo} not handled"}
```

**Paths handler_func válidos:**
- ✅ `apps.api_integrations.handlers.handle_stripe_webhook`
- ✅ `apps.ventas.webhooks.process_payment`
- ✅ `myapp.webhooks.handlers.custom_handler`
- ❌ `handle_webhook` (sin puntos, no es callable path)
- ❌ `123app.handler.func` (empieza con número)

---

## 🔐 Validadores (48 total)

### ProveedoresApi (12 validadores)

#### 1. `validar_nombre_proveedor(valor)`
Valida el nombre del proveedor.

**Reglas:**
- ✅ Mínimo 3 caracteres
- ✅ Máximo 100 caracteres
- ✅ Trim automático

**Ejemplos:**
```python
validar_nombre_proveedor("Stripe Payments")  # ✓ OK
validar_nombre_proveedor("PayPal")           # ✓ OK
validar_nombre_proveedor(" Twilio API ")     # ✓ OK → "Twilio API"
validar_nombre_proveedor("AB")               # ✗ ValidationError: min 3
validar_nombre_proveedor("A" * 101)          # ✗ ValidationError: max 100
```

---

#### 2. `validar_descripcion_proveedor(valor)`
Valida la descripción del proveedor.

**Reglas:**
- ✅ Mínimo 10 caracteres
- ✅ Máximo 5000 caracteres

**Ejemplos:**
```python
validar_descripcion_proveedor("API de pagos para procesar tarjetas de crédito")  # ✓ OK
validar_descripcion_proveedor("Muy corto")  # ✗ ValidationError: min 10
```

---

#### 3. `validar_tipo_servicio(valor)`
Valida el tipo de servicio API.

**Valores permitidos:**
- `REST` - RESTful HTTP API
- `SOAP` - Simple Object Access Protocol
- `GraphQL` - GraphQL API
- `WebSocket` - WebSocket real-time
- `gRPC` - gRPC Remote Procedure Call
- `XML-RPC` - XML Remote Procedure Call
- `OData` - Open Data Protocol

**Ejemplos:**
```python
validar_tipo_servicio("REST")      # ✓ OK
validar_tipo_servicio("GraphQL")   # ✓ OK
validar_tipo_servicio("gRPC")      # ✓ OK
validar_tipo_servicio("HTTP")      # ✗ ValidationError: no válido
```

---

#### 4. `validar_url_base(valor)`
Valida la URL base del proveedor usando `URLValidator` de Django.

**Reglas:**
- ✅ Protocolo http o https OBLIGATORIO
- ✅ Máximo 200 caracteres
- ✅ Formato URL válido

**Ejemplos:**
```python
validar_url_base("https://api.stripe.com")        # ✓ OK
validar_url_base("http://localhost:8000")         # ✓ OK
validar_url_base("https://api.paypal.com/v1")     # ✓ OK
validar_url_base("api.stripe.com")                # ✗ No protocolo
validar_url_base("ftp://example.com")             # ✗ Solo http/https
```

---

#### 5. `validar_version(valor)`
Valida el versionado semántico.

**Formato permitido:** `^v?\d+(\.\d+)*$`

**Ejemplos:**
```python
validar_version("v1.0.0")    # ✓ OK
validar_version("2.1.3")     # ✓ OK
validar_version("v3")        # ✓ OK
validar_version("1")         # ✓ OK
validar_version("v2.0")      # ✓ OK
validar_version("version-1") # ✗ Formato inválido
validar_version("1.0.0b")    # ✗ Contiene letra
```

---

#### 6. `validar_documentacion_proveedor(valor)`
Valida URL de documentación (opcional).

**Reglas:**
- ✅ Puede ser None o string vacío
- ✅ Si provisto: URL válida, máximo 200 caracteres

**Ejemplos:**
```python
validar_documentacion_proveedor("https://stripe.com/docs")  # ✓ OK
validar_documentacion_proveedor(None)                       # ✓ OK
validar_documentacion_proveedor("")                         # ✓ OK → None
validar_documentacion_proveedor("not-a-url")                # ✗ URL inválida
```

---

#### 7. `validar_tipo_auth(valor)`
Valida el tipo de autenticación.

**Valores permitidos:**
- `API_KEY` - API Key en header o query param
- `OAuth2` - OAuth 2.0 flow
- `Bearer` - Bearer token
- `Basic` - HTTP Basic Authentication
- `JWT` - JSON Web Token
- `None` - Sin autenticación
- `HMAC` - HMAC signature
- `Custom` - Autenticación personalizada

**Ejemplos:**
```python
validar_tipo_auth("API_KEY")   # ✓ OK
validar_tipo_auth("OAuth2")    # ✓ OK
validar_tipo_auth("None")      # ✓ OK
validar_tipo_auth("Token")     # ✗ No válido
```

---

#### 8. `validar_config_auth(valor)`
Valida la configuración JSON de autenticación.

**Reglas:**
- ✅ Debe ser un diccionario (no lista, no primitivo)
- ✅ No puede estar vacío
- ✅ Máximo 10KB serializado

**Ejemplos:**
```python
validar_config_auth({"header": "Authorization", "prefix": "Bearer"})  # ✓ OK
validar_config_auth({})                                               # ✗ No puede estar vacío
validar_config_auth([1, 2, 3])                                        # ✗ Debe ser dict
validar_config_auth({"key": "A" * 15000})                             # ✗ Excede 10KB
```

---

#### 9. `validar_timeout(valor)`
Valida el timeout de las llamadas.

**Reglas:**
- ✅ Mínimo: 1 segundo
- ✅ Máximo: 300 segundos (5 minutos)

**Ejemplos:**
```python
validar_timeout(30)    # ✓ OK
validar_timeout(1)     # ✓ OK (mínimo)
validar_timeout(300)   # ✓ OK (máximo)
validar_timeout(0)     # ✗ Demasiado bajo
validar_timeout(301)   # ✗ Demasiado alto
```

---

#### 10. `validar_max_reintentos(valor)`
Valida el número máximo de reintentos.

**Reglas:**
- ✅ Mínimo: 0 (sin reintentos)
- ✅ Máximo: 10

**Ejemplos:**
```python
validar_max_reintentos(3)    # ✓ OK
validar_max_reintentos(0)    # ✓ OK (sin reintentos)
validar_max_reintentos(10)   # ✓ OK (máximo)
validar_max_reintentos(-1)   # ✗ No puede ser negativo
validar_max_reintentos(11)   # ✗ Excede máximo
```

---

#### 11. `validar_activo_proveedor(valor)`
Valida el estado activo del proveedor.

**Reglas:**
- ✅ Debe ser booleano True o False

**Ejemplos:**
```python
validar_activo_proveedor(True)   # ✓ OK
validar_activo_proveedor(False)  # ✓ OK
validar_activo_proveedor(1)      # ✗ No es booleano
```

---

### EndpointsApi (11 validadores)

#### 12. `validar_nombre_endpoint(valor)`
Valida el nombre del endpoint.

**Reglas:**
- ✅ Mínimo 3 caracteres
- ✅ Máximo 100 caracteres

**Ejemplos:**
```python
validar_nombre_endpoint("Create Payment Intent")  # ✓ OK
validar_nombre_endpoint("List Customers")         # ✓ OK
validar_nombre_endpoint("OK")                     # ✗ Muy corto
```

---

#### 13. `validar_descripcion_endpoint(valor)`
Valida la descripción del endpoint.

**Reglas:**
- ✅ Mínimo 10 caracteres
- ✅ Máximo 2000 caracteres

---

#### 14. `validar_path_endpoint(valor)`
Valida el path del endpoint.

**Reglas:**
- ✅ Debe empezar con `/`
- ✅ Sin espacios
- ✅ Regex: `/[a-zA-Z0-9/_\-{}]*$`
- ✅ Soporta parámetros con llaves: `{customer_id}`

**Ejemplos:**
```python
validar_path_endpoint("/api/v1/payments")                          # ✓ OK
validar_path_endpoint("/users/{id}")                               # ✓ OK
validar_path_endpoint("/customers/{customer_id}/payments/{id}")    # ✓ OK
validar_path_endpoint("api/payments")                              # ✗ No empieza con /
validar_path_endpoint("/api /payments")                            # ✗ Contiene espacios
validar_path_endpoint("/api/payments?filter=active")               # ✗ Query params no permitidos
```

---

#### 15. `validar_metodo_http(valor)`
Valida y normaliza el método HTTP.

**Valores permitidos:**
- `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `HEAD`, `OPTIONS`

**Reglas:**
- ✅ Case-insensitive: `get` → `GET`
- ✅ Convierte a mayúsculas automáticamente

**Ejemplos:**
```python
validar_metodo_http("GET")      # ✓ OK → "GET"
validar_metodo_http("get")      # ✓ OK → "GET"
validar_metodo_http("Post")     # ✓ OK → "POST"
validar_metodo_http("CONNECT")  # ✗ No válido
```

---

#### 16. `validar_headers_endpoint(valor)`
Valida los headers HTTP.

**Reglas:**
- ✅ Debe ser un diccionario
- ✅ Keys deben ser nombres de headers HTTP válidos (alphanumeric + guiones)
- ✅ Puede estar vacío `{}`

**Ejemplos:**
```python
validar_headers_endpoint({"Content-Type": "application/json"})     # ✓ OK
validar_headers_endpoint({"Authorization": "Bearer token"})        # ✓ OK
validar_headers_endpoint({})                                       # ✓ OK
validar_headers_endpoint([1, 2, 3])                                # ✗ No es dict
validar_headers_endpoint({"Invalid Header!": "value"})             # ✗ Nombre inválido
```

---

#### 17. `validar_parametros_endpoint(valor)`
Valida los parámetros del endpoint.

**Reglas:**
- ✅ Puede ser diccionario o lista
- ✅ Validación JSON

**Ejemplos:**
```python
validar_parametros_endpoint({"customer_id": "cus_123"})       # ✓ OK
validar_parametros_endpoint(["param1", "param2"])             # ✓ OK
validar_parametros_endpoint({})                               # ✓ OK
```

---

#### 18. `validar_schema_request(valor)`
Valida el schema JSON del request.

**Reglas:**
- ✅ Puede ser None (opcional)
- ✅ Si provisto: debe ser diccionario
- ✅ Máximo 50KB serializado

**Ejemplos:**
```python
validar_schema_request({
    "type": "object",
    "properties": {"amount": {"type": "number"}}
})  # ✓ OK

validar_schema_request(None)  # ✓ OK (opcional)
validar_schema_request([])    # ✗ Debe ser dict
```

---

#### 19. `validar_schema_response(valor)`
Valida el schema JSON del response (mismo comportamiento que schema_request).

---

#### 20. `validar_cache_segundos(valor)`
Valida el tiempo de caché.

**Reglas:**
- ✅ Mínimo: 0 segundos (sin caché)
- ✅ Máximo: 86400 segundos (24 horas)

**Ejemplos:**
```python
validar_cache_segundos(0)       # ✓ OK (sin caché)
validar_cache_segundos(300)     # ✓ OK (5 minutos)
validar_cache_segundos(86400)   # ✓ OK (24 horas)
validar_cache_segundos(86401)   # ✗ Excede 24 horas
```

---

#### 21. `validar_requiere_auth_endpoint(valor)`
Valida si el endpoint requiere autenticación.

**Reglas:**
- ✅ Debe ser 0 (no requiere) o 1 (requiere)
- ✅ Acepta enteros o conversión

**Ejemplos:**
```python
validar_requiere_auth_endpoint(0)  # ✓ OK (público)
validar_requiere_auth_endpoint(1)  # ✓ OK (autenticado)
validar_requiere_auth_endpoint(2)  # ✗ Solo 0 o 1
```

---

#### 22. `validar_activo_endpoint(valor)`
Valida el estado activo del endpoint (booleano).

---

### LogsLlamadasApi (14 validadores)

#### 23. `validar_timestamp_log(valor)`
Valida el timestamp del log de llamada.

**Reglas:**
- ✅ Debe ser datetime con timezone UTC
- ✅ No puede estar más de 1 hora en el futuro (tolerancia clock skew)

**Ejemplos:**
```python
from datetime import datetime, timezone

validar_timestamp_log(datetime.now(timezone.utc))               # ✓ OK
validar_timestamp_log(datetime.now(timezone.utc) - timedelta(days=1))  # ✓ OK (pasado)
validar_timestamp_log(datetime.now(timezone.utc) + timedelta(hours=2)) # ✗ Más de 1h futuro
```

---

#### 24. `validar_metodo_log(valor)`
Valida el método HTTP del log (mismo que `validar_metodo_http`).

---

#### 25. `validar_url_log(valor)`
Valida la URL completa de la llamada.

**Reglas:**
- ✅ Mínimo 1 caracter
- ✅ Máximo 500 caracteres
- ✅ Formato URL válido

**Ejemplos:**
```python
validar_url_log("https://api.stripe.com/v1/payment_intents")  # ✓ OK
validar_url_log("http://localhost:8000/api/test")             # ✓ OK
validar_url_log("A" * 501)                                    # ✗ Muy larga
```

---

#### 26. `validar_headers_log(valor)`
Valida los headers del log (diccionario JSON).

---

#### 27. `validar_payload_log(valor)`
Valida el payload del log.

**Reglas:**
- ✅ Opcional: puede ser None o ""
- ✅ Máximo 1MB de texto

**Ejemplos:**
```python
validar_payload_log('{"amount": 1000}')  # ✓ OK
validar_payload_log(None)                # ✓ OK (opcional)
validar_payload_log("X" * (1024 * 1024 + 1))  # ✗ Excede 1MB
```

---

#### 28. `validar_status_code(valor)`
Valida el código de estado HTTP.

**Reglas:**
- ✅ Mínimo: 100
- ✅ Máximo: 599

**Ejemplos:**
```python
validar_status_code(200)  # ✓ OK
validar_status_code(404)  # ✓ OK
validar_status_code(500)  # ✓ OK
validar_status_code(99)   # ✗ Fuera de rango
validar_status_code(600)  # ✗ Fuera de rango
```

---

#### 29. `validar_tiempo_ms(valor)`
Valida el tiempo de respuesta en milisegundos.

**Reglas:**
- ✅ Mínimo: 0 ms
- ✅ Máximo: 3600000 ms (1 hora)

**Ejemplos:**
```python
validar_tiempo_ms(150)       # ✓ OK
validar_tiempo_ms(0)         # ✓ OK (mínimo)
validar_tiempo_ms(3600000)   # ✓ OK (1 hora)
validar_tiempo_ms(3600001)   # ✗ Excede 1 hora
```

---

#### 30. `validar_bytes_sent(valor)`
Valida los bytes enviados.

**Reglas:**
- ✅ Opcional: puede ser None
- ✅ Si provisto: mínimo 0, máximo 100MB (104857600 bytes)

**Ejemplos:**
```python
validar_bytes_sent(1024)       # ✓ OK
validar_bytes_sent(0)          # ✓ OK
validar_bytes_sent(None)       # ✓ OK (opcional)
validar_bytes_sent(104857600)  # ✓ OK (100MB)
validar_bytes_sent(-1)         # ✗ Negativo
```

---

#### 31. `validar_bytes_received(valor)`
Valida los bytes recibidos (mismo comportamiento que `validar_bytes_sent`).

---

#### 32. `validar_exitoso_log(valor)`
Valida el resultado de la llamada.

**Reglas:**
- ✅ Debe ser 0 (error) o 1 (éxito)

---

#### 33. `validar_error_msg_log(valor)`
Valida el mensaje de error.

**Reglas:**
- ✅ Opcional: puede ser None o ""
- ✅ Máximo 5000 caracteres

---

#### 34. `validar_intento_log(valor)`
Valida el número de intento.

**Reglas:**
- ✅ Mínimo: 1
- ✅ Máximo: 100

**Ejemplos:**
```python
validar_intento_log(1)    # ✓ OK (primer intento)
validar_intento_log(5)    # ✓ OK
validar_intento_log(100)  # ✓ OK (máximo)
validar_intento_log(0)    # ✗ Mínimo es 1
validar_intento_log(101)  # ✗ Excede máximo
```

---

#### 35. `validar_ip_origen_log(valor)`
Valida la IP de origen (opcional).

**Reglas:**
- ✅ Opcional: puede ser None o ""
- ✅ Si provisto: IPv4 o IPv6
- ✅ IPv4: `^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$`
- ✅ IPv6: `^[0-9a-fA-F:]+$`

**Ejemplos:**
```python
validar_ip_origen_log("192.168.1.1")    # ✓ OK (IPv4)
validar_ip_origen_log("127.0.0.1")      # ✓ OK (IPv4)
validar_ip_origen_log("2001:db8::1")    # ✓ OK (IPv6)
validar_ip_origen_log(None)             # ✓ OK (opcional)
validar_ip_origen_log("not-an-ip")      # ✗ Formato inválido
```

---

#### 36. `validar_contexto_log(valor)`
Valida el contexto JSON del log.

**Reglas:**
- ✅ Debe ser un diccionario
- ✅ Máximo 10KB serializado

**Ejemplos:**
```python
validar_contexto_log({"user_id": 123, "session": "abc"})  # ✓ OK
validar_contexto_log({})                                  # ✓ OK
validar_contexto_log({"data": "X" * 15000})               # ✗ Excede 10KB
```

---

### CredencialesApi (9 validadores)

#### 37. `validar_ambiente(valor)`
Valida el ambiente.

**Valores permitidos:**
- `development`
- `staging`
- `production`
- `testing`

**Reglas:**
- ✅ Case-insensitive: `PRODUCTION` → `production`

**Ejemplos:**
```python
validar_ambiente("production")   # ✓ OK → "production"
validar_ambiente("STAGING")      # ✓ OK → "staging"
validar_ambiente("qa")           # ✗ No válido
```

---

#### 38. `validar_api_key(valor)`
Valida la API key.

**Reglas:**
- ✅ Opcional: puede ser None o ""
- ✅ Si provisto: mínimo 10 caracteres, máximo 5000

**Ejemplos:**
```python
validar_api_key("sk_test_4eC39HqLyjWDarjtT1zdp7dc")  # ✓ OK
validar_api_key(None)                                # ✓ OK (opcional)
validar_api_key("short")                             # ✗ Muy corta
```

---

#### 39. `validar_secret(valor)`
Valida el secret (mismo comportamiento que `validar_api_key`).

---

#### 40. `validar_token(valor)`
Valida el token (mismo comportamiento que `validar_api_key`, JWTs pueden ser largos).

---

#### 41. `validar_configuracion_cred(valor)`
Valida la configuración adicional.

**Reglas:**
- ✅ Debe ser un diccionario
- ✅ Máximo 20KB serializado

---

#### 42. `validar_fecha_expiracion_cred(valor)`
Valida la fecha de expiración.

**Reglas:**
- ✅ Opcional: puede ser None
- ✅ Si provisto: debe ser fecha futura con tolerancia ±1 hora

**Ejemplos:**
```python
validar_fecha_expiracion_cred(datetime.now(timezone.utc) + timedelta(days=30))  # ✓ OK
validar_fecha_expiracion_cred(None)                                             # ✓ OK
validar_fecha_expiracion_cred(datetime.now(timezone.utc) - timedelta(days=1))   # ✗ Pasada
```

---

#### 43. `validar_updated_at_cred(valor)`
Valida el timestamp de actualización.

**Reglas:**
- ✅ Datetime con timezone UTC
- ✅ No más de 1 hora en el futuro

---

#### 44. `validar_activo_credencial(valor)`
Valida el estado activo (booleano).

---

### LogsWebhooks (10 validadores)

#### 45. `validar_timestamp_webhook(valor)`
Valida el timestamp del webhook (mismo que `validar_timestamp_log`).

---

#### 46. `validar_headers_webhook(valor)`
Valida los headers del webhook (diccionario JSON).

---

#### 47. `validar_payload_webhook(valor)`
Valida el payload del webhook.

**Reglas:**
- ✅ **REQUERIDO** (no opcional)
- ✅ No puede estar vacío
- ✅ Máximo 1MB

**Ejemplos:**
```python
validar_payload_webhook('{"event": "payment.created"}')  # ✓ OK
validar_payload_webhook("")                              # ✗ Requerido
```

---

#### 48. `validar_evento_tipo(valor)`
Valida el tipo de evento.

**Reglas:**
- ✅ Mínimo 3 caracteres
- ✅ Máximo 100 caracteres
- ✅ Regex: `^[a-zA-Z0-9._\-]+$`

**Ejemplos:**
```python
validar_evento_tipo("payment.created")    # ✓ OK
validar_evento_tipo("user_signup")        # ✓ OK
validar_evento_tipo("invoice.updated")    # ✓ OK
validar_evento_tipo("ok")                 # ✗ Muy corto
validar_evento_tipo("payment created!")   # ✗ Espacios y caracteres especiales
```

---

#### 49. `validar_verificacion_ok(valor)`
Valida el resultado de verificación (0 o 1).

---

#### 50. `validar_procesado_ok(valor)`
Valida el resultado de procesamiento (0 o 1).

---

#### 51. `validar_tiempo_proc_ms_webhook(valor)`
Valida el tiempo de procesamiento del webhook.

**Reglas:**
- ✅ Opcional: puede ser None
- ✅ Mínimo: 0 ms
- ✅ Máximo: 60000 ms (1 minuto)

---

#### 52. `validar_error_msg_webhook(valor)`
Valida el mensaje de error del webhook (opcional, máximo 5000 chars).

---

#### 53. `validar_ip_origen_webhook(valor)`
Valida la IP de origen del webhook.

**Reglas:**
- ✅ **REQUERIDO** (no opcional)
- ✅ IPv4 o IPv6

**Ejemplos:**
```python
validar_ip_origen_webhook("54.192.1.25")  # ✓ OK
validar_ip_origen_webhook("2001:db8::1")  # ✓ OK
validar_ip_origen_webhook(None)           # ✗ Requerido
```

---

#### 54. `validar_user_agent(valor)`
Valida el User-Agent.

**Reglas:**
- ✅ Opcional: puede ser None o ""
- ✅ Máximo 500 caracteres

---

### WebhookEndpoints (9 validadores)

#### 55. `validar_nombre_webhook(valor)`
Valida el nombre del webhook (3-100 caracteres).

---

#### 56. `validar_descripcion_webhook(valor)`
Valida la descripción del webhook (10-2000 caracteres).

---

#### 57. `validar_path_webhook(valor)`
Valida el path del webhook (mismo que `validar_path_endpoint`).

---

#### 58. `validar_requiere_verificacion(valor)`
Valida si requiere verificación (0 o 1).

---

#### 59. `validar_secret_key_webhook(valor)`
Valida el secret key del webhook.

**Reglas:**
- ✅ **MÍNIMO 32 caracteres** (requisito de seguridad)
- ✅ Máximo 255 caracteres

**Ejemplos:**
```python
validar_secret_key_webhook("whsec_" + "A" * 32)   # ✓ OK
validar_secret_key_webhook("short_secret")        # ✗ Muy corta (<32)
```

---

#### 60. `validar_header_verificacion(valor)`
Valida el nombre del header de verificación.

**Reglas:**
- ✅ Debe ser nombre de header HTTP válido
- ✅ Regex: `^[A-Za-z][A-Za-z0-9\-]*$` (debe empezar con letra)

**Ejemplos:**
```python
validar_header_verificacion("X-Stripe-Signature")  # ✓ OK
validar_header_verificacion("Authorization")       # ✓ OK
validar_header_verificacion("123-Header")          # ✗ Empieza con número
validar_header_verificacion("X Stripe Signature")  # ✗ Contiene espacios
```

---

#### 61. `validar_eventos_webhook(valor)`
Valida la lista de eventos del webhook.

**Reglas:**
- ✅ Debe ser array JSON
- ✅ No puede estar vacío
- ✅ Cada evento debe ser string de 3-100 caracteres
- ✅ Regex por evento: `^[a-zA-Z0-9._\-]+$`
- ✅ **Sin duplicados**

**Ejemplos:**
```python
validar_eventos_webhook(["payment.created", "payment.updated"])  # ✓ OK
validar_eventos_webhook([])                                      # ✗ No puede estar vacío
validar_eventos_webhook(["payment.created", "payment.created"])  # ✗ Duplicados
validar_eventos_webhook([123, "payment.created"])                # ✗ No son strings
validar_eventos_webhook(["ab"])                                  # ✗ Muy corto
```

---

#### 62. `validar_handler_func(valor)`
Valida el path de la función handler.

**Reglas:**
- ✅ Regex: `^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)+$`
- ✅ Debe ser path Python válido con al menos un punto
- ✅ Máximo 200 caracteres

**Ejemplos:**
```python
validar_handler_func("apps.api_integrations.handlers.handle_stripe_webhook")  # ✓ OK
validar_handler_func("myapp.webhooks.process_payment")                        # ✓ OK
validar_handler_func("handle_webhook")                                        # ✗ Sin puntos
validar_handler_func("123app.handler.func")                                   # ✗ Empieza con número
```

---

#### 63. `validar_activo_webhook(valor)`
Valida el estado activo del webhook (booleano).

---

#### 64. `validar_created_at_webhook(valor)`
Valida el timestamp de creación (no más de 1 hora en el futuro).

---

## 🔧 Configuración de Proveedores

### Ejemplo: Configurar Stripe

```python
from apps.api_integrations.models import ProveedoresApi
from datetime import datetime, timezone
import json

# Crear proveedor Stripe
stripe = ProveedoresApi.objects.create(
    nombre="Stripe Payments",
    descripcion="Plataforma de pagos en línea para procesamiento de tarjetas de crédito y débito",
    tipo_servicio="REST",
    url_base="https://api.stripe.com",
    version="v1",
    documentacion="https://stripe.com/docs/api",
    tipo_auth="Bearer",
    config_auth={
        "header": "Authorization",
        "prefix": "Bearer",
        "additional_headers": {
            "Stripe-Version": "2023-03-01"
        }
    },
    timeout=30,
    max_reintentos=3,
    activo=True,
    created_at=datetime.now(timezone.utc)
)
```

### Ejemplo: Configurar PayPal

```python
paypal = ProveedoresApi.objects.create(
    nombre="PayPal REST API",
    descripcion="API de PayPal para pagos, facturación y gestión de suscripciones",
    tipo_servicio="REST",
    url_base="https://api-m.paypal.com",
    version="v2",
    documentacion="https://developer.paypal.com/docs/api/overview/",
    tipo_auth="OAuth2",
    config_auth={
        "token_url": "https://api-m.paypal.com/v1/oauth2/token",
        "grant_type": "client_credentials",
        "scope": "https://uri.paypal.com/services/invoicing"
    },
    timeout=45,
    max_reintentos=2,
    activo=True,
    created_at=datetime.now(timezone.utc)
)
```

### Ejemplo: Configurar Twilio (SOAP)

```python
twilio = ProveedoresApi.objects.create(
    nombre="Twilio API",
    descripcion="API de comunicaciones para SMS, voz, video y autenticación",
    tipo_servicio="REST",
    url_base="https://api.twilio.com",
    version="2010-04-01",
    documentacion="https://www.twilio.com/docs/usage/api",
    tipo_auth="Basic",
    config_auth={
        "username_field": "AccountSid",
        "password_field": "AuthToken"
    },
    timeout=20,
    max_reintentos=3,
    activo=True,
    created_at=datetime.now(timezone.utc)
)
```

---

## 🌐 Gestión de Endpoints

### Crear Endpoint de Stripe

```python
from apps.api_integrations.models import EndpointsApi

# Endpoint: Crear Payment Intent
endpoint_create_payment = EndpointsApi.objects.create(
    nombre="Create Payment Intent",
    descripcion="Crea un nuevo payment intent para procesar un pago",
    path="/v1/payment_intents",
    metodo="POST",
    headers={
        "Content-Type": "application/json"
    },
    parametros={},
    schema_request={
        "type": "object",
        "required": ["amount", "currency"],
        "properties": {
            "amount": {
                "type": "number",
                "minimum": 50,
                "description": "Amount in cents"
            },
            "currency": {
                "type": "string",
                "enum": ["usd", "eur", "gbp", "pyg"],
                "description": "Three-letter ISO currency code"
            },
            "description": {
                "type": "string",
                "maxLength": 1000
            },
            "customer": {
                "type": "string",
                "description": "Customer ID"
            }
        }
    },
    schema_response={
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "amount": {"type": "number"},
            "currency": {"type": "string"},
            "status": {"type": "string"},
            "client_secret": {"type": "string"}
        }
    },
    cache_segundos=0,
    requiere_auth=1,
    activo=True,
    id_proveedor=stripe
)

# Endpoint: List Customers
endpoint_list_customers = EndpointsApi.objects.create(
    nombre="List Customers",
    descripcion="Lista todos los clientes con paginación",
    path="/v1/customers",
    metodo="GET",
    headers={},
    parametros={
        "limit": {"type": "integer", "default": 10, "maximum": 100},
        "starting_after": {"type": "string", "description": "Cursor para paginación"}
    },
    schema_request=None,
    schema_response={
        "type": "object",
        "properties": {
            "object": {"type": "string", "enum": ["list"]},
            "data": {
                "type": "array",
                "items": {"$ref": "#/definitions/customer"}
            },
            "has_more": {"type": "boolean"}
        }
    },
    cache_segundos=60,
    requiere_auth=1,
    activo=True,
    id_proveedor=stripe
)
```

### Realizar Llamada y Registrar Log

```python
from apps.api_integrations.models import LogsLlamadasApi
import requests
import json as json_lib

def call_api_endpoint(endpoint, payload=None, empleado=None):
    """
    Realiza llamada a un endpoint y registra el log
    
    Args:
        endpoint: Instancia de EndpointsApi
        payload: Diccionario con datos del request
        empleado: Instancia de Empleados (opcional)
        
    Returns:
        dict: Response data
    """
    proveedor = endpoint.id_proveedor
    
    # Construir URL
    url = proveedor.url_base + endpoint.path
    
    # Preparar headers
    headers = endpoint.headers.copy()
    
    # Agregar autenticación si requerida
    if endpoint.requiere_auth:
        # Obtener credenciales (ejemplo con production)
        cred = CredencialesApi.objects.get(
            id_proveedor=proveedor,
            ambiente='production',
            activo=True
        )
        
        if proveedor.tipo_auth == 'Bearer':
            headers['Authorization'] = f"Bearer {cred.token}"
        elif proveedor.tipo_auth == 'API_KEY':
            headers['Authorization'] = f"Bearer {cred.api_key}"
    
    # Realizar llamada
    start_time = datetime.now(timezone.utc)
    intento = 1
    
    try:
        response = requests.request(
            method=endpoint.metodo,
            url=url,
            headers=headers,
            json=payload,
            timeout=proveedor.timeout
        )
        
        end_time = datetime.now(timezone.utc)
        tiempo_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Registrar log exitoso
        log = LogsLlamadasApi.objects.create(
            timestamp=start_time,
            metodo=endpoint.metodo,
            url=url,
            headers_req=headers,
            payload_req=json_lib.dumps(payload) if payload else None,
            status_code=response.status_code,
            headers_res=dict(response.headers),
            payload_res=response.text,
            tiempo_ms=tiempo_ms,
            bytes_sent=len(json_lib.dumps(payload)) if payload else 0,
            bytes_received=len(response.content),
            exitoso=1 if 200 <= response.status_code < 300 else 0,
            error_msg=None,
            intento=intento,
            ip_origen=None,
            contexto={
                "proveedor": proveedor.nombre,
                "endpoint": endpoint.nombre
            },
            id_endpoint=endpoint,
            id_empleado=empleado
        )
        
        return response.json()
        
    except Exception as e:
        end_time = datetime.now(timezone.utc)
        tiempo_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Registrar log con error
        log = LogsLlamadasApi.objects.create(
            timestamp=start_time,
            metodo=endpoint.metodo,
            url=url,
            headers_req=headers,
            payload_req=json_lib.dumps(payload) if payload else None,
            status_code=0,
            headers_res={},
            payload_res=None,
            tiempo_ms=tiempo_ms,
            bytes_sent=len(json_lib.dumps(payload)) if payload else 0,
            bytes_received=0,
            exitoso=0,
            error_msg=str(e),
            intento=intento,
            ip_origen=None,
            contexto={
                "proveedor": proveedor.nombre,
                "endpoint": endpoint.nombre,
                "exception_type": type(e).__name__
            },
            id_endpoint=endpoint,
            id_empleado=empleado
        )
        
        raise

# Uso
stripe_endpoint = EndpointsApi.objects.get(nombre="Create Payment Intent")
response = call_api_endpoint(
    endpoint=stripe_endpoint,
    payload={
        "amount": 100000,  # 1000.00 PYG
        "currency": "pyg",
        "description": "Pago de almuerzo"
    }
)
```

---

## 🔐 Sistema de Credenciales

### Crear Credenciales por Ambiente

```python
from apps.api_integrations.models import CredencialesApi
from datetime import datetime, timedelta, timezone

# Credenciales Development
cred_dev = CredencialesApi.objects.create(
    ambiente="development",
    api_key="sk_test_4eC39HqLyjWDarjtT1zdp7dc",
    secret=None,
    token="pk_test_TYooMQauvdEDq54NiTphI7jx",
    configuracion={
        "webhook_secret": "whsec_dev_abc123",
        "endpoints_base": "https://api.stripe.com"
    },
    fecha_expiracion=None,
    updated_at=datetime.now(timezone.utc),
    activo=True,
    id_proveedor=stripe
)

# Credenciales Production
cred_prod = CredencialesApi.objects.create(
    ambiente="production",
    api_key="sk_live_XXXXXXXXXXXXXXXXXXXX",
    secret=None,
    token="pk_live_YYYYYYYYYYYYYYYYYYYY",
    configuracion={
        "webhook_secret": "whsec_prod_xyz789",
        "endpoints_base": "https://api.stripe.com",
        "rate_limit": {
            "requests_per_second": 100,
            "burst": 25
        }
    },
    fecha_expiracion=datetime.now(timezone.utc) + timedelta(days=365),
    updated_at=datetime.now(timezone.utc),
    activo=True,
    id_proveedor=stripe
)

# UNIQUE together: no puede haber dos credenciales para mismo proveedor+ambiente
# Esto lanzaría IntegrityError:
# cred_prod_duplicada = CredencialesApi.objects.create(
#     ambiente="production",
#     id_proveedor=stripe,
#     ...
# )  # ✗ IntegrityError: duplicate key
```

### Obtener Credenciales Activas

```python
def get_credenciales(proveedor, ambiente):
    """
    Obtiene credenciales activas para un proveedor y ambiente
    
    Args:
        proveedor: Instancia de ProveedoresApi o PK
        ambiente: 'development', 'staging', 'production', 'testing'
        
    Returns:
        CredencialesApi o None
    """
    try:
        return CredencialesApi.objects.get(
            id_proveedor=proveedor,
            ambiente=ambiente.lower(),
            activo=True
        )
    except CredencialesApi.DoesNotExist:
        return None

# Uso
creds = get_credenciales(stripe, 'production')
if creds:
    api_key = creds.api_key
    # Usar credenciales...
```

### Rotar Credenciales

```python
def rotar_credenciales(credencial, nueva_api_key, nuevo_token):
    """
    Rota las credenciales de un proveedor
    
    Args:
        credencial: Instancia de CredencialesApi
        nueva_api_key: Nueva API key
        nuevo_token: Nuevo token
    """
    credencial.api_key = nueva_api_key
    credencial.token = nuevo_token
    credencial.updated_at = datetime.now(timezone.utc)
    credencial.save()
    
    print(f"Credenciales rotadas para {credencial.id_proveedor.nombre} - {credencial.ambiente}")

# Uso
rotar_credenciales(
    credencial=cred_prod,
    nueva_api_key="sk_live_NEWKEYXXXXXXXXXX",
    nuevo_token="pk_live_NEWTOKENYYYYYYY"
)
```

---

## 🪝 Webhooks

### Configurar Webhook Endpoint

```python
from apps.api_integrations.models import WebhookEndpoints

webhook_stripe = WebhookEndpoints.objects.create(
    nombre="Stripe Payment Events",
    descripcion="Webhook para eventos de pagos de Stripe (creación, actualización, éxito, fallo)",
    path="/webhooks/stripe",
    requiere_verificacion=1,
    secret_key="whsec_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",  # 32+ chars
    header_verificacion="X-Stripe-Signature",
    eventos=[
        "payment_intent.created",
        "payment_intent.succeeded",
        "payment_intent.payment_failed",
        "charge.succeeded",
        "charge.refunded",
        "invoice.created",
        "invoice.paid",
        "customer.created",
        "customer.updated"
    ],
    handler_func="apps.api_integrations.handlers.handle_stripe_webhook",
    activo=True,
    created_at=datetime.now(timezone.utc),
    id_proveedor=stripe
)
```

### Implementar Handler

```python
# apps/api_integrations/handlers.py
import hmac
import hashlib
import json
from apps.api_integrations.models import LogsWebhooks

def handle_stripe_webhook(request):
    """
    Handler para webhooks de Stripe
    
    Verifica la firma HMAC y procesa el evento
    
    Args:
        request: HttpRequest de Django
        
    Returns:
        JsonResponse
    """
    from django.http import JsonResponse
    
    # Obtener webhook config
    webhook = WebhookEndpoints.objects.get(
        path="/webhooks/stripe",
        activo=True
    )
    
    payload = request.body.decode('utf-8')
    sig_header = request.META.get('HTTP_X_STRIPE_SIGNATURE')
    timestamp = request.META.get('HTTP_X_STRIPE_TIMESTAMP')
    
    # Verificar firma HMAC
    verificacion_ok = 0
    if webhook.requiere_verificacion:
        expected_sig = hmac.new(
            webhook.secret_key.encode('utf-8'),
            f"{timestamp}.{payload}".encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Stripe envía firma como "t=timestamp,v1=signature"
        signatures = {}
        for pair in sig_header.split(','):
            key, value = pair.split('=')
            signatures[key] = value
        
        if signatures.get('v1') == expected_sig:
            verificacion_ok = 1
    
    # Parse payload
    start_process = datetime.now(timezone.utc)
    procesado_ok = 0
    error_msg = None
    
    try:
        data = json.loads(payload)
        evento_tipo = data.get('type')
        
        # Procesar según tipo de evento
        if evento_tipo == 'payment_intent.succeeded':
            payment_id = data['data']['object']['id']
            amount = data['data']['object']['amount']
            
            # ... lógica de negocio ...
            # Actualizar estado de pago en base de datos
            # Enviar notificación al cliente
            # etc.
            
            procesado_ok = 1
            
        elif evento_tipo == 'invoice.paid':
            invoice_id = data['data']['object']['id']
            
            # ... procesar factura pagada ...
            
            procesado_ok = 1
            
        # ... otros eventos ...
        
        else:
            error_msg = f"Evento no manejado: {evento_tipo}"
            
    except Exception as e:
        error_msg = str(e)
    
    end_process = datetime.now(timezone.utc)
    tiempo_proc_ms = int((end_process - start_process).total_seconds() * 1000)
    
    # Registrar log del webhook
    log = LogsWebhooks.objects.create(
        timestamp=datetime.now(timezone.utc),
        headers=dict(request.META),
        payload=payload,
        evento_tipo=data.get('type', 'unknown'),
        verificacion_ok=verificacion_ok,
        procesado_ok=procesado_ok,
        tiempo_proc_ms=tiempo_proc_ms,
        error_msg=error_msg,
        ip_origen=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        id_webhook=webhook
    )
    
    if procesado_ok:
        return JsonResponse({"status": "success"}, status=200)
    else:
        return JsonResponse({"status": "error", "message": error_msg}, status=400)
```

### Configurar URL

```python
# apps/api_integrations/urls.py
from django.urls import path
from . import handlers

urlpatterns = [
    path('webhooks/stripe', handlers.handle_stripe_webhook, name='webhook_stripe'),
    path('webhooks/paypal', handlers.handle_paypal_webhook, name='webhook_paypal'),
    # ... más webhooks ...
]
```

---

## 📊 Logging y Monitoreo

### Consultas de Logs de Llamadas

```python
from apps.api_integrations.models import LogsLlamadasApi
from datetime import datetime, timedelta, timezone

# Logs exitosos de hoy
logs_exitosos_hoy = LogsLlamadasApi.objects.filter(
    timestamp__date=datetime.now().date(),
    exitoso=1
)

# Logs con errores 4xx (errores del cliente)
logs_4xx = LogsLlamadasApi.objects.filter(
    status_code__gte=400,
    status_code__lt=500
).order_by('-timestamp')

# Logs con errores 5xx (errores del servidor)
logs_5xx = LogsLlamadasApi.objects.filter(
    status_code__gte=500
).order_by('-timestamp')

# Tiempos de respuesta promedio por endpoint
from django.db.models import Avg, Max, Min, Count

stats = LogsLlamadasApi.objects.filter(
    id_endpoint__isnull=False,
    exitoso=1
).values('id_endpoint__nombre').annotate(
    promedio_ms=Avg('tiempo_ms'),
    maximo_ms=Max('tiempo_ms'),
    minimo_ms=Min('tiempo_ms'),
    total_llamadas=Count('id_log')
)

for stat in stats:
    print(f"{stat['id_endpoint__nombre']}: {stat['promedio_ms']:.2f}ms promedio, {stat['total_llamadas']} llamadas")

# Logs de última semana con reintentos
logs_reintentos = LogsLlamadasApi.objects.filter(
    timestamp__gte=datetime.now(timezone.utc) - timedelta(days=7),
    intento__gt=1
).order_by('-intento', '-timestamp')

# IPs que más llaman
from django.db.models import Count
ips_mas_activas = LogsLlamadasApi.objects.filter(
    ip_origen__isnull=False
).values('ip_origen').annotate(
    total=Count('id_log')
).order_by('-total')[:10]
```

### Consultas de Logs de Webhooks

```python
from apps.api_integrations.models import LogsWebhooks

# Webhooks con verificación fallida
webhooks_no_verificados = LogsWebhooks.objects.filter(
    verificacion_ok=0
).order_by('-timestamp')

# Webhooks procesados con error
webhooks_error = LogsWebhooks.objects.filter(
    procesado_ok=0
).order_by('-timestamp')

# Eventos por tipo (últimos 30 días)
eventos_stats = LogsWebhooks.objects.filter(
    timestamp__gte=datetime.now(timezone.utc) - timedelta(days=30)
).values('evento_tipo').annotate(
    total=Count('id_log'),
    exitosos=Count('id_log', filter=models.Q(procesado_ok=1)),
    fallidos=Count('id_log', filter=models.Q(procesado_ok=0)),
    promedio_tiempo=Avg('tiempo_proc_ms')
).order_by('-total')

# IPs sospechosas (muchas verificaciones fallidas)
ips_sospechosas = LogsWebhooks.objects.filter(
    verificacion_ok=0,
    timestamp__gte=datetime.now(timezone.utc) - timedelta(hours=24)
).values('ip_origen').annotate(
    total_fallos=Count('id_log')
).filter(total_fallos__gte=5).order_by('-total_fallos')
```

### Dashboard de Métricas

```python
def get_api_metrics(proveedor, desde, hasta):
    """
    Obtiene métricas de un proveedor en un rango de fechas
    
    Args:
        proveedor: Instancia de ProveedoresApi
        desde: datetime inicio
        hasta: datetime fin
        
    Returns:
        dict: Métricas
    """
    logs = LogsLlamadasApi.objects.filter(
        id_endpoint__id_proveedor=proveedor,
        timestamp__gte=desde,
        timestamp__lte=hasta
    )
    
    total = logs.count()
    exitosos = logs.filter(exitoso=1).count()
    fallidos = logs.filter(exitoso=0).count()
    
    promedio_tiempo = logs.filter(exitoso=1).aggregate(Avg('tiempo_ms'))['tiempo_ms__avg'] or 0
    max_tiempo = logs.filter(exitoso=1).aggregate(Max('tiempo_ms'))['tiempo_ms__max'] or 0
    
    status_codes = logs.values('status_code').annotate(
        total=Count('id_log')
    ).order_by('-total')
    
    return {
        'total_llamadas': total,
        'exitosas': exitosos,
        'fallidas': fallidos,
        'tasa_exito': (exitosos / total * 100) if total > 0 else 0,
        'promedio_tiempo_ms': round(promedio_tiempo, 2),
        'max_tiempo_ms': max_tiempo,
        'status_codes': list(status_codes),
        'periodo': {
            'desde': desde.isoformat(),
            'hasta': hasta.isoformat()
        }
    }

# Uso
metricas_stripe = get_api_metrics(
    proveedor=stripe,
    desde=datetime.now(timezone.utc) - timedelta(days=7),
    hasta=datetime.now(timezone.utc)
)

print(f"Tasa de éxito: {metricas_stripe['tasa_exito']:.2f}%")
print(f"Tiempo promedio: {metricas_stripe['promedio_tiempo_ms']}ms")
```

---

## 📚 Casos de Uso

### Caso 1: Integración con Stripe completa

```python
# 1. Configurar proveedor
stripe = ProveedoresApi.objects.create(
    nombre="Stripe Payments",
    tipo_servicio="REST",
    url_base="https://api.stripe.com",
    version="v1",
    tipo_auth="Bearer",
    config_auth={"header": "Authorization", "prefix": "Bearer"},
    timeout=30,
    max_reintentos=3,
    activo=True,
    created_at=datetime.now(timezone.utc)
)

# 2. Crear credenciales
cred_prod = CredencialesApi.objects.create(
    ambiente="production",
    token="sk_live_...",
    configuracion={"webhook_secret": "whsec_..."},
    activo=True,
    id_proveedor=stripe
)

# 3. Crear endpoint
endpoint_payment = EndpointsApi.objects.create(
    nombre="Create Payment Intent",
    path="/v1/payment_intents",
    metodo="POST",
    requiere_auth=1,
    activo=True,
    id_proveedor=stripe
)

# 4. Configurar webhook
webhook_stripe = WebhookEndpoints.objects.create(
    nombre="Stripe Payment Events",
    path="/webhooks/stripe",
    requiere_verificacion=1,
    secret_key="whsec_a1b2c3...",  # 32+ chars
    header_verificacion="X-Stripe-Signature",
    eventos=["payment_intent.succeeded", "charge.refunded"],
    handler_func="apps.api_integrations.handlers.handle_stripe_webhook",
    activo=True,
    id_proveedor=stripe
)

# 5. Realizar llamada (automáticamente crea log)
response = call_api_endpoint(
    endpoint=endpoint_payment,
    payload={"amount": 100000, "currency": "pyg"}
)

# 6. Ver logs
logs = LogsLlamadasApi.objects.filter(id_endpoint=endpoint_payment)
```

### Caso 2: Monitoreo de salud de API

```python
def check_api_health(proveedor):
    """
    Verifica la salud de un proveedor API
    
    Returns:
        dict: Status de salud
    """
    # Últimas 100 llamadas
    recent_logs = LogsLlamadasApi.objects.filter(
        id_endpoint__id_proveedor=proveedor
    ).order_by('-timestamp')[:100]
    
    if not recent_logs.exists():
        return {"status": "unknown", "message": "No hay datos"}
    
    total = recent_logs.count()
    exitosos = recent_logs.filter(exitoso=1).count()
    tasa_exito = (exitosos / total * 100)
    
    promedio_tiempo = recent_logs.filter(exitoso=1).aggregate(
        Avg('tiempo_ms')
    )['tiempo_ms__avg'] or 0
    
    # Definir salud
    if tasa_exito >= 95 and promedio_tiempo < 1000:
        status = "healthy"
        color = "green"
    elif tasa_exito >= 80:
        status = "degraded"
        color = "yellow"
    else:
        status = "critical"
        color = "red"
    
    return {
        "status": status,
        "color": color,
        "tasa_exito": round(tasa_exito, 2),
        "promedio_tiempo_ms": round(promedio_tiempo, 2),
        "total_llamadas": total
    }

# Uso
health = check_api_health(stripe)
print(f"Status: {health['status']} - {health['tasa_exito']}% éxito")
```

### Caso 3: Sistema de reintentos

```python
def call_with_retry(endpoint, payload, max_intentos=None):
    """
    Llama a un endpoint con sistema de reintentos
    
    Args:
        endpoint: EndpointsApi
        payload: dict
        max_intentos: int (None usa el del proveedor)
        
    Returns:
        Response data
    """
    proveedor = endpoint.id_proveedor
    max_intentos = max_intentos or proveedor.max_reintentos
    
    for intento in range(1, max_intentos + 2):  # +1 para intento inicial
        try:
            print(f"Intento {intento}/{max_intentos + 1}...")
            
            response = call_api_endpoint(endpoint, payload)
            
            print(f"✓ Éxito en intento {intento}")
            return response
            
        except requests.exceptions.RequestException as e:
            if intento <= max_intentos:
                # Esperar antes de reintentar (exponential backoff)
                wait_time = 2 ** intento  # 2, 4, 8, 16 segundos
                print(f"✗ Error: {e}. Reintentando en {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"✗ Fallo después de {intento} intentos")
                raise

# Uso
try:
    response = call_with_retry(endpoint_payment, {"amount": 100000})
except Exception as e:
    print(f"Error final: {e}")
```

---

## 🧪 Tests

### Resumen de Tests

```bash
$ python manage.py test apps.api_integrations.tests_validators

Found 180 test(s).
System check identified 1 issue (0 silenced).
................................................................................
....................................................................................................
----------------------------------------------------------------------
Ran 180 tests in 0.325s

OK
```

**Cobertura:**
- ✅ 48 validadores
- ✅ 180 tests (promedio ~3.75 tests por validador)
- ✅ Tests de valores válidos
- ✅ Tests de ValidationError
- ✅ Tests de edge cases
- ✅ Tests de valores opcionales
- ✅ 100% éxito

### Estructura de Tests

```
tests_validators.py (180 tests)
├── ProveedoresApi (36 tests)
│   ├── ValidarNombreProveedorTest (3)
│   ├── ValidarDescripcionProveedorTest (3)
│   ├── ValidarTipoServicioTest (3)
│   ├── ValidarUrlBaseTest (4)
│   ├── ValidarVersionTest (3)
│   ├── ValidarDocumentacionProveedorTest (3)
│   ├── ValidarTipoAuthTest (3)
│   ├── ValidarConfigAuthTest (4)
│   ├── ValidarTimeoutTest (3)
│   ├── ValidarMaxReintentosTest (3)
│   └── ValidarActivoProveedorTest (2)
├── EndpointsApi (33 tests)
│   ├── ValidarNombreEndpointTest (3)
│   ├── ValidarDescripcionEndpointTest (3)
│   ├── ValidarPathEndpointTest (4)
│   ├── ValidarMetodoHttpTest (2)
│   ├── ValidarHeadersEndpointTest (4)
│   ├── ValidarParametrosEndpointTest (4)
│   ├── ValidarSchemaRequestTest (4)
│   ├── ValidarSchemaResponseTest (2)
│   ├── ValidarCacheSegundosTest (3)
│   ├── ValidarRequiereAuthEndpointTest (2)
│   └── ValidarActivoEndpointTest (2)
├── LogsLlamadasApi (42 tests)
│   ├── ValidarTimestampLogTest (3)
│   ├── ValidarMetodoLogTest (2)
│   ├── ValidarUrlLogTest (3)
│   ├── ValidarHeadersLogTest (3)
│   ├── ValidarPayloadLogTest (3)
│   ├── ValidarStatusCodeTest (3)
│   ├── ValidarTiempoMsTest (3)
│   ├── ValidarBytesSentTest (4)
│   ├── ValidarBytesReceivedTest (2)
│   ├── ValidarExitosoLogTest (2)
│   ├── ValidarErrorMsgLogTest (3)
│   ├── ValidarIntentoLogTest (3)
│   ├── ValidarIpOrigenLogTest (4)
│   └── ValidarContextoLogTest (4)
├── CredencialesApi (27 tests)
│   ├── ValidarAmbienteTest (2)
│   ├── ValidarApiKeyTest (4)
│   ├── ValidarSecretTest (2)
│   ├── ValidarTokenTest (2)
│   ├── ValidarConfiguracionCredTest (4)
│   ├── ValidarFechaExpiracionCredTest (3)
│   ├── ValidarUpdatedAtCredTest (2)
│   └── ValidarActivoCredencialTest (2)
├── LogsWebhooks (30 tests)
│   ├── ValidarTimestampWebhookTest (2)
│   ├── ValidarHeadersWebhookTest (3)
│   ├── ValidarPayloadWebhookTest (3)
│   ├── ValidarEventoTipoTest (3)
│   ├── ValidarVerificacionOkTest (2)
│   ├── ValidarProcesadoOkTest (2)
│   ├── ValidarTiempoProcMsWebhookTest (3)
│   ├── ValidarErrorMsgWebhookTest (3)
│   ├── ValidarIpOrigenWebhookTest (2)
│   └── ValidarUserAgentTest (3)
└── WebhookEndpoints (27 tests)
    ├── ValidarNombreWebhookTest (2)
    ├── ValidarDescripcionWebhookTest (2)
    ├── ValidarPathWebhookTest (2)
    ├── ValidarRequiereVerificacionTest (2)
    ├── ValidarSecretKeyWebhookTest (3)
    ├── ValidarHeaderVerificacionTest (3)
    ├── ValidarEventosWebhookTest (5)
    ├── ValidarHandlerFuncTest (4)
    ├── ValidarActivoWebhookTest (2)
    └── ValidarCreatedAtWebhookTest (2)
```

### Tests Destacados

#### Test de URL con protocolo obligatorio
```python
class ValidarUrlBaseTest(TestCase):
    def test_url_valida_https(self):
        url = "https://api.stripe.com"
        self.assertEqual(validar_url_base(url), url)
    
    def test_url_sin_protocolo(self):
        # Debe fallar sin http/https
        with self.assertRaises(ValidationError):
            validar_url_base("api.stripe.com")
```

#### Test de versionado semántico
```python
class ValidarVersionTest(TestCase):
    def test_version_semantica(self):
        versiones_validas = ["v1.0.0", "2.1.3", "v3", "1"]
        for version in versiones_validas:
            self.assertEqual(validar_version(version), version)
    
    def test_version_invalida(self):
        with self.assertRaises(ValidationError):
            validar_version("version-1.0")
```

#### Test de IP origen (IPv4 e IPv6)
```python
class ValidarIpOrigenLogTest(TestCase):
    def test_ipv4_valida(self):
        ips = ["192.168.1.1", "127.0.0.1", "8.8.8.8"]
        for ip in ips:
            self.assertEqual(validar_ip_origen_log(ip), ip)
    
    def test_ipv6_valida(self):
        ip = "2001:db8::1"
        self.assertEqual(validar_ip_origen_log(ip), ip)
```

#### Test de eventos webhook sin duplicados
```python
class ValidarEventosWebhookTest(TestCase):
    def test_eventos_validos(self):
        eventos = ["payment.created", "payment.updated"]
        self.assertEqual(validar_eventos_webhook(eventos), eventos)
    
    def test_eventos_duplicados(self):
        # No se permiten duplicados
        with self.assertRaises(ValidationError):
            validar_eventos_webhook(["payment.created", "payment.created"])

```

---

## 📖 API Reference

### Modelos

| Modelo | Tabla DB | Descripción |
|--------|----------|-------------|
| `ProveedoresApi` | `proveedores_api` | Proveedores de servicios API |
| `EndpointsApi` | `endpoints_api` | Endpoints de cada proveedor |
| `LogsLlamadasApi` | `logs_llamadas_api` | Logs de llamadas API |
| `CredencialesApi` | `credenciales_api` | Credenciales por ambiente |
| `LogsWebhooks` | `logs_webhooks` | Logs de webhooks recibidos |
| `WebhookEndpoints` | `webhook_endpoints` | Configuración de webhooks |

### Validadores por Categoría

**ProveedoresApi (12):**
- `validar_nombre_proveedor`, `validar_descripcion_proveedor`, `validar_tipo_servicio`
- `validar_url_base`, `validar_version`, `validar_documentacion_proveedor`
- `validar_tipo_auth`, `validar_config_auth`
- `validar_timeout`, `validar_max_reintentos`, `validar_activo_proveedor`

**EndpointsApi (11):**
- `validar_nombre_endpoint`, `validar_descripcion_endpoint`, `validar_path_endpoint`
- `validar_metodo_http`, `validar_headers_endpoint`, `validar_parametros_endpoint`
- `validar_schema_request`, `validar_schema_response`
- `validar_cache_segundos`, `validar_requiere_auth_endpoint`, `validar_activo_endpoint`

**LogsLlamadasApi (14):**
- `validar_timestamp_log`, `validar_metodo_log`, `validar_url_log`
- `validar_headers_log`, `validar_payload_log`, `validar_status_code`
- `validar_tiempo_ms`, `validar_bytes_sent`, `validar_bytes_received`
- `validar_exitoso_log`, `validar_error_msg_log`, `validar_intento_log`
- `validar_ip_origen_log`, `validar_contexto_log`

**CredencialesApi (9):**
- `validar_ambiente`, `validar_api_key`, `validar_secret`, `validar_token`
- `validar_configuracion_cred`, `validar_fecha_expiracion_cred`
- `validar_updated_at_cred`, `validar_activo_credencial`

**LogsWebhooks (10):**
- `validar_timestamp_webhook`, `validar_headers_webhook`, `validar_payload_webhook`
- `validar_evento_tipo`, `validar_verificacion_ok`, `validar_procesado_ok`
- `validar_tiempo_proc_ms_webhook`, `validar_error_msg_webhook`
- `validar_ip_origen_webhook`, `validar_user_agent`

**WebhookEndpoints (9):**
- `validar_nombre_webhook`, `validar_descripcion_webhook`, `validar_path_webhook`
- `validar_requiere_verificacion`, `validar_secret_key_webhook`
- `validar_header_verificacion`, `validar_eventos_webhook`, `validar_handler_func`
- `validar_activo_webhook`, `validar_created_at_webhook`

### Constraints

**UNIQUE Together:**
- `CredencialesApi`: `(id_proveedor, ambiente)`
- `WebhookEndpoints`: `(id_proveedor, path)`

**ForeignKey Relations:**
- `EndpointsApi` → `ProveedoresApi`
- `LogsLlamadasApi` → `EndpointsApi`, `Empleados`
- `CredencialesApi` → `ProveedoresApi`
- `LogsWebhooks` → `WebhookEndpoints`
- `WebhookEndpoints` → `ProveedoresApi`

---

## 🎓 Mejores Prácticas

### 1. Seguridad de Credenciales
```python
# ✓ BUENO: Usar variables de entorno
import os
api_key = os.getenv('STRIPE_SECRET_KEY')

# ✗ MALO: Hardcodear credenciales
api_key = "sk_live_XXXXXXXXXX"  # ¡No hacer esto!
```

### 2. Manejo de Errores
```python
# ✓ BUENO: Capturar y loggear errores específicos
try:
    response = call_api_endpoint(endpoint, payload)
except requests.exceptions.Timeout:
    # Log específico de timeout
    pass
except requests.exceptions.RequestException as e:
    # Log general de error de request
    pass

# ✗ MALO: Catch genérico sin loggear
try:
    response = call_api_endpoint(endpoint, payload)
except:
    pass
```

### 3. Validación de Schemas
```python
# ✓ BUENO: Validar payload contra schema antes de enviar
import jsonschema

schema = endpoint.schema_request
jsonschema.validate(payload, schema)

# Luego enviar
response = call_api_endpoint(endpoint, payload)
```

### 4. Rate Limiting
```python
# ✓ BUENO: Implementar rate limiting
from time import sleep
from django.core.cache import cache

def rate_limited_call(endpoint, payload):
    cache_key = f"api_call_{endpoint.id_endpoint}"
    
    # Verificar últimas llamadas
    calls = cache.get(cache_key, 0)
    if calls >= 100:  # Límite: 100 llamadas/minuto
        sleep(60)
        cache.delete(cache_key)
    
    response = call_api_endpoint(endpoint, payload)
    cache.set(cache_key, calls + 1, 60)
    
    return response
```

### 5. Webhooks Idempotentes
```python
# ✓ BUENO: Verificar duplicados usando ID del evento
def handle_webhook_idempotent(evento_id, evento_tipo, payload):
    # Verificar si ya procesamos este evento
    if LogsWebhooks.objects.filter(
        evento_tipo=evento_tipo,
        payload__contains=evento_id
    ).exists():
        return {"status": "already_processed"}
    
    # Procesar evento...
    # Registrar log...
```

---

## 📝 Changelog

### Versión 1.0.0 (2024)
- ✅ 6 modelos implementados
- ✅ 48 validadores creados
- ✅ 180 tests (100% PASS)
- ✅ Admin con 6 modelos registrados
- ✅ Soporte para 7 tipos de servicios API
- ✅ 8 métodos de autenticación
- ✅ Sistema de webhooks con verificación HMAC
- ✅ Logging completo de requests/responses
- ✅ Multi-ambiente (development, staging, production, testing)
- ✅ Validación IPv4 e IPv6
- ✅ Schemas JSON con límites de tamaño
- ✅ Sistema de reintentos configurable

---

## 🤝 Contribuciones

Para contribuir al módulo api_integrations:

1. Seguir los patrones de validación existentes
2. Agregar tests para nuevas funcionalidades
3. Documentar cambios en el README
4. Validar que todos los tests pasen (100%)
5. Usar los validadores en los serializers/forms

---

## 📞 Soporte

Para preguntas o issues relacionados con API Integrations:
- Revisar logs en el admin de Django
- Consultar LogsLlamadasApi para debugging de llamadas
- Consultar LogsWebhooks para debugging de webhooks
- Verificar credenciales activas por ambiente
- Validar configuración de proveedores

---

**README creado el 2024 - Módulo API Integrations - Sistema Cantina Tita**
**Versión 1.0.0 - 180 tests OK - 48 validadores - 6 modelos**
