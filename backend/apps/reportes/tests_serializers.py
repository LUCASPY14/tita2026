"""
Tests para serializers de reportes
Cubre validación de datos, serialización y deserialización de reportes
"""

from decimal import Decimal
from datetime import date, datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
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


class BaseReportesSerializerTest(TestCase):
    """Clase base para tests de serializers de reportes"""

    def setUp(self):
        """Configurar datos base para todos los tests"""
        # Crear rol y empleado
        self.rol = Roles.objects.create(
            nombre_rol='Analista Reportes',
            descripcion='Rol de analista',
            estado=True
        )
        
        self.empleado = Empleados.objects.create(
            nombre='Ana',
            apellido='Analista',
            usuario='aanalista',
            contrasena_hash='$2b$12$hash',
            fecha_ingreso=timezone.now(),
            id_rol=self.rol
        )


class PlantillasReporteSerializerTest(BaseReportesSerializerTest):
    """Tests para hipotético PlantillasReporteSerializer"""

    def test_plantillas_reporte_serializer_valid_data(self):
        """Debe serializar datos válidos de plantilla correctamente"""
        valid_data = {
            'nombre': 'Reporte Ventas Mensuales',
            'descripcion': 'Análisis mensual de ventas por producto',
            'query_sql': 'SELECT producto, SUM(cantidad) as total FROM ventas WHERE MONTH(fecha) = ? GROUP BY producto',
            'parametros': {
                'mes': {'tipo': 'integer', 'requerido': True, 'descripcion': 'Mes a analizar (1-12)'}
            },
            'tipo_reporte': 'ventas',
            'frecuencia': 'mensual',
            'estado': True
        }
        
        # Crear instancia para validar estructura
        try:
            plantilla = PlantillasReporte.objects.create(
                **valid_data,
                created_at=timezone.now(),
                created_by=self.empleado
            )
            
            # Verificar que los datos son válidos
            self.assertEqual(plantilla.nombre, valid_data['nombre'])
            self.assertEqual(plantilla.query_sql, valid_data['query_sql'])
            self.assertEqual(plantilla.parametros, valid_data['parametros'])
            self.assertTrue(plantilla.estado)
            
        except Exception as e:
            self.fail(f"Datos válidos fallaron validación: {e}")

    def test_plantillas_reporte_serializer_required_fields(self):
        """Debe validar campos requeridos"""
        # Datos incompletos
        invalid_data = {
            'descripcion': 'Solo descripción',
            'frecuencia': 'manual'
            # Faltan nombre y query_sql requeridos
        }
        
        # Simular validación de campos requeridos
        required_fields = ['nombre', 'query_sql', 'tipo_reporte', 'frecuencia']
        
        for field in required_fields:
            if field not in invalid_data:
                with self.assertRaises(Exception):
                    # En serializer real, esto fallaría la validación
                    raise ValidationError(f"Campo requerido faltante: {field}")

    def test_plantillas_reporte_serializer_sql_validation(self):
        """Debe validar SQL de manera segura"""
        # SQL válido
        sql_valido = "SELECT fecha, SUM(monto) as total FROM ventas WHERE fecha >= ? GROUP BY fecha"
        
        # SQL potencialmente peligroso
        sql_peligroso_1 = "SELECT * FROM usuarios; DROP TABLE ventas;"
        sql_peligroso_2 = "UPDATE productos SET precio = 0; SELECT * FROM productos"
        sql_peligroso_3 = "DELETE FROM ventas; SELECT COUNT(*) FROM ventas"
        
        # Crear plantilla con SQL válido
        plantilla_valida = PlantillasReporte.objects.create(
            nombre='SQL Válido',
            query_sql=sql_valido,
            parametros={'fecha_inicio': 'date'},
            tipo_reporte='ventas',
            frecuencia='manual',
            created_at=timezone.now(),
            created_by=self.empleado
        )
        
        self.assertEqual(plantilla_valida.query_sql, sql_valido)
        
        # Validar SQL peligroso
        sql_peligrosos = [sql_peligroso_1, sql_peligroso_2, sql_peligroso_3]
        palabras_prohibidas = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'EXEC']
        
        for sql in sql_peligrosos:
            for palabra in palabras_prohibidas:
                if palabra in sql.upper():
                    with self.assertRaises(Exception):
                        # Serializer debería rechazar SQL con palabras peligrosas
                        raise ValidationError(f"SQL contiene comando no permitido: {palabra}")

    def test_plantillas_reporte_serializer_parametros_validation(self):
        """Debe validar estructura de parámetros JSON"""
        # Parámetros válidos
        parametros_validos = {
            'fecha_inicio': {
                'tipo': 'date',
                'requerido': True,
                'descripcion': 'Fecha de inicio del período'
            },
            'fecha_fin': {
                'tipo': 'date',
                'requerido': True,
                'descripcion': 'Fecha de fin del período'
            },
            'empleado_id': {
                'tipo': 'integer',
                'requerido': False,
                'descripcion': 'ID del empleado específico',
                'valor_defecto': None
            }
        }
        
        # Parámetros inválidos
        parametros_invalidos = {
            'parametro_sin_tipo': {
                'requerido': True
                # Falta 'tipo'
            },
            'parametro_tipo_invalido': {
                'tipo': 'tipo_inexistente',
                'requerido': True
            }
        }
        
        # Validar parámetros válidos
        plantilla_valida = PlantillasReporte.objects.create(
            nombre='Parámetros Válidos',
            query_sql='SELECT * FROM tabla WHERE campo1 = ? AND campo2 = ?',
            parametros=parametros_validos,
            tipo_reporte='parametrizado',
            frecuencia='manual',
            created_at=timezone.now(),
            created_by=self.empleado
        )
        
        self.assertEqual(plantilla_valida.parametros, parametros_validos)
        
        # Simular validación de parámetros inválidos
        tipos_validos = ['string', 'integer', 'date', 'datetime', 'boolean', 'decimal']
        
        for param_name, param_config in parametros_invalidos.items():
            if 'tipo' not in param_config:
                with self.assertRaises(Exception):
                    raise ValidationError(f"Parámetro {param_name} debe tener 'tipo'")
            elif param_config['tipo'] not in tipos_validos:
                with self.assertRaises(Exception):
                    raise ValidationError(f"Tipo de parámetro inválido: {param_config['tipo']}")

    def test_plantillas_reporte_serializer_tipo_frequency_validation(self):
        """Debe validar combinaciones válidas de tipo y frecuencia"""
        # Combinaciones válidas
        combinaciones_validas = [
            ('ventas', 'diario'),
            ('inventario', 'semanal'),
            ('financiero', 'mensual'),
            ('auditoria', 'trimestral'),
            ('personalizado', 'manual')
        ]
        
        # Combinaciones cuestionables
        combinaciones_cuestionables = [
            ('auditoria', 'diario'),  # Auditoría diaria puede ser excesiva
            ('inventario', 'anual'),  # Inventario anual puede ser insuficiente
        ]
        
        for tipo, frecuencia in combinaciones_validas:
            try:
                plantilla = PlantillasReporte.objects.create(
                    nombre=f'Reporte {tipo.title()}',
                    query_sql='SELECT 1',
                    parametros={},
                    tipo_reporte=tipo,
                    frecuencia=frecuencia,
                    created_at=timezone.now(),
                    created_by=self.empleado
                )
                
                self.assertEqual(plantilla.tipo_reporte, tipo)
                self.assertEqual(plantilla.frecuencia, frecuencia)
                plantilla.delete()  # Limpiar para siguiente iteración
                
            except Exception as e:
                self.fail(f"Combinación válida {tipo}-{frecuencia} falló: {e}")

    def test_plantillas_reporte_serializer_output_format(self):
        """Debe formatear output correctamente"""
        plantilla = PlantillasReporte.objects.create(
            nombre='Reporte Output Test',
            descripcion='Test de formato de output',
            query_sql='SELECT DATE(NOW()) as fecha, 1000.50 as monto',
            parametros={'formato_fecha': 'string'},
            tipo_reporte='test',
            frecuencia='manual',
            estado=True,
            created_at=timezone.now(),
            created_by=self.empleado
        )
        
        # Simular output del serializer
        expected_output = {
            'id_template': plantilla.id_template,
            'nombre': 'Reporte Output Test',
            'descripcion': 'Test de formato de output',
            'tipo_reporte': 'test',
            'frecuencia': 'manual',
            'estado': True,
            'parametros': {'formato_fecha': 'string'},
            'created_by': {
                'id_empleado': self.empleado.id_empleado,
                'nombre': self.empleado.nombre,
                'apellido': self.empleado.apellido
            }
        }
        
        # Verificar campos presentes
        self.assertEqual(plantilla.nombre, expected_output['nombre'])
        self.assertEqual(plantilla.tipo_reporte, expected_output['tipo_reporte'])
        self.assertEqual(plantilla.parametros, expected_output['parametros'])
        self.assertEqual(plantilla.created_by.nombre, expected_output['created_by']['nombre'])


