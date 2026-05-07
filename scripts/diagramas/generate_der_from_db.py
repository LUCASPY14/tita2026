#!/usr/bin/env python3
"""
Genera diagramas Entidad-Relación en formato draw.io (.drawio)
directamente desde la base de datos MySQL 'dbcantinatita'.

Salidas:
  docs/DER_completo.drawio            - Todas las tablas del negocio
  docs/DER_bloque_clientes.drawio     - Bloque Clientes
  docs/DER_bloque_ventas.drawio       - Bloque Ventas
  docs/DER_bloque_compras.drawio      - Bloque Compras

Uso:
  D:/tita2026/cantina_tita/venv/Scripts/python.exe scripts/generate_der_from_db.py
"""

import json
import os
import MySQLdb

# ── Conexión ──────────────────────────────────────────────────────────────────
DB_CFG = dict(host="localhost", user="root", passwd="L01G05S33Vice.42",
              db="dbcantinatita", charset="utf8mb4")

EXCLUDE_TABLES = {
    "auth_group", "auth_group_permissions", "auth_permission", "auth_user",
    "auth_user_groups", "auth_user_user_permissions", "django_admin_log",
    "django_celery_beat_clockedschedule", "django_celery_beat_crontabschedule",
    "django_celery_beat_intervalschedule", "django_celery_beat_periodictask",
    "django_celery_beat_periodictasks", "django_celery_beat_solarschedule",
    "django_content_type", "django_migrations", "django_session",
}

# ── Layout ────────────────────────────────────────────────────────────────────
HEADER_H  = 32   # alto encabezado
ROW_H     = 24   # alto por campo
ENTITY_W  = 250  # ancho total
TYPE_W    = 52   # columna tipo (PK/FK)
FIELD_W   = ENTITY_W - TYPE_W
COL_GAP   = 40   # espacio horizontal entre columnas de tablas
ROW_GAP   = 40   # espacio vertical entre tablas

# ── Colores por módulo (basado en prefijo/grupo de tabla) ─────────────────────
MODULE_COLOR = {
    # fill_header (hex)  stroke (hex)
    "clientes":     ("#d5e8d4", "#82b366"),
    "ventas":       ("#e1d5e7", "#9673a6"),
    "compras":      ("#fff2cc", "#d6b656"),
    "productos":    ("#f8cecc", "#b85450"),
    "usuarios":     ("#dae8fc", "#6c8ebf"),
    "core":         ("#dae8fc", "#6c8ebf"),
    "contabilidad": ("#ffe6cc", "#d79b00"),
    "almuerzos":    ("#d5e8d4", "#009900"),
    "notificaciones":("#f5f5f5","#666666"),
    "api":          ("#e6f3ff", "#336699"),
    "reportes":     ("#fff0e6", "#cc6600"),
    "default":      ("#f5f5f5", "#666666"),
}

