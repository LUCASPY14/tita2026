#!/usr/bin/env python3
"""
Genera diagrama Entidad-Relación en formato draw.io (.drawio)
para el proyecto Cantina Tita.

Uso:
    python scripts/generate_der_drawio.py

Salida:
    docs/DER_cantinatita.drawio
"""

import os

HEADER_H = 30   # alto del encabezado de la entidad
ROW_H = 26      # alto de cada campo
ENTITY_W = 220  # ancho total de la entidad
TYPE_W = 48     # ancho de la columna de tipo (PK/FK)
FIELD_W = ENTITY_W - TYPE_W

# Colores por módulo: (fill_header, stroke, fill_row)
COLORS = {
    "clientes":     ("#d5e8d4", "#82b366"),
    "core":         ("#dae8fc", "#6c8ebf"),
    "usuarios":     ("#fff2cc", "#d6b656"),
    "productos":    ("#f8cecc", "#b85450"),
    "ventas":       ("#e1d5e7", "#9673a6"),
    "contabilidad": ("#ffe6cc", "#d79b00"),
    "api":          ("#f5f5f5", "#666666"),
}

# ── Definición de entidades ─────────────────────────────────────────────────
# (id, modulo, nombre_tabla, x, y, [(campo, tipo)])
# tipo: 'PK', 'FK', 'PK/FK', ''
# IDs de entidad: múltiplos de 100 (100..2300)
# IDs de filas:   entity_id + índice_campo (1-based)
# IDs de sub-celdas: 5000 en adelante
# IDs de aristas: 3000 en adelante

