"""
Tests for apps/reportes/admin.py
Covers all custom display methods across 7 admin classes.
"""
from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.contrib.admin.sites import AdminSite

from apps.reportes.admin import (
    PlantillasReporteAdmin,
    DashboardsAdmin,
    KpiMetricasAdmin,
    ValoresKpiAdmin,
    PlantillasTareaAdmin,
    EjecucionesTareaAdmin,
    DestinatariosTareaAdmin,
)
from apps.reportes.models import (
    PlantillasReporte,
    Dashboards,
    KpiMetricas,
    ValoresKpi,
    PlantillasTarea,
    EjecucionesTarea,
    DestinatariosTarea,
)

_plain_format_html = lambda fmt, *a, **k: fmt.format(*a, **k)


def _mock_obj(**kwargs):
    obj = MagicMock()
    for k, v in kwargs.items():
        setattr(obj, k, v)
    return obj


# =============================================================================
# PlantillasReporteAdmin
# =============================================================================

@patch('apps.reportes.admin.format_html', _plain_format_html)
class PlantillasReporteAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = PlantillasReporteAdmin(PlantillasReporte, self.site)

    def test_tipo_reporte_badge_ventas(self):
        obj = _mock_obj(tipo_reporte="Ventas")
        result = str(self.admin.tipo_reporte_badge(obj))
        self.assertIn("green", result)
        self.assertIn("Ventas", result)

    def test_tipo_reporte_badge_inventario(self):
        obj = _mock_obj(tipo_reporte="Inventario")
        result = str(self.admin.tipo_reporte_badge(obj))
        self.assertIn("blue", result)

    def test_tipo_reporte_badge_compras(self):
        obj = _mock_obj(tipo_reporte="Compras")
        result = str(self.admin.tipo_reporte_badge(obj))
        self.assertIn("orange", result)

    def test_tipo_reporte_badge_financiero(self):
        obj = _mock_obj(tipo_reporte="Financiero")
        result = str(self.admin.tipo_reporte_badge(obj))
        self.assertIn("purple", result)

    def test_tipo_reporte_badge_cliente(self):
        obj = _mock_obj(tipo_reporte="Cliente")
        result = str(self.admin.tipo_reporte_badge(obj))
        self.assertIn("cyan", result)

    def test_tipo_reporte_badge_empleado(self):
        obj = _mock_obj(tipo_reporte="Empleado")
        result = str(self.admin.tipo_reporte_badge(obj))
        self.assertIn("pink", result)

    def test_tipo_reporte_badge_personalizado(self):
        obj = _mock_obj(tipo_reporte="Personalizado")
        result = str(self.admin.tipo_reporte_badge(obj))
        self.assertIn("gray", result)

    def test_tipo_reporte_badge_desconocido(self):
        obj = _mock_obj(tipo_reporte="Otro")
        result = str(self.admin.tipo_reporte_badge(obj))
        self.assertIn("gray", result)

    def test_frecuencia_badge_diario(self):
        obj = _mock_obj(frecuencia="Diario")
        result = str(self.admin.frecuencia_badge(obj))
        self.assertIn("green", result)

    def test_frecuencia_badge_semanal(self):
        obj = _mock_obj(frecuencia="Semanal")
        result = str(self.admin.frecuencia_badge(obj))
        self.assertIn("blue", result)

    def test_frecuencia_badge_mensual(self):
        obj = _mock_obj(frecuencia="Mensual")
        result = str(self.admin.frecuencia_badge(obj))
        self.assertIn("orange", result)

    def test_frecuencia_badge_trimestral(self):
        obj = _mock_obj(frecuencia="Trimestral")
        result = str(self.admin.frecuencia_badge(obj))
        self.assertIn("purple", result)

    def test_frecuencia_badge_anual(self):
        obj = _mock_obj(frecuencia="Anual")
        result = str(self.admin.frecuencia_badge(obj))
        self.assertIn("red", result)

    def test_frecuencia_badge_manual(self):
        obj = _mock_obj(frecuencia="Manual")
        result = str(self.admin.frecuencia_badge(obj))
        self.assertIn("gray", result)

    def test_frecuencia_badge_desconocida(self):
        obj = _mock_obj(frecuencia="Otro")
        result = str(self.admin.frecuencia_badge(obj))
        self.assertIn("gray", result)

    def test_activo_badge_activo(self):
        obj = _mock_obj(estado=True)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("green", result)
        self.assertIn("estado", result)

    def test_activo_badge_inactivo(self):
        obj = _mock_obj(estado=False)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("red", result)
        self.assertIn("Inactivo", result)


# =============================================================================
# DashboardsAdmin
# =============================================================================

