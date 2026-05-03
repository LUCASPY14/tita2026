"""
Tests para validadores del módulo Almuerzos
Cobertura completa de 30 validadores con casos positivos, negativos y edge cases
"""

from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from .validators import *

# ==============================================================================
# TESTS PARA PLANES DE ALMUERZO
# ==============================================================================


class ValidarNombrePlanTest(TestCase):
    """Tests para validar_nombre_plan"""

    def test_nombre_plan_valido(self):
        """Nombre válido debe pasar"""
        validar_nombre_plan("Plan Básico")
        validar_nombre_plan("Plan Completo 2024")
        validar_nombre_plan("Plan Premium (L-V)")

    def test_nombre_plan_vacio(self):
        """Nombre vacío debe fallar"""
        with self.assertRaises(ValidationError):
            validar_nombre_plan("")
        with self.assertRaises(ValidationError):
            validar_nombre_plan(None)

    def test_nombre_plan_muy_corto(self):
        """Nombre muy corto debe fallar"""
        with self.assertRaises(ValidationError):
            validar_nombre_plan("AB")

    def test_nombre_plan_muy_largo(self):
        """Nombre muy largo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_nombre_plan("A" * 101)

    def test_nombre_plan_caracteres_invalidos(self):
        """Caracteres no permitidos deben fallar"""
        with self.assertRaises(ValidationError):
            validar_nombre_plan("Plan Básico @#$")


class ValidarDescripcionPlanTest(TestCase):
    """Tests para validar_descripcion_plan"""

    def test_descripcion_valida(self):
        """Descripción válida debe pasar"""
        validar_descripcion_plan("Incluye almuerzo de lunes a viernes")
        validar_descripcion_plan(None)  # Opcional
        validar_descripcion_plan("")  # Opcional

    def test_descripcion_muy_larga(self):
        """Descripción muy larga debe fallar"""
        with self.assertRaises(ValidationError):
            validar_descripcion_plan("A" * 501)


class ValidarPrecioMensualPlanTest(TestCase):
    """Tests para validar_precio_mensual_plan"""

    def test_precio_valido(self):
        """Precio válido debe pasar"""
        validar_precio_mensual_plan(Decimal("100000.00"))
        validar_precio_mensual_plan(Decimal("1500.50"))

    def test_precio_cero(self):
        """Precio cero debe fallar"""
        with self.assertRaises(ValidationError):
            validar_precio_mensual_plan(Decimal("0.00"))

    def test_precio_negativo(self):
        """Precio negativo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_precio_mensual_plan(Decimal("-100.00"))

    def test_precio_excesivo(self):
        """Precio excesivo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_precio_mensual_plan(Decimal("5000001.00"))

    def test_precio_muchos_decimales(self):
        """Más de 2 decimales debe fallar"""
        with self.assertRaises(ValidationError):
            validar_precio_mensual_plan(Decimal("100.999"))

    def test_precio_none(self):
        """Precio None debe fallar"""
        with self.assertRaises(ValidationError):
            validar_precio_mensual_plan(None)


class ValidarDiasSemanaIncluidosTest(TestCase):
    """Tests para validar_dias_semana_incluidos"""

    def test_dias_validos(self):
        """Días válidos deben pasar"""
        validar_dias_semana_incluidos("L,M,Mi,J,V")
        validar_dias_semana_incluidos("L-V")
        validar_dias_semana_incluidos("Lunes, Miércoles, Viernes")

    def test_dias_vacios(self):
        """Días vacíos deben fallar"""
        with self.assertRaises(ValidationError):
            validar_dias_semana_incluidos("")
        with self.assertRaises(ValidationError):
            validar_dias_semana_incluidos(None)

    def test_dias_muy_largos(self):
        """Días muy largos deben fallar"""
        with self.assertRaises(ValidationError):
            validar_dias_semana_incluidos("A" * 61)

    def test_dias_sin_dia_valido(self):
        """Sin día válido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_dias_semana_incluidos("XYZ123")