ENTITIES = [
    # ── CLIENTES ──────────────────────────────────────────────────────────────
    (100, "clientes", "clientes", 20, 20, [
        ("id_cliente",          "PK"),
        ("nombres",             ""),
        ("apellidos",           ""),
        ("ruc_ci",              ""),
        ("id_lista",            "FK"),
        ("id_tipo_cliente",     "FK"),
        ("activo",              ""),
    ]),
    (200, "clientes", "hijos", 20, 252, [
        ("id_hijo",                 "PK"),
        ("nombre",                  ""),
        ("apellido",                ""),
        ("grado",                   ""),
        ("id_cliente_responsable",  "FK"),
        ("activo",                  ""),
    ]),
    (300, "clientes", "tipos_cliente", 20, 474, [
        ("id_tipo_cliente", "PK"),
        ("nombre_tipo",     ""),
        ("activo",          ""),
    ]),

    # ── CORE / TARJETAS ───────────────────────────────────────────────────────
    (400, "core", "tarjetas", 290, 20, [
        ("nro_tarjeta",     "PK"),
        ("saldo_actual",    ""),
        ("estado",          ""),
        ("fecha_vencimiento",""),
        ("id_hijo",         "FK"),
    ]),
    (500, "core", "cargas_saldo", 290, 202, [
        ("id_carga",        "PK"),
        ("monto_cargado",   ""),
        ("estado",          ""),
        ("metodo_pago",     ""),
        ("comision",        ""),
        ("nro_tarjeta",     "FK"),
        ("id_empleado",     "FK"),
    ]),
    (600, "core", "medios_pago", 290, 448, [
        ("id_medio_pago",   "PK"),
        ("nombre",          ""),
        ("tipo",            ""),
        ("activo",          ""),
    ]),

    # ── USUARIOS ──────────────────────────────────────────────────────────────
    (700, "usuarios", "empleados", 570, 20, [
        ("id_empleado", "PK"),
        ("nombre",      ""),
        ("apellido",    ""),
        ("usuario",     ""),
        ("email",       ""),
        ("activo",      ""),
        ("id_rol",      "FK"),
    ]),
    (800, "usuarios", "roles", 570, 252, [
        ("id_rol",       "PK"),
        ("nombre_rol",   ""),
        ("descripcion",  ""),
        ("activo",       ""),
    ]),
    (900, "usuarios", "perfiles_usuario", 570, 408, [
        ("id_perfil",    "PK"),
        ("id_empleado",  "FK"),
        ("tema",         ""),
        ("idioma",       ""),
    ]),

    # ── PRODUCTOS ─────────────────────────────────────────────────────────────
    (1000, "productos", "productos", 850, 20, [
        ("id_producto",     "PK"),
        ("nombre",          ""),
        ("precio",          ""),
        ("activo",          ""),
        ("id_categoria",    "FK"),
        ("id_unidad_medida","FK"),
    ]),
    (1100, "productos", "categorias", 850, 228, [
        ("id_categoria",        "PK"),
        ("nombre_categoria",    ""),
        ("id_categoria_padre",  "FK"),
    ]),
    (1200, "productos", "stock_unico", 850, 362, [
        ("id_producto",  "PK/FK"),
        ("stock_actual", ""),
        ("stock_minimo", ""),
        ("stock_maximo", ""),
    ]),
    (1300, "clientes", "listas_precios", 850, 500, [
        ("id_lista",     "PK"),
        ("nombre_lista", ""),
        ("activo",       ""),
    ]),

    # ── VENTAS ────────────────────────────────────────────────────────────────
    (1400, "ventas", "ventas", 1130, 20, [
        ("id_venta",    "PK"),
        ("fecha_venta", ""),
        ("total",       ""),
        ("estado",      ""),
        ("id_cliente",  "FK"),
        ("id_empleado", "FK"),
    ]),
    (1500, "ventas", "detalles_venta", 1130, 228, [
        ("id_detalle",      "PK"),
        ("cantidad",        ""),
        ("precio_unitario", ""),
        ("subtotal",        ""),
        ("id_venta",        "FK"),
        ("id_producto",     "FK"),
    ]),
    (1600, "ventas", "devoluciones", 1130, 462, [
        ("id_devolucion",   "PK"),
        ("motivo",          ""),
        ("estado",          ""),
        ("id_venta",        "FK"),
        ("id_empleado",     "FK"),
    ]),

    # ── CONTABILIDAD ──────────────────────────────────────────────────────────
    (1700, "contabilidad", "cajas", 1410, 20, [
        ("id_caja",      "PK"),
        ("nombre",       ""),
        ("estado",       ""),
        ("saldo_inicial",""),
    ]),
    (1800, "contabilidad", "movimientos_caja", 1410, 174, [
        ("id_movimiento",   "PK"),
        ("tipo",            ""),
        ("monto",           ""),
        ("descripcion",     ""),
        ("id_caja",         "FK"),
        ("id_empleado",     "FK"),
    ]),
    (1900, "contabilidad", "cierres_caja", 1410, 396, [
        ("id_cierre",       "PK"),
        ("total_ingresos",  ""),
        ("total_egresos",   ""),
        ("id_caja",         "FK"),
        ("id_empleado",     "FK"),
    ]),

    # ── API / INTEGRACIONES / NOTIFICACIONES ──────────────────────────────────
    (2000, "api", "proveedores_api", 1690, 20, [
        ("id_proveedor",    "PK"),
        ("nombre",          ""),
        ("tipo",            ""),
        ("activo",          ""),
    ]),
    (2100, "api", "endpoints_api", 1690, 174, [
        ("id_endpoint",     "PK"),
        ("nombre_endpoint", ""),
        ("url",             ""),
        ("metodo",          ""),
        ("id_proveedor",    "FK"),
    ]),
    (2200, "api", "alertas_sistema", 1690, 356, [
        ("id_alerta",       "PK"),
        ("tipo",            ""),
        ("mensaje",         ""),
        ("estado",          ""),
        ("fecha_creacion",  ""),
    ]),
    (2300, "api", "notificaciones_portal", 1690, 512, [
        ("id_notificacion", "PK"),
        ("tipo",            ""),
        ("titulo",          ""),
        ("mensaje",         ""),
        ("leida",           ""),
    ]),
]

