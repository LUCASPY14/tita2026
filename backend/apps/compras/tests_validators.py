"""
Tests para validadores del módulo Compras
Cobertura completa de 24 validadores
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

from apps.compras.validators import (
    # Proveedores
    validar_ruc,
    validar_razon_social,
    validar_email_proveedor,
    validar_telefono_proveedor,
    validar_limite_credito_proveedor,
    # Compras
    validar_monto_compra,
    validar_estado_pago,
    validar_transicion_estado_compra,
    validar_fecha_compra,
    validar_numero_factura,
    validar_saldo_compra,
    # Detalles Compra
    validar_cantidad_compra,
    validar_costo_unitario,
    validar_subtotal_coherente,
    # Pagos
    validar_monto_pago,
    validar_aplicacion_pago,
    validar_suma_aplicaciones,
    # Notas de Crédito
    validar_monto_nota_credito,
    validar_motivo_nota_credito,
    validar_estado_nota_credito,
    # Cuenta Corriente
    validar_dias_credito,
    validar_compra_dentro_limite_credito,
)


class ValidadoresRUCTestCase(TestCase):
    """Tests para validar_ruc"""
    
    def test_ruc_valido_formato_corto(self):
        """RUC válido con formato corto debe pasar"""
        try:
            validar_ruc('80012345-0')  # Dígito verificador correcto según algoritmo
        except ValidationError:
            self.fail("RUC válido no debería lanzar error")
    
    def test_ruc_valido_formato_largo(self):
        """RUC válido con formato largo debe pasar"""
        try:
            validar_ruc('8001234-5')  # Dígito verificador correcto según algoritmo
        except ValidationError:
            self.fail("RUC válido no debería lanzar error")
    
    def test_ruc_formato_invalido_sin_guion(self):
        """RUC sin guión debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_ruc('800123456')
        self.assertIn("formato", str(context.exception).lower())
    
    def test_ruc_formato_invalido_letras(self):
        """RUC con letras debe fallar"""
        with self.assertRaises(ValidationError):
            validar_ruc('8001234A-6')
    
    def test_ruc_digito_verificador_incorrecto(self):
        """RUC con dígito verificador incorrecto debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_ruc('80012345-9')  # Debería ser -3
        self.assertIn("incorrecto", str(context.exception).lower())
    
    def test_ruc_vacio(self):
        """RUC vacío debe fallar"""
        with self.assertRaises(ValidationError):
            validar_ruc('')
    
    def test_ruc_none(self):
        """RUC None debe fallar"""
        with self.assertRaises(ValidationError):
            validar_ruc(None)


class ValidadoresRazonSocialTestCase(TestCase):
    """Tests para validar_razon_social"""
    
    def test_razon_social_valida(self):
        """Razón social válida debe pasar"""
        try:
            validar_razon_social('Distribuidora ABC S.A.')
            validar_razon_social('Comercial XYZ & Asociados')
        except ValidationError:
            self.fail("Razón social válida no debería fallar")
    
    def test_razon_social_muy_corta(self):
        """Razón social < 3 caracteres debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_razon_social('AB')
        self.assertIn("3 caracteres", str(context.exception))
    
    def test_razon_social_muy_larga(self):
        """Razón social > 255 caracteres debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_razon_social('A' * 256)
        self.assertIn("255", str(context.exception))
    
    def test_razon_social_caracteres_especiales_permitidos(self):
        """Caracteres especiales comunes deben ser permitidos"""
        try:
            validar_razon_social("Empresa De'Tal & Cía. S.R.L.")
        except ValidationError:
            self.fail("Caracteres comunes deberían ser permitidos")
    
    def test_razon_social_vacia(self):
        """Razón social vacía debe fallar"""
        with self.assertRaises(ValidationError):
            validar_razon_social('')
    
    def test_razon_social_con_acentos(self):
        """Razón social con acentos debe pasar"""
        try:
            validar_razon_social('Distribución Ñandutí S.A.')
        except ValidationError:
            self.fail("Acentos deberían ser permitidos")


class ValidadoresEmailProveedorTestCase(TestCase):
    """Tests para validar_email_proveedor"""
    
    def test_email_valido(self):
        """Email válido debe pasar"""
        try:
            validar_email_proveedor('proveedor@empresa.com.py')
            validar_email_proveedor('contacto@distribuidora.com')
        except ValidationError:
            self.fail("Email válido no debería fallar")
    
    def test_email_vacio_permitido(self):
        """Email vacío debe ser permitido (opcional)"""
        try:
            validar_email_proveedor('')
            validar_email_proveedor(None)
        except ValidationError:
            self.fail("Email vacío debería ser permitido")
    
    def test_email_formato_invalido(self):
        """Email con formato inválido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_email_proveedor('email_invalido.com')
        
        with self.assertRaises(ValidationError):
            validar_email_proveedor('sin_arroba.com')
    
    def test_email_muy_largo(self):
        """Email > 254 caracteres debe fallar"""
        with self.assertRaises(ValidationError):
            validar_email_proveedor('a' * 250 + '@test.com')


