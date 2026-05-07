#!/usr/bin/env python3
"""
Genera diagramas ERD en formato .vuerd.json (compatible con ERD Editor de dineug)
directamente desde la base de datos MySQL 'dbcantinatita'.

Extensión VS Code: dineug.vuerd-vscode
Formato: vuerd.json versión 2.2.x

Salidas:
  docs/erd/DER_completo.vuerd.json
  docs/erd/DER_bloque_clientes.vuerd.json
  docs/erd/DER_bloque_ventas.vuerd.json
  docs/erd/DER_bloque_compras.vuerd.json

Uso:
  D:/tita2026/cantina_tita/venv/Scripts/python.exe scripts/generate_erd_vuerd.py
"""

import json
import os
import math
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

# ── Asignación tabla → módulo (para colores) ──────────────────────────────────
TABLE_MODULE = {
    "clientes": "clientes", "hijos": "clientes", "tipos_cliente": "clientes",
    "listas_precios": "clientes", "restricciones_hijos": "clientes",
    "historial_grados_hijos": "clientes", "grados": "clientes",
    "autorizaciones_saldo_negativo": "clientes",
    "tarjetas": "core", "cargas_saldo": "core", "medios_pago": "core",
    "consumos_tarjeta": "core", "tarjetas_autorizacion": "core",
    "transacciones_online": "core", "limites_transaccion": "core",
    "limites_transaccion_roles_autorizadores": "core",
    "registro_autorizaciones": "core", "logs_autorizaciones": "core",
    "tarifas_comision": "core", "auditoria_comisiones": "core",
    "conciliacion_pagos": "core", "configuracion_sistema": "core",
    "cache_configuracion": "core", "datos_empresa": "core",
    "ventas": "ventas", "detalles_venta": "ventas",
    "documentos_tributarios": "ventas", "documento_impuestos": "ventas",
    "pagos_venta": "ventas", "notas_credito_cliente": "ventas",
    "detalles_nota_credito": "ventas", "aplicacion_pagos_ventas": "ventas",
    "promociones": "ventas", "categorias_promocion": "ventas",
    "productos_promocion": "ventas", "promociones_aplicadas": "ventas",
    "impuestos": "ventas", "timbrados": "ventas", "puntos_expedicion": "ventas",
    "compras": "compras", "detalles_compra": "compras",
    "proveedores": "compras", "pagos_proveedores": "compras",
    "notas_credito_proveedor": "compras",
    "detalles_nota_credito_proveedor": "compras",
    "aplicacion_pagos_compras": "compras",
    "productos": "productos", "categorias": "productos",
    "unidades_medida": "productos", "stock_unico": "productos",
    "movimientos_stock": "productos", "lotes_producto": "productos",
    "alertas_stock": "productos", "alertas_vencimiento": "productos",
    "costos_historicos": "productos", "ajustes_inventario": "productos",
    "detalles_ajuste": "productos", "historico_precios": "productos",
    "precios_por_lista": "productos", "alergenos": "productos",
    "productos_alergenos": "productos",
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
    "cajas": "contabilidad", "movimientos_caja": "contabilidad",
    "cierres_caja": "contabilidad",
    "planes_almuerzo": "almuerzos", "suscripciones_almuerzo": "almuerzos",
    "tipos_almuerzo": "almuerzos", "registros_consumo_almuerzo": "almuerzos",
    "cuentas_almuerzo_mensual": "almuerzos",
    "pagos_almuerzo_mensual": "almuerzos", "pagos_cuentas_almuerzo": "almuerzos",
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
    "proveedores_api": "api", "endpoints_api": "api",
    "credenciales_api": "api", "logs_llamadas_api": "api",
    "webhook_endpoints": "api", "logs_webhooks": "api",
    "plantillas_reporte": "reportes", "kpi_metricas": "reportes",
    "valores_kpi": "reportes", "dashboards": "reportes",
    "plantillas_tarea": "reportes", "ejecuciones_tarea": "reportes",
    "destinatarios_tarea": "reportes", "restricciones_horarias": "reportes",
}

