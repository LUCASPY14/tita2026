# 📦 Módulo de Productos

## Descripción General

El módulo de **Productos** gestiona el catálogo completo de productos de la cantina, incluyendo categorización jerárquica, unidades de medida, listas de precios diferenciadas y auditoría de cambios de precios.

### Funcionalidades Principales

- ✅ **Gestión de Productos**: Código de barras, descripción, stock mínimo, categorización
- ✅ **Categorías Jerárquicas**: Organización multinivel (padre-hijo)
- ✅ **Unidades de Medida**: Kg, litros, unidades, etc.
- ✅ **Listas de Precios**: Minorista, mayorista, estudiantes, etc.
- ✅ **Precios Diferenciados**: Precio por producto según lista
- ✅ **Histórico de Precios**: Auditoría completa de cambios con variación porcentual
- ✅ **24 Validadores**: Validación exhaustiva de reglas de negocio
- ✅ **76 Tests**: Cobertura completa de validadores
- ✅ **Admin UI Avanzada**: Badges, jerarquías visuales, acciones batch

---

## 📋 Modelos

### 1. Productos

Información completa de cada producto del catálogo.

**Campos**:
- `id_producto` (AutoField): ID único del producto
- `codigo_barra` (CharField, 50): Código de barras (EAN-13, EAN-8, UPC, o interno)
- `descripcion` (CharField, 255): Nombre/descripción del producto
- `stock_minimo` (DecimalField, 10, 3): Stock mínimo para alertas
- `permite_stock_negativo` (BooleanField): Permitir vender sin stock
- `activo` (BooleanField): Estado del producto
- `id_categoria` (ForeignKey): Categoría del producto
- `id_impuesto` (ForeignKey): Impuesto aplicable (10%, 5%, 0%)
- `id_unidad_medida` (ForeignKey): Unidad de medida

**Propiedades**:
- `stock_actual`: Stock actual desde módulo de inventario
- `requiere_reposicion`: True si stock < stock_minimo

**Ejemplo**:
```python
from apps.productos.models import Productos
from decimal import Decimal

producto = Productos.objects.create(
    codigo_barra='7891234567890',
    descripcion='Coca Cola 500ml',
    stock_minimo=Decimal('10.000'),
    permite_stock_negativo=False,
    activo=True,
    id_categoria=categoria_bebidas,
    id_impuesto=impuesto_10,
    id_unidad_medida=unidad_unidad
)

print(producto)  # "7891234567890 - Coca Cola 500ml"
print(f"Requiere reposición: {producto.requiere_reposicion}")
```

**Validadores Aplicables**:
- `validar_codigo_barra(codigo)`
- `validar_descripcion_producto(descripcion)`
- `validar_stock_minimo(stock_minimo)`
- `validar_cambio_estado_producto(producto, nuevo_estado)`
- `validar_producto_unico(descripcion, codigo_barra, producto_id)`

---

### 2. Categorias

Organización jerárquica de productos (padre-hijo).

**Campos**:
- `id_categoria` (AutoField): ID único de la categoría
- `nombre` (CharField, 100): Nombre de la categoría
- `activo` (BooleanField): Estado de la categoría
- `id_categoria_padre` (ForeignKey self): Categoría padre (NULL para raíz)

**Propiedades**:
- `es_categoria_raiz`: True si no tiene padre

**Ejemplo**:
```python
from apps.productos.models import Categorias

# Crear categoría raíz
bebidas = Categorias.objects.create(
    nombre='Bebidas',
    activo=True
)

# Crear subcategoría
gaseosas = Categorias.objects.create(
    nombre='Gaseosas',
    activo=True,
    id_categoria_padre=bebidas
)

print(gaseosas)  # "Bebidas > Gaseosas"
print(f"Es raíz: {gaseosas.es_categoria_raiz}")  # False

# Acceder a subcategorías desde padre
print(bebidas.subcategorias.all())  # [<Categorias: Gaseosas>]
```

**Validadores Aplicables**:
- `validar_nombre_categoria(nombre)`
- `validar_jerarquia_categoria(categoria_padre, categoria_actual_id)`
- `validar_categoria_activa_con_productos(categoria)`

---

### 3. UnidadesMedida

Unidades de medida para productos (Kg, L, UN, etc.).

**Campos**:
- `id_unidad_medida` (AutoField): ID único de la unidad
- `nombre` (CharField, 50): Nombre completo (Kilogramo, Litro)
- `abreviatura` (CharField, 10): Abreviatura (Kg, L, UN)
- `activo` (BooleanField): Estado de la unidad

