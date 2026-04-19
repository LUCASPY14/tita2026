# Verificación de Consistencia - Base de Datos TITADB

**Fecha:** 2026-04-19 09:56:48

## Resumen Ejecutivo

- **Total de modelos analizados:** 23
- **Modelos con serializer:** 20
- **Modelos sin serializer:** 0
- **Modelos con interface frontend:** 7
- **Modelos sin interface frontend:** 13
- **Inconsistencias detectadas:** 12

## Análisis Detallado por Modelo

### clientes.Clientes

#### Campos del Modelo

| Campo | Tipo | Características |
|-------|------|----------------|
| `id_ciudad` | AutoField | - |
| `nombre` | CharField | - |

#### Serializer: `ClientesSerializer`

✅ Usa `'__all__'` - incluye todos los campos del modelo

#### Frontend Interface: `Cliente`

**Archivo:** `types/index.ts`

| Campo | Tipo TypeScript |
|-------|----------------|
| `apellidos` | `string` |
| `ciudad` | `string` |
| `credito_disponible` | `number` |
| `credito_utilizado` | `number` |
| `direccion` | `string` |
| `email` | `string` |
| `estado` | `boolean` |
| `fecha_registro` | `string` |
| `id_ciudad` | `number | null` |
| `id_cliente` | `number` |
| `id_lista` | `number` |
| `id_tipo_cliente` | `number` |
| `limite_credito` | `number` |
| `nombre_completo` | `string` |
| `nombres` | `string` |
| `porcentaje_credito_usado` | `number` |
| `razon_social` | `string` |
| `ruc_ci` | `string` |
| `telefono` | `string` |
| `tiene_credito_disponible` | `boolean` |

---

### clientes.Hijos

#### Campos del Modelo

| Campo | Tipo | Características |
|-------|------|----------------|
| `id_ciudad` | AutoField | - |
| `nombre` | CharField | - |

#### Serializer: `HijosSerializer`

✅ Usa `'__all__'` - incluye todos los campos del modelo

#### Frontend Interface: `Hijo`

**Archivo:** `types/index.ts`

| Campo | Tipo TypeScript |
|-------|----------------|
| `apellido` | `string` |
| `estado` | `boolean` |
| `fecha_nacimiento` | `string` |
| `foto_perfil` | `string` |
| `grado` | `string` |
| `id_cliente_responsable` | `number` |
| `id_hijo` | `number` |
| `nombre` | `string` |
| `nombre_completo` | `string` |

---

### clientes.TiposCliente

#### Campos del Modelo

| Campo | Tipo | Características |
|-------|------|----------------|
| `id_ciudad` | AutoField | - |
| `nombre` | CharField | - |

#### Serializer: `TiposClienteSerializer`

✅ Usa `'__all__'` - incluye todos los campos del modelo

#### Frontend

❌ No se encontró interface TypeScript para este modelo

---

### ventas.Ventas

#### Campos del Modelo

| Campo | Tipo | Características |
|-------|------|----------------|
| `id_condicion_venta` | AutoField | - |
| `nombre` | CharField | UNIQUE |

#### Serializer: `VentasSerializer`

✅ Usa `'__all__'` - incluye todos los campos del modelo

#### Frontend Interface: `Venta`

**Archivo:** `types/index.ts`

| Campo | Tipo TypeScript |
|-------|----------------|
| `cliente_nombre` | `string` |
| `estado` | `string` |
| `estado_pago` | `string` |
| `fecha` | `string` |
| `genera_factura_legal` | `boolean` |
| `hijo_nombre` | `string` |
| `id_cliente` | `number` |
| `id_documento` | `number | null` |
| `id_hijo` | `number` |
| `id_venta` | `number` |
| `iva_10` | `number` |
| `iva_5` | `number` |
| `monto_exenta` | `number` |
| `monto_gravada_10` | `number` |
| `monto_gravada_5` | `number` |
| `monto_total` | `number` |
| `nro_factura_venta` | `number` |
| `saldo_pendiente` | `number` |
| `tipo_venta` | `string` |

---

### ventas.DetallesVenta

#### Campos del Modelo

| Campo | Tipo | Características |
|-------|------|----------------|
| `id_condicion_venta` | AutoField | - |
| `nombre` | CharField | UNIQUE |

#### Serializer: `DetallesVentaSerializer`

✅ Usa `'__all__'` - incluye todos los campos del modelo

#### Frontend

❌ No se encontró interface TypeScript para este modelo

---

### ventas.PagosVentas

#### Serializer

❌ No se encontró serializer para este modelo

