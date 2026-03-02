# Módulo Inventario

## 📋 Descripción General

El módulo **Inventario** es el sistema central de gestión de stock de Cantina Tita. Maneja el control de existencias, movimientos, lotes, costos, alertas y ML forecasting con arquitectura ACID y concurrencia segura.

## 🎯 Características Principales

### ✅ Funcionalidades Core
- ✅ **Control de Stock Único**: Registro centralizado de existencias por producto
- ✅ **Movimientos Trazables**: Historial completo e inmutable de todos los movimientos
- ✅ **Ajustes de Inventario**: Sistema de aprobación para mermas, sobrantes y correcciones
- ✅ **Gestión de Lotes**: Control FEFO (First Expired, First Out) con alertas de vencimiento
- ✅ **Costos Históricos**: CPP (Costo Promedio Ponderado) automático
- ✅ **Alertas Inteligentes**: Notificaciones automáticas de stock bajo y vencimientos próximos
- ✅ **ML Forecasting**: Predicción de demanda con análisis de estacionalidad y tendencias
- ✅ **Concurrencia Segura**: select_for_update() en todas las operaciones críticas

### 🛡️ Seguridad y Auditoría
- ACID compliance en todas las transacciones
- Movimientos inmutables (no se permite borrado)
- Aprobación multinivel para ajustes
- Trazabilidad completa de autorizaciones
- Validación exhaustiva de datos

## 📊 Modelos del Sistema

El módulo cuenta con **8 modelos principales**:

### 1. StockUnico
**Inventario actual de cada producto**

```python
class StockUnico(models.Model):
    id_stock = AutoField(primary_key=True)
    cantidad = DecimalField(max_digits=10, decimal_places=3)
    fecha_ultima_actualizacion = DateTimeField(auto_now=True)
    id_producto = OneToOneField('productos.Productos')
```

#### Campos Principales
- `cantidad`: Stock actual disponible (3 decimales de precisión)
- `fecha_ultima_actualizacion`: Timestamp de última modificación
- `id_producto`: Relación 1:1 con Productos

#### Propiedades Calculadas
- `costo_promedio_ponderado`: CPP basado en compras históricas
- `valor_inventario`: cantidad × costo_promedio_ponderado
- `requiere_reposicion`: True si cantidad ≤ stock_minimo
- `dias_stock_disponible`: Días estimados según venta promedio

#### Reglas de Negocio
1. **Un solo registro por producto** (OneToOne)
2. **Stock nunca negativo** (excepto si producto.permite_stock_negativo=True)
3. **Actualización atómica** con select_for_update()
4. **Respaldado por MovimientosStock** (no modificar directamente)

#### Ejemplo de Uso
```python
from apps.inventario.models import StockUnico

# Consultar stock
stock = StockUnico.objects.get(id_producto=123)
print(f"Stock: {stock.cantidad}")
print(f"Valor: ₲ {stock.valor_inventario:,.0f}")
print(f"Reposición: {'Sí' if stock.requiere_reposicion else 'No'}")

# Actualización SEGURA con lock
with transaction.atomic():
    stock = StockUnico.objects.select_for_update().get(id_producto=123)
    stock.cantidad -= 10
    stock.save()
```

---

### 2. MovimientosStock
**Historial inmutable de todos los movimientos de inventario**

```python
class MovimientosStock(models.Model):
    id_movimiento_stock = AutoField(primary_key=True)
    tipo_movimiento = CharField(max_length=10)  # 'Ingreso' | 'Egreso'
    cantidad = DecimalField(max_digits=10, decimal_places=3)
    stock_anterior = DecimalField(max_digits=10, decimal_places=3)
    stock_resultante = DecimalField(max_digits=10, decimal_places=3)
    motivo = CharField(max_length=255)
    tipo_referencia = CharField(max_length=20)
    id_referencia = IntegerField()
    fecha_hora = DateTimeField(auto_now_add=True)
    id_producto = ForeignKey('productos.Productos')
    id_empleado = ForeignKey('usuarios.Empleados')
```

#### Tipos de Movimiento
- **Ingreso**: Compras, devoluciones de clientes, ajustes positivos, producción
- **Egreso**: Ventas, devoluciones a proveedores, mermas, deterioros, ajustes negativos

#### Tipos de Referencia
- `Compra`: Movimiento originado por compra (id_compra)
- `Venta`: Movimiento por venta (id_venta)
- `Ajuste`: Ajuste de inventario (id_ajuste)
- `Devolucion`: Devolución cliente/proveedor
- `Traslado`: Transferencia entre sucursales
- `Produccion`: Transformación de productos
- `Merma`: Pérdida por deterioro/robo
- `Inicial`: Carga inicial de stock