# Colores HEX por módulo (se usan en el campo "color" de la tabla en vuerd)
MODULE_COLOR = {
    "clientes":      "#82b366",
    "core":          "#6c8ebf",
    "ventas":        "#9673a6",
    "compras":       "#d6b656",
    "productos":     "#b85450",
    "usuarios":      "#2d7600",
    "contabilidad":  "#d79b00",
    "almuerzos":     "#006EAF",
    "notificaciones":"#666666",
    "api":           "#336699",
    "reportes":      "#cc6600",
    "default":       "#666666",
}


def get_module(t: str) -> str:
    return TABLE_MODULE.get(t, "default")


# ── Extracción del esquema MySQL ──────────────────────────────────────────────

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
    schema = {}   # table → [col_info]
    for table, col, ctype, key, nullable, extra in cur.fetchall():
        if table in EXCLUDE_TABLES:
            continue
        if table not in schema:
            schema[table] = []
        schema[table].append({
            "col": col,
            "type": ctype,
            "key": key,
            "nullable": nullable == "YES",
            "extra": extra,
            "is_pk": key == "PRI",
            "is_fk": False,   # se rellena luego
        })

    cur.execute(
        "SELECT table_name, column_name, referenced_table_name, "
        "referenced_column_name "
        "FROM information_schema.key_column_usage "
        "WHERE table_schema=%s AND referenced_table_name IS NOT NULL "
        "ORDER BY table_name, column_name",
        (DB_CFG["db"],),
    )
    fks = []
    fk_cols = set()
    for t, c, rt, rc in cur.fetchall():
        if t in EXCLUDE_TABLES or rt in EXCLUDE_TABLES:
            continue
        fks.append({"table": t, "col": c, "ref_table": rt, "ref_col": rc})
        fk_cols.add((t, c))

    cur.close()
    conn.close()

    for table, cols in schema.items():
        for c in cols:
            c["is_fk"] = (table, c["col"]) in fk_cols

    return schema, fks


# ── Helpers de tipo ───────────────────────────────────────────────────────────

def to_vuerd_type(raw: str) -> str:
    """Normaliza el tipo SQL para la pantalla del ERD Editor."""
    r = raw.upper()
    if "BIGINT" in r:
        return "BIGINT"
    if "SMALLINT" in r or "TINYINT(1)" in r:
        return "SMALLINT"
    if "TINYINT" in r:
        return "TINYINT"
    if "INT" in r:
        return "INT"
    if "DECIMAL" in r or "NUMERIC" in r:
        import re
        m = re.search(r'\(([\d,\s]+)\)', r)
        return f"DECIMAL({m.group(1)})" if m else "DECIMAL"
    if "DOUBLE" in r or "FLOAT" in r:
        return "FLOAT"
    if "LONGTEXT" in r:
        return "LONGTEXT"
    if "TEXT" in r:
        return "TEXT"
    if "VARCHAR" in r:
        import re
        m = re.search(r'\((\d+)\)', r)
        return f"VARCHAR({m.group(1)})" if m else "VARCHAR"
    if "CHAR" in r:
        return "CHAR"
    if "DATETIME" in r:
        return "DATETIME"
    if "TIMESTAMP" in r:
        return "TIMESTAMP"
    if "DATE" == r.strip():
        return "DATE"
    if "JSON" in r:
        return "JSON"
    if "BOOL" in r or "BIT" in r:
        return "BOOLEAN"
    return r[:20]


# ── Generador vuerd.json ──────────────────────────────────────────────────────

