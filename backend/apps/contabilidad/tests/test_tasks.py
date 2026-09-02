from datetime import timedelta
from decimal import Decimal

import pytest
from unittest.mock import patch, MagicMock
from celery.exceptions import Retry
from django.utils import timezone

from apps.contabilidad.tasks import (
    refrescar_mv_balance_cliente,
    recordar_facturacion_mensual_pendiente,
)


REFRESH_SQL = "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_balance_cliente;"


@pytest.mark.django_db
def test_refrescar_mv_balance_cliente_ejecuta_sql():
    """La tarea ejecuta el REFRESH MATERIALIZED VIEW correcto."""
    mock_cursor = MagicMock()
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cm.__exit__ = MagicMock(return_value=False)

    with patch("apps.contabilidad.tasks.connection") as mock_conn:
        mock_conn.cursor.return_value = mock_cm
        refrescar_mv_balance_cliente.apply()

    mock_cursor.execute.assert_called_once_with(REFRESH_SQL)


@pytest.mark.django_db
def test_refrescar_mv_balance_cliente_reintenta_en_error():
    """Cuando el cursor falla, la tarea lanza Retry (max_retries=2)."""
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("materialized view no existe")
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cm.__exit__ = MagicMock(return_value=False)

    with patch("apps.contabilidad.tasks.connection") as mock_conn:
        mock_conn.cursor.return_value = mock_cm
        with pytest.raises(Retry):
            refrescar_mv_balance_cliente.apply(throw=True)


@pytest.mark.django_db
class TestRecordarFacturacionMensualPendiente:

    def test_sin_pendientes_retorna_cero(self, db):
        result = recordar_facturacion_mensual_pendiente()
        assert result == {"clientes_alertados": 0}

    def test_item_reciente_no_alerta(self, cliente):
        from apps.core.models import CargaSaldo
        cliente.modalidad_facturacion = "MENSUAL"
        cliente.save(update_fields=["modalidad_facturacion"])
        CargaSaldo.objects.create(
            cliente_origen=cliente,
            monto_cargado=Decimal("20000"),
            estado=CargaSaldo.Estado.CONFIRMADA,
            fecha_carga=timezone.now() - timedelta(days=5),
        )
        result = recordar_facturacion_mensual_pendiente()
        assert result == {"clientes_alertados": 0}

    def test_item_antiguo_modalidad_inmediata_no_alerta(self, cliente):
        from apps.core.models import CargaSaldo
        assert cliente.modalidad_facturacion == "INMEDIATA"
        CargaSaldo.objects.create(
            cliente_origen=cliente,
            monto_cargado=Decimal("20000"),
            estado=CargaSaldo.Estado.CONFIRMADA,
            fecha_carga=timezone.now() - timedelta(days=45),
        )
        result = recordar_facturacion_mensual_pendiente()
        assert result == {"clientes_alertados": 0}

    def test_item_antiguo_modalidad_mensual_alerta_a_admins(self, cliente, usuario_admin):
        from apps.core.models import CargaSaldo
        from apps.notificaciones.models import Notificacion
        cliente.modalidad_facturacion = "MENSUAL"
        cliente.save(update_fields=["modalidad_facturacion"])
        CargaSaldo.objects.create(
            cliente_origen=cliente,
            monto_cargado=Decimal("20000"),
            estado=CargaSaldo.Estado.CONFIRMADA,
            fecha_carga=timezone.now() - timedelta(days=45),
        )
        result = recordar_facturacion_mensual_pendiente()
        assert result == {"clientes_alertados": 1}
        notif = Notificacion.objects.get(usuario=usuario_admin)
        assert cliente.nombre_completo in notif.titulo
        assert "1 ítem" in notif.mensaje

    def test_agrupa_varios_items_del_mismo_cliente_en_una_alerta(self, cliente, usuario_admin):
        from apps.core.models import CargaSaldo
        from apps.notificaciones.models import Notificacion
        cliente.modalidad_facturacion = "MENSUAL"
        cliente.save(update_fields=["modalidad_facturacion"])
        for _ in range(3):
            CargaSaldo.objects.create(
                cliente_origen=cliente,
                monto_cargado=Decimal("10000"),
                estado=CargaSaldo.Estado.CONFIRMADA,
                fecha_carga=timezone.now() - timedelta(days=40),
            )
        result = recordar_facturacion_mensual_pendiente()
        assert result == {"clientes_alertados": 1}
        assert Notificacion.objects.filter(usuario=usuario_admin).count() == 1
        notif = Notificacion.objects.get(usuario=usuario_admin)
        assert "3 ítem" in notif.mensaje