#### Reglas Críticas
1. **NUNCA eliminar movimientos** (auditoría permanente)
2. **stock_resultante debe coincidir con StockUnico.cantidad**
3. **motivo obligatorio** (mínimo 10 caracteres)
4. **Trazabilidad**: tipo_referencia + id_referencia apuntan al documento origen

#### Ejemplo de Registro
```python
from apps.inventario.models import MovimientosStock
from django.db import transaction

with transaction.atomic():
    # Obtener stock con lock
    stock = StockUnico.objects.select_for_update().get(id_producto=producto_id)
    
    # Registrar movimiento
    movimiento = MovimientosStock.objects.create(
        tipo_movimiento='Egreso',
        cantidad=10,
        stock_anterior=stock.cantidad,
        stock_resultante=stock.cantidad - 10,
        motivo='Venta a cliente #1234',
        tipo_referencia='Venta',
        id_referencia=1234,
        id_producto_id=producto_id,
        id_empleado_id=empleado_id
    )
    
    # Actualizar stock
    stock.cantidad -= 10
    stock.save()
```

---

### 3. AjustesInventario
**Sistema de aprobación para ajustes de inventario**

```python
class AjustesInventario(models.Model):
    id_ajuste = AutoField(primary_key=True)
    tipo_ajuste = CharField(max_length=15)  # Merma|Sobrante|Correccion|Vencimiento|Deterioro
    estado = CharField(max_length=10)  # Pendiente|Aprobado|Rechazado|Aplicado
    motivo = CharField(max_length=255)
    observaciones = TextField()
    fecha_hora = DateTimeField(auto_now_add=True)
    id_empleado = ForeignKey('usuarios.Empleados')
```

#### Tipos de Ajuste
- `Merma`: Pérdida por robo, deterioro, evaporación (cantidad negativa)
- `Sobrante`: Exceso detectado en inventario físico (cantidad positiva)
- `Correccion`: Corrección de error de registro (+ o -)
- `Vencimiento`: Baja por vencimiento (cantidad negativa)
- `Deterioro`: Baja por daño físico (cantidad negativa)

#### Estados del Ajuste
1. **Pendiente**: Creado, esperando aprobación
2. **Aprobado**: Autorizado por supervisor
3. **Rechazado**: No autorizado
4. **Aplicado**: Stock ya actualizado

#### Workflow de Aprobación
```python
from apps.inventario.models import AjustesInventario, DetallesAjuste

# 1. Crear ajuste
ajuste = AjustesInventario.objects.create(
    tipo_ajuste='Merma',
    estado='Pendiente',
    motivo='Merma detectada en inventario mensual',
    observaciones='5% de productos perecederos',
    id_empleado_id=empleado_id
)

# 2. Agregar detalles
DetallesAjuste.objects.create(
    id_ajuste=ajuste,
    id_producto_id=producto_id,
    cantidad_ajuste=Decimal('-5'),
    stock_antes=Decimal('100'),
    stock_despues=Decimal('95'),
    motivo_detalle='Deterioro por humedad'
)

# 3. Aprobar (supervisor)
ajuste.estado = 'Aprobado'
ajuste.fecha_aprobacion = timezone.now()
ajuste.save()

# 4. Aplicar a stock
with transaction.atomic():
    for detalle in ajuste.detalles.all():
        stock = StockUnico.objects.select_for_update().get(id_producto=detalle.id_producto)
        
        # Registrar movimiento
        MovimientosStock.objects.create(
            tipo_movimiento='Egreso' if detalle.cantidad_ajuste < 0 else 'Ingreso',
            cantidad=abs(detalle.cantidad_ajuste),
            stock_anterior=stock.cantidad,
            stock_resultante=stock.cantidad + detalle.cantidad_ajuste,
            motivo=f'Ajuste {ajuste.tipo_ajuste}: {ajuste.motivo}',
            tipo_referencia='Ajuste',
            id_referencia=ajuste.id_ajuste,
            id_producto=detalle.id_producto,
            id_empleado=ajuste.id_empleado
        )
        
        # Actualizar stock
        stock.cantidad += detalle.cantidad_ajuste
        stock.save()
    
    ajuste.estado = 'Aplicado'
    ajuste.save()
```

---

### 4. DetallesAjuste
**Líneas de productos ajustados en cada ajuste**

