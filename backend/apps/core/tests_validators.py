"""
Tests para validadores de la app Core

Este módulo contiene tests para todos los validadores de:
- Tarjetas (7 validadores)
- Tarjetas de Autorización (3 validadores)
- Cargas de Saldo (3 validadores)
- Consumos de Tarjeta (2 validadores)
- Transacciones Online (2 validadores)
- Medios de Pago (1 validador)
- Configuración del Sistema (4 validadores)
- Límites de Transacción (3 validadores)
- Registro de Autorizaciones (2 validadores)

Total: ~108 tests
"""

from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.core.validators import (  # Tarjetas; Tarjetas Autorización; Cargas Saldo; Consumos Tarjeta; Transacciones Online; Medios Pago; Configuración Sistema; Límites Transacción; Registro Autorizaciones
    validar_autorizadores_diferentes,
    validar_clave_configuracion,
    validar_codigo_barra_autorizacion,
    validar_codigo_barras_tarjeta,
    validar_descripcion_medio_pago,
    validar_estado_carga,
    validar_estado_tarjeta,
    validar_fecha_vencimiento_autorizacion,
    validar_fecha_vencimiento_tarjeta,
    validar_limite_credito,
    validar_metodo_pago_online,
    validar_monto_carga,
    validar_monto_consumo,
    validar_monto_limite,
    validar_monto_transaccion,
    validar_motivo_autorizacion,
    validar_numero_tarjeta,
    validar_referencia_pago,
    validar_saldo_alerta,
    validar_saldo_tarjeta,
    validar_saldos_coherentes,
    validar_tipo_autorizacion,
    validar_tipo_configuracion,
    validar_tipo_operacion_limite,
    validar_unicidad_rol_operacion,
    validar_valor_configuracion,
    validar_valores_permitidos,
)

# =============================================================================
# TESTS DE TARJETAS (7 validadores)
# =============================================================================


class ValidadoresNumeroTarjetaTestCase(TestCase):
    """Tests para validar_numero_tarjeta"""

    def test_numero_tarjeta_valido(self):
        """Números de tarjeta válidos no deberían generar error"""
        numeros_validos = [
            "TAR-001",
            "CARD-2024-001",
            "12345678",
            "ABC-DEF-123",
            "TARJETA-001",
        ]

        for numero in numeros_validos:
            try:
                validar_numero_tarjeta(numero)
            except ValidationError:  # pragma: no cover
                self.fail(f"Número de tarjeta válido '{numero}' generó ValidationError")

    def test_numero_tarjeta_vacio(self):
        """Número de tarjeta vacío debe fallar"""
        with self.assertRaises(ValidationError):
            validar_numero_tarjeta("")

        with self.assertRaises(ValidationError):
            validar_numero_tarjeta(None)

    def test_numero_tarjeta_muy_corto(self):
        """Número de tarjeta menor a 6 caracteres debe fallar"""
        with self.assertRaises(ValidationError):
            validar_numero_tarjeta("12345")

        with self.assertRaises(ValidationError):
            validar_numero_tarjeta("TAR")

    def test_numero_tarjeta_muy_largo(self):
        """Número de tarjeta mayor a 20 caracteres debe fallar"""
        with self.assertRaises(ValidationError):
            validar_numero_tarjeta("TARJETA-2024-0001-EXTRA-LONG")

    def test_numero_tarjeta_caracteres_invalidos(self):
        """Número de tarjeta con caracteres no permitidos debe fallar"""
        with self.assertRaises(ValidationError):
            validar_numero_tarjeta("TARJETA 001")  # Espacio

        with self.assertRaises(ValidationError):
            validar_numero_tarjeta("TARJETA@001")  # @

        with self.assertRaises(ValidationError):
            validar_numero_tarjeta("TARJETA#001")  # #

    def test_numero_tarjeta_con_guiones_extremos(self):
        """Número de tarjeta que empieza o termina con guion debe fallar"""
        with self.assertRaises(ValidationError):
            validar_numero_tarjeta("-TARJETA001")

        with self.assertRaises(ValidationError):
            validar_numero_tarjeta("TARJETA001-")


