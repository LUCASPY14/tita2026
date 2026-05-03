"""
Validadores para el módulo de Clientes
Incluye validaciones para clientes, hijos, grados y restricciones
"""

import re
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, validate_email

# ============================================================================
# VALIDADORES DE CLIENTES
# ============================================================================


def validar_nombres_cliente(nombres):
    """
    Valida el formato de nombres del cliente.

    Reglas:
    - Longitud: 2-100 caracteres
    - Solo letras, espacios, apóstrofes y guiones

    Args:
        nombres (str): Nombres del cliente

    Raises:
        ValidationError: Si el formato es inválido
    """
    if not nombres or len(nombres.strip()) < 2:
        raise ValidationError("Los nombres del cliente deben tener al menos 2 caracteres")

    if len(nombres) > 100:
        raise ValidationError("Los nombres no pueden exceder 100 caracteres")

    # Solo letras, espacios, apóstrofes y guiones
    if not re.match(r"^[a-záéíóúñA-ZÁÉÍÓÚÑ\s'\-]+$", nombres):
        raise ValidationError("Los nombres solo pueden contener letras, espacios, apóstrofes y guiones")


def validar_apellidos_cliente(apellidos):
    """
    Valida el formato de apellidos del cliente.

    Reglas:
    - Longitud: 2-100 caracteres
    - Solo letras, espacios, apóstrofes y guiones

    Args:
        apellidos (str): Apellidos del cliente

    Raises:
        ValidationError: Si el formato es inválido
    """
    if not apellidos or len(apellidos.strip()) < 2:
        raise ValidationError("Los apellidos del cliente deben tener al menos 2 caracteres")

    if len(apellidos) > 100:
        raise ValidationError("Los apellidos no pueden exceder 100 caracteres")

    # Solo letras, espacios, apóstrofes y guiones
    if not re.match(r"^[a-záéíóúñA-ZÁÉÍÓÚÑ\s'\-]+$", apellidos):
        raise ValidationError("Los apellidos solo pueden contener letras, espacios, apóstrofes y guiones")


def validar_razon_social(razon_social):
    """
    Valida el formato de razón social (para empresas).

    Reglas:
    - Longitud: 3-255 caracteres
    - Alfanumérico con caracteres especiales permitidos

    Args:
        razon_social (str): Razón social de la empresa

    Raises:
        ValidationError: Si el formato es inválido
    """
    if not razon_social:
        return  # Opcional

    razon_social = razon_social.strip()

    if len(razon_social) < 3:
        raise ValidationError("La razón social debe tener al menos 3 caracteres")

    if len(razon_social) > 255:
        raise ValidationError("La razón social no puede exceder 255 caracteres")

    # Alfanumérico (incluyendo acentuados), espacios, puntos, comas, guiones, &, paréntesis
    if not re.match(r"^[a-zA-Z0-9áéíóúñÁÉÍÓÚÑ\s\.\,\-\&\(\)]+$", razon_social):
        raise ValidationError("La razón social contiene caracteres no permitidos")


def validar_ruc_ci(ruc_ci):
    """
    Valida formato de RUC o Cédula de Identidad paraguaya.

    Formatos válidos:
    - RUC: XXXXX-Y o XXXXXXXX-Y (5 u 8 dígitos + guion + dígito verificador)
    - CI: 1.234.567 o 1234567 (7-8 dígitos con o sin puntos)

    Args:
        ruc_ci (str): RUC o CI del cliente

    Raises:
        ValidationError: Si el formato es inválido
    """
    if not ruc_ci:
        raise ValidationError("RUC/CI es obligatorio")

    ruc_ci = ruc_ci.strip()

    if len(ruc_ci) < 6 or len(ruc_ci) > 20:
        raise ValidationError("RUC/CI debe tener entre 6 y 20 caracteres")

    # Formato RUC: XXXXX-Y o XXXXXXXX-Y
    if "-" in ruc_ci:
        partes = ruc_ci.split("-")
        if len(partes) != 2:
            raise ValidationError("Formato de RUC inválido. Use: XXXXX-Y o XXXXXXXX-Y")

        numero, digito = partes

        if not numero.isdigit():
            raise ValidationError("El número del RUC debe ser numérico")

        if len(numero) not in [5, 8]:
            raise ValidationError("El RUC debe tener 5 u 8 dígitos antes del guion")

        if not digito.isdigit() or len(digito) != 1:
            raise ValidationError("El dígito verificador del RUC debe ser un solo dígito")

    # Formato CI: puede tener puntos
    elif "." in ruc_ci:
        # Remover puntos y validar
        numero_limpio = ruc_ci.replace(".", "")
        if not numero_limpio.isdigit():
            raise ValidationError("La CI debe contener solo dígitos y puntos")

        if len(numero_limpio) < 6 or len(numero_limpio) > 8:
            raise ValidationError("La CI debe tener entre 6 y 8 dígitos")

    # Solo números (sin guion ni puntos)
    else:
        if not ruc_ci.isdigit():
            raise ValidationError("RUC/CI debe ser numérico o tener formato válido (con guion o puntos)")

        if len(ruc_ci) < 6 or len(ruc_ci) > 8:
            raise ValidationError("CI debe tener entre 6 y 8 dígitos")


