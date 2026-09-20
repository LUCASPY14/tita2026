"""
Servicios de dominio para la app clientes.
Operaciones que involucran múltiples modelos o reglas de negocio complejas.
"""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import AlumnoResponsable, Cliente, Hijo, RestriccionHijo, TipoCliente

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
    # La deuda por categoría se recalcula sumando débitos/créditos etiquetados
    # con ese origen. Créditos históricos o no clasificados (origen GENERAL)
    # no se restan de ninguna categoría, así que la suma de ambas puede
    # superar la deuda total real — nunca puede ser menor. Limitamos acá para
    # no ofrecer/aceptar un pago mayor a lo que el cliente realmente debe.
    deuda_categoria = min(deuda_categoria, cliente.saldo_cuenta_corriente)
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


def crear_usuario_portal(cliente):
    """Crea (o vincula) un usuario CLIENTE_WEB para el cliente dado.

    - Si ya tiene usuario portal, no hace nada.
    - Usa el email del cliente como identificador; si no tiene email, genera
      uno sintético: <ruc_ci_limpio>@portal.tita.local
    - La contraseña inicial es el RUC/CI tal como está almacenado.
    - El usuario queda marcado con debe_cambiar_contrasena=True.
    """
    from apps.usuarios.models import Usuario

    if hasattr(cliente, "usuario_portal"):
        return

    ruc_ci_limpio = cliente.ruc_ci.strip()
    email = (cliente.email or "").strip()
    if not email:
        sufijo = ruc_ci_limpio.replace("-", "").replace(".", "")
        email = f"{sufijo}@portal.tita.local"

    usuario_existente = Usuario.objects.filter(email=email).first()
    if usuario_existente:
        # Ya existe un usuario con ese email: vincular si no tiene cliente
        if not usuario_existente.cliente_id:
            usuario_existente.cliente = cliente
            usuario_existente.save(update_fields=["cliente"])
        return

    Usuario.objects.create_user(
        email=email,
        password=ruc_ci_limpio,
        nombre=cliente.nombres,
        apellido=cliente.apellidos,
        rol=Usuario.Rol.CLIENTE_WEB,
        is_active=True,
        email_verificado=bool(cliente.email),
        debe_cambiar_contrasena=True,
        cliente=cliente,
    )


def crear_responsable_con_cliente_nuevo(
    hijo: Hijo,
    datos_cliente: dict,
    parentesco: str,
    orden_cobro: int = 1,
    recibe_notificaciones: bool = False,
    puede_ver_saldo: bool = False,
    added_by=None,
) -> AlumnoResponsable:
    """
    Crea un cliente nuevo y lo agrega como responsable del alumno, en una sola
    transacción — para cuando la persona a agregar (madre, abuelo, tutor...)
    todavía no está cargada como cliente en el sistema.

    El cliente nuevo se crea con tipo "Familia" y la lista de precios por
    defecto, sin pedirlos en el formulario. Si el ruc_ci ya pertenece a otro
    cliente, no se crea un duplicado: se avisa cuál es para elegirlo como
    "cliente existente" en su lugar.
    """
    from apps.productos.models import ListaPrecio

    ruc_ci = (datos_cliente.get("ruc_ci") or "").strip()
    existente = Cliente.objects.filter(ruc_ci=ruc_ci).first()
    if existente:
        raise ValidationError({
            "ruc_ci": (
                f'Ya existe un cliente con ese RUC/CI: {existente.nombre_completo}. '
                'Elegilo desde "Cliente existente" en vez de crear uno nuevo.'
            ),
        })

    tipo_familia, _ = TipoCliente.objects.get_or_create(nombre="Familia", defaults={"activo": True})
    lista = ListaPrecio.objects.filter(activo=True, es_por_defecto=True).first()
    if lista is None:
        lista, _ = ListaPrecio.objects.get_or_create(
            nombre="Lista General", defaults={"activo": True, "es_por_defecto": True},
        )

    with transaction.atomic():
        cliente = Cliente.objects.create(
            nombres=datos_cliente["nombres"],
            apellidos=datos_cliente["apellidos"],
            ruc_ci=ruc_ci,
            telefono=datos_cliente.get("telefono") or None,
            email=datos_cliente.get("email") or None,
            tipo_cliente=tipo_familia,
            lista_precio=lista,
        )
        crear_usuario_portal(cliente)
        return AlumnoResponsable.objects.create(
            hijo=hijo,
            cliente=cliente,
            parentesco=parentesco,
            orden_cobro=orden_cobro,
            recibe_notificaciones=recibe_notificaciones,
            puede_ver_saldo=puede_ver_saldo,
            activo=True,
            agregado_por=added_by,
        )


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
