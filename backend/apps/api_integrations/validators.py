"""
Validadores del módulo API Integrations
Validación de integraciones con APIs externas, webhooks, credenciales y logs
"""

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from datetime import datetime
import re
import json

# ============================================================================
# VALIDADORES DE PROVEEDORES API
# ============================================================================


def validar_nombre_proveedor(valor):
    """Valida el nombre del proveedor de API (3-100 caracteres)"""
    if not valor or not isinstance(valor, str):
        raise ValidationError("El nombre del proveedor es requerido.")

    valor = valor.strip()
    if len(valor) < 3:
        raise ValidationError("El nombre del proveedor debe tener al menos 3 caracteres.")
    if len(valor) > 100:
        raise ValidationError("El nombre del proveedor no puede exceder 100 caracteres.")

    return valor


def validar_descripcion_proveedor(valor):
    """Valida la descripción del proveedor (10-5000 caracteres)"""
    if not valor or not isinstance(valor, str):
        raise ValidationError("La descripción del proveedor es requerida.")

    valor = valor.strip()
    if len(valor) < 10:
        raise ValidationError("La descripción debe tener al menos 10 caracteres.")
    if len(valor) > 5000:
        raise ValidationError("La descripción no puede exceder 5000 caracteres.")

    return valor


def validar_tipo_servicio(valor):
    """Valida el tipo de servicio API"""
    if not valor or not isinstance(valor, str):
        raise ValidationError("El tipo de servicio es requerido.")

    tipos_validos = ["REST", "SOAP", "GraphQL", "WebSocket", "gRPC", "XML-RPC", "OData"]

    if valor not in tipos_validos:
        raise ValidationError(f'El tipo de servicio debe ser uno de: {", ".join(tipos_validos)}.')

    return valor


def validar_url_base(valor):
    """Valida la URL base del proveedor API"""
    if not valor or not isinstance(valor, str):
        raise ValidationError("La URL base es requerida.")

    valor = valor.strip()

    # Validar que comience con http:// o https://
    if not valor.startswith(("http://", "https://")):
        raise ValidationError("La URL base debe comenzar con http:// o https://.")

    # Validar formato URL
    url_validator = URLValidator()
    try:
        url_validator(valor)
    except ValidationError:
        raise ValidationError("La URL base no tiene un formato válido.")

    if len(valor) > 200:
        raise ValidationError("La URL base no puede exceder 200 caracteres.")

    return valor


def validar_version(valor):
    """Valida la versión del API (semantic versioning: v1.0.0)"""
    if not valor or not isinstance(valor, str):
        raise ValidationError("La versión del API es requerida.")

    valor = valor.strip()

    # Permitir formatos: v1.0.0, 1.0.0, v1, 2.0, etc.
    patron = re.compile(r"^v?\d+(\.\d+)*$")

    if not patron.match(valor):
        raise ValidationError(
            "La versión debe seguir el formato semantic versioning (ej: v1.0.0, 2.1, v3)."
        )

    if len(valor) > 20:
        raise ValidationError("La versión no puede exceder 20 caracteres.")

    return valor


def validar_documentacion_proveedor(valor):
    """Valida la URL de documentación del proveedor (opcional)"""
    if valor is None or valor == "":
        return valor

    if not isinstance(valor, str):
        raise ValidationError("La URL de documentación debe ser texto.")

    valor = valor.strip()

    # Validar formato URL
    url_validator = URLValidator()
    try:
        url_validator(valor)
    except ValidationError:
        raise ValidationError("La URL de documentación no tiene un formato válido.")

    if len(valor) > 200:
        raise ValidationError("La URL de documentación no puede exceder 200 caracteres.")

    return valor


def validar_tipo_auth(valor):
    """Valida el tipo de autenticación"""
    if not valor or not isinstance(valor, str):
        raise ValidationError("El tipo de autenticación es requerido.")

    tipos_validos = ["API_KEY", "OAuth2", "Bearer", "Basic", "JWT", "None", "HMAC", "Custom"]

    if valor not in tipos_validos:
        raise ValidationError(
            f'El tipo de autenticación debe ser uno de: {", ".join(tipos_validos)}.'
        )

    return valor


