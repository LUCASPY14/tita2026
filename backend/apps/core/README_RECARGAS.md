# Módulo de Recarga de Saldo Prepago - CANTINA_TITA

> ⚠️ **Documento desactualizado — no refleja la implementación actual.** Este
> README describe un diseño temprano (modelo `CargasSaldo`, `RecargaService`,
> endpoints `/api/v1/cargas-saldo/caja/`, `/transferencia/referencia/`,
> `/transferencia/validar/`, `/{id}/aprobar/`, webhook con firma HMAC-SHA256)
> que no es lo que terminó implementado. La integración Bancard real vive en
> [`bancard_service.py`](bancard_service.py) y [`bancard_views.py`](bancard_views.py)
> (webhook en `/api/v1/core/bancard/confirmar/`, token MD5 propio de Bancard —
> no HMAC), y las cargas manuales de caja/transferencia usan el modelo
> `CargaSaldo` (singular) vía `CargaSaldoViewSet` en [`views.py`](views.py),
> registrado en `/api/v1/core/cargas-saldo/`. Para el comportamiento real,
> leer el código directamente en vez de este documento.

## 📋 Índice
- [Descripción General](#descripción-general)
- [Actores y Canales](#actores-y-canales)
- [Reglas de Negocio](#reglas-de-negocio)
- [Flujos de Trabajo](#flujos-de-trabajo)
- [API Endpoints](#api-endpoints)
- [Modelos y Campos](#modelos-y-campos)
- [Servicios](#servicios)
- [Estados de Recarga](#estados-de-recarga)
- [Seguridad e Idempotencia](#seguridad-e-idempotencia)
- [Ejemplos de Uso](#ejemplos-de-uso)

---

## 🎯 Descripción General

El módulo de **Recarga de Saldo Prepago** permite acreditar saldo en las tarjetas prepago de los hijos para consumo en:
- **Cantina**: Compra de productos
- **Almuerzos**: Registro de consumo de almuerzo (independiente pero usa misma tarjeta)

### Garantías del Sistema
✅ **Integridad Financiera**: Cada operación es atómica y consistente  
✅ **Trazabilidad Total**: Auditoría completa de cada transacción  
✅ **Cumplimiento Fiscal**: Generación automática de facturas  
✅ **Seguridad**: Validación rigurosa, idempotencia, doble autorización

---

## 👥 Actores y Canales

| Actor | Canal | Descripción |
|-------|-------|-------------|
| **Padre/Representante** | Portal Web / App Móvil | Inicia recargas vía pasarela Bancard |
| **Padre/Representante** | Transferencia Bancaria | Realiza transferencia y presenta comprobante |
| **Cajero Autorizado** | Sistema de Caja | Registra recargas en efectivo o valida transferencias |
| **Supervisor** | Sistema de Caja | Aprueba recargas de monto elevado (doble validación) |
| **Sistema Core** | Backend | Procesa solicitudes, valida reglas, orquesta pagos |
| **Pasarela Bancard** | API Externa | Procesa pagos con tarjeta (webhook) |

---

## 📜 Reglas de Negocio

### 1. Generación de Factura
- ✅ Toda recarga constituye **venta de saldo electrónico**
- ✅ El monto facturado = **saldo acreditado** (NO incluye comisión)
- ❌ Las compras con saldo prepago **NO generan factura** (solo movimientos internos)

### 2. Cálculo de Comisiones

| Método de Pago | Comisión | Ejemplo (₲100.000 de saldo) |
|----------------|----------|------------------------------|
| **Efectivo** | 0% | Total cobrado: ₲100.000 |
| **Bancard** | 3.4% | Comisión: ₲3.400<br>Total cobrado: ₲103.400<br>Saldo acreditado: ₲100.000<br>Factura emitida: ₲100.000 |
| **Tarjeta POS** | 3.4% | (Igual que Bancard) |
| **Transferencia** | 0% | Total cobrado: ₲100.000 |

**Regla**: La comisión se traslada al cliente, NO incrementa el valor facturado.

### 3. Doble Validación
- Si monto > **₲500.000** (configurable): Requiere aprobación de supervisor
- Estado: `validacion_pendiente` → `completada` (después de aprobación)

---

## 🔄 Flujos de Trabajo

### Flujo 1: Recarga en Caja (Efectivo/POS)

```
1. Cajero autenticado selecciona hijo y monto
2. Sistema calcula total con comisión (si aplica)
3. POST /api/v1/cargas-saldo/caja/
   {
     "hijo_id": 123,
     "monto": 100000,
     "metodo_pago": "efectivo",
     "referencia": "CAJA-001"
   }
4. Backend:
   - Crea recarga con estado COMPLETADA
   - Acredita saldo inmediatamente
   - Genera factura fiscal
5. Sistema muestra comprobante
```

**Resultado**:
- ✅ Saldo acreditado instantáneamente
- ✅ Factura generada
- ✅ Registrado en historial

---

### Flujo 2: Transferencia con Código de Referencia (Recomendado)

**Paso A: Generar Referencia**
```
POST /api/v1/cargas-saldo/transferencia/referencia/
{
  "hijo_id": 123,
  "monto": 100000
}

Response:
{
  "codigo_referencia": "REF-20260302-00001",
  "monto_transferir": 100000,
  "datos_bancarios": {
    "banco": "Banco Nacional de Fomento",
    "titular": "CANTINA TITA S.A.",
    "cuenta": "1234567890",
    "ruc": "80012345-6"
  },
  "instrucciones": "Transferir ₲100.000 e incluir el código REF-20260302-00001 en el concepto"
}
```

**Paso B: Padre Realiza Transferencia**
- Transfiere el monto indicado
- Incluye código de referencia en el concepto
- Presenta comprobante en caja

**Paso C: Validación en Caja**
```
POST /api/v1/cargas-saldo/transferencia/validar/
{
  "codigo_referencia": "REF-20260302-00001",
  "numero_comprobante": "COMP-555",
  "empleado_id": 5,
  "imagen_comprobante": "/uploads/comprobante.jpg"
}

Response:
{
  "success": true,
  "monto_acreditado": 100000,
  "saldo_nuevo": 150000,
  "id_factura": 789,
  "mensaje": "Transferencia validada. Saldo acreditado."
}
```

---

### Flujo 3: Transferencia SIN Código (Manual)

```
POST /api/v1/cargas-saldo/transferencia/validar/
{
  "hijo_id": 123,
  "monto": 100000,
  "numero_comprobante": "COMP-666",
  "empleado_id": 5,
  "imagen_comprobante": "/uploads/comp2.jpg"
}
```

**Sistema**:
1. Calcula saldo a acreditar
2. Verifica que `numero_comprobante` no exista (idempotencia)
3. Acredita saldo
4. Genera factura

---

### Flujo 4: Aprobación de Supervisor (Monto Elevado)

```
# Si monto > ₲500.000, la validación devuelve:
{
  "success": true,
  "requiere_aprobacion": true,
  "id_recarga": 456,
  "monto": 600000,
  "mensaje": "Monto elevado. Requiere aprobación de supervisor."
}

# Supervisor aprueba:
POST /api/v1/cargas-saldo/456/aprobar/
{
  "supervisor_id": 10
}

Response:
{
  "success": true,
  "monto_acreditado": 600000,
  "saldo_nuevo": 750000,
  "id_factura": 999,
  "mensaje": "Recarga aprobada y procesada por supervisor Juan Pérez"
}
```

---

### Flujo 5: Pasarela Bancard (Pendiente de Implementación)

```
POST /api/v1/cargas-saldo/init/
{
  "hijo_id": 123,
  "monto": 100000,
  "redirect_url": "https://app.cantinatita.com/recarga/callback"
}

Response:
{
  "id_recarga": 456,
  "payment_url": "https://vpos.infonet.com.py/checkout/new?...",
  "total_cobrado": 103400,
  "comision": 3400
}

# Usuario es redirigido a Bancard
# Webhook POST /api/v1/webhooks/bancard (validar firma HMAC-SHA256)
# Backend actualiza estado a COMPLETADA y acredita saldo
```

---

## 🌐 API Endpoints

### Endpoints Disponibles

| Método | Endpoint | Descripción | Estado |
|--------|----------|-------------|--------|
| POST | `/api/v1/cargas-saldo/caja/` | Registra recarga en efectivo/POS | ✅ Implementado |
| POST | `/api/v1/cargas-saldo/transferencia/referencia/` | Genera código para transferencia | ✅ Implementado |
| POST | `/api/v1/cargas-saldo/transferencia/validar/` | Valida transferencia bancaria | ✅ Implementado |
| POST | `/api/v1/cargas-saldo/{id}/aprobar/` | Aprueba recarga (supervisor) | ✅ Implementado |
| POST | `/api/v1/cargas-saldo/init/` | Inicia recarga Bancard | ⏳ Pendiente |
| POST | `/api/v1/webhooks/bancard/` | Webhook de Bancard | ⏳ Pendiente |
| GET | `/api/v1/cargas-saldo/` | Lista recargas | ✅ DRF estándar |
| GET | `/api/v1/cargas-saldo/{id}/` | Detalle de recarga | ✅ DRF estándar |

### Filtros Disponibles
```
GET /api/v1/cargas-saldo/?estado=completada
GET /api/v1/cargas-saldo/?metodo_pago=efectivo
GET /api/v1/cargas-saldo/?nro_tarjeta=T001
GET /api/v1/cargas-saldo/?search=REF-20260302
```

---

## 📦 Modelos y Campos

### Modelo: `CargasSaldo`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id_carga` | BigAutoField | ID único de la recarga |
| `nro_tarjeta` | ForeignKey(Tarjetas) | Tarjeta destino |
| `id_cliente_origen` | ForeignKey(Clientes) | Cliente que realiza la recarga |
| `fecha_carga` | DateTimeField | Fecha de creación |
| `monto_cargado` | Decimal | **Saldo neto acreditado** |
| `total_cobrado` | Decimal | Monto total cobrado (incluye comisión) |
| `comision_aplicada` | Decimal | Comisión cobrada |
| `porcentaje_comision` | Decimal | % de comisión |
| `metodo_pago` | CharField | efectivo, bancard, tarjeta_pos, transferencia |
| `estado` | CharField | Ver [Estados](#estados-de-recarga) |
| `referencia` | CharField | Referencia general |
| `codigo_referencia_interno` | CharField | Código REF-XXXXX (único) |
| `numero_comprobante_externo` | CharField | Nº comprobante bancario (único, idempotencia) |
| `referencia_externa` | CharField | ID Bancard (único, idempotencia) |
| `usuario_responsable` | ForeignKey(Empleados) | Cajero que registró |
| `supervisor_aprobador` | ForeignKey(Empleados) | Supervisor que aprobó |
| `fecha_confirmacion` | DateTimeField | Cuándo se completó |
| `fecha_aprobacion` | DateTimeField | Cuándo aprobó el supervisor |
| `id_factura` | ForeignKey(Ventas) | Factura generada |
| `imagen_comprobante` | CharField | Ruta a imagen |
| `ip_origen` | GenericIPAddressField | IP de origen |
| `webhook_payload` | TextField | Payload JSON del webhook |
| `motivo_rechazo` | CharField | Razón de rechazo |
| `requiere_validacion_supervisor` | BooleanField | Flag de doble validación |

---

## ⚙️ Servicios

### `RecargaService`

Servicio centralizado en `apps/core/services.py`.

#### Métodos Principales

**`calcular_montos(monto_recarga, metodo_pago)`**
- Calcula comisión y total cobrado
- Returns: `{monto_recarga, comision_porcentaje, comision_monto, total_cobrado}`

**`generar_codigo_referencia()`**
- Genera código único formato `REF-YYYYMMDD-NNNNN`
- Secuencial por día

**`validar_idempotencia(numero_comprobante, referencia_externa)`**
- Verifica que no exista duplicado
- Returns: `True` si ya existe, `False` si es nuevo

**`acreditar_saldo(recarga)`**
- Actualiza `tarjeta.saldo_actual` (atomic)
- Registra en `ConsumosTarjeta` (historial)
- Returns: `{success, saldo_anterior, saldo_nuevo, monto_acreditado}`

**`generar_factura(recarga)`**
- Crea venta en `Ventas`
- Producto: `RECARGA-SALDO`
- Monto facturado = `monto_cargado` (NO incluye comisión)
- Returns: `{success, id_factura, numero_factura, monto_facturado}`

**`procesar_recarga_caja(hijo_id, monto, metodo_pago, empleado_id, referencia)`**
- Flujo completo para caja
- Estado inmediato: `COMPLETADA`
- Returns: resultado completo

**`iniciar_recarga_transferencia(hijo_id, monto)`**
- Genera código de referencia
- Crea recarga en estado `pendiente_validacion`
- Returns: código, datos bancarios, instrucciones

**`validar_transferencia(...)`**
- Valida con código O manual
- Verifica idempotencia
- Acredita saldo o pasa a validación supervisor
- Returns: resultado con requiere_aprobacion flag

**`aprobar_recarga_supervisor(recarga_id, supervisor_id)`**
- Cambia estado a `completada`
- Acredita saldo y genera factura
- Returns: resultado completo

---

## 🔄 Estados de Recarga

| Estado | Descripción | Siguiente Estado |
|--------|-------------|------------------|
| `pendiente` | Iniciada, esperando confirmación (Bancard) | completada / rechazada |
| `pendiente_validacion` | Transferencia con código, esperando validación del cajero | completada / validacion_pendiente |
| `validacion_pendiente` | Esperando aprobación de supervisor (monto elevado) | completada |
| `completada` | ✅ Exitosa, saldo acreditado | - (final) |
| `rechazada` | ❌ Pago rechazado | - (final) |
| `cancelada` | 🚫 Cancelada por usuario/sistema | - (final) |
| `reembolsada` | ↩️ Reembolsada | - (final) |
| `expirada` | ⏰ No confirmada en tiempo límite (24h) | - (final) |

---

## 🔒 Seguridad e Idempotencia

### Idempotencia Garantizada

**Por Transferencia**:
```python
numero_comprobante_externo = "COMP-555"  # UNIQUE en BD
```
- ❌ Si ya existe → ValidationError
- ✅ Si no existe → Procesa

**Por Bancard**:
```python
referencia_externa = "BAN-12345"  # UNIQUE en BD
```
- ❌ Webhook duplicado → Ignora (200 OK)
- ✅ Primer webhook → Procesa

### Validación de Webhook Bancard
```python
# 1. Validar IP contra lista blanca
BANCARD_IPS = ['190.104.10.20', '190.104.10.21']

# 2. Verificar firma HMAC-SHA256
import hmac, hashlib
expected_signature = hmac.new(
    SECRET_KEY.encode(),
    webhook_payload.encode(),
    hashlib.sha256
).hexdigest()

if signature != expected_signature:
    return 403 Forbidden
```

### Atomicidad
```python
from django.db import transaction

with transaction.atomic():
    tarjeta = Tarjetas.objects.select_for_update().get(...)
    tarjeta.saldo_actual += monto
    tarjeta.save()
    ConsumosTarjeta.objects.create(...)
```

---

## 💡 Ejemplos de Uso

### Ejemplo 1: Recarga en Efectivo

**Request**:
```python
import requests

response = requests.post(
    'http://localhost:8000/api/v1/cargas-saldo/caja/',
    json={
        'hijo_id': 123,
        'monto': 50000,
        'metodo_pago': 'efectivo',
        'empleado_id': 5,
        'referencia': 'CAJA-MAR-001'
    }
)

print(response.json())
```

**Response**:
```json
{
  "success": true,
  "id_recarga": 456,
  "estado": "completada",
  "monto_acreditado": 50000,
  "total_cobrado": 50000,
  "comision": 0,
  "saldo_nuevo": 75000,
  "id_factura": 789,
  "mensaje": "Recarga procesada exitosamente. Nuevo saldo: ₲75.000,00"
}
```

---

### Ejemplo 2: Transferencia con Código

**Generar Referencia**:
```python
response = requests.post(
    'http://localhost:8000/api/v1/cargas-saldo/transferencia/referencia/',
    json={
        'hijo_id': 123,
        'monto': 100000
    }
)

data = response.json()
print(f"Código: {data['codigo_referencia']}")
# Output: Código: REF-20260302-00001
```

**Validar Transferencia**:
```python
response = requests.post(
    'http://localhost:8000/api/v1/cargas-saldo/transferencia/validar/',
    json={
        'codigo_referencia': 'REF-20260302-00001',
        'numero_comprobante': 'COMP-555',
        'empleado_id': 5
    }
)

print(response.json())
```

**Response**:
```json
{
  "success": true,
  "requiere_aprobacion": false,
  "id_recarga": 457,
  "estado": "completada",
  "monto_acreditado": 100000,
  "saldo_nuevo": 175000,
  "id_factura": 790,
  "mensaje": "Transferencia validada. Saldo acreditado: ₲100.000,00"
}
```

---

### Ejemplo 3: Monto Elevado con Aprobación

**Validar Transferencia Grande**:
```python
response = requests.post(
    'http://localhost:8000/api/v1/cargas-saldo/transferencia/validar/',
    json={
        'hijo_id': 123,
        'monto': 600000,  # > ₲500.000
        'numero_comprobante': 'COMP-777',
        'empleado_id': 5
    }
)

data = response.json()
print(data)
```

**Response**:
```json
{
  "success": true,
  "requiere_aprobacion": true,
  "id_recarga": 458,
  "monto": 600000,
  "mensaje": "Monto elevado. Requiere aprobación de supervisor."
}
```

**Supervisor Aprueba**:
```python
response = requests.post(
    'http://localhost:8000/api/v1/cargas-saldo/458/aprobar/',
    json={
        'supervisor_id': 10
    }
)

print(response.json())
```

**Response**:
```json
{
  "success": true,
  "id_recarga": 458,
  "monto_acreditado": 600000,
  "saldo_nuevo": 775000,
  "id_factura": 791,
  "mensaje": "Recarga aprobada y procesada por supervisor Juan Pérez"
}
```

---

## 📊 Consideraciones Técnicas

### Umbral de Doble Validación
```python
# En services.py
UMBRAL_DOBLE_VALIDACION = Decimal('500000.00')  # ₲500.000

# Configurable desde ConfiguracionSistema:
from apps.core.models import ConfiguracionSistema
umbral = ConfiguracionSistema.get_valor('UMBRAL_VALIDACION_RECARGA', default=500000)
```

### Job de Expiración
```python
# Tarea programada (Celery o cron):
# Marcar recargas PENDIENTES con > 24h como EXPIRADAS

from django.utils import timezone
from datetime import timedelta
from apps.core.models import CargasSaldo

CargasSaldo.objects.filter(
    estado='pendiente',
    fecha_carga__lt=timezone.now() - timedelta(hours=24)
).update(estado='expirada')
```

### Optimistic Locking
```python
# Evitar condiciones de carrera en saldo:
from django.db import transaction

with transaction.atomic():
    tarjeta = Tarjetas.objects.select_for_update().get(pk=id)
    # Operaciones con tarjeta...
```

---

## ✅ Estado de Implementación

| Componente | Estado | Cobertura |
|------------|--------|-----------|
| Migración 0003 | ✅ Creada | Todos los campos nuevos |
| Modelo CargasSaldo | ✅ Expandido | 16 campos nuevos |
| RecargaService | ✅ Completo | 7 métodos principales |
| Validators | ✅ Actualizados | 4 validators nuevos |
| CargasSaldoViewSet | ✅ Implementado | 4 custom actions |
| Serializer | ✅ Expandido | Campos calculados |
| Signal | ⚠️ Deshabilitado | Lógica en servicio |
| Tests | ⏳ Pendiente | 0% |
| Integración Bancard | ⏳ Pendiente | API + Webhook |
| Frontend UI | ⏳ Pendiente | Portal/App |

---

## 🚀 Próximos Pasos

1. ✅ Ejecutar migración `0003_expand_cargas_saldo.py`
2. ⏳ Crear tests unitarios para `RecargaService`
3. ⏳ Implementar integración con API de Bancard
4. ⏳ Crear webhook endpoint con validación de firma
5. ⏳ Integrar con sistema de roles de usuarios
6. ⏳ Crear job de expiración de recargas pendientes
7. ⏳ Desarrollar interfaces de usuario (frontend)

---

## 📚 Referencias

- [Documentación API Bancard](https://www.bancard.com.py/desarrolladores)
- [Django Transactions](https://docs.djangoproject.com/en/stable/topics/db/transactions/)
- [DRF Custom Actions](https://www.django-rest-framework.org/api-guide/viewsets/#marking-extra-actions-for-routing)

---

**Última Actualización**: 2 de Marzo de 2026  
**Versión**: 2.0  
**Autor**: Sistema CANTINA_TITA
