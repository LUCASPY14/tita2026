"""
Validadores para la aplicación Notificaciones
Incluye validaciones para emails, SMS, plantillas, campañas y alertas
"""

import json
import re
from datetime import time
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator

# =============================================================================
# VALIDADORES - NOTIFICACIONES PORTAL
# =============================================================================


def validar_tipo_notificacion_portal(value):
    """Valida el tipo de notificación del portal"""
    if not value or not isinstance(value, str):
        raise ValidationError("El tipo de notificación es requerido.")

    value = value.strip()
    if len(value) < 3:
        raise ValidationError("El tipo debe tener al menos 3 caracteres.")
    if len(value) > 50:
        raise ValidationError("El tipo no puede exceder 50 caracteres.")

    tipos_validos = [
        "alerta",
        "recordatorio",
        "venta",
        "compra",
        "inventario",
        "pago",
        "saldo",
        "sistema",
        "promocion",
        "informativa",
    ]

    if value.lower() not in tipos_validos:
        tipos_str = ", ".join(tipos_validos)
        raise ValidationError(f"Tipo de notificación no válido. Tipos permitidos: {tipos_str}")


def validar_titulo_notificacion(value):
    """Valida el título de la notificación"""
    if not value or not isinstance(value, str):
        raise ValidationError("El título es requerido.")

    value = value.strip()
    if len(value) < 5:
        raise ValidationError("El título debe tener al menos 5 caracteres.")
    if len(value) > 255:
        raise ValidationError("El título no puede exceder 255 caracteres.")

    # Solo permitir caracteres alfanuméricos, espacios y puntuación básica
    patron = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,;:¿?¡!()-]+$"
    if not re.match(patron, value):
        raise ValidationError(
            "El título contiene caracteres no permitidos. " "Solo se permiten letras, números y puntuación básica."
        )


def validar_mensaje_notificacion(value):
    """Valida el mensaje de la notificación"""
    if not value or not isinstance(value, str):
        raise ValidationError("El mensaje es requerido.")

    value = value.strip()
    if len(value) < 10:
        raise ValidationError("El mensaje debe tener al menos 10 caracteres.")
    if len(value) > 5000:
        raise ValidationError("El mensaje no puede exceder 5000 caracteres.")


def validar_leida_notificacion(value):
    """Valida el estado de lectura (0 o 1)"""
    if value not in [0, 1]:
        raise ValidationError("El estado de lectura debe ser 0 (no leída) o 1 (leída).")


# =============================================================================
# VALIDADORES - NOTIFICACIONES SALDO
# =============================================================================


def validar_saldo_actual(value):
    """Valida el saldo actual en notificaciones de saldo"""
    if value is None:
        raise ValidationError("El saldo actual es requerido.")

    try:
        saldo = Decimal(str(value))
    except (ValueError, InvalidOperation):
        raise ValidationError("El saldo debe ser un número válido.")

    if saldo < Decimal("0.00"):
        raise ValidationError("El saldo no puede ser negativo.")

    if saldo > Decimal("99999999.99"):
        raise ValidationError("El saldo no puede exceder ₲99,999,999.99")

    # Máximo 2 decimales
    if saldo.as_tuple().exponent < -2:
        raise ValidationError("El saldo no puede tener más de 2 decimales.")


def validar_enviada_email(value):
    """Valida el estado de envío de email (0 o 1)"""
    if value not in [0, 1]:
        raise ValidationError("El estado de envío de email debe ser 0 (no enviado) o 1 (enviado).")


def validar_enviada_sms(value):
    """Valida el estado de envío de SMS (0 o 1)"""
    if value not in [0, 1]:
        raise ValidationError("El estado de envío de SMS debe ser 0 (no enviado) o 1 (enviado).")


# =============================================================================
# VALIDADORES - SOLICITUDES NOTIFICACIÓN
# =============================================================================


