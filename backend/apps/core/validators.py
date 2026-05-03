"""
Validadores para la app Core - Tarjetas, Configuración y Límites de Transacción

Este módulo contiene validadores para:
- Tarjetas de estudiantes (saldo, estado, vencimiento)
- Tarjetas de autorización (permisos, roles)
- Cargas de saldo (montos, estados, referencias)
- Consumos de tarjeta (coherencia de saldos)
- Transacciones online (métodos de pago, estados)
- Medios de pago (descripción)
- Configuración del sistema (tipos, valores, validación)
- Límites de transacción (roles, operaciones)
- Registro de autorizaciones (motivos, autorizadores)
"""

import re
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError

# =============================================================================
# VALIDADORES DE TARJETAS (7)
# =============================================================================


def validar_numero_tarjeta(numero_tarjeta):
    """
    Valida el formato del número de tarjeta.

    Reglas:
    - Longitud: 6-20 caracteres
    - Formato: alfanumérico, puede incluir guiones
    - Ejemplos válidos: "TAR-001", "12345678", "CARD-2024-001"

    Args:
        numero_tarjeta (str): Número de tarjeta a validar

    Raises:
        ValidationError: Si el formato es inválido
    """
    if not numero_tarjeta or not isinstance(numero_tarjeta, str):
        raise ValidationError("El número de tarjeta es obligatorio")

    # Limpiar espacios
    numero_limpio = numero_tarjeta.strip()

    # Validar longitud
    if len(numero_limpio) < 6:
        raise ValidationError("El número de tarjeta debe tener al menos 6 caracteres")

    if len(numero_limpio) > 20:
        raise ValidationError("El número de tarjeta no puede exceder 20 caracteres")

    # Validar formato alfanumérico con guiones opcionales
    if not re.match(r"^[A-Za-z0-9\-]+$", numero_limpio):
        raise ValidationError("El número de tarjeta solo puede contener letras, números y guiones")

    # No debe empezar o terminar con guion
    if numero_limpio.startswith("-") or numero_limpio.endswith("-"):
        raise ValidationError("El número de tarjeta no puede empezar ni terminar con guion")


def validar_saldo_tarjeta(saldo_actual, limite_credito, permite_negativo=False):
    """
    Valida que el saldo de la tarjeta esté dentro de los límites permitidos.

    Reglas:
    - Si no permite saldo negativo: saldo >= 0
    - Si permite saldo negativo: saldo >= -limite_credito
    - Límite máximo de saldo: ₲10,000,000

    Args:
        saldo_actual (Decimal): Saldo actual de la tarjeta
        limite_credito (Decimal): Límite de crédito configurado
        permite_negativo (bool): Si permite saldo negativo

    Raises:
        ValidationError: Si el saldo es inválido
    """
    if not isinstance(saldo_actual, Decimal):
        try:
            saldo_actual = Decimal(str(saldo_actual))
        except (ValueError, TypeError):
            raise ValidationError("El saldo debe ser un valor numérico")

    if not isinstance(limite_credito, Decimal):
        try:
            limite_credito = Decimal(str(limite_credito))
        except (ValueError, TypeError):
            raise ValidationError("El límite de crédito debe ser un valor numérico")

    # Validar saldo máximo
    saldo_maximo = Decimal("10000000.00")  # ₲10M
    if saldo_actual > saldo_maximo:
        raise ValidationError(f"El saldo no puede exceder ₲{saldo_maximo:,.2f}")

    # Validar saldo mínimo según configuración
    if not permite_negativo and saldo_actual < 0:
        raise ValidationError("El saldo no puede ser negativo. Esta tarjeta no permite crédito.")

    if permite_negativo:
        saldo_minimo = -limite_credito
        if saldo_actual < saldo_minimo:
            raise ValidationError(
                f"El saldo no puede ser menor a ₲{saldo_minimo:,.2f} " f"(límite de crédito: ₲{limite_credito:,.2f})"
            )


def validar_estado_tarjeta(estado):
    """
    Valida que el estado de la tarjeta sea válido.

    Estados válidos:
    - Activa: Tarjeta operativa
    - Bloqueada: Bloqueada temporalmente
    - Vencida: Fecha de vencimiento alcanzada
    - Cancelada: Cancelada permanentemente
    - Suspendida: Suspendida por motivos administrativos

    Args:
        estado (str): Estado a validar

    Raises:
        ValidationError: Si el estado no es válido
    """
    ESTADOS_VALIDOS = ["Activa", "Bloqueada", "Vencida", "Cancelada", "Suspendida"]

    if not estado:
        raise ValidationError("El estado de la tarjeta es obligatorio")

    if estado not in ESTADOS_VALIDOS:
        raise ValidationError(f"Estado '{estado}' no válido. Estados permitidos: {', '.join(ESTADOS_VALIDOS)}")