```python
class DetallesAjuste(models.Model):
    id_detalle_ajuste = AutoField(primary_key=True)
    cantidad_ajuste = DecimalField(max_digits=10, decimal_places=3)
    stock_antes = DecimalField(max_digits=10, decimal_places=3)
    stock_despues = DecimalField(max_digits=10, decimal_places=3)
    motivo_detalle = CharField(max_length=255)
    id_ajuste = ForeignKey(AjustesInventario)
    id_producto = ForeignKey('productos.Productos')
```

#### Validaciones
- `cantidad_ajuste != 0`
- `stock_despues = stock_antes + cantidad_ajuste`
- Mermas: cantidad_ajuste < 0
- Sobrantes: cantidad_ajuste > 0

---

### 5. CostosHistoricos
**Historial de costos para cálculo de CPP**

```python
class CostosHistoricos(models.Model):
    id_costo = AutoField(primary_key=True)
    costo_unitario = DecimalField(max_digits=15, decimal_places=2)
    cantidad_comprada = DecimalField(max_digits=10, decimal_places=3)
    fecha_registro = DateTimeField(auto_now_add=True)
    id_producto = ForeignKey('productos.Productos')
    id_proveedor = ForeignKey('compras.Proveedores')
    id_compra = ForeignKey('compras.Compras')
```

#### Costo Promedio Ponderado (CPP)
```python
def calcular_cpp(producto_id):
    """
    CPP = Σ(costo_unitario × cantidad) / Σ(cantidad)
    """
    costos = CostosHistoricos.objects.filter(
        id_producto=producto_id
    ).aggregate(
        total_monto=Sum(F('costo_unitario') * F('cantidad_comprada')),
        total_cantidad=Sum('cantidad_comprada')
    )
    
    if costos['total_cantidad'] and costos['total_cantidad'] > 0:
        return (costos['total_monto'] / costos['total_cantidad']).quantize(Decimal('0.01'))
    return Decimal('0.00')
```

#### Registro de Costo en Compra
```python
from apps.inventario.models import CostosHistoricos

# Al recibir compra
for detalle in compra.detalles.all():
    CostosHistoricos.objects.create(
        costo_unitario=detalle.precio_unitario,
        cantidad_comprada=detalle.cantidad,
        id_producto=detalle.id_producto,
        id_proveedor=compra.id_proveedor,
        id_compra=compra
    )
```

---

### 6. AlertasStock
**Notificaciones automáticas de stock bajo**

```python
class AlertasStock(models.Model):
    id_alerta = AutoField(primary_key=True)
    nivel_alerta = CharField(max_length=10)  # Critico|Alto|Medio|Bajo
    cantidad_actual = DecimalField(max_digits=10, decimal_places=3)
    cantidad_minima = DecimalField(max_digits=10, decimal_places=3)
    mensaje = CharField(max_length=255)
    estado = CharField(max_length=10)  # Activa|Resuelta
    fecha_creacion = DateTimeField(auto_now_add=True)
    fecha_resolucion = DateTimeField()
    id_producto = ForeignKey('productos.Productos')
```

#### Niveles de Alerta
- **Critico**: Stock ≤ 25% del mínimo (color rojo)
- **Alto**: Stock ≤ 50% del mínimo (color naranja)
- **Medio**: Stock ≤ 75% del mínimo (color amarillo)
- **Bajo**: Stock ≤ 100% del mínimo (color azul)

#### Generación Automática
```python
from apps.inventario.models import AlertasStock, StockUnico
from apps.productos.models import Productos

def generar_alertas_stock():
    """
    Ejecutar diariamente via Celery/cron
    """
    for stock in StockUnico.objects.filter(cantidad__lte=F('id_producto__stock_minimo')):
        producto = stock.id_producto
        porcentaje = (stock.cantidad / producto.stock_minimo) * 100
        
        if porcentaje <= 25:
            nivel = 'Critico'
        elif porcentaje <= 50:
            nivel = 'Alto'
        elif porcentaje <= 75:
            nivel = 'Medio'
        else:
            nivel = 'Bajo'
        
        # Crear alerta si no existe una activa
        if not AlertasStock.objects.filter(
            id_producto=producto,
            estado='Activa'
        ).exists():
            AlertasStock.objects.create(
                nivel_alerta=nivel,
                cantidad_actual=stock.cantidad,
                cantidad_minima=producto.stock_minimo,
                mensaje=f'Stock bajo: {stock.cantidad} de {producto.stock_minimo} mínimo',
                estado='Activa',
                id_producto=producto
            )
```

