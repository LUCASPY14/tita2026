"""
Validadores para el módulo de Almuerzos
Validación completa de datos para planes, suscripciones, consumos y alérgenos
"""

import re
from datetime import date, datetime, time
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone

# ==============================================================================
# VALIDADORES PARA PLANES DE ALMUERZO
# ==============================================================================


def validar_nombre_plan(valor):
    """
    Valida el nombre del plan de almuerzo.

    Reglas:
    - Longitud: 3-100 caracteres
    - Caracteres permitidos: letras, números, espacios, guiones, paréntesis
    - No puede ser solo espacios

    Args:
        valor: Nombre del plan a validar

    Raises:
        ValidationError: Si el nombre no cumple los criterios
    """
    if valor is None or valor == "":
        raise ValidationError("El nombre del plan es obligatorio.")

    valor = str(valor).strip()

    if len(valor) < 3:
        raise ValidationError("El nombre del plan debe tener al menos 3 caracteres.")

    if len(valor) > 100:
        raise ValidationError("El nombre del plan no puede exceder 100 caracteres.")

    # Alfanumérico + espacios + caracteres especiales comunes
    patron = r"^[a-zA-Z0-9áéíóúñÁÉÍÓÚÑ\s\-\(\)]+$"
    if not re.match(patron, valor):
        raise ValidationError("El nombre del plan contiene caracteres no permitidos.")


def validar_descripcion_plan(valor):
    """
    Valida la descripción del plan (opcional).

    Reglas:
    - Máximo 500 caracteres si se proporciona
    - Puede ser None/vacío

    Args:
        valor: Descripción a validar

    Raises:
        ValidationError: Si excede la longitud máxima
    """
    if valor is None or valor == "":
        return  # Opcional

    if len(str(valor)) > 500:
        raise ValidationError("La descripción no puede exceder 500 caracteres.")


def validar_precio_mensual_plan(valor):
    """
    Valida el precio mensual del plan.

    Reglas:
    - Debe ser mayor a 0
    - Máximo ₲5,000,000 (razonable para plan mensual)
    - Máximo 2 decimales

    Args:
        valor: Precio mensual a validar

    Raises:
        ValidationError: Si el precio no es válido
    """
    if valor is None:
        raise ValidationError("El precio mensual es obligatorio.")

    try:
        valor = Decimal(str(valor))
    except:
        raise ValidationError("El precio mensual debe ser un número válido.")

    if valor <= 0:
        raise ValidationError("El precio mensual debe ser mayor a 0.")

    if valor > Decimal("5000000.00"):
        raise ValidationError("El precio mensual no puede exceder ₲5,000,000.")

    # Verificar que tenga máximo 2 decimales
    valor_str = str(valor)
    if "." in valor_str:
        decimales = valor_str.split(".")[1]
        if len(decimales) > 2:
            raise ValidationError("El precio mensual puede tener máximo 2 decimales.")


def validar_dias_semana_incluidos(valor):
    """
    Valida los días de la semana incluidos en el plan.

    Reglas:
    - Formato: "L,M,Mi,J,V" o "L-V" o similar
    - Longitud máxima: 60 caracteres
    - Debe contener al menos 1 día

    Args:
        valor: String con días de la semana

    Raises:
        ValidationError: Si el formato no es válido
    """
    if valor is None or valor == "":
        raise ValidationError("Los días de la semana son obligatorios.")

    valor = str(valor).strip()

    if len(valor) > 60:
        raise ValidationError("Los días de la semana no pueden exceder 60 caracteres.")

    # Verificar que contenga al menos un día válido
    dias_validos = [
        "L",
        "M",
        "Mi",
        "J",
        "V",
        "S",
        "D",
        "Lunes",
        "Martes",
        "Miércoles",
        "Jueves",
        "Viernes",
        "Sábado",
        "Domingo",
    ]

    tiene_dia_valido = any(dia in valor for dia in dias_validos)

    if not tiene_dia_valido:
        raise ValidationError("Debe especificar al menos un día de la semana válido.")


# ==============================================================================
# VALIDADORES PARA TIPOS DE ALMUERZO
# ==============================================================================


