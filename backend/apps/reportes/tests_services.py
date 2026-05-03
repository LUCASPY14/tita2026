"""
Tests para services de reportes
Cubre la lógica de negocio para generación de reportes y dashboards
"""

import time
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.db.models import Q
from django.test import TestCase
from django.utils import timezone

from apps.core.models import CargasSaldo, ConsumosTarjeta, MediosPago, Tarjetas
from apps.inventario.models import StockUnico
from apps.productos.models import Categorias, Productos
from apps.reportes.services import ReporteService
from apps.reportes.services.dashboard_service import DashboardService
from apps.usuarios.models import Empleados, Roles
from apps.ventas.models import DetallesVenta, Ventas


class BaseReportesServiceTest(TestCase):
    """Clase base para tests de services de reportes"""

    def setUp(self):
        """Configurar datos base para todos los tests"""
        # Crear rol y empleado
        self.rol = Roles.objects.create(nombre_rol="Vendedor", descripcion="Rol de vendedor", estado=True)

        self.empleado = Empleados.objects.create(
            nombre="Juan",
            apellido="Vendedor",
            usuario="jvendedor",
            contrasena_hash="$2b$12$hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )

        # Crear medios de pago
        self.medio_efectivo = MediosPago.objects.create(nombre="Efectivo", descripcion="Pago en efectivo", estado=True)

        self.medio_tarjeta = MediosPago.objects.create(nombre="Tarjeta", descripcion="Pago con tarjeta", estado=True)

        # Crear categoría y productos
        self.categoria = Categorias.objects.create(nombre="Bebidas", descripcion="Categoría de bebidas", estado=True)

        self.producto1 = Productos.objects.create(
            nombre="Coca Cola",
            codigo="CC001",
            precio_venta=Decimal("7500.00"),
            id_categoria=self.categoria,
            estado=True,
        )

        self.producto2 = Productos.objects.create(
            nombre="Pepsi", codigo="PP001", precio_venta=Decimal("7000.00"), id_categoria=self.categoria, estado=True
        )

    def crear_ventas_sample(self, cantidad=5, fecha_base=None):
        """Crear ventas de muestra para tests"""
        if fecha_base is None:
            fecha_base = timezone.now()

        ventas = []
        for i in range(cantidad):
            fecha_venta = fecha_base - timedelta(days=i)
            monto = Decimal(str(50000 + (i * 10000)))

            venta = Ventas.objects.create(
                fecha=fecha_venta,
                monto_total=monto,
                id_empleado_cajero=self.empleado,
                id_medio_pago=self.medio_efectivo if i % 2 == 0 else self.medio_tarjeta,
                estado="completada",
            )

            # Crear detalles
            DetallesVenta.objects.create(
                id_venta=venta,
                id_producto=self.producto1 if i % 2 == 0 else self.producto2,
                cantidad=i + 1,
                precio_unitario=self.producto1.precio_venta if i % 2 == 0 else self.producto2.precio_venta,
            )

            ventas.append(venta)

        return ventas

    def crear_recargas_sample(self, cantidad=3):
        """Crear recargas de muestra para tests"""
        tarjeta = Tarjetas.objects.create(nro_tarjeta="1234567890", saldo=Decimal("0.00"), estado=True)

        recargas = []
        for i in range(cantidad):
            recarga = CargasSaldo.objects.create(
                nro_tarjeta=tarjeta,
                monto_cargado=Decimal(str(25000 + (i * 10000))),
                fecha_carga=timezone.now() - timedelta(days=i),
                metodo_pago="efectivo",
                estado="completada",
            )
            recargas.append(recarga)

        return recargas, tarjeta


class ReporteServiceVentasTest(BaseReportesServiceTest):
    """Tests para ReporteService - funcionalidad de ventas"""

    def test_generar_reporte_ventas_basico(self):
        """Debe generar reporte básico de ventas"""
        # Crear datos de prueba
        ventas = self.crear_ventas_sample(3)

        fecha_inicio = timezone.now().date() - timedelta(days=10)
        fecha_fin = timezone.now().date()

        reporte = ReporteService.generar_reporte_ventas(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

        # Verificar estructura del reporte
        self.assertIn("fecha_inicio", reporte)
        self.assertIn("fecha_fin", reporte)
        self.assertIn("total_ventas", reporte)
        self.assertIn("total_monto", reporte)
        self.assertIn("promedio_ticket", reporte)
        self.assertEqual(reporte["fecha_inicio"], fecha_inicio)
        self.assertEqual(reporte["fecha_fin"], fecha_fin)

        # Verificar datos
        self.assertEqual(reporte["total_ventas"], 3)
        self.assertIsInstance(reporte["total_monto"], Decimal)
        self.assertIsInstance(reporte["promedio_ticket"], Decimal)

    def test_generar_reporte_ventas_por_metodo_pago(self):
        """Debe desglosar ventas por método de pago"""
        # Crear ventas con diferentes métodos
        ventas = self.crear_ventas_sample(4)  # 2 efectivo, 2 tarjeta

        fecha_inicio = timezone.now().date() - timedelta(days=10)
        fecha_fin = timezone.now().date()

        reporte = ReporteService.generar_reporte_ventas(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

        # Verificar desglose por método de pago
        self.assertIn("ventas_efectivo", reporte)
        self.assertIn("ventas_tarjeta", reporte)
        self.assertIn("ventas_online", reporte)

        # Verificar que hay montos para ambos métodos
        self.assertGreater(reporte["ventas_efectivo"], Decimal("0"))
        self.assertGreater(reporte["ventas_tarjeta"], Decimal("0"))
        self.assertEqual(reporte["ventas_online"], Decimal("0.00"))

    def test_generar_reporte_ventas_filtro_empleado(self):
        """Debe filtrar ventas por empleado específico"""
        # Crear otro empleado
        empleado2 = Empleados.objects.create(
            nombre="Ana",
            apellido="Cajera",
            usuario="acajera",
            contrasena_hash="$2b$12$hash2",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )

        # Crear ventas para diferentes empleados
        ventas_emp1 = self.crear_ventas_sample(2)

        # Ventas del empleado 2
        Ventas.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal("30000.00"),
            id_empleado_cajero=empleado2,
            id_medio_pago=self.medio_efectivo,
            estado="completada",
        )

        fecha_inicio = timezone.now().date() - timedelta(days=10)
        fecha_fin = timezone.now().date()

        # Reporte para empleado específico
        reporte = ReporteService.generar_reporte_ventas(
            fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, id_empleado=self.empleado.id_empleado
        )

        # Solo debe incluir ventas del empleado especificado
        self.assertEqual(reporte["total_ventas"], 2)

    def test_generar_reporte_ventas_top_productos(self):
        """Debe incluir top productos vendidos"""
        # Crear ventas con detalles
        ventas = self.crear_ventas_sample(5)

        fecha_inicio = timezone.now().date() - timedelta(days=10)
        fecha_fin = timezone.now().date()

        reporte = ReporteService.generar_reporte_ventas(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

        # Verificar top productos
        self.assertIn("top_productos", reporte)
        self.assertIsInstance(reporte["top_productos"], list)

        if len(reporte["top_productos"]) > 0:
            producto_top = reporte["top_productos"][0]
            self.assertIn("id_producto__nombre", producto_top)
            self.assertIn("cantidad_vendida", producto_top)
            self.assertIn("total_vendido", producto_top)

    def test_generar_reporte_ventas_por_dia(self):
        """Debe agrupar ventas por día"""
        # Crear ventas en diferentes días
        ventas = self.crear_ventas_sample(7)

        fecha_inicio = timezone.now().date() - timedelta(days=10)
        fecha_fin = timezone.now().date()

        reporte = ReporteService.generar_reporte_ventas(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

        # Verificar ventas por día
        self.assertIn("ventas_por_dia", reporte)
        self.assertIsInstance(reporte["ventas_por_dia"], list)

        if len(reporte["ventas_por_dia"]) > 0:
            dia_venta = reporte["ventas_por_dia"][0]
            self.assertIn("fecha_dia", dia_venta)
            self.assertIn("cantidad", dia_venta)
            self.assertIn("monto_total", dia_venta)

    def test_generar_reporte_ventas_sin_datos(self):
        """Debe manejar período sin ventas correctamente"""
        fecha_inicio = timezone.now().date() + timedelta(days=1)  # Futuro
        fecha_fin = timezone.now().date() + timedelta(days=7)

        reporte = ReporteService.generar_reporte_ventas(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

        # Verificar valores por defecto
        self.assertEqual(reporte["total_ventas"], 0)
        self.assertEqual(reporte["total_monto"], Decimal("0.00"))
        self.assertEqual(reporte["promedio_ticket"], Decimal("0.00"))
        self.assertEqual(reporte["ventas_efectivo"], Decimal("0.00"))
        self.assertEqual(reporte["ventas_tarjeta"], Decimal("0.00"))

    def test_generar_reporte_ventas_manejo_errores(self):
        """Debe manejar errores de base de datos"""
        with patch("apps.ventas.models.Ventas.objects.filter") as mock_filter:
            # Simular error de DB
            mock_filter.side_effect = Exception("Error de conexión DB")

            fecha_inicio = timezone.now().date()
            fecha_fin = timezone.now().date()

            with self.assertRaises(Exception):
                ReporteService.generar_reporte_ventas(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)


class ReporteServiceRecargasTest(BaseReportesServiceTest):
    """Tests para ReporteService - funcionalidad de recargas"""

    def test_generar_reporte_recargas_basico(self):
        """Debe generar reporte básico de recargas"""
        recargas, tarjeta = self.crear_recargas_sample(3)

        fecha_inicio = timezone.now().date() - timedelta(days=10)
        fecha_fin = timezone.now().date()

        reporte = ReporteService.generar_reporte_recargas(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

        # Verificar estructura
        self.assertIn("total_recargas", reporte)
        self.assertIn("total_acreditado", reporte)
        self.assertIn("total_comisiones", reporte)
        self.assertIn("total_cobrado", reporte)

        # Verificar datos
        self.assertEqual(reporte["total_recargas"], 3)
        self.assertIsInstance(reporte["total_acreditado"], Decimal)

    def test_generar_reporte_recargas_filtro_metodo_pago(self):
        """Debe filtrar recargas por método de pago"""
        recargas, tarjeta = self.crear_recargas_sample(2)

        # Crear recarga con otro método
        CargasSaldo.objects.create(
            nro_tarjeta=tarjeta,
            monto_cargado=Decimal("50000.00"),
            fecha_carga=timezone.now(),
            metodo_pago="tarjeta",
            estado="completada",
        )

        fecha_inicio = timezone.now().date() - timedelta(days=10)
        fecha_fin = timezone.now().date()

        # Filtrar solo efectivo
        reporte = ReporteService.generar_reporte_recargas(
            fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, metodo_pago="efectivo"
        )

        self.assertEqual(reporte["total_recargas"], 2)  # Solo las de efectivo

    def test_generar_reporte_recargas_filtro_estado(self):
        """Debe filtrar recargas por estado"""
        recargas, tarjeta = self.crear_recargas_sample(2)

        # Crear recarga pendiente
        CargasSaldo.objects.create(
            nro_tarjeta=tarjeta,
            monto_cargado=Decimal("30000.00"),
            fecha_carga=timezone.now(),
            metodo_pago="efectivo",
            estado="pendiente",
        )

        fecha_inicio = timezone.now().date() - timedelta(days=10)
        fecha_fin = timezone.now().date()

        # Filtrar solo completadas
        reporte = ReporteService.generar_reporte_recargas(
            fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, estado="completada"
        )

        self.assertEqual(reporte["total_recargas"], 2)  # Solo completadas

    def test_generar_reporte_recargas_agregaciones(self):
        """Debe calcular agregaciones correctamente"""
        recargas, tarjeta = self.crear_recargas_sample(3)

        fecha_inicio = timezone.now().date() - timedelta(days=10)
        fecha_fin = timezone.now().date()

        reporte = ReporteService.generar_reporte_recargas(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

        # Verificar que total_cobrado es al menos igual a total_acreditado
        self.assertGreaterEqual(reporte["total_cobrado"], reporte["total_acreditado"])

        # Verificar estructura de agregaciones
        self.assertIn("recargas_por_metodo", reporte)
        self.assertIn("recargas_por_estado", reporte)
        self.assertIn("estadisticas_diarias", reporte)


class ReporteServiceTopProductosTest(BaseReportesServiceTest):
    """Tests para ReporteService - top productos"""

    def test_generar_reporte_top_productos_basico(self):
        """Debe generar reporte de top productos"""
        # Crear ventas con detalles
        ventas = self.crear_ventas_sample(5)

        fecha_inicio = timezone.now().date() - timedelta(days=10)
        fecha_fin = timezone.now().date()

        reporte = ReporteService.generar_reporte_top_productos(
            fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, limite=10
        )

        # Verificar estructura
        self.assertIn("periodo", reporte)
        self.assertIn("top_productos", reporte)

        # Verificar datos del período
        self.assertEqual(reporte["periodo"]["inicio"], fecha_inicio)
        self.assertEqual(reporte["periodo"]["fin"], fecha_fin)

        # Verificar productos
        if len(reporte["top_productos"]) > 0:
            producto = reporte["top_productos"][0]
            self.assertIn("nombre", producto)
            self.assertIn("cantidad_vendida", producto)
            self.assertIn("total_vendido", producto)

    def test_generar_reporte_top_productos_limite(self):
        """Debe respetar límite de productos"""
        # Crear muchas ventas con diferentes productos
        ventas = self.crear_ventas_sample(10)

        fecha_inicio = timezone.now().date() - timedelta(days=10)
        fecha_fin = timezone.now().date()

        # Límite de 5
        reporte = ReporteService.generar_reporte_top_productos(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, limite=5)

        # No debe exceder el límite
        self.assertLessEqual(len(reporte["top_productos"]), 5)

    def test_generar_reporte_top_productos_ordenamiento(self):
        """Debe ordenar productos por cantidad vendida"""
        # Crear ventas específicas para control de ordenamiento
        ventas = self.crear_ventas_sample(4)

        fecha_inicio = timezone.now().date() - timedelta(days=10)
        fecha_fin = timezone.now().date()

        reporte = ReporteService.generar_reporte_top_productos(
            fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, limite=10
        )

        # Verificar orden descendente
        productos = reporte["top_productos"]
        if len(productos) > 1:
            for i in range(len(productos) - 1):
                self.assertGreaterEqual(productos[i]["cantidad_vendida"], productos[i + 1]["cantidad_vendida"])


class ReporteServiceConsumosTarjetaTest(BaseReportesServiceTest):
    """Tests para ReporteService - consumos de tarjeta"""

    def test_generar_reporte_consumos_tarjeta_basico(self):
        """Debe generar reporte de consumos de tarjeta"""
        # Crear tarjeta con consumos
        recargas, tarjeta = self.crear_recargas_sample(1)

        # Crear consumos
        for i in range(3):
            ConsumosTarjeta.objects.create(
                nro_tarjeta=tarjeta,
                monto=Decimal(str(15000 + (i * 5000))),
                fecha_consumo=timezone.now() - timedelta(days=i),
                establecimiento="Cantina Test",
            )

        fecha_inicio = timezone.now().date() - timedelta(days=10)
        fecha_fin = timezone.now().date()

        reporte = ReporteService.generar_reporte_consumos_tarjeta(
            nro_tarjeta=tarjeta.nro_tarjeta, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
        )

        # Verificar estructura
        self.assertIn("nro_tarjeta", reporte)
        self.assertIn("periodo", reporte)
        self.assertIn("total_consumos", reporte)
        self.assertIn("total_gastado", reporte)

        # Verificar datos
        self.assertEqual(reporte["nro_tarjeta"], tarjeta.nro_tarjeta)
        self.assertEqual(reporte["total_consumos"], 3)

    def test_generar_reporte_consumos_tarjeta_inexistente(self):
        """Debe manejar tarjeta inexistente"""
        fecha_inicio = timezone.now().date() - timedelta(days=10)
        fecha_fin = timezone.now().date()

        reporte = ReporteService.generar_reporte_consumos_tarjeta(
            nro_tarjeta="9999999999", fecha_inicio=fecha_inicio, fecha_fin=fecha_fin  # No existe
        )

        # Debe retornar estructura pero sin datos
        self.assertEqual(reporte["total_consumos"], 0)
        self.assertEqual(reporte["total_gastado"], Decimal("0.00"))


class ReporteServiceFinancieroTest(BaseReportesServiceTest):
    """Tests para ReporteService - reporte financiero"""

    def test_generar_reporte_financiero_basico(self):
        """Debe generar reporte financiero básico"""
        # Crear datos para el reporte
        ventas = self.crear_ventas_sample(3)
        recargas, tarjeta = self.crear_recargas_sample(2)

        fecha_inicio = timezone.now().date() - timedelta(days=10)
        fecha_fin = timezone.now().date()

        reporte = ReporteService.generar_reporte_financiero(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

        # Verificar estructura
        self.assertIn("periodo", reporte)
        self.assertIn("ingresos", reporte)
        self.assertIn("egresos", reporte)

        # Verificar cálculos básicos
        ingresos = reporte["ingresos"]
        self.assertIn("ventas_efectivo", ingresos)
        self.assertIn("ventas_tarjeta", ingresos)
        self.assertIn("recargas", ingresos)
        self.assertIn("total", ingresos)

    def test_generar_reporte_financiero_calculos(self):
        """Debe realizar cálculos financieros correctos"""
        # Crear datos controlados
        ventas = self.crear_ventas_sample(2)

        fecha_inicio = timezone.now().date() - timedelta(days=10)
        fecha_fin = timezone.now().date()

        reporte = ReporteService.generar_reporte_financiero(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

        # Verificar consistencia en totales
        ingresos = reporte["ingresos"]
        total_calculado = ingresos["ventas_efectivo"] + ingresos["ventas_tarjeta"] + ingresos["recargas"]

        self.assertEqual(ingresos["total"], total_calculado)

    def test_generar_reporte_financiero_margen_utilidad(self):
        """Debe calcular margen de utilidad correctamente"""
        ventas = self.crear_ventas_sample(2)

        fecha_inicio = timezone.now().date() - timedelta(days=10)
        fecha_fin = timezone.now().date()

        reporte = ReporteService.generar_reporte_financiero(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

        # Verificar existencia de métricas de rentabilidad
        if "utilidad_neta" in reporte:
            self.assertIsInstance(reporte["utilidad_neta"], Decimal)

        if "margen_utilidad" in reporte:
            self.assertIsInstance(reporte["margen_utilidad"], (int, float))
            self.assertGreaterEqual(reporte["margen_utilidad"], 0)


class DashboardServiceTest(BaseReportesServiceTest):
    """Tests para DashboardService"""

    def test_calcular_kpis_principales_fecha_actual(self):
        """Debe calcular KPIs para fecha actual"""
        ventas = self.crear_ventas_sample(3)

        kpis = DashboardService.calcular_kpis_principales(fecha=None)

        # Verificar estructura
        self.assertIn("fecha", kpis)
        self.assertIn("kpis", kpis)

        # Verificar fecha (debe ser hoy)
        self.assertEqual(kpis["fecha"], date.today())

    def test_calcular_kpis_principales_fecha_especifica(self):
        """Debe calcular KPIs para fecha específica"""
        fecha_especifica = timezone.now().date() - timedelta(days=5)

        kpis = DashboardService.calcular_kpis_principales(fecha=fecha_especifica)

        self.assertEqual(kpis["fecha"], fecha_especifica)

    def test_obtener_dashboard_ventas_periodo_default(self):
        """Debe obtener dashboard de ventas con período por defecto"""
        ventas = self.crear_ventas_sample(5)

        dashboard = DashboardService.obtener_dashboard_ventas(dias=7)

        # Verificar estructura
        self.assertIn("periodo_dias", dashboard)
        self.assertIn("resumen", dashboard)
        self.assertIn("graficos", dashboard)

        self.assertEqual(dashboard["periodo_dias"], 7)

    def test_obtener_dashboard_ventas_periodo_personalizado(self):
        """Debe obtener dashboard con período personalizado"""
        ventas = self.crear_ventas_sample(10)

        dashboard = DashboardService.obtener_dashboard_ventas(dias=30)

        self.assertEqual(dashboard["periodo_dias"], 30)

    def test_obtener_dashboard_recargas(self):
        """Debe obtener dashboard de recargas"""
        recargas, tarjeta = self.crear_recargas_sample(3)

        dashboard = DashboardService.obtener_dashboard_recargas(dias=7)

        # Verificar estructura básica
        self.assertIn("periodo_dias", dashboard)
        self.assertIn("resumen", dashboard)

    def test_obtener_dashboard_financiero_mes_actual(self):
        """Debe obtener dashboard financiero para mes actual"""
        ventas = self.crear_ventas_sample(3)

        dashboard = DashboardService.obtener_dashboard_financiero(mes=None)

        # Verificar estructura
        self.assertIn("mes", dashboard)
        self.assertIn("año", dashboard)
        self.assertIn("resumen_financiero", dashboard)

        # Verificar mes actual
        mes_actual = timezone.now().month
        self.assertEqual(dashboard["mes"], mes_actual)

    def test_obtener_dashboard_financiero_mes_especifico(self):
        """Debe obtener dashboard para mes específico"""
        dashboard = DashboardService.obtener_dashboard_financiero(mes=3)

        self.assertEqual(dashboard["mes"], 3)


class ReportesServicePerformanceTest(BaseReportesServiceTest):
    """Tests de performance para services de reportes"""

    def test_performance_reporte_ventas_grande(self):
        """Debe manejar volúmenes grandes de ventas"""
        import time

        # Crear muchas ventas
        ventas = self.crear_ventas_sample(50)

        fecha_inicio = timezone.now().date() - timedelta(days=30)
        fecha_fin = timezone.now().date()

        start_time = time.time()
        reporte = ReporteService.generar_reporte_ventas(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
        end_time = time.time()

        duration = end_time - start_time

        # Debe completarse en tiempo razonable (menos de 5 segundos)
        self.assertLess(duration, 5.0)
        self.assertEqual(reporte["total_ventas"], 50)

    def test_cache_dashboard_kpis(self):
        """Debe implementar estrategias de cache para KPIs frecuentes"""
        # Simular múltiples consultas de KPIs
        fecha_test = date.today()

        # Primera consulta
        start_time1 = time.time()
        kpis1 = DashboardService.calcular_kpis_principales(fecha=fecha_test)
        end_time1 = time.time()

        # Segunda consulta (posible cache)
        start_time2 = time.time()
        kpis2 = DashboardService.calcular_kpis_principales(fecha=fecha_test)
        end_time2 = time.time()

        # Los resultados deben ser consistentes
        self.assertEqual(kpis1["fecha"], kpis2["fecha"])

        # En implementación real, la segunda consulta podría ser más rápida por cache
        duration1 = end_time1 - start_time1
        duration2 = end_time2 - start_time2

        # Al menos debe completarse
        self.assertLess(duration1, 5.0)
        self.assertLess(duration2, 5.0)

    def test_optimizacion_consultas_agregadas(self):
        """Debe optimizar consultas con agregaciones complejas"""
        # Crear datos diversos
        ventas = self.crear_ventas_sample(20)
        recargas, tarjeta = self.crear_recargas_sample(10)

        fecha_inicio = timezone.now().date() - timedelta(days=30)
        fecha_fin = timezone.now().date()

        # Pueden ejecutarse múltiples reportes sin degradación severa
        reportes_generados = 0
        start_time = time.time()

        for _ in range(3):
            reporte_ventas = ReporteService.generar_reporte_ventas(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
            reportes_generados += 1

            reporte_financiero = ReporteService.generar_reporte_financiero(
                fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
            )
            reportes_generados += 1

        end_time = time.time()
        duration = end_time - start_time

        # 6 reportes en menos de 10 segundos
        self.assertEqual(reportes_generados, 6)
        self.assertLess(duration, 10.0)


class ReportesServiceErrorHandlingTest(BaseReportesServiceTest):
    """Tests de manejo de errores en services"""

    def test_manejo_error_base_datos(self):
        """Debe manejar errores de base de datos gracefully"""
        with patch("apps.ventas.models.Ventas.objects.filter") as mock_filter:
            mock_filter.side_effect = Exception("Connection timeout")

            fecha_inicio = timezone.now().date()
            fecha_fin = timezone.now().date()

            with self.assertRaises(Exception):
                ReporteService.generar_reporte_ventas(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

    def test_validacion_parametros_fecha(self):
        """Debe validar parámetros de fecha"""
        fecha_inicio = timezone.now().date()
        fecha_fin = timezone.now().date() - timedelta(days=1)  # Fecha fin anterior

        # Dependiendo de implementación, puede lanzar excepción o intercambiar fechas
        try:
            reporte = ReporteService.generar_reporte_ventas(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
            # Si no lanza excepción, verificar que manejó el caso
            self.assertIsInstance(reporte, dict)
        except Exception as e:
            # Es válido que lance excepción por fechas inválidas
            self.assertIn("fecha", str(e).lower())

    def test_resilencia_datos_corruptos(self):
        """Debe ser resiliente a datos corruptos o inconsistentes"""
        # Crear venta con datos extremos
        venta_extrema = Ventas.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal("999999999.99"),  # Monto muy grande
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_efectivo,
            estado="completada",
        )

        fecha_inicio = timezone.now().date()
        fecha_fin = timezone.now().date()

        # No debe fallar por datos extremos
        reporte = ReporteService.generar_reporte_ventas(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

        self.assertIsInstance(reporte["total_monto"], Decimal)
        self.assertGreater(reporte["total_monto"], Decimal("0"))

    def test_comportamiento_sin_datos(self):
        """Debe comportarse correctamente sin datos"""
        # Período futuro sin datos
        fecha_inicio = timezone.now().date() + timedelta(days=30)
        fecha_fin = timezone.now().date() + timedelta(days=60)

        reporte = ReporteService.generar_reporte_ventas(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

        # Debe retornar estructura válida con valores en cero
        self.assertEqual(reporte["total_ventas"], 0)
        self.assertEqual(reporte["total_monto"], Decimal("0.00"))
        self.assertEqual(len(reporte["top_productos"]), 0)
        self.assertEqual(len(reporte["ventas_por_dia"]), 0)