def validar_config_auth(valor):
    """Valida la configuración de autenticación (JSON dict)"""
    if valor is None:
        raise ValidationError("La configuración de autenticación es requerida.")

    if not isinstance(valor, dict):
        raise ValidationError("La configuración de autenticación debe ser un objeto JSON (dict).")

    # Validar que no esté vacío
    if len(valor) == 0:
        raise ValidationError("La configuración de autenticación no puede estar vacía.")

    # Validar tamaño del JSON serializado
    try:
        json_str = json.dumps(valor)
        if len(json_str) > 10000:
            raise ValidationError(
                "La configuración de autenticación es demasiado grande (max 10000 caracteres)."
            )
    except (TypeError, ValueError) as e:
        raise ValidationError(f"La configuración de autenticación no es JSON válido: {str(e)}")

    return valor


def validar_timeout(valor):
    """Valida el timeout en segundos (1-300)"""
    if valor is None:
        raise ValidationError("El timeout es requerido.")

    try:
        timeout = int(valor)
    except (TypeError, ValueError):
        raise ValidationError("El timeout debe ser un número entero.")

    if timeout < 1:
        raise ValidationError("El timeout debe ser al menos 1 segundo.")
    if timeout > 300:
        raise ValidationError("El timeout no puede exceder 300 segundos (5 minutos).")

    return timeout


def validar_max_reintentos(valor):
    """Valida el máximo de reintentos (0-10)"""
    if valor is None:
        raise ValidationError("El máximo de reintentos es requerido.")

    try:
        reintentos = int(valor)
    except (TypeError, ValueError):
        raise ValidationError("El máximo de reintentos debe ser un número entero.")

    if reintentos < 0:
        raise ValidationError("El máximo de reintentos no puede ser negativo.")
    if reintentos > 10:
        raise ValidationError("El máximo de reintentos no puede exceder 10.")

    return reintentos


def validar_activo_proveedor(valor):
    """Valida el campo activo del proveedor"""
    if not isinstance(valor, bool):
        raise ValidationError("El campo activo debe ser un valor booleano (True/False).")

    return valor


# ============================================================================
# VALIDADORES DE ENDPOINTS API
# ============================================================================


def validar_nombre_endpoint(valor):
    """Valida el nombre del endpoint (3-100 caracteres)"""
    if not valor or not isinstance(valor, str):
        raise ValidationError("El nombre del endpoint es requerido.")

    valor = valor.strip()
    if len(valor) < 3:
        raise ValidationError("El nombre del endpoint debe tener al menos 3 caracteres.")
    if len(valor) > 100:
        raise ValidationError("El nombre del endpoint no puede exceder 100 caracteres.")

    return valor


def validar_descripcion_endpoint(valor):
    """Valida la descripción del endpoint (10-2000 caracteres)"""
    if not valor or not isinstance(valor, str):
        raise ValidationError("La descripción del endpoint es requerida.")

    valor = valor.strip()
    if len(valor) < 10:
        raise ValidationError("La descripción debe tener al menos 10 caracteres.")
    if len(valor) > 2000:
        raise ValidationError("La descripción no puede exceder 2000 caracteres.")

    return valor


def validar_path_endpoint(valor):
    """Valida el path del endpoint (debe comenzar con /, sin espacios)"""
    if not valor or not isinstance(valor, str):
        raise ValidationError("El path del endpoint es requerido.")

    valor = valor.strip()

    if not valor.startswith("/"):
        raise ValidationError("El path del endpoint debe comenzar con /.")

    if " " in valor:
        raise ValidationError("El path del endpoint no puede contener espacios.")

    # Validar caracteres permitidos: /a-zA-Z0-9_-{}
    patron = re.compile(r"^/[a-zA-Z0-9/_\-{}]*$")
    if not patron.match(valor):
        raise ValidationError(
            "El path del endpoint solo puede contener letras, números, guiones, guiones bajos, llaves y barras."
        )

    if len(valor) > 200:
        raise ValidationError("El path del endpoint no puede exceder 200 caracteres.")

    return valor


