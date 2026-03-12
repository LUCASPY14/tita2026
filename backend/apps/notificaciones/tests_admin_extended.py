"""
Tests for apps/notificaciones/admin.py
Covers all custom display methods across 15 admin classes.
"""
from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.contrib.admin.sites import AdminSite

from apps.notificaciones.admin import (
    NotificacionesPortalAdmin,
    NotificacionesSaldoAdmin,
    SolicitudesNotificacionAdmin,
    PreferenciasNotificacionAdmin,
    EmailsEnviadosAdmin,
    SmsEnviadosAdmin,
    PlantillasEmailAdmin,
    PlantillasSmsAdmin,
    CampanasComunicacionAdmin,
    AlertasAutomaticasAdmin,
    AlertaDestinatariosAdmin,
    AlertasSistemaAdmin,
    HistorialAlertasAdmin,
    AnomaliasDetectadasAdmin,
    RestriccionesHorariasAdmin,
)
from apps.notificaciones.models import (
    NotificacionesPortal,
    NotificacionesSaldo,
    SolicitudesNotificacion,
    PreferenciasNotificacion,
    EmailsEnviados,
    SmsEnviados,
    PlantillasEmail,
    PlantillasSms,
    CampanasComunicacion,
    AlertasAutomaticas,
    AlertaDestinatarios,
    AlertasSistema,
    HistorialAlertas,
    AnomaliasDetectadas,
    RestriccionesHorarias,
)

_plain_format_html = lambda fmt, *a, **k: fmt.format(*a, **k)


def _mock_obj(**kwargs):
    obj = MagicMock()
    for k, v in kwargs.items():
        setattr(obj, k, v)
    return obj


# =============================================================================
# NotificacionesPortalAdmin
# =============================================================================

@patch('apps.notificaciones.admin.format_html', _plain_format_html)
class NotificacionesPortalAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = NotificacionesPortalAdmin(NotificacionesPortal, self.site)

    def test_tipo_badge_alerta(self):
        obj = _mock_obj(tipo="alerta")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("red", result)
        self.assertIn("alerta", result)

    def test_tipo_badge_recordatorio(self):
        obj = _mock_obj(tipo="recordatorio")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("orange", result)

    def test_tipo_badge_venta(self):
        obj = _mock_obj(tipo="venta")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("green", result)

    def test_tipo_badge_compra(self):
        obj = _mock_obj(tipo="compra")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("blue", result)

    def test_tipo_badge_inventario(self):
        obj = _mock_obj(tipo="inventario")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("purple", result)

    def test_tipo_badge_pago(self):
        obj = _mock_obj(tipo="pago")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("green", result)

    def test_tipo_badge_saldo(self):
        obj = _mock_obj(tipo="saldo")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("orange", result)

    def test_tipo_badge_sistema(self):
        obj = _mock_obj(tipo="sistema")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("gray", result)

    def test_tipo_badge_promocion(self):
        obj = _mock_obj(tipo="promocion")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("pink", result)

    def test_tipo_badge_informativa(self):
        obj = _mock_obj(tipo="informativa")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("lightblue", result)

    def test_tipo_badge_desconocido(self):
        obj = _mock_obj(tipo="OTRO")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("gray", result)

    def test_leida_badge_leida(self):
        obj = _mock_obj(leida=1)
        result = str(self.admin.leida_badge(obj))
        self.assertIn("green", result)
        self.assertIn("Leída", result)

    def test_leida_badge_no_leida(self):
        obj = _mock_obj(leida=0)
        result = str(self.admin.leida_badge(obj))
        self.assertIn("orange", result)
        self.assertIn("No Leída", result)


# =============================================================================
# NotificacionesSaldoAdmin
# =============================================================================