**Ejemplo**:
```python
from apps.productos.models import UnidadesMedida

# Crear unidades de medida
unidades = [
    UnidadesMedida.objects.create(nombre='Kilogramo', abreviatura='Kg', activo=True),
    UnidadesMedida.objects.create(nombre='Litro', abreviatura='L', activo=True),
    UnidadesMedida.objects.create(nombre='Unidad', abreviatura='UN', activo=True),
    UnidadesMedida.objects.create(nombre='Gramo', abreviatura='g', activo=True),
    UnidadesMedida.objects.create(nombre='Metro cúbico', abreviatura='m³', activo=True),
]

print(unidades[0])  # "Kilogramo (Kg)"
```

**Validadores Aplicables**:
- `validar_nombre_unidad(nombre)`
- `validar_abreviatura_unidad(abreviatura)`
- `validar_unidad_activa_con_productos(unidad)`

---

### 4. ListasPrecios

Listas de precios diferenciadas (minorista, mayorista, etc.).

**Campos**:
- `id_lista` (AutoField): ID único de la lista
- `nombre_lista` (CharField, 100): Nombre de la lista
- `fecha_vigencia` (DateField): Fecha desde la cual es válida
- `moneda` (CharField, 3): Código de moneda (PYG, USD, EUR, BRL, ARS)
- `activo` (BooleanField): Estado de la lista

**Ejemplo**:
```python
from apps.productos.models import ListasPrecios
from django.utils import timezone

# Crear listas de precios
lista_minorista = ListasPrecios.objects.create(
    nombre_lista='Minorista',
    fecha_vigencia=timezone.now().date(),
    moneda='PYG',
    activo=True
)

lista_mayorista = ListasPrecios.objects.create(
    nombre_lista='Mayorista (10+ unidades)',
    fecha_vigencia=timezone.now().date(),
    moneda='PYG',
    activo=True
)

lista_estudiantes = ListasPrecios.objects.create(
    nombre_lista='Estudiantes',
    fecha_vigencia=timezone.now().date(),
    moneda='PYG',
    activo=True
)

print(lista_minorista)  # "Minorista (PYG)"
```

**Validadores Aplicables**:
- `validar_nombre_lista_precios(nombre)`
- `validar_fecha_vigencia_lista(fecha_vigencia)`
- `validar_moneda_lista(moneda)`
- `validar_lista_activa_con_precios(lista)`

---

### 5. PreciosPorLista

Precios específicos de cada producto según la lista.

**Campos**:
- `id_precio` (AutoField): ID único del precio
- `precio_unitario` (DecimalField, 12, 2): Precio en esta lista
- `fecha_vigencia` (DateTimeField): Vigencia del precio
- `id_lista` (ForeignKey): Lista de precios
- `id_producto` (ForeignKey): Producto

**Restricciones**:
- `unique_together`: `(id_producto, id_lista)` - Un precio por combinación

**Ejemplo**:
```python
from apps.productos.models import PreciosPorLista
from decimal import Decimal

# Asignar precios a un producto en diferentes listas
precio_minorista = PreciosPorLista.objects.create(
    precio_unitario=Decimal('5000.00'),
    id_lista=lista_minorista,
    id_producto=coca_cola
)

precio_mayorista = PreciosPorLista.objects.create(
    precio_unitario=Decimal('4500.00'),
    id_lista=lista_mayorista,
    id_producto=coca_cola
)

precio_estudiantes = PreciosPorLista.objects.create(
    precio_unitario=Decimal('4200.00'),
    id_lista=lista_estudiantes,
    id_producto=coca_cola
)

print(precio_minorista)  # "Coca Cola - Minorista: $5000.00"

# Acceder precios desde producto
precios = coca_cola.precios.all()
print(f"Total listas: {precios.count()}")  # 3
```

**Validadores Aplicables**:
- `validar_precio_unitario_lista(precio_unitario)`
- `validar_unicidad_precio_lista(id_producto, id_lista, id_precio)`
- `validar_variacion_precio(precio_nuevo, precio_anterior, max_variacion)`

---

### 6. HistoricoPrecios

Auditoría de cambios de precios de productos.

**Campos**:
- `id_historico` (BigAutoField): ID único del registro
- `precio_anterior` (DecimalField, 12, 2): Precio antes del cambio
- `precio_nuevo` (DecimalField, 12, 2): Precio después del cambio
- `fecha_cambio` (DateTimeField): Cuándo se hizo el cambio
- `id_empleado` (ForeignKey): Empleado que hizo el cambio (opcional)
- `id_producto` (ForeignKey): Producto afectado

**Propiedades**:
- `variacion_porcentual`: Calcula % de cambio

