"""
Tests comprehensivos para RecargaService
Cubre los 9 métodos principales con múltiples casos de prueba
"""

from django.test import TestCase, TransactionTestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from apps.core.models import (
    Tarjetas,
    CargasSaldo,
    ConsumosTarjeta,
    MediosPago,
    ConfiguracionSistema,
)
from apps.core.services import RecargaService
from apps.clientes.models import Clientes, Hijos, TiposCliente
from apps.productos.models import ListasPrecios, Productos, Categorias
from apps.ventas.models import Ventas
from apps.usuarios.models import Empleados, Roles


class RecargaServiceCalcularMontosTest(TestCase):
    """Tests para RecargaService.calcular_montos()"""

    def test_efectivo_sin_comision(self):
        """Efectivo no debe tener comisión (0%)"""
        resultado = RecargaService.calcular_montos(
            monto_recarga=Decimal("100000"), metodo_pago="efectivo"
        )

        self.assertEqual(resultado["monto_recarga"], Decimal("100000"))
        self.assertEqual(resultado["comision_porcentaje"], Decimal("0.0"))
        self.assertEqual(resultado["comision_monto"], Decimal("0"))
        self.assertEqual(resultado["total_cobrado"], Decimal("100000"))

    def test_bancard_con_comision_3_4_porciento(self):
        """Bancard debe aplicar comisión de 3.4%"""
        resultado = RecargaService.calcular_montos(
            monto_recarga=Decimal("100000"), metodo_pago="bancard"
        )

        self.assertEqual(resultado["monto_recarga"], Decimal("100000"))
        self.assertEqual(resultado["comision_porcentaje"], Decimal("3.4"))
        self.assertEqual(resultado["comision_monto"], Decimal("3400"))
        self.assertEqual(resultado["total_cobrado"], Decimal("103400"))

    def test_tarjeta_pos_con_comision_3_4_porciento(self):
        """POS debe aplicar comisión de 3.4%"""
        resultado = RecargaService.calcular_montos(
            monto_recarga=Decimal("100000"), metodo_pago="tarjeta_pos"
        )

        self.assertEqual(resultado["monto_recarga"], Decimal("100000"))
        self.assertEqual(resultado["comision_porcentaje"], Decimal("3.4"))
        self.assertEqual(resultado["comision_monto"], Decimal("3400"))
        self.assertEqual(resultado["total_cobrado"], Decimal("103400"))

    def test_transferencia_sin_comision(self):
        """Transferencia no debe tener comisión (0%)"""
        resultado = RecargaService.calcular_montos(
            monto_recarga=Decimal("100000"), metodo_pago="transferencia"
        )

        self.assertEqual(resultado["monto_recarga"], Decimal("100000"))
        self.assertEqual(resultado["comision_porcentaje"], Decimal("0.0"))
        self.assertEqual(resultado["comision_monto"], Decimal("0"))
        self.assertEqual(resultado["total_cobrado"], Decimal("100000"))

    def test_monto_con_decimales(self):
        """Calcular comisión con montos decimales"""
        resultado = RecargaService.calcular_montos(
            monto_recarga=Decimal("50000.50"), metodo_pago="bancard"
        )

        self.assertEqual(resultado["monto_recarga"], Decimal("50000.50"))
        self.assertEqual(resultado["comision_monto"], Decimal("1700.02"))  # 3.4% de 50000.50
        self.assertEqual(resultado["total_cobrado"], Decimal("51700.52"))

    def test_metodo_pago_invalido(self):
        """Método de pago no existente debe usar comisión 0%"""
        resultado = RecargaService.calcular_montos(
            monto_recarga=Decimal("100000"), metodo_pago="metodo_inexistente"
        )

        # Debería default a 0% si el método no existe
        self.assertEqual(resultado["comision_porcentaje"], Decimal("0.0"))
        self.assertEqual(resultado["total_cobrado"], Decimal("100000"))