class ValidadoresSaldoTarjetaTestCase(TestCase):
    """Tests para validar_saldo_tarjeta"""

    def test_saldo_positivo_valido(self):
        """Saldo positivo válido no debe generar error"""
        try:
            validar_saldo_tarjeta(
                saldo_actual=Decimal("1000.00"),
                limite_credito=Decimal("500.00"),
                permite_negativo=False,
            )
        except ValidationError:  # pragma: no cover
            self.fail("Saldo positivo válido generó ValidationError")

    def test_saldo_negativo_permitido(self):
        """Saldo negativo dentro del límite de crédito debe ser válido"""
        try:
            validar_saldo_tarjeta(
                saldo_actual=Decimal("-300.00"),
                limite_credito=Decimal("500.00"),
                permite_negativo=True,
            )
        except ValidationError:  # pragma: no cover
            self.fail("Saldo negativo dentro del límite generó ValidationError")

    def test_saldo_negativo_no_permitido(self):
        """Saldo negativo cuando no se permite debe fallar"""
        with self.assertRaises(ValidationError):
            validar_saldo_tarjeta(
                saldo_actual=Decimal("-100.00"),
                limite_credito=Decimal("500.00"),
                permite_negativo=False,
            )

    def test_saldo_excede_limite_credito(self):
        """Saldo negativo que excede límite de crédito debe fallar"""
        with self.assertRaises(ValidationError):
            validar_saldo_tarjeta(
                saldo_actual=Decimal("-600.00"),
                limite_credito=Decimal("500.00"),
                permite_negativo=True,
            )

    def test_saldo_excede_maximo(self):
        """Saldo mayor a ₲10M debe fallar"""
        with self.assertRaises(ValidationError):
            validar_saldo_tarjeta(
                saldo_actual=Decimal("15000000.00"),
                limite_credito=Decimal("0.00"),
                permite_negativo=False,
            )


class ValidadoresEstadoTarjetaTestCase(TestCase):
    """Tests para validar_estado_tarjeta"""

    def test_estados_validos(self):
        """Estados válidos no deberían generar error"""
        estados_validos = ["Activa", "Bloqueada", "Vencida", "Cancelada", "Suspendida"]

        for estado in estados_validos:
            try:
                validar_estado_tarjeta(estado)
            except ValidationError:  # pragma: no cover
                self.fail(f"Estado válido '{estado}' generó ValidationError")

    def test_estado_invalido(self):
        """Estado no permitido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_estado_tarjeta("EnProceso")

        with self.assertRaises(ValidationError):
            validar_estado_tarjeta("Pendiente")

    def test_estado_vacio(self):
        """Estado vacío debe fallar"""
        with self.assertRaises(ValidationError):
            validar_estado_tarjeta("")

        with self.assertRaises(ValidationError):
            validar_estado_tarjeta(None)


class ValidadoresCodigoBarrasTarjetaTestCase(TestCase):
    """Tests para validar_codigo_barras_tarjeta"""

    def test_codigo_barras_ean13_valido(self):
        """Código EAN-13 válido no debe generar error"""
        try:
            validar_codigo_barras_tarjeta("1234567890123")
        except ValidationError:  # pragma: no cover
            self.fail("Código EAN-13 válido generó ValidationError")

    def test_codigo_barras_ean8_valido(self):
        """Código EAN-8 válido no debe generar error"""
        try:
            validar_codigo_barras_tarjeta("12345678")
        except ValidationError:  # pragma: no cover
            self.fail("Código EAN-8 válido generó ValidationError")

    def test_codigo_barras_alfanumerico_valido(self):
        """Código alfanumérico válido no debe generar error"""
        try:
            validar_codigo_barras_tarjeta("CARD-2024-001")
        except ValidationError:  # pragma: no cover
            self.fail("Código alfanumérico válido generó ValidationError")

    def test_codigo_barras_muy_corto(self):
        """Código menor a 8 caracteres debe fallar"""
        with self.assertRaises(ValidationError):
            validar_codigo_barras_tarjeta("1234567")

    def test_codigo_barras_muy_largo(self):
        """Código mayor a 50 caracteres debe fallar"""
        with self.assertRaises(ValidationError):
            validar_codigo_barras_tarjeta("1" * 51)

    def test_codigo_barras_numerico_longitud_invalida(self):
        """Código numérico que no sea 8 o 13 dígitos debe fallar"""
        with self.assertRaises(ValidationError):
            validar_codigo_barras_tarjeta("1234567890")  # 10 dígitos

    def test_codigo_barras_caracteres_invalidos(self):
        """Código con caracteres no permitidos debe fallar"""
        with self.assertRaises(ValidationError):
            validar_codigo_barras_tarjeta("CARD@2024#001")


class ValidadoresFechaVencimientoTarjetaTestCase(TestCase):
    """Tests para validar_fecha_vencimiento_tarjeta"""

    def test_fecha_vencimiento_futura_valida(self):
        """Fecha de vencimiento futura válida no debe generar error"""
        fecha_futura = date.today() + timedelta(days=365)
        try:
            validar_fecha_vencimiento_tarjeta(fecha_futura)
        except ValidationError as e:
            if e.code != "warning":  # Permitir warning pero no error
                self.fail(f"Fecha futura válida generó ValidationError: {e}")

    def test_fecha_vencimiento_en_pasado(self):
        """Fecha de vencimiento en el pasado debe fallar"""
        fecha_pasada = date.today() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            validar_fecha_vencimiento_tarjeta(fecha_pasada)

    def test_fecha_vencimiento_muy_futura(self):
        """Fecha mayor a 10 años en el futuro debe fallar"""
        fecha_muy_futura = date.today() + timedelta(days=3700)
        with self.assertRaises(ValidationError):
            validar_fecha_vencimiento_tarjeta(fecha_muy_futura)

    def test_fecha_vencimiento_proxima_warning(self):
        """Fecha que vence en menos de 30 días debe generar warning"""
        fecha_proxima = date.today() + timedelta(days=15)
        with self.assertRaises(ValidationError) as context:
            validar_fecha_vencimiento_tarjeta(fecha_proxima)

        self.assertEqual(context.exception.code, "warning")


class ValidadoresLimiteCreditoTestCase(TestCase):
    """Tests para validar_limite_credito"""

    def test_limite_credito_valido(self):
        """Límite de crédito válido no debe generar error"""
        try:
            validar_limite_credito(Decimal("1000.00"))
        except ValidationError:  # pragma: no cover
            self.fail("Límite de crédito válido generó ValidationError")

    def test_limite_credito_cero_valido(self):
        """Límite de crédito cero es válido"""
        try:
            validar_limite_credito(Decimal("0.00"))
        except ValidationError:  # pragma: no cover
            self.fail("Límite cero generó ValidationError")

    def test_limite_credito_negativo(self):
        """Límite de crédito negativo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_limite_credito(Decimal("-100.00"))

    def test_limite_credito_excede_maximo(self):
        """Límite mayor a ₲5M debe fallar"""
        with self.assertRaises(ValidationError):
            validar_limite_credito(Decimal("6000000.00"))

    def test_limite_credito_demasiados_decimales(self):
        """Límite con más de 2 decimales debe fallar"""
        with self.assertRaises(ValidationError):
            validar_limite_credito(Decimal("1000.123"))