# Asignación tabla → módulo
TABLE_MODULE = {
    # ── CLIENTES
    "clientes": "clientes", "hijos": "clientes", "tipos_cliente": "clientes",
    "listas_precios": "clientes", "restricciones_hijos": "clientes",
    "historial_grados_hijos": "clientes", "grados": "clientes",
    "autorizaciones_saldo_negativo": "clientes",
    # ── CORE / TARJETAS
    "tarjetas": "core", "cargas_saldo": "core", "medios_pago": "core",
    "consumos_tarjeta": "core", "tarjetas_autorizacion": "core",
    "transacciones_online": "core", "limites_transaccion": "core",
    "limites_transaccion_roles_autorizadores": "core",
    "registro_autorizaciones": "core", "logs_autorizaciones": "core",
    "tarifas_comision": "core", "auditoria_comisiones": "core",
    "conciliacion_pagos": "core", "configuracion_sistema": "core",
    "cache_configuracion": "core", "datos_empresa": "core",
    # ── VENTAS
    "ventas": "ventas", "detalles_venta": "ventas",
    "documentos_tributarios": "ventas", "documento_impuestos": "ventas",
    "pagos_venta": "ventas", "notas_credito_cliente": "ventas",
    "detalles_nota_credito": "ventas", "aplicacion_pagos_ventas": "ventas",
    "promociones": "ventas", "categorias_promocion": "ventas",
    "productos_promocion": "ventas", "promociones_aplicadas": "ventas",
    "impuestos": "ventas", "timbrados": "ventas", "puntos_expedicion": "ventas",
    # ── COMPRAS
    "compras": "compras", "detalles_compra": "compras",
    "proveedores": "compras", "pagos_proveedores": "compras",
    "notas_credito_proveedor": "compras", "detalles_nota_credito_proveedor": "compras",
    "aplicacion_pagos_compras": "compras",
    # ── PRODUCTOS
    "productos": "productos", "categorias": "productos",
    "unidades_medida": "productos", "stock_unico": "productos",
    "movimientos_stock": "productos", "lotes_producto": "productos",
    "alertas_stock": "productos", "alertas_vencimiento": "productos",
    "costos_historicos": "productos", "ajustes_inventario": "productos",
    "detalles_ajuste": "productos", "historico_precios": "productos",
    "precios_por_lista": "productos", "alergenos": "productos",
    "productos_alergenos": "productos",
    # ── USUARIOS
    "empleados": "usuarios", "roles": "usuarios", "permisos": "usuarios",
    "roles_permisos": "usuarios", "perfiles_usuario": "usuarios",
    "sesiones_activas": "usuarios", "renovaciones_sesion": "usuarios",
    "autenticacion_2fa": "usuarios", "intentos_2fa": "usuarios",
    "intentos_login": "usuarios", "bloqueos_cuenta": "usuarios",
    "tokens_recuperacion": "usuarios", "tokens_verificacion": "usuarios",
    "auditoria_empleados": "usuarios", "auditoria_operaciones": "usuarios",
    "patrones_acceso": "usuarios", "usuarios_portal": "usuarios",
    "usuarios_web_clientes": "usuarios", "auditoria_usuarios_web": "usuarios",
    # ── CONTABILIDAD
    "cajas": "contabilidad", "movimientos_caja": "contabilidad",
    "cierres_caja": "contabilidad",
    # ── ALMUERZOS
    "planes_almuerzo": "almuerzos", "suscripciones_almuerzo": "almuerzos",
    "tipos_almuerzo": "almuerzos", "registros_consumo_almuerzo": "almuerzos",
    "cuentas_almuerzo_mensual": "almuerzos", "pagos_almuerzo_mensual": "almuerzos",
    "pagos_cuentas_almuerzo": "almuerzos",
    # ── NOTIFICACIONES
    "notificaciones_portal": "notificaciones", "notificaciones_saldo": "notificaciones",
    "solicitudes_notificacion": "notificaciones",
    "preferencias_notificacion": "notificaciones",
    "emails_enviados": "notificaciones", "sms_enviados": "notificaciones",
    "plantillas_email": "notificaciones", "plantillas_sms": "notificaciones",
    "campanas_comunicacion": "notificaciones",
    "alertas_sistema": "notificaciones", "alertas_automaticas": "notificaciones",
    "historial_alertas": "notificaciones", "anomalias_detectadas": "notificaciones",
    "alerta_destinatarios": "notificaciones",
    # ── API / INTEGRACIONES
    "proveedores_api": "api", "endpoints_api": "api",
    "credenciales_api": "api", "logs_llamadas_api": "api",
    "webhook_endpoints": "api", "logs_webhooks": "api",
    # ── REPORTES / KPI
    "plantillas_reporte": "reportes", "kpi_metricas": "reportes",
    "valores_kpi": "reportes", "dashboards": "reportes",
    "plantillas_tarea": "reportes", "ejecuciones_tarea": "reportes",
    "destinatarios_tarea": "reportes", "restricciones_horarias": "reportes",
    "historial_acceso": "usuarios",
}


def get_module(table_name: str) -> str:
    return TABLE_MODULE.get(table_name, "default")


# ── Extracción del esquema ────────────────────────────────────────────────────

