"""
Validadores del módulo Compras
Aseguran integridad de datos en compras, proveedores, pagos y notas de crédito
"""

from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
from django.utils import timezone
import re

# ============================
# Validadores de Proveedores
# ============================


def validar_ruc(ruc):
    """
    Valida formato y dígito verificador de RUC paraguayo.

    Reglas:
    - Debe tener formato: XXXXX-Y o XXXXXXX-Y
    - Parte numérica debe ser válida
    - Dígito verificador debe ser correcto

    Args:
        ruc (str): RUC a validar con formato XXXXX-Y

    Raises:
        ValidationError: Si el RUC no es válido

    Uso:
        validar_ruc('80012345-6')
    """
    if not ruc:
        raise ValidationError("El RUC no puede estar vacío")

    # Limpiar espacios
    ruc = str(ruc).strip()

    # Validar formato básico (5 a 8 dígitos antes del guión)
    if not re.match(r"^\d{5,8}-\d$", ruc):
        raise ValidationError(
            "El RUC debe tener formato XXXXX-Y o XXXXXXXX-Y (ejemplo: 80012345-6)"
        )

    # Separar número base y dígito verificador
    partes = ruc.split("-")
    numero_base = partes[0]
    digito_verificador = int(partes[1])

    # Calcular dígito verificador (módulo 11)
    total = 0
    multiplicador = 2
    for digito in reversed(numero_base):
        total += int(digito) * multiplicador
        multiplicador += 1
        if multiplicador > 11:  # pragma: no cover
            multiplicador = 2

    resto = total % 11
    digito_calculado = 0 if resto <= 1 else 11 - resto

    if digito_calculado != digito_verificador:
        raise ValidationError(
            f"El dígito verificador del RUC es incorrecto. Esperado: {digito_calculado}"
        )


def validar_razon_social(razon_social):
    """
    Valida que la razón social tenga formato válido.

    Reglas:
    - Mínimo 3 caracteres
    - Máximo 255 caracteres
    - Solo letras, números, espacios y símbolos comunes

    Args:
        razon_social (str): Razón social a validar

    Raises:
        ValidationError: Si la razón social no es válida
    """
    if not razon_social:
        raise ValidationError("La razón social no puede estar vacía")

    razon_social = str(razon_social).strip()

    if len(razon_social) < 3:
        raise ValidationError("La razón social debe tener al menos 3 caracteres")

    if len(razon_social) > 255:
        raise ValidationError("La razón social no puede exceder 255 caracteres")

    # Permitir letras, números, espacios y símbolos comunes de empresas
    if not re.match(r'^[a-záéíóúñA-ZÁÉÍÓÚÑ0-9\s\.,\-&()\'"]+$', razon_social):
        raise ValidationError("La razón social contiene caracteres no permitidos")


def validar_email_proveedor(email):
    """
    Valida formato de email para proveedores.

    Args:
        email (str): Email a validar

    Raises:
        ValidationError: Si el email no es válido
    """
    if not email:
        return  # Email es opcional

    email = str(email).strip()

    # Regex básico para email
    regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(regex, email):
        raise ValidationError(f"El email '{email}' no tiene un formato válido")

    if len(email) > 254:
        raise ValidationError("El email no puede exceder 254 caracteres")


def validar_telefono_proveedor(telefono):
    """
    Valida formato de teléfono paraguayo.

    Formatos aceptados:
    - 0981123456
    - +595981123456
    - 021-123456

    Args:
        telefono (str): Teléfono a validar

    Raises:
        ValidationError: Si el teléfono no es válido
    """
    if not telefono:
        return  # Teléfono es opcional

    telefono = str(telefono).strip()

    # Limpiar caracteres comunes
    telefono_limpio = re.sub(r"[\s\-()]", "", telefono)

    # Validar formato paraguayo
    # Celular: 09XX-XXXXXX o +5959XX-XXXXXX
    # Fijo: 0XX-XXXXXX
    if not re.match(r"^(\+595|0)?[0-9]{6,10}$", telefono_limpio):
        raise ValidationError(
            "El teléfono debe tener un formato válido (ej: 0981123456 o 021-123456)"
        )


