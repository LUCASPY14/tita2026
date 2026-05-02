"""
Tests for apps/almuerzos/admin.py
Covers all custom display methods across 9 admin classes.
"""

from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.contrib.admin.sites import AdminSite

from apps.almuerzos.admin import (
    PlanesAlmuerzoAdmin,
    TiposAlmuerzoAdmin,
    SuscripcionesAlmuerzoAdmin,
    RegistrosConsumoAlmuerzoAdmin,
    CuentasAlmuerzoMensualAdmin,
    PagosAlmuerzoMensualAdmin,
    PagosCuentasAlmuerzoAdmin,
    AlergenosAdmin,
    ProductosAlergenosAdmin,
)
from apps.almuerzos.models import (
    PlanesAlmuerzo,
    TiposAlmuerzo,
    SuscripcionesAlmuerzo,
    RegistrosConsumoAlmuerzo,
    CuentasAlmuerzoMensual,
    PagosAlmuerzoMensual,
    PagosCuentasAlmuerzo,
    Alergenos,
    ProductosAlergenos,
)

_plain_format_html = lambda fmt, *a, **k: fmt.format(*a, **k)


def _mock_obj(**kwargs):
    obj = MagicMock()
    for k, v in kwargs.items():
        setattr(obj, k, v)
    return obj


# =============================================================================
# PlanesAlmuerzoAdmin
# =============================================================================


@patch("apps.almuerzos.admin.format_html", _plain_format_html)
class PlanesAlmuerzoAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = PlanesAlmuerzoAdmin(PlanesAlmuerzo, self.site)

    def test_precio_mensual_badge_barato(self):
        obj = _mock_obj(precio_mensual=300000)
        result = str(self.admin.precio_mensual_badge(obj))
        self.assertIn("4CAF50", result)
        self.assertIn("300,000", result)

    def test_precio_mensual_badge_caro(self):
        obj = _mock_obj(precio_mensual=600000)
        result = str(self.admin.precio_mensual_badge(obj))
        self.assertIn("FF9800", result)
        self.assertIn("600,000", result)

    def test_precio_mensual_badge_exactamente_500000(self):
        obj = _mock_obj(precio_mensual=500000)
        result = str(self.admin.precio_mensual_badge(obj))
        # >= 500000 -> orange
        self.assertIn("FF9800", result)

    def test_estado_badge_activo(self):
        obj = _mock_obj(estado=True)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("4CAF50", result)
        self.assertIn("ACTIVO", result)

    def test_estado_badge_inactivo(self):
        obj = _mock_obj(estado=False)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("F44336", result)
        self.assertIn("INACTIVO", result)


# =============================================================================
# TiposAlmuerzoAdmin
# =============================================================================


@patch("apps.almuerzos.admin.format_html", _plain_format_html)
class TiposAlmuerzoAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = TiposAlmuerzoAdmin(TiposAlmuerzo, self.site)

    def test_precio_unitario_badge_barato(self):
        obj = _mock_obj(precio_unitario=30000)
        result = str(self.admin.precio_unitario_badge(obj))
        self.assertIn("2196F3", result)

    def test_precio_unitario_badge_caro(self):
        obj = _mock_obj(precio_unitario=80000)
        result = str(self.admin.precio_unitario_badge(obj))
        self.assertIn("FF9800", result)

    def test_precio_unitario_badge_exactamente_50000(self):
        obj = _mock_obj(precio_unitario=50000)
        result = str(self.admin.precio_unitario_badge(obj))
        # >= 50000 -> orange
        self.assertIn("FF9800", result)

    def test_estado_badge_activo(self):
        obj = _mock_obj(estado=True)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("4CAF50", result)

    def test_estado_badge_inactivo(self):
        obj = _mock_obj(estado=False)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("F44336", result)


# =============================================================================
# SuscripcionesAlmuerzoAdmin
# =============================================================================


@patch("apps.almuerzos.admin.format_html", _plain_format_html)
class SuscripcionesAlmuerzoAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = SuscripcionesAlmuerzoAdmin(SuscripcionesAlmuerzo, self.site)

    def test_estado_badge_activa(self):
        obj = _mock_obj(estado="Activa")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("4CAF50", result)
        self.assertIn("Activa", result)

    def test_estado_badge_pausada(self):
        obj = _mock_obj(estado="Pausada")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("FF9800", result)

    def test_estado_badge_cancelada(self):
        obj = _mock_obj(estado="Cancelada")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("F44336", result)

    def test_estado_badge_finalizada(self):
        obj = _mock_obj(estado="Finalizada")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("9E9E9E", result)

    def test_estado_badge_desconocido(self):
        obj = _mock_obj(estado="Otro")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("607D8B", result)

    def test_estado_badge_none(self):
        obj = _mock_obj(estado=None)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("N/A", result)


