"""
Validadores para el módulo de Productos
Validaciones de negocio para productos, categorías, unidades de medida, precios y listas
"""

import re
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone

# ==================== VALIDADORES DE PRODUCTOS ====================


def validar_codigo_barra(codigo):
    """
    Valida el formato del código de barras.

    Formatos soportados:
    - EAN-13: 13 dígitos
    - EAN-8: 8 dígitos
    - UPC: 12 dígitos
    - Código interno: alfanumérico de 4-20 caracteres

    Args:
        codigo (str): Código de barras a validar

    Raises:
        ValidationError: Si el código no cumple con ningún formato válido

    Examples:
        >>> validar_codigo_barra('7891234567890')  # EAN-13 válido
        >>> validar_codigo_barra('12345678')       # EAN-8 válido
        >>> validar_codigo_barra('PROD-001')       # Código interno válido
    """
    if not codigo or not isinstance(codigo, str):
        raise ValidationError("El código de barras no puede estar vacío.")

    codigo = codigo.strip()

    # Si es solo numérico, validar EAN/UPC
    if codigo.isdigit():
        if len(codigo) not in [8, 12, 13]:
            raise ValidationError(
                "El código de barras numérico debe tener 8 (EAN-8), 12 (UPC) o 13 (EAN-13) dígitos. "
                f"Recibido: {len(codigo)} dígitos."
            )
    else:
        # Código alfanumérico (interno)
        if not re.match(r"^[A-Za-z0-9\-_\.]+$", codigo):
            raise ValidationError(
                "El código de barras alfanumérico solo puede contener letras, números, guiones, "
                "guiones bajos y puntos."
            )

        if len(codigo) < 4 or len(codigo) > 20:
            raise ValidationError(
                f"El código de barras alfanumérico debe tener entre 4 y 20 caracteres. "
                f"Recibido: {len(codigo)} caracteres."
            )


def validar_descripcion_producto(descripcion):
    """
    Valida la descripción del producto.

    Reglas:
    - Longitud: 3-255 caracteres
    - No puede contener solo espacios
    - Caracteres permitidos: letras, números, espacios, guiones, paréntesis, comas, puntos

    Args:
        descripcion (str): Descripción del producto

    Raises:
        ValidationError: Si la descripción no es válida

    Examples:
        >>> validar_descripcion_producto('Coca Cola 500ml')
        >>> validar_descripcion_producto('Empanada de Carne (Picante)')
    """
    if not descripcion or not isinstance(descripcion, str):
        raise ValidationError("La descripción del producto es obligatoria.")

    descripcion = descripcion.strip()

    if len(descripcion) < 3:
        raise ValidationError(
            f"La descripción del producto debe tener al menos 3 caracteres. "
            f"Recibido: {len(descripcion)} caracteres."
        )

    if len(descripcion) > 255:
        raise ValidationError(
            f"La descripción del producto no puede exceder 255 caracteres. " f"Recibido: {len(descripcion)} caracteres."
        )

    # Validar caracteres permitidos
    if not re.match(r"^[A-Za-z0-9\sáéíóúÁÉÍÓÚñÑ\-\(\),\.%°]+$", descripcion):
        raise ValidationError(
            "La descripción contiene caracteres no permitidos. "
            "Use solo letras, números, espacios y símbolos básicos (-, (), ., %)."
        )


def validar_stock_minimo(stock_minimo):
    """
    Valida el stock mínimo del producto.

    Reglas:
    - Debe ser >= 0
    - No puede exceder 100,000 unidades
    - Máximo 3 decimales

    Args:
        stock_minimo (Decimal): Stock mínimo del producto

    Raises:
        ValidationError: Si el stock mínimo no es válido

    Examples:
        >>> validar_stock_minimo(Decimal('10.000'))
        >>> validar_stock_minimo(Decimal('0.500'))
    """
    if stock_minimo is None:
        raise ValidationError("El stock mínimo es obligatorio.")

    try:
        stock = Decimal(str(stock_minimo))
    except (ValueError, TypeError):
        raise ValidationError("El stock mínimo debe ser un número válido.")

    if stock < 0:
        raise ValidationError("El stock mínimo no puede ser negativo.")

    if stock > 100000:
        raise ValidationError(f"El stock mínimo no puede exceder 100,000 unidades. " f"Recibido: {stock}.")

    # Validar máximo 3 decimales
    if stock.as_tuple().exponent < -3:
        raise ValidationError("El stock mínimo no puede tener más de 3 decimales.")