---

### 7. LotesProducto
**Control de lotes y trazabilidad FEFO**

```python
class LotesProducto(models.Model):
    id_lote = AutoField(primary_key=True)
    numero_lote = CharField(max_length=50, unique=True)
    fecha_vencimiento = DateField()
    cantidad_inicial = DecimalField(max_digits=10, decimal_places=3)
    cantidad_actual = DecimalField(max_digits=10, decimal_places=3)
    estado = CharField(max_length=10)  # Activo|Agotado|Vencido
    fecha_ingreso = DateTimeField(auto_now_add=True)
    id_producto = ForeignKey('productos.Productos')
    id_compra = ForeignKey('compras.Compras')
```

#### Formato Número de Lote
- Mínimo 3 caracteres
- Solo alfanumérico y guiones: `LOT-20240115-001`, `ABC123`, `2024-01-PROV1`

#### Estados del Lote
- **Activo**: Lote disponible con stock
- **Agotado**: Cantidad_actual = 0
- **Vencido**: fecha_vencimiento < hoy

#### Implementación FEFO
```python
def obtener_lotes_disponibles(producto_id, cantidad_solicitada):
    """
    First Expired, First Out - usar lotes que vencen primero
    """
    lotes = LotesProducto.objects.filter(
        id_producto=producto_id,
        estado='Activo',
        cantidad_actual__gt=0
    ).order_by('fecha_vencimiento')
    
    asignaciones = []
    cantidad_restante = cantidad_solicitada
    
    for lote in lotes:
        if cantidad_restante <= 0:
            break
        
        cantidad_usar = min(lote.cantidad_actual, cantidad_restante)
        
        asignaciones.append({
            'lote': lote,
            'cantidad': cantidad_usar
        })
        
        cantidad_restante -= cantidad_usar
    
    if cantidad_restante > 0:
        raise ValueError(f"Stock insuficiente. Faltante: {cantidad_restante}")
    
    return asignaciones
```

---

### 8. AlertasVencimiento
**Avisos de proximación a fecha de vencimiento**

```python
class AlertasVencimiento(models.Model):
    id_alerta_vencimiento = AutoField(primary_key=True)
    dias_restantes = IntegerField()
    mensaje = CharField(max_length=255)
    estado = CharField(max_length=10)  # Activa|Resuelta
    fecha_creacion = DateTimeField(auto_now_add=True)
    fecha_resolucion = DateTimeField()
    id_lote = ForeignKey(LotesProducto)
    id_producto = ForeignKey('productos.Productos')
```

#### Umbrales de Alerta
- **Crítico** (≤ 3 días): Acción inmediata
- **Alta** (≤ 7 días): Promoción urgente
- **Media** (≤ 15 días): Planificar descuento
- **Baja** (≤ 30 días): Monitorear

#### Generación de Alertas
```python
from datetime import timedelta

def generar_alertas_vencimiento():
    """
    Ejecutar diariamente
    """
    hoy = timezone.now().date()
    
    for lote in LotesProducto.objects.filter(
        estado='Activo',
        cantidad_actual__gt=0,
        fecha_vencimiento__lte=hoy + timedelta(days=30)
    ):
        dias_restantes = (lote.fecha_vencimiento - hoy).days
        
        if días_restantes <= 7:
            # Crear alerta si no existe
            if not AlertasVencimiento.objects.filter(
                id_lote=lote,
                estado='Activa'
            ).exists():
                AlertasVencimiento.objects.create(
                    dias_restantes=dias_restantes,
                    mensaje=f'Lote {lote.numero_lote} vence en {dias_restantes} días',
                    estado='Activa',
                    id_lote=lote,
                    id_producto=lote.id_producto
                )
```

---

## 🤖 ML Forecasting

### StockForecastingService

Servicio de Machine Learning para predicción de demanda y optimización de inventario.

#### Funcionalidades

##### 1. obtener_datos_historicos(id_producto, dias)
Obtiene histórico de ventas para análisis.

```python
from apps.inventario.ml_forecasting import StockForecastingService

datos = StockForecastingService.obtener_datos_historicos(producto_id=123, dias=90)

# Retorna:
{
    'fechas': [date(2024,01,01), date(2024,01,02), ...],
    'cantidades': [Decimal('10'), Decimal('15'), ...],
    'total_registros': 90,
    'periodo': {
        'desde': date(2024,01,01),
        'hasta': date(2024,03,31)
    }
}
```