@patch('apps.notificaciones.admin.format_html', _plain_format_html)
class NotificacionesSaldoAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = NotificacionesSaldoAdmin(NotificacionesSaldo, self.site)

    def test_saldo_actual_badge_bajo(self):
        obj = _mock_obj(saldo_actual=30000)
        result = str(self.admin.saldo_actual_badge(obj))
        self.assertIn("red", result)
        self.assertIn("30,000", result)

    def test_saldo_actual_badge_medio(self):
        obj = _mock_obj(saldo_actual=75000)
        result = str(self.admin.saldo_actual_badge(obj))
        self.assertIn("orange", result)
        self.assertIn("75,000", result)

    def test_saldo_actual_badge_alto(self):
        obj = _mock_obj(saldo_actual=200000)
        result = str(self.admin.saldo_actual_badge(obj))
        self.assertIn("green", result)
        self.assertIn("200,000", result)

    def test_saldo_actual_badge_exactamente_50000(self):
        obj = _mock_obj(saldo_actual=50000)
        result = str(self.admin.saldo_actual_badge(obj))
        self.assertIn("orange", result)

    def test_saldo_actual_badge_exactamente_100000(self):
        obj = _mock_obj(saldo_actual=100000)
        result = str(self.admin.saldo_actual_badge(obj))
        self.assertIn("green", result)

    def test_leida_badge_leida(self):
        obj = _mock_obj(leida=1)
        result = str(self.admin.leida_badge(obj))
        self.assertIn("green", result)
        self.assertIn("Leída", result)

    def test_leida_badge_no_leida(self):
        obj = _mock_obj(leida=0)
        result = str(self.admin.leida_badge(obj))
        self.assertIn("orange", result)
        self.assertIn("No Leída", result)


# =============================================================================
# SolicitudesNotificacionAdmin
# =============================================================================

@patch('apps.notificaciones.admin.format_html', _plain_format_html)
class SolicitudesNotificacionAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = SolicitudesNotificacionAdmin(SolicitudesNotificacion, self.site)

    def test_saldo_alerta_badge(self):
        obj = _mock_obj(saldo_alerta=150000)
        result = str(self.admin.saldo_alerta_badge(obj))
        self.assertIn("orange", result)
        self.assertIn("150,000", result)

    def test_estado_badge_pendiente(self):
        obj = _mock_obj(estado="Pendiente")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("orange", result)
        self.assertIn("Pendiente", result)

    def test_estado_badge_enviada(self):
        obj = _mock_obj(estado="Enviada")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("green", result)

    def test_estado_badge_cancelada(self):
        obj = _mock_obj(estado="Cancelada")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("red", result)

    def test_estado_badge_desconocido(self):
        obj = _mock_obj(estado="Otro")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("gray", result)

    def test_estado_badge_none(self):
        obj = _mock_obj(estado=None)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("Sin Estado", result)


# =============================================================================
# PreferenciasNotificacionAdmin
# =============================================================================

@patch('apps.notificaciones.admin.format_html', _plain_format_html)
class PreferenciasNotificacionAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = PreferenciasNotificacionAdmin(PreferenciasNotificacion, self.site)

    def test_email_activo_badge_activo(self):
        obj = _mock_obj(email_activo=1)
        result = str(self.admin.email_activo_badge(obj))
        self.assertIn("green", result)
        self.assertIn("Activo", result)

    def test_email_activo_badge_inactivo(self):
        obj = _mock_obj(email_activo=0)
        result = str(self.admin.email_activo_badge(obj))
        self.assertIn("gray", result)
        self.assertIn("Inactivo", result)

    def test_push_activo_badge_activo(self):
        obj = _mock_obj(push_activo=1)
        result = str(self.admin.push_activo_badge(obj))
        self.assertIn("green", result)
        self.assertIn("Activo", result)

    def test_push_activo_badge_inactivo(self):
        obj = _mock_obj(push_activo=0)
        result = str(self.admin.push_activo_badge(obj))
        self.assertIn("gray", result)
        self.assertIn("Inactivo", result)


# =============================================================================
# EmailsEnviadosAdmin
# =============================================================================

