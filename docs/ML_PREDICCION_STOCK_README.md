# Sistema de Predicción de Stock con Machine Learning

## 📋 Descripción

Servicio de forecasting y análisis predictivo para gestión inteligente de inventario. Utiliza técnicas de Machine Learning para predecir demanda, calcular puntos de reorden óptimos y detectar anomalías en patrones de venta.

## 🎯 Características

### 1. Predicción de Demanda
- **Método**: Promedio móvil ajustado con análisis de estacionalidad
- **Horizonte**: Configurable (default 7 días)
- **Ajustes**: Por día de semana y tendencia histórica
- **Salida**: Demanda predicha + intervalo de confianza

### 2. Cálculo de Punto de Reorden
- **Fórmula**: `PR = (Demanda Diaria × Lead Time) + Stock Seguridad`
- **Stock de Seguridad**: Basado en variabilidad histórica
- **Lead Time**: Configurable por producto
- **Clasificación**: Crítico/Bajo/Saludable/Exceso

### 3. Detección de Anomalías
- **Método**: Análisis de desviación estándar (2-sigma)
- **Tipos**: Picos de venta / Caídas anómalas
- **Causas**: Eventos especiales, falta de stock, errores
- **Alertas**: Automáticas para revisión manual

### 4. Análisis de Estacionalidad
- **Patrones**: Semanales, mensuales
- **Identificación**: Días pico y valle
- **Recomendaciones**: Ajuste de pedidos según patrones

### 5. Recomendaciones de Compra
- **Cálculo**: Basado en demanda predicha y cobertura deseada
- **Urgencia**: 5 niveles (Crítica → No necesaria)
- **Optimización**: Minimiza quiebres y costos de almacenamiento

## 🚀 Endpoints API

### Base URL
```
/api/v1/inventario/ajustes/
```

### 1. Predicción de Demanda
```http
GET /prediccion-demanda/?id_producto=1&dias=7
```

**Respuesta:**
```json
{
    "producto": {...},
    "estadisticas": {
        "demanda_promedio_diaria": 12.5,
        "demanda_maxima": 25.0,
        "tendencia": "creciente",
        "estacionalidad": true
    },
    "predicciones": [
        {
            "fecha": "2026-03-02",
            "demanda_predicha": 13.2,
            "intervalo_confianza": [9.5, 16.9],
            "dia_semana": "Lunes",
            "confianza": 0.85
        }
    ],
    "patron_estacional": {...}
}
```

### 2. Punto de Reorden
```http
GET /punto-reorden/?id_producto=1&lead_time=7
```

**Respuesta:**
```json
{
    "producto": {...},
    "stock_actual": 50.0,
    "punto_reorden_calculado": 95.5,
    "stock_seguridad": 25.5,
    "demanda_durante_lead_time": 70.0,
    "estado": "saludable",
    "nivel_urgencia": "bajo",
    "recomendacion": "Stock en niveles adecuados"
}
```

### 3. Detectar Anomalías
```http
GET /detectar-anomalias/?id_producto=1&dias=30
```

**Respuesta:**
```json
{
    "producto": {...},
    "anomalias_detectadas": [
        {
            "fecha": "2026-02-15",
            "cantidad": 85,
            "tipo": "pico",
            "desviacion": 2.5,
            "explicacion": "Venta anormalmente alta (85 vs promedio 32)",
            "posible_causa": "Evento especial o promoción"
        }
    ],
    "total_anomalias": 3,
    "clasificacion": {
        "picos": 2,
        "caidas": 1
    }
}
```

### 4. Recomendación de Compra
```http
GET /recomendacion-compra/?id_producto=1&dias_cobertura=14
```

**Respuesta:**
```json
{
    "producto": {...},
    "stock_actual": 25.0,
    "cantidad_comprar": 150.0,
    "urgencia": "alta",
    "color_urgencia": "#fd7e14",
    "dias_cobertura_actual": 5,
    "prediccion_agotamiento": "2026-03-06",
    "justificacion": "Stock bajo: 5 días de cobertura"
}
```

### 5. Análisis Completo
```http
GET /analisis-completo/?id_producto=1
```

**Respuesta:** Consolidación de todos los análisis anteriores.

## 📊 Niveles de Urgencia