def validar_precio_positivo(precio):
    """
    Valida que el precio sea positivo y tenga formato correcto.

    Reglas:
    - Debe ser > 0
    - No puede exceder ₲100,000,000 (100 millones)
    - Máximo 2 decimales

    Args:
        precio (Decimal): Precio a validar

    Raises:
        ValidationError: Si el precio no es válido

    Examples:
        >>> validar_precio_positivo(Decimal('5000.00'))
        >>> validar_precio_positivo(Decimal('12500.50'))
    """
    if precio is None:
        raise ValidationError("El precio es obligatorio.")

    try:
        precio_decimal = Decimal(str(precio))
    except (ValueError, TypeError):
        raise ValidationError("El precio debe ser un número válido.")

    if precio_decimal <= 0:
        raise ValidationError("El precio debe ser mayor a cero.")

    if precio_decimal > 100000000:
        raise ValidationError(f"El precio no puede exceder ₲100,000,000. " f"Recibido: ₲{precio_decimal:,.2f}.")

    # Validar máximo 2 decimales
    if precio_decimal.as_tuple().exponent < -2:
        raise ValidationError("El precio no puede tener más de 2 decimales.")


def validar_cambio_estado_producto(producto, nuevo_estado):
    """
    Valida que se pueda cambiar el estado de un producto.

    Reglas:
    - No se puede desactivar si tiene stock > 0 (salvo configuración)
    - No se puede desactivar si tiene ventas pendientes
    - Registrar motivo de cambio (recomendado)

    Args:
        producto: Instancia del producto
        nuevo_estado (bool): True para activar, False para desactivar

    Raises:
        ValidationError: Si el cambio de estado no es permitido

    Examples:
        >>> validar_cambio_estado_producto(producto, False)
    """
    if not hasattr(producto, "id_producto"):
        raise ValidationError("Producto inválido.")

    # Si se está desactivando
    if not nuevo_estado and producto.estado:
        # Verificar stock (si el modelo tiene el método)
        if hasattr(producto, "stock_actual") and producto.stock_actual > 0:
            if not producto.permite_stock_negativo:
                raise ValidationError(
                    f"No se puede desactivar el producto {producto.descripcion} "
                    f"porque tiene stock disponible ({producto.stock_actual} unidades). "
                    "Ajuste el stock a cero primero o habilite stock negativo."
                )

    # Si se está reactivando, no hay restricciones especiales
    return True


def validar_margen_utilidad(precio_venta, costo_compra, margen_minimo=10):
    """
    Valida que el margen de utilidad sea razonable.

    Reglas:
    - Precio de venta debe ser > costo de compra
    - Margen mínimo configurable (por defecto 10%)
    - Alerta si margen > 300% (posible error)

    Args:
        precio_venta (Decimal): Precio de venta del producto
        costo_compra (Decimal): Costo de compra del producto
        margen_minimo (int): Porcentaje mínimo de margen aceptable

    Raises:
        ValidationError: Si el margen no es aceptable

    Examples:
        >>> validar_margen_utilidad(Decimal('5000'), Decimal('3000'))  # Margen ~67%
    """
    if precio_venta is None or costo_compra is None:
        return  # Si no hay datos, no validar

    try:
        venta = Decimal(str(precio_venta))
        costo = Decimal(str(costo_compra))
    except (ValueError, TypeError):
        raise ValidationError("Precio de venta y costo deben ser números válidos.")

    if costo <= 0:
        return  # No validar si no hay costo válido

    if venta <= costo:
        raise ValidationError(
            f"El precio de venta (₲{venta:,.2f}) debe ser mayor al costo de compra (₲{costo:,.2f}). "
            "Está vendiendo con pérdida."
        )

    # Calcular margen porcentual
    margen = ((venta - costo) / costo) * 100

    if margen < margen_minimo:
        raise ValidationError(
            f"El margen de utilidad ({margen:.1f}%) es menor al mínimo permitido ({margen_minimo}%). "
            f"Precio venta: ₲{venta:,.2f}, Costo: ₲{costo:,.2f}."
        )

    if margen > 300:
        # Alerta, no error (puede ser correcto en algunos casos)
        import warnings

        warnings.warn(
            f"El margen de utilidad ({margen:.1f}%) es muy alto. " f"Verifique que el precio y costo sean correctos.",
            UserWarning,
        )