#### Frontend

❌ No se encontró interface TypeScript para este modelo

#### ⚠️ Problemas Detectados

- Modelo no encontrado o no pudo ser leído

---

### productos.Productos

#### Campos del Modelo

| Campo | Tipo | Características |
|-------|------|----------------|
| `fecha_cambio` | DateTimeField | - |
| `id_empleado` | ForeignKey | NULL, FK |
| `id_historico` | BigAutoField | - |
| `id_producto` | ForeignKey | FK |
| `precio_anterior` | DecimalField | - |
| `precio_nuevo` | DecimalField | - |

#### Serializer: `ProductosSerializer`

✅ Usa `'__all__'` - incluye todos los campos del modelo

#### Frontend Interface: `Producto`

**Archivo:** `types/index.ts`

| Campo | Tipo TypeScript |
|-------|----------------|
| `categoria_nombre` | `string` |
| `codigo_barra` | `string` |
| `descripcion` | `string` |
| `estado` | `boolean` |
| `id_categoria` | `number` |
| `id_impuesto` | `number` |
| `id_producto` | `number` |
| `id_unidad_medida` | `number` |
| `permite_stock_negativo` | `boolean` |
| `precio` | `number` |
| `requiere_reposicion` | `boolean` |
| `stock_actual` | `number` |
| `stock_minimo` | `number` |
| `unidad_medida_abreviatura` | `string` |
| `unidad_medida_nombre` | `string` |

---

### productos.Categorias

#### Campos del Modelo

| Campo | Tipo | Características |
|-------|------|----------------|
| `fecha_cambio` | DateTimeField | - |
| `id_empleado` | ForeignKey | NULL, FK |
| `id_historico` | BigAutoField | - |
| `id_producto` | ForeignKey | FK |
| `precio_anterior` | DecimalField | - |
| `precio_nuevo` | DecimalField | - |

#### Serializer: `CategoriasSerializer`

✅ Usa `'__all__'` - incluye todos los campos del modelo

#### Frontend Interface: `Categoria`

**Archivo:** `types/index.ts`

| Campo | Tipo TypeScript |
|-------|----------------|
| `es_categoria_raiz` | `boolean` |
| `estado` | `boolean` |
| `id_categoria` | `number` |
| `id_categoria_padre` | `number` |
| `nombre` | `string` |
| `nombre_completo` | `string` |

---

### productos.PreciosPorLista

#### Campos del Modelo

| Campo | Tipo | Características |
|-------|------|----------------|
| `fecha_cambio` | DateTimeField | - |
| `id_empleado` | ForeignKey | NULL, FK |
| `id_historico` | BigAutoField | - |
| `id_producto` | ForeignKey | FK |
| `precio_anterior` | DecimalField | - |
| `precio_nuevo` | DecimalField | - |

#### Serializer: `PreciosPorListaSerializer`

✅ Usa `'__all__'` - incluye todos los campos del modelo

#### Frontend

❌ No se encontró interface TypeScript para este modelo

---

### compras.Compras

#### Campos del Modelo

| Campo | Tipo | Características |
|-------|------|----------------|
| `cantidad` | DecimalField | - |
| `id_detalle_nc_proveedor` | BigAutoField | - |
| `id_nota_proveedor` | ForeignKey | FK |
| `id_producto` | ForeignKey | FK |
| `precio_unitario` | DecimalField | - |
| `subtotal` | DecimalField | - |

#### Serializer: `ComprasSerializer`

✅ Usa `'__all__'` - incluye todos los campos del modelo

#### Frontend Interface: `Compra`

**Archivo:** `types/index.ts`

| Campo | Tipo TypeScript |
|-------|----------------|
| `detalles` | `DetalleCompra[]` |
| `estado_pago` | `'Pendiente' | 'Parcial' | 'Pagado'` |
| `fecha` | `string` |
| `id_compra` | `number` |
| `id_documento` | `number` |
| `id_medio_pago` | `number | null` |
| `id_proveedor` | `number` |
| `medio_pago_descripcion` | `string` |
| `monto_total` | `number` |
| `nro_factura` | `string` |
| `observaciones` | `string` |
| `proveedor_nombre` | `string` |
| `saldo_pendiente` | `number` |
| `tipo_pago` | `'Contado' | 'Crédito'` |

---

### compras.DetallesCompra

#### Campos del Modelo

| Campo | Tipo | Características |
|-------|------|----------------|
| `cantidad` | DecimalField | - |
| `id_detalle_nc_proveedor` | BigAutoField | - |
| `id_nota_proveedor` | ForeignKey | FK |
| `id_producto` | ForeignKey | FK |
| `precio_unitario` | DecimalField | - |
| `subtotal` | DecimalField | - |