@patch('apps.reportes.admin.format_html', _plain_format_html)
class DashboardsAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = DashboardsAdmin(Dashboards, self.site)

    def test_es_publico_badge_publico(self):
        obj = _mock_obj(es_publico=1)
        result = str(self.admin.es_publico_badge(obj))
        self.assertIn("green", result)
        self.assertIn("Público", result)

    def test_es_publico_badge_privado(self):
        obj = _mock_obj(es_publico=0)
        result = str(self.admin.es_publico_badge(obj))
        self.assertIn("gray", result)
        self.assertIn("Privado", result)

    def test_predeterminado_badge_si(self):
        obj = _mock_obj(predeterminado=1)
        result = str(self.admin.predeterminado_badge(obj))
        self.assertIn("blue", result)
        self.assertIn("Predeterminado", result)

    def test_predeterminado_badge_no(self):
        obj = _mock_obj(predeterminado=0)
        result = str(self.admin.predeterminado_badge(obj))
        self.assertIn("lightgray", result)
        self.assertIn("Normal", result)

    def test_activo_badge_activo(self):
        obj = _mock_obj(estado=True)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("green", result)

    def test_activo_badge_inactivo(self):
        obj = _mock_obj(estado=False)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("red", result)


# =============================================================================
# KpiMetricasAdmin
# =============================================================================

@patch('apps.reportes.admin.format_html', _plain_format_html)
class KpiMetricasAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = KpiMetricasAdmin(KpiMetricas, self.site)

    def test_valor_objetivo_display_con_valor(self):
        obj = _mock_obj(valor_objetivo=1000, unidad="$")
        result = self.admin.valor_objetivo_display(obj)
        self.assertIn("1,000.00", result)
        self.assertIn("$", result)

    def test_valor_objetivo_display_sin_valor(self):
        obj = _mock_obj(valor_objetivo=None)
        result = self.admin.valor_objetivo_display(obj)
        self.assertEqual(result, "-")

    def test_valor_objetivo_display_cero(self):
        obj = _mock_obj(valor_objetivo=0, unidad="%")
        result = self.admin.valor_objetivo_display(obj)
        # 0 is falsy → returns "-"
        self.assertEqual(result, "-")

    def test_categoria_badge_ventas(self):
        obj = _mock_obj(categoria="Ventas")
        result = str(self.admin.categoria_badge(obj))
        self.assertIn("green", result)

    def test_categoria_badge_inventario(self):
        obj = _mock_obj(categoria="Inventario")
        result = str(self.admin.categoria_badge(obj))
        self.assertIn("blue", result)

    def test_categoria_badge_compras(self):
        obj = _mock_obj(categoria="Compras")
        result = str(self.admin.categoria_badge(obj))
        self.assertIn("orange", result)

    def test_categoria_badge_financiero(self):
        obj = _mock_obj(categoria="Financiero")
        result = str(self.admin.categoria_badge(obj))
        self.assertIn("purple", result)

    def test_categoria_badge_cliente(self):
        obj = _mock_obj(categoria="Cliente")
        result = str(self.admin.categoria_badge(obj))
        self.assertIn("cyan", result)

    def test_categoria_badge_empleado(self):
        obj = _mock_obj(categoria="Empleado")
        result = str(self.admin.categoria_badge(obj))
        self.assertIn("pink", result)

    def test_categoria_badge_operacional(self):
        obj = _mock_obj(categoria="Operacional")
        result = str(self.admin.categoria_badge(obj))
        self.assertIn("brown", result)

    def test_categoria_badge_desconocida(self):
        obj = _mock_obj(categoria="Otro")
        result = str(self.admin.categoria_badge(obj))
        self.assertIn("gray", result)

    def test_frecuencia_badge_diario(self):
        obj = _mock_obj(frecuencia="Diario")
        result = str(self.admin.frecuencia_badge(obj))
        self.assertIn("green", result)

    def test_frecuencia_badge_semanal(self):
        obj = _mock_obj(frecuencia="Semanal")
        result = str(self.admin.frecuencia_badge(obj))
        self.assertIn("blue", result)

    def test_frecuencia_badge_mensual(self):
        obj = _mock_obj(frecuencia="Mensual")
        result = str(self.admin.frecuencia_badge(obj))
        self.assertIn("orange", result)

    def test_frecuencia_badge_trimestral(self):
        obj = _mock_obj(frecuencia="Trimestral")
        result = str(self.admin.frecuencia_badge(obj))
        self.assertIn("purple", result)

    def test_frecuencia_badge_anual(self):
        obj = _mock_obj(frecuencia="Anual")
        result = str(self.admin.frecuencia_badge(obj))
        self.assertIn("red", result)

    def test_frecuencia_badge_desconocida(self):
        obj = _mock_obj(frecuencia="Otro")
        result = str(self.admin.frecuencia_badge(obj))
        self.assertIn("gray", result)

    def test_activo_badge_activo(self):
        obj = _mock_obj(estado=True)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("green", result)

    def test_activo_badge_inactivo(self):
        obj = _mock_obj(estado=False)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("red", result)


