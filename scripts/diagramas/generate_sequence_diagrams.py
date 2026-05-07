"""
Generador de Diagramas de Secuencia – Cantina Tita
====================================================
Genera un JPG tamaño carta (8.5 × 11 in, 150 dpi) por módulo.
Cada diagrama muestra el flujo principal de mensajes entre participantes.
Salida: docs/sequence_diagrams/jpg/
"""

import os
import io
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrow
from matplotlib.lines import Line2D
from PIL import Image

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────────────────────
DPI   = 150
FIG_W = 8.5
FIG_H = 11.0

# Colores
C_BG         = "#FAFAFA"
C_TITLE_BG   = "#1565C0"
C_TITLE_TEXT = "#FFFFFF"
C_FOOTER_BG  = "#E3F2FD"
C_FOOTER_TXT = "#1565C0"

C_LIFELINE   = "#B0BEC5"
C_BOX_ACTOR  = "#1565C0"
C_BOX_SYSTEM = "#1976D2"
C_BOX_EXT    = "#6A1B9A"
C_BOX_TEXT   = "#FFFFFF"

C_MSG_SYNC   = "#0D47A1"   # flecha sólida  → llamada síncrona
C_MSG_RETURN = "#546E7A"   # flecha punteada ← retorno
C_MSG_ASYNC  = "#E65100"   # flecha open    → asíncrono / evento
C_ALT_BG     = "#FFF9C4"   # fondo bloque alt/loop
C_ALT_BORDER = "#F9A825"
C_NOTE_BG    = "#E8F5E9"
C_NOTE_BORDER= "#388E3C"
C_NOTE_TEXT  = "#1B5E20"
C_SEL_BG     = "#EDE7F6"
C_ACT_BOX    = "#90CAF9"   # caja de activación

FONT = "DejaVu Sans"


# ─────────────────────────────────────────────────────────────────────────────
# DEFINICIÓN DE DIAGRAMAS
#   participants: [{"name", "type": "actor"|"system"|"ext", "short"}]
#   steps: lista ordenada de instrucciones de dibujo
#     {"type":"msg",  "frm":"A","to":"B","label":"texto","style":"sync"|"return"|"async"}
#     {"type":"self", "who":"A","label":"texto"}
#     {"type":"alt",  "label":"[condición]","start":True|False}   (True=abre, False=cierra)
#     {"type":"note", "who":"A","label":"texto"}
#     {"type":"sep",  "label":""}    separador visual (línea horizontal punteada)
# ─────────────────────────────────────────────────────────────────────────────