class ValidadoresSaldoAlertaTestCase(TestCase):
    """Tests para validar_saldo_alerta"""

    def test_saldo_alerta_valido(self):
        """Saldo de alerta válido no debe generar error"""
        try:
            validar_saldo_alerta(saldo_alerta=Decimal("100.00"), saldo_actual=Decimal("1000.00"))
        except ValidationError as e:
            if e.code != "warning":
                self.fail(f"Saldo alerta válido generó error: {e}")

    def test_saldo_alerta_cero(self):
        """Saldo de alerta cero o negativo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_saldo_alerta(saldo_alerta=Decimal("0.00"), saldo_actual=Decimal("1000.00"))

    def test_saldo_alerta_excede_maximo(self):
        """Saldo de alerta mayor a ₲1M debe fallar"""
        with self.assertRaises(ValidationError):
            validar_saldo_alerta(saldo_alerta=Decimal("1500000.00"), saldo_actual=Decimal("2000000.00"))

    def test_saldo_alerta_mayor_igual_saldo_actual(self):
        """Saldo de alerta >= saldo actual debe generar warning"""
        with self.assertRaises(ValidationError) as context:
            validar_saldo_alerta(saldo_alerta=Decimal("1500.00"), saldo_actual=Decimal("1000.00"))

        self.assertEqual(context.exception.code, "warning")


# =============================================================================
# TESTS DE TARJETAS DE AUTORIZACIÓN (3 validadores)
# =============================================================================


class ValidadoresCodigoBarraAutorizacionTestCase(TestCase):
    """Tests para validar_codigo_barra_autorizacion"""

    def test_codigo_barra_autorizacion_valido(self):
        """Código de barras válido no debe generar error"""
        try:
            validar_codigo_barra_autorizacion("AUTH-2024-001")
        except ValidationError:  # pragma: no cover
            self.fail("Código válido generó ValidationError")

    def test_codigo_barra_autorizacion_vacio(self):
        """Código vacío debe fallar"""
        with self.assertRaises(ValidationError):
            validar_codigo_barra_autorizacion("")

        with self.assertRaises(ValidationError):
            validar_codigo_barra_autorizacion(None)

    def test_codigo_barra_autorizacion_muy_corto(self):
        """Código menor a 8 caracteres debe fallar"""
        with self.assertRaises(ValidationError):
            validar_codigo_barra_autorizacion("AUTH01")

    def test_codigo_barra_autorizacion_muy_largo(self):
        """Código mayor a 50 caracteres debe fallar"""
        with self.assertRaises(ValidationError):
            validar_codigo_barra_autorizacion("A" * 51)


class ValidadoresTipoAutorizacionTestCase(TestCase):
    """Tests para validar_tipo_autorizacion"""

    def test_tipos_autorizacion_validos(self):
        """Tipos de autorización válidos no deberían generar error"""
        tipos_validos = ["Supervisor", "Gerente", "Director", "Temporal"]

        for tipo in tipos_validos:
            try:
                validar_tipo_autorizacion(tipo)
            except ValidationError:  # pragma: no cover
                self.fail(f"Tipo válido '{tipo}' generó ValidationError")

    def test_tipo_autorizacion_invalido(self):
        """Tipo de autorización no permitido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_tipo_autorizacion("Empleado")

        with self.assertRaises(ValidationError):
            validar_tipo_autorizacion("Administrador")

    def test_tipo_autorizacion_vacio(self):
        """Tipo vacío debe fallar"""
        with self.assertRaises(ValidationError):
            validar_tipo_autorizacion("")