def validar_saldo_alerta(value):
    """Valida el saldo de alerta en solicitudes de notificación"""
    if value is None:
        raise ValidationError("El saldo de alerta es requerido.")

    try:
        saldo = Decimal(str(value))
    except (ValueError, InvalidOperation):
        raise ValidationError("El saldo de alerta debe ser un número válido.")

    if saldo <= Decimal("0.00"):
        raise ValidationError("El saldo de alerta debe ser mayor a cero.")

    if saldo > Decimal("9999999.99"):
        raise ValidationError("El saldo de alerta no puede exceder ₲9,999,999.99")

    # Máximo 2 decimales
    if saldo.as_tuple().exponent < -2:
        raise ValidationError("El saldo de alerta no puede tener más de 2 decimales.")


def validar_destino_notificacion(value):
    """Valida el destino de la notificación (Email o SMS)"""
    if not value or not isinstance(value, str):
        raise ValidationError("El destino es requerido.")

    destinos_validos = ["Email", "SMS", "Ambos"]
    if value not in destinos_validos:
        raise ValidationError(f"Destino no válido. Debe ser uno de: {', '.join(destinos_validos)}")


def validar_estado_solicitud(value):
    """Valida el estado de la solicitud de notificación"""
    if value is None:
        return  # Es opcional

    if not isinstance(value, str):
        raise ValidationError("El estado debe ser una cadena de texto.")

    estados_validos = ["Pendiente", "Enviada", "Cancelada"]
    if value not in estados_validos:
        raise ValidationError(f"Estado no válido. Debe ser uno de: {', '.join(estados_validos)}")


# =============================================================================
# VALIDADORES - PREFERENCIAS NOTIFICACIÓN
# =============================================================================


def validar_tipo_preferencia_notificacion(value):
    """Valida el tipo de notificación para preferencias"""
    if not value or not isinstance(value, str):
        raise ValidationError("El tipo de notificación es requerido.")

    value = value.strip()
    if len(value) < 3:
        raise ValidationError("El tipo debe tener al menos 3 caracteres.")
    if len(value) > 50:
        raise ValidationError("El tipo no puede exceder 50 caracteres.")

    tipos_validos = [
        "compras",
        "ventas",
        "inventario",
        "promociones",
        "alertas_sistema",
        "recordatorios",
        "reportes",
    ]

    if value.lower() not in tipos_validos:
        tipos_str = ", ".join(tipos_validos)
        raise ValidationError(f"Tipo de preferencia no válido. Tipos permitidos: {tipos_str}")


def validar_email_activo(value):
    """Valida si las notificaciones por email están activas"""
    if value not in [0, 1]:
        raise ValidationError("Email estado debe ser 0 (inactivo) o 1 (estado).")


def validar_push_activo(value):
    """Valida si las notificaciones push están activas"""
    if value not in [0, 1]:
        raise ValidationError("Push estado debe ser 0 (inactivo) o 1 (estado).")


# =============================================================================
# VALIDADORES - EMAILS ENVIADOS
# =============================================================================


def validar_email_destinatario(value):
    """Valida el email del destinatario"""
    if not value or not isinstance(value, str):
        raise ValidationError("El email es requerido.")

    value = value.strip()
    if len(value) > 254:
        raise ValidationError("El email no puede exceder 254 caracteres.")

    # Validación usando el validador de Django
    email_validator = EmailValidator(message="El email no es válido.")
    email_validator(value)


def validar_nombre_destinatario(value):
    """Valida el nombre del destinatario"""
    if not value or not isinstance(value, str):
        raise ValidationError("El nombre del destinatario es requerido.")

    value = value.strip()
    if len(value) < 2:
        raise ValidationError("El nombre debe tener al menos 2 caracteres.")
    if len(value) > 100:
        raise ValidationError("El nombre no puede exceder 100 caracteres.")

    # Permitir letras, espacios, tildes y algunos caracteres especiales
    patron = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\'-]+$"
    if not re.match(patron, value):
        raise ValidationError(
            "El nombre contiene caracteres no permitidos. "
            "Solo se permiten letras, espacios, tildes, apóstrofes y guiones."
        )


def validar_asunto_email(value):
    """Valida el asunto del email"""
    if not value or not isinstance(value, str):
        raise ValidationError("El asunto es requerido.")

    value = value.strip()
    if len(value) < 3:
        raise ValidationError("El asunto debe tener al menos 3 caracteres.")
    if len(value) > 200:
        raise ValidationError("El asunto no puede exceder 200 caracteres.")


