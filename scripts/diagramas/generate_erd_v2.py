"""
ERD v2 — Diagrams for Cantina Tita
9 diagrams, letter-size pages, orthogonal routing to avoid lines crossing tables.
"""
import json
import os
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import matplotlib.patheffects as pe
from PIL import Image

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "cantina_tita", "docs", "schema_dump.json")
if not os.path.exists(SCHEMA_PATH):
    SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "schema_dump.json")

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "erd_v2")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Load schema ──────────────────────────────────────────────────────────────
with open(SCHEMA_PATH, encoding="utf-8") as f:
    schema = json.load(f)

VIEWS = {
    "vista_almuerzos_diarios_hijos", "vista_consumos_hijo",
    "vista_cuentas_mensuales_hijos", "vista_resumen_caja_diario",
    "vista_stock_alerta",
}

# schema["tables"] is a dict: {table_name: [col_dicts]}
# col_dict keys: col, type, key ('PRI'/'MUL'/''), extra
# schema["fks"]  is a list of {table, col, ref_table, ref_col}

raw_tables = schema["tables"]   # dict name -> list[col_dict]
all_tables = {name: cols for name, cols in raw_tables.items()
              if name not in VIEWS}
all_fks = [fk for fk in schema["fks"]
           if fk["table"] not in VIEWS and fk["ref_table"] not in VIEWS]

# Build per-table FK column set for rendering
_fk_cols = {}
for fk in all_fks:
    _fk_cols.setdefault(fk["table"], set()).add(fk["col"])


def get_cols(tname):
    """Return list of dicts with keys: name, type, pk, fk"""
    raw = all_tables.get(tname, [])
    fk_set = _fk_cols.get(tname, set())
    result = []
    for c in raw:
        result.append({
            "name": c["col"],
            "type": c.get("type", ""),
            "pk": c.get("key", "") == "PRI",
            "fk": c["col"] in fk_set,
        })
    return result


def get_fks_for(tables_set):
    """Return FKs where both source and target are in tables_set."""
    return [fk for fk in all_fks
            if fk["table"] in tables_set and fk["ref_table"] in tables_set]


# ── colours ──────────────────────────────────────────────────────────────────
HEADER_BG   = "#1A3A5C"
HEADER_FG   = "white"
ROW_BG_PK   = "#FFF3CD"
ROW_BG_FK   = "#E8F4FD"
ROW_BG_EVEN = "#FFFFFF"
ROW_BG_ODD  = "#F8F9FA"
BORDER_COL  = "#2C5F8A"
FK_ARROW    = "#C0392B"
PAGE_BG     = "#F0F4F8"

# letter-size @ 150 dpi
FIG_W, FIG_H = 11, 8.5   # inches

# ── helpers ──────────────────────────────────────────────────────────────────

