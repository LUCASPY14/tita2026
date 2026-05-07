#!/usr/bin/env python3
"""
Script maestro: genera TODOS los diagramas ER del proyecto dbcantinatita.

Formatos generados:
  - draw.io (.drawio)       → abrir con draw.io desktop o app.diagrams.net
  - ERD Editor (.vuerd.json)→ abrir con extensión dineug.vuerd-vscode en VS Code

Bloques:
  DER completo, clientes, core/tarjetas, ventas, compras, productos,
  usuarios, contabilidad, almuerzos, notificaciones, api/integraciones

Uso:
  D:/tita2026/cantina_tita/venv/Scripts/python.exe scripts/generate_all_der.py

Salida:
  docs/der/
    completo.drawio
    bloque_clientes.drawio
    bloque_ventas.drawio
    ... (todos los bloques)
    vuerd/
      completo.vuerd.json
      bloque_clientes.vuerd.json
      ... (todos los bloques)
"""

import json
import os
import re

import MySQLdb

# ── Conexión ──────────────────────────────────────────────────────────────────
DB_CFG = dict(
    host="localhost", user="root",
    passwd="L01G05S33Vice.42", db="dbcantinatita", charset="utf8mb4"
)

EXCLUDE_TABLES = {
    "auth_group", "auth_group_permissions", "auth_permission",
    "auth_user", "auth_user_groups", "auth_user_user_permissions",
    "django_admin_log", "django_celery_beat_clockedschedule",
    "django_celery_beat_crontabschedule", "django_celery_beat_intervalschedule",
    "django_celery_beat_periodictask", "django_celery_beat_periodictasks",
    "django_celery_beat_solarschedule", "django_content_type",
    "django_migrations", "django_session",
}

# ── Módulos ───────────────────────────────────────────────────────────────────
TABLE_MODULE = {
    # clientes
    "clientes": "clientes", "hijos": "clientes", "tipos_cliente": "clientes",
    "listas_precios": "clientes", "restricciones_hijos": "clientes",
    "historial_grados_hijos": "clientes", "grados": "clientes",
    "autorizaciones_saldo_negativo": "clientes",
    # core / tarjetas
    "tarjetas": "core", "cargas_saldo": "core", "medios_pago": "core",
    "consumos_tarjeta": "core", "tarjetas_autorizacion": "core",
    "transacciones_online": "core", "limites_transaccion": "core",
    "limites_transaccion_roles_autorizadores": "core",
    "registro_autorizaciones": "core", "logs_autorizaciones": "core",
    "tarifas_comision": "core", "auditoria_comisiones": "core",
    "conciliacion_pagos": "core", "configuracion_sistema": "core",
    "cache_configuracion": "core", "datos_empresa": "core",
    # ventas
    "ventas": "ventas", "detalles_venta": "ventas",
    "documentos_tributarios": "ventas", "documento_impuestos": "ventas",
    "pagos_venta": "ventas", "notas_credito_cliente": "ventas",
    "detalles_nota_credito": "ventas", "aplicacion_pagos_ventas": "ventas",
    "promociones": "ventas", "categorias_promocion": "ventas",
    "productos_promocion": "ventas", "promociones_aplicadas": "ventas",
    "impuestos": "ventas", "timbrados": "ventas", "puntos_expedicion": "ventas",
    # compras
    "compras": "compras", "detalles_compra": "compras",
    "proveedores": "compras", "pagos_proveedores": "compras",
    "notas_credito_proveedor": "compras",
    "detalles_nota_credito_proveedor": "compras",
    "aplicacion_pagos_compras": "compras",
    # productos
    "productos": "productos", "categorias": "productos",
    "unidades_medida": "productos", "stock_unico": "productos",
    "movimientos_stock": "productos", "lotes_producto": "productos",
    "alertas_stock": "productos", "alertas_vencimiento": "productos",
    "costos_historicos": "productos", "ajustes_inventario": "productos",
    "detalles_ajuste": "productos", "historico_precios": "productos",
    "precios_por_lista": "productos", "alergenos": "productos",
    "productos_alergenos": "productos",
    # usuarios
    "empleados": "usuarios", "roles": "usuarios", "permisos": "usuarios",
    "roles_permisos": "usuarios", "perfiles_usuario": "usuarios",
    "sesiones_activas": "usuarios", "renovaciones_sesion": "usuarios",
    "autenticacion_2fa": "usuarios", "intentos_2fa": "usuarios",
    "intentos_login": "usuarios", "bloqueos_cuenta": "usuarios",
    "tokens_recuperacion": "usuarios", "tokens_verificacion": "usuarios",
    "auditoria_empleados": "usuarios", "auditoria_operaciones": "usuarios",
    "patrones_acceso": "usuarios", "usuarios_portal": "usuarios",
    "usuarios_web_clientes": "usuarios", "auditoria_usuarios_web": "usuarios",
    "historial_acceso": "usuarios",
    # contabilidad
    "cajas": "contabilidad", "movimientos_caja": "contabilidad",
    "cierres_caja": "contabilidad",
    # almuerzos
    "planes_almuerzo": "almuerzos", "suscripciones_almuerzo": "almuerzos",
    "tipos_almuerzo": "almuerzos", "registros_consumo_almuerzo": "almuerzos",
    "cuentas_almuerzo_mensual": "almuerzos",
    "pagos_almuerzo_mensual": "almuerzos", "pagos_cuentas_almuerzo": "almuerzos",
    # notificaciones
    "notificaciones_portal": "notificaciones",
    "notificaciones_saldo": "notificaciones",
    "solicitudes_notificacion": "notificaciones",
    "preferencias_notificacion": "notificaciones",
    "emails_enviados": "notificaciones", "sms_enviados": "notificaciones",
    "plantillas_email": "notificaciones", "plantillas_sms": "notificaciones",
    "campanas_comunicacion": "notificaciones",
    "alertas_sistema": "notificaciones", "alertas_automaticas": "notificaciones",
    "historial_alertas": "notificaciones", "anomalias_detectadas": "notificaciones",
    "alerta_destinatarios": "notificaciones",
    # api / integraciones
    "proveedores_api": "api", "endpoints_api": "api",
    "credenciales_api": "api", "logs_llamadas_api": "api",
    "webhook_endpoints": "api", "logs_webhooks": "api",
    # reportes / kpi
    "plantillas_reporte": "reportes", "kpi_metricas": "reportes",
    "valores_kpi": "reportes", "dashboards": "reportes",
    "plantillas_tarea": "reportes", "ejecuciones_tarea": "reportes",
    "destinatarios_tarea": "reportes", "restricciones_horarias": "reportes",
}