##### 2. calcular_estadisticas_basicas(id_producto, dias)
Métricas estadísticas de demanda.

```python
stats = StockForecastingService.calcular_estadisticas_basicas(producto_id=123, dias=30)

# Retorna:
{
    'demanda_promedio_diaria': Decimal('12.5'),
    'demanda_maxima': Decimal('25'),
    'demanda_minima': Decimal('5'),
    'desviacion_estandar': 4.2,
    'coeficiente_variacion': 0.336,
    'tendencia': 'creciente',  # creciente|decreciente|estable
    'estacionalidad': True,
    'total_dias_con_venta': 28,
    'periodo_analisis': 30
}
```

##### 3. predecir_demanda_simple(id_producto, dias_adelante=7)
Predicción usando promedios móviles y patrones semanales.

```python
predicciones = StockForecastingService.predecir_demanda_simple(producto_id=123, dias_adelante=7)

# Retorna:
[
    {
        'fecha': date(2024,04,01),
        'demanda_predicha': Decimal('13.5'),
        'intervalo_confianza': (Decimal('9.3'), Decimal('17.7')),
        'dia_semana': 'Lunes',
        'confianza': 0.85,
        'metodo': 'promedio_movil'
    },
    ...
]
```

##### 4. calcular_punto_reorden(id_producto, lead_time_dias=7)
Calcula nivel óptimo para ordenar reabastecimiento.

**Fórmula:**
```
Punto de Reorden = (Demanda Diaria × Lead Time) + Stock de Seguridad
Stock de Seguridad = max(Demanda_Máx - Demanda_Prom, Desv_Std × 1.65)
```

```python
punto = StockForecastingService.calcular_punto_reorden(producto_id=123, lead_time_dias=7)

# Retorna:
{
    'punto_reorden': Decimal('150'),
    'stock_seguridad': Decimal('50'),
    'demanda_durante_lead_time': Decimal('100'),
    'demanda_diaria_promedio': Decimal('14.3'),
    'lead_time_dias': 7,
    'metodo': 'demanda_promedio_mas_seguridad',
    'confianza': 0.85,
    'recomendacion': 'Actualizar stock mínimo de 80 a 150'
}
```

##### 5. detectar_anomalias(id_producto, dias=30)
Identifica picos y caídas anormales en ventas.

```python
anomalias = StockForecastingService.detectar_anomalias(producto_id=123, dias=30)

# Retorna:
[
    {
        'fecha': date(2024,03,15),
        'cantidad': Decimal('50'),
        'tipo': 'pico',
        'desviacion': 3.2,  # desviaciones estándar
        'explicacion': 'Venta anormalmente alta (50 vs promedio 12)',
        'posible_causa': 'Evento especial, promoción, o error de registro'
    },
    ...
]
```

##### 6. analizar_estacionalidad(id_producto, dias=90)
Detecta patrones estacionales semanales/mensuales.

```python
estacionalidad = StockForecastingService.analizar_estacionalidad(producto_id=123, dias=90)

# Retorna:
{
    'tiene_estacionalidad': True,
    'patron_semanal': {
        'Lunes': 10.5,
        'Martes': 12.0,
        'Miércoles': 11.5,
        'Jueves': 13.0,
        'Viernes': 18.5,
        'Sábado': 22.0,
        'Domingo': 8.0
    },
    'dias_pico': ['Viernes', 'Sábado'],
    'dias_valle': ['Domingo', 'Lunes'],
    'recomendacion': 'Ajustar pedidos según patrones detectados'
}
```

##### 7. obtener_recomendacion_compra(id_producto, stock_actual, dias_cobertura_deseada=14)
Recomienda cantidad óptima a comprar.

```python
recomendacion = StockForecastingService.obtener_recomendacion_compra(
    id_producto=123,
    stock_actual=Decimal('50'),
    dias_cobertura_deseada=14
)

# Retorna:
{
    'cantidad_comprar': Decimal('120'),
    'urgencia': 'alta',  # critica|alta|media|baja|no_necesaria
    'dias_cobertura_actual': 4,
    'dias_cobertura_deseada': 14,
    'prediccion_agotamiento': date(2024,04,05),
    'demanda_diaria_estimada': Decimal('12.5'),
    'punto_reorden': Decimal('150'),
    'justificacion': 'Stock bajo: 4 días de cobertura'
}
```

### Uso en Endpoints API

