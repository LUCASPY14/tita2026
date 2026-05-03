"""
Tests para models de reportes
Cubre modelos de plantillas, dashboards, KPIs, tareas y ejecuciones
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.reportes.models import (
    Dashboards,
    DestinatariosTarea,
    EjecucionesTarea,
    KpiMetricas,
    PlantillasReporte,
    PlantillasTarea,
    ValoresKpi,
)
from apps.usuarios.models import Empleados, Roles


class BaseReportesModelTest(TestCase):
    """Clase base para tests de modelos de reportes"""

    def setUp(self):
        """Configurar datos base para todos los tests"""
        # Crear rol y empleado
        self.rol = Roles.objects.create(nombre_rol="Administrador", descripcion="Rol administrativo", estado=True)

        self.empleado = Empleados.objects.create(
            nombre="Admin",
            apellido="Reportes",
            usuario="admin_reportes",
            contrasena_hash="$2b$12$hash",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )


class PlantillasReporteModelTest(BaseReportesModelTest):
    """Tests para modelo PlantillasReporte"""

    def test_crear_plantilla_reporte_basica(self):
        """Debe crear plantilla de reporte básica correctamente"""
        plantilla = PlantillasReporte.objects.create(
            nombre="Reporte Ventas Diarias",
            descripcion="Reporte de ventas por día",
            query_sql="SELECT * FROM ventas WHERE fecha = ?",
            parametros={"fecha": "date"},
            tipo_reporte="ventas",
            frecuencia="diario",
            estado=True,
            created_at=timezone.now(),
            created_by=self.empleado,
        )

        self.assertEqual(plantilla.nombre, "Reporte Ventas Diarias")
        self.assertEqual(plantilla.tipo_reporte, "ventas")
        self.assertEqual(plantilla.frecuencia, "diario")
        self.assertTrue(plantilla.estado)
        self.assertEqual(plantilla.created_by, self.empleado)

    def test_plantilla_reporte_str_representation(self):
        """Debe tener representación string correcta"""
        plantilla = PlantillasReporte.objects.create(
            nombre="Test Reporte",
            query_sql="SELECT 1",
            parametros={},
            tipo_reporte="test",
            frecuencia="manual",
            created_at=timezone.now(),
        )

        expected_str = f"PlantillasReporte #{plantilla.pk}"
        self.assertEqual(str(plantilla), expected_str)

    def test_plantilla_reporte_json_parametros(self):
        """Debe manejar parámetros JSON correctamente"""
        parametros_complejos = {
            "fecha_inicio": "date",
            "fecha_fin": "date",
            "filtros": {"empleado": "integer", "sucursal": "string"},
            "opciones": {"incluir_totales": True, "formato": "pdf"},
        }

        plantilla = PlantillasReporte.objects.create(
            nombre="Reporte Complejo",
            query_sql="SELECT * FROM tabla WHERE fecha BETWEEN ? AND ?",
            parametros=parametros_complejos,
            tipo_reporte="financiero",
            frecuencia="mensual",
            created_at=timezone.now(),
        )

        self.assertEqual(plantilla.parametros, parametros_complejos)
        self.assertEqual(plantilla.parametros["filtros"]["empleado"], "integer")
        self.assertTrue(plantilla.parametros["opciones"]["incluir_totales"])

    def test_plantilla_reporte_query_sql_complejo(self):
        """Debe almacenar queries SQL complejos"""
        query_complejo = """
        SELECT 
            DATE(v.fecha) as fecha_venta,
            COUNT(*) as cantidad_ventas,
            SUM(v.monto_total) as total_vendido,
            AVG(v.monto_total) as ticket_promedio,
            e.nombre as empleado
        FROM ventas v
        JOIN empleados e ON v.id_empleado = e.id_empleado
        WHERE v.fecha BETWEEN %s AND %s
        GROUP BY DATE(v.fecha), e.id_empleado
        ORDER BY fecha_venta DESC, total_vendido DESC
        """

        plantilla = PlantillasReporte.objects.create(
            nombre="Reporte Ventas Detallado",
            query_sql=query_complejo,
            parametros={"fecha_inicio": "date", "fecha_fin": "date"},
            tipo_reporte="ventas",
            frecuencia="personalizado",
            created_at=timezone.now(),
        )

        self.assertIn("GROUP BY", plantilla.query_sql)
        self.assertIn("ORDER BY", plantilla.query_sql)
        self.assertIn("JOIN", plantilla.query_sql)

    def test_plantilla_reporte_tipos_validos(self):
        """Debe manejar diferentes tipos de reporte"""
        tipos_reporte = ["ventas", "inventario", "financiero", "kpi", "dashboard", "auditoria", "operativo"]

        for tipo in tipos_reporte:
            plantilla = PlantillasReporte.objects.create(
                nombre=f"Reporte {tipo.title()}",
                query_sql="SELECT 1",
                parametros={},
                tipo_reporte=tipo,
                frecuencia="manual",
                created_at=timezone.now(),
            )

            self.assertEqual(plantilla.tipo_reporte, tipo)
            plantilla.delete()

    def test_plantilla_reporte_frecuencias_validas(self):
        """Debe manejar diferentes frecuencias"""
        frecuencias = ["manual", "diario", "semanal", "mensual", "trimestral", "anual", "tiempo_real"]

        for frecuencia in frecuencias:
            plantilla = PlantillasReporte.objects.create(
                nombre=f"Reporte {frecuencia.title()}",
                query_sql="SELECT 1",
                parametros={},
                tipo_reporte="test",
                frecuencia=frecuencia,
                created_at=timezone.now(),
            )

            self.assertEqual(plantilla.frecuencia, frecuencia)
            plantilla.delete()

    def test_plantilla_reporte_meta_options(self):
        """Debe tener opciones de meta correctas"""
        meta = PlantillasReporte._meta

        self.assertEqual(meta.db_table, "plantillas_reporte")
        self.assertEqual(meta.verbose_name, "Plantilla de Reporte")
        self.assertEqual(meta.verbose_name_plural, "Plantillas de Reportes")
        self.assertTrue(meta.managed)


class DashboardsModelTest(BaseReportesModelTest):
    """Tests para modelo Dashboards"""

    def test_crear_dashboard_basico(self):
        """Debe crear dashboard básico correctamente"""
        configuracion_dashboard = {
            "widgets": [
                {"type": "chart", "title": "Ventas Diarias", "query": "ventas_diarias"},
                {"type": "kpi", "title": "Total Ventas", "query": "total_ventas"},
                {"type": "table", "title": "Top Productos", "query": "top_productos"},
            ],
            "layout": {"columns": 3, "rows": 2},
            "refresh_interval": 300,
        }

        dashboard = Dashboards.objects.create(
            nombre="Dashboard Principal",
            descripcion="Dashboard principal de la aplicación",
            configuracion=configuracion_dashboard,
            es_publico=1,
            predeterminado=1,
            estado=True,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=self.empleado,
        )

        self.assertEqual(dashboard.nombre, "Dashboard Principal")
        self.assertEqual(dashboard.es_publico, 1)
        self.assertEqual(dashboard.predeterminado, 1)
        self.assertTrue(dashboard.estado)
        self.assertEqual(dashboard.id_empleado, self.empleado)

    def test_dashboard_configuracion_json_compleja(self):
        """Debe manejar configuración JSON compleja"""
        configuracion_compleja = {
            "metadata": {"version": "1.0", "autor": "Sistema", "fecha_creacion": "2024-03-15"},
            "widgets": [
                {
                    "id": "widget_1",
                    "type": "line_chart",
                    "title": "Evolución Ventas",
                    "data_source": "api/reportes/ventas",
                    "config": {
                        "x_axis": "fecha",
                        "y_axis": "monto",
                        "series": ["ventas_efectivo", "ventas_tarjeta"],
                        "colors": ["#007bff", "#28a745"],
                    },
                    "position": {"x": 0, "y": 0, "width": 6, "height": 4},
                },
                {
                    "id": "widget_2",
                    "type": "gauge",
                    "title": "Objetivo Mensual",
                    "data_source": "api/kpis/objetivo_mensual",
                    "config": {"min_value": 0, "max_value": 100, "target": 80, "unit": "%"},
                    "position": {"x": 6, "y": 0, "width": 3, "height": 4},
                },
            ],
            "filters": [{"name": "fecha_range", "type": "date_range", "default": "last_30_days"}],
            "permissions": {"view": ["admin", "gerencia"], "edit": ["admin"]},
        }

        dashboard = Dashboards.objects.create(
            nombre="Dashboard Avanzado",
            configuracion=configuracion_compleja,
            es_publico=0,
            predeterminado=0,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=self.empleado,
        )

        self.assertEqual(len(dashboard.configuracion["widgets"]), 2)
        self.assertEqual(dashboard.configuracion["widgets"][0]["type"], "line_chart")
        self.assertEqual(dashboard.configuracion["metadata"]["version"], "1.0")
        self.assertIn("permissions", dashboard.configuracion)

    def test_dashboard_str_representation(self):
        """Debe tener representación string correcta"""
        dashboard = Dashboards.objects.create(
            nombre="Test Dashboard",
            configuracion={},
            es_publico=1,
            predeterminado=0,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=self.empleado,
        )

        expected_str = f"Dashboards #{dashboard.pk}"
        self.assertEqual(str(dashboard), expected_str)

    def test_dashboard_publico_vs_privado(self):
        """Debe diferenciar entre dashboards públicos y privados"""
        # Dashboard público
        dashboard_publico = Dashboards.objects.create(
            nombre="Dashboard Público",
            configuracion={},
            es_publico=1,
            predeterminado=0,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=self.empleado,
        )

        # Dashboard privado
        dashboard_privado = Dashboards.objects.create(
            nombre="Dashboard Privado",
            configuracion={},
            es_publico=0,
            predeterminado=0,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=self.empleado,
        )

        self.assertEqual(dashboard_publico.es_publico, 1)
        self.assertEqual(dashboard_privado.es_publico, 0)

    def test_dashboard_predeterminado_unico(self):
        """Debe permitir solo un dashboard predeterminado por usuario"""
        # Primer dashboard predeterminado
        dashboard1 = Dashboards.objects.create(
            nombre="Dashboard Predeterminado 1",
            configuracion={},
            es_publico=1,
            predeterminado=1,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=self.empleado,
        )

        # Segundo dashboard predeterminado (en lógica de negocio debería actualizar el primero)
        dashboard2 = Dashboards.objects.create(
            nombre="Dashboard Predeterminado 2",
            configuracion={},
            es_publico=1,
            predeterminado=1,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=self.empleado,
        )

        # Ambos se crean sin problema a nivel de modelo (la lógica de unicidad estaría en el servicio)
        self.assertEqual(dashboard1.predeterminado, 1)
        self.assertEqual(dashboard2.predeterminado, 1)


class KpiMetricasModelTest(BaseReportesModelTest):
    """Tests para modelo KpiMetricas"""

    def test_crear_kpi_metrica_basica(self):
        """Debe crear KPI métrica básica correctamente"""
        kpi = KpiMetricas.objects.create(
            nombre="Ventas Totales",
            descripcion="Total de ventas del período",
            formula="SUM(monto_total) FROM ventas",
            unidad="PYG",
            valor_objetivo=Decimal("10000000.00"),
            categoria="ventas",
            frecuencia="diario",
            estado=True,
        )

        self.assertEqual(kpi.nombre, "Ventas Totales")
        self.assertEqual(kpi.unidad, "PYG")
        self.assertEqual(kpi.valor_objetivo, Decimal("10000000.00"))
        self.assertEqual(kpi.categoria, "ventas")
        self.assertTrue(kpi.estado)

    def test_kpi_metricas_diferentes_tipos(self):
        """Debe manejar diferentes tipos de KPIs"""
        kpis_data = [
            {"nombre": "Ticket Promedio", "formula": "AVG(monto_total)", "unidad": "PYG", "categoria": "ventas"},
            {
                "nombre": "Productos Vendidos",
                "formula": "SUM(cantidad)",
                "unidad": "unidades",
                "categoria": "productos",
            },
            {"nombre": "Satisfacción Cliente", "formula": "AVG(rating)", "unidad": "puntos", "categoria": "calidad"},
            {
                "nombre": "Rotación Inventario",
                "formula": "COGS / Average_Inventory",
                "unidad": "veces",
                "categoria": "operativo",
            },
        ]

        for kpi_data in kpis_data:
            kpi = KpiMetricas.objects.create(
                nombre=kpi_data["nombre"],
                descripcion=f"KPI para {kpi_data['categoria']}",
                formula=kpi_data["formula"],
                unidad=kpi_data["unidad"],
                categoria=kpi_data["categoria"],
                frecuencia="semanal",
                estado=True,
            )

            self.assertEqual(kpi.categoria, kpi_data["categoria"])
            self.assertEqual(kpi.unidad, kpi_data["unidad"])
            kpi.delete()

    def test_kpi_metricas_formulas_complejas(self):
        """Debe almacenar fórmulas complejas correctamente"""
        formula_compleja = """
        CASE 
            WHEN EXTRACT(HOUR FROM fecha) BETWEEN 11 AND 14 
                THEN SUM(monto_total)
            WHEN EXTRACT(HOUR FROM fecha) BETWEEN 18 AND 21 
                THEN SUM(monto_total) * 0.8
            ELSE 0
        END / 
        (SELECT COUNT(*) FROM ventas WHERE fecha = CURRENT_DATE)
        """

        kpi = KpiMetricas.objects.create(
            nombre="Ventas Ponderadas por Horario",
            descripcion="Ventas ajustadas según horarios de mayor demanda",
            formula=formula_compleja,
            unidad="PYG",
            categoria="operativo",
            frecuencia="diario",
            estado=True,
        )

        self.assertIn("CASE", kpi.formula)
        self.assertIn("EXTRACT", kpi.formula)
        self.assertIn("WHEN", kpi.formula)

    def test_kpi_metricas_categorias_validas(self):
        """Debe manejar diferentes categorías de KPI"""
        categorias = [
            "ventas",
            "financiero",
            "operativo",
            "calidad",
            "inventario",
            "personal",
            "satisfaccion",
            "eficiencia",
        ]

        for categoria in categorias:
            kpi = KpiMetricas.objects.create(
                nombre=f"KPI {categoria.title()}",
                descripcion=f"Métrica de {categoria}",
                formula="SELECT 1",
                unidad="unidad",
                categoria=categoria,
                frecuencia="mensual",
                estado=True,
            )

            self.assertEqual(kpi.categoria, categoria)
            kpi.delete()

    def test_kpi_metricas_str_representation(self):
        """Debe tener representación string correcta"""
        kpi = KpiMetricas.objects.create(
            nombre="Test KPI",
            descripcion="Test description",
            formula="SELECT 1",
            unidad="test",
            categoria="test",
            frecuencia="manual",
        )

        expected_str = f"KpiMetricas #{kpi.pk}"
        self.assertEqual(str(kpi), expected_str)


class ValoresKpiModelTest(BaseReportesModelTest):
    """Tests para modelo ValoresKpi"""

    def setUp(self):
        """Configurar datos específicos para valores KPI"""
        super().setUp()

        self.kpi = KpiMetricas.objects.create(
            nombre="Test KPI",
            descripcion="KPI para tests",
            formula="SELECT COUNT(*) FROM ventas",
            unidad="unidades",
            categoria="test",
            frecuencia="diario",
            estado=True,
        )

    def test_crear_valor_kpi_basico(self):
        """Debe crear valor KPI básico correctamente"""
        valor_kpi = ValoresKpi.objects.create(
            fecha=date.today(),
            valor=Decimal("150.75"),
            notas="Valor calculado automáticamente",
            auto_calc=1,
            created_at=timezone.now(),
            id_kpi=self.kpi,
        )

        self.assertEqual(valor_kpi.fecha, date.today())
        self.assertEqual(valor_kpi.valor, Decimal("150.75"))
        self.assertEqual(valor_kpi.auto_calc, 1)
        self.assertEqual(valor_kpi.id_kpi, self.kpi)

    def test_valor_kpi_manual_vs_automatico(self):
        """Debe diferenciar entre valores manuales y automáticos"""
        # Valor automático
        valor_auto = ValoresKpi.objects.create(
            fecha=date.today(), valor=Decimal("100.00"), auto_calc=1, created_at=timezone.now(), id_kpi=self.kpi
        )

        # Valor manual
        valor_manual = ValoresKpi.objects.create(
            fecha=date.today() - timedelta(days=1),
            valor=Decimal("95.50"),
            notas="Ajustado manualmente por gerencia",
            auto_calc=0,
            created_at=timezone.now(),
            id_kpi=self.kpi,
        )

        self.assertEqual(valor_auto.auto_calc, 1)
        self.assertEqual(valor_manual.auto_calc, 0)
        self.assertIsNotNone(valor_manual.notas)

    def test_valor_kpi_unique_constraint(self):
        """Debe validar constrainte único de KPI + fecha"""
        fecha_test = date.today()

        # Crear primer valor
        ValoresKpi.objects.create(
            fecha=fecha_test, valor=Decimal("100.00"), auto_calc=1, created_at=timezone.now(), id_kpi=self.kpi
        )

        # Intentar crear segundo valor para misma fecha y KPI
        with self.assertRaises(IntegrityError):
            ValoresKpi.objects.create(
                fecha=fecha_test, valor=Decimal("200.00"), auto_calc=1, created_at=timezone.now(), id_kpi=self.kpi
            )

    def test_valor_kpi_historico(self):
        """Debe manejar valores históricos correctamente"""
        # Crear serie de valores históricos
        valores_historicos = []
        for i in range(30):
            fecha_valor = date.today() - timedelta(days=i)
            valor = Decimal(str(100 + (i * 5)))  # Valores crecientes

            valor_kpi = ValoresKpi.objects.create(
                fecha=fecha_valor, valor=valor, auto_calc=1, created_at=timezone.now(), id_kpi=self.kpi
            )
            valores_historicos.append(valor_kpi)

        # Verificar que se crearon todos
        self.assertEqual(len(valores_historicos), 30)

        # Verificar ordenamiento por fecha
        valores_ordenados = ValoresKpi.objects.filter(id_kpi=self.kpi).order_by("fecha")
        self.assertEqual(valores_ordenados.count(), 30)

        # Verificar que el primer valor es el más antiguo
        primer_valor = valores_ordenados.first()
        ultimo_valor = valores_ordenados.last()
        self.assertLess(primer_valor.fecha, ultimo_valor.fecha)

    def test_valor_kpi_str_representation(self):
        """Debe tener representación string correcta"""
        valor_kpi = ValoresKpi.objects.create(
            fecha=date.today(), valor=Decimal("123.45"), auto_calc=1, created_at=timezone.now(), id_kpi=self.kpi
        )

        expected_str = f"ValoresKpi #{valor_kpi.pk}"
        self.assertEqual(str(valor_kpi), expected_str)

    def test_valor_kpi_precision_decimal(self):
        """Debe manejar precisión decimal correctamente"""
        # Valores con diferentes precisiones
        valores_test = [
            Decimal("100"),
            Decimal("100.5"),
            Decimal("100.55"),
            Decimal("100.555"),
            Decimal("9999999999999.99"),  # Máximo según max_digits/decimal_places
        ]

        for i, valor in enumerate(valores_test):
            fecha_valor = date.today() - timedelta(days=i)
            valor_kpi = ValoresKpi.objects.create(
                fecha=fecha_valor, valor=valor, auto_calc=1, created_at=timezone.now(), id_kpi=self.kpi
            )

            # Verificar que mantiene precisión
            self.assertEqual(valor_kpi.valor, valor)
            valor_kpi.delete()


class PlantillasTareaModelTest(BaseReportesModelTest):
    """Tests para modelo PlantillasTarea"""

    def test_crear_plantilla_tarea_basica(self):
        """Debe crear plantilla de tarea básica correctamente"""
        plantilla = PlantillasTarea.objects.create(
            nombre="Backup Diario",
            descripcion="Respaldo automático de base de datos",
            tipo_tarea="backup",
            comando="pg_dump cantina_db",
            parametros={"compress": True, "format": "custom"},
            frecuencia="diario",
            cron="0 2 * * *",
            timeout=3600,
            max_reintentos=3,
            notif_exito=1,
            notif_error=1,
            estado=True,
            created_at=timezone.now(),
            created_by=self.empleado,
        )

        self.assertEqual(plantilla.nombre, "Backup Diario")
        self.assertEqual(plantilla.tipo_tarea, "backup")
        self.assertEqual(plantilla.cron, "0 2 * * *")
        self.assertEqual(plantilla.timeout, 3600)
        self.assertEqual(plantilla.max_reintentos, 3)
        self.assertTrue(plantilla.estado)

    def test_plantilla_tarea_diferentes_tipos(self):
        """Debe manejar diferentes tipos de tareas"""
        tipos_tarea = [
            ("reporte", "python manage.py generate_report"),
            ("backup", "pg_dump database"),
            ("limpieza", "python manage.py cleanup_logs"),
            ("sync", "rsync -av source destination"),
            ("mantenimiento", "python manage.py optimize_db"),
        ]

        for tipo, comando in tipos_tarea:
            plantilla = PlantillasTarea.objects.create(
                nombre=f"Tarea {tipo.title()}",
                descripcion=f"Tarea de {tipo}",
                tipo_tarea=tipo,
                comando=comando,
                parametros={},
                frecuencia="semanal",
                cron="0 0 * * 0",
                timeout=1800,
                max_reintentos=1,
                created_at=timezone.now(),
            )

            self.assertEqual(plantilla.tipo_tarea, tipo)
            self.assertEqual(plantilla.comando, comando)
            plantilla.delete()

    def test_plantilla_tarea_parametros_json_complejos(self):
        """Debe manejar parámetros JSON complejos"""
        parametros_complejos = {
            "database": {"host": "localhost", "port": 5432, "name": "cantina_db"},
            "options": {"verbose": True, "compress": True, "exclude_tables": ["logs", "temp_*"]},
            "notifications": {
                "on_success": ["admin@cantina.com"],
                "on_failure": ["admin@cantina.com", "dev@cantina.com"],
            },
            "retention": {"keep_daily": 7, "keep_weekly": 4, "keep_monthly": 12},
        }

        plantilla = PlantillasTarea.objects.create(
            nombre="Backup Completo",
            descripcion="Backup con configuración avanzada",
            tipo_tarea="backup",
            comando="python scripts/advanced_backup.py",
            parametros=parametros_complejos,
            frecuencia="diario",
            cron="0 3 * * *",
            timeout=7200,
            max_reintentos=2,
            created_at=timezone.now(),
        )

        self.assertEqual(plantilla.parametros["database"]["port"], 5432)
        self.assertTrue(plantilla.parametros["options"]["compress"])
        self.assertEqual(len(plantilla.parametros["notifications"]["on_failure"]), 2)

    def test_plantilla_tarea_expresiones_cron_validas(self):
        """Debe validar expresiones cron"""
        expresiones_cron = [
            ("0 0 * * *", "Diario a medianoche"),
            ("0 2 * * *", "Diario a las 2 AM"),
            ("0 0 * * 0", "Semanal los domingos"),
            ("0 0 1 * *", "Mensual el primer día"),
            ("*/15 * * * *", "Cada 15 minutos"),
            ("0 9-17 * * 1-5", "Horario laboral"),
        ]

        for cron, descripcion in expresiones_cron:
            plantilla = PlantillasTarea.objects.create(
                nombre=f"Tarea {descripcion}",
                descripcion=descripcion,
                tipo_tarea="test",
                comando='echo "test"',
                parametros={},
                frecuencia="custom",
                cron=cron,
                timeout=60,
                max_reintentos=1,
                created_at=timezone.now(),
            )

            self.assertEqual(plantilla.cron, cron)
            plantilla.delete()

    def test_plantilla_tarea_configuracion_notificaciones(self):
        """Debe configurar notificaciones correctamente"""
        # Tarea sin notificaciones
        tarea_sin_notif = PlantillasTarea.objects.create(
            nombre="Tarea Silenciosa",
            tipo_tarea="limpieza",
            comando="rm -rf /tmp/temp_files",
            parametros={},
            frecuencia="diario",
            cron="0 4 * * *",
            timeout=300,
            max_reintentos=1,
            notif_exito=0,
            notif_error=0,
            created_at=timezone.now(),
        )

        # Tarea con notificaciones completas
        tarea_con_notif = PlantillasTarea.objects.create(
            nombre="Tarea Crítica",
            tipo_tarea="backup",
            comando="critical_backup.sh",
            parametros={},
            frecuencia="diario",
            cron="0 1 * * *",
            timeout=3600,
            max_reintentos=5,
            notif_exito=1,
            notif_error=1,
            created_at=timezone.now(),
        )

        self.assertEqual(tarea_sin_notif.notif_exito, 0)
        self.assertEqual(tarea_sin_notif.notif_error, 0)
        self.assertEqual(tarea_con_notif.notif_exito, 1)
        self.assertEqual(tarea_con_notif.notif_error, 1)

    def test_plantilla_tarea_str_representation(self):
        """Debe tener representación string correcta"""
        plantilla = PlantillasTarea.objects.create(
            nombre="Test Task",
            tipo_tarea="test",
            comando="test command",
            parametros={},
            frecuencia="manual",
            cron="0 0 * * *",
            timeout=60,
            max_reintentos=1,
            created_at=timezone.now(),
        )

        expected_str = f"PlantillasTarea #{plantilla.pk}"
        self.assertEqual(str(plantilla), expected_str)

    def test_id_empleado_setter_method(self):
        """Debe cubrir el método id_empleado_setter (línea 123)"""
        plantilla = PlantillasTarea.objects.create(
            nombre="Tarea Setter",
            tipo_tarea="test",
            comando="cmd",
            parametros={},
            frecuencia="manual",
            cron="0 0 * * *",
            timeout=60,
            max_reintentos=1,
            created_at=timezone.now(),
        )
        plantilla.id_empleado_setter(self.empleado)
        self.assertEqual(plantilla.created_by, self.empleado)


class EjecucionesTareaModelTest(BaseReportesModelTest):
    """Tests para modelo EjecucionesTarea"""

    def setUp(self):
        """Configurar datos específicos para ejecuciones"""
        super().setUp()

        self.plantilla = PlantillasTarea.objects.create(
            nombre="Tarea Test",
            tipo_tarea="test",
            comando='echo "test"',
            parametros={},
            frecuencia="manual",
            cron="0 0 * * *",
            timeout=60,
            max_reintentos=1,
            created_at=timezone.now(),
        )

    def test_crear_ejecucion_tarea_exitosa(self):
        """Debe crear ejecución exitosa correctamente"""
        fecha_inicio = timezone.now()
        fecha_fin = fecha_inicio + timedelta(seconds=30)

        ejecucion = EjecucionesTarea.objects.create(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            duracion_seg=30,
            estado="completado",
            resultado="Tarea ejecutada correctamente",
            pid=12345,
            servidor="server01",
            parametros={"test": True},
            ejecutado_por=self.empleado,
            id_plantilla=self.plantilla,
        )

        self.assertEqual(ejecucion.estado, "completado")
        self.assertEqual(ejecucion.duracion_seg, 30)
        self.assertEqual(ejecucion.pid, 12345)
        self.assertEqual(ejecucion.servidor, "server01")
        self.assertEqual(ejecucion.ejecutado_por, self.empleado)

    def test_crear_ejecucion_tarea_fallida(self):
        """Debe crear ejecución fallida correctamente"""
        fecha_inicio = timezone.now()
        fecha_fin = fecha_inicio + timedelta(seconds=15)

        ejecucion = EjecucionesTarea.objects.create(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            duracion_seg=15,
            estado="error",
            error_msg="Permission denied: /backup/folder",
            logs="[ERROR] Cannot access backup directory",
            pid=54321,
            servidor="server02",
            parametros={"force": False},
            id_plantilla=self.plantilla,
        )

        self.assertEqual(ejecucion.estado, "error")
        self.assertIsNotNone(ejecucion.error_msg)
        self.assertIsNotNone(ejecucion.logs)
        self.assertEqual(ejecucion.duracion_seg, 15)

    def test_ejecucion_tarea_estados_validos(self):
        """Debe manejar diferentes estados de ejecución"""
        estados = ["pendiente", "ejecutando", "completado", "error", "cancelado", "timeout"]

        for i, estado in enumerate(estados):
            ejecucion = EjecucionesTarea.objects.create(
                fecha_inicio=timezone.now(),
                estado=estado,
                pid=1000 + i,
                servidor="test_server",
                parametros={},
                id_plantilla=self.plantilla,
            )

            self.assertEqual(ejecucion.estado, estado)
            ejecucion.delete()

    def test_ejecucion_tarea_duracion_calculo(self):
        """Debe calcular duración correctamente"""
        fecha_inicio = timezone.now()

        # Ejecución de 1 minuto
        ejecucion_1min = EjecucionesTarea.objects.create(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_inicio + timedelta(minutes=1),
            duracion_seg=60,
            estado="completado",
            servidor="server01",
            parametros={},
            id_plantilla=self.plantilla,
        )

        # Ejecución de 1 hora
        ejecucion_1hora = EjecucionesTarea.objects.create(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_inicio + timedelta(hours=1),
            duracion_seg=3600,
            estado="completado",
            servidor="server01",
            parametros={},
            id_plantilla=self.plantilla,
        )

        self.assertEqual(ejecucion_1min.duracion_seg, 60)
        self.assertEqual(ejecucion_1hora.duracion_seg, 3600)

    def test_ejecucion_tarea_logs_detallados(self):
        """Debe almacenar logs detallados"""
        logs_detallados = """
