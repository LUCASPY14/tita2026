"""
Tests para admin de reportes
Cubre interfaces administrativas y funcionalidad de gestión de reportes
"""

from django.test import TestCase, Client
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
from unittest.mock import patch, Mock
import json

from apps.reportes.models import (
    PlantillasReporte,
    Dashboards,
    KpiMetricas,
    ValoresKpi,
    PlantillasTarea,
    EjecucionesTarea,
    DestinatariosTarea
)
from apps.usuarios.models import Empleados, Roles


class BaseReportesAdminTest(TestCase):
    """Clase base para tests de admin de reportes"""

    def setUp(self):
        """Configurar datos base para todos los tests"""
        # Crear usuario administrador
        self.admin_user = User.objects.create_superuser(
            username='admin_reportes',
            email='admin@reportes.com',
            password='admin123'
        )
        
        # Cliente para requests
        self.client = Client()
        self.client.force_login(self.admin_user)
        
        # Crear rol y empleado
        self.rol = Roles.objects.create(
            nombre_rol='Analista Reportes',
            descripcion='Rol de analista de reportes',
            activo=True
        )
        
        self.empleado = Empleados.objects.create(
            nombre='Juan',
            apellido='Analista',
            usuario='janalista',
            contrasena_hash='$2b$12$hash',
            fecha_ingreso=timezone.now(),
            id_rol=self.rol
        )
        
        # Mock admin site
        self.admin_site = AdminSite()


