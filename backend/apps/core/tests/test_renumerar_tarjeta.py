"""
Tests para TarjetaService.renumerar — corregir/reemplazar el número de una
tarjeta (su PK) sin perder nada de lo que ya tenía enganchado: movimientos,
cargas, pagos Bancard, ventas y consumos de almuerzo.
"""
from decimal import Decimal

import pytest
from rest_framework.exceptions import ValidationError


@pytest.fixture
def grado_ren(db):
    from apps.clientes.models import Grado
    g, _ = Grado.objects.get_or_create(nombre="G-REN", defaults={"nivel": 2, "orden": 2})
    return g


@pytest.fixture
def hijo_ren(db, cliente, grado_ren):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Renu", apellido="Merar", cliente_responsable=cliente, grado=grado_ren, activo=True,
    )


@pytest.fixture
def tarjeta_ren(db, hijo_ren):
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(nro_tarjeta="REN-VIEJO", hijo=hijo_ren)


@pytest.mark.django_db
class TestRenumerar:

    def test_renumera_tarjeta_sin_movimientos(self, tarjeta_ren, usuario_admin):
        from apps.core.models import Tarjeta
        from apps.core.services import TarjetaService

        nueva = TarjetaService.renumerar(
            tarjeta=tarjeta_ren, nro_nuevo="REN-NUEVO", motivo="TIPEO", usuario=usuario_admin,
        )

        assert nueva.pk == "REN-NUEVO"
        assert not Tarjeta.objects.filter(pk="REN-VIEJO").exists()
        assert nueva.hijo_id == tarjeta_ren.hijo_id

    def test_renumera_y_mueve_los_5_tipos_de_referencia(
        self, tarjeta_ren, hijo_ren, cliente, usuario_admin, usuario_cajero,
    ):
        """El caso real: una tarjeta usada, con historial en las 5 tablas que
        referencian nro_tarjeta. Verifica que ninguna quede huérfana ni
        bloquee el cambio (las FK ya son deferrable en la base para esto)."""
        from decimal import Decimal as D
        from apps.core.models import Tarjeta, MovimientoTarjeta, CargaSaldo, PagoBancard
        from apps.core.services import TarjetaService
        from apps.ventas.models import Venta
        from apps.almuerzos.models import RegistroConsumoAlmuerzo

        mov = MovimientoTarjeta.objects.create(
            tarjeta=tarjeta_ren, tipo=MovimientoTarjeta.Tipo.RECARGA,
            monto=D("10000"), saldo_anterior=D("0"), saldo_resultante=D("10000"),
        )
        carga = CargaSaldo.objects.create(
            tarjeta=tarjeta_ren, monto_cargado=D("10000"), estado=CargaSaldo.Estado.CONFIRMADA,
        )
        pago = PagoBancard.objects.create(
            tarjeta=tarjeta_ren, shop_process_id="shop-ren-1", monto=D("10000"),
        )
        venta = Venta.objects.create(
            cliente=cliente, cajero=usuario_cajero, tipo="CREDITO",
            estado_pago="PENDIENTE", monto_total=D("5000"), tarjeta=tarjeta_ren,
        )
        consumo = RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_ren, fecha_consumo="2026-07-15", nro_tarjeta=tarjeta_ren,
            costo_almuerzo=D("15000"), ya_cobrado=True, registrado_por=usuario_cajero,
        )

        TarjetaService.renumerar(
            tarjeta=tarjeta_ren, nro_nuevo="REN-NUEVO", motivo="EXTRAVIO", usuario=usuario_admin,
        )

        assert not Tarjeta.objects.filter(pk="REN-VIEJO").exists()
        mov.refresh_from_db(); assert mov.tarjeta_id == "REN-NUEVO"
        carga.refresh_from_db(); assert carga.tarjeta_id == "REN-NUEVO"
        pago.refresh_from_db(); assert pago.tarjeta_id == "REN-NUEVO"
        venta.refresh_from_db(); assert venta.tarjeta_id == "REN-NUEVO"
        consumo.refresh_from_db(); assert consumo.nro_tarjeta_id == "REN-NUEVO"

    def test_numero_nuevo_vacio_falla(self, tarjeta_ren, usuario_admin):
        from apps.core.services import TarjetaService
        with pytest.raises(ValidationError, match="obligatorio"):
            TarjetaService.renumerar(
                tarjeta=tarjeta_ren, nro_nuevo="  ", motivo="TIPEO", usuario=usuario_admin,
            )

    def test_numero_igual_al_actual_falla(self, tarjeta_ren, usuario_admin):
        from apps.core.services import TarjetaService
        with pytest.raises(ValidationError, match="igual al actual"):
            TarjetaService.renumerar(
                tarjeta=tarjeta_ren, nro_nuevo="REN-VIEJO", motivo="TIPEO", usuario=usuario_admin,
            )

    def test_numero_nuevo_ya_existe_falla(self, tarjeta_ren, hijo_ren, cliente, usuario_admin):
        from apps.clientes.models import Hijo, Grado
        from apps.core.models import Tarjeta
        from apps.core.services import TarjetaService

        grado, _ = Grado.objects.get_or_create(nombre="G-REN2", defaults={"nivel": 3, "orden": 3})
        otro_hijo = Hijo.objects.create(
            nombre="Otra", apellido="Tarjeta", cliente_responsable=cliente, grado=grado, activo=True,
        )
        Tarjeta.objects.create(nro_tarjeta="REN-OCUPADO", hijo=otro_hijo)

        with pytest.raises(ValidationError, match="Ya existe"):
            TarjetaService.renumerar(
                tarjeta=tarjeta_ren, nro_nuevo="REN-OCUPADO", motivo="TIPEO", usuario=usuario_admin,
            )

    def test_motivo_invalido_falla(self, tarjeta_ren, usuario_admin):
        from apps.core.services import TarjetaService
        with pytest.raises(ValidationError, match="Motivo inválido"):
            TarjetaService.renumerar(
                tarjeta=tarjeta_ren, nro_nuevo="REN-NUEVO", motivo="INVENTADO", usuario=usuario_admin,
            )

    def test_motivo_otro_sin_detalle_falla(self, tarjeta_ren, usuario_admin):
        from apps.core.services import TarjetaService
        with pytest.raises(ValidationError, match="Aclará el motivo"):
            TarjetaService.renumerar(
                tarjeta=tarjeta_ren, nro_nuevo="REN-NUEVO", motivo="OTRO",
                motivo_detalle="", usuario=usuario_admin,
            )

    def test_motivo_otro_con_detalle_ok(self, tarjeta_ren, usuario_admin):
        from apps.core.services import TarjetaService
        nueva = TarjetaService.renumerar(
            tarjeta=tarjeta_ren, nro_nuevo="REN-NUEVO", motivo="OTRO",
            motivo_detalle="Motivo particular del colegio", usuario=usuario_admin,
        )
        assert nueva.pk == "REN-NUEVO"
