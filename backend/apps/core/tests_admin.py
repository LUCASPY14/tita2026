"""Tests for apps/core/admin.py - covers custom display methods in all ModelAdmin classes."""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from apps.core.admin import (
    CacheConfiguracionAdmin,
    CargasSaldoAdmin,
    ConsumosTarjetaAdmin,
    ConfiguracionSistemaAdmin,
    LimitesTransaccionAdmin,
    MediosPagoAdmin,
    RegistroAutorizacionesAdmin,
    TarjetasAdmin,
    TarjetasAutorizacionAdmin,
    TransaccionesOnlineAdmin,
)

# format_html with format specs like {:,.2f} fails with Django's conditional_escape
# because it converts numerics to SafeString before applying format specs.
# Patch format_html in admin module to call str.format directly for testing.
_plain_format_html = lambda fmt, *a, **k: fmt.format(*a, **k)


def _mock_obj(**kwargs):
    """Create a MagicMock object with given attributes."""
    obj = MagicMock()
    for k, v in kwargs.items():
        setattr(obj, k, v)
    return obj


@patch('apps.core.admin.format_html', _plain_format_html)
class TarjetasAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = TarjetasAdmin(
            __import__("apps.core.models", fromlist=["Tarjetas"]).Tarjetas, self.site
        )

    def test_nro_tarjeta_badge(self):
        obj = _mock_obj(nro_tarjeta="T001")
        result = str(self.admin.nro_tarjeta_badge(obj))
        self.assertIn("T001", result)

    def test_hijo_info_con_hijo(self):
        hijo = _mock_obj(nombre="Juan", apellido="Perez", id_hijo=1)
        obj = _mock_obj(id_hijo=hijo)
        result = str(self.admin.hijo_info(obj))
        self.assertIn("Juan", result)
        self.assertIn("Perez", result)

    def test_hijo_info_sin_hijo(self):
        obj = _mock_obj(id_hijo=None)
        result = self.admin.hijo_info(obj)
        self.assertEqual(result, "-")

    def test_saldo_display_positivo(self):
        obj = _mock_obj(saldo_actual=Decimal("500.00"))
        result = str(self.admin.saldo_display(obj))
        self.assertIn("28a745", result)  # green color for positive
        self.assertIn("500.00", result)

    def test_saldo_display_negativo(self):
        obj = _mock_obj(saldo_actual=Decimal("-100.00"))
        result = str(self.admin.saldo_display(obj))
        self.assertIn("dc3545", result)  # red color for negative
        self.assertIn("100.00", result)

    def test_saldo_disponible_display(self):
        obj = _mock_obj(saldo_disponible=Decimal("300.00"))
        result = str(self.admin.saldo_disponible_display(obj))
        self.assertIn("300.00", result)

    def test_estado_badge_activa(self):
        obj = _mock_obj(estado="Activa")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("28a745", result)
        self.assertIn("ACTIVA", result)

    def test_estado_badge_bloqueada(self):
        obj = _mock_obj(estado="Bloqueada")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("ffc107", result)

    def test_estado_badge_cancelada(self):
        obj = _mock_obj(estado="Cancelada")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("dc3545", result)

    def test_estado_badge_desconocido(self):
        obj = _mock_obj(estado="Otro")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("6c757d", result)

    def test_alerta_saldo_en_alerta(self):
        obj = _mock_obj(esta_en_alerta=True)
        result = str(self.admin.alerta_saldo(obj))
        self.assertIn("Saldo bajo", result)

    def test_alerta_saldo_ok(self):
        obj = _mock_obj(esta_en_alerta=False)
        result = str(self.admin.alerta_saldo(obj))
        self.assertIn("OK", result)

    def test_fecha_vencimiento_vencida(self):
        obj = _mock_obj(fecha_vencimiento=date(2020, 1, 1))
        result = str(self.admin.fecha_vencimiento_display(obj))
        self.assertIn("VENCIDA", result)
        self.assertIn("dc3545", result)

    def test_fecha_vencimiento_proxima(self):
        obj = _mock_obj(fecha_vencimiento=date.today() + timedelta(days=10))
        result = str(self.admin.fecha_vencimiento_display(obj))
        self.assertIn("Próxima", result)
        self.assertIn("ffc107", result)

    def test_fecha_vencimiento_ok(self):
        obj = _mock_obj(fecha_vencimiento=date.today() + timedelta(days=90))
        result = str(self.admin.fecha_vencimiento_display(obj))
        self.assertIn("28a745", result)

    def test_fecha_vencimiento_none(self):
        obj = _mock_obj(fecha_vencimiento=None)
        result = self.admin.fecha_vencimiento_display(obj)
        self.assertEqual(result, "-")


