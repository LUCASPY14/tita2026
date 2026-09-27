"""
Tests para apps.core.tasks.verificar_consistencia_saldos — la red de
seguridad que revisa Tarjeta y SaldoAlmuerzo contra la suma real de sus
movimientos (los triggers de sincronización cubren todo lo que pasa por un
movimiento; esto detecta ediciones directas que los saltean por completo).
"""
from decimal import Decimal
from unittest.mock import patch

import pytest


@pytest.fixture
def hijo_vcs(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Verif", apellido="Consistencia", cliente_responsable=cliente, activo=True,
    )


@pytest.fixture
def tarjeta_vcs(db, hijo_vcs):
    from apps.core.models import Tarjeta, MovimientoTarjeta
    t = Tarjeta.objects.create(nro_tarjeta="VCS-01", hijo=hijo_vcs)
    MovimientoTarjeta.objects.create(
        tarjeta=t, tipo=MovimientoTarjeta.Tipo.RECARGA,
        monto=Decimal("10000"), saldo_anterior=Decimal("0"), saldo_resultante=Decimal("10000"),
    )
    t.refresh_from_db()
    return t


@pytest.mark.django_db
class TestVerificarConsistenciaSaldos:

    def test_sin_desajustes_no_manda_nada(self, tarjeta_vcs, hijo_vcs):
        from apps.almuerzos.models import SaldoAlmuerzo, MovimientoSaldoAlmuerzo
        from apps.core.tasks import verificar_consistencia_saldos

        saldo = SaldoAlmuerzo.objects.create(hijo=hijo_vcs)
        MovimientoSaldoAlmuerzo.objects.create(
            saldo=saldo, tipo=MovimientoSaldoAlmuerzo.Tipo.RECARGA,
            monto=Decimal("5000"), saldo_resultante=Decimal("5000"),
        )

        with patch("apps.notificaciones.services.EmailService.enviar_simple") as mock_email:
            result = verificar_consistencia_saldos()

        assert result == {"desajustes_tarjeta": 0, "desajustes_almuerzo": 0}
        mock_email.assert_not_called()

    def test_detecta_desajuste_de_tarjeta_editado_directo(self, tarjeta_vcs):
        """Un .update() directo salta save() y el trigger de movimientos
        (no toca core_movimientotarjeta) — exactamente lo que esta tarea
        debe detectar."""
        from apps.core.models import Tarjeta
        from apps.core.tasks import verificar_consistencia_saldos

        Tarjeta.objects.filter(pk=tarjeta_vcs.pk).update(saldo_actual=Decimal("999999"))

        with patch("apps.notificaciones.services.EmailService.enviar_simple") as mock_email:
            with patch("django.conf.settings.ADMINS", [("Admin", "admin@test.com")]):
                result = verificar_consistencia_saldos()

        assert result["desajustes_tarjeta"] == 1
        mock_email.assert_called_once()
        kwargs = mock_email.call_args[1]
        assert kwargs["destinatario_email"] == "admin@test.com"
        assert "VCS-01" in kwargs["cuerpo"]
        assert "999,999" in kwargs["cuerpo"]

    def test_detecta_desajuste_de_almuerzo_editado_directo(self, hijo_vcs):
        from apps.almuerzos.models import SaldoAlmuerzo, MovimientoSaldoAlmuerzo
        from apps.core.tasks import verificar_consistencia_saldos

        saldo = SaldoAlmuerzo.objects.create(hijo=hijo_vcs)
        MovimientoSaldoAlmuerzo.objects.create(
            saldo=saldo, tipo=MovimientoSaldoAlmuerzo.Tipo.RECARGA,
            monto=Decimal("5000"), saldo_resultante=Decimal("5000"),
        )
        SaldoAlmuerzo.objects.filter(pk=saldo.pk).update(saldo_actual=Decimal("-1"))

        with patch("apps.notificaciones.services.EmailService.enviar_simple") as mock_email:
            with patch("django.conf.settings.ADMINS", [("Admin", "admin@test.com")]):
                result = verificar_consistencia_saldos()

        assert result["desajustes_almuerzo"] == 1
        mock_email.assert_called_once()

    def test_sin_admins_no_falla(self, tarjeta_vcs):
        from apps.core.models import Tarjeta
        from apps.core.tasks import verificar_consistencia_saldos

        Tarjeta.objects.filter(pk=tarjeta_vcs.pk).update(saldo_actual=Decimal("1"))

        with patch("django.conf.settings.ADMINS", []):
            result = verificar_consistencia_saldos()

        assert result["desajustes_tarjeta"] == 1