# ── Relaciones ───────────────────────────────────────────────────────────────
# (entidad_origen, campo_origen(1-base), entidad_destino, campo_destino(1-base), etiqueta)
# La flecha va de PK origen al FK destino
EDGES = [
    # clientes ← hijos
    (100, 1,    200, 5,     "1:N"),   # clientes.id_cliente  →  hijos.id_cliente_responsable
    # hijos ← tarjetas
    (200, 1,    400, 5,     "1:N"),   # hijos.id_hijo  →  tarjetas.id_hijo
    # tarjetas ← cargas_saldo
    (400, 1,    500, 6,     "1:N"),   # tarjetas.nro_tarjeta  →  cargas_saldo.nro_tarjeta
    # empleados → cargas_saldo (supervisor)
    (700, 1,    500, 7,     "1:N"),   # empleados.id_empleado  →  cargas_saldo.id_empleado
    # tipos_cliente → clientes
    (300, 1,    100, 6,     "1:N"),   # tipos_cliente  →  clientes.id_tipo_cliente
    # listas_precios → clientes
    (1300, 1,   100, 5,     "1:N"),   # listas_precios  →  clientes.id_lista
    # roles → empleados
    (800, 1,    700, 7,     "1:N"),   # roles  →  empleados.id_rol
    # empleados ↔ perfiles
    (700, 1,    900, 2,     "1:1"),   # empleados  →  perfiles_usuario
    # categorias → productos
    (1100, 1,   1000, 5,    "1:N"),   # categorias  →  productos.id_categoria
    # productos ↔ stock_unico
    (1000, 1,   1200, 1,    "1:1"),   # productos  →  stock_unico
    # clientes → ventas
    (100, 1,    1400, 5,    "1:N"),   # clientes  →  ventas.id_cliente
    # empleados → ventas
    (700, 1,    1400, 6,    "1:N"),   # empleados  →  ventas.id_empleado
    # ventas → detalles_venta
    (1400, 1,   1500, 5,    "1:N"),   # ventas  →  detalles_venta.id_venta
    # productos → detalles_venta
    (1000, 1,   1500, 6,    "1:N"),   # productos  →  detalles_venta.id_producto
    # ventas → devoluciones
    (1400, 1,   1600, 4,    "1:N"),   # ventas  →  devoluciones.id_venta
    # empleados → devoluciones
    (700, 1,    1600, 5,    "1:N"),   # empleados  →  devoluciones.id_empleado
    # cajas → movimientos_caja
    (1700, 1,   1800, 5,    "1:N"),   # cajas  →  movimientos_caja.id_caja
    # empleados → movimientos_caja
    (700, 1,    1800, 6,    "1:N"),   # empleados  →  movimientos_caja.id_empleado
    # cajas → cierres_caja
    (1700, 1,   1900, 4,    "1:N"),   # cajas  →  cierres_caja.id_caja
    # empleados → cierres_caja
    (700, 1,    1900, 5,    "1:N"),   # empleados  →  cierres_caja.id_empleado
    # proveedores_api → endpoints_api
    (2000, 1,   2100, 5,    "1:N"),   # proveedores_api  →  endpoints_api.id_proveedor
]


# ── Generador XML ─────────────────────────────────────────────────────────────