# colores (fill/stroke para draw.io | color para vuerd)
MODULE_STYLE = {
    #  módulo        fill_hex    stroke_hex   vuerd_color
    "clientes":     ("#d5e8d4", "#82b366",  "#82b366"),
    "core":         ("#dae8fc", "#6c8ebf",  "#6c8ebf"),
    "ventas":       ("#e1d5e7", "#9673a6",  "#9673a6"),
    "compras":      ("#fff2cc", "#d6b656",  "#d6b656"),
    "productos":    ("#f8cecc", "#b85450",  "#b85450"),
    "usuarios":     ("#d5f0d5", "#2d7600",  "#2d7600"),
    "contabilidad": ("#ffe6cc", "#d79b00",  "#d79b00"),
    "almuerzos":    ("#cce5ff", "#006EAF",  "#006EAF"),
    "notificaciones":("#f5f5f5","#666666",  "#666666"),
    "api":          ("#e6f3ff", "#336699",  "#336699"),
    "reportes":     ("#fff0e6", "#cc6600",  "#cc6600"),
    "default":      ("#f5f5f5", "#666666",  "#666666"),
}

# ── Bloques definidos ─────────────────────────────────────────────────────────
BLOCKS = {
    "completo":         {"module": None,            "per_row": 7,  "canvas": 12000},
    "clientes":         {"module": "clientes",      "per_row": 4,  "canvas": 4000},
    "core_tarjetas":    {"module": "core",          "per_row": 4,  "canvas": 5000},
    "ventas":           {"module": "ventas",        "per_row": 5,  "canvas": 6000},
    "compras":          {"module": "compras",       "per_row": 4,  "canvas": 4000},
    "productos":        {"module": "productos",     "per_row": 4,  "canvas": 5000},
    "usuarios":         {"module": "usuarios",      "per_row": 5,  "canvas": 6000},
    "contabilidad":     {"module": "contabilidad",  "per_row": 3,  "canvas": 3000},
    "almuerzos":        {"module": "almuerzos",     "per_row": 4,  "canvas": 4000},
    "notificaciones":   {"module": "notificaciones","per_row": 4,  "canvas": 5000},
    "api_integraciones":{"module": "api",           "per_row": 3,  "canvas": 3000},
}