def generate_vuerd(
    tables: list,
    schema: dict,
    all_fks: list,
    db_name: str = "dbcantinatita",
    tables_per_row: int = 6,
    canvas_size: int = 6000,
) -> dict:
    """Construye el dict JSON en formato vuerd 2.2.x."""

    table_set = set(tables)
    fks = [f for f in all_fks
           if f["table"] in table_set and f["ref_table"] in table_set]

    # Asignar IDs únicos
    table_id = {}    # table_name → "T{i:04d}"
    col_id = {}      # (table_name, col_name) → "C{i:06d}"
    ctr = [0]

    def next_id(prefix):
        ctr[0] += 1
        return f"{prefix}{ctr[0]:06d}"

    for t in tables:
        table_id[t] = next_id("T")
        for col in schema.get(t, []):
            col_id[(t, col["col"])] = next_id("C")

    # Layout: cuadrícula columnas×filas
    TABLE_W = 280
    TABLE_GAP_X = 50
    TABLE_GAP_Y = 60

    # Altura aproximada de cada tabla
    def tbl_height(t):
        return 34 + len(schema.get(t, [])) * 35

    positions = {}
    cols_placed = 0
    row_x = 80
    row_y = 80
    max_h_in_row = 0
    col_idx = 0

    for t in tables:
        positions[t] = (row_x, row_y)
        h = tbl_height(t)
        max_h_in_row = max(max_h_in_row, h)
        row_x += TABLE_W + TABLE_GAP_X
        col_idx += 1
        if col_idx >= tables_per_row:
            col_idx = 0
            row_x = 80
            row_y += max_h_in_row + TABLE_GAP_Y
            max_h_in_row = 0

    # ── Tablas
    vuerd_tables = []
    for t in tables:
        tid = table_id[t]
        lx, ly = positions[t]
        mod = get_module(t)
        color = MODULE_COLOR.get(mod, "#666666")
        cols = schema.get(t, [])

        # Calcular widthName = max longitud de nombre de columna
        max_name_len = max((len(c["col"]) for c in cols), default=10)
        width_name = min(max(max_name_len * 8, 80), 180)
        max_type_len = max((len(to_vuerd_type(c["type"])) for c in cols), default=6)
        width_type = min(max(max_type_len * 7, 60), 140)

        vuerd_cols = []
        for col in cols:
            cid = col_id[(t, col["col"])]
            is_pk = col["is_pk"]
            is_fk = col["is_fk"]
            is_pfk = is_pk and is_fk
            auto_inc = "auto_increment" in col.get("extra", "").lower()
            not_null = not col["nullable"]

            vuerd_cols.append({
                "id": cid,
                "tableId": tid,
                "name": col["col"],
                "comment": "",
                "dataType": to_vuerd_type(col["type"]),
                "default": "",
                "option": {
                    "autoIncrement": auto_inc,
                    "primaryKey": is_pk,
                    "unique": col["key"] == "UNI",
                    "notNull": not_null,
                },
                "ui": {
                    "active": False,
                    "pk": is_pk and not is_fk,
                    "fk": is_fk and not is_pk,
                    "pfk": is_pfk,
                    "widthName": width_name,
                    "widthComment": 60,
                    "widthDataType": width_type,
                    "widthDefault": 60,
                },
            })

        vuerd_tables.append({
            "id": tid,
            "name": t,
            "comment": mod,
            "columns": vuerd_cols,
            "ui": {
                "active": False,
                "left": lx,
                "top": ly,
                "zIndex": 1,
                "widthName": width_name,
                "widthComment": 60,
            },
            "meta": {
                "openColor": True,
                "color": color,
            },
        })

    # ── Relaciones
    vuerd_rels = []
    for i, fk in enumerate(fks):
        rid = f"R{i+1:06d}"
        src_tid = table_id.get(fk["ref_table"])
        tgt_tid = table_id.get(fk["table"])
        src_cid_key = (fk["ref_table"], fk["ref_col"])
        tgt_cid_key = (fk["table"], fk["col"])
        src_cid = col_id.get(src_cid_key)
        tgt_cid = col_id.get(tgt_cid_key)

        if not all([src_tid, tgt_tid, src_cid, tgt_cid]):
            continue

        # Si la FK es también PK → identificativa (pfk)
        tgt_cols = schema.get(fk["table"], [])
        tgt_col_info = next((c for c in tgt_cols if c["col"] == fk["col"]), None)
        identification = bool(tgt_col_info and tgt_col_info["is_pk"] and tgt_col_info["is_fk"])

        vuerd_rels.append({
            "id": rid,
            "type": "ZeroN",
            "identification": identification,
            "start": {
                "tableId": src_tid,
                "columnIds": [src_cid],
                "x": 0,
                "y": 0,
                "direction": "right",
            },
            "end": {
                "tableId": tgt_tid,
                "columnIds": [tgt_cid],
                "x": 0,
                "y": 0,
                "direction": "left",
            },
        })

    return {
        "canvas": {
            "version": "2.2.11",
            "width": canvas_size,
            "height": canvas_size,
            "scrollTop": 0,
            "scrollLeft": 0,
            "zoomLevel": 1,
            "show": {
                "tableComment": True,
                "columnComment": False,
                "columnDataType": True,
                "columnDefault": False,
                "columnAutoIncrement": True,
                "columnPrimaryKey": True,
                "columnUnique": False,
                "columnNotNull": True,
                "relationship": True,
            },
            "database": "MySQL",
            "databaseName": db_name,
            "orderType": "columnOrder",
        },
        "table": {
            "tables": vuerd_tables,
            "memos": [],
        },
        "relationship": {
            "relationships": vuerd_rels,
        },
    }