def validar_cuerpo_email(value):
    """Valida el cuerpo del email"""
    if not value or not isinstance(value, str):
        raise ValidationError("El cuerpo del email es requerido.")

    value = value.strip()
    if len(value) < 10:
        raise ValidationError("El cuerpo debe tener al menos 10 caracteres.")
    if len(value) > 50000:
        raise ValidationError("El cuerpo no puede exceder 50,000 caracteres.")


def validar_estado_email(value):
    """Valida el estado del email enviado"""
    if not value or not isinstance(value, str):
        raise ValidationError("El estado es requerido.")

    estados_validos = [
        "Pendiente",
        "Enviado",
        "Entregado",
        "Fallido",
        "Rebotado",
        "Abierto",
        "Marcado_Spam",
    ]

    if value not in estados_validos:
        raise ValidationError(f"Estado no válido. Debe ser uno de: {', '.join(estados_validos)}")


def validar_intentos_envio(value):
    """Valida el número de intentos de envío"""
    if value is None or not isinstance(value, int):
        raise ValidationError("El número de intentos debe ser un entero.")

    if value < 0:
        raise ValidationError("El número de intentos no puede ser negativo.")

    if value > 10:
        raise ValidationError("El número de intentos no puede exceder 10.")


# =============================================================================
# VALIDADORES - SMS ENVIADOS
# =============================================================================


def validar_telefono_sms(value):
    """Valida el número de teléfono para SMS"""
    if not value or not isinstance(value, str):
        raise ValidationError("El número de teléfono es requerido.")

    value = value.strip()

    # Eliminar caracteres comunes de formateo
    telefono_limpio = re.sub(r"[\s\-\(\)\+]", "", value)

    # Validar que solo contenga dígitos después de limpiar
    if not telefono_limpio.isdigit():
        raise ValidationError("El teléfono debe contener solo números.")

    # Longitud válida para números de Paraguay
    if len(telefono_limpio) < 9:
        raise ValidationError("El número de teléfono debe tener al menos 9 dígitos.")

    if len(telefono_limpio) > 20:
        raise ValidationError("El número de teléfono no puede exceder 20 dígitos.")


def validar_mensaje_sms(value):
    """Valida el mensaje SMS (máximo 160 caracteres)"""
    if not value or not isinstance(value, str):
        raise ValidationError("El mensaje es requerido.")

    value = value.strip()
    if len(value) < 5:
        raise ValidationError("El mensaje debe tener al menos 5 caracteres.")

    if len(value) > 160:
        raise ValidationError("El mensaje no puede exceder 160 caracteres (límite SMS).")


def validar_estado_sms(value):
    """Valida el estado del SMS enviado"""
    if not value or not isinstance(value, str):
        raise ValidationError("El estado es requerido.")

    estados_validos = ["Pendiente", "Enviado", "Entregado", "Fallido", "Rechazado"]

    if value not in estados_validos:
        raise ValidationError(f"Estado no válido. Debe ser uno de: {', '.join(estados_validos)}")


def validar_costo_sms(value):
    """Valida el costo del SMS"""
    if value is None:
        return  # Es opcional

    try:
        costo = Decimal(str(value))
    except (ValueError, InvalidOperation):
        raise ValidationError("El costo debe ser un número válido.")

    if costo < Decimal("0.00"):
        raise ValidationError("El costo no puede ser negativo.")

    if costo > Decimal("99999.99"):
        raise ValidationError("El costo no puede exceder ₲99,999.99")

    # Máximo 2 decimales
    if costo.as_tuple().exponent < -2:
        raise ValidationError("El costo no puede tener más de 2 decimales.")


# =============================================================================
# VALIDADORES - PLANTILLAS EMAIL
# =============================================================================


def validar_codigo_template(value):
    """Valida el código único de la plantilla"""
    if not value or not isinstance(value, str):
        raise ValidationError("El código es requerido.")

    value = value.strip()
    if len(value) < 3:
        raise ValidationError("El código debe tener al menos 3 caracteres.")
    if len(value) > 50:
        raise ValidationError("El código no puede exceder 50 caracteres.")

    # Solo permitir letras, números y guiones bajos
    patron = r"^[a-zA-Z0-9_]+$"
    if not re.match(patron, value):
        raise ValidationError("El código solo puede contener letras, números y guiones bajos.")