# ═════════════════════════════════════════════════════════════════════════════
# EXTRACCIÓN MySQL
# ═════════════════════════════════════════════════════════════════════════════

def load_schema():
    conn = MySQLdb.connect(**DB_CFG)
    cur = conn.cursor()

    cur.execute(
        "SELECT table_name, column_name, column_type, column_key, "
        "is_nullable, extra "
        "FROM information_schema.columns "
        "WHERE table_schema=%s ORDER BY table_name, ordinal_position",
        (DB_CFG["db"],),
    )
    schema = {}
    for table, col, ctype, key, nullable, extra in cur.fetchall():
        if table in EXCLUDE_TABLES:
            continue
        schema.setdefault(table, []).append({
            "col": col, "type": ctype, "key": key,
            "nullable": nullable == "YES",
            "extra": extra, "is_pk": key == "PRI", "is_fk": False,
        })

    cur.execute(
        "SELECT table_name, column_name, referenced_table_name, "
        "referenced_column_name "
        "FROM information_schema.key_column_usage "
        "WHERE table_schema=%s AND referenced_table_name IS NOT NULL "
        "ORDER BY table_name, column_name",
        (DB_CFG["db"],),
    )
    fks, fk_set = [], set()
    for t, c, rt, rc in cur.fetchall():
        if t in EXCLUDE_TABLES or rt in EXCLUDE_TABLES:
            continue
        fks.append({"table": t, "col": c, "ref_table": rt, "ref_col": rc})
        fk_set.add((t, c))

    cur.close()
    conn.close()

    for tbl, cols in schema.items():
        for c in cols:
            c["is_fk"] = (tbl, c["col"]) in fk_set

    return schema, fks


def tables_for_block(module, schema, all_fks):
    """Tablas propias del módulo + tablas externas referenciadas (1 nivel)."""
    if module is None:
        return sorted(schema.keys())
    core = {t for t in schema if TABLE_MODULE.get(t) == module}
    referenced = {
        fk["ref_table"] for fk in all_fks
        if fk["table"] in core and fk["ref_table"] not in core
    }
    return sorted(core) + sorted(referenced)


# ═════════════════════════════════════════════════════════════════════════════
# HELPERS COMUNES
# ═════════════════════════════════════════════════════════════════════════════

def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def shorten_sql_type(t):
    t = t.upper()
    if "BIGINT" in t:   return "BIGINT"
    if "SMALLINT" in t: return "SMALLINT"
    if "TINYINT" in t:  return "TINYINT"
    if "INT" in t:      return "INT"
    if "DECIMAL" in t or "NUMERIC" in t:
        m = re.search(r'\(([\d,\s]+)\)', t)
        return f"DEC({m.group(1)})" if m else "DECIMAL"
    if "DOUBLE" in t or "FLOAT" in t: return "FLOAT"
    if "LONGTEXT" in t: return "LONGTEXT"
    if "TEXT" in t:     return "TEXT"
    if "VARCHAR" in t:
        m = re.search(r'\((\d+)\)', t)
        return f"VC({m.group(1)})" if m else "VARCHAR"
    if "CHAR" in t:     return "CHAR"
    if "DATETIME" in t: return "DATETIME"
    if "TIMESTAMP" in t:return "TIMESTAMP"
    if t.strip() == "DATE": return "DATE"
    if "JSON" in t:     return "JSON"
    if "BOOL" in t or "BIT" in t: return "BOOL"
    return t[:12]


def compute_layout(tables, schema, per_row, gap_x=40, gap_y=60,
                   tbl_w=260, hdr_h=32, row_h=24, start_x=60, start_y=60):
    positions, x, y, col = {}, start_x, start_y, 0
    row_max_h = 0
    for t in tables:
        h = hdr_h + len(schema.get(t, [])) * row_h
        positions[t] = (x, y)
        row_max_h = max(row_max_h, h)
        x += tbl_w + gap_x
        col += 1
        if col >= per_row:
            col, x = 0, start_x
            y += row_max_h + gap_y
            row_max_h = 0
    return positions


def get_style(module):
    return MODULE_STYLE.get(module, MODULE_STYLE["default"])


# ═════════════════════════════════════════════════════════════════════════════
# GENERADOR DRAW.IO
# ═════════════════════════════════════════════════════════════════════════════

ENTITY_W = 260
TYPE_W   = 52
FIELD_W  = ENTITY_W - TYPE_W
HEADER_H = 32
ROW_H    = 24


