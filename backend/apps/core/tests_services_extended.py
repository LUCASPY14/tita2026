"""
Extended tests for apps/core/services.py
Targeting missing lines: 66, 111-125, 201-221, 302-305, 614, 653-678
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone


class AutorizacionServiceSinRolTest(TestCase):
    """Cover line 66: empleado without id_rol raises ValidationError."""

    def test_empleado_sin_rol_raises(self):
        from apps.core.services import AutorizacionService

        empleado_mock = MagicMock(spec=[])  # No id_rol attribute
        with self.assertRaises(ValidationError):
            AutorizacionService.validar_operacion(
                empleado=empleado_mock,
                tipo_operacion="venta",
                monto=Decimal("100000"),
            )

    def test_empleado_con_id_rol_none_raises(self):
        from apps.core.services import AutorizacionService

        empleado_mock = MagicMock()
        empleado_mock.id_rol = None
        with self.assertRaises(ValidationError):
            AutorizacionService.validar_operacion(
                empleado=empleado_mock,
                tipo_operacion="venta",
                monto=Decimal("100000"),
            )


class AutorizacionServiceDobleAutorizacionTest(TestCase):
    """Cover lines 111-125: doble autorizacion logic."""

    def setUp(self):
        from apps.core.models import LimitesTransaccion
        from apps.usuarios.models import Empleados, Roles

        self.rol_cajero = Roles.objects.create(nombre_rol="Cajero", descripcion="Cajero")
        self.rol_gerente = Roles.objects.create(nombre_rol="Gerente", descripcion="Gerente")

        self.cajero = Empleados.objects.create(
            nombre="Juan",
            apellido="Cajero",
            usuario="cajero99",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            email="cajero99@test.com",
            estado=True,
            id_rol=self.rol_cajero,
        )
        self.gerente = Empleados.objects.create(
            nombre="Maria",
            apellido="Gerente",
            usuario="gerente99",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            email="gerente99@test.com",
            estado=True,
            id_rol=self.rol_gerente,
        )
        self.gerente2 = Empleados.objects.create(
            nombre="Ana",
            apellido="Gerente2",
            usuario="gerente98",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            email="gerente98@test.com",
            estado=True,
            id_rol=self.rol_gerente,
        )

        self.limite = LimitesTransaccion.objects.create(
            id_rol=self.rol_cajero,
            tipo_operacion="venta_doble",
            monto_maximo_sin_autorizacion=Decimal("1000.00"),
            requiere_autorizacion_doble=True,  # doble autorizacion required
            estado=True,
        )
        self.limite.roles_autorizadores.add(self.rol_gerente)

    def test_doble_autorizacion_sin_autorizador2_falla(self):
        """Line 113: doble_autorizacion required but no autorizador_2."""
        from apps.core.services import AutorizacionService

        result = AutorizacionService.validar_operacion(
            empleado=self.cajero,
            tipo_operacion="venta_doble",
            monto=Decimal("100000"),
            autorizador=self.gerente,
            motivo="Test",
        )
        self.assertFalse(result["puede_ejecutar"])
        self.assertTrue(any("dos supervisores" in e for e in result["errores"]))

    def test_doble_autorizacion_autorizador2_es_solicitante_falla(self):
        """Line 115: autorizador_2 == empleado."""
        from apps.core.services import AutorizacionService

        result = AutorizacionService.validar_operacion(
            empleado=self.cajero,
            tipo_operacion="venta_doble",
            monto=Decimal("100000"),
            autorizador=self.gerente,
            autorizador_2=self.cajero,  # Same as solicitante
            motivo="Test",
        )
        self.assertFalse(result["puede_ejecutar"])
        self.assertTrue(any("segundo autorizador" in e for e in result["errores"]))

    def test_doble_autorizacion_autorizadores_iguales_falla(self):
        """Line 117: autorizador_2 == autorizador."""
        from apps.core.services import AutorizacionService

        result = AutorizacionService.validar_operacion(
            empleado=self.cajero,
            tipo_operacion="venta_doble",
            monto=Decimal("100000"),
            autorizador=self.gerente,
            autorizador_2=self.gerente,  # Same as autorizador
            motivo="Test",
        )
        self.assertFalse(result["puede_ejecutar"])
        self.assertTrue(any("diferentes" in e for e in result["errores"]))

    def test_doble_autorizacion_valida_pasa(self):
        """Lines 119-125: valid doble_autorizacion passes."""
        from apps.core.services import AutorizacionService

        result = AutorizacionService.validar_operacion(
            empleado=self.cajero,
            tipo_operacion="venta_doble",
            monto=Decimal("100000"),
            autorizador=self.gerente,
            autorizador_2=self.gerente2,
            motivo="Test",
        )
        self.assertTrue(result["puede_ejecutar"])
        self.assertTrue(result["autorizado"])


class AutorizacionServiceHistorialTest(TestCase):
    """Cover lines 201-221: obtener_historial_autorizaciones with filters."""

    def setUp(self):
        from apps.core.models import RegistroAutorizaciones
        from apps.usuarios.models import Empleados, Roles

        self.rol = Roles.objects.create(nombre_rol="Admin_ext", descripcion="Admin")
        self.empleado = Empleados.objects.create(
            nombre="Test",
            apellido="Hist",
            usuario="hist99",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            email="hist99@test.com",
            estado=True,
            id_rol=self.rol,
        )
        self.autorizador = Empleados.objects.create(
            nombre="Auth",
            apellido="Hist",
            usuario="auth99",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            email="auth99@test.com",
            estado=True,
            id_rol=self.rol,
        )

        from apps.core.models import RegistroAutorizaciones

        RegistroAutorizaciones.objects.create(
            tipo_operacion="venta",
            monto=Decimal("100000"),
            motivo="Test",
            id_empleado_solicitante=self.empleado,
            id_empleado_autorizador=self.autorizador,
        )

    def test_historial_sin_filtros(self):
        """Lines 201-221: historial with no filters returns all."""
        from apps.core.services import AutorizacionService

        result = AutorizacionService.obtener_historial_autorizaciones()
        self.assertGreater(result.count(), 0)

    def test_historial_filtrado_por_empleado(self):
        """Filter by empleado covers the Q filter logic."""
        from apps.core.services import AutorizacionService

        result = AutorizacionService.obtener_historial_autorizaciones(empleado=self.empleado)
        self.assertGreater(result.count(), 0)

    def test_historial_filtrado_por_tipo_operacion(self):
        """Filter by tipo_operacion."""
        from apps.core.services import AutorizacionService

        result = AutorizacionService.obtener_historial_autorizaciones(tipo_operacion="venta")
        self.assertGreater(result.count(), 0)

    def test_historial_filtrado_por_fechas(self):
        """Filter by fecha_desde and fecha_hasta."""
        from datetime import timedelta

        from apps.core.services import AutorizacionService

        ahora = timezone.now()
        result = AutorizacionService.obtener_historial_autorizaciones(
            fecha_desde=ahora - timedelta(days=1),
            fecha_hasta=ahora + timedelta(days=1),
        )
        self.assertGreater(result.count(), 0)

    def test_historial_tipo_inexistente_retorna_vacio(self):
        """No results for non-matching tipo_operacion."""
        from apps.core.services import AutorizacionService

        result = AutorizacionService.obtener_historial_autorizaciones(tipo_operacion="tipo_inexistente")
        self.assertEqual(result.count(), 0)


class RecargaServiceGenCodigoExceptionTest(TestCase):
    """Cover lines 302-305: exception branch in generar_codigo_referencia."""

    @patch("apps.core.models.CargasSaldo.objects.filter")
    def test_referencia_invalida_usa_cero(self, mock_filter):
        """Lines 302-305: ValueError when parsing last reference number."""
        from apps.core.services import RecargaService

        ultimo_mock = MagicMock()
        ultimo_mock.referencia = "REF-20260101-abc"  # 'abc' raises ValueError in int()
        mock_filter.return_value.order_by.return_value.first.return_value = ultimo_mock

        codigo = RecargaService.generar_codigo_referencia()
        self.assertTrue(codigo.startswith("REF-"))
        # Should still generate a valid code despite the exception in parsing


class RecargaServiceValidarTransferenciaExtendedTest(TestCase):
    """Cover line 614 (monto alto with codigo), lines 653-678 (manual flow)."""

    def setUp(self):
        from apps.clientes.models import Clientes, Hijos
        from apps.core.models import Tarjetas
        from apps.usuarios.models import Empleados, Roles

        self.rol = Roles.objects.create(nombre_rol="Cajero_ext", descripcion="Cajero")
        self.empleado = Empleados.objects.create(
            nombre="Emp",
            apellido="Trans",
            usuario="emp_trans",
            contrasena_hash="hash",
            fecha_ingreso=timezone.now(),
            email="emp_trans@test.com",
            estado=True,
            id_rol=self.rol,
        )
        self.cliente = Clientes.objects.create(
            nombres="Cliente",
            apellidos="Trans",
            ruc_ci="12345678_trans",
            estado=True,
        )
        self.hijo = Hijos.objects.create(
            nombre="Hijo",
            apellido="Trans",
            id_cliente_responsable=self.cliente,
        )
        self.tarjeta = Tarjetas.objects.create(
            nro_tarjeta="TRTRANS001",
            id_hijo=self.hijo,
            saldo_actual=Decimal("0"),
            estado="Activa",
        )

    @patch("apps.core.services.RecargaService.validar_idempotencia", return_value=False)
    def test_manual_flow_monto_bajo_completa(self, mock_idem):
        """Lines 653-678: manual transfer (no codigo_referencia) with small amount."""
        from apps.core.services import RecargaService

        result = RecargaService.validar_transferencia(
            empleado_id=self.empleado.id_empleado,
            numero_comprobante="COMP001",
            hijo_id=self.hijo.id_hijo,
            monto=Decimal("100000"),  # Below threshold
        )
        self.assertTrue(result["success"])
        self.assertFalse(result["requiere_aprobacion"])

    @patch("apps.core.services.RecargaService.validar_idempotencia", return_value=False)
    def test_manual_flow_monto_alto_requiere_aprobacion(self, mock_idem):
        """Lines 653-678: manual transfer with amount above threshold requires approval."""
        from apps.core.services import RecargaService

        result = RecargaService.validar_transferencia(
            empleado_id=self.empleado.id_empleado,
            numero_comprobante="COMP002",
            hijo_id=self.hijo.id_hijo,
            monto=Decimal("1000000"),  # Above threshold (500000)
        )
        self.assertTrue(result["success"])
        self.assertTrue(result["requiere_aprobacion"])

    @patch("apps.core.services.RecargaService.validar_idempotencia", return_value=False)
    def test_manual_flow_sin_hijo_ni_monto_raises(self, mock_idem):
        """Manual flow without hijo_id or monto raises ValidationError."""
        from apps.core.services import RecargaService

        with self.assertRaises(ValidationError):
            RecargaService.validar_transferencia(
                empleado_id=self.empleado.id_empleado,
                numero_comprobante="COMP003",
                # No hijo_id, no monto
            )

    @patch("apps.core.services.RecargaService.validar_idempotencia", return_value=False)
    def test_codigo_referencia_monto_alto_requiere_aprobacion(self, mock_idem):
        """Line 614: transferencia with codigo and monto above threshold."""
        from apps.core.models import CargasSaldo
        from apps.core.services import RecargaService

        # Create a pending recarga
        recarga = CargasSaldo.objects.create(
            nro_tarjeta=self.tarjeta,
            fecha_carga=timezone.now(),
            monto_cargado=Decimal("600000"),  # Above threshold
            total_cobrado=Decimal("600000"),
            comision=Decimal("0"),
            metodo_pago="transferencia",
            estado="pendiente_validacion",
            referencia="REF-TEST-001",
            custom_identifier="REF-TEST-001",
        )

        result = RecargaService.validar_transferencia(
            empleado_id=self.empleado.id_empleado,
            numero_comprobante="COMP_ALTO",
            codigo_referencia="REF-TEST-001",
        )
        self.assertTrue(result["success"])
        self.assertTrue(result["requiere_aprobacion"])