def validar_codigo_barras_tarjeta(codigo_barras):
    """
    Valida el formato del código de barras de la tarjeta.

    Formatos aceptados:
    - EAN-13: 13 dígitos
    - EAN-8: 8 dígitos
    - Código 128: Alfanumérico 8-50 caracteres

    Args:
        codigo_barras (str): Código de barras a validar

    Raises:
        ValidationError: Si el formato es inválido
    """
    if not codigo_barras:
        return  # El código de barras es opcional

    codigo_limpio = codigo_barras.strip()

    # Validar longitud
    if len(codigo_limpio) < 8:
        raise ValidationError("El código de barras debe tener al menos 8 caracteres")

    if len(codigo_limpio) > 50:
        raise ValidationError("El código de barras no puede exceder 50 caracteres")

    # Si es numérico, validar que sea EAN-13 o EAN-8
    if codigo_limpio.isdigit():
        if len(codigo_limpio) not in [8, 13]:
            raise ValidationError("Código de barras numérico debe tener 8 (EAN-8) o 13 (EAN-13) dígitos")
    else:
        # Código 128: alfanumérico
        if not re.match(r"^[A-Za-z0-9\-]+$", codigo_limpio):
            raise ValidationError("El código de barras solo puede contener letras, números y guiones")


def validar_fecha_vencimiento_tarjeta(fecha_vencimiento):
    """
    Valida la fecha de vencimiento de la tarjeta.

    Reglas:
    - No puede ser menor a la fecha actual
    - No puede ser mayor a 10 años en el futuro
    - Warning si es menor a 30 días

    Args:
        fecha_vencimiento (date): Fecha de vencimiento

    Raises:
        ValidationError: Si la fecha es inválida
    """
    if not fecha_vencimiento:
        return  # La fecha de vencimiento es opcional

    if not isinstance(fecha_vencimiento, date):
        raise ValidationError("La fecha de vencimiento debe ser una fecha válida")

    hoy = date.today()

    # No puede estar vencida al crear/editar
    if fecha_vencimiento < hoy:
        raise ValidationError(
            f"La fecha de vencimiento no puede ser en el pasado. "
            f"Fecha proporcionada: {fecha_vencimiento.strftime('%d/%m/%Y')}"
        )

    # No puede ser mayor a 10 años
    max_fecha = hoy + timedelta(days=3650)  # ~10 años
    if fecha_vencimiento > max_fecha:
        raise ValidationError(
            f"La fecha de vencimiento no puede ser mayor a 10 años en el futuro. "
            f"Fecha máxima: {max_fecha.strftime('%d/%m/%Y')}"
        )

    # Warning si vence en menos de 30 días
    limite_warning = hoy + timedelta(days=30)
    if fecha_vencimiento <= limite_warning:
        raise ValidationError(
            f"⚠️ Advertencia: La tarjeta vence en menos de 30 días "
            f"({fecha_vencimiento.strftime('%d/%m/%Y')}). "
            f"Considere extender la vigencia.",
            code="warning",
        )


def validar_limite_credito(limite_credito):
    """
    Valida el límite de crédito de la tarjeta.

    Reglas:
    - Debe ser >= 0
    - No puede exceder ₲5,000,000
    - Máximo 2 decimales

    Args:
        limite_credito (Decimal): Límite de crédito

    Raises:
        ValidationError: Si el límite es inválido
    """
    if not isinstance(limite_credito, Decimal):
        try:
            limite_credito = Decimal(str(limite_credito))
        except (ValueError, TypeError):
            raise ValidationError("El límite de crédito debe ser un valor numérico")

    if limite_credito < 0:
        raise ValidationError("El límite de crédito no puede ser negativo")

    # Límite máximo
    limite_maximo = Decimal("5000000.00")  # ₲5M
    if limite_credito > limite_maximo:
        raise ValidationError(f"El límite de crédito no puede exceder ₲{limite_maximo:,.2f}")

    # Validar máximo 2 decimales
    if limite_credito.as_tuple().exponent < -2:
        raise ValidationError("El límite de crédito no puede tener más de 2 decimales")