DIAGRAMS = [

    # ── 1. Autenticación – Iniciar Sesión ────────────────────────────────
    {
        "title":    "Autenticación y Seguridad – Iniciar Sesión",
        "filename": "01_autenticacion_inicio_sesion",
        "participants": [
            {"name": "Empleado",      "type": "actor",  "short": "Emp"},
            {"name": "Frontend",      "type": "system", "short": "FE"},
            {"name": "AuthService",   "type": "system", "short": "Auth"},
            {"name": "BD Usuarios",   "type": "system", "short": "BD"},
            {"name": "JWT Token",     "type": "ext",    "short": "JWT"},
        ],
        "steps": [
            {"type":"msg",  "frm":"Empleado",    "to":"Frontend",    "label":"Ingresa usuario\ny contraseña",                "style":"sync"},
            {"type":"msg",  "frm":"Frontend",    "to":"AuthService", "label":"POST /api/auth/login/",                        "style":"sync"},
            {"type":"msg",  "frm":"AuthService", "to":"BD Usuarios", "label":"Buscar empleado\npor usuario",                 "style":"sync"},
            {"type":"msg",  "frm":"BD Usuarios", "to":"AuthService", "label":"Retorna datos\ndel empleado",                  "style":"return"},
            {"type":"alt",  "label":"[Credenciales válidas]",         "start":True},
            {"type":"msg",  "frm":"AuthService", "to":"AuthService", "label":"Verificar bcrypt\nhash contraseña",            "style":"sync"},
            {"type":"msg",  "frm":"AuthService", "to":"JWT Token",   "label":"Generar access token\n+ refresh token",        "style":"sync"},
            {"type":"msg",  "frm":"JWT Token",   "to":"AuthService", "label":"Retorna tokens",                               "style":"return"},
            {"type":"msg",  "frm":"AuthService", "to":"BD Usuarios", "label":"Registrar sesión\nactiva",                     "style":"async"},
            {"type":"msg",  "frm":"AuthService", "to":"Frontend",    "label":"200 OK {access, refresh}",                     "style":"return"},
            {"type":"msg",  "frm":"Frontend",    "to":"Empleado",    "label":"Redirige al Dashboard",                        "style":"return"},
            {"type":"alt",  "label":"[Credenciales inválidas]",       "start":False},
            {"type":"msg",  "frm":"AuthService", "to":"BD Usuarios", "label":"Registrar intento\nfallido",                   "style":"async"},
            {"type":"msg",  "frm":"AuthService", "to":"Frontend",    "label":"401 Unauthorized",                             "style":"return"},
            {"type":"msg",  "frm":"Frontend",    "to":"Empleado",    "label":"Muestra error\nde credenciales",               "style":"return"},
            {"type":"sep",  "label":""},
            {"type":"note", "who":"AuthService", "label":"Bloquea cuenta\ntras 5 intentos fallidos"},
        ],
    },

    # ── 2. Clientes – Registrar Cliente e Hijo ────────────────────────────
    {
        "title":    "Gestión de Clientes e Hijos – Registrar Cliente e Hijo",
        "filename": "02_clientes_registro",
        "participants": [
            {"name": "Empleado",      "type": "actor",  "short": "Emp"},
            {"name": "Frontend",      "type": "system", "short": "FE"},
            {"name": "API Clientes",  "type": "system", "short": "API"},
            {"name": "BD",            "type": "system", "short": "BD"},
            {"name": "Servicio\nEmail","type": "ext",   "short": "Email"},
        ],
        "steps": [
            {"type":"msg",  "frm":"Empleado",     "to":"Frontend",    "label":"Completa formulario\nde cliente",             "style":"sync"},
            {"type":"msg",  "frm":"Frontend",     "to":"API Clientes","label":"POST /api/clientes/",                         "style":"sync"},
            {"type":"msg",  "frm":"API Clientes", "to":"API Clientes","label":"Validar RUC/CI\ny datos requeridos",          "style":"sync"},
            {"type":"alt",  "label":"[Datos válidos]",                 "start":True},
            {"type":"msg",  "frm":"API Clientes", "to":"BD",          "label":"INSERT Clientes",                             "style":"sync"},
            {"type":"msg",  "frm":"BD",           "to":"API Clientes","label":"id_cliente nuevo",                            "style":"return"},
            {"type":"msg",  "frm":"Empleado",     "to":"Frontend",    "label":"Ingresa datos\ndel hijo/estudiante",          "style":"sync"},
            {"type":"msg",  "frm":"Frontend",     "to":"API Clientes","label":"POST /api/hijos/",                            "style":"sync"},
            {"type":"msg",  "frm":"API Clientes", "to":"BD",          "label":"INSERT Hijos\n(con id_cliente)",              "style":"sync"},
            {"type":"msg",  "frm":"BD",           "to":"API Clientes","label":"id_hijo nuevo",                               "style":"return"},
            {"type":"msg",  "frm":"API Clientes", "to":"Servicio\nEmail","label":"Enviar bienvenida\nal cliente",            "style":"async"},
            {"type":"msg",  "frm":"API Clientes", "to":"Frontend",    "label":"201 Created {cliente, hijo}",                 "style":"return"},
            {"type":"msg",  "frm":"Frontend",     "to":"Empleado",    "label":"Confirmación\nregistro exitoso",              "style":"return"},
            {"type":"alt",  "label":"[Datos inválidos / duplicado]",   "start":False},
            {"type":"msg",  "frm":"API Clientes", "to":"Frontend",    "label":"400 Bad Request\n{errors}",                   "style":"return"},
            {"type":"msg",  "frm":"Frontend",     "to":"Empleado",    "label":"Muestra errores\nde validación",              "style":"return"},
            {"type":"sep",  "label":""},
            {"type":"note", "who":"API Clientes", "label":"Valida unicidad\nRUC/CI en la BD"},
        ],
    },

    # ── 3. Tarjetas – Recargar Saldo ──────────────────────────────────────
    {
        "title":    "Tarjetas y Recargas – Recarga de Saldo (Efectivo)",
        "filename": "03_tarjetas_recarga_efectivo",
        "participants": [
            {"name": "Cajero",        "type": "actor",  "short": "Caj"},
            {"name": "Frontend",      "type": "system", "short": "FE"},
            {"name": "API Core",      "type": "system", "short": "API"},
            {"name": "RecargaService","type": "system", "short": "Svc"},
            {"name": "BD",            "type": "system", "short": "BD"},
        ],
        "steps": [
            {"type":"msg",  "frm":"Cajero",       "to":"Frontend",     "label":"Busca tarjeta\ndel estudiante",              "style":"sync"},
            {"type":"msg",  "frm":"Frontend",     "to":"API Core",     "label":"GET /api/tarjetas/?nro=...",                 "style":"sync"},
            {"type":"msg",  "frm":"API Core",     "to":"BD",           "label":"SELECT Tarjetas",                            "style":"sync"},
            {"type":"msg",  "frm":"BD",           "to":"API Core",     "label":"Datos tarjeta\n+ saldo actual",              "style":"return"},
            {"type":"msg",  "frm":"API Core",     "to":"Frontend",     "label":"200 OK {tarjeta}",                           "style":"return"},
            {"type":"msg",  "frm":"Cajero",       "to":"Frontend",     "label":"Ingresa monto\ny método=efectivo",           "style":"sync"},
            {"type":"msg",  "frm":"Frontend",     "to":"API Core",     "label":"POST /api/cargas-saldo/",                    "style":"sync"},
            {"type":"msg",  "frm":"API Core",     "to":"API Core",     "label":"Validar monto,\ntarjeta activa",             "style":"sync"},
            {"type":"msg",  "frm":"API Core",     "to":"BD",           "label":"INSERT CargasSaldo\n(estado=pendiente)",     "style":"sync"},
            {"type":"msg",  "frm":"BD",           "to":"API Core",     "label":"id_carga",                                   "style":"return"},
            {"type":"msg",  "frm":"API Core",     "to":"RecargaService","label":"acreditar_saldo(carga)",                    "style":"sync"},
            {"type":"msg",  "frm":"RecargaService","to":"BD",          "label":"UPDATE Tarjetas\nSET saldo += monto",        "style":"sync"},
            {"type":"msg",  "frm":"RecargaService","to":"BD",          "label":"INSERT ConsumosTarjeta\n(registro auditoría)","style":"sync"},
            {"type":"msg",  "frm":"RecargaService","to":"BD",          "label":"UPDATE CargasSaldo\n(estado=completada)",    "style":"sync"},
            {"type":"msg",  "frm":"RecargaService","to":"API Core",    "label":"Retorna resultado",                          "style":"return"},
            {"type":"msg",  "frm":"API Core",     "to":"Frontend",     "label":"201 Created {recarga, saldo_nuevo}",         "style":"return"},
            {"type":"msg",  "frm":"Frontend",     "to":"Cajero",       "label":"Muestra saldo\nactualizado",                 "style":"return"},
            {"type":"note", "who":"RecargaService","label":"Operación atómica\n(transaction.atomic)"},
        ],
    },

    # ── 4. Punto de Venta – Registrar Venta ───────────────────────────────
    {
        "title":    "Punto de Venta – Registrar Venta con Tarjeta",
        "filename": "04_ventas_registro",
        "participants": [
            {"name": "Cajero",        "type": "actor",  "short": "Caj"},
            {"name": "Frontend",      "type": "system", "short": "FE"},
            {"name": "API Ventas",    "type": "system", "short": "API"},
            {"name": "Inventario\nSvc","type": "system","short": "Inv"},
            {"name": "BD",            "type": "system", "short": "BD"},
        ],
        "steps": [
            {"type":"msg",  "frm":"Cajero",       "to":"Frontend",    "label":"Escanea/busca\nproducto",                     "style":"sync"},
            {"type":"msg",  "frm":"Frontend",     "to":"API Ventas",  "label":"GET /api/productos/?q=...",                   "style":"sync"},
            {"type":"msg",  "frm":"API Ventas",   "to":"BD",          "label":"SELECT Productos\n(con stock)",               "style":"sync"},
            {"type":"msg",  "frm":"BD",           "to":"API Ventas",  "label":"Datos producto\n+ precio",                   "style":"return"},
            {"type":"msg",  "frm":"API Ventas",   "to":"Frontend",    "label":"200 OK {productos}",                          "style":"return"},
            {"type":"msg",  "frm":"Cajero",       "to":"Frontend",    "label":"Selecciona items\ny confirma venta",          "style":"sync"},
            {"type":"msg",  "frm":"Frontend",     "to":"API Ventas",  "label":"POST /api/ventas/\n{items, nro_tarjeta}",     "style":"sync"},
            {"type":"msg",  "frm":"API Ventas",   "to":"BD",          "label":"SELECT saldo\nTarjeta (lock)",               "style":"sync"},
            {"type":"alt",  "label":"[Saldo suficiente]",              "start":True},
            {"type":"msg",  "frm":"API Ventas",   "to":"BD",          "label":"INSERT Ventas\n+ DetalleVentas",              "style":"sync"},
            {"type":"msg",  "frm":"API Ventas",   "to":"Inventario\nSvc","label":"Descontar stock\npor items vendidos",      "style":"async"},
            {"type":"msg",  "frm":"API Ventas",   "to":"BD",          "label":"UPDATE saldo\nTarjeta -= total",              "style":"sync"},
            {"type":"msg",  "frm":"API Ventas",   "to":"BD",          "label":"INSERT ConsumosTarjeta\n(registro consumo)",   "style":"sync"},
            {"type":"msg",  "frm":"API Ventas",   "to":"Frontend",    "label":"201 Created {venta, ticket}",                 "style":"return"},
            {"type":"msg",  "frm":"Frontend",     "to":"Cajero",      "label":"Imprime/muestra\nticket",                    "style":"return"},
            {"type":"alt",  "label":"[Saldo insuficiente]",            "start":False},
            {"type":"msg",  "frm":"API Ventas",   "to":"Frontend",    "label":"400 Saldo insuficiente",                      "style":"return"},
            {"type":"msg",  "frm":"Frontend",     "to":"Cajero",      "label":"Solicita autorización\no método alternativo", "style":"return"},
            {"type":"sep",  "label":""},
            {"type":"note", "who":"API Ventas",   "label":"SELECT … FOR UPDATE\nevita condición de carrera"},
        ],
    },

    # ── 5. Almuerzos – Registrar Asistencia ───────────────────────────────
    {
        "title":    "Gestión de Almuerzos – Registrar Asistencia Diaria",
        "filename": "05_almuerzos_asistencia",
        "participants": [
            {"name": "Cajero",        "type": "actor",  "short": "Caj"},
            {"name": "Frontend",      "type": "system", "short": "FE"},
            {"name": "API Almuerzos", "type": "system", "short": "API"},
            {"name": "BD",            "type": "system", "short": "BD"},
            {"name": "Facturación\nSvc","type": "system","short": "Fact"},
        ],
        "steps": [
            {"type":"msg",  "frm":"Cajero",       "to":"Frontend",     "label":"Abre asistencia\ndel día",                  "style":"sync"},
            {"type":"msg",  "frm":"Frontend",     "to":"API Almuerzos","label":"GET /api/menu-dia/?fecha=hoy",               "style":"sync"},
            {"type":"msg",  "frm":"API Almuerzos","to":"BD",           "label":"SELECT MenuDia\n+ PlanesAlmuerzos activos",  "style":"sync"},
            {"type":"msg",  "frm":"BD",           "to":"API Almuerzos","label":"Lista de estudiantes\ncon plan activo",      "style":"return"},
            {"type":"msg",  "frm":"API Almuerzos","to":"Frontend",     "label":"200 OK {menu, estudiantes}",                 "style":"return"},
            {"type":"msg",  "frm":"Cajero",       "to":"Frontend",     "label":"Marca asistencia\npor estudiante",           "style":"sync"},
            {"type":"msg",  "frm":"Frontend",     "to":"API Almuerzos","label":"POST /api/asistencia-almuerzo/\n{id_hijo, fecha, presente}","style":"sync"},
            {"type":"msg",  "frm":"API Almuerzos","to":"BD",           "label":"Verificar plan\nactivo del hijo",            "style":"sync"},
            {"type":"alt",  "label":"[Tiene plan activo]",              "start":True},
            {"type":"msg",  "frm":"API Almuerzos","to":"BD",           "label":"INSERT AsistenciaAlmuerzo",                  "style":"sync"},
            {"type":"msg",  "frm":"BD",           "to":"API Almuerzos","label":"OK",                                         "style":"return"},
            {"type":"msg",  "frm":"API Almuerzos","to":"Frontend",     "label":"201 Created",                                "style":"return"},
            {"type":"alt",  "label":"[Sin plan / ausente justificado]", "start":False},
            {"type":"msg",  "frm":"API Almuerzos","to":"BD",           "label":"INSERT Ausencia\nJustificada",               "style":"sync"},
            {"type":"msg",  "frm":"API Almuerzos","to":"Frontend",     "label":"201 Created (ausencia)",                     "style":"return"},
            {"type":"sep",  "label":""},
            {"type":"msg",  "frm":"Cajero",       "to":"Frontend",     "label":"Cierra asistencia\ndel día",                 "style":"sync"},
            {"type":"msg",  "frm":"Frontend",     "to":"API Almuerzos","label":"POST /api/cerrar-dia/",                      "style":"sync"},
            {"type":"msg",  "frm":"API Almuerzos","to":"Facturación\nSvc","label":"Generar pre-factura\nmensual (async)",    "style":"async"},
            {"type":"msg",  "frm":"API Almuerzos","to":"Frontend",     "label":"200 OK",                                     "style":"return"},
        ],
    },

    # ── 6. Inventario – Registrar Movimiento de Stock ─────────────────────
    {
        "title":    "Control de Inventario – Registrar Movimiento de Stock",
        "filename": "06_inventario_movimiento",
        "participants": [
            {"name": "Encargado",     "type": "actor",  "short": "Enc"},
            {"name": "Frontend",      "type": "system", "short": "FE"},
            {"name": "API Inventario","type": "system", "short": "API"},
            {"name": "AlertaSvc",     "type": "system", "short": "Alr"},
            {"name": "BD",            "type": "system", "short": "BD"},
        ],
        "steps": [
            {"type":"msg",  "frm":"Encargado",    "to":"Frontend",     "label":"Selecciona producto\ny tipo de movimiento",  "style":"sync"},
            {"type":"msg",  "frm":"Frontend",     "to":"API Inventario","label":"POST /api/movimientos-stock/\n{producto, cantidad, tipo}","style":"sync"},
            {"type":"msg",  "frm":"API Inventario","to":"BD",          "label":"SELECT Inventario\n(stock actual, mínimo)",  "style":"sync"},
            {"type":"msg",  "frm":"BD",           "to":"API Inventario","label":"Stock actual",                              "style":"return"},
            {"type":"msg",  "frm":"API Inventario","to":"API Inventario","label":"Calcular\nnuevo stock",                   "style":"sync"},
            {"type":"alt",  "label":"[Stock no negativo]",              "start":True},
            {"type":"msg",  "frm":"API Inventario","to":"BD",          "label":"UPDATE Inventario\nSET stock = nuevo",       "style":"sync"},
            {"type":"msg",  "frm":"API Inventario","to":"BD",          "label":"INSERT MovimientosStock\n(auditoría)",       "style":"sync"},
            {"type":"msg",  "frm":"BD",           "to":"API Inventario","label":"OK",                                        "style":"return"},
            {"type":"msg",  "frm":"API Inventario","to":"AlertaSvc",   "label":"Verificar umbral\nstock mínimo",             "style":"async"},
            {"type":"msg",  "frm":"AlertaSvc",    "to":"BD",           "label":"Notificar alerta\nstock bajo (si aplica)",   "style":"async"},
            {"type":"msg",  "frm":"API Inventario","to":"Frontend",    "label":"201 Created {movimiento}",                   "style":"return"},
            {"type":"msg",  "frm":"Frontend",     "to":"Encargado",    "label":"Muestra nuevo\nstock actualizado",           "style":"return"},
            {"type":"alt",  "label":"[Stock insuficiente para salida]", "start":False},
            {"type":"msg",  "frm":"API Inventario","to":"Frontend",    "label":"400 Stock insuficiente",                     "style":"return"},
            {"type":"msg",  "frm":"Frontend",     "to":"Encargado",    "label":"Error: stock\ninsuficiente",                 "style":"return"},
            {"type":"note", "who":"API Inventario","label":"transaction.atomic()\ngarantiza consistencia"},
        ],
    },

    # ── 7. Compras – Crear Orden de Compra ────────────────────────────────
    {
        "title":    "Compras y Proveedores – Crear Orden de Compra",
        "filename": "07_compras_orden",
        "participants": [
            {"name": "Administrador", "type": "actor",  "short": "Adm"},
            {"name": "Frontend",      "type": "system", "short": "FE"},
            {"name": "API Compras",   "type": "system", "short": "API"},
            {"name": "BD",            "type": "system", "short": "BD"},
            {"name": "Email\nProveedor","type": "ext",  "short": "Eml"},
        ],
        "steps": [
            {"type":"msg",  "frm":"Administrador","to":"Frontend",     "label":"Selecciona proveedor\ny productos a pedir",  "style":"sync"},
            {"type":"msg",  "frm":"Frontend",     "to":"API Compras",  "label":"GET /api/proveedores/\n(catálogo precios)",  "style":"sync"},
            {"type":"msg",  "frm":"API Compras",  "to":"BD",           "label":"SELECT Proveedores\n+ PreciosInsumos",       "style":"sync"},
            {"type":"msg",  "frm":"BD",           "to":"API Compras",  "label":"Lista proveedores\ny precios",               "style":"return"},
            {"type":"msg",  "frm":"API Compras",  "to":"Frontend",     "label":"200 OK {proveedores}",                       "style":"return"},
            {"type":"msg",  "frm":"Administrador","to":"Frontend",     "label":"Confirma orden\nde compra",                  "style":"sync"},
            {"type":"msg",  "frm":"Frontend",     "to":"API Compras",  "label":"POST /api/ordenes-compra/\n{proveedor, items, fecha}","style":"sync"},
            {"type":"msg",  "frm":"API Compras",  "to":"API Compras",  "label":"Validar items\ny montos",                   "style":"sync"},
            {"type":"msg",  "frm":"API Compras",  "to":"BD",           "label":"INSERT OrdenCompra\n+ DetalleOrden",         "style":"sync"},
            {"type":"msg",  "frm":"BD",           "to":"API Compras",  "label":"id_orden",                                   "style":"return"},
            {"type":"msg",  "frm":"API Compras",  "to":"BD",           "label":"INSERT CuentasPorPagar",                     "style":"sync"},
            {"type":"msg",  "frm":"API Compras",  "to":"Email\nProveedor","label":"Enviar orden\nal proveedor (email)",      "style":"async"},
            {"type":"msg",  "frm":"API Compras",  "to":"Frontend",     "label":"201 Created {orden}",                        "style":"return"},
            {"type":"msg",  "frm":"Frontend",     "to":"Administrador","label":"Orden creada\ny enviada al proveedor",       "style":"return"},
            {"type":"sep",  "label":""},
            {"type":"msg",  "frm":"Administrador","to":"Frontend",     "label":"Registra recepción\nde mercadería",          "style":"sync"},
            {"type":"msg",  "frm":"Frontend",     "to":"API Compras",  "label":"POST /api/recepciones/\n{id_orden, items_recibidos}","style":"sync"},
            {"type":"msg",  "frm":"API Compras",  "to":"BD",           "label":"UPDATE Inventario\n(incrementar stock)",     "style":"sync"},
            {"type":"msg",  "frm":"API Compras",  "to":"Frontend",     "label":"201 OK",                                     "style":"return"},
        ],
    },

    # ── 8. Reportes – Generar Reporte de Ventas ───────────────────────────
    {
        "title":    "Reportes y Contabilidad – Generar Reporte de Ventas",
        "filename": "08_reportes_ventas",
        "participants": [
            {"name": "Administrador", "type": "actor",  "short": "Adm"},
            {"name": "Frontend",      "type": "system", "short": "FE"},
            {"name": "API Reportes",  "type": "system", "short": "API"},
            {"name": "ReporteService","type": "system", "short": "Svc"},
            {"name": "BD",            "type": "system", "short": "BD"},
        ],
        "steps": [
            {"type":"msg",  "frm":"Administrador","to":"Frontend",     "label":"Selecciona periodo\ny tipo de reporte",      "style":"sync"},
            {"type":"msg",  "frm":"Frontend",     "to":"API Reportes", "label":"GET /api/reportes/ventas/\n?desde=X&hasta=Y","style":"sync"},
            {"type":"msg",  "frm":"API Reportes", "to":"ReporteService","label":"generar_reporte_ventas\n(desde, hasta)",    "style":"sync"},
            {"type":"msg",  "frm":"ReporteService","to":"BD",          "label":"SELECT Ventas\n+ DetalleVentas (agregado)",  "style":"sync"},
            {"type":"msg",  "frm":"BD",           "to":"ReporteService","label":"Datos de ventas\ncon totales",              "style":"return"},
            {"type":"msg",  "frm":"ReporteService","to":"BD",          "label":"SELECT CierresCaja\ndel periodo",            "style":"sync"},
            {"type":"msg",  "frm":"BD",           "to":"ReporteService","label":"Datos de\ncierres de caja",                "style":"return"},
            {"type":"msg",  "frm":"ReporteService","to":"ReporteService","label":"Calcular KPIs:\ntotal, promedio, top products","style":"sync"},
            {"type":"msg",  "frm":"ReporteService","to":"API Reportes","label":"Retorna reporte\ncompleto",                  "style":"return"},
            {"type":"msg",  "frm":"API Reportes", "to":"Frontend",     "label":"200 OK {reporte, kpis}",                    "style":"return"},
            {"type":"msg",  "frm":"Frontend",     "to":"Administrador","label":"Muestra dashboard\ncon gráficas",           "style":"return"},
            {"type":"sep",  "label":""},
            {"type":"msg",  "frm":"Administrador","to":"Frontend",     "label":"Solicita exportar\na CSV/PDF",              "style":"sync"},
            {"type":"msg",  "frm":"Frontend",     "to":"API Reportes", "label":"GET /api/reportes/ventas/exportar/\n?formato=csv","style":"sync"},
            {"type":"msg",  "frm":"API Reportes", "to":"ReporteService","label":"Generar archivo\nexportable",              "style":"sync"},
            {"type":"msg",  "frm":"ReporteService","to":"API Reportes","label":"Retorna archivo\nbinario",                  "style":"return"},
            {"type":"msg",  "frm":"API Reportes", "to":"Frontend",     "label":"200 OK (archivo adjunto)",                  "style":"return"},
            {"type":"msg",  "frm":"Frontend",     "to":"Administrador","label":"Descarga archivo\nCSV/PDF",                 "style":"return"},
        ],
    },

    # ── 9. Notificaciones – Alerta de Saldo Bajo ──────────────────────────
    {
        "title":    "Notificaciones – Alerta de Saldo Bajo",
        "filename": "09_notificaciones_saldo_bajo",
        "participants": [
            {"name": "Sistema",       "type": "system", "short": "Sis"},
            {"name": "Signal\nDjango","type": "system", "short": "Sig"},
            {"name": "Notif.Svc",    "type": "system", "short": "Svc"},
            {"name": "BD",            "type": "system", "short": "BD"},
            {"name": "Padre /\nCliente","type": "actor","short": "Pad"},
        ],
        "steps": [
            {"type":"msg",  "frm":"Sistema",      "to":"Sistema",      "label":"Consumo registrado\nen tarjeta",             "style":"sync"},
            {"type":"msg",  "frm":"Sistema",      "to":"Signal\nDjango","label":"post_save signal\nConsumosTarjeta",         "style":"async"},
            {"type":"msg",  "frm":"Signal\nDjango","to":"Signal\nDjango","label":"Verificar saldo\nvs umbral alerta",        "style":"sync"},
            {"type":"alt",  "label":"[Saldo <= umbral de alerta]",      "start":True},
            {"type":"msg",  "frm":"Signal\nDjango","to":"Notif.Svc",   "label":"crear_notificacion\n(tipo=saldo_bajo)",      "style":"sync"},
            {"type":"msg",  "frm":"Notif.Svc",    "to":"BD",           "label":"SELECT config\nnotificaciones tarjeta",      "style":"sync"},
            {"type":"msg",  "frm":"BD",           "to":"Notif.Svc",    "label":"Config: canal, umbral,\npush_enabled",       "style":"return"},
            {"type":"msg",  "frm":"Notif.Svc",    "to":"BD",           "label":"INSERT Notificaciones\n(estado=pendiente)",  "style":"sync"},
            {"type":"msg",  "frm":"Notif.Svc",    "to":"BD",           "label":"INSERT AlertasSistema",                      "style":"sync"},
            {"type":"msg",  "frm":"Notif.Svc",    "to":"Notif.Svc",   "label":"Enviar push/email\nal padre",                "style":"async"},
            {"type":"msg",  "frm":"Signal\nDjango","to":"Sistema",     "label":"Notificación\nenviada",                      "style":"return"},
            {"type":"alt",  "label":"[Saldo > umbral]",                 "start":False},
            {"type":"msg",  "frm":"Signal\nDjango","to":"Sistema",     "label":"Sin acción\n(saldo OK)",                    "style":"return"},
            {"type":"sep",  "label":""},
            {"type":"msg",  "frm":"Padre /\nCliente","to":"BD",        "label":"GET /api/notificaciones/\nmisPendientes",    "style":"sync"},
            {"type":"msg",  "frm":"BD",           "to":"Padre /\nCliente","label":"Lista notificaciones\nsin leer",         "style":"return"},
            {"type":"msg",  "frm":"Padre /\nCliente","to":"BD",        "label":"PATCH /api/notificaciones/{id}/\n(marcar leída)","style":"sync"},
            {"type":"msg",  "frm":"BD",           "to":"Padre /\nCliente","label":"200 OK",                                  "style":"return"},
            {"type":"note", "who":"Notif.Svc",    "label":"Respeta configuración\nde notificaciones de la tarjeta"},
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# MOTOR DE DIBUJO
# ─────────────────────────────────────────────────────────────────────────────

# Dimensiones lógicas de la figura (coordenadas internas)
LW  = 10.0    # ancho lógico
LH  = 13.0    # alto lógico

# Fila superior para cabeceras de participantes
HDR_Y   = 12.1
HDR_H   = 0.62   # alto de la caja del participante
HDR_W   = 1.30   # ancho de la caja del participante

# Espacio de mensajes
MSG_TOP = HDR_Y - HDR_H - 0.15   # y donde empiezan los mensajes (de arriba hacia abajo)
MSG_BOT = 0.55                   # y donde terminan las líneas de vida
LINE_H  = 0.68                   # altura por paso de mensaje

# Ancho del bloque de activación
ACT_W   = 0.12


def participant_x(idx, n):
    """Centro X del participante idx sobre n participantes."""
    margin = 0.5
    usable = LW - 2 * margin
    if n == 1:
        return LW / 2
    return margin + idx * usable / (n - 1)


def draw_header_box(ax, cx, y, label, color):
    hw = HDR_W / 2
    ax.add_patch(FancyBboxPatch(
        (cx - hw, y - HDR_H / 2), HDR_W, HDR_H,
        boxstyle="round,pad=0.04",
        facecolor=color, edgecolor="#FFFFFF",
        linewidth=1.2, zorder=5
    ))
    ax.text(cx, y, label, ha="center", va="center",
            fontsize=6.8, fontweight="bold", color=C_BOX_TEXT,
            fontfamily=FONT, zorder=6, multialignment="center")


def color_for_type(ptype):
    return {
        "actor":  C_BOX_ACTOR,
        "system": C_BOX_SYSTEM,
        "ext":    C_BOX_EXT,
    }.get(ptype, C_BOX_SYSTEM)


def arrow_sync(ax, x1, x2, y, label, color=C_MSG_SYNC):
    """Flecha sólida cerrada (llamada síncrona)."""
    going_right = x2 > x1
    ax.annotate("",
                xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.3),
                zorder=4)
    lx = (x1 + x2) / 2
    ax.text(lx, y + 0.05, label, ha="center", va="bottom",
            fontsize=6.2, color=color, fontfamily=FONT,
            multialignment="center", zorder=5)


def arrow_return(ax, x1, x2, y, label, color=C_MSG_RETURN):
    """Flecha punteada (retorno)."""
    ax.annotate("",
                xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.0,
                                linestyle="dashed"),
                zorder=4)
    lx = (x1 + x2) / 2
    ax.text(lx, y + 0.05, label, ha="center", va="bottom",
            fontsize=6.0, color=color, fontfamily=FONT, style="italic",
            multialignment="center", zorder=5)


def arrow_async(ax, x1, x2, y, label, color=C_MSG_ASYNC):
    """Flecha abierta (asíncrona / evento)."""
    ax.annotate("",
                xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="->", color=color, lw=1.2,
                                linestyle="dashed"),
                zorder=4)
    lx = (x1 + x2) / 2
    ax.text(lx, y + 0.05, label, ha="center", va="bottom",
            fontsize=6.0, color=color, fontfamily=FONT,
            multialignment="center", zorder=5)