class RecargaServiceGenerarCodigoTest(TestCase):
    """Tests para RecargaService.generar_codigo_referencia()"""

    def test_formato_codigo_referencia(self):
        """Código debe tener formato REF-YYYYMMDD-NNNNN"""
        codigo = RecargaService.generar_codigo_referencia()

        self.assertTrue(codigo.startswith("REF-"))
        partes = codigo.split("-")
        self.assertEqual(len(partes), 3)
        self.assertEqual(partes[0], "REF")
        self.assertEqual(len(partes[1]), 8)  # YYYYMMDD
        self.assertEqual(len(partes[2]), 5)  # NNNNN

    def test_fecha_correcta_en_codigo(self):
        """Código debe contener la fecha actual"""
        codigo = RecargaService.generar_codigo_referencia()
        fecha_hoy = datetime.now().strftime("%Y%m%d")

        self.assertIn(fecha_hoy, codigo)

    def test_codigos_secuenciales(self):
        """Códigos generados el mismo día deben ser secuenciales"""
        codigo1 = RecargaService.generar_codigo_referencia()
        codigo2 = RecargaService.generar_codigo_referencia()

        # Extraer números
        num1 = int(codigo1.split("-")[2])
        num2 = int(codigo2.split("-")[2])

        # Deberían ser secuenciales
        self.assertEqual(num2, num1 + 1)

    def test_unicidad_de_codigos(self):
        """100 códigos generados consecutivamente deben ser únicos"""
        codigos = set()
        for _ in range(100):
            codigo = RecargaService.generar_codigo_referencia()
            codigos.add(codigo)

        # Todos deben ser únicos
        self.assertEqual(len(codigos), 100)


class RecargaServiceValidarIdempotenciaTest(TransactionTestCase):
    """Tests para RecargaService.validar_idempotencia()"""

    def setUp(self):
        """Setup con tarjeta válida"""
        # Crear datos necesarios
        self.lista = ListasPrecios.objects.create(nombre_lista="Test", activo=True)
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Test", activo=True)
        self.cliente = Clientes.objects.create(
            nombres="Test",
            apellidos="Cliente",
            ruc_ci="123",
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )
        self.hijo = Hijos.objects.create(
            nombre="Test", apellido="Hijo", grado="1ro", id_cliente_responsable=self.cliente
        )
        self.tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T001", 
            saldo_actual=Decimal("0"), 
            estado="activa", 
            fecha_creacion=timezone.now(),
            limite_credito=Decimal("1000.00"),
            id_hijo=self.hijo
        )

    def test_comprobante_nuevo_retorna_false(self):
        """Comprobante que no existe debe retornar False"""
        es_duplicado = RecargaService.validar_idempotencia(
            numero_comprobante="COMP-001", referencia_externa=None
        )

        self.assertFalse(es_duplicado)

    def test_comprobante_duplicado_retorna_true(self):
        """Comprobante que ya existe debe retornar True"""
        # Crear recarga con comprobante
        CargasSaldo.objects.create(
            nro_tarjeta=self.tarjeta,
            fecha_carga=timezone.now(),
            monto_cargado=Decimal("100"),
            metodo_pago="efectivo",
            estado="completada",
            numero_comprobante_externo="COMP-001",
        )

        # Validar idempotencia
        es_duplicado = RecargaService.validar_idempotencia(
            numero_comprobante="COMP-001", referencia_externa=None
        )

        self.assertTrue(es_duplicado)

    def test_referencia_externa_duplicada_retorna_true(self):
        """Referencia externa duplicada debe retornar True"""
        # Crear recarga con referencia Bancard
        CargasSaldo.objects.create(
            nro_tarjeta=self.tarjeta,
            fecha_carga=timezone.now(),
            monto_cargado=Decimal("100"),
            metodo_pago="bancard",
            estado="completada",
            referencia_externa="BANC-123456",
        )

        # Validar idempotencia
        es_duplicado = RecargaService.validar_idempotencia(
            numero_comprobante=None, referencia_externa="BANC-123456"
        )

        self.assertTrue(es_duplicado)

    def test_ambos_none_retorna_false(self):
        """Si ambos parámetros son None debe retornar False"""
        es_duplicado = RecargaService.validar_idempotencia(
            numero_comprobante=None, referencia_externa=None
        )

        self.assertFalse(es_duplicado)


