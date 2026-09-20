"""
Promoción anual de grados.

Flujo: el ADMIN genera un borrador (una línea por alumno con la decisión sugerida),
lo ajusta (repite, cambia, egresa, no continúa) y lo aplica UNA sola vez por año,
en una transacción. Cada cambio deja historial con su motivo.

Reglas acordadas:
- Solo se aplica después del cierre del año lectivo (por defecto 31/12): antes, los
  alumnos de 2° AÑO pasarían a 3° AÑO y la baja automática los daría de baja como
  egresados. El borrador se puede preparar antes.
- Un alumno del último curso marcado REPITE/CAMBIA en el borrador no recibe la baja
  automática; si ya fue dado de baja, la promoción lo reincorpora.
- Egresar o no continuar da de baja al alumno y abre su cierre de cuentas.
- No hay "deshacer": los casos puntuales se corrigen editando al alumno (ADMIN), que
  también queda en el historial.
"""
import re
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.usuarios.auditoria import registrar_auditoria
from common.permissions import exigir_rol

from .models import Grado, Hijo, HistorialGrado, PromocionAlumno, PromocionAnual
from .vigencia import obtener_calendario

D = PromocionAlumno.Decision
DIAS_BAJA_AUTOMATICA = 30  # mismo margen que dar_baja_alumnos_ultimo_curso


# ── Sugerencia del grado siguiente ───────────────────────────────────────────

def sugerir_siguiente(grado, por_nombre):
    """(estado, destino, detalle) para un grado, deducido del nombre.

    estado: OK (destino sugerido), EGRESA (último curso), ELEGIR (9° Grado → 1° AÑO:
    el bachillerato se elige por alumno) o AMBIGUO (no hay equivalente exacto).
    """
    if grado.es_ultimo:
        return "EGRESA", None, "Último curso: egresa."
    nombre = grado.nombre

    m = re.match(r"^(\d+)° Grado ([A-Z])$", nombre)
    if m:
        numero, sufijo = int(m.group(1)), m.group(2)
        if numero == 9:
            return "ELEGIR", None, "Pasa a 1° AÑO: el bachillerato se elige por alumno."
        destino = por_nombre.get(f"{numero + 1}° Grado {sufijo}")
        if destino:
            return "OK", destino, ""
        return "AMBIGUO", None, f"No existe {numero + 1}° Grado {sufijo}."

    m = re.match(r"^(\d)° AÑO (.+)$", nombre)
    if m:
        destino = por_nombre.get(f"{int(m.group(1)) + 1}° AÑO {m.group(2)}")
        return ("OK", destino, "") if destino else ("AMBIGUO", None, "Sin equivalente en el año siguiente.")

    m = re.match(r"^(Jardin|Pre-escolar) ([ET])$", nombre)
    if m:
        base, sufijo = m.groups()
        siguiente = f"Pre-escolar {sufijo}" if base == "Jardin" else f"1° Grado {sufijo}"
        destino = por_nombre.get(siguiente)
        return ("OK", destino, "") if destino else ("AMBIGUO", None, f"No existe {siguiente}.")

    if nombre == "Maternal":
        destino = por_nombre.get("Pre-Jardin")
        return ("OK", destino, "") if destino else ("AMBIGUO", None, "No existe Pre-Jardin.")
    return "AMBIGUO", None, "Sin regla para este grado."


def sugerir_siguientes(aplicar=True):
    """Completa `siguiente` de los grados que no lo tienen y tienen una sugerencia clara.
    Nunca pisa un grado ya configurado."""
    grados = list(Grado.objects.all().order_by("nivel", "orden", "nombre"))
    por_nombre = {g.nombre: g for g in grados}
    asignados, pendientes, ya = [], [], 0
    for g in grados:
        if g.es_ultimo:
            continue
        if g.siguiente_id:
            ya += 1
            continue
        estado, destino, detalle = sugerir_siguiente(g, por_nombre)
        if estado == "OK":
            asignados.append({"grado": g.nombre, "siguiente": destino.nombre})
            if aplicar:
                g.siguiente = destino
                g.save(update_fields=["siguiente"])
        else:
            pendientes.append({"grado": g.nombre, "motivo": detalle})
    return {"asignados": asignados, "pendientes": pendientes, "ya_configurados": ya, "aplicado": aplicar}


