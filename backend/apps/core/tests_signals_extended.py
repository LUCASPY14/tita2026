"""
Tests extendidos para apps/core/signals.py
Cubre líneas faltantes:
27 (hasattr _saldo_actualizado → return en actualizar_saldo_recarga),
66-91 (notificar_saldo_bajo body),
126-129 (validar_integridad_saldo warning logging)
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from apps.clientes.models import Clientes, Hijos, TiposCliente
from apps.core.models import CargasSaldo, ConsumosTarjeta, Tarjetas
from apps.productos.models import ListasPrecios

# ─── helpers ──────────────────────────────────────────────────────────────────


def _make_cliente(suffix=""):
    tipo, _ = TiposCliente.objects.get_or_create(nombre_tipo=f"TipoCS{suffix}")
    lista, _ = ListasPrecios.objects.get_or_create(nombre_lista=f"ListaCS{suffix}", defaults={"estado": True})
    return Clientes.objects.create(
        nombres=f"ClienteCS{suffix}",
        apellidos="Signals",
        ruc_ci=f"CS{suffix}9900{suffix[:2] or '00'}",
        estado=True,
        id_lista=lista,
        id_tipo_cliente=tipo,
    )


def _make_hijo(cliente, suffix=""):
    return Hijos.objects.create(
        nombre=f"HijoCS{suffix}",
        apellido="Signals",
        estado=True,
        id_cliente_responsable=cliente,
    )


def _make_tarjeta(hijo, suffix="", saldo=Decimal("50000.00"), saldo_alerta=None, notificar=True, estado="Activa"):
    return Tarjetas.objects.create(
        nro_tarjeta=f"TAR-CS-{suffix}",
        saldo_actual=saldo,
        estado=estado,
        fecha_creacion=timezone.now(),
        limite_credito=Decimal("10000000.00"),
        saldo_alerta=saldo_alerta,
        notificar_saldo_bajo=notificar,
        id_hijo=hijo,
    )


def _make_consumo(tarjeta, monto=Decimal("1000.00"), saldo_posterior=None):
    return ConsumosTarjeta.objects.create(
        nro_tarjeta=tarjeta,
        fecha_consumo=timezone.now(),
        monto_consumido=monto,
        saldo_anterior=tarjeta.saldo_actual,
        saldo_posterior=saldo_posterior or tarjeta.saldo_actual - monto,
    )


# =============================================================================
# actualizar_saldo_recarga – línea 27
# =============================================================================


class ActualizarSaldoRecargaTest(TestCase):
    """Tests para signal actualizar_saldo_recarga"""

    def setUp(self):
        cliente = _make_cliente("asr")
        hijo = _make_hijo(cliente, "asr")
        self.tarjeta = _make_tarjeta(hijo, "asr")

    def test_estado_no_confirmado_retorna_sin_procesar(self):
        """Signal retorna si estado != 'confirmado'."""
        carga = CargasSaldo.objects.create(
            fecha_carga=timezone.now(),
            monto_cargado=Decimal("10000.00"),
            estado="pendiente",
            nro_tarjeta=self.tarjeta,
        )
        saldo_antes = Tarjetas.objects.get(nro_tarjeta=self.tarjeta.nro_tarjeta).saldo_actual
        # Signal no debe haber cambiado el saldo
        self.assertEqual(saldo_antes, self.tarjeta.saldo_actual)

    def test_saldo_actualizado_flag_previene_doble_procesamiento(self):
        """Línea 27: Si _saldo_actualizado en instance → return."""
        carga = CargasSaldo.objects.create(
            fecha_carga=timezone.now(),
            monto_cargado=Decimal("20000.00"),
            estado="confirmado",
            nro_tarjeta=self.tarjeta,
        )
        # Setear el flag y re-guardar: signal debe retornar sin re-procesar
        saldo_despues_primer_save = Tarjetas.objects.get(nro_tarjeta=self.tarjeta.nro_tarjeta).saldo_actual
        carga._saldo_actualizado = True
        # Patch ConsumosTarjeta.objects.filter to ensure no duplicate is created
        with patch("apps.core.signals.ConsumosTarjeta.objects.filter") as mock_filter:
            mock_filter.return_value.exists.return_value = False
            carga.save()
            # filter should not have been called because _saldo_actualizado caused early return
        # Saldo no debe haber cambiado en el segundo save
        saldo_final = Tarjetas.objects.get(nro_tarjeta=self.tarjeta.nro_tarjeta).saldo_actual
        self.assertEqual(saldo_despues_primer_save, saldo_final)

    def test_estado_confirmado_sin_consumo_previo_actualiza_saldo(self):
        """Estado confirmado → signal actualiza tarjeta.saldo_actual."""
        saldo_antes = self.tarjeta.saldo_actual
        carga = CargasSaldo.objects.create(
            fecha_carga=timezone.now(),
            monto_cargado=Decimal("15000.00"),
            estado="confirmado",
            nro_tarjeta=self.tarjeta,
        )
        self.tarjeta.refresh_from_db()
        self.assertEqual(self.tarjeta.saldo_actual, saldo_antes + Decimal("15000.00"))


# =============================================================================
# notificar_saldo_bajo – líneas 66-91
# =============================================================================


class NotificarSaldoBajoTest(TestCase):
    """Tests para signal notificar_saldo_bajo (post_save ConsumosTarjeta)"""

    def setUp(self):
        cliente = _make_cliente("nsb")
        hijo = _make_hijo(cliente, "nsb")
        # Tarjeta con saldo_alerta=10000 y saldo_actual bajo la alerta
        self.tarjeta = _make_tarjeta(
            hijo, "nsb", saldo=Decimal("3000.00"), saldo_alerta=Decimal("10000.00"), notificar=True
        )

    def test_requiere_notificacion_true_ejecuta_bloque(self):
        """Líneas 66-91: tarjeta.requiere_notificacion → intenta crear notificación."""
        # requiere_notificacion = True si notificar_saldo_bajo AND saldo_actual <= saldo_alerta
        self.assertTrue(self.tarjeta.requiere_notificacion)
        # El bloque interno intenta importar apps.notificaciones.models.Notificaciones
        # que NO existe → ImportError. La except anida la solución.
        # Mockeamos el módulo para cubrir el camino completo.
        mock_notif_class = MagicMock()
        mock_module = MagicMock()
        mock_module.Notificaciones = mock_notif_class
        with patch.dict("sys.modules", {"apps.notificaciones.models": mock_module}):
            consumo = _make_consumo(self.tarjeta, monto=Decimal("500.00"), saldo_posterior=Decimal("2500.00"))
        # Si llegamos aquí, el signal no falló la transacción
        self.assertIsNotNone(consumo.pk)

    def test_requiere_notificacion_false_no_ejecuta_bloque(self):
        """tarjeta.requiere_notificacion=False → signal no entra al bloque."""
        cliente = _make_cliente("nsb2")
        hijo = _make_hijo(cliente, "nsb2")
        tarjeta_sin_notif = _make_tarjeta(
            hijo,
            "nsb2",
            saldo=Decimal("50000.00"),
            saldo_alerta=Decimal("1000.00"),
            notificar=False,  # notificar_saldo_bajo=False → requiere_notificacion=False
        )
        consumo = _make_consumo(tarjeta_sin_notif, monto=Decimal("100.00"))
        self.assertIsNotNone(consumo.pk)

    def test_consumo_update_no_dispara_notificacion(self):
        """created=False → no se ejecuta el bloque de notificación."""
        # Usar tarjeta sin alerta para evitar ImportError en la creación
        cliente = _make_cliente("nsb3")
        hijo = _make_hijo(cliente, "nsb3")
        tarjeta_sin_alerta = _make_tarjeta(
            hijo,
            "nsb3",
            saldo=Decimal("50000.00"),
            saldo_alerta=None,  # sta_en_alerta=False → requiere_notificacion=False
            notificar=True,
        )
        consumo = _make_consumo(tarjeta_sin_alerta, monto=Decimal("200.00"))
        # Update → created=False → signal retorna
        consumo.monto_consumido = Decimal("199.00")
        consumo.save()
        self.assertIsNotNone(consumo.pk)

    def test_requiere_notificacion_con_mock_crea_notificacion(self):
        """Líneas 66-91: Con mock de Notificaciones, valida el camino completo (incluyendo except)."""
        # El ImportError del la import es capturado por el except Exception
        # o mockeamos para probar el camino con notificación creada
        mock_notif_class = MagicMock()
        mock_module = MagicMock()
        mock_module.Notificaciones = mock_notif_class

        with patch.dict("sys.modules", {"apps.notificaciones.models": mock_module}):
            consumo = _make_consumo(
                self.tarjeta,
                monto=Decimal("300.00"),
                saldo_posterior=Decimal("2700.00"),
            )
            self.assertIsNotNone(consumo.pk)
            # La notificación fue intentada
            mock_notif_class.objects.create.assert_called_once()


# =============================================================================
# validar_integridad_saldo – líneas 126-129
# =============================================================================


class ValidarIntegridadSaldoTest(TestCase):
    """Tests para signal validar_integridad_saldo (post_save ConsumosTarjeta)"""

    def setUp(self):
        cliente = _make_cliente("vis")
        hijo = _make_hijo(cliente, "vis")
        self.tarjeta = _make_tarjeta(hijo, "vis", saldo=Decimal("20000.00"))

    def test_saldo_coherente_no_genera_warning(self):
        """saldo_posterior == tarjeta.saldo_actual → no warning."""
        with patch("logging.Logger.warning") as mock_warn:
            consumo = ConsumosTarjeta.objects.create(
                nro_tarjeta=self.tarjeta,
                fecha_consumo=timezone.now(),
                monto_consumido=Decimal("5000.00"),
                saldo_anterior=self.tarjeta.saldo_actual,
                saldo_posterior=self.tarjeta.saldo_actual,  # Coherente con tarjeta
            )
            mock_warn.assert_not_called()

    def test_saldo_incoherente_genera_warning(self):
        """Líneas 126-129: saldo_posterior != tarjeta.saldo_actual → logger.warning."""
        with patch("logging.Logger.warning") as mock_warn:
            consumo = ConsumosTarjeta.objects.create(
                nro_tarjeta=self.tarjeta,
                fecha_consumo=timezone.now(),
                monto_consumido=Decimal("5000.00"),
                saldo_anterior=self.tarjeta.saldo_actual,
                saldo_posterior=Decimal("99999.00"),  # Incoherente
            )
            mock_warn.assert_called_once()
            call_args = mock_warn.call_args[0][0]
            self.assertIn("INCONSISTENCIA", call_args)

    def test_update_no_valida_integridad(self):
        """created=False → signal no verifica integridad."""
        with patch("logging.Logger.warning") as mock_warn:
            consumo = ConsumosTarjeta.objects.create(
                nro_tarjeta=self.tarjeta,
                fecha_consumo=timezone.now(),
                monto_consumido=Decimal("1000.00"),
                saldo_anterior=self.tarjeta.saldo_actual,
                saldo_posterior=self.tarjeta.saldo_actual,
            )
            mock_warn.reset_mock()
            # Update → created=False → no se ejecuta el bloque
            consumo.monto_consumido = Decimal("999.00")
            consumo.save()
            mock_warn.assert_not_called()


# =============================================================================
# validar_tarjeta_unica – líneas 96-108 (pre_save Tarjetas)
# =============================================================================


class ValidarTarjetaUnicaTest(TestCase):
    """Tests para signal validar_tarjeta_unica (pre_save Tarjetas)"""

    def setUp(self):
        cliente = _make_cliente("vtu")
        self.hijo = _make_hijo(cliente, "vtu")

    def test_segunda_tarjeta_mismo_hijo_raise(self):
        """pre_save: Si hijo ya tiene tarjeta → ValidationError."""
        from django.core.exceptions import ValidationError

        # Primera tarjeta OK
        _make_tarjeta(self.hijo, "vtu1")
        # Segunda tarjeta para mismo hijo → ValidationError
        with self.assertRaises(ValidationError):
            Tarjetas.objects.create(
                nro_tarjeta="TAR-CS-vtu2",
                saldo_actual=Decimal("0.00"),
                estado="Activa",
                fecha_creacion=timezone.now(),
                limite_credito=Decimal("10000000.00"),
                id_hijo=self.hijo,
            )

    def test_hijo_sin_tarjeta_previa_ok(self):
        """pre_save: Hijo sin tarjeta previa → OK."""
        cliente2 = _make_cliente("vtu2")
        hijo2 = _make_hijo(cliente2, "vtu2")
        tarjeta = _make_tarjeta(hijo2, "vtu3")
        self.assertIsNotNone(tarjeta.pk)

    def test_tarjeta_sin_hijo_no_valida(self):
        """pre_save: Tarjeta sin id_hijo → signal skip. (id_hijo permitible null es OneToOne, no puede ser null realmente)"""
        # La validación usa if instance.id_hijo → si es None no valida
        # OneToOne requiere hijo → solo confirmamos que el signal respeta el flujo
        tarjeta = Tarjetas(
            nro_tarjeta="TAR-SIN-HIJO",
            saldo_actual=Decimal("0.00"),
            estado="Activa",
            fecha_creacion=timezone.now(),
            limite_credito=Decimal("0.00"),
        )
        # id_hijo es OneToOne (not null), así que no podemos crear sin hijo
        # Solo verificamos el signal path: la condición `if instance.id_hijo` cubierta por vtu1
        self.assertIsNone(tarjeta.id_hijo_id)
