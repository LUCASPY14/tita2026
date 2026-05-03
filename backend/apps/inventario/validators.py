"""
Validadores del módulo Inventario
Aseguran integridad de datos en stock, movimientos, ajustes y ML forecasting
"""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.utils import timezone

# ============================
# Validadores de Stock
# ============================


def validar_cantidad_positiva(cantidad):
    """
    Valida que la cantidad sea mayor a cero.

    Args:
        cantidad (Decimal|int|float): Cantidad a validar

    Raises:
        ValidationError: Si cantidad <= 0

    Uso:
        validar_cantidad_positiva(cantidad_solicitada)
    """
    if cantidad is None:
        raise ValidationError("La cantidad no puede ser nula")

    try:
        cantidad_decimal = Decimal(str(cantidad))
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("La cantidad debe ser un número válido")

    if cantidad_decimal <= 0:
        raise ValidationError(f"La cantidad debe ser mayor a cero. Valor recibido: {cantidad}")


def validar_cantidad_no_negativa(cantidad):
    """
    Valida que la cantidad no sea negativa (permite 0).

    Args:
        cantidad (Decimal|int|float): Cantidad a validar

    Raises:
        ValidationError: Si cantidad < 0

    Uso:
        # Útil para stock que puede estar en 0
        validar_cantidad_no_negativa(stock_actual)
    """
    if cantidad is None:
        return  # Permitir nulos en algunos contextos

    try:
        cantidad_decimal = Decimal(str(cantidad))
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("La cantidad debe ser un número válido")

    if cantidad_decimal < 0:
        raise ValidationError(f"La cantidad no puede ser negativa. Valor recibido: {cantidad}")


def validar_stock_minimo_maximo(cantidad_minima, cantidad_maxima):
    """
    Valida que el stock mínimo sea menor al máximo.

    Args:
        cantidad_minima (Decimal): Stock mínimo
        cantidad_maxima (Decimal): Stock máximo

    Raises:
        ValidationError: Si mínimo >= máximo

    Uso:
        validar_stock_minimo_maximo(producto.stock_minimo, producto.stock_maximo)
    """
    if cantidad_minima is None or cantidad_maxima is None:
        return  # Validación opcional

    try:
        min_decimal = Decimal(str(cantidad_minima))
        max_decimal = Decimal(str(cantidad_maxima))
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("Stock mínimo y máximo deben ser números válidos")

    if min_decimal < 0:
        raise ValidationError(f"El stock mínimo no puede ser negativo: {cantidad_minima}")

    if max_decimal <= 0:
        raise ValidationError(f"El stock máximo debe ser mayor a cero: {cantidad_maxima}")

    if min_decimal >= max_decimal:
        raise ValidationError(f"El stock mínimo ({cantidad_minima}) debe ser menor que el máximo ({cantidad_maxima})")


def validar_punto_reorden(punto_reorden, stock_minimo, stock_maximo):
    """
    Valida que el punto de reorden esté entre stock mínimo y máximo.

    Args:
        punto_reorden (Decimal): Punto de reorden
        stock_minimo (Decimal): Stock mínimo permitido
        stock_maximo (Decimal): Stock máximo permitido

    Raises:
        ValidationError: Si punto de reorden está fuera de rango

    Regla de negocio:
        stock_minimo <= punto_reorden <= stock_maximo
    """
    if punto_reorden is None:
        return

    try:
        reorden = Decimal(str(punto_reorden))
        minimo = Decimal(str(stock_minimo))
        maximo = Decimal(str(stock_maximo))
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("Los valores de stock deben ser números válidos")

    if reorden <= 0:
        raise ValidationError(f"El punto de reorden debe ser positivo: {punto_reorden}")

    if reorden < minimo:
        raise ValidationError(
            f"El punto de reorden ({punto_reorden}) no puede ser menor que el stock mínimo ({stock_minimo})"
        )

    if reorden > maximo:
        raise ValidationError(
            f"El punto de reorden ({punto_reorden}) no puede ser mayor que el stock máximo ({stock_maximo})"
        )


