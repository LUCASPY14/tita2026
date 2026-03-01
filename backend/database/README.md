# Base de Datos - Cantina Tita

Este directorio contiene el esquema completo de la base de datos `dbcantinatita`.

## Estructura de la Base de datos

El esquema incluye **55+ tablas** organizadas en los siguientes módulos:

### 📋 Tablas Maestras (Catálogos)
- **Usuarios y Seguridad**: `roles`, `empleados`, `auditoria_*`, `sesiones_activas`
- **Clientes**: `tipos_cliente`, `clientes`, `listas_precios`
- **Hijos/Estudiantes**: `hijos`, `grados`, `restricciones_hijos`, `historial_grados_hijos`
- **Productos**: `categorias`, `productos`, `unidades_medida`, `impuestos`, `stock_unico`
- **Proveedores**: `proveedores`
- **Alergenos**: `alergenos`, `productos_alergenos`
- **Promociones**: `promociones`, `productos_promocion`, `categorias_promocion`

### 💳 Tarjetas y Saldo
- `tarjetas` - Tarjetas RFID/código de barras para hijos
- `cargas_saldo` - Recargas de saldo (efectivo, transferencia, etc.)
- `consumos_tarjeta` - Consumos diarios de los hijos
- `notificaciones_saldo` - Alertas de saldo bajo

### 🍽️ Almuerzos
- `tipos_almuerzo` - Tipos de almuerzo (completo, básico, etc.)
- `planes_almuerzo` - Planes mensuales (5 días, 3 días, etc.)
- `suscripciones_almuerzo` - Suscripciones activas de hijos
- `registros_consumo_almuerzo` - Registro diario de consumo
- `cuentas_almuerzo_mensual` - Facturación mensual de almuerzos
- `pagos_cuentas_almuerzo` - Pagos de cuentas mensuales

### 💰 Ventas y Compras
- **Ventas**: `ventas`, `detalles_venta`, `pagos_venta`, `promociones_aplicadas`
- **Compras**: `compras`, `detalles_compra`, `costos_historicos`
- **Notas de Crédito**: `notas_credito_cliente`, `notas_credito_proveedor`

### 🧾 Facturación Electrónica (Paraguay)
- `puntos_expedicion` - Puntos de expedición
- `timbrados` - Timbrados de SET
- `documentos_tributarios` - Facturas electrónicas (CDC, SIFEN)
- `documento_impuestos` - Desglose de impuestos por documento

### 💵 Caja y Pagos
- `cajas` - Puntos de venta
- `cierres_caja` - Aperturas y cierres diarios
- `movimientos_caja` - Movimientos de efectivo
- `medios_pago` - Efectivo, tarjetas, transferencias, etc.
- `tarifas_comision` - Comisiones por medio de pago
- `conciliacion_pagos` - Conciliación bancaria

### 📦 Inventario
- `movimientos_stock` - Entradas/salidas de stock
- `ajustes_inventario` - Ajustes manuales
- `detalles_ajuste` - Detalles de ajustes

### 🔐 Seguridad y Auditoría
- `auditoria_operaciones` - Registro de todas las operaciones
- `intentos_login` - Intentos de inicio de sesión
- `bloqueos_cuenta` - Bloqueos de seguridad
- `anomalias_detectadas` - Detección de comportamiento anormal
- `tarjetas_autorizacion` - Tarjetas de autorización para empleados

### ⚙️ Configuración
- `configuracion_sistema` - Configuraciones del sistema
- `datos_empresa` - Datos de la empresa
- `dashboards` - Dashboards personalizados
- `perfiles_usuario` - Preferencias de usuario

## 📊 Vistas Principales

- `vista_stock_alerta` - Productos con stock crítico o bajo
- `vista_consumos_hijo` - Resumen de consumos por hijo
- `vista_almuerzos_diarios_hijos` - Almuerzos consumidos diariamente
- `vista_resumen_caja_diario` - Resumen diario de caja
- `vista_cuentas_mensuales_hijos` - Cuentas mensuales de almuerzos

## 🚀 Instalación de la Base de Datos

### Opción 1: Script PowerShell (Recomendado)

```powershell
.\database\import_database.ps1
```

Este script:
1. Verifica si MySQL está instalado
2. Solicita credenciales de MySQL
3. Verifica si la base de datos existe
4. Ejecuta el schema SQL
5. Confirma la creación exitosa

### Opción 2: MySQL Workbench

1. Abrir MySQL Workbench
2. Conectarse al servidor MySQL
3. File → Open SQL Script → Seleccionar `dbcantinatita_schema.sql`
4. Ejecutar el script (⚡ Execute)

### Opción 3: Línea de Comandos MySQL

```bash
mysql -u root -p < database/dbcantinatita_schema.sql
```

O si ya existe la base de datos:

```bash
mysql -u root -p dbcantinatita < database/dbcantinatita_schema.sql
```

## 🔧 Configuración de Django

Una vez creada la base de datos, Django se conectará automáticamente usando la configuración en:
- `backend/settings/development.py`

### Generar modelos Django desde la base de datos existente:

```powershell
python manage.py inspectdb > apps/all_models.py
```

Luego puedes separar los modelos por app según corresponda.

## 📝 Notas Importantes

1. **Codificación**: La base de datos usa `utf8mb4_unicode_ci` para soporte completo de caracteres Unicode
2. **Motor**: Todas las tablas usan `InnoDB` para soporte de transacciones y claves foráneas
3. **Índices**: Se han creado índices en campos frecuentemente consultados
4. **Normalización**: El esquema está en 3FN (Tercera Forma Normal)
5. **Convención**: Se usa `snake_case` para nombres de tablas y columnas

## 🔑 Campos Comunes

La mayoría de tablas incluyen:
- `id_*` - Clave primaria AUTO_INCREMENT
- `activo` - Boolean para soft delete
- `fecha_creacion` / `created_at` - Timestamp de creación
- `fecha_actualizacion` / `updated_at` - Timestamp de última modificación

## 📞 Soporte

Para más información sobre la estructura, consulta el esquema SQL completo en:
`dbcantinatita_schema.sql`
