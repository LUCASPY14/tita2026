"""
Tests para apps/almuerzos/views.py
Cubre RegistrosConsumoAlmuerzoViewSet.perform_create() y _agregar_a_cuenta_mensual()
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from apps.almuerzos.models import (
    PlanesAlmuerzo,
    RegistrosConsumoAlmuerzo,
    SuscripcionesAlmuerzo,
    TiposAlmuerzo,
)
from apps.almuerzos.views import RegistrosConsumoAlmuerzoViewSet
from apps.clientes.models import Clientes, Hijos, TiposCliente
from apps.core.models import Tarjetas
from apps.productos.models import ListasPrecios
from apps.usuarios.models import Empleados, Roles


def _make_viewset():
    """Helper to create a viewset instance"""
    return RegistrosConsumoAlmuerzoViewSet()


class AlmuerzosViewSetPerformCreateSinTarjetaTest(TestCase):
    """perform_create debe fallar si no se provee nro_tarjeta"""

    def test_sin_tarjeta_lanza_validation_error(self):
        vs = _make_viewset()
        serializer = MagicMock()
        serializer.validated_data = {
            "id_hijo": MagicMock(),
            "fecha_consumo": date.today(),
            "nro_tarjeta": None,
            "id_tipo_almuerzo": MagicMock(),
            "id_suscripcion": None,
        }
        with self.assertRaises(ValidationError):
            vs.perform_create(serializer)


class AlmuerzosViewSetCreateBaseFixture(TestCase):
    """Base fixture for perform_create tests that require real data"""

    def setUp(self):
        lista = ListasPrecios.objects.create(nombre_lista="Minorista", estado=True)
        tipo_c = TiposCliente.objects.create(nombre_tipo="Regular", estado=True)
        self.cliente = Clientes.objects.create(
            nombres="Rosa",
            apellidos="Test",
            ruc_ci="12345678",
            limite_credito=Decimal("100.00"),
            estado=True,
            id_lista=lista,
            id_tipo_cliente=tipo_c,
        )
        self.hijo = Hijos.objects.create(
            nombre="Luisa",
            apellido="Test",
            grado="3ro",
            estado=True,
            id_cliente_responsable=self.cliente,
        )
        self.tarjeta = Tarjetas.objects.create(
            nro_tarjeta="ALM001",
            saldo_actual=Decimal("500.00"),
            estado="activa",
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal("0.00"),
            notificar_saldo_bajo=True,
            id_hijo=self.hijo,
            codigo_barras="BARM001",
        )
        self.plan = PlanesAlmuerzo.objects.create(
            nombre_plan="Plan Prueba",
            descripcion="Plan test",
            precio_mensual=Decimal("120.00"),
            dias_semana_incluidos="Lunes,Martes",
            fecha_creacion=timezone.now(),
            estado=True,
        )
        self.tipo_almuerzo = TiposAlmuerzo.objects.create(
            nombre="Almuerzo Std",
            descripcion="desc",
            precio_unitario=Decimal("10.00"),
            incluye_plato_principal=True,
            incluye_postre=False,
            incluye_bebida=False,
            fecha_creacion=timezone.now(),
            estado=True,
        )
        rol = Roles.objects.create(nombre_rol="CocinaX", estado=True)
        self.empleado = Empleados.objects.create(
            nombre="Emp",
            apellido="Test",
            usuario="emptest",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            estado=True,
            id_rol=rol,
        )


class AlmuerzosViewSetSinSuscripcionYSinTipoTest(AlmuerzosViewSetCreateBaseFixture):
    """Sin suscripción y sin tipo → ValidationError"""

    def test_sin_tipo_y_sin_suscripcion_lanza_error(self):
        vs = _make_viewset()
        serializer = MagicMock()
        serializer.validated_data = {
            "id_hijo": self.hijo,
            "fecha_consumo": date.today(),
            "nro_tarjeta": self.tarjeta,
            "id_tipo_almuerzo": None,
            "id_suscripcion": None,
        }
        with patch("apps.almuerzos.validators.validar_limite_registros_diarios", return_value=None):
            with patch("apps.almuerzos.validators.determinar_si_cobra", return_value=True):
                with self.assertRaises(ValidationError):
                    vs.perform_create(serializer)


class AlmuerzosViewSetSuscripcionNoActivaTest(AlmuerzosViewSetCreateBaseFixture):
    """Suscripción inactiva → ValidationError"""

    def test_suscripcion_no_activa_lanza_error(self):
        suscripcion = SuscripcionesAlmuerzo.objects.create(
            fecha_inicio=date.today(),
            fecha_fin=None,
            estado="inactiva",
            id_hijo=self.hijo,
            id_plan_almuerzo=self.plan,
        )
        vs = _make_viewset()
        serializer = MagicMock()
        serializer.validated_data = {
            "id_hijo": self.hijo,
            "fecha_consumo": date.today(),
            "nro_tarjeta": self.tarjeta,
            "id_tipo_almuerzo": None,
            "id_suscripcion": suscripcion,
        }
        with patch("apps.almuerzos.validators.validar_limite_registros_diarios", return_value=None):
            with patch("apps.almuerzos.validators.determinar_si_cobra", return_value=True):
                with self.assertRaises(ValidationError):
                    vs.perform_create(serializer)


class AlmuerzosViewSetSaldoInsuficienteTest(AlmuerzosViewSetCreateBaseFixture):
    """Tarjeta con saldo bajo → el registro igual se crea (tarjeta es sólo identificación,
    no se descuenta saldo según la regla de negocio actual)"""

    def test_saldo_insuficiente_no_lanza_error(self):
        """El saldo de la tarjeta no se descuenta, por lo que saldo bajo no bloquea el registro"""
        self.tarjeta.saldo_actual = Decimal("1.00")
        self.tarjeta.save()

        vs = _make_viewset()

        def mock_save(**kwargs):
            return RegistrosConsumoAlmuerzo.objects.create(
                fecha_consumo=date.today(),
                hora_registro=timezone.now().time(),
                costo_almuerzo=kwargs.get("costo_almuerzo", Decimal("10.00")),
                marcado_en_cuenta=False,
                ya_cobrado=kwargs.get("ya_cobrado", True),
                estado="Confirmado",
                id_hijo=self.hijo,
                id_tipo_almuerzo=self.tipo_almuerzo,
                nro_tarjeta=self.tarjeta,
                id_empleado_registro=self.empleado,
            )

        serializer = MagicMock()
        serializer.validated_data = {
            "id_hijo": self.hijo,
            "fecha_consumo": date.today(),
            "nro_tarjeta": self.tarjeta,
            "id_tipo_almuerzo": self.tipo_almuerzo,
            "id_suscripcion": None,
        }
        serializer.save.side_effect = mock_save
        with patch("apps.almuerzos.validators.validar_limite_registros_diarios", return_value=None):
            # Should not raise — saldo is not checked per current business rule
            vs.perform_create(serializer)

        self.tarjeta.refresh_from_db()
        # Saldo unchanged: tarjeta is only used for identification
        self.assertEqual(self.tarjeta.saldo_actual, Decimal("1.00"))


class AlmuerzosViewSetConTipoAlmuerzoCobraTest(AlmuerzosViewSetCreateBaseFixture):
    """Con tipo de almuerzo y saldo suficiente → exitoso"""

    def test_registro_con_tipo_almuerzo_cobra(self):
        vs = _make_viewset()

        def mock_save(**kwargs):
            return RegistrosConsumoAlmuerzo.objects.create(
                fecha_consumo=date.today(),
                hora_registro=timezone.now().time(),
                costo_almuerzo=Decimal("10.00"),
                marcado_en_cuenta=False,
                ya_cobrado=True,
                estado="Confirmado",
                id_hijo=self.hijo,
                id_tipo_almuerzo=self.tipo_almuerzo,
                nro_tarjeta=self.tarjeta,
                id_empleado_registro=self.empleado,
            )

        serializer = MagicMock()
        serializer.validated_data = {
            "id_hijo": self.hijo,
            "fecha_consumo": date.today(),
            "nro_tarjeta": self.tarjeta,
            "id_tipo_almuerzo": self.tipo_almuerzo,
            "id_suscripcion": None,
        }
        serializer.save.side_effect = mock_save

        with patch("apps.almuerzos.validators.validar_limite_registros_diarios", return_value=None):
            with patch("apps.almuerzos.validators.determinar_si_cobra", return_value=True):
                vs.perform_create(serializer)

        self.tarjeta.refresh_from_db()
        # Saldo unchanged: tarjeta is only used for identification, not debited
        self.assertEqual(self.tarjeta.saldo_actual, Decimal("500.00"))


class AlmuerzosViewSetSegundoRegistroNoCobra(AlmuerzosViewSetCreateBaseFixture):
    """Segundo registro del día → no cobrar"""

    def test_segundo_registro_no_cobra(self):
        vs = _make_viewset()

        def mock_save(**kwargs):
            r = RegistrosConsumoAlmuerzo.objects.create(
                fecha_consumo=date.today(),
                hora_registro=timezone.now().time(),
                costo_almuerzo=Decimal("0.00"),
                marcado_en_cuenta=False,
                ya_cobrado=False,
                estado="Confirmado",
                id_hijo=self.hijo,
                id_tipo_almuerzo=self.tipo_almuerzo,
                nro_tarjeta=self.tarjeta,
                id_empleado_registro=self.empleado,
            )
            r.save()
            return r

        serializer = MagicMock()
        serializer.validated_data = {
            "id_hijo": self.hijo,
            "fecha_consumo": date.today(),
            "nro_tarjeta": self.tarjeta,
            "id_tipo_almuerzo": self.tipo_almuerzo,
            "id_suscripcion": None,
        }
        serializer.save.side_effect = mock_save

        with patch("apps.almuerzos.validators.validar_limite_registros_diarios", return_value=None):
            with patch("apps.almuerzos.validators.determinar_si_cobra", return_value=False):
                vs.perform_create(serializer)

        self.tarjeta.refresh_from_db()
        self.assertEqual(self.tarjeta.saldo_actual, Decimal("500.00"))
