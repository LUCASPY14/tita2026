"""Tests para apps.ventas.tasks — generar_resumen_diario_ventas, cerrar_cajas_automatico."""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone


@pytest.fixture
def caja_t(db):
    from apps.contabilidad.models import Caja
    return Caja.objects.create(nombre="Caja Task Test", activo=True)


@pytest.fixture
def cierre_abierto_ayer(db, caja_t, usuario_cajero):
    """CierreCaja ABIERTO cuya fecha_apertura es de ayer → candidato a cierre automático."""
    from apps.contabilidad.models import CierreCaja
    return CierreCaja.objects.create(
        caja=caja_t,
        empleado=usuario_cajero,
        monto_inicial=Decimal("100000"),
        estado=CierreCaja.Estado.ABIERTO,
        fecha_apertura=timezone.now() - timedelta(days=1),
    )


@pytest.fixture
def cierre_abierto_hoy(db, caja_t, usuario_cajero):
    """CierreCaja ABIERTO de hoy → NO debe cerrarse."""
    from apps.contabilidad.models import CierreCaja
    return CierreCaja.objects.create(
        caja=caja_t,
        empleado=usuario_cajero,
        monto_inicial=Decimal("50000"),
        estado=CierreCaja.Estado.ABIERTO,
    )


@pytest.fixture
def venta_ayer(db, cliente, usuario_cajero):
    """Venta del día anterior."""
    from apps.ventas.models import Venta
    venta = Venta.objects.create(
        cliente=cliente,
        cajero=usuario_cajero,
        estado=Venta.Estado.ACTIVA,
        monto_total=Decimal("15000"),
    )
    Venta.objects.filter(pk=venta.pk).update(
        fecha=timezone.now() - timedelta(days=1)
    )
    return venta


# ── generar_resumen_diario_ventas ──────────────────────────────────────────────

@pytest.mark.django_db
class TestGenerarResumenDiarioVentas:

    def test_sin_ventas_retorna_cero(self, db):
        from apps.ventas.tasks import generar_resumen_diario_ventas
        result = generar_resumen_diario_ventas()
        assert result["cantidad_ventas"] == 0
        assert result["monto_total"] == 0
        assert "fecha" in result

    def test_con_venta_de_ayer_incluye_totales(self, venta_ayer):
        from apps.ventas.tasks import generar_resumen_diario_ventas
        result = generar_resumen_diario_ventas()
        assert result["cantidad_ventas"] >= 1
        assert result["monto_total"] >= 15000


# ── cerrar_cajas_automatico ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCerrarCajasAutomatico:

    def test_sin_cajas_abiertas_retorna_cero(self, db):
        from apps.ventas.tasks import cerrar_cajas_automatico
        result = cerrar_cajas_automatico()
        assert result == {"cajas_cerradas": 0}

    def test_cierre_abierto_de_ayer_se_cierra(self, cierre_abierto_ayer):
        from apps.contabilidad.models import CierreCaja
        from apps.ventas.tasks import cerrar_cajas_automatico
        result = cerrar_cajas_automatico()
        assert result["cajas_cerradas"] >= 1
        cierre_abierto_ayer.refresh_from_db()
        assert cierre_abierto_ayer.estado == CierreCaja.Estado.CERRADO
        assert cierre_abierto_ayer.fecha_cierre is not None

    def test_cierre_abierto_de_hoy_no_se_cierra(self, cierre_abierto_hoy):
        from apps.contabilidad.models import CierreCaja
        from apps.ventas.tasks import cerrar_cajas_automatico
        result = cerrar_cajas_automatico()
        assert result["cajas_cerradas"] == 0
        cierre_abierto_hoy.refresh_from_db()
        assert cierre_abierto_hoy.estado == CierreCaja.Estado.ABIERTO

    def test_cierre_ya_procesado_por_otro_worker_se_ignora(self, cierre_abierto_ayer):
        """Simula race condition: pk en lista inicial pero ya cerrado en select_for_update (líneas 56-57)."""
        from apps.contabilidad.models import CierreCaja
        from apps.ventas.tasks import cerrar_cajas_automatico
        from unittest.mock import patch, MagicMock

        pk = cierre_abierto_ayer.pk
        # El pk aparece en la lista inicial pero el get() falla porque otro worker ya lo cerró
        mock_qs = MagicMock()
        mock_qs.values_list.return_value = [pk]

        with patch.object(CierreCaja, "objects") as mock_mgr:
            mock_mgr.filter.return_value = mock_qs
            mock_mgr.select_for_update.return_value.get.side_effect = CierreCaja.DoesNotExist

            result = cerrar_cajas_automatico()

        assert result == {"cajas_cerradas": 0}

    def test_monto_esperado_con_ingresos_y_egresos(self, cierre_abierto_ayer, usuario_cajero):
        from apps.contabilidad.models import MovimientoCaja
        from apps.ventas.tasks import cerrar_cajas_automatico
        # monto_inicial=100000, ingreso=20000, egreso=10000 → esperado=110000
        MovimientoCaja.objects.create(
            cierre=cierre_abierto_ayer,
            tipo=MovimientoCaja.Tipo.INGRESO,
            monto=Decimal("20000"),
            descripcion="Ingreso test",
        )
        MovimientoCaja.objects.create(
            cierre=cierre_abierto_ayer,
            tipo=MovimientoCaja.Tipo.EGRESO,
            monto=Decimal("10000"),
            descripcion="Egreso test",
        )
        cerrar_cajas_automatico()
        cierre_abierto_ayer.refresh_from_db()
        assert cierre_abierto_ayer.monto_contado_fisico == Decimal("110000")
        assert cierre_abierto_ayer.diferencia_efectivo == 0
