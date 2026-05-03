"""
Tests para validadores personalizados del módulo de ventas
Coverage completo de validators.py
"""

from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.clientes.models import Clientes, TiposCliente
from apps.core.models import Tarjetas
from apps.productos.models import ListasPrecios
from apps.ventas.validators import (
    validar_cantidad_producto,
    validar_codigo_promocion,
    validar_credito_disponible,
    validar_dias_semana,
    validar_estado_pago,
    validar_estado_venta,
    validar_fecha_rango_promocion,
    validar_fecha_venta,
    validar_monto_positivo,
    validar_monto_rango,
    validar_motivo_credito,
    validar_numero_factura,
    validar_porcentaje_descuento,
    validar_saldo_tarjeta,
    validar_tipo_venta,
)


class ValidarMontoPositivoTest(TestCase):
    """Tests para validar_monto_positivo"""

    def test_monto_positivo_valido(self):
        """Montos positivos son válidos"""
        validar_monto_positivo(Decimal("100.50"))
        validar_monto_positivo(Decimal("0.01"))
        validar_monto_positivo(1000)
        validar_monto_positivo(50.75)
        # No debe lanzar excepción
        self.assertTrue(True)

    def test_monto_cero_invalido(self):
        """Monto cero es inválido"""
        with self.assertRaises(ValidationError) as context:
            validar_monto_positivo(Decimal("0"))

        self.assertIn("mayor a cero", str(context.exception))

    def test_monto_negativo_invalido(self):
        """Monto negativo es inválido"""
        with self.assertRaises(ValidationError):
            validar_monto_positivo(Decimal("-10.50"))

    def test_tipo_invalido(self):
        """Tipo no numérico es inválido"""
        with self.assertRaises(ValidationError) as context:
            validar_monto_positivo("abc")

        self.assertIn("numérico", str(context.exception))


class ValidarMontoRangoTest(TestCase):
    """Tests para validar_monto_rango"""

    def test_monto_dentro_rango(self):
        """Monto dentro del rango es válido"""
        validar_monto_rango(Decimal("500"), minimo=Decimal("100"), maximo=Decimal("1000"))
        # No debe lanzar excepción

    def test_monto_menor_minimo(self):
        """Monto menor al mínimo es inválido"""
        with self.assertRaises(ValidationError) as context:
            validar_monto_rango(Decimal("50"), minimo=Decimal("100"))

        self.assertIn("al menos", str(context.exception))

    def test_monto_mayor_maximo(self):
        """Monto mayor al máximo es inválido"""
        with self.assertRaises(ValidationError) as context:
            validar_monto_rango(Decimal("1500"), maximo=Decimal("1000"))

        self.assertIn("no puede exceder", str(context.exception))

    def test_sin_limites(self):
        """Sin límites, cualquier monto es válido"""
        validar_monto_rango(Decimal("99999"))
        # No debe lanzar excepción


class ValidarFechaVentaTest(TestCase):
    """Tests para validar_fecha_venta"""

    def test_fecha_actual_valida(self):
        """Fecha actual es válida"""
        validar_fecha_venta(timezone.now())
        # No debe lanzar excepción

    def test_fecha_reciente_valida(self):
        """Fecha de hace 5 días es válida"""
        fecha = timezone.now() - timedelta(days=5)
        validar_fecha_venta(fecha)

    def test_fecha_futura_invalida(self):
        """Fecha futura (más de 1 hora) es inválida"""
        fecha_futura = timezone.now() + timedelta(hours=2)

        with self.assertRaises(ValidationError) as context:
            validar_fecha_venta(fecha_futura)

        self.assertIn("futura", str(context.exception))

    def test_fecha_muy_antigua_invalida(self):
        """Fecha de hace 31 días es inválida"""
        fecha_antigua = timezone.now() - timedelta(days=31)

        with self.assertRaises(ValidationError) as context:
            validar_fecha_venta(fecha_antigua)

        self.assertIn("antigua", str(context.exception))

    def test_tipo_invalido(self):
        """Tipo no datetime es inválido"""
        with self.assertRaises(ValidationError):
            validar_fecha_venta("2026-03-01")


