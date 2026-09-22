# 📦 Módulo de Productos

## Descripción General

El módulo de **Productos** gestiona el catálogo completo de productos de la cantina, incluyendo categorización jerárquica, unidades de medida, listas de precios diferenciadas, impuestos y auditoría de cambios de precios.

### Funcionalidades Principales

- ✅ **Gestión de Productos**: Código de barras, código interno, descripción, stock mínimo, categorización
- ✅ **Categorías Jerárquicas**: Organización multinivel (padre-hijo)
- ✅ **Unidades de Medida**: Kg, litros, unidades, etc.
- ✅ **Listas de Precios**: Una lista activa por defecto (hoy "Lista General"); soporta varias listas en paralelo
- ✅ **Precios Diferenciados**: Precio por producto según lista, con histórico de cambios
- ✅ **Histórico de Precios**: Auditoría completa de cambios con variación porcentual
- ✅ **Impuestos**: Asignación de un impuesto por producto vía tabla intermedia
- ✅ **Admin UI**: Links entre modelos relacionados, badges de variación de precio

---

## 📋 Modelos

### 1. Producto

Información completa de cada producto del catálogo.

**Campos**:
- `id_producto` (BigAutoField): ID único del producto
- `codigo_barra` (CharField, 50, único, opcional): Código de barras para escaneo
- `codigo` (CharField, 50, único, opcional): Código interno del producto
- `descripcion` (CharField, 255): Nombre/descripción del producto
- `categoria` (ForeignKey → Categoria, PROTECT): Categoría del producto
- `unidad_medida` (ForeignKey → UnidadMedida, opcional): Unidad de medida
- `stock_minimo` (DecimalField, 10, 3): Cantidad mínima antes de generar alerta
- `permite_stock_negativo` (BooleanField): Permitir vender sin stock disponible
- `es_servicio` (BooleanField): True si no requiere stock físico
- `requiere_stock` (BooleanField): True si debe controlar stock
- `activo` (BooleanField)

**Propiedades**:
- `precio_actual`: precio de la lista por defecto activa (o de la primera lista disponible si no hay ninguna marcada por defecto)
- `stock_actual`: cantidad actual desde `apps.inventario.Stock`
- `requiere_reposicion`: `True` si `stock_actual < stock_minimo`

**Nota sobre impuestos**: `Producto` no tiene un campo `impuesto` directo — el vínculo es a través de `ProductoImpuesto` (ver más abajo), que en la práctica se usa como "a lo sumo un impuesto por producto" aunque el modelo permitiría varios.

**Ejemplo**:
```python
from apps.productos.models import Producto, Categoria, UnidadMedida
from decimal import Decimal

producto = Producto.objects.create(
    codigo_barra='7891234567890',
    descripcion='Coca Cola 500ml',
    categoria=categoria_bebidas,
    unidad_medida=unidad_unidad,
    stock_minimo=Decimal('10.000'),
    permite_stock_negativo=False,
    activo=True,
)

print(producto)  # "7891234567890 - Coca Cola 500ml"
print(f"Requiere reposición: {producto.requiere_reposicion}")
```

---

### 2. Categoria

Organización jerárquica de productos (padre-hijo).

**Campos**:
- `id_categoria` (BigAutoField)
- `nombre` (CharField, 100)
- `descripcion` (TextField, opcional)
- `categoria_padre` (ForeignKey self, opcional): categoría padre (`null` para raíz)
- `activo` (BooleanField)

**Propiedades**:
- `es_categoria_raiz`: `True` si no tiene `categoria_padre`

**Relaciones inversas útiles**: `categoria.subcategorias` (hijas directas), `categoria.productos` (productos de esa categoría, `related_name` del FK en `Producto`).

**Ejemplo**:
```python
from apps.productos.models import Categoria

bebidas = Categoria.objects.create(nombre='Bebidas', activo=True)
gaseosas = Categoria.objects.create(nombre='Gaseosas', activo=True, categoria_padre=bebidas)

print(gaseosas)  # "Bebidas > Gaseosas"
print(f"Es raíz: {gaseosas.es_categoria_raiz}")  # False
print(bebidas.subcategorias.all())  # [<Categoria: Bebidas > Gaseosas>]
```

---

### 3. UnidadMedida

Unidades de medida para productos (Kg, L, Un, etc.).

**Campos**:
- `id_unidad_medida` (BigAutoField)
- `nombre` (CharField, 50): nombre completo (Kilogramo, Litro)
- `abreviatura` (CharField, 10): abreviatura (Kg, L, Un)
- `activo` (BooleanField)

