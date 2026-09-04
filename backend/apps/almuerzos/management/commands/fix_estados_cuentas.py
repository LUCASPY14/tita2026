from django.core.management.base import BaseCommand
from django.db.models import Count, Sum
from apps.almuerzos.models import CuentaAlmuerzoMensual, RegistroConsumoAlmuerzo


class Command(BaseCommand):
    help = "Recalcula monto_total y cantidad_almuerzos en CuentaAlmuerzoMensual desde los registros reales, luego corrige estados"

    def handle(self, *args, **options):
        cuentas = CuentaAlmuerzoMensual.objects.all()
        corregidas = 0

        for c in cuentas:
            # Totales reales desde los registros
            agg = RegistroConsumoAlmuerzo.objects.filter(
                hijo=c.hijo,
                fecha_consumo__year=c.anio,
                fecha_consumo__month=c.mes,
                ya_cobrado=True,
                estado=RegistroConsumoAlmuerzo.Estado.REGISTRADO,
            ).aggregate(
                total=Sum("costo_almuerzo"),
                cantidad=Count("id_registro_consumo"),
            )
            real_total = agg["total"] or 0
            real_cantidad = agg["cantidad"] or 0

            cambios = []
            if c.monto_total != real_total:
                cambios.append(f"monto_total {c.monto_total}→{real_total}")
                c.monto_total = real_total
            if c.cantidad_almuerzos != real_cantidad:
                cambios.append(f"cantidad {c.cantidad_almuerzos}→{real_cantidad}")
                c.cantidad_almuerzos = real_cantidad

            estado_anterior = c.estado
            c._calcular_estado()
            if c.estado != estado_anterior:
                cambios.append(f"estado {estado_anterior}→{c.estado}")

            if cambios:
                c.save(update_fields=["cantidad_almuerzos", "monto_total", "estado", "fecha_pago"])
                self.stdout.write(f"  {c.hijo} {c.mes:02d}/{c.anio}: {', '.join(cambios)}")
                corregidas += 1

        if corregidas == 0:
            self.stdout.write(self.style.SUCCESS("No se encontraron inconsistencias."))
        else:
            self.stdout.write(self.style.SUCCESS(f"\n{corregidas} cuenta(s) corregida(s)."))
