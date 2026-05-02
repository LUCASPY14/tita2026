"""
Validadores personalizados para el módulo de ventas.
Validaciones de negocio reutilizables.
"""

from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
import re


def validar_monto_positivo(valor):
    """
    Valida que un monto sea mayor a cero.

    Args:
        valor: Decimal o float a validar

    Raises:
        ValidationError: Si el monto es <= 0

    Example:
        >>> validar_monto_positivo(Decimal('100.50'))  # OK
        >>> validar_monto_positivo(Decimal('0'))  # ValidationError
        >>> validar_monto_positivo(Decimal('-10'))  # ValidationError
    """
    if not isinstance(valor, (Decimal, float, int)):
        raise ValidationError(f"El valor debe ser numérico, recibido: {type(valor).__name__}")

    valor_decimal = Decimal(str(valor))

    if valor_decimal <= 0:
        raise ValidationError(f"El monto debe ser mayor a cero. Valor recibido: {valor_decimal}")


def validar_monto_rango(valor, minimo=None, maximo=None):
    """
    Valida que un monto esté dentro de un rango.

    Args:
        valor: Monto a validar
        minimo: Valor mínimo permitido (inclusive)
        maximo: Valor máximo permitido (inclusive)

    Raises:
        ValidationError: Si está fuera del rango

    Example:
        >>> validar_monto_rango(Decimal('500'), minimo=Decimal('100'), maximo=Decimal('1000'))
        >>> validar_monto_rango(Decimal('50'), minimo=Decimal('100'))  # Error
    """
    valor_decimal = Decimal(str(valor))

    if minimo is not None and valor_decimal < Decimal(str(minimo)):
        raise ValidationError(f"El monto debe ser al menos {minimo:,.2f}. Valor recibido: {valor_decimal:,.2f}")

    if maximo is not None and valor_decimal > Decimal(str(maximo)):
        raise ValidationError(f"El monto no puede exceder {maximo:,.2f}. Valor recibido: {valor_decimal:,.2f}")


def validar_fecha_venta(fecha):
    """
    Valida que una fecha de venta sea válida.

    Reglas:
    - No puede ser fecha futura (más de 1 hora en el futuro)
    - No puede ser muy antigua (más de 30 días atrás)

    Args:
        fecha: datetime a validar

    Raises:
        ValidationError: Si la fecha es inválida

    Example:
        >>> validar_fecha_venta(timezone.now())  # OK
        >>> validar_fecha_venta(timezone.now() + timedelta(days=2))  # Error
    """
    if not isinstance(fecha, datetime):
        raise ValidationError("La fecha debe ser un objeto datetime")

    ahora = timezone.now()

    # Permitir hasta 1 hora en el futuro (para ajustes de zona horaria)
    if fecha > ahora + timedelta(hours=1):
        raise ValidationError(
            f"La fecha de venta no puede ser futura. " f"Fecha recibida: {fecha}, Fecha actual: {ahora}"
        )

    # No permitir ventas de más de 30 días atrás
    hace_30_dias = ahora - timedelta(days=30)
    if fecha < hace_30_dias:
        raise ValidationError(
            f"La fecha de venta es muy antigua. "
            f"Las ventas no pueden tener más de 30 días de antigüedad. "
            f"Fecha recibida: {fecha}"
        )


def validar_codigo_promocion(codigo):
    """
    Valida el formato de un código de promoción.

    Reglas:
    - Solo letras mayúsculas, números y guiones
    - Entre 3 y 20 caracteres
    - No espacios

    Args:
        codigo: String del código

    Raises:
        ValidationError: Si el formato es inválido

    Example:
        >>> validar_codigo_promocion('VERANO2026')  # OK
        >>> validar_codigo_promocion('DESC-50')  # OK
        >>> validar_codigo_promocion('promo 123')  # Error (minúsculas y espacios)
    """
    if not codigo:
        raise ValidationError("El código de promoción es requerido")

    if not isinstance(codigo, str):
        raise ValidationError("El código debe ser un string")

    # Verificar longitud
    if len(codigo) < 3 or len(codigo) > 20:
        raise ValidationError(f"El código debe tener entre 3 y 20 caracteres. " f"Longitud actual: {len(codigo)}")

    # Verificar formato: solo mayúsculas, números y guiones
    patron = r"^[A-Z0-9\-]+$"
    if not re.match(patron, codigo):
        raise ValidationError(
            f"El código solo puede contener letras mayúsculas, números y guiones. " f"Código recibido: {codigo}"
        )