class ValidarCodigoPromocionTest(TestCase):
    """Tests para validar_codigo_promocion"""

    def test_codigo_valido(self):
        """Códigos válidos"""
        validar_codigo_promocion("VERANO2026")
        validar_codigo_promocion("DESC-50")
        validar_codigo_promocion("MARZO")
        validar_codigo_promocion("2X1")

    def test_codigo_minusculas_invalido(self):
        """Código con minúsculas es inválido"""
        with self.assertRaises(ValidationError):
            validar_codigo_promocion("promo123")

    def test_codigo_con_espacios_invalido(self):
        """Código con espacios es inválido"""
        with self.assertRaises(ValidationError):
            validar_codigo_promocion("PROMO 123")

    def test_codigo_muy_corto(self):
        """Código menor a 3 caracteres es inválido"""
        with self.assertRaises(ValidationError) as context:
            validar_codigo_promocion("AB")

        self.assertIn("entre 3 y 20", str(context.exception))

    def test_codigo_muy_largo(self):
        """Código mayor a 20 caracteres es inválido"""
        with self.assertRaises(ValidationError):
            validar_codigo_promocion("A" * 21)

    def test_codigo_vacio_invalido(self):
        """Código vacío es inválido"""
        with self.assertRaises(ValidationError):
            validar_codigo_promocion("")


class ValidarPorcentajeDescuentoTest(TestCase):
    """Tests para validar_porcentaje_descuento"""

    def test_porcentaje_valido(self):
        """Porcentajes válidos entre 0 y 100"""
        validar_porcentaje_descuento(Decimal("0"))
        validar_porcentaje_descuento(Decimal("50"))
        validar_porcentaje_descuento(Decimal("100"))
        validar_porcentaje_descuento(Decimal("15.5"))

    def test_porcentaje_negativo_invalido(self):
        """Porcentaje negativo es inválido"""
        with self.assertRaises(ValidationError):
            validar_porcentaje_descuento(Decimal("-5"))

    def test_porcentaje_mayor_100_invalido(self):
        """Porcentaje mayor a 100 es inválido"""
        with self.assertRaises(ValidationError):
            validar_porcentaje_descuento(Decimal("150"))


class ValidarEstadosTest(TestCase):
    """Tests para validadores de estados"""

    def test_estado_venta_valido(self):
        """Estados de venta válidos"""
        validar_estado_venta("Activa")
        validar_estado_venta("Cancelada")
        validar_estado_venta("Anulada")

    def test_estado_venta_invalido(self):
        """Estado de venta inválido"""
        with self.assertRaises(ValidationError) as context:
            validar_estado_venta("Procesando")

        self.assertIn("inválido", str(context.exception))

    def test_estado_pago_valido(self):
        """Estados de pago válidos"""
        validar_estado_pago("Pagada")
        validar_estado_pago("Pendiente")
        validar_estado_pago("Parcial")

    def test_estado_pago_invalido(self):
        """Estado de pago inválido"""
        with self.assertRaises(ValidationError):
            validar_estado_pago("Rechazada")

    def test_tipo_venta_valido(self):
        """Tipos de venta válidos"""
        validar_tipo_venta("Contado")
        validar_tipo_venta("Crédito")

    def test_tipo_venta_invalido(self):
        """Tipo de venta inválido"""
        with self.assertRaises(ValidationError):
            validar_tipo_venta("Consignación")


class ValidarCantidadProductoTest(TestCase):
    """Tests para validar_cantidad_producto"""

    def test_cantidad_valida(self):
        """Cantidades válidas"""
        validar_cantidad_producto(Decimal("1"))
        validar_cantidad_producto(Decimal("10.5"))
        validar_cantidad_producto(Decimal("100.250"))

    def test_cantidad_cero_invalida(self):
        """Cantidad cero es inválida"""
        with self.assertRaises(ValidationError):
            validar_cantidad_producto(Decimal("0"))

    def test_cantidad_negativa_invalida(self):
        """Cantidad negativa es inválida"""
        with self.assertRaises(ValidationError):
            validar_cantidad_producto(Decimal("-5"))

    def test_cantidad_excesiva_invalida(self):
        """Cantidad mayor a 9999 es inválida"""
        with self.assertRaises(ValidationError):
            validar_cantidad_producto(Decimal("10000"))

    def test_demasiados_decimales_invalido(self):
        """Más de 3 decimales es inválido"""
        with self.assertRaises(ValidationError) as context:
            validar_cantidad_producto(Decimal("10.1234"))

        self.assertIn("decimales", str(context.exception))


