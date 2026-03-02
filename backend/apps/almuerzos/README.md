# 🍽️ Módulo de Almuerzos

## Descripción General

El módulo **Almuerzos** gestiona el sistema completo de almuerzo escolar de la cantina, incluyendo planes de suscripción, registro diario de consumos, facturación mensual, pagos, y control de alérgenos en productos.

## Tabla de Contenidos

- [Modelos](#modelos)
- [Validadores](#validadores)
- [Tests](#tests)
- [Panel de Administración](#panel-de-administración)
- [API Endpoints](#api-endpoints)
- [Ejemplos de Uso](#ejemplos-de-uso)
- [Mejores Prácticas](#mejores-prácticas)
- [Integración con otros Módulos](#integración-con-otros-módulos)

---

## Modelos

### 1. PlanesAlmuerzo

Planes mensuales de almuerzo con días y precios específicos.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id_plan_almuerzo` | AutoField | PK, identificador único |
| `nombre_plan` | CharField(100) | Nombre del plan (único) |
| `descripcion` | TextField | Descripción opcional del plan |
| `precio_mensual` | Decimal(10,2) | Precio mensual del plan |
| `dias_semana_incluidos` | CharField(60) | Días incluidos (ej: "L,M,Mi,J,V") |
| `fecha_creacion` | DateTimeField | Fecha de creación del plan |
| `activo` | BooleanField | Estado activo/inactivo |

**Validadores aplicados**:
- `validar_nombre_plan`: 3-100 chars, alfanumérico
- `validar_descripcion_plan`: Max 500 chars (opcional)
- `validar_precio_mensual_plan`: 0-₲5M, 2 decimales
- `validar_dias_semana_incluidos`: Max 60 chars, al menos 1 día válido

---

### 2. TiposAlmuerzo

Tipos de almuerzo con componentes específicos (plato, postre, bebida).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id_tipo_almuerzo` | AutoField | PK, identificador único |
| `nombre` | CharField(100) | Nombre del tipo |
| `descripcion` | TextField | Descripción opcional |
| `precio_unitario` | Decimal(10,2) | Precio por unidad |
| `incluye_plato_principal` | BooleanField | Incluye plato principal (default: True) |
| `incluye_postre` | BooleanField | Incluye postre (default: False) |
| `incluye_bebida` | BooleanField | Incluye bebida (default: False) |
| `fecha_creacion` | DateTimeField | Fecha de creación |
| `activo` | BooleanField | Estado activo/inactivo |

**Validadores aplicados**:
- `validar_nombre_tipo_almuerzo`: 3-100 chars, alfanumérico
- `validar_precio_unitario_tipo`: 0-₲500K, 2 decimales

---

### 3. SuscripcionesAlmuerzo

Suscripción de un estudiante a un plan de almuerzo.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id_suscripcion` | BigAutoField | PK, identificador único |
| `id_hijo` | ForeignKey | FK a Clientes.Hijos |
| `id_plan_almuerzo` | ForeignKey | FK a PlanesAlmuerzo |
| `fecha_inicio` | DateField | Fecha de inicio de la suscripción |
| `fecha_fin` | DateField | Fecha de finalización (opcional) |
| `estado` | CharField(10) | Activa, Pausada, Cancelada, Finalizada |

**Unique Together**: `(id_hijo, id_plan_almuerzo, estado)`

**Validadores aplicados**:
- `validar_fecha_inicio_suscripcion`: >= 2020, max 1 año futuro
- `validar_fecha_fin_suscripcion`: >= 2020, max 5 años futuro (opcional)
- `validar_estado_suscripcion`: Activa, Pausada, Cancelada, Finalizada
- `validar_rango_fechas_suscripcion`: fecha_fin > fecha_inicio

---

### 4. RegistrosConsumoAlmuerzo

Registro diario de consumo de almuerzo de cada estudiante.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id_registro_consumo` | BigAutoField | PK, identificador único |
| `id_hijo` | ForeignKey | FK a Clientes.Hijos |
| `id_suscripcion` | ForeignKey | FK a SuscripcionesAlmuerzo (opcional) |
| `id_tipo_almuerzo` | ForeignKey | FK a TiposAlmuerzo (opcional) |
| `nro_tarjeta` | ForeignKey | FK a Core.Tarjetas (opcional) |
| `id_empleado_registro` | ForeignKey | FK a Usuarios.Empleados (opcional) |
| `fecha_consumo` | DateField | Fecha del consumo |
| `hora_registro` | TimeField | Hora del registro |
| `costo_almuerzo` | Decimal(10,2) | Costo del almuerzo (opcional) |
| `marcado_en_cuenta` | BooleanField | Agregado a cuenta mensual (default: False) |
| `estado` | CharField(20) | Registrado, Confirmado, Rechazado, Cancelado |
| `motivo_rechazo` | CharField(255) | Motivo si rechazado (opcional) |

**Validadores aplicados**:
- `validar_fecha_consumo`: No futura, >= 2020, max 90 días atrás
- `validar_hora_registro`: 06:00-16:00
- `validar_costo_almuerzo`: 0-₲200K, 2 decimales (opcional)
- `validar_estado_consumo`: Registrado, Confirmado, Rechazado, Cancelado
- `validar_motivo_rechazo`: 10-255 chars (requerido si rechazado)

---

### 5. CuentasAlmuerzoMensual

Cuenta mensual de almuerzos por estudiante.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id_cuenta` | BigAutoField | PK, identificador único |
| `id_hijo` | ForeignKey | FK a Clientes.Hijos |
| `anio` | IntegerField | Año de la cuenta |
| `mes` | SmallIntegerField | Mes (1-12) |
| `cantidad_almuerzos` | IntegerField | Cantidad de almuerzos consumidos |
| `monto_total` | Decimal(10,2) | Monto total de la cuenta |
| `forma_cobro` | CharField(20) | Efectivo, Transferencia, Tarjeta, Cuenta Corriente |
| `monto_pagado` | Decimal(10,2) | Monto ya pagado |
| `estado` | CharField(10) | Pendiente, Pagada, Vencida, Cancelada |
| `fecha_generacion` | DateField | Fecha de generación de la cuenta |
| `fecha_actualizacion` | DateTimeField | Última actualización |
| `observaciones` | TextField | Observaciones opcionales |

**Unique Together**: `(id_hijo, anio, mes)`

**Propiedades calculadas**:
```python
@property
def saldo_pendiente(self):
    """Calcula saldo pendiente: monto_total - monto_pagado"""
    return self.monto_total - self.monto_pagado
```

**Validadores aplicados**:
- `validar_anio_cuenta`: 2020 a año_actual+1
- `validar_mes_cuenta`: 1-12
- `validar_cantidad_almuerzos`: 0-31
- `validar_monto_total_cuenta`: 0-₲10M, 2 decimales
- `validar_forma_cobro`: Efectivo, Transferencia, Tarjeta, Cuenta Corriente, Débito Automático
- `validar_monto_pagado_cuenta`: 0-₲10M, 2 decimales
- `validar_estado_cuenta`: Pendiente, Pagada, Vencida, Cancelada
- `validar_coherencia_montos_cuenta`: monto_pagado <= monto_total * 1.10

---

### 6. PagosAlmuerzoMensual

Pagos de suscripciones mensuales de almuerzo.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id_pago_almuerzo` | BigAutoField | PK, identificador único |
| `id_suscripcion` | ForeignKey | FK a SuscripcionesAlmuerzo |
| `id_venta` | OneToOneField | FK a Ventas.Ventas (opcional) |
| `fecha_pago` | DateTimeField | Fecha y hora del pago |
| `monto_pagado` | Decimal(10,2) | Monto del pago |
| `mes_pagado` | DateField | Mes correspondiente al pago |
| `estado` | CharField(9) | Pendiente, Confirmado, Rechazado |

**Unique Together**: `(id_suscripcion, mes_pagado)`

**Validadores aplicados**:
- `validar_fecha_pago`: No futura, >= 2020
- `validar_monto_pago`: >0, <=₲10M, 2 decimales
- `validar_estado_pago_mensual`: Pendiente, Confirmado, Rechazado (opcional)

---

### 7. PagosCuentasAlmuerzo

Pagos individuales aplicados a cuentas mensuales.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id_pago` | BigAutoField | PK, identificador único |
| `id_cuenta` | ForeignKey | FK a CuentasAlmuerzoMensual |
| `id_empleado_registro` | ForeignKey | FK a Usuarios.Empleados (opcional) |
| `fecha_pago` | DateTimeField | Fecha y hora del pago |
| `medio_pago` | CharField(15) | Efectivo, Transferencia, Tarjeta Débito, Tarjeta Crédito, Cheque |
| `monto` | Decimal(10,2) | Monto del pago |
| `referencia` | CharField(50) | Referencia del pago (opcional) |
| `observaciones` | TextField | Observaciones opcionales |

**Validadores aplicados**:
- `validar_fecha_pago`: No futura, >= 2020
- `validar_monto_pago`: >0, <=₲10M, 2 decimales
- `validar_medio_pago`: Efectivo, Transferencia, Tarjeta Débito, Tarjeta Crédito, Cheque
- `validar_referencia_pago`: Max 50 chars, alfanumérico (opcional)

---

### 8. Alergenos

Catálogo de alérgenos con niveles de severidad.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id_alergeno` | AutoField | PK, identificador único |
| `nombre` | CharField(100) | Nombre del alérgeno (único) |
| `descripcion` | TextField | Descripción del alérgeno (opcional) |
| `palabras_clave` | JSONField | Lista de palabras clave |
| `nivel_severidad` | CharField(10) | Baja, Media, Alta, Crítica |
| `icono` | CharField(10) | Icono o emoji (opcional) |
| `activo` | BooleanField | Estado activo/inactivo |
| `fecha_creacion` | DateTimeField | Fecha de creación |
| `usuario_creacion` | CharField(100) | Usuario que creó el registro (opcional) |

**Propiedades calculadas**:
```python
@property
def es_critico(self):
    """Verifica si el alérgeno es de severidad Crítica"""
    return self.nivel_severidad == 'Crítica'
```

**Validadores aplicados**:
- `validar_nombre_alergeno`: 3-100 chars, alfanumérico
- `validar_palabras_clave_alergeno`: Lista 1-20 palabras, 2-50 chars cada una
- `validar_nivel_severidad_alergeno`: Baja, Media, Alta, Crítica
- `validar_icono_alergeno`: Max 10 chars (opcional)
- `validar_usuario_creacion`: Max 100 chars, alfanumérico (opcional)

---

### 9. ProductosAlergenos

Relación entre productos y alérgenos que contienen.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id_producto_alergeno` | AutoField | PK, identificador único |
| `id_producto` | ForeignKey | FK a Productos.Productos |
| `id_alergeno` | ForeignKey | FK a Alergenos |
| `contiene` | BooleanField | True=Contiene, False=Puede contener trazas |
| `observaciones` | TextField | Observaciones opcionales |
| `fecha_registro` | DateTimeField | Fecha de registro |
| `usuario_registro` | CharField(100) | Usuario que registró (opcional) |

**Unique Together**: `(id_producto, id_alergeno)`

**Validadores aplicados**:
- `validar_observaciones_producto_alergeno`: Max 500 chars (opcional)

---

## Validadores

El módulo incluye **30 validadores** organizados por categoría:

### Planes y Tipos (4 validadores)
1. `validar_nombre_plan` - Nombre 3-100 chars
2. `validar_descripcion_plan` - Max 500 chars (opcional)
3. `validar_precio_mensual_plan` - ₲0-₲5M
4. `validar_dias_semana_incluidos` - Formato válido de días

### Tipos de Almuerzo (2 validadores)
5. `validar_nombre_tipo_almuerzo` - Nombre 3-100 chars
6. `validar_precio_unitario_tipo` - ₲0-₲500K

### Suscripciones (4 validadores)
7. `validar_fecha_inicio_suscripcion` - >=2020, max 1 año futuro
8. `validar_fecha_fin_suscripcion` - >=2020, max 5 años futuro
9. `validar_estado_suscripcion` - 4 estados válidos
10. `validar_rango_fechas_suscripcion` - Coherencia de fechas

### Consumos (5 validadores)
11. `validar_fecha_consumo` - No futura, max 90 días atrás
12. `validar_hora_registro` - 06:00-16:00
13. `validar_costo_almuerzo` - ₲0-₲200K
14. `validar_estado_consumo` - 4 estados válidos
15. `validar_motivo_rechazo` - 10-255 chars si rechazado

### Cuentas Mensuales (7 validadores)
16. `validar_anio_cuenta` - 2020 a año+1
17. `validar_mes_cuenta` - 1-12
18. `validar_cantidad_almuerzos` - 0-31
19. `validar_monto_total_cuenta` - ₲0-₲10M
20. `validar_forma_cobro` - 5 formas válidas
21. `validar_monto_pagado_cuenta` - ₲0-₲10M
22. `validar_estado_cuenta` - 4 estados válidos
23. `validar_coherencia_montos_cuenta` - Tolerancia 10%

### Pagos (4 validadores)
24. `validar_fecha_pago` - No futura, >=2020
25. `validar_monto_pago` - >₲0, <=₲10M
26. `validar_medio_pago` - 5 medios válidos
27. `validar_referencia_pago` - Max 50 chars (opcional)
28. `validar_estado_pago_mensual` - 3 estados válidos

### Alérgenos (3 validadores)
29. `validar_nombre_alergeno` - 3-100 chars, único
30. `validar_palabras_clave_alergeno` - Lista JSON 1-20 palabras
31. `validar_nivel_severidad_alergeno` - 4 niveles válidos
32. `validar_icono_alergeno` - Max 10 chars (opcional)
33. `validar_usuario_creacion` - Max 100 chars (opcional)

### Productos-Alérgenos (1 validador)
34. `validar_observaciones_producto_alergeno` - Max 500 chars

---

## Tests

**Cobertura**: 122 tests, 100% PASS en 0.305s ✅

### Distribución de Tests

| Categoría | Tests | Cobertura |
|-----------|-------|-----------|
| Planes de Almuerzo | 16 | Nombre, descripción, precio, días |
| Tipos de Almuerzo | 10 | Nombre, precio unitario |
| Suscripciones | 12 | Fechas, estados, rangos |
| Registros de Consumo | 20 | Fechas, horas, costos, estados, motivos |
| Cuentas Mensuales | 24 | Años, meses, cantidades, montos, coherencia |
| Pagos | 16 | Fechas, montos, medios, referencias |
| Alérgenos | 16 | Nombres, palabras clave, severidad, iconos |
| Productos-Alérgenos | 4 | Observaciones |
| Edge Cases | 4 | Casos límite y especiales |
| **TOTAL** | **122** | **100% PASS** |

### Ejecutar Tests

```bash
# Todos los tests del módulo
python manage.py test apps.almuerzos.tests_validators

# Tests específicos por categoría
python manage.py test apps.almuerzos.tests_validators.ValidarNombrePlanTest
python manage.py test apps.almuerzos.tests_validators.ValidarFechaConsumoTest

# Con verbosidad
python manage.py test apps.almuerzos.tests_validators -v 2
```

---

## Panel de Administración

### 1. PlanesAlmuerzoAdmin

**Características**:
- Badge de precio con color (verde <₲500K, naranja >=₲500K)
- Badge de estado (ACTIVO/INACTIVO)
- Filtros por activo y fecha de creación
- Búsqueda por nombre y descripción
- Fieldsets organizados

**List Display**:
- ID, nombre, precio (badge), días incluidos, estado (badge), fecha creación

---

### 2. TiposAlmuerzoAdmin

**Características**:
- Badge de precio unitario con color
- Indicadores booleanos de componentes (plato, postre, bebida)
- Badge de estado
- Filtros por activo y componentes incluidos

**List Display**:
- ID, nombre, precio (badge), incluye plato/postre/bebida, estado (badge)

---

### 3. SuscripcionesAlmuerzoAdmin

**Características**:
- Badge de estado con colores:
  - Verde: Activa
  - Naranja: Pausada
  - Rojo: Cancelada
  - Gris: Finalizada
- Filtros por estado y fecha de inicio
- Búsqueda por hijo y plan

**List Display**:
- ID, hijo, plan, fecha inicio, fecha fin, estado (badge)

---

### 4. RegistrosConsumoAlmuerzoAdmin

**Características**:
- Badge de costo con formato de moneda
- Badge de estado con colores (Registrado, Confirmado, Rechazado, Cancelado)  - Indicador de "marcado en cuenta"
- Filtros por estado, fecha y marcado
- Ordenamiento por fecha/hora descendente

**List Display**:
- ID, fecha, hora, hijo, costo (badge), estado (badge), marcado en cuenta

---

### 5. CuentasAlmuerzoMensual Admin

**Características**:
- Display de periodo (ej: "Marzo 2024")
- Badge de monto total (₲)
- Badge de monto pagado con color (verde si completo, naranja si parcial)
- Badge de saldo con color (verde si $0, rojo si pendiente)
- Badge de estado con colores
- Campo calculado de saldo pendiente

**List Display**:
- ID, hijo, periodo, cantidad almuerzos, total (badge), pagado (badge), saldo (badge), estado (badge)

---

### 6. PagosAlmuerzoMensualAdmin

**Características**:
- Badge de monto pagado (verde)
- Badge de estado (Pendiente, Confirmado, Rechazado)
- Relación con ventas (OneToOne)
- Filtros por estado y fecha

**List Display**:
- ID, suscripción, mes pagado, monto (badge), fecha pago, estado (badge)

---

### 7. PagosCuentasAlmuerzoAdmin

**Características**:
- Badge de monto (verde)
- Display de medio de pago
- Referencia de pago visible
- Empleado que registró
- Observaciones colapsables

**List Display**:
- ID, cuenta, fecha pago, medio pago, monto (badge), referencia, empleado

---

### 8. AlergenosAdmin

**Características**:
- Badge de severidad con iconos y colores:
  - 🔴 Rojo: Crítica
  - 🟡 Naranja: Alta/Media
  - 🟢 Verde: Baja
- Display de icono (emoji)
- Badge de estado
- Filtros por severidad y activo

**List Display**:
- ID, nombre, icono, severidad (badge), estado (badge), fecha creación

---

### 9. ProductosAlergenosAdmin

**Características**:
- Badge de "contiene":
  - Rojo "⚠️ CONTIENE": Si contiene el alérgeno
  - Naranja "PUEDE CONTENER TRAZAS": Si solo trazas
- Búsqueda por producto, alérgeno y observaciones
- Filtros por tipo de contención

**List Display**:
- ID, producto, alérgeno, contiene (badge), fecha registro, usuario

---

## API Endpoints

### Planes de Almuerzo

```python
# GET /api/v1/almuerzos/planes/
# Listar todos los planes activos

# POST /api/v1/almuerzos/planes/
{
    "nombre_plan": "Plan Básico",
    "descripcion": "Almuerzo de lunes a viernes",
    "precio_mensual": 450000.00,
    "dias_semana_incluidos": "L,M,Mi,J,V",
    "activo": true
}

# GET /api/v1/almuerzos/planes/{id}/
# Obtener detalles de un plan

# PUT/PATCH /api/v1/almuerzos/planes/{id}/
# Actualizar plan

# DELETE /api/v1/almuerzos/planes/{id}/
# Desactivar plan
```

### Suscripciones

```python
# POST /api/v1/almuerzos/suscripciones/
{
    "id_hijo": 1,
    "id_plan_almuerzo": 1,
    "fecha_inicio": "2024-03-01",
    "estado": "Activa"
}

# PUT /api/v1/almuerzos/suscripciones/{id}/pausar/
# Pausar una suscripción

# PUT /api/v1/almuerzos/suscripciones/{id}/cancelar/
# Cancelar una suscripción
```

### Registros de Consumo

```python
# POST /api/v1/almuerzos/registros-consumo/
{
    "id_hijo": 1,
    "id_suscripcion": 1,
    "fecha_consumo": "2024-03-01",
    "hora_registro": "12:30:00",
    "estado": "Registrado"
}

# GET /api/v1/almuerzos/registros-consumo/?fecha_consumo=2024-03-01
# Listar consumos del día
```

### Alérgenos

```python
# POST /api/v1/almuerzos/alergenos/
{
    "nombre": "Maní",
    "descripcion": "Alergia a maní y derivados",
    "palabras_clave": ["maní", "cacahuate", "peanut"],
    "nivel_severidad": "Crítica",
    "icono": "🥜",
    "activo": true
}

# POST /api/v1/almuerzos/productos-alergenos/
{
    "id_producto": 10,
    "id_alergeno": 1,
    "contiene": true,
    "observaciones": "Contiene maní en la preparación"
}
```

---

## Ejemplos de Uso

### Ejemplo 1: Crear Plan y Suscribir Estudiante

```python
from apps.almuerzos.models import PlanesAlmuerzo, SuscripcionesAlmuerzo
from apps.clientes.models import Hijos
from decimal import Decimal
from datetime import date

# 1. Crear plan de almuerzo
plan = PlanesAlmuerzo.objects.create(
    nombre_plan="Plan Completo 2024",
    descripcion="Incluye almuerzo de lunes a viernes con postre",
    precio_mensual=Decimal('480000.00'),
    dias_semana_incluidos="L,M,Mi,J,V",
    activo=True
)

# 2. Obtener estudiante
hijo = Hijos.objects.get(id_hijo=1)

# 3. Crear suscripción
suscripcion = SuscripcionesAlmuerzo.objects.create(
    id_hijo=hijo,
    id_plan_almuerzo=plan,
    fecha_inicio=date(2024, 3, 1),
    estado='Activa'
)

print(f"Suscripción creada: {suscripcion.id_suscripcion}")
print(f"Estudiante: {hijo.nombre_completo}")
print(f"Plan: {plan.nombre_plan} - ₲{plan.precio_mensual:,.0f}/mes")
```

### Ejemplo 2: Registrar Consumo de Almuerzo

```python
from apps.almuerzos.models import RegistrosConsumoAlmuerzo, TiposAlmuerzo
from datetime import date, time

# 1. Obtener el tipo de almuerzo
tipo = TiposAlmuerzo.objects.get(nombre="Menú Ejecutivo")

# 2. Registrar consumo
registro = RegistrosConsumoAlmuerzo.objects.create(
    id_hijo=hijo,
    id_suscripcion=suscripcion,
    id_tipo_almuerzo=tipo,
    fecha_consumo=date.today(),
    hora_registro=time(12, 30, 0),
    costo_almuerzo=tipo.precio_unitario,
    estado='Confirmado',
    marcado_en_cuenta=False
)

print(f"Consumo registrado: {registro.id_registro_consumo}")
print(f"Fecha: {registro.fecha_consumo} a las {registro.hora_registro}")
print(f"Costo: ₲{registro.costo_almuerzo:,.0f}")
```

### Ejemplo 3: Generar Cuenta Mensual

```python
from apps.almuerzos.models import CuentasAlmuerzoMensual, RegistrosConsumoAlmuerzo
from django.db.models import Sum, Count
from decimal import Decimal

# 1. Calcular consumos del mes
anio, mes = 2024, 3
consumos = RegistrosConsumoAlmuerzo.objects.filter(
    id_hijo=hijo,
    fecha_consumo__year=anio,
    fecha_consumo__month=mes,
    estado='Confirmado',
    marcado_en_cuenta=False
)

cantidad = consumos.count()
monto_total = consumos.aggregate(Sum('costo_almuerzo'))['costo_almuerzo__sum'] or Decimal('0.00')

# 2. Crear cuenta mensual
cuenta = CuentasAlmuerzoMensual.objects.create(
    id_hijo=hijo,
    anio=anio,
    mes=mes,
    cantidad_almuerzos=cantidad,
    monto_total=monto_total,
    forma_cobro='Cuenta Corriente',
    monto_pagado=Decimal('0.00'),
    estado='Pendiente',
    fecha_generacion=date.today()
)

# 3. Marcar consumos como procesados
consumos.update(marcado_en_cuenta=True)

print(f"Cuenta generada: {cuenta.id_cuenta}")
print(f"Periodo: {mes}/{anio}")
print(f"Cantidad de almuerzos: {cantidad}")
print(f"Monto total: ₲{monto_total:,.0f}")
print(f"Saldo pendiente: ₲{cuenta.saldo_pendiente:,.0f}")
```

### Ejemplo 4: Gestionar Alérgenos en Productos

```python
from apps.almuerzos.models import Alergenos, ProductosAlergenos
from apps.productos.models import Productos

# 1. Crear alérgeno
alergeno_gluten = Alergenos.objects.create(
    nombre="Gluten",
    descripcion="Proteína presente en trigo, cebada y centeno",
    palabras_clave=["gluten", "trigo", "wheat", "cebada", "centeno"],
    nivel_severidad="Alta",
    icono="🌾",
    activo=True,
    usuario_creacion="admin"
)

# 2. Asociar alérgeno a productos
producto_pan = Productos.objects.get(nombre__icontains="Pan")

ProductosAlergenos.objects.create(
    id_producto=producto_pan,
    id_alergeno=alergeno_gluten,
    contiene=True,
    observaciones="Contiene trigo como ingrediente principal",
    usuario_registro="admin"
)

# 3. Verificar alérgenos de un producto
alergenos_producto = ProductosAlergenos.objects.filter(
    id_producto=producto_pan,
    contiene=True
)

print(f"Producto: {producto_pan.nombre}")
print(f"Alérgenos que CONTIENE:")
for rel in alergenos_producto:
    icono = rel.id_alergeno.icono or "⚠️"
    severidad = rel.id_alergeno.nivel_severidad
    print(f"  {icono} {rel.id_alergeno.nombre} - Severidad: {severidad}")
```

### Ejemplo 5: Verificar Restricciones de Hijo con Alérgenos

```python
from apps.clientes.models import RestriccionesHijos
from apps.almuerzos.models import ProductosAlergenos

# 1. Obtener restricciones alimentarias del hijo
restricciones = RestriccionesHijos.objects.filter(
    id_hijo=hijo,
    activo=True,
    severidad__in=['Alta', 'Crítica']
)

# 2. Verificar si un producto tiene alérgenos peligrosos para el hijo
def verificar_producto_seguro(producto, hijo):
    """
    Verifica si un producto es seguro para un hijo con restricciones
    """
    # Obtener alérgenos del producto
    alergenos_producto = ProductosAlergenos.objects.filter(
        id_producto=producto,
        contiene=True
    ).values_list('id_alergeno__nombre', flat=True)
    
    # Obtener restricciones del hijo
    restricciones_hijo = RestriccionesHijos.objects.filter(
        id_hijo=hijo,
        activo=True
    ).values_list('tipo_restriccion', flat=True)
    
    # Buscar coincidencias
    conflictos = []
    for alergeno in alergenos_producto:
        for restriccion in restricciones_hijo:
            if alergeno.lower() in restriccion.lower() or restriccion.lower() in alergeno.lower():
                conflictos.append({
                    'alergeno': alergeno,
                    'restriccion': restriccion
                })
    
    return len(conflictos) == 0, conflictos

# 3. Ejemplo de uso
producto = Productos.objects.get(nombre__icontains="Sandwich")
es_seguro, conflictos = verificar_producto_seguro(producto, hijo)

if es_seguro:
    print(f"✅ {producto.nombre} es SEGURO para {hijo.nombre_completo}")
else:
    print(f"⚠️ {producto.nombre} NO ES SEGURO para {hijo.nombre_completo}")
    print("Conflictos detectados:")
    for conflicto in conflictos:
        print(f"  - Alérgeno: {conflicto['alergeno']} | Restricción: {conflicto['restriccion']}")
```

---

## Mejores Prácticas

### 1. Validación de Consumos Diarios

```python
from datetime import date, time

def registrar_consumo_con_validacion(hijo, suscripcion, hora=None):
    """
    Registra un consumo validando reglas de negocio
    """
    # Verificar que la suscripción esté activa
    if suscripcion.estado != 'Activa':
        raise ValidationError("La suscripción no está activa")
    
    # Verificar que el día esté incluido en el plan
    hoy = date.today()
    dia_semana = hoy.strftime("%a")  # Mon, Tue, etc.
    if dia_semana not in suscripcion.id_plan_almuerzo.dias_semana_incluidos:
        raise ValidationError(f"El plan no incluye almuerzos los {dia_semana}")
    
    # Verificar que no haya consumo duplicado
    if RegistrosConsumoAlmuerzo.objects.filter(
        id_hijo=hijo,
        fecha_consumo=hoy,
        estado__in=['Registrado', 'Confirmado']
    ).exists():
        raise ValidationError("Ya existe un consumo registrado para hoy")
    
    # Registrar consumo
    return RegistrosConsumoAlmuerzo.objects.create(
        id_hijo=hijo,
        id_suscripcion=suscripcion,
        fecha_consumo=hoy,
        hora_registro=hora or time.now().time(),
        estado='Registrado'
    )
```

### 2. Cálculo Automático de Cuentas

```python
from django.db.models import Sum
from decimal import Decimal

def generar_cuenta_mensual(hijo, anio, mes):
    """
    Genera automáticamente la cuenta mensual de un hijo
    """
    # Verificar si ya existe
    cuenta_existente = CuentasAlmuerzoMensual.objects.filter(
        id_hijo=hijo,
        anio=anio,
        mes=mes
    ).first()
    
    if cuenta_existente:
        raise ValidationError("Ya existe una cuenta para este periodo")
    
    # Calcular consumos
    consumos = RegistrosConsumoAlmuerzo.objects.filter(
        id_hijo=hijo,
        fecha_consumo__year=anio,
        fecha_consumo__month=mes,
        estado='Confirmado',
        marcado_en_cuenta=False
    )
    
    cantidad = consumos.count()
    monto_total = consumos.aggregate(
        total=Sum('costo_almuerzo')
    )['total'] or Decimal('0.00')
    
    # Crear cuenta
    cuenta = CuentasAlmuerzoMensual.objects.create(
        id_hijo=hijo,
        anio=anio,
        mes=mes,
        cantidad_almuerzos=cantidad,
        monto_total=monto_total,
        forma_cobro='Cuenta Corriente',
        monto_pagado=Decimal('0.00'),
        estado='Pendiente',
        fecha_generacion=date.today()
    )
    
    # Marcar consumos como procesados
    consumos.update(marcado_en_cuenta=True)
    
    return cuenta
```

### 3. Alertas de Alérgenos

```python
def obtener_alertas_alergenos(hijo):
    """
    Obtiene alertas de alérgenos basadas en restricciones del hijo
    """
    # Obtener restricciones críticas
    restricciones_criticas = RestriccionesHijos.objects.filter(
        id_hijo=hijo,
        activo=True,
        severidad='Crítica'
    )
    
    alertas = []
    for restriccion in restricciones_criticas:
        # Buscar alérgenos relacionados
        alergenos = Alergenos.objects.filter(
            nombre__icontains=restriccion.tipo_restriccion,
            nivel_severidad__in=['Alta', 'Crítica'],
            activo=True
        )
        
        for alergeno in alergenos:
            # Buscar productos que contienen este alérgeno
            productos = ProductosAlergenos.objects.filter(
                id_alergeno=alergeno,
                contiene=True
            ).select_related('id_producto')
            
            if productos.exists():
                alertas.append({
                    'restriccion': restriccion,
                    'alergeno': alergeno,
                    'productos_peligrosos': [p.id_producto for p in productos],
                    'nivel_riesgo': 'CRÍTICO'
                })
    
    return alertas
```

### 4. Dashboard de Consumo

```python
def obtener_dashboard_almuerzos(hijo, anio, mes=None):
    """
    Genera un dashboard con métricas de almuerzos
    """
    from django.db.models import Avg, Count
    
    # Base queryset
    qs = RegistrosConsumoAlmuerzo.objects.filter(
        id_hijo=hijo,
        fecha_consumo__year=anio
    )
    
    if mes:
        qs = qs.filter(fecha_consumo__month=mes)
    
    # Métricas
    dashboard = {
        'total_consumos': qs.filter(estado='Confirmado').count(),
        'consumos_rechazados': qs.filter(estado='Rechazado').count(),
        'costo_promedio': qs.filter(estado='Confirmado').aggregate(
            Avg('costo_almuerzo')
        )['costo_almuerzo__avg'] or 0,
        'costo_total': qs.filter(estado='Confirmado').aggregate(
            Sum('costo_almuerzo')
        )['costo_almuerzo__sum'] or 0,
        'consumos_por_mes': qs.filter(estado='Confirmado').values('fecha_consumo__month').annotate(
            cantidad=Count('id_registro_consumo')
        ),
        'tasa_asistencia': None  # Calcular basado en días hábiles del plan
    }
    
    # Calcular tasa de asistencia si hay suscripción activa
    suscripcion = SuscripcionesAlmuerzo.objects.filter(
        id_hijo=hijo,
        estado='Activa'
    ).first()
    
    if suscripcion:
        dias_plan = len(suscripcion.id_plan_almuerzo.dias_semana_incluidos.split(','))
        dias_mes = 4.33 * dias_plan  # Promedio semanal * 4.33 semanas/mes
        if dias_mes > 0:
            dashboard['tasa_asistencia'] = (dashboard['total_consumos'] / dias_mes) * 100
    
    return dashboard
```

---

## Integración con otros Módulos

### Con Clientes (Hijos)

```python
# Obtener todos los hijos de un cliente con suscripción activa
from apps.clientes.models import Clientes, Hijos
from apps.almuerzos.models import SuscripcionesAlmuerzo

cliente = Clientes.objects.get(id_cliente=1)
hijos_suscritos = Hijos.objects.filter(
    id_cliente_responsable=cliente,
    suscripciones__estado='Activa'
).distinct()

# Generar cuenta consolidada familiar
for hijo in hijos_suscritos:
    cuenta = generar_cuenta_mensual(hijo, 2024, 3)
```

### Con Productos

```python
# Verificar alérgenos antes de servir un producto
from apps.productos.models import Productos
from apps.almuerzos.models import ProductosAlergenos

def puede_consumir_producto(hijo, producto):
    """
    Verifica si un hijo puede consumir un producto
    """
    # Obtener alérgenos del producto
    alergenos = ProductosAlergenos.objects.filter(
        id_producto=producto,
        contiene=True
    ).values_list('id_alergeno__nombre', flat=True)
    
    # Verificar restricciones del hijo
    restricciones = RestriccionesHijos.objects.filter(
        id_hijo=hijo,
        activo=True,
        severidad__in=['Alta', 'Crítica']
    )
    
    for restriccion in restricciones:
        for alergeno in alergenos:
            if alergeno.lower() in restriccion.tipo_restriccion.lower():
                return False, f"Contiene {alergeno} (restricción: {restriccion.tipo_restriccion})"
    
    return True, "Producto seguro"
```

### Con Ventas

```python
# Crear venta desde pago de almuerzo
from apps.ventas.models import Ventas
from apps.almuerzos.models import PagosAlmuerzoMensual

def crear_venta_desde_pago_almuerzo(pago_almuerzo):
    """
    Crea una venta cuando se paga una suscripción de almuerzo
    """
    venta = Ventas.objects.create(
        id_cliente=pago_almuerzo.id_suscripcion.id_hijo.id_cliente_responsable,
        tipo_venta='Servicio',
        metodo_pago='Efectivo',
        monto_total=pago_almuerzo.monto_pagado,
        estado_pago='Pagado',
        observaciones=f"Pago de almuerzo - Mes: {pago_almuerzo.mes_pagado}"
    )
    
    # Asociar venta al pago
    pago_almuerzo.id_venta = venta
    pago_almuerzo.save()
    
    return venta
```

### Con Core (Tarjetas)

```python
# Registrar consumo mediante tarjeta
from apps.core.models import Tarjetas
from apps.almuerzos.models import RegistrosConsumoAlmuerzo

def registrar_consumo_con_tarjeta(codigo_tarjeta):
    """
    Registra un consumo escaneando una tarjeta
    """
    try:
        tarjeta = Tarjetas.objects.get(codigo_barra=codigo_tarjeta, estado='Activa')
        hijo = tarjeta.id_hijo
        
        # Verificar suscripción activa
        suscripcion = SuscripcionesAlmuerzo.objects.filter(
            id_hijo=hijo,
            estado='Activa'
        ).first()
        
        if not suscripcion:
            return None, "No tiene suscripción activa"
        
        # Registrar consumo
        registro = RegistrosConsumoAlmuerzo.objects.create(
            id_hijo=hijo,
            id_suscripcion=suscripcion,
            nro_tarjeta=tarjeta,
            fecha_consumo=date.today(),
            hora_registro=time.now().time(),
            estado='Confirmado'
        )
        
        return registro, "Consumo registrado exitosamente"
        
    except Tarjetas.DoesNotExist:
        return None, "Tarjeta no válida"
```

---

## Métricas y Reportes

### Dashboard de Almuerzos (Ejemplo)

```python
{
    'periodo': 'Marzo 2024',
    'total_suscripciones_activas': 250,
    'total_consumos_mes': 4850,
    'promedio_consumos_dia': 242,
    'costo_promedio_almuerzo': 18500.00,
    'ingreso_total_mes': 89325000.00,
    'cuentas_pendientes': 45,
    'cuentas_pagadas': 205,
    'tasa_cobro': 82.0,  # % de cuentas pagadas
    'alergenos_registrados': 15,
    'alergenos_criticos': 3,
    'productos_con_restricciones': 127,
    'alertas_restricciones_activas': 8
}
```

---

## Changelog

### Versión 1.0.0 (2024-03-01)

**Nuevo**:
- ✅ 9 modelos completos con relaciones
- ✅ 30 validadores con reglas de negocio
- ✅ 122 tests (100% PASS en 0.305s)
- ✅ Panel de administración con 9 modelos
- ✅ Sistema de alérgenos con severidad
- ✅ Gestión de cuentas mensuales
- ✅ Integración con Clientes, Productos, Ventas, Core
- ✅ Dashboard de métricas
- ✅ Documentación completa

---

## Próximas Mejoras

1. **Notificaciones automáticas**:
   - Recordatorios de pago de cuentas vencidas
   - Alertas de alérgenos al registrar consumo
   - Notificación a padres de consumos diarios

2. **Reportes avanzados**:
   - Reporte nutricional por estudiante
   - Análisis de preferencias alimentarias
   - Predicción de consumo mensual

3. **Mejoras de UX**:
   - Calendario visual de consumos
   - Gráficos de asistencia por hijo
   - Comparativa de planes de almuerzo

4. **Seguridad**:
   - Auditoría de cambios en alérgenos
   - Confirmación doble para restricciones críticas
   - Bloqueo de productos peligrosos según restricciones

---

## Soporte

Para más información o reportar problemas:
- Email: soporte@cantinatita.edu.py
- Documentación: `/docs/almuerzos/`
- Issues: `/backend/apps/almuerzos/issues/`

---

**Módulo Almuerzos - Cantina Tita Backend v1.0.0**  
Última actualización: 2024-03-01