@patch('apps.core.admin.format_html', _plain_format_html)
class TarjetasAutorizacionAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        from apps.core.models import TarjetasAutorizacion
        self.admin = TarjetasAutorizacionAdmin(TarjetasAutorizacion, self.site)

    def test_codigo_barra_badge(self):
        obj = _mock_obj(codigo_barra="CB007")
        result = str(self.admin.codigo_barra_badge(obj))
        self.assertIn("CB007", result)

    def test_tipo_badge_supervisor(self):
        obj = _mock_obj(tipo_autorizacion="Supervisor")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("17a2b8", result)
        self.assertIn("SUPERVISOR", result)

    def test_tipo_badge_gerente(self):
        obj = _mock_obj(tipo_autorizacion="Gerente")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("6610f2", result)

    def test_tipo_badge_desconocido(self):
        obj = _mock_obj(tipo_autorizacion="Otro")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("6c757d", result)

    def test_empleado_info_con_empleado(self):
        empleado = _mock_obj(nombre="Ana", apellido="Garcia")
        obj = _mock_obj(id_empleado=empleado)
        result = str(self.admin.empleado_info(obj))
        self.assertIn("Ana", result)

    def test_empleado_info_sin_empleado(self):
        obj = _mock_obj(id_empleado=None)
        result = self.admin.empleado_info(obj)
        self.assertEqual(result, "-")

    def test_permisos_badge_con_permisos(self):
        obj = _mock_obj(
            puede_anular_almuerzos=True,
            puede_anular_ventas=True,
            puede_anular_recargas=False,
            puede_modificar_precios=True,
        )
        result = str(self.admin.permisos_badge(obj))
        self.assertIn("Almuerzos", result)
        self.assertIn("Ventas", result)
        self.assertIn("Precios", result)

    def test_permisos_badge_sin_permisos(self):
        obj = _mock_obj(
            puede_anular_almuerzos=False,
            puede_anular_ventas=False,
            puede_anular_recargas=False,
            puede_modificar_precios=False,
        )
        result = str(self.admin.permisos_badge(obj))
        self.assertIn("Sin permisos", result)

    def test_estado_badge_activo(self):
        obj = _mock_obj(activo=True)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("ACTIVA", result)
        self.assertIn("28a745", result)

    def test_estado_badge_inactivo(self):
        obj = _mock_obj(activo=False)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("INACTIVA", result)

    def test_fecha_vencimiento_vencida(self):
        obj = _mock_obj(fecha_vencimiento=date(2020, 1, 1))
        result = str(self.admin.fecha_vencimiento_display(obj))
        self.assertIn("VENCIDA", result)

    def test_fecha_vencimiento_vigente(self):
        obj = _mock_obj(fecha_vencimiento=date.today() + timedelta(days=90))
        result = str(self.admin.fecha_vencimiento_display(obj))
        self.assertIn("28a745", result)

    def test_fecha_vencimiento_none(self):
        obj = _mock_obj(fecha_vencimiento=None)
        result = str(self.admin.fecha_vencimiento_display(obj))
        self.assertIn("Sin vencimiento", result)