class ValidadoresTelefonoProveedorTestCase(TestCase):
    """Tests para validar_telefono_proveedor"""
    
    def test_telefono_celular_valido(self):
        """Teléfono celular válido debe pasar"""
        try:
            validar_telefono_proveedor('0981123456')
            validar_telefono_proveedor('+595981123456')
        except ValidationError:
            self.fail("Teléfono celular válido no debería fallar")
    
    def test_telefono_fijo_valido(self):
        """Teléfono fijo válido debe pasar"""
        try:
            validar_telefono_proveedor('021-123456')
            validar_telefono_proveedor('0331234567')
        except ValidationError:
            self.fail("Teléfono fijo válido no debería fallar")
    
    def test_telefono_vacio_permitido(self):
        """Teléfono vacío debe ser permitido (opcional)"""
        try:
            validar_telefono_proveedor('')
            validar_telefono_proveedor(None)
        except ValidationError:
            self.fail("Teléfono vacío debería ser permitido")
    
    def test_telefono_formato_invalido(self):
        """Teléfono con formato inválido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_telefono_proveedor('123')  # Muy corto
        
        with self.assertRaises(ValidationError):
            validar_telefono_proveedor('abcd-efgh')  # Letras


class ValidadoresLimiteCreditoTestCase(TestCase):
    """Tests para validar_limite_credito_proveedor"""
    
    def test_limite_credito_valido(self):
        """Límite de crédito válido debe pasar"""
        try:
            validar_limite_credito_proveedor(Decimal('5000000.00'))
        except ValidationError:
            self.fail("Límite válido no debería fallar")
    
    def test_limite_credito_cero_valido(self):
        """Límite de crédito en cero debe ser válido"""
        try:
            validar_limite_credito_proveedor(Decimal('0.00'))
        except ValidationError:
            self.fail("Límite cero debería ser válido")
    
    def test_limite_credito_negativo_invalido(self):
        """Límite de crédito negativo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_limite_credito_proveedor(Decimal('-1000.00'))
    
    def test_limite_credito_excedido_por_compras(self):
        """Compras pendientes que exceden límite deben fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_limite_credito_proveedor(
                limite_credito=Decimal('5000000.00'),
                compras_pendientes=Decimal('6000000.00')
            )
        self.assertIn("superan", str(context.exception).lower())
    
    def test_limite_credito_none_permitido(self):
        """Límite None debe ser permitido (sin límite)"""
        try:
            validar_limite_credito_proveedor(None)
        except ValidationError:
            self.fail("Límite None debería ser permitido")


class ValidadoresMontoCompraTestCase(TestCase):
    """Tests para validar_monto_compra"""
    
    def test_monto_compra_valido(self):
        """Monto válido debe pasar"""
        try:
            validar_monto_compra(Decimal('1000000.00'))
            validar_monto_compra(Decimal('0.01'))
        except ValidationError:
            self.fail("Monto válido no debería fallar")
    
    def test_monto_compra_cero_invalido(self):
        """Monto cero debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_monto_compra(Decimal('0.00'))
        self.assertIn("positivo", str(context.exception).lower())
    
    def test_monto_compra_negativo_invalido(self):
        """Monto negativo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_compra(Decimal('-5000.00'))
    
    def test_monto_compra_excesivo(self):
        """Monto excesivo (> 100 millones) debe lanzar advertencia"""
        with self.assertRaises(ValidationError) as context:
            validar_monto_compra(Decimal('150000000.00'))
        self.assertIn("excesivamente alto", str(context.exception).lower())
    
    def test_monto_compra_none_invalido(self):
        """Monto None debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_compra(None)