def validar_saldo_alerta(saldo_alerta, saldo_actual):
    """
    Valida el saldo de alerta de la tarjeta.

    Reglas:
    - Debe ser > 0
    - Debe ser < saldo_actual (para tener sentido)
    - No puede exceder ₲1,000,000

    Args:
        saldo_alerta (Decimal): Saldo de alerta
        saldo_actual (Decimal): Saldo actual de la tarjeta

    Raises:
        ValidationError: Si el saldo de alerta es inválido
    """
    if saldo_alerta is None:
        return  # El saldo de alerta es opcional

    if not isinstance(saldo_alerta, Decimal):
        try:
            saldo_alerta = Decimal(str(saldo_alerta))
        except (ValueError, TypeError):
            raise ValidationError("El saldo de alerta debe ser un valor numérico")

    if saldo_alerta <= 0:
        raise ValidationError("El saldo de alerta debe ser mayor a cero")

    # Límite máximo
    limite_maximo = Decimal("1000000.00")  # ₲1M
    if saldo_alerta > limite_maximo:
        raise ValidationError(f"El saldo de alerta no puede exceder ₲{limite_maximo:,.2f}")

    # Warning si saldo_alerta >= saldo_actual
    if isinstance(saldo_actual, Decimal) and saldo_alerta >= saldo_actual:
        raise ValidationError(
            f"⚠️ Advertencia: El saldo de alerta (₲{saldo_alerta:,.2f}) "
            f"es mayor o igual al saldo actual (₲{saldo_actual:,.2f}). "
            f"Se enviará notificación inmediatamente.",
            code="warning",
        )


# =============================================================================
# VALIDADORES DE TARJETAS DE AUTORIZACIÓN (3)
# =============================================================================


def validar_codigo_barra_autorizacion(codigo_barra):
    """
    Valida el código de barras de tarjeta de autorización.

    Reglas:
    - Longitud: 8-50 caracteres
    - Formato: alfanumérico con guiones
    - Debe ser único

    Args:
        codigo_barra (str): Código de barras

    Raises:
        ValidationError: Si el formato es inválido
    """
    if not codigo_barra:
        raise ValidationError("El código de barras es obligatorio")

    codigo_limpio = codigo_barra.strip()

    # Validar longitud
    if len(codigo_limpio) < 8:
        raise ValidationError("El código de barras debe tener al menos 8 caracteres")

    if len(codigo_limpio) > 50:
        raise ValidationError("El código de barras no puede exceder 50 caracteres")

    # Validar formato
    if not re.match(r"^[A-Za-z0-9\-]+$", codigo_limpio):
        raise ValidationError("El código de barras solo puede contener letras, números y guiones")


def validar_tipo_autorizacion(tipo_autorizacion):
    """
    Valida el tipo de autorización.

    Tipos válidos:
    - Supervisor: Autorización de supervisor
    - Gerente: Autorización de gerente
    - Director: Autorización de director
    - Temporal: Autorización temporal

    Args:
        tipo_autorizacion (str): Tipo de autorización

    Raises:
        ValidationError: Si el tipo no es válido
    """
    TIPOS_VALIDOS = ["Supervisor", "Gerente", "Director", "Temporal"]

    if not tipo_autorizacion:
        raise ValidationError("El tipo de autorización es obligatorio")

    if tipo_autorizacion not in TIPOS_VALIDOS:
        raise ValidationError(f"Tipo '{tipo_autorizacion}' no válido. " f"Tipos permitidos: {', '.join(TIPOS_VALIDOS)}")


def validar_fecha_vencimiento_autorizacion(fecha_vencimiento, tipo_autorizacion):
    """
    Valida la fecha de vencimiento de tarjeta de autorización.

    Reglas:
    - Si es 'Temporal', fecha_vencimiento es obligatoria
    - No puede ser menor a la fecha actual
    - No puede ser mayor a 2 años en el futuro

    Args:
        fecha_vencimiento (date): Fecha de vencimiento
        tipo_autorizacion (str): Tipo de autorización

    Raises:
        ValidationError: Si la fecha es inválida
    """
    # Si es temporal, fecha es obligatoria
    if tipo_autorizacion == "Temporal" and not fecha_vencimiento:
        raise ValidationError("Las autorizaciones temporales requieren fecha de vencimiento")

    if not fecha_vencimiento:
        return  # Opcional para tipos permanentes

    if not isinstance(fecha_vencimiento, date):
        raise ValidationError("La fecha de vencimiento debe ser una fecha válida")

    hoy = date.today()

    # No puede estar vencida
    if fecha_vencimiento < hoy:
        raise ValidationError(
            f"La fecha de vencimiento no puede ser en el pasado. "
            f"Fecha proporcionada: {fecha_vencimiento.strftime('%d/%m/%Y')}"
        )

    # No puede ser mayor a 2 años
    max_fecha = hoy + timedelta(days=730)  # 2 años
    if fecha_vencimiento > max_fecha:
        raise ValidationError(
            f"La fecha de vencimiento no puede ser mayor a 2 años en el futuro. "
            f"Fecha máxima: {max_fecha.strftime('%d/%m/%Y')}"
        )


