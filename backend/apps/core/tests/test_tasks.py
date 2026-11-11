"""Tests para apps.core.tasks — expirar_recargas_pendientes."""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone


@pytest.fixture
def hijo_t(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Task", apellido="Core",
        cliente_responsable=cliente, activo=True,
    )


@pytest.fixture
def tarjeta_t(db, hijo_t):
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(
        nro_tarjeta="TASK-CORE01",
        hijo=hijo_t,
        estado=Tarjeta.Estado.ACTIVA,
    )


@pytest.fixture
def carga_pendiente_antigua(db, tarjeta_t, usuario_cajero):
    from apps.core.models import CargaSaldo
    return CargaSaldo.objects.create(
        tarjeta=tarjeta_t,
        monto_cargado=Decimal("50000"),
        estado=CargaSaldo.Estado.PENDIENTE,
        responsable=usuario_cajero,
        fecha_carga=timezone.now() - timedelta(hours=25),
    )


@pytest.fixture
def carga_pendiente_reciente(db, tarjeta_t, usuario_cajero):
    from apps.core.models import CargaSaldo
    return CargaSaldo.objects.create(
        tarjeta=tarjeta_t,
        monto_cargado=Decimal("30000"),
        estado=CargaSaldo.Estado.PENDIENTE,
        responsable=usuario_cajero,
    )


@pytest.mark.django_db
class TestExpirarRecargasPendientes:

    def test_sin_cargas_retorna_cero(self, db):
        from apps.core.tasks import expirar_recargas_pendientes
        result = expirar_recargas_pendientes()
        assert result == {"expiradas": 0}

    def test_carga_antigua_se_marca_rechazada(self, carga_pendiente_antigua):
        from apps.core.models import CargaSaldo
        from apps.core.tasks import expirar_recargas_pendientes
        result = expirar_recargas_pendientes()
        assert result["expiradas"] == 1
        carga_pendiente_antigua.refresh_from_db()
        assert carga_pendiente_antigua.estado == CargaSaldo.Estado.RECHAZADA

    def test_carga_reciente_no_se_expira(self, carga_pendiente_reciente):
        from apps.core.models import CargaSaldo
        from apps.core.tasks import expirar_recargas_pendientes
        result = expirar_recargas_pendientes()
        assert result["expiradas"] == 0
        carga_pendiente_reciente.refresh_from_db()
        assert carga_pendiente_reciente.estado == CargaSaldo.Estado.PENDIENTE

    def test_mezcla_antigua_y_reciente(self, carga_pendiente_antigua, carga_pendiente_reciente):
        from apps.core.tasks import expirar_recargas_pendientes
        result = expirar_recargas_pendientes()
        assert result["expiradas"] == 1


# ── crear_particion_anio_siguiente ────────────────────────────────────────────

from unittest.mock import patch


@pytest.mark.django_db
class TestCrearParticionAnioSiguiente:

    @patch("django.core.management.call_command")
    def test_llama_create_year_partition(self, mock_cmd):
        from apps.core.tasks import crear_particion_anio_siguiente
        from django.utils import timezone
        crear_particion_anio_siguiente()
        mock_cmd.assert_called_once()
        args, kwargs = mock_cmd.call_args
        assert args[0] == "create_year_partition"
        assert kwargs["year"] == timezone.now().year + 1

    @patch("django.core.management.call_command")
    def test_retorna_anio_siguiente(self, mock_cmd):
        from apps.core.tasks import crear_particion_anio_siguiente
        from django.utils import timezone
        result = crear_particion_anio_siguiente()
        assert result["año"] == timezone.now().year + 1

    @patch("django.core.management.call_command")
    def test_resultado_contiene_output(self, mock_cmd):
        from apps.core.tasks import crear_particion_anio_siguiente
        result = crear_particion_anio_siguiente()
        assert "resultado" in result
        assert isinstance(result["resultado"], str)

    @patch("django.core.management.call_command")
    def test_re_lanza_excepcion_si_falla(self, mock_cmd):
        from apps.core.tasks import crear_particion_anio_siguiente
        mock_cmd.side_effect = RuntimeError("partición ya existe")
        with pytest.raises(RuntimeError, match="partición ya existe"):
            crear_particion_anio_siguiente()


# ─── reconciliar_pagos_bancard_pendientes ────────────────────────────────────

@pytest.fixture
def pago_bancard_pendiente(db, tarjeta_t, cliente):
    from apps.core.models import PagoBancard
    pago = PagoBancard.objects.create(
        tarjeta=tarjeta_t, cliente=cliente,
        monto=Decimal("50000"),
        shop_process_id="TASK-RECON-OLD",
        estado=PagoBancard.Estado.PENDIENTE,
    )
    PagoBancard.objects.filter(pk=pago.pk).update(
        fecha_creacion=timezone.now() - timedelta(minutes=10)
    )
    pago.refresh_from_db()
    return pago


@pytest.fixture
def pago_bancard_reciente(db, tarjeta_t, cliente):
    from apps.core.models import PagoBancard
    return PagoBancard.objects.create(
        tarjeta=tarjeta_t, cliente=cliente,
        monto=Decimal("30000"),
        shop_process_id="TASK-RECON-NEW",
        estado=PagoBancard.Estado.PENDIENTE,
    )


@pytest.mark.django_db
class TestReconciliarPagosBancardPendientes:

    def test_sin_pendientes_retorna_cero(self, db):
        from apps.core.tasks import reconciliar_pagos_bancard_pendientes
        result = reconciliar_pagos_bancard_pendientes()
        assert result == {"revisados": 0, "resueltos": 0}

    @patch("apps.core.bancard_service.get_confirmation")
    def test_resuelve_pendiente_antiguo_cuando_bancard_ya_tiene_resultado(
        self, mock_get_conf, pago_bancard_pendiente
    ):
        from apps.core.models import PagoBancard
        from apps.core.tasks import reconciliar_pagos_bancard_pendientes

        mock_get_conf.return_value = {
            "status": "success",
            "confirmation": {"response_code": "00"},
        }
        result = reconciliar_pagos_bancard_pendientes()

        assert result == {"revisados": 1, "resueltos": 1}
        pago_bancard_pendiente.refresh_from_db()
        assert pago_bancard_pendiente.estado == PagoBancard.Estado.APROBADO

    def test_no_toca_pendiente_reciente(self, pago_bancard_reciente):
        """Menos de 3 minutos de antigüedad — ni siquiera se reconsulta (el
        webhook normal todavía tiene tiempo de llegar solo)."""
        from apps.core.models import PagoBancard
        from apps.core.tasks import reconciliar_pagos_bancard_pendientes

        result = reconciliar_pagos_bancard_pendientes()

        assert result == {"revisados": 0, "resueltos": 0}
        pago_bancard_reciente.refresh_from_db()
        assert pago_bancard_reciente.estado == PagoBancard.Estado.PENDIENTE

    @patch("apps.core.bancard_service.get_confirmation")
    def test_pendiente_antiguo_sin_resultado_sigue_pendiente(
        self, mock_get_conf, pago_bancard_pendiente
    ):
        from apps.core.models import PagoBancard
        from apps.core.tasks import reconciliar_pagos_bancard_pendientes

        mock_get_conf.return_value = {"status": "error", "messages": [{"dsc": "circuit breaker"}]}
        result = reconciliar_pagos_bancard_pendientes()

        assert result == {"revisados": 1, "resueltos": 0}
        pago_bancard_pendiente.refresh_from_db()
        assert pago_bancard_pendiente.estado == PagoBancard.Estado.PENDIENTE
