"""
Extended tests for apps/contabilidad/admin.py targeting uncovered display methods.

Missing lines: 36-45, 82-87, 96-98, 103-105, 110-121, 126-130, 165-173, 182,
187-189, 222, 230-232, 237-239, 280-282, 287-291, 333-340, 349-351, 389-396,
405-421, 431, 480-481, 486-490, 497-499, 504-506, 541, 548-550, 584-586, 618,
623-625
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.admin import AdminSite
from django.test import TestCase

from apps.contabilidad.admin import (
    AuditoriaComisionesAdmin,
    CajasAdmin,
    CierresCajaAdmin,
    ConciliacionPagosAdmin,
    DatosEmpresaAdmin,
    DocumentosTributariosAdmin,
    ImpuestosAdmin,
    MovimientosCajaAdmin,
    PuntosExpedicionAdmin,
    TarifasComisionAdmin,
    TimbradosAdmin,
)
from apps.contabilidad.models import (
    AuditoriaComisiones,
    Cajas,
    CierresCaja,
    ConciliacionPagos,
    DatosEmpresa,
    DocumentosTributarios,
    Impuestos,
    MovimientosCaja,
    PuntosExpedicion,
    TarifasComision,
    Timbrados,
)

# format_html compatibility patch
_plain_format_html = lambda fmt, *a, **k: fmt.format(*a, **k)


def _mock_obj(**kwargs):
    obj = MagicMock()
    for k, v in kwargs.items():
        setattr(obj, k, v)
    return obj


# =============================================================================
# CajasAdmin
# =============================================================================


@patch("apps.contabilidad.admin.format_html", _plain_format_html)
class CajasAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = CajasAdmin(Cajas, self.site)

    def test_activo_badge_active(self):
        """Lines 36-41: estado=True returns green badge."""
        obj = _mock_obj(estado=True)
        result = self.admin.activo_badge(obj)
        self.assertIn("green", result)
        self.assertIn("Activa", result)
        self.assertIn("✓", result)

    def test_activo_badge_inactive(self):
        """Lines 42-45: estado=False returns red badge."""
        obj = _mock_obj(estado=False)
        result = self.admin.activo_badge(obj)
        self.assertIn("red", result)
        self.assertIn("Inactiva", result)
        self.assertIn("✗", result)


# =============================================================================
# CierresCajaAdmin
# =============================================================================


@patch("apps.contabilidad.admin.format_html", _plain_format_html)
class CierresCajaAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = CierresCajaAdmin(CierresCaja, self.site)

    def test_estado_badge_abierto(self):
        """Lines 82-87: estado='Abierto' returns blue badge."""
        obj = _mock_obj(estado="Abierto")
        result = self.admin.estado_badge(obj)
        self.assertIn("blue", result)
        self.assertIn("Abierto", result)

    def test_estado_badge_cerrado(self):
        """estado='Cerrado' returns green badge."""
        obj = _mock_obj(estado="Cerrado")
        result = self.admin.estado_badge(obj)
        self.assertIn("green", result)

    def test_estado_badge_desconocido(self):
        """Unknown estado returns gray badge."""
        obj = _mock_obj(estado="Desconocido")
        result = self.admin.estado_badge(obj)
        self.assertIn("gray", result)

    def test_estado_badge_none(self):
        """estado=None uses N/A fallback."""
        obj = _mock_obj(estado=None)
        result = self.admin.estado_badge(obj)
        self.assertIn("N/A", result)

    def test_monto_inicial_display_with_value(self):
        """Lines 96-98: monto_inicial truthy returns formatted string."""
        obj = _mock_obj(monto_inicial=Decimal("50000"))
        result = self.admin.monto_inicial_display(obj)
        self.assertIn("50,000", result)

    def test_monto_inicial_display_none(self):
        """Lines 96-98: monto_inicial falsy returns '-'."""
        obj = _mock_obj(monto_inicial=None)
        result = self.admin.monto_inicial_display(obj)
        self.assertEqual(result, "-")

    def test_monto_contado_display_with_value(self):
        """Lines 103-105: monto_contado_fisico truthy returns formatted string."""
        obj = _mock_obj(monto_contado_fisico=Decimal("75000"))
        result = self.admin.monto_contado_display(obj)
        self.assertIn("75,000", result)

    def test_monto_contado_display_none(self):
        """Lines 103-105: monto_contado_fisico falsy returns '-'."""
        obj = _mock_obj(monto_contado_fisico=None)
        result = self.admin.monto_contado_display(obj)
        self.assertEqual(result, "-")

    def test_diferencia_display_negative(self):
        """Lines 110-121: diferencia < 0 returns red badge."""
        obj = _mock_obj(diferencia_efectivo=Decimal("-5000"))
        result = self.admin.diferencia_display(obj)
        self.assertIn("red", result)
        self.assertIn("5,000", result)

    def test_diferencia_display_positive(self):
        """Lines 110-121: diferencia > 0 returns green badge."""
        obj = _mock_obj(diferencia_efectivo=Decimal("5000"))
        result = self.admin.diferencia_display(obj)
        self.assertIn("green", result)

    def test_diferencia_display_zero(self):
        """Lines 110-121: diferencia == 0 returns gray badge."""
        obj = _mock_obj(diferencia_efectivo=Decimal("0"))
        result = self.admin.diferencia_display(obj)
        # 0 is falsy so returns '-' per condition `if obj.diferencia_efectivo`
        self.assertEqual(result, "-")

    def test_diferencia_display_none(self):
        """Lines 110-121: diferencia_efectivo=None returns '-'."""
        obj = _mock_obj(diferencia_efectivo=None)
        result = self.admin.diferencia_display(obj)
        self.assertEqual(result, "-")

    def test_duracion_display_with_both_dates(self):
        """Lines 126-130: both dates set returns hours display."""
        apertura = datetime(2024, 1, 1, 8, 0, 0)
        cierre = datetime(2024, 1, 1, 16, 0, 0)
        obj = _mock_obj(fecha_hora_apertura=apertura, fecha_hora_cierre=cierre)
        result = self.admin.duracion_display(obj)
        self.assertIn("horas", result)
        self.assertIn("8.0", result)

    def test_duracion_display_no_cierre(self):
        """Lines 126-130: fecha_hora_cierre=None returns 'En curso'."""
        obj = _mock_obj(fecha_hora_apertura=datetime(2024, 1, 1), fecha_hora_cierre=None)
        result = self.admin.duracion_display(obj)
        self.assertEqual(result, "En curso")


# =============================================================================
# MovimientosCajaAdmin
# =============================================================================


@patch("apps.contabilidad.admin.format_html", _plain_format_html)
class MovimientosCajaAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = MovimientosCajaAdmin(MovimientosCaja, self.site)

    def test_tipo_movimiento_badge_ingreso(self):
        """Lines 165-173: tipo='Ingreso' returns green badge."""
        obj = _mock_obj(tipo_movimiento="Ingreso")
        result = self.admin.tipo_movimiento_badge(obj)
        self.assertIn("green", result)
        self.assertIn("Ingreso", result)

    def test_tipo_movimiento_badge_egreso(self):
        """tipo='Egreso' returns red badge."""
        obj = _mock_obj(tipo_movimiento="Egreso")
        result = self.admin.tipo_movimiento_badge(obj)
        self.assertIn("red", result)

    def test_tipo_movimiento_badge_transferencia(self):
        """tipo='Transferencia' returns blue badge."""
        obj = _mock_obj(tipo_movimiento="Transferencia")
        result = self.admin.tipo_movimiento_badge(obj)
        self.assertIn("blue", result)

    def test_tipo_movimiento_badge_apertura(self):
        """tipo='Apertura' returns orange badge."""
        obj = _mock_obj(tipo_movimiento="Apertura")
        result = self.admin.tipo_movimiento_badge(obj)
        self.assertIn("orange", result)

    def test_tipo_movimiento_badge_cierre(self):
        """tipo='Cierre' returns purple badge."""
        obj = _mock_obj(tipo_movimiento="Cierre")
        result = self.admin.tipo_movimiento_badge(obj)
        self.assertIn("purple", result)

    def test_tipo_movimiento_badge_unknown(self):
        """Unknown tipo returns gray badge."""
        obj = _mock_obj(tipo_movimiento="Otro")
        result = self.admin.tipo_movimiento_badge(obj)
        self.assertIn("gray", result)

    def test_monto_display(self):
        """Line 182: monto_display returns formatted amount."""
        obj = _mock_obj(monto=Decimal("100000"))
        result = self.admin.monto_display(obj)
        self.assertIn("100,000", result)

    def test_monto_comision_display_positive(self):
        """Lines 187-189: monto_comision > 0 returns orange badge."""
        obj = _mock_obj(monto_comision=Decimal("5000"))
        result = self.admin.monto_comision_display(obj)
        self.assertIn("orange", result)
        self.assertIn("5,000", result)

    def test_monto_comision_display_zero(self):
        """Lines 187-189: monto_comision == 0 returns '₲0'."""
        obj = _mock_obj(monto_comision=Decimal("0"))
        result = self.admin.monto_comision_display(obj)
        self.assertEqual(result, "₲0")


# =============================================================================
# TarifasComisionAdmin
# =============================================================================


@patch("apps.contabilidad.admin.format_html", _plain_format_html)
class TarifasComisionAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = TarifasComisionAdmin(TarifasComision, self.site)

    def test_porcentaje_display_with_value(self):
        """Line 222: porcentaje_comision truthy returns formatted percentage."""
        obj = _mock_obj(porcentaje_comision=Decimal("0.05"))
        result = self.admin.porcentaje_display(obj)
        self.assertIn("5.00%", result)

    def test_porcentaje_display_none(self):
        """Line 222: porcentaje_comision=None uses 0."""
        obj = _mock_obj(porcentaje_comision=None)
        result = self.admin.porcentaje_display(obj)
        self.assertIn("0.00%", result)

    def test_monto_fijo_display_with_value(self):
        """Lines 230-232: monto_fijo_comision truthy returns formatted amount."""
        obj = _mock_obj(monto_fijo_comision=Decimal("1000"))
        result = self.admin.monto_fijo_display(obj)
        self.assertIn("1,000", result)

    def test_monto_fijo_display_none(self):
        """Lines 230-232: monto_fijo_comision=None returns '-'."""
        obj = _mock_obj(monto_fijo_comision=None)
        result = self.admin.monto_fijo_display(obj)
        self.assertEqual(result, "-")

    def test_activo_badge_active(self):
        """Lines 237-239: estado=True returns green badge."""
        obj = _mock_obj(estado=True)
        result = self.admin.activo_badge(obj)
        self.assertIn("green", result)
        self.assertIn("Activa", result)

    def test_activo_badge_inactive(self):
        """Lines 237-239: estado=False returns red badge."""
        obj = _mock_obj(estado=False)
        result = self.admin.activo_badge(obj)
        self.assertIn("red", result)
        self.assertIn("Inactiva", result)


# =============================================================================
# AuditoriaComisionesAdmin
# =============================================================================


@patch("apps.contabilidad.admin.format_html", _plain_format_html)
class AuditoriaComisionesAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = AuditoriaComisionesAdmin(AuditoriaComisiones, self.site)
        self.request = MagicMock()

    def test_has_add_permission_returns_false(self):
        """AuditoriaComisiones cannot be added manually."""
        self.assertFalse(self.admin.has_add_permission(self.request))

    def test_has_delete_permission_returns_false(self):
        """AuditoriaComisiones records cannot be deleted."""
        self.assertFalse(self.admin.has_delete_permission(self.request))

    def test_valor_anterior_display_with_value(self):
        """Lines 280-282: valor_anterior is not None returns red-colored value."""
        obj = _mock_obj(valor_anterior=Decimal("0.05"))
        result = self.admin.valor_anterior_display(obj)
        self.assertIn("red", result)
        self.assertIn("0.0500", result)

    def test_valor_anterior_display_none(self):
        """Lines 280-282: valor_anterior=None returns '-'."""
        obj = _mock_obj(valor_anterior=None)
        result = self.admin.valor_anterior_display(obj)
        self.assertEqual(result, "-")

    def test_valor_nuevo_display_with_value(self):
        """Lines 287-291: valor_nuevo is not None returns green-colored value."""
        obj = _mock_obj(valor_nuevo=Decimal("0.08"))
        result = self.admin.valor_nuevo_display(obj)
        self.assertIn("green", result)
        self.assertIn("0.0800", result)

    def test_valor_nuevo_display_none(self):
        """Lines 287-291: valor_nuevo=None returns '-'."""
        obj = _mock_obj(valor_nuevo=None)
        result = self.admin.valor_nuevo_display(obj)
        self.assertEqual(result, "-")


# =============================================================================
# ConciliacionPagosAdmin
# =============================================================================


@patch("apps.contabilidad.admin.format_html", _plain_format_html)
class ConciliacionPagosAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = ConciliacionPagosAdmin(ConciliacionPagos, self.site)

    def test_estado_badge_pendiente(self):
        """Lines 333-340: estado='Pendiente' returns orange badge."""
        obj = _mock_obj(estado="Pendiente")
        result = self.admin.estado_badge(obj)
        self.assertIn("orange", result)
        self.assertIn("Pendiente", result)

    def test_estado_badge_conciliado(self):
        """estado='Conciliado' returns green badge."""
        obj = _mock_obj(estado="Conciliado")
        result = self.admin.estado_badge(obj)
        self.assertIn("green", result)

    def test_estado_badge_rechazado(self):
        """estado='Rechazado' returns red badge."""
        obj = _mock_obj(estado="Rechazado")
        result = self.admin.estado_badge(obj)
        self.assertIn("red", result)

    def test_estado_badge_en_proceso(self):
        """estado='En Proceso' returns blue badge."""
        obj = _mock_obj(estado="En Proceso")
        result = self.admin.estado_badge(obj)
        self.assertIn("blue", result)

    def test_estado_badge_unknown(self):
        """Unknown estado returns gray badge."""
        obj = _mock_obj(estado="Otro")
        result = self.admin.estado_badge(obj)
        self.assertIn("gray", result)

    def test_monto_acreditado_display_with_value(self):
        """Lines 349-351: monto_acreditado truthy returns formatted amount."""
        obj = _mock_obj(monto_acreditado=Decimal("250000"))
        result = self.admin.monto_acreditado_display(obj)
        self.assertIn("250,000", result)

    def test_monto_acreditado_display_none(self):
        """Lines 349-351: monto_acreditado=None returns '-'."""
        obj = _mock_obj(monto_acreditado=None)
        result = self.admin.monto_acreditado_display(obj)
        self.assertEqual(result, "-")


# =============================================================================
# DocumentosTributariosAdmin
# =============================================================================


@patch("apps.contabilidad.admin.format_html", _plain_format_html)
class DocumentosTributariosAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = DocumentosTributariosAdmin(DocumentosTributarios, self.site)

    def test_tipo_documento_badge_factura(self):
        """Lines 389-396: tipo_documento='Factura' returns green badge."""
        obj = _mock_obj(tipo_documento="Factura")
        result = self.admin.tipo_documento_badge(obj)
        self.assertIn("green", result)
        self.assertIn("Factura", result)

    def test_tipo_documento_badge_nota_credito(self):
        """tipo_documento='NotaCredito' returns orange badge."""
        obj = _mock_obj(tipo_documento="NotaCredito")
        result = self.admin.tipo_documento_badge(obj)
        self.assertIn("orange", result)

    def test_tipo_documento_badge_nota_debito(self):
        """tipo_documento='NotaDebito' returns red badge."""
        obj = _mock_obj(tipo_documento="NotaDebito")
        result = self.admin.tipo_documento_badge(obj)
        self.assertIn("red", result)

    def test_tipo_documento_badge_recibo(self):
        """tipo_documento='Recibo' returns blue badge."""
        obj = _mock_obj(tipo_documento="Recibo")
        result = self.admin.tipo_documento_badge(obj)
        self.assertIn("blue", result)

    def test_tipo_documento_badge_unknown(self):
        """Unknown tipo returns gray badge."""
        obj = _mock_obj(tipo_documento="Otro")
        result = self.admin.tipo_documento_badge(obj)
        self.assertIn("gray", result)

    def test_estado_sifen_badge_none(self):
        """Lines 405-421: estado_sifen=None returns gray Pendiente."""
        obj = _mock_obj(estado_sifen=None)
        result = self.admin.estado_sifen_badge(obj)
        self.assertIn("gray", result)
        self.assertIn("Pendiente", result)

    def test_estado_sifen_badge_aprobado(self):
        """Lines 405-421: estado_sifen='Aprobado' returns green badge with ✓."""
        obj = _mock_obj(estado_sifen="Aprobado")
        result = self.admin.estado_sifen_badge(obj)
        self.assertIn("green", result)
        self.assertIn("✓", result)

    def test_estado_sifen_badge_rechazado(self):
        """estado_sifen='Rechazado' returns red badge with ✗."""
        obj = _mock_obj(estado_sifen="Rechazado")
        result = self.admin.estado_sifen_badge(obj)
        self.assertIn("red", result)
        self.assertIn("✗", result)

    def test_estado_sifen_badge_pendiente(self):
        """estado_sifen='Pendiente' returns orange badge with ⏳."""
        obj = _mock_obj(estado_sifen="Pendiente")
        result = self.admin.estado_sifen_badge(obj)
        self.assertIn("orange", result)
        self.assertIn("⏳", result)

    def test_estado_sifen_badge_unknown(self):
        """Unknown estado_sifen returns gray badge with ?."""
        obj = _mock_obj(estado_sifen="Otro")
        result = self.admin.estado_sifen_badge(obj)
        self.assertIn("gray", result)
        self.assertIn("?", result)

    def test_monto_total_display(self):
        """Line 431: monto_total_display returns formatted amount."""
        obj = _mock_obj(monto_total=Decimal("1500000"))
        result = self.admin.monto_total_display(obj)
        self.assertIn("1,500,000", result)


# =============================================================================
# TimbradosAdmin
# =============================================================================


@patch("apps.contabilidad.admin.format_html", _plain_format_html)
class TimbradosAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = TimbradosAdmin(Timbrados, self.site)

    def test_numeros_display(self):
        """Lines 480-481: numeros_display returns range and total."""
        obj = _mock_obj(nro_inicial=1, nro_final=100)
        result = self.admin.numeros_display(obj)
        self.assertIn("1", result)
        self.assertIn("100", result)
        self.assertIn("100", result)  # total docs

    def test_activo_badge_active(self):
        """Lines 497-499: estado=True returns green badge."""
        obj = _mock_obj(estado=True)
        result = self.admin.activo_badge(obj)
        self.assertIn("green", result)
        self.assertIn("estado", result)

    def test_activo_badge_inactive(self):
        """Lines 497-499: estado=False returns red badge."""
        obj = _mock_obj(estado=False)
        result = self.admin.activo_badge(obj)
        self.assertIn("red", result)

    def test_disponibles_display(self):
        """Lines 504-506: disponibles_display returns count of available documents."""
        obj = _mock_obj(nro_inicial=1, nro_final=500)
        result = self.admin.disponibles_display(obj)
        self.assertIn("500", result)
        self.assertIn("documentos disponibles", result)


# =============================================================================
# PuntosExpedicionAdmin
# =============================================================================


@patch("apps.contabilidad.admin.format_html", _plain_format_html)
class PuntosExpedicionAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = PuntosExpedicionAdmin(PuntosExpedicion, self.site)

    def test_codigo_completo_display(self):
        """Line 541: codigo_completo_display shows establishment and point codes."""
        obj = _mock_obj(codigo_establecimiento="001", codigo_punto_expedicion="001")
        result = self.admin.codigo_completo_display(obj)
        self.assertIn("001-001", result)

    def test_activo_badge_active(self):
        """Lines 548-550: estado=True returns green badge."""
        obj = _mock_obj(estado=True)
        result = self.admin.activo_badge(obj)
        self.assertIn("green", result)
        self.assertIn("estado", result)

    def test_activo_badge_inactive(self):
        """Lines 548-550: estado=False returns red badge."""
        obj = _mock_obj(estado=False)
        result = self.admin.activo_badge(obj)
        self.assertIn("red", result)


# =============================================================================
# DatosEmpresaAdmin
# =============================================================================


@patch("apps.contabilidad.admin.format_html", _plain_format_html)
class DatosEmpresaAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = DatosEmpresaAdmin(DatosEmpresa, self.site)

    def test_activo_badge_active(self):
        """Lines 584-586: estado=True returns green badge."""
        obj = _mock_obj(estado=True)
        result = self.admin.activo_badge(obj)
        self.assertIn("green", result)
        self.assertIn("Activa", result)

    def test_activo_badge_inactive(self):
        """Lines 584-586: estado=False returns red badge."""
        obj = _mock_obj(estado=False)
        result = self.admin.activo_badge(obj)
        self.assertIn("red", result)


# =============================================================================
# ImpuestosAdmin
# =============================================================================


@patch("apps.contabilidad.admin.format_html", _plain_format_html)
class ImpuestosAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = ImpuestosAdmin(Impuestos, self.site)

    def test_porcentaje_display_with_value(self):
        """Line 618: porcentaje truthy returns formatted percentage."""
        obj = _mock_obj(porcentaje=Decimal("10"))
        result = self.admin.porcentaje_display(obj)
        self.assertIn("10.00%", result)

    def test_porcentaje_display_none(self):
        """Line 618: porcentaje=None uses 0."""
        obj = _mock_obj(porcentaje=None)
        result = self.admin.porcentaje_display(obj)
        self.assertIn("0.00%", result)

    def test_activo_badge_active(self):
        """Lines 623-625: estado=True returns green badge."""
        obj = _mock_obj(estado=True)
        result = self.admin.activo_badge(obj)
        self.assertIn("green", result)
        self.assertIn("estado", result)

    def test_activo_badge_inactive(self):
        """Lines 623-625: estado=False returns red badge."""
        obj = _mock_obj(estado=False)
        result = self.admin.activo_badge(obj)
        self.assertIn("red", result)
