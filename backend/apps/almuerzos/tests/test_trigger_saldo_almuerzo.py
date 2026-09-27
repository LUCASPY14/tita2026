"""
Trigger trg_sync_saldo_almuerzo (migración 0029): saldo_actual de
SaldoAlmuerzo se recalcula solo, sumando MovimientoSaldoAlmuerzo.monto
(ya viene con signo), igual que trg_sync_saldo_tarjeta del lado de cantina.
"""
from decimal import Decimal

import pytest


@pytest.fixture
def hijo_trigger(db, cliente):
    from apps.clientes.models import Grado, Hijo
    grado, _ = Grado.objects.get_or_create(nombre="G-TRIG", defaults={"nivel": 2, "orden": 2})
    return Hijo.objects.create(
        nombre="Trig", apellido="Ger", cliente_responsable=cliente, grado=grado, activo=True,
    )


@pytest.mark.django_db
class TestTriggerSaldoAlmuerzo:

    def test_recarga_actualiza_saldo_solo(self, hijo_trigger):
        from apps.almuerzos.models import SaldoAlmuerzo, MovimientoSaldoAlmuerzo

        saldo = SaldoAlmuerzo.objects.create(hijo=hijo_trigger)
        assert saldo.saldo_actual == Decimal("0")

        MovimientoSaldoAlmuerzo.objects.create(
            saldo=saldo, tipo=MovimientoSaldoAlmuerzo.Tipo.RECARGA,
            monto=Decimal("30000"), saldo_resultante=Decimal("30000"),
        )
        saldo.refresh_from_db()
        assert saldo.saldo_actual == Decimal("30000")

    def test_consumo_resta_por_ser_negativo(self, hijo_trigger):
        from apps.almuerzos.models import SaldoAlmuerzo, MovimientoSaldoAlmuerzo

        saldo = SaldoAlmuerzo.objects.create(hijo=hijo_trigger)
        MovimientoSaldoAlmuerzo.objects.create(
            saldo=saldo, tipo=MovimientoSaldoAlmuerzo.Tipo.RECARGA,
            monto=Decimal("30000"), saldo_resultante=Decimal("30000"),
        )
        MovimientoSaldoAlmuerzo.objects.create(
            saldo=saldo, tipo=MovimientoSaldoAlmuerzo.Tipo.CONSUMO,
            monto=Decimal("-25000"), saldo_resultante=Decimal("5000"),
        )
        saldo.refresh_from_db()
        assert saldo.saldo_actual == Decimal("5000")

    def test_asignacion_directa_de_saldo_actual_se_descarta_en_el_proximo_movimiento(self, hijo_trigger):
        """Aunque alguien setee saldo_actual a mano (sin movimiento), el
        trigger lo recalcula desde el libro mayor apenas se cree cualquier
        movimiento real — el saldo "de mentira" no sobrevive."""
        from apps.almuerzos.models import SaldoAlmuerzo, MovimientoSaldoAlmuerzo

        saldo = SaldoAlmuerzo.objects.create(hijo=hijo_trigger, saldo_actual=Decimal("999999"))

        MovimientoSaldoAlmuerzo.objects.create(
            saldo=saldo, tipo=MovimientoSaldoAlmuerzo.Tipo.AJUSTE,
            monto=Decimal("1000"), saldo_resultante=Decimal("1000"),
        )
        saldo.refresh_from_db()
        assert saldo.saldo_actual == Decimal("1000")

    def test_multiples_movimientos_coinciden_con_la_suma_del_libro_mayor(self, hijo_trigger):
        from apps.almuerzos.models import SaldoAlmuerzo, MovimientoSaldoAlmuerzo

        saldo = SaldoAlmuerzo.objects.create(hijo=hijo_trigger)
        movimientos = [
            (MovimientoSaldoAlmuerzo.Tipo.RECARGA, Decimal("50000")),
            (MovimientoSaldoAlmuerzo.Tipo.CONSUMO, Decimal("-25000")),
            (MovimientoSaldoAlmuerzo.Tipo.CONSUMO, Decimal("-25000")),
            (MovimientoSaldoAlmuerzo.Tipo.AJUSTE, Decimal("-10000")),
        ]
        for tipo, monto in movimientos:
            MovimientoSaldoAlmuerzo.objects.create(
                saldo=saldo, tipo=tipo, monto=monto, saldo_resultante=Decimal("0"),
            )

        saldo.refresh_from_db()
        esperado = sum(m for _, m in movimientos)
        assert saldo.saldo_actual == esperado == Decimal("-10000")
