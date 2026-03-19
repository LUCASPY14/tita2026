# 📋 CUENTA CORRIENTE DE PROVEEDORES
## Lógica y Reglas de Negocio

---

## 🎯 CONCEPTO

La **Cuenta Corriente de Proveedores** es un registro detallado de:
- ✅ Todas las compras realizadas a un proveedor
- 💰 Pagos efectuados al proveedor
- 📊 Saldo pendiente de pago (deuda actual)

Similar a un estado de cuenta bancario, pero desde la perspectiva de la empresa como deudor.

---

## 📐 ESTRUCTURA DE DATOS

### 1. **Tabla: Compras**
```
id_compra           → ID único de la compra
fecha               → Fecha de la compra
id_proveedor        → Proveedor (relación)
monto_total         → Total de la factura
saldo_pendiente     → Cuánto falta pagar de esta compra
estado_pago         → Estado: Pendiente/Pagado/Parcial
tipo_pago           → Contado o Crédito
id_medio_pago       → Forma de pago (efectivo, transferencia, etc.)
nro_factura         → Número de factura del proveedor
```

### 2. **Tabla: PagosProveedores**
```
id_pago_proveedor   → ID único del pago
fecha_creacion      → Fecha del pago
id_medio_pago       → Forma de pago (efectivo, transferencia, etc.)
monto_total         → Monto total pagado en este pago
```

### 3. **Tabla: AplicacionPagosCompras** (Tabla de relación)
```
id_aplicacion       → ID único
id_pago_proveedor   → Pago realizado
id_compra           → Compra a la que se aplica
monto_aplicado      → Cuánto de este pago se aplica a esta compra
```

Esta última tabla permite que **un solo pago pueda aplicarse a múltiples compras**.

---

## 🔄 FLUJO DE OPERACIONES

### **Escenario 1: Compra al CONTADO**

**Paso 1: Registro de compra**
```
Compra #1
- Fecha: 18/03/2026
- Proveedor: El Arroyense
- Monto Total: Gs. 900.000
- Tipo Pago: Contado
- Medio Pago: Efectivo
- Estado Pago: Pagado
- Saldo Pendiente: Gs. 0
```

**Reglas:**
- ✅ `saldo_pendiente` se crea en 0 desde el inicio
- ✅ `estado_pago` = "Pagado"
- ✅ Se registra automáticamente en caja como salida de efectivo
- ✅ NO se genera deuda en cuenta corriente

---

### **Escenario 2: Compra a CRÉDITO**

**Paso 1: Registro de compra**
```
Compra #2
- Fecha: 18/03/2026
- Proveedor: El Arroyense
- Monto Total: Gs. 1.500.000
- Tipo Pago: Crédito
- Medio Pago: NULL (se pagará después)
- Estado Pago: Pendiente
- Saldo Pendiente: Gs. 1.500.000
```

**Reglas:**
- ✅ `saldo_pendiente` = `monto_total` (deuda completa)
- ✅ `estado_pago` = "Pendiente"
- ✅ Se incrementa la cuenta corriente del proveedor
- ✅ NO afecta caja aún

**Paso 2: Pago parcial (después de 15 días)**
```
Pago #1
- Fecha: 02/04/2026
- Monto: Gs. 800.000
- Medio: Transferencia Bancaria
```

**Se crea relación:**
```
AplicacionPagosCompras
- id_pago_proveedor: 1
- id_compra: 2
- monto_aplicado: Gs. 800.000
```

**Resultado en Compra #2:**
```
- Saldo Pendiente: Gs. 700.000 (antes: 1.500.000)
- Estado Pago: Parcial
```

**Paso 3: Pago final**
```
Pago #2
- Fecha: 15/04/2026
- Monto: Gs. 700.000
- Medio: Transferencia Bancaria
```

**Resultado en Compra #2:**
```
- Saldo Pendiente: Gs. 0
- Estado Pago: Pagado
```

