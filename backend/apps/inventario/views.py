from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from apps.common.permissions import CanManageInventario, IsAdminOrReadOnly
from apps.common.throttling import BurstRateThrottle, SustainedRateThrottle
from .models import StockUnico, MovimientosStock, AjustesInventario
from .serializers import (
    StockUnicoSerializer,
    MovimientosStockSerializer,
    AjustesInventarioSerializer,
)
from .ml_forecasting import StockForecastingService
from decimal import Decimal


class StockUnicoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar stock de productos.

    Permisos:
    - Admin y Encargados de Inventario: CRUD completo
    - Otros: Solo lectura
    """

    queryset = StockUnico.objects.all().order_by("id_stock")
    serializer_class = StockUnicoSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    throttle_classes = [BurstRateThrottle]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["id_producto"]
    search_fields = ["id_producto__descripcion"]


class MovimientosStockViewSet(viewsets.ModelViewSet):
    """
    ViewSet para movimientos de inventario.

    Permisos:
    - Solo personal autorizado puede gestionar movimientos
    """

    queryset = MovimientosStock.objects.all()
    serializer_class = MovimientosStockSerializer
    permission_classes = [IsAuthenticated, CanManageInventario]
    throttle_classes = [SustainedRateThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["tipo_movimiento", "id_producto"]
    ordering_fields = ["fecha_hora"]
    ordering = ["-fecha_hora"]


class AjustesInventarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para ajustes de inventario.

    Permisos:
    - Solo gerentes y encargados de inventario
    """

    queryset = AjustesInventario.objects.all()
    serializer_class = AjustesInventarioSerializer
    permission_classes = [IsAuthenticated, CanManageInventario]
    throttle_classes = [BurstRateThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["tipo_ajuste", "estado"]
    ordering = ["-fecha_hora"]

    @action(detail=False, methods=["get"])
    def reporte_mermas_mensual(self, request):
        """
        Reporte de mermas mensuales con análisis detallado.

        GET /api/v1/inventario/ajustes/reporte_mermas_mensual/?mes=2026-03

        Returns:
            {
                "periodo": "2026-03",
                "resumen": {
                    "total_merma_unidades": 150.5,
                    "total_merma_valor": 450000,
                    "total_ajustes": 12,
                    "porcentaje_sobre_compras": 2.3
                },
                "por_producto": [...],
                "por_motivo": {...},
                "tendencia": "aumentando"
            }
        """
        from django.db.models import Sum, Count, Avg
        from decimal import Decimal
        from apps.inventario.models import DetallesAjuste
        from apps.productos.models import Productos, PreciosPorLista

        mes = request.query_params.get("mes")  # Formato: YYYY-MM
        tipo_merma = request.query_params.get("tipo", "Merma")

        if not mes:
            return Response(
                {"error": "Se requiere parámetro mes (formato: YYYY-MM)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Parse periodo
        year, month = mes.split("-")

        # Obtener ajustes de merma del mes
        ajustes_merma = AjustesInventario.objects.filter(
            tipo_ajuste=tipo_merma,
            estado="Aprobado",
            fecha_hora__year=year,
            fecha_hora__month=month,
        )

        # Resumen general
        total_ajustes = ajustes_merma.count()

        # Analizar detalles
        detalles = DetallesAjuste.objects.filter(id_ajuste__in=ajustes_merma)

        total_unidades = detalles.aggregate(total=Sum("cantidad_ajustada"))["total"] or Decimal("0")

        # Calcular valor estimado (usando precio promedio)
        valor_estimado = Decimal("0")
        por_producto = []

        productos_merma = (
            detalles.values("id_producto")
            .annotate(
                cantidad_total=Sum("cantidad_ajustada"),
                num_ajustes=Count("id_ajuste", distinct=True),
            )
            .order_by("-cantidad_total")
        )

        for item in productos_merma:
            producto = Productos.objects.get(id_producto=item["id_producto"])

            # Obtener precio promedio (de lista minorista si existe)
            try:
                precio = PreciosPorLista.objects.filter(id_producto=producto).first()
                precio_unitario = precio.precio_unitario if precio else Decimal("0")
            except:  # pragma: no cover
                precio_unitario = Decimal("0")

            valor = item["cantidad_total"] * precio_unitario
            valor_estimado += valor

            por_producto.append(
                {
                    "id_producto": producto.id_producto,
                    "descripcion": producto.descripcion,
                    "cantidad_merma": str(item["cantidad_total"]),
                    "num_ajustes": item["num_ajustes"],
                    "valor_estimado": str(valor),
                    "precio_unitario": str(precio_unitario),
                }
            )

        # Análisis por motivo
        por_motivo = {}
        for ajuste in ajustes_merma:
            motivo = ajuste.motivo or "Sin especificar"
            if motivo not in por_motivo:
                por_motivo[motivo] = {"count": 0, "ejemplos": []}

            por_motivo[motivo]["count"] += 1
            if len(por_motivo[motivo]["ejemplos"]) < 3:
                por_motivo[motivo]["ejemplos"].append(
                    {"id_ajuste": ajuste.id_ajuste, "fecha": ajuste.fecha_hora.strftime("%Y-%m-%d")}
                )

        # Tendencia (comparar con mes anterior)
        mes_anterior = int(month) - 1
        year_anterior = int(year)
        if mes_anterior == 0:
            mes_anterior = 12
            year_anterior -= 1

        ajustes_mes_anterior = AjustesInventario.objects.filter(
            tipo_ajuste=tipo_merma,
            estado="Aprobado",
            fecha_hora__year=year_anterior,
            fecha_hora__month=mes_anterior,
        ).count()

        if ajustes_mes_anterior == 0:
            tendencia = "sin_datos"
        elif total_ajustes > ajustes_mes_anterior:
            tendencia = "aumentando"
        elif total_ajustes < ajustes_mes_anterior:
            tendencia = "disminuyendo"
        else:
            tendencia = "estable"

        return Response(
            {
                "periodo": mes,
                "resumen": {
                    "total_merma_unidades": str(total_unidades),
                    "total_merma_valor": str(valor_estimado),
                    "total_ajustes": total_ajustes,
                    "comparacion_mes_anterior": {
                        "mes_anterior": f"{year_anterior}-{mes_anterior:02d}",
                        "ajustes_mes_anterior": ajustes_mes_anterior,
                        "tendencia": tendencia,
                    },
                },
                "por_producto": por_producto[:10],  # Top 10
                "por_motivo": por_motivo,
                "tendencia": tendencia,
            }
        )

    @action(detail=False, methods=["get"])
    def productos_mayor_desperdicio(self, request):
        """
        Productos con mayor índice de desperdicio/merma.

        GET /api/v1/inventario/ajustes/productos_mayor_desperdicio/?limite=20&periodo_dias=90

        Returns:
            {
                "ranking": [
                    {
                        "posicion": 1,
                        "producto": "Yogurt Natural",
                        "total_merma": 45.5,
                        "num_incidencias": 8,
                        "valor_estimado": 68000,
                        "porcentaje_sobre_compras": 5.2
                    }
                ]
            }
        """
        from django.db.models import Sum, Count
        from django.utils import timezone
        from datetime import timedelta
        from apps.inventario.models import DetallesAjuste
        from apps.productos.models import Productos, PreciosPorLista

        limite = int(request.query_params.get("limite", 20))
        periodo_dias = int(request.query_params.get("periodo_dias", 90))

        # Fecha límite
        fecha_desde = timezone.now() - timedelta(days=periodo_dias)

        # Ajustes de merma aprobados
        ajustes_merma = AjustesInventario.objects.filter(
            tipo_ajuste="Merma", estado="Aprobado", fecha_hora__gte=fecha_desde
        )

        # Agrupar por producto
        detalles = (
            DetallesAjuste.objects.filter(id_ajuste__in=ajustes_merma)
            .values("id_producto")
            .annotate(
                total_merma=Sum("cantidad_ajustada"),
                num_incidencias=Count("id_ajuste", distinct=True),
            )
            .order_by("-total_merma")[:limite]
        )

        ranking = []
        for idx, item in enumerate(detalles, start=1):
            producto = Productos.objects.get(id_producto=item["id_producto"])

            # Precio estimado
            try:
                precio = PreciosPorLista.objects.filter(id_producto=producto).first()
                precio_unitario = precio.precio_unitario if precio else Decimal("0")
            except:  # pragma: no cover
                precio_unitario = Decimal("0")

            valor_total = item["total_merma"] * precio_unitario

            ranking.append(
                {
                    "posicion": idx,
                    "id_producto": producto.id_producto,
                    "producto": producto.descripcion,
                    "total_merma": str(item["total_merma"]),
                    "num_incidencias": item["num_incidencias"],
                    "valor_estimado": str(valor_total),
                    "promedio_por_incidencia": str(item["total_merma"] / item["num_incidencias"]),
                }
            )

        return Response({"periodo_dias": periodo_dias, "ranking": ranking})

    @action(detail=False, methods=["get"])
    def analisis_causas_merma(self, request):
        """
        Análisis de causas de merma para prevención.

        GET /api/v1/inventario/ajustes/analisis_causas_merma/?periodo_dias=90

        Returns:
            {
                "causas_principales": [
                    {
                        "motivo": "Producto vencido",
                        "frecuencia": 12,
                        "porcentaje": 35.3,
                        "productos_afectados": 8,
                        "recomendacion": "Mejorar rotación de inventario"
                    }
                ],
                "patrones_temporales": {...}
            }
        """
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count
        import re

        periodo_dias = int(request.query_params.get("periodo_dias", 90))
        fecha_desde = timezone.now() - timedelta(days=periodo_dias)

        # Ajustes de merma
        ajustes = AjustesInventario.objects.filter(tipo_ajuste="Merma", estado="Aprobado", fecha_hora__gte=fecha_desde)

        total_mermas = ajustes.count()

        # Clasificar motivos
        motivos_clasificados = {}
        for ajuste in ajustes:
            motivo_raw = ajuste.motivo or "Sin especificar"

            # Clasificar motivo
            if "vencid" in motivo_raw.lower():
                categoria = "Producto vencido"
            elif "dañ" in motivo_raw.lower() or "rotur" in motivo_raw.lower():
                categoria = "Daño físico"
            elif "robo" in motivo_raw.lower() or "hurto" in motivo_raw.lower():
                categoria = "Robo/Hurto"
            elif "conteo" in motivo_raw.lower() or "inventario" in motivo_raw.lower():
                categoria = "Diferencia de inventario"
            else:
                categoria = "Otros"

            if categoria not in motivos_clasificados:
                motivos_clasificados[categoria] = {"frecuencia": 0, "ajustes": []}

            motivos_clasificados[categoria]["frecuencia"] += 1
            motivos_clasificados[categoria]["ajustes"].append(ajuste.id_ajuste)

        # Generar recomendaciones
        recomendaciones = {
            "Producto vencido": "Mejorar sistema FIFO y alertas de vencimiento",
            "Daño físico": "Revisar procesos de manipulación y almacenamiento",
            "Robo/Hurto": "Reforzar seguridad y control de accesos",
            "Diferencia de inventario": "Implementar conteos cíclicos más frecuentes",
            "Otros": "Documentar mejor las causas específicas",
        }

        # Ordenar por frecuencia
        causas = []
        for motivo, datos in sorted(motivos_clasificados.items(), key=lambda x: x[1]["frecuencia"], reverse=True):
            porcentaje = (datos["frecuencia"] / total_mermas * 100) if total_mermas > 0 else 0

            causas.append(
                {
                    "motivo": motivo,
                    "frecuencia": datos["frecuencia"],
                    "porcentaje": round(porcentaje, 1),
                    "recomendacion": recomendaciones.get(motivo, "Analizar caso por caso"),
                }
            )

        return Response(
            {
                "periodo_dias": periodo_dias,
                "total_mermas": total_mermas,
                "causas_principales": causas,
            }
        )

    @action(detail=False, methods=["get"], url_path="prediccion-demanda")
    def prediccion_demanda(self, request):
        """
        Predice la demanda futura de un producto usando ML.

        GET /api/v1/inventario/ajustes/prediccion-demanda/
        ?id_producto=1&dias=7

        Retorna:
        {
            "producto": {...},
            "estadisticas": {...},
            "predicciones": [
                {
                    "fecha": "2026-03-02",
                    "demanda_predicha": 12.5,
                    "intervalo_confianza": [8.3, 16.7],
                    "dia_semana": "Lunes",
                    "confianza": 0.85
                }
            ],
            "patron_estacional": {...}
        }
        """
        from apps.productos.models import Productos

        id_producto = request.query_params.get("id_producto")
        dias_adelante = int(request.query_params.get("dias", 7))

        if not id_producto:
            return Response({"error": "Parámetro id_producto es requerido"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            producto = Productos.objects.get(id_producto=id_producto)
        except Productos.DoesNotExist:
            return Response({"error": "Producto no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        # Obtener estadísticas básicas
        estadisticas = StockForecastingService.calcular_estadisticas_basicas(int(id_producto), dias=30)

        # Generar predicciones
        predicciones = StockForecastingService.predecir_demanda_simple(int(id_producto), dias_adelante=dias_adelante)

        # Analizar estacionalidad
        patron_estacional = StockForecastingService.analizar_estacionalidad(int(id_producto), dias=90)

        return Response(
            {
                "producto": {
                    "id": producto.id_producto,
                    "codigo": producto.codigo_producto,
                    "descripcion": producto.descripcion,
                },
                "estadisticas": estadisticas,
                "predicciones": predicciones,
                "patron_estacional": patron_estacional,
                "metodo_ml": "promedio_movil_ajustado",
                "dias_historico_usado": 30,
            }
        )

    @action(detail=False, methods=["get"], url_path="punto-reorden")
    def punto_reorden(self, request):
        """
        Calcula el punto de reorden óptimo para un producto.

        GET /api/v1/inventario/ajustes/punto-reorden/
        ?id_producto=1&lead_time=7

        Retorna:
        {
            "producto": {...},
            "punto_reorden": 45.5,
            "stock_seguridad": 15.0,
            "demanda_durante_lead_time": 30.5,
            "stock_actual": 50.0,
            "estado": "saludable",
            "recomendacion": "..."
        }
        """
        from apps.productos.models import Productos

        id_producto = request.query_params.get("id_producto")
        lead_time = int(request.query_params.get("lead_time", 7))

        if not id_producto:
            return Response({"error": "Parámetro id_producto es requerido"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            producto = Productos.objects.get(id_producto=id_producto)
            stock_actual = StockUnico.objects.get(id_producto=producto).cantidad
        except Productos.DoesNotExist:
            return Response({"error": "Producto no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        except StockUnico.DoesNotExist:
            stock_actual = Decimal("0")

        # Calcular punto de reorden
        resultado = StockForecastingService.calcular_punto_reorden(int(id_producto), lead_time_dias=lead_time)

        # Determinar estado del stock
        if "error" not in resultado:
            punto_reorden = resultado["punto_reorden"]

            if stock_actual <= punto_reorden * Decimal("0.5"):
                estado = "critico"
                nivel_urgencia = "alto"
            elif stock_actual <= punto_reorden:
                estado = "bajo"
                nivel_urgencia = "medio"
            elif stock_actual <= punto_reorden * Decimal("1.5"):
                estado = "saludable"
                nivel_urgencia = "bajo"
            else:
                estado = "exceso"
                nivel_urgencia = "ninguno"
        else:
            estado = "sin_datos"
            nivel_urgencia = "revisar"

        return Response(
            {
                "producto": {
                    "id": producto.id_producto,
                    "codigo": producto.codigo_producto,
                    "descripcion": producto.descripcion,
                    "stock_minimo_configurado": producto.stock_minimo,
                },
                "stock_actual": stock_actual,
                "punto_reorden_calculado": resultado.get("punto_reorden", Decimal("0")),
                "stock_seguridad": resultado.get("stock_seguridad", Decimal("0")),
                "demanda_durante_lead_time": resultado.get("demanda_durante_lead_time", Decimal("0")),
                "lead_time_dias": lead_time,
                "estado": estado,
                "nivel_urgencia": nivel_urgencia,
                "recomendacion": resultado.get("recomendacion", "Sin datos suficientes"),
                "confianza": resultado.get("confianza", 0),
            }
        )

    @action(detail=False, methods=["get"], url_path="detectar-anomalias")
    def detectar_anomalias(self, request):
        """
        Detecta patrones anómalos en las ventas de un producto.

        GET /api/v1/inventario/ajustes/detectar-anomalias/
        ?id_producto=1&dias=30

        Retorna:
        {
            "producto": {...},
            "periodo_analizado": {...},
            "anomalias_detectadas": [
                {
                    "fecha": "2026-02-15",
                    "cantidad": 85,
                    "tipo": "pico",
                    "desviacion": 2.5,
                    "explicacion": "...",
                    "posible_causa": "..."
                }
            ],
            "total_anomalias": 3,
            "clasificacion": {...}
        }
        """
        from apps.productos.models import Productos

        id_producto = request.query_params.get("id_producto")
        dias = int(request.query_params.get("dias", 30))

        if not id_producto:
            return Response({"error": "Parámetro id_producto es requerido"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            producto = Productos.objects.get(id_producto=id_producto)
        except Productos.DoesNotExist:
            return Response({"error": "Producto no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        # Detectar anomalías
        anomalias = StockForecastingService.detectar_anomalias(int(id_producto), dias=dias)

        # Clasificar anomalías
        picos = [a for a in anomalias if a["tipo"] == "pico"]
        caidas = [a for a in anomalias if a["tipo"] == "caida"]

        return Response(
            {
                "producto": {
                    "id": producto.id_producto,
                    "codigo": producto.codigo_producto,
                    "descripcion": producto.descripcion,
                },
                "periodo_analizado": {
                    "dias": dias,
                    "desde": None if not anomalias else min(a["fecha"] for a in anomalias),
                    "hasta": None if not anomalias else max(a["fecha"] for a in anomalias),
                },
                "anomalias_detectadas": anomalias,
                "total_anomalias": len(anomalias),
                "clasificacion": {"picos": len(picos), "caidas": len(caidas)},
                "metodo": "desviacion_estandar",
                "umbral": "2_sigma",
            }
        )

    @action(detail=False, methods=["get"], url_path="recomendacion-compra")
    def recomendacion_compra(self, request):
        """
        Recomienda cantidad óptima a comprar basado en predicciones ML.

        GET /api/v1/inventario/ajustes/recomendacion-compra/
        ?id_producto=1&dias_cobertura=14

        Retorna:
        {
            "producto": {...},
            "stock_actual": 25.0,
            "cantidad_comprar": 150.0,
            "urgencia": "alta",
            "dias_cobertura_actual": 5,
            "dias_cobertura_deseada": 14,
            "prediccion_agotamiento": "2026-03-06",
            "justificacion": "...",
            "punto_reorden": 45.5
        }
        """
        from apps.productos.models import Productos

        id_producto = request.query_params.get("id_producto")
        dias_cobertura = int(request.query_params.get("dias_cobertura", 14))

        if not id_producto:
            return Response({"error": "Parámetro id_producto es requerido"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            producto = Productos.objects.get(id_producto=id_producto)
            stock_actual = StockUnico.objects.get(id_producto=producto).cantidad
        except Productos.DoesNotExist:
            return Response({"error": "Producto no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        except StockUnico.DoesNotExist:
            stock_actual = Decimal("0")

        # Obtener recomendación
        recomendacion = StockForecastingService.obtener_recomendacion_compra(
            int(id_producto), stock_actual=stock_actual, dias_cobertura_deseada=dias_cobertura
        )

        # Agregar colores para UI
        colores_urgencia = {
            "critica": "#dc3545",  # Rojo
            "alta": "#fd7e14",  # Naranja
            "media": "#ffc107",  # Amarillo
            "baja": "#17a2b8",  # Azul
            "no_necesaria": "#28a745",  # Verde
        }

        return Response(
            {
                "producto": {
                    "id": producto.id_producto,
                    "codigo": producto.codigo_producto,
                    "descripcion": producto.descripcion,
                },
                "stock_actual": stock_actual,
                "cantidad_comprar": recomendacion.get("cantidad_comprar", Decimal("0")),
                "urgencia": recomendacion.get("urgencia", "revisar_manualmente"),
                "color_urgencia": colores_urgencia.get(recomendacion.get("urgencia"), "#6c757d"),
                "dias_cobertura_actual": recomendacion.get("dias_cobertura_actual", 0),
                "dias_cobertura_deseada": dias_cobertura,
                "prediccion_agotamiento": recomendacion.get("prediccion_agotamiento"),
                "demanda_diaria_estimada": recomendacion.get("demanda_diaria_estimada", Decimal("0")),
                "punto_reorden": recomendacion.get("punto_reorden", Decimal("0")),
                "justificacion": recomendacion.get("justificacion", "Sin datos suficientes"),
            }
        )

    @action(detail=False, methods=["get"], url_path="analisis-completo")
    def analisis_completo(self, request):
        """
        Análisis completo de un producto combinando todas las funciones ML.

        GET /api/v1/inventario/ajustes/analisis-completo/
        ?id_producto=1

        Retorna consolidación de:
        - Estadísticas históricas
        - Predicción de demanda (7 días)
        - Punto de reorden
        - Anomalías detectadas
        - Recomendación de compra
        - Patrón estacional
        """
        from apps.productos.models import Productos

        id_producto = request.query_params.get("id_producto")

        if not id_producto:
            return Response({"error": "Parámetro id_producto es requerido"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            producto = Productos.objects.get(id_producto=id_producto)
            stock_actual = StockUnico.objects.get(id_producto=producto).cantidad
        except Productos.DoesNotExist:
            return Response({"error": "Producto no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        except StockUnico.DoesNotExist:
            stock_actual = Decimal("0")

        # Ejecutar todos los análisis
        estadisticas = StockForecastingService.calcular_estadisticas_basicas(int(id_producto), dias=30)

        predicciones = StockForecastingService.predecir_demanda_simple(int(id_producto), dias_adelante=7)

        punto_reorden_data = StockForecastingService.calcular_punto_reorden(int(id_producto), lead_time_dias=7)

        anomalias = StockForecastingService.detectar_anomalias(int(id_producto), dias=30)

        recomendacion = StockForecastingService.obtener_recomendacion_compra(
            int(id_producto), stock_actual=stock_actual, dias_cobertura_deseada=14
        )

        patron_estacional = StockForecastingService.analizar_estacionalidad(int(id_producto), dias=90)

        # Calcular demanda total predicha (7 días)
        demanda_total_7dias = sum(p["demanda_predicha"] for p in predicciones) if predicciones else Decimal("0")

        return Response(
            {
                "producto": {
                    "id": producto.id_producto,
                    "codigo": producto.codigo_producto,
                    "descripcion": producto.descripcion,
                    "stock_actual": stock_actual,
                    "stock_minimo": producto.stock_minimo,
                },
                "resumen": {
                    "demanda_diaria_promedio": estadisticas.get("demanda_promedio_diaria", Decimal("0")),
                    "demanda_predicha_7dias": demanda_total_7dias,
                    "tendencia": estadisticas.get("tendencia", "sin_datos"),
                    "tiene_estacionalidad": patron_estacional.get("tiene_estacionalidad", False),
                    "anomalias_detectadas": len(anomalias),
                    "urgencia_compra": recomendacion.get("urgencia", "revisar"),
                },
                "estadisticas_historicas": estadisticas,
                "predicciones_7dias": predicciones,
                "punto_reorden": punto_reorden_data,
                "anomalias": {
                    "total": len(anomalias),
                    "ultimas_5": anomalias[:5] if anomalias else [],
                },
                "recomendacion_compra": recomendacion,
                "patron_estacional": patron_estacional,
                "generado_en": timezone.now(),
            }
        )
