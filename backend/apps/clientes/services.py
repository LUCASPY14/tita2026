"""
Servicios de dominio para la app clientes.
Operaciones que involucran múltiples modelos o reglas de negocio complejas.
"""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import AlumnoResponsable, Hijo, RestriccionHijo

_ORIGENES_CC_VALIDOS = {"CANTINA", "ALMUERZO"}


def resolver_origen_pago_cc(cliente, origen_solicitado, monto) -> str:
    """
    Resuelve a qué categoría (CANTINA/ALMUERZO) corresponde un pago de
    cuenta corriente, usado tanto por el pago directo del cajero
    (CuentaCorrienteClienteViewSet) como por el pago del portal vía Bancard.

    - Si el cliente debe en ambas categorías, origen_solicitado es obligatorio.
    - Si debe en una sola, se infiere aunque no se mande (así el frontend
      puede ocultar el selector cuando no hace falta elegir).
    - El monto no puede superar la deuda de la categoría resuelta.
    """
    deuda_cantina = cliente.saldo_cc_cantina
    deuda_almuerzo = cliente.saldo_cc_almuerzo
    origen = (origen_solicitado or "").strip().upper()

    if deuda_cantina > 0 and deuda_almuerzo > 0:
        if origen not in _ORIGENES_CC_VALIDOS:
            raise ValidationError({
                "origen": "El cliente tiene deuda en cantina y almuerzo — indicá 'origen': 'CANTINA' o 'ALMUERZO'.",
            })
    elif deuda_cantina > 0:
        origen = "CANTINA"
    elif deuda_almuerzo > 0:
        origen = "ALMUERZO"
    else:
        # Sin deuda categorizada — puede quedar deuda GENERAL histórica sin
        # clasificar; no hay categoría contra la cual validar el monto.
        return origen if origen in _ORIGENES_CC_VALIDOS else "GENERAL"

    deuda_categoria = deuda_cantina if origen == "CANTINA" else deuda_almuerzo
    if monto > deuda_categoria:
        raise ValidationError({
            "monto": f"El pago (₲{monto:,.0f}) supera la deuda de {origen.lower()} (₲{deuda_categoria:,.0f}).",
        })

    return origen


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


def purgar_alumno(hijo: Hijo, aprobado_por) -> Hijo:
    """
    Anonimiza los datos sensibles de un alumno dado de baja hace más de un
    año: restricciones médicas, foto, fecha de nacimiento, grado y nombre.

    La fila de Hijo NO se borra — todo el historial financiero (ventas,
    facturas, cuenta corriente) sigue colgando de ella. Requiere aprobación
    explícita de un ADMIN (ver HijoViewSet.aprobar_purga); esta función no
    valida el estado por su cuenta, eso lo hace quien la llama.
    """
    with transaction.atomic():
        hijo = Hijo.objects.select_for_update().get(pk=hijo.pk)

        RestriccionHijo.objects.filter(hijo=hijo).delete()

        if hijo.foto_perfil:
            hijo.foto_perfil.delete(save=False)

        fecha_str = timezone.now().strftime("%Y-%m-%d")
        hijo.nombre = "Alumno purgado"
        hijo.apellido = f"— {fecha_str} #{hijo.pk}"
        hijo.fecha_nacimiento = None
        hijo.grado = None
        hijo.fecha_foto = None
        hijo.datos_purgados = True
        hijo.save()

        return hijo
