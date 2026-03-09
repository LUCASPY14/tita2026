"""
Generador de Diagramas Entidad-Relación (ERD) – Cantina Tita
=============================================================
• Lee docs/schema_dump.json (columnas + FKs reales de MySQL)
• Genera 9 diagramas JPG tamaño carta (8.5×11 in, 150 DPI)
• Cada diagrama cubre un módulo; tablas clave se repiten entre diagramas
• Salida: docs/erd_jpg/
"""

import os, io, json, math, textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D
from PIL import Image

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG GLOBAL
# ─────────────────────────────────────────────────────────────────────────────
DPI   = 150
FIG_W = 8.5
FIG_H = 11.0

SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "docs", "schema_dump.json"
)
OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "docs", "erd_jpg"
)

# ── Colores ───────────────────────────────────────────────────────────────────
C_BG          = "#F5F7FA"
C_TITLE_BG    = "#1A237E"
C_TITLE_FG    = "#FFFFFF"
C_FOOTER_BG   = "#E8EAF6"
C_FOOTER_FG   = "#1A237E"

C_TBL_HDR     = "#1565C0"   # cabecera de tabla
C_TBL_HDR_FG  = "#FFFFFF"
C_TBL_HDR_ALT = "#283593"   # cabecera de tabla "compartida" / foránea
C_ROW_PK      = "#E3F2FD"   # fila PK
C_ROW_FK      = "#FFF9C4"   # fila FK
C_ROW_ODD     = "#FFFFFF"
C_ROW_EVEN    = "#F5F5F5"
C_BORDER      = "#90A4AE"
C_BORDER_TBL  = "#1565C0"

C_FK_LINE     = "#1976D2"
C_FK_LINE_EXT = "#7B1FA2"   # FK hacia tabla de otro módulo

PK_ICON  = "[PK] "
FK_ICON  = "[FK] "
UNI_ICON = "[U]  "

FONT     = "DejaVu Sans"
MONO     = "DejaVu Sans Mono"

# ── Tipografía en puntos ──────────────────────────────────────────────────────
FS_TBL_HDR   = 7.0
FS_COL       = 6.2
FS_TYPE      = 5.5

# ── Geometría ERD (coordenadas lógicas 0‥LW × 0‥LH) ─────────────────────────
LW = 10.0
LH = 13.0

TITLE_Y  = 12.25   # centro del encabezado
CONTENT_TOP = 11.90
CONTENT_BOT = 0.55

ROW_H    = 0.225   # alto por fila de columna
HDR_H    = 0.35    # alto de la cabecera de tabla
PADDING  = 0.06    # padding interno (no utilizado directamente)

# ─────────────────────────────────────────────────────────────────────────────
# CARGA DEL ESQUEMA
# ─────────────────────────────────────────────────────────────────────────────

def load_schema():
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    tables = raw["tables"]   # {tbl_name: [{col, type, key, extra}, ...]}
    fks    = raw["fks"]      # [{table, col, ref_table, ref_col}, ...]
    return tables, fks


def fk_index(fks):
    """Construye índice FK → {(tabla_origen, col): (tabla_dest, col)}."""
    idx = {}
    for fk in fks:
        key = (fk["table"], fk["col"])
        idx[key] = (fk["ref_table"], fk["ref_col"])
    return idx


def fks_between(fks, tables_in_diagram):
    """Retorna lista de FKs donde AMBOS extremos están en el conjunto."""
    s = set(tables_in_diagram)
    return [fk for fk in fks
            if fk["table"] in s and fk["ref_table"] in s]


# ─────────────────────────────────────────────────────────────────────────────
# DEFINICIÓN DE GRUPOS  (tablas ordenadas; primeras = zona izquierda/arriba)
# ─────────────────────────────────────────────────────────────────────────────