@patch('apps.core.admin.format_html', _plain_format_html)
class CargasSaldoAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        from apps.core.models import CargasSaldo
        self.admin = CargasSaldoAdmin(CargasSaldo, self.site)

    def test_nro_tarjeta_link_con_tarjeta(self):
        tarjeta = _mock_obj(nro_tarjeta="T001")
        obj = _mock_obj(nro_tarjeta=tarjeta)
        with patch("apps.core.admin.reverse", return_value="/admin/core/tarjetas/T001/change/"):
            result = str(self.admin.nro_tarjeta_link(obj))
        self.assertIn("T001", result)
        self.assertIn("<a href=", result)

    def test_nro_tarjeta_link_sin_tarjeta(self):
        obj = _mock_obj(nro_tarjeta=None)
        result = self.admin.nro_tarjeta_link(obj)
        self.assertEqual(result, "-")

    def test_monto_display(self):
        obj = _mock_obj(monto_cargado=Decimal("200.00"))
        result = str(self.admin.monto_display(obj))
        self.assertIn("200.00", result)
        self.assertIn("28a745", result)

    def test_estado_badge_confirmado(self):
        obj = _mock_obj(estado="Confirmado")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("28a745", result)

    def test_estado_badge_pendiente(self):
        obj = _mock_obj(estado="Pendiente")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("ffc107", result)

    def test_estado_badge_rechazado(self):
        obj = _mock_obj(estado="Rechazado")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("dc3545", result)

    def test_estado_badge_desconocido(self):
        obj = _mock_obj(estado="Otro")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("6c757d", result)

    def test_fecha_carga_display(self):
        import datetime
        obj = _mock_obj(fecha_carga=datetime.datetime(2024, 3, 15, 10, 30))
        result = self.admin.fecha_carga_display(obj)
        self.assertIn("15/03/2024", result)

    def test_referencia_badge_corta(self):
        obj = _mock_obj(referencia="REF001")
        result = str(self.admin.referencia_badge(obj))
        self.assertIn("REF001", result)

    def test_referencia_badge_larga(self):
        obj = _mock_obj(referencia="A" * 30)
        result = str(self.admin.referencia_badge(obj))
        self.assertIn("...", result)

    def test_referencia_badge_none(self):
        obj = _mock_obj(referencia=None)
        result = self.admin.referencia_badge(obj)
        self.assertEqual(result, "-")

    def test_cliente_info_con_cliente(self):
        cliente = _mock_obj(nombre="Maria", apellido="Lopez")
        obj = _mock_obj(id_cliente_origen=cliente)
        result = str(self.admin.cliente_info(obj))
        self.assertIn("Maria", result)

    def test_cliente_info_sin_cliente(self):
        obj = _mock_obj(id_cliente_origen=None)
        result = str(self.admin.cliente_info(obj))
        self.assertIn("-", result)