# ==============================================================================
# TESTS PARA TIPOS DE ALMUERZO
# ==============================================================================


class ValidarNombreTipoAlmuerzoTest(TestCase):
    """Tests para validar_nombre_tipo_almuerzo"""

    def test_nombre_tipo_valido(self):
        """Nombre válido debe pasar"""
        validar_nombre_tipo_almuerzo("Almuerzo Completo")
        validar_nombre_tipo_almuerzo("Menú Ejecutivo")

    def test_nombre_tipo_vacio(self):
        """Nombre vacío debe fallar"""
        with self.assertRaises(ValidationError):
            validar_nombre_tipo_almuerzo("")

    def test_nombre_tipo_muy_corto(self):
        """Nombre muy corto debe fallar"""
        with self.assertRaises(ValidationError):
            validar_nombre_tipo_almuerzo("AB")

    def test_nombre_tipo_muy_largo(self):
        """Nombre muy largo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_nombre_tipo_almuerzo("A" * 101)

    def test_nombre_tipo_caracteres_invalidos(self):
        """Caracteres no permitidos deben fallar"""
        with self.assertRaises(ValidationError):
            validar_nombre_tipo_almuerzo("Tipo @#$")


class ValidarPrecioUnitarioTipoTest(TestCase):
    """Tests para validar_precio_unitario_tipo"""

    def test_precio_unitario_valido(self):
        """Precio válido debe pasar"""
        validar_precio_unitario_tipo(Decimal("15000.00"))
        validar_precio_unitario_tipo(Decimal("35000.50"))

    def test_precio_unitario_cero(self):
        """Precio cero debe fallar"""
        with self.assertRaises(ValidationError):
            validar_precio_unitario_tipo(Decimal("0.00"))

    def test_precio_unitario_negativo(self):
        """Precio negativo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_precio_unitario_tipo(Decimal("-100.00"))

    def test_precio_unitario_excesivo(self):
        """Precio excesivo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_precio_unitario_tipo(Decimal("500001.00"))

    def test_precio_unitario_muchos_decimales(self):
        """Más de 2 decimales debe fallar"""
        with self.assertRaises(ValidationError):
            validar_precio_unitario_tipo(Decimal("100.999"))


# ==============================================================================
# TESTS PARA SUSCRIPCIONES
# ==============================================================================


class ValidarFechaInicioSuscripcionTest(TestCase):
    """Tests para validar_fecha_inicio_suscripcion"""

    def test_fecha_inicio_valida(self):
        """Fecha válida debe pasar"""
        validar_fecha_inicio_suscripcion(date(2024, 1, 1))
        validar_fecha_inicio_suscripcion(date.today())

    def test_fecha_inicio_string_valida(self):
        """Fecha como string válida debe pasar"""
        validar_fecha_inicio_suscripcion("2024-03-01")

    def test_fecha_inicio_muy_antigua(self):
        """Fecha muy antigua debe fallar"""
        with self.assertRaises(ValidationError):
            validar_fecha_inicio_suscripcion(date(2019, 12, 31))

    def test_fecha_inicio_muy_futura(self):
        """Fecha muy futura debe fallar"""
        fecha_futura = date.today().replace(year=date.today().year + 2)
        with self.assertRaises(ValidationError):
            validar_fecha_inicio_suscripcion(fecha_futura)

    def test_fecha_inicio_none(self):
        """Fecha None debe fallar"""
        with self.assertRaises(ValidationError):
            validar_fecha_inicio_suscripcion(None)

    def test_fecha_inicio_formato_invalido(self):
        """Formato inválido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_fecha_inicio_suscripcion("2024/01/01")


