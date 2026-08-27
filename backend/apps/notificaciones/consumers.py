import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework_simplejwt.tokens import AccessToken


# ── Shared auth helpers ───────────────────────────────────────────────────────

def _parse_token(query_string: str) -> str:
    for part in query_string.split("&"):
        if part.startswith("token="):
            return part[len("token="):]
    return ""


@database_sync_to_async
def _authenticate(token_str: str):
    from apps.usuarios.models import Usuario
    try:
        payload = AccessToken(token_str)
        return Usuario.objects.get(pk=payload["user_id"])
    except Exception:
        return None


# ── NotificacionConsumer ──────────────────────────────────────────────────────

class NotificacionConsumer(AsyncWebsocketConsumer):
    _parse_token = staticmethod(_parse_token)
    _authenticate = staticmethod(_authenticate)

    async def connect(self):
        token_str = self._parse_token(self.scope["query_string"].decode())
        user = await self._authenticate(token_str)
        if user is None:
            await self.close(code=4001)
            return
        self.group_name = f"notificaciones_{user.pk}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        pass  # canal unidireccional — el servidor solo emite, no recibe

    async def notificacion_nueva(self, event):
        await self.send(text_data=json.dumps(event["data"]))


# ── DashboardConsumer — KPI en tiempo real ────────────────────────────────────

class DashboardConsumer(AsyncWebsocketConsumer):
    """
    ws/dashboard/?token=<access>

    Envía un snapshot de KPIs al conectarse y recibe actualizaciones en tiempo
    real cuando se registran nuevas ventas (via signal → channel_layer.group_send).
    """

    GROUP = "dashboard_kpi"
    _parse_token = staticmethod(_parse_token)
    _authenticate = staticmethod(_authenticate)

    async def connect(self):
        token_str = self._parse_token(self.scope["query_string"].decode())
        user = await self._authenticate(token_str)
        if user is None:
            await self.close(code=4001)
            return
        await self.channel_layer.group_add(self.GROUP, self.channel_name)
        await self.accept()
        snapshot = await self._get_kpis()
        await self.send(text_data=json.dumps({"type": "kpi_snapshot", **snapshot}))

    async def disconnect(self, code):
        if hasattr(self, "channel_name"):
            await self.channel_layer.group_discard(self.GROUP, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        pass  # clientes solo escuchan

    async def kpi_update(self, event):
        """Recibe broadcast desde el signal post_save de Venta."""
        await self.send(text_data=json.dumps(event["data"]))

    @database_sync_to_async
    def _get_kpis(self) -> dict:
        from django.db.models import Count, Sum, F
        from django.utils.timezone import localdate
        from apps.ventas.models import Venta
        from apps.clientes.models import Cliente, Hijo
        from apps.productos.models import Producto
        from apps.inventario.models import AlertaStock
        from apps.contabilidad.models import CierreCaja
        from apps.core.models import CargaSaldo, Tarjeta
        from apps.almuerzos.models import RegistroConsumoAlmuerzo

        hoy = localdate()
        ventas_hoy = Venta.objects.filter(
            fecha__date=hoy, estado=Venta.Estado.ACTIVA,
        ).aggregate(cantidad=Count("id"), monto=Sum("monto_total"))

        recargas_hoy = CargaSaldo.objects.filter(
            fecha_carga__date=hoy, estado=CargaSaldo.Estado.CONFIRMADA,
        ).aggregate(cantidad=Count("id"), monto=Sum("monto_cargado"))

        almuerzos_hoy = RegistroConsumoAlmuerzo.objects.filter(fecha_consumo=hoy).count()

        tarjetas_alerta = Tarjeta.objects.filter(
            notificar_saldo_bajo=True,
            saldo_alerta__isnull=False,
            saldo_actual__lte=F("saldo_alerta"),
        ).count()

        cumpleaneros_hoy = list(
            Hijo.objects.filter(
                fecha_nacimiento__month=hoy.month,
                fecha_nacimiento__day=hoy.day,
                activo=True,
            ).select_related("grado").values("id", "nombre", "apellido", "grado__nombre")
        )

        return {
            "ventasHoy":       ventas_hoy["cantidad"] or 0,
            "montoHoy":        int(ventas_hoy["monto"] or 0),
            "clientes":        Cliente.objects.filter(activo=True).count(),
            "productos":       Producto.objects.filter(activo=True).count(),
            "stockBajo":       AlertaStock.objects.filter(activa=True).count(),
            "cajasAbiertas":   CierreCaja.objects.filter(estado=CierreCaja.Estado.ABIERTO).count(),
            "recargasHoy":     recargas_hoy["cantidad"] or 0,
            "montoRecargasHoy": int(recargas_hoy["monto"] or 0),
            "almuerzoHoy":     almuerzos_hoy,
            "tarjetasEnAlerta": tarjetas_alerta,
            "cumpleanosHoy":   len(cumpleaneros_hoy),
            "cumpleaneros": [
                {"id": h["id"], "nombre": f'{h["nombre"]} {h["apellido"]}', "grado": h["grado__nombre"]}
                for h in cumpleaneros_hoy
            ],
        }