@patch('apps.core.admin.format_html', _plain_format_html)
class ConsumosTarjetaAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        from apps.core.models import ConsumosTarjeta
        self.admin = ConsumosTarjetaAdmin(ConsumosTarjeta, self.site)

    def test_nro_tarjeta_link_con_tarjeta(self):
        tarjeta = _mock_obj(nro_tarjeta="T002")
        obj = _mock_obj(nro_tarjeta=tarjeta)
        with patch("apps.core.admin.reverse", return_value="/admin/core/tarjetas/T002/change/"):
            result = str(self.admin.nro_tarjeta_link(obj))
        self.assertIn("T002", result)

    def test_nro_tarjeta_link_sin_tarjeta(self):
        obj = _mock_obj(nro_tarjeta=None)
        result = self.admin.nro_tarjeta_link(obj)
        self.assertEqual(result, "-")

    def test_monto_display(self):
        obj = _mock_obj(monto_consumido=Decimal("50.00"))
        result = str(self.admin.monto_display(obj))
        self.assertIn("50.00", result)
        self.assertIn("dc3545", result)

    def test_detalle_corto_normal(self):
        obj = _mock_obj(detalle="Compra almuerzo")
        result = self.admin.detalle_corto(obj)
        self.assertEqual(result, "Compra almuerzo")

    def test_detalle_corto_largo(self):
        obj = _mock_obj(detalle="A" * 50)
        result = self.admin.detalle_corto(obj)
        self.assertIn("...", result)
        self.assertLessEqual(len(result), 43)

    def test_detalle_corto_none(self):
        obj = _mock_obj(detalle=None)
        result = self.admin.detalle_corto(obj)
        self.assertEqual(result, "-")

    def test_saldos_display(self):
        obj = _mock_obj(saldo_anterior=Decimal("500.00"), saldo_posterior=Decimal("450.00"))
        result = str(self.admin.saldos_display(obj))
        self.assertIn("500.00", result)
        self.assertIn("450.00", result)

    def test_fecha_consumo_display(self):
        import datetime
        obj = _mock_obj(fecha_consumo=datetime.datetime(2024, 5, 20, 14, 00))
        result = self.admin.fecha_consumo_display(obj)
        self.assertIn("20/05/2024", result)

    def test_empleado_registro_con_empleado(self):
        empleado = _mock_obj(nombre="Pedro", apellido="Santos")
        obj = _mock_obj(id_empleado_registro=empleado)
        result = str(self.admin.empleado_registro(obj))
        self.assertIn("Pedro", result)

    def test_empleado_registro_sin_empleado(self):
        obj = _mock_obj(id_empleado_registro=None)
        result = str(self.admin.empleado_registro(obj))
        self.assertIn("Sistema", result)


@patch('apps.core.admin.format_html', _plain_format_html)
class TransaccionesOnlineAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        from apps.core.models import TransaccionesOnline
        self.admin = TransaccionesOnlineAdmin(TransaccionesOnline, self.site)

    def test_monto_display(self):
        obj = _mock_obj(monto=Decimal("150.00"))
        result = str(self.admin.monto_display(obj))
        self.assertIn("150.00", result)

    def test_metodo_pago_badge_tarjeta_credito(self):
        obj = _mock_obj(metodo_pago="tarjeta_credito")
        result = str(self.admin.metodo_pago_badge(obj))
        self.assertIn("T. CRÉDITO", result)

    def test_metodo_pago_badge_qr(self):
        obj = _mock_obj(metodo_pago="qr")
        result = str(self.admin.metodo_pago_badge(obj))
        self.assertIn("28a745", result)

    def test_metodo_pago_badge_desconocido(self):
        obj = _mock_obj(metodo_pago="otro")
        result = str(self.admin.metodo_pago_badge(obj))
        self.assertIn("6c757d", result)

    def test_estado_badge_confirmado(self):
        obj = _mock_obj(estado="Confirmado")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("28a745", result)

    def test_estado_badge_rechazado(self):
        obj = _mock_obj(estado="Rechazado")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("dc3545", result)

    def test_fecha_transaccion_display(self):
        import datetime
        obj = _mock_obj(fecha_transaccion=datetime.datetime(2024, 1, 10, 9, 0))
        result = self.admin.fecha_transaccion_display(obj)
        self.assertIn("10/01/2024", result)

    def test_referencia_badge_corta(self):
        obj = _mock_obj(referencia_pago="PAY001")
        result = str(self.admin.referencia_badge(obj))
        self.assertIn("PAY001", result)

    def test_referencia_badge_larga(self):
        obj = _mock_obj(referencia_pago="B" * 25)
        result = str(self.admin.referencia_badge(obj))
        self.assertIn("...", result)

    def test_referencia_badge_none(self):
        obj = _mock_obj(referencia_pago=None)
        result = self.admin.referencia_badge(obj)
        self.assertEqual(result, "-")


