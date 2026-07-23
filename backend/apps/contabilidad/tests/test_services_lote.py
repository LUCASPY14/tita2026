"""
Tests para FacturacionService.emitir_lote.
Cubre las cuatro ramas (CARGA_SALDO, PAGO_ALMUERZO, VENTA, PAGO_CREDITO)
y sus validaciones principales: ids inexistentes, estados inválidos,
ya facturados, y clientes distintos.
"""
import pytest
from decimal import Decimal
from rest_framework.exceptions import ValidationError


# ─── Fixtures locales ─────────────────────────────────────────────────────────

@pytest.fixture
def hijo(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Lote",
        apellido="Test",
        cliente_responsable=cliente,
        activo=True,
    )


@pytest.fixture
def tarjeta(db, hijo):
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(
        nro_tarjeta="LOTE-TAR-001",
        hijo=hijo,
        saldo_actual=Decimal("0"),
    )


@pytest.fixture
def cuenta_mensual(db, hijo):
    from apps.almuerzos.models import CuentaAlmuerzoMensual
    return CuentaAlmuerzoMensual.objects.create(
        hijo=hijo,
        anio=2026,
        mes=6,
        cantidad_almuerzos=10,
        monto_total=Decimal("60000"),
        forma_cobro=CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
    )


@pytest.fixture
def cliente_2(db, tipo_cliente, lista_precio):
    from apps.clientes.models import Cliente
    return Cliente.objects.create(
        nombres="Otro",
        apellidos="Cliente",
        ruc_ci="LOTE_CLI_002",
        tipo_cliente=tipo_cliente,
        lista_precio=lista_precio,
    )


@pytest.fixture
def hijo_2(db, cliente_2):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Otro",
        apellido="Hijo",
        cliente_responsable=cliente_2,
        activo=True,
    )


def _carga_confirmada(tarjeta, cliente, monto=Decimal("20000")):
    from apps.core.models import CargaSaldo
    return CargaSaldo.objects.create(
        tarjeta=tarjeta,
        cliente_origen=cliente,
        monto_cargado=monto,
        estado=CargaSaldo.Estado.CONFIRMADA,
    )


def _pago_almuerzo(cuenta_mensual, cajero, monto=Decimal("20000")):
    from apps.almuerzos.models import PagoCuentaAlmuerzo
    return PagoCuentaAlmuerzo.objects.create(
        cuenta=cuenta_mensual,
        monto=monto,
        medio_pago="EFECTIVO",
        registrado_por=cajero,
    )


def _venta_con_factura(cliente, cajero, medio_pago, producto, stock_producto):
    from apps.ventas.services import VentaService
    return VentaService.registrar_venta(
        cliente=cliente,
        cajero=cajero,
        tipo="CONTADO",
        medio_pago=medio_pago,
        items=[{
            "producto": producto,
            "cantidad": Decimal("1"),
            "precio_unitario": Decimal("10000"),
        }],
        genera_factura_legal=True,
    )


def _pago_cc(cliente, cajero, genera=True):
    from apps.clientes.models import CuentaCorrienteCliente
    return CuentaCorrienteCliente.objects.create(
        cliente=cliente,
        tipo=CuentaCorrienteCliente.Tipo.CREDITO,
        monto=Decimal("15000"),
        saldo_anterior=Decimal("15000"),
        saldo_resultante=Decimal("0"),
        descripcion="Pago lote test",
        genera_factura_legal=genera,
        creado_por=cajero,
    )


# ─── emitir_lote — CARGA_SALDO ───────────────────────────────────────────────