def validar_limite_credito_proveedor(limite_credito, compras_pendientes=None):
    """
    Valida que el límite de crédito del proveedor sea coherente.

    Args:
        limite_credito (Decimal): Límite de crédito
        compras_pendientes (Decimal): Monto de compras pendientes de pago

    Raises:
        ValidationError: Si el límite no es válido
    """
    if limite_credito is None:
        return  # Límite opcional

    try:
        limite = Decimal(str(limite_credito))
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("El límite de crédito debe ser un número válido")

    if limite < 0:
        raise ValidationError("El límite de crédito no puede ser negativo")

    # Advertencia si compras pendientes superan el límite
    if compras_pendientes:
        try:
            pendientes = Decimal(str(compras_pendientes))
            if pendientes > limite:
                raise ValidationError(
                    f"Las compras pendientes (₲{pendientes:,.0f}) superan el límite de crédito (₲{limite:,.0f})"
                )
        except (ValueError, TypeError, InvalidOperation):  # pragma: no cover
            pass


# ============================
# Validadores de Compras
# ============================


def validar_monto_compra(monto):
    """
    Valida que el monto de compra sea válido.

    Args:
        monto (Decimal): Monto a validar

    Raises:
        ValidationError: Si el monto no es válido
    """
    if monto is None:
        raise ValidationError("El monto de la compra no puede ser nulo")

    try:
        monto_decimal = Decimal(str(monto))
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("El monto debe ser un número válido")

    if monto_decimal <= 0:
        raise ValidationError(
            f"El monto de la compra debe ser positivo. Valor recibido: ₲{monto_decimal:,.0f}"
        )

    # Límite razonable de 100 millones de guaraníes
    if monto_decimal > Decimal("100000000.00"):
        raise ValidationError(
            f"El monto de la compra (₲{monto_decimal:,.0f}) parece excesivamente alto. Verifique."
        )


def validar_estado_pago(estado):
    """
    Valida que el estado de pago sea uno de los permitidos.

    Estados válidos:
    - Pendiente: Compra registrada, pendiente de confirmación
    - Confirmado: Compra confirmada, pendiente de pago
    - Pagado: Compra totalmente pagada
    - Cancelado: Compra cancelada

    Args:
        estado (str): Estado a validar

    Raises:
        ValidationError: Si el estado no es válido
    """
    if not estado:
        raise ValidationError("El estado de pago no puede estar vacío")

    estados_validos = ["Pendiente", "Confirmado", "Pagado", "Parcial", "Cancelado"]

    if estado not in estados_validos:
        raise ValidationError(
            f"Estado '{estado}' no válido. Debe ser uno de: {', '.join(estados_validos)}"
        )


def validar_transicion_estado_compra(estado_actual, estado_nuevo):
    """
    Valida que la transición entre estados de compra sea permitida.

    Flujo permitido:
    - Pendiente → Confirmado, Cancelado
    - Confirmado → Parcial, Pagado, Cancelado
    - Parcial → Pagado, Cancelado
    - Pagado → (ninguna transición permitida)
    - Cancelado → (ninguna transición permitida)

    Args:
        estado_actual (str): Estado actual
        estado_nuevo (str): Estado nuevo deseado

    Raises:
        ValidationError: Si la transición no está permitida
    """
    transiciones = {
        "Pendiente": ["Confirmado", "Cancelado"],
        "Confirmado": ["Parcial", "Pagado", "Cancelado"],
        "Parcial": ["Pagado", "Cancelado"],
        "Pagado": [],
        "Cancelado": [],
    }

    if estado_actual not in transiciones:
        raise ValidationError(f"Estado actual '{estado_actual}' no reconocido")

    if estado_nuevo not in transiciones.get(estado_actual, []):
        raise ValidationError(
            f"No se puede cambiar de '{estado_actual}' a '{estado_nuevo}'. "
            f"Transiciones permitidas: {', '.join(transiciones[estado_actual]) if transiciones[estado_actual] else 'ninguna'}"
        )