**Ejemplo**:
```python
from apps.productos.models import HistoricoPrecios
from decimal import Decimal

# Registrar cambio de precio
historico = HistoricoPrecios.objects.create(
    precio_anterior=Decimal('5000.00'),
    precio_nuevo=Decimal('5500.00'),
    id_producto=coca_cola,
    id_empleado=empleado_admin
)

print(historico)  # "Coca Cola: $5000.00 → $5500.00"
print(f"Variación: {historico.variacion_porcentual:.1f}%")  # 10.0%

# Consultar histórico de un producto
historial = HistoricoPrecios.objects.filter(
    id_producto=coca_cola
).order_by('-fecha_cambio')[:10]

for cambio in historial:
    print(f"{cambio.fecha_cambio.strftime('%d/%m/%Y')}: ₲{cambio.precio_anterior:,.0f} → ₲{cambio.precio_nuevo:,.0f} ({cambio.variacion_porcentual:+.1f}%)")
```

**Validadores Aplicables**:
- `validar_cambio_precio_historico(precio_anterior, precio_nuevo)`
- `validar_fecha_cambio_precio(fecha_cambio)`

---

## ✅ Validadores

El módulo incluye **24 validadores** organizados en 6 categorías:

### Validadores de Productos (8)

#### `validar_codigo_barra(codigo)`
Valida formato del código de barras.

**Formatos soportados**:
- EAN-13: 13 dígitos
- EAN-8: 8 dígitos
- UPC: 12 dígitos
- Código interno: alfanumérico 4-20 caracteres

**Ejemplo**:
```python
from apps.productos.validators import validar_codigo_barra

validar_codigo_barra('7891234567890')  # EAN-13 ✅
validar_codigo_barra('12345678')       # EAN-8 ✅
validar_codigo_barra('PROD-001')       # Código interno ✅
validar_codigo_barra('123')            # ❌ ValidationError: muy corto
```

#### `validar_descripcion_producto(descripcion)`
Valida descripción del producto.

**Reglas**:
- Longitud: 3-255 caracteres
- Caracteres permitidos: letras, números, espacios, -, (), ., %

**Ejemplo**:
```python
from apps.productos.validators import validar_descripcion_producto

validar_descripcion_producto('Coca Cola 500ml')              # ✅
validar_descripcion_producto('Empanada de Carne (Picante)')  # ✅
validar_descripcion_producto('AB')                           # ❌ muy corto
```

#### `validar_stock_minimo(stock_minimo)`
Valida stock mínimo del producto.

**Reglas**:
- Debe ser >= 0
- No puede exceder 100,000
- Máximo 3 decimales

**Ejemplo**:
```python
from apps.productos.validators import validar_stock_minimo
from decimal import Decimal

validar_stock_minimo(Decimal('10.000'))    # ✅
validar_stock_minimo(Decimal('-1'))        # ❌ negativo
validar_stock_minimo(Decimal('10.1234'))   # ❌ demasiados decimales
```

#### `validar_precio_positivo(precio)`
Valida que el precio sea positivo y tenga formato correcto.

**Reglas**:
- Debe ser > 0
- No puede exceder ₲100,000,000
- Máximo 2 decimales

**Ejemplo**:
```python
from apps.productos.validators import validar_precio_positivo
from decimal import Decimal

validar_precio_positivo(Decimal('5000.00'))  # ✅
validar_precio_positivo(Decimal('0'))        # ❌ cero
validar_precio_positivo(Decimal('5000.123')) # ❌ demasiados decimales
```

#### `validar_cambio_estado_producto(producto, nuevo_estado)`
Valida que se pueda cambiar el estado de un producto.

**Reglas**:
- No se puede desactivar si tiene stock > 0 (salvo si permite stock negativo)

**Ejemplo**:
```python
from apps.productos.validators import validar_cambio_estado_producto

validar_cambio_estado_producto(producto, False)  # Intenta desactivar
# Valida si tiene stock, etc.
```

#### `validar_margen_utilidad(precio_venta, costo_compra, margen_minimo=10)`
Valida que el margen de utilidad sea razonable.

**Reglas**:
- Precio de venta > costo de compra
- Margen mínimo 10% (configurable)
- Alerta si margen > 300%

**Ejemplo**:
```python
from apps.productos.validators import validar_margen_utilidad
from decimal import Decimal

validar_margen_utilidad(Decimal('5000'), Decimal('3000'))  # ✅ margen ~67%
validar_margen_utilidad(Decimal('105'), Decimal('100'))    # ❌ margen muy bajo (5%)
validar_margen_utilidad(Decimal('2000'), Decimal('3000'))  # ❌ vendiendo con pérdida
```