# =============================================================================
# RegistrosConsumoAlmuerzoAdmin
# =============================================================================


@patch("apps.almuerzos.admin.format_html", _plain_format_html)
class RegistrosConsumoAlmuerzoAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = RegistrosConsumoAlmuerzoAdmin(RegistrosConsumoAlmuerzo, self.site)

    def test_costo_badge_con_costo(self):
        obj = _mock_obj(costo_almuerzo=25000)
        result = str(self.admin.costo_badge(obj))
        self.assertIn("25,000", result)

    def test_costo_badge_sin_costo(self):
        obj = _mock_obj(costo_almuerzo=None)
        result = str(self.admin.costo_badge(obj))
        self.assertIn("N/A", result)

    def test_costo_badge_cero(self):
        obj = _mock_obj(costo_almuerzo=0)
        result = str(self.admin.costo_badge(obj))
        # 0 is falsy -> N/A
        self.assertIn("N/A", result)

    def test_estado_badge_registrado(self):
        obj = _mock_obj(estado="Registrado")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("2196F3", result)

    def test_estado_badge_confirmado(self):
        obj = _mock_obj(estado="Confirmado")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("4CAF50", result)

    def test_estado_badge_rechazado(self):
        obj = _mock_obj(estado="Rechazado")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("F44336", result)

    def test_estado_badge_cancelado(self):
        obj = _mock_obj(estado="Cancelado")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("FF9800", result)

    def test_estado_badge_desconocido(self):
        obj = _mock_obj(estado="Otro")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("607D8B", result)


# =============================================================================
# CuentasAlmuerzoMensualAdmin
# =============================================================================


@patch("apps.almuerzos.admin.format_html", _plain_format_html)
class CuentasAlmuerzoMensualAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = CuentasAlmuerzoMensualAdmin(CuentasAlmuerzoMensual, self.site)

    def test_periodo_display(self):
        obj = _mock_obj(mes=3, anio=2024)
        result = str(self.admin.periodo_display(obj))
        self.assertIn("Marzo", result)
        self.assertIn("2024", result)

    def test_periodo_display_mes_1(self):
        obj = _mock_obj(mes=1, anio=2023)
        result = str(self.admin.periodo_display(obj))
        self.assertIn("Enero", result)

    def test_periodo_display_mes_12(self):
        obj = _mock_obj(mes=12, anio=2024)
        result = str(self.admin.periodo_display(obj))
        self.assertIn("Diciembre", result)

    def test_periodo_display_mes_invalido(self):
        obj = _mock_obj(mes=13, anio=2024)
        result = str(self.admin.periodo_display(obj))
        self.assertIn("13", result)

    def test_monto_total_badge(self):
        obj = _mock_obj(monto_total=150000)
        result = str(self.admin.monto_total_badge(obj))
        self.assertIn("150,000", result)

    def test_monto_pagado_badge_completo(self):
        obj = _mock_obj(monto_pagado=100000, monto_total=100000)
        result = str(self.admin.monto_pagado_badge(obj))
        self.assertIn("4CAF50", result)

    def test_monto_pagado_badge_parcial(self):
        obj = _mock_obj(monto_pagado=50000, monto_total=100000)
        result = str(self.admin.monto_pagado_badge(obj))
        self.assertIn("FF9800", result)

    def test_saldo_badge_sin_deuda(self):
        obj = _mock_obj(monto_total=100000, monto_pagado=100000)
        result = str(self.admin.saldo_badge(obj))
        self.assertIn("4CAF50", result)

    def test_saldo_badge_con_deuda(self):
        obj = _mock_obj(monto_total=100000, monto_pagado=50000)
        result = str(self.admin.saldo_badge(obj))
        self.assertIn("F44336", result)

    def test_saldo_badge_pago_excedido(self):
        obj = _mock_obj(monto_total=100000, monto_pagado=120000)
        result = str(self.admin.saldo_badge(obj))
        # saldo = -20000 <= 0 -> green
        self.assertIn("4CAF50", result)

    def test_saldo_pendiente_display(self):
        obj = _mock_obj(monto_total=100000, monto_pagado=30000)
        result = str(self.admin.saldo_pendiente_display(obj))
        self.assertIn("70,000.00", result)

    def test_estado_badge_pendiente(self):
        obj = _mock_obj(estado="Pendiente")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("FF9800", result)

    def test_estado_badge_pagada(self):
        obj = _mock_obj(estado="Pagada")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("4CAF50", result)

    def test_estado_badge_vencida(self):
        obj = _mock_obj(estado="Vencida")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("F44336", result)

    def test_estado_badge_cancelada(self):
        obj = _mock_obj(estado="Cancelada")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("9E9E9E", result)

    def test_estado_badge_desconocido(self):
        obj = _mock_obj(estado="Otro")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("607D8B", result)