@pytest.mark.django_db
class TestEmitirLoteCargaSaldo:

    def test_lote_carga_saldo_ok(self, tarjeta, cliente, usuario_cajero):
        from apps.contabilidad.services import FacturacionService
        from apps.contabilidad.models import Factura

        c1 = _carga_confirmada(tarjeta, cliente, Decimal("10000"))
        c2 = _carga_confirmada(tarjeta, cliente, Decimal("20000"))

        factura = FacturacionService.emitir_lote(
            tipo="CARGA_SALDO",
            ids=[c1.pk, c2.pk],
            nro_factura="001-001-9100001",
        )

        assert factura.estado == Factura.Estado.EMITIDA
        assert factura.monto_total == Decimal("30000")
        c1.refresh_from_db()
        c2.refresh_from_db()
        assert c1.factura_id == factura.pk
        assert c2.factura_id == factura.pk

    def test_lote_carga_ids_inexistentes_falla(self):
        from apps.contabilidad.services import FacturacionService

        with pytest.raises(ValidationError, match="no existen"):
            FacturacionService.emitir_lote(
                tipo="CARGA_SALDO",
                ids=[999998, 999999],
                nro_factura="001-001-9100002",
            )

    def test_lote_carga_sin_ids_falla(self):
        from apps.contabilidad.services import FacturacionService

        with pytest.raises(ValidationError, match="al menos un"):
            FacturacionService.emitir_lote(
                tipo="CARGA_SALDO",
                ids=[],
                nro_factura="001-001-9100003",
            )

    def test_lote_carga_no_confirmada_falla(self, tarjeta, cliente):
        from apps.contabilidad.services import FacturacionService
        from apps.core.models import CargaSaldo

        carga_pendiente = CargaSaldo.objects.create(
            tarjeta=tarjeta,
            cliente_origen=cliente,
            monto_cargado=Decimal("5000"),
            estado=CargaSaldo.Estado.PENDIENTE,
        )
        with pytest.raises(ValidationError, match="no está confirmada"):
            FacturacionService.emitir_lote(
                tipo="CARGA_SALDO",
                ids=[carga_pendiente.pk],
                nro_factura="001-001-9100004",
            )

    def test_lote_carga_ya_facturada_falla(self, tarjeta, cliente):
        from apps.contabilidad.services import FacturacionService

        c = _carga_confirmada(tarjeta, cliente)
        FacturacionService.emitir_lote(
            tipo="CARGA_SALDO",
            ids=[c.pk],
            nro_factura="001-001-9100005",
        )
        with pytest.raises(ValidationError, match="ya tiene factura"):
            FacturacionService.emitir_lote(
                tipo="CARGA_SALDO",
                ids=[c.pk],
                nro_factura="001-001-9100006",
            )

    def test_lote_carga_clientes_distintos_falla(
        self, tarjeta, cliente, hijo_2, cliente_2
    ):
        from apps.contabilidad.services import FacturacionService
        from apps.core.models import Tarjeta

        tarjeta_2 = Tarjeta.objects.create(
            nro_tarjeta="LOTE-TAR-002",
            hijo=hijo_2,
            saldo_actual=Decimal("0"),
        )
        c1 = _carga_confirmada(tarjeta, cliente)
        c2 = _carga_confirmada(tarjeta_2, cliente_2)

        with pytest.raises(ValidationError, match="mismo cliente"):
            FacturacionService.emitir_lote(
                tipo="CARGA_SALDO",
                ids=[c1.pk, c2.pk],
                nro_factura="001-001-9100007",
            )


# ─── emitir_lote — PAGO_ALMUERZO ─────────────────────────────────────────────

@pytest.mark.django_db
class TestEmitirLotePagoAlmuerzo:

    def test_lote_pago_almuerzo_ok(self, cuenta_mensual, hijo, cliente, usuario_cajero):
        from apps.contabilidad.services import FacturacionService
        from apps.contabilidad.models import Factura

        p1 = _pago_almuerzo(cuenta_mensual, usuario_cajero, Decimal("10000"))
        p2 = _pago_almuerzo(cuenta_mensual, usuario_cajero, Decimal("15000"))

        factura = FacturacionService.emitir_lote(
            tipo="PAGO_ALMUERZO",
            ids=[p1.pk, p2.pk],
            nro_factura="001-001-9200001",
        )

        assert factura.estado == Factura.Estado.EMITIDA
        assert factura.monto_total == Decimal("25000")
        p1.refresh_from_db()
        p2.refresh_from_db()
        assert p1.factura_id == factura.pk
        assert p2.factura_id == factura.pk

    def test_lote_pago_almuerzo_ya_facturado_falla(self, cuenta_mensual, usuario_cajero):
        from apps.contabilidad.services import FacturacionService

        p = _pago_almuerzo(cuenta_mensual, usuario_cajero)
        FacturacionService.emitir_lote(
            tipo="PAGO_ALMUERZO",
            ids=[p.pk],
            nro_factura="001-001-9200002",
        )
        with pytest.raises(ValidationError, match="ya tiene factura"):
            FacturacionService.emitir_lote(
                tipo="PAGO_ALMUERZO",
                ids=[p.pk],
                nro_factura="001-001-9200003",
            )

    def test_lote_pago_almuerzo_clientes_distintos_falla(
        self, cuenta_mensual, hijo_2, cliente_2, usuario_cajero
    ):
        from apps.contabilidad.services import FacturacionService
        from apps.almuerzos.models import CuentaAlmuerzoMensual, PagoCuentaAlmuerzo

        cuenta_2 = CuentaAlmuerzoMensual.objects.create(
            hijo=hijo_2,
            anio=2026,
            mes=6,
            cantidad_almuerzos=5,
            monto_total=Decimal("30000"),
            forma_cobro=CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
        )
        p1 = _pago_almuerzo(cuenta_mensual, usuario_cajero)
        p2 = _pago_almuerzo(cuenta_2, usuario_cajero)

        with pytest.raises(ValidationError, match="mismo cliente"):
            FacturacionService.emitir_lote(
                tipo="PAGO_ALMUERZO",
                ids=[p1.pk, p2.pk],
                nro_factura="001-001-9200004",
            )

    def test_lote_pago_almuerzo_ids_inexistentes_falla(self):
        from apps.contabilidad.services import FacturacionService

        with pytest.raises(ValidationError, match="no existen"):
            FacturacionService.emitir_lote(
                tipo="PAGO_ALMUERZO",
                ids=[999997],
                nro_factura="001-001-9200005",
            )


