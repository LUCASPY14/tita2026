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