def validar_nombre_tipo_almuerzo(valor):
    """
    Valida el nombre del tipo de almuerzo.

    Reglas:
    - Longitud: 3-100 caracteres
    - Alfanumérico con espacios y tildes

    Args:
        valor: Nombre del tipo a validar

    Raises:
        ValidationError: Si el nombre no es válido
    """
    if valor is None or valor == "":
        raise ValidationError("El nombre del tipo de almuerzo es obligatorio.")

    valor = str(valor).strip()

    if len(valor) < 3:
        raise ValidationError("El nombre debe tener al menos 3 caracteres.")

    if len(valor) > 100:
        raise ValidationError("El nombre no puede exceder 100 caracteres.")

    patron = r"^[a-zA-Z0-9áéíóúñÁÉÍÓÚÑ\s]+$"
    if not re.match(patron, valor):
        raise ValidationError("El nombre contiene caracteres no permitidos.")


def validar_precio_unitario_tipo(valor):
    """
    Valida el precio unitario del tipo de almuerzo.

    Reglas:
    - Debe ser mayor a 0
    - Máximo ₲500,000 (precio por almuerzo individual)
    - Máximo 2 decimales

    Args:
        valor: Precio unitario a validar

    Raises:
        ValidationError: Si el precio no es válido
    """
    if valor is None:
        raise ValidationError("El precio unitario es obligatorio.")

    try:
        valor = Decimal(str(valor))
    except:
        raise ValidationError("El precio unitario debe ser un número válido.")

    if valor <= 0:
        raise ValidationError("El precio unitario debe ser mayor a 0.")

    if valor > Decimal("500000.00"):
        raise ValidationError("El precio unitario no puede exceder ₲500,000.")

    # Verificar decimales
    valor_str = str(valor)
    if "." in valor_str:
        decimales = valor_str.split(".")[1]
        if len(decimales) > 2:
            raise ValidationError("El precio puede tener máximo 2 decimales.")


# ==============================================================================
# VALIDADORES PARA SUSCRIPCIONES
# ==============================================================================


def validar_fecha_inicio_suscripcion(valor):
    """
    Valida la fecha de inicio de la suscripción.

    Reglas:
    - No puede ser anterior a 2020
    - No puede ser más de 1 año en el futuro

    Args:
        valor: Fecha de inicio a validar

    Raises:
        ValidationError: Si la fecha no es válida
    """
    if valor is None:
        raise ValidationError("La fecha de inicio es obligatoria.")

    if isinstance(valor, str):
        try:
            valor = datetime.strptime(valor, "%Y-%m-%d").date()
        except:
            raise ValidationError("Formato de fecha inválido. Use YYYY-MM-DD.")

    if valor < date(2020, 1, 1):
        raise ValidationError("La fecha de inicio no puede ser anterior a 2020.")

    fecha_limite_futura = date.today().replace(year=date.today().year + 1)
    if valor > fecha_limite_futura:
        raise ValidationError("La fecha de inicio no puede ser más de 1 año en el futuro.")


def validar_fecha_fin_suscripcion(valor):
    """
    Valida la fecha de fin de la suscripción (opcional).

    Reglas:
    - Puede ser None (suscripción activa)
    - Si existe, no puede ser anterior a 2020
    - No puede ser más de 5 años en el futuro

    Args:
        valor: Fecha de fin a validar

    Raises:
        ValidationError: Si la fecha no es válida
    """
    if valor is None or valor == "":
        return  # Opcional

    if isinstance(valor, str):
        try:
            valor = datetime.strptime(valor, "%Y-%m-%d").date()
        except:
            raise ValidationError("Formato de fecha inválido. Use YYYY-MM-DD.")

    if valor < date(2020, 1, 1):
        raise ValidationError("La fecha de fin no puede ser anterior a 2020.")

    fecha_limite_futura = date.today().replace(year=date.today().year + 5)
    if valor > fecha_limite_futura:
        raise ValidationError("La fecha de fin no puede ser más de 5 años en el futuro.")