class ValidadoresFechaVencimientoAutorizacionTestCase(TestCase):
    """Tests para validar_fecha_vencimiento_autorizacion"""

    def test_fecha_vencimiento_temporal_obligatoria(self):
        """Autorización temporal debe requerir fecha de vencimiento"""
        with self.assertRaises(ValidationError):
            validar_fecha_vencimiento_autorizacion(None, "Temporal")

    def test_fecha_vencimiento_permanente_opcional(self):
        """Autorización permanente no requiere fecha de vencimiento"""
        try:
            validar_fecha_vencimiento_autorizacion(None, "Supervisor")
        except ValidationError:  # pragma: no cover
            self.fail("Fecha opcional para tipo permanente generó error")

    def test_fecha_vencimiento_futura_valida(self):
        """Fecha futura válida no debe generar error"""
        fecha_futura = date.today() + timedelta(days=30)
        try:
            validar_fecha_vencimiento_autorizacion(fecha_futura, "Temporal")
        except ValidationError:  # pragma: no cover
            self.fail("Fecha futura válida generó ValidationError")

    def test_fecha_vencimiento_pasada(self):
        """Fecha en el pasado debe fallar"""
        fecha_pasada = date.today() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            validar_fecha_vencimiento_autorizacion(fecha_pasada, "Temporal")

    def test_fecha_vencimiento_muy_futura(self):
        """Fecha mayor a 2 años debe fallar"""
        fecha_muy_futura = date.today() + timedelta(days=800)
        with self.assertRaises(ValidationError):
            validar_fecha_vencimiento_autorizacion(fecha_muy_futura, "Temporal")


# =============================================================================
# TESTS DE CARGAS DE SALDO (3 validadores)
# =============================================================================


class ValidadoresMontoCargaTestCase(TestCase):
    """Tests para validar_monto_carga"""

    def test_monto_carga_valido(self):
        """Monto de carga válido no debe generar error"""
        try:
            validar_monto_carga(Decimal("50000.00"))
        except ValidationError:  # pragma: no cover
            self.fail("Monto válido generó ValidationError")

    def test_monto_carga_cero(self):
        """Monto cero debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_carga(Decimal("0.00"))

    def test_monto_carga_negativo(self):
        """Monto negativo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_carga(Decimal("-1000.00"))

    def test_monto_carga_excede_maximo(self):
        """Monto mayor a ₲10M debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_carga(Decimal("15000000.00"))

    def test_monto_carga_demasiados_decimales(self):
        """Monto con más de 2 decimales debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_carga(Decimal("1000.123"))


class ValidadoresEstadoCargaTestCase(TestCase):
    """Tests para validar_estado_carga"""

    def test_estados_carga_validos(self):
        """Estados de carga válidos no deberían generar error"""
        estados_validos = ["Pendiente", "Confirmado", "Rechazado", "Cancelado", "Reembolsado"]

        for estado in estados_validos:
            try:
                validar_estado_carga(estado)
            except ValidationError:  # pragma: no cover
                self.fail(f"Estado válido '{estado}' generó ValidationError")

    def test_estado_carga_invalido(self):
        """Estado no permitido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_estado_carga("EnProceso")

    def test_estado_carga_vacio(self):
        """Estado vacío debe fallar"""
        with self.assertRaises(ValidationError):
            validar_estado_carga("")


class ValidadoresReferenciaPagoTestCase(TestCase):
    """Tests para validar_referencia_pago"""

    def test_referencia_pago_valida(self):
        """Referencia de pago válida no debe generar error"""
        try:
            validar_referencia_pago("REF-2024-001")
        except ValidationError:  # pragma: no cover
            self.fail("Referencia válida generó ValidationError")

    def test_referencia_pago_muy_corta(self):
        """Referencia menor a 5 caracteres debe fallar"""
        with self.assertRaises(ValidationError):
            validar_referencia_pago("REF1")

    def test_referencia_pago_muy_larga(self):
        """Referencia mayor a 100 caracteres debe fallar"""
        with self.assertRaises(ValidationError):
            validar_referencia_pago("R" * 101)

    def test_referencia_pago_caracteres_invalidos(self):
        """Referencia con caracteres no permitidos debe fallar"""
        with self.assertRaises(ValidationError):
            validar_referencia_pago("REF@2024#001")


# =============================================================================
# TESTS DE CONSUMOS DE TARJETA (2 validadores)
# =============================================================================


class ValidadoresMontoConsumoTestCase(TestCase):
    """Tests para validar_monto_consumo"""

    def test_monto_consumo_valido(self):
        """Monto de consumo válido no debe generar error"""
        try:
            validar_monto_consumo(Decimal("15000.00"))
        except ValidationError:  # pragma: no cover
            self.fail("Monto válido generó ValidationError")

    def test_monto_consumo_cero(self):
        """Monto cero debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_consumo(Decimal("0.00"))

    def test_monto_consumo_negativo(self):
        """Monto negativo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_consumo(Decimal("-500.00"))

    def test_monto_consumo_excede_maximo(self):
        """Monto mayor a ₲1M debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_consumo(Decimal("1500000.00"))