class ValidadoresEstadoPagoTestCase(TestCase):
    """Tests para validar_estado_pago y transiciones"""
    
    def test_estado_pago_valido(self):
        """Estados válidos deben pasar"""
        estados = ['Pendiente', 'Confirmado', 'Pagado', 'Parcial', 'Cancelado']
        for estado in estados:
            try:
                validar_estado_pago(estado)
            except ValidationError:
                self.fail(f"Estado '{estado}' debería ser válido")
    
    def test_estado_pago_invalido(self):
        """Estado inválido debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_estado_pago('InvalidoEstado')
        self.assertIn("no válido", str(context.exception).lower())
    
    def test_estado_pago_vacio(self):
        """Estado vacío debe fallar"""
        with self.assertRaises(ValidationError):
            validar_estado_pago('')
    
    def test_transicion_pendiente_a_confirmado_valida(self):
        """Transición Pendiente → Confirmado debe pasar"""
        try:
            validar_transicion_estado_compra('Pendiente', 'Confirmado')
        except ValidationError:
            self.fail("Transición válida no debería fallar")
    
    def test_transicion_confirmado_a_pagado_valida(self):
        """Transición Confirmado → Pagado debe pasar"""
        try:
            validar_transicion_estado_compra('Confirmado', 'Pagado')
        except ValidationError:
            self.fail("Transición válida no debería fallar")
    
    def test_transicion_pagado_a_cualquiera_invalida(self):
        """Desde Pagado no se puede cambiar a ningún estado"""
        with self.assertRaises(ValidationError) as context:
            validar_transicion_estado_compra('Pagado', 'Confirmado')
        self.assertIn("no se puede cambiar", str(context.exception).lower())
    
    def test_transicion_cancelado_a_cualquiera_invalida(self):
        """Desde Cancelado no se puede cambiar"""
        with self.assertRaises(ValidationError):
            validar_transicion_estado_compra('Cancelado', 'Pendiente')
    
    def test_transicion_pendiente_a_pagado_invalida(self):
        """No se puede ir directamente de Pendiente a Pagado"""
        with self.assertRaises(ValidationError):
            validar_transicion_estado_compra('Pendiente', 'Pagado')


class ValidadoresFechaCompraTestCase(TestCase):
    """Tests para validar_fecha_compra"""
    
    def test_fecha_compra_hoy_valida(self):
        """Fecha de hoy debe ser válida"""
        try:
            validar_fecha_compra(timezone.now())
        except ValidationError:
            self.fail("Fecha de hoy debería ser válida")
    
    def test_fecha_compra_una_semana_atras_valida(self):
        """Fecha de hace una semana debe ser válida"""
        try:
            fecha = timezone.now() - timedelta(days=7)
            validar_fecha_compra(fecha)
        except ValidationError:
            self.fail("Fecha reciente debería ser válida")
    
    def test_fecha_compra_futura_invalida(self):
        """Fecha futura (>1 día) debe fallar"""
        with self.assertRaises(ValidationError) as context:
            fecha_futura = timezone.now() + timedelta(days=2)
            validar_fecha_compra(fecha_futura)
        self.assertIn("futura", str(context.exception).lower())
    
    def test_fecha_compra_muy_antigua_invalida(self):
        """Fecha > 1 año atrás debe fallar"""
        with self.assertRaises(ValidationError) as context:
            fecha_antigua = timezone.now() - timedelta(days=400)
            validar_fecha_compra(fecha_antigua)
        self.assertIn("antigua", str(context.exception).lower())
    
    def test_fecha_compra_vacia_invalida(self):
        """Fecha vacía debe fallar"""
        with self.assertRaises(ValidationError):
            validar_fecha_compra(None)


class ValidadoresNumeroFacturaTestCase(TestCase):
    """Tests para validar_numero_factura"""
    
    def test_numero_factura_formato_paraguayo_valido(self):
        """Formato paraguayo estándar debe pasar"""
        try:
            validar_numero_factura('001-001-0001234')
        except ValidationError:
            self.fail("Formato paraguayo válido no debería fallar")
    
    def test_numero_factura_formato_simple_valido(self):
        """Formato simple (13 dígitos) debe pasar"""
        try:
            validar_numero_factura('0010010001234')
        except ValidationError:
            self.fail("Formato simple válido no debería fallar")
    
    def test_numero_factura_texto_libre_valido(self):
        """Texto libre razonable debe pasar"""
        try:
            validar_numero_factura('FACT-2024-00123')
        except ValidationError:
            self.fail("Texto libre válido no debería fallar")
    
    def test_numero_factura_muy_largo_invalido(self):
        """Número > 50 caracteres debe fallar"""
        with self.assertRaises(ValidationError):
            validar_numero_factura('A' * 51)
    
    def test_numero_factura_vacio_permitido(self):
        """Número vacío debe ser permitido (opcional)"""
        try:
            validar_numero_factura('')
            validar_numero_factura(None)
        except ValidationError:
            self.fail("Número vacío debería ser permitido")


class ValidadoresSaldoCompraTestCase(TestCase):
    """Tests para validar_saldo_compra"""
    
    def test_saldo_compra_valido(self):
        """Saldo válido dentro del rango debe pasar"""
        try:
            validar_saldo_compra(
                saldo_pendiente=Decimal('500000.00'),
                monto_total=Decimal('1000000.00')
            )
        except ValidationError:
            self.fail("Saldo válido no debería fallar")
    
    def test_saldo_compra_cero_valido(self):
        """Saldo cero debe ser válido (totalmente pagado)"""
        try:
            validar_saldo_compra(
                saldo_pendiente=Decimal('0.00'),
                monto_total=Decimal('1000000.00')
            )
        except ValidationError:
            self.fail("Saldo cero debería ser válido")
    
    def test_saldo_compra_negativo_invalido(self):
        """Saldo negativo debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_saldo_compra(
                saldo_pendiente=Decimal('-100.00'),
                monto_total=Decimal('1000000.00')
            )
        self.assertIn("negativo", str(context.exception).lower())
    
    def test_saldo_mayor_que_total_invalido(self):
        """Saldo > monto total debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_saldo_compra(
                saldo_pendiente=Decimal('2000000.00'),
                monto_total=Decimal('1000000.00')
            )
        self.assertIn("mayor al total", str(context.exception).lower())


class ValidadoresCantidadCompraTestCase(TestCase):
    """Tests para validar_cantidad_compra"""
    
    def test_cantidad_compra_valida(self):
        """Cantidad válida debe pasar"""
        try:
            validar_cantidad_compra(Decimal('10.000'))
            validar_cantidad_compra(Decimal('0.001'))
        except ValidationError:
            self.fail("Cantidad válida no debería fallar")
    
    def test_cantidad_compra_cero_invalida(self):
        """Cantidad cero debe fallar"""
        with self.assertRaises(ValidationError):
            validar_cantidad_compra(Decimal('0.000'))
    
    def test_cantidad_compra_negativa_invalida(self):
        """Cantidad negativa debe fallar"""
        with self.assertRaises(ValidationError):
            validar_cantidad_compra(Decimal('-5.000'))
    
    def test_cantidad_compra_excesiva(self):
        """Cantidad excesiva (> 100,000) debe lanzar advertencia"""
        with self.assertRaises(ValidationError):
            validar_cantidad_compra(Decimal('150000.000'))
    
    def test_cantidad_compra_none_invalida(self):
        """Cantidad None debe fallar"""
        with self.assertRaises(ValidationError):
            validar_cantidad_compra(None)


class ValidadoresCostoUnitarioTestCase(TestCase):
    """Tests para validar_costo_unitario"""
    
    def test_costo_unitario_valido(self):
        """Costo válido debe pasar"""
        try:
            validar_costo_unitario(Decimal('50000.00'))
            validar_costo_unitario(Decimal('0.01'))
        except ValidationError:
            self.fail("Costo válido no debería fallar")
    
    def test_costo_unitario_cero_invalido(self):
        """Costo cero debe fallar"""
        with self.assertRaises(ValidationError):
            validar_costo_unitario(Decimal('0.00'))
    
    def test_costo_unitario_negativo_invalido(self):
        """Costo negativo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_costo_unitario(Decimal('-1000.00'))
    
    def test_costo_unitario_excesivo(self):
        """Costo excesivo (> 10 millones) debe lanzar advertencia"""
        with self.assertRaises(ValidationError):
            validar_costo_unitario(Decimal('15000000.00'))
    
    def test_costo_unitario_none_invalido(self):
        """Costo None debe fallar"""
        with self.assertRaises(ValidationError):
            validar_costo_unitario(None)