def validar_metodo_http(valor):
    """Valida el método HTTP"""
    if not valor or not isinstance(valor, str):
        raise ValidationError("El método HTTP es requerido.")

    metodos_validos = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]

    valor = valor.upper()

    if valor not in metodos_validos:
        raise ValidationError(f'El método HTTP debe ser uno de: {", ".join(metodos_validos)}.')

    return valor


def validar_headers_endpoint(valor):
    """Valida los headers del endpoint (JSON dict)"""
    if valor is None:
        raise ValidationError("Los headers del endpoint son requeridos.")

    if not isinstance(valor, dict):
        raise ValidationError("Los headers del endpoint deben ser un objeto JSON (dict).")

    # Permitir dict vacío (sin headers custom)

    # Validar que las claves sean strings válidos (nombres de headers)
    for key in valor.keys():
        if not isinstance(key, str):
            raise ValidationError("Los nombres de los headers deben ser strings.")
        if not re.match(r"^[A-Za-z0-9\-]+$", key):
            raise ValidationError(
                f'El nombre del header "{key}" contiene caracteres inválidos. '
                "Solo se permiten letras, números y guiones."
            )

    return valor


def validar_parametros_endpoint(valor):
    """Valida los parámetros del endpoint (JSON dict o list)"""
    if valor is None:
        raise ValidationError("Los parámetros del endpoint son requeridos.")

    if not isinstance(valor, (dict, list)):
        raise ValidationError("Los parámetros del endpoint deben ser un objeto o array JSON.")

    # Permitir estructura vacía

    return valor


def validar_schema_json(valor, nombre_campo="schema"):
    """Valida un schema JSON (request o response)"""
    if valor is None:
        # Permitir null para schemas opcionales
        return valor

    if not isinstance(valor, dict):
        raise ValidationError(f"El {nombre_campo} debe ser un objeto JSON (dict) o null.")

    # Validar tamaño del JSON
    try:
        json_str = json.dumps(valor)
        if len(json_str) > 50000:
            raise ValidationError(f"El {nombre_campo} es demasiado grande (max 50000 caracteres).")
    except (TypeError, ValueError) as e:
        raise ValidationError(f"El {nombre_campo} no es JSON válido: {str(e)}")

    return valor


def validar_schema_request(valor):
    """Valida el schema de request"""
    return validar_schema_json(valor, "schema de request")


def validar_schema_response(valor):
    """Valida el schema de response"""
    return validar_schema_json(valor, "schema de response")


def validar_cache_segundos(valor):
    """Valida los segundos de caché (0-86400 = 24 horas)"""
    if valor is None:
        raise ValidationError("Los segundos de caché son requeridos.")

    try:
        cache = int(valor)
    except (TypeError, ValueError):
        raise ValidationError("Los segundos de caché deben ser un número entero.")

    if cache < 0:
        raise ValidationError("Los segundos de caché no pueden ser negativos.")
    if cache > 86400:
        raise ValidationError("Los segundos de caché no pueden exceder 86400 (24 horas).")

    return cache


def validar_requiere_auth_endpoint(valor):
    """Valida si el endpoint requiere autenticación (0 o 1)"""
    if valor is None:
        raise ValidationError("El campo requiere_auth es requerido.")

    try:
        auth = int(valor)
    except (TypeError, ValueError):
        raise ValidationError("El campo requiere_auth debe ser 0 o 1.")

    if auth not in [0, 1]:
        raise ValidationError("El campo requiere_auth debe ser 0 (no) o 1 (sí).")

    return auth


def validar_activo_endpoint(valor):
    """Valida el campo activo del endpoint"""
    if not isinstance(valor, bool):
        raise ValidationError("El campo activo debe ser un valor booleano (True/False).")

    return valor


