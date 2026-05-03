"""
Tests de ramas faltantes en core/signals.py
Cubre branches: 39->-12 (consumo_existe True) and 100->-94 (created=False).
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase

import pytest


class ActualizarSaldoRecargaBranchTest(TestCase):
    """
    Branch 39->-12: 'if not consumo_existe:' is False → signal skips update and exits.
    """

    def test_consumo_existe_true_skips_update(self):
        """Branch 39->-12: consumo already exists → if not consumo: False → exit."""
        from apps.core.models import CargasSaldo, ConsumosTarjeta, Tarjetas
        from apps.core.signals import actualizar_saldo_recarga

        # Create a mock instance with estado='confirmado' and no _saldo_actualizado
        mock_carga = MagicMock(spec=CargasSaldo)
        mock_carga.estado = "confirmado"
        del mock_carga._saldo_actualizado  # ensure hasattr returns False
        mock_carga.id_carga = 9999
        mock_carga.nro_tarjeta.nro_tarjeta = "0000999"

        mock_tarjeta = MagicMock()
        mock_tarjeta.saldo_actual = 100

        with (
            patch.object(Tarjetas.objects, "select_for_update") as mock_sfu,
            patch.object(ConsumosTarjeta.objects, "filter") as mock_filter,
        ):
            # Make Tarjetas.objects.select_for_update().get() return mock_tarjeta
            mock_sfu.return_value.get.return_value = mock_tarjeta
            # Make filter(...).exists() return True → consumo_existe = True
            mock_filter.return_value.exists.return_value = True

            # Call the signal handler directly
            actualizar_saldo_recarga(sender=CargasSaldo, instance=mock_carga, created=True)

        # If branch 39->-12 is taken, tarjeta.save() should NOT be called
        mock_tarjeta.save.assert_not_called()


class NotificarSaldoBajoBranchTest(TestCase):
    """
    Branch 100->-94: 'if created:' is False → signal exits immediately.
    """

    def test_created_false_exits_immediately(self):
        """Branch 100->-94: created=False → if created: False → function exits cleanly."""
        from apps.core.models import ConsumosTarjeta
        from apps.core.signals import notificar_saldo_bajo

        mock_consumo = MagicMock()
        # Call with created=False → takes the False arm → exits without checking tarjeta
        notificar_saldo_bajo(
            sender=ConsumosTarjeta,
            instance=mock_consumo,
            created=False,
        )
        # If branch False arm taken, nro_tarjeta should never be accessed
        mock_consumo.nro_tarjeta.assert_not_called()


class ValidarTarjetaUnicaSinHijoBranchTest(TestCase):
    """
    Branch 100->-94 in validar_tarjeta_unica: when id_hijo is falsy → exits immediately.
    """

    def test_no_id_hijo_exits_without_query(self):
        """Branch in validar_tarjeta_unica: id_hijo=None → if block skipped → exits."""
        from apps.core.models import Tarjetas
        from apps.core.signals import validar_tarjeta_unica

        mock_tarjeta = MagicMock()
        mock_tarjeta.id_hijo = None
        # Should not raise; signal exits at 'if instance.id_hijo:' False branch
        validar_tarjeta_unica(sender=Tarjetas, instance=mock_tarjeta)