class ValidadoresSaldosCoherentesTestCase(TestCase):
    """Tests para validar_saldos_coherentes"""

    def test_saldos_coherentes_exactos(self):
        """Saldos exactamente coherentes no deben generar error"""
        try:
            validar_saldos_coherentes(
                saldo_anterior=Decimal("1000.00"),
                saldo_posterior=Decimal("500.00"),
                monto_consumido=Decimal("500.00"),
            )
        except ValidationError:  # pragma: no cover
            self.fail("Saldos coherentes generaron ValidationError")

    def test_saldos_coherentes_con_tolerancia(self):
        """Saldos con diferencia <= ₱0.02 deben ser válidos"""
        try:
            validar_saldos_coherentes(
                saldo_anterior=Decimal("1000.00"),
                saldo_posterior=Decimal("499.99"),
                monto_consumido=Decimal("500.00"),
            )
        except ValidationError:  # pragma: no cover
            self.fail("Saldos dentro de tolerancia generaron ValidationError")

    def test_saldos_incoherentes(self):
        """Saldos con diferencia > ₱0.02 deben fallar"""
        with self.assertRaises(ValidationError):
            validar_saldos_coherentes(
                saldo_anterior=Decimal("1000.00"),
                saldo_posterior=Decimal("400.00"),
                monto_consumido=Decimal("500.00"),
            )


# =============================================================================
# TESTS DE TRANSACCIONES ONLINE (2 validadores)
# =============================================================================


class ValidadoresMontoTransaccionTestCase(TestCase):
    """Tests para validar_monto_transaccion"""

    def test_monto_transaccion_valido(self):
        """Monto de transacción válido no debe generar error"""
        try:
            validar_monto_transaccion(Decimal("100000.00"))
        except ValidationError:  # pragma: no cover
            self.fail("Monto válido generó ValidationError")

    def test_monto_transaccion_cero(self):
        """Monto cero debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_transaccion(Decimal("0.00"))

    def test_monto_transaccion_excede_maximo(self):
        """Monto mayor a ₲10M debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_transaccion(Decimal("15000000.00"))