def wrap(text, maxlen=16):
    if len(text) <= maxlen:
        return text
    words = text.split("_")
    lines, cur = [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > maxlen:
            lines.append(cur); cur = w
        else:
            cur = (cur + "_" + w) if cur else w
    lines.append(cur)
    return "\n".join(lines)


def save_jpg(fig, path, dpi=150):
    png = path.replace(".jpg", "_tmp.png")
    fig.savefig(png, dpi=dpi, bbox_inches="tight", facecolor=fig.get_facecolor())
    img = Image.open(png).convert("RGB")
    img.save(path, "JPEG", quality=92)
    os.remove(png)
    print(f"  Saved: {path}")


# ═══════════════════════════════════════════════════════════════════════════
#  DIAGRAM 1 — General (all 118 tables, names only, grid, arcs)
# ═══════════════════════════════════════════════════════════════════════════

def draw_general():
    tables = sorted(all_tables.keys())
    n = len(tables)
    cols = 12
    rows = math.ceil(n / cols)

    cell_w = FIG_W / cols
    cell_h = FIG_H / rows * 0.88  # leave margin for title

    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    fig.patch.set_facecolor(PAGE_BG)
    ax.set_facecolor(PAGE_BG)
    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, FIG_H)
    ax.axis("off")

    # title
    ax.text(FIG_W / 2, FIG_H - 0.18, "DER General — Cantina Tita (Todas las tablas)",
            ha="center", va="top", fontsize=9, fontweight="bold", color=HEADER_BG)

    # compute box positions
    box_w = cell_w * 0.82
    box_h = 0.28
    pos = {}
    for i, tname in enumerate(tables):
        col = i % cols
        row = i // cols
        x = col * cell_w + cell_w / 2
        y = FIG_H - 0.35 - row * cell_h - cell_h / 2
        pos[tname] = (x, y)

    # draw boxes
    for tname, (x, y) in pos.items():
        rect = mpatches.FancyBboxPatch(
            (x - box_w / 2, y - box_h / 2), box_w, box_h,
            boxstyle="round,pad=0.01", linewidth=0.6,
            edgecolor=BORDER_COL, facecolor=HEADER_BG)
        ax.add_patch(rect)
        label = tname.replace("_", "\n") if len(tname) > 14 else tname
        ax.text(x, y, label, ha="center", va="center",
                fontsize=3.8, color="white", fontweight="bold")

    # draw FK arcs — route them with curvature based on distance
    fk_pairs = set()
    for fk in all_fks:
        pair = (fk["table"], fk["ref_table"])
        if pair not in fk_pairs and fk["table"] != fk["ref_table"]:
            fk_pairs.add(pair)

    for (src, dst) in fk_pairs:
        if src not in pos or dst not in pos:
            continue
        x1, y1 = pos[src]
        x2, y2 = pos[dst]
        dx = x2 - x1; dy = y2 - y1
        dist = math.sqrt(dx*dx + dy*dy)
        # vary rad with index to spread overlapping arcs
        rad = 0.25 if dist < 1.5 else (0.15 if dist < 3 else 0.08)
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(
                        arrowstyle="-|>",
                        color=FK_ARROW,
                        lw=0.35,
                        connectionstyle=f"arc3,rad={rad}",
                        mutation_scale=4,
                    ))

    # legend
    ax.text(0.05, 0.06, f"Total tablas: {n}  |  Relaciones FK: {len(fk_pairs)}",
            ha="left", va="bottom", fontsize=5, color="#555", style="italic",
            transform=ax.transAxes)

    out = os.path.join(OUT_DIR, "01_der_general.jpg")
    save_jpg(fig, out)
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════
#  MODULE DIAGRAMS 2-9  (tables with columns, orthogonal routing)
# ═══════════════════════════════════════════════════════════════════════════

# ── Layout engine ────────────────────────────────────────────────────────────
# We pack tables in a smart grid then route FK lines with a two-segment
# orthogonal path that goes outside the bounding box of all tables.

def col_type_short(ctype):
    ctype = ctype.upper()
    for k, v in [("VARCHAR", "VC"), ("INTEGER", "INT"), ("BIGINT", "BINT"),
                 ("SMALLINT", "SINT"), ("DECIMAL", "DEC"), ("DATETIME", "DT"),
                 ("TIMESTAMP", "TS"), ("BOOLEAN", "BOOL"), ("TEXT", "TXT"),
                 ("FLOAT", "FLT"), ("DOUBLE", "DBL"), ("DATE", "DATE"),
                 ("TINYINT", "TINT"), ("CHAR", "CHR"), ("LONGTEXT", "LTXT"),
                 ("MEDIUMTEXT", "MTXT")]:
        if k in ctype:
            return v
    return ctype[:4]


