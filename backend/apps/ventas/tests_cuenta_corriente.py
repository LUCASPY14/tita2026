"""
Tests para Cuenta Corriente de Clientes y Proveedores
Valida reglas de negocio de crédito, pagos y notas de crédito
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from apps.clientes.models import Clientes, TiposCliente
from apps.ventas.models import Ventas, AplicacionPagosVentas, PagosVenta, NotasCreditoCliente
from apps.compras.models import (
    Proveedores,
    Compras,
    AplicacionPagosCompras,
    PagosProveedores,
    NotasCreditoProveedor,
)
from apps.core.models import MediosPago
from apps.usuarios.models import Empleados, Roles
from apps.productos.models import ListasPrecios


class CuentaCorrienteClienteTest(TestCase):
    """Tests para cuenta corriente de clientes"""

    def setUp(self):
        """Configurar datos de prueba"""
        # Tipo de cliente
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Mayorista", estado=True)

        # Lista de precios
        self.lista_precios = ListasPrecios.objects.create(nombre_lista="Mayorista")

        # Cliente con límite de crédito
        self.cliente = Clientes.objects.create(
            nombres="Juan",
            apellidos="Pérez",
            ruc_ci="1234567",
            limite_credito=Decimal("500000.00"),
            estado=True,
            id_tipo_cliente=self.tipo_cliente,
            id_lista=self.lista_precios,
        )

        # Rol para empleado
        self.rol = Roles.objects.create(nombre_rol="Cajero", descripcion="Cajero de ventas", estado=True)

        # Empleado cajero
        self.empleado = Empleados.objects.create(
            nombre="María",
            apellido="González",
            usuario="mgonzalez",
            contrasena_hash="hash123",
            fecha_ingreso=timezone.now(),
            id_rol=self.rol,
        )

        # Medio de pago
        self.medio_pago, _ = MediosPago.objects.get_or_create(
            descripcion="Efectivo",
            defaults={"genera_comision": False, "requiere_validacion": False, "estado": True},
        )

    def test_cliente_sin_credito_usado(self):
        """Cliente nuevo no debe tener crédito utilizado"""
        self.assertEqual(self.cliente.credito_utilizado, Decimal("0.00"))
        self.assertEqual(self.cliente.credito_disponible, Decimal("500000.00"))
        self.assertTrue(self.cliente.tiene_credito_disponible)
        self.assertEqual(self.cliente.porcentaje_credito_usado, Decimal("0.00"))

    def test_calculo_credito_utilizado(self):
        """Calcular crédito utilizado con ventas pendientes"""
        # Crear venta a crédito
        Ventas.objects.create(
            monto_total=Decimal("100000.00"),
            saldo_pendiente=Decimal("100000.00"),
            estado_pago="Pendiente",
            estado="Activa",
            tipo_venta="Crédito",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            genera_factura_legal=True,
        )

        # Refrescar cliente
        self.cliente.refresh_from_db()

        # Verificar cálculos
        self.assertEqual(self.cliente.credito_utilizado, Decimal("100000.00"))
        self.assertEqual(self.cliente.credito_disponible, Decimal("400000.00"))
        self.assertEqual(self.cliente.porcentaje_credito_usado, Decimal("20.00"))

    def test_limite_credito_excedido(self):
        """No permitir ventas que excedan el límite de crédito"""
        # Usar 450,000 del crédito
        Ventas.objects.create(
            monto_total=Decimal("450000.00"),
            saldo_pendiente=Decimal("450000.00"),
            estado_pago="Pendiente",
            estado="Activa",
            tipo_venta="Crédito",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
        )

        # Refrescar
        self.cliente.refresh_from_db()

        # Crédito disponible debe ser 50,000
        self.assertEqual(self.cliente.credito_disponible, Decimal("50000.00"))

        # Intentar venta de 100,000 debe fallar (excede el disponible)
        # Esto se valida en el ViewSet con ValidationError

    def test_actualizacion_saldo_con_pago(self):
        """Signal debe actualizar saldo_pendiente al registrar pago"""
        # Crear venta a crédito
        venta = Ventas.objects.create(
            monto_total=Decimal("200000.00"),
            saldo_pendiente=Decimal("200000.00"),
            estado_pago="Pendiente",
            estado="Activa",
            tipo_venta="Crédito",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
        )

        # Registrar pago
        pago = PagosVenta.objects.create(
            monto=Decimal("80000.00"),
            fecha_pago=timezone.now(),
            estado="confirmado",
            id_medio_pago=self.medio_pago,
            id_venta=venta,
        )

        # Aplicar pago a venta
        AplicacionPagosVentas.objects.create(monto_aplicado=Decimal("80000.00"), id_pago_venta=pago, id_venta=venta)

        # Refrescar venta
        venta.refresh_from_db()

        # Verificar actualización automática por signal
        self.assertEqual(venta.saldo_pendiente, Decimal("120000.00"))
        self.assertEqual(venta.estado_pago, "Parcial")

    def test_pago_completo_actualiza_estado(self):
        """Pago completo debe cambiar estado a 'Pagada'"""
        venta = Ventas.objects.create(
            monto_total=Decimal("100000.00"),
            saldo_pendiente=Decimal("100000.00"),
            estado_pago="Pendiente",
            estado="Activa",
            tipo_venta="Crédito",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
        )

        pago = PagosVenta.objects.create(
            monto=Decimal("100000.00"),
            fecha_pago=timezone.now(),
            estado="confirmado",
            id_medio_pago=self.medio_pago,
            id_venta=venta,
        )

        AplicacionPagosVentas.objects.create(monto_aplicado=Decimal("100000.00"), id_pago_venta=pago, id_venta=venta)

        venta.refresh_from_db()

        self.assertEqual(venta.saldo_pendiente, Decimal("0.00"))
        self.assertEqual(venta.estado_pago, "Pagada")

    def test_nota_credito_reduce_saldo(self):
        """Nota de crédito aplicada debe reducir saldo pendiente"""
        venta = Ventas.objects.create(
            monto_total=Decimal("150000.00"),
            saldo_pendiente=Decimal("150000.00"),
            estado_pago="Pendiente",
            estado="Activa",
            tipo_venta="Crédito",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
        )

        # Crear y aplicar nota de crédito
        nota = NotasCreditoCliente.objects.create(
            nro_nota_credito=1001,
            fecha_emision=timezone.now(),
            motivo="Devolución de productos",
            monto_total=Decimal("50000.00"),
            estado="Aplicada",
            id_cliente=self.cliente,
            id_empleado_autoriza=self.empleado,
            id_venta_origen=venta,
        )

        venta.refresh_from_db()

        # Saldo debe reducirse
        self.assertEqual(venta.saldo_pendiente, Decimal("100000.00"))
        self.assertEqual(venta.estado_pago, "Parcial")

    def test_cuenta_corriente_completa(self):
        """Propiedad cuenta_corriente debe calcular correctamente"""
        # Crear 2 ventas pendientes
        Ventas.objects.create(
            monto_total=Decimal("100000.00"),
            saldo_pendiente=Decimal("60000.00"),
            estado_pago="Parcial",
            estado="Activa",
            tipo_venta="Crédito",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
        )

        Ventas.objects.create(
            monto_total=Decimal("80000.00"),
            saldo_pendiente=Decimal("80000.00"),
            estado_pago="Pendiente",
            estado="Activa",
            tipo_venta="Crédito",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
        )

        # Nota de crédito sin aplicar
        NotasCreditoCliente.objects.create(
            nro_nota_credito=1002,
            fecha_emision=timezone.now(),
            motivo="Bonificación",
            monto_total=Decimal("20000.00"),
            estado="Emitida",
            id_cliente=self.cliente,
            id_empleado_autoriza=self.empleado,
        )

        cuenta = self.cliente.cuenta_corriente

        self.assertEqual(cuenta["total_debe"], Decimal("140000.00"))
        self.assertEqual(cuenta["total_haber"], Decimal("20000.00"))
        self.assertEqual(cuenta["saldo_neto"], Decimal("120000.00"))
        self.assertEqual(cuenta["cantidad_facturas_pendientes"], 2)
        self.assertEqual(cuenta["cantidad_notas_credito"], 1)


class CuentaCorrienteProveedorTest(TestCase):
    """Tests para cuenta corriente de proveedores"""

    def setUp(self):
        """Configurar datos de prueba"""
        self.proveedor = Proveedores.objects.create(
            ruc="80012345",
            razon_social="Distribuidora ABC S.A.",
            estado=True,
            fecha_registro=timezone.now(),
        )

        self.medio_pago, _ = MediosPago.objects.get_or_create(
            descripcion="Transferencia Bancaria",
            defaults={"genera_comision": False, "requiere_validacion": False, "estado": True},
        )

    def test_actualizacion_saldo_compra_con_pago(self):
        """Signal debe actualizar saldo de compra al pagar"""
        compra = Compras.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal("300000.00"),
            saldo_pendiente=Decimal("300000.00"),
            estado_pago="Pendiente",
            nro_factura="001-002-0001234",
            id_proveedor=self.proveedor,
        )

        # Registrar pago parcial
        pago = PagosProveedores.objects.create(fecha_creacion=timezone.now(), id_medio_pago=self.medio_pago)

        AplicacionPagosCompras.objects.create(
            monto_aplicado=Decimal("150000.00"), id_compra=compra, id_pago_proveedor=pago
        )

        compra.refresh_from_db()

        self.assertEqual(compra.saldo_pendiente, Decimal("150000.00"))
        self.assertEqual(compra.estado_pago, "Parcial")

    def test_pago_multiple_facturas(self):
        """Un pago puede aplicarse a múltiples facturas"""
        # Crear 3 facturas
        compra1 = Compras.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal("100000.00"),
            saldo_pendiente=Decimal("100000.00"),
            estado_pago="Pendiente",
            id_proveedor=self.proveedor,
        )

        compra2 = Compras.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal("150000.00"),
            saldo_pendiente=Decimal("150000.00"),
            estado_pago="Pendiente",
            id_proveedor=self.proveedor,
        )

        compra3 = Compras.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal("200000.00"),
            saldo_pendiente=Decimal("200000.00"),
            estado_pago="Pendiente",
            id_proveedor=self.proveedor,
        )

        # Pago de 350,000 distribuido
        pago = PagosProveedores.objects.create(fecha_creacion=timezone.now(), id_medio_pago=self.medio_pago)

        AplicacionPagosCompras.objects.create(
            monto_aplicado=Decimal("100000.00"), id_compra=compra1, id_pago_proveedor=pago
        )

        AplicacionPagosCompras.objects.create(
            monto_aplicado=Decimal("150000.00"), id_compra=compra2, id_pago_proveedor=pago
        )

        AplicacionPagosCompras.objects.create(
            monto_aplicado=Decimal("100000.00"), id_compra=compra3, id_pago_proveedor=pago
        )

        # Refrescar
        compra1.refresh_from_db()
        compra2.refresh_from_db()
        compra3.refresh_from_db()

        # Verificar
        self.assertEqual(compra1.saldo_pendiente, Decimal("0.00"))
        self.assertEqual(compra1.estado_pago, "Pagada")

        self.assertEqual(compra2.saldo_pendiente, Decimal("0.00"))
        self.assertEqual(compra2.estado_pago, "Pagada")

        self.assertEqual(compra3.saldo_pendiente, Decimal("100000.00"))
        self.assertEqual(compra3.estado_pago, "Parcial")

    def test_nota_credito_proveedor(self):
        """Nota de crédito de proveedor reduce saldo de compra"""
        compra = Compras.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal("500000.00"),
            saldo_pendiente=Decimal("500000.00"),
            estado_pago="Pendiente",
            id_proveedor=self.proveedor,
        )

        # Nota de crédito por devolución
        NotasCreditoProveedor.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal("100000.00"),
            estado="Aplicada",
            fecha_creacion=timezone.now(),
            id_proveedor=self.proveedor,
            id_compra_original=compra,
        )

        compra.refresh_from_db()

        self.assertEqual(compra.saldo_pendiente, Decimal("400000.00"))
        self.assertEqual(compra.estado_pago, "Parcial")