def validar_estado_suscripcion(valor):
    """
    Valida el estado de la suscripción.

    Reglas:
    - Valores permitidos: Activa, Pausada, Cancelada, Finalizada
    - Máximo 10 caracteres

    Args:
        valor: Estado a validar

    Raises:
        ValidationError: Si el estado no es válido
    """
    if valor is None or valor == "":
        return  # Puede ser opcional según modelo

    estados_validos = ["Activa", "Pausada", "Cancelada", "Finalizada"]

    if valor not in estados_validos:
        raise ValidationError(f'Estado inválido. Valores permitidos: {", ".join(estados_validos)}')


def validar_rango_fechas_suscripcion(fecha_inicio, fecha_fin):
    """
    Valida que el rango de fechas de la suscripción sea coherente.

    Reglas:
    - fecha_fin debe ser posterior a fecha_inicio

    Args:
        fecha_inicio: Fecha de inicio
        fecha_fin: Fecha de fin

    Raises:
        ValidationError: Si el rango no es válido
    """
    if fecha_inicio is None:
        return

    if fecha_fin is not None and fecha_fin <= fecha_inicio:
        raise ValidationError("La fecha de fin debe ser posterior a la fecha de inicio.")


# ==============================================================================
# VALIDADORES PARA REGISTROS DE CONSUMO
# ==============================================================================


def validar_fecha_consumo(valor):
    """
    Valida la fecha del consumo de almuerzo.

    Reglas:
    - No puede ser futura
    - No puede ser anterior a 2020
    - No puede ser más de 90 días en el pasado

    Args:
        valor: Fecha de consumo a validar

    Raises:
        ValidationError: Si la fecha no es válida
    """
    if valor is None:
        raise ValidationError("La fecha de consumo es obligatoria.")

    if isinstance(valor, str):
        try:
            valor = datetime.strptime(valor, "%Y-%m-%d").date()
        except:
            raise ValidationError("Formato de fecha inválido. Use YYYY-MM-DD.")

    if valor > date.today():
        raise ValidationError("La fecha de consumo no puede ser futura.")

    if valor < date(2020, 1, 1):
        raise ValidationError("La fecha de consumo no puede ser anterior a 2020.")

    # No más de 90 días atrás (política de registro)
    from datetime import timedelta

    fecha_limite_pasado = date.today() - timedelta(days=90)
    if valor < fecha_limite_pasado:
        raise ValidationError("La fecha de consumo no puede ser más de 90 días en el pasado.")


def validar_hora_registro(valor):
    """
    Valida la hora de registro del consumo.

    Reglas:
    - Formato válido HH:MM:SS
    - Dentro del horario de almuerzo razonable (06:00 - 16:00)

    Args:
        valor: Hora de registro a validar

    Raises:
        ValidationError: Si la hora no es válida
    """
    if valor is None:
        raise ValidationError("La hora de registro es obligatoria.")

    if isinstance(valor, str):
        try:
            valor = datetime.strptime(valor, "%H:%M:%S").time()
        except:
            try:
                valor = datetime.strptime(valor, "%H:%M").time()
            except:
                raise ValidationError("Formato de hora inválido. Use HH:MM:SS o HH:MM.")

    # Verificar rango razonable (6 AM a 4 PM)
    hora_inicio = time(6, 0, 0)
    hora_fin = time(16, 0, 0)

    if valor < hora_inicio or valor > hora_fin:
        raise ValidationError("La hora de registro debe estar entre 06:00 y 16:00.")


def validar_costo_almuerzo(valor):
    """
    Valida el costo del almuerzo en el registro de consumo.

    Reglas:
    - Puede ser None (se calcula automáticamente)
    - Si existe, debe ser >= 0 y <= ₲200,000
    - Máximo 2 decimales

    Args:
        valor: Costo a validar

    Raises:
        ValidationError: Si el costo no es válido
    """
    if valor is None or valor == "":
        return  # Opcional

    try:
        valor = Decimal(str(valor))
    except:
        raise ValidationError("El costo debe ser un número válido.")

    if valor < 0:
        raise ValidationError("El costo no puede ser negativo.")

    if valor > Decimal("200000.00"):
        raise ValidationError("El costo no puede exceder ₲200,000.")

    # Verificar decimales
    valor_str = str(valor)
    if "." in valor_str:
        decimales = valor_str.split(".")[1]
        if len(decimales) > 2:
            raise ValidationError("El costo puede tener máximo 2 decimales.")