class ValidarFechaFinSuscripcionTest(TestCase):
    """Tests para validar_fecha_fin_suscripcion"""

    def test_fecha_fin_valida(self):
        """Fecha válida debe pasar"""
        validar_fecha_fin_suscripcion(date(2024, 12, 31))
        validar_fecha_fin_suscripcion(None)  # Opcional

    def test_fecha_fin_muy_antigua(self):
        """Fecha muy antigua debe fallar"""
        with self.assertRaises(ValidationError):
            validar_fecha_fin_suscripcion(date(2019, 12, 31))

    def test_fecha_fin_muy_futura(self):
        """Fecha muy futura debe fallar"""
        fecha_futura = date.today().replace(year=date.today().year + 6)
        with self.assertRaises(ValidationError):
            validar_fecha_fin_suscripcion(fecha_futura)


class ValidarEstadoSuscripcionTest(TestCase):
    """Tests para validar_estado_suscripcion"""

    def test_estado_suscripcion_valido(self):
        """Estados válidos deben pasar"""
        validar_estado_suscripcion("Activa")
        validar_estado_suscripcion("Pausada")
        validar_estado_suscripcion("Cancelada")
        validar_estado_suscripcion("Finalizada")

    def test_estado_suscripcion_invalido(self):
        """Estado inválido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_estado_suscripcion("Pendiente")


class ValidarRangoFechasSuscripcionTest(TestCase):
    """Tests para validar_rango_fechas_suscripcion"""

    def test_rango_valido(self):
        """Rango válido debe pasar"""
        validar_rango_fechas_suscripcion(date(2024, 1, 1), date(2024, 12, 31))

    def test_rango_fin_antes_inicio(self):
        """Fecha fin antes de inicio debe fallar"""
        with self.assertRaises(ValidationError):
            validar_rango_fechas_suscripcion(date(2024, 12, 31), date(2024, 1, 1))

    def test_rango_fechas_iguales(self):
        """Fechas iguales deben fallar"""
        with self.assertRaises(ValidationError):
            validar_rango_fechas_suscripcion(date(2024, 1, 1), date(2024, 1, 1))


# ==============================================================================
# TESTS PARA REGISTROS DE CONSUMO
# ==============================================================================


class ValidarFechaConsumoTest(TestCase):
    """Tests para validar_fecha_consumo"""

    def test_fecha_consumo_valida(self):
        """Fecha válida debe pasar"""
        validar_fecha_consumo(date.today())
        validar_fecha_consumo(date.today() - timedelta(days=30))

    def test_fecha_consumo_futura(self):
        """Fecha futura debe fallar"""
        with self.assertRaises(ValidationError):
            validar_fecha_consumo(date.today() + timedelta(days=1))

    def test_fecha_consumo_muy_antigua(self):
        """Fecha muy antigua debe fallar"""
        with self.assertRaises(ValidationError):
            validar_fecha_consumo(date(2019, 12, 31))

    def test_fecha_consumo_muy_vieja(self):
        """Fecha más de 90 días atrás debe fallar"""
        with self.assertRaises(ValidationError):
            validar_fecha_consumo(date.today() - timedelta(days=91))

    def test_fecha_consumo_none(self):
        """Fecha None debe fallar"""
        with self.assertRaises(ValidationError):
            validar_fecha_consumo(None)


class ValidarHoraRegistroTest(TestCase):
    """Tests para validar_hora_registro"""

    def test_hora_registro_valida(self):
        """Hora válida debe pasar"""
        validar_hora_registro(time(12, 0, 0))
        validar_hora_registro(time(11, 30, 0))

    def test_hora_registro_string_valida(self):
        """Hora como string válida debe pasar"""
        validar_hora_registro("12:00:00")
        validar_hora_registro("11:30")

    def test_hora_registro_muy_temprana(self):
        """Hora muy temprana debe fallar"""
        with self.assertRaises(ValidationError):
            validar_hora_registro(time(5, 59, 0))

    def test_hora_registro_muy_tardia(self):
        """Hora muy tardía debe fallar"""
        with self.assertRaises(ValidationError):
            validar_hora_registro(time(16, 1, 0))

    def test_hora_registro_none(self):
        """Hora None debe fallar"""
        with self.assertRaises(ValidationError):
            validar_hora_registro(None)


class ValidarCostoAlmuerzoTest(TestCase):
    """Tests para validar_costo_almuerzo"""

    def test_costo_almuerzo_valido(self):
        """Costo válido debe pasar"""
        validar_costo_almuerzo(Decimal("25000.00"))
        validar_costo_almuerzo(None)  # Opcional

    def test_costo_almuerzo_negativo(self):
        """Costo negativo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_costo_almuerzo(Decimal("-100.00"))

    def test_costo_almuerzo_excesivo(self):
        """Costo excesivo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_costo_almuerzo(Decimal("200001.00"))

    def test_costo_almuerzo_muchos_decimales(self):
        """Más de 2 decimales debe fallar"""
        with self.assertRaises(ValidationError):
            validar_costo_almuerzo(Decimal("100.999"))


class ValidarEstadoConsumoTest(TestCase):
    """Tests para validar_estado_consumo"""

    def test_estado_consumo_valido(self):
        """Estados válidos deben pasar"""
        validar_estado_consumo("Registrado")
        validar_estado_consumo("Confirmado")
        validar_estado_consumo("Rechazado")
        validar_estado_consumo("Cancelado")

    def test_estado_consumo_invalido(self):
        """Estado inválido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_estado_consumo("Pendiente")

    def test_estado_consumo_vacio(self):
        """Estado vacío debe fallar"""
        with self.assertRaises(ValidationError):
            validar_estado_consumo("")