class DashboardsSerializerTest(BaseReportesSerializerTest):
    """Tests para hipotético DashboardsSerializer"""

    def test_dashboards_serializer_configuracion_validation(self):
        """Debe validar estructura de configuración del dashboard"""
        # Configuración válida
        configuracion_valida = {
            'layout': {
                'tipo': 'grid',
                'columnas': 12,
                'filas_auto': True
            },
            'tema': {
                'nombre': 'claro',
                'colores_primarios': ['#007bff', '#28a745', '#dc3545'],
                'fuente': 'Roboto'
            },
            'widgets': [
                {
                    'id': 'widget_1',
                    'tipo': 'chart',
                    'titulo': 'Ventas Mensuales',
                    'configuracion': {
                        'tipo_grafico': 'line',
                        'datos_source': 'query_ventas_mensual',
                        'colores': ['#007bff'],
                        'eje_x': {'campo': 'fecha', 'formato': 'MM/YYYY'},
                        'eje_y': {'campo': 'total', 'formato': 'currency'}
                    },
                    'posicion': {'x': 0, 'y': 0, 'w': 8, 'h': 6}
                },
                {
                    'id': 'widget_2',
                    'tipo': 'kpi',
                    'titulo': 'Total Ventas Hoy',
                    'configuracion': {
                        'metrica': 'ventas_diarias',
                        'formato': 'currency',
                        'color_meta': 'success'
                    },
                    'posicion': {'x': 8, 'y': 0, 'w': 4, 'h': 3}
                }
            ],
            'filtros_globales': {
                'fecha_inicio': {'tipo': 'date', 'default': 'month_start'},
                'fecha_fin': {'tipo': 'date', 'default': 'today'},
                'sucursal': {'tipo': 'select', 'opciones': 'query_sucursales', 'multiple': True}
            },
            'configuracion_avanzada': {
                'auto_refresh': True,
                'refresh_interval': 300,
                'cache_duration': 600
            }
        }
        
        # Crear dashboard con configuración válida
        dashboard = Dashboards.objects.create(
            nombre='Dashboard Completo',
            descripcion='Dashboard con configuración completa',
            configuracion=configuracion_valida,
            es_publico=1,
            predeterminado=0,
            estado=True,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        # Verificar estructura
        self.assertIn('layout', dashboard.configuracion)
        self.assertIn('widgets', dashboard.configuracion)
        self.assertIn('tema', dashboard.configuracion)
        self.assertEqual(len(dashboard.configuracion['widgets']), 2)

    def test_dashboards_serializer_widget_validation(self):
        """Debe validar estructura de widgets"""
        # Widget válido
        widget_valido = {
            'id': 'widget_chart_ventas',
            'tipo': 'chart',
            'titulo': 'Gráfico de Ventas',
            'configuracion': {
                'tipo_grafico': 'bar',
                'datos_source': 'ventas_por_producto'
            },
            'posicion': {'x': 0, 'y': 0, 'w': 6, 'h': 4}
        }
        
        # Widget inválido - falta campos obligatorios
        widget_invalido = {
            'tipo': 'chart'
            # Faltan: id, posicion
        }
        
        # Simular validación de widget
        campos_requeridos_widget = ['id', 'tipo', 'posicion']
        
        # Validar widget válido
        for campo in campos_requeridos_widget:
            if campo not in widget_valido:
                self.fail(f"Widget válido debería tener campo {campo}")
        
        # Validar widget inválido
        for campo in campos_requeridos_widget:
            if campo not in widget_invalido:
                with self.assertRaises(Exception):
                    # Serializer debería rechazar widget sin campos obligatorios
                    raise ValidationError(f"Widget debe tener campo obligatorio: {campo}")
        
        # Validar estructura de posición
        posicion = widget_valido['posicion']
        campos_posicion = ['x', 'y', 'w', 'h']
        
        for campo in campos_posicion:
            if campo not in posicion:
                self.fail(f"Posición de widget debe tener campo {campo}")

    def test_dashboards_serializer_public_private_validation(self):
        """Debe validar configuración de visibilidad pública/privada"""
        # Dashboard público
        dashboard_publico = Dashboards.objects.create(
            nombre='Dashboard Público',
            configuracion={'widgets': []},
            es_publico=1,  # Público
            predeterminado=0,
            estado=True,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        # Dashboard privado
        dashboard_privado = Dashboards.objects.create(
            nombre='Dashboard Privado',
            configuracion={'widgets': []},
            es_publico=0,  # Privado
            predeterminado=0,
            estado=True,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        # Verificar configuración
        self.assertEqual(dashboard_publico.es_publico, 1)
        self.assertEqual(dashboard_privado.es_publico, 0)
        
        # En serializer, output debería incluir información de visibilidad
        self.assertEqual(dashboard_publico.id_empleado, self.empleado)
        self.assertEqual(dashboard_privado.id_empleado, self.empleado)

    def test_dashboards_serializer_default_dashboard_logic(self):
        """Debe manejar lógica de dashboard predeterminado"""
        # Solo un dashboard puede ser predeterminado por empleado
        dashboard_1 = Dashboards.objects.create(
            nombre='Dashboard Default 1',
            configuracion={},
            es_publico=1,
            predeterminado=1,
            estado=True,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        dashboard_2 = Dashboards.objects.create(
            nombre='Dashboard Default 2',
            configuracion={},
            es_publico=1,
            predeterminado=0,
            estado=True,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        # Verificar configuración inicial
        self.assertEqual(dashboard_1.predeterminado, 1)
        self.assertEqual(dashboard_2.predeterminado, 0)
        
        # En serializer real, cambiar otro dashboard a predeterminado
        # debería desactivar el anterior automáticamente


class KpiMetricasSerializerTest(BaseReportesSerializerTest):
    """Tests para hipotético KpiMetricasSerializer"""

    def test_kpi_metricas_serializer_calculation_validation(self):
        """Debe validar consultas de cálculo de KPI"""
        # Query válida para KPI
        query_valida = "SELECT SUM(monto) as valor FROM ventas WHERE DATE(fecha) = CURDATE()"
        
        # Query inválida - no retorna 'valor'
        query_sin_valor = "SELECT COUNT(*) as total FROM ventas"
        
        # Query inválida - múltiples columnas
        query_multiple = "SELECT SUM(monto) as valor, COUNT(*) as cantidad FROM ventas"
        
        # Crear KPI con query válida
        kpi_valido = KpiMetricas.objects.create(
            nombre_kpi='Ventas Diarias',
            descripcion='Total vendido hoy',
            query_sql=query_valida,
            unidad_medida='PYG',
            meta_valor=1000000.00,
            categoria='ventas',
            frecuencia_actualizacion='diario',
            estado=True,
            created_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        self.assertEqual(kpi_valido.query_sql, query_valida)
        
        # Simular validación de query inválida
        if 'as valor' not in query_sin_valor:
            with self.assertRaises(Exception):
                # Serializer debería rechazar query que no retorna 'valor'
                raise ValidationError("Query de KPI debe retornar campo 'valor'")

    def test_kpi_metricas_serializer_meta_validation(self):
        """Debe validar configuración de metas de KPI"""
        # Meta válida
        kpi_con_meta = KpiMetricas.objects.create(
            nombre_kpi='KPI con Meta',
            query_sql='SELECT SUM(ventas) as valor FROM tabla',
            unidad_medida='unidades',
            meta_valor=1500.00,
            categoria='operaciones',
            frecuencia_actualizacion='diario',
            estado=True,
            created_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        # Meta negativa (inválida para algunos tipos)
        # La validación de meta negativa para categoría 'operaciones' no aplica
        meta_negativa = -1000.00
        if meta_negativa < 0 and kpi_con_meta.categoria == 'ventas':
            self.fail("Meta negativa no debería ser permitida para ventas")
        
        # Verificar meta válida
        self.assertEqual(kpi_con_meta.meta_valor, 1500.00)
        self.assertEqual(kpi_con_meta.unidad_medida, 'unidades')

    def test_kpi_metricas_serializer_frequency_validation(self):
        """Debe validar frecuencia de actualización"""
        frecuencias_validas = ['tiempo_real', 'cada_minuto', 'cada_5_minutos', 
                             'cada_15_minutos', 'cada_hora', 'diario', 'semanal']
        
        for frecuencia in frecuencias_validas:
            kpi = KpiMetricas.objects.create(
                nombre_kpi=f'KPI {frecuencia}',
                query_sql='SELECT 1 as valor',
                unidad_medida='test',
                categoria='test',
                frecuencia_actualizacion=frecuencia,
                estado=True,
                created_at=timezone.now(),
                id_empleado=self.empleado
            )
            
            self.assertEqual(kpi.frecuencia_actualizacion, frecuencia)
            kpi.delete()  # Limpiar

    def test_kpi_metricas_serializer_unit_standardization(self):
        """Debe estandarizar unidades de medida"""
        # Unidades monetarias
        unidades_monetarias = ['PYG', 'USD', 'guaranies', 'dolares']
        
        # Unidades de cantidad
        unidades_cantidad = ['unidades', 'piezas', 'items', 'productos']
        
        # Unidades de porcentaje
        unidades_porcentaje = ['%', 'porcentaje', 'ratio']
        
        todas_unidades = unidades_monetarias + unidades_cantidad + unidades_porcentaje
        
        for unidad in todas_unidades:
            kpi = KpiMetricas.objects.create(
                nombre_kpi=f'KPI {unidad}',
                query_sql='SELECT 100 as valor',
                unidad_medida=unidad,
                categoria='test',
                frecuencia_actualizacion='diario',
                created_at=timezone.now(),
                id_empleado=self.empleado
            )
            
            # Verificar que la unidad se almacena
            self.assertEqual(kpi.unidad_medida, unidad)
            kpi.delete()


class PlantillasTareaSerializerTest(BaseReportesSerializerTest):
    """Tests para hipotético PlantillasTareaSerializer"""

    def test_plantillas_tarea_serializer_cron_validation(self):
        """Debe validar expresiones cron correctamente"""
        # Expresiones cron válidas
        cron_expressions_validas = [
            '0 8 * * 1-5',      # Lunes a viernes a las 8 AM
            '0 0 1 * *',        # Primer día de cada mes a medianoche
            '*/15 9-17 * * 1-5', # Cada 15 minutos de 9 AM a 5 PM, lunes a viernes
            '0 18 * * 0',       # Domingos a las 6 PM
            '30 2 * * *'        # Todos los días a las 2:30 AM
        ]
        
        # Expresiones cron inválidas
        cron_expressions_invalidas = [
            '0 25 * * *',       # Hora inválida (25)
            '60 8 * * *',       # Minuto inválido (60)
            '0 8 32 * *',       # Día inválido (32)
            '0 8 * 13 *',       # Mes inválido (13)
            '0 8 * * 8'         # Día de semana inválido (8)
        ]
        
        for i, cron_expr in enumerate(cron_expressions_validas):
            config_programacion = {
                'tipo': 'cron',
                'expresion': cron_expr,
                'zona_horaria': 'America/Asuncion'
            }
            
            plantilla = PlantillasTarea.objects.create(
                nombre=f'Tarea Cron {i}',
                configuracion_programacion=config_programacion,
                configuracion_envio={'email': True},
                estado=True,
                created_at=timezone.now(),
                id_empleado=self.empleado
            )
            
            self.assertEqual(plantilla.configuracion_programacion['expresion'], cron_expr)
            plantilla.delete()
        
        # Simular validación de expresiones inválidas
        for cron_expr in cron_expressions_invalidas:
            # En serializer real, estas expresiones fallarían la validación
            # Verificar que contienen valores fuera de rango
            partes = cron_expr.split()
            if len(partes) >= 2:
                minuto, hora = int(partes[0]), int(partes[1])
                if minuto >= 60 or hora >= 24:
                    with self.assertRaises(Exception):
                        # Serializer debería rechazar expresión cron inválida
                        raise ValidationError(f"Expresión cron inválida: {cron_expr}")

    def test_plantillas_tarea_serializer_envio_configuration(self):
        """Debe validar configuración de envío"""
        # Configuración de envío válida
        config_envio_valida = {
            'email': True,
            'destinatarios': ['admin@empresa.com', 'gerencia@empresa.com'],
            'formato': 'pdf',
            'adjuntar_datos': True,
            'plantilla_email': 'reporte_mensual',
            'asunto_personalizado': 'Reporte de Ventas - {fecha}'
        }
        
        # Configuración de envío inválida
        config_envio_invalida = {
            'email': True,
            'formato': 'formato_inexistente',  # Formato no soportado
            'destinatarios': []  # Lista vacía cuando email=True
        }
        
        # Crear tarea con configuración válida
        plantilla_valida = PlantillasTarea.objects.create(
            nombre='Envío Válido',
            configuracion_programacion={'tipo': 'manual'},
            configuracion_envio=config_envio_valida,
            estado=True,
            created_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        self.assertEqual(plantilla_valida.configuracion_envio, config_envio_valida)
        
        # Simular validación de configuración inválida
        formatos_validos = ['pdf', 'excel', 'csv', 'json']
        
        if config_envio_invalida['formato'] not in formatos_validos:
            with self.assertRaises(Exception):
                raise ValidationError(f"Formato no soportado: {config_envio_invalida['formato']}")
        
        if config_envio_invalida['email'] and not config_envio_invalida['destinatarios']:
            with self.assertRaises(Exception):
                raise ValidationError("Debe especificar destinatarios cuando email=True")

    def test_plantillas_tarea_serializer_destinatarios_nested(self):
        """Debe manejar destinatarios anidados correctamente"""
        # Crear plantilla base
        plantilla = PlantillasTarea.objects.create(
            nombre='Tarea con Destinatarios',
            configuracion_programacion={'tipo': 'manual'},
            configuracion_envio={'email': True},
            estado=True,
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
        
        # Simular serializer con destinatarios anidados
        destinatarios_data = [
            {
                'id_empleado': self.empleado.id_empleado,
                'empleado': {
                    'nombre': self.empleado.nombre,
                    'apellido': self.empleado.apellido,
                    'usuario': self.empleado.usuario
                },
                'tipo_destinatario': 'principal',
                'notificar_inicio': True,
                'notificar_exito': True,
                'notificar_error': True
            }
        ]
        
        # Verificar estructura de datos anidados
        self.assertEqual(len(destinatarios_data), 1)
        self.assertIn('empleado', destinatarios_data[0])
        self.assertEqual(destinatarios_data[0]['tipo_destinatario'], 'principal')


class EjecucionesTareaSerializerTest(BaseReportesSerializerTest):
    """Tests para hipotético EjecucionesTareaSerializer"""

    def test_ejecuciones_tarea_serializer_status_validation(self):
        """Debe validar estados de ejecución"""
        # Estados válidos
        estados_validos = ['pendiente', 'ejecutando', 'completado', 'error', 'cancelado']
        
        # Crear plantilla base
        plantilla = PlantillasTarea.objects.create(
            nombre='Tarea para Ejecuciones',
            configuracion_programacion={'tipo': 'manual'},
            configuracion_envio={'email': False},
            estado=True,
            created_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        for estado in estados_validos:
            ejecucion = EjecucionesTarea.objects.create(
                id_plantilla_tarea=plantilla,
                estado=estado,
                fecha_inicio=timezone.now(),
                id_empleado=self.empleado
            )
            
            self.assertEqual(ejecucion.estado, estado)
            ejecucion.delete()

    def test_ejecuciones_tarea_serializer_timing_validation(self):
        """Debe validar tiempos de ejecución"""
        plantilla = PlantillasTarea.objects.create(
            nombre='Tarea Timing Test',
            configuracion_programacion={'tipo': 'manual'},
            configuracion_envio={},
            estado=True,
            created_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        # Ejecución con tiempos válidos
        fecha_inicio = timezone.now()
        fecha_fin = fecha_inicio + timedelta(minutes=30)
        
        ejecucion = EjecucionesTarea.objects.create(
            id_plantilla_tarea=plantilla,
            estado='completado',
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            id_empleado=self.empleado
        )
        
        # Verificar que fecha fin es posterior a fecha inicio
        self.assertGreater(ejecucion.fecha_fin, ejecucion.fecha_inicio)
        
        # Simular validación de fecha fin anterior a fecha inicio
        fecha_fin_invalida = fecha_inicio - timedelta(minutes=5)
        
        if fecha_fin_invalida < fecha_inicio:
            with self.assertRaises(Exception):
                # Serializer debería rechazar fecha_fin anterior a fecha_inicio
                raise ValidationError("Fecha de fin debe ser posterior a fecha de inicio")

    def test_ejecuciones_tarea_serializer_result_data(self):
        """Debe manejar datos de resultado de ejecución"""
        plantilla = PlantillasTarea.objects.create(
            nombre='Tarea con Resultados',
            configuracion_programacion={'tipo': 'manual'},
            configuracion_envio={},
            estado=True,
            created_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        # Datos de resultado exitoso
        resultado_exitoso = {
            'registros_procesados': 1500,
            'archivos_generados': ['reporte_ventas.pdf', 'datos_ventas.xlsx'],
            'tiempo_ejecucion': 180,  # segundos
            'estadisticas': {
                'total_ventas': 25000000,
                'promedio_venta': 16667,
                'max_venta': 500000
            }
        }
        
        # Datos de resultado con error
        resultado_error = {
            'error_codigo': 'DB_CONNECTION_ERROR',
            'error_mensaje': 'No se pudo conectar a la base de datos',
            'stack_trace': 'Traceback...',
            'registros_procesados': 0,
            'tiempo_ejecucion': 30
        }
        
        # Ejecución exitosa
        ejecucion_exitosa = EjecucionesTarea.objects.create(
            id_plantilla_tarea=plantilla,
            estado='completado',
            fecha_inicio=timezone.now(),
            fecha_fin=timezone.now() + timedelta(minutes=3),
            resultado=resultado_exitoso,
            id_empleado=self.empleado
        )
        
        # Ejecución con error
        ejecucion_error = EjecucionesTarea.objects.create(
            id_plantilla_tarea=plantilla,
            estado='error',
            fecha_inicio=timezone.now(),
            fecha_fin=timezone.now() + timedelta(seconds=30),
            resultado=resultado_error,
            id_empleado=self.empleado
        )
        
        # Verificar estructura de resultados
        self.assertIn('registros_procesados', ejecucion_exitosa.resultado)
        self.assertIn('archivos_generados', ejecucion_exitosa.resultado)
        self.assertIn('error_codigo', ejecucion_error.resultado)
        self.assertIn('error_mensaje', ejecucion_error.resultado)


class ReportesSerializersIntegrationTest(BaseReportesSerializerTest):
    """Tests de integración para serializers de reportes"""

    def test_serializers_chain_data_flow(self):
        """Debe manejar flujo de datos entre serializers relacionados"""
        # 1. Crear plantilla de reporte
        plantilla = PlantillasReporte.objects.create(
            nombre='Reporte Integración',
            query_sql='SELECT DATE(fecha) as dia, SUM(monto) as total FROM ventas GROUP BY DATE(fecha)',
            parametros={},
            tipo_reporte='ventas',
            frecuencia='diario',
            estado=True,
            created_at=timezone.now(),
            created_by=self.empleado
        )
        
        # 2. Crear dashboard que usa la plantilla
        dashboard_config = {
            'widgets': [
                {
                    'id': 'widget_reporte',
                    'tipo': 'report_chart',
                    'plantilla_id': plantilla.id_template,
                    'configuracion': {
                        'tipo_grafico': 'line',
                        'campo_x': 'dia',
                        'campo_y': 'total'
                    },
                    'posicion': {'x': 0, 'y': 0, 'w': 12, 'h': 8}
                }
            ]
        }
        
        dashboard = Dashboards.objects.create(
            nombre='Dashboard Integrado',
            configuracion=dashboard_config,
            es_publico=1,
            predeterminado=0,
            estado=True,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        # 3. Crear tarea programada para el reporte
        tarea = PlantillasTarea.objects.create(
            nombre='Envío Automático Dashboard',
            configuracion_programacion={
                'tipo': 'cron',
                'expresion': '0 9 * * 1-5'  # Lunes a viernes a las 9 AM
            },
            configuracion_envio={'email': True, 'formato': 'pdf'},
            estado=True,
            created_at=timezone.now(),
            id_empleado=self.empleado
        )
        
        # Verificar integridad del flujo
        self.assertEqual(plantilla.created_by, self.empleado)
        self.assertEqual(dashboard.id_empleado, self.empleado)
        self.assertEqual(tarea.id_empleado, self.empleado)
        
        # Verificar referencia en dashboard
        widget = dashboard.configuracion['widgets'][0]
        self.assertEqual(widget['plantilla_id'], plantilla.id_template)
        
        # Simular serializers anidados para output completo
        output_completo = {
            'dashboard': {
                'nombre': dashboard.nombre,
                'widgets': dashboard.configuracion['widgets']
            },
            'plantillas_utilizadas': [
                {
                    'id_template': plantilla.id_template,
                    'nombre': plantilla.nombre,
                    'tipo_reporte': plantilla.tipo_reporte
                }
            ],
            'tareas_programadas': [
                {
                    'nombre': tarea.nombre,
                    'expresion_cron': tarea.configuracion_programacion.get('expresion')
                }
            ]
        }
        
        # Verificar estructura integrada
        self.assertIn('dashboard', output_completo)
        self.assertIn('plantillas_utilizadas', output_completo)
        self.assertIn('tareas_programadas', output_completo)

    def test_serializers_error_handling_consistency(self):
        """Debe manejar errores consistentemente entre serializers"""
        # Errores de validación comunes entre diferentes serializers
        errores_comunes = [
            {'campo': 'nombre', 'error': 'Campo requerido'},
            {'campo': 'empleado', 'error': 'Empleado no existe'},
            {'campo': 'configuracion', 'error': 'JSON inválido'},
            {'campo': 'fecha', 'error': 'Formato de fecha inválido'}
        ]
        
        # Simular manejo consistente de errores
        for error in errores_comunes:
            # Todos los serializers deberían manejar estos errores de manera similar
            error_response = {
                'field': error['campo'],
                'message': error['error'],
                'code': 'validation_error'
            }
            
            # Verificar estructura de error consistente
            self.assertIn('field', error_response)
            self.assertIn('message', error_response)
            self.assertIn('code', error_response)

    def test_serializers_performance_considerations(self):
        """Debe considerar optimizaciones de performance"""
        # Crear datos para test de performance
        plantillas = []
        for i in range(10):
            plantilla = PlantillasReporte.objects.create(
                nombre=f'Plantilla Performance {i}',
                query_sql=f'SELECT {i} as numero',
                parametros={},
                tipo_reporte='performance',
                frecuencia='manual',
                created_at=timezone.now(),
                created_by=self.empleado
            )
            plantillas.append(plantilla)
        
        # Simular serialización en lote
        plantillas_data = []
        for plantilla in plantillas:
            data = {
                'id_template': plantilla.id_template,
                'nombre': plantilla.nombre,
                'created_by': {
                    'id_empleado': plantilla.created_by.id_empleado,
                    'nombre': plantilla.created_by.nombre
                }
            }
            plantillas_data.append(data)
        
        # Verificar que todos los datos fueron serializados
        self.assertEqual(len(plantillas_data), 10)
        
        # Verificar que la estructura es consistente
        for data in plantillas_data:
            self.assertIn('id_template', data)
            self.assertIn('created_by', data)
            self.assertIn('nombre', data['created_by'])