# ============================================================================
# VALIDADORES DE LOGS LLAMADAS API
# ============================================================================


def validar_timestamp_log(valor):
    """Valida que el timestamp no sea futuro"""
    if valor is None:
        raise ValidationError("El timestamp es requerido.")

    if not isinstance(valor, datetime):
        raise ValidationError("El timestamp debe ser un objeto datetime.")

    # Permitir timestamps con una tolerancia de 1 hora en el futuro (por diferencia de reloj)
    from datetime import timezone, timedelta

    ahora = datetime.now(timezone.utc)
    if valor > ahora + timedelta(hours=1):
        raise ValidationError("El timestamp no puede estar más de 1 hora en el futuro.")

    return valor


def validar_metodo_log(valor):
    """Valida el método HTTP del log"""
    if not valor or not isinstance(valor, str):
        raise ValidationError("El método HTTP es requerido.")

    metodos_validos = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]

    valor = valor.upper()

    if valor not in metodos_validos:
        raise ValidationError(f'El método HTTP debe ser uno de: {", ".join(metodos_validos)}.')

    return valor


def validar_url_log(valor):
    """Valida la URL del log (1-500 caracteres)"""
    if not valor or not isinstance(valor, str):
        raise ValidationError("La URL es requerida.")

    valor = valor.strip()

    if len(valor) < 1:
        raise ValidationError("La URL no puede estar vacía.")
    if len(valor) > 500:
        raise ValidationError("La URL no puede exceder 500 caracteres.")

    # Validar formato URL
    url_validator = URLValidator()
    try:
        url_validator(valor)
    except ValidationError:
        raise ValidationError("La URL no tiene un formato válido.")

    return valor


def validar_headers_log(valor):
    """Valida los headers del log (JSON dict)"""
    if valor is None:
        raise ValidationError("Los headers son requeridos.")

    if not isinstance(valor, dict):
        raise ValidationError("Los headers deben ser un objeto JSON (dict).")

    return valor


def validar_payload_log(valor):
    """Valida el payload del log (opcional, texto)"""
    if valor is None or valor == "":
        return valor

    if not isinstance(valor, str):
        raise ValidationError("El payload debe ser texto.")

    # Validar tamaño máximo (1MB)
    if len(valor) > 1000000:
        raise ValidationError("El payload no puede exceder 1MB.")

    return valor


def validar_status_code(valor):
    """Valida el código de estado HTTP (100-599)"""
    if valor is None:
        raise ValidationError("El código de estado HTTP es requerido.")

    try:
        code = int(valor)
    except (TypeError, ValueError):
        raise ValidationError("El código de estado debe ser un número entero.")

    if code < 100 or code > 599:
        raise ValidationError("El código de estado HTTP debe estar entre 100 y 599.")

    return code


def validar_tiempo_ms(valor):
    """Valida el tiempo en milisegundos (0-3600000 = 1 hora)"""
    if valor is None:
        raise ValidationError("El tiempo en milisegundos es requerido.")

    try:
        tiempo = int(valor)
    except (TypeError, ValueError):
        raise ValidationError("El tiempo debe ser un número entero.")

    if tiempo < 0:
        raise ValidationError("El tiempo no puede ser negativo.")
    if tiempo > 3600000:
        raise ValidationError("El tiempo no puede exceder 3600000 ms (1 hora).")

    return tiempo


def validar_bytes_transferidos(valor, nombre_campo="bytes"):
    """Valida bytes enviados/recibidos (opcional, >= 0)"""
    if valor is None:
        return valor

    try:
        bytes_val = int(valor)
    except (TypeError, ValueError):
        raise ValidationError(f"Los {nombre_campo} deben ser un número entero.")

    if bytes_val < 0:
        raise ValidationError(f"Los {nombre_campo} no pueden ser negativos.")

    # Límite razonable: 100MB
    if bytes_val > 100000000:
        raise ValidationError(f"Los {nombre_campo} no pueden exceder 100MB.")

    return bytes_val