def validar_porcentaje_descuento(porcentaje):
    """
    Valida un porcentaje de descuento.

    Reglas:
    - Entre 0 y 100
    - Positivo

    Args:
        porcentaje: Decimal del porcentaje

    Raises:
        ValidationError: Si está fuera de rango

    Example:
        >>> validar_porcentaje_descuento(Decimal('15'))  # OK
        >>> validar_porcentaje_descuento(Decimal('150'))  # Error
    """
    porcentaje_decimal = Decimal(str(porcentaje))

    if porcentaje_decimal < 0:
        raise ValidationError(f"El porcentaje no puede ser negativo. Valor: {porcentaje_decimal}")

    if porcentaje_decimal > 100:
        raise ValidationError(f"El porcentaje no puede ser mayor a 100. Valor: {porcentaje_decimal}")


def validar_estado_venta(estado):
    """
    Valida que el estado de venta sea válido.

    Estados permitidos: Activa, Cancelada, Anulada

    Args:
        estado: String del estado

    Raises:
        ValidationError: Si el estado no es válido
    """
    estados_validos = ["Activa", "Cancelada", "Anulada"]

    if estado not in estados_validos:
        raise ValidationError(f"Estado inválido: {estado}. " f'Estados válidos: {", ".join(estados_validos)}')


def validar_estado_pago(estado):
    """
    Valida que el estado de pago sea válido.

    Estados permitidos: Pagada, Pendiente, Parcial

    Args:
        estado: String del estado

    Raises:
        ValidationError: Si el estado no es válido
    """
    estados_validos = ["Pagada", "Pendiente", "Parcial"]

    if estado not in estados_validos:
        raise ValidationError(f"Estado de pago inválido: {estado}. " f'Estados válidos: {", ".join(estados_validos)}')


def validar_tipo_venta(tipo):
    """
    Valida que el tipo de venta sea válido.

    Tipos permitidos: Contado, Crédito

    Args:
        tipo: String del tipo

    Raises:
        ValidationError: Si el tipo no es válido
    """
    tipos_validos = ["Contado", "Crédito"]

    if tipo not in tipos_validos:
        raise ValidationError(f"Tipo de venta inválido: {tipo}. " f'Tipos válidos: {", ".join(tipos_validos)}')


def validar_cantidad_producto(cantidad):
    """
    Valida la cantidad de un producto.

    Reglas:
    - Mayor a cero
    - Máximo 3 decimales
    - Máximo 9999 unidades

    Args:
        cantidad: Decimal de la cantidad

    Raises:
        ValidationError: Si la cantidad es inválida
    """
    cantidad_decimal = Decimal(str(cantidad))

    if cantidad_decimal <= 0:
        raise ValidationError(f"La cantidad debe ser mayor a cero. Valor: {cantidad_decimal}")

    if cantidad_decimal > 9999:
        raise ValidationError(f"La cantidad no puede exceder 9999 unidades. Valor: {cantidad_decimal}")

    # Verificar máximo 3 decimales
    # Convertir a string y verificar decimales
    cantidad_str = str(cantidad_decimal)
    if "." in cantidad_str:
        decimales = len(cantidad_str.split(".")[1])
        if decimales > 3:
            raise ValidationError(f"La cantidad no puede tener más de 3 decimales. " f"Decimales actuales: {decimales}")


def validar_fecha_rango_promocion(fecha_inicio, fecha_fin=None):
    """
    Valida el rango de fechas de una promoción.

    Reglas:
    - fecha_inicio no puede ser pasada (más de 30 días atrás)
    - Si hay fecha_fin, debe ser posterior a fecha_inicio
    - El rango no puede ser mayor a 365 días

    Args:
        fecha_inicio: date de inicio
        fecha_fin: date de fin (opcional)

    Raises:
        ValidationError: Si el rango es inválido
    """
    ahora = timezone.now().date()
    hace_30_dias = ahora - timedelta(days=30)

    # Fecha inicio no muy antigua
    if fecha_inicio < hace_30_dias:
        raise ValidationError(
            f"La fecha de inicio no puede ser más antigua que 30 días. " f"Fecha recibida: {fecha_inicio}"
        )

    if fecha_fin:
        # Fecha fin debe ser posterior a inicio
        if fecha_fin <= fecha_inicio:
            raise ValidationError(
                f"La fecha de fin debe ser posterior a la fecha de inicio. " f"Inicio: {fecha_inicio}, Fin: {fecha_fin}"
            )

        # Rango máximo de 365 días
        dias_diferencia = (fecha_fin - fecha_inicio).days
        if dias_diferencia > 365:
            raise ValidationError(
                f"El rango de la promoción no puede ser mayor a 365 días. " f"Días actuales: {dias_diferencia}"
            )