#### `validar_producto_unico(descripcion, codigo_barra, producto_id)`
Valida que no exista otro producto con la misma descripción o código.

**Ejemplo**:
```python
from apps.productos.validators import validar_producto_unico

validar_producto_unico('Coca Cola 500ml', '7890123', None)     # Nuevo producto ✅
validar_producto_unico('Coca Cola 500ml', '7890123', 5)        # Editar producto id=5 ✅
```

---

### Validadores de Categorías (3)

#### `validar_nombre_categoria(nombre)`
Valida el nombre de la categoría.

**Reglas**:
- Longitud: 3-100 caracteres
- Solo letras, números, espacios, guiones

**Ejemplo**:
```python
from apps.productos.validators import validar_nombre_categoria

validar_nombre_categoria('Bebidas')         # ✅
validar_nombre_categoria('Snacks Salados')  # ✅
validar_nombre_categoria('AB')              # ❌ muy corto
```

#### `validar_jerarquia_categoria(categoria_padre, categoria_actual_id)`
Valida que no se creen ciclos en la jerarquía.

**Ciclo inválido**: A es padre de B, B es padre de C, C es padre de A

**Ejemplo**:
```python
from apps.productos.validators import validar_jerarquia_categoria

validar_jerarquia_categoria(bebidas, None)            # Nueva categoría raíz ✅
validar_jerarquia_categoria(bebidas, gaseosas.id)     # Gaseosas hija de Bebidas ✅
validar_jerarquia_categoria(gaseosas, bebidas.id)     # ❌ crearía ciclo
```

#### `validar_categoria_activa_con_productos(categoria)`
Valida que no se desactiven categorías con productos activos.

**Ejemplo**:
```python
from apps.productos.validators import validar_categoria_activa_con_productos

validar_categoria_activa_con_productos(categoria_vacia)       # ✅
validar_categoria_activa_con_productos(categoria_con_prods)   # ❌ tiene productos
```

---

### Validadores de Unidades de Medida (3)

#### `validar_nombre_unidad(nombre)`
Valida el nombre de la unidad.

**Reglas**:
- Longitud: 2-50 caracteres
- Solo letras y espacios

**Ejemplo**:
```python
from apps.productos.validators import validar_nombre_unidad

validar_nombre_unidad('Kilogramo')    # ✅
validar_nombre_unidad('Metro cúbico') # ✅
validar_nombre_unidad('Kilo123')      # ❌ contiene números
```

#### `validar_abreviatura_unidad(abreviatura)`
Valida la abreviatura de la unidad.

**Reglas**:
- Longitud: 1-10 caracteres
- Solo letras, números, símbolos básicos (², ³, °)
- Sin espacios

**Ejemplo**:
```python
from apps.productos.validators import validar_abreviatura_unidad

validar_abreviatura_unidad('Kg')   # ✅
validar_abreviatura_unidad('m³')   # ✅
validar_abreviatura_unidad('K g')  # ❌ contiene espacio
```

#### `validar_unidad_activa_con_productos(unidad)`
Valida que no se desactiven unidades con productos activos.

---

### Validadores de Listas de Precios (4)

#### `validar_nombre_lista_precios(nombre)`
Valida el nombre de la lista de precios.

**Reglas**:
- Longitud: 3-100 caracteres
- Letras, números, espacios, -, (), +

**Ejemplo**:
```python
from apps.productos.validators import validar_nombre_lista_precios

validar_nombre_lista_precios('Minorista')              # ✅
validar_nombre_lista_precios('Mayorista (10+ unidades)')  # ✅
```

#### `validar_fecha_vigencia_lista(fecha_vigencia)`
Valida la fecha de vigencia de la lista.

**Reglas**:
- No puede ser > 1 año en el futuro
- Advertencia si es > 2 años en el pasado

**Ejemplo**:
```python
from apps.productos.validators import validar_fecha_vigencia_lista
from datetime import date, timedelta

validar_fecha_vigencia_lista(date.today())                     # ✅
validar_fecha_vigencia_lista(date.today() + timedelta(days=30))   # ✅
validar_fecha_vigencia_lista(date.today() + timedelta(days=400))  # ❌ muy futura
```

#### `validar_moneda_lista(moneda)`
Valida el código de moneda.

**Monedas soportadas**: PYG, USD, EUR, BRL, ARS

**Ejemplo**:
```python
from apps.productos.validators import validar_moneda_lista

validar_moneda_lista('PYG')  # ✅
validar_moneda_lista('USD')  # ✅
validar_moneda_lista('XYZ')  # ❌ no soportado
```

#### `validar_lista_activa_con_precios(lista)`
Advertencia si se desactiva lista con precios asignados.