class ValidarMotivoRechazoTest(TestCase):
    """Tests para validar_motivo_rechazo"""

    def test_motivo_rechazo_valido(self):
        """Motivo válido cuando estado es Rechazado debe pasar"""
        validar_motivo_rechazo("Estudiante no tiene suscripción activa", "Rechazado")

    def test_motivo_rechazo_requerido_cuando_rechazado(self):
        """Motivo requerido cuando estado es Rechazado"""
        with self.assertRaises(ValidationError):
            validar_motivo_rechazo(None, "Rechazado")
        with self.assertRaises(ValidationError):
            validar_motivo_rechazo("", "Rechazado")

    def test_motivo_rechazo_muy_corto(self):
        """Motivo muy corto debe fallar"""
        with self.assertRaises(ValidationError):
            validar_motivo_rechazo("Corto", "Rechazado")

    def test_motivo_rechazo_muy_largo(self):
        """Motivo muy largo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_motivo_rechazo("A" * 256, "Rechazado")

    def test_motivo_rechazo_sin_estado_rechazado(self):
        """Motivo sin estado Rechazado debe fallar"""
        with self.assertRaises(ValidationError):
            validar_motivo_rechazo("Algún motivo", "Confirmado")


# ==============================================================================
# TESTS PARA CUENTAS MENSUALES
# ==============================================================================


class ValidarAnioСuentaTest(TestCase):
    """Tests para validar_anio_cuenta"""

    def test_anio_valido(self):
        """Año válido debe pasar"""
        validar_anio_cuenta(2024)
        validar_anio_cuenta(date.today().year)

    def test_anio_muy_antiguo(self):
        """Año muy antiguo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_anio_cuenta(2019)

    def test_anio_muy_futuro(self):
        """Año muy futuro debe fallar"""
        with self.assertRaises(ValidationError):
            validar_anio_cuenta(date.today().year + 2)

    def test_anio_none(self):
        """Año None debe fallar"""
        with self.assertRaises(ValidationError):
            validar_anio_cuenta(None)


class ValidarMesCuentaTest(TestCase):
    """Tests para validar_mes_cuenta"""

    def test_mes_valido(self):
        """Mes válido debe pasar"""
        validar_mes_cuenta(1)
        validar_mes_cuenta(12)
        validar_mes_cuenta(6)

    def test_mes_cero(self):
        """Mes cero debe fallar"""
        with self.assertRaises(ValidationError):
            validar_mes_cuenta(0)

    def test_mes_trece(self):
        """Mes 13 debe fallar"""
        with self.assertRaises(ValidationError):
            validar_mes_cuenta(13)

    def test_mes_none(self):
        """Mes None debe fallar"""
        with self.assertRaises(ValidationError):
            validar_mes_cuenta(None)


