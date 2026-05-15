"""
Validadores para el modulo de Almuerzos
Solo reglas de negocio que Django no cubre automaticamente
"""

from django.core.exceptions import ValidationError


def validar_limite_registros_diarios(hijo, fecha_consumo, registro_actual=None):
    """
    Valida que un hijo no tenga mas de 2 registros de almuerzo en el mismo dia.

    REGLA DE NEGOCIO:
    - Maximo 2 registros por alumno por dia
    - Primer registro: genera cobro (ya_cobrado=True)
    - Segundo registro: NO genera cobro (ya_cobrado=False)
    - Tercer intento: BLOQUEADO

    Returns:
        bool: True si es el primer registro (cobra), False si es el segundo (no cobra)
    """
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

    registros_existentes = query.count()

    if registros_existentes >= 2:
        raise ValidationError(
            f"Limite alcanzado: Ya existen {registros_existentes} registros de almuerzo "
            f"para este alumno el {fecha_consumo}. Maximo permitido: 2 registros por dia."
        )

    return registros_existentes == 0