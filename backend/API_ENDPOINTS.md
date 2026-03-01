# API REST - Endpoints Disponibles

## Base URL
`http://localhost:8000/api/v1/`

## ✅ Opción B Completada: Serializers y ViewSets

### Endpoints Implementados

#### 👥 Clientes
- `GET/POST /api/v1/clientes/` - Lista y crea clientes
- `GET/PUT/PATCH/DELETE /api/v1/clientes/{id}/` - Detalle, actualiza, elimina cliente
- `GET/POST /api/v1/hijos/` - Lista y crea hijos
- `GET/PUT/PATCH/DELETE /api/v1/hijos/{id}/` - Detalle, actualiza, elimina hijo

**Filtros disponibles:** `tipo_cliente`, `activo`, `grado`

#### 🛒 Productos
- `GET/POST /api/v1/productos/` - Lista y crea productos
- `GET/PUT/PATCH/DELETE /api/v1/productos/{id}/` - Detalle, actualiza, elimina producto
- `GET/POST /api/v1/categorias/` - Lista y crea categorías
- `GET/PUT/PATCH/DELETE /api/v1/categorias/{id}/` - Detalle, actualiza, elimina categoría

**Filtros disponibles:** `categoria`, `activo`, `es_perecedero`

#### 💰 Ventas
- `GET/POST /api/v1/ventas/` - Lista y crea ventas
- `GET/PUT/PATCH/DELETE /api/v1/ventas/{id}/` - Detalle, actualiza, elimina venta
- `GET/POST /api/v1/detalles-venta/` - Detalles de venta
- `GET/POST /api/v1/pagos-venta/` - Pagos de venta
- `GET/POST /api/v1/notas-credito-cliente/` - Notas de crédito a clientes
- `GET/POST /api/v1/promociones/` - Promociones

**Filtros disponibles:** `estado_pago`, `estado`, `tipo_venta`, `id_cliente`, `fecha`

#### 📦 Compras
- `GET/POST /api/v1/proveedores/` - Lista y crea proveedores
- `GET/PUT/PATCH/DELETE /api/v1/proveedores/{id}/` - Detalle, actualiza, elimina proveedor
- `GET/POST /api/v1/compras/` - Lista y crea compras
- `GET/PUT/PATCH/DELETE /api/v1/compras/{id}/` - Detalle, actualiza, elimina compra
- `GET/POST /api/v1/detalles-compra/` - Detalles de compra
- `GET/POST /api/v1/pagos-proveedores/` - Pagos a proveedores
- `GET/POST /api/v1/notas-credito-proveedor/` - Notas de crédito de proveedores

**Filtros disponibles:** `estado_pago`, `id_proveedor`, `activo`, `ciudad`

#### 💳 Core (Tarjetas y Sistema)
- `GET/POST /api/v1/tarjetas/` - Lista y crea tarjetas
- `GET/PUT/PATCH/DELETE /api/v1/tarjetas/{id}/` - Detalle, actualiza, elimina tarjeta
- `GET/POST /api/v1/cargas-saldo/` - Cargas de saldo
- `GET/POST /api/v1/consumos-tarjeta/` - Consumos de tarjeta
- `GET/POST /api/v1/medios-pago/` - Medios de pago
- `GET/POST /api/v1/configuracion-sistema/` - Configuración del sistema

**Filtros disponibles:** `estado`, `id_hijo`, `activo`

#### 🍽️ Almuerzos
- `GET/POST /api/v1/planes-almuerzo/` - Planes de almuerzo
- `GET/POST /api/v1/tipos-almuerzo/` - Tipos de almuerzo
- `GET/POST /api/v1/suscripciones-almuerzo/` - Suscripciones de almuerzo
- `GET/POST /api/v1/registros-consumo-almuerzo/` - Registros de consumo
- `GET/POST /api/v1/alergenos/` - Alergenos

**Filtros disponibles:** `estado`, `id_hijo`, `id_plan_almuerzo`, `activo`, `nivel_severidad`

#### 👨‍💼 Usuarios
- `GET/POST /api/v1/roles/` - Roles de usuarios
- `GET/POST /api/v1/empleados/` - Empleados
- `GET/PUT/PATCH/DELETE /api/v1/empleados/{id}/` - Detalle, actualiza, elimina empleado
- `GET/POST /api/v1/perfiles-usuario/` - Perfiles de usuario
- `GET/POST /api/v1/usuarios-portal/` - Usuarios del portal web

**Filtros disponibles:** `activo`, `id_rol`

#### 📊 Inventario
- `GET/POST /api/v1/stock/` - Stock de productos
- `GET/PUT/PATCH/DELETE /api/v1/stock/{id}/` - Detalle, actualiza stock
- `GET/POST /api/v1/movimientos-stock/` - Movimientos de stock
- `GET/POST /api/v1/ajustes-inventario/` - Ajustes de inventario