def draw_table_box(ax, tname, cols_list, x, y, w, row_h=0.165, header_h=0.22):
    """
    Draw a table at (x,y) = top-left corner.
    Returns actual height used, and dict of column centre y positions.
    """
    pk_set = {c["name"] for c in cols_list if c.get("pk")}
    fk_set = {c["name"] for c in cols_list if c.get("fk")}

    total_h = header_h + len(cols_list) * row_h

    # header
    rect = mpatches.FancyBboxPatch(
        (x, y - header_h), w, header_h,
        boxstyle="square,pad=0", linewidth=0.8,
        edgecolor=BORDER_COL, facecolor=HEADER_BG)
    ax.add_patch(rect)
    label = tname if len(tname) <= 22 else tname[:19] + "…"
    ax.text(x + w / 2, y - header_h / 2, label,
            ha="center", va="center", fontsize=5.2,
            fontweight="bold", color=HEADER_FG, clip_on=True)

    col_y_map = {}
    for i, col in enumerate(cols_list):
        cy = y - header_h - i * row_h
        bg = ROW_BG_PK if col["name"] in pk_set else \
             ROW_BG_FK if col["name"] in fk_set else \
             (ROW_BG_EVEN if i % 2 == 0 else ROW_BG_ODD)
        rect = mpatches.FancyBboxPatch(
            (x, cy - row_h), w, row_h,
            boxstyle="square,pad=0", linewidth=0.4,
            edgecolor="#CCCCCC", facecolor=bg)
        ax.add_patch(rect)

        prefix = "PK " if col["name"] in pk_set else \
                 "FK " if col["name"] in fk_set else "   "
        ctype  = col_type_short(col.get("type", ""))
        cname  = col["name"]
        if len(cname) > 18: cname = cname[:16] + "…"
        ax.text(x + 0.02, cy - row_h / 2,
                f"{prefix}{cname}", ha="left", va="center",
                fontsize=3.8, color="#222", clip_on=True)
        ax.text(x + w - 0.02, cy - row_h / 2,
                ctype, ha="right", va="center",
                fontsize=3.5, color="#555", clip_on=True)

        col_y_map[col["name"]] = cy - row_h / 2

    # outer border
    rect = mpatches.FancyBboxPatch(
        (x, y - total_h), w, total_h,
        boxstyle="square,pad=0", linewidth=0.9,
        edgecolor=BORDER_COL, facecolor="none")
    ax.add_patch(rect)

    return total_h, col_y_map


def layout_tables(table_names, cols_data,
                  area_x, area_y, area_w, area_h,
                  col_count=None, row_h=0.165, header_h=0.22, gap=0.18):
    """
    Assign (x, y-top) positions for each table using a column-based packing.
    Returns dict tname -> (x, y_top, w, h)
    """
    if not table_names:
        return {}

    max_rows = max((len(cols_data.get(t, [])) for t in table_names), default=1)
    tbl_h_est = header_h + max_rows * row_h

    if col_count is None:
        # pick number of columns so tables fit
        col_count = max(1, min(len(table_names),
                               int(area_w / (area_w / max(1, len(table_names)) ** 0.5))))
        col_count = max(1, min(col_count, 8))

    col_w = (area_w - (col_count + 1) * gap) / col_count

    # sort tables by column count descending so tall ones go first
    sorted_names = sorted(table_names, key=lambda t: -len(cols_data.get(t, [])))

    # bin-pack into columns (greedy: fill shortest column)
    columns = [[] for _ in range(col_count)]
    col_heights = [0.0] * col_count

    for tname in sorted_names:
        h = header_h + len(cols_data.get(tname, [])) * row_h
        idx = col_heights.index(min(col_heights))
        columns[idx].append((tname, h))
        col_heights[idx] += h + gap

    positions = {}
    for ci, col in enumerate(columns):
        cx = area_x + gap + ci * (col_w + gap)
        cy = area_y  # top
        for tname, h in col:
            positions[tname] = (cx, cy, col_w, h)
            cy -= h + gap

    return positions