class ValidarCantidadAlmuerzosTest(TestCase):
    """Tests para validar_cantidad_almuerzos"""

    def test_cantidad_valida(self):
        """Cantidad válida debe pasar"""
        validar_cantidad_almuerzos(0)
        validar_cantidad_almuerzos(20)
        validar_cantidad_almuerzos(31)

    def test_cantidad_negativa(self):
        """Cantidad negativa debe fallar"""
        with self.assertRaises(ValidationError):
            validar_cantidad_almuerzos(-1)

    def test_cantidad_excesiva(self):
        """Cantidad excesiva debe fallar"""
        with self.assertRaises(ValidationError):
            validar_cantidad_almuerzos(32)

    def test_cantidad_none(self):
        """Cantidad None debe fallar"""
        with self.assertRaises(ValidationError):
            validar_cantidad_almuerzos(None)


class ValidarMontoTotalCuentaTest(TestCase):
    """Tests para validar_monto_total_cuenta"""

    def test_monto_total_valido(self):
        """Monto válido debe pasar"""
        validar_monto_total_cuenta(Decimal("500000.00"))
        validar_monto_total_cuenta(Decimal("0.00"))

    def test_monto_total_negativo(self):
        """Monto negativo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_total_cuenta(Decimal("-100.00"))

    def test_monto_total_excesivo(self):
        """Monto excesivo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_total_cuenta(Decimal("10000001.00"))


class ValidarFormaCobroTest(TestCase):
    """Tests para validar_forma_cobro"""

    def test_forma_cobro_valida(self):
        """Formas válidas deben pasar"""
        validar_forma_cobro("Efectivo")
        validar_forma_cobro("Transferencia")
        validar_forma_cobro("Tarjeta")
        validar_forma_cobro("Cuenta Corriente")

    def test_forma_cobro_invalida(self):
        """Forma inválida debe fallar"""
        with self.assertRaises(ValidationError):
            validar_forma_cobro("Cheque")

    def test_forma_cobro_vacia(self):
        """Forma vacía debe fallar"""
        with self.assertRaises(ValidationError):
            validar_forma_cobro("")


class ValidarMontoPagadoCuentaTest(TestCase):
    """Tests para validar_monto_pagado_cuenta"""

    def test_monto_pagado_valido(self):
        """Monto válido debe pasar"""
        validar_monto_pagado_cuenta(Decimal("500000.00"))
        validar_monto_pagado_cuenta(Decimal("0.00"))

    def test_monto_pagado_negativo(self):
        """Monto negativo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_pagado_cuenta(Decimal("-100.00"))


class ValidarEstadoCuentaTest(TestCase):
    """Tests para validar_estado_cuenta"""

    def test_estado_cuenta_valido(self):
        """Estados válidos deben pasar"""
        validar_estado_cuenta("Pendiente")
        validar_estado_cuenta("Pagada")
        validar_estado_cuenta("Vencida")
        validar_estado_cuenta("Cancelada")

    def test_estado_cuenta_invalido(self):
        """Estado inválido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_estado_cuenta("Procesando")


class ValidarCoherenciaMontosCuentaTest(TestCase):
    """Tests para validar_coherencia_montos_cuenta"""

    def test_coherencia_valida(self):
        """Montos coherentes deben pasar"""
        validar_coherencia_montos_cuenta(Decimal("100000.00"), Decimal("100000.00"))
        validar_coherencia_montos_cuenta(Decimal("100000.00"), Decimal("50000.00"))

    def test_pago_excede_tolerancia(self):
        """Pago excediendo tolerancia debe fallar"""
        with self.assertRaises(ValidationError):
            validar_coherencia_montos_cuenta(Decimal("100000.00"), Decimal("115000.00"))


# ==============================================================================
# TESTS PARA PAGOS
# ==============================================================================


