"""
Tests para FacturacionService (facturacion_service.py)

Cubre:
  - get_cola(): sin ventas, con ventas elegibles, excluye ya facturadas
  - emitir(): sin timbrado, nro fuera de rango, nro duplicado, emisión exitosa
  - anular(): desvincula ventas y marca como Factura-Anulada
"""
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.contabilidad.facturacion_service import FacturacionService
from apps.contabilidad.models import DocumentosTributarios, PuntosExpedicion, Timbrados
from apps.clientes.models import Clientes, TiposCliente
from apps.productos.models import ListasPrecios
from apps.usuarios.models import Empleados, Roles
from apps.ventas.models import Ventas


# ─── setUp compartido ─────────────────────────────────────────────────────────

class FacturacionServiceBaseTest(TestCase):
    """Configura los datos base reutilizados por todos los tests."""

    def setUp(self):
        hoy = date.today()

        # Punto de expedición
        self.punto = PuntosExpedicion.objects.create(
            codigo_establecimiento="001",
            codigo_punto_expedicion="001",
            descripcion_ubicacion="Principal",
            estado=True,
        )

        # Timbrado vigente
        self.timbrado = Timbrados.objects.create(
            nro_timbrado=12345678,
            tipo_documento="Factura",
            fecha_inicio=hoy - timedelta(days=30),
            fecha_fin=hoy + timedelta(days=335),
            nro_inicial=1,
            nro_final=999,
            estado=True,
            id_punto=self.punto,
        )

        # Cliente
        lista = ListasPrecios.objects.create(nombre_lista="Minorista", estado=True)
        tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular", estado=True)
        self.cliente = Clientes.objects.create(
            nombres="Juan",
            apellidos="Pérez",
            ruc_ci="1234567",
            limite_credito=Decimal("0.00"),
            estado=True,
            id_lista=lista,
            id_tipo_cliente=tipo_cliente,
        )

        # Empleado cajero (requerido por Ventas)
        rol = Roles.objects.create(nombre_rol="Cajero", estado=True)
        self.cajero = Empleados.objects.create(
            nombre="Ana",
            apellido="García",
            usuario="cajero1",
            contrasena_hash="x",
            fecha_ingreso=timezone.now(),
            estado=True,
            id_rol=rol,
        )


# ─── get_cola() ──────────────────────────────────────────────────────────────

class GetColaVaciaTest(FacturacionServiceBaseTest):
    """get_cola retorna lista vacía cuando no hay ventas elegibles."""

    def test_sin_ventas_retorna_lista_vacia(self):
        cola = FacturacionService.get_cola()
        self.assertEqual(cola, [])

    def test_venta_sin_factura_legal_no_aparece(self):
        """Ventas con genera_factura_legal=False no deben aparecer en la cola."""
        Ventas.objects.create(
            monto_total=Decimal("50000.00"),
            saldo_pendiente=Decimal("0.00"),
            estado_pago="pagada",
            estado="Activa",
            tipo_venta="contado",
            genera_factura_legal=False,
            id_cliente=self.cliente,
            id_empleado_cajero=self.cajero,
        )
        cola = FacturacionService.get_cola()
        self.assertEqual(cola, [])

    def test_venta_ya_facturada_no_aparece(self):
        """Ventas con id_documento ya asignado no deben aparecer."""
        doc = DocumentosTributarios.objects.create(
            nro_secuencial=1,
            fecha_emision=timezone.now(),
            monto_total=Decimal("50000.00"),
            nro_timbrado=self.timbrado,
            tipo_documento="Factura",
            nro_preimpreso_interno="001-001-0000001",
            id_cliente=self.cliente,
        )
        Ventas.objects.create(
            monto_total=Decimal("50000.00"),
            saldo_pendiente=Decimal("0.00"),
            estado_pago="pagada",
            estado="Activa",
            tipo_venta="contado",
            genera_factura_legal=True,
            id_cliente=self.cliente,
            id_empleado_cajero=self.cajero,
            id_documento=doc,
        )
        cola = FacturacionService.get_cola()
        self.assertEqual(cola, [])

    def test_venta_pendiente_pago_no_aparece(self):
        """Ventas no pagadas no deben aparecer en la cola."""
        Ventas.objects.create(
            monto_total=Decimal("50000.00"),
            saldo_pendiente=Decimal("50000.00"),
            estado_pago="pendiente",
            estado="Activa",
            tipo_venta="credito",
            genera_factura_legal=True,
            id_cliente=self.cliente,
            id_empleado_cajero=self.cajero,
        )
        cola = FacturacionService.get_cola()
        self.assertEqual(cola, [])