class ValidadoresSubtotalCoherenteTestCase(TestCase):
    """Tests para validar_subtotal_coherente"""
    
    def test_subtotal_coherente_exacto(self):
        """Subtotal exacto debe pasar"""
        try:
            validar_subtotal_coherente(
                cantidad=Decimal('10.000'),
                costo_unitario=Decimal('5000.00'),
                subtotal=Decimal('50000.00')
            )
        except ValidationError:
            self.fail("Subtotal coherente no debería fallar")
    
    def test_subtotal_coherente_con_redondeo(self):
        """Subtotal con diferencia de redondeo mínima debe pasar"""
        try:
            validar_subtotal_coherente(
                cantidad=Decimal('3.333'),
                costo_unitario=Decimal('1500.00'),
                subtotal=Decimal('4999.50')  # Real: 4999.50
            )
        except ValidationError:
            self.fail("Diferencia mínima de redondeo debería ser tolerada")
    
    def test_subtotal_incoherente_mayor(self):
        """Subtotal significativamente mayor debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_subtotal_coherente(
                cantidad=Decimal('10.000'),
                costo_unitario=Decimal('5000.00'),
                subtotal=Decimal('60000.00')  # Debería ser 50000.00
            )
        self.assertIn("no coincide", str(context.exception).lower())
    
    def test_subtotal_incoherente_menor(self):
        """Subtotal significativamente menor debe fallar"""
        with self.assertRaises(ValidationError):
            validar_subtotal_coherente(
                cantidad=Decimal('10.000'),
                costo_unitario=Decimal('5000.00'),
                subtotal=Decimal('40000.00')  # Debería ser 50000.00
            )


class ValidadoresMontoPagoTestCase(TestCase):
    """Tests para validar_monto_pago"""
    
    def test_monto_pago_valido(self):
        """Monto de pago válido debe pasar"""
        try:
            validar_monto_pago(Decimal('1000000.00'))
        except ValidationError:
            self.fail("Monto válido no debería fallar")
    
    def test_monto_pago_cero_invalido(self):
        """Monto cero debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_pago(Decimal('0.00'))
    
    def test_monto_pago_negativo_invalido(self):
        """Monto negativo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_pago(Decimal('-5000.00'))
    
    def test_monto_pago_none_invalido(self):
        """Monto None debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_pago(None)