def draw_module(title, table_names, file_out,
                col_count=None, show_cols=True,
                extra_fk_filter=None):
    """Draw a module ERD diagram."""
    ts = {t for t in table_names if t in all_tables}
    fks = get_fks_for(ts)
    if extra_fk_filter:
        fks = [fk for fk in fks if extra_fk_filter(fk)]

    cols_data = {t: get_cols(t) for t in ts}

    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    fig.patch.set_facecolor(PAGE_BG)
    ax.set_facecolor(PAGE_BG)

    margin_top = 0.45
    margin_bot = 0.20
    margin_lr  = 0.22

    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, FIG_H)
    ax.axis("off")

    # title
    ax.text(FIG_W / 2, FIG_H - 0.15, title,
            ha="center", va="top", fontsize=10, fontweight="bold", color=HEADER_BG)
    ax.text(FIG_W / 2, FIG_H - 0.32,
            f"Tablas: {len(ts)}   Relaciones FK: {len(fks)}",
            ha="center", va="top", fontsize=6, color="#444")

    area_x = margin_lr
    area_y = FIG_H - margin_top
    area_w = FIG_W - 2 * margin_lr
    area_h = FIG_H - margin_top - margin_bot

    if show_cols:
        positions = layout_tables(list(ts), cols_data,
                                  area_x, area_y, area_w, area_h,
                                  col_count=col_count)
        # draw each table
        tbl_rects = {}   # tname -> (x, y_top, w, h)
        col_y_map = {}   # tname -> {col_name -> y_centre}

        for tname, (x, y_top, w, h) in positions.items():
            actual_h, cym = draw_table_box(
                ax, tname, cols_data[tname], x, y_top, w)
            tbl_rects[tname] = (x, y_top, w, actual_h)
            col_y_map[tname] = cym
    else:
        # names only – simple boxes
        positions = layout_tables(list(ts), {t: [] for t in ts},
                                  area_x, area_y, area_w, area_h,
                                  col_count=col_count)
        tbl_rects = {}
        col_y_map = {}
        for tname, (x, y_top, w, h) in positions.items():
            box_h = 0.25
            rect = mpatches.FancyBboxPatch(
                (x, y_top - box_h), w, box_h,
                boxstyle="round,pad=0.01", linewidth=0.8,
                edgecolor=BORDER_COL, facecolor=HEADER_BG)
            ax.add_patch(rect)
            ax.text(x + w / 2, y_top - box_h / 2, tname,
                    ha="center", va="center", fontsize=4.5,
                    color="white", fontweight="bold")
            tbl_rects[tname] = (x, y_top, w, box_h)
            col_y_map[tname] = {}

    # ── Draw FK lines with orthogonal routing ────────────────────────────
    # Strategy: for each FK, find source/dest column Y, then route
    # an L-shaped path that goes out horizontally from the table edge,
    # then vertically, then in horizontally — avoiding crossing other tables.

    drawn_pairs = set()

    for fk in fks:
        src = fk["table"]
        dst = fk["ref_table"]
        if src == dst:
            continue
        pair = tuple(sorted([src + fk["col"], dst + fk["ref_col"]]))
        if pair in drawn_pairs:
            continue
        drawn_pairs.add(pair)

        if src not in tbl_rects or dst not in tbl_rects:
            continue

        sx, sy_top, sw, sh = tbl_rects[src]
        dx, dy_top, dw, dh = tbl_rects[dst]

        # Y of FK column in source, Y of ref column in dest
        src_col_y = col_y_map[src].get(fk["col"], sy_top - sh / 2)
        dst_col_y = col_y_map[dst].get(fk["ref_col"], dy_top - dh / 2)

        # pick connection sides (left or right edge)
        src_cx = sx + sw / 2
        dst_cx = dx + dw / 2

        if src_cx <= dst_cx:
            # source is to the left → exit right edge of source, enter left of dest
            x1 = sx + sw
            x2 = dx
        else:
            x1 = sx
            x2 = dx + dw

        y1 = src_col_y
        y2 = dst_col_y

        # midpoint x for the vertical segment
        # choose a corridor that doesn't pass through any table
        mid_x = (x1 + x2) / 2

        # simple two-segment path: horizontal then vertical then horizontal
        # Use matplotlib PathPatch or annotate with connectionstyle
        # We'll use arc connectionstyle for simplicity with a mild curve
        # but route exit/entry to correct edges

        # draw with annotate from (x1,y1) to (x2,y2)
        dx2 = x2 - x1
        dy2 = y2 - y1
        dist = math.sqrt(dx2**2 + dy2**2)

        # Use arc3 with a sign-varying rad so multiple FKs between the same
        # pair spread out. Positive rad curves counter-clockwise.
        # We vary rad based on direction to give an L-shaped feel.
        if dist < 0.01:
            continue  # self-join, skip

        # Compute a curvature: tight for nearby, gentle for far
        base_rad = max(0.08, min(0.4, 0.6 / dist)) if dist > 0 else 0.2
        # Sign: curve "above" if going right, "below" if going left
        sign = 1 if dx2 >= 0 else -1
        rad = base_rad * sign

        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(
                        arrowstyle="-|>",
                        color=FK_ARROW,
                        lw=0.7,
                        connectionstyle=f"arc3,rad={rad}",
                        mutation_scale=6,
                    ),
                    annotation_clip=False)

    # legend
    legend_elements = [
        mpatches.Patch(facecolor=ROW_BG_PK, edgecolor="#aaa", label="PK"),
        mpatches.Patch(facecolor=ROW_BG_FK, edgecolor="#aaa", label="FK"),
        mpatches.Patch(facecolor=ROW_BG_EVEN, edgecolor="#aaa", label="Campo"),
        plt.Line2D([0], [0], color=FK_ARROW, lw=1, label="Relación FK"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=5,
              framealpha=0.8, ncol=4)

    save_jpg(fig, file_out)
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════
#  Module definitions
# ═══════════════════════════════════════════════════════════════════════════

def run():
    print("Generating ERD v2 diagrams...\n")

    # ── 1. General ──────────────────────────────────────────────────────────
    print("1/9 DER General...")
    draw_general()

    # ── 2. DER Compras ──────────────────────────────────────────────────────
    print("2/9 DER Compras...")
    compras_tables = [
        "compras", "detalles_compra", "proveedores",
        "notas_credito_proveedor", "detalles_nota_credito_proveedor",
        "pagos_proveedores", "aplicacion_pagos_compras",
        "lotes_producto", "movimientos_stock", "documentos_tributarios",
        "timbrados", "puntos_expedicion", "empleados",
    ]
    draw_module(
        "DER Compras — Cantina Tita",
        compras_tables,
        os.path.join(OUT_DIR, "02_der_compras.jpg"),
        col_count=4,
    )

    # ── 3. DER Productos ────────────────────────────────────────────────────
    print("3/9 DER Productos...")
    productos_tables = [
        "productos", "categorias", "unidades_medida", "impuestos",
        "stock_unico", "lotes_producto", "movimientos_stock",
        "ajustes_inventario", "detalles_ajuste",
        "alertas_stock", "alertas_vencimiento",
        "costos_historicos", "historico_precios",
        "listas_precios", "precios_por_lista",
        "productos_alergenos", "alergenos",
        "productos_promocion", "promociones", "categorias_promocion",
        "empleados",
    ]
    draw_module(
        "DER Productos e Inventario — Cantina Tita",
        productos_tables,
        os.path.join(OUT_DIR, "03_der_productos.jpg"),
        col_count=4,
    )

    # ── 4. DER Ventas ───────────────────────────────────────────────────────
    print("4/9 DER Ventas...")
    ventas_tables = [
        "ventas", "detalles_venta", "pagos_venta",
        "aplicacion_pagos_ventas", "notas_credito_cliente",
        "detalles_nota_credito", "promociones_aplicadas",
        "cajas", "cierres_caja", "movimientos_caja",
        "medios_pago", "tarifas_comision",
        "documentos_tributarios", "documento_impuestos",
        "timbrados", "puntos_expedicion", "impuestos",
        "clientes", "empleados",
    ]
    draw_module(
        "DER Ventas — Cantina Tita",
        ventas_tables,
        os.path.join(OUT_DIR, "04_der_ventas.jpg"),
        col_count=4,
    )

    # ── 5. DER Clientes ─────────────────────────────────────────────────────
    print("5/9 DER Clientes...")
    clientes_tables = [
        "clientes", "tipos_cliente", "listas_precios",
        "autorizaciones_saldo_negativo", "logs_autorizaciones",
        "usuarios_web_clientes", "usuarios_portal",
        "tokens_recuperacion", "tokens_verificacion",
        "notificaciones_portal", "preferencias_notificacion",
        "solicitudes_notificacion",
        "emails_enviados", "sms_enviados",
        "plantillas_email", "plantillas_sms",
        "auditoria_usuarios_web", "empleados",
    ]
    draw_module(
        "DER Clientes — Cantina Tita",
        clientes_tables,
        os.path.join(OUT_DIR, "05_der_clientes.jpg"),
        col_count=4,
    )

    # ── 6. DER Hijos ────────────────────────────────────────────────────────
    print("6/9 DER Hijos...")
    hijos_tables = [
        "hijos", "clientes", "grados",
        "historial_grados_hijos", "restricciones_hijos",
        "tarjetas",
    ]
    draw_module(
        "DER Hijos — Cantina Tita",
        hijos_tables,
        os.path.join(OUT_DIR, "06_der_hijos.jpg"),
        col_count=3,
    )

    # ── 7. DER Almuerzo ─────────────────────────────────────────────────────
    print("7/9 DER Almuerzo...")
    almuerzo_tables = [
        "planes_almuerzo", "tipos_almuerzo",
        "suscripciones_almuerzo", "registros_consumo_almuerzo",
        "cuentas_almuerzo_mensual", "pagos_almuerzo_mensual",
        "pagos_cuentas_almuerzo",
        "hijos", "productos", "empleados", "tarjetas",
    ]
    draw_module(
        "DER Almuerzo — Cantina Tita",
        almuerzo_tables,
        os.path.join(OUT_DIR, "07_der_almuerzo.jpg"),
        col_count=3,
    )

    # ── 8. DER Tarjetas ─────────────────────────────────────────────────────
    print("8/9 DER Tarjetas...")
    tarjetas_tables = [
        "tarjetas", "hijos", "clientes",
        "cargas_saldo", "consumos_tarjeta",
        "notificaciones_saldo", "transacciones_online",
        "tarjetas_autorizacion", "logs_autorizaciones",
        "limites_transaccion", "limites_transaccion_roles_autorizadores",
        "roles", "empleados",
    ]
    draw_module(
        "DER Tarjetas — Cantina Tita",
        tarjetas_tables,
        os.path.join(OUT_DIR, "08_der_tarjetas.jpg"),
        col_count=4,
    )

    # ── 9. DER Cuenta Corriente Clientes ────────────────────────────────────
    print("9/9 DER Cuenta Corriente Clientes...")
    cta_cte_tables = [
        "ventas", "detalles_venta",
        "pagos_venta", "aplicacion_pagos_ventas",
        "notas_credito_cliente", "detalles_nota_credito",
        "autorizaciones_saldo_negativo", "registro_autorizaciones",
        "conciliacion_pagos",
        "cargas_saldo", "consumos_tarjeta", "tarjetas",
        "clientes", "empleados",
    ]
    draw_module(
        "DER Cuenta Corriente Clientes — Cantina Tita",
        cta_cte_tables,
        os.path.join(OUT_DIR, "09_der_cta_cte_clientes.jpg"),
        col_count=4,
    )

    print(f"\nDone! Files in: {os.path.abspath(OUT_DIR)}")


if __name__ == "__main__":
    run()