def arrow_self(ax, cx, y, label, color=C_MSG_SYNC):
    """Bucle de auto-mensaje."""
    r = 0.30
    ax.annotate("",
                xy=(cx, y - 0.18), xytext=(cx, y),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.1,
                                connectionstyle=f"arc3,rad=-0.5"),
                zorder=4)
    ax.text(cx + r + 0.08, y - 0.09, label, ha="left", va="center",
            fontsize=6.0, color=color, fontfamily=FONT,
            multialignment="left", zorder=5)


def draw_alt_block(ax, y_top, y_bot, label, bg=C_ALT_BG, border=C_ALT_BORDER):
    """Rectángulo de bloque combinado (alt/loop)."""
    margin = 0.18
    w = LW - 2 * margin
    h = y_top - y_bot
    ax.add_patch(FancyBboxPatch(
        (margin, y_bot), w, h,
        boxstyle="square,pad=0",
        facecolor=bg, edgecolor=border,
        linewidth=1.0, linestyle="--",
        alpha=0.55, zorder=1
    ))
    ax.text(margin + 0.10, y_top - 0.06, label,
            ha="left", va="top",
            fontsize=6.2, color=border, fontfamily=FONT,
            fontweight="bold", zorder=3)


def draw_note(ax, cx, y, label):
    """Post-it de nota."""
    w, h = 2.0, 0.46
    x0 = cx - w / 2
    ax.add_patch(FancyBboxPatch(
        (x0, y - h / 2), w, h,
        boxstyle="round,pad=0.05",
        facecolor=C_NOTE_BG, edgecolor=C_NOTE_BORDER,
        linewidth=0.9, zorder=4
    ))
    ax.text(cx, y, label, ha="center", va="center",
            fontsize=5.8, color=C_NOTE_TEXT, fontfamily=FONT,
            multialignment="center", zorder=5)