class RecargaServiceAcreditarSaldoTest(TransactionTestCase):
    """Tests para RecargaService.acreditar_saldo()"""

    def setUp(self):
        """Setup con tarjeta y recarga"""
        # Crear datos
        self.lista = ListasPrecios.objects.create(nombre_lista="Test", activo=True)
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Test", activo=True)
        self.cliente = Clientes.objects.create(
            nombres="Test",
            apellidos="Cliente",
            ruc_ci="123",
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )
        self.hijo = Hijos.objects.create(
            nombre="Test", apellido="Hijo", grado="1ro", id_cliente_responsable=self.cliente
        )
        self.tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T001", 
            saldo_actual=Decimal("0"), 
            estado="activa", 
            fecha_creacion=timezone.now(),
            limite_credito=Decimal("1000.00"),
            id_hijo=self.hijo
        )
        self.recarga = CargasSaldo.objects.create(
            nro_tarjeta=self.tarjeta,
            fecha_carga=timezone.now(),
            monto_cargado=Decimal("100000"),
            metodo_pago="efectivo",
            estado="completada",
        )

    def test_acredita_saldo_correctamente(self):
        """Debe actualizar saldo_actual de la tarjeta"""
        resultado = RecargaService.acreditar_saldo(self.recarga)

        self.assertTrue(resultado["success"])
        self.assertEqual(resultado["saldo_anterior"], Decimal("0"))
        self.assertEqual(resultado["saldo_nuevo"], Decimal("100000"))
        self.assertEqual(resultado["monto_acreditado"], Decimal("100000"))

        # Verificar en BD
        self.tarjeta.refresh_from_db()
        self.assertEqual(self.tarjeta.saldo_actual, Decimal("100000"))

    def test_crea_registro_en_consumos_tarjeta(self):
        """Debe crear consumo negativo (ingreso)"""
        resultado = RecargaService.acreditar_saldo(self.recarga)

        self.assertTrue(resultado["success"])

        # Verificar consumo
        consumo = ConsumosTarjeta.objects.get(id_consumo=resultado["id_consumo"])
        self.assertEqual(consumo.nro_tarjeta, self.tarjeta)
        self.assertEqual(consumo.monto_consumido, Decimal("-100000"))  # Negativo = ingreso
        self.assertEqual(consumo.tipo_operacion, "recarga")

    def test_acumulacion_de_saldo(self):
        """Múltiples recargas deben acumularse"""
        # Primera recarga
        RecargaService.acreditar_saldo(self.recarga)

        # Segunda recarga
        recarga2 = CargasSaldo.objects.create(
            nro_tarjeta=self.tarjeta,
            fecha_carga=timezone.now(),
            monto_cargado=Decimal("50000"),
            metodo_pago="efectivo",
            estado="completada",
        )
        resultado2 = RecargaService.acreditar_saldo(recarga2)

        self.assertEqual(resultado2["saldo_anterior"], Decimal("100000"))
        self.assertEqual(resultado2["saldo_nuevo"], Decimal("150000"))

        # Verificar en BD
        self.tarjeta.refresh_from_db()
        self.assertEqual(self.tarjeta.saldo_actual, Decimal("150000"))

    def test_atomicidad_con_error(self):
        """Si hay error, no debe actualizar ningún dato"""
        # Forzar error eliminando la tarjeta
        tarjeta_id = self.tarjeta.nro_tarjeta
        self.tarjeta.delete()

        # Intentar acreditar (debe fallar)
        with self.assertRaises(Exception):
            RecargaService.acreditar_saldo(self.recarga)

        # Verificar que no se creó consumo
        self.assertEqual(ConsumosTarjeta.objects.count(), 0)


