"""
Seed maestro para UAT (User Acceptance Testing) con la cantina.

Crea el conjunto completo de datos demo realistas para probar todos los
flujos con el personal de la cantina: cajeros, ModoRecreo, portal de padres,
almuerzos, reportes, etc.

Idempotente: puede ejecutarse múltiples veces sin duplicar datos.

Orden de ejecución:
  1. Catálogo base   (categorías, unidades, lista de precios, productos)
  2. Maestros        (grados, tipos de cliente, cajas, medios de pago)
  3. Usuarios demo   (create_demo_users)
  4. Negocio         (seed_negocio — almuerzos, proveedores, stock, SIPAP)
  5. Familias UAT    (10 padres, 15 alumnos, tarjetas con saldo)
  6. Portal demo     (seed_portal_demo — usuario portal@tita.local)

Uso:
    python manage.py seed_uat
    python manage.py seed_uat --reset
    python manage.py seed_uat --password OtraClave
"""

from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Seed maestro para UAT: crea todos los datos demo en el orden correcto."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Elimina datos seed antes de recrearlos (pasa --reset a los sub-comandos).",
        )
        parser.add_argument(
            "--password",
            default="demo1234",
            help="Contraseña para todos los usuarios demo (default: demo1234)",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("═══ seed_uat — UAT Cantina Tita ═══\n"))

        with transaction.atomic():
            self._seed_catalogo()
            self._seed_maestros()

        # Sub-comandos con sus propias transacciones
        call_command("create_demo_users", password=options["password"], verbosity=0)
        self.stdout.write("  ✓ create_demo_users")

        if options["reset"]:
            call_command("seed_negocio", reset=True, verbosity=0)
        else:
            call_command("seed_negocio", verbosity=0)
        self.stdout.write("  ✓ seed_negocio")

        with transaction.atomic():
            self._seed_familias()

        if options["reset"]:
            call_command("seed_portal_demo", reset=True, password=options["password"], verbosity=0)
        else:
            call_command("seed_portal_demo", password=options["password"], verbosity=0)
        self.stdout.write("  ✓ seed_portal_demo")

        self.stdout.write(self.style.SUCCESS(
            "\n═══ seed_uat completado ═══\n"
            "Usuarios demo (contraseña: demo1234):\n"
            "  admin@tita.local      ADMIN\n"
            "  cajero@tita.local     CAJERO\n"
            "  supervisor@tita.local SUPERVISOR\n"
            "  cobrador@tita.local   COBRADOR\n"
            "  cocina@tita.local     COCINA\n"
            "  portal@tita.local     CLIENTE_WEB\n"
        ))

    # =========================================================================
    # 1. CATÁLOGO BASE
    # =========================================================================

    def _seed_catalogo(self):
        self.stdout.write("[1/5] Catálogo base (categorías, productos, precios)...")

        from apps.productos.models import (
            Categoria, UnidadMedida, ListaPrecio, Producto, PrecioPorLista
        )

        # -- Unidades de medida --
        unidad, _ = UnidadMedida.objects.get_or_create(
            abreviatura="Un", defaults={"nombre": "Unidad", "activo": True}
        )
        UnidadMedida.objects.get_or_create(
            abreviatura="L",  defaults={"nombre": "Litro", "activo": True}
        )
        UnidadMedida.objects.get_or_create(
            abreviatura="Kg", defaults={"nombre": "Kilogramo", "activo": True}
        )

        # -- Lista de precios por defecto --
        lista, _ = ListaPrecio.objects.get_or_create(
            nombre="Lista General",
            defaults={"moneda": "PYG", "activo": True, "es_por_defecto": True},
        )
        if not lista.es_por_defecto:
            lista.es_por_defecto = True
            lista.save()

        # -- Categorías --
        cat_bebidas, _ = Categoria.objects.get_or_create(
            nombre="Bebidas", defaults={"activo": True}
        )
        cat_comidas, _ = Categoria.objects.get_or_create(
            nombre="Comidas", defaults={"activo": True}
        )
        cat_snacks, _ = Categoria.objects.get_or_create(
            nombre="Snacks", defaults={"activo": True}
        )
        cat_lacteos, _ = Categoria.objects.get_or_create(
            nombre="Lácteos y Frutas", defaults={"activo": True}
        )

        # -- Productos con precios (típicos de cantina escolar) --
        catalogo = [
            # (codigo, descripcion, categoria, precio_gs)
            ("BEB-001", "Agua Mineral 500ml",        cat_bebidas, Decimal("3000")),
            ("BEB-002", "Jugo de naranja 300ml",     cat_bebidas, Decimal("5000")),
            ("BEB-003", "Coca Cola 500ml",           cat_bebidas, Decimal("7000")),
            ("BEB-004", "Té frío 500ml",             cat_bebidas, Decimal("4000")),
            ("BEB-005", "Leche saborizada 200ml",    cat_bebidas, Decimal("4500")),
            ("COM-001", "Empanada de carne",         cat_comidas, Decimal("5000")),
            ("COM-002", "Sandwich de milanesa",      cat_comidas, Decimal("15000")),
            ("COM-003", "Chipa",                     cat_comidas, Decimal("3000")),
            ("COM-004", "Tostada con manteca",       cat_comidas, Decimal("4000")),
            ("COM-005", "Fideos con salsa",          cat_comidas, Decimal("12000")),
            ("SNK-001", "Papas fritas 50g",          cat_snacks,  Decimal("5000")),
            ("SNK-002", "Alfajor de chocolate",      cat_snacks,  Decimal("4000")),
            ("SNK-003", "Galletitas saladas",        cat_snacks,  Decimal("3000")),
            ("SNK-004", "Barrita de cereal",         cat_snacks,  Decimal("4500")),
            ("LAC-001", "Yogurt frutado 150g",       cat_lacteos, Decimal("5000")),
            ("LAC-002", "Manzana",                   cat_lacteos, Decimal("3000")),
            ("LAC-003", "Banana",                    cat_lacteos, Decimal("2500")),
        ]

        creados = 0
        for codigo, descripcion, categoria, precio in catalogo:
            prod, created = Producto.objects.get_or_create(
                codigo=codigo,
                defaults={
                    "descripcion": descripcion,
                    "categoria": categoria,
                    "unidad_medida": unidad,
                    "activo": True,
                    "requiere_stock": True,
                    "stock_minimo": Decimal("5"),
                },
            )
            if created:
                creados += 1

            PrecioPorLista.objects.get_or_create(
                producto=prod,
                lista=lista,
                defaults={"precio_unitario": precio},
            )

        self.stdout.write(f"  Productos: {creados} creados / {len(catalogo) - creados} ya existían")

    # =========================================================================
    # 2. MAESTROS OPERATIVOS
    # =========================================================================

    def _seed_maestros(self):
        self.stdout.write("[2/5] Maestros operativos (grados, cajas, medios de pago)...")

        from apps.clientes.models import TipoCliente, Grado
        from apps.contabilidad.models import Caja
        from apps.core.models import MedioPago

        # -- Tipos de cliente --
        TipoCliente.objects.get_or_create(nombre="Familia", defaults={"activo": True})
        TipoCliente.objects.get_or_create(nombre="Docente", defaults={"activo": True})
        TipoCliente.objects.get_or_create(nombre="Personal", defaults={"activo": True})

        # -- Grados (1° a 9° con paralelos A y B) --
        grados_data = [
            (f"{n}° Grado {p}", f"g{n}{p.lower()}")
            for n in range(1, 10)
            for p in ["A", "B"]
        ]
        creados_g = 0
        for nombre, _ in grados_data:
            _, c = Grado.objects.get_or_create(
                nombre=nombre, defaults={"activo": True}
            )
            if c:
                creados_g += 1
        self.stdout.write(f"  Grados: {creados_g} creados")

        # -- Cajas --
        caja_principal, c1 = Caja.objects.get_or_create(
            nombre="Caja Principal",
            defaults={"ubicacion": "Cantina — mostrador principal", "activo": True},
        )
        caja_recreo, c2 = Caja.objects.get_or_create(
            nombre="Caja Recreo",
            defaults={"ubicacion": "Cantina — mostrador recreo", "activo": True},
        )
        self.stdout.write(f"  Cajas: {'2 creadas' if c1 and c2 else 'ya existían'}")

        # -- Medios de pago --
        medios = [
            ("Efectivo",             False),
            ("Tarjeta RFID",         False),
            ("Transferencia",        True),
            ("QR (SIPAP)",           True),
            ("POS (débito/crédito)", True),
        ]
        creados_m = 0
        for descripcion, requiere_validacion in medios:
            _, c = MedioPago.objects.get_or_create(
                descripcion=descripcion,
                defaults={"requiere_validacion": requiere_validacion, "activo": True},
            )
            if c:
                creados_m += 1
        self.stdout.write(f"  MediosPago: {creados_m} creados")

    # =========================================================================
    # 5. FAMILIAS UAT
    # =========================================================================

    def _seed_familias(self):
        self.stdout.write("[4/5] Familias UAT (padres, alumnos, tarjetas)...")

        from apps.clientes.models import Cliente, TipoCliente, Hijo, Grado
        from apps.core.models import Tarjeta

        tipo = TipoCliente.objects.filter(activo=True, nombre="Familia").first() \
            or TipoCliente.objects.filter(activo=True).first()

        from apps.productos.models import ListaPrecio
        lista = ListaPrecio.objects.filter(activo=True, es_por_defecto=True).first() \
            or ListaPrecio.objects.filter(activo=True).first()

        grados = list(Grado.objects.filter(activo=True).order_by("nombre"))

        # (ruc_ci, nombre_padre, apellido, hijos: [(nombre, grado_idx, nro_tarjeta, saldo)])
        familias = [
            ("1234567-1", "Carlos",    "Rodríguez", [
                ("Matías",   0,  "T-00101", Decimal("75000")),
                ("Valentina",2,  "T-00102", Decimal("45000")),
            ]),
            ("2345678-2", "María",     "González",  [
                ("Diego",    1,  "T-00201", Decimal("120000")),
            ]),
            ("3456789-3", "Roberto",   "Martínez",  [
                ("Camila",   4,  "T-00301", Decimal("30000")),
                ("Tomás",    6,  "T-00302", Decimal("8000")),   # saldo bajo → alerta
            ]),
            ("4567890-4", "Ana",       "Pérez",     [
                ("Sofía",    3,  "T-00401", Decimal("60000")),
            ]),
            ("5678901-5", "Luis",      "Fernández", [
                ("Joaquín",  5,  "T-00501", Decimal("25000")),
                ("Luciana",  7,  "T-00502", Decimal("90000")),
            ]),
            ("6789012-6", "Patricia",  "López",     [
                ("Emilia",   8,  "T-00601", Decimal("15000")),
            ]),
            ("7890123-7", "Fernando",  "Sánchez",   [
                ("Santiago", 0,  "T-00701", Decimal("55000")),
                ("Nicolás",  2,  "T-00702", Decimal("40000")),
            ]),
            ("8901234-8", "Graciela",  "Torres",    [
                ("Milagros", 1,  "T-00801", Decimal("85000")),
            ]),
            ("9012345-9", "Hugo",      "Ramírez",   [
                ("Franco",   3,  "T-00901", Decimal("20000")),
                ("Renata",   5,  "T-00902", Decimal("65000")),
            ]),
            ("0123456-0", "Claudia",   "Benítez",   [
                ("Agustín",  6,  "T-01001", Decimal("50000")),
            ]),
        ]

        padres_c = 0
        hijos_c = 0
        tarjetas_c = 0

        for ruc_ci, nombre, apellido, hijos_data in familias:
            cliente, cp = Cliente.objects.get_or_create(
                ruc_ci=ruc_ci,
                defaults={
                    "nombres": nombre,
                    "apellidos": apellido,
                    "email": f"{nombre.lower()}.{apellido.lower()}@tita.local",
                    "tipo_cliente": tipo,
                    "lista_precio": lista,
                    "activo": True,
                },
            )
            if cp:
                padres_c += 1

            for h_nombre, grado_idx, nro_tarjeta, saldo in hijos_data:
                grado = grados[grado_idx] if grado_idx < len(grados) else None

                hijo, ch = Hijo.objects.get_or_create(
                    cliente_responsable=cliente,
                    nombre=h_nombre,
                    apellido=apellido,
                    defaults={"grado": grado, "activo": True},
                )
                if ch:
                    hijos_c += 1

                _, ct = Tarjeta.objects.get_or_create(
                    nro_tarjeta=nro_tarjeta,
                    defaults={
                        "hijo": hijo,
                        "saldo_actual": saldo,
                        "estado": Tarjeta.Estado.ACTIVA,
                        "saldo_alerta": Decimal("15000"),
                        "notificar_saldo_bajo": True,
                    },
                )
                if ct:
                    tarjetas_c += 1

        self.stdout.write(
            f"  Padres: {padres_c} nuevos | "
            f"Alumnos: {hijos_c} nuevos | "
            f"Tarjetas: {tarjetas_c} nuevas"
        )