```python
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.inventario.ml_forecasting import StockForecastingService

class StockUnicoViewSet(viewsets.ModelViewSet):
    
    @action(detail=True, methods=['get'])
    def prediccion_demanda(self, request, pk=None):
        """
        GET /api/v1/inventario/stock/{id}/prediccion_demanda/?dias=7
        """
        stock = self.get_object()
        dias = int(request.query_params.get('dias', 7))
        
        predicciones = StockForecastingService.predecir_demanda_simple(
            id_producto=stock.id_producto.id_producto,
            dias_adelante=dias
        )
        
        return Response({
            'producto': stock.id_producto.descripcion,
            'stock_actual': stock.cantidad,
            'predicciones': predicciones
        })
    
    @action(detail=True, methods=['get'])
    def recomendacion_compra(self, request, pk=None):
        """
        GET /api/v1/inventario/stock/{id}/recomendacion_compra/?cobertura=14
        """
        stock = self.get_object()
        cobertura = int(request.query_params.get('cobertura', 14))
        
        recomendacion = StockForecastingService.obtener_recomendacion_compra(
            id_producto=stock.id_producto.id_producto,
            stock_actual=stock.cantidad,
            dias_cobertura_deseada=cobertura
        )
        
        return Response(recomendacion)
```

---

## ✅ Validadores

El módulo incluye **24 validadores** para asegurar integridad de datos.

### Validadores de Stock
```python
from apps.inventario.validators import (
    validar_cantidad_positiva,
    validar_cantidad_no_negativa,
    validar_stock_minimo_maximo,
    validar_punto_reorden,
    validar_stock_disponible
)

# Uso
validar_cantidad_positiva(10)  # OK
validar_cantidad_positiva(0)   # ❌ ValidationError

validar_stock_minimo_maximo(10, 100)  # OK
validar_stock_minimo_maximo(100, 10)  # ❌ ValidationError

validar_stock_disponible(producto_id=123, cantidad_solicitada=50)
```

### Validadores de Movimientos
```python
from apps.inventario.validators import (
    validar_tipo_movimiento,
    validar_motivo_movimiento,
    validar_referencia_movimiento
)

validar_tipo_movimiento('Ingreso')  # OK
validar_tipo_movimiento('Traslado')  # ❌ ValidationError

validar_motivo_movimiento('Compra de mercadería')  # OK (>= 10 chars)
validar_motivo_movimiento('Compra')  # ❌ ValidationError (muy corto)
```

### Validadores de Ajustes
```python
from apps.inventario.validators import (
    validar_tipo_ajuste,
    validar_estado_ajuste,
    validar_cantidad_ajuste,
    validar_merma_aceptable
)

validar_cantidad_ajuste(Decimal('-10'), 'Merma')  # OK (negativo)
validar_cantidad_ajuste(Decimal('10'), 'Merma')   # ❌ ValidationError

validar_merma_aceptable(
    cantidad_merma=Decimal('3'),
    cantidad_total=Decimal('100'),
    porcentaje_max=5  # 3% < 5% = OK
)
```

### Validadores de ML
```python
from apps.inventario.validators import (
    validar_dias_historico,
    validar_umbral_confianza,
    validar_lead_time,
    validar_dias_cobertura
)

validar_dias_historico(30)  # OK (7-365)
validar_dias_historico(5)   # ❌ ValidationError (mínimo 7)

validar_umbral_confianza(0.85)  # OK (0.50-0.99)
validar_umbral_confianza(0.3)   # ❌ ValidationError
```

**Ver lista completa en:** [validators.py](validators.py)

---

## 🧪 Testing

### Ejecutar Tests
```bash
# Todos los tests del módulo
python manage.py test apps.inventario

# Solo tests de validadores
python manage.py test apps.inventario.tests_validators

# Solo tests de ML
python manage.py test apps.inventario.tests_ml

# Con cobertura
coverage run --source='apps.inventario' manage.py test apps.inventario
coverage report
```

### Cobertura Actual
- **tests_validators.py**: 88 tests, 100% cobertura de validadores
- **tests_ml.py**: 15 tests, cobertura de ML forecasting
- **tests.py**: Tests de modelos y servicios

---

## 🔒 Buenas Prácticas

### 1. Actualización de Stock

❌ **NUNCA hacer esto:**
```python
# MAL - Race condition
stock = StockUnico.objects.get(id_producto=123)
stock.cantidad -= 10
stock.save()
```