def validar_fecha_compra(fecha_compra):
    """
    Valida que la fecha de compra sea coherente.

    Reglas:
    - No puede ser futura (más de 1 día en el futuro)
    - No puede ser muy antigua (> 1 año atrás)

    Args:
        fecha_compra (datetime): Fecha a validar

    Raises:
        ValidationError: Si la fecha no es válida
    """
    if not fecha_compra:
        raise ValidationError("La fecha de compra no puede estar vacía")

    if isinstance(fecha_compra, str):
        try:
            fecha_compra = datetime.fromisoformat(fecha_compra.replace("Z", "+00:00"))
        except ValueError:
            raise ValidationError("Formato de fecha inválido")

    ahora = timezone.now()

    # No puede ser más de 1 día en el futuro
    if fecha_compra > ahora + timedelta(days=1):
        raise ValidationError(
            f"La fecha de compra no puede ser futura ({fecha_compra.strftime('%d/%m/%Y')})"
        )

    # No puede ser más de 1 año atrás
    hace_un_anio = ahora - timedelta(days=365)
    if fecha_compra < hace_un_anio:
        raise ValidationError(
            f"La fecha de compra ({fecha_compra.strftime('%d/%m/%Y')}) es demasiado antigua (> 1 año)"
        )


def validar_numero_factura(numero_factura):
    """
    Valida formato de número de factura.

    Formatos aceptados:
    - 001-001-0001234
    - 0010010001234
    - Texto libre hasta 50 caracteres

    Args:
        numero_factura (str): Número de factura

    Raises:
        ValidationError: Si el formato no es válido
    """
    if not numero_factura:
        return  # Número de factura es opcional

    numero_factura = str(numero_factura).strip()

    if len(numero_factura) > 50:
        raise ValidationError("El número de factura no puede exceder 50 caracteres")

    # Formato paraguayo típico: 001-001-0001234
    formato_paraguayo = r"^\d{3}-\d{3}-\d{7}$"
    formato_simple = r"^\d{13}$"

    if not (
        re.match(formato_paraguayo, numero_factura)
        or re.match(formato_simple, numero_factura)
        or len(numero_factura) >= 5
    ):
        raise ValidationError(
            "El número de factura debe tener un formato válido (ej: 001-001-0001234)"
        )


def validar_saldo_compra(saldo_pendiente, monto_total):
    """
    Valida que el saldo pendiente sea coherente con el monto total.

    Args:
        saldo_pendiente (Decimal): Saldo pendiente de pago
        monto_total (Decimal): Monto total de la compra

    Raises:
        ValidationError: Si el saldo no es coherente
    """
    if saldo_pendiente is None or monto_total is None:
        return

    try:
        saldo = Decimal(str(saldo_pendiente))
        total = Decimal(str(monto_total))
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("Los montos deben ser números válidos")

    if saldo < 0:
        raise ValidationError(f"El saldo pendiente no puede ser negativo. Valor: ₲{saldo:,.0f}")

    if saldo > total:
        raise ValidationError(
            f"El saldo pendiente (₲{saldo:,.0f}) no puede ser mayor al total (₲{total:,.0f})"
        )


# ============================
# Validadores de Detalles de Compra
# ============================


def validar_cantidad_compra(cantidad):
    """
    Valida que la cantidad de compra sea válida.

    Args:
        cantidad (Decimal): Cantidad a validar

    Raises:
        ValidationError: Si la cantidad no es válida
    """
    if cantidad is None:
        raise ValidationError("La cantidad no puede ser nula")

    try:
        cantidad_decimal = Decimal(str(cantidad))
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("La cantidad debe ser un número válido")

    if cantidad_decimal <= 0:
        raise ValidationError(f"La cantidad debe ser positiva. Valor recibido: {cantidad_decimal}")

    # Límite razonable de 100,000 unidades
    if cantidad_decimal > Decimal("100000.000"):
        raise ValidationError(
            f"La cantidad ({cantidad_decimal}) parece excesivamente alta. Verifique."
        )