def load_schema():
    conn = MySQLdb.connect(**DB_CFG)
    cur = conn.cursor()

    cur.execute(
        "SELECT table_name, column_name, column_type, column_key, extra "
        "FROM information_schema.columns "
        "WHERE table_schema=%s ORDER BY table_name, ordinal_position",
        (DB_CFG["db"],),
    )
    schema = {}
    for table, col, ctype, key, extra in cur.fetchall():
        if table in EXCLUDE_TABLES:
            continue
        if table not in schema:
            schema[table] = []
        is_pk = key == "PRI"
        is_fk = False  # se rellena después
        schema[table].append({
            "col": col, "type": ctype, "key": key,
            "is_pk": is_pk, "extra": extra,
        })

    cur.execute(
        "SELECT table_name, column_name, referenced_table_name, referenced_column_name "
        "FROM information_schema.key_column_usage "
        "WHERE table_schema=%s AND referenced_table_name IS NOT NULL "
        "ORDER BY table_name, column_name",
        (DB_CFG["db"],),
    )
    fks = []
    fk_set = {}   # (table, col) → (ref_table, ref_col)
    for t, c, rt, rc in cur.fetchall():
        if t in EXCLUDE_TABLES or rt in EXCLUDE_TABLES:
            continue
        fks.append({"table": t, "col": c, "ref_table": rt, "ref_col": rc})
        fk_set[(t, c)] = (rt, rc)

    cur.close()
    conn.close()

    # Marcar columnas FK
    for table, cols in schema.items():
        for c in cols:
            c["is_fk"] = (table, c["col"]) in fk_set

    return schema, fks


# ── Generador XML draw.io ─────────────────────────────────────────────────────

def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def shorten_type(t: str) -> str:
    """Acorta el tipo de columna para legibilidad."""
    t = t.lower()
    for kw in ("bigint", "smallint", "tinyint", "int"):
        if kw in t:
            return "INT"
    if "varchar" in t:
        import re
        m = re.search(r'\((\d+)\)', t)
        return f"VARCHAR({m.group(1)})" if m else "VARCHAR"
    if "decimal" in t:
        import re
        m = re.search(r'\(([\d,]+)\)', t)
        return f"DEC({m.group(1)})" if m else "DECIMAL"
    if "datetime" in t:
        return "DATETIME"
    if "date" == t:
        return "DATE"
    if "text" in t:
        return "TEXT"
    if "json" in t:
        return "JSON"
    if "bool" in t:
        return "BOOL"
    return t.upper()[:12]


def layout_tables(table_names, schema, tables_per_row=5):
    """Calcula posición (x, y) para cada tabla."""
    positions = {}
    col_widths = [0] * tables_per_row

    rows = []
    current_row = []
    for t in table_names:
        current_row.append(t)
        if len(current_row) == tables_per_row:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)

    y_offset = 60
    for row_idx, row in enumerate(rows):
        row_heights = []
        for col_idx, t in enumerate(row):
            h = HEADER_H + len(schema.get(t, [])) * ROW_H
            row_heights.append(h)

        max_h = max(row_heights) if row_heights else HEADER_H
        x_offset = 20
        for col_idx, t in enumerate(row):
            positions[t] = (x_offset, y_offset)
            x_offset += ENTITY_W + COL_GAP

        y_offset += max_h + ROW_GAP

    return positions