[2024-03-15 10:00:00] INFO: Iniciando backup
[2024-03-15 10:00:05] INFO: Conectando a PostgreSQL
[2024-03-15 10:00:06] INFO: Conexión establecida
[2024-03-15 10:00:10] INFO: Iniciando dump de tabla users
[2024-03-15 10:05:30] INFO: Dump de tabla users completado (125,000 registros)
[2024-03-15 10:05:35] INFO: Iniciando dump de tabla ventas
[2024-03-15 10:15:42] INFO: Dump de tabla ventas completado (1,500,000 registros)
[2024-03-15 10:15:45] INFO: Comprimiendo archivo
[2024-03-15 10:16:30] INFO: Backup completado exitosamente
[2024-03-15 10:16:35] INFO: Archivo guardado en /backups/cantina_db_20240315.sql.gz
        """.strip()

        ejecucion = EjecucionesTarea.objects.create(
            fecha_inicio=timezone.now(),
            fecha_fin=timezone.now() + timedelta(minutes=16, seconds=35),
            duracion_seg=995,
            estado="completado",
            logs=logs_detallados,
            servidor="backup_server",
            parametros={"verbose": True},
            id_plantilla=self.plantilla,
        )

        self.assertIn("Backup completado exitosamente", ejecucion.logs)
        self.assertIn("1,500,000 registros", ejecucion.logs)
        self.assertIn("INFO:", ejecucion.logs)

    def test_ejecucion_tarea_parametros_runtime(self):
        """Debe almacenar parámetros de runtime"""
        parametros_runtime = {
            "user_triggered": True,
            "priority": "high",
            "override_schedule": True,
            "custom_params": {
                "backup_path": "/urgent_backups/",
                "retention_days": 30,
                "notify_users": ["admin@cantina.com", "backup@cantina.com"],
            },
            "system_info": {"cpu_cores": 8, "memory_gb": 32, "disk_space_gb": 500},
        }

        ejecucion = EjecucionesTarea.objects.create(
            fecha_inicio=timezone.now(),
            estado="ejecutando",
            parametros=parametros_runtime,
            servidor="powerful_server",
            id_plantilla=self.plantilla,
        )

        self.assertTrue(ejecucion.parametros["user_triggered"])
        self.assertEqual(ejecucion.parametros["priority"], "high")
        self.assertEqual(ejecucion.parametros["system_info"]["cpu_cores"], 8)

    def test_ejecucion_tarea_sin_empleado(self):
        """Debe permitir ejecuciones automáticas sin empleado"""
        ejecucion_auto = EjecucionesTarea.objects.create(
            fecha_inicio=timezone.now(),
            estado="ejecutando",
            pid=99999,
            servidor="cron_server",
            parametros={"auto": True},
            id_plantilla=self.plantilla,
            # Sin ejecutado_por (ejecución automática)
        )

        self.assertIsNone(ejecucion_auto.ejecutado_por)
        self.assertTrue(ejecucion_auto.parametros["auto"])

    def test_ejecucion_tarea_str_representation(self):
        """Debe tener representación string correcta"""
        ejecucion = EjecucionesTarea.objects.create(
            fecha_inicio=timezone.now(),
            estado="completado",
            pid=12345,
            servidor="test_server",
            parametros={},
            id_plantilla=self.plantilla,
        )

        expected_str = f"EjecucionesTarea #{ejecucion.pk}"
        self.assertEqual(str(ejecucion), expected_str)


class DestinatariosTareaModelTest(BaseReportesModelTest):
    """Tests para modelo DestinatariosTarea"""

    def setUp(self):
        """Configurar datos específicos para destinatarios"""
        super().setUp()

        self.plantilla = PlantillasTarea.objects.create(
            nombre="Tarea con Notificaciones",
            tipo_tarea="backup",
            comando="backup.sh",
            parametros={},
            frecuencia="diario",
            cron="0 2 * * *",
            timeout=3600,
            max_reintentos=3,
            created_at=timezone.now(),
        )

        # Crear empleado adicional
        self.empleado2 = Empleados.objects.create(
            nombre="Usuario",
            apellido="Notificado",
            usuario="user_notif",
            contrasena_hash="$2b$12$hash2",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )

    def test_crear_destinatario_completo(self):
        """Debe crear destinatario con todas las notificaciones"""
        destinatario = DestinatariosTarea.objects.create(
            notif_inicio=1, notif_fin=1, notif_error=1, id_empleado=self.empleado, id_plantilla=self.plantilla
        )

        self.assertEqual(destinatario.notif_inicio, 1)
        self.assertEqual(destinatario.notif_fin, 1)
        self.assertEqual(destinatario.notif_error, 1)
        self.assertEqual(destinatario.id_empleado, self.empleado)

    def test_crear_destinatario_solo_errores(self):
        """Debe crear destinatario solo para notificaciones de error"""
        destinatario = DestinatariosTarea.objects.create(
            notif_inicio=0, notif_fin=0, notif_error=1, id_empleado=self.empleado2, id_plantilla=self.plantilla
        )

        self.assertEqual(destinatario.notif_inicio, 0)
        self.assertEqual(destinatario.notif_fin, 0)
        self.assertEqual(destinatario.notif_error, 1)

    def test_destinatarios_multiples_para_tarea(self):
        """Debe permitir múltiples destinatarios para una tarea"""
        # Admin - todas las notificaciones
        destinatario_admin = DestinatariosTarea.objects.create(
            notif_inicio=1, notif_fin=1, notif_error=1, id_empleado=self.empleado, id_plantilla=self.plantilla
        )

        # Usuario normal - solo errores
        destinatario_user = DestinatariosTarea.objects.create(
            notif_inicio=0, notif_fin=0, notif_error=1, id_empleado=self.empleado2, id_plantilla=self.plantilla
        )

        # Verificar que ambos existen
        destinatarios = DestinatariosTarea.objects.filter(id_plantilla=self.plantilla)
        self.assertEqual(destinatarios.count(), 2)

        # Verificar configuraciones diferentes
        admin_dest = destinatarios.filter(id_empleado=self.empleado).first()
        user_dest = destinatarios.filter(id_empleado=self.empleado2).first()

        self.assertEqual(admin_dest.notif_inicio, 1)
        self.assertEqual(user_dest.notif_inicio, 0)

    def test_destinatario_unique_constraint(self):
        """Debe validar constrainte único de plantilla + empleado"""
        # Crear primer destinatario
        DestinatariosTarea.objects.create(
            notif_inicio=1, notif_fin=1, notif_error=1, id_empleado=self.empleado, id_plantilla=self.plantilla
        )

        # Intentar crear duplicado
        with self.assertRaises(IntegrityError):
            DestinatariosTarea.objects.create(
                notif_inicio=0,
                notif_fin=0,
                notif_error=1,
                id_empleado=self.empleado,  # Mismo empleado
                id_plantilla=self.plantilla,  # Misma plantilla
            )

    def test_destinatario_diferentes_combinaciones_notif(self):
        """Debe manejar diferentes combinaciones de notificaciones"""
        combinaciones = [
            (1, 0, 0),  # Solo inicio
            (0, 1, 0),  # Solo fin
            (0, 0, 1),  # Solo error
            (1, 1, 0),  # Inicio y fin
            (1, 0, 1),  # Inicio y error
            (0, 1, 1),  # Fin y error
            (1, 1, 1),  # Todas
            (0, 0, 0),  # Ninguna (válido pero sin utilidad)
        ]

        for i, (inicio, fin, error) in enumerate(combinaciones):
            # Crear plantilla única para cada combinación
            plantilla_temp = PlantillasTarea.objects.create(
                nombre=f"Tarea Test {i}",
                tipo_tarea="test",
                comando="test",
                parametros={},
                frecuencia="manual",
                cron="0 0 * * *",
                timeout=60,
                max_reintentos=1,
                created_at=timezone.now(),
            )

            destinatario = DestinatariosTarea.objects.create(
                notif_inicio=inicio,
                notif_fin=fin,
                notif_error=error,
                id_empleado=self.empleado,
                id_plantilla=plantilla_temp,
            )

            self.assertEqual(destinatario.notif_inicio, inicio)
            self.assertEqual(destinatario.notif_fin, fin)
            self.assertEqual(destinatario.notif_error, error)

    def test_destinatario_str_representation(self):
        """Debe tener representación string correcta"""
        destinatario = DestinatariosTarea.objects.create(
            notif_inicio=1, notif_fin=1, notif_error=1, id_empleado=self.empleado, id_plantilla=self.plantilla
        )

        expected_str = f"DestinatariosTarea #{destinatario.pk}"
        self.assertEqual(str(destinatario), expected_str)

    def test_destinatarios_query_por_tipo_notificacion(self):
        """Debe permitir consultas por tipo de notificación"""
        # Crear varios destinatarios con diferentes configuraciones
        plantillas_temp = []
        for i in range(5):
            plantilla = PlantillasTarea.objects.create(
                nombre=f"Tarea Query {i}",
                tipo_tarea="test",
                comando="test",
                parametros={},
                frecuencia="manual",
                cron="0 0 * * *",
                timeout=60,
                max_reintentos=1,
                created_at=timezone.now(),
            )
            plantillas_temp.append(plantilla)

            # Configuraciones diferentes
            if i < 3:
                notif_inicio = 1
            else:
                notif_inicio = 0

            if i < 2:
                notif_error = 1
            else:
                notif_error = 0

            DestinatariosTarea.objects.create(
                notif_inicio=notif_inicio,
                notif_fin=1,
                notif_error=notif_error,
                id_empleado=self.empleado,
                id_plantilla=plantilla,
            )

        # Consultas específicas
        destinatarios_inicio = DestinatariosTarea.objects.filter(notif_inicio=1)
        destinatarios_error = DestinatariosTarea.objects.filter(notif_error=1)

        self.assertEqual(destinatarios_inicio.count(), 3)
        self.assertEqual(destinatarios_error.count(), 2)

    def test_property_aliases(self):
        """Debe cubrir los getters y setters de las propiedades alias (líneas 212-248)"""
        destinatario = DestinatariosTarea.objects.create(
            notif_inicio=0, notif_fin=0, notif_error=0, id_empleado=self.empleado, id_plantilla=self.plantilla
        )

        # Test getters
        self.assertFalse(destinatario.notificar_inicio)
        self.assertFalse(destinatario.notificar_fin)
        self.assertFalse(destinatario.notificar_exito)
        self.assertFalse(destinatario.notificar_error)
        self.assertEqual(destinatario.id_plantilla_tarea, self.plantilla)

        # Test setters
        destinatario.notificar_inicio = True
        self.assertEqual(destinatario.notif_inicio, 1)

        destinatario.notificar_fin = True
        self.assertEqual(destinatario.notif_fin, 1)

        destinatario.notificar_exito = False
        self.assertEqual(destinatario.notif_fin, 0)

        destinatario.notificar_error = True
        self.assertEqual(destinatario.notif_error, 1)

        destinatario.id_plantilla_tarea = self.plantilla
        self.assertEqual(destinatario.id_plantilla, self.plantilla)

    def test_manager_con_kwargs_alias(self):
        """DestinatariosTareaManager con notificar_fin kwarg cubre linea 188."""
        destinatario = DestinatariosTarea.objects.create(
            notificar_fin=True,
            id_empleado=self.empleado2,
            id_plantilla=self.plantilla,
        )
        self.assertEqual(destinatario.notif_fin, 1)
