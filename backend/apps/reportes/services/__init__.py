"""
Service Layer para Sistema de Reportes

Este módulo contiene la lógica de negocio para:
- Generación de reportes de ventas
- Generación de reportes de recargas
- Generación de reportes de consumos
- Reportes de inventario
- Reportes financieros
- Exportación a PDF/Excel

Autor: Cantina Tita Development Team
Fecha: Marzo 2026
"""

import logging
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Optional

from django.core.exceptions import ValidationError
from django.db.models import Avg, Count, F, Sum
from django.utils.timezone import make_aware

from apps.core.models import CargasSaldo, ConsumosTarjeta, Tarjetas
from apps.ventas.models import DetallesVenta, Ventas

logger = logging.getLogger(__name__)


class ReporteService:
    """
    Service Layer para generación de reportes.

    Métodos principales:
    - generar_reporte_ventas()
    - generar_reporte_recargas()
    - generar_reporte_top_productos()
    - generar_reporte_consumos_tarjeta()
    - generar_reporte_financiero()
    - exportar_excel()
    - exportar_pdf()
    """

    @staticmethod
    def generar_reporte_ventas(
        fecha_inicio: date,
        fecha_fin: date,
        metodo_pago: Optional[str] = None,
        id_empleado: Optional[int] = None,
    ) -> Dict:
        """
        Genera reporte de ventas en un rango de fechas.

        Args:
            fecha_inicio: Fecha inicio del reporte
            fecha_fin: Fecha fin del reporte
            metodo_pago: Filtrar por método de pago (opcional)
            id_empleado: Filtrar por empleado (opcional)

        Returns:
            {
                'fecha_inicio': date,
                'fecha_fin': date,
                'total_ventas': int,
                'total_monto': Decimal,
                'promedio_ticket': Decimal,
                'ventas_efectivo': Decimal,
                'ventas_tarjeta': Decimal,
                'ventas_online': Decimal,
                'top_productos': List[Dict],
                'ventas_por_dia': List[Dict],
                'detalles': List[Dict]
            }
        """
        try:
            # Base query
            ventas_query = Ventas.objects.filter(fecha__date__gte=fecha_inicio, fecha__date__lte=fecha_fin)

            # Filtros opcionales
            if metodo_pago:
                ventas_query = ventas_query.filter(id_medio_pago__descripcion__iexact=metodo_pago)

            if id_empleado:
                ventas_query = ventas_query.filter(id_empleado_cajero=id_empleado)

            # Estadísticas generales
            stats = ventas_query.aggregate(
                total_ventas=Count("id_venta"),
                total_monto=Sum("monto_total"),
                promedio_ticket=Avg("monto_total"),
            )

            # Ventas por método de pago
            ventas_efectivo = ventas_query.filter(id_medio_pago__descripcion__icontains="efectivo").aggregate(
                total=Sum("monto_total")
            )["total"] or Decimal("0.00")

            ventas_tarjeta = ventas_query.filter(id_medio_pago__descripcion__icontains="tarjeta").aggregate(
                total=Sum("monto_total")
            )["total"] or Decimal("0.00")

            ventas_online = ventas_query.filter(id_medio_pago__descripcion__icontains="online").aggregate(
                total=Sum("monto_total")
            )["total"] or Decimal("0.00")

            # Top 10 productos más vendidos
            top_productos_qs = (
                DetallesVenta.objects.filter(id_venta__in=ventas_query)
                .values("id_producto__descripcion", "id_producto__codigo_barra")
                .annotate(
                    cantidad_vendida=Sum("cantidad"),
                    total_vendido=Sum(F("cantidad") * F("precio_unitario")),
                )
                .order_by("-cantidad_vendida")[:10]
            )
            # Añadir alias id_producto__nombre para compatibilidad con tests
            top_productos = [
                {**item, "id_producto__nombre": item.get("id_producto__descripcion")} for item in top_productos_qs
            ]

            # Ventas por día
            ventas_por_dia = (
                ventas_query.extra(select={"fecha_dia": "CAST(fecha AS DATE)"})
                .values("fecha_dia")
                .annotate(cantidad=Count("id_venta"), monto_total=Sum("monto_total"))
                .order_by("fecha_dia")
            )

            # Detalles de ventas
            ventas_detalle = ventas_query.select_related("id_empleado_cajero").values(
                "id_venta",
                "fecha",
                "monto_total",
                "id_empleado_cajero__nombre",
                "id_empleado_cajero__apellido",
            )

            return {
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "total_ventas": stats["total_ventas"] or 0,
                "total_monto": stats["total_monto"] or Decimal("0.00"),
                "promedio_ticket": stats["promedio_ticket"] or Decimal("0.00"),
                "ventas_efectivo": ventas_efectivo,
                "ventas_tarjeta": ventas_tarjeta,
                "ventas_online": ventas_online,
                "top_productos": list(top_productos),
                "ventas_por_dia": list(ventas_por_dia),
                "detalles": list(ventas_detalle),
            }

        except Exception as e:
            logger.error(f"Error generando reporte de ventas: {str(e)}")
            raise ValidationError(f"Error: {str(e)}")

    @staticmethod
    def generar_reporte_recargas(
        fecha_inicio: date,
        fecha_fin: date,
        metodo_pago: Optional[str] = None,
        estado: Optional[str] = None,
    ) -> Dict:
        """
        Genera reporte de recargas en un rango de fechas.

        Args:
            fecha_inicio: Fecha inicio
            fecha_fin: Fecha fin
            metodo_pago: Filtrar por método (opcional)
            estado: Filtrar por estado (opcional)

        Returns:
            {
                'total_recargas': int,
                'total_acreditado': Decimal,
                'total_comisiones': Decimal,
                'total_cobrado': Decimal,
                'recargas_por_metodo': Dict,
                'recargas_por_estado': Dict,
                'estadisticas_diarias': List[Dict]
            }
        """
        try:
            # Base query
            recargas_query = CargasSaldo.objects.filter(
                fecha_carga__date__gte=fecha_inicio, fecha_carga__date__lte=fecha_fin
            )

            # Filtros
            if metodo_pago:
                recargas_query = recargas_query.filter(metodo_pago=metodo_pago)

            if estado:
                recargas_query = recargas_query.filter(estado=estado)

            # Estadísticas generales
            stats = recargas_query.aggregate(
                total_recargas=Count("id_carga"),
                total_acreditado=Sum("monto_cargado"),
                total_cobrado=Sum("monto_cargado"),
            )
            stats["total_comisiones"] = Decimal("0.00")

            # Recargas por estado
            recargas_por_metodo = recargas_query.values("estado").annotate(
                cantidad=Count("id_carga"), monto_total=Sum("monto_cargado")
            )

            # Recargas por estado (desglose)
            recargas_por_estado = recargas_query.values("estado").annotate(
                cantidad=Count("id_carga"), monto_total=Sum("monto_cargado")
            )

            # Estadísticas diarias
            estadisticas_diarias = (
                recargas_query.extra(select={"fecha_dia": "CAST(fecha_carga AS DATE)"})
                .values("fecha_dia")
                .annotate(cantidad_recargas=Count("id_carga"), monto_acreditado=Sum("monto_cargado"))
                .order_by("fecha_dia")
            )

            return {
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "total_recargas": stats["total_recargas"] or 0,
                "total_acreditado": stats["total_acreditado"] or Decimal("0.00"),
                "total_comisiones": stats["total_comisiones"] or Decimal("0.00"),
                "total_cobrado": stats["total_cobrado"] or Decimal("0.00"),
                "recargas_por_metodo": list(recargas_por_metodo),
                "recargas_por_estado": list(recargas_por_estado),
                "estadisticas_diarias": list(estadisticas_diarias),
            }

        except Exception as e:
            logger.error(f"Error generando reporte de recargas: {str(e)}")
            raise ValidationError(f"Error: {str(e)}")

    @staticmethod
    def generar_reporte_top_productos(fecha_inicio: date, fecha_fin: date, limite: int = 20) -> Dict:
        """
        Genera reporte de productos más vendidos.

        Args:
            fecha_inicio: Fecha inicio
            fecha_fin: Fecha fin
            limite: Cantidad de productos a retornar

        Returns:
            {
                'top_productos': List[Dict],
                'total_productos_vendidos': int,
                'monto_total_ventas': Decimal
            }
        """
        try:
            # Query de productos vendidos
            top_productos = (
                DetallesVenta.objects.filter(
                    id_venta__fecha__date__gte=fecha_inicio, id_venta__fecha__date__lte=fecha_fin
                )
                .values(
                    "id_producto__id_producto",
                    "id_producto__codigo_barra",
                    "id_producto__descripcion",
                    "id_producto__id_categoria__nombre",
                )
                .annotate(
                    cantidad_vendida=Sum("cantidad"),
                    total_vendido=Sum(F("cantidad") * F("precio_unitario")),
                    precio_promedio=Avg("precio_unitario"),
                    ventas_count=Count("id_detalle"),
                )
                .order_by("-cantidad_vendida")[:limite]
            )

            # Totales
            totales = top_productos.aggregate(total_productos=Sum("cantidad_vendida"), monto_total=Sum("total_vendido"))

            # Añadir alias 'nombre' para compatibilidad con tests
            top_productos_list = [{**item, "nombre": item.get("id_producto__descripcion")} for item in top_productos]

            return {
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "periodo": {"inicio": fecha_inicio, "fin": fecha_fin},
                "top_productos": top_productos_list,
                "total_productos_vendidos": totales["total_productos"] or 0,
                "monto_total_ventas": totales["monto_total"] or Decimal("0.00"),
            }

        except Exception as e:
            logger.error(f"Error generando reporte top productos: {str(e)}")
            raise ValidationError(f"Error: {str(e)}")

    @staticmethod
    def generar_reporte_consumos_tarjeta(nro_tarjeta: str, fecha_inicio: date, fecha_fin: date) -> Dict:
        """
        Genera reporte de consumos de una tarjeta.

        Args:
            nro_tarjeta: Número de tarjeta
            fecha_inicio: Fecha inicio
            fecha_fin: Fecha fin

        Returns:
            {
                'nro_tarjeta': str,
                'estudiante': str,
                'total_consumos': int,
                'monto_total_consumido': Decimal,
                'saldo_inicial': Decimal,
                'saldo_final': Decimal,
                'consumos': List[Dict]
            }
        """
        try:
            try:
                tarjeta = Tarjetas.objects.select_related("id_hijo").get(nro_tarjeta=nro_tarjeta)
            except Tarjetas.DoesNotExist:
                return {
                    "nro_tarjeta": nro_tarjeta,
                    "periodo": {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
                    "total_consumos": 0,
                    "total_gastado": Decimal("0.00"),
                    "consumos": [],
                }

            # Obtener consumos
            from django.conf import settings as _s

            if getattr(_s, "USE_TZ", True):
                fecha_inicio_dt = make_aware(datetime(fecha_inicio.year, fecha_inicio.month, fecha_inicio.day, 0, 0, 0))
                fecha_fin_dt = make_aware(datetime(fecha_fin.year, fecha_fin.month, fecha_fin.day, 23, 59, 59))
            else:
                fecha_inicio_dt = datetime(fecha_inicio.year, fecha_inicio.month, fecha_inicio.day, 0, 0, 0)
                fecha_fin_dt = datetime(fecha_fin.year, fecha_fin.month, fecha_fin.day, 23, 59, 59)
            consumos = ConsumosTarjeta.objects.filter(
                nro_tarjeta=tarjeta, fecha_consumo__gte=fecha_inicio_dt, fecha_consumo__lte=fecha_fin_dt
            )

            # Estadísticas
            stats = consumos.aggregate(total_consumos=Count("id_consumo"), monto_total=Sum("monto_consumido"))

            # Saldo inicial (primer consumo del período)
            primer_consumo = consumos.order_by("fecha_consumo").first()
            saldo_inicial = primer_consumo.saldo_anterior if primer_consumo else tarjeta.saldo_actual

            # Detalles de consumos
            consumos_detalle = consumos.values(
                "id_consumo",
                "fecha_consumo",
                "monto_consumido",
                "saldo_anterior",
                "saldo_posterior",
            ).order_by("-fecha_consumo")

            total_gastado = abs(stats["monto_total"] or Decimal("0.00"))
            return {
                "nro_tarjeta": nro_tarjeta,
                "periodo": {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
                "estudiante": f"{tarjeta.id_hijo.nombre} {tarjeta.id_hijo.apellido}",
                "total_consumos": stats["total_consumos"] or 0,
                "total_gastado": total_gastado,
                "monto_total_consumido": total_gastado,
                "saldo_inicial": saldo_inicial,
                "saldo_final": tarjeta.saldo_actual,
                "consumos": list(consumos_detalle),
            }

        except Exception as e:
            logger.error(f"Error generando reporte consumos: {str(e)}")
            raise ValidationError(f"Error: {str(e)}")

    @staticmethod
    def generar_reporte_consumos_hijo(id_hijo: int, fecha_inicio: date, fecha_fin: date) -> Dict:
        """
        Genera reporte de consumos de un hijo por su id_hijo.

        Args:
            id_hijo: ID del hijo
            fecha_inicio: Fecha inicio
            fecha_fin: Fecha fin

        Returns:
            Reporte con datos del estudiante, tarjeta, lista de consumos y totales.
        """
        try:
            try:
                tarjeta = Tarjetas.objects.select_related("id_hijo").get(id_hijo=id_hijo)
            except Tarjetas.DoesNotExist:
                return {
                    "id_hijo": id_hijo,
                    "tiene_tarjeta": False,
                    "periodo": {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
                    "total_consumos": 0,
                    "total_gastado": Decimal("0.00"),
                    "consumos": [],
                }

            from django.conf import settings as _s

            if getattr(_s, "USE_TZ", True):
                fecha_inicio_dt = make_aware(datetime(fecha_inicio.year, fecha_inicio.month, fecha_inicio.day, 0, 0, 0))
                fecha_fin_dt = make_aware(datetime(fecha_fin.year, fecha_fin.month, fecha_fin.day, 23, 59, 59))
            else:
                fecha_inicio_dt = datetime(fecha_inicio.year, fecha_inicio.month, fecha_inicio.day, 0, 0, 0)
                fecha_fin_dt = datetime(fecha_fin.year, fecha_fin.month, fecha_fin.day, 23, 59, 59)
            consumos = ConsumosTarjeta.objects.filter(
                nro_tarjeta=tarjeta,
                fecha_consumo__gte=fecha_inicio_dt,
                fecha_consumo__lte=fecha_fin_dt,
            )

            stats = consumos.aggregate(total_consumos=Count("id_consumo"), monto_total=Sum("monto_consumido"))

            primer_consumo = consumos.order_by("fecha_consumo").first()
            saldo_inicial = primer_consumo.saldo_anterior if primer_consumo else tarjeta.saldo_actual

            consumos_detalle = list(
                consumos.values(
                    "id_consumo",
                    "fecha_consumo",
                    "monto_consumido",
                    "detalle",
                    "saldo_anterior",
                    "saldo_posterior",
                ).order_by("-fecha_consumo")
            )

            # Adjuntar productos de cada venta --------------------------------
            venta_ids = []
            for c in consumos_detalle:
                match = re.search(r"Venta #(\d+)", c.get("detalle") or "")
                if match:
                    venta_ids.append(int(match.group(1)))

            detalles_por_venta: Dict[int, list] = {}
            if venta_ids:
                from apps.ventas.models import DetallesVenta

                filas = (
                    DetallesVenta.objects.filter(id_venta__in=venta_ids)
                    .select_related("id_producto")
                    .values(
                        "id_venta_id",
                        "id_producto__descripcion",
                        "cantidad",
                        "precio_unitario",
                        "subtotal",
                    )
                )
                for fila in filas:
                    vid = fila["id_venta_id"]
                    detalles_por_venta.setdefault(vid, []).append(
                        {
                            "descripcion": fila["id_producto__descripcion"],
                            "cantidad": fila["cantidad"],
                            "precio_unitario": fila["precio_unitario"],
                            "subtotal": fila["subtotal"],
                        }
                    )

            for c in consumos_detalle:
                match = re.search(r"Venta #(\d+)", c.get("detalle") or "")
                vid = int(match.group(1)) if match else None
                c["productos"] = detalles_por_venta.get(vid, [])
            # -----------------------------------------------------------------

            total_gastado = abs(stats["monto_total"] or Decimal("0.00"))
            hijo = tarjeta.id_hijo

            return {
                "id_hijo": id_hijo,
                "tiene_tarjeta": True,
                "nro_tarjeta": tarjeta.nro_tarjeta,
                "estudiante": f"{hijo.nombre} {hijo.apellido}",
                "grado": hijo.grado or "",
                "saldo_actual": tarjeta.saldo_actual,
                "periodo": {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
                "total_consumos": stats["total_consumos"] or 0,
                "total_gastado": total_gastado,
                "monto_total_consumido": total_gastado,
                "saldo_inicial": saldo_inicial,
                "saldo_final": tarjeta.saldo_actual,
                "consumos": consumos_detalle,
            }

        except Exception as e:
            logger.error(f"Error generando reporte consumos por hijo: {str(e)}")
            raise ValidationError(f"Error: {str(e)}")

    @staticmethod
    def generar_reporte_financiero(fecha_inicio: date, fecha_fin: date) -> Dict:
        """
        Genera reporte financiero consolidado.

        Incluye:
        - Ingresos por ventas
        - Ingresos por recargas
        - Comisiones cobradas
        - Movimientos de inventario

        Args:
            fecha_inicio: Fecha inicio
            fecha_fin: Fecha fin

        Returns:
            {
                'ingresos_ventas': Decimal,
                'ingresos_recargas': Decimal,
                'comisiones_cobradas': Decimal,
                'ingreso_total': Decimal,
                'costo_inventario': Decimal,
                'margen_bruto': Decimal,
                'resumen_por_dia': List[Dict]
            }
        """
        try:
            # Ingresos por ventas
            ventas_stats = Ventas.objects.filter(fecha__date__gte=fecha_inicio, fecha__date__lte=fecha_fin).aggregate(
                total_ventas=Sum("monto_total")
            )

            ingresos_ventas = ventas_stats["total_ventas"] or Decimal("0.00")

            # Ingresos por recargas
            recargas_stats = CargasSaldo.objects.filter(
                fecha_carga__date__gte=fecha_inicio, fecha_carga__date__lte=fecha_fin, estado="completada"
            ).aggregate(total_recargas=Sum("monto_cargado"))

            ingresos_recargas = recargas_stats["total_recargas"] or Decimal("0.00")
            comisiones_cobradas = Decimal("0.00")

            # Ingreso total
            ingreso_total = ingresos_ventas + comisiones_cobradas

            # Costo de inventario (estimado)
            # Aquí podrías calcular el costo real basado en compras
            costo_inventario = Decimal("0.00")  # Implementar según necesidad

            # Margen bruto
            margen_bruto = ingreso_total - costo_inventario

            # Ventas por método de pago
            ventas_efectivo_stats = Ventas.objects.filter(
                fecha__date__gte=fecha_inicio,
                fecha__date__lte=fecha_fin,
                id_medio_pago__descripcion__icontains="efectivo",
            ).aggregate(total=Sum("monto_total"))
            ventas_efectivo_monto = ventas_efectivo_stats["total"] or Decimal("0.00")

            ventas_tarjeta_stats = Ventas.objects.filter(
                fecha__date__gte=fecha_inicio,
                fecha__date__lte=fecha_fin,
                id_medio_pago__descripcion__icontains="tarjeta",
            ).aggregate(total=Sum("monto_total"))
            ventas_tarjeta_monto = ventas_tarjeta_stats["total"] or Decimal("0.00")

            ingresos_dict = {
                "ventas_efectivo": ventas_efectivo_monto,
                "ventas_tarjeta": ventas_tarjeta_monto,
                "recargas": ingresos_recargas,
                "total": ingresos_ventas + ingresos_recargas,
            }

            return {
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "periodo": {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
                "ingresos": ingresos_dict,
                "egresos": {"total": costo_inventario},
                "ingresos_ventas": ingresos_ventas,
                "ingresos_recargas": ingresos_recargas,
                "comisiones_cobradas": comisiones_cobradas,
                "ingreso_total": ingreso_total,
                "utilidad_neta": margen_bruto,
                "costo_inventario": costo_inventario,
                "margen_bruto": margen_bruto,
                "porcentaje_margen": ((margen_bruto / ingreso_total * 100) if ingreso_total > 0 else Decimal("0.00")),
            }

        except Exception as e:
            logger.error(f"Error generando reporte financiero: {str(e)}")
            raise ValidationError(f"Error: {str(e)}")