def generate_drawio(
    tables: list,
    schema: dict,
    all_fks: list,
    diagram_name: str = "DER",
    tables_per_row: int = 6,
) -> str:
    """Genera el XML completo para draw.io."""

    table_set = set(tables)
    # Solo FK donde AMBOS extremos están en el diagrama
    fks = [f for f in all_fks
           if f["table"] in table_set and f["ref_table"] in table_set]

    positions = layout_tables(tables, schema, tables_per_row)

    # IDs: entidades base 1000 (paso 100), filas entity+i, edges 50000+
    entity_id_map = {}  # table → base_id
    for i, t in enumerate(tables):
        entity_id_map[t] = (i + 1) * 100

    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<mxfile host="Electron" version="21.7.6" type="device">')
    lines.append(f'  <diagram id="{esc(diagram_name)}" name="{esc(diagram_name)}">')

    # Canvas muy grande para diagramas completos
    canvas_w = tables_per_row * (ENTITY_W + COL_GAP) + 200
    n_rows = (len(tables) + tables_per_row - 1) // tables_per_row
    canvas_h = n_rows * (30 * ROW_H + HEADER_H + ROW_GAP) + 200

    lines.append(
        f'    <mxGraphModel dx="2000" dy="1200" grid="1" gridSize="10" '
        f'guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" '
        f'pageScale="1" pageWidth="{max(canvas_w, 2000)}" '
        f'pageHeight="{max(canvas_h, 1400)}" math="0" shadow="0">'
    )
    lines.append("      <root>")
    lines.append('        <mxCell id="0"/>')
    lines.append('        <mxCell id="1" parent="0"/>')

    # Sub-cell counter (rows ID: entity_base + field_index; sub-cells 200000+)
    sub_id = 200000

    for t in tables:
        base_id = entity_id_map[t]
        x, y = positions[t]
        cols = schema.get(t, [])
        h = HEADER_H + len(cols) * ROW_H
        mod = get_module(t)
        fill, stroke = MODULE_COLOR.get(mod, MODULE_COLOR["default"])

        # Tabla contenedora
        lines.append(
            f'        <mxCell id="{base_id}" value="{esc(t)}" '
            f'style="shape=table;startSize={HEADER_H};container=1;collapsible=1;'
            f'childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;align=center;'
            f'resizeLast=1;fontSize=13;fillColor={fill};strokeColor={stroke};'
            f'fontColor=#000000;" '
            f'vertex="1" parent="1">'
        )
        lines.append(
            f'          <mxGeometry x="{x}" y="{y}" '
            f'width="{ENTITY_W}" height="{h}" as="geometry"/>'
        )
        lines.append("        </mxCell>")

        for i, col in enumerate(cols, 1):
            row_id = base_id + i
            row_y = HEADER_H + (i - 1) * ROW_H
            is_last = i == len(cols)

            if col["is_pk"] and col["is_fk"]:
                label = "PK/FK"
                bg = "#ffe6cc"
                fs = "fontStyle=1;"
            elif col["is_pk"]:
                label = "PK"
                bg = "#fff2cc"
                fs = "fontStyle=1;"
            elif col["is_fk"]:
                label = "FK"
                bg = "#dae8fc"
                fs = ""
            else:
                label = ""
                bg = "none"
                fs = ""

            # Fila
            lines.append(
                f'        <mxCell id="{row_id}" value="" '
                f'style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;'
                f'swimlaneBody=0;fillColor=none;collapsible=0;dropTarget=0;'
                f'points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontSize=11;'
                f'top=0;left=0;right=0;bottom={"1" if is_last else "0"};" '
                f'vertex="1" parent="{base_id}">'
            )
            lines.append(
                f'          <mxGeometry y="{row_y}" '
                f'width="{ENTITY_W}" height="{ROW_H}" as="geometry"/>'
            )
            lines.append("        </mxCell>")

            # Sub-celda izquierda: tipo
            sub_id += 1
            lines.append(
                f'        <mxCell id="{sub_id}" value="{esc(label)}" '
                f'style="shape=partialRectangle;connectable=0;fillColor={bg};'
                f'top=0;left=0;bottom=0;right=0;{fs}overflow=hidden;fontSize=10;" '
                f'vertex="1" parent="{row_id}">'
            )
            lines.append(
                f'          <mxGeometry width="{TYPE_W}" height="{ROW_H}" as="geometry">'
                f'<mxRectangle width="{TYPE_W}" height="{ROW_H}" as="alternateBounds"/>'
                f"</mxGeometry>"
            )
            lines.append("        </mxCell>")

            # Sub-celda derecha: nombre + tipo SQL abreviado
            sub_id += 1
            col_label = f'{esc(col["col"])} : {shorten_type(col["type"])}'
            lines.append(
                f'        <mxCell id="{sub_id}" value="{col_label}" '
                f'style="shape=partialRectangle;connectable=0;fillColor=none;'
                f'top=0;left=0;bottom=0;right=0;overflow=hidden;fontSize=11;" '
                f'vertex="1" parent="{row_id}">'
            )
            lines.append(
                f'          <mxGeometry x="{TYPE_W}" width="{FIELD_W}" '
                f'height="{ROW_H}" as="geometry">'
                f'<mxRectangle width="{FIELD_W}" height="{ROW_H}" as="alternateBounds"/>'
                f"</mxGeometry>"
            )
            lines.append("        </mxCell>")

    # ── Aristas (relaciones FK)
    for edge_idx, fk in enumerate(fks):
        edge_id = 50000 + edge_idx
        src_base = entity_id_map[fk["table"]]
        tgt_base = entity_id_map[fk["ref_table"]]
        src_cols = schema.get(fk["table"], [])
        tgt_cols = schema.get(fk["ref_table"], [])

        # Buscar índice de columna FK en source
        src_row = src_base + 1  # fallback
        for i, c in enumerate(src_cols, 1):
            if c["col"] == fk["col"]:
                src_row = src_base + i
                break

        # Buscar índice de columna PK en target
        tgt_row = tgt_base + 1  # fallback
        for i, c in enumerate(tgt_cols, 1):
            if c["col"] == fk["ref_col"]:
                tgt_row = tgt_base + i
                break

        lines.append(
            f'        <mxCell id="{edge_id}" value="" '
            f'style="edgeStyle=entityRelationEdgeStyle;html=1;'
            f'endArrow=ERmany;endFill=0;startArrow=ERone;startFill=0;'
            f'exitX=1;exitY=0.5;exitDx=0;exitDy=0;'
            f'entryX=0;entryY=0.5;entryDx=0;entryDy=0;fontSize=10;" '
            f'edge="1" source="{src_row}" target="{tgt_row}" parent="1">'
        )
        lines.append('          <mxGeometry relative="1" as="geometry"/>')
        lines.append("        </mxCell>")

    lines.append("      </root>")
    lines.append("    </mxGraphModel>")
    lines.append("  </diagram>")
    lines.append("</mxfile>")

    return "\n".join(lines)