class ValidarFechaPagoTest(TestCase):
    """Tests para validar_fecha_pago"""

    def test_fecha_pago_valida(self):
        """Fecha válida debe pasar"""
        validar_fecha_pago(date.today())
        validar_fecha_pago(date(2024, 1, 1))

    def test_fecha_pago_futura(self):
        """Fecha futura debe fallar"""
        with self.assertRaises(ValidationError):
            validar_fecha_pago(date.today() + timedelta(days=1))

    def test_fecha_pago_muy_antigua(self):
        """Fecha muy antigua debe fallar"""
        with self.assertRaises(ValidationError):
            validar_fecha_pago(date(2019, 12, 31))


class ValidarMontoPagoTest(TestCase):
    """Tests para validar_monto_pago"""

    def test_monto_pago_valido(self):
        """Monto válido debe pasar"""
        validar_monto_pago(Decimal("100000.00"))
        validar_monto_pago(Decimal("1.00"))

    def test_monto_pago_cero(self):
        """Monto cero debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_pago(Decimal("0.00"))

    def test_monto_pago_negativo(self):
        """Monto negativo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_pago(Decimal("-100.00"))

    def test_monto_pago_excesivo(self):
        """Monto excesivo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_pago(Decimal("10000001.00"))


class ValidarMedioPagoTest(TestCase):
    """Tests para validar_medio_pago"""

    def test_medio_pago_valido(self):
        """Medios válidos deben pasar"""
        validar_medio_pago("Efectivo")
        validar_medio_pago("Transferencia")
        validar_medio_pago("Tarjeta Débito")
        validar_medio_pago("Tarjeta Crédito")
        validar_medio_pago("Cheque")

    def test_medio_pago_invalido(self):
        """Medio inválido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_medio_pago("Bitcoin")


class ValidarReferenciaPagoTest(TestCase):
    """Tests para validar_referencia_pago"""

    def test_referencia_valida(self):
        """Referencia válida debe pasar"""
        validar_referencia_pago("REF-12345")
        validar_referencia_pago(None)  # Opcional
        validar_referencia_pago("")  # Opcional

    def test_referencia_muy_larga(self):
        """Referencia muy larga debe fallar"""
        with self.assertRaises(ValidationError):
            validar_referencia_pago("A" * 51)

    def test_referencia_caracteres_invalidos(self):
        """Caracteres no permitidos deben fallar"""
        with self.assertRaises(ValidationError):
            validar_referencia_pago("REF@#$12345")


class ValidarEstadoPagoMensualTest(TestCase):
    """Tests para validar_estado_pago_mensual"""

    def test_estado_pago_mensual_valido(self):
        """Estados válidos deben pasar"""
        validar_estado_pago_mensual("Pendiente")
        validar_estado_pago_mensual("Confirmado")
        validar_estado_pago_mensual("Rechazado")
        validar_estado_pago_mensual(None)  # Opcional

    def test_estado_pago_mensual_invalido(self):
        """Estado inválido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_estado_pago_mensual("Procesando")


# ==============================================================================
# TESTS PARA ALÉRGENOS
# ==============================================================================


class ValidarNombreAlergenoTest(TestCase):
    """Tests para validar_nombre_alergeno"""

    def test_nombre_alergeno_valido(self):
        """Nombre válido debe pasar"""
        validar_nombre_alergeno("Maní")
        validar_nombre_alergeno("Gluten")
        validar_nombre_alergeno("Lactosa")

    def test_nombre_alergeno_vacio(self):
        """Nombre vacío debe fallar"""
        with self.assertRaises(ValidationError):
            validar_nombre_alergeno("")

    def test_nombre_alergeno_muy_corto(self):
        """Nombre muy corto debe fallar"""
        with self.assertRaises(ValidationError):
            validar_nombre_alergeno("AB")

    def test_nombre_alergeno_muy_largo(self):
        """Nombre muy largo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_nombre_alergeno("A" * 101)