class ValidadoresMetodoPagoOnlineTestCase(TestCase):
    """Tests para validar_metodo_pago_online"""

    def test_metodos_pago_validos(self):
        """Métodos de pago válidos no deberían generar error"""
        metodos_validos = ["tarjeta_credito", "tarjeta_debito", "transferencia", "qr", "billetera"]

        for metodo in metodos_validos:
            try:
                validar_metodo_pago_online(metodo)
            except ValidationError:  # pragma: no cover
                self.fail(f"Método válido '{metodo}' generó ValidationError")

    def test_metodo_pago_invalido(self):
        """Método de pago no permitido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_metodo_pago_online("efectivo")

        with self.assertRaises(ValidationError):
            validar_metodo_pago_online("cheque")

    def test_metodo_pago_vacio(self):
        """Método vacío debe fallar"""
        with self.assertRaises(ValidationError):
            validar_metodo_pago_online("")


# =============================================================================
# TESTS DE MEDIOS DE PAGO (1 validador)
# =============================================================================


class ValidadoresDescripcionMedioPagoTestCase(TestCase):
    """Tests para validar_descripcion_medio_pago"""

    def test_descripcion_medio_pago_valida(self):
        """Descripción válida no debe generar error"""
        try:
            validar_descripcion_medio_pago("Efectivo")
        except ValidationError:  # pragma: no cover
            self.fail("Descripción válida generó ValidationError")

    def test_descripcion_medio_pago_muy_corta(self):
        """Descripción menor a 3 caracteres debe fallar"""
        with self.assertRaises(ValidationError):
            validar_descripcion_medio_pago("EF")

    def test_descripcion_medio_pago_muy_larga(self):
        """Descripción mayor a 50 caracteres debe fallar"""
        with self.assertRaises(ValidationError):
            validar_descripcion_medio_pago("M" * 51)

    def test_descripcion_medio_pago_vacia(self):
        """Descripción vacía debe fallar"""
        with self.assertRaises(ValidationError):
            validar_descripcion_medio_pago("")


# =============================================================================
# TESTS DE CONFIGURACIÓN DEL SISTEMA (4 validadores)
# =============================================================================


class ValidadoresClaveConfiguracionTestCase(TestCase):
    """Tests para validar_clave_configuracion"""

    def test_clave_configuracion_valida(self):
        """Clave en snake_case válida no debe generar error"""
        claves_validas = [
            "max_intentos_login",
            "tiempo_sesion",
            "api_key_externa",
            "notificacion_saldo_bajo",
        ]

        for clave in claves_validas:
            try:
                validar_clave_configuracion(clave)
            except ValidationError:  # pragma: no cover
                self.fail(f"Clave válida '{clave}' generó ValidationError")

    def test_clave_configuracion_mayusculas(self):
        """Clave con mayúsculas debe fallar"""
        with self.assertRaises(ValidationError):
            validar_clave_configuracion("MaxIntentosLogin")

    def test_clave_configuracion_guiones(self):
        """Clave con guiones (kebab-case) debe fallar"""
        with self.assertRaises(ValidationError):
            validar_clave_configuracion("max-intentos-login")

    def test_clave_configuracion_muy_corta(self):
        """Clave menor a 3 caracteres debe fallar"""
        with self.assertRaises(ValidationError):
            validar_clave_configuracion("ab")

    def test_clave_configuracion_guion_bajo_extremos(self):
        """Clave que empieza/termina con _ debe fallar"""
        with self.assertRaises(ValidationError):
            validar_clave_configuracion("_clave")

        with self.assertRaises(ValidationError):
            validar_clave_configuracion("clave_")


class ValidadoresTipoConfiguracionTestCase(TestCase):
    """Tests para validar_tipo_configuracion"""

    def test_tipos_configuracion_validos(self):
        """Tipos de configuración válidos no deberían generar error"""
        tipos_validos = ["string", "int", "decimal", "bool", "json", "email", "url", "date"]

        for tipo in tipos_validos:
            try:
                validar_tipo_configuracion(tipo)
            except ValidationError:  # pragma: no cover
                self.fail(f"Tipo válido '{tipo}' generó ValidationError")

    def test_tipo_configuracion_invalido(self):
        """Tipo no permitido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_tipo_configuracion("float")

        with self.assertRaises(ValidationError):
            validar_tipo_configuracion("array")

    def test_tipo_configuracion_vacio(self):
        """Tipo vacío debe fallar"""
        with self.assertRaises(ValidationError):
            validar_tipo_configuracion("")