def validar_email_cliente(email):
    """
    Valida formato de email del cliente.

    Args:
        email (str): Email del cliente

    Raises:
        ValidationError: Si el formato es inválido
    """
    if not email:
        return  # Opcional

    email = email.strip()

    try:
        validate_email(email)
    except ValidationError:
        raise ValidationError("Formato de email inválido")


def validar_telefono_cliente(telefono):
    """
    Valida formato de teléfono paraguayo.

    Formatos aceptados:
    - Móvil: 0981123456, 09 81 123456, 0981-123456
    - Fijo: 021123456, 021-123456, 021 123456

    Args:
        telefono (str): Teléfono del cliente

    Raises:
        ValidationError: Si el formato es inválido
    """
    if not telefono:
        return  # Opcional

    telefono = telefono.strip()

    if len(telefono) < 7 or len(telefono) > 20:
        raise ValidationError("El teléfono debe tener entre 7 y 20 caracteres")

    # Remover espacios, guiones y paréntesis para validar
    telefono_limpio = re.sub(r"[\s\-\(\)]", "", telefono)

    if not telefono_limpio.isdigit():
        raise ValidationError("El teléfono debe contener solo dígitos, espacios, guiones o paréntesis")

    # Paraguay: móviles empiezan con 09, fijos con 0 + código de área (21, 61, etc.)
    if telefono_limpio.startswith("09"):
        # Móvil: debe tener 10 dígitos
        if len(telefono_limpio) != 10:
            raise ValidationError("Teléfono móvil debe tener 10 dígitos (ej: 0981123456)")
    elif telefono_limpio.startswith("0"):
        # Fijo: debe tener 9 dígitos (0 + 2 dígitos área + 6 dígitos)
        if len(telefono_limpio) not in [9, 10]:
            raise ValidationError("Teléfono fijo debe tener 9 dígitos (ej: 021123456)")
    else:
        raise ValidationError("Teléfono debe comenzar con 0")


def validar_limite_credito_cliente(limite_credito):
    """
    Valida el límite de crédito del cliente.

    Reglas:
    - Debe ser >= 0
    - No puede exceder ₲50,000,000
    - Máximo 2 decimales

    Args:
        limite_credito (Decimal): Límite de crédito

    Raises:
        ValidationError: Si el límite es inválido
    """
    if limite_credito is None:
        return  # Opcional

    if not isinstance(limite_credito, Decimal):
        try:
            limite_credito = Decimal(str(limite_credito))
        except:
            raise ValidationError("Límite de crédito debe ser un número válido")

    if limite_credito < 0:
        raise ValidationError("El límite de crédito no puede ser negativo")

    if limite_credito > Decimal("50000000.00"):
        raise ValidationError("El límite de crédito no puede exceder ₲50,000,000")

    # Validar máximo 2 decimales
    if limite_credito.as_tuple().exponent < -2:
        raise ValidationError("El límite de crédito no puede tener más de 2 decimales")


def validar_direccion_cliente(direccion):
    """
    Valida formato de dirección del cliente.

    Reglas:
    - Longitud: 5-255 caracteres

    Args:
        direccion (str): Dirección del cliente

    Raises:
        ValidationError: Si el formato es inválido
    """
    if not direccion:
        return  # Opcional

    direccion = direccion.strip()

    if len(direccion) < 5:
        raise ValidationError("La dirección debe tener al menos 5 caracteres")

    if len(direccion) > 255:
        raise ValidationError("La dirección no puede exceder 255 caracteres")


# ============================================================================
# VALIDADORES DE TIPOS DE CLIENTE
# ============================================================================