@patch('apps.notificaciones.admin.format_html', _plain_format_html)
class EmailsEnviadosAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = EmailsEnviadosAdmin(EmailsEnviados, self.site)

    def test_estado_badge_pendiente(self):
        obj = _mock_obj(estado="Pendiente")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("orange", result)

    def test_estado_badge_enviado(self):
        obj = _mock_obj(estado="Enviado")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("blue", result)

    def test_estado_badge_entregado(self):
        obj = _mock_obj(estado="Entregado")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("green", result)

    def test_estado_badge_fallido(self):
        obj = _mock_obj(estado="Fallido")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("red", result)

    def test_estado_badge_rebotado(self):
        obj = _mock_obj(estado="Rebotado")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("darkred", result)

    def test_estado_badge_abierto(self):
        obj = _mock_obj(estado="Abierto")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("lightgreen", result)

    def test_estado_badge_spam(self):
        obj = _mock_obj(estado="Marcado_Spam")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("gray", result)

    def test_estado_badge_desconocido(self):
        obj = _mock_obj(estado="Otro")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("gray", result)

    def test_intentos_badge_muchos(self):
        obj = _mock_obj(intentos=5)
        result = str(self.admin.intentos_badge(obj))
        self.assertIn("red", result)
        self.assertIn("5", result)

    def test_intentos_badge_pocos(self):
        obj = _mock_obj(intentos=2)
        result = str(self.admin.intentos_badge(obj))
        self.assertIn("orange", result)

    def test_intentos_badge_uno(self):
        obj = _mock_obj(intentos=1)
        result = str(self.admin.intentos_badge(obj))
        self.assertIn("green", result)

    def test_intentos_badge_exactamente_3(self):
        obj = _mock_obj(intentos=3)
        result = str(self.admin.intentos_badge(obj))
        self.assertIn("orange", result)

    def test_intentos_badge_exactamente_4(self):
        obj = _mock_obj(intentos=4)
        result = str(self.admin.intentos_badge(obj))
        self.assertIn("red", result)


# =============================================================================
# SmsEnviadosAdmin
# =============================================================================

@patch('apps.notificaciones.admin.format_html', _plain_format_html)
class SmsEnviadosAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = SmsEnviadosAdmin(SmsEnviados, self.site)

    def test_mensaje_preview_corto(self):
        obj = _mock_obj(mensaje="Hola mundo")
        result = self.admin.mensaje_preview(obj)
        self.assertEqual(result, "Hola mundo")

    def test_mensaje_preview_largo(self):
        obj = _mock_obj(mensaje="A" * 60)
        result = self.admin.mensaje_preview(obj)
        self.assertTrue(result.endswith("..."))
        self.assertEqual(len(result), 53)

    def test_mensaje_preview_exactamente_50(self):
        obj = _mock_obj(mensaje="A" * 50)
        result = self.admin.mensaje_preview(obj)
        self.assertEqual(result, "A" * 50)

    def test_estado_badge_pendiente(self):
        obj = _mock_obj(estado="Pendiente")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("orange", result)

    def test_estado_badge_enviado(self):
        obj = _mock_obj(estado="Enviado")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("blue", result)

    def test_estado_badge_entregado(self):
        obj = _mock_obj(estado="Entregado")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("green", result)

    def test_estado_badge_fallido(self):
        obj = _mock_obj(estado="Fallido")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("red", result)

    def test_estado_badge_rechazado(self):
        obj = _mock_obj(estado="Rechazado")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("darkred", result)

    def test_estado_badge_desconocido(self):
        obj = _mock_obj(estado="Otro")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("gray", result)

    def test_costo_badge_con_costo(self):
        obj = _mock_obj(costo=500)
        result = str(self.admin.costo_badge(obj))
        self.assertIn("green", result)
        self.assertIn("500", result)

    def test_costo_badge_sin_costo(self):
        obj = _mock_obj(costo=None)
        result = self.admin.costo_badge(obj)
        self.assertEqual(result, "-")

    def test_costo_badge_cero(self):
        obj = _mock_obj(costo=0)
        result = self.admin.costo_badge(obj)
        # 0 is falsy, so returns "-"
        self.assertEqual(result, "-")


# =============================================================================
# PlantillasEmailAdmin
# =============================================================================

