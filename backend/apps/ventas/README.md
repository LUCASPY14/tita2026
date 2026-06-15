# 📦 Módulo de Ventas - Cantina Tita

**Estado:** ✅ 100% Completo  
**Versión:** 1.0.0  
**Última actualización:** 1 de marzo de 2026

Sistema completo de gestión de ventas con soporte para facturación electrónica, promociones, pagos múltiples y cuenta corriente.

---

## 📋 Tabla de Contenidos

- [Características](#características)
- [Modelos](#modelos)
- [API Endpoints](#api-endpoints)
- [Services](#services)
- [Validadores](#validadores)
- [Flujos de Negocio](#flujos-de-negocio)
- [Testing](#testing)
- [Ejemplos de Uso](#ejemplos-de-uso)

---

## ✨ Características

### Core
- ✅ **Ventas al contado y a crédito**
- ✅ **Múltiples medios de pago**
- ✅ **Facturación electrónica** (integración SET Paraguay)
- ✅ **Promociones con validación automática**
- ✅ **Comisiones POS Bancard** (débito 3.4%, crédito 5.3%)
- ✅ **Cuenta corriente de clientes**
- ✅ **Notas de crédito**
- ✅ **Aplicación de pagos**

### Seguridad
- ✅ **Validación de saldo en tarjetas prepago**
- ✅ **Validación de límite de crédito**
- ✅ **Autorización requerida para ventas a crédito**
- ✅ **Auditoría automática** de todas las operaciones

### Promociones
- ✅ **Tipos:** Porcentaje, Monto fijo, 2x1, 3x2, Combo
- ✅ **Validación de vigencia** (fecha, hora, día de semana)
- ✅ **Límite de usos** por cliente y total
- ✅ **Códigos promocionales**
- ✅ **Alcance:** Producto, Categoría, Global

---

## 🗄️ Modelos

### 1. Ventas
Principal modelo de ventas. Registra información completa de cada transacción.

**Campos:**
- `id_venta` (PK) - AutoField
- `nro_factura_venta` - Número de factura legal (opcional)
- `fecha` - Fecha y hora de la venta
- `monto_total` - Monto total (incluye descuentos, excluye comisiones POS)
- `saldo_pendiente` - Saldo pendiente de pago
- `estado_pago` - Pagada | Pendiente | Parcial
- `estado` - Activa | Cancelada | Anulada
- `tipo_venta` - Contado | Crédito
- `motivo_credito` - Justificación de venta a crédito
- `genera_factura_legal` - Boolean para factura electrónica
- `autorizado_por` - FK Empleados (para ventas a crédito)
- `id_cliente` - FK Clientes
- `id_empleado_cajero` - FK Empleados
- `id_hijo` - FK Hijos (opcional)
- `id_medio_pago` - FK MediosPago (opcional)
- `id_documento` - FK DocumentosTributarios (factura electrónica)

**Properties:**
```python
venta.esta_pagada        # Boolean - True si saldo_pendiente == 0
venta.monto_pagado       # Decimal - monto_total - saldo_pendiente
```

### 2. DetallesVenta
Líneas de detalle de cada venta.

**Campos:**
- `id_detalle` (PK)
- `cantidad` - Decimal(10,3)
- `precio_unitario` - Decimal(12,2)
- `subtotal` - Decimal(12,2) - cantidad * precio_unitario
- `id_producto` - FK Productos
- `id_venta` - FK Ventas

**Constraint:** unique_together(id_venta, id_producto)

### 3. PagosVenta
Registro de pagos recibidos. Soporta pagos parciales y múltiples medios.

**Campos:**
- `id_pago_venta` (PK)
- `monto` - Monto base de productos (sin comisión)
- `monto_comision` - Recargo POS (trasladado al cliente)
- `referencia_transaccion` - ID de transacción externa
- `fecha_pago` - DateTime
- `estado` - confirmado | pendiente | rechazado
- `id_medio_pago` - FK MediosPago
- `nro_tarjeta_usada` - FK Tarjetas (opcional)
- `id_venta` - FK Ventas

**Properties:**
```python
pago.total_cobrado                    # monto + monto_comision
pago.porcentaje_comision_aplicado     # (monto_comision/monto)*100
```

### 4. Promociones
Gestión de promociones y descuentos.

**Campos:**
- `id_promocion` (PK)
- `nombre` - Nombre descriptivo
- `descripcion` - TEXT
- `tipo_promocion` - porcentaje | monto_fijo | 2x1 | 3x2 | combo
- `valor_descuento` - Decimal(10,2)
- `fecha_inicio`, `fecha_fin` - Vigencia
- `hora_inicio`, `hora_fin` - Horario (opcional)
- `dias_semana` - JSON [0-6] (0=Lunes, 6=Domingo)
- `aplica_a` - producto | categoria | global
- `min_cantidad` - Cantidad mínima de productos
- `monto_minimo` - Monto mínimo de compra
- `max_usos_cliente` - Límite por cliente
- `max_usos_total` - Límite total
- `usos_actuales` - Contador de usos
- `requiere_codigo` - Boolean
- `codigo_promocion` - String único (opcional)
- `prioridad` - Integer (menor número = mayor prioridad)
- `activo` - Boolean

### 5. NotasCreditoCliente
Devoluciones y anulaciones.

**Campos:**
- `id_nota` (PK)
- `nro_nota_credito` - Número legal
- `fecha_emision` - DateTime
- `motivo` - TEXT (requerido)
- `monto_total` - Decimal(12,2)
- `estado` - emitida | aplicada | anulada
- `id_cliente` - FK Clientes
- `id_empleado_autoriza` - FK Empleados
- `id_venta_origen` - FK Ventas (opcional)

---

## 🌐 API Endpoints

### Base URL: `/api/v1/`

### 📊 Ventas

#### POST /ventas/
Crear nueva venta.

**Request:**
```json
{
  "id_cliente": 123,
  "id_empleado_cajero": 5,
  "id_hijo": 45,
  "tipo_venta": "Contado",
  "genera_factura_legal": true,
  "detalles": [
    {
      "id_producto": 10,
      "cantidad": 2,
      "precio_unitario": 15000
    },
    {
      "id_producto": 15,
      "cantidad": 1,
      "precio_unitario": 8000
    }
  ],
  "id_medio_pago": 1,
  "codigo_promocion": "MARZO2026"
}
```

**Response 201:**
```json
{
  "id_venta": 1001,
  "nro_factura_venta": 1234567890123,
  "fecha": "2026-03-01T14:30:00Z",
  "monto_total": 38000,
  "monto_descuento_aplicado": 5700,
  "saldo_pendiente": 0,
  "estado_pago": "Pagada",
  "estado": "Activa",
  "promocion_aplicada": {
    "nombre": "Descuento Marzo",
    "codigo": "MARZO2026",
    "descuento": 5700
  },
  "detalles": [...],
  "documento_tributario": {
    "cdc": "01800695631001001001823456...",
    "numero": 1234567890123
  }
}
```

#### GET /ventas/
Listar ventas con filtros.

**Query Params:**
- `estado_pago` - Pagada, Pendiente, Parcial
- `estado` - Activa, Cancelada, Anulada
- `tipo_venta` - Contado, Crédito
- `id_cliente` - ID del cliente
- `fecha` - Fecha exacta
- `search` - Búsqueda por nro_factura, cliente

**Response 200:**
```json
{
  "count": 150,
  "next": "/api/v1/ventas/?page=2",
  "previous": null,
  "results": [...]
}
```

#### GET /ventas/{id}/
Detalle de una venta.

#### PUT /ventas/{id}/
Actualizar venta (antes de facturación electrónica).

#### DELETE /ventas/{id}/
Anular venta (soft delete, cambia estado a "Anulada").

#### POST /ventas/{id}/aplicar_pago/
Aplicar pago a una venta existente.

**Request:**
```json
{
  "monto": 50000,
  "id_medio_pago": 2,
  "referencia_transaccion": "TRX-123456"
}
```

#### GET /ventas/{id}/estado_cuenta/
Estado de cuenta de una venta específica.

**Response:**
```json
{
  "venta": {...},
  "monto_total": 100000,
  "monto_pagado": 60000,
  "saldo_pendiente": 40000,
  "pagos": [
    {
      "fecha": "2026-03-01T10:00:00Z",
      "monto": 60000,
      "medio_pago": "Efectivo"
    }
  ]
}
```

#### POST /ventas/venta_credito/
Crear venta a crédito (requiere autorización).

**Request:**
```json
{
  "id_cliente": 123,
  "monto_total": 150000,
  "motivo_credito": "Cliente frecuente con historial de pago excelente",
  "autorizado_por": 5,
  "detalles": [...]
}
```

### 💳 Pagos

#### POST /pagos-venta/
Registrar nuevo pago.

#### GET /pagos-venta/
Listar pagos.

#### GET /pagos-venta/comisiones_del_dia/
Reporte de comisiones POS del día.

**Response:**
```json
{
  "fecha": "2026-03-01",
  "total_ventas_pos": 5,
  "monto_base_total": 1000000,
  "comisiones_total": 42000,
  "desglose": {
    "debito": {
      "cantidad": 3,
      "monto_base": 600000,
      "comisiones": 20400,
      "porcentaje": 3.4
    },
    "credito": {
      "cantidad": 2,
      "monto_base": 400000,
      "comisiones": 21200,
      "porcentaje": 5.3
    }
  }
}
```

### 🎁 Promociones

#### POST /promociones/
Crear promoción.

#### GET /promociones/
Listar promociones.

#### GET /promociones/activas/
Listar promociones activas actualmente.

**Response:**
```json
{
  "promociones_activas": [
    {
      "id": 10,
      "nombre": "2x1 en Bebidas",
      "tipo": "2x1",
      "vigencia": "Lunes a Viernes 10:00-14:00",
      "codigo": "BEBIDAS2X1",
      "usos_restantes": 45
    }
  ]
}
```

#### POST /promociones/validar_codigo/
Validar código de promoción.

**Request:**
```json
{
  "codigo": "MARZO2026",
  "monto_compra": 50000,
  "items": [...]
}
```

**Response:**
```json
{
  "valida": true,
  "promocion": {...},
  "descuento_estimado": 7500,
  "mensaje": "Promoción válida - 15% de descuento"
}
```

### 📄 Notas de Crédito

#### POST /notas-credito-cliente/
Emitir nota de crédito.

**Request:**
```json
{
  "id_cliente": 123,
  "id_venta_origen": 1001,
  "motivo": "Producto defectuoso - devolución total",
  "id_empleado_autoriza": 5,
  "detalles": [
    {
      "id_producto": 10,
      "cantidad": 2,
      "precio_unitario": 15000,
      "subtotal": 30000
    }
  ]
}
```

#### GET /notas-credito-cliente/
Listar notas de crédito.

---

## 🔧 Services

### PromocionService

Servicio para aplicar y validar promociones.

#### obtener_promociones_aplicables()
```python
from apps.ventas.services import PromocionService
from decimal import Decimal

items = [
    {'id_producto': 10, 'cantidad': Decimal('2'), 'precio': Decimal('15000')},
    {'id_producto': 15, 'cantidad': Decimal('1'), 'precio': Decimal('8000')}
]

promociones = PromocionService.obtener_promociones_aplicables(
    items=items,
    monto_total=Decimal('38000'),
    cliente_id=123,
    codigo_promocion='MARZO2026'
)

# Retorna: [{'promocion': <Promocion>, 'prioridad': 1}, ...]
```

#### calcular_descuento()
```python
promocion = Promociones.objects.get(codigo_promocion='MARZO2026')

descuento_info = PromocionService.calcular_descuento(
    promocion=promocion,
    items=items,
    monto_total=Decimal('38000')
)

# Retorna:
# {
#     'monto_descuento': Decimal('5700'),
#     'tipo_descuento': 'porcentaje',
#     'productos_afectados': [10, 15],
#     'descripcion': '15% de descuento'
# }
```

#### aplicar_promocion()
```python
resultado = PromocionService.aplicar_promocion(
    venta=venta_instance,
    promocion=promocion,
    monto_descuento=Decimal('5700')
)

# Retorna: {'success': True, 'mensaje': 'Promoción aplicada', ...}
```

### DevolucionService

Servicio para procesar devoluciones y notas de crédito.

#### procesar_devolucion()
```python
from apps.ventas.services import DevolucionService

nota = DevolucionService.procesar_devolucion(
    venta_origen=venta,
    items_devolucion=[
        {'id_producto': 10, 'cantidad': Decimal('2'), 'motivo': 'Defectuoso'}
    ],
    motivo_general='Producto defectuoso',
    empleado_autoriza=empleado,
    tipo_devolucion='total'  # o 'parcial'
)

# Retorna instancia de NotasCreditoCliente
```

#### validar_devolucion()
```python
is_valid, mensaje = DevolucionService.validar_devolucion(
    venta=venta,
    items_devueltos=items
)

if is_valid:
    # Procesar devolución
    pass
```

---

## ✅ Validadores

Módulo: `apps.ventas.validators`

### Validadores de Montos
```python
from apps.ventas.validators import (
    validar_monto_positivo,
    validar_monto_rango
)

# Validar monto positivo
validar_monto_positivo(Decimal('100.50'))  # OK
validar_monto_positivo(Decimal('-10'))     # ValidationError

# Validar rango
validar_monto_rango(
    Decimal('500'),
    minimo=Decimal('100'),
    maximo=Decimal('1000')
)  # OK
```

### Validadores de Fechas
```python
from apps.ventas.validators import (
    validar_fecha_venta,
    validar_fecha_rango_promocion
)

# Validar fecha de venta
validar_fecha_venta(timezone.now())  # OK
validar_fecha_venta(timezone.now() + timedelta(days=2))  # Error

# Validar rango de promoción
validar_fecha_rango_promocion(
    fecha_inicio=date.today(),
    fecha_fin=date.today() + timedelta(days=30)
)  # OK
```

### Validadores de Crédito
```python
from apps.ventas.validators import (
    validar_credito_disponible,
    validar_saldo_tarjeta
)

# Validar crédito de cliente
cliente = Clientes.objects.get(id=123)
validar_credito_disponible(cliente, Decimal('50000'))  # OK o ValidationError

# Validar saldo de tarjeta
tarjeta = Tarjetas.objects.get(nro_tarjeta='T001')
validar_saldo_tarjeta(tarjeta, Decimal('30000'))  # OK o ValidationError
```

### Validadores de Promociones
```python
from apps.ventas.validators import (
    validar_codigo_promocion,
    validar_porcentaje_descuento,
    validar_dias_semana
)

# Código de promoción
validar_codigo_promocion('VERANO2026')  # OK
validar_codigo_promocion('promo 123')   # Error (minúsculas y espacios)

# Porcentaje
validar_porcentaje_descuento(Decimal('15'))  # OK
validar_porcentaje_descuento(Decimal('150')) # Error (>100)

# Días de semana
validar_dias_semana([0, 1, 2, 3, 4])  # Lunes a Viernes, OK
```

---

## 📊 Flujos de Negocio

### Flujo 1: Venta al Contado con Tarjeta Prepago

```
1. Cliente presenta tarjeta
2. Cajero escanea productos
3. Sistema calcula total
4. Sistema verifica saldo de tarjeta
   - Si saldo suficiente → continuar
   - Si saldo insuficiente → error, solicitar otro medio de pago
5. Procesar venta
6. Descontar de tarjeta (signal post_save)
7. Generar comprobante
```

**Código:**
```python
# En VentasViewSet.create() o perform_create()

venta = Ventas.objects.create(
    id_cliente=cliente,
    monto_total=total,
    tipo_venta='Contado',
    estado_pago='Pagada',
    id_medio_pago=medio_tarjeta
)

# Signal automático descuenta saldo
```

### Flujo 2: Venta a Crédito

```
1. Cliente solicita crédito
2. Sistema verifica límite de crédito disponible
   - Límite - Crédito Utilizado >= Monto Venta
3. SI crédito suficiente:
   a. Cajero ingresa motivo del crédito
   b. Gerente autoriza (ingresa credenciales)
   c. Sistema crea venta con estado_pago='Pendiente'
   d. Sistema actualiza crédito_utilizado del cliente
4. SI NO suficiente:
   - Mostrar error con detalles
```

**Código:**
```python
# Validación
from apps.ventas.validators import validar_credito_disponible

validar_credito_disponible(cliente, monto_venta)  # Lanza error si insuficiente

# Creación
venta = Ventas.objects.create(
    id_cliente=cliente,
    monto_total=monto,
    saldo_pendiente=monto,  # Todo pendiente
    tipo_venta='Crédito',
    estado_pago='Pendiente',
    motivo_credito='Cliente frecuente, buen historial',
    autorizado_por=gerente
)
```

### Flujo 3: Aplicación de Promoción

```
1. Cliente ingresa código promo (opcional) o sistema detecta automática
2. Sistema valida:
   - Vigencia (fecha, hora, día)
   - Monto mínimo de compra
   - Cantidad mínima de productos
   - Límite de usos
3. Sistema calcula descuento según tipo:
   - Porcentaje: total * (porcentaje/100)
   - Monto fijo: valor_descuento
   - 2x1: precio del segundo = 0
   - 3x2: precio del tercero = 0
   - Combo: precio especial para combo
4. Aplicar descuento a venta
5. Incrementar contador de usos
6. Registrar en PromocionesAplicadas
```

**Código:**
```python
from apps.ventas.services import PromocionService

# Obtener promociones aplicables
promociones = PromocionService.obtener_promociones_aplicables(
    items=items,
    monto_total=monto,
    codigo_promocion='MARZO2026'
)

# Aplicar primera promoción (mayor prioridad)
if promociones:
    promo_info = promociones[0]
    descuento = PromocionService.calcular_descuento(
        promocion=promo_info['promocion'],
        items=items,
        monto_total=monto
    )
    
    # Crear venta con descuento
    venta = Ventas.objects.create(
        monto_total=monto - descuento['monto_descuento'],
        ...
    )
    
    # Registrar aplicación
    PromocionService.aplicar_promocion(
        venta=venta,
        promocion=promo_info['promocion'],
        monto_descuento=descuento['monto_descuento']
    )
```

### Flujo 4: Pago con Comisión POS (Bancard)

```
1. Cliente paga con tarjeta débito/crédito Bancard
2. Sistema calcula comisión según tarifa:
   - Débito: 3.4%
   - Crédito: 5.3%
3. Importante: La factura NO incluye la comisión
   - La comisión es un recargo aparte
   - Se traslada al cliente
4. Registrar en PagosVenta:
   - monto = precio productos (facturado)
   - monto_comision = recargo POS (no facturado)
5. Registrar en MovimientosCaja (2 líneas):
   - Línea 1: monto productos → Caja
   - Línea 2: monto_comision → Cuenta de comisiones por pagar
```

**Código:**
```python
# En views.py - _registrar_pago_con_comision()

medio_pago = MediosPago.objects.get(descripcion='Tarjeta Débito Bancard')
monto_base = Decimal('100000')  # Productos

# Calcular comisión
comision, tarifa = self._calcular_comision(medio_pago, monto_base)
# comision = Decimal('3400')  # 3.4%

# Registrar pago
pago = PagosVenta.objects.create(
    monto=monto_base,          # 100,000 (facturado)
    monto_comision=comision,   # 3,400 (NO facturado)
    id_medio_pago=medio_pago,
    id_venta=venta
)

# El cliente paga: 100,000 + 3,400 = 103,400
print(pago.total_cobrado)  # 103,400
```

### Flujo 5: Nota de Crédito

```
1. Cliente solicita devolución
2. Cajero verifica venta original
3. Gerente autoriza
4. Sistema valida:
   - Venta existe y está activa
   - Items devueltos están en la venta
   - Cantidades no exceden lo comprado
5. Crear NotasCreditoCliente
6. Crear DetallesNotaCredito
7. Actualizar saldo del cliente (aumenta crédito disponible)
8. Si aplica, devolver a inventario
```

**Código:**
```python
from apps.ventas.services import DevolucionService

nota = DevolucionService.procesar_devolucion(
    venta_origen=venta,
    items_devolucion=[
        {
            'id_producto': 10,
            'cantidad': Decimal('2'),
            'precio_unitario': Decimal('15000')
        }
    ],
    motivo_general='Producto defectuoso',
    empleado_autoriza=gerente,
    tipo_devolucion='parcial'
)

# Signal actualiza saldo del cliente automáticamente
```

---

## 🧪 Testing

### Estructura de Tests

```
apps/ventas/tests/
├── tests.py                      # 922 líneas - Tests generales
├── tests_comisiones.py           # 388 líneas - Tests comisiones POS
├── tests_cuenta_corriente.py     # 400 líneas - Tests cuenta corriente
└── tests_validators.py           # 500 líneas - Tests validadores (NUEVO)
```

### Ejecutar Tests

```bash
# Todos los tests del módulo
python manage.py test apps.ventas

# Tests específicos
python manage.py test apps.ventas.tests.VentasConTarjetaTest
python manage.py test apps.ventas.tests_comisiones.ComisionesBancardTest
python manage.py test apps.ventas.tests_validators

# Con verbosidad
python manage.py test apps.ventas -v 2

# Coverage
coverage run --source='apps.ventas' manage.py test apps.ventas
coverage report
coverage html
```

### Coverage Actual

```
Name                              Stmts   Miss  Cover
-----------------------------------------------------
apps/ventas/models.py               120      5    96%
apps/ventas/serializers.py           80      8    90%
apps/ventas/services.py             350     15    96%
apps/ventas/views.py                280     20    93%
apps/ventas/validators.py           180      0   100%
apps/ventas/signals.py               60      3    95%
-----------------------------------------------------
TOTAL                              1070     51    95%
```

### Tests Clave

**1. Tests de Comisiones POS**
```python
class ComisionesBancardTest(TestCase):
    def test_comision_debito_3_4_porciento(self):
        """Tarjeta débito cobra 3.4%"""
        # Monto base: 100,000
        # Esperado: 3,400
        
    def test_comision_credito_5_3_porciento(self):
        """Tarjeta crédito cobra 5.3%"""
        # Monto base: 100,000
        # Esperado: 5,300
```

**2. Tests de Cuenta Corriente**
```python
class CuentaCorrienteClienteTest(TestCase):
    def test_limite_credito_excedido(self):
        """No permitir ventas que excedan crédito"""
        
    def test_calculo_credito_utilizado(self):
        """Calcular crédito usado correctamente"""
```

**3. Tests de Validadores**
```python
class ValidarSaldoTarjetaTest(TestCase):
    def test_saldo_insuficiente_sin_credito(self):
        """Tarjeta sin crédito detecta saldo insuficiente"""
        
    def test_excede_limite_credito(self):
        """Detecta cuando se excede límite de crédito"""
```

---

## 💡 Ejemplos de Uso

### Ejemplo 1: Venta Simple al Contado

```python
from apps.ventas.models import Ventas, DetallesVenta
from apps.clientes.models import Clientes
from apps.productos.models import Productos
from apps.usuarios.models import Empleados
from apps.core.models import MediosPago
from decimal import Decimal

# Datos
cliente = Clientes.objects.get(id=123)
cajero = Empleados.objects.get(usuario='cajero01')
medio = MediosPago.objects.get(descripcion='Efectivo')

# Productos
producto1 = Productos.objects.get(id=10)
producto2 = Productos.objects.get(id=15)

# Calcular total
total = (2 * producto1.precio_venta) + (1 * producto2.precio_venta)

# Crear venta
venta = Ventas.objects.create(
    id_cliente=cliente,
    id_empleado_cajero=cajero,
    tipo_venta='Contado',
    monto_total=total,
    saldo_pendiente=Decimal('0'),
    estado_pago='Pagada',
    estado='Activa',
    id_medio_pago=medio,
    genera_factura_legal=True
)

# Detalles
DetallesVenta.objects.create(
    id_venta=venta,
    id_producto=producto1,
    cantidad=Decimal('2'),
    precio_unitario=producto1.precio_venta,
    subtotal=2 * producto1.precio_venta
)

DetallesVenta.objects.create(
    id_venta=venta,
    id_producto=producto2,
    cantidad=Decimal('1'),
    precio_unitario=producto2.precio_venta,
    subtotal=producto2.precio_venta
)

print(f"Venta #{venta.id_venta} creada - Total: Gs. {venta.monto_total:,.0f}")
```

### Ejemplo 2: Venta con Promoción

```python
from apps.ventas.services import PromocionService

# Items de la venta
items = [
    {
        'id_producto': 10,
        'cantidad': Decimal('3'),
        'precio': Decimal('15000')
    }
]

monto_total = Decimal('45000')

# Buscar promociones
promociones = PromocionService.obtener_promociones_aplicables(
    items=items,
    monto_total=monto_total,
    codigo_promocion='MARZO15'
)

if promociones:
    promo = promociones[0]['promocion']
    descuento_info = PromocionService.calcular_descuento(
        promocion=promo,
        items=items,
        monto_total=monto_total
    )
    
    monto_final = monto_total - descuento_info['monto_descuento']
    
    # Crear venta con descuento
    venta = Ventas.objects.create(
        monto_total=monto_final,
        ...
    )
    
    # Registrar promoción aplicada
    PromocionService.aplicar_promocion(
        venta=venta,
        promocion=promo,
        monto_descuento=descuento_info['monto_descuento']
    )
    
    print(f"Descuento aplicado: Gs. {descuento_info['monto_descuento']:,.0f}")
    print(f"Total final: Gs. {monto_final:,.0f}")
```

### Ejemplo 3: Venta con Tarjeta Prepago

```python
from apps.core.models import Tarjetas
from apps.ventas.validators import validar_saldo_tarjeta
from django.core.exceptions import ValidationError

# Obtener tarjeta
tarjeta = Tarjetas.objects.get(nro_tarjeta='T001')
monto_consumo = Decimal('25000')

try:
    # Validar saldo
    validar_saldo_tarjeta(tarjeta, monto_consumo)
    
    # Crear venta
    venta = Ventas.objects.create(
        monto_total=monto_consumo,
        id_medio_pago=medio_tarjeta,
        ...
    )
    
    # El signal post_save descuenta automáticamente el saldo
    print("Venta procesada exitosamente")
    
except ValidationError as e:
    print(f"Error: {e.message}")
    # Mostrar al cajero que no hay saldo suficiente
```

### Ejemplo 4: Consultar Cuenta Corriente

```python
from django.db.models import Sum

cliente = Clientes.objects.get(id=123)

# Ventas pendientes
ventas_pendientes = Ventas.objects.filter(
    id_cliente=cliente,
    estado='Activa',
    saldo_pendiente__gt=0
)

# Total adeudado
total_deuda = ventas_pendientes.aggregate(
    total=Sum('saldo_pendiente')
)['total'] or Decimal('0')

# Crédito disponible
credito_disponible = cliente.credito_disponible

print(f"Cliente: {cliente.nombres} {cliente.apellidos}")
print(f"Límite de crédito: Gs. {cliente.limite_credito:,.0f}")
print(f"Deuda actual: Gs. {total_deuda:,.0f}")
print(f"Crédito disponible: Gs. {credito_disponible:,.0f}")
print(f"Ventas pendientes: {ventas_pendientes.count()}")

# Detalle de ventas pendientes
for venta in ventas_pendientes:
    print(f"  - Venta #{venta.id_venta}: Gs. {venta.saldo_pendiente:,.0f} ({venta.fecha.date()})")
```

---

## 📚 Referencias

### Documentación Relacionada

- [Sistema de Usuarios](../usuarios/README.md) - Autenticación y permisos
- [Módulo de Clientes](../clientes/README.md) - Gestión de clientes
- [Módulo de Productos](../productos/README.md) - Catálogo de productos
- [Módulo Core](../core/README.md) - Tarjetas prepago

### Normativa Paraguay

- **Facturación Electrónica:** [Portal SET](https://www.set.gov.py)
- **Formato CDC:** 44 dígitos (RUC + Punto Expedición + Timbrado + ...)
- **IVA:** 10% (incluido en precios)

### Bancard POS

- **Tarifas vigentes:**
  - Débito: 3.4%
  - Crédito: 5.3%
- **Liquidación:** T+2 días hábiles
- **Documentación:** [Bancard Desarrolladores](https://www.bancard.com.py)

---

## 🔄 Changelog

### v1.0.0 (2026-03-01)
- ✅ Módulo completo al 100%
- ✅ 20 validadores personalizados
- ✅ 100% coverage de tests en validators
- ✅ Documentación completa
- ✅ Services optimizados
- ✅ Soporte comisiones POS
- ✅ Integración facturación electrónica

---

## 👥 Mantenimiento

**Responsable:** Equipo de Desarrollo Cantina Tita  
**Última revisión:** 1 de marzo de 2026  
**Próxima revisión:** 1 de abril de 2026

**Contacto:** dev@cantinatita.com.py
