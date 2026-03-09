"""
Generador de Diagramas de Casos de Uso – Cantina Tita
======================================================
Genera un PNG tamaño carta (8.5 × 11 in, 150 dpi) por módulo.
Cada diagrama muestra actores, casos de uso y relaciones principales.
Salida: docs/use_cases/
"""

import os
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Ellipse, Arc, FancyArrow
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES DE ESTILO
# ─────────────────────────────────────────────────────────────────────────────
DPI      = 150
FIG_W    = 8.5   # pulgadas (carta)
FIG_H    = 11.0  # pulgadas (carta)

COLOR_BG         = "#FAFAFA"
COLOR_BOUNDARY   = "#1565C0"
COLOR_BOUNDARY_FILL = "#E3F2FD"
COLOR_UC_FILL    = "#FFFFFF"
COLOR_UC_EDGE    = "#1976D2"
COLOR_UC_TEXT    = "#0D47A1"
COLOR_ACTOR_BODY = "#1565C0"
COLOR_ACTOR_TEXT = "#1A237E"
COLOR_LINE       = "#546E7A"
COLOR_INCLUDE    = "#7B1FA2"
COLOR_EXTEND     = "#E65100"
COLOR_TITLE_BG   = "#1565C0"
COLOR_TITLE_TEXT = "#FFFFFF"
COLOR_SYSTEM_LABEL = "#1565C0"

FONT_FAMILY = "DejaVu Sans"