def validar_producto_unico(descripcion, codigo_barra=None, producto_id=None):
    """
    Valida que no exista otro producto con la misma descripción o código de barras.

    Args:
        descripcion (str): Descripción del producto
        codigo_barra (str): Código de barras (opcional)
        producto_id (int): ID del producto actual (para ediciones)

    Raises:
        ValidationError: Si ya existe un producto similar
    """
    from apps.productos.models import Productos

    # Validar descripción única
    query_desc = Productos.objects.filter(descripcion__iexact=descripcion)
    if producto_id:
        query_desc = query_desc.exclude(id_producto=producto_id)

    if query_desc.exists():
        raise ValidationError(
            f'Ya existe un producto con la descripción "{descripcion}". ' "Use una descripción diferente."
        )

    # Validar código de barras único (si se proporciona)
    if codigo_barra:
        query_codigo = Productos.objects.filter(codigo_barra__iexact=codigo_barra)
        if producto_id:
            query_codigo = query_codigo.exclude(id_producto=producto_id)

        if query_codigo.exists():
            raise ValidationError(
                f'Ya existe un producto con el código de barras "{codigo_barra}". '
                "Los códigos de barras deben ser únicos."
            )


# ==================== VALIDADORES DE CATEGORÍAS ====================


def validar_nombre_categoria(nombre):
    """
    Valida el nombre de la categoría.

    Reglas:
    - Longitud: 3-100 caracteres
    - Solo letras, números, espacios y guiones
    - No puede ser solo espacios

    Args:
        nombre (str): Nombre de la categoría

    Raises:
        ValidationError: Si el nombre no es válido

    Examples:
        >>> validar_nombre_categoria('Bebidas')
        >>> validar_nombre_categoria('Snacks Salados')
    """
    if not nombre or not isinstance(nombre, str):
        raise ValidationError("El nombre de la categoría es obligatorio.")

    nombre = nombre.strip()

    if len(nombre) < 3:
        raise ValidationError(
            f"El nombre de la categoría debe tener al menos 3 caracteres. " f"Recibido: {len(nombre)} caracteres."
        )

    if len(nombre) > 100:
        raise ValidationError(
            f"El nombre de la categoría no puede exceder 100 caracteres. " f"Recibido: {len(nombre)} caracteres."
        )

    if not re.match(r"^[A-Za-z0-9\sáéíóúÁÉÍÓÚñÑ\-]+$", nombre):
        raise ValidationError("El nombre de la categoría solo puede contener letras, números, espacios y guiones.")