✅ **SIEMPRE usar transacción atómica:**
```python
from django.db import transaction

with transaction.atomic():
    stock = StockUnico.objects.select_for_update().get(id_producto=123)
    
    # Validar
    if stock.cantidad < 10:
        raise ValueError("Stock insuficiente")
    
    # Registrar movimiento PRIMERO
    MovimientosStock.objects.create(
        tipo_movimiento='Egreso',
        cantidad=10,
        stock_anterior=stock.cantidad,
        stock_resultante=stock.cantidad - 10,
        motivo='Venta #1234',
        tipo_referencia='Venta',
        id_referencia=1234,
        id_producto_id=123,
        id_empleado_id=empleado_id
    )
    
    # Actualizar stock DESPUÉS
    stock.cantidad -= 10
    stock.save()
```

### 2. Validación de Stock en Ventas

```python
from apps.inventario.validators import validar_stock_disponible
from django.core.exceptions import ValidationError

try:
    validar_stock_disponible(producto_id=123, cantidad_solicitada=50)
except ValidationError as e:
    return Response({'error': str(e)}, status=400)
```

### 3. Uso de Forecasting

```python
# Obtener recomendación antes de crear orden de compra
recomendacion = StockForecastingService.obtener_recomendacion_compra(
    id_producto=producto.id_producto,
    stock_actual=stock.cantidad,
    dias_cobertura_deseada=14
)

if recomendacion['urgencia'] in ['critica', 'alta']:
    # Crear orden de compra automática
    crear_orden_compra(producto, recomendacion['cantidad_comprar'])
```

---

## 📡 API Endpoints

### Stock
```
GET    /api/v1/inventario/stock/                    # Listar stock
GET    /api/v1/inventario/stock/{id}/               # Detalle
GET    /api/v1/inventario/stock/{id}/prediccion_demanda/     # ML
GET    /api/v1/inventario/stock/{id}/recomendacion_compra/   # ML
POST   /api/v1/inventario/stock/{id}/ajustar/       # Ajuste manual
```

### Movimientos
```
GET    /api/v1/inventario/movimientos/              # Listar movimientos
GET    /api/v1/inventario/movimientos/{id}/         # Detalle
GET    /api/v1/inventario/movimientos/?producto=123  # Por producto
GET    /api/v1/inventario/movimientos/?fecha_desde=2024-01-01  # Filtros
```

### Ajustes
```
GET    /api/v1/inventario/ajustes/                  # Listar ajustes
POST   /api/v1/inventario/ajustes/                  # Crear ajuste
GET    /api/v1/inventario/ajustes/{id}/             # Detalle
PATCH  /api/v1/inventario/ajustes/{id}/aprobar/    # Aprobar
PATCH  /api/v1/inventario/ajustes/{id}/rechazar/   # Rechazar
POST   /api/v1/inventario/ajustes/{id}/aplicar/    # Aplicar a stock
```

---

## 📊 Dashboard de Inventario

### Métricas Clave
```python
# Valor total del inventario
total_valor = StockUnico.objects.aggregate(
    valor_total=Sum(
        F('cantidad') * F('id_producto__costoshistoricos__costo_unitario')
    )
)['valor_total']

# Productos que requieren reposición
productos_bajo_stock = StockUnico.objects.filter(
    cantidad__lte=F('id_producto__stock_minimo')
).count()

# Alertas activas
alertas_criticas = AlertasStock.objects.filter(
    estado='Activa',
    nivel_alerta='Critico'
).count()

# Lotes próximos a vencer (7 días)
lotes_vencer_pronto = LotesProducto.objects.filter(
    estado='Activo',
    fecha_vencimiento__lte=timezone.now().date() + timedelta(days=7)
).count()
```

---

## 🔧 Mantenimiento

### Tareas Periódicas (Celery)

```python
from celery import shared_task

@shared_task
def generar_alertas_diarias():
    """
    Ejecutar diariamente a las 6:00 AM
    """
    generar_alertas_stock()
    generar_alertas_vencimiento()

@shared_task
def actualizar_estados_lotes():
    """
    Ejecutar diariamente a las 0:00
    """
    hoy = timezone.now().date()
    
    # Marcar lotes vencidos
    LotesProducto.objects.filter(
        fecha_vencimiento__lt=hoy,
        estado='Activo'
    ).update(estado='Vencido')
    
    # Marcar lotes agotados
    LotesProducto.objects.filter(
        cantidad_actual=0,
        estado='Activo'
    ).update(estado='Agotado')

@shared_task
def calcular_puntos_reorden_automaticos():
    """
    Ejecutar semanalmente
    """
    for stock in StockUnico.objects.all():
        resultado = StockForecastingService.calcular_punto_reorden(
            id_producto=stock.id_producto.id_producto
        )
        
        # Actualizar producto si punto calculado es mayor
        if 'punto_reorden' in resultado:
            producto = stock.id_producto
            if resultado['punto_reorden'] > producto.stock_minimo:
                producto.stock_minimo = resultado['punto_reorden']
                producto.save()
```

