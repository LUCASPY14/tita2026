"""
Cobertura de ramas no alcanzadas en core/models.py:
  - Tarjeta.clean() — 4 branches de validación
  - MovimientoTarjeta.__str__() — tipo REVERSO (signo +)
  - MovimientoTarjeta.save() — saldo_anterior=None sin movimientos previos
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError


@pytest.fixture
def hijo(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Test", apellido="Clean",
        cliente_responsable=cliente, activo=True,
    )


@pytest.fixture
def tarjeta_existente(db, hijo):
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(
        nro_tarjeta="CLEAN001",
        hijo=hijo,
        saldo_actual=Decimal("0"),
        estado=Tarjeta.Estado.ACTIVA,
    )


# ==============================================================================
# Tarjeta.clean()
# ==============================================================================

@pytest.mark.django_db
class TestTarjetaClean:

    def test_clean_sin_hijo_ni_cliente_directo_falla(self, db):
        from apps.core.models import Tarjeta
        t = Tarjeta(
            nro_tarjeta="CLEAN-BAD1",
            saldo_actual=Decimal("0"),
            estado=Tarjeta.Estado.ACTIVA,
        )
        with pytest.raises(ValidationError, match="debe tener un alumno"):
            t.clean()

    def test_clean_con_hijo_y_cliente_directo_falla(self, db, hijo, cliente):
        from apps.core.models import Tarjeta
        t = Tarjeta(
            nro_tarjeta="CLEAN-BAD2",
            hijo=hijo,
            cliente_directo=cliente,
            saldo_actual=Decimal("0"),
            estado=Tarjeta.Estado.ACTIVA,
        )
        with pytest.raises(ValidationError, match="no puede tener alumno y cliente"):
            t.clean()

    def test_clean_hijo_ya_tiene_tarjeta_falla(self, db, hijo, tarjeta_existente):
        from apps.core.models import Tarjeta
        t = Tarjeta(
            nro_tarjeta="CLEAN-DUP1",
            hijo=hijo,
            saldo_actual=Decimal("0"),
            estado=Tarjeta.Estado.ACTIVA,
        )
        with pytest.raises(ValidationError) as exc_info:
            t.clean()
        assert "hijo" in exc_info.value.message_dict

    def test_clean_cliente_directo_ya_tiene_tarjeta_falla(self, db, cliente):
        from apps.core.models import Tarjeta
        Tarjeta.objects.create(
            nro_tarjeta="CLEAN-CD1",
            cliente_directo=cliente,
            saldo_actual=Decimal("0"),
            estado=Tarjeta.Estado.ACTIVA,
        )
        t = Tarjeta(
            nro_tarjeta="CLEAN-CD2",
            cliente_directo=cliente,
            saldo_actual=Decimal("0"),
            estado=Tarjeta.Estado.ACTIVA,
        )
        with pytest.raises(ValidationError) as exc_info:
            t.clean()
        assert "cliente_directo" in exc_info.value.message_dict

    def test_clean_valida_correctamente_con_hijo(self, db, hijo, tarjeta_existente):
        """Misma tarjeta (excluida por nro_tarjeta) no genera duplicado."""
        from apps.core.models import Tarjeta
        # Actualizar la tarjeta existente pasa clean sin error (se excluye a sí misma)
        t = Tarjeta.objects.get(pk=tarjeta_existente.pk)
        t.clean()  # no debe lanzar


# ==============================================================================
# MovimientoTarjeta.__str__() — tipo REVERSO
# ==============================================================================

@pytest.mark.django_db
class TestMovimientoTarjetaStr:

    def test_str_tipo_reverso_muestra_signo_positivo(self, db, hijo):
        from apps.core.models import Tarjeta, MovimientoTarjeta
        tarjeta = Tarjeta.objects.create(
            nro_tarjeta="MOV-REV01",
            hijo=hijo,
            saldo_actual=Decimal("50000"),
            estado=Tarjeta.Estado.ACTIVA,
        )
        mov = MovimientoTarjeta.objects.create(
            tarjeta=tarjeta,
            tipo=MovimientoTarjeta.Tipo.REVERSO,
            monto=Decimal("10000"),
            saldo_anterior=Decimal("50000"),
            saldo_resultante=Decimal("60000"),
        )
        assert str(mov).startswith("Reverso")
        assert "+₲10,000" in str(mov)

    def test_str_tipo_recarga_muestra_signo_positivo(self, db, hijo):
        from apps.core.models import Tarjeta, MovimientoTarjeta
        tarjeta = Tarjeta.objects.create(
            nro_tarjeta="MOV-REC01",
            hijo=hijo,
            saldo_actual=Decimal("30000"),
            estado=Tarjeta.Estado.ACTIVA,
        )
        mov = MovimientoTarjeta.objects.create(
            tarjeta=tarjeta,
            tipo=MovimientoTarjeta.Tipo.RECARGA,
            monto=Decimal("20000"),
            saldo_anterior=Decimal("10000"),
            saldo_resultante=Decimal("30000"),
        )
        assert "+₲20,000" in str(mov)

    def test_str_tipo_consumo_muestra_signo_negativo(self, db, hijo):
        from apps.core.models import Tarjeta, MovimientoTarjeta
        tarjeta = Tarjeta.objects.create(
            nro_tarjeta="MOV-CONS01",
            hijo=hijo,
            saldo_actual=Decimal("40000"),
            estado=Tarjeta.Estado.ACTIVA,
        )
        mov = MovimientoTarjeta.objects.create(
            tarjeta=tarjeta,
            tipo=MovimientoTarjeta.Tipo.CONSUMO,
            monto=Decimal("5000"),
            saldo_anterior=Decimal("40000"),
            saldo_resultante=Decimal("35000"),
        )
        assert "-₲5,000" in str(mov)


# ==============================================================================
# MovimientoTarjeta.save() — saldo_anterior=None sin movimientos previos
# ==============================================================================

@pytest.mark.django_db
class TestMovimientoTarjetaSave:

    def test_save_sin_saldo_anterior_y_sin_movimientos_previos_usa_cero(self, db, hijo):
        """Cuando saldo_anterior=None y no hay movimientos anteriores → usa Decimal('0')."""
        from apps.core.models import Tarjeta, MovimientoTarjeta
        tarjeta = Tarjeta.objects.create(
            nro_tarjeta="MOV-NOSALDO01",
            hijo=hijo,
            saldo_actual=Decimal("0"),
            estado=Tarjeta.Estado.ACTIVA,
        )
        mov = MovimientoTarjeta(
            tarjeta=tarjeta,
            tipo=MovimientoTarjeta.Tipo.RECARGA,
            monto=Decimal("15000"),
            saldo_anterior=None,
        )
        mov.save()
        mov.refresh_from_db()
        assert mov.saldo_anterior == Decimal("0")
        assert mov.saldo_resultante == Decimal("15000")