# =============================================================================
# VALIDADORES DE CARGAS DE SALDO (3)
# =============================================================================


def validar_monto_carga(monto):
    """
    Valida el monto de carga de saldo.

    Reglas:
    - Debe ser > 0
    - No puede exceder ₲10,000,000
    - Máximo 2 decimales

    Args:
        monto (Decimal): Monto de la carga

    Raises:
        ValidationError: Si el monto es inválido
    """
    if not isinstance(monto, Decimal):
        try:
            monto = Decimal(str(monto))
        except (ValueError, TypeError):
            raise ValidationError("El monto debe ser un valor numérico")

    if monto <= 0:
        raise ValidationError("El monto de carga debe ser mayor a cero")

    # Límite máximo por carga
    limite_maximo = Decimal("10000000.00")  # ₲10M
    if monto > limite_maximo:
        raise ValidationError(f"El monto de carga no puede exceder ₲{limite_maximo:,.2f}")

    # Validar máximo 2 decimales
    if monto.as_tuple().exponent < -2:
        raise ValidationError("El monto no puede tener más de 2 decimales")


def validar_estado_carga(estado):
    """
    Valida el estado de la carga de saldo.

    Estados válidos:
    - pendiente: Recarga iniciada, esperando confirmación
    - pendiente_validacion: Transferencia recibida, esperando validación del cajero
    - validacion_pendiente: Esperando aprobación de supervisor (monto elevado)
    - completada: Recarga exitosa, saldo acreditado
    - rechazada: Pago rechazado
    - cancelada: Carga cancelada
    - reembolsada: Carga reembolsada
    - expirada: Recarga no confirmada en tiempo límite

    Args:
        estado (str): Estado de la carga

    Raises:
        ValidationError: Si el estado no es válido
    """
    ESTADOS_VALIDOS = [
        "pendiente",
        "pendiente_validacion",
        "validacion_pendiente",
        "completada",
        "confirmado",
        "rechazada",
        "rechazado",
        "cancelada",
        "cancelado",
        "reembolsada",
        "reembolsado",
        "expirada",
    ]

    if not estado:
        raise ValidationError("El estado de la carga es obligatorio")

    if estado.lower() not in ESTADOS_VALIDOS and estado not in ESTADOS_VALIDOS:
        raise ValidationError(f"Estado '{estado}' no válido. Estados permitidos: {', '.join(ESTADOS_VALIDOS)}")


def validar_referencia_pago(referencia):
    """
    Valida la referencia de pago.

    Reglas:
    - Longitud: 5-100 caracteres
    - Formato: alfanumérico con guiones y guiones bajos

    Args:
        referencia (str): Referencia del pago

    Raises:
        ValidationError: Si la referencia es inválida
    """
    if not referencia:
        return  # La referencia es opcional

    referencia_limpia = referencia.strip()

    # Validar longitud
    if len(referencia_limpia) < 5:
        raise ValidationError("La referencia debe tener al menos 5 caracteres")

    if len(referencia_limpia) > 100:
        raise ValidationError("La referencia no puede exceder 100 caracteres")

    # Validar formato alfanumérico
    if not re.match(r"^[A-Za-z0-9\-_]+$", referencia_limpia):
        raise ValidationError("La referencia solo puede contener letras, números, guiones y guiones bajos")


def validar_metodo_pago_recarga(metodo_pago):
    """
    Valida el método de pago de la recarga.

    Métodos válidos:
    - efectivo: Pago en efectivo en caja
    - bancard: Pasarela de pago Bancard
    - tarjeta_pos: Tarjeta física en POS de caja
    - transferencia: Transferencia bancaria

    Args:
        metodo_pago (str): Método de pago

    Raises:
        ValidationError: Si el método no es válido
    """
    METODOS_VALIDOS = ["efectivo", "bancard", "tarjeta_pos", "transferencia"]

    if not metodo_pago:
        raise ValidationError("El método de pago es obligatorio")

    if metodo_pago not in METODOS_VALIDOS:
        raise ValidationError(f"Método '{metodo_pago}' no válido. Métodos permitidos: {', '.join(METODOS_VALIDOS)}")