def validar_bytes_sent(valor):
    """Valida bytes enviados"""
    return validar_bytes_transferidos(valor, "bytes enviados")


def validar_bytes_received(valor):
    """Valida bytes recibidos"""
    return validar_bytes_transferidos(valor, "bytes recibidos")


def validar_exitoso_log(valor):
    """Valida si la llamada fue exitosa (0 o 1)"""
    if valor is None:
        raise ValidationError("El campo exitoso es requerido.")

    try:
        exitoso = int(valor)
    except (TypeError, ValueError):
        raise ValidationError("El campo exitoso debe ser 0 o 1.")

    if exitoso not in [0, 1]:
        raise ValidationError("El campo exitoso debe ser 0 (fallido) o 1 (exitoso).")

    return exitoso


def validar_error_msg_log(valor):
    """Valida el mensaje de error (opcional)"""
    if valor is None or valor == "":
        return valor

    if not isinstance(valor, str):
        raise ValidationError("El mensaje de error debe ser texto.")

    if len(valor) > 5000:
        raise ValidationError("El mensaje de error no puede exceder 5000 caracteres.")

    return valor


def validar_intento_log(valor):
    """Valida el número de intento (1-100)"""
    if valor is None:
        raise ValidationError("El número de intento es requerido.")

    try:
        intento = int(valor)
    except (TypeError, ValueError):
        raise ValidationError("El número de intento debe ser un número entero.")

    if intento < 1:
        raise ValidationError("El número de intento debe ser al menos 1.")
    if intento > 100:
        raise ValidationError("El número de intento no puede exceder 100.")

    return intento


def validar_ip_origen(valor, nombre_campo="IP de origen"):
    """Valida dirección IPv4 o IPv6"""
    if valor is None or valor == "":
        if "opcional" in nombre_campo.lower():
            return valor
        raise ValidationError(f"La {nombre_campo} es requerida.")

    if not isinstance(valor, str):
        raise ValidationError(f"La {nombre_campo} debe ser texto.")

    valor = valor.strip()

    # Validar IPv4 (simple)
    patron_ipv4 = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    # Validar IPv6 (simplificado)
    patron_ipv6 = re.compile(r"^[0-9a-fA-F:]+$")

    if patron_ipv4.match(valor):
        # Validar rangos IPv4
        octetos = valor.split(".")
        for octeto in octetos:
            if int(octeto) > 255:
                raise ValidationError(f"La {nombre_campo} IPv4 tiene octetos inválidos.")
        return valor
    elif patron_ipv6.match(valor) and ":" in valor:
        # Validación básica IPv6
        if len(valor) > 39:
            raise ValidationError(f"La {nombre_campo} IPv6 es demasiado larga.")
        return valor
    else:
        raise ValidationError(f"La {nombre_campo} debe ser una dirección IPv4 o IPv6 válida.")


def validar_ip_origen_log(valor):
    """Valida IP de origen del log (opcional)"""
    return validar_ip_origen(valor, "IP de origen (opcional)")


def validar_contexto_log(valor):
    """Valida el contexto del log (JSON dict)"""
    if valor is None:
        raise ValidationError("El contexto es requerido.")

    if not isinstance(valor, dict):
        raise ValidationError("El contexto debe ser un objeto JSON (dict).")

    # Validar tamaño
    try:
        json_str = json.dumps(valor)
        if len(json_str) > 10000:
            raise ValidationError("El contexto es demasiado grande (max 10000 caracteres).")
    except (TypeError, ValueError) as e:
        raise ValidationError(f"El contexto no es JSON válido: {str(e)}")

    return valor


# ============================================================================
# VALIDADORES DE CREDENCIALES API
# ============================================================================


def validar_ambiente(valor):
    """Valida el ambiente (development/staging/production)"""
    if not valor or not isinstance(valor, str):
        raise ValidationError("El ambiente es requerido.")

    ambientes_validos = ["development", "staging", "production", "testing"]

    valor_lower = valor.lower()

    if valor_lower not in ambientes_validos:
        raise ValidationError(f'El ambiente debe ser uno de: {", ".join(ambientes_validos)}.')

    return valor


