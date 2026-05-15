"""
Script para cargar datos de prueba en La Cantina de Tita
Ejecutar: python manage.py shell < scripts/cargar_datos.py
O: python manage.py runscript cargar_datos (si instalás django-extensions)
"""

import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.base')

import django
django.setup()

from decimal import Decimal
from django.utils import timezone
from datetime import date

# ==============================================================================
# USUARIOS
# ==============================================================================
from apps.usuarios.models import Usuario, Rol, Permiso, Empleado

print("Creando roles...")
admin_rol, _ = Rol.objects.get_or_create(nombre_rol="Administrador", defaults={"descripcion": "Acceso total"})
cajero_rol, _ = Rol.objects.get_or_create(nombre_rol="Cajero", defaults={"descripcion": "Punto de venta"})
cocina_rol, _ = Rol.objects.get_or_create(nombre_rol="Cocina", defaults={"descripcion": "Preparacion de almuerzos"})

print("Creando permisos...")
permisos_data = [
    ("ventas_crear", "Crear ventas", "ventas"),
    ("ventas_anular", "Anular ventas", "ventas"),
    ("compras_crear", "Crear compras", "compras"),
    ("productos_gestionar", "Gestionar productos", "productos"),
    ("clientes_gestionar", "Gestionar clientes", "clientes"),
    ("reportes_ver", "Ver reportes", "reportes"),
    ("caja_abrir", "Abrir caja", "contabilidad"),
    ("caja_cerrar", "Cerrar caja", "contabilidad"),
    ("almuerzos_registrar", "Registrar almuerzos", "almuerzos"),
    ("tarjetas_recargar", "Recargar tarjetas", "core"),
]
for codigo, nombre, modulo in permisos_data:
    Permiso.objects.get_or_create(codigo_permiso=codigo, defaults={"nombre": nombre, "modulo": modulo})

print("Creando empleados...")
empleados_data = [
    ("Maria", "Gonzalez", "maria@cantinatita.com", admin_rol),
    ("Juan", "Ramirez", "juan@cantinatita.com", cajero_rol),
    ("Ana", "Martinez", "ana@cantinatita.com", cajero_rol),
    ("Pedro", "Lopez", "pedro@cantinatita.com", cocina_rol),
]
for nombre, apellido, email, rol in empleados_data:
    emp, created = Empleado.objects.get_or_create(
        email=email,
        defaults={
            "nombre": nombre,
            "apellido": apellido,
            "id_rol": rol,
            "fecha_ingreso": timezone.now(),
        }
    )
    if created:
        print(f"  Empleado: {nombre} {apellido}")

# ==============================================================================
# CORE - Medios de pago
# ==============================================================================
from apps.core.models import MedioPago

print("Creando medios de pago...")
medios_data = [
    ("Efectivo", False, False),
    ("POS Debito", True, True),
    ("POS Credito", True, True),
    ("Transferencia Bancaria", False, True),
    ("QR SIPAP", False, True),
    ("Billetera Electronica", True, True),
    ("Cheque", False, True),
    ("Tarjeta Prepaga", False, False),
    ("Vale Interno", False, False),
    ("Cortesia", False, False),
]
for desc, comision, validacion in medios_data:
    mp, created = MedioPago.objects.get_or_create(descripcion=desc, defaults={"genera_comision": comision, "requiere_validacion": validacion})
    if created:
        print(f"  Medio de pago: {desc}")

# ==============================================================================
# CONTABILIDAD - Cajas
# ==============================================================================
from apps.contabilidad.models import Caja, DatosEmpresa

print("Creando cajas...")
cajas_data = [
    "Caja Principal - Entrada",
    "Caja Secundaria - Patio",
    "Caja Almuerzos - Comedor",
]
for nombre in cajas_data:
    Caja.objects.get_or_create(nombre=nombre)

print("Creando datos de empresa...")
DatosEmpresa.objects.get_or_create(
    ruc="80012345-6",
    defaults={
        "razon_social": "Cantina Tita S.A.",
        "direccion": "Av. Mariscal Lopez 1234",
        "ciudad": "Asuncion",
        "pais": "Paraguay",
        "telefono": "021-123456",
        "email": "info@cantinatita.com",
    }
)

# ==============================================================================
# PRODUCTOS
# ==============================================================================
from apps.productos.models import Categoria, UnidadMedida, Impuesto, Producto, ListaPrecio, PrecioPorLista

print("Creando categorias...")
cats_data = ["Bebidas", "Comidas", "Snacks", "Lacteos", "Frutas", "Golosinas", "Panificados", "Embutidos", "Limpieza", "Varios"]
for nombre in cats_data:
    Categoria.objects.get_or_create(nombre=nombre)

