"""
Test de integración WebSocket — ventas.signals.broadcast_kpi_update → DashboardConsumer.

Usa WebsocketCommunicator con InMemoryChannelLayer (configurado por defecto en
backend.settings.test) para verificar el flujo completo:
  Venta.save() → post_save signal → channel_layer.group_send("dashboard_kpi") → consumer
"""
import asyncio
import pytest
from decimal import Decimal


# ── helpers ────────────────────────────────────────────────────────────────────

def _token(user):
    from rest_framework_simplejwt.tokens import AccessToken
    return str(AccessToken.for_user(user))


def _communicator(token):
    from channels.testing import WebsocketCommunicator
    from apps.notificaciones.consumers import DashboardConsumer
    return WebsocketCommunicator(
        DashboardConsumer.as_asgi(),
        f"ws/dashboard/?token={token}",
    )


# ── snapshot al conectar ───────────────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
def test_dashboard_envia_snapshot_al_conectar(usuario_admin):
    """Al conectarse con JWT válido, el consumer responde con kpi_snapshot."""

    async def _test():
        comm = _communicator(_token(usuario_admin))
        connected, _ = await comm.connect()
        assert connected, "La conexión debe aceptarse"

        msg = await comm.receive_json_from(timeout=3)
        assert msg["type"] == "kpi_snapshot"
        for key in ("ventasHoy", "montoHoy", "clientes", "productos", "stockBajo", "cajasAbiertas"):
            assert key in msg, f"Falta campo '{key}' en kpi_snapshot"

        await comm.disconnect()

    asyncio.run(_test())


# ── rechazo sin token válido ───────────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
def test_dashboard_rechaza_token_invalido():
    """Sin JWT válido el consumer cierra con código 4001."""

    async def _test():
        from channels.testing import WebsocketCommunicator
        from apps.notificaciones.consumers import DashboardConsumer
        comm = WebsocketCommunicator(
            DashboardConsumer.as_asgi(),
            "ws/dashboard/?token=esto_no_es_un_jwt",
        )
        connected, code = await comm.connect()
        assert not connected
        assert code == 4001

    asyncio.run(_test())


# ── broadcast kpi_update al crear una Venta ────────────────────────────────────

@pytest.mark.django_db(transaction=True)
def test_venta_creada_emite_kpi_update(
    usuario_admin, cliente, producto, stock_producto, medio_pago_efectivo,
):
    """
    Crear una Venta mediante VentaService dispara post_save → broadcast_kpi_update
    (ventas/signals.py) → group_send("dashboard_kpi") → el consumer conectado
    recibe un mensaje kpi_update con los campos KPI correctos.
    """
    from asgiref.sync import sync_to_async
    from apps.ventas.services import VentaService
    from apps.contabilidad.models import Caja, CierreCaja

    # Caja abierta (creada antes de entrar en el loop async — ya committed)
    caja = Caja.objects.create(nombre="Caja WS Test", activo=True)
    cierre = CierreCaja.objects.create(
        caja=caja,
        empleado=usuario_admin,
        monto_inicial=Decimal("100000"),
        estado=CierreCaja.Estado.ABIERTO,
    )

    async def _test():
        comm = _communicator(_token(usuario_admin))
        connected, _ = await comm.connect()
        assert connected

        # Descartamos el snapshot inicial
        snapshot = await comm.receive_json_from(timeout=3)
        assert snapshot["type"] == "kpi_snapshot"

        # Crear una Venta — dispara el signal en el hilo del thread-pool;
        # async_to_sync dentro del signal lo agenda en este event loop.
        await sync_to_async(VentaService.registrar_venta)(
            cliente=cliente,
            cajero=usuario_admin,
            tipo="CONTADO",
            medio_pago=medio_pago_efectivo,
            items=[{
                "producto": producto,
                "cantidad": Decimal("2"),
                "precio_unitario": Decimal("3000"),
            }],
            cierre_caja=cierre,
        )

        # El consumer debe recibir kpi_update vía group_send("dashboard_kpi")
        update = await comm.receive_json_from(timeout=3)
        assert update["type"] == "kpi_update"
        for key in ("ventasHoy", "montoHoy", "clientes", "productos", "stockBajo", "cajasAbiertas"):
            assert key in update, f"Falta campo '{key}' en kpi_update"

        assert update["ventasHoy"] >= 1
        assert update["montoHoy"] > 0

        await comm.disconnect()

    asyncio.run(_test())


# ── kpi_update refleja el estado real de la BD ────────────────────────────────

@pytest.mark.django_db(transaction=True)
def test_kpi_update_cuenta_ventas_correctamente(
    usuario_admin, cliente, producto, stock_producto, medio_pago_efectivo,
):
    """
    Después de dos ventas, ventasHoy en kpi_update debe ser 2 y montoHoy la suma.
    """
    from asgiref.sync import sync_to_async
    from apps.ventas.services import VentaService
    from apps.contabilidad.models import Caja, CierreCaja

    caja = Caja.objects.create(nombre="Caja WS Doble", activo=True)
    cierre = CierreCaja.objects.create(
        caja=caja,
        empleado=usuario_admin,
        monto_inicial=Decimal("500000"),
        estado=CierreCaja.Estado.ABIERTO,
    )
    items = [{"producto": producto, "cantidad": Decimal("1"), "precio_unitario": Decimal("3000")}]
    kwargs = dict(
        cliente=cliente, cajero=usuario_admin, tipo="CONTADO",
        medio_pago=medio_pago_efectivo, items=items, cierre_caja=cierre,
    )

    async def _test():
        comm = _communicator(_token(usuario_admin))
        connected, _ = await comm.connect()
        assert connected

        await comm.receive_json_from(timeout=3)  # snapshot

        # Primera venta
        await sync_to_async(VentaService.registrar_venta)(**kwargs)
        update1 = await comm.receive_json_from(timeout=3)
        assert update1["ventasHoy"] == 1

        # Segunda venta
        await sync_to_async(VentaService.registrar_venta)(**kwargs)
        update2 = await comm.receive_json_from(timeout=3)
        assert update2["ventasHoy"] == 2
        assert update2["montoHoy"] == 6000  # 2 × Gs 3000

        await comm.disconnect()

    asyncio.run(_test())