def validar_credencial_opcional(valor, nombre_campo="credencial"):
    """Valida api_key/secret/token (opcional, mínimo 10 caracteres)"""
    if valor is None or valor == "":
        return valor

    if not isinstance(valor, str):
        raise ValidationError(f"La {nombre_campo} debe ser texto.")

    # Mínimo 10 caracteres para seguridad
    if len(valor) < 10:
        raise ValidationError(f"La {nombre_campo} debe tener al menos 10 caracteres.")

    # Máximo 5000 caracteres (tokens JWT pueden ser largos)
    if len(valor) > 5000:
        raise ValidationError(f"La {nombre_campo} no puede exceder 5000 caracteres.")

    return valor


def validar_api_key(valor):
    """Valida API key"""
    return validar_credencial_opcional(valor, "API key")


def validar_secret(valor):
    """Valida secret"""
    return validar_credencial_opcional(valor, "secret")


def validar_token(valor):
    """Valida token"""
    return validar_credencial_opcional(valor, "token")


def validar_configuracion_cred(valor):
    """Valida la configuración de credenciales (JSON dict)"""
    if valor is None:
        raise ValidationError("La configuración es requerida.")

    if not isinstance(valor, dict):
        raise ValidationError("La configuración debe ser un objeto JSON (dict).")

    # Validar tamaño
    try:
        json_str = json.dumps(valor)
        if len(json_str) > 20000:
            raise ValidationError("La configuración es demasiado grande (max 20000 caracteres).")
    except (TypeError, ValueError) as e:
        raise ValidationError(f"La configuración no es JSON válido: {str(e)}")

    return valor


def validar_fecha_expiracion_cred(valor):
    """Valida fecha de expiración (opcional, debe ser futura)"""
    if valor is None:
        return valor

    if not isinstance(valor, datetime):
        raise ValidationError("La fecha de expiración debe ser un objeto datetime.")

    # Validar que sea futura (con tolerancia de 1 hora por zona horaria)
    from datetime import timezone, timedelta

    ahora = datetime.now(timezone.utc)
    if valor < ahora - timedelta(hours=1):
        raise ValidationError("La fecha de expiración debe ser una fecha futura.")

    return valor


def validar_updated_at_cred(valor):
    """Valida el timestamp de actualización"""
    if valor is None:
        raise ValidationError("La fecha de actualización es requerida.")

    if not isinstance(valor, datetime):
        raise ValidationError("La fecha de actualización debe ser un objeto datetime.")

    # No puede ser futuro (con tolerancia de 1 hora)
    from datetime import timezone, timedelta

    ahora = datetime.now(timezone.utc)
    if valor > ahora + timedelta(hours=1):
        raise ValidationError("La fecha de actualización no puede estar en el futuro.")

    return valor


def validar_activo_credencial(valor):
    """Valida el campo activo de credencial"""
    if not isinstance(valor, bool):
        raise ValidationError("El campo activo debe ser un valor booleano (True/False).")

    return valor


# ============================================================================
# VALIDADORES DE LOGS WEBHOOKS
# ============================================================================


def validar_timestamp_webhook(valor):
    """Valida el timestamp del webhook (no futuro)"""
    return validar_timestamp_log(valor)


def validar_headers_webhook(valor):
    """Valida los headers del webhook (JSON dict)"""
    return validar_headers_log(valor)


def validar_payload_webhook(valor):
    """Valida el payload del webhook (texto no vacío)"""
    if not valor or not isinstance(valor, str):
        raise ValidationError("El payload del webhook es requerido.")

    valor = valor.strip()
    if len(valor) == 0:
        raise ValidationError("El payload del webhook no puede estar vacío.")

    # Límite de 1MB
    if len(valor) > 1000000:
        raise ValidationError("El payload del webhook no puede exceder 1MB.")

    return valor