# ─── emitir_lote — VENTA ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEmitirLoteVenta:

    def test_lote_venta_ok(
        self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto
    ):
        from apps.contabilidad.services import FacturacionService
        from apps.contabilidad.models import Factura
        from apps.inventario.models import Stock
        from decimal import Decimal

        # Asegurar stock suficiente para 2 ventas
        Stock.objects.filter(producto=producto).update(cantidad=Decimal("100"))

        v1 = _venta_con_factura(cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto)
        v2 = _venta_con_factura(cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto)

        factura = FacturacionService.emitir_lote(
            tipo="VENTA",
            ids=[v1.pk, v2.pk],
            nro_factura="001-001-9300001",
        )

        assert factura.estado == Factura.Estado.EMITIDA
        assert factura.monto_total == v1.monto_total + v2.monto_total
        v1.refresh_from_db()
        v2.refresh_from_db()
        assert v1.nro_factura == "001-001-9300001"
        assert v2.nro_factura == "001-001-9300001"

    def test_lote_venta_anulada_falla(
        self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto, usuario_admin
    ):
        from apps.contabilidad.services import FacturacionService
        from apps.ventas.services import VentaService

        venta = _venta_con_factura(
            cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto
        )
        VentaService.anular_venta(venta, anulado_por=usuario_admin)

        with pytest.raises(ValidationError, match="anulada"):
            FacturacionService.emitir_lote(
                tipo="VENTA",
                ids=[venta.pk],
                nro_factura="001-001-9300002",
            )

    def test_lote_venta_sin_factura_legal_falla(
        self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto
    ):
        from apps.contabilidad.services import FacturacionService
        from apps.ventas.services import VentaService

        venta = VentaService.registrar_venta(
            cliente=cliente,
            cajero=usuario_cajero,
            tipo="CONTADO",
            medio_pago=medio_pago_efectivo,
            items=[{
                "producto": producto,
                "cantidad": Decimal("1"),
                "precio_unitario": Decimal("10000"),
            }],
            genera_factura_legal=False,
        )
        with pytest.raises(ValidationError, match="factura legal"):
            FacturacionService.emitir_lote(
                tipo="VENTA",
                ids=[venta.pk],
                nro_factura="001-001-9300003",
            )

    def test_lote_venta_ya_facturada_falla(
        self, cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto
    ):
        from apps.contabilidad.services import FacturacionService

        venta = _venta_con_factura(
            cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto
        )
        FacturacionService.emitir_lote(
            tipo="VENTA",
            ids=[venta.pk],
            nro_factura="001-001-9300004",
        )
        with pytest.raises(ValidationError, match="ya tiene factura"):
            FacturacionService.emitir_lote(
                tipo="VENTA",
                ids=[venta.pk],
                nro_factura="001-001-9300005",
            )

    def test_lote_venta_clientes_distintos_falla(
        self, cliente, cliente_2, usuario_cajero, medio_pago_efectivo, producto, stock_producto
    ):
        from apps.contabilidad.services import FacturacionService
        from apps.inventario.models import Stock

        Stock.objects.filter(producto=producto).update(cantidad=Decimal("100"))

        v1 = _venta_con_factura(
            cliente, usuario_cajero, medio_pago_efectivo, producto, stock_producto
        )
        v2 = _venta_con_factura(
            cliente_2, usuario_cajero, medio_pago_efectivo, producto, stock_producto
        )

        with pytest.raises(ValidationError, match="mismo cliente"):
            FacturacionService.emitir_lote(
                tipo="VENTA",
                ids=[v1.pk, v2.pk],
                nro_factura="001-001-9300006",
            )

    def test_lote_venta_ids_inexistentes_falla(self):
        from apps.contabilidad.services import FacturacionService

        with pytest.raises(ValidationError, match="no existen"):
            FacturacionService.emitir_lote(
                tipo="VENTA",
                ids=[999996],
                nro_factura="001-001-9300007",
            )