def validar_estado_consumo(valor):
    """
    Valida el estado del registro de consumo.

    Reglas:
    - Valores permitidos: Registrado, Confirmado, Rechazado, Cancelado
    - Máximo 20 caracteres

    Args:
        valor: Estado a validar

    Raises:
        ValidationError: Si el estado no es válido
    """
    if valor is None or valor == "":
        raise ValidationError("El estado del consumo es obligatorio.")

    estados_validos = ["Registrado", "Confirmado", "Rechazado", "Cancelado"]

    if valor not in estados_validos:
        raise ValidationError(f'Estado inválido. Valores permitidos: {", ".join(estados_validos)}')


def validar_motivo_rechazo(valor, estado):
    """
    Valida el motivo de rechazo (requerido si estado es Rechazado).

    Reglas:
    - Obligatorio si estado = 'Rechazado'
    - Longitud: 10-255 caracteres

    Args:
        valor: Motivo de rechazo
        estado: Estado del consumo

    Raises:
        ValidationError: Si el motivo no es válido
    """
    if estado == "Rechazado":
        if valor is None or valor == "":
            raise ValidationError("El motivo de rechazo es obligatorio cuando el estado es Rechazado.")

        if len(str(valor)) < 10:
            raise ValidationError("El motivo de rechazo debe tener al menos 10 caracteres.")

        if len(str(valor)) > 255:
            raise ValidationError("El motivo de rechazo no puede exceder 255 caracteres.")
    else:
        # Si el estado no es Rechazado, el motivo debe estar vacío
        if valor is not None and valor != "":
            raise ValidationError("El motivo de rechazo solo debe proporcionarse cuando el estado es Rechazado.")


def validar_limite_registros_diarios(id_hijo, fecha_consumo, registro_actual_id=None):
    """
    Valida que un hijo no tenga más de 2 registros de almuerzo en el mismo día.

    REGLA DE NEGOCIO:
    - Máximo 2 registros por alumno por día
    - Primer registro: genera cobro (ya_cobrado=True)
    - Segundo registro: NO genera cobro (ya_cobrado=False)
    - Tercer intento: BLOQUEADO

    Args:
        id_hijo: ID del hijo
        fecha_consumo: Fecha del consumo
        registro_actual_id: ID del registro actual (para excluir en updates)

    Raises:
        ValidationError: Si ya existen 2 registros en el día
    """
    from .models import RegistrosConsumoAlmuerzo

    if id_hijo is None or fecha_consumo is None:
        return

    # Convertir fecha a date si es string
    if isinstance(fecha_consumo, str):
        from datetime import datetime

        try:
            fecha_consumo = datetime.strptime(fecha_consumo, "%Y-%m-%d").date()
        except:
            return  # Si la fecha es inválida, otro validador lo manejará

    # Contar registros existentes del hijo en la fecha (excluir registro actual si es update)
    query = RegistrosConsumoAlmuerzo.objects.filter(
        id_hijo=id_hijo,
        fecha_consumo=fecha_consumo,
        estado__in=["Registrado", "Confirmado"],  # Solo contar registros válidos
    )

    if registro_actual_id is not None:
        query = query.exclude(id_registro_consumo=registro_actual_id)

    registros_existentes = query.count()

    # Bloquear si ya hay 2 registros
    if registros_existentes >= 2:
        raise ValidationError(
            f"Límite alcanzado: Ya existen {registros_existentes} registros de almuerzo "
            f'para este alumno el {fecha_consumo.strftime("%d/%m/%Y")}. '
            f"Máximo permitido: 2 registros por día."
        )

    # Retornar True si es el primer registro (cobrará), False si es el segundo (no cobrará)
    return registros_existentes == 0