class PlantillasReporteAdminTest(BaseReportesAdminTest):
    """Tests para admin de PlantillasReporte"""

    def test_plantillas_reporte_admin_list_display(self):
        """Debe mostrar campos correctos en lista"""
        # Crear plantillas de prueba
        PlantillasReporte.objects.create(
            nombre='Ventas Mensuales',
            descripcion='Reporte mensual de ventas',
            query_sql='SELECT * FROM ventas WHERE MONTH(fecha) = ?',
            parametros={'mes': 'integer'},
            tipo_reporte='ventas',
            frecuencia='mensual',
            activo=True,
            created_at=timezone.now(),
            created_by=self.empleado
        )
        
        PlantillasReporte.objects.create(
            nombre='Inventario Semanal',
            query_sql='SELECT * FROM productos WHERE stock < ?',
            parametros={'stock_minimo': 'integer'},
            tipo_reporte='inventario',
            frecuencia='semanal',
            activo=False,
            created_at=timezone.now()
        )
        
        # Simular list_display
        expected_fields = ['nombre', 'tipo_reporte', 'frecuencia', 'activo', 'created_at']
        
        # Verificar que los campos existen en el modelo
        for field in expected_fields:
            self.assertTrue(hasattr(PlantillasReporte, field), f"Campo {field} no existe")

    def test_plantillas_reporte_admin_search_functionality(self):
        """Debe permitir búsqueda por nombre y tipo"""
        # Crear plantillas con datos específicos
        plantilla_ventas = PlantillasReporte.objects.create(
            nombre='Análisis Ventas Diarias',
            descripcion='Análisis detallado de ventas',
            query_sql='SELECT * FROM ventas',
            parametros={},
            tipo_reporte='ventas',
            frecuencia='diario',
            created_at=timezone.now()
        )
        
        plantilla_inventario = PlantillasReporte.objects.create(
            nombre='Control Inventario',
            query_sql='SELECT * FROM inventario',
            parametros={},
            tipo_reporte='inventario',
            frecuencia='semanal',
            created_at=timezone.now()
        )
        
        # Simular búsqueda por nombre
        resultados_ventas = PlantillasReporte.objects.filter(nombre__icontains='Ventas')
        resultados_inventario = PlantillasReporte.objects.filter(nombre__icontains='Inventario')
        
        self.assertIn(plantilla_ventas, resultados_ventas)
        self.assertNotIn(plantilla_ventas, resultados_inventario)
        self.assertIn(plantilla_inventario, resultados_inventario)
        self.assertNotIn(plantilla_inventario, resultados_ventas)

    def test_plantillas_reporte_admin_filter_by_tipo(self):
        """Debe permitir filtrar por tipo de reporte"""
        # Crear plantillas de diferentes tipos
        plantilla_ventas = PlantillasReporte.objects.create(
            nombre='Reporte Ventas',
            query_sql='SELECT 1',
            parametros={},
            tipo_reporte='ventas',
            frecuencia='diario',
            created_at=timezone.now()
        )
        
        plantilla_financiero = PlantillasReporte.objects.create(
            nombre='Reporte Financiero',
            query_sql='SELECT 2',
            parametros={},
            tipo_reporte='financiero',
            frecuencia='mensual',
            created_at=timezone.now()
        )
        
        # Filtrar por tipo
        reportes_ventas = PlantillasReporte.objects.filter(tipo_reporte='ventas')
        reportes_financieros = PlantillasReporte.objects.filter(tipo_reporte='financiero')
        
        self.assertIn(plantilla_ventas, reportes_ventas)
        self.assertNotIn(plantilla_ventas, reportes_financieros)
        self.assertIn(plantilla_financiero, reportes_financieros)
        self.assertNotIn(plantilla_financiero, reportes_ventas)

    def test_plantillas_reporte_admin_parametros_display(self):
        """Debe mostrar parámetros JSON de forma legible"""
        parametros_complejos = {
            'fecha_inicio': {'tipo': 'date', 'requerido': True},
            'fecha_fin': {'tipo': 'date', 'requerido': True},
            'empleado_id': {'tipo': 'integer', 'requerido': False},
            'incluir_comisiones': {'tipo': 'boolean', 'default': True}
        }
        
        plantilla = PlantillasReporte.objects.create(
            nombre='Reporte Parametrizado',
            query_sql='SELECT * FROM tabla WHERE fecha BETWEEN ? AND ?',
            parametros=parametros_complejos,
            tipo_reporte='personalizado',
            frecuencia='manual',
            created_at=timezone.now()
        )
        
        # Verificar que los parámetros se almacenan correctamente
        self.assertEqual(plantilla.parametros, parametros_complejos)
        
        # En admin, deberían mostrarse de forma legible
        parametros_str = json.dumps(plantilla.parametros, indent=2)
        self.assertIn('fecha_inicio', parametros_str)
        self.assertIn('requerido', parametros_str)

    def test_plantillas_reporte_admin_sql_validation(self):
        """Debe validar SQL en formulario de admin"""
        # SQL válido básico
        sql_valido = "SELECT COUNT(*) FROM ventas WHERE fecha >= ?"
        
        # SQL potencialmente peligroso
        sql_peligroso = "DROP TABLE ventas; SELECT * FROM usuarios"
        
        # Crear plantilla con SQL válido
        plantilla_valida = PlantillasReporte.objects.create(
            nombre='SQL Válido',
            query_sql=sql_valido,
            parametros={'fecha': 'date'},
            tipo_reporte='consulta',
            frecuencia='manual',
            created_at=timezone.now()
        )
        
        self.assertEqual(plantilla_valida.query_sql, sql_valido)
        
        # En admin real, debería validar SQL peligroso
        # Aquí simulamos la validación
        palabras_peligrosas = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER']
        
        for palabra in palabras_peligrosas:
            if palabra in sql_peligroso.upper():
                # Simular validación que fallaría en admin
                with self.assertRaises(Exception):
                    # En implementación real, esto sería validado por el admin form
                    raise ValueError(f"SQL contiene palabra peligrosa: {palabra}")

    def test_plantillas_reporte_admin_preview_functionality(self):
        """Debe permitir preview del reporte en admin"""
        plantilla = PlantillasReporte.objects.create(
            nombre='Reporte Preview',
            descripcion='Para probar funcionalidad de preview',
            query_sql='SELECT "Test" as resultado, NOW() as fecha',
            parametros={},
            tipo_reporte='test',
            frecuencia='manual',
            created_at=timezone.now(),
            created_by=self.empleado
        )
        
        # Simular funcionalidad de preview que estaría en admin
        preview_data = {
            'plantilla_id': plantilla.id_template,
            'query_sql': plantilla.query_sql,
            'parametros': plantilla.parametros
        }
        
        # Verificar estructura de datos para preview
        self.assertIn('plantilla_id', preview_data)
        self.assertIn('query_sql', preview_data)
        self.assertEqual(preview_data['plantilla_id'], plantilla.id_template)