@patch('apps.notificaciones.admin.format_html', _plain_format_html)
class PlantillasEmailAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = PlantillasEmailAdmin(PlantillasEmail, self.site)

    def test_activo_badge_activo(self):
        obj = _mock_obj(activo=True)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("green", result)
        self.assertIn("Activo", result)

    def test_activo_badge_inactivo(self):
        obj = _mock_obj(activo=False)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("red", result)
        self.assertIn("Inactivo", result)

    def test_variables_count_con_variables(self):
        obj = _mock_obj(variables=["a", "b", "c"])
        result = str(self.admin.variables_count(obj))
        self.assertIn("3", result)
        self.assertIn("variables", result)

    def test_variables_count_sin_variables(self):
        obj = _mock_obj(variables=None)
        result = str(self.admin.variables_count(obj))
        self.assertIn("0", result)

    def test_variables_count_lista_vacia(self):
        obj = _mock_obj(variables=[])
        result = str(self.admin.variables_count(obj))
        self.assertIn("0", result)


# =============================================================================
# PlantillasSmsAdmin
# =============================================================================

@patch('apps.notificaciones.admin.format_html', _plain_format_html)
class PlantillasSmsAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = PlantillasSmsAdmin(PlantillasSms, self.site)

    def test_mensaje_preview_corto(self):
        obj = _mock_obj(mensaje="Hola")
        result = self.admin.mensaje_preview(obj)
        self.assertEqual(result, "Hola")

    def test_mensaje_preview_largo(self):
        obj = _mock_obj(mensaje="B" * 70)
        result = self.admin.mensaje_preview(obj)
        self.assertTrue(result.endswith("..."))
        self.assertEqual(len(result), 53)

    def test_activo_badge_activo(self):
        obj = _mock_obj(activo=True)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("green", result)

    def test_activo_badge_inactivo(self):
        obj = _mock_obj(activo=False)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("red", result)

    def test_variables_count_con_variables(self):
        obj = _mock_obj(variables={"key1": "val1", "key2": "val2"})
        result = str(self.admin.variables_count(obj))
        self.assertIn("2", result)

    def test_variables_count_sin_variables(self):
        obj = _mock_obj(variables=None)
        result = str(self.admin.variables_count(obj))
        self.assertIn("0", result)


# =============================================================================
# CampanasComunicacionAdmin
# =============================================================================

@patch('apps.notificaciones.admin.format_html', _plain_format_html)
class CampanasComunicacionAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = CampanasComunicacionAdmin(CampanasComunicacion, self.site)

    def test_tipo_badge_email(self):
        obj = _mock_obj(tipo="Email")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("blue", result)
        self.assertIn("Email", result)

    def test_tipo_badge_sms(self):
        obj = _mock_obj(tipo="SMS")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("green", result)

    def test_tipo_badge_mixta(self):
        obj = _mock_obj(tipo="Mixta")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("purple", result)

    def test_tipo_badge_push(self):
        obj = _mock_obj(tipo="Push")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("orange", result)

    def test_tipo_badge_desconocido(self):
        obj = _mock_obj(tipo="Otro")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("gray", result)

    def test_estado_badge_borrador(self):
        obj = _mock_obj(estado="Borrador")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("gray", result)

    def test_estado_badge_programada(self):
        obj = _mock_obj(estado="Programada")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("blue", result)

    def test_estado_badge_enviando(self):
        obj = _mock_obj(estado="Enviando")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("orange", result)

    def test_estado_badge_enviada(self):
        obj = _mock_obj(estado="Enviada")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("green", result)

    def test_estado_badge_cancelada(self):
        obj = _mock_obj(estado="Cancelada")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("red", result)

    def test_estado_badge_fallida(self):
        obj = _mock_obj(estado="Fallida")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("darkred", result)

    def test_estado_badge_desconocido(self):
        obj = _mock_obj(estado="Otro")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("gray", result)

    def test_tasa_entrega_alta(self):
        obj = _mock_obj(total_enviados=100, total_entregados=95)
        result = str(self.admin.tasa_entrega(obj))
        self.assertIn("green", result)
        self.assertIn("95.0%", result)

    def test_tasa_entrega_media(self):
        obj = _mock_obj(total_enviados=100, total_entregados=75)
        result = str(self.admin.tasa_entrega(obj))
        self.assertIn("orange", result)
        self.assertIn("75.0%", result)

    def test_tasa_entrega_baja(self):
        obj = _mock_obj(total_enviados=100, total_entregados=50)
        result = str(self.admin.tasa_entrega(obj))
        self.assertIn("red", result)
        self.assertIn("50.0%", result)

    def test_tasa_entrega_sin_enviados(self):
        obj = _mock_obj(total_enviados=0, total_entregados=0)
        result = self.admin.tasa_entrega(obj)
        self.assertEqual(result, "-")

    def test_tasa_entrega_exactamente_90(self):
        obj = _mock_obj(total_enviados=100, total_entregados=90)
        result = str(self.admin.tasa_entrega(obj))
        self.assertIn("green", result)

    def test_tasa_entrega_exactamente_70(self):
        obj = _mock_obj(total_enviados=100, total_entregados=70)
        result = str(self.admin.tasa_entrega(obj))
        self.assertIn("orange", result)


