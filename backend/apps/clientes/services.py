"""
Servicios de dominio para la app clientes.
Operaciones que involucran múltiples modelos o reglas de negocio complejas.
"""

from django.db import transaction

from .models import AlumnoResponsable, Hijo


def cambiar_titular(hijo: Hijo, nuevo_cliente_id: int, changed_by=None) -> AlumnoResponsable:
    """
    Cambia el responsable titular de un alumno de forma atómica.

    Reglas:
    - El nuevo cliente debe ya tener una fila en AlumnoResponsable para ese hijo.
    - Se desactiva es_titular en el titular actual.
    - Se activa es_titular en el nuevo titular.
    - Se sincroniza Hijo.cliente_responsable para mantener compatibilidad con el
      modelo financiero existente (ventas, facturas, recargas).

    Raises:
        AlumnoResponsable.DoesNotExist: si nuevo_cliente_id no está en la tabla pivot.
        ValueError: si se intenta designar un responsable inactivo como titular.
    """
    with transaction.atomic():
        nuevo = AlumnoResponsable.objects.select_for_update().get(
            hijo=hijo,
            cliente_id=nuevo_cliente_id,
        )
        if not nuevo.activo:
            raise ValueError("No se puede designar un responsable inactivo como titular.")

        # Quitar titular actual (puede ser None si la tabla está vacía)
        AlumnoResponsable.objects.filter(
            hijo=hijo, es_titular=True
        ).exclude(pk=nuevo.pk).update(es_titular=False)

        # Activar nuevo titular
        nuevo.es_titular = True
        nuevo.activo = True
        nuevo.save(update_fields=["es_titular", "activo"])

        # Sincronizar Hijo.cliente_responsable
        Hijo.objects.filter(pk=hijo.pk).update(cliente_responsable_id=nuevo_cliente_id)

        return nuevo


def agregar_responsable(
    hijo: Hijo,
    cliente_id: int,
    parentesco: str,
    orden_cobro: int = 1,
    recibe_notificaciones: bool = False,
    puede_ver_saldo: bool = False,
    added_by=None,
) -> AlumnoResponsable:
    """
    Agrega un nuevo responsable al alumno. No lo designa como titular.
    Usa get_or_create para ser idempotente.
    """
    responsable, created = AlumnoResponsable.objects.get_or_create(
        hijo=hijo,
        cliente_id=cliente_id,
        defaults={
            "parentesco": parentesco,
            "orden_cobro": orden_cobro,
            "recibe_notificaciones": recibe_notificaciones,
            "puede_ver_saldo": puede_ver_saldo,
            "activo": True,
            "agregado_por": added_by,
        },
    )
    if not created and not responsable.activo:
        responsable.activo = True
        responsable.save(update_fields=["activo"])
    return responsable