#### Serializer: `DetallesCompraSerializer`

✅ Usa `'__all__'` - incluye todos los campos del modelo

#### Frontend

❌ No se encontró interface TypeScript para este modelo

---

### compras.Proveedores

#### Campos del Modelo

| Campo | Tipo | Características |
|-------|------|----------------|
| `cantidad` | DecimalField | - |
| `id_detalle_nc_proveedor` | BigAutoField | - |
| `id_nota_proveedor` | ForeignKey | FK |
| `id_producto` | ForeignKey | FK |
| `precio_unitario` | DecimalField | - |
| `subtotal` | DecimalField | - |

#### Serializer: `ProveedoresSerializer`

✅ Usa `'__all__'` - incluye todos los campos del modelo

#### Frontend

❌ No se encontró interface TypeScript para este modelo

---

### usuarios.Empleados

#### Campos del Modelo

| Campo | Tipo | Características |
|-------|------|----------------|
| `campo_modificado` | CharField | - |
| `fecha_cambio` | DateTimeField | - |
| `id_auditoria` | BigAutoField | - |
| `id_cliente` | ForeignKey | NULL, FK |
| `ip_origen` | CharField | NULL |
| `valor_anterior` | TextField | NULL |
| `valor_nuevo` | TextField | NULL |

#### Serializer: `EmpleadosSerializer`

✅ Usa `'__all__'` - incluye todos los campos del modelo

#### Frontend

❌ No se encontró interface TypeScript para este modelo

---

### usuarios.Roles

#### Campos del Modelo

| Campo | Tipo | Características |
|-------|------|----------------|
| `campo_modificado` | CharField | - |
| `fecha_cambio` | DateTimeField | - |
| `id_auditoria` | BigAutoField | - |
| `id_cliente` | ForeignKey | NULL, FK |
| `ip_origen` | CharField | NULL |
| `valor_anterior` | TextField | NULL |
| `valor_nuevo` | TextField | NULL |

#### Serializer: `RolesSerializer`

✅ Usa `'__all__'` - incluye todos los campos del modelo

#### Frontend

❌ No se encontró interface TypeScript para este modelo

---

### cobros.Tarjetas

#### Serializer

❌ No se encontró serializer para este modelo

#### Frontend

❌ No se encontró interface TypeScript para este modelo

#### ⚠️ Problemas Detectados

- Modelo no encontrado o no pudo ser leído

---

### cobros.CargasSaldo

#### Serializer

❌ No se encontró serializer para este modelo

#### Frontend

❌ No se encontró interface TypeScript para este modelo

#### ⚠️ Problemas Detectados

- Modelo no encontrado o no pudo ser leído

---

### inventario.StockUnico

#### Campos del Modelo

| Campo | Tipo | Características |
|-------|------|----------------|
| `accion_tomada` | CharField | NULL |
| `cantidad_lote` | DecimalField | - |
| `dias_restantes` | IntegerField | - |
| `fecha_accion` | DateTimeField | NULL |
| `fecha_generada` | DateTimeField | - |
| `fecha_vencimiento` | DateField | - |
| `id_alerta` | AutoField | - |
| `id_empleado_responsable` | ForeignKey | NULL, FK |
| `id_lote` | ForeignKey | FK |
| `notificacion_enviada` | BooleanField | - |
| `tipo_alerta` | CharField | - |

#### Serializer: `StockUnicoSerializer`

✅ Usa `'__all__'` - incluye todos los campos del modelo

#### Frontend

❌ No se encontró interface TypeScript para este modelo

---

### inventario.MovimientosStock

#### Campos del Modelo

| Campo | Tipo | Características |
|-------|------|----------------|
| `accion_tomada` | CharField | NULL |
| `cantidad_lote` | DecimalField | - |
| `dias_restantes` | IntegerField | - |
| `fecha_accion` | DateTimeField | NULL |
| `fecha_generada` | DateTimeField | - |
| `fecha_vencimiento` | DateField | - |
| `id_alerta` | AutoField | - |
| `id_empleado_responsable` | ForeignKey | NULL, FK |
| `id_lote` | ForeignKey | FK |
| `notificacion_enviada` | BooleanField | - |
| `tipo_alerta` | CharField | - |

#### Serializer: `MovimientosStockSerializer`

✅ Usa `'__all__'` - incluye todos los campos del modelo

#### Frontend

