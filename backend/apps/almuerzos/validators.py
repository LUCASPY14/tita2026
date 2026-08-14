"""
Validadores para el modulo de Almuerzos
Solo reglas de negocio que Django no cubre automaticamente
"""

from rest_framework.exceptions import ValidationError


def validar_restricciones_alergenicas(hijo, forzar: bool = False) -> list[dict]:
    """
    Verifica las restricciones activas del hijo.
    - Severidad CRITICA + requiere_autorizacion=True → bloquea salvo forzar=True.
    - Otras restricciones → retorna lista de advertencias para mostrar al cajero.

    Returns:
        list[dict]: advertencias [{tipo, severidad, descripcion}]
    Raises:
        ValidationError si hay restricciones CRITICA bloqueantes y forzar=False.
    """
    from apps.clientes.models import RestriccionHijo

    restricciones = RestriccionHijo.objects.filter(hijo=hijo)
    advertencias = []
    bloqueantes = []

    for r in restricciones:
        entry = {
            "tipo": r.tipo,
            "severidad": r.severidad,
            "descripcion": r.descripcion or "",
        }
        if r.severidad == RestriccionHijo.Severidad.CRITICA and r.requiere_autorizacion:
            bloqueantes.append(entry)
        else:
            advertencias.append(entry)

    if bloqueantes and not forzar:
        raise ValidationError({
            "error": "El alumno tiene restricciones críticas que requieren autorización.",
            "restricciones": bloqueantes,
            "hint": "Incluya 'forzar_restriccion': true para registrar de todos modos.",
        })

    return advertencias + bloqueantes


def verificar_alergenos_venta(hijo, productos: list) -> list[dict]:
    """
    Cruza los alérgenos de los productos con las restricciones del hijo.
    Matching: nombre del alergeno o sus palabras_clave aparecen en tipo/descripcion de la restriccion.

    Returns:
        list[dict]: advertencias [{producto, alergeno, restriccion, severidad}]
    """
    from apps.clientes.models import RestriccionHijo
    from apps.almuerzos.models import ProductoAlergeno

    if not hijo or not productos:
        return []

    restricciones = list(RestriccionHijo.objects.filter(hijo=hijo, activo=True))
    if not restricciones:
        return []

    alergenos_productos = (
        ProductoAlergeno.objects
        .filter(producto__in=productos)
        .select_related("alergeno", "producto")
    )
    if not alergenos_productos:
        return []

    advertencias = []
    for pa in alergenos_productos:
        alergeno = pa.alergeno
        palabras = [alergeno.nombre.lower()] + [
            p.lower() for p in (alergeno.palabras_clave or [])
        ]
        for restriccion in restricciones:
            texto = f"{restriccion.tipo} {restriccion.descripcion or ''}".lower()
            if any(p in texto for p in palabras):
                advertencias.append({
                    "producto": pa.producto.descripcion,
                    "alergeno": alergeno.nombre,
                    "contiene": pa.contiene,
                    "restriccion": restriccion.tipo,
                    "severidad": restriccion.severidad,
                })

    return advertencias


SEGUNDOS_MINIMOS_SEGUNDO_REGISTRO = 240


def validar_limite_registros_diarios(hijo, fecha_consumo, registro_actual=None):
    """
    Valida que un hijo no tenga mas de 2 registros de almuerzo en el mismo dia,
    y que el segundo se registre al menos SEGUNDOS_MINIMOS_SEGUNDO_REGISTRO
    despues del primero — un alumno no puede volver a servirse en cuestion de
    segundos, así que cualquier reintento antes de ese margen se trata como un
    doble-escaneo accidental, no como un segundo ingreso real.

    REGLA DE NEGOCIO:
    - Maximo 2 registros por alumno por dia
    - Primer registro: genera cobro (ya_cobrado=True)
    - Segundo registro: NO genera cobro (ya_cobrado=False), requiere que hayan
      pasado al menos SEGUNDOS_MINIMOS_SEGUNDO_REGISTRO desde el primero
    - Tercer intento: BLOQUEADO

    Returns:
        bool: True si es el primer registro (cobra), False si es el segundo (no cobra)
    """
    from datetime import datetime

    from django.utils import timezone

    from .models import RegistroConsumoAlmuerzo

    if hijo is None or fecha_consumo is None:
        return True

    query = RegistroConsumoAlmuerzo.objects.filter(
        hijo=hijo,
        fecha_consumo=fecha_consumo,
        estado=RegistroConsumoAlmuerzo.Estado.REGISTRADO,
    )

    if registro_actual:
        query = query.exclude(pk=registro_actual.pk)

    registros_existentes = list(query.order_by("-hora_registro"))
    cantidad = len(registros_existentes)

    if cantidad >= 2:
        raise ValidationError({
            "error": (
                f"Limite alcanzado: Ya existen {cantidad} registros de almuerzo "
                f"para este alumno el {fecha_consumo}. Maximo permitido: 2 registros por dia."
            )
        })

    if cantidad == 1:
        ultimo = registros_existentes[0]
        inicio = timezone.make_aware(datetime.combine(fecha_consumo, ultimo.hora_registro))
        transcurridos = (timezone.localtime() - inicio).total_seconds()
        if transcurridos < SEGUNDOS_MINIMOS_SEGUNDO_REGISTRO:
            faltan = int(SEGUNDOS_MINIMOS_SEGUNDO_REGISTRO - transcurridos)
            raise ValidationError({
                "error": (
                    "Todavia es muy pronto para un segundo ingreso de almuerzo. "
                    f"Esperar {faltan} segundos mas."
                )
            })

    return cantidad == 0