def validar_stock_disponible(id_producto, cantidad_solicitada):
    """
    Valida que haya stock suficiente para una operación.

    Args:
        id_producto (int|Productos): ID del producto o instancia
        cantidad_solicitada (Decimal): Cantidad que se desea consumir

    Raises:
        ValidationError: Si no hay stock suficiente

    Uso:
        # En serializer o view
        validar_stock_disponible(producto.id_producto, cantidad)
    """
    from apps.inventario.models import StockUnico
    from apps.productos.models import Productos

    if cantidad_solicitada is None or cantidad_solicitada <= 0:
        raise ValidationError("La cantidad solicitada debe ser mayor a cero")

    try:
        # Obtener ID si se pasa instancia
        if hasattr(id_producto, "id_producto"):
            producto_id = id_producto.id_producto
        else:
            producto_id = int(id_producto)

        producto = Productos.objects.get(id_producto=producto_id)

        # Productos que permiten stock negativo pasan validación
        if producto.permite_stock_negativo:
            return

        stock = StockUnico.objects.get(id_producto=producto_id)

        if stock.cantidad < Decimal(str(cantidad_solicitada)):
            raise ValidationError(
                f"Stock insuficiente para {producto.descripcion}. "
                f"Disponible: {stock.cantidad}, Solicitado: {cantidad_solicitada}"
            )

    except Productos.DoesNotExist:
        raise ValidationError(f"Producto {id_producto} no existe")
    except StockUnico.DoesNotExist:
        raise ValidationError(f"No hay registro de stock para el producto {id_producto}")


# ============================
# Validadores de Movimientos
# ============================


def validar_tipo_movimiento(tipo_movimiento):
    """
    Valida que el tipo de movimiento sea válido.

    Args:
        tipo_movimiento (str): 'Ingreso' o 'Egreso'

    Raises:
        ValidationError: Si tipo no es válido
    """
    TIPOS_VALIDOS = ["Ingreso", "Egreso"]

    if not tipo_movimiento:
        raise ValidationError("El tipo de movimiento es requerido")

    if tipo_movimiento not in TIPOS_VALIDOS:
        raise ValidationError(
            f"Tipo de movimiento inválido: '{tipo_movimiento}'. " f"Valores permitidos: {', '.join(TIPOS_VALIDOS)}"
        )


def validar_motivo_movimiento(motivo):
    """
    Valida que el motivo del movimiento sea descriptivo.

    Args:
        motivo (str): Descripción del motivo

    Raises:
        ValidationError: Si motivo es muy corto o vacío

    Reglas:
        - Mínimo 10 caracteres
        - No puede estar vacío o solo espacios
    """
    if not motivo or not motivo.strip():
        raise ValidationError("El motivo del movimiento es requerido")

    if len(motivo.strip()) < 10:
        raise ValidationError(f"El motivo debe tener al menos 10 caracteres. Actual: {len(motivo.strip())}")


def validar_referencia_movimiento(tipo_referencia, id_referencia):
    """
    Valida que la referencia del movimiento sea válida.

    Args:
        tipo_referencia (str): 'Compra', 'Venta', 'Ajuste', etc.
        id_referencia (int): ID del documento que origina el movimiento

    Raises:
        ValidationError: Si la referencia no existe
    """
    TIPOS_REFERENCIA = [
        "Compra",
        "Venta",
        "Ajuste",
        "Devolucion",
        "Traslado",
        "Produccion",
        "Merma",
        "Inicial",
    ]

    if tipo_referencia not in TIPOS_REFERENCIA:
        raise ValidationError(
            f"Tipo de referencia inválido: '{tipo_referencia}'. " f"Valores permitidos: {', '.join(TIPOS_REFERENCIA)}"
        )

    if id_referencia is not None and id_referencia <= 0:
        raise ValidationError(f"El ID de referencia debe ser positivo: {id_referencia}")


# ============================
# Validadores de Ajustes
# ============================