def validar_numero_comprobante(numero_comprobante):
    """
    Valida el número de comprobante bancario/externo.

    Reglas:
    - Longitud: 5-100 caracteres
    - Formato: alfanumérico con guiones
    - Unicidad: Se verifica en servicio

    Args:
        numero_comprobante (str): Número del comprobante

    Raises:
        ValidationError: Si el número es inválido
    """
    if not numero_comprobante:
        return  # Es opcional en algunos flujos

    comprobante_limpio = numero_comprobante.strip().upper()

    if len(comprobante_limpio) < 5:
        raise ValidationError("El número de comprobante debe tener al menos 5 caracteres")

    if len(comprobante_limpio) > 100:
        raise ValidationError("El número de comprobante no puede exceder 100 caracteres")

    if not re.match(r"^[A-Z0-9\-_]+$", comprobante_limpio):
        raise ValidationError(
            "El número de comprobante solo puede contener letras mayúsculas, números, guiones y guiones bajos"
        )


def validar_codigo_referencia_interno(codigo):
    """
    Valida el código de referencia interno para transferencias.

    Formato esperado: REF-YYYYMMDD-NNNNN
    Ejemplo: REF-20260302-00001

    Args:
        codigo (str): Código de referencia

    Raises:
        ValidationError: Si el código es inválido
    """
    if not codigo:
        return  # Es opcional

    if not re.match(r"^REF-\d{8}-\d{5}$", codigo):
        raise ValidationError(
            "El código de referencia debe tener el formato REF-YYYYMMDD-NNNNN (ej: REF-20260302-00001)"
        )


# =============================================================================
# VALIDADORES DE CONSUMOS DE TARJETA (2)
# =============================================================================


def validar_monto_consumo(monto):
    """
    Valida el monto de consumo de tarjeta.

    Reglas:
    - Debe ser > 0
    - No puede exceder ₲1,000,000 (por seguridad)
    - Máximo 2 decimales

    Args:
        monto (Decimal): Monto del consumo

    Raises:
        ValidationError: Si el monto es inválido
    """
    if not isinstance(monto, Decimal):
        try:
            monto = Decimal(str(monto))
        except (ValueError, TypeError):
            raise ValidationError("El monto debe ser un valor numérico")

    if monto <= 0:
        raise ValidationError("El monto de consumo debe ser mayor a cero")

    # Límite máximo por consumo
    limite_maximo = Decimal("1000000.00")  # ₲1M
    if monto > limite_maximo:
        raise ValidationError(
            f"El monto de consumo no puede exceder ₲{limite_maximo:,.2f}. "
            f"Para montos mayores, contacte al administrador."
        )

    # Validar máximo 2 decimales
    if monto.as_tuple().exponent < -2:
        raise ValidationError("El monto no puede tener más de 2 decimales")


def validar_saldos_coherentes(saldo_anterior, saldo_posterior, monto_consumido):
    """
    Valida que los saldos sean coherentes.

    Regla:
    - saldo_posterior = saldo_anterior - monto_consumido (±₱0.02 tolerancia)

    Args:
        saldo_anterior (Decimal): Saldo antes del consumo
        saldo_posterior (Decimal): Saldo después del consumo
        monto_consumido (Decimal): Monto consumido

    Raises:
        ValidationError: Si los saldos no son coherentes
    """
    if not all(isinstance(x, Decimal) for x in [saldo_anterior, saldo_posterior, monto_consumido]):
        try:
            saldo_anterior = Decimal(str(saldo_anterior))
            saldo_posterior = Decimal(str(saldo_posterior))
            monto_consumido = Decimal(str(monto_consumido))
        except (ValueError, TypeError):
            raise ValidationError("Los saldos y montos deben ser valores numéricos")

    # Calcular saldo esperado
    saldo_esperado = saldo_anterior - monto_consumido

    # Tolerancia de redondeo
    tolerancia = Decimal("0.02")
    diferencia = abs(saldo_posterior - saldo_esperado)

    if diferencia > tolerancia:
        raise ValidationError(
            f"Los saldos no son coherentes. "
            f"Saldo anterior: ₲{saldo_anterior:,.2f}, "
            f"Monto consumido: ₲{monto_consumido:,.2f}, "
            f"Saldo posterior esperado: ₲{saldo_esperado:,.2f}, "
            f"Saldo posterior registrado: ₲{saldo_posterior:,.2f}. "
            f"Diferencia: ₲{diferencia:,.2f}"
        )


# =============================================================================
# VALIDADORES DE TRANSACCIONES ONLINE (2)
# =============================================================================