**Ejemplo**:
```python
from apps.productos.models import UnidadMedida

unidades = [
    UnidadMedida.objects.create(nombre='Kilogramo', abreviatura='Kg', activo=True),
    UnidadMedida.objects.create(nombre='Litro', abreviatura='L', activo=True),
    UnidadMedida.objects.create(nombre='Unidad', abreviatura='Un', activo=True),
]

print(unidades[0])  # "Kilogramo (Kg)"
```

---

### 4. ListaPrecio

Lista de precios diferenciada (hoy la cantina usa una sola lista activa por defecto, "Lista General"; el modelo soporta varias en paralelo).

**Campos**:
- `id_lista_precio` (BigAutoField)
- `nombre` (CharField, 100, único)
- `fecha_vigencia` (DateField, opcional)
- `moneda` (CharField, 3, default `"PYG"`)
- `activo` (BooleanField)
- `es_por_defecto` (BooleanField): la lista usada como referencia cuando no se especifica ninguna. `save()` se asegura de que **solo una** pueda tener `es_por_defecto=True` a la vez (al marcar una, desmarca cualquier otra automáticamente).

**Ejemplo**:
```python
from apps.productos.models import ListaPrecio

lista_general = ListaPrecio.objects.create(
    nombre='Lista General',
    moneda='PYG',
    activo=True,
    es_por_defecto=True,
)
print(lista_general)  # "Lista General (PYG)"
```

---

### 5. PrecioPorLista

Precio de un producto en una lista específica.

**Campos**:
- `id_precio_lista` (BigAutoField)
- `producto` (ForeignKey → Producto)
- `lista` (ForeignKey → ListaPrecio)
- `precio_unitario` (DecimalField, 12, 0 — Guaraníes, sin decimales)
- `fecha_vigencia` (DateTimeField, `auto_now_add=True` — se registra sola al crear el registro, no es editable a mano)

**Restricciones**: `unique_together (producto, lista)` — un precio por combinación.

**Ejemplo**:
```python
from apps.productos.models import PrecioPorLista
from decimal import Decimal

precio = PrecioPorLista.objects.create(
    producto=coca_cola,
    lista=lista_general,
    precio_unitario=Decimal('5000'),
)
print(precio)  # "7891234567890 - Coca Cola 500ml - Lista General (PYG): ₲5,000"

# Acceder a los precios de un producto en todas las listas
print(coca_cola.precios.all())
```

En la práctica, casi nunca se crea/edita `PrecioPorLista` a mano — se usa la acción
`POST /api/v1/productos/productos/{id}/set-precio/` (ver `ProductoViewSet.set_precio`
en `views.py`), que crea o actualiza el precio en la lista por defecto **y** registra
el cambio en `HistoricoPrecio` si el precio efectivamente cambió.

---

### 6. HistoricoPrecio

Auditoría de cambios de precios de productos.

**Campos**:
- `id_historico_precio` (BigAutoField)
- `producto` (ForeignKey → Producto)
- `precio_anterior` (DecimalField, 12, 0)
- `precio_nuevo` (DecimalField, 12, 0)
- `fecha_cambio` (DateTimeField, `auto_now_add=True`)
- `modificado_por` (ForeignKey → Usuario, opcional)

**Propiedades**:
- `variacion_porcentual`: `(precio_nuevo - precio_anterior) / precio_anterior * 100` (0 si `precio_anterior` es 0)

**Ejemplo**:
```python
from apps.productos.models import HistoricoPrecio
from decimal import Decimal

historico = HistoricoPrecio.objects.create(
    producto=coca_cola,
    precio_anterior=Decimal('5000'),
    precio_nuevo=Decimal('5500'),
    modificado_por=usuario_admin,
)
print(historico)  # "7891234567890 - Coca Cola 500ml: ₲5,000 → ₲5,500"
print(f"Variación: {historico.variacion_porcentual:.1f}%")  # 10.0%

historial = HistoricoPrecio.objects.filter(producto=coca_cola).order_by('-fecha_cambio')[:10]
```

---

### 7. Impuesto / ProductoImpuesto

`Impuesto` (nombre, `porcentaje`, `vigente_desde`/`vigente_hasta`, `activo`) es independiente de `Producto`. El vínculo se hace vía `ProductoImpuesto` (FK a `Producto` + FK a `Impuesto`, `unique_together`), y se maneja con la acción
`POST /api/v1/productos/productos/{id}/set-impuesto/` (`{"impuesto": <id> | null}`),
que reemplaza el impuesto asignado (borra el vínculo anterior y crea el nuevo, o
deja al producto sin impuesto si se manda `null`).

```python
from apps.productos.models import Impuesto, ProductoImpuesto
from decimal import Decimal
from datetime import date

iva_10 = Impuesto.objects.create(nombre='IVA 10%', porcentaje=Decimal('10.00'), vigente_desde=date.today())
ProductoImpuesto.objects.create(producto=coca_cola, impuesto=iva_10)
```

---