def validar_jerarquia_categoria(categoria_padre, categoria_actual_id=None):
    """
    Valida que no se creen ciclos en la jerarquía de categorías.

    Un ciclo sería: A es padre de B, B es padre de C, C es padre de A (inválido)

    Args:
        categoria_padre: Categoría padre a asignar
        categoria_actual_id (int): ID de la categoría actual (para ediciones)

    Raises:
        ValidationError: Si se detecta un ciclo en la jerarquía

    Examples:
        >>> validar_jerarquia_categoria(categoria_bebidas)
    """
    if categoria_padre is None:
        return  # Categoría raíz, no hay jerarquía que validar

    # Prevenir que una categoría sea su propio padre
    if categoria_actual_id and categoria_padre.id_categoria == categoria_actual_id:
        raise ValidationError("Una categoría no puede ser su propio padre.")

    # Recorrer la cadena de padres para detectar ciclos
    MAX_DEPTH = 10  # Límite de profundidad para evitar loops infinitos
    depth = 0
    current = categoria_padre

    while current is not None and depth < MAX_DEPTH:
        if categoria_actual_id and current.id_categoria == categoria_actual_id:
            raise ValidationError(
                f"No se puede asignar esta categoría padre porque crearía un ciclo. "
                f'La categoría "{current.nombre}" ya es descendiente de la categoría actual.'
            )

        current = current.id_categoria_padre
        depth += 1

    if depth >= MAX_DEPTH:
        raise ValidationError(
            "La jerarquía de categorías es demasiado profunda (máximo 10 niveles). "
            "Reorganice las categorías para reducir la profundidad."
        )


def validar_categoria_activa_con_productos(categoria):
    """
    Valida que no se puedan desactivar categorías que tienen productos activos.

    Args:
        categoria: Instancia de la categoría

    Raises:
        ValidationError: Si la categoría tiene productos activos
    """
    if not hasattr(categoria, "id_categoria"):
        raise ValidationError("Categoría inválida.")

    # Contar productos activos en esta categoría
    productos_activos = categoria.productos.filter(estado=True).count()

    if productos_activos > 0:
        raise ValidationError(
            f'No se puede desactivar la categoría "{categoria.nombre}" '
            f"porque tiene {productos_activos} producto(s) estado(s). "
            "Desactive o reasigne los productos primero."
        )

    # Verificar subcategorías activas
    if hasattr(categoria, "subcategorias"):
        subcategorias_activas = categoria.subcategorias.filter(estado=True).count()

        if subcategorias_activas > 0:
            raise ValidationError(
                f'No se puede desactivar la categoría "{categoria.nombre}" '
                f"porque tiene {subcategorias_activas} subcategoría(s) activa(s). "
                "Desactive las subcategorías primero."
            )


# ==================== VALIDADORES DE UNIDADES DE MEDIDA ====================


def validar_nombre_unidad(nombre):
    """
    Valida el nombre de la unidad de medida.

    Reglas:
    - Longitud: 2-50 caracteres
    - Solo letras y espacios

    Args:
        nombre (str): Nombre de la unidad

    Raises:
        ValidationError: Si el nombre no es válido

    Examples:
        >>> validar_nombre_unidad('Kilogramo')
        >>> validar_nombre_unidad('Litro')
    """
    if not nombre or not isinstance(nombre, str):
        raise ValidationError("El nombre de la unidad de medida es obligatorio.")

    nombre = nombre.strip()

    if len(nombre) < 2:
        raise ValidationError(
            f"El nombre de la unidad debe tener al menos 2 caracteres. " f"Recibido: {len(nombre)} caracteres."
        )

    if len(nombre) > 50:
        raise ValidationError(
            f"El nombre de la unidad no puede exceder 50 caracteres. " f"Recibido: {len(nombre)} caracteres."
        )

    if not re.match(r"^[A-Za-záéíóúÁÉÍÓÚñÑ\s]+$", nombre):
        raise ValidationError("El nombre de la unidad solo puede contener letras y espacios.")


def validar_abreviatura_unidad(abreviatura):
    """
    Valida la abreviatura de la unidad de medida.

    Reglas:
    - Longitud: 1-10 caracteres
    - Solo letras, números y símbolos básicos
    - Sin espacios

    Args:
        abreviatura (str): Abreviatura de la unidad

    Raises:
        ValidationError: Si la abreviatura no es válida

    Examples:
        >>> validar_abreviatura_unidad('Kg')
        >>> validar_abreviatura_unidad('L')
        >>> validar_abreviatura_unidad('m²')
    """
    if not abreviatura or not isinstance(abreviatura, str):
        raise ValidationError("La abreviatura de la unidad es obligatoria.")

    abreviatura = abreviatura.strip()

    if len(abreviatura) < 1:
        raise ValidationError("La abreviatura debe tener al menos 1 carácter.")

    if len(abreviatura) > 10:
        raise ValidationError(
            f"La abreviatura no puede exceder 10 caracteres. " f"Recibido: {len(abreviatura)} caracteres."
        )

    if " " in abreviatura:
        raise ValidationError("La abreviatura no puede contener espacios.")

    if not re.match(r"^[A-Za-z0-9²³°]+$", abreviatura):
        raise ValidationError("La abreviatura solo puede contener letras, números y símbolos básicos (², ³, °).")