---

### Validadores de Precios por Lista (3)

#### `validar_precio_unitario_lista(precio_unitario)`
Valida el precio unitario (reutiliza `validar_precio_positivo`).

#### `validar_unicidad_precio_lista(id_producto, id_lista, id_precio)`
Valida que no exista otro precio para la misma combinación producto-lista.

**Ejemplo**:
```python
from apps.productos.validators import validar_unicidad_precio_lista

validar_unicidad_precio_lista(producto.id, lista.id, None)     # Nuevo precio ✅
validar_unicidad_precio_lista(producto.id, lista.id, 10)       # Editar precio id=10 ✅
```

#### `validar_variacion_precio(precio_nuevo, precio_anterior, max_variacion=50)`
Valida que la variación de precio no sea excesiva.

**Reglas**:
- Variación > 50% genera advertencia
- Variación > 200% genera error

**Ejemplo**:
```python
from apps.productos.validators import validar_variacion_precio
from decimal import Decimal

validar_variacion_precio(Decimal('5500'), Decimal('5000'))  # +10% ✅
validar_variacion_precio(Decimal('8000'), Decimal('5000'))  # +60% ⚠️ warning
validar_variacion_precio(Decimal('20000'), Decimal('5000')) # +300% ❌ error
```

---

### Validadores de Histórico (2)

#### `validar_cambio_precio_historico(precio_anterior, precio_nuevo)`
Valida que el cambio de precio sea válido.

**Reglas**:
- Precios deben ser diferentes
- Ambos > 0
- Diferencia significativa (>₲1)

**Ejemplo**:
```python
from apps.productos.validators import validar_cambio_precio_historico
from decimal import Decimal

validar_cambio_precio_historico(Decimal('4000'), Decimal('5000'))  # ✅
validar_cambio_precio_historico(Decimal('5000'), Decimal('5000'))  # ❌ iguales
```

#### `validar_fecha_cambio_precio(fecha_cambio)`
Valida que la fecha de cambio sea razonable.

**Reglas**:
- No puede ser futura
- No puede ser > 5 años antigua

---

## 🧪 Tests

El módulo incluye **76 tests** organizados en 18 clases que cubren todos los validadores.

### Ejecutar Tests

```bash
# Todos los tests de validadores
python manage.py test apps.productos.tests_validators --verbosity=2

# Todos los tests del módulo
python manage.py test apps.productos --verbosity=2

# Tests específicos
python manage.py test apps.productos.tests_validators.ValidadoresCodigoBarraTestCase --verbosity=2
```

### Resultados Esperados

```
Found 76 test(s).
Ran 76 tests in 0.138s
OK
```

### Cobertura de Tests

**Validadores de Productos (36 tests)**:
- ValidadoresCodigoBarraTestCase (9 tests)
- ValidadoresDescripcionProductoTestCase (5 tests)
- ValidadoresStockMinimoTestCase (4 tests)
- ValidadoresPrecioPositivoTestCase (5 tests)
- ValidadoresMargenUtilidadTestCase (5 tests)
- ValidadoresConModelosTestCase (8 tests)

**Validadores de Categorías (8 tests)**:
- ValidadoresNombreCategoriaTestCase (4 tests)
- ValidadoresJerarquiaCategoriaTestCase (4 tests)

**Validadores de Unidades (8 tests)**:
- ValidadoresNombreUnidadTestCase (4 tests)
- ValidadoresAbreviaturaUnidadTestCase (4 tests)

**Validadores de Listas de Precios (13 tests)**:
- ValidadoresNombreListaPreciosTestCase (3 tests)
- ValidadoresFechaVigenciaListaTestCase (5 tests)
- ValidadoresMonedaListaTestCase (5 tests)

**Validadores de Precios y Histórico (11 tests)**:
- ValidadoresVariacionPrecioTestCase (4 tests)
- ValidadoresCambioPrecioHistoricoTestCase (4 tests)
- ValidadoresFechaCambioPrecioTestCase (3 tests)

---

## 🎨 Admin UI

El módulo incluye una interfaz de administración avanzada con:

### Características Destacadas

1. **Categorías**:
   - Visualización jerárquica con indentación
   - Iconos (📁 para carpetas, 📄 para hojas)
   - Badges de nivel jerárquico (Raíz, Nivel 1, Nivel 2...)
   - Total de productos por categoría
   - Link a categoría padre
   - Actions: activar/desactivar categorías

2. **Unidades de Medida**:
   - Abreviatura en badge
   - Total de productos por unidad
   - Estado coloreado