def validar_tipo_ajuste(tipo_ajuste):
    """
    Valida que el tipo de ajuste sea válido.

    Args:
        tipo_ajuste (str): Tipo de ajuste de inventario

    Raises:
        ValidationError: Si tipo no es válido
    """
    TIPOS_VALIDOS = ["Merma", "Sobrante", "Correccion", "Vencimiento", "Deterioro"]

    if not tipo_ajuste:
        raise ValidationError("El tipo de ajuste es requerido")

    if tipo_ajuste not in TIPOS_VALIDOS:
        raise ValidationError(
            f"Tipo de ajuste inválido: '{tipo_ajuste}'. " f"Valores permitidos: {', '.join(TIPOS_VALIDOS)}"
        )


def validar_estado_ajuste(estado):
    """
    Valida que el estado del ajuste sea válido.

    Args:
        estado (str): Estado del ajuste

    Raises:
        ValidationError: Si estado no es válido
    """
    ESTADOS_VALIDOS = ["Pendiente", "Aprobado", "Rechazado", "Aplicado"]

    if not estado:
        raise ValidationError("El estado del ajuste es requerido")

    if estado not in ESTADOS_VALIDOS:
        raise ValidationError(f"Estado inválido: '{estado}'. " f"Valores permitidos: {', '.join(ESTADOS_VALIDOS)}")


def validar_cantidad_ajuste(cantidad_ajuste, tipo_ajuste):
    """
    Valida la cantidad de ajuste según el tipo.

    Args:
        cantidad_ajuste (Decimal): Cantidad del ajuste
        tipo_ajuste (str): Tipo de ajuste

    Raises:
        ValidationError: Si cantidad no es coherente con el tipo

    Reglas:
        - Merma/Vencimiento/Deterioro: cantidad negativa
        - Sobrante/Correccion: cantidad puede ser cualquiera
    """
    if cantidad_ajuste is None:
        raise ValidationError("La cantidad de ajuste es requerida")

    try:
        cantidad = Decimal(str(cantidad_ajuste))
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("La cantidad debe ser un número válido")

    if cantidad == 0:
        raise ValidationError("La cantidad de ajuste no puede ser cero")

    # Mermas, vencimientos y deterioros deben ser negativos
    if tipo_ajuste in ["Merma", "Vencimiento", "Deterioro"]:
        if cantidad > 0:
            raise ValidationError(
                f"Los ajustes de tipo '{tipo_ajuste}' deben tener cantidad negativa. " f"Valor recibido: {cantidad}"
            )

    # Sobrantes deben ser positivos
    if tipo_ajuste == "Sobrante":
        if cantidad < 0:
            raise ValidationError(
                f"Los ajustes de tipo 'Sobrante' deben tener cantidad positiva. " f"Valor recibido: {cantidad}"
            )


def validar_merma_aceptable(cantidad_merma, cantidad_total, porcentaje_max=5):
    """
    Valida que la merma no supere el porcentaje aceptable.

    Args:
        cantidad_merma (Decimal): Cantidad de merma
        cantidad_total (Decimal): Cantidad total del producto
        porcentaje_max (int): Porcentaje máximo aceptable (default 5%)

    Raises:
        ValidationError: Si merma supera el porcentaje máximo

    Uso:
        # En validación de ajustes
        validar_merma_aceptable(cantidad_ajuste, stock_antes_ajuste)
    """
    if cantidad_total <= 0:
        raise ValidationError("La cantidad total debe ser mayor a cero")

    try:
        merma = abs(Decimal(str(cantidad_merma)))
        total = Decimal(str(cantidad_total))
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("Las cantidades deben ser números válidos")

    porcentaje_merma = (merma / total) * 100

    if porcentaje_merma > porcentaje_max:
        raise ValidationError(
            f"La merma ({porcentaje_merma:.2f}%) supera el máximo permitido ({porcentaje_max}%). "
            f"Merma: {merma}, Total: {total}. Requiere autorización especial."
        )


# ============================
# Validadores de Lotes
# ============================