# ── Definición de bloques ─────────────────────────────────────────────────────

def tables_for_block(module: str, schema: dict, all_fks: list) -> list:
    """Tablas del módulo + tablas referenciadas en 1 nivel."""
    core = {t for t in schema if TABLE_MODULE.get(t) == module}
    referenced = set()
    for fk in all_fks:
        if fk["table"] in core and fk["ref_table"] not in core:
            referenced.add(fk["ref_table"])
    return sorted(core) + sorted(referenced - core)


BLOCKS = {
    "clientes": {"module": "clientes", "tables_per_row": 4, "canvas": 4000},
    "ventas":   {"module": "ventas",   "tables_per_row": 5, "canvas": 6000},
    "compras":  {"module": "compras",  "tables_per_row": 4, "canvas": 4000},
}


def main():
    out_dir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "docs", "erd")
    )
    os.makedirs(out_dir, exist_ok=True)

    print("⏳ Leyendo esquema de MySQL...")
    schema, all_fks = load_schema()
    print(f"   Tablas: {len(schema)}, FKs: {len(all_fks)}")

    # ── 1. Diagrama completo
    all_tables = sorted(schema.keys())
    print(f"\n📐 Generando vuerd COMPLETO ({len(all_tables)} tablas)...")
    data = generate_vuerd(all_tables, schema, all_fks,
                          tables_per_row=7, canvas_size=10000)
    out = os.path.join(out_dir, "DER_completo.vuerd.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    sz = os.path.getsize(out)
    print(f"   ✅ {out}  ({sz:,} bytes)")

    # ── 2. Bloques
    for block, cfg in BLOCKS.items():
        tables = tables_for_block(cfg["module"], schema, all_fks)
        print(f"\n📐 Generando bloque '{block}' ({len(tables)} tablas)...")
        data = generate_vuerd(tables, schema, all_fks,
                              tables_per_row=cfg["tables_per_row"],
                              canvas_size=cfg["canvas"])
        out = os.path.join(out_dir, f"DER_bloque_{block}.vuerd.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        sz = os.path.getsize(out)
        print(f"   ✅ {out}  ({sz:,} bytes)")

    print("\n🎉 Archivos generados en docs/erd/")
    print("   Instalar extensión: dineug.vuerd-vscode")
    print("   Abrir: clic derecho en el archivo → 'Open with ERD Editor'")


if __name__ == "__main__":
    main()