3. **Productos**:
   - Código de barras en <code>
   - Categoría en tag coloreado
   - IVA destacado
   - Stock mínimo formateado
   - Icono para stock negativo permitido
   - Actions: activar, desactivar, duplicar

4. **Listas de Precios**:
   - Nombre en badge coloreado
   - Moneda con símbolo (₲, $, €, R$)
   - Fecha de vigencia coloreada (futuro, hoy, pasado)
   - Total de precios + promedio
   - Date hierarchy

5. **Precios por Lista**:
   - Información completa del producto
   - Lista en badge
   - Precio formateado con símbolo de moneda
   - Variación vs precio anterior (▲ aumento, ▼ disminución)

6. **Histórico de Precios**:
   - Link al producto
   - Precios anterior y nuevo formateados
   - Flecha indicando cambio
   - Variación porcentual en badge coloreado
   - Empleado que registró el cambio
   - Date hierarchy

---

## 📊 Ejemplos de Uso

### Ejemplo 1: Crear Producto Completo

```python
from apps.productos.models import Productos, Categorias, UnidadesMedida
from apps.contabilidad.models import Impuestos
from apps.productos.validators import validar_codigo_barra, validar_descripcion_producto, validar_stock_minimo
from decimal import Decimal
from django.core.exceptions import ValidationError

# 1. Crear categoría
bebidas = Categorias.objects.create(
    nombre='Bebidas',
    activo=True
)

# 2. Crear unidad de medida
unidad = UnidadesMedida.objects.create(
    nombre='Unidad',
    abreviatura='UN',
    activo=True
)

# 3. Obtener impuesto
impuesto_10 = Impuestos.objects.get(porcentaje=Decimal('10.00'))

# 4. Validar datos
codigo = '7891234567890'
descripcion = 'Coca Cola 500ml'
stock_min = Decimal('10.000')

try:
    validar_codigo_barra(codigo)
    validar_descripcion_producto(descripcion)
    validar_stock_minimo(stock_min)
except ValidationError as e:
    print(f"Error de validación: {e}")
    exit(1)

# 5. Crear producto
producto = Productos.objects.create(
    codigo_barra=codigo,
    descripcion=descripcion,
    stock_minimo=stock_min,
    permite_stock_negativo=False,
    activo=True,
    id_categoria=bebidas,
    id_impuesto=impuesto_10,
    id_unidad_medida=unidad
)

print(f"Producto creado: {producto}")
print(f"ID: {producto.id_producto}")
```

### Ejemplo 2: Configurar Listas de Precios con Precios Diferenciados

```python
from apps.productos.models import ListasPrecios, PreciosPorLista
from apps.productos.validators import validar_nombre_lista_precios, validar_moneda_lista, validar_precio_unitario_lista
from django.utils import timezone
from decimal import Decimal

# 1. Crear listas de precios
listas = []

for nombre, moneda in [
    ('Minorista', 'PYG'),
    ('Mayorista (10+ unidades)', 'PYG'),
    ('Estudiantes', 'PYG'),
]:
    validar_nombre_lista_precios(nombre)
    validar_moneda_lista(moneda)
    
    lista = ListasPrecios.objects.create(
        nombre_lista=nombre,
        fecha_vigencia=timezone.now().date(),
        moneda=moneda,
        activo=True
    )
    listas.append(lista)
    print(f"Lista creada: {lista}")

# 2. Asignar precios diferenciados
precios = [
    (listas[0], Decimal('5000.00')),   # Minorista
    (listas[1], Decimal('4500.00')),   # Mayorista (-10%)
    (listas[2], Decimal('4200.00')),   # Estudiantes (-16%)
]

for lista, precio in precios:
    validar_precio_unitario_lista(precio)
    
    precio_obj = PreciosPorLista.objects.create(
        precio_unitario=precio,
        id_lista=lista,
        id_producto=producto
    )
    print(f"{lista.nombre_lista}: ₲{precio:,.2f}")

# 3. Consultar precios de un producto
print(f"\nPrecios de {producto.descripcion}:")
for precio in producto.precios.all():
    print(f"  - {precio.id_lista.nombre_lista}: ₲{precio.precio_unitario:,.2f}")
```

### Ejemplo 3: Registrar Cambio de Precio con Validación