def validar_nombre_template(value):
    """Valida el nombre de la plantilla"""
    if not value or not isinstance(value, str):
        raise ValidationError("El nombre es requerido.")

    value = value.strip()
    if len(value) < 3:
        raise ValidationError("El nombre debe tener al menos 3 caracteres.")
    if len(value) > 100:
        raise ValidationError("El nombre no puede exceder 100 caracteres.")


def validar_variables_template(value):
    """Valida las variables de la plantilla (JSON)"""
    if value is None:
        raise ValidationError("Las variables son requeridas (puede ser lista vacía).")

    # Si es string, intentar parsear como JSON
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            raise ValidationError("Las variables deben ser un JSON válido.")

    # Debe ser una lista
    if not isinstance(value, list):
        raise ValidationError("Las variables deben ser una lista JSON.")

    # Máximo 50 variables
    if len(value) > 50:
        raise ValidationError("No se pueden definir más de 50 variables.")

    # Cada variable debe ser un string
    for var in value:
        if not isinstance(var, str):
            raise ValidationError("Cada variable debe ser una cadena de texto.")
        if len(var) < 2 or len(var) > 50:
            raise ValidationError("Cada variable debe tener entre 2 y 50 caracteres.")


def validar_categoria_template(value):
    """Valida la categoría de la plantilla"""
    if not value or not isinstance(value, str):
        raise ValidationError("La categoría es requerida.")

    categorias_validas = [
        "Ventas",
        "Compras",
        "Inventario",
        "Promociones",
        "Recordatorios",
        "Alertas",
        "Reportes",
        "Bienvenida",
        "Otro",
    ]

    if value not in categorias_validas:
        raise ValidationError(f"Categoría no válida. Debe ser una de: {', '.join(categorias_validas)}")


def validar_cuerpo_html_template(value):
    """Valida el cuerpo HTML de la plantilla de email"""
    if not value or not isinstance(value, str):
        raise ValidationError("El cuerpo HTML es requerido.")

    value = value.strip()
    if len(value) < 20:
        raise ValidationError("El cuerpo HTML debe tener al menos 20 caracteres.")
    if len(value) > 100000:
        raise ValidationError("El cuerpo HTML no puede exceder 100,000 caracteres.")


# =============================================================================
# VALIDADORES - CAMPAÑAS COMUNICACIÓN
# =============================================================================


def validar_nombre_campana(value):
    """Valida el nombre de la campaña"""
    if not value or not isinstance(value, str):
        raise ValidationError("El nombre de la campaña es requerido.")

    value = value.strip()
    if len(value) < 5:
        raise ValidationError("El nombre debe tener al menos 5 caracteres.")
    if len(value) > 100:
        raise ValidationError("El nombre no puede exceder 100 caracteres.")


def validar_tipo_campana(value):
    """Valida el tipo de campaña"""
    if not value or not isinstance(value, str):
        raise ValidationError("El tipo de campaña es requerido.")

    tipos_validos = ["Email", "SMS", "Mixta", "Push"]
    if value not in tipos_validos:
        raise ValidationError(f"Tipo no válido. Debe ser uno de: {', '.join(tipos_validos)}")


def validar_estado_campana(value):
    """Valida el estado de la campaña"""
    if not value or not isinstance(value, str):
        raise ValidationError("El estado es requerido.")

    estados_validos = ["Borrador", "Programada", "Enviando", "Enviada", "Cancelada", "Fallida"]

    if value not in estados_validos:
        raise ValidationError(f"Estado no válido. Debe ser uno de: {', '.join(estados_validos)}")


def validar_total_destinatarios(value):
    """Valida el total de destinatarios de la campaña"""
    if value is None or not isinstance(value, int):
        raise ValidationError("El total de destinatarios debe ser un entero.")

    if value < 0:
        raise ValidationError("El total de destinatarios no puede ser negativo.")

    if value > 1000000:
        raise ValidationError("El total de destinatarios no puede exceder 1,000,000.")