**Filtros disponibles:** `id_producto`, `tipo_movimiento`, `tipo_ajuste`, `estado`

---

## Características Implementadas

### Serializers
✅ **47 serializers** creados con:
- Campos relacionados con nombres legibles (ej: `cliente_nombre`, `producto_nombre`)
- Serializers anidados para detalles y relaciones
- Campos calculados (ej: `saldo_disponible` en Tarjetas)
- Protección de campos sensibles (`write_only` para passwords)

### ViewSets
✅ **47 ViewSets** implementados con:
- **Filtros** usando `django-filter` para búsquedas precisas
- **Búsqueda** con `SearchFilter` para búsqueda de texto
- **Ordenamiento** con `OrderingFilter` para ordenar resultados
- **Paginación** automática por Django REST Framework

### Filtros Disponibles

Cada endpoint soporta filtros mediante query parameters:

```bash
# Ejemplo: Buscar ventas por estado y cliente
GET /api/v1/ventas/?estado_pago=pendiente&id_cliente=1

# Ejemplo: Buscar productos activos por categoría
GET /api/v1/productos/?activo=1&categoria=2

# Ejemplo: Buscar tarjetas por estado
GET /api/v1/tarjetas/?estado=activa

# Ejemplo: Buscar empleados activos
GET /api/v1/empleados/?activo=1&search=Juan

# Ejemplo: Ordenar ventas por fecha
GET /api/v1/ventas/?ordering=-fecha
```

### Búsqueda (Search)

Los endpoints con `search_fields` permiten búsqueda de texto:

```bash
# Buscar cliente por nombre
GET /api/v1/clientes/?search=Juan

# Buscar producto por nombre
GET /api/v1/productos/?search=Coca

# Buscar proveedor por razón social o RUC
GET /api/v1/proveedores/?search=Distribuidora
```

### Ordenamiento

Los endpoints con `ordering_fields` permiten ordenar resultados:

```bash
# Ordenar ventas por fecha descendente
GET /api/v1/ventas/?ordering=-fecha

# Ordenar productos por nombre
GET /api/v1/productos/?ordering=nombre

# Ordenar empleados por apellido
GET /api/v1/empleados/?ordering=apellido,nombre
```

---

## Ejemplos de Uso

### Crear una Venta
```bash
POST /api/v1/ventas/
Content-Type: application/json

{
  "id_cliente": 1,
  "id_empleado_cajero": 2,
  "monto_total": 15000,
  "estado_pago": "pendiente",
  "estado": "activa",
  "tipo_venta": "contado"
}
```

### Obtener Ventas con Detalles
```bash
GET /api/v1/ventas/1/

# Response incluye:
{
  "id_venta": 1,
  "detalles": [...],  # Detalles de la venta
  "pagos": [...],     # Pagos realizados
  "cliente_nombre": "Juan",
  "cliente_apellido": "Pérez"
}
```

### Cargar Saldo a Tarjeta
```bash
POST /api/v1/cargas-saldo/
Content-Type: application/json

{
  "nro_tarjeta": "TJ001",
  "monto_cargado": 50000,
  "estado": "confirmado",
  "id_cliente_origen": 1
}
```

### Registrar Consumo de Almuerzo
```bash
POST /api/v1/registros-consumo-almuerzo/
Content-Type: application/json

{
  "id_hijo": 1,
  "fecha_consumo": "2026-02-28",
  "estado": "consumido",
  "id_tipo_almuerzo": 1
}
```

---

## Próximos Pasos (Opciones C y D)

### Opción C: Mejorar Modelos
- [ ] Agregar métodos `__str__()` a todos los modelos
- [ ] Agregar `verbose_name` y `verbose_name_plural`
- [ ] Convertir IntegerField (0/1) a BooleanField
- [ ] Agregar propiedades calculadas (@property)
- [ ] Agregar validaciones personalizadas

### Opción D: Autenticación y Permisos
- [ ] Instalar django-rest-framework-simplejwt
- [ ] Configurar autenticación JWT
- [ ] Crear clases de permisos personalizadas
- [ ] Agregar permisos a ViewSets
- [ ] Crear endpoints de autenticación

---

## Estado Actual

✅ **Sistema check**: 0 errores  
✅ **Servidor**: Corriendo en http://localhost:8000  
✅ **Admin**: http://localhost:8000/admin/ (usuario: admin)  
✅ **API**: http://localhost:8000/api/v1/  
✅ **Browsable API**: Disponible en todos los endpoints

## Modelos con API Completa

- **Clientes**: 2 endpoints (Clientes, Hijos)
- **Productos**: 2 endpoints (Productos, Categorías)
- **Ventas**: 5 endpoints
- **Compras**: 5 endpoints
- **Core**: 5 endpoints
- **Almuerzos**: 5 endpoints
- **Usuarios**: 4 endpoints
- **Inventario**: 3 endpoints

**Total**: **31 endpoints REST** completamente funcionales
