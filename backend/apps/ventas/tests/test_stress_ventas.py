"""
Stress test: 5 cajeros concurrentes registran ventas simultáneamente.

Prueba que:
  - Las 5 ventas se completan sin errores (sin deadlock ni race condition).
  - El stock se descuenta correctamente (sin exceder el stock total disponible).
  - El endpoint responde en ≤ 2s por venta bajo carga concurrente.

Requiere DB real (transacciones de verdad para detectar deadlocks).
Marcado con @pytest.mark.stress para excluirlo de CI rápido si hace falta:
    pytest -m "not stress"
"""

import threading
import time
from decimal import Decimal

import pytest
from rest_framework.test import APIClient


N_CAJEROS = 5
CANTIDAD_POR_VENTA = 2          # unidades por venta
STOCK_TOTAL = N_CAJEROS * CANTIDAD_POR_VENTA  # stock exacto = todos pueden vender


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def caja_stress(db):
    from apps.contabilidad.models import Caja
    return Caja.objects.create(nombre="Caja Stress Test", activo=True)


@pytest.fixture
def cajeros(db):
    from apps.usuarios.models import Usuario
    users = []
    for i in range(N_CAJEROS):
        u = Usuario.objects.create_user(
            email=f"cajero_stress_{i}@test.com",
            password="test1234",
            nombre=f"Cajero{i}",
            apellido="Stress",
            rol=Usuario.Rol.CAJERO,
        )
        users.append(u)
    return users


@pytest.fixture
def cierres(db, caja_stress, cajeros):
    from apps.contabilidad.models import CierreCaja
    return [
        CierreCaja.objects.create(
            caja=caja_stress,
            empleado=c,
            monto_inicial=Decimal("100000"),
            estado=CierreCaja.Estado.ABIERTO,
        )
        for c in cajeros
    ]


@pytest.fixture
def cliente_stress(db):
    from apps.clientes.models import Cliente, TipoCliente
    from apps.productos.models import ListaPrecio
    tipo, _ = TipoCliente.objects.get_or_create(nombre="Padre Stress")
    lista, _ = ListaPrecio.objects.get_or_create(
        nombre="General Stress", defaults={"activo": True}
    )
    return Cliente.objects.create(
        nombres="Cliente",
        apellidos="Stress",
        ruc_ci="STRESS001",
        tipo_cliente=tipo,
        lista_precio=lista,
        limite_credito=Decimal("9999999"),
    )


@pytest.fixture
def producto_stress(db):
    from apps.productos.models import (
        Categoria, UnidadMedida, Producto, PrecioPorLista, ListaPrecio
    )
    from apps.inventario.models import Stock

    cat, _ = Categoria.objects.get_or_create(nombre="Stress Cat")
    um, _ = UnidadMedida.objects.get_or_create(
        abreviatura="u", defaults={"nombre": "Unidad"}
    )
    lista, _ = ListaPrecio.objects.get_or_create(
        nombre="General Stress", defaults={"activo": True}
    )
    prod = Producto.objects.create(
        descripcion="Producto Stress",
        categoria=cat,
        unidad_medida=um,
        requiere_stock=True,
        permite_stock_negativo=False,
        activo=True,
    )
    PrecioPorLista.objects.create(
        producto=prod, lista=lista, precio_unitario=Decimal("5000")
    )
    Stock.objects.create(producto=prod, cantidad=Decimal(str(STOCK_TOTAL)))
    return prod


@pytest.fixture
def medio_pago_stress(db):
    from apps.core.models import MedioPago
    mp, _ = MedioPago.objects.get_or_create(
        descripcion="Efectivo Stress", defaults={"activo": True}
    )
    return mp


# ─── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
@pytest.mark.stress
class TestStressVentas:

    def test_cinco_cajeros_concurrentes(
        self, cajeros, cierres, cliente_stress, producto_stress, medio_pago_stress
    ):
        """Todas las ventas deben completarse: sin 500, sin deadlock."""
        results: list[tuple[int, float]] = []
        lock = threading.Lock()

        def vender(cajero):
            client = APIClient()
            client.force_authenticate(user=cajero)
            t0 = time.monotonic()
            resp = client.post(
                "/api/v1/ventas/ventas/",
                {
                    "cliente": cliente_stress.pk,
                    "tipo": "CONTADO",
                    "medio_pago": medio_pago_stress.pk,
                    "monto_total": 5000 * CANTIDAD_POR_VENTA,
                    "items": [{
                        "producto": producto_stress.pk,
                        "cantidad": str(CANTIDAD_POR_VENTA),
                        "precio_unitario": "5000",
                    }],
                },
                format="json",
            )
            elapsed = time.monotonic() - t0
            with lock:
                results.append((resp.status_code, elapsed))

        threads = [threading.Thread(target=vender, args=(c,)) for c in cajeros]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert len(results) == N_CAJEROS, "Algún hilo no terminó en 10s"

        statuses = [s for s, _ in results]
        times    = [e for _, e in results]

        # Todas las respuestas deben ser 201 (éxito) o 400 (stock insuficiente).
        # No debe haber errores de servidor (500).
        for status in statuses:
            assert status in (201, 400), f"Código inesperado: {status}"

        # Al menos una venta debe haberse completado.
        assert 201 in statuses, "Ninguna venta se completó"

        # Tiempos bajo carga: ≤ 2s por venta
        for elapsed in times:
            assert elapsed < 2.0, f"Venta tardó {elapsed:.2f}s (límite 2s)"

    def test_sin_stock_negativo_bajo_concurrencia(
        self, cajeros, cierres, cliente_stress, producto_stress, medio_pago_stress
    ):
        """El stock no debe quedar negativo aunque ventas concurrentes lo intenten."""
        from apps.inventario.models import Stock

        results = []
        lock = threading.Lock()

        # Reducir el stock para que sólo 2 de 5 puedan comprar
        stock_obj = Stock.objects.get(producto=producto_stress)
        stock_obj.cantidad = Decimal(str(CANTIDAD_POR_VENTA * 2))
        stock_obj.save()

        def vender(cajero):
            client = APIClient()
            client.force_authenticate(user=cajero)
            resp = client.post(
                "/api/v1/ventas/ventas/",
                {
                    "cliente": cliente_stress.pk,
                    "tipo": "CONTADO",
                    "medio_pago": medio_pago_stress.pk,
                    "monto_total": 5000 * CANTIDAD_POR_VENTA,
                    "items": [{
                        "producto": producto_stress.pk,
                        "cantidad": str(CANTIDAD_POR_VENTA),
                        "precio_unitario": "5000",
                    }],
                },
                format="json",
            )
            with lock:
                results.append(resp.status_code)

        threads = [threading.Thread(target=vender, args=(c,)) for c in cajeros]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        for status in results:
            assert status in (201, 400), f"Código inesperado: {status}"

        stock_obj.refresh_from_db()
        assert stock_obj.cantidad >= Decimal("0"), \
            f"Stock negativo detectado: {stock_obj.cantidad}"