def determinar_si_cobra(id_hijo, fecha_consumo, registro_actual_id=None):
    """
    Determina si un registro de almuerzo debe generar cobro de saldo.

    LÓGICA:
    - Primer registro del día → ya_cobrado=True (genera cobro)
    - Segundo registro del día → ya_cobrado=False (no genera cobro)

    Args:
        id_hijo: ID del hijo
        fecha_consumo: Fecha del consumo
        registro_actual_id: ID del registro actual (para excluir en updates)

    Returns:
        bool: True si debe cobrar, False si no debe cobrar
    """
    from .models import RegistrosConsumoAlmuerzo

    if id_hijo is None or fecha_consumo is None:
        return True  # Por defecto cobra

    # Convertir fecha a date si es string
    if isinstance(fecha_consumo, str):
        from datetime import datetime

        try:
            fecha_consumo = datetime.strptime(fecha_consumo, "%Y-%m-%d").date()
        except:
            return True

    # Contar registros existentes del hijo en la fecha
    query = RegistrosConsumoAlmuerzo.objects.filter(
        id_hijo=id_hijo, fecha_consumo=fecha_consumo, estado__in=["Registrado", "Confirmado"]
    )

    if registro_actual_id is not None:
        query = query.exclude(id_registro_consumo=registro_actual_id)

    registros_existentes = query.count()

    # Primer registro (0 existentes) → cobra (True)
    # Segundo registro (1 existente) → NO cobra (False)
    return registros_existentes == 0


# ==============================================================================
# VALIDADORES PARA CUENTAS MENSUALES
# ==============================================================================


def validar_anio_cuenta(valor):
    """
    Valida el año de la cuenta mensual.

    Reglas:
    - Rango: 2020 a año_actual + 1

    Args:
        valor: Año a validar

    Raises:
        ValidationError: Si el año no es válido
    """
    if valor is None:
        raise ValidationError("El año es obligatorio.")

    try:
        valor = int(valor)
    except:
        raise ValidationError("El año debe ser un número entero.")

    anio_actual = date.today().year

    if valor < 2020:
        raise ValidationError("El año no puede ser anterior a 2020.")

    if valor > anio_actual + 1:
        raise ValidationError(f"El año no puede ser posterior a {anio_actual + 1}.")


def validar_mes_cuenta(valor):
    """
    Valida el mes de la cuenta mensual.

    Reglas:
    - Rango: 1-12

    Args:
        valor: Mes a validar

    Raises:
        ValidationError: Si el mes no es válido
    """
    if valor is None:
        raise ValidationError("El mes es obligatorio.")

    try:
        valor = int(valor)
    except:
        raise ValidationError("El mes debe ser un número entero.")

    if valor < 1 or valor > 12:
        raise ValidationError("El mes debe estar entre 1 y 12.")


def validar_cantidad_almuerzos(valor):
    """
    Valida la cantidad de almuerzos en la cuenta mensual.

    Reglas:
    - Entero >= 0
    - Máximo 31 (máximo días en un mes)

    Args:
        valor: Cantidad a validar

    Raises:
        ValidationError: Si la cantidad no es válida
    """
    if valor is None:
        raise ValidationError("La cantidad de almuerzos es obligatoria.")

    try:
        valor = int(valor)
    except:
        raise ValidationError("La cantidad debe ser un número entero.")

    if valor < 0:
        raise ValidationError("La cantidad no puede ser negativa.")

    if valor > 31:
        raise ValidationError("La cantidad no puede exceder 31 almuerzos por mes.")


def validar_monto_total_cuenta(valor):
    """
    Valida el monto total de la cuenta mensual.

    Reglas:
    - >= 0 y <= ₲10,000,000
    - Máximo 2 decimales

    Args:
        valor: Monto total a validar

    Raises:
        ValidationError: Si el monto no es válido
    """
    if valor is None:
        raise ValidationError("El monto total es obligatorio.")

    try:
        valor = Decimal(str(valor))
    except:
        raise ValidationError("El monto total debe ser un número válido.")

    if valor < 0:
        raise ValidationError("El monto total no puede ser negativo.")

    if valor > Decimal("10000000.00"):
        raise ValidationError("El monto total no puede exceder ₲10,000,000.")

    # Verificar decimales
    valor_str = str(valor)
    if "." in valor_str:
        decimales = valor_str.split(".")[1]
        if len(decimales) > 2:
            raise ValidationError("El monto puede tener máximo 2 decimales.")