def validar_monto_transaccion(monto):
    """
    Valida el monto de transacción online.

    Reglas:
    - Debe ser > 0
    - No puede exceder ₲10,000,000
    - Máximo 2 decimales

    Args:
        monto (Decimal): Monto de la transacción

    Raises:
        ValidationError: Si el monto es inválido
    """
    if not isinstance(monto, Decimal):
        try:
            monto = Decimal(str(monto))
        except (ValueError, TypeError):
            raise ValidationError("El monto debe ser un valor numérico")

    if monto <= 0:
        raise ValidationError("El monto de transacción debe ser mayor a cero")

    # Límite máximo
    limite_maximo = Decimal("10000000.00")  # ₲10M
    if monto > limite_maximo:
        raise ValidationError(f"El monto de transacción no puede exceder ₲{limite_maximo:,.2f}")

    # Validar máximo 2 decimales
    if monto.as_tuple().exponent < -2:
        raise ValidationError("El monto no puede tener más de 2 decimales")


def validar_metodo_pago_online(metodo_pago):
    """
    Valida el método de pago online.

    Métodos válidos:
    - tarjeta_credito: Tarjeta de crédito
    - tarjeta_debito: Tarjeta de débito
    - transferencia: Transferencia bancaria
    - qr: Código QR (Wally, Gire, etc.)
    - billetera: Billetera digital

    Args:
        metodo_pago (str): Método de pago

    Raises:
        ValidationError: Si el método no es válido
    """
    METODOS_VALIDOS = ["tarjeta_credito", "tarjeta_debito", "transferencia", "qr", "billetera"]

    if not metodo_pago:
        raise ValidationError("El método de pago es obligatorio")

    if metodo_pago not in METODOS_VALIDOS:
        raise ValidationError(f"Método '{metodo_pago}' no válido. " f"Métodos permitidos: {', '.join(METODOS_VALIDOS)}")


# =============================================================================
# VALIDADORES DE MEDIOS DE PAGO (1)
# =============================================================================


def validar_descripcion_medio_pago(descripcion):
    """
    Valida la descripción del medio de pago.

    Reglas:
    - Longitud: 3-50 caracteres
    - Debe ser único

    Args:
        descripcion (str): Descripción del medio de pago

    Raises:
        ValidationError: Si la descripción es inválida
    """
    if not descripcion:
        raise ValidationError("La descripción del medio de pago es obligatoria")

    descripcion_limpia = descripcion.strip()

    # Validar longitud
    if len(descripcion_limpia) < 3:
        raise ValidationError("La descripción debe tener al menos 3 caracteres")

    if len(descripcion_limpia) > 50:
        raise ValidationError("La descripción no puede exceder 50 caracteres")


# =============================================================================
# VALIDADORES DE CONFIGURACIÓN DEL SISTEMA (4)
# =============================================================================


def validar_clave_configuracion(clave):
    """
    Valida el formato de la clave de configuración.

    Reglas:
    - Formato snake_case
    - 3-100 caracteres
    - Solo letras minúsculas, números y guiones bajos

    Args:
        clave (str): Clave de configuración

    Raises:
        ValidationError: Si el formato es inválido
    """
    if not clave:
        raise ValidationError("La clave de configuración es obligatoria")

    clave_limpia = clave.strip()

    # Validar longitud
    if len(clave_limpia) < 3:
        raise ValidationError("La clave debe tener al menos 3 caracteres")

    if len(clave_limpia) > 100:
        raise ValidationError("La clave no puede exceder 100 caracteres")

    # Validar formato snake_case
    if not re.match(r"^[a-z0-9_]+$", clave_limpia):
        raise ValidationError("La clave debe estar en formato snake_case (minúsculas, números y guiones bajos)")

    # No debe empezar o terminar con guion bajo
    if clave_limpia.startswith("_") or clave_limpia.endswith("_"):
        raise ValidationError("La clave no puede empezar ni terminar con guion bajo")


def validar_tipo_configuracion(tipo):
    """
    Valida el tipo de configuración.

    Tipos válidos:
    - string: Cadena de texto
    - int: Número entero
    - decimal: Número decimal
    - bool: Booleano (true/false)
    - json: Objeto JSON
    - email: Dirección de email
    - url: URL
    - date: Fecha

    Args:
        tipo (str): Tipo de configuración

    Raises:
        ValidationError: Si el tipo no es válido
    """
    TIPOS_VALIDOS = ["string", "int", "decimal", "bool", "json", "email", "url", "date"]

    if not tipo:
        raise ValidationError("El tipo de configuración es obligatorio")

    if tipo not in TIPOS_VALIDOS:
        raise ValidationError(f"Tipo '{tipo}' no válido. Tipos permitidos: {', '.join(TIPOS_VALIDOS)}")