# ── Definición de bloques ─────────────────────────────────────────────────────

def tables_for_block(block: str, schema: dict, all_fks: list) -> list:
    """Retorna tablas del bloque + tablas referenciadas directamente (1 nivel)."""
    core = {t for t in schema if TABLE_MODULE.get(t) == block}

    # Incluir tablas referenciadas por FK directas (para contexto)
    referenced = set()
    for fk in all_fks:
        if fk["table"] in core and fk["ref_table"] not in core:
            referenced.add(fk["ref_table"])

    return sorted(core) + sorted(referenced - core)


BLOCK_TABLES_PER_ROW = {
    "clientes": 4,
    "ventas":   5,
    "compras":  4,
}

BLOCK_MODULE = {
    "clientes": "clientes",
    "ventas":   "ventas",
    "compras":  "compras",
}


def main():
    out_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    out_dir = os.path.normpath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    print("⏳ Leyendo esquema de MySQL...")
    schema, all_fks = load_schema()
    print(f"   Tablas: {len(schema)}, FKs reales: {len(all_fks)}")

    # ── 1. Diagrama COMPLETO
    all_tables = sorted(schema.keys())
    print(f"\n📐 Generando DER completo ({len(all_tables)} tablas)...")
    xml = generate_drawio(all_tables, schema, all_fks,
                          diagram_name="DER Completo - dbcantinatita",
                          tables_per_row=7)
    out = os.path.join(out_dir, "DER_completo.drawio")
    with open(out, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"   ✅ {out}  ({len(xml):,} bytes)")

    # ── 2-4. Bloques
    for block, module in BLOCK_MODULE.items():
        tables = tables_for_block(module, schema, all_fks)
        per_row = BLOCK_TABLES_PER_ROW[block]
        print(f"\n📐 Generando bloque '{block}' ({len(tables)} tablas)...")
        xml = generate_drawio(tables, schema, all_fks,
                              diagram_name=f"DER Bloque - {block.upper()}",
                              tables_per_row=per_row)
        out = os.path.join(out_dir, f"DER_bloque_{block}.drawio")
        with open(out, "w", encoding="utf-8") as f:
            f.write(xml)
        print(f"   ✅ {out}  ({len(xml):,} bytes)")

    print("\n🎉 Listo. Archivos generados en docs/")
    print("   Abrir con draw.io app o app.diagrams.net")


if __name__ == "__main__":
    main()