❌ No se encontró interface TypeScript para este modelo

---

### almuerzos.PlanesAlmuerzo

#### Campos del Modelo

| Campo | Tipo | Características |
|-------|------|----------------|
| `contiene` | BooleanField | - |
| `fecha_registro` | DateTimeField | - |
| `id_alergeno` | ForeignKey | FK |
| `id_producto` | ForeignKey | FK |
| `id_producto_alergeno` | AutoField | - |
| `observaciones` | TextField | NULL |
| `usuario_registro` | CharField | NULL |

#### Serializer: `PlanesAlmuerzoSerializer`

✅ Usa `'__all__'` - incluye todos los campos del modelo

#### Frontend

❌ No se encontró interface TypeScript para este modelo

---

### almuerzos.SuscripcionesAlmuerzo

#### Campos del Modelo

| Campo | Tipo | Características |
|-------|------|----------------|
| `contiene` | BooleanField | - |
| `fecha_registro` | DateTimeField | - |
| `id_alergeno` | ForeignKey | FK |
| `id_producto` | ForeignKey | FK |
| `id_producto_alergeno` | AutoField | - |
| `observaciones` | TextField | NULL |
| `usuario_registro` | CharField | NULL |

#### Serializer: `SuscripcionesAlmuerzoSerializer`

✅ Usa `'__all__'` - incluye todos los campos del modelo

#### Frontend

❌ No se encontró interface TypeScript para este modelo

---

### contabilidad.Impuestos

#### Campos del Modelo

| Campo | Tipo | Características |
|-------|------|----------------|
| `estado` | BooleanField | - |
| `id_impuesto` | AutoField | - |
| `nombre_impuesto` | CharField | UNIQUE |
| `porcentaje` | DecimalField | - |
| `vigente_desde` | DateField | - |
| `vigente_hasta` | DateField | NULL |

#### Serializer: `ImpuestosSerializer`

✅ Usa `'__all__'` - incluye todos los campos del modelo

#### Frontend Interface: `Impuesto`

**Archivo:** `types/index.ts`

| Campo | Tipo TypeScript |
|-------|----------------|
| `estado` | `boolean` |
| `id_impuesto` | `number` |
| `nombre_impuesto` | `string` |
| `porcentaje` | `number` |

---

### contabilidad.CierresCaja

#### Campos del Modelo

| Campo | Tipo | Características |
|-------|------|----------------|
| `estado` | BooleanField | - |
| `id_impuesto` | AutoField | - |
| `nombre_impuesto` | CharField | UNIQUE |
| `porcentaje` | DecimalField | - |
| `vigente_desde` | DateField | - |
| `vigente_hasta` | DateField | NULL |

#### Serializer: `CierresCajaSerializer`

✅ Usa `'__all__'` - incluye todos los campos del modelo

#### Frontend

❌ No se encontró interface TypeScript para este modelo

---

### core.MediosPago

#### Campos del Modelo

| Campo | Tipo | Características |
|-------|------|----------------|
| `fecha_autorizacion` | DateTimeField | - |
| `id_ajuste` | ForeignKey | NULL, FK |
| `id_autorizacion` | AutoField | - |
| `id_compra` | ForeignKey | NULL, FK |
| `id_empleado_autorizador` | ForeignKey | FK |
| `id_empleado_autorizador_2` | ForeignKey | NULL, FK |
| `id_empleado_solicitante` | ForeignKey | FK |
| `id_venta` | ForeignKey | NULL, FK |
| `ip_address` | GenericIPAddressField | NULL |
| `monto` | DecimalField | - |
| `motivo` | TextField | - |
| `tipo_operacion` | CharField | - |

#### Serializer: `MediosPagoSerializer`

Campos incluidos: `id_medio_pago`, `descripcion`, `nombre`, `genera_comision`, `requiere_validacion`, `estado`

#### Frontend

❌ No se encontró interface TypeScript para este modelo

#### ⚠️ Problemas Detectados

- Campos faltantes en serializer: id_compra, monto, id_venta, id_ajuste, motivo, tipo_operacion, fecha_autorizacion, ip_address, id_empleado_autorizador_2, id_empleado_solicitante, id_autorizacion, id_empleado_autorizador

---

## Recomendaciones

1. **Serializers faltantes:** Crear serializers para los modelos que no los tienen
2. **Interfaces TypeScript:** Definir interfaces para los modelos sin representación en frontend
3. **Campos faltantes en serializers:** Agregar campos del modelo o usar `'__all__'`
4. **Documentación:** Agregar help_text a todos los campos para mejor comprensión