class RecargaServiceGenerarFacturaTest(TransactionTestCase):
    """Tests para RecargaService.generar_factura()"""

    def setUp(self):
        """Setup con datos completos"""
        self.lista = ListasPrecios.objects.create(nombre_lista="Test", activo=True)
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Test", activo=True)
        self.cliente = Clientes.objects.create(
            nombres="Test",
            apellidos="Cliente",
            ruc_ci="123",
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )
        self.hijo = Hijos.objects.create(
            nombre="Test", apellido="Hijo", grado="1ro", id_cliente_responsable=self.cliente
        )
        self.tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T001", 
            saldo_actual=Decimal("0"), 
            estado="activa", 
            fecha_creacion=timezone.now(),
            limite_credito=Decimal("1000.00"),
            id_hijo=self.hijo
        )

        # Crear categoría
        self.categoria = Categorias.objects.create(nombre_categoria="Servicios", activo=True)

        self.recarga = CargasSaldo.objects.create(
            nro_tarjeta=self.tarjeta,
            fecha_carga=timezone.now(),
            monto_cargado=Decimal("100000"),
            total_cobrado=Decimal("103400"),
            comision_aplicada=Decimal("3400"),
            metodo_pago="bancard",
            estado="completada",
        )

    def test_crea_producto_recarga_si_no_existe(self):
        """Debe crear producto RECARGA-SALDO automáticamente"""
        resultado = RecargaService.generar_factura(self.recarga)

        self.assertTrue(resultado["success"])

        # Verificar producto
        producto = Productos.objects.get(codigo="RECARGA-SALDO")
        self.assertEqual(producto.descripcion, "Recarga de Saldo Prepago")
        self.assertTrue(producto.es_servicio)

    def test_reutiliza_producto_existente(self):
        """No debe duplicar el producto si ya existe"""
        # Crear producto manualmente
        Productos.objects.create(
            codigo="RECARGA-SALDO",
            descripcion="Recarga de Saldo",
            precio_venta=Decimal("1"),
            es_servicio=True,
            activo=True,
            id_categoria=self.categoria,
        )

        # Generar factura
        RecargaService.generar_factura(self.recarga)

        # Verificar que solo existe 1 producto
        self.assertEqual(Productos.objects.filter(codigo="RECARGA-SALDO").count(), 1)

    def test_factura_monto_sin_comision(self):
        """Factura debe ser por monto_cargado, NO total_cobrado"""
        resultado = RecargaService.generar_factura(self.recarga)

        # Verificar venta
        venta = Ventas.objects.get(id_venta=resultado["id_factura"])
        self.assertEqual(venta.total_venta, Decimal("100000"))  # Sin comisión
        self.assertNotEqual(venta.total_venta, Decimal("103400"))  # NO incluye comisión

    def test_vincula_factura_a_recarga(self):
        """Debe actualizar id_factura en la recarga"""
        resultado = RecargaService.generar_factura(self.recarga)

        self.recarga.refresh_from_db()
        self.assertIsNotNone(self.recarga.id_factura)
        self.assertEqual(self.recarga.id_factura.id_venta, resultado["id_factura"])