def _drawio_entity(entity_base, table, x, y, cols, module):
    fill, stroke, _ = get_style(module)
    h = HEADER_H + len(cols) * ROW_H
    out = []
    out.append(
        f'        <mxCell id="{entity_base}" value="{esc(table)}" '
        f'style="shape=table;startSize={HEADER_H};container=1;collapsible=1;'
        f'childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;align=center;'
        f'resizeLast=1;fontSize=13;fillColor={fill};strokeColor={stroke};" '
        f'vertex="1" parent="1">'
    )
    out.append(f'          <mxGeometry x="{x}" y="{y}" width="{ENTITY_W}" height="{h}" as="geometry"/>')
    out.append("        </mxCell>")
    return out, h


def _drawio_row(entity_base, row_idx, col_info, is_last, sub_id_start):
    row_id = entity_base + row_idx
    row_y  = HEADER_H + (row_idx - 1) * ROW_H

    is_pk  = col_info["is_pk"]
    is_fk  = col_info["is_fk"]
    if is_pk and is_fk:
        lbl, bg, fs = "PK/FK", "#ffe6cc", "fontStyle=1;"
    elif is_pk:
        lbl, bg, fs = "PK",    "#fff2cc", "fontStyle=1;"
    elif is_fk:
        lbl, bg, fs = "FK",    "#dae8fc", ""
    else:
        lbl, bg, fs = "",      "none",    ""

    out = []
    out.append(
        f'        <mxCell id="{row_id}" value="" '
        f'style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;'
        f'swimlaneBody=0;fillColor=none;collapsible=0;dropTarget=0;'
        f'points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontSize=11;'
        f'top=0;left=0;right=0;bottom={"1" if is_last else "0"};" '
        f'vertex="1" parent="{entity_base}">'
    )
    out.append(f'          <mxGeometry y="{row_y}" width="{ENTITY_W}" height="{ROW_H}" as="geometry"/>')
    out.append("        </mxCell>")

    sid1 = sub_id_start
    out.append(
        f'        <mxCell id="{sid1}" value="{esc(lbl)}" '
        f'style="shape=partialRectangle;connectable=0;fillColor={bg};'
        f'top=0;left=0;bottom=0;right=0;{fs}overflow=hidden;fontSize=10;" '
        f'vertex="1" parent="{row_id}">'
    )
    out.append(
        f'          <mxGeometry width="{TYPE_W}" height="{ROW_H}" as="geometry">'
        f'<mxRectangle width="{TYPE_W}" height="{ROW_H}" as="alternateBounds"/>'
        f"</mxGeometry>"
    )
    out.append("        </mxCell>")

    sid2 = sub_id_start + 1
    col_label = f'{esc(col_info["col"])} : {shorten_sql_type(col_info["type"])}'
    out.append(
        f'        <mxCell id="{sid2}" value="{col_label}" '
        f'style="shape=partialRectangle;connectable=0;fillColor=none;'
        f'top=0;left=0;bottom=0;right=0;overflow=hidden;fontSize=11;" '
        f'vertex="1" parent="{row_id}">'
    )
    out.append(
        f'          <mxGeometry x="{TYPE_W}" width="{FIELD_W}" height="{ROW_H}" as="geometry">'
        f'<mxRectangle width="{FIELD_W}" height="{ROW_H}" as="alternateBounds"/>'
        f"</mxGeometry>"
    )
    out.append("        </mxCell>")

    return out, sid2 + 1  # next free sub_id


