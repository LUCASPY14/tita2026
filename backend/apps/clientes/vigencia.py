"""
Vigencia operativa de una tarjeta / alumno.

Se DERIVA en el momento (no hay estados que sincronizar):
- Alumno dado de baja: no opera ni recarga.
- Alumno del último curso: opera hasta el cierre del año lectivo; desde la fecha
  de aviso se le avisa que se acerca el cierre de cuentas.
- Tarjeta con fecha de vencimiento manual (excepción, p. ej. docentes): vence al
  final del día indicado; puede seguir recargándose para no trabar el dinero.
- Cursos normales: sin vencimiento.
"""
from dataclasses import dataclass, replace
from datetime import date

from django.utils import timezone
from rest_framework.exceptions import ValidationError

AVISO_POR_DEFECTO = (10, 1)    # 01/10
CIERRE_POR_DEFECTO = (12, 31)  # 31/12
DIAS_AVISO_VENCIMIENTO = 30


def obtener_calendario(anio, cache=None):
    """Calendario del año: la fila configurada o los valores por defecto (sin guardar)."""
    from .models import CalendarioLectivo

    if cache is not None and anio in cache:
        return cache[anio]
    cal = CalendarioLectivo.objects.filter(anio=anio).first()
    if cal is None:
        cal = CalendarioLectivo(
            anio=anio,
            fecha_aviso_ultimo_curso=date(anio, *AVISO_POR_DEFECTO),
            fecha_cierre_lectivo=date(anio, *CIERRE_POR_DEFECTO),
        )
    if cache is not None:
        cache[anio] = cal
    return cal


@dataclass(frozen=True)
class EstadoVigencia:
    operativa: bool = True
    puede_recargar: bool = True
    motivo: str | None = None          # por qué NO opera
    aviso: str | None = None           # advertencia que no bloquea
    fecha_cierre: date | None = None   # solo alumnos del último curso

    def como_dict(self):
        return {
            "operativa": self.operativa,
            "puede_recargar": self.puede_recargar,
            "motivo": self.motivo,
            "aviso": self.aviso,
            "fecha_cierre": self.fecha_cierre.isoformat() if self.fecha_cierre else None,
        }


def _fmt(d):
    return d.strftime("%d/%m/%Y")


def evaluar_hijo(hijo, hoy=None, cache=None):
    hoy = hoy or timezone.localdate()
    if not hijo.activo:
        return EstadoVigencia(
            operativa=False, puede_recargar=False,
            motivo="El alumno está dado de baja. Su saldo se resuelve en el cierre de cuentas.",
        )
    grado = hijo.grado
    if grado is None or not grado.es_ultimo:
        return EstadoVigencia()

    cal = obtener_calendario(hoy.year, cache)
    cierre = cal.fecha_cierre_lectivo
    if hoy > cierre:
        return EstadoVigencia(
            operativa=False, puede_recargar=False, fecha_cierre=cierre,
            motivo=(
                f"Cierre del año lectivo ({_fmt(cierre)}): la tarjeta del último curso ya no opera. "
                "Resolvé el saldo en el cierre de cuentas."
            ),
        )
    aviso = None
    if hoy >= cal.fecha_aviso_ultimo_curso:
        aviso = (
            f"Último curso: la tarjeta opera hasta el {_fmt(cierre)}. "
            "Resolvé saldos y deudas antes del cierre de cuentas."
        )
    return EstadoVigencia(aviso=aviso, fecha_cierre=cierre)


def evaluar_tarjeta(tarjeta, hoy=None, cache=None):
    hoy = hoy or timezone.localdate()
    estado = evaluar_hijo(tarjeta.hijo, hoy, cache) if tarjeta.hijo_id else EstadoVigencia()
    if not estado.operativa:
        return estado

    vencimiento = tarjeta.fecha_vencimiento
    if vencimiento:
        if hoy > vencimiento:
            texto = f"Tarjeta vencida el {_fmt(vencimiento)}. Renovala en administración."
            return replace(estado, operativa=False, motivo=texto, aviso=texto)
        dias = (vencimiento - hoy).days
        if dias <= DIAS_AVISO_VENCIMIENTO:
            texto = f"La tarjeta vence el {_fmt(vencimiento)} (en {dias} días)."
            return replace(estado, aviso=f"{estado.aviso} {texto}" if estado.aviso else texto)
    return estado


# ── Validaciones (lanzan 400 con el mensaje para mostrar en pantalla) ────────

def exigir_tarjeta_operativa(tarjeta, hoy=None):
    estado = evaluar_tarjeta(tarjeta, hoy)
    if not estado.operativa:
        raise ValidationError({"error": estado.motivo})


def exigir_hijo_operativo(hijo, hoy=None):
    estado = evaluar_hijo(hijo, hoy)
    if not estado.operativa:
        raise ValidationError({"error": estado.motivo})


def motivo_no_recarga_tarjeta(tarjeta, hoy=None):
    """Texto si la tarjeta NO puede recibir recargas (baja/cierre), o None."""
    estado = evaluar_tarjeta(tarjeta, hoy)
    return None if estado.puede_recargar else estado.motivo


def motivo_no_recarga_hijo(hijo, hoy=None):
    estado = evaluar_hijo(hijo, hoy)
    return None if estado.puede_recargar else estado.motivo