# =============================================================================
# ValoresKpiAdmin
# =============================================================================

@patch('apps.reportes.admin.format_html', _plain_format_html)
class ValoresKpiAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = ValoresKpiAdmin(ValoresKpi, self.site)

    def test_valor_display_con_kpi(self):
        kpi = _mock_obj(unidad="kg")
        obj = _mock_obj(valor=1500, id_kpi=kpi)
        result = self.admin.valor_display(obj)
        self.assertIn("1,500.00", result)
        self.assertIn("kg", result)

    def test_valor_display_sin_kpi(self):
        obj = _mock_obj(valor=200, id_kpi=None)
        result = self.admin.valor_display(obj)
        self.assertIn("200.00", result)

    def test_auto_calc_badge_auto(self):
        obj = _mock_obj(auto_calc=1)
        result = str(self.admin.auto_calc_badge(obj))
        self.assertIn("blue", result)
        self.assertIn("Auto", result)

    def test_auto_calc_badge_manual(self):
        obj = _mock_obj(auto_calc=0)
        result = str(self.admin.auto_calc_badge(obj))
        self.assertIn("gray", result)
        self.assertIn("Manual", result)


# =============================================================================
# PlantillasTareaAdmin
# =============================================================================

@patch('apps.reportes.admin.format_html', _plain_format_html)
class PlantillasTareaAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = PlantillasTareaAdmin(PlantillasTarea, self.site)

    def test_tipo_tarea_badge_reporte(self):
        obj = _mock_obj(tipo_tarea="Reporte")
        result = str(self.admin.tipo_tarea_badge(obj))
        self.assertIn("blue", result)

    def test_tipo_tarea_badge_backup(self):
        obj = _mock_obj(tipo_tarea="Backup")
        result = str(self.admin.tipo_tarea_badge(obj))
        self.assertIn("green", result)

    def test_tipo_tarea_badge_limpieza(self):
        obj = _mock_obj(tipo_tarea="Limpieza")
        result = str(self.admin.tipo_tarea_badge(obj))
        self.assertIn("orange", result)

    def test_tipo_tarea_badge_sincronizacion(self):
        obj = _mock_obj(tipo_tarea="Sincronización")
        result = str(self.admin.tipo_tarea_badge(obj))
        self.assertIn("purple", result)

    def test_tipo_tarea_badge_calculo(self):
        obj = _mock_obj(tipo_tarea="Cálculo")
        result = str(self.admin.tipo_tarea_badge(obj))
        self.assertIn("cyan", result)

    def test_tipo_tarea_badge_notificacion(self):
        obj = _mock_obj(tipo_tarea="Notificación")
        result = str(self.admin.tipo_tarea_badge(obj))
        self.assertIn("pink", result)

    def test_tipo_tarea_badge_personalizado(self):
        obj = _mock_obj(tipo_tarea="Personalizado")
        result = str(self.admin.tipo_tarea_badge(obj))
        self.assertIn("gray", result)

    def test_tipo_tarea_badge_desconocido(self):
        obj = _mock_obj(tipo_tarea="Otro")
        result = str(self.admin.tipo_tarea_badge(obj))
        self.assertIn("gray", result)

    def test_frecuencia_badge_cada_hora(self):
        obj = _mock_obj(frecuencia="Cada hora")
        result = str(self.admin.frecuencia_badge(obj))
        self.assertIn("green", result)

    def test_frecuencia_badge_diario(self):
        obj = _mock_obj(frecuencia="Diario")
        result = str(self.admin.frecuencia_badge(obj))
        self.assertIn("blue", result)

    def test_frecuencia_badge_semanal(self):
        obj = _mock_obj(frecuencia="Semanal")
        result = str(self.admin.frecuencia_badge(obj))
        self.assertIn("orange", result)

    def test_frecuencia_badge_mensual(self):
        obj = _mock_obj(frecuencia="Mensual")
        result = str(self.admin.frecuencia_badge(obj))
        self.assertIn("purple", result)

    def test_frecuencia_badge_personalizado(self):
        obj = _mock_obj(frecuencia="Personalizado")
        result = str(self.admin.frecuencia_badge(obj))
        self.assertIn("gray", result)

    def test_frecuencia_badge_desconocida(self):
        obj = _mock_obj(frecuencia="Otro")
        result = str(self.admin.frecuencia_badge(obj))
        self.assertIn("gray", result)

    def test_cron_display_con_cron(self):
        obj = _mock_obj(cron="0 * * * *")
        result = str(self.admin.cron_display(obj))
        self.assertIn("0 * * * *", result)

    def test_cron_display_sin_cron(self):
        obj = _mock_obj(cron=None)
        result = self.admin.cron_display(obj)
        self.assertEqual(result, "-")

    def test_timeout_display_horas(self):
        obj = _mock_obj(timeout=7200)  # 2h
        result = self.admin.timeout_display(obj)
        self.assertIn("2h", result)
        self.assertIn("0m", result)

    def test_timeout_display_minutos(self):
        obj = _mock_obj(timeout=150)  # 2m 30s
        result = self.admin.timeout_display(obj)
        self.assertIn("2m", result)
        self.assertIn("30s", result)

    def test_timeout_display_segundos(self):
        obj = _mock_obj(timeout=45)
        result = self.admin.timeout_display(obj)
        self.assertIn("45s", result)

    def test_timeout_display_sin_timeout(self):
        obj = _mock_obj(timeout=None)
        result = self.admin.timeout_display(obj)
        self.assertEqual(result, "-")

    def test_activo_badge_activo(self):
        obj = _mock_obj(estado=True)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("green", result)

    def test_activo_badge_inactivo(self):
        obj = _mock_obj(estado=False)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("red", result)


