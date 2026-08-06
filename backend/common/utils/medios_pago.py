"""
Resolución de MedioPago a partir de códigos de método de pago.

El frontend usa códigos fijos (frontend/src/constants/mediosPago.ts:
EFECTIVO, POS DEBITO, POS CREDITO, TRANSFERENCIA) que no siempre
coinciden textualmente con el catálogo real de MedioPago (editable desde
Configuración). El mapa de alias cubre los casos conocidos que no
matchean ni por nombre exacto ni por substring.
"""

_ALIAS_MEDIOS_PAGO = {
    "POS DEBITO": "POS Bancario debito",
    "POS CREDITO": "POS Bancario crédito",
}


def resolver_medio_pago(metodo: str):
    """Busca un MedioPago por nombre exacto (case-insensitive), probando
    primero los alias conocidos y luego una búsqueda parcial como último
    recurso. Retorna None si no encuentra ninguno."""
    from apps.core.models import MedioPago

    if not metodo:
        return None

    alias = _ALIAS_MEDIOS_PAGO.get(metodo.strip().upper())
    if alias:
        exacto = MedioPago.objects.filter(descripcion__iexact=alias).first()
        if exacto:
            return exacto

    return (
        MedioPago.objects.filter(descripcion__iexact=metodo).first()
        or MedioPago.objects.filter(descripcion__icontains=metodo).first()
    )