---

## 🎓 Ejemplos de Uso Completos

### Ejemplo 1: Procesar Venta con Stock
```python
from django.db import transaction
from apps.inventario.models import StockUnico, MovimientosStock
from apps.inventario.validators import validar_stock_disponible
from decimal import Decimal

def procesar_venta_con_stock(venta_id, detalles_venta, empleado_id):
    """
    Procesar venta actualizando stock de forma segura
    """
    with transaction.atomic():
        for detalle in detalles_venta:
            producto_id = detalle['producto_id']
            cantidad = Decimal(str(detalle['cantidad']))
            
            # 1. Validar disponibilidad
            validar_stock_disponible(producto_id, cantidad)
            
            # 2. Bloquear stock para actualización
            stock = StockUnico.objects.select_for_update().get(id_producto=producto_id)
            
            # 3. Registrar movimiento
            MovimientosStock.objects.create(
                tipo_movimiento='Egreso',
                cantidad=cantidad,
                stock_anterior=stock.cantidad,
                stock_resultante=stock.cantidad - cantidad,
                motivo=f'Venta #{venta_id}',
                tipo_referencia='Venta',
                id_referencia=venta_id,
                id_producto_id=producto_id,
                id_empleado_id=empleado_id
            )
            
            # 4. Actualizar stock
            stock.cantidad -= cantidad
            stock.save()
            
            # 5. Verificar si genera alerta
            if stock.requiere_reposicion:
                generar_alerta_stock_bajo(producto_id)
```

### Ejemplo 2: Recepción de Compra con Lotes
```python
def recepcionar_compra_con_lotes(compra_id, detalles, empleado_id):
    """
    Recepcionar compra registrando lotes y actualizando costos
    """
    with transaction.atomic():
        for detalle in detalles:
            producto_id = detalle['producto_id']
            cantidad = Decimal(str(detalle['cantidad']))
            costo_unitario = Decimal(str(detalle['precio_unitario']))
            numero_lote = detalle.get('numero_lote')
            fecha_vencimiento = detalle.get('fecha_vencimiento')
            
            # 1. Registrar costo histórico
            CostosHistoricos.objects.create(
                costo_unitario=costo_unitario,
                cantidad_comprada=cantidad,
                id_producto_id=producto_id,
                id_proveedor_id=compra.id_proveedor_id,
                id_compra_id=compra_id
            )
            
            # 2. Crear lote si aplica
            if numero_lote:
                lote = LotesProducto.objects.create(
                    numero_lote=numero_lote,
                    fecha_vencimiento=fecha_vencimiento,
                    cantidad_inicial=cantidad,
                    cantidad_actual=cantidad,
                    estado='Activo',
                    id_producto_id=producto_id,
                    id_compra_id=compra_id
                )
            
            # 3. Actualizar stock
            stock = StockUnico.objects.select_for_update().get(id_producto=producto_id)
            
            MovimientosStock.objects.create(
                tipo_movimiento='Ingreso',
                cantidad=cantidad,
                stock_anterior=stock.cantidad,
                stock_resultante=stock.cantidad + cantidad,
                motivo=f'Compra #{compra_id}',
                tipo_referencia='Compra',
                id_referencia=compra_id,
                id_producto_id=producto_id,
                id_empleado_id=empleado_id
            )
            
            stock.cantidad += cantidad
            stock.save()
```

---

## 📝 Notas Finales

### Estado del Módulo
- **Completitud**: 100% ✅
- **Tests**: 100+ tests ✅
- **Documentación**: Completa ✅
- **Producción**: Listo ✅

### Dependencias
- `numpy`: Para cálculos estadísticos en ML
- `django-celery-beat`: Para tareas periódicas
- Apps relacionadas: `productos`, `compras`, `ventas`, `usuarios`

### Próximas Mejoras
- [ ] Integración con scikit-learn para RandomForest
- [ ] Reportes de rotación de inventario
- [ ] API de exportación a Excel
- [ ] Dashboard en tiempo real con WebSockets

---

**Última actualización**: Enero 2024
**Versión**: 1.0.0
**Mantenedor**: Equipo Cantina Tita