print("Creando unidades de medida...")
unidades_data = [
    ("Unidad", "Un"),
    ("Litro", "L"),
    ("Kilogramo", "Kg"),
    ("Gramo", "g"),
    ("Mililitro", "ml"),
    ("Paquete", "Pq"),
    ("Caja", "Cj"),
    ("Docena", "Doc"),
    ("Porcion", "Por"),
    ("Botella", "Bot"),
]
for nombre, abrev in unidades_data:
    UnidadMedida.objects.get_or_create(nombre=nombre, defaults={"abreviatura": abrev})

print("Creando impuestos...")
impuestos_data = [
    ("IVA 10%", Decimal("10")),
    ("IVA 5%", Decimal("5")),
    ("Exento", Decimal("0")),
]
for nombre, porc in impuestos_data:
    Impuesto.objects.get_or_create(nombre_impuesto=nombre, defaults={"porcentaje": porc, "vigente_desde": date(2024, 1, 1)})

print("Creando lista de precios...")
lista_general, _ = ListaPrecio.objects.get_or_create(nombre="General", defaults={"moneda": "PYG"})

print("Creando productos...")
cat_bebidas = Categoria.objects.get(nombre="Bebidas")
cat_comidas = Categoria.objects.get(nombre="Comidas")
cat_snacks = Categoria.objects.get(nombre="Snacks")
cat_lacteos = Categoria.objects.get(nombre="Lacteos")
cat_frutas = Categoria.objects.get(nombre="Frutas")
cat_golosinas = Categoria.objects.get(nombre="Golosinas")
cat_panificados = Categoria.objects.get(nombre="Panificados")
un_unidad = UnidadMedida.objects.get(nombre="Unidad")
un_litro = UnidadMedida.objects.get(nombre="Litro")
un_porcion = UnidadMedida.objects.get(nombre="Porcion")
iva10 = Impuesto.objects.get(nombre_impuesto="IVA 10%")
iva5 = Impuesto.objects.get(nombre_impuesto="IVA 5%")
exento = Impuesto.objects.get(nombre_impuesto="Exento")

productos_data = [
    # (codigo_barra, descripcion, categoria, unidad, impuesto, precio, stock_minimo)
    ("7791234000010", "Coca Cola 500ml", cat_bebidas, un_unidad, iva10, 6000, 20),
    ("7791234000027", "Agua Mineral 500ml", cat_bebidas, un_unidad, iva5, 3000, 30),
    ("7791234000034", "Jugo de Naranja 300ml", cat_bebidas, un_unidad, iva10, 5000, 15),
    ("7791234000041", "Empanada de Carne", cat_comidas, un_unidad, iva10, 4000, 40),
    ("7791234000058", "Sandwich de Milanesa", cat_comidas, un_unidad, iva10, 8000, 25),
    ("7791234000065", "Chipa", cat_panificados, un_unidad, iva5, 2500, 50),
    ("7791234000072", "Papas Fritas 50g", cat_snacks, un_unidad, iva10, 3500, 30),
    ("7791234000089", "Yogurt Frutado", cat_lacteos, un_unidad, iva5, 4000, 20),
    ("7791234000096", "Manzana", cat_frutas, un_unidad, exento, 2000, 30),
    ("7791234000102", "Alfajor de Chocolate", cat_golosinas, un_unidad, iva10, 3000, 35),
    ("7791234000119", "Galletitas Saladas", cat_snacks, un_unidad, iva10, 2500, 25),
    ("7791234000126", "Leche 1L", cat_lacteos, un_litro, iva5, 5500, 15),
]

for codigo, desc, cat, unidad, imp, precio, stock_min in productos_data:
    prod, created = Producto.objects.get_or_create(
        codigo_barra=codigo,
        defaults={
            "descripcion": desc,
            "categoria": cat,
            "unidad_medida": unidad,
            "stock_minimo": stock_min,
        }
    )
    if created:
        PrecioPorLista.objects.create(producto=prod, lista=lista_general, precio_unitario=precio)
        from apps.productos.models import ProductoImpuesto
        ProductoImpuesto.objects.create(producto=prod, impuesto=imp)
        print(f"  Producto: {desc} - Gs. {precio:,}")

# ==============================================================================
# CLIENTES
# ==============================================================================
from apps.clientes.models import Cliente, TipoCliente, Hijo, Grado, Pais, Ciudad

print("Creando tipos de cliente...")
tipos_data = ["Regular", "Estudiante", "Profesor", "Funcionario", "Visitante"]
for nombre in tipos_data:
    TipoCliente.objects.get_or_create(nombre=nombre)

tipo_regular = TipoCliente.objects.get(nombre="Regular")