def validar_nombre_tipo_cliente(nombre_tipo):
    """
    Valida el nombre del tipo de cliente.

    Reglas:
    - Longitud: 3-50 caracteres
    - Solo letras, números y espacios

    Args:
        nombre_tipo (str): Nombre del tipo de cliente

    Raises:
        ValidationError: Si el formato es inválido
    """
    if not nombre_tipo or len(nombre_tipo.strip()) < 3:
        raise ValidationError("El nombre del tipo de cliente debe tener al menos 3 caracteres")

    if len(nombre_tipo) > 50:
        raise ValidationError("El nombre del tipo de cliente no puede exceder 50 caracteres")

    if not re.match(r"^[a-zA-Z0-9\sáéíóúñÁÉÍÓÚÑ]+$", nombre_tipo):
        raise ValidationError("El nombre del tipo solo puede contener letras, números y espacios")


# ============================================================================
# VALIDADORES DE HIJOS
# ============================================================================


def validar_nombre_hijo(nombre):
    """
    Valida el formato de nombre del hijo/estudiante.

    Reglas:
    - Longitud: 2-100 caracteres
    - Solo letras, espacios, apóstrofes y guiones

    Args:
        nombre (str): Nombre del estudiante

    Raises:
        ValidationError: Si el formato es inválido
    """
    if not nombre or len(nombre.strip()) < 2:
        raise ValidationError("El nombre del estudiante debe tener al menos 2 caracteres")

    if len(nombre) > 100:
        raise ValidationError("El nombre no puede exceder 100 caracteres")

    if not re.match(r"^[a-záéíóúñA-ZÁÉÍÓÚÑ\s'\-]+$", nombre):
        raise ValidationError("El nombre solo puede contener letras, espacios, apóstrofes y guiones")


def validar_apellido_hijo(apellido):
    """
    Valida el formato de apellido del hijo/estudiante.

    Reglas:
    - Longitud: 2-100 caracteres
    - Solo letras, espacios, apóstrofes y guiones

    Args:
        apellido (str): Apellido del estudiante

    Raises:
        ValidationError: Si el formato es inválido
    """
    if not apellido or len(apellido.strip()) < 2:
        raise ValidationError("El apellido del estudiante debe tener al menos 2 caracteres")

    if len(apellido) > 100:
        raise ValidationError("El apellido no puede exceder 100 caracteres")

    if not re.match(r"^[a-záéíóúñA-ZÁÉÍÓÚÑ\s'\-]+$", apellido):
        raise ValidationError("El apellido solo puede contener letras, espacios, apóstrofes y guiones")


def validar_fecha_nacimiento(fecha_nacimiento):
    """
    Valida la fecha de nacimiento del estudiante.

    Reglas:
    - No puede ser futura
    - No puede ser anterior a 1950
    - Edad mínima: 3 años
    - Edad máxima: 25 años (para estudiantes)

    Args:
        fecha_nacimiento (date): Fecha de nacimiento

    Raises:
        ValidationError: Si la fecha es inválida
    """
    if not fecha_nacimiento:
        return  # Opcional

    hoy = date.today()

    if fecha_nacimiento > hoy:
        raise ValidationError("La fecha de nacimiento no puede ser futura")

    if fecha_nacimiento.year < 1950:
        raise ValidationError("La fecha de nacimiento no puede ser anterior a 1950")

    # Calcular edad
    edad = hoy.year - fecha_nacimiento.year
    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1

    if edad < 3:
        raise ValidationError("El estudiante debe tener al menos 3 años")

    if edad >= 25:
        raise ValidationError("La edad del estudiante no puede ser mayor o igual a 25 años")


def validar_grado_hijo(grado):
    """
    Valida el grado del estudiante.

    Reglas:
    - Longitud: 2-50 caracteres

    Args:
        grado (str): Grado del estudiante

    Raises:
        ValidationError: Si el formato es inválido
    """
    if not grado:
        return  # Opcional

    grado = grado.strip()

    if len(grado) < 2:
        raise ValidationError("El grado debe tener al menos 2 caracteres")

    if len(grado) > 50:
        raise ValidationError("El grado no puede exceder 50 caracteres")