# =============================================================================
# VALIDADORES - ALERTAS AUTOMÁTICAS
# =============================================================================


def validar_nombre_alerta(value):
    """Valida el nombre de la alerta automática"""
    if not value or not isinstance(value, str):
        raise ValidationError("El nombre de la alerta es requerido.")

    value = value.strip()
    if len(value) < 5:
        raise ValidationError("El nombre debe tener al menos 5 caracteres.")
    if len(value) > 100:
        raise ValidationError("El nombre no puede exceder 100 caracteres.")


def validar_tipo_alerta(value):
    """Valida el tipo de alerta automática"""
    if not value or not isinstance(value, str):
        raise ValidationError("El tipo de alerta es requerido.")

    tipos_validos = ["Inventario", "Ventas", "Compras", "Saldo", "Sistema", "Seguridad"]

    if value not in tipos_validos:
        raise ValidationError(f"Tipo no válido. Debe ser uno de: {', '.join(tipos_validos)}")


def validar_criticidad_alerta(value):
    """Valida la criticidad de la alerta"""
    if not value or not isinstance(value, str):
        raise ValidationError("La criticidad es requerida.")

    criticidades_validas = ["Baja", "Media", "Alta", "Crítica"]

    if value not in criticidades_validas:
        raise ValidationError(f"Criticidad no válida. Debe ser una de: {', '.join(criticidades_validas)}")


def validar_frecuencia_minutos(value):
    """Valida la frecuencia mínima de verificación en minutos"""
    if value is None or not isinstance(value, int):
        raise ValidationError("La frecuencia mínima debe ser un entero.")

    if value < 1:
        raise ValidationError("La frecuencia mínima debe ser al menos 1 minuto.")

    if value > 43200:  # 30 días en minutos
        raise ValidationError("La frecuencia mínima no puede exceder 43,200 minutos (30 días).")


# =============================================================================
# VALIDADORES - ALERTAS SISTEMA
# =============================================================================


def validar_tipo_alerta_sistema(value):
    """Valida el tipo de alerta del sistema"""
    if not value or not isinstance(value, str):
        raise ValidationError("El tipo de alerta es requerido.")

    tipos_validos = ["error", "warning", "info", "success", "critical"]

    if value.lower() not in tipos_validos:
        raise ValidationError(f"Tipo no válido. Debe ser uno de: {', '.join(tipos_validos)}")


def validar_mensaje_alerta_sistema(value):
    """Valida el mensaje de la alerta del sistema"""
    if not value or not isinstance(value, str):
        raise ValidationError("El mensaje es requerido.")

    value = value.strip()
    if len(value) < 10:
        raise ValidationError("El mensaje debe tener al menos 10 caracteres.")

    if len(value) > 500:
        raise ValidationError("El mensaje no puede exceder 500 caracteres.")


def validar_estado_alerta_sistema(value):
    """Valida el estado de la alerta del sistema"""
    if value is None:
        return  # Es opcional

    if not isinstance(value, str):
        raise ValidationError("El estado debe ser una cadena de texto.")

    estados_validos = ["Pendiente", "Resuelta", "Ignorada"]

    if value not in estados_validos:
        raise ValidationError(f"Estado no válido. Debe ser uno de: {', '.join(estados_validos)}")


# =============================================================================
# VALIDADORES - HISTORIAL ALERTAS
# =============================================================================


def validar_datos_contexto_historial(value):
    """Valida los datos de contexto del historial de alertas (JSON)"""
    if value is None:
        raise ValidationError("Los datos de contexto son requeridos (puede ser dict vacío).")

    # Si es string, intentar parsear como JSON
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            raise ValidationError("Los datos de contexto deben ser un JSON válido.")

    # Debe ser un diccionario
    if not isinstance(value, dict):
        raise ValidationError("Los datos de contexto deben ser un objeto JSON.")


def validar_resuelto_historial(value):
    """Valida el estado de resolución del historial (0 o 1)"""
    if value not in [0, 1]:
        raise ValidationError("El estado de resolución debe ser 0 (no resuelto) o 1 (resuelto).")


# =============================================================================
# VALIDADORES - ANOMALÍAS DETECTADAS
# =============================================================================