class ValidadoresValorConfiguracionTestCase(TestCase):
    """Tests para validar_valor_configuracion"""

    def test_valor_int_valido(self):
        """Valor entero válido no debe generar error"""
        try:
            validar_valor_configuracion("5", "int", valor_min="1", valor_max="10")
        except ValidationError:  # pragma: no cover
            self.fail("Valor int válido generó ValidationError")

    def test_valor_int_fuera_rango(self):
        """Valor entero fuera de rango debe fallar"""
        with self.assertRaises(ValidationError):
            validar_valor_configuracion("15", "int", valor_min="1", valor_max="10")

    def test_valor_decimal_valido(self):
        """Valor decimal válido no debe generar error"""
        try:
            validar_valor_configuracion("5.50", "decimal", valor_min="0", valor_max="10")
        except ValidationError:  # pragma: no cover
            self.fail("Valor decimal válido generó ValidationError")

    def test_valor_bool_valido(self):
        """Valores booleanos válidos no deberían generar error"""
        valores_validos = ["true", "false", "1", "0"]

        for valor in valores_validos:
            try:
                validar_valor_configuracion(valor, "bool")
            except ValidationError:  # pragma: no cover
                self.fail(f"Valor bool válido '{valor}' generó ValidationError")

    def test_valor_bool_invalido(self):
        """Valor booleano inválido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_valor_configuracion("yes", "bool")

    def test_valor_email_valido(self):
        """Email válido no debe generar error"""
        try:
            validar_valor_configuracion("usuario@example.com", "email")
        except ValidationError:  # pragma: no cover
            self.fail("Email válido generó ValidationError")

    def test_valor_email_invalido(self):
        """Email inválido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_valor_configuracion("usuario@", "email")

    def test_valor_url_valida(self):
        """URL válida no debe generar error"""
        try:
            validar_valor_configuracion("https://example.com/api", "url")
        except ValidationError:  # pragma: no cover
            self.fail("URL válida generó ValidationError")

    def test_valor_url_invalida(self):
        """URL inválida debe fallar"""
        with self.assertRaises(ValidationError):
            validar_valor_configuracion("not-a-url", "url")

    def test_valor_date_valida(self):
        """Fecha válida no debe generar error"""
        try:
            validar_valor_configuracion("2024-03-01", "date")
        except ValidationError:  # pragma: no cover
            self.fail("Fecha válida generó ValidationError")

    def test_valor_date_invalida(self):
        """Fecha inválida debe fallar"""
        with self.assertRaises(ValidationError):
            validar_valor_configuracion("01/03/2024", "date")

    def test_valor_en_lista_permitidos(self):
        """Valor en lista de valores permitidos debe ser válido"""
        try:
            validar_valor_configuracion("opcion1", "string", valores_permitidos=["opcion1", "opcion2", "opcion3"])
        except ValidationError:  # pragma: no cover
            self.fail("Valor en lista permitidos generó ValidationError")

    def test_valor_fuera_lista_permitidos(self):
        """Valor fuera de lista de valores permitidos debe fallar"""
        with self.assertRaises(ValidationError):
            validar_valor_configuracion("opcion4", "string", valores_permitidos=["opcion1", "opcion2", "opcion3"])


class ValidadoresValoresPermitidosTestCase(TestCase):
    """Tests para validar_valores_permitidos"""

    def test_valores_permitidos_lista_valida(self):
        """Lista válida no debe generar error"""
        try:
            validar_valores_permitidos(["valor1", "valor2", "valor3"], "string")
        except ValidationError:  # pragma: no cover
            self.fail("Lista válida generó ValidationError")

    def test_valores_permitidos_no_lista(self):
        """Valores permitidos que no son lista deben fallar"""
        with self.assertRaises(ValidationError):
            validar_valores_permitidos("valor1,valor2", "string")

    def test_valores_permitidos_demasiados(self):
        """Lista con más de 100 elementos debe fallar"""
        with self.assertRaises(ValidationError):
            validar_valores_permitidos(["valor" + str(i) for i in range(101)], "string")


# =============================================================================
# TESTS DE LÍMITES DE TRANSACCIÓN (3 validadores)
# =============================================================================


class ValidadoresTipoOperacionLimiteTestCase(TestCase):
    """Tests para validar_tipo_operacion_limite"""

    def test_tipos_operacion_validos(self):
        """Tipos de operación válidos no deberían generar error"""
        tipos_validos = [
            "venta",
            "descuento",
            "nota_credito_cliente",
            "nota_credito_proveedor",
            "ajuste_inventario",
            "exceder_credito",
            "anular_venta",
            "retiro_caja",
            "devolucion",
        ]

        for tipo in tipos_validos:
            try:
                validar_tipo_operacion_limite(tipo)
            except ValidationError:  # pragma: no cover
                self.fail(f"Tipo válido '{tipo}' generó ValidationError")

    def test_tipo_operacion_invalido(self):
        """Tipo de operación no permitido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_tipo_operacion_limite("compra")

    def test_tipo_operacion_vacio(self):
        """Tipo vacío debe fallar"""
        with self.assertRaises(ValidationError):
            validar_tipo_operacion_limite("")


class ValidadoresMontoLimiteTestCase(TestCase):
    """Tests para validar_monto_limite"""

    def test_monto_limite_valido(self):
        """Monto límite válido no debe generar error"""
        try:
            validar_monto_limite(Decimal("500000.00"))
        except ValidationError:  # pragma: no cover
            self.fail("Monto válido generó ValidationError")

    def test_monto_limite_cero(self):
        """Monto límite cero debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_limite(Decimal("0.00"))

    def test_monto_limite_negativo(self):
        """Monto límite negativo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_limite(Decimal("-1000.00"))

    def test_monto_limite_excede_maximo(self):
        """Monto mayor a ₲100M debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_limite(Decimal("150000000.00"))