---

## 📊 CÁLCULO DE CUENTA CORRIENTE

### **Función: `obtener_cuenta_corriente_proveedor()`**

**Entrada:** ID del proveedor

**Salida:**
```json
{
  "total_compras": 2400000,        // Suma de todas las compras
  "total_pagado": 1500000,         // Suma de todos los pagos aplicados
  "saldo_pendiente": 900000,       // total_compras - total_pagado
  "cantidad_compras": 3,           // Total de compras
  "cantidad_pendientes": 2,        // Compras con saldo > 0
  "compras_pendientes": [
    {
      "id_compra": 5,
      "fecha": "2026-03-15",
      "nro_factura": "001-001-0000123",
      "monto_total": "1200000",
      "saldo_pendiente": "600000",
      "dias_vencimiento": 5         // Días desde la compra
    }
  ]
}
```

### **Fórmulas:**

```python
# Saldo pendiente de una compra individual
saldo_pendiente = monto_total - Σ(pagos_aplicados)

# Saldo total con el proveedor
saldo_total = Σ(saldo_pendiente de todas las compras)

# Estado de pago de una compra
if saldo_pendiente == 0:
    estado_pago = "Pagado"
elif saldo_pendiente == monto_total:
    estado_pago = "Pendiente"
else:
    estado_pago = "Parcial"
```

---

## ⚠️ REGLAS DE NEGOCIO CRÍTICAS

### 1. **Tipos de Pago**
- **Contado:** Pago inmediato al registrar la compra
  - `saldo_pendiente = 0`
  - `estado_pago = "Pagado"`
  - Debe tener `id_medio_pago`
  
- **Crédito:** Pago posterior
  - `saldo_pendiente = monto_total`
  - `estado_pago = "Pendiente"`
  - `id_medio_pago` puede ser NULL

### 2. **Estados de Pago**
- **Pendiente:** No se ha pagado nada (`saldo = monto_total`)
- **Parcial:** Se pagó parte (`0 < saldo < monto_total`)
- **Pagado:** Cancelado completamente (`saldo = 0`)

### 3. **Aplicación de Pagos**
- ✅ Un pago puede aplicarse a MÚLTIPLES compras
- ✅ Una compra puede recibir MÚLTIPLES pagos
- ✅ El total aplicado NO puede exceder el monto del pago
- ✅ El monto aplicado a una compra NO puede exceder su saldo pendiente

### 4. **Antigüedad de Deuda**
```
dias_vencimiento = Fecha_Actual - Fecha_Compra
```
- 0-30 días: Al día
- 31-60 días: Vencida
- 61-90 días: Morosa
- +90 días: En gestión

### 5. **Conciliación**
```
SIEMPRE debe cumplirse:
Σ(montos_aplicados) ≤ monto_del_pago
Σ(pagos_aplicados_a_compra) ≤ monto_total_compra
```

---

## 🔐 VALIDACIONES TÉCNICAS

### Al crear una compra:
```python
✅ id_proveedor debe existir y estar activo
✅ monto_total > 0
✅ Si tipo_pago = "Contado" → id_medio_pago requerido
✅ Si tipo_pago = "Contado" → saldo_pendiente = 0
✅ Si tipo_pago = "Crédito" → saldo_pendiente = monto_total
✅ Debe tener al menos un detalle (producto)
```

### Al registrar un pago:
```python
✅ id_proveedor existe
✅ Existe al menos una compra con saldo pendiente
✅ Monto del pago > 0
✅ Σ(montos_aplicados) = monto_total_pago (asignar todo)
✅ No aplicar más del saldo pendiente de cada compra
```

### Al aplicar pago a compra:
```python
✅ monto_aplicado > 0
✅ monto_aplicado ≤ saldo_pendiente_compra
✅ Actualizar saldo_pendiente de la compra
✅ Actualizar estado_pago de la compra
```

---

## 📈 REPORTES Y CONSULTAS ÚTILES