# ── Borrador ─────────────────────────────────────────────────────────────────

def _candidatos(anio):
    """Alumnos que entran a la promoción: activos con grado y los egresados que la baja
    automática ya dio de baja (por si hay que reincorporar a quien repite)."""
    cierre = obtener_calendario(anio).fecha_cierre_lectivo
    activos = Hijo.objects.filter(activo=True, grado__isnull=False)
    egresados_dados_de_baja = Hijo.objects.filter(
        activo=False, grado__es_ultimo=True,
        fecha_baja__date__gt=cierre,
        fecha_baja__date__lte=cierre + timedelta(days=DIAS_BAJA_AUTOMATICA),
    )
    return (activos | egresados_dados_de_baja).select_related("grado", "grado__siguiente").distinct()


def _decision_por_defecto(hijo):
    if hijo.grado.es_ultimo or not hijo.activo:
        return D.EGRESA, None
    return D.PROMUEVE, hijo.grado.siguiente


def refrescar(promocion):
    """Agrega al borrador los alumnos que faltan. No toca las decisiones ya tomadas."""
    if promocion.estado != PromocionAnual.Estado.BORRADOR:
        raise ValidationError({"error": "La promoción ya fue aplicada."})
    existentes = set(promocion.lineas.values_list("hijo_id", flat=True))
    nuevas = []
    for hijo in _candidatos(promocion.anio):
        if hijo.pk in existentes:
            continue
        decision, destino = _decision_por_defecto(hijo)
        nuevas.append(PromocionAlumno(
            promocion=promocion, hijo=hijo, grado_origen=hijo.grado, decision=decision, grado_destino=destino,
        ))
    PromocionAlumno.objects.bulk_create(nuevas)
    return len(nuevas)


def generar_borrador(anio, usuario):
    """Crea el borrador del año (o lo refresca si ya existe)."""
    exigir_rol(usuario, {"ADMIN"}, "Solo un administrador prepara la promoción anual.")
    promocion, creada = PromocionAnual.objects.get_or_create(anio=anio, defaults={"creada_por": usuario})
    agregados = refrescar(promocion)
    if creada:
        registrar_auditoria(
            usuario=usuario, operacion="PROMOCION_GENERAR", tabla="clientes_promocionanual",
            id_registro=promocion.pk, descripcion=f"Borrador {anio}: {agregados} alumnos",
        )
    return promocion, creada


def _validar_decision(linea, decision, destino):
    """Devuelve el destino normalizado o lanza ValidationError."""
    origen = linea.grado_origen
    if decision not in D.values:
        raise ValidationError({"decision": "Decisión inválida."})
    if origen is None:
        raise ValidationError({"error": "El alumno no tiene grado de origen."})
    inactivo = not linea.hijo.activo

    if decision == D.PROMUEVE:
        if origen.es_ultimo:
            raise ValidationError({"decision": "Un alumno del último curso egresa, repite o cambia."})
        if inactivo:
            raise ValidationError({"decision": "Un alumno dado de baja solo puede repetir o egresar."})
        destino = destino or origen.siguiente
        if destino is None:
            raise ValidationError({"grado_destino": "Falta el grado de destino."})
        if destino.pk == origen.pk:
            raise ValidationError({"grado_destino": "Para quedarse en el mismo grado usá «Repite»."})
        return destino
    if decision == D.CAMBIA:
        if inactivo:
            raise ValidationError({"decision": "Un alumno dado de baja solo puede repetir o egresar."})
        if destino is None:
            raise ValidationError({"grado_destino": "Elegí el grado de destino."})
        if destino.pk == origen.pk:
            raise ValidationError({"grado_destino": "Para quedarse en el mismo grado usá «Repite»."})
        return destino
    if decision == D.REPITE:
        return origen
    if decision == D.EGRESA:
        if not origen.es_ultimo:
            raise ValidationError({"decision": "Solo el último curso egresa; usá «No continúa»."})
        return None
    if inactivo:  # NO_CONTINUA
        raise ValidationError({"decision": "El alumno ya está dado de baja."})
    return None