def validar_fecha_vencimiento(fecha_vencimiento):
    """
    Valida que la fecha de vencimiento sea futura.

    Args:
        fecha_vencimiento (date|datetime): Fecha de vencimiento

    Raises:
        ValidationError: Si fecha está en el pasado
    """
    if not fecha_vencimiento:
        return  # Algunos productos no tienen vencimiento

    hoy = timezone.now().date()

    # Convertir datetime a date si es necesario
    if isinstance(fecha_vencimiento, datetime):
        fecha_vencimiento = fecha_vencimiento.date()

    if fecha_vencimiento < hoy:
        raise ValidationError(f"La fecha de vencimiento no puede estar en el pasado: {fecha_vencimiento}")


def validar_numero_lote(numero_lote):
    """
    Valida el formato del número de lote.

    Args:
        numero_lote (str): Número de lote

    Raises:
        ValidationError: Si formato no es válido

    Formato esperado:
        - Mínimo 3 caracteres
        - Solo alfanumérico y guiones
    """
    if not numero_lote or not numero_lote.strip():
        raise ValidationError("El número de lote es requerido")

    lote = numero_lote.strip()

    if len(lote) < 3:
        raise ValidationError(f"El número de lote debe tener al menos 3 caracteres: '{lote}'")

    if not re.match(r"^[A-Za-z0-9\-]+$", lote):
        raise ValidationError(f"El número de lote solo puede contener letras, números y guiones: '{lote}'")


def validar_cantidad_lote(cantidad_lote, cantidad_movimiento):
    """
    Valida que la cantidad del lote coincida con el movimiento.

    Args:
        cantidad_lote (Decimal): Cantidad en el lote
        cantidad_movimiento (Decimal): Cantidad del movimiento

    Raises:
        ValidationError: Si cantidades no coinciden
    """
    try:
        lote = Decimal(str(cantidad_lote))
        movimiento = Decimal(str(cantidad_movimiento))
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("Las cantidades deben ser números válidos")

    if lote <= 0:
        raise ValidationError(f"La cantidad del lote debe ser positiva: {cantidad_lote}")

    if lote != movimiento:
        raise ValidationError(
            f"La cantidad del lote ({cantidad_lote}) no coincide con el movimiento ({cantidad_movimiento})"
        )


# ============================
# Validadores de ML Forecasting
# ============================


def validar_dias_historico(dias):
    """
    Valida el rango de días para análisis histórico.

    Args:
        dias (int): Número de días para análisis

    Raises:
        ValidationError: Si días está fuera de rango válido

    Rango válido: 7-365 días
    """
    if dias is None:
        raise ValidationError("El número de días es requerido")

    try:
        dias_int = int(dias)
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("Los días deben ser un número entero")

    if dias_int < 7:
        raise ValidationError(f"El análisis requiere mínimo 7 días de histórico. Valor recibido: {dias}")

    if dias_int > 365:
        raise ValidationError(f"El análisis no puede superar 365 días. Valor recibido: {dias}")


def validar_umbral_confianza(umbral):
    """
    Valida el umbral de confianza para predicciones.

    Args:
        umbral (float): Umbral de confianza (0-1)

    Raises:
        ValidationError: Si umbral está fuera de rango

    Rango válido: 0.50 - 0.99
    """
    if umbral is None:
        raise ValidationError("El umbral de confianza es requerido")

    try:
        umbral_float = float(umbral)
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("El umbral debe ser un número decimal")

    if umbral_float < 0.50:
        raise ValidationError(f"El umbral de confianza no puede ser menor a 0.50: {umbral}")

    if umbral_float >= 1.0:
        raise ValidationError(f"El umbral de confianza debe ser menor a 1.0: {umbral}")


def validar_lead_time(lead_time_dias):
    """
    Valida el tiempo de entrega (lead time).

    Args:
        lead_time_dias (int): Días de lead time

    Raises:
        ValidationError: Si lead time está fuera de rango

    Rango válido: 1-90 días
    """
    if lead_time_dias is None:
        raise ValidationError("El lead time es requerido")

    try:
        lead_time = int(lead_time_dias)
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("El lead time debe ser un número entero")

    if lead_time < 1:
        raise ValidationError(f"El lead time debe ser al menos 1 día: {lead_time_dias}")

    if lead_time > 90:
        raise ValidationError(f"El lead time no puede superar 90 días: {lead_time_dias}")