def validar_foto_perfil(foto_perfil):
    """
    Valida la URL o path de la foto de perfil.

    Reglas:
    - Longitud máxima: 255 caracteres
    - Si es URL, debe ser válida

    Args:
        foto_perfil (str): URL o path de la foto

    Raises:
        ValidationError: Si el formato es inválido
    """
    if not foto_perfil:
        return  # Opcional

    foto_perfil = foto_perfil.strip()

    if len(foto_perfil) > 255:
        raise ValidationError("La ruta de la foto no puede exceder 255 caracteres")

    # Si parece una URL, validarla
    if foto_perfil.startswith("http://") or foto_perfil.startswith("https://"):
        validator = URLValidator()
        try:
            validator(foto_perfil)
        except ValidationError:
            raise ValidationError("URL de foto inválida")


# ============================================================================
# VALIDADORES DE GRADOS
# ============================================================================


def validar_nombre_grado(nombre_grado):
    """
    Valida el nombre del grado escolar.

    Reglas:
    - Longitud: 2-50 caracteres
    - Alfanumérico con espacios y guiones

    Args:
        nombre_grado (str): Nombre del grado

    Raises:
        ValidationError: Si el formato es inválido
    """
    if not nombre_grado or len(nombre_grado.strip()) < 2:
        raise ValidationError("El nombre del grado debe tener al menos 2 caracteres")

    if len(nombre_grado) > 50:
        raise ValidationError("El nombre del grado no puede exceder 50 caracteres")

    if not re.match(r"^[a-zA-Z0-9\sáéíóúñÁÉÍÓÚÑ\-°]+$", nombre_grado):
        raise ValidationError("El nombre del grado contiene caracteres no permitidos")


def validar_nivel_grado(nivel):
    """
    Valida el nivel numérico del grado.

    Reglas:
    - Debe estar entre 1 y 12 (niveles escolares estándar)

    Args:
        nivel (int): Nivel del grado

    Raises:
        ValidationError: Si el nivel es inválido
    """
    if nivel is None:
        raise ValidationError("El nivel del grado es obligatorio")

    if not isinstance(nivel, int):
        try:
            nivel = int(nivel)
        except:
            raise ValidationError("El nivel debe ser un número entero")

    if nivel < 1 or nivel > 12:
        raise ValidationError("El nivel del grado debe estar entre 1 y 12")


def validar_orden_visualizacion(orden):
    """
    Valida el orden de visualización del grado.

    Reglas:
    - Debe ser >= 1
    - No puede exceder 100

    Args:
        orden (int): Orden de visualización

    Raises:
        ValidationError: Si el orden es inválido
    """
    if orden is None:
        raise ValidationError("El orden de visualización es obligatorio")

    if not isinstance(orden, int):
        try:
            orden = int(orden)
        except:
            raise ValidationError("El orden debe ser un número entero")

    if orden < 1:
        raise ValidationError("El orden de visualización debe ser al menos 1")

    if orden > 100:
        raise ValidationError("El orden de visualización no puede exceder 100")


# ============================================================================
# VALIDADORES DE HISTORIAL DE GRADOS
# ============================================================================


def validar_anio_escolar(anio):
    """
    Valida el año escolar.

    Reglas:
    - Debe ser un año válido
    - No puede ser anterior a 1990
    - No puede ser posterior a año actual + 1

    Args:
        anio (int): Año escolar

    Raises:
        ValidationError: Si el año es inválido
    """
    if anio is None:
        raise ValidationError("El año escolar es obligatorio")

    if not isinstance(anio, int):
        try:
            anio = int(anio)
        except:
            raise ValidationError("El año debe ser un número entero")

    anio_actual = date.today().year

    if anio < 1990:
        raise ValidationError("El año escolar no puede ser anterior a 1990")

    if anio > anio_actual + 1:
        raise ValidationError(f"El año escolar no puede ser posterior a {anio_actual + 1}")


def validar_motivo_cambio_grado(motivo):
    """
    Valida el motivo del cambio de grado.

    Motivos válidos:
    - Promoción
    - Repetición
    - Transferencia
    - Corrección
    - Otro

    Args:
        motivo (str): Motivo del cambio

    Raises:
        ValidationError: Si el motivo es inválido
    """
    motivos_validos = [
        "Promoción",
        "Repetición",
        "Transferencia",
        "Corrección",
        "Otro",
        "Promocion",
        "Repeticion",
        "Correccion",
    ]  # Con y sin tilde

    if not motivo:
        raise ValidationError("El motivo del cambio es obligatorio")

    motivo = motivo.strip()

    if motivo not in motivos_validos:
        raise ValidationError(f"Motivo inválido. Debe ser uno de: {', '.join(set(motivos_validos))}")