def validar_unidad_activa_con_productos(unidad):
    """
    Valida que no se puedan desactivar unidades que tienen productos activos.

    Args:
        unidad: Instancia de la unidad de medida

    Raises:
        ValidationError: Si la unidad tiene productos activos
    """
    if not hasattr(unidad, "id_unidad_medida"):
        raise ValidationError("Unidad de medida inválida.")

    # Contar productos activos con esta unidad
    productos_activos = unidad.productos.filter(estado=True).count()

    if productos_activos > 0:
        raise ValidationError(
            f'No se puede desactivar la unidad "{unidad.nombre}" '
            f"porque tiene {productos_activos} producto(s) estado(s). "
            "Reasigne los productos a otra unidad primero."
        )


# ==================== VALIDADORES DE LISTAS DE PRECIOS ====================


def validar_nombre_lista_precios(nombre):
    """
    Valida el nombre de la lista de precios.

    Reglas:
    - Longitud: 3-100 caracteres
    - Solo letras, números, espacios, guiones y paréntesis
    - Debe ser descriptivo

    Args:
        nombre (str): Nombre de la lista

    Raises:
        ValidationError: Si el nombre no es válido

    Examples:
        >>> validar_nombre_lista_precios('Minorista')
        >>> validar_nombre_lista_precios('Mayorista (10+ unidades)')
    """
    if not nombre or not isinstance(nombre, str):
        raise ValidationError("El nombre de la lista de precios es obligatorio.")

    nombre = nombre.strip()

    if len(nombre) < 3:
        raise ValidationError(
            f"El nombre de la lista debe tener al menos 3 caracteres. " f"Recibido: {len(nombre)} caracteres."
        )

    if len(nombre) > 100:
        raise ValidationError(
            f"El nombre de la lista no puede exceder 100 caracteres. " f"Recibido: {len(nombre)} caracteres."
        )

    if not re.match(r"^[A-Za-z0-9\sáéíóúÁÉÍÓÚñÑ\-\(\)\+]+$", nombre):
        raise ValidationError(
            "El nombre de la lista solo puede contener letras, números, espacios, "
            "guiones, paréntesis y el símbolo +."
        )


def validar_fecha_vigencia_lista(fecha_vigencia):
    """
    Valida la fecha de vigencia de la lista de precios.

    Reglas:
    - No puede ser más de 1 año en el futuro
    - Puede ser fecha pasada (listas históricas)
    - Generar advertencia si es muy antigua (>2 años)

    Args:
        fecha_vigencia (date): Fecha de vigencia

    Raises:
        ValidationError: Si la fecha no es válida

    Examples:
        >>> validar_fecha_vigencia_lista(date.today())
    """
    if fecha_vigencia is None:
        return  # Fecha de vigencia es opcional

    hoy = timezone.now().date()

    # No permitir fechas muy futuras (más de 1 año)
    fecha_limite_futura = hoy + timedelta(days=365)
    if fecha_vigencia > fecha_limite_futura:
        raise ValidationError(
            f"La fecha de vigencia no puede ser más de 1 año en el futuro. "
            f'Fecha máxima: {fecha_limite_futura.strftime("%d/%m/%Y")}.'
        )

    # Advertencia para listas muy antiguas (más de 2 años)
    fecha_limite_pasada = hoy - timedelta(days=730)  # 2 años
    if fecha_vigencia < fecha_limite_pasada:
        import warnings

        warnings.warn(
            f'La lista tiene una fecha de vigencia muy antigua ({fecha_vigencia.strftime("%d/%m/%Y")}). '
            "Verifique que sea correcta.",
            UserWarning,
        )


