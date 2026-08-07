from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum

from apps.almuerzos.models import (
    CuentaAlmuerzoMensual, MovimientoSaldoAlmuerzo, SaldoAlmuerzo, SuscripcionAlmuerzo,
)


class Command(BaseCommand):
    help = (
        "Crea SaldoAlmuerzo (cuenta corriente) para cada hijo con historial o "
        "suscripcion de almuerzo. El saldo inicial es la suma historica de "
        "(monto_pagado - monto_total) de sus CuentaAlmuerzoMensual — traslada "
        "creditos y deudas ya existentes al saldo nuevo. Idempotente: no toca "
        "hijos que ya tienen SaldoAlmuerzo."
    )

    def handle(self, *args, **options):
        hijo_ids = set(
            CuentaAlmuerzoMensual.objects.values_list("hijo_id", flat=True)
        ) | set(
            SuscripcionAlmuerzo.objects.values_list("hijo_id", flat=True)
        )
        hijo_ids -= set(SaldoAlmuerzo.objects.values_list("hijo_id", flat=True))

        creados = 0
        with transaction.atomic():
            for hijo_id in hijo_ids:
                agg = CuentaAlmuerzoMensual.objects.filter(hijo_id=hijo_id).aggregate(
                    pagado=Sum("monto_pagado"), total=Sum("monto_total"),
                )
                saldo_inicial = (agg["pagado"] or Decimal("0")) - (agg["total"] or Decimal("0"))

                saldo = SaldoAlmuerzo.objects.create(hijo_id=hijo_id, saldo_actual=saldo_inicial)
                if saldo_inicial != 0:
                    MovimientoSaldoAlmuerzo.objects.create(
                        saldo=saldo,
                        tipo=MovimientoSaldoAlmuerzo.Tipo.AJUSTE,
                        monto=saldo_inicial,
                        saldo_resultante=saldo_inicial,
                        observaciones="Saldo inicial migrado desde CuentaAlmuerzoMensual histórica",
                    )
                creados += 1
                self.stdout.write(f"  {saldo.hijo}: saldo inicial ₲{saldo_inicial:,.0f}")

        if creados == 0:
            self.stdout.write(self.style.SUCCESS("No hay hijos pendientes de migrar."))
        else:
            self.stdout.write(self.style.SUCCESS(f"\n{creados} saldo(s) de almuerzo creado(s)."))