def validar_cambio_grado(grado_anterior, grado_nuevo):
    """
    Valida que el cambio de grado sea lógico.

    Reglas:
    - Los grados deben ser diferentes
    - No se permite cambio a "Sin grado"

    Args:
        grado_anterior (str): Grado anterior
        grado_nuevo (str): Grado nuevo

    Raises:
        ValidationError: Si el cambio es inválido
    """
    if not grado_nuevo:
        raise ValidationError("El grado nuevo es obligatorio")

    if grado_anterior and grado_anterior == grado_nuevo:
        raise ValidationError("El grado nuevo debe ser diferente al grado anterior")

    if grado_nuevo.lower() == "sin grado":
        raise ValidationError("No se puede cambiar a 'Sin grado'")


# ============================================================================
# VALIDADORES DE RESTRICCIONES
# ============================================================================


def validar_tipo_restriccion(tipo):
    """
    Valida el tipo de restricción.

    Reglas:
    - Longitud: 3-100 caracteres
    - Solo letras, números, espacios y guiones

    Args:
        tipo (str): Tipo de restricción

    Raises:
        ValidationError: Si el formato es inválido
    """
    if not tipo or len(tipo.strip()) < 3:
        raise ValidationError("El tipo de restricción debe tener al menos 3 caracteres")

    if len(tipo) > 100:
        raise ValidationError("El tipo de restricción no puede exceder 100 caracteres")

    if not re.match(r"^[a-zA-Z0-9\sáéíóúñÁÉÍÓÚÑ\-]+$", tipo):
        raise ValidationError("El tipo de restricción contiene caracteres no permitidos")


def validar_descripcion_restriccion(descripcion):
    """
    Valida la descripción de la restricción.

    Reglas:
    - Longitud mínima: 10 caracteres
    - Longitud máxima: 500 caracteres

    Args:
        descripcion (str): Descripción de la restricción

    Raises:
        ValidationError: Si el formato es inválido
    """
    if not descripcion:
        return  # Opcional

    descripcion = descripcion.strip()

    if len(descripcion) < 10:
        raise ValidationError("La descripción debe tener al menos 10 caracteres")

    if len(descripcion) > 500:
        raise ValidationError("La descripción no puede exceder 500 caracteres")


def validar_severidad_restriccion(severidad):
    """
    Valida el nivel de severidad de la restricción.

    Severidades válidas:
    - Baja
    - Media
    - Alta
    - Crítica

    Args:
        severidad (str): Nivel de severidad

    Raises:
        ValidationError: Si la severidad es inválida
    """
    severidades_validas = ["Baja", "Media", "Alta", "Crítica", "Critica"]  # Con y sin tilde

    if not severidad:
        raise ValidationError("La severidad es obligatoria")

    severidad = severidad.strip()

    if severidad not in severidades_validas:
        raise ValidationError(f"Severidad inválida. Debe ser una de: Baja, Media, Alta, Crítica")


def validar_observaciones_restriccion(observaciones):
    """
    Valida las observaciones de la restricción.

    Reglas:
    - Longitud máxima: 1000 caracteres

    Args:
        observaciones (str): Observaciones adicionales

    Raises:
        ValidationError: Si excede el límite
    """
    if not observaciones:
        return  # Opcional

    if len(observaciones) > 1000:
        raise ValidationError("Las observaciones no pueden exceder 1000 caracteres")


# ============================================================================
# VALIDADORES DE AUTORIZACIONES DE SALDO NEGATIVO
# ============================================================================


def validar_monto_autorizado(monto):
    """
    Valida el monto autorizado para saldo negativo.

    Reglas:
    - Debe ser > 0 (monto en negativo que se autoriza)
    - No puede exceder ₲5,000,000
    - Máximo 2 decimales

    Args:
        monto (Decimal): Monto autorizado

    Raises:
        ValidationError: Si el monto es inválido
    """
    if not monto:
        raise ValidationError("El monto autorizado es obligatorio")

    if not isinstance(monto, Decimal):
        try:
            monto = Decimal(str(monto))
        except:
            raise ValidationError("El monto debe ser un número válido")

    if monto <= 0:
        raise ValidationError("El monto autorizado debe ser mayor a 0")

    if monto > Decimal("5000000.00"):
        raise ValidationError("El monto autorizado no puede exceder ₲5,000,000")

    # Validar máximo 2 decimales
    if monto.as_tuple().exponent < -2:
        raise ValidationError("El monto no puede tener más de 2 decimales")