GROUPS = [
    {
        "title":    "Usuarios y Seguridad",
        "filename": "01_usuarios_seguridad",
        "subtitle": "Módulo de Empleados, Roles, Autenticación y Auditoría",
        "tables": [
            "roles",
            "empleados",
            "perfiles_usuario",
            "sesiones_activas",
            "intentos_login",
            "bloqueos_cuenta",
            "tokens_recuperacion",
            "auditoria_empleados",
            "auditoria_operaciones",
        ],
        # cols importantes a mostrar por tabla (None = auto primeras N)
        "max_cols": 8,
    },
    {
        "title":    "Clientes e Hijos",
        "filename": "02_clientes_hijos",
        "subtitle": "Módulo de Clientes, Estudiantes, Grados y Restricciones",
        "tables": [
            "tipos_cliente",
            "listas_precios",
            "clientes",
            "hijos",
            "grados",
            "historial_grados_hijos",
            "restricciones_hijos",
            "autorizaciones_saldo_negativo",
            "usuarios_web_clientes",
        ],
        "max_cols": 8,
    },
    {
        "title":    "Tarjetas y Recargas de Saldo",
        "filename": "03_tarjetas_recargas",
        "subtitle": "Módulo de Tarjetas, Cargas, Consumos y Notificaciones de Saldo",
        "tables": [
            "hijos",
            "tarjetas",
            "cargas_saldo",
            "consumos_tarjeta",
            "notificaciones_saldo",
            "transacciones_online",
            "tarjetas_autorizacion",
            "limites_transaccion",
            "empleados",
        ],
        "max_cols": 8,
    },
    {
        "title":    "Punto de Venta y Caja",
        "filename": "04_ventas_caja",
        "subtitle": "Módulo de Ventas, Pagos, Cajas y Documentos Tributarios",
        "tables": [
            "medios_pago",
            "clientes",
            "empleados",
            "ventas",
            "detalles_venta",
            "pagos_venta",
            "cajas",
            "cierres_caja",
            "movimientos_caja",
            "documentos_tributarios",
        ],
        "max_cols": 7,
    },
    {
        "title":    "Almuerzos y Suscripciones",
        "filename": "05_almuerzos",
        "subtitle": "Módulo de Planes de Almuerzo, Asistencia y Facturación Mensual",
        "tables": [
            "tipos_almuerzo",
            "hijos",
            "planes_almuerzo",
            "suscripciones_almuerzo",
            "registros_consumo_almuerzo",
            "cuentas_almuerzo_mensual",
            "pagos_almuerzo_mensual",
            "pagos_cuentas_almuerzo",
        ],
        "max_cols": 8,
    },
    {
        "title":    "Inventario y Productos",
        "filename": "06_inventario_productos",
        "subtitle": "Módulo de Productos, Stock, Lotes, Movimientos y Alertas",
        "tables": [
            "categorias",
            "unidades_medida",
            "productos",
            "stock_unico",
            "lotes_producto",
            "movimientos_stock",
            "ajustes_inventario",
            "alertas_stock",
            "alergenos",
            "productos_alergenos",
        ],
        "max_cols": 7,
    },
    {
        "title":    "Compras y Proveedores",
        "filename": "07_compras_proveedores",
        "subtitle": "Módulo de Proveedores, Órdenes de Compra y Pagos",
        "tables": [
            "proveedores",
            "compras",
            "detalles_compra",
            "pagos_proveedores",
            "aplicacion_pagos_compras",
            "notas_credito_proveedor",
            "detalles_nota_credito_proveedor",
            "productos",
            "empleados",
        ],
        "max_cols": 8,
    },
    {
        "title":    "Notificaciones y Comunicaciones",
        "filename": "08_notificaciones",
        "subtitle": "Módulo de Alertas, Notificaciones, Email, SMS y Campañas",
        "tables": [
            "alertas_sistema",
            "alertas_automaticas",
            "alerta_destinatarios",
            "notificaciones_portal",
            "preferencias_notificacion",
            "emails_enviados",
            "sms_enviados",
            "plantillas_email",
            "plantillas_sms",
            "campanas_comunicacion",
        ],
        "max_cols": 7,
    },
    {
        "title":    "Reportes, KPIs y Configuración",
        "filename": "09_reportes_kpi",
        "subtitle": "Módulo de Métricas, Dashboards, Reportes y Configuración del Sistema",
        "tables": [
            "kpi_metricas",
            "valores_kpi",
            "dashboards",
            "plantillas_reporte",
            "configuracion_sistema",
            "datos_empresa",
            "impuestos",
            "documento_impuestos",
            "listas_precios",
            "precios_por_lista",
        ],
        "max_cols": 7,
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT AUTOMÁTICO
# ─────────────────────────────────────────────────────────────────────────────

def table_height(ncols):
    return HDR_H + ncols * ROW_H + 0.08   # +padding inferior


def compute_layout(group_tables, all_cols, max_cols):
    """
    Coloca tablas en una cuadrícula adaptativa dentro del área de contenido.
    Retorna: dict {tbl_name: (x0, y0, w, h)}
    """
    area_w = LW - 0.30
    area_h = CONTENT_TOP - CONTENT_BOT

    n = len(group_tables)
    # Determinar número de columnas de la grilla
    ncols_grid = math.ceil(math.sqrt(n * 1.3))   # ligeramente más ancho que alto
    ncols_grid = max(2, min(ncols_grid, 5))
    nrows_grid = math.ceil(n / ncols_grid)

    cell_w = area_w / ncols_grid
    cell_h = area_h / nrows_grid

    positions = {}
    for idx, tbl in enumerate(group_tables):
        gc = idx % ncols_grid
        gr = idx // ncols_grid
        # Centro de la celda
        cx = 0.15 + gc * cell_w + cell_w / 2
        cy = CONTENT_TOP - gr * cell_h - cell_h / 2

        # Calcular dimensiones reales de la tabla
        cols = all_cols.get(tbl, [])
        ncols_show = min(len(cols), max_cols)
        th = table_height(ncols_show)
        tw = cell_w * 0.90

        x0 = cx - tw / 2
        y0 = cy + th / 2
        positions[tbl] = (x0, y0, tw, th, ncols_show)

    return positions


# ─────────────────────────────────────────────────────────────────────────────
# DIBUJO DE UNA TABLA
# ─────────────────────────────────────────────────────────────────────────────

def is_fk_col(tbl, col, fk_idx):
    return (tbl, col) in fk_idx


def col_icon(col_meta, tbl, fk_idx):
    k = col_meta.get("key", "")
    if k == "PRI":
        return PK_ICON
    if is_fk_col(tbl, col_meta["col"], fk_idx):
        return FK_ICON
    if k == "UNI":
        return UNI_ICON
    return "  "


def abbrev_type(t):
    t = t.lower()
    MAP = {
        "bigint": "BIGINT", "int": "INT", "tinyint(1)": "BOOL",
        "varchar": "VARCHAR", "char": "CHAR", "text": "TEXT",
        "datetime": "DATETIME", "date": "DATE", "time": "TIME",
        "decimal": "DEC", "float": "FLOAT", "double": "DOUBLE",
        "json": "JSON", "longtext": "TEXT", "mediumtext": "TEXT",
        "smallint": "SMALLINT", "bigautofield": "BIGINT AI",
    }
    for k, v in MAP.items():
        if t.startswith(k):
            return v
    # Extraer base
    base = t.split("(")[0].upper()
    return base[:10]


def draw_table(ax, tbl, x0, y0, tw, max_cols, all_cols, fk_idx, is_shared=False):
    """
    Dibuja la caja de la tabla con cabecera y filas de columnas.
    y0 = top-left Y (coordenada superior).
    Retorna dict {col_name: (cx_anchor_left, cy, cx_anchor_right, cy)}.
    """
    cols = all_cols.get(tbl, [])[:max_cols]
    th   = table_height(len(cols))
    hdr_color = C_TBL_HDR_ALT if is_shared else C_TBL_HDR

    # Sombra suave
    ax.add_patch(FancyBboxPatch(
        (x0 + 0.03, y0 - th - 0.03), tw, th,
        boxstyle="round,pad=0.02",
        facecolor="#CCCCCC", edgecolor="none",
        alpha=0.35, zorder=1
    ))

    # Marco exterior
    ax.add_patch(FancyBboxPatch(
        (x0, y0 - th), tw, th,
        boxstyle="square,pad=0",
        facecolor=C_ROW_ODD, edgecolor=C_BORDER_TBL,
        linewidth=1.2, zorder=2
    ))

    # Cabecera
    ax.add_patch(FancyBboxPatch(
        (x0, y0 - HDR_H), tw, HDR_H,
        boxstyle="square,pad=0",
        facecolor=hdr_color, edgecolor=C_BORDER_TBL,
        linewidth=1.2, zorder=3
    ))
    ax.text(x0 + tw / 2, y0 - HDR_H / 2,
            tbl.upper().replace("_", " "),
            ha="center", va="center",
            fontsize=FS_TBL_HDR, fontweight="bold",
            color=C_TBL_HDR_FG, fontfamily=FONT, zorder=4,
            clip_on=True)

    # Filas de columnas
    col_anchors = {}
    for i, col_meta in enumerate(cols):
        col_name = col_meta["col"]
        col_type = abbrev_type(col_meta.get("type", ""))
        key      = col_meta.get("key", "")
        icon     = col_icon(col_meta, tbl, fk_idx)

        row_y_top = y0 - HDR_H - i * ROW_H
        row_y_bot = row_y_top - ROW_H

        # Color de fondo de fila
        if key == "PRI":
            bg = C_ROW_PK
        elif is_fk_col(tbl, col_name, fk_idx):
            bg = C_ROW_FK
        elif i % 2 == 0:
            bg = C_ROW_ODD
        else:
            bg = C_ROW_EVEN

        ax.add_patch(mpatches.Rectangle(
            (x0, row_y_bot), tw, ROW_H,
            facecolor=bg, edgecolor=C_BORDER,
            linewidth=0.4, zorder=2
        ))

        # Icono + nombre columna
        label = f"{icon}{col_name}"
        ax.text(x0 + 0.06, row_y_bot + ROW_H / 2,
                label,
                ha="left", va="center",
                fontsize=FS_COL,
                color="#1A237E" if key == "PRI" else (
                    "#E65100" if is_fk_col(tbl, col_name, fk_idx) else "#212121"),
                fontfamily=MONO if key == "PRI" else FONT,
                fontweight="bold" if key in ("PRI", "UNI") else "normal",
                zorder=4, clip_on=True)

        # Tipo de dato (a la derecha)
        ax.text(x0 + tw - 0.05, row_y_bot + ROW_H / 2,
                col_type,
                ha="right", va="center",
                fontsize=FS_TYPE, color="#546E7A",
                fontfamily=MONO, zorder=4, clip_on=True)

        # Ancho de ancla FK (punto de conexión)
        cy_mid = row_y_bot + ROW_H / 2
        col_anchors[col_name] = (x0, cy_mid, x0 + tw, cy_mid)

    return col_anchors


# ─────────────────────────────────────────────────────────────────────────────
# DIBUJO DE RELACIONES FK
# ─────────────────────────────────────────────────────────────────────────────

def midpoint_avoid(x1, y1, x2, y2, offset=0.25):
    """Calcula puntos de control evitando solapamiento."""
    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy) or 1
    nx = -dy / length * offset
    ny =  dx / length * offset
    return mx + nx, my + ny


def draw_fk_lines(ax, fks_local, tbl_anchors, tbl_positions, external=False):
    """
    Dibuja líneas de FK entre tablas.
    tbl_anchors: {tbl: {col: (lx,ly, rx, ry)}}
    tbl_positions: {tbl: (x0,y0,tw,th,_)}
    """
    color = C_FK_LINE_EXT if external else C_FK_LINE
    drawn = set()

    for fk in fks_local:
        src_tbl  = fk["table"]
        src_col  = fk["col"]
        dst_tbl  = fk["ref_table"]
        dst_col  = fk["ref_col"]

        if src_tbl not in tbl_anchors or dst_tbl not in tbl_anchors:
            continue
        if src_col not in tbl_anchors[src_tbl]:
            continue
        if dst_col not in tbl_anchors[dst_tbl]:
            continue

        pair_key = tuple(sorted([(src_tbl, src_col), (dst_tbl, dst_col)]))
        if pair_key in drawn:
            continue
        drawn.add(pair_key)

        lx1, ly1, rx1, ry1 = tbl_anchors[src_tbl][src_col]
        lx2, ly2, rx2, ry2 = tbl_anchors[dst_tbl][dst_col]

        # Elegir el lado más cercano
        x0s, y0s = tbl_positions[src_tbl][0], tbl_positions[src_tbl][1]
        x0d, y0d = tbl_positions[dst_tbl][0], tbl_positions[dst_tbl][1]

        cx_s = x0s + tbl_positions[src_tbl][2] / 2
        cx_d = x0d + tbl_positions[dst_tbl][2] / 2

        if cx_s < cx_d:
            sx, sy = rx1, ly1
            dx, dy = lx2, ly2
        else:
            sx, sy = lx1, ly1
            dx, dy = rx2, ly2

        # Línea con curvatura suave tipo "elbow"
        mx = (sx + dx) / 2
        ax.annotate("",
                    xy=(dx, dy), xytext=(sx, sy),
                    arrowprops=dict(
                        arrowstyle="-|>",
                        color=color,
                        lw=0.9,
                        connectionstyle=f"arc3,rad=0.0"
                    ),
                    zorder=5)
        # Rombo en el origen (lado N)
        ax.plot(sx, sy, "D", color=color, ms=3, zorder=6)


# ─────────────────────────────────────────────────────────────────────────────
# GENERADOR PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def generate_erd(group, all_cols, all_fks, fk_idx, output_jpg):
    tables_in_group = [t for t in group["tables"] if t in all_cols]
    max_cols        = group.get("max_cols", 8)

    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=DPI)
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)
    ax.set_xlim(0, LW)
    ax.set_ylim(0, LH)
    ax.set_aspect("equal")
    ax.axis("off")

    # ── Encabezado ──────────────────────────────────────────────────────────
    ax.add_patch(FancyBboxPatch((0, 12.1), LW, 0.85,
                                boxstyle="square,pad=0",
                                facecolor=C_TITLE_BG, edgecolor="none", zorder=8))
    ax.text(LW / 2, 12.59, group["title"],
            ha="center", va="center",
            fontsize=13, fontweight="bold", color=C_TITLE_FG,
            fontfamily=FONT, zorder=9)
    ax.text(LW / 2, 12.12, group["subtitle"],
            ha="center", va="top",
            fontsize=6.5, color="#90CAF9",
            fontfamily=FONT, zorder=9)

    # ── Leyenda ──────────────────────────────────────────────────────────────
    lx, ly = 0.12, 0.85
    # PK
    ax.add_patch(mpatches.Rectangle((lx, ly - 0.12), 0.22, 0.18,
                                     facecolor=C_ROW_PK, edgecolor=C_BORDER, lw=0.5))
    ax.text(lx + 0.26, ly - 0.03, "[PK]  Clave primaria",
            va="center", fontsize=5.5, color="#0D47A1", fontfamily=FONT)
    ly -= 0.22
    # FK
    ax.add_patch(mpatches.Rectangle((lx, ly - 0.12), 0.22, 0.18,
                                     facecolor=C_ROW_FK, edgecolor=C_BORDER, lw=0.5))
    ax.text(lx + 0.26, ly - 0.03, "[FK]  Clave foranea",
            va="center", fontsize=5.5, color="#E65100", fontfamily=FONT)
    ly -= 0.22
    # Relación
    ax.annotate("", xy=(lx + 0.40, ly - 0.03), xytext=(lx, ly - 0.03),
                arrowprops=dict(arrowstyle="-|>", color=C_FK_LINE, lw=0.9), zorder=6)
    ax.plot(lx, ly - 0.03, "D", color=C_FK_LINE, ms=3, zorder=7)
    ax.text(lx + 0.44, ly - 0.03, "Relación FK",
            va="center", fontsize=5.5, color=C_FK_LINE, fontfamily=FONT)

    # ── Pie de página ────────────────────────────────────────────────────────
    ax.add_patch(FancyBboxPatch((0, 0), LW, 0.50,
                                boxstyle="square,pad=0",
                                facecolor=C_FOOTER_BG, edgecolor=C_TITLE_BG,
                                linewidth=0.5, zorder=8))
    ax.text(LW / 2, 0.25,
            "Cantina Tita  ·  Diagrama Entidad–Relación  ·  Marzo 2026",
            ha="center", va="center",
            fontsize=6, color=C_FOOTER_FG, fontfamily=FONT, zorder=9)

    # ── Layout de tablas ──────────────────────────────────────────────────────
    positions = compute_layout(tables_in_group, all_cols, max_cols)

    # ── Dibujar tablas ────────────────────────────────────────────────────────
    tbl_anchors = {}   # {tbl: {col: (lx,ly,rx,ry)}}
    for tbl in tables_in_group:
        x0, y0, tw, th, ncols_show = positions[tbl]
        anchors = draw_table(ax, tbl, x0, y0, tw, ncols_show,
                             all_cols, fk_idx, is_shared=False)
        tbl_anchors[tbl] = anchors

    # ── Dibujar relaciones dentro del grupo ───────────────────────────────────
    local_fks = fks_between(all_fks, tables_in_group)
    draw_fk_lines(ax, local_fks, tbl_anchors, positions)

    # ── Subtítulo de tablas incluidas ─────────────────────────────────────────
    n_tbls = len(tables_in_group)
    n_fks_shown = len(local_fks)
    info = f"{n_tbls} tablas  ·  {n_fks_shown} relaciones"
    ax.text(LW - 0.12, 12.55, info,
            ha="right", va="center",
            fontsize=6, color="#90CAF9", fontfamily=FONT, zorder=9)

    plt.tight_layout(pad=0.05)

    # ── Guardar JPG ────────────────────────────────────────────────────────
    buf = io.BytesIO()
    fig.savefig(buf, dpi=DPI, bbox_inches="tight",
                facecolor=C_BG, format="png")
    buf.seek(0)
    img = Image.open(buf).convert("RGB")
    img.save(output_jpg, "JPEG", quality=95)
    plt.close(fig)
    print(f"  ✅  {output_jpg}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"\n[*] Cargando esquema desde {SCHEMA_PATH}")
    all_cols, all_fks = load_schema()
    fk_idx = fk_index(all_fks)

    print(f"   Tablas: {len(all_cols)}  |  FKs: {len(all_fks)}\n")
    print(f"[*] Generando ERDs en '{OUT_DIR}' ...\n")

    for i, group in enumerate(GROUPS):
        print(f"[{i+1}/{len(GROUPS)}] {group['title']}")
        out = os.path.join(OUT_DIR, f"{group['filename']}.jpg")
        generate_erd(group, all_cols, all_fks, fk_idx, out)

    print(f"\n[OK] {len(GROUPS)} diagramas ERD generados en:\n   {OUT_DIR}\n")


if __name__ == "__main__":
    main()