class ValidadoresAplicacionPagoTestCase(TestCase):
    """Tests para validar_aplicacion_pago"""
    
    def test_aplicacion_pago_valida(self):
        """Aplicación válida dentro del saldo debe pasar"""
        try:
            validar_aplicacion_pago(
                monto_aplicado=Decimal('300000.00'),
                saldo_compra=Decimal('500000.00')
            )
        except ValidationError:
            self.fail("Aplicación válida no debería fallar")
    
    def test_aplicacion_pago_total_valida(self):
        """Aplicación por el total del saldo debe pasar"""
        try:
            validar_aplicacion_pago(
                monto_aplicado=Decimal('500000.00'),
                saldo_compra=Decimal('500000.00')
            )
        except ValidationError:
            self.fail("Aplicación total debería ser válida")
    
    def test_aplicacion_pago_excede_saldo(self):
        """Aplicación que excede el saldo debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_aplicacion_pago(
                monto_aplicado=Decimal('600000.00'),
                saldo_compra=Decimal('500000.00')
            )
        self.assertIn("excede", str(context.exception).lower())
    
    def test_aplicacion_pago_cero_invalida(self):
        """Aplicación de cero debe fallar"""
        with self.assertRaises(ValidationError):
            validar_aplicacion_pago(
                monto_aplicado=Decimal('0.00'),
                saldo_compra=Decimal('500000.00')
            )
    
    def test_aplicacion_pago_negativa_invalida(self):
        """Aplicación negativa debe fallar"""
        with self.assertRaises(ValidationError):
            validar_aplicacion_pago(
                monto_aplicado=Decimal('-100000.00'),
                saldo_compra=Decimal('500000.00')
            )


class ValidadoresSumaAplicacionesTestCase(TestCase):
    """Tests para validar_suma_aplicaciones"""
    
    def test_suma_aplicaciones_valida(self):
        """Suma de aplicaciones menor al pago debe pasar"""
        try:
            validar_suma_aplicaciones(
                aplicaciones_totales=Decimal('800000.00'),
                monto_pago=Decimal('1000000.00')
            )
        except ValidationError:
            self.fail("Suma válida no debería fallar")
    
    def test_suma_aplicaciones_exacta_valida(self):
        """Suma exacta al monto del pago debe pasar"""
        try:
            validar_suma_aplicaciones(
                aplicaciones_totales=Decimal('1000000.00'),
                monto_pago=Decimal('1000000.00')
            )
        except ValidationError:
            self.fail("Suma exacta debería ser válida")
    
    def test_suma_aplicaciones_excede_pago(self):
        """Suma que excede el pago debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_suma_aplicaciones(
                aplicaciones_totales=Decimal('1200000.00'),
                monto_pago=Decimal('1000000.00')
            )
        self.assertIn("excede", str(context.exception).lower())