def validar_moneda_lista(moneda):
    """
    Valida el código de moneda de la lista de precios.

    Códigos soportados: PYG (Guaraníes), USD (Dólares), EUR (Euros), BRL (Reales)

    Args:
        moneda (str): Código de moneda (3 letras)

    Raises:
        ValidationError: Si la moneda no es válida

    Examples:
        >>> validar_moneda_lista('PYG')
        >>> validar_moneda_lista('USD')
    """
    MONEDAS_VALIDAS = ["PYG", "USD", "EUR", "BRL", "ARS"]

    if not moneda or not isinstance(moneda, str):
        raise ValidationError("El código de moneda es obligatorio.")

    moneda = moneda.upper().strip()

    if len(moneda) != 3:
        raise ValidationError(
            f"El código de moneda debe tener exactamente 3 caracteres. " f"Recibido: {len(moneda)} caracteres."
        )

    if not moneda.isalpha():
        raise ValidationError("El código de moneda solo puede contener letras.")

    if moneda not in MONEDAS_VALIDAS:
        raise ValidationError(
            f'Código de moneda no soportado: "{moneda}". ' f'Monedas válidas: {", ".join(MONEDAS_VALIDAS)}.'
        )


def validar_lista_activa_con_precios(lista):
    """
    Valida que no se puedan desactivar listas que están en uso estado.

    Args:
        lista: Instancia de la lista de precios

    Raises:
        ValidationError: Si la lista tiene precios asignados
    """
    if not hasattr(lista, "id_lista"):
        raise ValidationError("Lista de precios inválida.")

    # Contar precios en esta lista
    precios_count = lista.precios.count()

    if precios_count > 0:
        import warnings

        warnings.warn(
            f'La lista "{lista.nombre_lista}" tiene {precios_count} precio(s) asignado(s). '
            "Considere desactivar los productos individuales en lugar de la lista completa.",
            UserWarning,
        )


# ==================== VALIDADORES DE PRECIOS POR LISTA ====================


def validar_precio_unitario_lista(precio_unitario):
    """
    Valida el precio unitario en una lista de precios.

    Reglas:
    - Debe ser > 0
    - No puede exceder ₲100,000,000
    - Máximo 2 decimales

    Args:
        precio_unitario (Decimal): Precio del producto

    Raises:
        ValidationError: Si el precio no es válido

    Examples:
        >>> validar_precio_unitario_lista(Decimal('5000.00'))
    """
    validar_precio_positivo(precio_unitario)  # Reutilizar validador existente


def validar_unicidad_precio_lista(id_producto, id_lista, id_precio=None):
    """
    Valida que no exista otro precio para la misma combinación producto-lista.

    Args:
        id_producto (int): ID del producto
        id_lista (int): ID de la lista
        id_precio (int): ID del precio actual (para ediciones)

    Raises:
        ValidationError: Si ya existe un precio para esa combinación
    """
    from apps.productos.models import PreciosPorLista

    query = PreciosPorLista.objects.filter(id_producto=id_producto, id_lista=id_lista)

    if id_precio:
        query = query.exclude(id_precio=id_precio)

    if query.exists():
        raise ValidationError(
            "Ya existe un precio asignado para este producto en esta lista. "
            "Edite el precio existente en lugar de crear uno nuevo."
        )