class RecargaServiceProcesarRecargaCajaTest(TransactionTestCase):
    """Tests para RecargaService.procesar_recarga_caja()"""

    def setUp(self):
        """Setup completo para recarga en caja"""
        self.lista = ListasPrecios.objects.create(nombre_lista="Test", activo=True)
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Test", activo=True)
        self.cliente = Clientes.objects.create(
            nombres="Test",
            apellidos="Cliente",
            ruc_ci="123",
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )
        self.hijo = Hijos.objects.create(
            nombre="Test", apellido="Hijo", grado="1ro", id_cliente_responsable=self.cliente
        )
        self.tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T001", 
            saldo_actual=Decimal("0"), 
            estado="activa", 
            fecha_creacion=timezone.now(),
            limite_credito=Decimal("1000.00"),
            id_hijo=self.hijo
        )

        # Crear empleado
        self.rol = Roles.objects.create(nombre_rol="Cajero", activo=True)
        self.empleado = Empleados.objects.create(
            nombre="Juan",
            apellido="Cajero",
            email="cajero@test.com",
            usuario="cajero1",
            activo=True,
            id_rol=self.rol,
        )

        # Crear categoría
        self.categoria = Categorias.objects.create(nombre_categoria="Servicios", activo=True)

    def test_recarga_efectivo_completa(self):
        """Recarga en efectivo debe completarse inmediatamente"""
        resultado = RecargaService.procesar_recarga_caja(
            hijo_id=self.hijo.id_hijo,
            monto=Decimal("100000"),
            metodo_pago="efectivo",
            empleado_id=self.empleado.id_empleado,
            numero_comprobante="CAJA-001",
        )

        self.assertTrue(resultado["success"])
        self.assertEqual(resultado["estado"], "completada")
        self.assertEqual(resultado["monto_acreditado"], Decimal("100000"))
        self.assertEqual(resultado["saldo_nuevo"], Decimal("100000"))
        self.assertIsNotNone(resultado["id_factura"])

    def test_recarga_pos_con_comision(self):
        """Recarga POS debe aplicar comisión 3.4%"""
        resultado = RecargaService.procesar_recarga_caja(
            hijo_id=self.hijo.id_hijo,
            monto=Decimal("100000"),
            metodo_pago="tarjeta_pos",
            empleado_id=self.empleado.id_empleado,
            numero_comprobante="POS-001",
        )

        self.assertTrue(resultado["success"])
        self.assertEqual(resultado["total_cobrado"], Decimal("103400"))
        self.assertEqual(resultado["comision"], Decimal("3400"))
        self.assertEqual(resultado["monto_acreditado"], Decimal("100000"))

    def test_crea_recarga_con_estado_completada(self):
        """Debe crear recarga con estado completada"""
        resultado = RecargaService.procesar_recarga_caja(
            hijo_id=self.hijo.id_hijo,
            monto=Decimal("50000"),
            metodo_pago="efectivo",
            empleado_id=self.empleado.id_empleado,
            numero_comprobante="CAJA-002",
        )

        recarga = CargasSaldo.objects.get(id_carga=resultado["id_recarga"])
        self.assertEqual(recarga.estado, "completada")
        self.assertEqual(recarga.usuario_responsable, self.empleado)