class ValidarPalabrasClaveAlergenoTest(TestCase):
    """Tests para validar_palabras_clave_alergeno"""

    def test_palabras_clave_validas(self):
        """Palabras clave válidas deben pasar"""
        validar_palabras_clave_alergeno(["maní", "cacahuate", "peanut"])
        validar_palabras_clave_alergeno(["gluten", "trigo", "wheat"])

    def test_palabras_clave_como_json_string(self):
        """JSON string válido debe pasar"""
        validar_palabras_clave_alergeno('["maní", "cacahuate"]')

    def test_palabras_clave_vacia(self):
        """Lista vacía debe fallar"""
        with self.assertRaises(ValidationError):
            validar_palabras_clave_alergeno([])

    def test_palabras_clave_none(self):
        """None debe fallar"""
        with self.assertRaises(ValidationError):
            validar_palabras_clave_alergeno(None)

    def test_palabras_clave_excesivas(self):
        """Más de 20 palabras debe fallar"""
        with self.assertRaises(ValidationError):
            validar_palabras_clave_alergeno(["palabra" + str(i) for i in range(21)])

    def test_palabra_clave_muy_corta(self):
        """Palabra muy corta debe fallar"""
        with self.assertRaises(ValidationError):
            validar_palabras_clave_alergeno(["a"])

    def test_palabra_clave_muy_larga(self):
        """Palabra muy larga debe fallar"""
        with self.assertRaises(ValidationError):
            validar_palabras_clave_alergeno(["A" * 51])


class ValidarNivelSeveridadAlergenoTest(TestCase):
    """Tests para validar_nivel_severidad_alergeno"""

    def test_nivel_severidad_valido(self):
        """Niveles válidos deben pasar"""
        validar_nivel_severidad_alergeno("Baja")
        validar_nivel_severidad_alergeno("Media")
        validar_nivel_severidad_alergeno("Alta")
        validar_nivel_severidad_alergeno("Crítica")

    def test_nivel_severidad_invalido(self):
        """Nivel inválido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_nivel_severidad_alergeno("Moderada")

    def test_nivel_severidad_vacio(self):
        """Nivel vacío debe fallar"""
        with self.assertRaises(ValidationError):
            validar_nivel_severidad_alergeno("")


class ValidarIconoAlergenoTest(TestCase):
    """Tests para validar_icono_alergeno"""

    def test_icono_valido(self):
        """Icono válido debe pasar"""
        validar_icono_alergeno("🥜")
        validar_icono_alergeno("⚠️")
        validar_icono_alergeno(None)  # Opcional

    def test_icono_muy_largo(self):
        """Icono muy largo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_icono_alergeno("A" * 11)


class ValidarUsuarioCreacionTest(TestCase):
    """Tests para validar_usuario_creacion"""

    def test_usuario_valido(self):
        """Usuario válido debe pasar"""
        validar_usuario_creacion("admin")
        validar_usuario_creacion("usuario.sistema")
        validar_usuario_creacion(None)  # Opcional

    def test_usuario_muy_largo(self):
        """Usuario muy largo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_usuario_creacion("A" * 101)

    def test_usuario_caracteres_invalidos(self):
        """Caracteres no permitidos deben fallar"""
        with self.assertRaises(ValidationError):
            validar_usuario_creacion("admin@#$")


# ==============================================================================
# TESTS PARA PRODUCTOS-ALÉRGENOS
# ==============================================================================


class ValidarObservacionesProductoAlergenoTest(TestCase):
    """Tests para validar_observaciones_producto_alergeno"""

    def test_observaciones_validas(self):
        """Observaciones válidas deben pasar"""
        validar_observaciones_producto_alergeno("Puede contener trazas")
        validar_observaciones_producto_alergeno(None)  # Opcional
        validar_observaciones_producto_alergeno("")  # Opcional

    def test_observaciones_muy_largas(self):
        """Observaciones muy largas deben fallar"""
        with self.assertRaises(ValidationError):
            validar_observaciones_producto_alergeno("A" * 501)
