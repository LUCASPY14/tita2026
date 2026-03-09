"""
Admin configuration for Clientes module - Simple version for testing
Re-exports admin classes from admin.py for backwards compatibility.
"""

from apps.clientes.admin import (  # noqa: F401
    ClientesAdmin,
    TiposClienteAdmin,
    HijosAdmin,
    GradosAdmin,
    HistorialGradosHijosAdmin,
    RestriccionesHijosAdmin,
    AutorizacionesSaldoNegativoAdmin,
    LogsAutorizacionesAdmin,
)
