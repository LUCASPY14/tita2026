"""
Tests para los validadores del módulo Notificaciones
Cobertura completa de los 45 valid

adores
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime, date, time
from apps.notificaciones.validators import *

# =============================================================================
# TESTS - NOTIFICACIONES PORTAL
# =============================================================================


class ValidarTipoNotificacionPortalTest(TestCase):
    def test_tipo_valido(self):
        try:
            validar_tipo_notificacion_portal("alerta")
            validar_tipo_notificacion_portal("recordatorio")
        except ValidationError:
            self.fail("Tipo válido lanzó ValidationError")

    def test_tipo_vacio(self):
        with self.assertRaises(ValidationError):
            validar_tipo_notificacion_portal("")

    def test_tipo_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_tipo_notificacion_portal("ab")

    def test_tipo_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_tipo_notificacion_portal("a" * 51)

    def test_tipo_no_valido(self):
        with self.assertRaises(ValidationError):
            validar_tipo_notificacion_portal("tipo_invalido")


class ValidarTituloNotificacionTest(TestCase):
    def test_titulo_valido(self):
        try:
            validar_titulo_notificacion("Nueva venta registrada")
        except ValidationError:
            self.fail("Título válido lanzó ValidationError")

    def test_titulo_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_titulo_notificacion("Hola")

    def test_titulo_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_titulo_notificacion("a" * 256)

    def test_titulo_caracteres_invalidos(self):
        with self.assertRaises(ValidationError):
            validar_titulo_notificacion("Título con <script>")


class ValidarMensajeNotificacionTest(TestCase):
    def test_mensaje_valido(self):
        try:
            validar_mensaje_notificacion("Este es un mensaje de prueba válido.")
        except ValidationError:
            self.fail("Mensaje válido lanzó ValidationError")

    def test_mensaje_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_mensaje_notificacion("Corto")

    def test_mensaje_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_mensaje_notificacion("a" * 5001)


class ValidarLeidaNotificacionTest(TestCase):
    def test_leida_valida(self):
        try:
            validar_leida_notificacion(0)
            validar_leida_notificacion(1)
        except ValidationError:
            self.fail("Estado válido lanzó ValidationError")

    def test_leida_invalida(self):
        with self.assertRaises(ValidationError):
            validar_leida_notificacion(2)
        with self.assertRaises(ValidationError):
            validar_leida_notificacion(-1)


# =============================================================================
# TESTS - NOTIFICACIONES SALDO
# =============================================================================


class ValidarSaldoActualTest(TestCase):
    def test_saldo_valido(self):
        try:
            validar_saldo_actual(Decimal("1000.00"))
            validar_saldo_actual(Decimal("0.00"))
        except ValidationError:
            self.fail("Saldo válido lanzó ValidationError")

    def test_saldo_negativo(self):
        with self.assertRaises(ValidationError):
            validar_saldo_actual(Decimal("-100.00"))

    def test_saldo_excesivo(self):
        with self.assertRaises(ValidationError):
            validar_saldo_actual(Decimal("100000000.00"))

    def test_saldo_muchos_decimales(self):
        with self.assertRaises(ValidationError):
            validar_saldo_actual(Decimal("100.123"))


class ValidarEnviadaEmailTest(TestCase):
    def test_enviada_valida(self):
        try:
            validar_enviada_email(0)
            validar_enviada_email(1)
        except ValidationError:
            self.fail("Estado válido lanzó ValidationError")

    def test_enviada_invalida(self):
        with self.assertRaises(ValidationError):
            validar_enviada_email(2)


class ValidarEnviadaSmsTest(TestCase):
    def test_enviada_valida(self):
        try:
            validar_enviada_sms(0)
            validar_enviada_sms(1)
        except ValidationError:
            self.fail("Estado válido lanzó ValidationError")

    def test_enviada_invalida(self):
        with self.assertRaises(ValidationError):
            validar_enviada_sms(2)


# =============================================================================
# TESTS - SOLICITUDES NOTIFICACIÓN
# =============================================================================


class ValidarSaldoAlertaTest(TestCase):
    def test_saldo_valido(self):
        try:
            validar_saldo_alerta(Decimal("500.00"))
        except ValidationError:
            self.fail("Saldo válido lanzó ValidationError")

    def test_saldo_cero(self):
        with self.assertRaises(ValidationError):
            validar_saldo_alerta(Decimal("0.00"))

    def test_saldo_negativo(self):
        with self.assertRaises(ValidationError):
            validar_saldo_alerta(Decimal("-50.00"))

    def test_saldo_excesivo(self):
        with self.assertRaises(ValidationError):
            validar_saldo_alerta(Decimal("10000000.00"))


class ValidarDestinoNotificacionTest(TestCase):
    def test_destino_valido(self):
        try:
            validar_destino_notificacion("Email")
            validar_destino_notificacion("SMS")
            validar_destino_notificacion("Ambos")
        except ValidationError:
            self.fail("Destino válido lanzó ValidationError")

    def test_destino_invalido(self):
        with self.assertRaises(ValidationError):
            validar_destino_notificacion("WhatsApp")


class ValidarEstadoSolicitudTest(TestCase):
    def test_estado_valido(self):
        try:
            validar_estado_solicitud("Pendiente")
            validar_estado_solicitud("Enviada")
        except ValidationError:
            self.fail("Estado válido lanzó ValidationError")

    def test_estado_none(self):
        try:
            validar_estado_solicitud(None)
        except ValidationError:
            self.fail("None no debería lanzar error (es opcional)")

    def test_estado_invalido(self):
        with self.assertRaises(ValidationError):
            validar_estado_solicitud("Procesando")


# =============================================================================
# TESTS - PREFERENCIAS NOTIFICACIÓN
# =============================================================================


class ValidarTipoPreferenciaNotificacionTest(TestCase):
    def test_tipo_valido(self):
        try:
            validar_tipo_preferencia_notificacion("ventas")
            validar_tipo_preferencia_notificacion("compras")
        except ValidationError:
            self.fail("Tipo válido lanzó ValidationError")

    def test_tipo_invalido(self):
        with self.assertRaises(ValidationError):
            validar_tipo_preferencia_notificacion("tipo_invalido")

    def test_tipo_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_tipo_preferencia_notificacion("a" * 51)


class ValidarEmailActivoTest(TestCase):
    def test_email_activo_valido(self):
        try:
            validar_email_activo(0)
            validar_email_activo(1)
        except ValidationError:
            self.fail("Estado válido lanzó ValidationError")

    def test_email_activo_invalido(self):
        with self.assertRaises(ValidationError):
            validar_email_activo(2)


class ValidarPushActivoTest(TestCase):
    def test_push_activo_valido(self):
        try:
            validar_push_activo(0)
            validar_push_activo(1)
        except ValidationError:
            self.fail("Estado válido lanzó ValidationError")

    def test_push_activo_invalido(self):
        with self.assertRaises(ValidationError):
            validar_push_activo(2)


# =============================================================================
# TESTS - EMAILS ENVIADOS
# =============================================================================


class ValidarEmailDestinatarioTest(TestCase):
    def test_email_valido(self):
        try:
            validar_email_destinatario("usuario@ejemplo.com")
            validar_email_destinatario("test.user+tag@dominio.py")
        except ValidationError:
            self.fail("Email válido lanzó ValidationError")

    def test_email_invalido(self):
        with self.assertRaises(ValidationError):
            validar_email_destinatario("email_sin_arroba.com")
        with self.assertRaises(ValidationError):
            validar_email_destinatario("email@")

    def test_email_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_email_destinatario("a" * 250 + "@test.com")


class ValidarNombreDestinatarioTest(TestCase):
    def test_nombre_valido(self):
        try:
            validar_nombre_destinatario("Juan Pérez")
            validar_nombre_destinatario("O'Connor")
        except ValidationError:
            self.fail("Nombre válido lanzó ValidationError")

    def test_nombre_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_nombre_destinatario("A")

    def test_nombre_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_nombre_destinatario("a" * 101)

    def test_nombre_caracteres_invalidos(self):
        with self.assertRaises(ValidationError):
            validar_nombre_destinatario("Juan123")


class ValidarAsuntoEmailTest(TestCase):
    def test_asunto_valido(self):
        try:
            validar_asunto_email("Confirmación de compra")
        except ValidationError:
            self.fail("Asunto válido lanzó ValidationError")

    def test_asunto_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_asunto_email("OK")

    def test_asunto_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_asunto_email("a" * 201)


class ValidarCuerpoEmailTest(TestCase):
    def test_cuerpo_valido(self):
        try:
            validar_cuerpo_email("Este es el cuerpo del email con contenido suficiente.")
        except ValidationError:
            self.fail("Cuerpo válido lanzó ValidationError")

    def test_cuerpo_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_cuerpo_email("Hola")

    def test_cuerpo_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_cuerpo_email("a" * 50001)


class ValidarEstadoEmailTest(TestCase):
    def test_estado_valido(self):
        try:
            validar_estado_email("Pendiente")
            validar_estado_email("Enviado")
            validar_estado_email("Entregado")
        except ValidationError:
            self.fail("Estado válido lanzó ValidationError")

    def test_estado_invalido(self):
        with self.assertRaises(ValidationError):
            validar_estado_email("Procesando")


class ValidarIntentosEnvioTest(TestCase):
    def test_intentos_validos(self):
        try:
            validar_intentos_envio(0)
            validar_intentos_envio(5)
            validar_intentos_envio(10)
        except ValidationError:
            self.fail("Intentos válidos lanzaron ValidationError")

    def test_intentos_negativos(self):
        with self.assertRaises(ValidationError):
            validar_intentos_envio(-1)

    def test_intentos_excesivos(self):
        with self.assertRaises(ValidationError):
            validar_intentos_envio(11)


# =============================================================================
# TESTS - SMS ENVIADOS
# =============================================================================


class ValidarTelefonoSmsTest(TestCase):
    def test_telefono_valido(self):
        try:
            validar_telefono_sms("0981123456")
            validar_telefono_sms("+595981123456")
            validar_telefono_sms("(0981) 123-456")
        except ValidationError:
            self.fail("Teléfono válido lanzó ValidationError")

    def test_telefono_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_telefono_sms("12345")

    def test_telefono_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_telefono_sms("1" * 21)

    def test_telefono_caracteres_invalidos(self):
        with self.assertRaises(ValidationError):
            validar_telefono_sms("098abc1234")


class ValidarMensajeSmsTest(TestCase):
    def test_mensaje_valido(self):
        try:
            validar_mensaje_sms("Este es un mensaje SMS válido.")
        except ValidationError:
            self.fail("Mensaje válido lanzó ValidationError")

    def test_mensaje_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_mensaje_sms("Hola")

    def test_mensaje_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_mensaje_sms("a" * 161)


class ValidarEstadoSmsTest(TestCase):
    def test_estado_valido(self):
        try:
            validar_estado_sms("Pendiente")
            validar_estado_sms("Enviado")
        except ValidationError:
            self.fail("Estado válido lanzó ValidationError")

    def test_estado_invalido(self):
        with self.assertRaises(ValidationError):
            validar_estado_sms("Procesando")


class ValidarCostoSmsTest(TestCase):
    def test_costo_valido(self):
        try:
            validar_costo_sms(Decimal("50.00"))
            validar_costo_sms(None)  # Opcional
        except ValidationError:
            self.fail("Costo válido lanzó ValidationError")

    def test_costo_negativo(self):
        with self.assertRaises(ValidationError):
            validar_costo_sms(Decimal("-10.00"))

    def test_costo_excesivo(self):
        with self.assertRaises(ValidationError):
            validar_costo_sms(Decimal("100000.00"))


# =============================================================================
# TESTS - PLANTILLAS EMAIL/SMS
# =============================================================================


class ValidarCodigoTemplateTest(TestCase):
    def test_codigo_valido(self):
        try:
            validar_codigo_template("TPL_BIENVENIDA_01")
            validar_codigo_template("codigo_123")
        except ValidationError:
            self.fail("Código válido lanzó ValidationError")

    def test_codigo_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_codigo_template("AB")

    def test_codigo_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_codigo_template("a" * 51)

    def test_codigo_caracteres_invalidos(self):
        with self.assertRaises(ValidationError):
            validar_codigo_template("codigo-con-guion")


class ValidarNombreTemplateTest(TestCase):
    def test_nombre_valido(self):
        try:
            validar_nombre_template("Plantilla de Bienvenida")
        except ValidationError:
            self.fail("Nombre válido lanzó ValidationError")

    def test_nombre_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_nombre_template("AB")

    def test_nombre_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_nombre_template("a" * 101)


class ValidarVariablesTemplateTest(TestCase):
    def test_variables_validas(self):
        try:
            validar_variables_template(["nombre", "apellido", "email"])
            validar_variables_template([])  # Lista vacía es válida
        except ValidationError:
            self.fail("Variables válidas lanzaron ValidationError")

    def test_variables_como_json_string(self):
        try:
            validar_variables_template('["nombre", "email"]')
        except ValidationError:
            self.fail("JSON string válido lanzó ValidationError")

    def test_variables_no_lista(self):
        with self.assertRaises(ValidationError):
            validar_variables_template({"nombre": "Usuario"})

    def test_variables_excesivas(self):
        with self.assertRaises(ValidationError):
            validar_variables_template(["var" + str(i) for i in range(51)])

    def test_variable_muy_corta(self):
        with self.assertRaises(ValidationError):
            validar_variables_template(["a"])

    def test_variable_muy_larga(self):
        with self.assertRaises(ValidationError):
            validar_variables_template(["a" * 51])


class ValidarCategoriaTemplateTest(TestCase):
    def test_categoria_valida(self):
        try:
            validar_categoria_template("Ventas")
            validar_categoria_template("Promociones")
        except ValidationError:
            self.fail("Categoría válida lanzó ValidationError")

    def test_categoria_invalida(self):
        with self.assertRaises(ValidationError):
            validar_categoria_template("Categoría Inválida")


class ValidarCuerpoHtmlTemplateTest(TestCase):
    def test_cuerpo_html_valido(self):
        try:
            validar_cuerpo_html_template("<html><body><h1>Título</h1></body></html>")
        except ValidationError:
            self.fail("Cuerpo HTML válido lanzó ValidationError")

    def test_cuerpo_html_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_cuerpo_html_template("<p>Corto</p>")

    def test_cuerpo_html_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_cuerpo_html_template("<p>" + "a" * 100000 + "</p>")


# =============================================================================
# TESTS - CAMPAÑAS COMUNICACIÓN
# =============================================================================


class ValidarNombreCampanaTest(TestCase):
    def test_nombre_valido(self):
        try:
            validar_nombre_campana("Campaña de Verano 2024")
        except ValidationError:
            self.fail("Nombre válido lanzó ValidationError")

    def test_nombre_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_nombre_campana("Camp")

    def test_nombre_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_nombre_campana("a" * 101)


class ValidarTipoCampanaTest(TestCase):
    def test_tipo_valido(self):
        try:
            validar_tipo_campana("Email")
            validar_tipo_campana("SMS")
            validar_tipo_campana("Mixta")
        except ValidationError:
            self.fail("Tipo válido lanzó ValidationError")

    def test_tipo_invalido(self):
        with self.assertRaises(ValidationError):
            validar_tipo_campana("WhatsApp")


class ValidarEstadoCampanaTest(TestCase):
    def test_estado_valido(self):
        try:
            validar_estado_campana("Borrador")
            validar_estado_campana("Programada")
            validar_estado_campana("Enviada")
        except ValidationError:
            self.fail("Estado válido lanzó ValidationError")

    def test_estado_invalido(self):
        with self.assertRaises(ValidationError):
            validar_estado_campana("En Proceso")


class ValidarTotalDestinatariosTest(TestCase):
    def test_total_valido(self):
        try:
            validar_total_destinatarios(0)
            validar_total_destinatarios(1000)
            validar_total_destinatarios(1000000)
        except ValidationError:
            self.fail("Total válido lanzó ValidationError")

    def test_total_negativo(self):
        with self.assertRaises(ValidationError):
            validar_total_destinatarios(-1)

    def test_total_excesivo(self):
        with self.assertRaises(ValidationError):
            validar_total_destinatarios(1000001)


# =============================================================================
# TESTS - ALERTAS AUTOMÁTICAS
# =============================================================================


class ValidarNombreAlertaTest(TestCase):
    def test_nombre_valido(self):
        try:
            validar_nombre_alerta("Alerta de Stock Bajo")
        except ValidationError:
            self.fail("Nombre válido lanzó ValidationError")

    def test_nombre_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_nombre_alerta("ABCD")

    def test_nombre_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_nombre_alerta("a" * 101)


class ValidarTipoAlertaTest(TestCase):
    def test_tipo_valido(self):
        try:
            validar_tipo_alerta("Inventario")
            validar_tipo_alerta("Ventas")
        except ValidationError:
            self.fail("Tipo válido lanzó ValidationError")

    def test_tipo_invalido(self):
        with self.assertRaises(ValidationError):
            validar_tipo_alerta("TipoInválido")


class ValidarCriticidadAlertaTest(TestCase):
    def test_criticidad_valida(self):
        try:
            validar_criticidad_alerta("Baja")
            validar_criticidad_alerta("Media")
            validar_criticidad_alerta("Alta")
            validar_criticidad_alerta("Crítica")
        except ValidationError:
            self.fail("Criticidad válida lanzó ValidationError")

    def test_criticidad_invalida(self):
        with self.assertRaises(ValidationError):
            validar_criticidad_alerta("Urgente")


class ValidarFrecuenciaMinutosTest(TestCase):
    def test_frecuencia_valida(self):
        try:
            validar_frecuencia_minutos(1)
            validar_frecuencia_minutos(60)
            validar_frecuencia_minutos(43200)
        except ValidationError:
            self.fail("Frecuencia válida lanzó ValidationError")

    def test_frecuencia_cero(self):
        with self.assertRaises(ValidationError):
            validar_frecuencia_minutos(0)

    def test_frecuencia_excesiva(self):
        with self.assertRaises(ValidationError):
            validar_frecuencia_minutos(43201)


# =============================================================================
# TESTS - ALERTAS SISTEMA
# =============================================================================


class ValidarTipoAlertaSistemaTest(TestCase):
    def test_tipo_valido(self):
        try:
            validar_tipo_alerta_sistema("error")
            validar_tipo_alerta_sistema("warning")
            validar_tipo_alerta_sistema("info")
        except ValidationError:
            self.fail("Tipo válido lanzó ValidationError")

    def test_tipo_invalido(self):
        with self.assertRaises(ValidationError):
            validar_tipo_alerta_sistema("tipo_invalido")


class ValidarMensajeAlertaSistemaTest(TestCase):
    def test_mensaje_valido(self):
        try:
            validar_mensaje_alerta_sistema("Error en el sistema de ventas.")
        except ValidationError:
            self.fail("Mensaje válido lanzó ValidationError")

    def test_mensaje_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_mensaje_alerta_sistema("Error")

    def test_mensaje_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_mensaje_alerta_sistema("a" * 501)


class ValidarEstadoAlertaSistemaTest(TestCase):
    def test_estado_valido(self):
        try:
            validar_estado_alerta_sistema("Pendiente")
            validar_estado_alerta_sistema("Resuelta")
            validar_estado_alerta_sistema(None)  # Opcional
        except ValidationError:
            self.fail("Estado válido lanzó ValidationError")

    def test_estado_invalido(self):
        with self.assertRaises(ValidationError):
            validar_estado_alerta_sistema("En Proceso")


# =============================================================================
# TESTS - HISTORIAL ALERTAS
# =============================================================================


class ValidarDatosContextoHistorialTest(TestCase):
    def test_datos_validos(self):
        try:
            validar_datos_contexto_historial({"usuario": "admin", "accion": "login"})
            validar_datos_contexto_historial({})  # Dict vacío es válido
        except ValidationError:
            self.fail("Datos válidos lanzaron ValidationError")

    def test_datos_como_json_string(self):
        try:
            validar_datos_contexto_historial('{"usuario": "admin"}')
        except ValidationError:
            self.fail("JSON string válido lanzó ValidationError")

    def test_datos_no_dict(self):
        with self.assertRaises(ValidationError):
            validar_datos_contexto_historial(["lista", "no", "valida"])


class ValidarResueltoHistorialTest(TestCase):
    def test_resuelto_valido(self):
        try:
            validar_resuelto_historial(0)
            validar_resuelto_historial(1)
        except ValidationError:
            self.fail("Estado válido lanzó ValidationError")

    def test_resuelto_invalido(self):
        with self.assertRaises(ValidationError):
            validar_resuelto_historial(2)


# =============================================================================
# TESTS - ANOMALÍAS DETECTADAS
# =============================================================================


class ValidarUsuarioAnomaliaTest(TestCase):
    def test_usuario_valido(self):
        try:
            validar_usuario_anomalia("admin")
            validar_usuario_anomalia("usuario_test")
        except ValidationError:
            self.fail("Usuario válido lanzó ValidationError")

    def test_usuario_muy_corto(self):
        with self.assertRaises(ValidationError):
            validar_usuario_anomalia("ab")

    def test_usuario_muy_largo(self):
        with self.assertRaises(ValidationError):
            validar_usuario_anomalia("a" * 101)


class ValidarTipoAnomaliaTest(TestCase):
    def test_tipo_valido(self):
        try:
            validar_tipo_anomalia("acceso_inusual")
            validar_tipo_anomalia("intentos_fallidos")
        except ValidationError:
            self.fail("Tipo válido lanzó ValidationError")

    def test_tipo_invalido(self):
        with self.assertRaises(ValidationError):
            validar_tipo_anomalia("tipo_invalido")


class ValidarIpAddressTest(TestCase):
    def test_ipv4_valida(self):
        try:
            validar_ip_address("192.168.1.1")
            validar_ip_address("10.0.0.1")
            validar_ip_address(None)  # Opcional
        except ValidationError:
            self.fail("IPv4 válida lanzó ValidationError")

    def test_ipv6_valida(self):
        try:
            validar_ip_address("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
            validar_ip_address("::1")
        except ValidationError:
            self.fail("IPv6 válida lanzó ValidationError")

    def test_ip_invalida(self):
        with self.assertRaises(ValidationError):
            validar_ip_address("999.999.999.999")
        with self.assertRaises(ValidationError):
            validar_ip_address("no_es_ip")


class ValidarNivelRiesgoAnomaliaTest(TestCase):
    def test_nivel_valido(self):
        try:
            validar_nivel_riesgo_anomalia("Bajo")
            validar_nivel_riesgo_anomalia("Medio")
            validar_nivel_riesgo_anomalia("Alto")
            validar_nivel_riesgo_anomalia("Crítico")
        except ValidationError:
            self.fail("Nivel válido lanzó ValidationError")

    def test_nivel_invalido(self):
        with self.assertRaises(ValidationError):
            validar_nivel_riesgo_anomalia("Urgente")


class ValidarNotificadoAnomaliaTest(TestCase):
    def test_notificado_valido(self):
        try:
            validar_notificado_anomalia(0)
            validar_notificado_anomalia(1)
        except ValidationError:
            self.fail("Estado válido lanzó ValidationError")

    def test_notificado_invalido(self):
        with self.assertRaises(ValidationError):
            validar_notificado_anomalia(2)


# =============================================================================
# TESTS - RESTRICCIONES HORARIAS
# =============================================================================


class ValidarTipoUsuarioRestriccionTest(TestCase):
    def test_tipo_valido(self):
        try:
            validar_tipo_usuario_restriccion("Empleado")
            validar_tipo_usuario_restriccion("Cliente")
        except ValidationError:
            self.fail("Tipo válido lanzó ValidationError")

    def test_tipo_invalido(self):
        with self.assertRaises(ValidationError):
            validar_tipo_usuario_restriccion("Usuario")


class ValidarDiaSemanaRestriccionTest(TestCase):
    def test_dia_valido(self):
        try:
            validar_dia_semana_restriccion("Lunes")
            validar_dia_semana_restriccion("Martes")
            validar_dia_semana_restriccion("Todos")
        except ValidationError:
            self.fail("Día válido lanzó ValidationError")

    def test_dia_invalido(self):
        with self.assertRaises(ValidationError):
            validar_dia_semana_restriccion("Monday")


class ValidarRangoHorarioRestriccionTest(TestCase):
    def test_rango_valido(self):
        try:
            validar_rango_horario_restriccion(time(8, 0), time(18, 0))
        except ValidationError:
            self.fail("Rango válido lanzó ValidationError")

    def test_rango_invalido(self):
        with self.assertRaises(ValidationError):
            validar_rango_horario_restriccion(time(18, 0), time(8, 0))

    def test_rango_igual(self):
        with self.assertRaises(ValidationError):
            validar_rango_horario_restriccion(time(8, 0), time(8, 0))

    def test_hora_inicio_no_es_time(self):
        """Line 777: hora_inicio not a time object."""
        with self.assertRaises(ValidationError):
            validar_rango_horario_restriccion("08:00", time(18, 0))

    def test_hora_fin_no_es_time(self):
        """Line 780: hora_fin not a time object."""
        with self.assertRaises(ValidationError):
            validar_rango_horario_restriccion(time(8, 0), "18:00")


# =============================================================================
# EXTRA TESTS for missing lines (None / invalid-type branches)
# =============================================================================

class ValidarTituloNoneTest(TestCase):
    def test_titulo_none(self):
        """Line 50: titulo=None."""
        with self.assertRaises(ValidationError):
            validar_titulo_notificacion(None)


class ValidarMensajeNoneTest(TestCase):
    def test_mensaje_none(self):
        """Line 70: mensaje=None."""
        with self.assertRaises(ValidationError):
            validar_mensaje_notificacion(None)


class ValidarSaldoActualNoneTest(TestCase):
    def test_saldo_none(self):
        """Line 93: saldo=None."""
        with self.assertRaises(ValidationError):
            validar_saldo_actual(None)

    def test_saldo_invalido_conversion(self):
        """Lines 97-98: Decimal('abc') raises InvalidOperation → ValidationError."""
        with self.assertRaises(ValidationError):
            validar_saldo_actual("no_es_numero")


class ValidarSaldoAlertaNoneTest(TestCase):
    def test_saldo_alerta_none(self):
        """Line 131: saldo_alerta=None."""
        with self.assertRaises(ValidationError):
            validar_saldo_alerta(None)

    def test_saldo_alerta_invalido(self):
        """Lines 135-136: Decimal('abc') → ValidationError."""
        with self.assertRaises(ValidationError):
            validar_saldo_alerta("texto")

    def test_saldo_alerta_muchos_decimales(self):
        """Line 146: saldo has more than 2 decimals."""
        with self.assertRaises(ValidationError):
            validar_saldo_alerta(Decimal("100.123"))


class ValidarDestinoNoneTest(TestCase):
    def test_destino_none(self):
        """Line 152: destino=None."""
        with self.assertRaises(ValidationError):
            validar_destino_notificacion(None)


class ValidarEstadoSolicitudNoStringTest(TestCase):
    def test_estado_no_string(self):
        """Line 165: estado not None but not a string."""
        with self.assertRaises(ValidationError):
            validar_estado_solicitud(123)


class ValidarTipoPreferenciaNoneTest(TestCase):
    def test_tipo_none(self):
        """Line 180: tipo=None."""
        with self.assertRaises(ValidationError):
            validar_tipo_preferencia_notificacion(None)

    def test_tipo_muy_corto(self):
        """Line 184: tipo < 3 chars."""
        with self.assertRaises(ValidationError):
            validar_tipo_preferencia_notificacion("ab")


class ValidarEmailDestinatarioNoneTest(TestCase):
    def test_email_none(self):
        """Line 223: email=None."""
        with self.assertRaises(ValidationError):
            validar_email_destinatario(None)


class ValidarNombreDestinatarioNoneTest(TestCase):
    def test_nombre_none(self):
        """Line 237: nombre=None."""
        with self.assertRaises(ValidationError):
            validar_nombre_destinatario(None)


class ValidarAsuntoNoneTest(TestCase):
    def test_asunto_none(self):
        """Line 257: asunto=None."""
        with self.assertRaises(ValidationError):
            validar_asunto_email(None)


class ValidarCuerpoEmailNoneTest(TestCase):
    def test_cuerpo_none(self):
        """Line 269: cuerpo=None."""
        with self.assertRaises(ValidationError):
            validar_cuerpo_email(None)


class ValidarEstadoEmailNoneTest(TestCase):
    def test_estado_none(self):
        """Line 281: estado=None."""
        with self.assertRaises(ValidationError):
            validar_estado_email(None)


class ValidarIntentosEnvioNoneTest(TestCase):
    def test_intentos_none(self):
        """Line 300: value=None (not int)."""
        with self.assertRaises(ValidationError):
            validar_intentos_envio(None)


class ValidarTelefonoNoneTest(TestCase):
    def test_telefono_none(self):
        """Line 317: telefono=None."""
        with self.assertRaises(ValidationError):
            validar_telefono_sms(None)


class ValidarMensajeSmsNoneTest(TestCase):
    def test_mensaje_sms_none(self):
        """Line 339: mensaje=None."""
        with self.assertRaises(ValidationError):
            validar_mensaje_sms(None)


class ValidarEstadoSmsNoneTest(TestCase):
    def test_estado_sms_none(self):
        """Line 352: estado=None."""
        with self.assertRaises(ValidationError):
            validar_estado_sms(None)


class ValidarCostoSmsInvalidTest(TestCase):
    def test_costo_invalido_conversion(self):
        """Lines 367-368: Decimal('abc') → ValidationError."""
        with self.assertRaises(ValidationError):
            validar_costo_sms("no_numero")

    def test_costo_muchos_decimales(self):
        """Line 378: costo has more than 2 decimals."""
        with self.assertRaises(ValidationError):
            validar_costo_sms(Decimal("10.123"))


class ValidarCodigoTemplateNoneTest(TestCase):
    def test_codigo_none(self):
        """Line 389: codigo=None."""
        with self.assertRaises(ValidationError):
            validar_codigo_template(None)


class ValidarNombreTemplateNoneTest(TestCase):
    def test_nombre_none(self):
        """Line 406: nombre=None."""
        with self.assertRaises(ValidationError):
            validar_nombre_template(None)


class ValidarVariablesTemplateNoneTest(TestCase):
    def test_variables_none(self):
        """Line 418: variables=None."""
        with self.assertRaises(ValidationError):
            validar_variables_template(None)

    def test_variables_json_invalido(self):
        """Lines 424-425: invalid JSON string → JSONDecodeError."""
        with self.assertRaises(ValidationError):
            validar_variables_template("{invalid json")

    def test_variable_no_string(self):
        """Line 438: variable inside list is not a string."""
        with self.assertRaises(ValidationError):
            validar_variables_template([123, "nombre"])


class ValidarCategoriaNoneTest(TestCase):
    def test_categoria_none(self):
        """Line 446: categoria=None."""
        with self.assertRaises(ValidationError):
            validar_categoria_template(None)


class ValidarCuerpoHtmlNoneTest(TestCase):
    def test_cuerpo_html_none(self):
        """Line 469: cuerpo_html=None."""
        with self.assertRaises(ValidationError):
            validar_cuerpo_html_template(None)


class ValidarNombreCampanaNoneTest(TestCase):
    def test_nombre_campana_none(self):
        """Line 486: nombre_campana=None."""
        with self.assertRaises(ValidationError):
            validar_nombre_campana(None)


class ValidarTipoCampanaNoneTest(TestCase):
    def test_tipo_campana_none(self):
        """Line 498: tipo_campana=None."""
        with self.assertRaises(ValidationError):
            validar_tipo_campana(None)


class ValidarEstadoCampanaNoneTest(TestCase):
    def test_estado_campana_none(self):
        """Line 508: estado_campana=None."""
        with self.assertRaises(ValidationError):
            validar_estado_campana(None)


class ValidarTotalDestinatariosNoneTest(TestCase):
    def test_total_none(self):
        """Line 519: total=None (not int)."""
        with self.assertRaises(ValidationError):
            validar_total_destinatarios(None)


class ValidarNombreAlertaNoneTest(TestCase):
    def test_nombre_alerta_none(self):
        """Line 536: nombre=None."""
        with self.assertRaises(ValidationError):
            validar_nombre_alerta(None)


class ValidarTipoAlertaNoneTest(TestCase):
    def test_tipo_alerta_none(self):
        """Line 548: tipo=None."""
        with self.assertRaises(ValidationError):
            validar_tipo_alerta(None)


class ValidarCriticidadNoneTest(TestCase):
    def test_criticidad_none(self):
        """Line 559: criticidad=None."""
        with self.assertRaises(ValidationError):
            validar_criticidad_alerta(None)


class ValidarFrecuenciaNoneTest(TestCase):
    def test_frecuencia_none(self):
        """Line 572: value=None (not int)."""
        with self.assertRaises(ValidationError):
            validar_frecuencia_minutos(None)


class ValidarTipoAlertaSistemaNoneTest(TestCase):
    def test_tipo_alerta_sistema_none(self):
        """Line 589: tipo=None."""
        with self.assertRaises(ValidationError):
            validar_tipo_alerta_sistema(None)


class ValidarMensajeAlertaSistemaNoneTest(TestCase):
    def test_mensaje_alerta_none(self):
        """Line 600: mensaje=None."""
        with self.assertRaises(ValidationError):
            validar_mensaje_alerta_sistema(None)


class ValidarEstadoAlertaSistemaNoStringTest(TestCase):
    def test_estado_not_string_not_none(self):
        """Line 616: estado not None and not string."""
        with self.assertRaises(ValidationError):
            validar_estado_alerta_sistema(42)


class ValidarDatosContextoNoneTest(TestCase):
    def test_datos_none(self):
        """Line 632: datos=None."""
        with self.assertRaises(ValidationError):
            validar_datos_contexto_historial(None)

    def test_datos_json_invalido(self):
        """Lines 638-639: invalid JSON string → JSONDecodeError."""
        with self.assertRaises(ValidationError):
            validar_datos_contexto_historial("{invalid json")


class ValidarUsuarioAnomaliaNoneTest(TestCase):
    def test_usuario_none(self):
        """Line 660: usuario=None."""
        with self.assertRaises(ValidationError):
            validar_usuario_anomalia(None)


class ValidarTipoAnomaliaNoneTest(TestCase):
    def test_tipo_anomalia_none(self):
        """Line 672: tipo=None."""
        with self.assertRaises(ValidationError):
            validar_tipo_anomalia(None)


class ValidarIpAddressNoStringTest(TestCase):
    def test_ip_not_string_not_none(self):
        """Line 693: value not None and not string."""
        with self.assertRaises(ValidationError):
            validar_ip_address(12345)


class ValidarNivelRiesgoNoneTest(TestCase):
    def test_nivel_none(self):
        """Line 716: nivel=None."""
        with self.assertRaises(ValidationError):
            validar_nivel_riesgo_anomalia(None)


class ValidarTipoUsuarioRestriccionNoneTest(TestCase):
    def test_tipo_usuario_none(self):
        """Line 742: tipo=None."""
        with self.assertRaises(ValidationError):
            validar_tipo_usuario_restriccion(None)


class ValidarDiaSemanaRestriccionNoneTest(TestCase):
    def test_dia_none(self):
        """Line 755: dia=None."""
        with self.assertRaises(ValidationError):
            validar_dia_semana_restriccion(None)