def generate_drawio(tables, schema, all_fks, diagram_name="DER", per_row=6):
    table_set = set(tables)
    fks = [f for f in all_fks
           if f["table"] in table_set and f["ref_table"] in table_set]

    positions = compute_layout(tables, schema, per_row,
                               tbl_w=ENTITY_W, hdr_h=HEADER_H, row_h=ROW_H)

    # entity_base IDs: índice*1000 + 1000 (para que quepan ≤999 filas)
    entity_base_map = {t: (i + 1) * 1000 for i, t in enumerate(tables)}

    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<mxfile host="Electron" version="21.7.6" type="device">')
    lines.append(f'  <diagram id="{esc(diagram_name)}" name="{esc(diagram_name)}">')

    n_rows = max(1, (len(tables) + per_row - 1) // per_row)
    canvas_w = per_row * (ENTITY_W + 40) + 200
    canvas_h = n_rows * (35 * ROW_H + HEADER_H + 60) + 200

    lines.append(
        f'    <mxGraphModel dx="2000" dy="1200" grid="1" gridSize="10" '
        f'guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" '
        f'pageScale="1" pageWidth="{max(canvas_w, 2000)}" '
        f'pageHeight="{max(canvas_h, 1400)}" math="0" shadow="0">'
    )
    lines.append("      <root>")
    lines.append('        <mxCell id="0"/>')
    lines.append('        <mxCell id="1" parent="0"/>')

    sub_id = 500000

    for t in tables:
        base = entity_base_map[t]
        x, y = positions[t]
        cols = schema.get(t, [])
        mod  = TABLE_MODULE.get(t, "default")

        ent_lines, _ = _drawio_entity(base, t, x, y, cols, mod)
        lines.extend(ent_lines)

        for i, col in enumerate(cols, 1):
            row_lines, sub_id = _drawio_row(base, i, col, i == len(cols), sub_id)
            lines.extend(row_lines)

    # Aristas
    for ei, fk in enumerate(fks):
        edge_id = 900000 + ei
        src_base = entity_base_map[fk["ref_table"]]
        tgt_base = entity_base_map[fk["table"]]

        src_idx = next(
            (i for i, c in enumerate(schema.get(fk["ref_table"], []), 1)
             if c["col"] == fk["ref_col"]), 1)
        tgt_idx = next(
            (i for i, c in enumerate(schema.get(fk["table"], []), 1)
             if c["col"] == fk["col"]), 1)

        lines.append(
            f'        <mxCell id="{edge_id}" value="" '
            f'style="edgeStyle=entityRelationEdgeStyle;html=1;'
            f'endArrow=ERmany;endFill=0;startArrow=ERone;startFill=0;fontSize=10;" '
            f'edge="1" source="{src_base + src_idx}" '
            f'target="{tgt_base + tgt_idx}" parent="1">'
        )
        lines.append('          <mxGeometry relative="1" as="geometry"/>')
        lines.append("        </mxCell>")

    lines.extend(["      </root>", "    </mxGraphModel>",
                  "  </diagram>", "</mxfile>"])
    return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════════
# GENERADOR VUERD.JSON  (dineug.vuerd-vscode)
# ═════════════════════════════════════════════════════════════════════════════

def generate_vuerd(tables, schema, all_fks,
                   db_name="dbcantinatita", per_row=6, canvas_size=8000):
    table_set = set(tables)
    fks = [f for f in all_fks
           if f["table"] in table_set and f["ref_table"] in table_set]

    positions = compute_layout(tables, schema, per_row,
                               tbl_w=280, hdr_h=34, row_h=35)

    ctr = [0]
    def nid(prefix):
        ctr[0] += 1
        return f"{prefix}{ctr[0]:06d}"

    table_id = {t: nid("T") for t in tables}
    col_id = {}
    for t in tables:
        for c in schema.get(t, []):
            col_id[(t, c["col"])] = nid("C")

    vuerd_tables = []
    for t in tables:
        tid    = table_id[t]
        lx, ly = positions[t]
        mod    = TABLE_MODULE.get(t, "default")
        _, _, color = get_style(mod)
        cols   = schema.get(t, [])

        max_name = max((len(c["col"]) for c in cols), default=10)
        wn = min(max(max_name * 8, 80), 200)
        max_type = max((len(shorten_sql_type(c["type"])) for c in cols), default=6)
        wt = min(max(max_type * 7, 60), 140)

        vuerd_cols = []
        for col in cols:
            cid = col_id[(t, col["col"])]
            is_pk, is_fk = col["is_pk"], col["is_fk"]
            vuerd_cols.append({
                "id": cid, "tableId": tid,
                "name": col["col"], "comment": "",
                "dataType": shorten_sql_type(col["type"]),
                "default": "",
                "option": {
                    "autoIncrement": "auto_increment" in col.get("extra","").lower(),
                    "primaryKey": is_pk,
                    "unique": col["key"] == "UNI",
                    "notNull": not col["nullable"],
                },
                "ui": {
                    "active": False,
                    "pk": is_pk and not is_fk,
                    "fk": is_fk and not is_pk,
                    "pfk": is_pk and is_fk,
                    "widthName": wn,
                    "widthComment": 60,
                    "widthDataType": wt,
                    "widthDefault": 60,
                },
            })

        vuerd_tables.append({
            "id": tid, "name": t, "comment": mod,
            "columns": vuerd_cols,
            "ui": {"active": False, "left": lx, "top": ly,
                   "zIndex": 1, "widthName": wn, "widthComment": 60},
            "meta": {"openColor": True, "color": color},
        })

    vuerd_rels = []
    for i, fk in enumerate(fks):
        src_tid = table_id.get(fk["ref_table"])
        tgt_tid = table_id.get(fk["table"])
        src_cid = col_id.get((fk["ref_table"], fk["ref_col"]))
        tgt_cid = col_id.get((fk["table"],     fk["col"]))
        if not all([src_tid, tgt_tid, src_cid, tgt_cid]):
            continue
        tgt_pk  = any(c["is_pk"] and c["col"] == fk["col"]
                      for c in schema.get(fk["table"], []))
        vuerd_rels.append({
            "id": f"R{i+1:06d}", "type": "ZeroN",
            "identification": tgt_pk,
            "start": {"tableId": src_tid, "columnIds": [src_cid],
                      "x": 0, "y": 0, "direction": "right"},
            "end":   {"tableId": tgt_tid, "columnIds": [tgt_cid],
                      "x": 0, "y": 0, "direction": "left"},
        })

    return {
        "canvas": {
            "version": "2.2.11",
            "width": canvas_size, "height": canvas_size,
            "scrollTop": 0, "scrollLeft": 0,
            "zoomLevel": 1,
            "show": {
                "tableComment": True, "columnComment": False,
                "columnDataType": True, "columnDefault": False,
                "columnAutoIncrement": True, "columnPrimaryKey": True,
                "columnUnique": False, "columnNotNull": True,
                "relationship": True,
            },
            "database": "MySQL", "databaseName": db_name, "orderType": "columnOrder",
        },
        "table":        {"tables": vuerd_tables, "memos": []},
        "relationship": {"relationships": vuerd_rels},
    }


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def write(path, content, binary=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = "wb" if binary else "w"
    kw   = {} if binary else {"encoding": "utf-8"}
    with open(path, mode, **kw) as f:
        if binary:
            f.write(content)
        else:
            f.write(content)
    return os.path.getsize(path)


def main():
    base = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    drawio_dir = os.path.join(base, "docs", "der")
    vuerd_dir  = os.path.join(base, "docs", "der", "vuerd")

    print("=" * 60)
    print("  GENERADOR DE DIAGRAMAS ER — dbcantinatita")
    print("=" * 60)
    print("\n⏳ Conectando a MySQL y leyendo esquema...")
    schema, all_fks = load_schema()
    print(f"   ✔ {len(schema)} tablas  |  {len(all_fks)} FK reales\n")

    results = []

    for block_name, cfg in BLOCKS.items():
        tables  = tables_for_block(cfg["module"], schema, all_fks)
        per_row = cfg["per_row"]
        canvas  = cfg["canvas"]
        label   = block_name.replace("_", " ").upper()

        print(f"📐 [{label}]  {len(tables)} tablas")

        # draw.io
        xml  = generate_drawio(tables, schema, all_fks,
                               diagram_name=f"DER {label}", per_row=per_row)
        path = os.path.join(drawio_dir, f"{block_name}.drawio")
        sz   = write(path, xml)
        rel  = os.path.relpath(path, base)
        print(f"   draw.io  → {rel}  ({sz:,} B)")
        results.append((rel, sz))

        # vuerd
        data = generate_vuerd(tables, schema, all_fks,
                              per_row=per_row, canvas_size=canvas)
        path = os.path.join(vuerd_dir, f"{block_name}.vuerd.json")
        sz   = write(path, json.dumps(data, ensure_ascii=False, separators=(",",":")))
        rel  = os.path.relpath(path, base)
        print(f"   vuerd    → {rel}  ({sz:,} B)")
        results.append((rel, sz))

        print()

    total = sum(s for _, s in results)
    print("=" * 60)
    print(f"  ✅ {len(results)} archivos generados  |  {total:,} bytes totales")
    print("=" * 60)
    print()
    print("  draw.io  → abrir con draw.io desktop o app.diagrams.net")
    print("  vuerd    → instalar 'dineug.vuerd-vscode' en VS Code")
    print("             clic derecho en el .vuerd.json → Open with ERD Editor")
    print()
    print("  Para regenerar:")
    print("  D:/tita2026/cantina_tita/venv/Scripts/python.exe scripts/generate_all_der.py")


if __name__ == "__main__":
    main()