def validar_dias_cobertura(dias_cobertura):
    """
    Valida los días de cobertura deseados.

    Args:
        dias_cobertura (int): Días de cobertura

    Raises:
        ValidationError: Si días de cobertura está fuera de rango

    Rango válido: 7-60 días
    """
    if dias_cobertura is None:
        raise ValidationError("Los días de cobertura son requeridos")

    try:
        dias = int(dias_cobertura)
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("Los días de cobertura deben ser un número entero")

    if dias < 7:
        raise ValidationError(f"La cobertura mínima es 7 días: {dias_cobertura}")

    if dias > 60:
        raise ValidationError(f"La cobertura máxima es 60 días: {dias_cobertura}")


# ============================
# Validadores de Costos
# ============================


def validar_costo_unitario(costo):
    """
    Valida que el costo unitario sea positivo.

    Args:
        costo (Decimal): Costo unitario

    Raises:
        ValidationError: Si costo no es válido
    """
    if costo is None:
        raise ValidationError("El costo unitario es requerido")

    try:
        costo_decimal = Decimal(str(costo))
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("El costo debe ser un número válido")

    if costo_decimal <= 0:
        raise ValidationError(f"El costo unitario debe ser mayor a cero: {costo}")


def validar_variacion_costo(costo_nuevo, costo_anterior, porcentaje_max_variacion=30):
    """
    Valida que la variación de costo no sea excesiva.

    Args:
        costo_nuevo (Decimal): Nuevo costo
        costo_anterior (Decimal): Costo anterior
        porcentaje_max_variacion (int): Variación máxima permitida (default 30%)

    Raises:
        ValidationError: Si variación supera el máximo

    Alerta si hay variaciones > 30% que pueden indicar error de entrada
    """
    if costo_anterior is None or costo_anterior == 0:
        return  # No hay costo anterior para comparar

    try:
        nuevo = Decimal(str(costo_nuevo))
        anterior = Decimal(str(costo_anterior))
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("Los costos deben ser números válidos")

    variacion_absoluta = abs(nuevo - anterior)
    variacion_porcentual = (variacion_absoluta / anterior) * 100

    if variacion_porcentual > porcentaje_max_variacion:
        raise ValidationError(
            f"La variación del costo ({variacion_porcentual:.2f}%) supera el máximo permitido ({porcentaje_max_variacion}%). "
            f"Costo anterior: {anterior}, Costo nuevo: {nuevo}. "
            f"Verificar si es correcto o requiere autorización especial."
        )


# ============================
# Validadores de Alertas
# ============================


def validar_nivel_alerta(nivel):
    """
    Valida el nivel de alerta.

    Args:
        nivel (str): Nivel de alerta

    Raises:
        ValidationError: Si nivel no es válido
    """
    NIVELES_VALIDOS = ["Bajo", "Medio", "Alto", "Critico"]

    if not nivel:
        raise ValidationError("El nivel de alerta es requerido")

    if nivel not in NIVELES_VALIDOS:
        raise ValidationError(
            f"Nivel de alerta inválido: '{nivel}'. " f"Valores permitidos: {', '.join(NIVELES_VALIDOS)}"
        )


def validar_umbral_alerta(umbral_cantidad, stock_minimo, stock_maximo):
    """
    Valida que el umbral de alerta esté en rango válido.

    Args:
        umbral_cantidad (Decimal): Cantidad que activa la alerta
        stock_minimo (Decimal): Stock mínimo del producto
        stock_maximo (Decimal): Stock máximo del producto

    Raises:
        ValidationError: Si umbral está fuera de rango
    """
    try:
        umbral = Decimal(str(umbral_cantidad))
        Decimal(str(stock_minimo))
        maximo = Decimal(str(stock_maximo))
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("Los valores deben ser números válidos")

    if umbral < 0:
        raise ValidationError(f"El umbral de alerta no puede ser negativo: {umbral_cantidad}")

    # El umbral normalmente debería estar entre mínimo y punto de reorden
    if umbral > maximo:
        raise ValidationError(
            f"El umbral de alerta ({umbral_cantidad}) no puede ser mayor que el stock máximo ({stock_maximo})"
        )