def validar_forma_cobro(valor):
    """
    Valida la forma de cobro de la cuenta mensual.

    Reglas:
    - Valores permitidos: Efectivo, Transferencia, Tarjeta, Cuenta Corriente
    - Máximo 20 caracteres

    Args:
        valor: Forma de cobro a validar

    Raises:
        ValidationError: Si la forma de cobro no es válida
    """
    if valor is None or valor == "":
        raise ValidationError("La forma de cobro es obligatoria.")

    formas_validas = [
        "Efectivo",
        "Transferencia",
        "Tarjeta",
        "Cuenta Corriente",
        "Débito Automático",
    ]

    if valor not in formas_validas:
        raise ValidationError(f'Forma de cobro inválida. Valores permitidos: {", ".join(formas_validas)}')


def validar_monto_pagado_cuenta(valor):
    """
    Valida el monto pagado de la cuenta mensual.

    Reglas:
    - >= 0 y <= ₲10,000,000
    - Máximo 2 decimales

    Args:
        valor: Monto pagado a validar

    Raises:
        ValidationError: Si el monto no es válido
    """
    if valor is None:
        raise ValidationError("El monto pagado es obligatorio.")

    try:
        valor = Decimal(str(valor))
    except:
        raise ValidationError("El monto pagado debe ser un número válido.")

    if valor < 0:
        raise ValidationError("El monto pagado no puede ser negativo.")

    if valor > Decimal("10000000.00"):
        raise ValidationError("El monto pagado no puede exceder ₲10,000,000.")

    # Verificar decimales
    valor_str = str(valor)
    if "." in valor_str:
        decimales = valor_str.split(".")[1]
        if len(decimales) > 2:
            raise ValidationError("El monto puede tener máximo 2 decimales.")


def validar_estado_cuenta(valor):
    """
    Valida el estado de la cuenta mensual.

    Reglas:
    - Valores permitidos: Pendiente, Pagada, Vencida, Cancelada
    - Máximo 10 caracteres

    Args:
        valor: Estado a validar

    Raises:
        ValidationError: Si el estado no es válido
    """
    if valor is None or valor == "":
        raise ValidationError("El estado de la cuenta es obligatorio.")

    estados_validos = ["Pendiente", "Pagada", "Vencida", "Cancelada"]

    if valor not in estados_validos:
        raise ValidationError(f'Estado inválido. Valores permitidos: {", ".join(estados_validos)}')


def validar_coherencia_montos_cuenta(monto_total, monto_pagado):
    """
    Valida la coherencia entre monto total y monto pagado.

    Reglas:
    - monto_pagado no puede exceder monto_total + 10% (tolerancia por cambios)

    Args:
        monto_total: Monto total de la cuenta
        monto_pagado: Monto pagado

    Raises:
        ValidationError: Si los montos no son coherentes
    """
    if monto_total is None or monto_pagado is None:
        return

    try:
        monto_total = Decimal(str(monto_total))
        monto_pagado = Decimal(str(monto_pagado))
    except:
        return

    # Tolerancia del 10% para cambios de última hora
    tolerancia = monto_total * Decimal("1.10")

    if monto_pagado > tolerancia:
        raise ValidationError(
            f"El monto pagado (₲{monto_pagado:,.2f}) excede el monto total + tolerancia (₲{tolerancia:,.2f})."
        )


# ==============================================================================
# VALIDADORES PARA PAGOS
# ==============================================================================