def validar_costo_unitario(costo_unitario):
    """
    Valida que el costo unitario sea válido.

    Args:
        costo_unitario (Decimal): Costo a validar

    Raises:
        ValidationError: Si el costo no es válido
    """
    if costo_unitario is None:
        raise ValidationError("El costo unitario no puede ser nulo")

    try:
        costo = Decimal(str(costo_unitario))
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("El costo unitario debe ser un número válido")

    if costo <= 0:
        raise ValidationError(f"El costo unitario debe ser positivo. Valor recibido: ₲{costo:,.0f}")

    # Límite razonable de 10 millones de guaraníes
    if costo > Decimal("10000000.00"):
        raise ValidationError(
            f"El costo unitario (₲{costo:,.0f}) parece excesivamente alto. Verifique."
        )


def validar_subtotal_coherente(cantidad, costo_unitario, subtotal):
    """
    Valida que el subtotal sea coherente con cantidad * costo_unitario.

    Tolera diferencias de redondeo de ±0.02

    Args:
        cantidad (Decimal): Cantidad
        costo_unitario (Decimal): Costo unitario
        subtotal (Decimal): Subtotal a validar

    Raises:
        ValidationError: Si el subtotal no es coherente
    """
    try:
        cant = Decimal(str(cantidad))
        costo = Decimal(str(costo_unitario))
        sub = Decimal(str(subtotal))
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("Los valores deben ser números válidos")

    subtotal_calculado = (cant * costo).quantize(Decimal("0.01"))
    diferencia = abs(sub - subtotal_calculado)

    # Tolerancia de ±0.02 por redondeo
    if diferencia > Decimal("0.02"):
        raise ValidationError(
            f"El subtotal (₲{sub:,.2f}) no coincide con cantidad × costo (₲{subtotal_calculado:,.2f}). "
            f"Diferencia: ₲{diferencia:.2f}"
        )


def validar_producto_duplicado_compra(detalles_compra, id_producto):
    """
    Valida que un producto no esté duplicado en los detalles de compra.

    Args:
        detalles_compra (list): Lista de detalles de compra existentes
        id_producto (int): ID del producto a validar

    Raises:
        ValidationError: Si el producto está duplicado
    """
    productos_ids = [d.id_producto_id for d in detalles_compra if hasattr(d, "id_producto_id")]

    if id_producto in productos_ids:
        raise ValidationError(
            f"El producto ID {id_producto} ya está en esta compra. No se permiten duplicados."
        )


# ============================
# Validadores de Pagos
# ============================


def validar_monto_pago(monto_pago):
    """
    Valida que el monto de pago sea válido.

    Args:
        monto_pago (Decimal): Monto a validar

    Raises:
        ValidationError: Si el monto no es válido
    """
    if monto_pago is None:
        raise ValidationError("El monto de pago no puede ser nulo")

    try:
        monto = Decimal(str(monto_pago))
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("El monto de pago debe ser un número válido")

    if monto <= 0:
        raise ValidationError(f"El monto de pago debe ser positivo. Valor: ₲{monto:,.0f}")


def validar_aplicacion_pago(monto_aplicado, saldo_compra):
    """
    Valida que el monto a aplicar no exceda el saldo de la compra.

    Args:
        monto_aplicado (Decimal): Monto a aplicar al pago
        saldo_compra (Decimal): Saldo pendiente de la compra

    Raises:
        ValidationError: Si el monto aplicado excede el saldo
    """
    try:
        aplicado = Decimal(str(monto_aplicado))
        saldo = Decimal(str(saldo_compra))
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("Los montos deben ser números válidos")

    if aplicado <= 0:
        raise ValidationError(f"El monto a aplicar debe ser positivo. Valor: ₲{aplicado:,.0f}")

    if aplicado > saldo:
        raise ValidationError(
            f"El monto a aplicar (₲{aplicado:,.0f}) excede el saldo de la compra (₲{saldo:,.0f})"
        )


def validar_suma_aplicaciones(aplicaciones_totales, monto_pago):
    """
    Valida que la suma de aplicaciones no exceda el monto del pago.

    Args:
        aplicaciones_totales (Decimal): Suma de todas las aplicaciones
        monto_pago (Decimal): Monto total del pago

    Raises:
        ValidationError: Si la suma excede el monto
    """
    try:
        total_aplicado = Decimal(str(aplicaciones_totales))
        pago = Decimal(str(monto_pago))
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("Los montos deben ser números válidos")

    if total_aplicado > pago:
        raise ValidationError(
            f"La suma de aplicaciones (₲{total_aplicado:,.0f}) excede el monto del pago (₲{pago:,.0f})"
        )