# =============================================================================
# AlertasAutomaticasAdmin
# =============================================================================

@patch('apps.notificaciones.admin.format_html', _plain_format_html)
class AlertasAutomaticasAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = AlertasAutomaticasAdmin(AlertasAutomaticas, self.site)

    def test_tipo_alerta_badge_inventario(self):
        obj = _mock_obj(tipo_alerta="Inventario")
        result = str(self.admin.tipo_alerta_badge(obj))
        self.assertIn("purple", result)

    def test_tipo_alerta_badge_ventas(self):
        obj = _mock_obj(tipo_alerta="Ventas")
        result = str(self.admin.tipo_alerta_badge(obj))
        self.assertIn("green", result)

    def test_tipo_alerta_badge_compras(self):
        obj = _mock_obj(tipo_alerta="Compras")
        result = str(self.admin.tipo_alerta_badge(obj))
        self.assertIn("blue", result)

    def test_tipo_alerta_badge_saldo(self):
        obj = _mock_obj(tipo_alerta="Saldo")
        result = str(self.admin.tipo_alerta_badge(obj))
        self.assertIn("orange", result)

    def test_tipo_alerta_badge_sistema(self):
        obj = _mock_obj(tipo_alerta="Sistema")
        result = str(self.admin.tipo_alerta_badge(obj))
        self.assertIn("red", result)

    def test_tipo_alerta_badge_seguridad(self):
        obj = _mock_obj(tipo_alerta="Seguridad")
        result = str(self.admin.tipo_alerta_badge(obj))
        self.assertIn("darkred", result)

    def test_tipo_alerta_badge_desconocido(self):
        obj = _mock_obj(tipo_alerta="Otro")
        result = str(self.admin.tipo_alerta_badge(obj))
        self.assertIn("gray", result)

    def test_criticidad_badge_baja(self):
        obj = _mock_obj(criticidad="Baja")
        result = str(self.admin.criticidad_badge(obj))
        self.assertIn("green", result)
        self.assertIn("Baja", result)

    def test_criticidad_badge_media(self):
        obj = _mock_obj(criticidad="Media")
        result = str(self.admin.criticidad_badge(obj))
        self.assertIn("orange", result)

    def test_criticidad_badge_alta(self):
        obj = _mock_obj(criticidad="Alta")
        result = str(self.admin.criticidad_badge(obj))
        self.assertIn("darkorange", result)

    def test_criticidad_badge_critica(self):
        obj = _mock_obj(criticidad="Crítica")
        result = str(self.admin.criticidad_badge(obj))
        self.assertIn("red", result)

    def test_criticidad_badge_desconocida(self):
        obj = _mock_obj(criticidad="Otra")
        result = str(self.admin.criticidad_badge(obj))
        self.assertIn("gray", result)

    def test_activo_badge_activo(self):
        obj = _mock_obj(activo=True)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("green", result)

    def test_activo_badge_inactivo(self):
        obj = _mock_obj(activo=False)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("red", result)


# =============================================================================
# AlertaDestinatariosAdmin
# =============================================================================