def validar_fecha_pago(valor):
    """
    Valida la fecha de pago.

    Reglas:
    - No puede ser futura
    - No puede ser anterior a 2020

    Args:
        valor: Fecha de pago a validar

    Raises:
        ValidationError: Si la fecha no es válida
    """
    if valor is None:
        raise ValidationError("La fecha de pago es obligatoria.")

    # Si es datetime, extraer la fecha
    if isinstance(valor, datetime):
        valor = valor.date()
    elif isinstance(valor, str):
        try:
            valor = datetime.strptime(valor.split()[0], "%Y-%m-%d").date()
        except:
            raise ValidationError("Formato de fecha inválido.")

    if valor > date.today():
        raise ValidationError("La fecha de pago no puede ser futura.")

    if valor < date(2020, 1, 1):
        raise ValidationError("La fecha de pago no puede ser anterior a 2020.")


def validar_monto_pago(valor):
    """
    Valida el monto de un pago.

    Reglas:
    - Debe ser > 0
    - Máximo ₲10,000,000
    - Máximo 2 decimales

    Args:
        valor: Monto a validar

    Raises:
        ValidationError: Si el monto no es válido
    """
    if valor is None:
        raise ValidationError("El monto del pago es obligatorio.")

    try:
        valor = Decimal(str(valor))
    except:
        raise ValidationError("El monto debe ser un número válido.")

    if valor <= 0:
        raise ValidationError("El monto del pago debe ser mayor a 0.")

    if valor > Decimal("10000000.00"):
        raise ValidationError("El monto del pago no puede exceder ₲10,000,000.")

    # Verificar decimales
    valor_str = str(valor)
    if "." in valor_str:
        decimales = valor_str.split(".")[1]
        if len(decimales) > 2:
            raise ValidationError("El monto puede tener máximo 2 decimales.")


def validar_medio_pago(valor):
    """
    Valida el medio de pago.

    Reglas:
    - Valores permitidos: Efectivo, Transferencia, Tarjeta Débito, Tarjeta Crédito, Cheque
    - Máximo 15 caracteres

    Args:
        valor: Medio de pago a validar

    Raises:
        ValidationError: Si el medio de pago no es válido
    """
    if valor is None or valor == "":
        raise ValidationError("El medio de pago es obligatorio.")

    medios_validos = ["Efectivo", "Transferencia", "Tarjeta Débito", "Tarjeta Crédito", "Cheque"]

    if valor not in medios_validos:
        raise ValidationError(f'Medio de pago inválido. Valores permitidos: {", ".join(medios_validos)}')


def validar_referencia_pago(valor):
    """
    Valida la referencia del pago (opcional).

    Reglas:
    - Máximo 50 caracteres si se proporciona
    - Alfanumérico con guiones

    Args:
        valor: Referencia a validar

    Raises:
        ValidationError: Si la referencia no es válida
    """
    if valor is None or valor == "":
        return  # Opcional

    if len(str(valor)) > 50:
        raise ValidationError("La referencia no puede exceder 50 caracteres.")

    # Alfanumérico + guiones + espacios
    patron = r"^[a-zA-Z0-9\-\s]+$"
    if not re.match(patron, str(valor)):
        raise ValidationError("La referencia contiene caracteres no permitidos.")


def validar_estado_pago_mensual(valor):
    """
    Valida el estado del pago mensual.

    Reglas:
    - Valores permitidos: Pendiente, Confirmado, Rechazado
    - Máximo 9 caracteres

    Args:
        valor: Estado a validar

    Raises:
        ValidationError: Si el estado no es válido
    """
    if valor is None or valor == "":
        return  # Puede ser opcional

    estados_validos = ["Pendiente", "Confirmado", "Rechazado"]

    if valor not in estados_validos:
        raise ValidationError(f'Estado inválido. Valores permitidos: {", ".join(estados_validos)}')


# ==============================================================================
# VALIDADORES PARA ALÉRGENOS
# ==============================================================================


def validar_nombre_alergeno(valor):
    """
    Valida el nombre del alérgeno.

    Reglas:
    - Longitud: 3-100 caracteres
    - Alfanumérico con espacios y tildes
    - Debe ser único

    Args:
        valor: Nombre del alérgeno a validar

    Raises:
        ValidationError: Si el nombre no es válido
    """
    if valor is None or valor == "":
        raise ValidationError("El nombre del alérgeno es obligatorio.")

    valor = str(valor).strip()

    if len(valor) < 3:
        raise ValidationError("El nombre debe tener al menos 3 caracteres.")

    if len(valor) > 100:
        raise ValidationError("El nombre no puede exceder 100 caracteres.")

    patron = r"^[a-zA-Z0-9áéíóúñÁÉÍÓÚÑ\s]+$"
    if not re.match(patron, valor):
        raise ValidationError("El nombre contiene caracteres no permitidos.")