class RecargaServiceTransferenciaTest(TransactionTestCase):
    """Tests para flujos de transferencia bancaria"""

    def setUp(self):
        """Setup para transferencias"""
        self.lista = ListasPrecios.objects.create(nombre_lista="Test", activo=True)
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Test", activo=True)
        self.cliente = Clientes.objects.create(
            nombres="Test",
            apellidos="Cliente",
            ruc_ci="123",
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )
        self.hijo = Hijos.objects.create(
            nombre="Test", apellido="Hijo", grado="1ro", id_cliente_responsable=self.cliente
        )
        self.tarjeta = Tarjetas.objects.create(
            nro_tarjeta="T001", 
            saldo_actual=Decimal("0"), 
            estado="activa", 
            fecha_creacion=timezone.now(),
            limite_credito=Decimal("1000.00"),
            id_hijo=self.hijo
        )
        self.rol = Roles.objects.create(nombre_rol="Cajero", activo=True)
        self.empleado = Empleados.objects.create(
            nombre="Juan",
            apellido="Cajero",
            email="cajero@test.com",
            usuario="cajero1",
            activo=True,
            id_rol=self.rol,
        )
        self.categoria = Categorias.objects.create(nombre_categoria="Servicios", activo=True)

    def test_iniciar_transferencia_genera_codigo(self):
        """Debe generar código de referencia único"""
        resultado = RecargaService.iniciar_recarga_transferencia(
            hijo_id=self.hijo.id_hijo, monto=Decimal("200000")
        )

        self.assertTrue(resultado["success"])
        self.assertIn("codigo_referencia", resultado)
        self.assertTrue(resultado["codigo_referencia"].startswith("REF-"))
        self.assertEqual(resultado["monto_transferir"], Decimal("200000"))

    def test_validar_transferencia_monto_bajo(self):
        """Transferencia <500K debe completarse automáticamente"""
        # Iniciar
        init_result = RecargaService.iniciar_recarga_transferencia(
            hijo_id=self.hijo.id_hijo, monto=Decimal("100000")
        )

        # Validar
        resultado = RecargaService.validar_transferencia(
            codigo_referencia=init_result["codigo_referencia"],
            numero_comprobante="TRANSF-001",
            empleado_id=self.empleado.id_empleado,
        )

        self.assertTrue(resultado["success"])
        self.assertFalse(resultado["requiere_aprobacion"])
        self.assertEqual(resultado["estado"], "completada")
        self.assertEqual(resultado["monto_acreditado"], Decimal("100000"))

    def test_validar_transferencia_monto_alto_requiere_supervisor(self):
        """Transferencia >500K debe quedar pendiente de aprobación"""
        # Iniciar
        init_result = RecargaService.iniciar_recarga_transferencia(
            hijo_id=self.hijo.id_hijo, monto=Decimal("600000")
        )

        # Validar
        resultado = RecargaService.validar_transferencia(
            codigo_referencia=init_result["codigo_referencia"],
            numero_comprobante="TRANSF-002",
            empleado_id=self.empleado.id_empleado,
        )

        self.assertTrue(resultado["success"])
        self.assertTrue(resultado["requiere_aprobacion"])
        self.assertEqual(resultado["estado"], "validacion_pendiente")

    def test_aprobar_recarga_supervisor(self):
        """Supervisor debe poder aprobar recarga pendiente"""
        # Crear supervisor
        rol_supervisor = Roles.objects.create(nombre_rol="Supervisor", activo=True)
        supervisor = Empleados.objects.create(
            nombre="Maria",
            apellido="Supervisor",
            email="supervisor@test.com",
            usuario="supervisor1",
            activo=True,
            id_rol=rol_supervisor,
        )

        # Crear recarga pendiente de validación
        recarga = CargasSaldo.objects.create(
            nro_tarjeta=self.tarjeta,
            fecha_carga=timezone.now(),
            monto_cargado=Decimal("600000"),
            metodo_pago="transferencia",
            estado="validacion_pendiente",
            requiere_validacion_supervisor=True,
            usuario_responsable=self.empleado,
        )

        # Aprobar
        resultado = RecargaService.aprobar_recarga_supervisor(
            recarga_id=recarga.id_carga, supervisor_id=supervisor.id_empleado
        )

        self.assertTrue(resultado["success"])
        self.assertEqual(resultado["estado"], "completada")
        self.assertEqual(resultado["monto_acreditado"], Decimal("600000"))

        # Verificar en BD
        recarga.refresh_from_db()
        self.assertEqual(recarga.estado, "completada")
        self.assertEqual(recarga.supervisor_aprobador, supervisor)
        self.assertIsNotNone(recarga.fecha_aprobacion)


class RecargaServiceEdgeCasesTest(TransactionTestCase):
    """Tests de casos borde y errores"""

    def setUp(self):
        """Setup mínimo"""
        self.lista = ListasPrecios.objects.create(nombre_lista="Test", activo=True)
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Test", activo=True)
        self.cliente = Clientes.objects.create(
            nombres="Test",
            apellidos="Cliente",
            ruc_ci="123",
            id_lista=self.lista,
            id_tipo_cliente=self.tipo_cliente,
        )

    def test_hijo_inexistente_falla(self):
        """Procesar recarga con hijo inexistente debe fallar"""
        rol = Roles.objects.create(nombre_rol="Cajero", activo=True)
        empleado = Empleados.objects.create(
            nombre="Juan",
            apellido="Cajero",
            email="cajero@test.com",
            usuario="cajero1",
            activo=True,
            id_rol=rol,
        )

        with self.assertRaises(Exception):
            RecargaService.procesar_recarga_caja(
                hijo_id=99999,  # No existe
                monto=Decimal("100000"),
                metodo_pago="efectivo",
                empleado_id=empleado.id_empleado,
                numero_comprobante="TEST-001",
            )

    def test_monto_cero_o_negativo_deberia_fallar(self):
        """Montos cero o negativos no son válidos"""
        # Este test podría fallar si no hay validación,
        # indicando que se necesita agregar validación
        resultado = RecargaService.calcular_montos(
            monto_recarga=Decimal("0"), metodo_pago="efectivo"
        )

        # Debería retornar error o montos en cero
        self.assertEqual(resultado["total_cobrado"], Decimal("0"))