# ─────────────────────────────────────────────────────────────────────────────
# DEFINICIÓN DE DIAGRAMAS
# ─────────────────────────────────────────────────────────────────────────────
DIAGRAMS = [

    # ── 1. Autenticación y Seguridad ──────────────────────────────────────
    {
        "title":  "Autenticación y Seguridad",
        "system": "Sistema Cantina Tita – Módulo de Acceso",
        "actors": [
            {"name": "Administrador", "side": "left",  "row": 0.5},
            {"name": "Empleado",      "side": "left",  "row": 2.0},
            {"name": "Cliente\nPortal", "side": "right", "row": 0.5},
            {"name": "Sistema",       "side": "right", "row": 2.0},
        ],
        "use_cases": [
            {"id": "UC1",  "label": "Iniciar Sesión",           "col": 0, "row": 0},
            {"id": "UC2",  "label": "Cerrar Sesión",            "col": 1, "row": 0},
            {"id": "UC3",  "label": "Recuperar Contraseña",     "col": 2, "row": 0},
            {"id": "UC4",  "label": "Cambiar Contraseña",       "col": 0, "row": 1},
            {"id": "UC5",  "label": "Gestionar Roles",          "col": 1, "row": 1},
            {"id": "UC6",  "label": "Gestionar Empleados",      "col": 2, "row": 1},
            {"id": "UC7",  "label": "Ver Auditoría",            "col": 0, "row": 2},
            {"id": "UC8",  "label": "Bloquear Cuenta",          "col": 1, "row": 2},
            {"id": "UC9",  "label": "Gestionar Sesiones\nActivas", "col": 2, "row": 2},
        ],
        "associations": [
            ("Administrador", "UC1"), ("Administrador", "UC4"),
            ("Administrador", "UC5"), ("Administrador", "UC6"),
            ("Administrador", "UC7"), ("Administrador", "UC8"),
            ("Administrador", "UC9"),
            ("Empleado", "UC1"), ("Empleado", "UC2"), ("Empleado", "UC4"),
            ("Cliente\nPortal", "UC1"), ("Cliente\nPortal", "UC2"),
            ("Cliente\nPortal", "UC3"),
            ("Sistema", "UC8"), ("Sistema", "UC9"),
        ],
        "includes":  [],
        "extends":   [("UC3", "UC4")],
    },

    # ── 2. Gestión de Clientes e Hijos ────────────────────────────────────
    {
        "title":  "Gestión de Clientes e Hijos",
        "system": "Sistema Cantina Tita – Módulo de Clientes",
        "actors": [
            {"name": "Administrador", "side": "left",  "row": 0.5},
            {"name": "Empleado",      "side": "left",  "row": 2.0},
            {"name": "Padre /\nCliente",     "side": "right", "row": 0.8},
            {"name": "Sistema",       "side": "right", "row": 2.2},
        ],
        "use_cases": [
            {"id": "UC1", "label": "Registrar Cliente",              "col": 0, "row": 0},
            {"id": "UC2", "label": "Consultar Cliente",              "col": 1, "row": 0},
            {"id": "UC3", "label": "Editar Datos de Cliente",        "col": 2, "row": 0},
            {"id": "UC4", "label": "Registrar Hijo /\nEstudiante",   "col": 0, "row": 1},
            {"id": "UC5", "label": "Asignar Grado / Curso",          "col": 1, "row": 1},
            {"id": "UC6", "label": "Ver Datos del Hijo",             "col": 2, "row": 1},
            {"id": "UC7", "label": "Configurar Restricciones\nAlimenticias", "col": 0, "row": 2},
            {"id": "UC8", "label": "Autorizar Saldo Negativo",       "col": 1, "row": 2},
            {"id": "UC9", "label": "Ver Historial de\nAutorizaciones","col": 2, "row": 2},
        ],
        "associations": [
            ("Administrador", "UC1"), ("Administrador", "UC3"),
            ("Administrador", "UC8"), ("Administrador", "UC9"),
            ("Administrador", "UC7"),
            ("Empleado", "UC1"), ("Empleado", "UC2"), ("Empleado", "UC4"),
            ("Empleado", "UC5"),
            ("Padre /\nCliente", "UC2"), ("Padre /\nCliente", "UC6"),
            ("Padre /\nCliente", "UC3"),
            ("Sistema", "UC9"),
        ],
        "includes": [("UC4", "UC5")],
        "extends":  [("UC8", "UC9")],
    },

    # ── 3. Tarjetas y Recargas ────────────────────────────────────────────
    {
        "title":  "Tarjetas y Recargas de Saldo",
        "system": "Sistema Cantina Tita – Módulo de Tarjetas/Recargas",
        "actors": [
            {"name": "Administrador", "side": "left",  "row": 0.3},
            {"name": "Cajero",        "side": "left",  "row": 1.5},
            {"name": "Supervisor",    "side": "left",  "row": 2.7},
            {"name": "Padre /\nCliente", "side": "right", "row": 0.8},
            {"name": "Sistema",       "side": "right", "row": 2.2},
        ],
        "use_cases": [
            {"id": "UC1", "label": "Crear Tarjeta",                 "col": 0, "row": 0},
            {"id": "UC2", "label": "Activar / Bloquear\nTarjeta",   "col": 1, "row": 0},
            {"id": "UC3", "label": "Consultar Saldo",               "col": 2, "row": 0},
            {"id": "UC4", "label": "Recargar Saldo\n(Efectivo)",    "col": 0, "row": 1},
            {"id": "UC5", "label": "Recargar Saldo\n(Transferencia)","col": 1, "row": 1},
            {"id": "UC6", "label": "Aprobar Recarga\n(Supervisor)", "col": 2, "row": 1},
            {"id": "UC7", "label": "Ver Historial\nde Consumos",    "col": 0, "row": 2},
            {"id": "UC8", "label": "Configurar Alerta\nSaldo Bajo", "col": 1, "row": 2},
            {"id": "UC9", "label": "Acreditar Saldo\nAutomático",   "col": 2, "row": 2},
        ],
        "associations": [
            ("Administrador", "UC1"), ("Administrador", "UC2"),
            ("Cajero", "UC4"), ("Cajero", "UC5"), ("Cajero", "UC7"),
            ("Supervisor", "UC6"),
            ("Padre /\nCliente", "UC3"), ("Padre /\nCliente", "UC7"),
            ("Padre /\nCliente", "UC8"),
            ("Sistema", "UC9"),
        ],
        "includes": [("UC4", "UC6"), ("UC5", "UC6")],
        "extends":  [("UC9", "UC2")],
    },

    # ── 4. Punto de Venta ─────────────────────────────────────────────────
    {
        "title":  "Punto de Venta",
        "system": "Sistema Cantina Tita – Módulo de Ventas",
        "actors": [
            {"name": "Cajero",         "side": "left",  "row": 0.5},
            {"name": "Administrador",  "side": "left",  "row": 2.2},
            {"name": "Estudiante /\nPortador", "side": "right", "row": 0.5},
            {"name": "Sistema",        "side": "right", "row": 2.2},
        ],
        "use_cases": [
            {"id": "UC1", "label": "Abrir Caja",               "col": 0, "row": 0},
            {"id": "UC2", "label": "Buscar Producto",          "col": 1, "row": 0},
            {"id": "UC3", "label": "Registrar Venta",          "col": 2, "row": 0},
            {"id": "UC4", "label": "Pago con Tarjeta",         "col": 0, "row": 1},
            {"id": "UC5", "label": "Pago en Efectivo",         "col": 1, "row": 1},
            {"id": "UC6", "label": "Aplicar Descuento",        "col": 2, "row": 1},
            {"id": "UC7", "label": "Emitir Factura / Ticket",  "col": 0, "row": 2},
            {"id": "UC8", "label": "Cerrar Caja",              "col": 1, "row": 2},
            {"id": "UC9", "label": "Ver Historial\nde Ventas", "col": 2, "row": 2},
        ],
        "associations": [
            ("Cajero", "UC1"), ("Cajero", "UC2"), ("Cajero", "UC3"),
            ("Cajero", "UC4"), ("Cajero", "UC5"), ("Cajero", "UC6"),
            ("Cajero", "UC7"), ("Cajero", "UC8"),
            ("Administrador", "UC8"), ("Administrador", "UC9"),
            ("Estudiante /\nPortador", "UC4"),
            ("Sistema", "UC7"), ("Sistema", "UC9"),
        ],
        "includes": [("UC3", "UC2"), ("UC3", "UC7")],
        "extends":  [("UC6", "UC3")],
    },

    # ── 5. Almuerzos ──────────────────────────────────────────────────────
    {
        "title":  "Gestión de Almuerzos",
        "system": "Sistema Cantina Tita – Módulo de Almuerzos",
        "actors": [
            {"name": "Administrador", "side": "left",  "row": 0.5},
            {"name": "Cajero",        "side": "left",  "row": 2.0},
            {"name": "Padre /\nCliente", "side": "right", "row": 0.5},
            {"name": "Sistema",       "side": "right", "row": 2.0},
        ],
        "use_cases": [
            {"id": "UC1", "label": "Crear Plan\nde Almuerzos",      "col": 0, "row": 0},
            {"id": "UC2", "label": "Configurar Menú\ndel Día",      "col": 1, "row": 0},
            {"id": "UC3", "label": "Suscribir Plan\nMensual",       "col": 2, "row": 0},
            {"id": "UC4", "label": "Registrar Asistencia\n/ Consumo","col": 0, "row": 1},
            {"id": "UC5", "label": "Consultar Plan\ndel Hijo",      "col": 1, "row": 1},
            {"id": "UC6", "label": "Ver Menú del Día",              "col": 2, "row": 1},
            {"id": "UC7", "label": "Generar Factura\nMensual",      "col": 0, "row": 2},
            {"id": "UC8", "label": "Ver Historial\nde Asistencia",  "col": 1, "row": 2},
            {"id": "UC9", "label": "Registrar Ausencia\nJustificada","col": 2, "row": 2},
        ],
        "associations": [
            ("Administrador", "UC1"), ("Administrador", "UC2"),
            ("Administrador", "UC7"),
            ("Cajero", "UC4"), ("Cajero", "UC8"), ("Cajero", "UC9"),
            ("Padre /\nCliente", "UC3"), ("Padre /\nCliente", "UC5"),
            ("Padre /\nCliente", "UC6"),
            ("Sistema", "UC7"), ("Sistema", "UC8"),
        ],
        "includes":  [("UC1", "UC2"), ("UC7", "UC4")],
        "extends":   [("UC9", "UC4")],
    },

    # ── 6. Inventario ─────────────────────────────────────────────────────
    {
        "title":  "Control de Inventario",
        "system": "Sistema Cantina Tita – Módulo de Inventario",
        "actors": [
            {"name": "Administrador",  "side": "left",  "row": 0.5},
            {"name": "Encargado de\nInventario", "side": "left", "row": 2.0},
            {"name": "Sistema",        "side": "right", "row": 1.2},
        ],
        "use_cases": [
            {"id": "UC1", "label": "Registrar Producto",           "col": 0, "row": 0},
            {"id": "UC2", "label": "Ver Inventario\nActual",       "col": 1, "row": 0},
            {"id": "UC3", "label": "Actualizar Stock",             "col": 2, "row": 0},
            {"id": "UC4", "label": "Configurar Stock\nMínimo",     "col": 0, "row": 1},
            {"id": "UC5", "label": "Registrar Movimiento\nde Stock","col": 1, "row": 1},
            {"id": "UC6", "label": "Recibir Alerta\nStock Bajo",   "col": 2, "row": 1},
            {"id": "UC7", "label": "Ajustar Inventario",           "col": 0, "row": 2},
            {"id": "UC8", "label": "Ver Historial\nMovimientos",   "col": 1, "row": 2},
            {"id": "UC9", "label": "Categorizar\nProductos",       "col": 2, "row": 2},
        ],
        "associations": [
            ("Administrador", "UC1"), ("Administrador", "UC4"),
            ("Administrador", "UC7"), ("Administrador", "UC9"),
            ("Administrador", "UC2"),
            ("Encargado de\nInventario", "UC2"), ("Encargado de\nInventario", "UC3"),
            ("Encargado de\nInventario", "UC5"), ("Encargado de\nInventario", "UC8"),
            ("Sistema", "UC6"),
        ],
        "includes": [("UC3", "UC5")],
        "extends":  [("UC6", "UC4")],
    },

    # ── 7. Compras y Proveedores ───────────────────────────────────────────
    {
        "title":  "Compras y Proveedores",
        "system": "Sistema Cantina Tita – Módulo de Compras",
        "actors": [
            {"name": "Administrador", "side": "left",  "row": 0.5},
            {"name": "Encargado de\nCompras",  "side": "left",  "row": 2.0},
            {"name": "Proveedor\n(Externo)",   "side": "right", "row": 1.2},
            {"name": "Sistema",       "side": "right", "row": 2.5},
        ],
        "use_cases": [
            {"id": "UC1", "label": "Registrar Proveedor",           "col": 0, "row": 0},
            {"id": "UC2", "label": "Ver Catálogo\nde Proveedores",  "col": 1, "row": 0},
            {"id": "UC3", "label": "Crear Orden\nde Compra",        "col": 2, "row": 0},
            {"id": "UC4", "label": "Registrar Precio\nde Insumo",   "col": 0, "row": 1},
            {"id": "UC5", "label": "Recibir Mercadería",            "col": 1, "row": 1},
            {"id": "UC6", "label": "Registrar Pago\na Proveedor",   "col": 2, "row": 1},
            {"id": "UC7", "label": "Ver Historial\nde Compras",     "col": 0, "row": 2},
            {"id": "UC8", "label": "Ver Cuentas\npor Pagar",        "col": 1, "row": 2},
            {"id": "UC9", "label": "Actualizar\nInventario",        "col": 2, "row": 2},
        ],
        "associations": [
            ("Administrador", "UC1"), ("Administrador", "UC3"),
            ("Administrador", "UC6"), ("Administrador", "UC7"),
            ("Administrador", "UC8"),
            ("Encargado de\nCompras", "UC4"), ("Encargado de\nCompras", "UC5"),
            ("Encargado de\nCompras", "UC7"),
            ("Proveedor\n(Externo)", "UC1"), ("Proveedor\n(Externo)", "UC4"),
            ("Sistema", "UC9"), ("Sistema", "UC8"),
        ],
        "includes": [("UC5", "UC9"), ("UC3", "UC2")],
        "extends":  [("UC6", "UC8")],
    },

    # ── 8. Reportes y Contabilidad ────────────────────────────────────────
    {
        "title":  "Reportes y Contabilidad",
        "system": "Sistema Cantina Tita – Módulo de Reportes/Contabilidad",
        "actors": [
            {"name": "Administrador", "side": "left",  "row": 0.5},
            {"name": "Contador",      "side": "left",  "row": 2.0},
            {"name": "Sistema",       "side": "right", "row": 1.2},
        ],
        "use_cases": [
            {"id": "UC1", "label": "Ver Dashboard\nde KPIs",              "col": 0, "row": 0},
            {"id": "UC2", "label": "Generar Reporte\nde Ventas",          "col": 1, "row": 0},
            {"id": "UC3", "label": "Generar Reporte\nde Inventario",      "col": 2, "row": 0},
            {"id": "UC4", "label": "Ver Cierre\nde Caja",                 "col": 0, "row": 1},
            {"id": "UC5", "label": "Generar Reporte\nde Clientes",        "col": 1, "row": 1},
            {"id": "UC6", "label": "Ver Balance\nde Cuentas",             "col": 2, "row": 1},
            {"id": "UC7", "label": "Exportar Datos\n(CSV / PDF)",         "col": 0, "row": 2},
            {"id": "UC8", "label": "Generar Reporte\nde Compras",         "col": 1, "row": 2},
            {"id": "UC9", "label": "Configurar\nPeriodo de Reporte",      "col": 2, "row": 2},
        ],
        "associations": [
            ("Administrador", "UC1"), ("Administrador", "UC2"),
            ("Administrador", "UC4"), ("Administrador", "UC5"),
            ("Administrador", "UC7"), ("Administrador", "UC9"),
            ("Contador", "UC3"), ("Contador", "UC6"),
            ("Contador", "UC7"), ("Contador", "UC8"), ("Contador", "UC9"),
            ("Sistema", "UC1"), ("Sistema", "UC2"),
        ],
        "includes": [("UC2", "UC9"), ("UC3", "UC9"), ("UC5", "UC9")],
        "extends":  [("UC7", "UC2"), ("UC7", "UC3")],
    },

    # ── 9. Notificaciones ─────────────────────────────────────────────────
    {
        "title":  "Gestión de Notificaciones",
        "system": "Sistema Cantina Tita – Módulo de Notificaciones",
        "actors": [
            {"name": "Administrador", "side": "left",  "row": 0.5},
            {"name": "Sistema",       "side": "left",  "row": 2.0},
            {"name": "Padre /\nCliente", "side": "right", "row": 0.8},
            {"name": "Empleado",      "side": "right", "row": 2.2},
        ],
        "use_cases": [
            {"id": "UC1", "label": "Configurar Umbral\nSaldo Bajo",     "col": 0, "row": 0},
            {"id": "UC2", "label": "Crear Notificación\nManual",        "col": 1, "row": 0},
            {"id": "UC3", "label": "Enviar Notificación\nMasiva",       "col": 2, "row": 0},
            {"id": "UC4", "label": "Enviar Alerta\nSaldo Bajo",         "col": 0, "row": 1},
            {"id": "UC5", "label": "Ver Notificaciones\nRecibidas",     "col": 1, "row": 1},
            {"id": "UC6", "label": "Marcar como Leída",                 "col": 2, "row": 1},
            {"id": "UC7", "label": "Configurar Alertas\nde Sistema",    "col": 0, "row": 2},
            {"id": "UC8", "label": "Ver Historial\nde Notificaciones",  "col": 1, "row": 2},
            {"id": "UC9", "label": "Desactivar\nNotificaciones",        "col": 2, "row": 2},
        ],
        "associations": [
            ("Administrador", "UC1"), ("Administrador", "UC2"),
            ("Administrador", "UC3"), ("Administrador", "UC7"),
            ("Administrador", "UC8"),
            ("Sistema", "UC4"), ("Sistema", "UC8"),
            ("Padre /\nCliente", "UC5"), ("Padre /\nCliente", "UC6"),
            ("Padre /\nCliente", "UC9"),
            ("Empleado", "UC5"), ("Empleado", "UC6"),
        ],
        "includes": [("UC4", "UC1")],
        "extends":  [("UC2", "UC3")],
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIONES DE DIBUJO
# ─────────────────────────────────────────────────────────────────────────────

def draw_actor(ax, x, y, name, color=COLOR_ACTOR_BODY, text_color=COLOR_ACTOR_TEXT):
    """Dibuja una figura de palito (stick figure) con su nombre."""
    r = 0.18   # radio de la cabeza
    # Cabeza
    circle = plt.Circle((x, y + 0.55), r, color=color, zorder=5, linewidth=1.5,
                         fill=True, ec=color)
    ax.add_patch(circle)
    # Cuerpo
    ax.plot([x, x], [y + 0.37, y - 0.05], color=color, lw=2.0, zorder=4)
    # Brazos
    ax.plot([x - 0.28, x + 0.28], [y + 0.15, y + 0.15], color=color, lw=2.0, zorder=4)
    # Pierna izquierda
    ax.plot([x, x - 0.22], [y - 0.05, y - 0.45], color=color, lw=2.0, zorder=4)
    # Pierna derecha
    ax.plot([x, x + 0.22], [y - 0.05, y - 0.45], color=color, lw=2.0, zorder=4)
    # Nombre (debajo)
    ax.text(x, y - 0.65, name, ha="center", va="top",
            fontsize=7.5, fontweight="bold", color=text_color,
            fontfamily=FONT_FAMILY, zorder=6,
            multialignment="center")


def draw_use_case(ax, cx, cy, w, h, label,
                  fill=COLOR_UC_FILL, edge=COLOR_UC_EDGE, text_color=COLOR_UC_TEXT):
    """Dibuja un óvalo (elipse) que representa un caso de uso."""
    ellipse = Ellipse((cx, cy), w, h,
                      facecolor=fill, edgecolor=edge,
                      linewidth=1.8, zorder=3)
    ax.add_patch(ellipse)
    ax.text(cx, cy, label, ha="center", va="center",
            fontsize=7.8, color=text_color,
            fontfamily=FONT_FAMILY, zorder=4,
            multialignment="center",
            wrap=False)


def draw_line(ax, x1, y1, x2, y2, style="-", color=COLOR_LINE, lw=1.0, zorder=2):
    """Dibuja una línea de asociación o relación."""
    ax.plot([x1, x2], [y1, y2], linestyle=style, color=color, lw=lw, zorder=zorder)


def draw_arrow_dashed(ax, x1, y1, x2, y2, label, color):
    """Dibuja flecha punteada para <<include>> o <<extend>>."""
    ax.annotate("",
                xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>",
                                color=color,
                                lw=1.2,
                                linestyle="dashed",
                                connectionstyle="arc3,rad=0.0"),
                zorder=2)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    ax.text(mx, my + 0.06, label, ha="center", va="bottom",
            fontsize=6.5, color=color, style="italic",
            fontfamily=FONT_FAMILY, zorder=3)


# ─────────────────────────────────────────────────────────────────────────────
# MOTOR DE LAYOUT
# ─────────────────────────────────────────────────────────────────────────────

def compute_layout(diagram):
    """
    Calcula las coordenadas en un sistema 0→10 (ancho) × 0→13 (alto).
    Los actores van al margen lateral; los UC se distribuyen dentro
    del límite del sistema.
    """
    # Área útil total: (0,0)→(10,13)
    # Borde del sistema: x ∈ [1.5, 8.5], y ∈ [1.0, 12.0]
    SYS_X0, SYS_X1 = 1.5, 8.5
    SYS_Y0, SYS_Y1 = 1.0, 12.0
    SYS_W = SYS_X1 - SYS_X0
    SYS_H = SYS_Y1 - SYS_Y0

    UC_W = 1.95  # ancho del óvalo UC
    UC_H = 0.80  # alto del óvalo UC

    uc_data = diagram["use_cases"]
    n_cols = max(d["col"] for d in uc_data) + 1
    n_rows = max(d["row"] for d in uc_data) + 1

    # Espaciado entre UCs
    col_step = SYS_W / n_cols
    row_step = SYS_H / (n_rows + 0.5)

    uc_pos = {}
    for uc in uc_data:
        cx = SYS_X0 + col_step * (uc["col"] + 0.5)
        cy = SYS_Y1 - row_step * (uc["row"] + 0.8)
        uc_pos[uc["id"]] = (cx, cy, UC_W, UC_H, uc["label"])

    # Posición de actores
    actor_rows = {}
    for actor in diagram["actors"]:
        actor_rows.setdefault(actor["side"], []).append(actor)

    left_actors  = sorted(actor_rows.get("left",  []), key=lambda a: a["row"])
    right_actors = sorted(actor_rows.get("right", []), key=lambda a: a["row"])

    n_left  = max(len(left_actors), 1)
    n_right = max(len(right_actors), 1)

    actor_pos = {}
    for i, actor in enumerate(left_actors):
        ay = SYS_Y0 + SYS_H * (i + 0.7) / (n_left + 0.3)
        actor_pos[actor["name"]] = (0.70, ay)

    for i, actor in enumerate(right_actors):
        ay = SYS_Y0 + SYS_H * (i + 0.7) / (n_right + 0.3)
        actor_pos[actor["name"]] = (9.30, ay)

    return uc_pos, actor_pos, (SYS_X0, SYS_Y0, SYS_X1, SYS_Y1), (UC_W, UC_H)


def resolve_edge(x_actor, y_actor, cx, cy, uw, uh):
    """
    Devuelve el punto en el borde del óvalo más cercano al actor,
    y el punto junto al actor (centrado en el torso).
    """
    dx = cx - x_actor
    dy = cy - y_actor
    dist = math.hypot(dx, dy) or 1e-9
    # Punto en borde del elipse (aproximación)
    t = math.atan2(dy * (uw / 2), dx * (uh / 2))
    ex = cx - (uw / 2) * math.cos(t)
    ey = cy - (uh / 2) * math.sin(t)
    # Punto próximo al actor (nivel del torso)
    ax_end = x_actor + 0.30 * (1 if dx > 0 else -1)
    ay_end = y_actor + 0.10
    return (ax_end, ay_end), (ex, ey)


# ─────────────────────────────────────────────────────────────────────────────
# GENERADOR PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def generate_diagram(diagram, output_path_png, output_path_jpg):
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=DPI)
    fig.patch.set_facecolor(COLOR_BG)
    ax.set_facecolor(COLOR_BG)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 13)
    ax.set_aspect("equal")
    ax.axis("off")

    uc_pos, actor_pos, sys_bounds, (UC_W, UC_H) = compute_layout(diagram)
    SYS_X0, SYS_Y0, SYS_X1, SYS_Y1 = sys_bounds

    # ── Encabezado ──────────────────────────────────────────────────────
    ax.add_patch(FancyBboxPatch((0, 12.2), 10, 0.78,
                                boxstyle="square,pad=0",
                                facecolor=COLOR_TITLE_BG, edgecolor="none", zorder=6))
    ax.text(5, 12.60, diagram["title"],
            ha="center", va="center",
            fontsize=13, fontweight="bold", color=COLOR_TITLE_TEXT,
            fontfamily=FONT_FAMILY, zorder=7)
    ax.text(5, 12.22, "Sistema Cantina Tita  ·  Diagrama de Casos de Uso  ·  UML",
            ha="center", va="top",
            fontsize=6.5, color="#64B5F6",
            fontfamily=FONT_FAMILY, zorder=7)

    # ── Límite del sistema ───────────────────────────────────────────────
    sys_rect = FancyBboxPatch(
        (SYS_X0, SYS_Y0),
        SYS_X1 - SYS_X0, SYS_Y1 - SYS_Y0,
        boxstyle="round,pad=0.05",
        facecolor=COLOR_BOUNDARY_FILL,
        edgecolor=COLOR_BOUNDARY,
        linewidth=2.0, linestyle="--",
        zorder=1
    )
    ax.add_patch(sys_rect)
    ax.text(SYS_X0 + 0.12, SYS_Y1 - 0.09,
            diagram["system"],
            ha="left", va="top",
            fontsize=7, color=COLOR_SYSTEM_LABEL,
            fontfamily=FONT_FAMILY,
            fontweight="bold", zorder=5)

    # ── Leyenda ──────────────────────────────────────────────────────────
    lx, ly = 0.12, 1.3
    ax.plot([lx, lx + 0.35], [ly, ly], "-", color=COLOR_LINE, lw=1.2)
    ax.text(lx + 0.40, ly, "Asociación", va="center", fontsize=6, color=COLOR_LINE,
            fontfamily=FONT_FAMILY)
    ly -= 0.30
    ax.plot([lx, lx + 0.35], [ly, ly], "--", color=COLOR_INCLUDE, lw=1.2)
    ax.annotate("", xy=(lx + 0.35, ly), xytext=(lx, ly),
                arrowprops=dict(arrowstyle="-|>", color=COLOR_INCLUDE, lw=1.0))
    ax.text(lx + 0.40, ly, "«include»", va="center", fontsize=6, color=COLOR_INCLUDE,
            style="italic", fontfamily=FONT_FAMILY)
    ly -= 0.30
    ax.plot([lx, lx + 0.35], [ly, ly], "--", color=COLOR_EXTEND, lw=1.2)
    ax.annotate("", xy=(lx + 0.35, ly), xytext=(lx, ly),
                arrowprops=dict(arrowstyle="-|>", color=COLOR_EXTEND, lw=1.0))
    ax.text(lx + 0.40, ly, "«extend»", va="center", fontsize=6, color=COLOR_EXTEND,
            style="italic", fontfamily=FONT_FAMILY)

    # ── Actores ──────────────────────────────────────────────────────────
    drawn_actors = {}
    for actor in diagram["actors"]:
        px, py = actor_pos[actor["name"]]
        draw_actor(ax, px, py, actor["name"])
        drawn_actors[actor["name"]] = (px, py)

    # ── Casos de uso ──────────────────────────────────────────────────────
    for uid, (cx, cy, w, h, label) in uc_pos.items():
        draw_use_case(ax, cx, cy, w, h, label)

    # ── Asociaciones actor → UC ───────────────────────────────────────────
    for (actor_name, uc_id) in diagram["associations"]:
        if actor_name not in drawn_actors or uc_id not in uc_pos:
            continue
        ax_x, ay_y = drawn_actors[actor_name]
        cx, cy, w, h, _ = uc_pos[uc_id]
        (ax_end, ay_end), (ex, ey) = resolve_edge(ax_x, ay_y, cx, cy, w, h)
        draw_line(ax, ax_end, ay_end, ex, ey, style="-", color=COLOR_LINE, lw=1.0)

    # ── Relaciones <<include>> ─────────────────────────────────────────────
    for (src_id, tgt_id) in diagram.get("includes", []):
        if src_id not in uc_pos or tgt_id not in uc_pos:
            continue
        sx, sy, sw, sh, _ = uc_pos[src_id]
        tx, ty, tw, th, _ = uc_pos[tgt_id]
        draw_arrow_dashed(ax, sx, sy, tx, ty, "«include»", COLOR_INCLUDE)

    # ── Relaciones <<extend>> ─────────────────────────────────────────────
    for (src_id, tgt_id) in diagram.get("extends", []):
        if src_id not in uc_pos or tgt_id not in uc_pos:
            continue
        sx, sy, sw, sh, _ = uc_pos[src_id]
        tx, ty, tw, th, _ = uc_pos[tgt_id]
        draw_arrow_dashed(ax, sx, sy, tx, ty, "«extend»", COLOR_EXTEND)

    # ── Pie de página ─────────────────────────────────────────────────────
    ax.add_patch(FancyBboxPatch((0, 0), 10, 0.40,
                                boxstyle="square,pad=0",
                                facecolor="#E3F2FD", edgecolor=COLOR_BOUNDARY,
                                linewidth=0.5, zorder=6))
    ax.text(5, 0.20,
            "Cantina Tita  ·  Documento de Análisis  ·  Marzo 2026",
            ha="center", va="center",
            fontsize=6, color=COLOR_SYSTEM_LABEL,
            fontfamily=FONT_FAMILY, zorder=7)

    plt.tight_layout(pad=0.1)

    # Guardar PNG
    fig.savefig(output_path_png, dpi=DPI, bbox_inches="tight",
                facecolor=COLOR_BG, format="png")
    # Guardar JPG (via Pillow para control de calidad)
    from PIL import Image
    import io
    buf = io.BytesIO()
    fig.savefig(buf, dpi=DPI, bbox_inches="tight",
                facecolor=COLOR_BG, format="png")
    buf.seek(0)
    img = Image.open(buf).convert("RGB")
    img.save(output_path_jpg, "JPEG", quality=95)

    plt.close(fig)
    print(f"  ✅ PNG: {output_path_png}")
    print(f"  ✅ JPG: {output_path_jpg}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    base_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs", "use_cases"
    )
    png_dir = os.path.join(base_dir, "png")
    jpg_dir = os.path.join(base_dir, "jpg")
    os.makedirs(png_dir, exist_ok=True)
    os.makedirs(jpg_dir, exist_ok=True)

    print(f"\n🎨 Generando diagramas de casos de uso en '{base_dir}' ...\n")

    slugs = [
        "01_autenticacion_seguridad",
        "02_clientes_hijos",
        "03_tarjetas_recargas",
        "04_punto_de_venta",
        "05_almuerzos",
        "06_inventario",
        "07_compras_proveedores",
        "08_reportes_contabilidad",
        "09_notificaciones",
    ]

    for i, (diag, slug) in enumerate(zip(DIAGRAMS, slugs)):
        print(f"[{i+1}/{len(DIAGRAMS)}] {diag['title']}")
        png_path = os.path.join(png_dir, f"{slug}.png")
        jpg_path = os.path.join(jpg_dir, f"{slug}.jpg")
        generate_diagram(diag, png_path, jpg_path)

    print(f"\n🎉 {len(DIAGRAMS)} diagramas generados.")
    print(f"   PNG → {png_dir}")
    print(f"   JPG → {jpg_dir}\n")


if __name__ == "__main__":
    main()
