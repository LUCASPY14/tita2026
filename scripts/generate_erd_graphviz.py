"""
ERD profesional con Graphviz — Cantina Tita v3
Motor 'dot' (Sugiyama): líneas se enrutan ALREDEDOR de las tablas, nunca sobre ellas.
Salida: docs/erd_gv/  9 JPG tamaño carta (11×8.5"), 300 DPI, bien legibles.
"""
import json
import os
import warnings
import subprocess
from pathlib import Path
from PIL import Image

Image.MAX_IMAGE_PIXELS = None   # allow large renders (carta a 300 DPI)

# ── Paths ────────────────────────────────────────────────────────────────────
BASE   = Path(__file__).parent.parent / "cantina_tita"
if not (BASE / "docs" / "schema_dump.json").exists():
    BASE = Path(__file__).parent.parent

SCHEMA = BASE / "docs" / "schema_dump.json"
OUT    = BASE / "docs" / "erd_gv"
OUT.mkdir(parents=True, exist_ok=True)

# Carta landscape a 300 DPI
DPI          = 300
LETTER_W_PX  = round(11.0 * DPI)   # 3300
LETTER_H_PX  = round(8.5  * DPI)   # 2550
MARGIN_PX    = round(0.35 * DPI)   # 105 px


# ── Load schema ───────────────────────────────────────────────────────────────
with open(SCHEMA, encoding="utf-8") as f:
    schema = json.load(f)

VIEWS = {
    "vista_almuerzos_diarios_hijos", "vista_consumos_hijo",
    "vista_cuentas_mensuales_hijos", "vista_resumen_caja_diario",
    "vista_stock_alerta",
}

raw_tables = {k: v for k, v in schema["tables"].items() if k not in VIEWS}
all_fks    = [fk for fk in schema["fks"]
              if fk["table"] not in VIEWS and fk["ref_table"] not in VIEWS]

_fk_cols = {}
for fk in all_fks:
    _fk_cols.setdefault(fk["table"], set()).add(fk["col"])


def col_type_short(t):
    t = t.upper().split("(")[0]
    MAP = {"VARCHAR": "VC", "INTEGER": "INT", "BIGINT": "BINT",
           "SMALLINT": "SINT", "DECIMAL": "DEC", "DATETIME": "DT",
           "TIMESTAMP": "TS", "BOOLEAN": "BOOL", "TEXT": "TXT",
           "FLOAT": "FLT", "DOUBLE": "DBL", "TINYINT": "TINT",
           "CHAR": "CHR", "LONGTEXT": "LTXT", "MEDIUMTEXT": "MTXT",
           "DATE": "DATE", "TIME": "TIME"}
    return MAP.get(t, t[:5])


# ── Graphviz HTML-like label for a table ─────────────────────────────────────
def table_label(tname, show_cols=True):
    cols   = raw_tables.get(tname, [])
    fk_set = _fk_cols.get(tname, set())

    # header row
    header = (
        '<TR><TD BGCOLOR="#1A3A5C" ALIGN="CENTER" COLSPAN="3">'
        f'<FONT COLOR="white" POINT-SIZE="11"><B>{tname}</B></FONT>'
        '</TD></TR>'
    )

    if not show_cols:
        return (
            "<\n<TABLE BORDER='0' CELLBORDER='1' CELLSPACING='0' CELLPADDING='4'>\n"
            f"{header}\n</TABLE>\n>"
        )

    rows = []
    for c in cols:
        cname  = c["col"]
        ctype  = col_type_short(c.get("type", ""))
        is_pk  = c.get("key", "") == "PRI"
        is_fk  = cname in fk_set

        if is_pk:
            bg  = "#FFF3CD"
            tag = '<FONT COLOR="#856404"><B>PK</B></FONT>'
        elif is_fk:
            bg  = "#D4EDFF"
            tag = '<FONT COLOR="#0056B3"><B>FK</B></FONT>'
        else:
            bg  = "#FFFFFF"
            tag = '&#160;&#160;'   # non-breaking spaces (no tag column)

        display = cname if len(cname) <= 24 else cname[:22] + "…"

        rows.append(
            f'<TR>'
            f'<TD BGCOLOR="{bg}" ALIGN="LEFT" WIDTH="28">{tag}</TD>'
            f'<TD BGCOLOR="{bg}" ALIGN="LEFT" WIDTH="180">'
            f'<FONT POINT-SIZE="9">{display}</FONT></TD>'
            f'<TD BGCOLOR="{bg}" ALIGN="LEFT" WIDTH="45">'
            f'<FONT POINT-SIZE="8" COLOR="#555555">{ctype}</FONT></TD>'
            f'</TR>'
        )

    body = "\n".join(rows) if rows else '<TR><TD COLSPAN="3">(sin columnas)</TD></TR>'
    return (
        "<\n<TABLE BORDER='0' CELLBORDER='1' CELLSPACING='0' CELLPADDING='3'>\n"
        f"{header}\n{body}\n</TABLE>\n>"
    )