class ValidarFechaRangoPromocionTest(TestCase):
    """Tests para validar_fecha_rango_promocion"""

    def test_rango_valido(self):
        """Rango válido de fechas"""
        hoy = timezone.now().date()
        fin = hoy + timedelta(days=30)
        validar_fecha_rango_promocion(hoy, fin)

    def test_sin_fecha_fin_valido(self):
        """Sin fecha fin es válido (promoción indefinida)"""
        hoy = timezone.now().date()
        validar_fecha_rango_promocion(hoy, None)

    def test_fecha_inicio_muy_antigua(self):
        """Fecha inicio muy antigua es inválida"""
        hace_35_dias = timezone.now().date() - timedelta(days=35)

        with self.assertRaises(ValidationError) as context:
            validar_fecha_rango_promocion(hace_35_dias)

        self.assertIn("antigua", str(context.exception))

    def test_fecha_fin_antes_de_inicio(self):
        """Fecha fin antes de inicio es inválida"""
        hoy = timezone.now().date()
        ayer = hoy - timedelta(days=1)

        with self.assertRaises(ValidationError) as context:
            validar_fecha_rango_promocion(hoy, ayer)

        self.assertIn("posterior", str(context.exception))

    def test_rango_muy_largo(self):
        """Rango mayor a 365 días es inválido"""
        hoy = timezone.now().date()
        fin = hoy + timedelta(days=400)

        with self.assertRaises(ValidationError) as context:
            validar_fecha_rango_promocion(hoy, fin)

        self.assertIn("365", str(context.exception))


class ValidarCreditoDisponibleTest(TestCase):
    """Tests para validar_credito_disponible"""

    def setUp(self):
        """Configurar cliente con crédito"""
        self.tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular", estado=True)

        self.lista = ListasPrecios.objects.create(nombre_lista="Minorista", estado=True)

        self.cliente = Clientes.objects.create(
            nombres="Test",
            apellidos="Cliente",
            ruc_ci="123456",
            limite_credito=Decimal("100000.00"),
            estado=True,
            id_tipo_cliente=self.tipo_cliente,
            id_lista=self.lista,
        )

    def test_credito_suficiente(self):
        """Cliente con crédito suficiente"""
        validar_credito_disponible(self.cliente, Decimal("50000"))
        # No debe lanzar excepción

    def test_credito_insuficiente(self):
        """Cliente sin crédito suficiente"""
        with self.assertRaises(ValidationError) as context:
            validar_credito_disponible(self.cliente, Decimal("150000"))

        self.assertIn("Crédito insuficiente", str(context.exception))
        self.assertIn("Disponible", str(context.exception))