def draw_sep(ax, y):
    """Línea separadora punteada horizontal."""
    ax.plot([0.3, LW - 0.3], [y, y],
            linestyle=":", color="#90A4AE", lw=0.8, zorder=2)


def generate_diagram(diag, output_jpg):
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=DPI)
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)
    ax.set_xlim(0, LW)
    ax.set_ylim(0, LH)
    ax.set_aspect("equal")
    ax.axis("off")

    participants = diag["participants"]
    n = len(participants)
    px = [participant_x(i, n) for i in range(n)]
    name_to_x = {p["name"]: px[i] for i, p in enumerate(participants)}

    # ── Título ───────────────────────────────────────────────────────────
    ax.add_patch(FancyBboxPatch((0, 12.3), LW, 0.65,
                                boxstyle="square,pad=0",
                                facecolor=C_TITLE_BG, edgecolor="none", zorder=6))
    ax.text(LW / 2, 12.63, diag["title"],
            ha="center", va="center",
            fontsize=11, fontweight="bold", color=C_TITLE_TEXT,
            fontfamily=FONT, zorder=7)
    ax.text(LW / 2, 12.30, "Cantina Tita  ·  Diagrama de Secuencia  ·  UML",
            ha="center", va="top", fontsize=6, color="#64B5F6",
            fontfamily=FONT, zorder=7)

    # ── Cabeceras de participantes ────────────────────────────────────────
    for i, p in enumerate(participants):
        c = color_for_type(p["type"])
        draw_header_box(ax, px[i], HDR_Y, p["name"], c)

    # ── Líneas de vida ────────────────────────────────────────────────────
    for x in px:
        ax.plot([x, x], [HDR_Y - HDR_H / 2, MSG_BOT],
                linestyle="--", color=C_LIFELINE, lw=0.9, zorder=0)

    # ── Leyenda ───────────────────────────────────────────────────────────
    leg_x, leg_y = 0.10, 0.70
    # sync
    ax.annotate("", xy=(leg_x + 0.45, leg_y), xytext=(leg_x, leg_y),
                arrowprops=dict(arrowstyle="-|>", color=C_MSG_SYNC, lw=1.0), zorder=4)
    ax.text(leg_x + 0.50, leg_y, "síncrono", va="center", fontsize=5.5,
            color=C_MSG_SYNC, fontfamily=FONT)
    leg_y -= 0.18
    ax.annotate("", xy=(leg_x + 0.45, leg_y), xytext=(leg_x, leg_y),
                arrowprops=dict(arrowstyle="-|>", color=C_MSG_RETURN, lw=1.0,
                                linestyle="dashed"), zorder=4)
    ax.text(leg_x + 0.50, leg_y, "retorno", va="center", fontsize=5.5,
            color=C_MSG_RETURN, fontfamily=FONT, style="italic")
    leg_y -= 0.18
    ax.annotate("", xy=(leg_x + 0.45, leg_y), xytext=(leg_x, leg_y),
                arrowprops=dict(arrowstyle="->", color=C_MSG_ASYNC, lw=1.0,
                                linestyle="dashed"), zorder=4)
    ax.text(leg_x + 0.50, leg_y, "asíncrono", va="center", fontsize=5.5,
            color=C_MSG_ASYNC, fontfamily=FONT)

    # ── Pie de página ─────────────────────────────────────────────────────
    ax.add_patch(FancyBboxPatch((0, 0), LW, 0.38,
                                boxstyle="square,pad=0",
                                facecolor=C_FOOTER_BG, edgecolor=C_TITLE_BG,
                                linewidth=0.5, zorder=6))
    ax.text(LW / 2, 0.19,
            "Cantina Tita  ·  Documento de Análisis  ·  Marzo 2026",
            ha="center", va="center", fontsize=5.8, color=C_FOOTER_TXT,
            fontfamily=FONT, zorder=7)

    # ── Procesar steps ────────────────────────────────────────────────────
    steps = diag["steps"]

    # Primera pasada: calcular altura necesaria total
    # y ajustar desde MSG_TOP hacia abajo
    cur_y = MSG_TOP

    # Acumular bloques alt abiertos (API simple: 1 nivel)
    alt_open_y = None   # y donde abrió el alt

    # Colección de pasos procesados para dibujar bloques alt
    alt_blocks = []   # lista de (y_top, y_bot, label)
    alt_label  = None

    # Para calcular posiciones primero
    step_ys = []
    for step in steps:
        step_ys.append(cur_y)
        t = step["type"]
        if t == "msg":
            cur_y -= LINE_H
        elif t == "self":
            cur_y -= LINE_H * 0.85
        elif t == "alt":
            if step["start"]:
                alt_open_y = cur_y
                alt_label  = step["label"]
                cur_y -= 0.28
            else:
                if alt_open_y is not None:
                    alt_blocks.append((alt_open_y, cur_y, alt_label))
                    alt_open_y = None
                cur_y -= 0.20
        elif t == "note":
            cur_y -= 0.60
        elif t == "sep":
            cur_y -= 0.30

    # Escalar si el contenido no cabe
    content_h = MSG_TOP - MSG_BOT
    used_h    = MSG_TOP - cur_y
    scale = 1.0
    if used_h > content_h and used_h > 0:
        scale = content_h / used_h

    # Segunda pasada: dibujar
    cur_y = MSG_TOP
    alt_open_y = None
    alt_label  = None
    alt_blocks_draw = []

    for step in steps:
        t = step["type"]

        if t == "msg":
            frm  = step["frm"]
            to   = step["to"]
            lbl  = step["label"]
            styl = step["style"]
            x1   = name_to_x.get(frm, LW / 2)
            x2   = name_to_x.get(to,  LW / 2)
            y    = cur_y - LINE_H * scale / 2
            if styl == "return":
                arrow_return(ax, x1, x2, y, lbl)
            elif styl == "async":
                arrow_async(ax, x1, x2, y, lbl)
            else:
                if x1 == x2:
                    arrow_self(ax, x1, y, lbl)
                else:
                    arrow_sync(ax, x1, x2, y, lbl)
            # caja de activación
            act_x = x1 - ACT_W / 2
            act_h = LINE_H * scale * 0.40
            ax.add_patch(FancyBboxPatch(
                (act_x, y - act_h / 2), ACT_W, act_h,
                boxstyle="square,pad=0",
                facecolor=C_ACT_BOX, edgecolor="#1976D2",
                linewidth=0.6, alpha=0.60, zorder=3
            ))
            cur_y -= LINE_H * scale

        elif t == "self":
            who = step["who"]
            lbl = step["label"]
            x   = name_to_x.get(who, LW / 2)
            y   = cur_y - LINE_H * scale * 0.55
            arrow_self(ax, x, y, lbl)
            cur_y -= LINE_H * scale * 0.85

        elif t == "alt":
            if step["start"]:
                alt_open_y = cur_y
                alt_label  = step["label"]
                cur_y -= 0.28 * scale
            else:
                if alt_open_y is not None:
                    alt_blocks_draw.append((alt_open_y, cur_y, alt_label))
                    alt_open_y = None
                cur_y -= 0.20 * scale

        elif t == "note":
            who = step["who"]
            lbl = step["label"]
            x   = name_to_x.get(who, LW / 2)
            y   = cur_y - 0.30 * scale
            draw_note(ax, x, y, lbl)
            cur_y -= 0.60 * scale

        elif t == "sep":
            y = cur_y - 0.15 * scale
            draw_sep(ax, y)
            cur_y -= 0.30 * scale

    # Dibujar bloques alt debajo de todo lo demás
    for (y_top, y_bot, lbl) in alt_blocks_draw:
        draw_alt_block(ax, y_top, max(y_bot, MSG_BOT + 0.1), lbl)

    plt.tight_layout(pad=0.05)

    # Guardar JPG via Pillow
    buf = io.BytesIO()
    fig.savefig(buf, dpi=DPI, bbox_inches="tight",
                facecolor=C_BG, format="png")
    buf.seek(0)
    img = Image.open(buf).convert("RGB")
    img.save(output_jpg, "JPEG", quality=95)
    plt.close(fig)
    print(f"  ✅ JPG: {output_jpg}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    base_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs", "sequence_diagrams", "jpg"
    )
    os.makedirs(base_dir, exist_ok=True)

    print(f"\n🎨 Generando diagramas de secuencia en '{base_dir}' ...\n")

    for i, diag in enumerate(DIAGRAMS):
        print(f"[{i+1}/{len(DIAGRAMS)}] {diag['title']}")
        out = os.path.join(base_dir, f"{diag['filename']}.jpg")
        generate_diagram(diag, out)

    print(f"\n🎉 {len(DIAGRAMS)} diagramas generados en:\n   {base_dir}\n")


if __name__ == "__main__":
    main()