def validar_credito_disponible(cliente, monto_venta):
    """
    Valida que el cliente tenga crédito disponible suficiente.

    Args:
        cliente: Instancia de Clientes
        monto_venta: Decimal del monto de la venta

    Raises:
        ValidationError: Si no hay crédito suficiente

    Example:
        >>> cliente = Clientes.objects.get(id=123)
        >>> validar_credito_disponible(cliente, Decimal('50000'))
    """
    from apps.clientes.models import Clientes

    if not isinstance(cliente, Clientes):
        raise ValidationError("Se requiere una instancia válida de Cliente")

    monto_decimal = Decimal(str(monto_venta))

    # Refrescar datos del cliente
    cliente.refresh_from_db()

    credito_disponible = cliente.credito_disponible

    if monto_decimal > credito_disponible:
        raise ValidationError(
            f"Crédito insuficiente. "
            f"Disponible: Gs. {credito_disponible:,.0f}, "
            f"Requerido: Gs. {monto_decimal:,.0f}, "
            f"Faltante: Gs. {(monto_decimal - credito_disponible):,.0f}"
        )


def validar_saldo_tarjeta(tarjeta, monto_consumo):
    """
    Valida que la tarjeta tenga saldo suficiente.

    Considera si la tarjeta permite saldo negativo y el límite de crédito.

    Args:
        tarjeta: Instancia de Tarjetas
        monto_consumo: Decimal del monto a consumir

    Raises:
        ValidationError: Si no hay saldo suficiente
    """
    from apps.core.models import Tarjetas

    if not isinstance(tarjeta, Tarjetas):
        raise ValidationError("Se requiere una instancia válida de Tarjeta")

    monto_decimal = Decimal(str(monto_consumo))

    # Refrescar tarjeta
    tarjeta.refresh_from_db()

    saldo_actual = tarjeta.saldo_actual
    saldo_despues = saldo_actual - monto_decimal

    # Si permite saldo negativo, verificar límite de crédito
    if tarjeta.permite_saldo_negativo:
        saldo_minimo_permitido = -tarjeta.limite_credito

        if saldo_despues < saldo_minimo_permitido:
            raise ValidationError(
                f"Límite de crédito excedido. "
                f"Saldo actual: Gs. {saldo_actual:,.0f}, "
                f"Consumo: Gs. {monto_decimal:,.0f}, "
                f"Límite crédito: Gs. {tarjeta.limite_credito:,.0f}, "
                f"Saldo mínimo permitido: Gs. {saldo_minimo_permitido:,.0f}"
            )
    else:
        # No permite saldo negativo
        if saldo_despues < 0:
            raise ValidationError(
                f"Saldo insuficiente. "
                f"Saldo actual: Gs. {saldo_actual:,.0f}, "
                f"Consumo: Gs. {monto_decimal:,.0f}, "
                f"Faltante: Gs. {abs(saldo_despues):,.0f}"
            )


def validar_dias_semana(dias):
    """
    Valida un array de días de semana para promociones.

    Args:
        dias: Lista de números 0-6 (0=Lunes, 6=Domingo)

    Raises:
        ValidationError: Si los días son inválidos

    Example:
        >>> validar_dias_semana([0, 1, 2, 3, 4])  # Lunes a Viernes, OK
        >>> validar_dias_semana([7, 8])  # Error
    """
    if not isinstance(dias, list):
        raise ValidationError("Los días deben ser una lista")

    if not dias:
        raise ValidationError("Debe especificar al menos un día")

    for dia in dias:
        if not isinstance(dia, int):
            raise ValidationError(f"Cada día debe ser un número entero. Recibido: {dia} ({type(dia).__name__})")

        if dia < 0 or dia > 6:
            raise ValidationError(f"Los días deben estar entre 0 (Lunes) y 6 (Domingo). " f"Valor inválido: {dia}")


def validar_numero_factura(numero):
    """
    Valida un número de factura legal.

    Reglas Paraguay:
    - Máximo 15 dígitos
    - Solo números

    Args:
        numero: Int o String del número

    Raises:
        ValidationError: Si el formato es inválido
    """
    if numero is None or numero == "":
        return  # Puede ser opcional

    numero_str = str(numero)

    # Solo números
    if not numero_str.isdigit():
        raise ValidationError(f"El número de factura solo puede contener dígitos. " f"Valor recibido: {numero_str}")

    # Máximo 15 dígitos
    if len(numero_str) > 15:
        raise ValidationError(
            f"El número de factura no puede tener más de 15 dígitos. " f"Longitud actual: {len(numero_str)}"
        )


def validar_motivo_credito(motivo, tipo_venta):
    """
    Valida que una venta a crédito tenga motivo.

    Args:
        motivo: String del motivo
        tipo_venta: 'Contado' o 'Crédito'

    Raises:
        ValidationError: Si falta el motivo en venta a crédito
    """
    if tipo_venta == "Crédito":
        if not motivo or motivo.strip() == "":
            raise ValidationError("Las ventas a crédito requieren un motivo")

        if len(motivo) < 10:
            raise ValidationError(f"El motivo debe tener al menos 10 caracteres. " f"Longitud actual: {len(motivo)}")
