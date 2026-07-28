"""
Carga los permisos del sistema en la tabla `permisos`.
Idempotente: usa get_or_create — seguro correrlo varias veces.
"""

from django.core.management.base import BaseCommand

from apps.usuarios.models import Permiso

PERMISOS = [
    # ── Ventas ────────────────────────────────────────────────────────────────
    {"codigo_permiso": "ventas.ver",    "nombre": "Ver ventas",            "modulo": "Ventas"},
    {"codigo_permiso": "ventas.crear",  "nombre": "Registrar venta",       "modulo": "Ventas"},
    {"codigo_permiso": "ventas.anular", "nombre": "Anular venta",          "modulo": "Ventas"},
    # ── Cobros ────────────────────────────────────────────────────────────────
    {"codigo_permiso": "cobros.ver",       "nombre": "Ver cobros / cuenta corriente", "modulo": "Cobros"},
    {"codigo_permiso": "cobros.registrar", "nombre": "Registrar cobro",               "modulo": "Cobros"},
    # ── Clientes ──────────────────────────────────────────────────────────────
    {"codigo_permiso": "clientes.ver",    "nombre": "Ver clientes",   "modulo": "Clientes"},
    {"codigo_permiso": "clientes.crear",  "nombre": "Crear cliente",  "modulo": "Clientes"},
    {"codigo_permiso": "clientes.editar", "nombre": "Editar cliente", "modulo": "Clientes"},
    # ── Tarjetas ──────────────────────────────────────────────────────────────
    {"codigo_permiso": "tarjetas.ver",          "nombre": "Ver tarjetas",                 "modulo": "Tarjetas"},
    {"codigo_permiso": "tarjetas.cargar_saldo", "nombre": "Cargar saldo",                 "modulo": "Tarjetas"},
    {"codigo_permiso": "tarjetas.asignar",      "nombre": "Asignar / desvincular tarjeta","modulo": "Tarjetas"},
    # ── Caja ──────────────────────────────────────────────────────────────────
    {"codigo_permiso": "caja.ver",    "nombre": "Ver caja",    "modulo": "Caja"},
    {"codigo_permiso": "caja.abrir",  "nombre": "Abrir caja",  "modulo": "Caja"},
    {"codigo_permiso": "caja.cerrar", "nombre": "Cerrar caja", "modulo": "Caja"},
    # ── Facturación ───────────────────────────────────────────────────────────
    {"codigo_permiso": "facturacion.ver",    "nombre": "Ver facturación",  "modulo": "Facturación"},
    {"codigo_permiso": "facturacion.emitir", "nombre": "Emitir factura",   "modulo": "Facturación"},
    {"codigo_permiso": "facturacion.anular", "nombre": "Anular factura",   "modulo": "Facturación"},
    # ── Inventario ────────────────────────────────────────────────────────────
    {"codigo_permiso": "inventario.ver",            "nombre": "Ver inventario / stock",      "modulo": "Inventario"},
    {"codigo_permiso": "inventario.ajustar",        "nombre": "Registrar ajuste de stock",   "modulo": "Inventario"},
    {"codigo_permiso": "inventario.aprobar_ajuste", "nombre": "Aprobar ajuste de stock",     "modulo": "Inventario"},
    # ── Productos ─────────────────────────────────────────────────────────────
    {"codigo_permiso": "productos.ver",    "nombre": "Ver productos",    "modulo": "Productos"},
    {"codigo_permiso": "productos.crear",  "nombre": "Crear producto",   "modulo": "Productos"},
    {"codigo_permiso": "productos.editar", "nombre": "Editar producto",  "modulo": "Productos"},
    # ── Compras ───────────────────────────────────────────────────────────────
    {"codigo_permiso": "compras.ver",        "nombre": "Ver compras",              "modulo": "Compras"},
    {"codigo_permiso": "compras.crear_oc",   "nombre": "Crear orden de compra",    "modulo": "Compras"},
    {"codigo_permiso": "compras.aprobar_oc", "nombre": "Aprobar orden de compra",  "modulo": "Compras"},
    # ── Almuerzos ─────────────────────────────────────────────────────────────
    {"codigo_permiso": "almuerzos.ver",               "nombre": "Ver almuerzos",               "modulo": "Almuerzos"},
    {"codigo_permiso": "almuerzos.gestionar_menu",    "nombre": "Gestionar menú diario",       "modulo": "Almuerzos"},
    {"codigo_permiso": "almuerzos.registrar_consumo", "nombre": "Registrar consumo comedor",   "modulo": "Almuerzos"},
    # ── Reportes ──────────────────────────────────────────────────────────────
    {"codigo_permiso": "reportes.ver",      "nombre": "Ver reportes",                 "modulo": "Reportes"},
    {"codigo_permiso": "reportes.exportar", "nombre": "Exportar reportes (CSV/Excel)","modulo": "Reportes"},
    # ── Usuarios ──────────────────────────────────────────────────────────────
    {"codigo_permiso": "usuarios.ver",             "nombre": "Ver usuarios y empleados",    "modulo": "Usuarios"},
    {"codigo_permiso": "usuarios.crear",           "nombre": "Crear usuario",               "modulo": "Usuarios"},
    {"codigo_permiso": "usuarios.editar",          "nombre": "Editar usuario",              "modulo": "Usuarios"},
    {"codigo_permiso": "usuarios.gestionar_roles", "nombre": "Gestionar roles y permisos",  "modulo": "Usuarios"},
    # ── Configuración ─────────────────────────────────────────────────────────
    {"codigo_permiso": "configuracion.ver",    "nombre": "Ver configuración",               "modulo": "Configuración"},
    {"codigo_permiso": "configuracion.editar", "nombre": "Editar configuración del sistema","modulo": "Configuración"},
]


class Command(BaseCommand):
    help = "Carga los permisos del sistema en la tabla permisos (idempotente)."

    def handle(self, *args, **options):
        creados = 0
        for p in PERMISOS:
            _, created = Permiso.objects.get_or_create(
                codigo_permiso=p["codigo_permiso"],
                defaults={"nombre": p["nombre"], "modulo": p["modulo"], "estado": True},
            )
            if created:
                creados += 1

        total = Permiso.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"{creados} permisos creados, {total} en total."
            )
        )