print("Creando paises...")
py, _ = Pais.objects.get_or_create(nombre="Paraguay")
ar, _ = Pais.objects.get_or_create(nombre="Argentina")

print("Creando ciudades...")
ciudades_data = ["Asuncion", "San Lorenzo", "Luque", "Fernando de la Mora", "Lambare", "Villa Elisa", "Capiata", "Mariano Roque Alonso", "Encarnacion", "Ciudad del Este"]
for nombre in ciudades_data:
    Ciudad.objects.get_or_create(nombre=nombre)

print("Creando grados...")
grados_data = [
    ("Primero", 1), ("Segundo", 2), ("Tercero", 3),
    ("Cuarto", 4), ("Quinto", 5), ("Sexto", 6),
    ("Septimo", 7), ("Octavo", 8), ("Noveno", 9),
]
for nombre, nivel in grados_data:
    Grado.objects.get_or_create(nombre=nombre, defaults={"nivel": nivel, "orden": nivel})

print("Creando clientes e hijos...")
clientes_data = [
    ("Lucia", "Gomez", "1234567-8", "0985-123456", [
        ("Carlos", "Gomez", "Cuarto"),
        ("Sofia", "Gomez", "Primero"),
    ]),
    ("Ramon", "Benitez", "2345678-9", "0985-234567", [
        ("Mateo", "Benitez", "Sexto"),
    ]),
    ("Carmen", "Vera", "3456789-0", "0985-345678", [
        ("Valentina", "Vera", "Tercero"),
        ("Lucas", "Vera", "Quinto"),
    ]),
    ("Jorge", "Diaz", "4567890-1", "0985-456789", [
        ("Emilia", "Diaz", "Segundo"),
    ]),
    ("Patricia", "Rojas", "5678901-2", "0985-567890", [
        ("Nicolas", "Rojas", "Septimo"),
        ("Camila", "Rojas", "Cuarto"),
        ("Benjamin", "Rojas", "Primero"),
    ]),
    ("Roberto", "Nunez", "6789012-3", "0985-678901", [
        ("Agustina", "Nunez", "Octavo"),
    ]),
    ("Graciela", "Ortiz", "7890123-4", "0985-789012", [
        ("Joaquin", "Ortiz", "Quinto"),
        ("Victoria", "Ortiz", "Tercero"),
    ]),
    ("Fernando", "Silva", "8901234-5", "0985-890123", [
        ("Martina", "Silva", "Noveno"),
    ]),
    ("Adriana", "Torres", "9012345-6", "0985-901234", [
        ("Sebastian", "Torres", "Sexto"),
        ("Luciana", "Torres", "Primero"),
    ]),
    ("Gustavo", "Acosta", "0123456-7", "0985-012345", [
        ("Franco", "Acosta", "Cuarto"),
    ]),
]

total_clientes = 0
total_hijos = 0

for nombres, apellidos, ruc, tel, hijos_data in clientes_data:
    cliente, created = Cliente.objects.get_or_create(
        ruc_ci=ruc,
        defaults={
            "nombres": nombres,
            "apellidos": apellidos,
            "telefono": tel,
            "limite_credito": 500000,
            "tipo_cliente": tipo_regular,
            "lista_precio": lista_general,
        }
    )
    if created:
        total_clientes += 1
        for hijo_nombre, hijo_apellido, grado_nombre in hijos_data:
            grado = Grado.objects.get(nombre=grado_nombre)
            Hijo.objects.create(
                nombre=hijo_nombre,
                apellido=hijo_apellido,
                grado=grado.nombre,
                cliente_responsable=cliente,
            )
            total_hijos += 1

print(f"  Clientes creados: {total_clientes}")
print(f"  Hijos creados: {total_hijos}")

# ==============================================================================
# CORE - Tarjetas para hijos
# ==============================================================================
from apps.core.models import Tarjeta

print("Creando tarjetas para hijos...")
total_tarjetas = 0
hijos = Hijo.objects.all()
for i, hijo in enumerate(hijos, 1):
    nro = f"TJT-{i:04d}"
    tarjeta, created = Tarjeta.objects.get_or_create(
        nro_tarjeta=nro,
        defaults={
            "hijo": hijo,
            "codigo_barras": f"BAR{nro}",
            "saldo_actual": 50000,
            "saldo_alerta": 10000,
            "limite_credito": 100000,
            "permite_saldo_negativo": True,
        }
    )
    if created:
        total_tarjetas += 1
print(f"  Tarjetas creadas: {total_tarjetas}")

# ==============================================================================
# ALMUERZOS
# ==============================================================================
from apps.almuerzos.models import TipoAlmuerzo, PlanAlmuerzo, PrecioAlmuerzo