@patch('apps.notificaciones.admin.format_html', _plain_format_html)
class AlertaDestinatariosAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = AlertaDestinatariosAdmin(AlertaDestinatarios, self.site)

    def test_via_email_badge_activo(self):
        obj = _mock_obj(via_email=1)
        result = str(self.admin.via_email_badge(obj))
        self.assertIn("green", result)
        self.assertIn("Email", result)

    def test_via_email_badge_inactivo(self):
        obj = _mock_obj(via_email=0)
        result = str(self.admin.via_email_badge(obj))
        self.assertIn("gray", result)

    def test_via_sistema_badge_activo(self):
        obj = _mock_obj(via_sistema=1)
        result = str(self.admin.via_sistema_badge(obj))
        self.assertIn("green", result)
        self.assertIn("Sistema", result)

    def test_via_sistema_badge_inactivo(self):
        obj = _mock_obj(via_sistema=0)
        result = str(self.admin.via_sistema_badge(obj))
        self.assertIn("gray", result)

    def test_activo_badge_activo(self):
        obj = _mock_obj(activo=True)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("green", result)

    def test_activo_badge_inactivo(self):
        obj = _mock_obj(activo=False)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("red", result)


# =============================================================================
# AlertasSistemaAdmin
# =============================================================================

@patch('apps.notificaciones.admin.format_html', _plain_format_html)
class AlertasSistemaAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = AlertasSistemaAdmin(AlertasSistema, self.site)

    def test_mensaje_preview_corto(self):
        obj = _mock_obj(mensaje="Error simple")
        result = self.admin.mensaje_preview(obj)
        self.assertEqual(result, "Error simple")

    def test_mensaje_preview_largo(self):
        obj = _mock_obj(mensaje="C" * 80)
        result = self.admin.mensaje_preview(obj)
        self.assertTrue(result.endswith("..."))
        self.assertEqual(len(result), 63)

    def test_mensaje_preview_exactamente_60(self):
        obj = _mock_obj(mensaje="C" * 60)
        result = self.admin.mensaje_preview(obj)
        self.assertEqual(result, "C" * 60)

    def test_tipo_badge_error(self):
        obj = _mock_obj(tipo="error")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("red", result)

    def test_tipo_badge_warning(self):
        obj = _mock_obj(tipo="warning")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("orange", result)

    def test_tipo_badge_info(self):
        obj = _mock_obj(tipo="info")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("blue", result)

    def test_tipo_badge_success(self):
        obj = _mock_obj(tipo="success")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("green", result)

    def test_tipo_badge_critical(self):
        obj = _mock_obj(tipo="critical")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("darkred", result)

    def test_tipo_badge_desconocido(self):
        obj = _mock_obj(tipo="otro")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("gray", result)

    def test_tipo_badge_uppercase(self):
        # tipo.lower() is used before dict lookup
        obj = _mock_obj(tipo="ERROR")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("red", result)

    def test_estado_badge_pendiente(self):
        obj = _mock_obj(estado="Pendiente")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("orange", result)

    def test_estado_badge_resuelta(self):
        obj = _mock_obj(estado="Resuelta")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("green", result)

    def test_estado_badge_ignorada(self):
        obj = _mock_obj(estado="Ignorada")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("gray", result)

    def test_estado_badge_desconocido(self):
        obj = _mock_obj(estado="Otro")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("gray", result)

    def test_estado_badge_none(self):
        obj = _mock_obj(estado=None)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("Sin Estado", result)


# =============================================================================
# HistorialAlertasAdmin
# =============================================================================

@patch('apps.notificaciones.admin.format_html', _plain_format_html)
class HistorialAlertasAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = HistorialAlertasAdmin(HistorialAlertas, self.site)

    def test_resuelto_badge_resuelto(self):
        obj = _mock_obj(resuelto=1)
        result = str(self.admin.resuelto_badge(obj))
        self.assertIn("green", result)
        self.assertIn("Resuelto", result)

    def test_resuelto_badge_pendiente(self):
        obj = _mock_obj(resuelto=0)
        result = str(self.admin.resuelto_badge(obj))
        self.assertIn("orange", result)
        self.assertIn("Pendiente", result)


# =============================================================================
# AnomaliasDetectadasAdmin
# =============================================================================