## 🎨 Admin UI

Interfaz de administración estándar de Django, con estos extras por modelo (ver `admin.py`):

- **Categoria**: link a la categoría padre.
- **Producto**: link a la categoría, precio actual y stock mostrados en la lista (anotados con subqueries para evitar N+1), filtros por `activo`/`categoria`/`es_servicio`/`requiere_stock`, búsqueda por código de barras/código/descripción.
- **UnidadMedida**, **ListaPrecio**, **Impuesto**: administración simple (lista + búsqueda).
- **PrecioPorLista**: links a producto y lista, precio formateado en Guaraníes.
- **HistoricoPrecio**: links a producto y a quien modificó, precios formateados, badge de variación porcentual coloreado (rojo si subió, verde si bajó).
- **ProductoImpuesto**: links a producto e impuesto.

---

## 📊 Ejemplos de Uso

### Ejemplo 1: Crear un producto completo con precio e impuesto

```python
from apps.productos.models import Producto, Categoria, UnidadMedida, ListaPrecio, PrecioPorLista
from decimal import Decimal

bebidas = Categoria.objects.create(nombre='Bebidas', activo=True)
unidad = UnidadMedida.objects.create(nombre='Unidad', abreviatura='Un', activo=True)

producto = Producto.objects.create(
    codigo_barra='7891234567890',
    descripcion='Coca Cola 500ml',
    categoria=bebidas,
    unidad_medida=unidad,
    stock_minimo=Decimal('10.000'),
    activo=True,
)

# Precio: normalmente vía la acción set-precio de la API (crea + registra histórico).
# A nivel ORM directo, equivale a:
lista_defecto = ListaPrecio.objects.get(es_por_defecto=True, activo=True)
PrecioPorLista.objects.create(producto=producto, lista=lista_defecto, precio_unitario=Decimal('5000'))

print(f"Producto creado: {producto} (id={producto.id_producto})")
```

### Ejemplo 2: Precios diferenciados en varias listas

```python
from apps.productos.models import ListaPrecio, PrecioPorLista
from decimal import Decimal

listas = [
    ListaPrecio.objects.create(nombre='Lista General', moneda='PYG', activo=True, es_por_defecto=True),
    ListaPrecio.objects.create(nombre='Mayorista', moneda='PYG', activo=True),
]

for lista, precio in zip(listas, [Decimal('5000'), Decimal('4500')]):
    PrecioPorLista.objects.create(producto=producto, lista=lista, precio_unitario=precio)

for p in producto.precios.select_related('lista'):
    print(f"  - {p.lista.nombre}: ₲{p.precio_unitario:,.0f}")
```

### Ejemplo 3: Cambiar el precio de venta con historial (como lo hace la API)

```python
from apps.productos.models import PrecioPorLista, HistoricoPrecio
from decimal import Decimal

precio_actual = PrecioPorLista.objects.get(producto=producto, lista=lista_defecto)
precio_nuevo = Decimal('5500')

if precio_nuevo != precio_actual.precio_unitario:
    anterior = precio_actual.precio_unitario
    precio_actual.precio_unitario = precio_nuevo
    precio_actual.save()
    HistoricoPrecio.objects.create(
        producto=producto, precio_anterior=anterior, precio_nuevo=precio_nuevo,
        modificado_por=usuario_actual,
    )
```

Esta es exactamente la lógica de `ProductoViewSet.set_precio` — en la práctica conviene
llamar al endpoint (`POST /api/v1/productos/productos/{id}/set-precio/`) en vez de repetirla.

### Ejemplo 4: Productos por categoría, incluyendo subcategorías

```python
from apps.productos.models import Categoria, Producto

bebidas = Categoria.objects.create(nombre='Bebidas', activo=True)
gaseosas = Categoria.objects.create(nombre='Gaseosas', activo=True, categoria_padre=bebidas)
jugos = Categoria.objects.create(nombre='Jugos', activo=True, categoria_padre=bebidas)

def productos_por_categoria_recursivo(categoria):
    """Productos de una categoría y todas sus subcategorías."""
    ids = [categoria.pk]

    def agregar_subcategorias(cat):
        for subcat in cat.subcategorias.filter(activo=True):
            ids.append(subcat.pk)
            agregar_subcategorias(subcat)

    agregar_subcategorias(categoria)
    return Producto.objects.filter(categoria_id__in=ids, activo=True)

productos_bebidas = productos_por_categoria_recursivo(bebidas)
print(f"Total en Bebidas (con subcategorías): {productos_bebidas.count()}")
```

---

## 📈 Métricas y Reportes

### Ejemplo: métricas básicas del catálogo

