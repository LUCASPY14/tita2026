from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Venta


@receiver(post_save, sender=Venta)
def broadcast_kpi_update(sender, instance, **kwargs):
    """Tras guardar una Venta, actualiza el dashboard KPI en tiempo real."""
    from django.db.models import Count, Sum
    from django.utils.timezone import localdate
    from apps.clientes.models import Cliente
    from apps.productos.models import Producto
    from apps.inventario.models import AlertaStock
    from apps.contabilidad.models import CierreCaja

    hoy = localdate()
    ventas_hoy = Venta.objects.filter(
        fecha__date=hoy, estado=Venta.Estado.ACTIVA,
    ).aggregate(cantidad=Count("id"), monto=Sum("monto_total"))

    data = {
        "type":          "kpi_update",
        "ventasHoy":     ventas_hoy["cantidad"] or 0,
        "montoHoy":      int(ventas_hoy["monto"] or 0),
        "clientes":      Cliente.objects.filter(activo=True).count(),
        "productos":     Producto.objects.filter(activo=True).count(),
        "stockBajo":     AlertaStock.objects.filter(activa=True).count(),
        "cajasAbiertas": CierreCaja.objects.filter(estado=CierreCaja.Estado.ABIERTO).count(),
    }

    layer = get_channel_layer()
    if layer is not None:
        async_to_sync(layer.group_send)("dashboard_kpi", {"type": "kpi_update", "data": data})