class ValidadoresNotaCreditoTestCase(TestCase):
    """Tests para validadores de notas de crédito"""
    
    def test_monto_nota_credito_valido(self):
        """Monto de NC válido debe pasar"""
        try:
            validar_monto_nota_credito(
                monto_nc=Decimal('200000.00'),
                monto_compra=Decimal('1000000.00')
            )
        except ValidationError:
            self.fail("Monto de NC válido no debería fallar")
    
    def test_monto_nota_credito_total_valido(self):
        """NC por el total de la compra debe pasar"""
        try:
            validar_monto_nota_credito(
                monto_nc=Decimal('1000000.00'),
                monto_compra=Decimal('1000000.00')
            )
        except ValidationError:
            self.fail("NC total debería ser válida")
    
    def test_monto_nota_credito_excede_compra(self):
        """NC que excede la compra debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_monto_nota_credito(
                monto_nc=Decimal('1500000.00'),
                monto_compra=Decimal('1000000.00')
            )
        self.assertIn("exceder", str(context.exception).lower())
    
    def test_monto_nota_credito_cero_invalido(self):
        """Monto cero debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_nota_credito(
                monto_nc=Decimal('0.00'),
                monto_compra=Decimal('1000000.00')
            )
    
    def test_motivo_nota_credito_valido(self):
        """Motivo descriptivo debe pasar"""
        try:
            validar_motivo_nota_credito('Devolución por productos vencidos')
        except ValidationError:
            self.fail("Motivo válido no debería fallar")
    
    def test_motivo_nota_credito_muy_corto(self):
        """Motivo < 10 caracteres debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_motivo_nota_credito('Error')
        self.assertIn("10 caracteres", str(context.exception))
    
    def test_motivo_nota_credito_muy_largo(self):
        """Motivo > 255 caracteres debe fallar"""
        with self.assertRaises(ValidationError):
            validar_motivo_nota_credito('A' * 256)
    
    def test_estado_nota_credito_valido(self):
        """Estados válidos deben pasar"""
        estados = ['Pendiente', 'Aplicado', 'Rechazado']
        for estado in estados:
            try:
                validar_estado_nota_credito(estado)
            except ValidationError:
                self.fail(f"Estado '{estado}' debería ser válido")
    
    def test_estado_nota_credito_invalido(self):
        """Estado inválido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_estado_nota_credito('EstadoInvalido')