@patch('apps.core.admin.format_html', _plain_format_html)
class MediosPagoAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        from apps.core.models import MediosPago
        self.admin = MediosPagoAdmin(MediosPago, self.site)

    def test_descripcion_badge(self):
        obj = _mock_obj(descripcion="Efectivo")
        result = str(self.admin.descripcion_badge(obj))
        self.assertIn("Efectivo", result)

    def test_genera_comision_badge_true(self):
        obj = _mock_obj(genera_comision=True)
        result = str(self.admin.genera_comision_badge(obj))
        self.assertIn("Cobra comisión", result)

    def test_genera_comision_badge_false(self):
        obj = _mock_obj(genera_comision=False)
        result = str(self.admin.genera_comision_badge(obj))
        self.assertIn("6c757d", result)

    def test_requiere_validacion_badge_true(self):
        obj = _mock_obj(requiere_validacion=True)
        result = str(self.admin.requiere_validacion_badge(obj))
        self.assertIn("Requiere validación", result)

    def test_requiere_validacion_badge_false(self):
        obj = _mock_obj(requiere_validacion=False)
        result = str(self.admin.requiere_validacion_badge(obj))
        self.assertIn("6c757d", result)

    def test_estado_badge_activo(self):
        obj = _mock_obj(activo=True)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("ACTIVO", result)

    def test_estado_badge_inactivo(self):
        obj = _mock_obj(activo=False)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("INACTIVO", result)


@patch('apps.core.admin.format_html', _plain_format_html)
class ConfiguracionSistemaAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        from apps.core.models import ConfiguracionSistema
        self.admin = ConfiguracionSistemaAdmin(ConfiguracionSistema, self.site)

    def test_clave_badge(self):
        obj = _mock_obj(clave="LIMITE_SALDO")
        result = str(self.admin.clave_badge(obj))
        self.assertIn("LIMITE_SALDO", result)

    def test_valor_display_corto(self):
        obj = _mock_obj(valor="true")
        result = self.admin.valor_display(obj)
        self.assertEqual(result, "true")

    def test_valor_display_largo(self):
        obj = _mock_obj(valor="V" * 60)
        result = str(self.admin.valor_display(obj))
        self.assertIn("...", result)

    def test_tipo_badge_string(self):
        obj = _mock_obj(tipo="string")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("STRING", result)

    def test_tipo_badge_bool(self):
        obj = _mock_obj(tipo="bool")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("28a745", result)

    def test_tipo_badge_json(self):
        obj = _mock_obj(tipo="json")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("6610f2", result)

    def test_tipo_badge_desconocido(self):
        obj = _mock_obj(tipo="otro")
        result = str(self.admin.tipo_badge(obj))
        self.assertIn("6c757d", result)

    def test_categoria_badge(self):
        obj = _mock_obj(categoria="pagos")
        result = str(self.admin.categoria_badge(obj))
        self.assertIn("pagos", result)

    def test_requerido_badge_true(self):
        obj = _mock_obj(requerido=True)
        result = str(self.admin.requerido_badge(obj))
        self.assertIn("Obligatorio", result)

    def test_requerido_badge_false(self):
        obj = _mock_obj(requerido=False)
        result = str(self.admin.requerido_badge(obj))
        self.assertIn("Opcional", result)

    def test_updated_info_con_usuario(self):
        import datetime
        empleado = _mock_obj(nombre="Carlos", apellido="Diaz")
        obj = _mock_obj(
            updated_by=empleado,
            updated_at=datetime.datetime(2024, 6, 1, 12, 0),
        )
        result = str(self.admin.updated_info(obj))
        self.assertIn("Carlos", result)

    def test_updated_info_sin_usuario(self):
        import datetime
        obj = _mock_obj(
            updated_by=None,
            updated_at=datetime.datetime(2024, 6, 1, 12, 0),
        )
        result = self.admin.updated_info(obj)
        self.assertIn("01/06/2024", result)