# =============================================================================
# EjecucionesTareaAdmin
# =============================================================================

@patch('apps.reportes.admin.format_html', _plain_format_html)
class EjecucionesTareaAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = EjecucionesTareaAdmin(EjecucionesTarea, self.site)

    def test_estado_badge_pendiente(self):
        obj = _mock_obj(estado="Pendiente")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("orange", result)
        self.assertIn("Pendiente", result)

    def test_estado_badge_ejecutando(self):
        obj = _mock_obj(estado="Ejecutando")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("blue", result)

    def test_estado_badge_exitoso(self):
        obj = _mock_obj(estado="Exitoso")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("green", result)

    def test_estado_badge_fallido(self):
        obj = _mock_obj(estado="Fallido")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("red", result)

    def test_estado_badge_cancelado(self):
        obj = _mock_obj(estado="Cancelado")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("gray", result)

    def test_estado_badge_timeout(self):
        obj = _mock_obj(estado="Timeout")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("darkred", result)

    def test_estado_badge_desconocido(self):
        obj = _mock_obj(estado="Otro")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("gray", result)

    def test_duracion_display_horas(self):
        obj = _mock_obj(duracion_seg=3661)  # 1h 1m 1s
        result = str(self.admin.duracion_display(obj))
        self.assertIn("1h", result)
        self.assertIn("1m", result)
        self.assertIn("1s", result)

    def test_duracion_display_minutos(self):
        obj = _mock_obj(duracion_seg=90)  # 1m 30s
        result = str(self.admin.duracion_display(obj))
        self.assertIn("1m", result)
        self.assertIn("30s", result)

    def test_duracion_display_segundos(self):
        obj = _mock_obj(duracion_seg=15)
        result = str(self.admin.duracion_display(obj))
        self.assertIn("15s", result)

    def test_duracion_display_none(self):
        obj = _mock_obj(duracion_seg=None)
        result = self.admin.duracion_display(obj)
        self.assertEqual(result, "-")

    def test_duracion_display_cero(self):
        obj = _mock_obj(duracion_seg=0)
        result = str(self.admin.duracion_display(obj))
        self.assertIn("0s", result)


# =============================================================================
# DestinatariosTareaAdmin
# =============================================================================

@patch('apps.reportes.admin.format_html', _plain_format_html)
class DestinatariosTareaAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = DestinatariosTareaAdmin(DestinatariosTarea, self.site)

    def test_notif_inicio_badge_si(self):
        obj = _mock_obj(notif_inicio=1)
        result = str(self.admin.notif_inicio_badge(obj))
        self.assertIn("green", result)

    def test_notif_inicio_badge_no(self):
        obj = _mock_obj(notif_inicio=0)
        result = str(self.admin.notif_inicio_badge(obj))
        self.assertIn("lightgray", result)

    def test_notif_fin_badge_si(self):
        obj = _mock_obj(notif_fin=1)
        result = str(self.admin.notif_fin_badge(obj))
        self.assertIn("green", result)

    def test_notif_fin_badge_no(self):
        obj = _mock_obj(notif_fin=0)
        result = str(self.admin.notif_fin_badge(obj))
        self.assertIn("lightgray", result)

    def test_notif_error_badge_si(self):
        obj = _mock_obj(notif_error=1)
        result = str(self.admin.notif_error_badge(obj))
        self.assertIn("red", result)

    def test_notif_error_badge_no(self):
        obj = _mock_obj(notif_error=0)
        result = str(self.admin.notif_error_badge(obj))
        self.assertIn("lightgray", result)