| Nivel | Días Cobertura | Color | Acción Recomendada |
|-------|---------------|-------|-------------------|
| 🔴 Crítica | ≤ 2 días | #dc3545 | Compra URGENTE |
| 🟠 Alta | ≤ 5 días | #fd7e14 | Compra prioritaria |
| 🟡 Media | ≤ 10 días | #ffc107 | Planificar compra |
| 🔵 Baja | > 10 días | #17a2b8 | Monitorear |
| 🟢 No necesaria | > cobertura deseada | #28a745 | Stock suficiente |

## 🎓 Algoritmos Utilizados

### Promedio Móvil Ajustado
```python
# Demanda base (promedio del día de semana)
demanda_base = promedio_historico[dia_semana]

# Ajuste por tendencia
if tendencia == 'creciente':
    factor = 1.05  # 5% incremento proyectado
elif tendencia == 'decreciente':
    factor = 0.95  # 5% decremento proyectado
else:
    factor = 1.0

# Predicción final
demanda_predicha = demanda_base * (factor^(dias/30))
```

### Stock de Seguridad (Método Dual)
```python
# Método 1: Diferencia máximo-promedio
ss1 = demanda_maxima - demanda_promedio

# Método 2: Desviación estándar (95% confianza)
ss2 = desviacion_estandar * 1.65

# Usar el mayor para mayor seguridad
stock_seguridad = max(ss1, ss2)
```

### Detección de Anomalías (2-Sigma)
```python
# Umbrales estadísticos
umbral_superior = media + (2 * desviacion_std)
umbral_inferior = media - (2 * desviacion_std)

# Clasificación
if valor > umbral_superior:
    tipo = "pico"
elif valor < umbral_inferior:
    tipo = "caida"
```

## ⚙️ Configuración

### Constantes de Negocio
```python
DIAS_HISTORICO_MINIMO = 30  # Mínimo para entrenar modelos
DIAS_HISTORICO_OPTIMO = 90  # Óptimo para mejores predicciones
STOCK_SEGURIDAD_FACTOR = 1.5  # Multiplicador de seguridad
CONFIANZA_MINIMA = 0.6  # Confianza mínima del modelo
```

### Requisitos de Datos
- **Mínimo**: 7 días de historial de ventas
- **Recomendado**: 30-90 días
- **Óptimo**: 90+ días para análisis estacional completo

## 🛠️ Tecnologías

- **Python 3.14+**
- **NumPy 2.4.2**: Cálculos numéricos y estadísticos
- **Django REST Framework**: Exposición de endpoints
- **Sin scikit-learn**: Implementación ligera sin dependencias pesadas

## 📈 Mejoras Futuras

### Corto Plazo
- [ ] Implementar caching de predicciones (TTL: 1 hora)
- [ ] Tests unitarios completos (actualmente pendiente por complejidad de fixtures)
- [ ] Dashboard visual con gráficos de predicciones

### Mediano Plazo
- [ ] Modelo ARIMA para series temporales
- [ ] Análisis de correlación entre productos
- [ ] Predicción de promociones óptimas

### Largo Plazo
- [ ] Deep Learning (LSTM) para productos con alta variabilidad
- [ ] Integración con sistema de órdenes automáticas
- [ ] A/B testing de algoritmos

## 📝 Notas de Implementación

1. **Sin Datos Históricos**: Si un producto no tiene suficiente historial, el sistema retorna un error descriptivo y recomienda configuración manual.

2. **Performance**: Las consultas están optimizadas con `.filter()` y agregaciones de Django ORM. Para catálogos grandes (>10,000 productos), consider implementing background tasks.

3. **Precisión**: La confianza del modelo aumenta con más datos históricos:
   - 7-30 días: Confianza ~50-70%
   - 30-60 días: Confianza ~70-85%
   - 60+ días: Confianza ~85-95%

4. **Casos Especiales**:
   - Productos nuevos: Usar promedio de categoría similar
   - Productos estacionales: Requiere al menos un ciclo completo
   - Productos promocionales: Excluir días de promoción del análisis base

## 🔗 Referencias

- [Inventory Management Best Practices](https://en.wikipedia.org/wiki/Inventory_management)
- [Reorder Point Formula](https://en.wikipedia.org/wiki/Reorder_point)
- [Time Series Forecasting](https://en.wikipedia.org/wiki/Time_series)
- [Anomaly Detection](https://en.wikipedia.org/wiki/Anomaly_detection)

## 👥 Contacto

Para dudas o sugerencias sobre el sistema de ML, contactar al equipo de desarrollo.

---

**Versión**: 1.0.0  
**Fecha**: 1 de marzo de 2026  
**Autor**: Sistema Cantina Tita - Módulo ML