# =============================================================================
# PagosAlmuerzoMensualAdmin
# =============================================================================


@patch("apps.almuerzos.admin.format_html", _plain_format_html)
class PagosAlmuerzoMensualAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = PagosAlmuerzoMensualAdmin(PagosAlmuerzoMensual, self.site)

    def test_monto_pagado_badge(self):
        obj = _mock_obj(monto_pagado=75000)
        result = str(self.admin.monto_pagado_badge(obj))
        self.assertIn("4CAF50", result)
        self.assertIn("75,000", result)

    def test_estado_badge_pendiente(self):
        obj = _mock_obj(estado="Pendiente")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("FF9800", result)

    def test_estado_badge_confirmado(self):
        obj = _mock_obj(estado="Confirmado")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("4CAF50", result)

    def test_estado_badge_rechazado(self):
        obj = _mock_obj(estado="Rechazado")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("F44336", result)

    def test_estado_badge_desconocido(self):
        obj = _mock_obj(estado="Otro")
        result = str(self.admin.estado_badge(obj))
        self.assertIn("607D8B", result)

    def test_estado_badge_none(self):
        obj = _mock_obj(estado=None)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("N/A", result)


# =============================================================================
# PagosCuentasAlmuerzoAdmin
# =============================================================================


@patch("apps.almuerzos.admin.format_html", _plain_format_html)
class PagosCuentasAlmuerzoAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = PagosCuentasAlmuerzoAdmin(PagosCuentasAlmuerzo, self.site)

    def test_monto_badge(self):
        obj = _mock_obj(monto=50000)
        result = str(self.admin.monto_badge(obj))
        self.assertIn("4CAF50", result)
        self.assertIn("50,000", result)


# =============================================================================
# AlergenosAdmin
# =============================================================================


@patch("apps.almuerzos.admin.format_html", _plain_format_html)
class AlergenosAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = AlergenosAdmin(Alergenos, self.site)

    def test_nivel_severidad_badge_critica(self):
        obj = _mock_obj(nivel_severidad="Critica")
        result = str(self.admin.nivel_severidad_badge(obj))
        self.assertIn("F44336", result)
        self.assertIn("Critica", result)

    def test_nivel_severidad_badge_alta(self):
        obj = _mock_obj(nivel_severidad="Alta")
        result = str(self.admin.nivel_severidad_badge(obj))
        self.assertIn("FF9800", result)

    def test_nivel_severidad_badge_media(self):
        obj = _mock_obj(nivel_severidad="Media")
        result = str(self.admin.nivel_severidad_badge(obj))
        self.assertIn("FFC107", result)

    def test_nivel_severidad_badge_baja(self):
        obj = _mock_obj(nivel_severidad="Baja")
        result = str(self.admin.nivel_severidad_badge(obj))
        self.assertIn("4CAF50", result)

    def test_nivel_severidad_badge_desconocido(self):
        obj = _mock_obj(nivel_severidad="Otro")
        result = str(self.admin.nivel_severidad_badge(obj))
        self.assertIn("607D8B", result)

    def test_estado_badge_activo(self):
        obj = _mock_obj(estado=True)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("4CAF50", result)
        self.assertIn("ACTIVO", result)

    def test_estado_badge_inactivo(self):
        obj = _mock_obj(estado=False)
        result = str(self.admin.estado_badge(obj))
        self.assertIn("F44336", result)
        self.assertIn("INACTIVO", result)


# =============================================================================
# ProductosAlergenosAdmin
# =============================================================================


@patch("apps.almuerzos.admin.format_html", _plain_format_html)
class ProductosAlergenosAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = ProductosAlergenosAdmin(ProductosAlergenos, self.site)

    def test_contiene_badge_contiene(self):
        obj = _mock_obj(contiene=True)
        result = str(self.admin.contiene_badge(obj))
        self.assertIn("F44336", result)
        self.assertIn("CONTIENE", result)

    def test_contiene_badge_puede_contener(self):
        obj = _mock_obj(contiene=False)
        result = str(self.admin.contiene_badge(obj))
        self.assertIn("FF9800", result)
        self.assertIn("TRAZAS", result)