class ValidadoresUnicidadRolOperacionTestCase(TestCase):
    """Tests para validar_unicidad_rol_operacion"""

    def setUp(self):
        """Configurar datos de prueba"""
        from datetime import datetime

        from apps.core.models import LimitesTransaccion
        from apps.usuarios.models import Roles

        # Crear rol de prueba
        self.rol = Roles.objects.create(
            nombre_rol="Cajero",
            descripcion="Rol de cajero",
            estado=True,
            fecha_creacion=datetime.now(),
        )

        # Crear límite existente
        self.limite = LimitesTransaccion.objects.create(
            id_rol=self.rol,
            tipo_operacion="venta",
            monto_maximo_sin_autorizacion=Decimal("100000.00"),
            estado=True,
        )

    def test_unicidad_nuevo_limite_diferente_operacion(self):
        """Nuevo límite con diferente operación no debe fallar"""
        try:
            validar_unicidad_rol_operacion(id_rol=self.rol, tipo_operacion="descuento", id_limite_actual=None)
        except ValidationError:  # pragma: no cover
            self.fail("Límite con diferente operación generó ValidationError")

    def test_unicidad_limite_duplicado(self):
        """Nuevo límite con misma combinación rol-operación debe fallar"""
        with self.assertRaises(ValidationError):
            validar_unicidad_rol_operacion(id_rol=self.rol, tipo_operacion="venta", id_limite_actual=None)

    def test_unicidad_editar_mismo_limite(self):
        """Editar el mismo límite no debe generar error"""
        try:
            validar_unicidad_rol_operacion(
                id_rol=self.rol, tipo_operacion="venta", id_limite_actual=self.limite.id_limite
            )
        except ValidationError:  # pragma: no cover
            self.fail("Editar mismo límite generó ValidationError")


# =============================================================================
# TESTS DE REGISTRO DE AUTORIZACIONES (2 validadores)
# =============================================================================


class ValidadoresMotivoAutorizacionTestCase(TestCase):
    """Tests para validar_motivo_autorizacion"""

    def test_motivo_autorizacion_valido(self):
        """Motivo válido no debe generar error"""
        try:
            validar_motivo_autorizacion("Cliente especial requiere descuento por volumen de compras recurrentes")
        except ValidationError:  # pragma: no cover
            self.fail("Motivo válido generó ValidationError")

    def test_motivo_autorizacion_muy_corto(self):
        """Motivo menor a 10 caracteres debe fallar"""
        with self.assertRaises(ValidationError):
            validar_motivo_autorizacion("Cliente VIP")

    def test_motivo_autorizacion_muy_largo(self):
        """Motivo mayor a 500 caracteres debe fallar"""
        with self.assertRaises(ValidationError):
            validar_motivo_autorizacion("M" * 501)

    def test_motivo_autorizacion_vacio(self):
        """Motivo vacío debe fallar"""
        with self.assertRaises(ValidationError):
            validar_motivo_autorizacion("")


class ValidadoresAutorizadoresDiferentesTestCase(TestCase):
    """Tests para validar_autorizadores_diferentes"""

    def setUp(self):
        """Configurar empleados de prueba"""
        from datetime import date

        from apps.usuarios.models import Empleados

        self.empleado1 = Empleados.objects.create(
            nombre="Juan", apellido="Pérez", email="juan@example.com", fecha_ingreso=date.today()
        )

        self.empleado2 = Empleados.objects.create(
            nombre="María",
            apellido="González",
            email="maria@example.com",
            fecha_ingreso=date.today(),
        )

        self.empleado3 = Empleados.objects.create(
            nombre="Carlos",
            apellido="Rodríguez",
            email="carlos@example.com",
            fecha_ingreso=date.today(),
        )

    def test_autorizadores_diferentes_validos(self):
        """Autorizadores diferentes no deben generar error"""
        try:
            validar_autorizadores_diferentes(
                id_empleado_solicitante=self.empleado1,
                id_empleado_autorizador=self.empleado2,
                id_empleado_autorizador_2=self.empleado3,
            )
        except ValidationError:  # pragma: no cover
            self.fail("Autorizadores diferentes generaron ValidationError")

    def test_autorizador_igual_solicitante(self):
        """Autorizador igual a solicitante debe fallar"""
        with self.assertRaises(ValidationError):
            validar_autorizadores_diferentes(
                id_empleado_solicitante=self.empleado1, id_empleado_autorizador=self.empleado1
            )

    def test_autorizadores_iguales_doble_autorizacion(self):
        """Dos autorizadores iguales debe fallar"""
        with self.assertRaises(ValidationError):
            validar_autorizadores_diferentes(
                id_empleado_solicitante=self.empleado1,
                id_empleado_autorizador=self.empleado2,
                id_empleado_autorizador_2=self.empleado2,
            )

    def test_segundo_autorizador_igual_solicitante(self):
        """Segundo autorizador igual a solicitante debe fallar"""
        with self.assertRaises(ValidationError):
            validar_autorizadores_diferentes(
                id_empleado_solicitante=self.empleado1,
                id_empleado_autorizador=self.empleado2,
                id_empleado_autorizador_2=self.empleado1,
            )