class ValidarSaldoTarjetaTest(TestCase):
    """Tests para validar_saldo_tarjeta"""

    def setUp(self):
        """Configurar tarjeta"""
        from apps.clientes.models import Hijos

        tipo_cliente = TiposCliente.objects.create(nombre_tipo="Regular", estado=True)

        lista = ListasPrecios.objects.create(nombre_lista="Minorista", estado=True)

        cliente = Clientes.objects.create(
            nombres="Test",
            apellidos="Cliente",
            ruc_ci="123456",
            estado=True,
            id_tipo_cliente=tipo_cliente,
            id_lista=lista,
        )

        hijo = Hijos.objects.create(
            nombre="Test", apellido="Hijo", grado="1ro", estado=True, id_cliente_responsable=cliente
        )

        hijo2 = Hijos.objects.create(
            nombre="Test2", apellido="Hijo", grado="2do", estado=True, id_cliente_responsable=cliente
        )

        self.tarjeta_sin_credito = Tarjetas.objects.create(
            nro_tarjeta="T001",
            saldo_actual=Decimal("50000"),
            estado="activa",
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=False,
            limite_credito=Decimal("0"),
            id_hijo=hijo,
            codigo_barras="BAR001",
        )

        self.tarjeta_con_credito = Tarjetas.objects.create(
            nro_tarjeta="T002",
            saldo_actual=Decimal("20000"),
            estado="activa",
            fecha_creacion=timezone.now(),
            permite_saldo_negativo=True,
            limite_credito=Decimal("50000"),
            id_hijo=hijo2,
            codigo_barras="BAR002",
        )

    def test_saldo_suficiente_sin_credito(self):
        """Tarjeta sin crédito con saldo suficiente"""
        validar_saldo_tarjeta(self.tarjeta_sin_credito, Decimal("30000"))
        # No debe lanzar excepción

    def test_saldo_insuficiente_sin_credito(self):
        """Tarjeta sin crédito con saldo insuficiente"""
        with self.assertRaises(ValidationError) as context:
            validar_saldo_tarjeta(self.tarjeta_sin_credito, Decimal("60000"))

        self.assertIn("Saldo insuficiente", str(context.exception))

    def test_credito_disponible(self):
        """Tarjeta con crédito puede usar saldo negativo"""
        # Saldo 20,000 + crédito 50,000 = puede gastar hasta 70,000
        validar_saldo_tarjeta(self.tarjeta_con_credito, Decimal("60000"))
        # No debe lanzar excepción

    def test_excede_limite_credito(self):
        """Exceder límite de crédito es inválido"""
        # Saldo 20,000 + crédito 50,000 = máximo 70,000
        with self.assertRaises(ValidationError) as context:
            validar_saldo_tarjeta(self.tarjeta_con_credito, Decimal("80000"))

        self.assertIn("Límite de crédito excedido", str(context.exception))


class ValidarDiasSemanaTest(TestCase):
    """Tests para validar_dias_semana"""

    def test_dias_validos(self):
        """Días válidos 0-6"""
        validar_dias_semana([0, 1, 2, 3, 4])  # Lunes a Viernes
        validar_dias_semana([5, 6])  # Fin de semana
        validar_dias_semana([0, 6])  # Lunes y Domingo

    def test_lista_vacia_invalida(self):
        """Lista vacía es inválida"""
        with self.assertRaises(ValidationError):
            validar_dias_semana([])

    def test_no_es_lista_invalido(self):
        """No lista es inválido"""
        with self.assertRaises(ValidationError):
            validar_dias_semana("0,1,2")

    def test_dia_fuera_rango_invalido(self):
        """Día fuera de rango 0-6 es inválido"""
        with self.assertRaises(ValidationError):
            validar_dias_semana([0, 1, 7])  # 7 es inválido

    def test_dia_negativo_invalido(self):
        """Día negativo es inválido"""
        with self.assertRaises(ValidationError):
            validar_dias_semana([-1, 0, 1])


class ValidarNumeroFacturaTest(TestCase):
    """Tests para validar_numero_factura"""

    def test_numero_valido(self):
        """Números de factura válidos"""
        validar_numero_factura(123456789)
        validar_numero_factura("001000123456")
        validar_numero_factura(None)  # Opcional
        validar_numero_factura("")

    def test_numero_con_letras_invalido(self):
        """Número con letras es inválido"""
        with self.assertRaises(ValidationError):
            validar_numero_factura("ABC123")

    def test_numero_muy_largo_invalido(self):
        """Número mayor a 15 dígitos es inválido"""
        with self.assertRaises(ValidationError):
            validar_numero_factura("1234567890123456")  # 16 dígitos


class ValidarMotivoCreditoTest(TestCase):
    """Tests para validar_motivo_credito"""

    def test_credito_con_motivo_valido(self):
        """Venta a crédito con motivo es válida"""
        validar_motivo_credito("Cliente frecuente con buen historial de pago", "Crédito")

    def test_contado_sin_motivo_valido(self):
        """Venta al contado no requiere motivo"""
        validar_motivo_credito(None, "Contado")
        validar_motivo_credito("", "Contado")

    def test_credito_sin_motivo_invalido(self):
        """Venta a crédito sin motivo es inválida"""
        with self.assertRaises(ValidationError) as context:
            validar_motivo_credito("", "Crédito")

        self.assertIn("requieren un motivo", str(context.exception))

    def test_motivo_muy_corto_invalido(self):
        """Motivo menor a 10 caracteres es inválido"""
        with self.assertRaises(ValidationError) as context:
            validar_motivo_credito("Corto", "Crédito")

        self.assertIn("al menos 10", str(context.exception))