def validar_palabras_clave_alergeno(valor):
    """
    Valida las palabras clave del alérgeno (JSON).

    Reglas:
    - Debe ser una lista válida
    - Cada palabra clave: 2-50 caracteres
    - Máximo 20 palabras clave

    Args:
        valor: Lista de palabras clave o JSON string

    Raises:
        ValidationError: Si las palabras clave no son válidas
    """
    import json

    if valor is None:
        raise ValidationError("Las palabras clave son obligatorias.")

    # Si es string JSON, convertir a lista
    if isinstance(valor, str):
        try:
            valor = json.loads(valor)
        except:
            raise ValidationError("El formato JSON de palabras clave no es válido.")

    if not isinstance(valor, list):
        raise ValidationError("Las palabras clave deben ser una lista.")

    if len(valor) == 0:
        raise ValidationError("Debe proporcionar al menos una palabra clave.")

    if len(valor) > 20:
        raise ValidationError("No puede tener más de 20 palabras clave.")

    for palabra in valor:
        if not isinstance(palabra, str):
            raise ValidationError("Cada palabra clave debe ser un texto.")

        if len(palabra) < 2:
            raise ValidationError("Cada palabra clave debe tener al menos 2 caracteres.")

        if len(palabra) > 50:
            raise ValidationError("Cada palabra clave no puede exceder 50 caracteres.")


def validar_nivel_severidad_alergeno(valor):
    """
    Valida el nivel de severidad del alérgeno.

    Reglas:
    - Valores permitidos: Baja, Media, Alta, Crítica
    - Máximo 10 caracteres

    Args:
        valor: Nivel de severidad a validar

    Raises:
        ValidationError: Si el nivel de severidad no es válido
    """
    if valor is None or valor == "":
        raise ValidationError("El nivel de severidad es obligatorio.")

    niveles_validos = ["Baja", "Media", "Alta", "Crítica"]

    if valor not in niveles_validos:
        raise ValidationError(f'Nivel de severidad inválido. Valores permitidos: {", ".join(niveles_validos)}')


def validar_icono_alergeno(valor):
    """
    Valida el icono del alérgeno (opcional).

    Reglas:
    - Máximo 10 caracteres (emoji o código)
    - Puede ser None

    Args:
        valor: Icono a validar

    Raises:
        ValidationError: Si el icono no es válido
    """
    if valor is None or valor == "":
        return  # Opcional

    if len(str(valor)) > 10:
        raise ValidationError("El icono no puede exceder 10 caracteres.")


def validar_usuario_creacion(valor):
    """
    Valida el usuario de creación (opcional).

    Reglas:
    - Máximo 100 caracteres
    - Alfanumérico con espacios

    Args:
        valor: Usuario a validar

    Raises:
        ValidationError: Si el usuario no es válido
    """
    if valor is None or valor == "":
        return  # Opcional

    if len(str(valor)) > 100:
        raise ValidationError("El usuario no puede exceder 100 caracteres.")

    patron = r"^[a-zA-Z0-9\s\.\_\-]+$"
    if not re.match(patron, str(valor)):
        raise ValidationError("El usuario contiene caracteres no permitidos.")


# ==============================================================================
# VALIDADORES PARA PRODUCTOS-ALÉRGENOS
# ==============================================================================


def validar_observaciones_producto_alergeno(valor):
    """
    Valida las observaciones del producto-alérgeno (opcional).

    Reglas:
    - Máximo 500 caracteres si se proporciona

    Args:
        valor: Observaciones a validar

    Raises:
        ValidationError: Si las observaciones no son válidas
    """
    if valor is None or valor == "":
        return  # Opcional

    if len(str(valor)) > 500:
        raise ValidationError("Las observaciones no pueden exceder 500 caracteres.")