class GetColaConVentasTest(FacturacionServiceBaseTest):
    """get_cola retorna datos cuando hay ventas elegibles."""

    def test_venta_elegible_aparece_en_cola(self):
        venta = Ventas.objects.create(
            monto_total=Decimal("75000.00"),
            saldo_pendiente=Decimal("0.00"),
            estado_pago="pagada",
            estado="Activa",
            tipo_venta="contado",
            genera_factura_legal=True,
            id_cliente=self.cliente,
            id_empleado_cajero=self.cajero,
        )
        cola = FacturacionService.get_cola()

        self.assertEqual(len(cola), 1)
        entrada = cola[0]
        self.assertEqual(entrada["id_cliente"], self.cliente.id_cliente)
        self.assertEqual(len(entrada["ventas"]), 1)
        self.assertEqual(cola[0]["ventas"][0]["id"], venta.id_venta)

    def test_total_pendiente_acumula_ventas_del_mismo_cliente(self):
        Ventas.objects.create(
            monto_total=Decimal("30000.00"),
            saldo_pendiente=Decimal("0.00"),
            estado_pago="pagada",
            estado="Activa",
            tipo_venta="contado",
            genera_factura_legal=True,
            id_cliente=self.cliente,
            id_empleado_cajero=self.cajero,
        )
        Ventas.objects.create(
            monto_total=Decimal("20000.00"),
            saldo_pendiente=Decimal("0.00"),
            estado_pago="pagada",
            estado="Activa",
            tipo_venta="contado",
            genera_factura_legal=True,
            id_cliente=self.cliente,
            id_empleado_cajero=self.cajero,
        )
        cola = FacturacionService.get_cola()
        self.assertEqual(len(cola), 1)
        self.assertEqual(len(cola[0]["ventas"]), 2)
        self.assertAlmostEqual(cola[0]["total_pendiente"], 50000.0)

    def test_ventas_de_dos_clientes_producen_dos_entradas(self):
        lista2 = ListasPrecios.objects.create(nombre_lista="Mayorista", estado=True)
        tipo2 = TiposCliente.objects.create(nombre_tipo="Empresa", estado=True)
        cliente2 = Clientes.objects.create(
            nombres="Carlos",
            apellidos="Ramírez",
            ruc_ci="9999999",
            limite_credito=Decimal("0.00"),
            estado=True,
            id_lista=lista2,
            id_tipo_cliente=tipo2,
        )
        for cliente in [self.cliente, cliente2]:
            Ventas.objects.create(
                monto_total=Decimal("10000.00"),
                saldo_pendiente=Decimal("0.00"),
                estado_pago="pagada",
                estado="Activa",
                tipo_venta="contado",
                genera_factura_legal=True,
                id_cliente=cliente,
                id_empleado_cajero=self.cajero,
            )
        cola = FacturacionService.get_cola()
        self.assertEqual(len(cola), 2)


# ─── emitir() ────────────────────────────────────────────────────────────────

class EmitirSinTimbradoTest(FacturacionServiceBaseTest):
    """emitir() falla cuando no hay timbrado vigente."""

    def test_sin_timbrado_activo_lanza_value_error(self):
        self.timbrado.estado = False
        self.timbrado.save()
        with self.assertRaises(ValueError) as ctx:
            FacturacionService.emitir(
                id_cliente=self.cliente.id_cliente,
                nro_preimpreso=1,
                ventas_ids=[],
                almuerzos_ids=[],
            )
        self.assertIn("No hay timbrado vigente", str(ctx.exception))

    def test_timbrado_vencido_lanza_value_error(self):
        self.timbrado.fecha_fin = date.today() - timedelta(days=1)
        self.timbrado.save()
        with self.assertRaises(ValueError):
            FacturacionService.emitir(
                id_cliente=self.cliente.id_cliente,
                nro_preimpreso=1,
                ventas_ids=[],
                almuerzos_ids=[],
            )


class EmitirValidacionesTest(FacturacionServiceBaseTest):
    """emitir() valida el rango y duplicados de nro_preimpreso."""

    def test_nro_fuera_de_rango_lanza_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            FacturacionService.emitir(
                id_cliente=self.cliente.id_cliente,
                nro_preimpreso=9999,          # fuera del rango 1-999
                ventas_ids=[],
                almuerzos_ids=[],
            )
        self.assertIn("fuera del rango", str(ctx.exception))

    def test_nro_duplicado_lanza_value_error(self):
        # Emitir la primera vez
        FacturacionService.emitir(
            id_cliente=self.cliente.id_cliente,
            nro_preimpreso=100,
            ventas_ids=[],
            almuerzos_ids=[],
        )
        # Intentar emitir de nuevo con el mismo número
        with self.assertRaises(ValueError) as ctx:
            FacturacionService.emitir(
                id_cliente=self.cliente.id_cliente,
                nro_preimpreso=100,
                ventas_ids=[],
                almuerzos_ids=[],
            )
        self.assertIn("ya fue emitido", str(ctx.exception))