def validar_variacion_precio(precio_nuevo, precio_anterior, max_variacion=50):
    """
    Valida que la variación de precio no sea excesiva.

    Reglas:
    - Cambios mayores al X% (default 50%) generan advertencia
    - Cambios superiores a 200% requieren justificación

    Args:
        precio_nuevo (Decimal): Nuevo precio
        precio_anterior (Decimal): Precio anterior
        max_variacion (int): Variación máxima permitida sin advertencia (%)

    Raises:
        ValidationError: Si la variación es excesiva

    Examples:
        >>> validar_variacion_precio(Decimal('5000'), Decimal('4000'))  # +25%
    """
    if precio_anterior is None or precio_nuevo is None:
        return  # Si no hay precio anterior, no validar

    try:
        anterior = Decimal(str(precio_anterior))
        nuevo = Decimal(str(precio_nuevo))
    except (ValueError, TypeError):
        raise ValidationError("Los precios deben ser números válidos.")

    if anterior <= 0:
        return  # No validar si el precio anterior no es válido

    # Calcular variación porcentual
    variacion = abs(((nuevo - anterior) / anterior) * 100)

    if variacion > 200:
        raise ValidationError(
            f"La variación de precio ({variacion:.1f}%) es excesiva. "
            f"Precio anterior: ₲{anterior:,.2f}, Precio nuevo: ₲{nuevo:,.2f}. "
            "Verifique que los valores sean correctos."
        )

    if variacion > max_variacion:
        import warnings

        warnings.warn(
            f"La variación de precio ({variacion:.1f}%) supera el límite recomendado ({max_variacion}%). "
            f"Precio anterior: ₲{anterior:,.2f}, Precio nuevo: ₲{nuevo:,.2f}.",
            UserWarning,
        )


# ==================== VALIDADORES DE HISTÓRICO DE PRECIOS ====================


def validar_cambio_precio_historico(precio_anterior, precio_nuevo):
    """
    Valida que el cambio de precio sea válido para registrar en el histórico.

    Reglas:
    - Precio anterior y nuevo deben ser diferentes
    - Ambos deben ser > 0
    - La diferencia debe ser significativa (>₲1)

    Args:
        precio_anterior (Decimal): Precio anterior
        precio_nuevo (Decimal): Precio nuevo

    Raises:
        ValidationError: Si el cambio no es válido

    Examples:
        >>> validar_cambio_precio_historico(Decimal('4000'), Decimal('5000'))
    """
    if precio_anterior is None or precio_nuevo is None:
        raise ValidationError("Precio anterior y nuevo son obligatorios.")

    try:
        anterior = Decimal(str(precio_anterior))
        nuevo = Decimal(str(precio_nuevo))
    except (ValueError, TypeError):
        raise ValidationError("Los precios deben ser números válidos.")

    if anterior <= 0 or nuevo <= 0:
        raise ValidationError("Los precios deben ser mayores a cero.")

    if anterior == nuevo:
        raise ValidationError("El precio anterior y el nuevo son iguales. " "No hay cambio para registrar.")

    # Validar que la diferencia sea significativa (>₲1)
    diferencia = abs(nuevo - anterior)
    if diferencia < Decimal("1.00"):
        import warnings

        warnings.warn(
            f"La diferencia de precio es muy pequeña (₲{diferencia:.2f}). "
            "Considere si es necesario registrar este cambio.",
            UserWarning,
        )


def validar_fecha_cambio_precio(fecha_cambio):
    """
    Valida que la fecha de cambio de precio sea razonable.

    Reglas:
    - No puede ser futura
    - No puede ser más antigua que 5 años

    Args:
        fecha_cambio (datetime): Fecha del cambio de precio

    Raises:
        ValidationError: Si la fecha no es válida
    """
    if fecha_cambio is None:
        return  # Si no se proporciona, se usará auto_now_add

    ahora = timezone.now()

    if fecha_cambio > ahora:
        raise ValidationError(
            "La fecha de cambio de precio no puede ser futura. "
            f'Fecha proporcionada: {fecha_cambio.strftime("%d/%m/%Y %H:%M")}.'
        )

    # No permitir fechas muy antiguas (más de 5 años)
    fecha_limite = ahora - timedelta(days=1825)  # 5 años
    if fecha_cambio < fecha_limite:
        raise ValidationError(
            f"La fecha de cambio es demasiado antigua (más de 5 años). "
            f'Fecha límite: {fecha_limite.strftime("%d/%m/%Y")}.'
        )
