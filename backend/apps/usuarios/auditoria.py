"""
Helper para registrar operaciones en AuditoriaOperacion.
Uso: from apps.usuarios.auditoria import registrar_auditoria

Nunca lanza excepción — si falla, ignora el error para no romper la operación principal.
"""

from __future__ import annotations


def registrar_auditoria(
    *,
    request=None,
    usuario=None,
    operacion: str,
    tabla: str | None = None,
    id_registro=None,
    descripcion: str | None = None,
    resultado: str = "EXITO",
    ip: str | None = None,
    mensaje_error: str | None = None,
) -> None:
    try:
        from .models import AuditoriaOperacion

        if request is not None:
            if usuario is None:
                u = getattr(request, "user", None)
                usuario = u if (u and getattr(u, "is_authenticated", False)) else None
            if ip is None:
                from common.utils.request_ip import get_client_ip
                ip = get_client_ip(request)

        AuditoriaOperacion.objects.create(
            usuario=usuario,
            operacion=operacion,
            tabla_afectada=tabla,
            id_registro=int(id_registro) if id_registro is not None else None,
            descripcion=descripcion,
            resultado=resultado,
            ip_address=ip,
            mensaje_error=mensaje_error,
        )
    except Exception:
        pass