class EmitirExitosoTest(FacturacionServiceBaseTest):
    """emitir() crea el documento y vincula ventas correctamente."""

    def setUp(self):
        super().setUp()
        self.venta = Ventas.objects.create(
            monto_total=Decimal("150000.00"),
            saldo_pendiente=Decimal("0.00"),
            estado_pago="pagada",
            estado="Activa",
            tipo_venta="contado",
            genera_factura_legal=True,
            id_cliente=self.cliente,
            id_empleado_cajero=self.cajero,
        )

    def test_crea_documento_tributario(self):
        doc = FacturacionService.emitir(
            id_cliente=self.cliente.id_cliente,
            nro_preimpreso=50,
            ventas_ids=[self.venta.id_venta],
            almuerzos_ids=[],
        )
        self.assertIsNotNone(doc.id_documento)
        self.assertEqual(doc.nro_secuencial, 50)
        self.assertEqual(doc.monto_total, Decimal("150000.00"))

    def test_nro_preimpreso_interno_formateado(self):
        doc = FacturacionService.emitir(
            id_cliente=self.cliente.id_cliente,
            nro_preimpreso=50,
            ventas_ids=[self.venta.id_venta],
            almuerzos_ids=[],
        )
        # Formato esperado: "001-001-0000050"
        self.assertEqual(doc.nro_preimpreso_interno, "001-001-0000050")

    def test_venta_queda_vinculada_al_documento(self):
        doc = FacturacionService.emitir(
            id_cliente=self.cliente.id_cliente,
            nro_preimpreso=50,
            ventas_ids=[self.venta.id_venta],
            almuerzos_ids=[],
        )
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.id_documento_id, doc.id_documento)

    def test_condicion_venta_credito(self):
        doc = FacturacionService.emitir(
            id_cliente=self.cliente.id_cliente,
            nro_preimpreso=51,
            ventas_ids=[self.venta.id_venta],
            almuerzos_ids=[],
            condicion_venta="CREDITO",
            plazo_dias=30,
        )
        self.assertEqual(doc.condicion_venta, "CREDITO")
        self.assertEqual(doc.plazo_dias, 30)

    def test_emision_sin_ventas_monto_cero(self):
        """Emitir sin ventas ni almuerzos produce monto_total = 0."""
        doc = FacturacionService.emitir(
            id_cliente=self.cliente.id_cliente,
            nro_preimpreso=200,
            ventas_ids=[],
            almuerzos_ids=[],
        )
        self.assertEqual(doc.monto_total, Decimal("0"))


# ─── anular() ────────────────────────────────────────────────────────────────

class AnularTest(FacturacionServiceBaseTest):
    """anular() desvincula ventas y marca el documento como Factura-Anulada."""

    def setUp(self):
        super().setUp()
        self.venta = Ventas.objects.create(
            monto_total=Decimal("80000.00"),
            saldo_pendiente=Decimal("0.00"),
            estado_pago="pagada",
            estado="Activa",
            tipo_venta="contado",
            genera_factura_legal=True,
            id_cliente=self.cliente,
            id_empleado_cajero=self.cajero,
        )
        self.doc = FacturacionService.emitir(
            id_cliente=self.cliente.id_cliente,
            nro_preimpreso=77,
            ventas_ids=[self.venta.id_venta],
            almuerzos_ids=[],
        )

    def test_anular_marca_como_factura_anulada(self):
        FacturacionService.anular(self.doc.id_documento)
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.tipo_documento, "Factura-Anulada")

    def test_anular_desvincula_ventas(self):
        FacturacionService.anular(self.doc.id_documento)
        self.venta.refresh_from_db()
        self.assertIsNone(self.venta.id_documento_id)

    def test_venta_anulada_vuelve_a_aparecer_en_cola(self):
        FacturacionService.anular(self.doc.id_documento)
        cola = FacturacionService.get_cola()
        self.assertEqual(len(cola), 1)
        self.assertEqual(cola[0]["ventas"][0]["id"], self.venta.id_venta)