# ── Save PNG → letter-size JPG via PIL ───────────────────────────────────────
def save_letter_jpg(tmp_png: Path, out_jpg: Path):
    img = Image.open(tmp_png).convert("RGB")

    # Scale to fit inside letter minus margins, maintaining aspect ratio
    max_w = LETTER_W_PX - 2 * MARGIN_PX
    max_h = LETTER_H_PX - 2 * MARGIN_PX
    img.thumbnail((max_w, max_h), Image.LANCZOS)

    # Center on white letter canvas
    canvas = Image.new("RGB", (LETTER_W_PX, LETTER_H_PX), "#FFFFFF")
    paste_x = (LETTER_W_PX - img.width)  // 2
    paste_y = (LETTER_H_PX - img.height) // 2
    canvas.paste(img, (paste_x, paste_y))
    canvas.save(out_jpg, "JPEG", quality=93, dpi=(DPI, DPI))
    tmp_png.unlink()


# ── Core render function ───────────────────────────────────────────────────────
def render_diagram(title, tables_in, out_stem,
                   show_cols=True,
                   engine="dot",
                   rankdir="LR",
                   splines="ortho",
                   nodesep=0.55,
                   ranksep=1.0,
                   concentrate=False):
    """
    Build DOT source, render with Graphviz at 300 DPI, resize to letter in PIL.
    splines='ortho' → L-shaped edges that go AROUND nodes (never through them).
    """
    tables  = {t for t in tables_in if t in raw_tables}
    fks     = [fk for fk in all_fks
               if fk["table"] in tables and fk["ref_table"] in tables]

    edge_map = {}
    for fk in fks:
        if fk["table"] == fk["ref_table"]:
            continue
        key = (fk["table"], fk["ref_table"])
        edge_map.setdefault(key, []).append(f'{fk["col"]}→{fk["ref_col"]}')

    conc = "true" if concentrate else "false"

    lines = [
        "digraph ERD {",
        f'  graph [label="{title}" labelloc="t" fontname="Helvetica-Bold"'
        f'         fontsize="20" bgcolor="#F5F7FA"'
        f'         rankdir="{rankdir}" splines="{splines}"'
        f'         nodesep="{nodesep}" ranksep="{ranksep}"'
        f'         pad="0.5" concentrate="{conc}"];',
        '  node  [shape=plaintext fontname="Helvetica" margin="0.05"];',
        '  edge  [color="#C0392B" arrowhead="open" arrowsize="0.9"'
        '         fontname="Helvetica" fontsize="8" fontcolor="#C0392B"];',
        "",
    ]

    for tname in sorted(tables):
        lbl = table_label(tname, show_cols=show_cols)
        lines.append(f'  "{tname}" [label={lbl}];')

    lines.append("")

    for (src, dst), col_labels in edge_map.items():
        lbl = ", ".join(col_labels[:2])
        if len(col_labels) > 2:
            lbl += f" +{len(col_labels)-2}"
        lines.append(f'  "{src}" -> "{dst}" [label="{lbl}"];')

    lines.append("}")

    dot_src = "\n".join(lines)

    dot_file = OUT / f"{out_stem}.dot"
    dot_file.write_text(dot_src, encoding="utf-8")

    tmp_png  = OUT / f"{out_stem}_tmp.png"
    jpg_file = OUT / f"{out_stem}.jpg"

    result = subprocess.run(
        [engine, "-Tpng", f"-Gdpi={DPI}", str(dot_file), "-o", str(tmp_png)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  ERROR ({engine}): {result.stderr[:400]}")
        return

    save_letter_jpg(tmp_png, jpg_file)
    dot_file.unlink()   # remove intermediate .dot

    size_kb = jpg_file.stat().st_size // 1024
    print(f"  ✓  {jpg_file.name}  ({size_kb} KB, {LETTER_W_PX}×{LETTER_H_PX} px)")


# ═══════════════════════════════════════════════════════════════════════════
#  9 Diagrams
# ═══════════════════════════════════════════════════════════════════════════

def run():
    print(f"Graphviz ERD v3 — {len(raw_tables)} tablas  |  {DPI} DPI  |  {LETTER_W_PX}×{LETTER_H_PX} px\n")

    # ── 1. DER General ─────────────────────────────────────────────────────
    print("1/9  DER General (todas las tablas, solo nombres)...")
    render_diagram(
        title       = "DER General — Cantina Tita (118 tablas)",
        tables_in   = list(raw_tables.keys()),
        out_stem    = "01_der_general",
        show_cols   = False,
        rankdir     = "LR",
        splines     = "polyline",
        nodesep     = 0.30,
        ranksep     = 0.60,
        concentrate = True,
    )

    # ── 2. DER Compras ─────────────────────────────────────────────────────
    print("2/9  DER Compras...")
    render_diagram(
        title     = "DER Compras — Cantina Tita",
        tables_in = [
            "compras", "detalles_compra", "proveedores",
            "notas_credito_proveedor", "detalles_nota_credito_proveedor",
            "pagos_proveedores", "aplicacion_pagos_compras",
            "lotes_producto", "movimientos_stock",
            "documentos_tributarios", "timbrados", "puntos_expedicion",
            "empleados",
        ],
        out_stem  = "02_der_compras",
        nodesep   = 0.55,
        ranksep   = 1.0,
    )

    # ── 3. DER Productos ───────────────────────────────────────────────────
    print("3/9  DER Productos...")
    render_diagram(
        title     = "DER Productos e Inventario — Cantina Tita",
        tables_in = [
            "productos", "categorias", "unidades_medida", "impuestos",
            "stock_unico", "lotes_producto", "movimientos_stock",
            "ajustes_inventario", "detalles_ajuste",
            "alertas_stock", "alertas_vencimiento",
            "costos_historicos", "historico_precios",
            "listas_precios", "precios_por_lista",
            "productos_alergenos", "alergenos",
            "productos_promocion", "promociones", "categorias_promocion",
            "empleados",
        ],
        out_stem  = "03_der_productos",
        nodesep   = 0.50,
        ranksep   = 0.95,
    )

    # ── 4. DER Ventas ──────────────────────────────────────────────────────
    print("4/9  DER Ventas...")
    render_diagram(
        title     = "DER Ventas — Cantina Tita",
        tables_in = [
            "ventas", "detalles_venta", "pagos_venta",
            "aplicacion_pagos_ventas", "notas_credito_cliente",
            "detalles_nota_credito", "promociones_aplicadas",
            "cajas", "cierres_caja", "movimientos_caja",
            "medios_pago", "tarifas_comision",
            "documentos_tributarios", "documento_impuestos",
            "timbrados", "puntos_expedicion", "impuestos",
            "clientes", "empleados",
        ],
        out_stem  = "04_der_ventas",
        nodesep   = 0.55,
        ranksep   = 1.0,
    )

    # ── 5. DER Clientes ────────────────────────────────────────────────────
    print("5/9  DER Clientes...")
    render_diagram(
        title     = "DER Clientes — Cantina Tita",
        tables_in = [
            "clientes", "tipos_cliente", "listas_precios",
            "autorizaciones_saldo_negativo", "logs_autorizaciones",
            "usuarios_web_clientes", "usuarios_portal",
            "tokens_recuperacion", "tokens_verificacion",
            "notificaciones_portal", "preferencias_notificacion",
            "solicitudes_notificacion",
            "emails_enviados", "sms_enviados",
            "plantillas_email", "plantillas_sms",
            "auditoria_usuarios_web", "empleados",
        ],
        out_stem  = "05_der_clientes",
        nodesep   = 0.50,
        ranksep   = 0.95,
    )

    # ── 6. DER Hijos ───────────────────────────────────────────────────────
    print("6/9  DER Hijos...")
    render_diagram(
        title     = "DER Hijos — Cantina Tita",
        tables_in = [
            "hijos", "clientes", "grados",
            "historial_grados_hijos", "restricciones_hijos",
            "tarjetas",
        ],
        out_stem  = "06_der_hijos",
        rankdir   = "TB",
        nodesep   = 0.70,
        ranksep   = 1.10,
    )

    # ── 7. DER Almuerzo ────────────────────────────────────────────────────
    print("7/9  DER Almuerzo...")
    render_diagram(
        title     = "DER Almuerzo — Cantina Tita",
        tables_in = [
            "planes_almuerzo", "tipos_almuerzo",
            "suscripciones_almuerzo", "registros_consumo_almuerzo",
            "cuentas_almuerzo_mensual", "pagos_almuerzo_mensual",
            "pagos_cuentas_almuerzo",
            "hijos", "productos", "empleados", "tarjetas",
        ],
        out_stem  = "07_der_almuerzo",
        nodesep   = 0.60,
        ranksep   = 1.0,
    )

    # ── 8. DER Tarjetas ────────────────────────────────────────────────────
    print("8/9  DER Tarjetas...")
    render_diagram(
        title     = "DER Tarjetas — Cantina Tita",
        tables_in = [
            "tarjetas", "hijos", "clientes",
            "cargas_saldo", "consumos_tarjeta",
            "notificaciones_saldo", "transacciones_online",
            "tarjetas_autorizacion", "logs_autorizaciones",
            "limites_transaccion", "limites_transaccion_roles_autorizadores",
            "roles", "empleados",
        ],
        out_stem  = "08_der_tarjetas",
        nodesep   = 0.55,
        ranksep   = 1.0,
    )

    # ── 9. DER Cuenta Corriente Clientes ───────────────────────────────────
    print("9/9  DER Cuenta Corriente Clientes...")
    render_diagram(
        title     = "DER Cuenta Corriente Clientes — Cantina Tita",
        tables_in = [
            "ventas", "detalles_venta",
            "pagos_venta", "aplicacion_pagos_ventas",
            "notas_credito_cliente", "detalles_nota_credito",
            "autorizaciones_saldo_negativo", "registro_autorizaciones",
            "conciliacion_pagos",
            "cargas_saldo", "consumos_tarjeta", "tarjetas",
            "clientes", "empleados",
        ],
        out_stem  = "09_der_cta_cte_clientes",
        nodesep   = 0.55,
        ranksep   = 1.0,
    )

    print(f"\nListo. Archivos en: {OUT.resolve()}")


if __name__ == "__main__":
    run()
