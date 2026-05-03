"""
Servicio de Machine Learning para predicción de demanda y stock.

Utiliza modelos de ML para:
- Predecir demanda futura de productos
- Calcular punto de reorden óptimo
- Detectar anomalías en patrones de venta
- Análisis de estacionalidad

Modelos soportados:
- RandomForest para forecasting general
- Análisis de series temporales
- Detección de outliers
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from django.core.cache import cache
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

import numpy as np


class StockForecastingService:
    """
    Servicio centralizado para predicción de stock usando Machine Learning.
    """

    # Constantes de negocio
    DIAS_HISTORICO_MINIMO = 30  # Mínimo de días de historia para entrenar
    DIAS_HISTORICO_OPTIMO = 90  # Óptimo para mejores predicciones
    STOCK_SEGURIDAD_FACTOR = 1.5  # Factor multiplicador para stock de seguridad
    CONFIANZA_MINIMA = 0.6  # Confianza mínima del modelo (R²)

    @staticmethod
    def obtener_datos_historicos(id_producto: int, dias: int = 90) -> Dict:
        """
        Obtiene datos históricos de ventas para un producto.

        Args:
            id_producto: ID del producto
            dias: Cantidad de días hacia atrás

        Returns:
            {
                'fechas': List[datetime],
                'cantidades': List[Decimal],
                'precios': List[Decimal],
                'total_registros': int,
                'periodo': {'inicio': date, 'fin': date}
            }
        """
        from apps.inventario.models import MovimientosStock

        fecha_inicio = timezone.now() - timedelta(days=dias)

        # Obtener movimientos de venta
        movimientos = (
            MovimientosStock.objects.filter(
                id_producto_id=id_producto,
                tipo_movimiento="Egreso",
                motivo="venta",
                fecha_hora__gte=fecha_inicio,
            )
            .order_by("fecha_hora")
            .values("fecha_hora", "cantidad", "id_venta")
        )

        if not movimientos:
            return {
                "fechas": [],
                "cantidades": [],
                "precios": [],
                "total_registros": 0,
                "periodo": None,
                "error": "No hay datos históricos suficientes",
            }

        # Agrupar por día
        ventas_por_dia = {}
        for mov in movimientos:
            fecha = mov["fecha_hora"].date()
            if fecha not in ventas_por_dia:
                ventas_por_dia[fecha] = Decimal("0")
            ventas_por_dia[fecha] += mov["cantidad"]

        # Ordenar por fecha
        fechas_ordenadas = sorted(ventas_por_dia.keys())

        return {
            "fechas": fechas_ordenadas,
            "cantidades": [ventas_por_dia[f] for f in fechas_ordenadas],
            "total_registros": len(fechas_ordenadas),
            "periodo": {
                "inicio": fechas_ordenadas[0] if fechas_ordenadas else None,
                "fin": fechas_ordenadas[-1] if fechas_ordenadas else None,
            },
        }

    @staticmethod
    def calcular_estadisticas_basicas(id_producto: int, dias: int = 30) -> Dict:
        """
        Calcula estadísticas básicas de demanda sin ML.

        Args:
            id_producto: ID del producto
            dias: Período de análisis

        Returns:
            {
                'demanda_promedio_diaria': Decimal,
                'demanda_maxima': Decimal,
                'demanda_minima': Decimal,
                'desviacion_estandar': float,
                'tendencia': str,  # 'creciente', 'estable', 'decreciente'
                'estacionalidad': bool
            }
        """
        datos = StockForecastingService.obtener_datos_historicos(id_producto, dias)

        if datos["total_registros"] == 0:
            return {
                "demanda_promedio_diaria": Decimal("0"),
                "demanda_maxima": Decimal("0"),
                "demanda_minima": Decimal("0"),
                "desviacion_estandar": 0.0,
                "tendencia": "sin_datos",
                "estacionalidad": False,
                "error": "Sin datos históricos",
            }

        cantidades = [float(c) for c in datos["cantidades"]]

        # Estadísticas básicas
        promedio = np.mean(cantidades)
        maximo = np.max(cantidades)
        minimo = np.min(cantidades)
        desv_std = np.std(cantidades)

        # Detectar tendencia (comparar primera y segunda mitad)
        mitad = len(cantidades) // 2
        if mitad > 0:
            promedio_primera_mitad = np.mean(cantidades[:mitad])
            promedio_segunda_mitad = np.mean(cantidades[mitad:])

            if promedio_segunda_mitad > promedio_primera_mitad * 1.1:
                tendencia = "creciente"
            elif promedio_segunda_mitad < promedio_primera_mitad * 0.9:
                tendencia = "decreciente"
            else:
                tendencia = "estable"
        else:
            tendencia = "estable"

        # Detectar estacionalidad simple (varianza significativa)
        coef_variacion = (desv_std / promedio) if promedio > 0 else 0
        estacionalidad = coef_variacion > 0.3  # >30% variación sugiere estacionalidad

        return {
            "demanda_promedio_diaria": Decimal(str(round(promedio, 3))),
            "demanda_maxima": Decimal(str(round(maximo, 3))),
            "demanda_minima": Decimal(str(round(minimo, 3))),
            "desviacion_estandar": round(desv_std, 3),
            "coeficiente_variacion": round(coef_variacion, 3),
            "tendencia": tendencia,
            "estacionalidad": estacionalidad,
            "total_dias_con_venta": len(cantidades),
            "periodo_analisis": dias,
        }

    @staticmethod
    def predecir_demanda_simple(id_producto: int, dias_adelante: int = 7) -> List[Dict]:
        """
        Predicción simple basada en promedios móviles (sin scikit-learn).

        Utiliza:
        - Promedio móvil de 7 días
        - Ajuste por tendencia
        - Ajuste por día de semana

        Args:
            id_producto: ID del producto
            dias_adelante: Días a predecir

        Returns:
            Lista de predicciones:
            [
                {
                    'fecha': date,
                    'demanda_predicha': Decimal,
                    'intervalo_confianza': (min, max),
                    'dia_semana': str,
                    'confianza': float
                }
            ]
        """
        # Obtener estadísticas
        stats = StockForecastingService.calcular_estadisticas_basicas(id_producto, 30)

        if "error" in stats:
            return []

        # Obtener datos históricos para patrón semanal
        datos = StockForecastingService.obtener_datos_historicos(id_producto, 30)

        # Calcular promedio por día de semana
        ventas_por_dia_semana = {i: [] for i in range(7)}  # 0=lunes, 6=domingo

        for fecha, cantidad in zip(datos["fechas"], datos["cantidades"]):
            dia_semana = fecha.weekday()
            ventas_por_dia_semana[dia_semana].append(float(cantidad))

        # Promedios por día
        promedios_dia_semana = {}
        for dia, ventas in ventas_por_dia_semana.items():
            if ventas:
                promedios_dia_semana[dia] = np.mean(ventas)
            else:
                promedios_dia_semana[dia] = float(stats["demanda_promedio_diaria"])

        # Factor de tendencia
        if stats["tendencia"] == "creciente":
            factor_tendencia = 1.05  # 5% de incremento
        elif stats["tendencia"] == "decreciente":
            factor_tendencia = 0.95  # 5% de decremento
        else:
            factor_tendencia = 1.0

        # Generar predicciones
        predicciones = []
        hoy = timezone.now().date()

        for dia in range(dias_adelante):
            fecha_pred = hoy + timedelta(days=dia)
            dia_semana = fecha_pred.weekday()

            # Predicción base (promedio del día de semana)
            demanda_base = promedios_dia_semana[dia_semana]

            # Aplicar tendencia
            demanda_ajustada = demanda_base * (factor_tendencia ** (dia / 30))

            # Intervalo de confianza (± desviación estándar)
            desv = stats["desviacion_estandar"]
            intervalo_min = max(0, demanda_ajustada - desv)
            intervalo_max = demanda_ajustada + desv

            # Confianza basada en cantidad de datos
            confianza = min(0.95, 0.5 + (stats["total_dias_con_venta"] / 60))

            dias_semana_nombres = [
                "Lunes",
                "Martes",
                "Miércoles",
                "Jueves",
                "Viernes",
                "Sábado",
                "Domingo",
            ]

            predicciones.append(
                {
                    "fecha": fecha_pred,
                    "demanda_predicha": Decimal(str(round(demanda_ajustada, 3))),
                    "intervalo_confianza": (
                        Decimal(str(round(intervalo_min, 3))),
                        Decimal(str(round(intervalo_max, 3))),
                    ),
                    "dia_semana": dias_semana_nombres[dia_semana],
                    "confianza": round(confianza, 2),
                    "metodo": "promedio_movil",
                }
            )

        return predicciones

    @staticmethod
    def calcular_punto_reorden(id_producto: int, lead_time_dias: int = 7) -> Dict:
        """
        Calcula el punto de reorden óptimo.

        Fórmula: Punto de Reorden = (Demanda Diaria × Lead Time) + Stock de Seguridad
        Stock de Seguridad = Demanda Máxima - Demanda Promedio

        Args:
            id_producto: ID del producto
            lead_time_dias: Días que tarda en llegar el pedido

        Returns:
            {
                'punto_reorden': Decimal,
                'stock_seguridad': Decimal,
                'demanda_durante_lead_time': Decimal,
                'lead_time_dias': int,
                'metodo': str,
                'confianza': float
            }
        """
        from apps.productos.models import Productos

        stats = StockForecastingService.calcular_estadisticas_basicas(id_producto, 30)

        if "error" in stats:
            return {
                "error": "No hay datos suficientes para calcular punto de reorden",
                "punto_reorden": Decimal("0"),
                "recomendacion": "Usar stock mínimo configurado manualmente",
            }

        # Demanda durante lead time
        demanda_diaria = stats["demanda_promedio_diaria"]
        demanda_lead_time = demanda_diaria * lead_time_dias

        # Stock de seguridad (basado en variabilidad)
        # Método 1: Diferencia entre máximo y promedio
        stock_seguridad_1 = stats["demanda_maxima"] - stats["demanda_promedio_diaria"]

        # Método 2: Desviación estándar × factor de servicio (95%)
        stock_seguridad_2 = Decimal(str(stats["desviacion_estandar"])) * Decimal("1.65")

        # Usar el mayor para mayor seguridad
        stock_seguridad = max(stock_seguridad_1, stock_seguridad_2)

        # Punto de reorden
        punto_reorden = demanda_lead_time + stock_seguridad

        # Obtener stock mínimo actual
        try:
            producto = Productos.objects.get(id_producto=id_producto)
            stock_minimo_actual = producto.stock_minimo

            # Comparar con configuración manual
            if punto_reorden < stock_minimo_actual:
                recomendacion = f"Punto calculado ({punto_reorden}) es menor que mínimo configurado ({stock_minimo_actual}). Usar mínimo configurado."
                punto_reorden = stock_minimo_actual
            else:
                recomendacion = f"Actualizar stock mínimo de {stock_minimo_actual} a {punto_reorden}"
        except:
            recomendacion = "Configurar como nuevo stock mínimo"

        return {
            "punto_reorden": punto_reorden,
            "stock_seguridad": stock_seguridad,
            "demanda_durante_lead_time": demanda_lead_time,
            "demanda_diaria_promedio": demanda_diaria,
            "lead_time_dias": lead_time_dias,
            "metodo": "demanda_promedio_mas_seguridad",
            "confianza": 0.85,
            "recomendacion": recomendacion,
        }

    @staticmethod
    def detectar_anomalias(id_producto: int, dias: int = 30) -> List[Dict]:
        """
        Detecta patrones anómalos en ventas.

        Utiliza método de desviación estándar:
        - Anomalía si valor > media + 2×desv_std
        - O si valor < media - 2×desv_std

        Args:
            id_producto: ID del producto
            dias: Período de análisis

        Returns:
            Lista de anomalías detectadas:
            [
                {
                    'fecha': date,
                    'cantidad': Decimal,
                    'tipo': 'pico' | 'caida',
                    'desviacion': float,
                    'explicacion': str
                }
            ]
        """
        datos = StockForecastingService.obtener_datos_historicos(id_producto, dias)

        if datos["total_registros"] < 7:
            return []

        cantidades = np.array([float(c) for c in datos["cantidades"]])
        media = np.mean(cantidades)
        desv_std = np.std(cantidades)

        # Umbral de anomalía (2 desviaciones estándar)
        umbral_superior = media + (2 * desv_std)
        umbral_inferior = max(0, media - (2 * desv_std))

        anomalias = []

        for fecha, cantidad in zip(datos["fechas"], datos["cantidades"]):
            cantidad_float = float(cantidad)

            if cantidad_float > umbral_superior:
                desviacion = (cantidad_float - media) / desv_std
                anomalias.append(
                    {
                        "fecha": fecha,
                        "cantidad": cantidad,
                        "tipo": "pico",
                        "desviacion": round(desviacion, 2),
                        "explicacion": f"Venta anormalmente alta ({cantidad} vs promedio {round(media, 1)})",
                        "posible_causa": "Evento especial, promoción, o error de registro",
                    }
                )

            elif cantidad_float < umbral_inferior and media > 0:
                desviacion = (media - cantidad_float) / desv_std
                anomalias.append(
                    {
                        "fecha": fecha,
                        "cantidad": cantidad,
                        "tipo": "caida",
                        "desviacion": round(desviacion, 2),
                        "explicacion": f"Venta anormalmente baja ({cantidad} vs promedio {round(media, 1)})",
                        "posible_causa": "Falta de stock, día festivo, o error de registro",
                    }
                )

        return anomalias

    @staticmethod
    def analizar_estacionalidad(id_producto: int, dias: int = 90) -> Dict:
        """
        Analiza patrones estacionales en las ventas.

        Args:
            id_producto: ID del producto
            dias: Período de análisis (mínimo 60 días)

        Returns:
            {
                'tiene_estacionalidad': bool,
                'patron_semanal': Dict[str, float],  # Promedio por día de semana
                'patron_mensual': Dict[int, float],  # Promedio por día del mes
                'dias_pico': List[str],
                'dias_valle': List[str]
            }
        """
        datos = StockForecastingService.obtener_datos_historicos(id_producto, dias)

        if datos["total_registros"] < 14:  # Mínimo 2 semanas
            return {
                "tiene_estacionalidad": False,
                "error": "Datos insuficientes para análisis de estacionalidad",
            }

        # Agrupar por día de semana
        ventas_por_dia_semana = {i: [] for i in range(7)}

        for fecha, cantidad in zip(datos["fechas"], datos["cantidades"]):
            dia_semana = fecha.weekday()
            ventas_por_dia_semana[dia_semana].append(float(cantidad))

        # Calcular promedios
        dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        patron_semanal = {}

        for dia, ventas in ventas_por_dia_semana.items():
            if ventas:
                patron_semanal[dias_nombres[dia]] = round(np.mean(ventas), 2)
            else:
                patron_semanal[dias_nombres[dia]] = 0

        # Detectar picos y valles
        valores = list(patron_semanal.values())
        if valores:
            promedio_general = np.mean([v for v in valores if v > 0])

            dias_pico = [dia for dia, valor in patron_semanal.items() if valor > promedio_general * 1.2]
            dias_valle = [dia for dia, valor in patron_semanal.items() if valor < promedio_general * 0.8 and valor > 0]

            # Determinar si hay estacionalidad significativa
            varianza = np.std(valores)
            tiene_estacionalidad = (varianza / promedio_general) > 0.2 if promedio_general > 0 else False
        else:  # pragma: no cover
            dias_pico = []
            dias_valle = []
            tiene_estacionalidad = False

        return {
            "tiene_estacionalidad": tiene_estacionalidad,
            "patron_semanal": patron_semanal,
            "dias_pico": dias_pico,
            "dias_valle": dias_valle,
            "recomendacion": (
                "Ajustar pedidos según patrones detectados" if tiene_estacionalidad else "Demanda estable"
            ),
        }

    @staticmethod
    def obtener_recomendacion_compra(id_producto: int, stock_actual: Decimal, dias_cobertura_deseada: int = 14) -> Dict:
        """
        Recomienda cantidad a comprar basado en predicciones.

        Args:
            id_producto: ID del producto
            stock_actual: Stock actual disponible
            dias_cobertura_deseada: Días de cobertura deseados (default 14)

        Returns:
            {
                'cantidad_comprar': Decimal,
                'urgencia': str,  # 'critica', 'alta', 'media', 'baja', 'no_necesaria'
                'dias_cobertura_actual': int,
                'prediccion_agotamiento': date,
                'justificacion': str
            }
        """
        # Obtener estadísticas
        stats = StockForecastingService.calcular_estadisticas_basicas(id_producto, 30)

        if "error" in stats:
            return {
                "error": "No hay datos suficientes para recomendar compra",
                "cantidad_comprar": Decimal("0"),
                "urgencia": "revisar_manualmente",
            }

        demanda_diaria = stats["demanda_promedio_diaria"]

        # Calcular días de cobertura actual
        if demanda_diaria > 0:
            dias_cobertura_actual = int(stock_actual / demanda_diaria)
        else:
            dias_cobertura_actual = 999  # Stock suficiente

        # Calcular punto de reorden
        punto_reorden_data = StockForecastingService.calcular_punto_reorden(id_producto)
        punto_reorden = punto_reorden_data["punto_reorden"]

        # Demanda para periodo deseado
        demanda_periodo = demanda_diaria * dias_cobertura_deseada

        # Cantidad a comprar
        if stock_actual < punto_reorden:
            # Comprar para cubrir periodo + reposición
            cantidad_comprar = demanda_periodo + punto_reorden - stock_actual
        else:
            # No es urgente, pero proyectar necesidad
            cantidad_comprar = max(Decimal("0"), demanda_periodo - stock_actual)

        # Determinar urgencia
        if dias_cobertura_actual <= 2:
            urgencia = "critica"
            justificacion = f"Stock crítico: solo {dias_cobertura_actual} días de cobertura"
        elif dias_cobertura_actual <= 5:
            urgencia = "alta"
            justificacion = f"Stock bajo: {dias_cobertura_actual} días de cobertura"
        elif dias_cobertura_actual <= 10:
            urgencia = "media"
            justificacion = f"Stock moderado: {dias_cobertura_actual} días de cobertura"
        elif stock_actual < punto_reorden:
            urgencia = "baja"
            justificacion = f"Por debajo del punto de reorden ({punto_reorden})"
        else:
            urgencia = "no_necesaria"
            justificacion = f"Stock suficiente: {dias_cobertura_actual} días de cobertura"
            cantidad_comprar = Decimal("0")

        # Predicción de agotamiento
        if demanda_diaria > 0:
            prediccion_agotamiento = timezone.now().date() + timedelta(days=dias_cobertura_actual)
        else:
            prediccion_agotamiento = None

        return {
            "cantidad_comprar": cantidad_comprar,
            "urgencia": urgencia,
            "dias_cobertura_actual": dias_cobertura_actual,
            "dias_cobertura_deseada": dias_cobertura_deseada,
            "prediccion_agotamiento": prediccion_agotamiento,
            "demanda_diaria_estimada": demanda_diaria,
            "punto_reorden": punto_reorden,
            "justificacion": justificacion,
        }
