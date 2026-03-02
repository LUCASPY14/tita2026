"""
Tests para validadores del módulo de Reportes
Cantina Tita - Sistema de Gestión

Tests completos para todos los validadores del módulo de reportes.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
import json

from .validators import (
    # Plantillas de Reporte
    validar_nombre_plantilla_reporte,
    validar_query_sql,
    validar_parametros_reporte,
    validar_tipo_reporte,
    validar_frecuencia_reporte,
    # Dashboards
    validar_nombre_dashboard,
    validar_configuracion_dashboard,
    validar_es_publico_dashboard,
    validar_predeterminado_dashboard,
    # KPI Métricas
    validar_nombre_kpi,
    validar_descripcion_kpi,
    validar_formula_kpi,
    validar_unidad_kpi,
    validar_valor_objetivo_kpi,
    validar_categoria_kpi,
    validar_frecuencia_kpi,
    # Valores KPI
    validar_valor_kpi,
    validar_auto_calc_valores_kpi,
    # Plantillas de Tarea
    validar_nombre_plantilla_tarea,
    validar_descripcion_tarea,
    validar_tipo_tarea,
    validar_comando_tarea,
    validar_parametros_tarea,
    validar_frecuencia_tarea,
    validar_cron_expresion,
    validar_timeout_tarea,
    validar_max_reintentos_tarea,
    validar_notif_exito_tarea,
    validar_notif_error_tarea,
    # Ejecuciones de Tarea
    validar_duracion_seg_ejecucion,
    validar_estado_ejecucion,
    validar_pid_ejecucion,
    validar_servidor_ejecucion,
    # Destinatarios de Tarea
    validar_notif_inicio_destinatario,
    validar_notif_fin_destinatario,
    validar_notif_error_destinatario,
)


# =============================================================================
# TESTS - PLANTILLAS DE REPORTE
# =============================================================================

class TestValidarNombrePlantillaReporte(TestCase):
    def test_nombre_valido(self):
        """Prueba con nombre válido"""
        validar_nombre_plantilla_reporte("Reporte Mensual de Ventas")
        validar_nombre_plantilla_reporte("ABC")
        validar_nombre_plantilla_reporte("Reporte de Inventario")
    
    def test_nombre_muy_corto(self):
        """Prueba con nombre muy corto"""
        with self.assertRaises(ValidationError):
            validar_nombre_plantilla_reporte("AB")
        with self.assertRaises(ValidationError):
            validar_nombre_plantilla_reporte("")
    
    def test_nombre_muy_largo(self):
        """Prueba con nombre muy largo"""
        with self.assertRaises(ValidationError):
            validar_nombre_plantilla_reporte("A" * 101)


class TestValidarQuerySQL(TestCase):
    def test_query_valida(self):
        """Prueba con query SQL válida"""
        validar_query_sql("SELECT * FROM ventas WHERE fecha > '2024-01-01'")
        validar_query_sql("SELECT nombre, total FROM clientes")
    
    def test_query_muy_corta(self):
        """Prueba con query muy corta"""
        with self.assertRaises(ValidationError):
            validar_query_sql("SELECT *")
    
    def test_query_muy_larga(self):
        """Prueba con query muy larga"""
        with self.assertRaises(ValidationError):
            validar_query_sql("SELECT " + "column, " * 5000 + "FROM tabla")
    
    def test_query_sin_select(self):
        """Prueba con query sin SELECT"""
        with self.assertRaises(ValidationError):
            validar_query_sql("DELETE FROM tabla WHERE id = 1")


class TestValidarParametrosReporte(TestCase):
    def test_parametros_validos_dict(self):
        """Prueba con parámetros válidos como dict"""
        validar_parametros_reporte({"fecha_inicio": "2024-01-01", "fecha_fin": "2024-12-31"})
        validar_parametros_reporte({"id_empleado": 1})
    
    def test_parametros_validos_json_string(self):
        """Prueba con parámetros válidos como JSON string"""
        validar_parametros_reporte('{"fecha": "2024-01-01"}')
    
    def test_parametros_none(self):
        """Prueba con parámetros None (válido)"""
        validar_parametros_reporte(None)
    
    def test_parametros_invalidos_no_dict(self):
        """Prueba con parámetros que no son dict"""
        with self.assertRaises(ValidationError):
            validar_parametros_reporte([1, 2, 3])
    
    def test_parametros_json_invalido(self):
        """Prueba con JSON inválido"""
        with self.assertRaises(ValidationError):
            validar_parametros_reporte('{"invalido": }')
    
    def test_parametros_exceso(self):
        """Prueba con demasiados parámetros"""
        parametros_exceso = {f"param{i}": i for i in range(21)}
        with self.assertRaises(ValidationError):
            validar_parametros_reporte(parametros_exceso)


class TestValidarTipoReporte(TestCase):
    def test_tipos_validos(self):
        """Prueba con tipos válidos"""
        validar_tipo_reporte("Ventas")
        validar_tipo_reporte("Inventario")
        validar_tipo_reporte("Compras")
        validar_tipo_reporte("Financiero")
        validar_tipo_reporte("Cliente")
        validar_tipo_reporte("Empleado")
        validar_tipo_reporte("Personalizado")
    
    def test_tipo_invalido(self):
        """Prueba con tipo inválido"""
        with self.assertRaises(ValidationError):
            validar_tipo_reporte("Otro")


class TestValidarFrecuenciaReporte(TestCase):
    def test_frecuencias_validas(self):
        """Prueba con frecuencias válidas"""
        validar_frecuencia_reporte("Diario")
        validar_frecuencia_reporte("Semanal")
        validar_frecuencia_reporte("Mensual")
        validar_frecuencia_reporte("Trimestral")
        validar_frecuencia_reporte("Anual")
        validar_frecuencia_reporte("Manual")
    
    def test_frecuencia_invalida(self):
        """Prueba con frecuencia inválida"""
        with self.assertRaises(ValidationError):
            validar_frecuencia_reporte("Bimensual")


# =============================================================================
# TESTS - DASHBOARDS
# =============================================================================

class TestValidarNombreDashboard(TestCase):
    def test_nombre_valido(self):
        """Prueba con nombre válido"""
        validar_nombre_dashboard("Dashboard Principal")
        validar_nombre_dashboard("KPIs de Ventas")
    
    def test_nombre_muy_corto(self):
        """Prueba con nombre muy corto"""
        with self.assertRaises(ValidationError):
            validar_nombre_dashboard("AB")
    
    def test_nombre_muy_largo(self):
        """Prueba con nombre muy largo"""
        with self.assertRaises(ValidationError):
            validar_nombre_dashboard("A" * 101)


class TestValidarConfiguracionDashboard(TestCase):
    def test_configuracion_valida(self):
        """Prueba con configuración válida"""
        config = {
            "widgets": [
                {"tipo": "grafico", "datos": "ventas"},
                {"tipo": "tabla", "datos": "clientes"}
            ]
        }
        validar_configuracion_dashboard(config)
    
    def test_configuracion_valida_json_string(self):
        """Prueba con configuración como JSON string"""
        config_str = '{"widgets": [{"tipo": "grafico"}]}'
        validar_configuracion_dashboard(config_str)
    
    def test_configuracion_none(self):
        """Prueba con configuración None"""
        with self.assertRaises(ValidationError):
            validar_configuracion_dashboard(None)
    
    def test_configuracion_sin_widgets(self):
        """Prueba con configuración sin widgets"""
        with self.assertRaises(ValidationError):
            validar_configuracion_dashboard({"layout": "vertical"})
    
    def test_configuracion_widgets_no_lista(self):
        """Prueba con widgets que no es lista"""
        with self.assertRaises(ValidationError):
            validar_configuracion_dashboard({"widgets": "no es lista"})
    
    def test_configuracion_exceso_widgets(self):
        """Prueba con demasiados widgets"""
        config = {"widgets": [{"tipo": "grafico"} for _ in range(21)]}
        with self.assertRaises(ValidationError):
            validar_configuracion_dashboard(config)


class TestValidarEsPublicoDashboard(TestCase):
    def test_valores_validos(self):
        """Prueba con valores válidos"""
        validar_es_publico_dashboard(0)
        validar_es_publico_dashboard(1)
    
    def test_valores_invalidos(self):
        """Prueba con valores inválidos"""
        with self.assertRaises(ValidationError):
            validar_es_publico_dashboard(2)
        with self.assertRaises(ValidationError):
            validar_es_publico_dashboard(-1)


class TestValidarPredeterminadoDashboard(TestCase):
    def test_valores_validos(self):
        """Prueba con valores válidos"""
        validar_predeterminado_dashboard(0)
        validar_predeterminado_dashboard(1)
    
    def test_valores_invalidos(self):
        """Prueba con valores inválidos"""
        with self.assertRaises(ValidationError):
            validar_predeterminado_dashboard(2)


# =============================================================================
# TESTS - KPI MÉTRICAS
# =============================================================================

class TestValidarNombreKpi(TestCase):
    def test_nombre_valido(self):
        """Prueba con nombre válido"""
        validar_nombre_kpi("Tasa de Conversión")
        validar_nombre_kpi("ROI")
    
    def test_nombre_muy_corto(self):
        """Prueba con nombre muy corto"""
        with self.assertRaises(ValidationError):
            validar_nombre_kpi("AB")
    
    def test_nombre_muy_largo(self):
        """Prueba con nombre muy largo"""
        with self.assertRaises(ValidationError):
            validar_nombre_kpi("A" * 101)


class TestValidarDescripcionKpi(TestCase):
    def test_descripcion_valida(self):
        """Prueba con descripción válida"""
        validar_descripcion_kpi("Este KPI mide el rendimiento de ventas mensual")
    
    def test_descripcion_muy_corta(self):
        """Prueba con descripción muy corta"""
        with self.assertRaises(ValidationError):
            validar_descripcion_kpi("Corto")
    
    def test_descripcion_muy_larga(self):
        """Prueba con descripción muy larga"""
        with self.assertRaises(ValidationError):
            validar_descripcion_kpi("A" * 1001)


class TestValidarFormulaKpi(TestCase):
    def test_formula_valida(self):
        """Prueba con fórmula válida"""
        validar_formula_kpi("(ventas / clientes) * 100")
        validar_formula_kpi("SUM(total)")
    
    def test_formula_muy_corta(self):
        """Prueba con fórmula muy corta"""
        with self.assertRaises(ValidationError):
            validar_formula_kpi("A+B")
    
    def test_formula_muy_larga(self):
        """Prueba con fórmula muy larga"""
        with self.assertRaises(ValidationError):
            validar_formula_kpi("A" * 501)


class TestValidarUnidadKpi(TestCase):
    def test_unidades_validas(self):
        """Prueba con unidades válidas"""
        validar_unidad_kpi("%")
        validar_unidad_kpi("₲")
        validar_unidad_kpi("USD")
        validar_unidad_kpi("unidades")
        validar_unidad_kpi("días")
        validar_unidad_kpi("horas")
        validar_unidad_kpi("ratio")
        validar_unidad_kpi("puntos")
    
    def test_unidad_invalida(self):
        """Prueba con unidad inválida"""
        with self.assertRaises(ValidationError):
            validar_unidad_kpi("kilogramos")


class TestValidarValorObjetivoKpi(TestCase):
    def test_valor_valido(self):
        """Prueba con valor objetivo válido"""
        validar_valor_objetivo_kpi(Decimal('100.50'))
        validar_valor_objetivo_kpi(Decimal('0.00'))
        validar_valor_objetivo_kpi(Decimal('999999999.99'))
    
    def test_valor_none(self):
        """Prueba con valor None (válido)"""
        validar_valor_objetivo_kpi(None)
    
    def test_valor_muy_bajo(self):
        """Prueba con valor muy bajo"""
        with self.assertRaises(ValidationError):
            validar_valor_objetivo_kpi(Decimal('-1000000000.00'))
    
    def test_valor_muy_alto(self):
        """Prueba con valor muy alto"""
        with self.assertRaises(ValidationError):
            validar_valor_objetivo_kpi(Decimal('1000000000.00'))
    
    def test_valor_demasiados_decimales(self):
        """Prueba con demasiados decimales"""
        with self.assertRaises(ValidationError):
            validar_valor_objetivo_kpi(Decimal('100.123'))


class TestValidarCategoriaKpi(TestCase):
    def test_categorias_validas(self):
        """Prueba con categorías válidas"""
        validar_categoria_kpi("Ventas")
        validar_categoria_kpi("Inventario")
        validar_categoria_kpi("Compras")
        validar_categoria_kpi("Financiero")
        validar_categoria_kpi("Cliente")
        validar_categoria_kpi("Empleado")
        validar_categoria_kpi("Operacional")
    
    def test_categoria_invalida(self):
        """Prueba con categoría inválida"""
        with self.assertRaises(ValidationError):
            validar_categoria_kpi("Marketing")


class TestValidarFrecuenciaKpi(TestCase):
    def test_frecuencias_validas(self):
        """Prueba con frecuencias válidas"""
        validar_frecuencia_kpi("Diario")
        validar_frecuencia_kpi("Semanal")
        validar_frecuencia_kpi("Mensual")
        validar_frecuencia_kpi("Trimestral")
        validar_frecuencia_kpi("Anual")
    
    def test_frecuencia_invalida(self):
        """Prueba con frecuencia inválida"""
        with self.assertRaises(ValidationError):
            validar_frecuencia_kpi("Bimestral")


# =============================================================================
# TESTS - VALORES KPI
# =============================================================================

class TestValidarValorKpi(TestCase):
    def test_valor_valido(self):
        """Prueba con valor válido"""
        validar_valor_kpi(Decimal('100.50'))
        validar_valor_kpi(Decimal('0.00'))
        validar_valor_kpi(Decimal('-50.25'))
    
    def test_valor_muy_bajo(self):
        """Prueba con valor muy bajo"""
        with self.assertRaises(ValidationError):
            validar_valor_kpi(Decimal('-1000000000.00'))
    
    def test_valor_muy_alto(self):
        """Prueba con valor muy alto"""
        with self.assertRaises(ValidationError):
            validar_valor_kpi(Decimal('1000000000.00'))
    
    def test_valor_demasiados_decimales(self):
        """Prueba con demasiados decimales"""
        with self.assertRaises(ValidationError):
            validar_valor_kpi(Decimal('100.123'))


class TestValidarAutoCalcValoresKpi(TestCase):
    def test_valores_validos(self):
        """Prueba con valores válidos"""
        validar_auto_calc_valores_kpi(0)
        validar_auto_calc_valores_kpi(1)
    
    def test_valores_invalidos(self):
        """Prueba con valores inválidos"""
        with self.assertRaises(ValidationError):
            validar_auto_calc_valores_kpi(2)
        with self.assertRaises(ValidationError):
            validar_auto_calc_valores_kpi(-1)


# =============================================================================
# TESTS - PLANTILLAS DE TAREA
# =============================================================================

class TestValidarNombrePlantillaTarea(TestCase):
    def test_nombre_valido(self):
        """Prueba con nombre válido"""
        validar_nombre_plantilla_tarea("Backup Diario")
        validar_nombre_plantilla_tarea("Limpieza de Logs")
    
    def test_nombre_muy_corto(self):
        """Prueba con nombre muy corto"""
        with self.assertRaises(ValidationError):
            validar_nombre_plantilla_tarea("AB")
    
    def test_nombre_muy_largo(self):
        """Prueba con nombre muy largo"""
        with self.assertRaises(ValidationError):
            validar_nombre_plantilla_tarea("A" * 101)


class TestValidarDescripcionTarea(TestCase):
    def test_descripcion_valida(self):
        """Prueba con descripción válida"""
        validar_descripcion_tarea("Esta tarea realiza un backup completo de la base de datos")
    
    def test_descripcion_muy_corta(self):
        """Prueba con descripción muy corta"""
        with self.assertRaises(ValidationError):
            validar_descripcion_tarea("Corta")
    
    def test_descripcion_muy_larga(self):
        """Prueba con descripción muy larga"""
        with self.assertRaises(ValidationError):
            validar_descripcion_tarea("A" * 1001)


class TestValidarTipoTarea(TestCase):
    def test_tipos_validos(self):
        """Prueba con tipos válidos"""
        validar_tipo_tarea("Reporte")
        validar_tipo_tarea("Backup")
        validar_tipo_tarea("Limpieza")
        validar_tipo_tarea("Sincronización")
        validar_tipo_tarea("Cálculo")
        validar_tipo_tarea("Notificación")
        validar_tipo_tarea("Personalizado")
    
    def test_tipo_invalido(self):
        """Prueba con tipo inválido"""
        with self.assertRaises(ValidationError):
            validar_tipo_tarea("Otro")


class TestValidarComandoTarea(TestCase):
    def test_comando_valido(self):
        """Prueba con comando válido"""
        validar_comando_tarea("python manage.py backup")
        validar_comando_tarea("/usr/bin/backup.sh")
    
    def test_comando_muy_corto(self):
        """Prueba con comando muy corto"""
        with self.assertRaises(ValidationError):
            validar_comando_tarea("ls")
    
    def test_comando_muy_largo(self):
        """Prueba con comando muy largo"""
        with self.assertRaises(ValidationError):
            validar_comando_tarea("A" * 501)


class TestValidarParametrosTarea(TestCase):
    def test_parametros_validos(self):
        """Prueba con parámetros válidos"""
        validar_parametros_tarea({"ruta": "/backup", "formato": "zip"})
    
    def test_parametros_json_string(self):
        """Prueba con parámetros como JSON string"""
        validar_parametros_tarea('{"ruta": "/backup"}')
    
    def test_parametros_none(self):
        """Prueba con parámetros None (válido)"""
        validar_parametros_tarea(None)
    
    def test_parametros_exceso(self):
        """Prueba con demasiados parámetros"""
        parametros_exceso = {f"param{i}": i for i in range(21)}
        with self.assertRaises(ValidationError):
            validar_parametros_tarea(parametros_exceso)


class TestValidarFrecuenciaTarea(TestCase):
    def test_frecuencias_validas(self):
        """Prueba con frecuencias válidas"""
        validar_frecuencia_tarea("Cada hora")
        validar_frecuencia_tarea("Diario")
        validar_frecuencia_tarea("Semanal")
        validar_frecuencia_tarea("Mensual")
        validar_frecuencia_tarea("Personalizado")
    
    def test_frecuencia_invalida(self):
        """Prueba con frecuencia inválida"""
        with self.assertRaises(ValidationError):
            validar_frecuencia_tarea("Anual")


class TestValidarCronExpresion(TestCase):
    def test_expresiones_validas(self):
        """Prueba con expresiones cron válidas"""
        validar_cron_expresion("0 2 * * *")  # Diario a las 2 AM
        validar_cron_expresion("*/15 * * * *")  # Cada 15 minutos
        validar_cron_expresion("0 0 1 * *")  # Primer día del mes
    
    def test_expresion_muy_corta(self):
        """Prueba con expresión muy corta"""
        with self.assertRaises(ValidationError):
            validar_cron_expresion("* *")
    
    def test_expresion_muy_larga(self):
        """Prueba con expresión muy larga"""
        with self.assertRaises(ValidationError):
            validar_cron_expresion("A" * 101)
    
    def test_expresion_campos_incorrectos(self):
        """Prueba con número incorrecto de campos"""
        with self.assertRaises(ValidationError):
            validar_cron_expresion("* * *")  # Solo 3 campos
        with self.assertRaises(ValidationError):
            validar_cron_expresion("* * * * * *")  # 6 campos


class TestValidarTimeoutTarea(TestCase):
    def test_timeout_valido(self):
        """Prueba con timeout válido"""
        validar_timeout_tarea(60)  # 1 minuto
        validar_timeout_tarea(3600)  # 1 hora
        validar_timeout_tarea(86400)  # 24 horas
    
    def test_timeout_muy_corto(self):
        """Prueba con timeout muy corto"""
        with self.assertRaises(ValidationError):
            validar_timeout_tarea(5)
    
    def test_timeout_muy_largo(self):
        """Prueba con timeout muy largo"""
        with self.assertRaises(ValidationError):
            validar_timeout_tarea(86401)


class TestValidarMaxReintentosTarea(TestCase):
    def test_reintentos_validos(self):
        """Prueba con reintentos válidos"""
        validar_max_reintentos_tarea(0)
        validar_max_reintentos_tarea(3)
        validar_max_reintentos_tarea(10)
    
    def test_reintentos_negativos(self):
        """Prueba con reintentos negativos"""
        with self.assertRaises(ValidationError):
            validar_max_reintentos_tarea(-1)
    
    def test_reintentos_excesivos(self):
        """Prueba con demasiados reintentos"""
        with self.assertRaises(ValidationError):
            validar_max_reintentos_tarea(11)


class TestValidarNotifExitoTarea(TestCase):
    def test_valores_validos(self):
        """Prueba con valores válidos"""
        validar_notif_exito_tarea(0)
        validar_notif_exito_tarea(1)
    
    def test_valores_invalidos(self):
        """Prueba con valores inválidos"""
        with self.assertRaises(ValidationError):
            validar_notif_exito_tarea(2)


class TestValidarNotifErrorTarea(TestCase):
    def test_valores_validos(self):
        """Prueba con valores válidos"""
        validar_notif_error_tarea(0)
        validar_notif_error_tarea(1)
    
    def test_valores_invalidos(self):
        """Prueba con valores inválidos"""
        with self.assertRaises(ValidationError):
            validar_notif_error_tarea(2)


# =============================================================================
# TESTS - EJECUCIONES DE TAREA
# =============================================================================

class TestValidarDuracionSegEjecucion(TestCase):
    def test_duracion_valida(self):
        """Prueba con duración válida"""
        validar_duracion_seg_ejecucion(60)
        validar_duracion_seg_ejecucion(3600)
        validar_duracion_seg_ejecucion(0)
    
    def test_duracion_none(self):
        """Prueba con duración None (válida)"""
        validar_duracion_seg_ejecucion(None)
    
    def test_duracion_negativa(self):
        """Prueba con duración negativa"""
        with self.assertRaises(ValidationError):
            validar_duracion_seg_ejecucion(-1)
    
    def test_duracion_excesiva(self):
        """Prueba con duración excesiva"""
        with self.assertRaises(ValidationError):
            validar_duracion_seg_ejecucion(86401)


class TestValidarEstadoEjecucion(TestCase):
    def test_estados_validos(self):
        """Prueba con estados válidos"""
        validar_estado_ejecucion("Pendiente")
        validar_estado_ejecucion("Ejecutando")
        validar_estado_ejecucion("Exitoso")
        validar_estado_ejecucion("Fallido")
        validar_estado_ejecucion("Cancelado")
        validar_estado_ejecucion("Timeout")
    
    def test_estado_invalido(self):
        """Prueba con estado inválido"""
        with self.assertRaises(ValidationError):
            validar_estado_ejecucion("Completado")


class TestValidarPidEjecucion(TestCase):
    def test_pid_valido(self):
        """Prueba con PID válido"""
        validar_pid_ejecucion(1234)
        validar_pid_ejecucion(99999)
    
    def test_pid_none(self):
        """Prueba con PID None (válido)"""
        validar_pid_ejecucion(None)
    
    def test_pid_invalido(self):
        """Prueba con PID inválido"""
        with self.assertRaises(ValidationError):
            validar_pid_ejecucion(0)
        with self.assertRaises(ValidationError):
            validar_pid_ejecucion(-1)


class TestValidarServidorEjecucion(TestCase):
    def test_servidor_valido(self):
        """Prueba con servidor válido"""
        validar_servidor_ejecucion("servidor-produccion")
        validar_servidor_ejecucion("192.168.1.100")
    
    def test_servidor_muy_corto(self):
        """Prueba con servidor muy corto"""
        with self.assertRaises(ValidationError):
            validar_servidor_ejecucion("A")
    
    def test_servidor_muy_largo(self):
        """Prueba con servidor muy largo"""
        with self.assertRaises(ValidationError):
            validar_servidor_ejecucion("A" * 101)


# =============================================================================
# TESTS - DESTINATARIOS DE TAREA
# =============================================================================

class TestValidarNotifInicioDestinatario(TestCase):
    def test_valores_validos(self):
        """Prueba con valores válidos"""
        validar_notif_inicio_destinatario(0)
        validar_notif_inicio_destinatario(1)
    
    def test_valores_invalidos(self):
        """Prueba con valores inválidos"""
        with self.assertRaises(ValidationError):
            validar_notif_inicio_destinatario(2)


class TestValidarNotifFinDestinatario(TestCase):
    def test_valores_validos(self):
        """Prueba con valores válidos"""
        validar_notif_fin_destinatario(0)
        validar_notif_fin_destinatario(1)
    
    def test_valores_invalidos(self):
        """Prueba con valores inválidos"""
        with self.assertRaises(ValidationError):
            validar_notif_fin_destinatario(2)


class TestValidarNotifErrorDestinatario(TestCase):
    def test_valores_validos(self):
        """Prueba con valores válidos"""
        validar_notif_error_destinatario(0)
        validar_notif_error_destinatario(1)
    
    def test_valores_invalidos(self):
        """Prueba con valores inválidos"""
        with self.assertRaises(ValidationError):
            validar_notif_error_destinatario(2)