print("Creando tipos de almuerzo...")
tipos_almuerzo_data = [
    ("Completo", "Plato principal + postre + bebida", 15000, True, True, True),
    ("Plato Principal", "Solo plato principal", 10000, True, False, False),
    ("Vegetariano", "Opcion sin carne", 12000, True, False, True),
    ("Light", "Ensalada + proteina", 11000, True, False, True),
    ("Postre", "Solo postre", 4000, False, True, False),
]
for nombre, desc, precio, pp, postre, bebida in tipos_almuerzo_data:
    TipoAlmuerzo.objects.get_or_create(
        nombre=nombre,
        defaults={
            "descripcion": desc,
            "precio_unitario": precio,
            "incluye_plato_principal": pp,
            "incluye_postre": postre,
            "incluye_bebida": bebida,
        }
    )

print("Creando precios de almuerzo...")
PrecioAlmuerzo.objects.get_or_create(
    fecha_inicio_vigencia=date(2025, 1, 1),
    defaults={"precio_unitario": 15000, "descripcion": "Precio base 2025"}
)

print("Creando planes de almuerzo...")
planes_data = [
    ("Plan Mensual Completo", "Almuerzo completo todos los dias", "SIN_LIMITE", 300000, 20, 350000),
    ("Plan 10 Almuerzos", "10 almuerzos por mes", "CANTIDAD", 150000, 10, 200000),
    ("Plan 20 Almuerzos", "20 almuerzos por mes", "CANTIDAD", 280000, 20, 350000),
]
for nombre, desc, tipo, precio, cantidad, limite in planes_data:
    PlanAlmuerzo.objects.get_or_create(
        nombre=nombre,
        defaults={
            "descripcion": desc,
            "tipo": tipo,
            "precio_mensual": precio,
            "cantidad_almuerzos_mes": cantidad if tipo == "CANTIDAD" else None,
            "limite_credito_mensual": limite,
            "dias_semana_incluidos": "LUN,MAR,MIE,JUE,VIE",
        }
    )

# ==============================================================================
# ALERGENOS
# ==============================================================================
from apps.almuerzos.models import Alergeno

print("Creando alergenos...")
alergenos_data = [
    ("Lacteos", "Leche y derivados", "ALTA"),
    ("Gluten", "Trigo, avena, cebada", "MEDIA"),
    ("Mani", "Mani y derivados", "CRITICA"),
    ("Huevo", "Huevo y derivados", "MEDIA"),
    ("Soja", "Soja y derivados", "BAJA"),
]
for nombre, desc, sev in alergenos_data:
    Alergeno.objects.get_or_create(
        nombre=nombre,
        defaults={"descripcion": desc, "severidad": sev, "palabras_clave": [nombre.lower()]}
    )

# ==============================================================================
# CONTABILIDAD - Tarifas comision
# ==============================================================================
from apps.contabilidad.models import TarifaComision

print("Creando tarifas de comision...")
tarifas_data = [
    (MedioPago.objects.get(descripcion="POS Debito"), Decimal("2.50"), None),
    (MedioPago.objects.get(descripcion="POS Credito"), Decimal("3.50"), None),
    (MedioPago.objects.get(descripcion="Billetera Electronica"), Decimal("1.50"), None),
    (MedioPago.objects.get(descripcion="QR SIPAP"), Decimal("1.00"), None),
]
for medio, porc, fijo in tarifas_data:
    TarifaComision.objects.get_or_create(
        medio_pago=medio,
        defaults={"porcentaje_comision": porc, "monto_fijo": fijo}
    )

# ==============================================================================
# RESUMEN
# ==============================================================================
print("\n" + "="*50)
print("DATOS DE PRUEBA CARGADOS EXITOSAMENTE")
print("="*50)
print(f"  Usuarios/Empleados: {Empleado.objects.count()}")
print(f"  Roles: {Rol.objects.count()}")
print(f"  Permisos: {Permiso.objects.count()}")
print(f"  Medios de pago: {MedioPago.objects.count()}")
print(f"  Categorias: {Categoria.objects.count()}")
print(f"  Unidades de medida: {UnidadMedida.objects.count()}")
print(f"  Impuestos: {Impuesto.objects.count()}")
print(f"  Productos: {Producto.objects.count()}")
print(f"  Clientes: {Cliente.objects.count()}")
print(f"  Hijos: {Hijo.objects.count()}")
print(f"  Grados: {Grado.objects.count()}")
print(f"  Tarjetas: {Tarjeta.objects.count()}")
print(f"  Tipos de almuerzo: {TipoAlmuerzo.objects.count()}")
print(f"  Planes de almuerzo: {PlanAlmuerzo.objects.count()}")
print(f"  Alergenos: {Alergeno.objects.count()}")
print(f"  Tarifas de comision: {TarifaComision.objects.count()}")
print("="*50)