```python
from apps.productos.models import Producto, Categoria, ListaPrecio
from django.db.models import Count, Avg, Min, Max, Q

metricas = {
    'total_productos': Producto.objects.filter(activo=True).count(),
    'total_categorias': Categoria.objects.filter(activo=True).count(),
    'sin_codigo_barra': Producto.objects.filter(activo=True, codigo_barra__isnull=True).count(),
    'permiten_stock_negativo': Producto.objects.filter(activo=True, permite_stock_negativo=True).count(),
}

productos_por_categoria = Categoria.objects.filter(activo=True).annotate(
    total=Count('productos', filter=Q(productos__activo=True))
).order_by('-total')

precios_por_lista = ListaPrecio.objects.filter(activo=True).annotate(
    total_productos=Count('precios'),
    precio_promedio=Avg('precios__precio_unitario'),
    precio_minimo=Min('precios__precio_unitario'),
    precio_maximo=Max('precios__precio_unitario'),
)
```

### Cambios de precio recientes

```python
from apps.productos.models import HistoricoPrecio
from django.utils import timezone
from datetime import timedelta

hace_un_mes = timezone.now() - timedelta(days=30)
cambios = HistoricoPrecio.objects.filter(
    fecha_cambio__gte=hace_un_mes
).select_related('producto', 'modificado_por').order_by('-fecha_cambio')

for c in cambios:
    quien = c.modificado_por.nombre_completo if c.modificado_por else '—'
    print(f"{c.fecha_cambio:%d/%m/%Y} - {c.producto.descripcion}: "
          f"₲{c.precio_anterior:,.0f} → ₲{c.precio_nuevo:,.0f} ({c.variacion_porcentual:+.1f}%) — {quien}")
```

Esto es también lo que expone `GET /api/v1/productos/historico-precios/reporte/?producto=<id>&desde=&hasta=`.

---

## 🔄 Integración con Otros Módulos

### Con Inventario

`Producto.stock_actual` y `Producto.requiere_reposicion` consultan `apps.inventario.Stock` en vivo (import lazy dentro de la property, para no crear una dependencia circular entre apps):

```python
if producto.requiere_reposicion:
    print(f"⚠️ {producto.descripcion}: stock {producto.stock_actual} < mínimo {producto.stock_minimo}")
```

### Con Ventas

`apps.ventas.DetalleVenta` referencia `producto` y guarda su propio `precio_unitario` (una foto del precio al momento de la venta — no sigue cambios posteriores de `PrecioPorLista`).

### Con Compras

`apps.compras.DetalleCompra` referencia `producto` y guarda su propio `costo_unitario`. El costo de compra **no** se guarda en `Producto` ni en este módulo — vive en `apps.compras.ProductoProveedor` (último precio pagado a cada proveedor) y en `apps.inventario.CostoHistorico` (historial completo, para costo promedio). Ver el README de `apps/compras` para el detalle de esa relación.

---

## 🛡️ Best Practices

1. **Usar transacciones para operaciones que tocan varios modelos**:
   ```python
   from django.db import transaction

   with transaction.atomic():
       existing = PrecioPorLista.objects.filter(producto=producto, lista=lista).first()
       if existing and existing.precio_unitario != nuevo_precio:
           anterior = existing.precio_unitario
           existing.precio_unitario = nuevo_precio
           existing.save()
           HistoricoPrecio.objects.create(
               producto=producto, precio_anterior=anterior, precio_nuevo=nuevo_precio,
           )
   ```

2. **Preferir la acción `set-precio` de la API a tocar `PrecioPorLista` a mano** — ya encapsula la lógica de crear-o-actualizar y registrar el histórico solo si el precio cambió.

3. **Optimizar queries con `select_related`/`prefetch_related`**:
   ```python
   productos = Producto.objects.select_related(
       'categoria', 'unidad_medida',
   ).prefetch_related('precios__lista').filter(activo=True)
   ```

4. **No asumir que un producto tiene impuesto**: `ProductoImpuesto` es opcional — verificar `producto.impuestos.exists()` (o usar `impuesto_actual` del serializer) antes de asumir un porcentaje.

---

## 📝 Estado del Módulo

- ✅ **Modelos**: 8 modelos (`Producto`, `Categoria`, `UnidadMedida`, `ListaPrecio`, `PrecioPorLista`, `HistoricoPrecio`, `Impuesto`, `ProductoImpuesto`)
- ✅ **Admin**: registrado para los 8 modelos, con links entre relacionados y badge de variación de precio
- ✅ **Documentación**: este README, alineado con `models.py`/`serializers.py`/`views.py`/`admin.py` actuales

La validación de reglas de negocio (formato de código de barras, unicidad,
márgenes, etc.) se hace hoy en los serializers y en las vistas de cada app
que usa `Producto` — no hay un módulo `validators.py` centralizado en
`apps/productos` (existió en una versión anterior y fue removido en la
reestructuración del backend).
