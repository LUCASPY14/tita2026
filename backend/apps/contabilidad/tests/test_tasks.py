import pytest
from unittest.mock import patch, MagicMock
from celery.exceptions import Retry

from apps.contabilidad.tasks import refrescar_mv_balance_cliente


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