def actualizar_linea(linea, decision, grado_destino=None, motivo=""):
    if linea.promocion.estado != PromocionAnual.Estado.BORRADOR:
        raise ValidationError({"error": "La promoción ya fue aplicada."})
    destino = _validar_decision(linea, decision, grado_destino)
    linea.decision = decision
    linea.grado_destino = destino
    linea.motivo = motivo or ""
    linea.save(update_fields=["decision", "grado_destino", "motivo"])
    return linea


def actualizar_grupo(promocion, grado_origen, decision, grado_destino=None):
    """Aplica la misma decisión a todos los alumnos de un grado de origen. Los que no
    admiten esa decisión (por ejemplo, ya dados de baja) se omiten y se informan."""
    actualizadas, omitidas = 0, []
    for linea in promocion.lineas.filter(grado_origen=grado_origen).select_related("hijo", "grado_origen"):
        try:
            actualizar_linea(linea, decision, grado_destino)
            actualizadas += 1
        except ValidationError as exc:
            omitidas.append({"hijo": linea.hijo.nombre_completo, "motivo": _texto(exc)})
    return {"actualizadas": actualizadas, "omitidas": omitidas}


def _texto(exc):
    detalle = exc.detail
    if isinstance(detalle, dict):
        detalle = next(iter(detalle.values()))
    if isinstance(detalle, (list, tuple)):
        detalle = detalle[0]
    return str(detalle)


# ── Requisitos y aplicación ──────────────────────────────────────────────────

def problema_de_linea(linea):
    if linea.decision in (D.PROMUEVE, D.CAMBIA) and linea.grado_destino_id is None:
        return "Falta el grado de destino."
    return ""


def requisitos(promocion):
    """Qué falta para poder aplicar: errores (bloquean), avisos y fecha habilitada."""
    cierre = obtener_calendario(promocion.anio).fecha_cierre_lectivo
    habilitada_desde = cierre + timedelta(days=1)
    hoy = timezone.localdate()
    errores, avisos = [], []

    sin_grado = list(Hijo.objects.filter(activo=True, grado__isnull=True))
    if sin_grado:
        nombres = ", ".join(h.nombre_completo for h in sin_grado[:8])
        mas = f" y {len(sin_grado) - 8} más" if len(sin_grado) > 8 else ""
        errores.append(
            f"{len(sin_grado)} alumno(s) activos sin grado: {nombres}{mas}. Asignales un grado o dalos de baja."
        )

    lineas = list(promocion.lineas.select_related("hijo", "grado_origen"))
    if not lineas:
        errores.append("El borrador no tiene alumnos.")
    sin_destino = [x for x in lineas if problema_de_linea(x)]
    if sin_destino:
        nombres = ", ".join(x.hijo.nombre_completo for x in sin_destino[:8])
        mas = f" y {len(sin_destino) - 8} más" if len(sin_destino) > 8 else ""
        errores.append(f"{len(sin_destino)} alumno(s) sin grado de destino: {nombres}{mas}.")

    puede_por_fecha = hoy >= habilitada_desde
    if not puede_por_fecha:
        avisos.append(
            f"Todavía no cerró el año lectivo: podés preparar el borrador, pero solo se aplica desde el "
            f"{habilitada_desde.strftime('%d/%m/%Y')}."
        )
    if promocion.estado == PromocionAnual.Estado.APLICADA:
        errores.append("La promoción ya fue aplicada.")

    conteo = {d: 0 for d in D.values}
    for x in lineas:
        conteo[x.decision] += 1
    return {
        "errores": errores,
        "avisos": avisos,
        "habilitada_desde": habilitada_desde.isoformat(),
        "puede_aplicar": not errores and puede_por_fecha,
        "resumen": conteo,
    }