# ─── emitir_lote — PAGO_CREDITO ──────────────────────────────────────────────

@pytest.mark.django_db
class TestEmitirLotePagoCredito:

    def test_lote_pago_credito_ok(self, cliente, usuario_cajero):
        from apps.contabilidad.services import FacturacionService
        from apps.contabilidad.models import Factura

        p1 = _pago_cc(cliente, usuario_cajero)
        p2 = _pago_cc(cliente, usuario_cajero)

        factura = FacturacionService.emitir_lote(
            tipo="PAGO_CREDITO",
            ids=[p1.pk, p2.pk],
            nro_factura="001-001-9400001",
        )

        assert factura.estado == Factura.Estado.EMITIDA
        assert factura.monto_total == Decimal("30000")
        p1.refresh_from_db()
        p2.refresh_from_db()
        assert p1.factura_id == factura.pk
        assert p2.factura_id == factura.pk

    def test_lote_pago_credito_sin_factura_legal_falla(self, cliente, usuario_cajero):
        from apps.contabilidad.services import FacturacionService

        p = _pago_cc(cliente, usuario_cajero, genera=False)
        with pytest.raises(ValidationError, match="factura legal"):
            FacturacionService.emitir_lote(
                tipo="PAGO_CREDITO",
                ids=[p.pk],
                nro_factura="001-001-9400002",
            )

    def test_lote_pago_credito_ya_facturado_falla(self, cliente, usuario_cajero):
        from apps.contabilidad.services import FacturacionService

        p = _pago_cc(cliente, usuario_cajero)
        FacturacionService.emitir_lote(
            tipo="PAGO_CREDITO",
            ids=[p.pk],
            nro_factura="001-001-9400003",
        )
        with pytest.raises(ValidationError, match="ya tiene factura"):
            FacturacionService.emitir_lote(
                tipo="PAGO_CREDITO",
                ids=[p.pk],
                nro_factura="001-001-9400004",
            )

    def test_lote_pago_credito_clientes_distintos_falla(
        self, cliente, cliente_2, usuario_cajero
    ):
        from apps.contabilidad.services import FacturacionService

        p1 = _pago_cc(cliente, usuario_cajero)
        p2 = _pago_cc(cliente_2, usuario_cajero)

        with pytest.raises(ValidationError, match="mismo cliente"):
            FacturacionService.emitir_lote(
                tipo="PAGO_CREDITO",
                ids=[p1.pk, p2.pk],
                nro_factura="001-001-9400005",
            )

    def test_lote_pago_credito_ids_inexistentes_falla(self):
        from apps.contabilidad.services import FacturacionService

        with pytest.raises(ValidationError, match="no existen"):
            FacturacionService.emitir_lote(
                tipo="PAGO_CREDITO",
                ids=[999995],
                nro_factura="001-001-9400006",
            )


# ─── emitir_lote — tipo desconocido ──────────────────────────────────────────

@pytest.mark.django_db
class TestEmitirLoteTipoDesconocido:

    def test_tipo_desconocido_falla(self):
        from apps.contabilidad.services import FacturacionService

        with pytest.raises(ValidationError, match="Tipo desconocido"):
            FacturacionService.emitir_lote(
                tipo="INVALIDO",
                ids=[1],
                nro_factura="001-001-9900001",
            )