def validar_evento_tipo(valor):
    """Valida el tipo de evento (3-100 caracteres)"""
    if not valor or not isinstance(valor, str):
        raise ValidationError("El tipo de evento es requerido.")

    valor = valor.strip()
    if len(valor) < 3:
        raise ValidationError("El tipo de evento debe tener al menos 3 caracteres.")
    if len(valor) > 100:
        raise ValidationError("El tipo de evento no puede exceder 100 caracteres.")

    # Validar formato: letras, números, puntos, guiones (snake_case o kebab-case o dot.notation)
    patron = re.compile(r"^[a-zA-Z0-9._\-]+$")
    if not patron.match(valor):
        raise ValidationError(
            "El tipo de evento solo puede contener letras, números, puntos, guiones y guiones bajos."
        )

    return valor


def validar_verificacion_ok(valor):
    """Valida si la verificación fue exitosa (0 o 1)"""
    if valor is None:
        raise ValidationError("El campo verificacion_ok es requerido.")

    try:
        verif = int(valor)
    except (TypeError, ValueError):
        raise ValidationError("El campo verificacion_ok debe ser 0 o 1.")

    if verif not in [0, 1]:
        raise ValidationError("El campo verificacion_ok debe ser 0 (fallido) o 1 (exitoso).")

    return verif


def validar_procesado_ok(valor):
    """Valida si el procesamiento fue exitoso (0 o 1)"""
    if valor is None:
        raise ValidationError("El campo procesado_ok es requerido.")

    try:
        proc = int(valor)
    except (TypeError, ValueError):
        raise ValidationError("El campo procesado_ok debe ser 0 o 1.")

    if proc not in [0, 1]:
        raise ValidationError("El campo procesado_ok debe ser 0 (fallido) o 1 (exitoso).")

    return proc


def validar_tiempo_proc_ms_webhook(valor):
    """Valida el tiempo de procesamiento en ms (opcional, 0-60000 = 1 min)"""
    if valor is None:
        return valor

    try:
        tiempo = int(valor)
    except (TypeError, ValueError):
        raise ValidationError("El tiempo de procesamiento debe ser un número entero.")

    if tiempo < 0:
        raise ValidationError("El tiempo de procesamiento no puede ser negativo.")
    if tiempo > 60000:
        raise ValidationError("El tiempo de procesamiento no puede exceder 60000 ms (1 minuto).")

    return tiempo


def validar_error_msg_webhook(valor):
    """Valida el mensaje de error del webhook (opcional)"""
    return validar_error_msg_log(valor)


def validar_ip_origen_webhook(valor):
    """Valida IP de origen del webhook (requerida)"""
    return validar_ip_origen(valor, "IP de origen")


def validar_user_agent(valor):
    """Valida el User-Agent (opcional)"""
    if valor is None or valor == "":
        return valor

    if not isinstance(valor, str):
        raise ValidationError("El User-Agent debe ser texto.")

    if len(valor) > 500:
        raise ValidationError("El User-Agent no puede exceder 500 caracteres.")

    return valor


# ============================================================================
# VALIDADORES DE WEBHOOK ENDPOINTS
# ============================================================================


def validar_nombre_webhook(valor):
    """Valida el nombre del webhook (3-100 caracteres)"""
    return validar_nombre_endpoint(valor)


def validar_descripcion_webhook(valor):
    """Valida la descripción del webhook (10-2000 caracteres)"""
    return validar_descripcion_endpoint(valor)


def validar_path_webhook(valor):
    """Valida el path del webhook (debe comenzar con /)"""
    return validar_path_endpoint(valor)


def validar_requiere_verificacion(valor):
    """Valida si requiere verificación (0 o 1)"""
    if valor is None:
        raise ValidationError("El campo requiere_verificacion es requerido.")

    try:
        verif = int(valor)
    except (TypeError, ValueError):
        raise ValidationError("El campo requiere_verificacion debe ser 0 o 1.")

    if verif not in [0, 1]:
        raise ValidationError("El campo requiere_verificacion debe ser 0 (no) o 1 (sí).")

    return verif