def validar_usuario_anomalia(value):
    """Valida el usuario en anomalías detectadas"""
    if not value or not isinstance(value, str):
        raise ValidationError("El usuario es requerido.")

    value = value.strip()
    if len(value) < 3:
        raise ValidationError("El usuario debe tener al menos 3 caracteres.")
    if len(value) > 100:
        raise ValidationError("El usuario no puede exceder 100 caracteres.")


def validar_tipo_anomalia(value):
    """Valida el tipo de anomalía"""
    if not value or not isinstance(value, str):
        raise ValidationError("El tipo de anomalía es requerido.")

    tipos_validos = [
        "acceso_inusual",
        "intentos_fallidos",
        "cambio_horario",
        "ip_sospechosa",
        "múltiples_sesiones",
        "actividad_alta",
    ]

    if value.lower() not in tipos_validos:
        raise ValidationError(f"Tipo no válido. Debe ser uno de: {', '.join(tipos_validos)}")


def validar_ip_address(value):
    """Valida la dirección IP"""
    if value is None:
        return  # Es opcional

    if not isinstance(value, str):
        raise ValidationError("La dirección IP debe ser una cadena de texto.")

    value = value.strip()

    # Validar formato IPv4
    patron_ipv4 = r"^(\d{1,3}\.){3}\d{1,3}$"
    # Validar formato IPv6 simplificado
    patron_ipv6 = r"^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$"

    if not (re.match(patron_ipv4, value) or re.match(patron_ipv6, value)):
        raise ValidationError("La dirección IP no tiene un formato válido (IPv4 o IPv6).")

    # Para IPv4, validar rangos
    if re.match(patron_ipv4, value):
        octetos = value.split(".")
        for octeto in octetos:
            if int(octeto) > 255:
                raise ValidationError("La dirección IPv4 tiene octetos inválidos (0-255).")


def validar_nivel_riesgo_anomalia(value):
    """Valida el nivel de riesgo de la anomalía"""
    if not value or not isinstance(value, str):
        raise ValidationError("El nivel de riesgo es requerido.")

    niveles_validos = ["Bajo", "Medio", "Alto", "Crítico"]

    if value not in niveles_validos:
        raise ValidationError(f"Nivel de riesgo no válido. Debe ser uno de: {', '.join(niveles_validos)}")


def validar_notificado_anomalia(value):
    """Valida si la anomalía fue notificada (0 o 1)"""
    if value not in [0, 1]:
        raise ValidationError("El estado de notificación debe ser 0 (no notificado) o 1 (notificado).")


# =============================================================================
# VALIDADORES - RESTRICCIONES HORARIAS
# =============================================================================


def validar_tipo_usuario_restriccion(value):
    """Valida el tipo de usuario para restricciones horarias"""
    if not value or not isinstance(value, str):
        raise ValidationError("El tipo de usuario es requerido.")

    tipos_validos = ["Empleado", "Cliente", "Proveedor", "Administrador", "Todos"]

    if value not in tipos_validos:
        raise ValidationError(f"Tipo de usuario no válido. Debe ser uno de: {', '.join(tipos_validos)}")


def validar_dia_semana_restriccion(value):
    """Valida el día de la semana para restricciones"""
    if not value or not isinstance(value, str):
        raise ValidationError("El día de la semana es requerido.")

    dias_validos = [
        "Lunes",
        "Martes",
        "Miércoles",
        "Jueves",
        "Viernes",
        "Sábado",
        "Domingo",
        "Todos",
    ]

    if value not in dias_validos:
        raise ValidationError(f"Día de la semana no válido. Debe ser uno de: {', '.join(dias_validos)}")


def validar_rango_horario_restriccion(hora_inicio, hora_fin):
    """Valida que el rango horario sea coherente"""
    if not isinstance(hora_inicio, time):
        raise ValidationError("La hora de inicio debe ser un objeto time.")

    if not isinstance(hora_fin, time):
        raise ValidationError("La hora de fin debe ser un objeto time.")

    if hora_inicio >= hora_fin:
        raise ValidationError("La hora de inicio debe ser anterior a la hora de fin.")