# ============================
# Validadores de Notas de Crédito
# ============================


def validar_monto_nota_credito(monto_nc, monto_compra):
    """
    Valida que el monto de la nota de crédito sea coherente.

    Args:
        monto_nc (Decimal): Monto de la nota de crédito
        monto_compra (Decimal): Monto de la compra original

    Raises:
        ValidationError: Si el monto no es válido
    """
    try:
        nc = Decimal(str(monto_nc))
        compra = Decimal(str(monto_compra))
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("Los montos deben ser números válidos")

    if nc <= 0:
        raise ValidationError(
            f"El monto de la nota de crédito debe ser positivo. Valor: ₲{nc:,.0f}"
        )

    if nc > compra:
        raise ValidationError(
            f"El monto de la NC (₲{nc:,.0f}) no puede exceder el monto de la compra (₲{compra:,.0f})"
        )


def validar_motivo_nota_credito(motivo):
    """
    Valida que el motivo de la nota de crédito sea descriptivo.

    Args:
        motivo (str): Motivo de la NC

    Raises:
        ValidationError: Si el motivo no es válido
    """
    if not motivo:
        raise ValidationError("El motivo de la nota de crédito no puede estar vacío")

    motivo = str(motivo).strip()

    if len(motivo) < 10:
        raise ValidationError("El motivo de la nota de crédito debe tener al menos 10 caracteres")

    if len(motivo) > 255:
        raise ValidationError("El motivo no puede exceder 255 caracteres")


def validar_estado_nota_credito(estado):
    """
    Valida que el estado de la nota de crédito sea válido.

    Estados válidos:
    - Pendiente: NC registrada, pendiente de aplicación
    - Aplicado: NC aplicada a la compra
    - Rechazado: NC rechazada

    Args:
        estado (str): Estado a validar

    Raises:
        ValidationError: Si el estado no es válido
    """
    if not estado:
        raise ValidationError("El estado de la nota de crédito no puede estar vacío")

    estados_validos = ["Pendiente", "Aplicado", "Rechazado"]

    if estado not in estados_validos:
        raise ValidationError(
            f"Estado '{estado}' no válido. Debe ser uno de: {', '.join(estados_validos)}"
        )


# ============================
# Validadores de Cuenta Corriente
# ============================


def validar_dias_credito(dias_credito):
    """
    Valida que los días de crédito otorgados sean razonables.

    Args:
        dias_credito (int): Días de crédito

    Raises:
        ValidationError: Si los días no son válidos
    """
    if dias_credito is None:
        return  # Días de crédito opcionales

    try:
        dias = int(dias_credito)
    except (ValueError, TypeError):
        raise ValidationError("Los días de crédito deben ser un número entero")

    if dias < 0:
        raise ValidationError("Los días de crédito no pueden ser negativos")

    if dias > 180:
        raise ValidationError(
            f"Los días de crédito ({dias}) parecen excesivos (máximo recomendado: 180 días)"
        )


def validar_compra_dentro_limite_credito(monto_compra, saldo_actual, limite_credito):
    """
    Valida que una nueva compra no exceda el límite de crédito del proveedor.

    Args:
        monto_compra (Decimal): Monto de la nueva compra
        saldo_actual (Decimal): Saldo actual pendiente con el proveedor
        limite_credito (Decimal): Límite de crédito del proveedor

    Raises:
        ValidationError: Si excede el límite
    """
    if limite_credito is None:
        return  # Sin límite establecido

    try:
        compra = Decimal(str(monto_compra))
        saldo = Decimal(str(saldo_actual))
        limite = Decimal(str(limite_credito))
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError("Los montos deben ser números válidos")

    saldo_proyectado = saldo + compra

    if saldo_proyectado > limite:
        raise ValidationError(
            f"La compra (₲{compra:,.0f}) llevaría el saldo a ₲{saldo_proyectado:,.0f}, "
            f"excediendo el límite de crédito (₲{limite:,.0f})"
        )