def esc(s: str) -> str:
    """Escapa caracteres especiales para XML."""
    return (s
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def entity_height(fields) -> int:
    return HEADER_H + len(fields) * ROW_H


def generate() -> str:
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<mxfile host="Electron" version="21.7.6" type="device">')
    lines.append('  <diagram id="DER_CantinaTitle" name="DER Cantina Tita">')
    lines.append(
        '    <mxGraphModel dx="2400" dy="1600" grid="1" gridSize="10" guides="1" '
        'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
        'pageWidth="2339" pageHeight="1654" math="0" shadow="0">'
    )
    lines.append("      <root>")
    lines.append('        <mxCell id="0"/>')
    lines.append('        <mxCell id="1" parent="0"/>')

    # ── Etiquetas de módulo (rectángulos de fondo)
    module_backgrounds = {
        "clientes":     (10,    10,   260, 610),
        "core":         (278,   10,   265, 610),
        "usuarios":     (558,   10,   245, 610),
        "productos":    (838,   10,   245, 620),
        "ventas":       (1118,  10,   245, 620),
        "contabilidad": (1398,  10,   245, 610),
        "api":          (1678,  10,   245, 700),
    }
    MODULE_LABELS = {
        "clientes":     "CLIENTES",
        "core":         "CORE / TARJETAS",
        "usuarios":     "USUARIOS",
        "productos":    "PRODUCTOS",
        "ventas":       "VENTAS",
        "contabilidad": "CONTABILIDAD",
        "api":          "API / NOTIFICACIONES",
    }
    bg_id_start = 4000
    for i, (mod, (bx, by, bw, bh)) in enumerate(module_backgrounds.items()):
        fill, stroke = COLORS[mod]
        bg_id = bg_id_start + i
        label = MODULE_LABELS[mod]
        lines.append(
            f'        <mxCell id="{bg_id}" value="{esc(label)}" '
            f'style="swimlane;startSize=22;fillColor={fill}33;strokeColor={stroke};'
            f'fontStyle=1;fontSize=12;fontColor={stroke};align=center;'
            f'verticalAlign=top;collapsible=0;pointerEvents=0;" '
            f'vertex="1" parent="1">'
        )
        lines.append(f'          <mxGeometry x="{bx}" y="{by}" width="{bw}" height="{bh}" as="geometry"/>')
        lines.append("        </mxCell>")

    # ── Entidades (tablas)
    sub_id = 5000  # contador para sub-celdas de filas

    for entity_id, module, name, x, y, fields in ENTITIES:
        fill, stroke = COLORS[module]
        h = entity_height(fields)

        # Contenedor tabla
        lines.append(
            f'        <mxCell id="{entity_id}" value="{esc(name)}" '
            f'style="shape=table;startSize={HEADER_H};container=1;collapsible=1;'
            f'childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;align=center;'
            f'resizeLast=1;fontSize=13;fillColor={fill};strokeColor={stroke};" '
            f'vertex="1" parent="1">'
        )
        lines.append(f'          <mxGeometry x="{x}" y="{y}" width="{ENTITY_W}" height="{h}" as="geometry"/>')
        lines.append("        </mxCell>")

        # Filas de campos
        for i, (fname, ftype) in enumerate(fields, 1):
            row_id = entity_id + i
            row_y = HEADER_H + (i - 1) * ROW_H
            is_last = i == len(fields)
            bottom = "1" if is_last else "0"

            lines.append(
                f'        <mxCell id="{row_id}" value="" '
                f'style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;'
                f'swimlaneBody=0;fillColor=none;collapsible=0;dropTarget=0;'
                f'points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontSize=12;'
                f'top=0;left=0;right=0;bottom={bottom};" '
                f'vertex="1" parent="{entity_id}">'
            )
            lines.append(f'          <mxGeometry y="{row_y}" width="{ENTITY_W}" height="{ROW_H}" as="geometry"/>')
            lines.append("        </mxCell>")

            # Sub-celda izquierda: tipo (PK / FK)
            type_bg = "#fff2cc" if ftype == "PK" else ("#dae8fc" if "FK" in ftype else "none")
            type_style = "fontStyle=1;" if ftype else ""
            sub_id += 1
            lines.append(
                f'        <mxCell id="{sub_id}" value="{esc(ftype)}" '
                f'style="shape=partialRectangle;connectable=0;fillColor={type_bg};'
                f'top=0;left=0;bottom=0;right=0;{type_style}overflow=hidden;fontSize=11;" '
                f'vertex="1" parent="{row_id}">'
            )
            lines.append(
                f'          <mxGeometry width="{TYPE_W}" height="{ROW_H}" as="geometry">'
                f'<mxRectangle width="{TYPE_W}" height="{ROW_H}" as="alternateBounds"/>'
                f"</mxGeometry>"
            )
            lines.append("        </mxCell>")

            # Sub-celda derecha: nombre del campo
            sub_id += 1
            lines.append(
                f'        <mxCell id="{sub_id}" value="{esc(fname)}" '
                f'style="shape=partialRectangle;connectable=0;fillColor=none;'
                f'top=0;left=0;bottom=0;right=0;overflow=hidden;fontSize=12;" '
                f'vertex="1" parent="{row_id}">'
            )
            lines.append(
                f'          <mxGeometry x="{TYPE_W}" width="{FIELD_W}" height="{ROW_H}" as="geometry">'
                f'<mxRectangle width="{FIELD_W}" height="{ROW_H}" as="alternateBounds"/>'
                f"</mxGeometry>"
            )
            lines.append("        </mxCell>")

    # ── Aristas (relaciones)
    for edge_idx, (src_eid, src_fidx, tgt_eid, tgt_fidx, label) in enumerate(EDGES):
        edge_id = 3000 + edge_idx
        src_row = src_eid + src_fidx
        tgt_row = tgt_eid + tgt_fidx
        edge_style = (
            "edgeStyle=entityRelationEdgeStyle;html=1;"
            "endArrow=ERmany;endFill=0;startArrow=ERone;startFill=0;"
            "exitX=1;exitY=0.5;exitDx=0;exitDy=0;"
            "entryX=0;entryY=0.5;entryDx=0;entryDy=0;"
            "fontSize=11;fontStyle=1;"
        )
        lines.append(
            f'        <mxCell id="{edge_id}" value="{esc(label)}" '
            f'style="{edge_style}" '
            f'edge="1" source="{src_row}" target="{tgt_row}" parent="1">'
        )
        lines.append('          <mxGeometry relative="1" as="geometry"/>')
        lines.append("        </mxCell>")

    lines.append("      </root>")
    lines.append("    </mxGraphModel>")
    lines.append("  </diagram>")
    lines.append("</mxfile>")

    return "\n".join(lines)


if __name__ == "__main__":
    content = generate()

    out_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    out_path = os.path.normpath(os.path.join(out_dir, "DER_cantinatita.drawio"))

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Generado: {out_path}")
    print(f"   Tamaño : {len(content):,} bytes")
    print(f"   Módulos: clientes, core/tarjetas, usuarios, productos, ventas, contabilidad, api")
    print(f"   Tablas : {len(ENTITIES)}")
    print(f"   Relaciones: {len(EDGES)}")
    print()
    print("Abrir con: draw.io (app de escritorio) o app.diagrams.net")