@patch('apps.notificaciones.admin.format_html', _plain_format_html)
class AnomaliasDetectadasAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = AnomaliasDetectadasAdmin(AnomaliasDetectadas, self.site)

    def test_tipo_anomalia_badge_acceso_inusual(self):
        obj = _mock_obj(tipo_anomalia="acceso_inusual")
        result = str(self.admin.tipo_anomalia_badge(obj))
        self.assertIn("orange", result)

    def test_tipo_anomalia_badge_intentos_fallidos(self):
        obj = _mock_obj(tipo_anomalia="intentos_fallidos")
        result = str(self.admin.tipo_anomalia_badge(obj))
        self.assertIn("red", result)

    def test_tipo_anomalia_badge_cambio_horario(self):
        obj = _mock_obj(tipo_anomalia="cambio_horario")
        result = str(self.admin.tipo_anomalia_badge(obj))
        self.assertIn("blue", result)

    def test_tipo_anomalia_badge_ip_sospechosa(self):
        obj = _mock_obj(tipo_anomalia="ip_sospechosa")
        result = str(self.admin.tipo_anomalia_badge(obj))
        self.assertIn("darkred", result)

    def test_tipo_anomalia_badge_multiples_sesiones(self):
        obj = _mock_obj(tipo_anomalia="múltiples_sesiones")
        result = str(self.admin.tipo_anomalia_badge(obj))
        self.assertIn("purple", result)

    def test_tipo_anomalia_badge_actividad_alta(self):
        obj = _mock_obj(tipo_anomalia="actividad_alta")
        result = str(self.admin.tipo_anomalia_badge(obj))
        self.assertIn("pink", result)

    def test_tipo_anomalia_badge_desconocido(self):
        obj = _mock_obj(tipo_anomalia="otro")
        result = str(self.admin.tipo_anomalia_badge(obj))
        self.assertIn("gray", result)

    def test_tipo_anomalia_badge_uppercase(self):
        # .lower() applied before dict lookup
        obj = _mock_obj(tipo_anomalia="ACCESO_INUSUAL")
        result = str(self.admin.tipo_anomalia_badge(obj))
        self.assertIn("orange", result)

    def test_nivel_riesgo_badge_bajo(self):
        obj = _mock_obj(nivel_riesgo="Bajo")
        result = str(self.admin.nivel_riesgo_badge(obj))
        self.assertIn("green", result)
        self.assertIn("Bajo", result)

    def test_nivel_riesgo_badge_medio(self):
        obj = _mock_obj(nivel_riesgo="Medio")
        result = str(self.admin.nivel_riesgo_badge(obj))
        self.assertIn("orange", result)

    def test_nivel_riesgo_badge_alto(self):
        obj = _mock_obj(nivel_riesgo="Alto")
        result = str(self.admin.nivel_riesgo_badge(obj))
        self.assertIn("darkorange", result)

    def test_nivel_riesgo_badge_critico(self):
        obj = _mock_obj(nivel_riesgo="Crítico")
        result = str(self.admin.nivel_riesgo_badge(obj))
        self.assertIn("red", result)

    def test_nivel_riesgo_badge_desconocido(self):
        obj = _mock_obj(nivel_riesgo="Otro")
        result = str(self.admin.nivel_riesgo_badge(obj))
        self.assertIn("gray", result)

    def test_notificado_badge_si(self):
        obj = _mock_obj(notificado=1)
        result = str(self.admin.notificado_badge(obj))
        self.assertIn("green", result)
        self.assertIn("Notificado", result)

    def test_notificado_badge_no(self):
        obj = _mock_obj(notificado=0)
        result = str(self.admin.notificado_badge(obj))
        self.assertIn("orange", result)
        self.assertIn("Sin Notificar", result)


# =============================================================================
# RestriccionesHorariasAdmin
# =============================================================================

@patch('apps.notificaciones.admin.format_html', _plain_format_html)
class RestriccionesHorariasAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = RestriccionesHorariasAdmin(RestriccionesHorarias, self.site)

    def test_rango_horario(self):
        hora_inicio = MagicMock()
        hora_inicio.strftime.return_value = "08:00"
        hora_fin = MagicMock()
        hora_fin.strftime.return_value = "17:00"
        obj = _mock_obj(hora_inicio=hora_inicio, hora_fin=hora_fin)
        result = str(self.admin.rango_horario(obj))
        self.assertIn("08:00", result)
        self.assertIn("17:00", result)

    def test_activo_badge_activo(self):
        obj = _mock_obj(activo=True)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("green", result)

    def test_activo_badge_inactivo(self):
        obj = _mock_obj(activo=False)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("red", result)