_MOTIVO_HISTORIAL = {
    D.PROMUEVE: HistorialGrado.Motivo.PROMOCION,
    D.REPITE: HistorialGrado.Motivo.REPITE,
    D.CAMBIA: HistorialGrado.Motivo.CAMBIO,
    D.EGRESA: HistorialGrado.Motivo.EGRESO,
    D.NO_CONTINUA: HistorialGrado.Motivo.EGRESO,
}


def _aplicar_linea(promocion, linea, usuario, ahora):
    from apps.cierre_cuentas.services import CierreCuentaService

    hijo = Hijo.objects.select_for_update().get(pk=linea.hijo_id)
    origen = linea.grado_origen.nombre if linea.grado_origen else None
    registro = dict(
        hijo=hijo, grado_anterior=origen, anio_escolar=promocion.anio + 1,
        motivo=_MOTIVO_HISTORIAL[linea.decision], promocion=promocion,
        usuario_registro=getattr(usuario, "email", None), observaciones=linea.motivo or None,
    )
    if linea.decision in (D.PROMUEVE, D.CAMBIA, D.REPITE):
        if not hijo.activo:  # reincorporación de quien repite el último curso
            hijo.activo = True
            hijo.fecha_baja = None
        hijo.grado = linea.grado_destino
        hijo.save(update_fields=["grado", "activo", "fecha_baja"])
        HistorialGrado.objects.create(grado_nuevo=linea.grado_destino.nombre, **registro)
        return
    # EGRESA / NO_CONTINUA: baja y expediente de cierre de cuentas
    if hijo.activo:
        hijo.activo = False
        hijo.fecha_baja = ahora
        hijo.save(update_fields=["activo", "fecha_baja"])
    HistorialGrado.objects.create(
        grado_nuevo="Egresado" if linea.decision == D.EGRESA else "No continúa", **registro,
    )
    CierreCuentaService.abrir(hijo, promocion.anio, usuario)


def aplicar(promocion, usuario):
    """Aplica la promoción, una sola vez, en una transacción. Devuelve el resumen."""
    exigir_rol(usuario, {"ADMIN"}, "Solo un administrador aplica la promoción anual.")
    with transaction.atomic():
        promocion = PromocionAnual.objects.select_for_update().get(pk=promocion.pk)
        if promocion.estado == PromocionAnual.Estado.APLICADA:
            raise ValidationError({"error": "La promoción de este año ya fue aplicada."})
        req = requisitos(promocion)
        if req["errores"]:
            raise ValidationError({"error": " ".join(req["errores"]), "errores": req["errores"]})
        if not req["puede_aplicar"]:
            desde = obtener_calendario(promocion.anio).fecha_cierre_lectivo + timedelta(days=1)
            raise ValidationError({
                "error": (
                    f"La promoción se aplica desde el {desde.strftime('%d/%m/%Y')}, "
                    "después del cierre del año lectivo."
                ),
            })

        ahora = timezone.now()
        lineas = list(promocion.lineas.select_related("grado_origen", "grado_destino"))
        for linea in lineas:
            _aplicar_linea(promocion, linea, usuario, ahora)
        promocion.estado = PromocionAnual.Estado.APLICADA
        promocion.aplicada_por = usuario
        promocion.fecha_aplicacion = ahora
        promocion.save(update_fields=["estado", "aplicada_por", "fecha_aplicacion"])

    registrar_auditoria(
        usuario=usuario, operacion="PROMOCION_APLICAR", tabla="clientes_promocionanual",
        id_registro=promocion.pk,
        descripcion=f"Promoción {promocion.anio}: " + ", ".join(f"{k}={v}" for k, v in req["resumen"].items() if v),
    )
    return req["resumen"]