def validar_valor_configuracion(valor, tipo, valores_permitidos=None, valor_min=None, valor_max=None):
    """
    Valida el valor de configuración según su tipo.

    Args:
        valor (str): Valor a validar
        tipo (str): Tipo de configuración (string, int, decimal, bool, json, email, url, date)
        valores_permitidos (list): Lista de valores permitidos (opcional)
        valor_min: Valor mínimo permitido (opcional)
        valor_max: Valor máximo permitido (opcional)

    Raises:
        ValidationError: Si el valor no cumple con las reglas
    """
    if not valor and valor != "0" and valor != "false":
        raise ValidationError("El valor de configuración es obligatorio")

    # Validar según tipo
    if tipo == "int":
        try:
            valor_int = int(valor)
            if valor_min is not None and valor_int < int(valor_min):
                raise ValidationError(f"El valor debe ser mayor o igual a {valor_min}")
            if valor_max is not None and valor_int > int(valor_max):
                raise ValidationError(f"El valor debe ser menor o igual a {valor_max}")
        except ValueError:
            raise ValidationError(f"El valor '{valor}' no es un número entero válido")

    elif tipo == "decimal":
        try:
            valor_decimal = Decimal(valor)
            if valor_min is not None and valor_decimal < Decimal(valor_min):
                raise ValidationError(f"El valor debe ser mayor o igual a {valor_min}")
            if valor_max is not None and valor_decimal > Decimal(valor_max):
                raise ValidationError(f"El valor debe ser menor o igual a {valor_max}")
        except (ValueError, TypeError):
            raise ValidationError(f"El valor '{valor}' no es un número decimal válido")

    elif tipo == "bool":
        if str(valor).lower() not in ["true", "false", "1", "0"]:
            raise ValidationError("El valor booleano debe ser 'true', 'false', '1' o '0'")

    elif tipo == "email":
        # Regex básico para email
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", valor):
            raise ValidationError(f"'{valor}' no es una dirección de email válida")

    elif tipo == "url":
        # Regex básico para URL
        if not re.match(r"^https?://[^\s/$.?#].[^\s]*$", valor):
            raise ValidationError(f"'{valor}' no es una URL válida")

    elif tipo == "date":
        try:
            datetime.strptime(valor, "%Y-%m-%d")
        except ValueError:
            raise ValidationError(f"'{valor}' no es una fecha válida. Formato esperado: YYYY-MM-DD")

    # Validar valores permitidos si existen
    if valores_permitidos and len(valores_permitidos) > 0:
        if valor not in valores_permitidos:
            raise ValidationError(
                f"El valor '{valor}' no está en la lista de valores permitidos: {', '.join(map(str, valores_permitidos))}"
            )


def validar_valores_permitidos(valores_permitidos, tipo):
    """
    Valida la lista de valores permitidos.

    Args:
        valores_permitidos (list): Lista de valores permitidos
        tipo (str): Tipo de configuración

    Raises:
        ValidationError: Si la lista es inválida
    """
    if not valores_permitidos:
        return  # Es opcional

    if not isinstance(valores_permitidos, list):
        raise ValidationError("Los valores permitidos deben ser una lista")

    if len(valores_permitidos) > 100:
        raise ValidationError("No puede haber más de 100 valores permitidos")


# =============================================================================
# VALIDADORES DE LÍMITES DE TRANSACCIÓN (3)
# =============================================================================