def validar_saldos_autorizacion(saldo_anterior, saldo_resultante, monto_autorizado):
    """
    Valida la coherencia de saldos en la autorización.

    Reglas:
    - saldo_resultante debe ser menor que saldo_anterior
    - La diferencia debe corresponder al monto de la venta
    - saldo_resultante no puede ser menor que -monto_autorizado

    Args:
        saldo_anterior (Decimal): Saldo antes de la venta
        saldo_resultante (Decimal): Saldo después de la venta
        monto_autorizado (Decimal): Monto máximo autorizado en negativo

    Raises:
        ValidationError: Si los saldos son incoherentes
    """
    if saldo_resultante >= saldo_anterior:
        raise ValidationError("El saldo resultante debe ser menor que el saldo anterior")

    # El saldo resultante no puede ser más negativo que el monto autorizado
    if saldo_resultante < -monto_autorizado:
        raise ValidationError(
            f"El saldo resultante (₲{saldo_resultante:,.2f}) excede el monto autorizado (₲{monto_autorizado:,.2f})"
        )


def validar_motivo_autorizacion(motivo):
    """
    Valida el motivo de la autorización.

    Reglas:
    - Longitud mínima: 10 caracteres
    - Longitud máxima: 500 caracteres

    Args:
        motivo (str): Justificación de la autorización

    Raises:
        ValidationError: Si el motivo es inválido
    """
    if not motivo or len(motivo.strip()) < 10:
        raise ValidationError("El motivo de la autorización debe tener al menos 10 caracteres")

    if len(motivo) > 500:
        raise ValidationError("El motivo no puede exceder 500 caracteres")


# ============================================================================
# VALIDADORES DE LOGS DE AUTORIZACIONES
# ============================================================================


def validar_tipo_operacion_log(tipo_operacion):
    """
    Valida el tipo de operación del log.

    Tipos válidos:
    - Lectura
    - Autorización
    - Validación
    - Rechazo
    - Otro

    Args:
        tipo_operacion (str): Tipo de operación

    Raises:
        ValidationError: Si el tipo es inválido
    """
    tipos_validos = [
        "Lectura",
        "Autorización",
        "Autorizacion",
        "Validación",
        "Validacion",
        "Rechazo",
        "Otro",
    ]

    if not tipo_operacion:
        raise ValidationError("El tipo de operación es obligatorio")

    tipo_operacion = tipo_operacion.strip()

    if tipo_operacion not in tipos_validos:
        raise ValidationError(
            f"Tipo de operación inválido. Debe ser uno de: Lectura, Autorización, Validación, Rechazo, Otro"
        )


def validar_resultado_log(resultado):
    """
    Valida el resultado del log.

    Resultados válidos:
    - Exitoso
    - Fallido
    - Denegado

    Args:
        resultado (str): Resultado de la operación

    Raises:
        ValidationError: Si el resultado es inválido
    """
    resultados_validos = ["Exitoso", "Fallido", "Denegado"]

    if not resultado:
        raise ValidationError("El resultado es obligatorio")

    resultado = resultado.strip()

    if resultado not in resultados_validos:
        raise ValidationError(f"Resultado inválido. Debe ser uno de: {', '.join(resultados_validos)}")


def validar_ip_origen(ip):
    """
    Valida el formato de dirección IP.

    Soporta:
    - IPv4: 192.168.1.1
    - IPv6: 2001:0db8:85a3:0000:0000:8a2e:0370:7334

    Args:
        ip (str): Dirección IP

    Raises:
        ValidationError: Si el formato es inválido
    """
    if not ip:
        return  # Opcional

    ip = ip.strip()

    # Validar IPv4
    ipv4_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    if re.match(ipv4_pattern, ip):
        # Verificar que cada octeto esté en rango 0-255
        octetos = ip.split(".")
        for octeto in octetos:
            if int(octeto) > 255:
                raise ValidationError(f"IP inválida: octeto {octeto} excede 255")
        return

    # Validar IPv6 (formato simplificado)
    ipv6_pattern = r"^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"
    if re.match(ipv6_pattern, ip):
        return

    # También aceptar IPv6 comprimido (con ::)
    if "::" in ip:
        return

    raise ValidationError("Formato de IP inválido. Debe ser IPv4 o IPv6 válida")