@patch('apps.core.admin.format_html', _plain_format_html)
class CacheConfiguracionAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        from apps.core.models import CacheConfiguracion
        self.admin = CacheConfiguracionAdmin(CacheConfiguracion, self.site)

    def test_clave_badge(self):
        obj = _mock_obj(clave="session_cache")
        result = str(self.admin.clave_badge(obj))
        self.assertIn("session_cache", result)

    def test_tipo_cache_badge_redis(self):
        obj = _mock_obj(tipo_cache="redis")
        result = str(self.admin.tipo_cache_badge(obj))
        self.assertIn("REDIS", result)
        self.assertIn("dc3545", result)

    def test_tipo_cache_badge_memory(self):
        obj = _mock_obj(tipo_cache="memory")
        result = str(self.admin.tipo_cache_badge(obj))
        self.assertIn("28a745", result)

    def test_tipo_cache_badge_desconocido(self):
        obj = _mock_obj(tipo_cache="otro")
        result = str(self.admin.tipo_cache_badge(obj))
        self.assertIn("6c757d", result)

    def test_ttl_display_segundos(self):
        obj = _mock_obj(ttl_segundos=30)
        result = str(self.admin.ttl_display(obj))
        self.assertIn("30", result)
        self.assertIn("seg", result)

    def test_ttl_display_minutos(self):
        obj = _mock_obj(ttl_segundos=120)
        result = str(self.admin.ttl_display(obj))
        self.assertIn("2", result)
        self.assertIn("min", result)

    def test_ttl_display_horas(self):
        obj = _mock_obj(ttl_segundos=7200)
        result = str(self.admin.ttl_display(obj))
        self.assertIn("2", result)
        self.assertIn("hrs", result)

    def test_size_display(self):
        obj = _mock_obj(max_size_mb=50)
        result = str(self.admin.size_display(obj))
        self.assertIn("50", result)
        self.assertIn("MB", result)

    def test_performance_display_sin_datos(self):
        obj = _mock_obj(hits=0, misses=0)
        result = self.admin.performance_display(obj)
        self.assertEqual(result, "-")

    def test_performance_display_alto_hit_rate(self):
        obj = _mock_obj(hits=90, misses=10)
        result = str(self.admin.performance_display(obj))
        self.assertIn("90.0%", result)
        self.assertIn("28a745", result)

    def test_performance_display_medio_hit_rate(self):
        obj = _mock_obj(hits=65, misses=35)
        result = str(self.admin.performance_display(obj))
        self.assertIn("ffc107", result)

    def test_performance_display_bajo_hit_rate(self):
        obj = _mock_obj(hits=40, misses=60)
        result = str(self.admin.performance_display(obj))
        self.assertIn("dc3545", result)

    def test_activo_badge_activo(self):
        obj = _mock_obj(activo=True)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("ACTIVO", result)

    def test_activo_badge_inactivo(self):
        obj = _mock_obj(activo=False)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("INACTIVO", result)