```python
from apps.productos.models import HistoricoPrecios
from apps.productos.validators import validar_cambio_precio_historico, validar_variacion_precio
from decimal import Decimal

# Producto actual con precio
precio_actual = PreciosPorLista.objects.get(
    id_producto=producto,
    id_lista=lista_minorista
)

precio_anterior = precio_actual.precio_unitario
precio_nuevo = Decimal('5500.00')

# 1. Validar cambio
try:
    validar_cambio_precio_historico(precio_anterior, precio_nuevo)
    validar_variacion_precio(precio_nuevo, precio_anterior, max_variacion=50)
except ValidationError as e:
    print(f"Error: {e}")
    exit(1)

# 2. Actualizar precio
precio_actual.precio_unitario = precio_nuevo
precio_actual.save()

# 3. Registrar en histórico
historico = HistoricoPrecios.objects.create(
    precio_anterior=precio_anterior,
    precio_nuevo=precio_nuevo,
    id_producto=producto,
    id_empleado=empleado  # Si está disponible
)

print(f"Cambio registrado: {historico}")
print(f"Variación: {historico.variacion_porcentual:.1f}%")
```

### Ejemplo 4: Consultar Productos por Categoría con Jerarquía

```python
from apps.productos.models import Categorias, Productos

# 1. Crear jerarquía de categorías
bebidas = Categorias.objects.create(nombre='Bebidas', activo=True)
gaseosas = Categorias.objects.create(nombre='Gaseosas', activo=True, id_categoria_padre=bebidas)
jugos = Categorias.objects.create(nombre='Jugos', activo=True, id_categoria_padre=bebidas)

# 2. Asignar productos a subcategorías
productos_gaseosas = Productos.objects.filter(id_categoria=gaseosas)
productos_jugos = Productos.objects.filter(id_categoria=jugos)

# 3. Consultar todos los productos de Bebidas (incluyendo subcategorías)
from django.db.models import Q

def productos_por_categoria_recursivo(categoria):
    """Obtiene productos de una categoría y todas sus subcategorías"""
    categorias_ids = [categoria.id_categoria]
    
    # Agregar IDs de subcategorías
    def agregar_subcategorias(cat):
        for subcat in cat.subcategorias.filter(activo=True):
            categorias_ids.append(subcat.id_categoria)
            agregar_subcategorias(subcat)
    
    agregar_subcategorias(categoria)
    
    return Productos.objects.filter(
        id_categoria_id__in=categorias_ids,
        activo=True
    )

productos_bebidas = productos_por_categoria_recursivo(bebidas)
print(f"Total productos en Bebidas (incluyendo subcategorías): {productos_bebidas.count()}")

for producto in productos_bebidas:
    print(f"  - {producto.descripcion} ({producto.id_categoria.nombre})")
```

---

## 📈 Métricas y Reportes

### Dashboard de Productos

```python
from apps.productos.models import Productos, Categorias, PreciosPorLista
from django.db.models import Count, Avg, Min, Max, Sum
from decimal import Decimal

# Métricas generales
metricas = {
    'total_productos': Productos.objects.filter(activo=True).count(),
    'total_categorias': Categorias.objects.filter(activo=True).count(),
    'productos_sin_codigo': Productos.objects.filter(activo=True, codigo_barra__isnull=True).count(),
    'productos_stock_negativo': Productos.objects.filter(activo=True, permite_stock_negativo=True).count(),
}

# Productos por categoría
productos_por_categoria = Categorias.objects.filter(activo=True).annotate(
    total_productos=Count('productos', filter=Q(productos__activo=True))
).order_by('-total_productos')

# Precios promedio por lista
precios_por_lista = ListasPrecios.objects.filter(activo=True).annotate(
    total_productos=Count('precios'),
    precio_promedio=Avg('precios__precio_unitario'),
    precio_minimo=Min('precios__precio_unitario'),
    precio_maximo=Max('precios__precio_unitario'),
).values('nombre_lista', 'total_productos', 'precio_promedio', 'precio_minimo', 'precio_maximo')

print("=== DASHBOARD DE PRODUCTOS ===")
print(f"Total productos activos: {metricas['total_productos']}")
print(f"Total categorías activas: {metricas['total_categorias']}")
print(f"Productos sin código: {metricas['productos_sin_codigo']}")
print(f"Productos con stock negativo: {metricas['productos_stock_negativo']}")

print("\n=== PRODUCTOS POR CATEGORÍA ===")
for categoria in productos_por_categoria[:10]:
    print(f"{categoria.nombre}: {categoria.total_productos} productos")

print("\n=== PRECIOS POR LISTA ===")
for lista in precios_por_lista:
    print(f"{lista['nombre_lista']}:")
    print(f"  Productos: {lista['total_productos']}")
    print(f"  Promedio: ₲{lista['precio_promedio']:,.2f}")
    print(f"  Rango: ₲{lista['precio_minimo']:,.2f} - ₲{lista['precio_maximo']:,.2f}")
```

### Reporte de Cambios de Precio