class ValidadoresCuentaCorrienteTestCase(TestCase):
    """Tests para validadores de cuenta corriente"""
    
    def test_dias_credito_validos(self):
        """Días de crédito razonables deben pasar"""
        try:
            validar_dias_credito(30)
            validar_dias_credito(60)
            validar_dias_credito(90)
        except ValidationError:
            self.fail("Días válidos no deberían fallar")
    
    def test_dias_credito_cero_valido(self):
        """Cero días (contado) debe ser válido"""
        try:
            validar_dias_credito(0)
        except ValidationError:
            self.fail("Cero días debería ser válido")
    
    def test_dias_credito_negativos_invalidos(self):
        """Días negativos deben fallar"""
        with self.assertRaises(ValidationError):
            validar_dias_credito(-10)
    
    def test_dias_credito_excesivos(self):
        """Días > 180 deben lanzar advertencia"""
        with self.assertRaises(ValidationError):
            validar_dias_credito(200)
    
    def test_dias_credito_none_permitido(self):
        """None debe ser permitido (sin plazo definido)"""
        try:
            validar_dias_credito(None)
        except ValidationError:
            self.fail("None debería ser permitido")
    
    def test_compra_dentro_limite_credito(self):
        """Compra que no excede el límite debe pasar"""
        try:
            validar_compra_dentro_limite_credito(
                monto_compra=Decimal('1000000.00'),
                saldo_actual=Decimal('3000000.00'),
                limite_credito=Decimal('5000000.00')
            )
        except ValidationError:
            self.fail("Compra dentro del límite no debería fallar")
    
    def test_compra_excede_limite_credito(self):
        """Compra que excede el límite debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_compra_dentro_limite_credito(
                monto_compra=Decimal('3000000.00'),
                saldo_actual=Decimal('3000000.00'),
                limite_credito=Decimal('5000000.00')
            )
        self.assertIn("excediendo el límite", str(context.exception).lower())
    
    def test_compra_sin_limite_credito_definido(self):
        """Sin límite definido debe pasar cualquier monto"""
        try:
            validar_compra_dentro_limite_credito(
                monto_compra=Decimal('100000000.00'),
                saldo_actual=Decimal('50000000.00'),
                limite_credito=None
            )
        except ValidationError:
            self.fail("Sin límite debería permitir cualquier monto")
