"""
Cobertura de ramas no alcanzadas en almuerzos/serializers.py:
  - PagoCuentaAlmuerzoSerializer.validate(): monto ≤ 0, monto > saldo
  - DetalleMenuDiarioSerializer.validate_cantidad(): valor ≤ 0
"""
import pytest
from datetime import date
from decimal import Decimal


@pytest.fixture
def grado(db):
    from apps.clientes.models import Grado
    g, _ = Grado.objects.get_or_create(
        nombre="3er Grado Test",
        defaults={"nivel": 3, "orden": 3, "activo": True},
    )
    return g


@pytest.fixture
def hijo_ser(db, cliente, grado):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="SerTest", apellido="A",
        cliente_responsable=cliente, grado=grado, activo=True,
    )


@pytest.fixture
def cuenta_almuerzo(db, hijo_ser):
    from apps.almuerzos.models import CuentaAlmuerzoMensual
    hoy = date.today()
    return CuentaAlmuerzoMensual.objects.create(
        hijo=hijo_ser,
        anio=hoy.year,
        mes=hoy.month,
        cantidad_almuerzos=20,
        monto_total=Decimal("60000"),
        forma_cobro=CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
    )


# ==============================================================================
# RegistroConsumoAlmuerzoSerializer.validate()
# ==============================================================================

@pytest.mark.django_db
# NOTA: RegistroConsumoAlmuerzoSerializer ya no valida "suscripcion" (pasó a
# ser read_only — se resuelve del lado del servidor vía
# validators.resolver_suscripcion_activa, no la elige el cliente). La
# cobertura de "no pertenece al hijo" / "fecha_inicio futura" / "vencida" vive
# ahora en test_validators.py::TestResolverSuscripcionActiva.


# ==============================================================================
# PagoCuentaAlmuerzoSerializer.validate()
# ==============================================================================

@pytest.mark.django_db
class TestPagoCuentaAlmuerzoSerializerValidate:

    def test_monto_cero_falla(self, cuenta_almuerzo, usuario_cajero):
        from apps.almuerzos.serializers import PagoCuentaAlmuerzoSerializer
        ser = PagoCuentaAlmuerzoSerializer(data={
            "cuenta": cuenta_almuerzo.pk,
            "monto": "0",
            "medio_pago": "EFECTIVO",
            "registrado_por": usuario_cajero.pk,
        })
        assert not ser.is_valid()
        assert "monto" in ser.errors

    def test_monto_negativo_falla(self, cuenta_almuerzo, usuario_cajero):
        from apps.almuerzos.serializers import PagoCuentaAlmuerzoSerializer
        ser = PagoCuentaAlmuerzoSerializer(data={
            "cuenta": cuenta_almuerzo.pk,
            "monto": "-1000",
            "medio_pago": "EFECTIVO",
            "registrado_por": usuario_cajero.pk,
        })
        assert not ser.is_valid()
        assert "monto" in ser.errors

    def test_monto_mayor_a_saldo_pendiente_falla(self, cuenta_almuerzo, usuario_cajero):
        from apps.almuerzos.serializers import PagoCuentaAlmuerzoSerializer
        # saldo_pendiente = monto_total(60000) - monto_pagado(0) = 60000
        ser = PagoCuentaAlmuerzoSerializer(data={
            "cuenta": cuenta_almuerzo.pk,
            "monto": "99999",
            "medio_pago": "EFECTIVO",
            "registrado_por": usuario_cajero.pk,
        })
        assert not ser.is_valid()
        assert "monto" in ser.errors

    def test_monto_valido_ok(self, cuenta_almuerzo, usuario_cajero):
        from apps.almuerzos.serializers import PagoCuentaAlmuerzoSerializer
        ser = PagoCuentaAlmuerzoSerializer(data={
            "cuenta": cuenta_almuerzo.pk,
            "monto": "20000",
            "medio_pago": "EFECTIVO",
            "registrado_por": usuario_cajero.pk,
        })
        assert ser.is_valid(), ser.errors


# ==============================================================================
# DetalleMenuDiarioSerializer.validate_cantidad()
# ==============================================================================

@pytest.mark.django_db
class TestDetalleMenuDiarioSerializerValidateCantidad:

    @pytest.fixture
    def menu_diario(self, db):
        from apps.almuerzos.models import MenuDiario
        return MenuDiario.objects.create(
            fecha=date.today(),
            plato_principal="Sopa de verduras",
        )

    def test_cantidad_cero_falla(self, menu_diario, producto):
        from apps.almuerzos.serializers import DetalleMenuDiarioSerializer
        ser = DetalleMenuDiarioSerializer(data={
            "menu": menu_diario.pk,
            "producto": producto.pk,
            "cantidad": "0",
            "curso": "PLATO_PRINCIPAL",
        })
        assert not ser.is_valid()
        assert "cantidad" in ser.errors

    def test_cantidad_negativa_falla(self, menu_diario, producto):
        from apps.almuerzos.serializers import DetalleMenuDiarioSerializer
        ser = DetalleMenuDiarioSerializer(data={
            "menu": menu_diario.pk,
            "producto": producto.pk,
            "cantidad": "-5",
            "curso": "PLATO_PRINCIPAL",
        })
        assert not ser.is_valid()
        assert "cantidad" in ser.errors

    def test_cantidad_positiva_ok(self, menu_diario, producto):
        from apps.almuerzos.serializers import DetalleMenuDiarioSerializer
        ser = DetalleMenuDiarioSerializer(data={
            "menu": menu_diario.pk,
            "producto": producto.pk,
            "cantidad": "10",
            "curso": "PLATO_PRINCIPAL",
        })
        assert ser.is_valid(), ser.errors