```python
from apps.productos.models import HistoricoPrecios
from django.utils import timezone
from datetime import timedelta

# Cambios de precio en el último mes
hace_un_mes = timezone.now() - timedelta(days=30)

cambios = HistoricoPrecios.objects.filter(
    fecha_cambio__gte=hace_un_mes
).select_related('id_producto', 'id_empleado').order_by('-fecha_cambio')

print("=== CAMBIOS DE PRECIO (ÚLTIMO MES) ===")
for cambio in cambios:
    producto = cambio.id_producto
    empleado = cambio.id_empleado
    
    print(f"{cambio.fecha_cambio.strftime('%d/%m/%Y')} - {producto.descripcion}")
    print(f"  ₲{cambio.precio_anterior:,.2f} → ₲{cambio.precio_nuevo:,.2f} ({cambio.variacion_porcentual:+.1f}%)")
    if empleado:
        print(f"  Por: {empleado.nombre} {empleado.apellido}")
    print()
```

---

## 🔄 Integración con Otros Módulos

### Con Inventario

```python
# El producto tiene propiedad stock_actual que consulta inventario
producto = Productos.objects.get(id_producto=1)

if producto.requiere_reposicion:
    print(f"⚠️ {producto.descripcion} requiere reposición")
    print(f"Stock actual: {producto.stock_actual}")
    print(f"Stock mínimo: {producto.stock_minimo}")
```

### Con Ventas

```python
# Los precios por lista se usan en ventas para calcular totales
from apps.ventas.models import Ventas, DetallesVenta

venta = Ventas.objects.create(
    id_cliente=cliente,
    id_lista=lista_minorista,
    # ...
)

# Obtener precio del producto según lista
precio = PreciosPorLista.objects.get(
    id_producto=producto,
    id_lista=lista_minorista
)

detalle = DetallesVenta.objects.create(
    id_venta=venta,
    id_producto=producto,
    cantidad=Decimal('2'),
    precio_unitario=precio.precio_unitario,
    # ...
)
```

### Con Compras

```python
# Al registrar una compra se puede calcular margen de utilidad
from apps.compras.models import Compras, DetallesCompra

detalle_compra = DetallesCompra.objects.get(id_producto=producto)
precio_venta = PreciosPorLista.objects.get(id_producto=producto, id_lista=lista_minorista)

# Validar margen
from apps.productos.validators import validar_margen_utilidad

validar_margen_utilidad(
    precio_venta.precio_unitario,
    detalle_compra.costo_unitario,
    margen_minimo=15
)
```

---

## 🛡️ Best Practices

1. **Siempre validar antes de guardar**:
   ```python
   from django.core.exceptions import ValidationError
   
   try:
       validar_codigo_barra(codigo)
       validar_descripcion_producto(descripcion)
       # ... más validaciones
       producto.save()
   except ValidationError as e:
       # Manejar error
       pass
   ```

2. **Usar transacciones para operaciones complejas**:
   ```python
   from django.db import transaction
   
   with transaction.atomic():
       producto.save()
       # Crear precios en todas las listas
       for lista in listas:
           PreciosPorLista.objects.create(...)
   ```

3. **Registrar cambios de precio**:
   ```python
   # Siempre que se actualice un precio, registrar en histórico
   if precio_actual.precio_unitario != precio_nuevo:
       HistoricoPrecios.objects.create(
           precio_anterior=precio_actual.precio_unitario,
           precio_nuevo=precio_nuevo,
           id_producto=producto,
           id_empleado=request.user.empleado
       )
       precio_actual.precio_unitario = precio_nuevo
       precio_actual.save()
   ```

4. **Validar jerarquías antes de asignar categorías**:
   ```python
   from apps.productos.validators import validar_jerarquia_categoria
   
   validar_jerarquia_categoria(categoria_padre, categoria_actual.id_categoria)
   categoria_actual.id_categoria_padre = categoria_padre
   categoria_actual.save()
   ```

5. **Optimizar queries con select_related y prefetch_related**:
   ```python
   # Evitar N+1 queries
   productos = Productos.objects.select_related(
       'id_categoria',
       'id_impuesto',
       'id_unidad_medida'
   ).prefetch_related('precios__id_lista').filter(activo=True)
   ```

---

## 📝 Estado del Módulo

- ✅ **Modelos**: 6 modelos completos y documentados
- ✅ **Validadores**: 24 validadores con lógica de negocio
- ✅ **Tests**: 76 tests, 100% PASS
- ✅ **Admin**: UI avanzada con badges, jerarquías, acciones
- ✅ **Documentación**: README completo con ejemplos
- ✅ **Cobertura**: 100% de validadores probados

**Estado**: ✅ **100% COMPLETO**