### 1. **Top 10 Proveedores con Mayor Deuda**
```sql
SELECT 
    p.razon_social,
    SUM(c.saldo_pendiente) as deuda_total
FROM proveedores p
JOIN compras c ON c.id_proveedor = p.id_proveedor
WHERE c.saldo_pendiente > 0
GROUP BY p.id_proveedor
ORDER BY deuda_total DESC
LIMIT 10
```

### 2. **Compras Vencidas (más de 30 días sin pagar)**
```sql
SELECT *
FROM compras c
WHERE c.saldo_pendiente > 0
  AND c.fecha < NOW() - INTERVAL 30 DAY
ORDER BY c.fecha ASC
```

### 3. **Resumen por Proveedor**
```sql
SELECT 
    p.razon_social,
    COUNT(c.id_compra) as total_compras,
    SUM(c.monto_total) as total_comprado,
    SUM(c.saldo_pendiente) as saldo_pendiente,
    AVG(DATEDIFF(NOW(), c.fecha)) as promedio_dias_pago
FROM proveedores p
LEFT JOIN compras c ON c.id_proveedor = p.id_proveedor
GROUP BY p.id_proveedor
```

---

## 🎨 EJEMPLO COMPLETO

### Situación inicial: Proveedor "Distribuidora Central"

**Compra 1** (15/03/2026)
- Monto: Gs. 2.000.000
- Tipo: Crédito
- Saldo: Gs. 2.000.000

**Compra 2** (18/03/2026)
- Monto: Gs. 1.500.000
- Tipo: Crédito
- Saldo: Gs. 1.500.000

**Total deuda:** Gs. 3.500.000

---

### Pago 1 (20/03/2026): Gs. 2.200.000

**Distribución:**
- Compra 1: Gs. 2.000.000 (salda completamente)
- Compra 2: Gs. 200.000 (pago parcial)

**Resultado:**
- Compra 1: Saldo = Gs. 0 (PAGADO)
- Compra 2: Saldo = Gs. 1.300.000 (PARCIAL)
- **Total deuda:** Gs. 1.300.000

---

### Pago 2 (25/03/2026): Gs. 1.300.000

**Distribución:**
- Compra 2: Gs. 1.300.000 (salda completamente)

**Resultado:**
- Compra 2: Saldo = Gs. 0 (PAGADO)
- **Total deuda:** Gs. 0

---

## 🚀 ENDPOINTS DE API

```
GET  /api/v1/proveedores/{id}/cuenta_corriente/
     → Obtener estado de cuenta

GET  /api/v1/compras/?estado_pago=Pendiente
     → Listar compras pendientes

POST /api/v1/pagos-proveedores/
     → Registrar un nuevo pago

POST /api/v1/pagos-proveedores/{id}/aplicar/
     → Aplicar un pago a compras específicas
```

---

## ✅ BENEFICIOS DEL SISTEMA

1. **Trazabilidad completa:** Cada peso pagado se puede rastrear
2. **Control de morosidad:** Identificar deudas antiguas
3. **Planificación financiera:** Saber cuánto se debe y cuándo
4. **Conciliación bancaria:** Matching automático de pagos
5. **Reportes gerenciales:** Análisis de relación con proveedores
6. **Auditoría:** Registro detallado de todas las transacciones

---

## 📝 NOTAS IMPORTANTES

- Los pagos SIEMPRE se registran individualmente, nunca se edita el saldo directamente
- La tabla `AplicacionPagosCompras` es la "fuente de verdad" para conciliación
- El campo `saldo_pendiente` en Compras se actualiza automáticamente al aplicar pagos
- Para reportes de antigüedad, usar la fecha de la compra original, no del último pago
- Considerar agregar campo `fecha_vencimiento` para alertas automáticas

---

**Fecha de documentación:** 18/03/2026  
**Autor:** Sistema Cantina TITA  
**Versión:** 1.0