def validar_tipo_operacion_limite(tipo_operacion):
    """
    Valida el tipo de operación para límites de transacción.

    Operaciones válidas:
    - venta: Venta
    - descuento: Aplicar descuento
    - nota_credito_cliente: Nota de crédito a cliente
    - nota_credito_proveedor: Nota de crédito de proveedor
    - ajuste_inventario: Ajuste de inventario
    - exceder_credito: Exceder límite de crédito cliente
    - anular_venta: Anular venta
    - retiro_caja: Retiro de caja
    - devolucion: Procesar devolución

    Args:
        tipo_operacion (str): Tipo de operación

    Raises:
        ValidationError: Si el tipo no es válido
    """
    TIPOS_VALIDOS = [
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

    if not tipo_operacion:
        raise ValidationError("El tipo de operación es obligatorio")

    if tipo_operacion not in TIPOS_VALIDOS:
        raise ValidationError(
            f"Tipo de operación '{tipo_operacion}' no válido. " f"Operaciones permitidas: {', '.join(TIPOS_VALIDOS)}"
        )


def validar_monto_limite(monto):
    """
    Valida el monto máximo sin autorización.

    Reglas:
    - Debe ser > 0
    - No puede exceder ₲100,000,000
    - Máximo 2 decimales

    Args:
        monto (Decimal): Monto límite

    Raises:
        ValidationError: Si el monto es inválido
    """
    if not isinstance(monto, Decimal):
        try:
            monto = Decimal(str(monto))
        except (ValueError, TypeError):
            raise ValidationError("El monto límite debe ser un valor numérico")

    if monto <= 0:
        raise ValidationError("El monto límite debe ser mayor a cero")

    # Límite máximo
    limite_maximo = Decimal("100000000.00")  # ₲100M
    if monto > limite_maximo:
        raise ValidationError(f"El monto límite no puede exceder ₲{limite_maximo:,.2f}")

    # Validar máximo 2 decimales
    if monto.as_tuple().exponent < -2:
        raise ValidationError("El monto límite no puede tener más de 2 decimales")


def validar_unicidad_rol_operacion(id_rol, tipo_operacion, id_limite_actual=None):
    """
    Valida que no exista otro límite para la misma combinación rol-operación.

    Args:
        id_rol: ID del rol
        tipo_operacion (str): Tipo de operación
        id_limite_actual (int, optional): ID del límite actual (al editar)

    Raises:
        ValidationError: Si ya existe un límite para esta combinación
    """
    from apps.core.models import LimitesTransaccion

    if not id_rol or not tipo_operacion:
        return

    # Buscar límite existente
    query = LimitesTransaccion.objects.filter(id_rol=id_rol, tipo_operacion=tipo_operacion, estado=True)

    # Excluir el límite actual si estamos editando
    if id_limite_actual:
        query = query.exclude(id_limite=id_limite_actual)

    if query.exists():
        limite_existente = query.first()
        raise ValidationError(
            f"Ya existe un límite estado para el rol '{limite_existente.id_rol.nombre_rol}' "
            f"y la operación '{limite_existente.get_tipo_operacion_display()}'. "
            f"Monto actual: ₲{limite_existente.monto_maximo_sin_autorizacion:,.2f}"
        )


# =============================================================================
# VALIDADORES DE REGISTRO DE AUTORIZACIONES (2)
# =============================================================================


def validar_motivo_autorizacion(motivo):
    """
    Valida el motivo de la autorización.

    Reglas:
    - Longitud: 10-500 caracteres
    - Obligatorio

    Args:
        motivo (str): Motivo de la autorización

    Raises:
        ValidationError: Si el motivo es inválido
    """
    if not motivo or not str(motivo).strip():
        raise ValidationError("El motivo de la autorización es obligatorio")

    motivo_limpio = str(motivo).strip()

    # Validar longitud (mínimo 20 caracteres para contexto adecuado)
    if len(motivo_limpio) < 20:
        raise ValidationError("El motivo debe tener al menos 20 caracteres para proporcionar contexto adecuado")

    if len(motivo_limpio) > 500:
        raise ValidationError("El motivo no puede exceder 500 caracteres")


def validar_autorizadores_diferentes(id_empleado_solicitante, id_empleado_autorizador, id_empleado_autorizador_2=None):
    """
    Valida que los autorizadores sean diferentes al solicitante y entre sí.

    Reglas:
    - Autorizador != Solicitante
    - Si hay doble autorización: Autorizador1 != Autorizador2

    Args:
        id_empleado_solicitante: Empleado que solicita
        id_empleado_autorizador: Primer autorizador
        id_empleado_autorizador_2 (optional): Segundo autorizador

    Raises:
        ValidationError: Si los autorizadores no son válidos
    """
    if not id_empleado_solicitante or not id_empleado_autorizador:
        return  # Se validará como FK obligatorio

    # El autorizador no puede ser el mismo que el solicitante
    if id_empleado_solicitante == id_empleado_autorizador:
        raise ValidationError(
            "El empleado no puede autorizar su propia solicitud. " "Debe ser autorizada por un supervisor o gerente."
        )

    # Si hay doble autorización, los dos autorizadores deben ser diferentes
    if id_empleado_autorizador_2:
        if id_empleado_autorizador == id_empleado_autorizador_2:
            raise ValidationError("Los dos autorizadores deben ser empleados diferentes")

        if id_empleado_solicitante == id_empleado_autorizador_2:
            raise ValidationError("El empleado no puede ser su propio segundo autorizador")