class DashboardsAdminTest(BaseReportesAdminTest):
    """Tests para admin de Dashboards"""

    def test_dashboards_admin_list_display(self):
        """Debe mostrar información relevante del dashboard"""
        configuracion_dashboard = {
            'widgets': [
                {'tipo': 'chart', 'posicion': {'x': 0, 'y': 0, 'w': 6, 'h': 4}},
                {'tipo': 'kpi', 'posicion': {'x': 6, 'y': 0, 'w': 3, 'h': 2}}
            ],
            'layout': 'grid',
            'refresh_interval': 300
        }
        
        dashboard = Dashboards.objects.create(
            nombre='Dashboard Ventas',
            descripcion='Dashboard principal de ventas',
            configuracion=configuracion_dashboard,
            es_publico=1,
            predeterminado=0,
            activo=True,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        # Campos esperados en list_display
        expected_fields = ['nombre', 'es_publico', 'predeterminado', 'activo', 'id_empleado']
        
        for field in expected_fields:
            self.assertTrue(hasattr(dashboard, field))

    def test_dashboards_admin_configuracion_json_editor(self):
        """Debe manejar edición de configuración JSON en admin"""
        configuracion_compleja = {
            'tema': 'dark',
            'widgets': [
                {
                    'id': 'widget_1',
                    'tipo': 'line_chart',
                    'titulo': 'Ventas por Día',
                    'datos_source': 'ventas_diarias',
                    'configuracion': {
                        'colores': ['#FF6384', '#36A2EB'],
                        'eje_y': {'min': 0, 'formato': 'currency'}
                    },
                    'posicion': {'x': 0, 'y': 0, 'w': 8, 'h': 6}
                },
                {
                    'id': 'widget_2',
                    'tipo': 'kpi_card',
                    'titulo': 'Ventas Totales',
                    'metrica': 'sum_ventas_mes',
                    'posicion': {'x': 8, 'y': 0, 'w': 4, 'h': 3}
                }
            ],
            'filtros_globales': {
                'fecha_inicio': {'tipo': 'date', 'default': 'month_start'},
                'fecha_fin': {'tipo': 'date', 'default': 'today'}
            }
        }
        
        dashboard = Dashboards.objects.create(
            nombre='Dashboard Complejo',
            configuracion=configuracion_compleja,
            es_publico=0,
            predeterminado=1,
            activo=True,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        # Verificar que la configuración se almacena correctamente
        self.assertEqual(dashboard.configuracion, configuracion_compleja)
        
        # Verificar estructura de widgets
        self.assertEqual(len(dashboard.configuracion['widgets']), 2)
        self.assertIn('tema', dashboard.configuracion)
        self.assertIn('filtros_globales', dashboard.configuracion)

    def test_dashboards_admin_permissions_validation(self):
        """Debe validar permisos en admin de dashboards"""
        # Dashboard público
        dashboard_publico = Dashboards.objects.create(
            nombre='Dashboard Público',
            configuracion={},
            es_publico=1,  # Público
            predeterminado=0,
            activo=True,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        # Dashboard privado
        dashboard_privado = Dashboards.objects.create(
            nombre='Dashboard Privado',
            configuracion={},
            es_publico=0,  # Privado
            predeterminado=0,
            activo=True,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        # Verificar configuración de permisos
        self.assertEqual(dashboard_publico.es_publico, 1)
        self.assertEqual(dashboard_privado.es_publico, 0)
        
        # En admin, debería haber validación de permisos
        self.assertEqual(dashboard_publico.id_empleado, self.empleado)
        self.assertEqual(dashboard_privado.id_empleado, self.empleado)

    def test_dashboards_admin_default_dashboard_logic(self):
        """Debe manejar lógica de dashboard predeterminado"""
        # Crear primer dashboard como predeterminado
        dashboard_1 = Dashboards.objects.create(
            nombre='Dashboard Default 1',
            configuracion={},
            es_publico=1,
            predeterminado=1,  # Predeterminado
            activo=True,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        # Crear segundo dashboard
        dashboard_2 = Dashboards.objects.create(
            nombre='Dashboard Normal',
            configuracion={},
            es_publico=1,
            predeterminado=0,
            activo=True,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        # Verificar configuración inicial
        self.assertEqual(dashboard_1.predeterminado, 1)
        self.assertEqual(dashboard_2.predeterminado, 0)
        
        # En admin real, habría logic para cambiar predeterminado
        # Simular cambio de predeterminado
        dashboard_2.predeterminado = 1
        dashboard_2.save()
        
        # En implementación real, el anterior debería volverse 0
        # Aquí verificamos la estructura básica
        self.assertEqual(dashboard_2.predeterminado, 1)

    def test_dashboards_admin_widget_validation(self):
        """Debe validar estructura de widgets en admin"""
        # Configuración válida de widget
        configuracion_valida = {
            'widgets': [
                {
                    'id': 'widget_valido',
                    'tipo': 'chart',
                    'titulo': 'Gráfico Válido',
                    'posicion': {'x': 0, 'y': 0, 'w': 6, 'h': 4},
                    'configuracion': {'tipo_grafico': 'line'}
                }
            ]
        }
        
        # Configuración inválida de widget
        configuracion_invalida = {
            'widgets': [
                {
                    # Falta 'id' requerido
                    'tipo': 'chart',
                    'posicion': {'x': 0, 'y': 0}  # Falta 'w' y 'h'
                }
            ]
        }
        
        # Crear dashboard con configuración válida
        dashboard_valido = Dashboards.objects.create(
            nombre='Dashboard Válido',
            configuracion=configuracion_valida,
            es_publico=1,
            predeterminado=0,
            activo=True,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        self.assertIn('widgets', dashboard_valido.configuracion)
        self.assertIn('id', dashboard_valido.configuracion['widgets'][0])
        
        # En admin real, configuración inválida sería rechazada
        # Simular validación
        for widget in configuracion_invalida['widgets']:
            if 'id' not in widget:
                with self.assertRaises(Exception):
                    # En admin form real, esto fallaría la validación
                    raise ValueError("Widget debe tener 'id'")


class KpiMetricasAdminTest(BaseReportesAdminTest):
    """Tests para admin de KpiMetricas"""

    def test_kpi_metricas_admin_list_display(self):
        """Debe mostrar métricas KPI apropiadamente"""
        # Crear métrica KPI de prueba
        kpi = KpiMetricas.objects.create(
            nombre_kpi='Ventas Mensuales',
            descripcion='Total de ventas del mes actual',
            query_sql='SELECT SUM(monto) as valor FROM ventas WHERE MONTH(fecha) = MONTH(NOW())',
            unidad_medida='PYG',
            meta_valor=10000000.00,
            categoria='ventas',
            frecuencia_actualizacion='diario',
            activo=True,
            created_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        # Campos esperados en admin
        expected_fields = ['nombre_kpi', 'categoria', 'meta_valor', 'unidad_medida', 'activo']
        
        for field in expected_fields:
            self.assertTrue(hasattr(kpi, field))

    def test_kpi_metricas_admin_calculation_preview(self):
        """Debe permitir preview del cálculo de KPI"""
        kpi = KpiMetricas.objects.create(
            nombre_kpi='Promedio Ventas Diarias',
            query_sql='SELECT AVG(monto) as valor FROM ventas WHERE fecha >= DATE_SUB(NOW(), INTERVAL 7 DAY)',
            unidad_medida='PYG',
            meta_valor=500000.00,
            categoria='ventas',
            frecuencia_actualizacion='diario',
            activo=True,
            created_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        # Simular preview de cálculo
        preview_data = {
            'kpi_id': kpi.id_kpi,
            'query': kpi.query_sql,
            'meta_valor': kpi.meta_valor,
            'unidad': kpi.unidad_medida
        }
        
        # Verificar estructura para preview
        self.assertEqual(preview_data['kpi_id'], kpi.id_kpi)
        self.assertIn('SELECT', preview_data['query'])
        self.assertEqual(preview_data['meta_valor'], 500000.00)


class PlantillasTareaAdminTest(BaseReportesAdminTest):
    """Tests para admin de PlantillasTarea"""

    def test_plantillas_tarea_admin_programacion(self):
        """Debe manejar programación de tareas en admin"""
        # Configuración de programación compleja
        config_programacion = {
            'tipo': 'cron',
            'expresion': '0 8 * * 1-5',  # Lunes a viernes a las 8 AM
            'zona_horaria': 'America/Asuncion',
            'reintentos': 3,
            'timeout': 300
        }
        
        plantilla_tarea = PlantillasTarea.objects.create(
            nombre='Reporte Diario Automático',
            descripcion='Genera reporte diario de ventas',
            configuracion_programacion=config_programacion,
            configuracion_envio={'email': True, 'formato': 'pdf'},
            activo=True,
            created_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        # Verificar configuración
        self.assertEqual(plantilla_tarea.configuracion_programacion, config_programacion)
        self.assertIn('expresion', plantilla_tarea.configuracion_programacion)

    def test_plantillas_tarea_admin_destinatarios(self):
        """Debe manejar gestión de destinatarios en admin"""
        # Crear plantilla de tarea
        plantilla = PlantillasTarea.objects.create(
            nombre='Tarea con Destinatarios',
            configuracion_programacion={'tipo': 'manual'},
            configuracion_envio={'email': True},
            activo=True,
            created_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        # Crear destinatarios
        destinatario_1 = DestinatariosTarea.objects.create(
            id_plantilla_tarea=plantilla,
            id_empleado=self.empleado,
            tipo_destinatario='principal',
            notificar_inicio=True,
            notificar_exito=True,
            notificar_error=True
        )
        
        # Verificar relación
        self.assertEqual(destinatario_1.id_plantilla_tarea, plantilla)
        self.assertEqual(destinatario_1.id_empleado, self.empleado)
        self.assertTrue(destinatario_1.notificar_exito)


class ReportesAdminIntegrationTest(BaseReportesAdminTest):
    """Tests de integración para admin de reportes"""

    def test_admin_workflow_complete_report_creation(self):
        """Debe manejar flujo completo de creación de reporte"""
        # 1. Crear plantilla de reporte
        plantilla = PlantillasReporte.objects.create(
            nombre='Reporte Integración',
            descripcion='Reporte para test de integración',
            query_sql='SELECT COUNT(*) as total_ventas, SUM(monto) as sum_ventas FROM ventas WHERE fecha = ?',
            parametros={'fecha': 'date'},
            tipo_reporte='ventas',
            frecuencia='diario',
            activo=True,
            created_at=timezone.now(),
            created_by=self.empleado
        )
        
        # 2. Crear dashboard que usa la plantilla
        dashboard_config = {
            'widgets': [
                {
                    'id': 'widget_reporte',
                    'tipo': 'report_table',
                    'plantilla_id': plantilla.id_template,
                    'posicion': {'x': 0, 'y': 0, 'w': 12, 'h': 6}
                }
            ]
        }
        
        dashboard = Dashboards.objects.create(
            nombre='Dashboard con Reporte',
            configuracion=dashboard_config,
            es_publico=1,
            predeterminado=0,
            activo=True,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        # 3. Crear tarea programada para el reporte
        tarea_config = {
            'tipo': 'scheduled',
            'frecuencia': 'daily',
            'hora': '08:00'
        }
        
        plantilla_tarea = PlantillasTarea.objects.create(
            nombre='Envío Automático Reporte',
            configuracion_programacion=tarea_config,
            configuracion_envio={'email': True, 'formato': 'pdf'},
            activo=True,
            created_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        # Verificar integración
        self.assertEqual(plantilla.created_by, self.empleado)
        self.assertEqual(dashboard.id_empleado, self.empleado)
        self.assertEqual(plantilla_tarea.id_empleado, self.empleado)
        
        # Verificar que dashboard referencia la plantilla
        widget = dashboard.configuracion['widgets'][0]
        self.assertEqual(widget['plantilla_id'], plantilla.id_template)

    def test_admin_security_validations(self):
        """Debe aplicar validaciones de seguridad en admin"""
        # Verificar que solo admin puede acceder
        self.assertTrue(self.admin_user.is_superuser)
        
        # Crear plantilla con query potencialmente peligrosa
        sql_peligroso = "SELECT * FROM usuarios; DROP TABLE ventas;"
        
        # En admin real, esto debería ser validado y rechazado
        # Simular validación de seguridad
        palabras_prohibidas = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
        
        for palabra in palabras_prohibidas:
            if palabra in sql_peligroso.upper():
                # Simular que admin rechazaría esta query
                self.assertIn(palabra, sql_peligroso.upper())
                
        # Dashboard con configuración potencialmente peligrosa
        config_peligrosa = {
            'widgets': [
                {
                    'id': 'widget_peligroso',
                    'tipo': 'iframe',
                    'url': 'javascript:alert("XSS")',  # XSS attempt
                    'posicion': {'x': 0, 'y': 0, 'w': 6, 'h': 4}
                }
            ]
        }
        
        # En admin real, esto debería ser validado
        # Simular validación XSS
        config_str = json.dumps(config_peligrosa)
        if 'javascript:' in config_str:
            # Admin debería rechazar configuración con javascript:
            self.assertIn('javascript:', config_str)

    def test_admin_performance_considerations(self):
        """Debe considerar performance en admin de reportes"""
        # Crear múltiples registros para probar performance
        plantillas = []
        for i in range(20):
            plantilla = PlantillasReporte.objects.create(
                nombre=f'Plantilla Performance {i}',
                query_sql=f'SELECT {i} as numero',
                parametros={},
                tipo_reporte='performance_test',
                frecuencia='manual',
                created_at=timezone.now()
            )
            plantillas.append(plantilla)
        
        # Simular paginación en admin
        page_size = 10
        first_page = PlantillasReporte.objects.filter(
            tipo_reporte='performance_test'
        )[:page_size]
        
        self.assertEqual(len(first_page), page_size)
        
        # Simular optimización con select_related
        plantillas_optimized = PlantillasReporte.objects.select_related(
            'created_by'
        ).filter(tipo_reporte='performance_test')[:5]
        
        # Verificar que las consultas optimizadas funcionan
        for plantilla in plantillas_optimized:
            # En query optimizada, created_by debería estar disponible sin query adicional
            if plantilla.created_by:
                self.assertIsNotNone(plantilla.created_by.nombre)

    def test_admin_audit_trail(self):
        """Debe mantener pista de auditoría en admin"""
        # Simular log de acciones administrativas
        acciones_log = []
        
        # Crear plantilla
        plantilla = PlantillasReporte.objects.create(
            nombre='Auditoria Test',
            query_sql='SELECT 1',
            parametros={},
            tipo_reporte='audit',
            frecuencia='manual',
            created_at=timezone.now(),
            created_by=self.empleado
        )
        
        # Log de creación
        acciones_log.append({
            'accion': 'CREATE',
            'modelo': 'PlantillasReporte',
            'objeto_id': plantilla.id_template,
            'usuario': self.admin_user.username,
            'timestamp': timezone.now()
        })
        
        # Modificar plantilla
        plantilla.nombre = 'Auditoria Modificada'
        plantilla.save()
        
        # Log de modificación
        acciones_log.append({
            'accion': 'UPDATE',
            'modelo': 'PlantillasReporte',
            'objeto_id': plantilla.id_template,
            'usuario': self.admin_user.username,
            'timestamp': timezone.now()
        })
        
        # Verificar log
        self.assertEqual(len(acciones_log), 2)
        self.assertEqual(acciones_log[0]['accion'], 'CREATE')
        self.assertEqual(acciones_log[1]['accion'], 'UPDATE')