def validar_secret_key_webhook(valor):
    """Valida la secret key del webhook (mínimo 32 caracteres)"""
    if not valor or not isinstance(valor, str):
        raise ValidationError("La secret key es requerida.")

    valor = valor.strip()

    if len(valor) < 32:
        raise ValidationError("La secret key debe tener al menos 32 caracteres para seguridad.")

    if len(valor) > 255:
        raise ValidationError("La secret key no puede exceder 255 caracteres.")

    return valor


def validar_header_verificacion(valor):
    """Valida el nombre del header de verificación (HTTP header válido)"""
    if not valor or not isinstance(valor, str):
        raise ValidationError("El header de verificación es requerido.")

    valor = valor.strip()

    # Validar que sea un nombre de header HTTP válido
    # Formato: letras, números, guiones (no puede empezar con guion o número)
    patron = re.compile(r"^[A-Za-z][A-Za-z0-9\-]*$")

    if not patron.match(valor):
        raise ValidationError(
            "El header de verificación debe ser un nombre de HTTP header válido "
            "(letras, números, guiones; debe empezar con letra)."
        )

    if len(valor) > 100:
        raise ValidationError("El header de verificación no puede exceder 100 caracteres.")

    return valor


def validar_eventos_webhook(valor):
    """Valida la lista de eventos del webhook (JSON array de strings)"""
    if valor is None:
        raise ValidationError("Los eventos son requeridos.")

    if not isinstance(valor, list):
        raise ValidationError("Los eventos deben ser un array JSON (list).")

    if len(valor) == 0:
        raise ValidationError("Debe especificar al menos un evento.")

    # Validar que todos los elementos sean strings
    for i, evento in enumerate(valor):
        if not isinstance(evento, str):
            raise ValidationError(f"El evento en la posición {i} debe ser un string.")

        # Validar formato del evento
        if len(evento) < 3 or len(evento) > 100:
            raise ValidationError(f'El evento "{evento}" debe tener entre 3 y 100 caracteres.')

        if not re.match(r"^[a-zA-Z0-9._\-]+$", evento):
            raise ValidationError(
                f'El evento "{evento}" contiene caracteres inválidos. '
                "Solo se permiten letras, números, puntos, guiones y guiones bajos."
            )

    # Validar que no haya duplicados
    if len(valor) != len(set(valor)):
        raise ValidationError("Los eventos no pueden estar duplicados.")

    return valor


def validar_handler_func(valor):
    """Valida el handler function (Python callable path)"""
    if not valor or not isinstance(valor, str):
        raise ValidationError("El handler function es requerido.")

    valor = valor.strip()

    # Formato esperado: modulo.submodulo.funcion o clase.metodo
    # Ejemplo: apps.api_integrations.handlers.handle_payment_webhook
    patron = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)+$")

    if not patron.match(valor):
        raise ValidationError(
            "El handler function debe ser una ruta Python válida " "(ej: modulo.submodulo.funcion)."
        )

    if len(valor) > 200:
        raise ValidationError("El handler function no puede exceder 200 caracteres.")

    return valor


def validar_activo_webhook(valor):
    """Valida el campo activo del webhook"""
    if not isinstance(valor, bool):
        raise ValidationError("El campo activo debe ser un valor booleano (True/False).")

    return valor


def validar_created_at_webhook(valor):
    """Valida la fecha de creación del webhook"""
    if valor is None:
        raise ValidationError("La fecha de creación es requerida.")

    if not isinstance(valor, datetime):
        raise ValidationError("La fecha de creación debe ser un objeto datetime.")

    # No puede ser futuro (con tolerancia de 1 hora)
    from datetime import timezone, timedelta

    ahora = datetime.now(timezone.utc)
    if valor > ahora + timedelta(hours=1):
        raise ValidationError("La fecha de creación no puede estar en el futuro.")

    return valor