@patch('apps.core.admin.format_html', _plain_format_html)
class LimitesTransaccionAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        from apps.core.models import LimitesTransaccion
        self.admin = LimitesTransaccionAdmin(LimitesTransaccion, self.site)

    def test_rol_badge(self):
        rol = _mock_obj(nombre_rol="Cajero")
        obj = _mock_obj(id_rol=rol)
        result = str(self.admin.rol_badge(obj))
        self.assertIn("Cajero", result)

    def test_operacion_badge_venta(self):
        obj = _mock_obj(tipo_operacion="venta")
        obj.get_tipo_operacion_display.return_value = "Venta"
        result = str(self.admin.operacion_badge(obj))
        self.assertIn("28a745", result)

    def test_operacion_badge_descuento(self):
        obj = _mock_obj(tipo_operacion="descuento")
        obj.get_tipo_operacion_display.return_value = "Descuento"
        result = str(self.admin.operacion_badge(obj))
        self.assertIn("ffc107", result)

    def test_operacion_badge_desconocido(self):
        obj = _mock_obj(tipo_operacion="otro")
        obj.get_tipo_operacion_display.return_value = "Otro"
        result = str(self.admin.operacion_badge(obj))
        self.assertIn("6c757d", result)

    def test_monto_limite_display(self):
        obj = _mock_obj(monto_maximo_sin_autorizacion=Decimal("5000.00"))
        result = str(self.admin.monto_limite_display(obj))
        self.assertIn("5,000.00", result)

    def test_doble_autorizacion_badge_true(self):
        obj = _mock_obj(requiere_autorizacion_doble=True)
        result = str(self.admin.doble_autorizacion_badge(obj))
        self.assertIn("doble autorización", result)

    def test_doble_autorizacion_badge_false(self):
        obj = _mock_obj(requiere_autorizacion_doble=False)
        result = str(self.admin.doble_autorizacion_badge(obj))
        self.assertIn("simple", result)

    def test_activo_badge_true(self):
        obj = _mock_obj(activo=True)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("ACTIVO", result)

    def test_activo_badge_false(self):
        obj = _mock_obj(activo=False)
        result = str(self.admin.activo_badge(obj))
        self.assertIn("INACTIVO", result)


@patch('apps.core.admin.format_html', _plain_format_html)
class RegistroAutorizacionesAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        from apps.core.models import RegistroAutorizaciones
        self.admin = RegistroAutorizacionesAdmin(RegistroAutorizaciones, self.site)

    def test_operacion_badge(self):
        obj = _mock_obj(tipo_operacion="venta")
        result = str(self.admin.operacion_badge(obj))
        self.assertIn("VENTA", result)
        self.assertIn("17a2b8", result)

    def test_operacion_badge_con_underscore(self):
        obj = _mock_obj(tipo_operacion="nota_credito_cliente")
        result = str(self.admin.operacion_badge(obj))
        self.assertIn("NOTA CREDITO CLIENTE", result)

    def test_monto_display(self):
        obj = _mock_obj(monto=Decimal("1000.00"))
        result = str(self.admin.monto_display(obj))
        self.assertIn("1,000.00", result)

    def test_solicitante_info_con_empleado(self):
        empleado = _mock_obj(nombre="Luis", apellido="Torres")
        obj = _mock_obj(id_empleado_solicitante=empleado)
        result = str(self.admin.solicitante_info(obj))
        self.assertIn("Luis", result)

    def test_solicitante_info_sin_empleado(self):
        obj = _mock_obj(id_empleado_solicitante=None)
        result = self.admin.solicitante_info(obj)
        self.assertEqual(result, "-")

    def test_autorizador_info_con_empleado(self):
        empleado = _mock_obj(nombre="Sofia", apellido="Vega")
        obj = _mock_obj(id_empleado_autorizador=empleado)
        result = str(self.admin.autorizador_info(obj))
        self.assertIn("Sofia", result)
        self.assertIn("28a745", result)

    def test_autorizador_info_sin_empleado(self):
        obj = _mock_obj(id_empleado_autorizador=None)
        result = self.admin.autorizador_info(obj)
        self.assertEqual(result, "-")

    def test_autorizador2_info_con_empleado(self):
        empleado = _mock_obj(nombre="Rosa", apellido="Mora")
        obj = _mock_obj(id_empleado_autorizador_2=empleado)
        result = str(self.admin.autorizador2_info(obj))
        self.assertIn("Rosa", result)

    def test_autorizador2_info_sin_empleado(self):
        obj = _mock_obj(id_empleado_autorizador_2=None)
        result = str(self.admin.autorizador2_info(obj))
        self.assertIn("-", result)

    def test_fecha_autorizacion_display(self):
        import datetime
        obj = _mock_obj(fecha_autorizacion=datetime.datetime(2024, 4, 8, 16, 45))
        result = self.admin.fecha_autorizacion_display(obj)
        self.assertIn("08/04/2024", result)
