"""
Utilidades para comparar CI / RUC de clientes del portal de padres.

Los padres cargaron en el formulario de alta su CI (ej. 2222222) o su RUC
(ej. 2222222-2). Para que puedan ingresar con cualquiera de los dos:

- se ignoran puntos y espacios ("2.222.222-2" == "2222222-2");
- CI y RUC del mismo numero se consideran equivalentes
  ("2222222" == "2222222-2");
- dos RUC con distinto digito verificador NO son equivalentes
  ("2222222-2" != "2222222-5").
"""

import re

from django.db.models import Q, Value
from django.db.models.functions import Replace


def limpiar_ci(valor) -> str:
    """Quita puntos y espacios: '2.222.222-2' -> '2222222-2'."""
    return re.sub(r"[\s.]", "", str(valor or "")).upper()


def base_ci(valor) -> str:
    """Numero sin digito verificador: '2222222-2' -> '2222222'."""
    return limpiar_ci(valor).split("-")[0]


def ci_equivalente(a, b) -> bool:
    """True si a y b son el mismo CI/RUC (con o sin digito verificador)."""
    la, lb = limpiar_ci(a), limpiar_ci(b)
    if not la or not lb:
        return False
    if la == lb:
        return True
    if "-" in la and "-" in lb:  # los dos con DV, pero distinto
        return False
    return la.split("-")[0] == lb.split("-")[0]


def buscar_cliente_portal(identificador):
    """
    Devuelve el Cliente (con acceso activo al portal) que corresponde al CI/RUC
    escrito, o None. Primero busca coincidencia exacta; si no hay, prueba el
    "otro" formato (CI <-> RUC). Si hay mas de un candidato, no adivina.
    """
    from apps.clientes.models import Cliente

    limpio = limpiar_ci(identificador)
    base = limpio.split("-")[0]
    if not base:
        return None

    qs = (
        Cliente.objects.select_related("usuario_portal")
        .filter(usuario_portal__isnull=False, usuario_portal__is_active=True)
        .annotate(
            ruc_limpio=Replace(
                Replace("ruc_ci", Value("."), Value("")), Value(" "), Value("")
            )
        )
    )

    # 1) exactamente lo que cargo en el formulario
    exacto = list(qs.filter(ruc_limpio__iexact=limpio)[:2])
    if len(exacto) == 1:
        return exacto[0]
    if len(exacto) > 1:
        return None

    # 2) el otro formato
    if "-" in limpio:  # escribio RUC, cargo CI
        filtro = Q(ruc_limpio=base)
    else:              # escribio CI, cargo RUC
        filtro = Q(ruc_limpio=base) | Q(ruc_limpio__startswith=base + "-")
    candidatos = list(qs.filter(filtro)[:2])
    return candidatos[0] if len(candidatos) == 1 else None
