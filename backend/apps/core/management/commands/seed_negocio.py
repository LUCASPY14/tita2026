"""
Comando de seed para poblar datos de prueba de negocio.
Idempotente: puede ejecutarse múltiples veces sin duplicar datos.

Módulos cubiertos:
  - Tipos y planes de almuerzo
  - Precio de almuerzo vigente
  - Suscripciones de todos los alumnos al plan estándar
  - Menú diario de la semana actual + siguiente
  - Proveedores de compras
  - Stock inicial de productos
  - Roles-Permisos por rol
"""

from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Pobla datos de prueba para todos los módulos de negocio."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Elimina los datos seed antes de volver a crearlos.",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== seed_negocio ==="))

        with transaction.atomic():
            if options["reset"]:
                self._reset()

            self._seed_almuerzo()
            self._seed_menus()
            self._seed_suscripciones()
            self._seed_proveedores()
            self._seed_stock()
            self._seed_roles_permisos()

        self.stdout.write(self.style.SUCCESS("\nSeed completado exitosamente."))

    # =========================================================================
    # RESET
    # =========================================================================

    def _reset(self):
        from apps.almuerzos.models import SuscripcionAlmuerzo, MenuDiario, PlanAlmuerzo, TipoAlmuerzo, PrecioAlmuerzo
        from apps.compras.models import Proveedor
        from apps.inventario.models import Stock

        self.stdout.write("  Reseteando datos seed...")
        SuscripcionAlmuerzo.objects.filter(descripcion_seed=True).delete() if hasattr(SuscripcionAlmuerzo, 'descripcion_seed') else None
        SuscripcionAlmuerzo.objects.all().delete()
        MenuDiario.objects.all().delete()
        PrecioAlmuerzo.objects.all().delete()
        PlanAlmuerzo.objects.all().delete()
        TipoAlmuerzo.objects.all().delete()
        Proveedor.objects.all().delete()
        Stock.objects.all().delete()

    # =========================================================================
    # ALMUERZO: tipos, planes, precio
    # =========================================================================

    def _seed_almuerzo(self):
        from apps.almuerzos.models import TipoAlmuerzo, PlanAlmuerzo, PrecioAlmuerzo

        self.stdout.write("\n[1/6] Tipos de almuerzo...")

        tipo_completo, created = TipoAlmuerzo.objects.get_or_create(
            nombre="Almuerzo Completo",
            defaults={
                "descripcion": "Plato principal + guarnición + postre + bebida",
                "precio_unitario": Decimal("15000"),
                "incluye_plato_principal": True,
                "incluye_postre": True,
                "incluye_bebida": True,
                "activo": True,
            },
        )
        self._log_created("TipoAlmuerzo", "Almuerzo Completo", created)

        tipo_simple, created = TipoAlmuerzo.objects.get_or_create(
            nombre="Almuerzo Simple",
            defaults={
                "descripcion": "Plato principal + guarnición",
                "precio_unitario": Decimal("12000"),
                "incluye_plato_principal": True,
                "incluye_postre": False,
                "incluye_bebida": False,
                "activo": False,
            },
        )
        self._log_created("TipoAlmuerzo", "Almuerzo Simple", created)

        self.stdout.write("\n[2/6] Planes de almuerzo...")

        plan_std, created = PlanAlmuerzo.objects.get_or_create(
            nombre="Plan Estándar Mensual",
            defaults={
                "descripcion": "Almuerzo todos los días de lunes a viernes sin límite de días",
                "tipo": PlanAlmuerzo.TipoPlan.SIN_LIMITE,
                "precio_mensual": Decimal("270000"),
                "dias_semana_incluidos": "1,2,3,4,5",
                "activo": True,
            },
        )
        self._log_created("PlanAlmuerzo", "Plan Estándar Mensual", created)

        plan_basico, created = PlanAlmuerzo.objects.get_or_create(
            nombre="Plan Básico 20 días",
            defaults={
                "descripcion": "Hasta 20 almuerzos por mes",
                "tipo": PlanAlmuerzo.TipoPlan.CANTIDAD,
                "precio_mensual": Decimal("240000"),
                "cantidad_almuerzos_mes": 20,
                "dias_semana_incluidos": "1,2,3,4,5",
                "activo": False,
            },
        )
        self._log_created("PlanAlmuerzo", "Plan Básico 20 días", created)

        self.stdout.write("\n[3/6] Precio de almuerzo vigente...")

        precio, created = PrecioAlmuerzo.objects.get_or_create(
            fecha_inicio_vigencia=date(2026, 1, 1),
            defaults={
                "precio_unitario": Decimal("15000"),
                "descripcion": "Precio vigente 2026",
                "activo": True,
            },
        )
        self._log_created("PrecioAlmuerzo", "Gs 15.000 desde 01/01/2026", created)

        self._plan_std = plan_std

    # =========================================================================
    # MENÚS DIARIOS
    # =========================================================================

    def _seed_menus(self):
        from apps.almuerzos.models import MenuDiario

        self.stdout.write("\n[4/6] Menús diarios (2 semanas)...")

        menus = [
            # Semana 1
            ("Milanesa de pollo", "Arroz blanco y ensalada mixta", "Naranja", "Jugo de naranja natural"),
            ("Guiso de lentejas", "Pan casero", "Yogurt", "Agua"),
            ("Pollo al horno", "Puré de papa", "Manzana", "Limonada"),
            ("Fideos con salsa", "Ensalada de tomate", "Banana", "Agua"),
            ("Hamburguesa artesanal", "Papas al horno", "Fruta de estación", "Jugo"),
            # Semana 2
            ("Bife de ternera", "Arroz y zanahoria", "Postre de leche", "Agua"),
            ("Sopa de verduras", "Pan integral", "Yogurt", "Agua"),
            ("Pollo grillado", "Fideos salteados", "Naranja", "Limonada"),
            ("Locro paraguayo", "Ensalada verde", "Fruta", "Jugo de maracuyá"),
            ("Puchero", "Caldo y verduras", "Banana", "Agua"),
        ]

        hoy = date.today()
        # Start from the closest Monday
        lunes = hoy - timedelta(days=hoy.weekday())

        creados = 0
        for i, (plato, guarnicion, postre, bebida) in enumerate(menus):
            semana = i // 5
            dia_semana = i % 5
            fecha = lunes + timedelta(weeks=semana, days=dia_semana)

            _, created = MenuDiario.objects.get_or_create(
                fecha=fecha,
                defaults={
                    "plato_principal": plato,
                    "guarnicion": guarnicion,
                    "postre": postre,
                    "bebida": bebida,
                    "descripcion": "Menú generado por seed_negocio",
                    "activo": True,
                },
            )
            if created:
                creados += 1

        self.stdout.write(f"    MenuDiario: {creados} creados, {len(menus) - creados} ya existían")

    # =========================================================================
    # SUSCRIPCIONES
    # =========================================================================

    def _seed_suscripciones(self):
        from apps.almuerzos.models import SuscripcionAlmuerzo
        from apps.clientes.models import Hijo

        self.stdout.write("\n[5/6] Suscripciones de alumnos...")

        plan = self._plan_std
        hoy = date.today()
        inicio_ciclo = date(hoy.year, 2, 1)  # Ciclo escolar desde febrero
        fin_ciclo = date(hoy.year, 11, 30)

        creados = 0
        for hijo in Hijo.objects.filter(activo=True):
            _, created = SuscripcionAlmuerzo.objects.get_or_create(
                hijo=hijo,
                plan=plan,
                estado=SuscripcionAlmuerzo.Estado.ACTIVA,
                defaults={
                    "fecha_inicio": inicio_ciclo,
                    "fecha_fin": fin_ciclo,
                },
            )
            if created:
                creados += 1

        total = Hijo.objects.filter(activo=True).count()
        self.stdout.write(f"    SuscripcionAlmuerzo: {creados} creadas, {total - creados} ya existían")

    # =========================================================================
    # PROVEEDORES
    # =========================================================================

    def _seed_proveedores(self):
        from apps.compras.models import Proveedor

        self.stdout.write("\n[6/6] Proveedores...")

        proveedores_data = [
            {
                "ruc": "80012345-6",
                "razon_social": "Distribuidora Central S.A.",
                "telefono": "021-456789",
                "email": "compras@distcentral.com.py",
                "direccion": "Av. España 1234",
                "ciudad": "Asunción",
            },
            {
                "ruc": "80023456-7",
                "razon_social": "Alimentos del Sur S.R.L.",
                "telefono": "021-567890",
                "email": "ventas@alimentossur.com.py",
                "direccion": "Ruta 1 km 12",
                "ciudad": "Luque",
            },
            {
                "ruc": "80034567-8",
                "razon_social": "Frigorífico Nacional S.A.",
                "telefono": "021-678901",
                "email": "pedidos@frigonac.com.py",
                "direccion": "Industrial Norte 456",
                "ciudad": "Asunción",
            },
            {
                "ruc": "80045678-9",
                "razon_social": "Bebidas y Refrescos Cía. Ltda.",
                "telefono": "021-789012",
                "email": "comercial@bebidas-py.com",
                "direccion": "Zona Industrial, Manzana 8",
                "ciudad": "Fernando de la Mora",
            },
        ]

        creados = 0
        for data in proveedores_data:
            _, created = Proveedor.objects.get_or_create(
                ruc=data["ruc"],
                defaults={**data, "activo": True},
            )
            if created:
                creados += 1
                self.stdout.write(f"    + {data['razon_social']}")

        self.stdout.write(f"    Proveedor: {creados} creados")

    # =========================================================================
    # STOCK
    # =========================================================================

    def _seed_stock(self):
        from apps.inventario.models import Stock
        from apps.productos.models import Producto

        self.stdout.write("\n[7/6] Stock inicial de productos...")

        # Realistic initial quantities for a school cantina
        cantidades = {
            "Coca Cola 500ml":        Decimal("48"),
            "Agua Mineral 500ml":     Decimal("60"),
            "Jugo de Naranja 300ml":  Decimal("36"),
            "Empanada de Carne":      Decimal("80"),
            "Sandwich de Milanesa":   Decimal("40"),
            "Chipa":                  Decimal("100"),
            "Papas Fritas 50g":       Decimal("50"),
            "Yogurt Frutado":         Decimal("30"),
            "Manzana":                Decimal("60"),
            "Alfajor de Chocolate":   Decimal("48"),
            "Galletitas Saladas":     Decimal("40"),
            "Leche 1L":               Decimal("24"),
        }

        creados = 0
        sin_match = []
        for producto in Producto.objects.filter(activo=True):
            cantidad = cantidades.get(producto.descripcion, Decimal("20"))
            _, created = Stock.objects.get_or_create(
                producto=producto,
                defaults={"cantidad": cantidad},
            )
            if created:
                creados += 1
            elif producto.descripcion not in cantidades:
                sin_match.append(producto.descripcion)

        self.stdout.write(f"    Stock: {creados} registros creados")
        if sin_match:
            self.stdout.write(f"    Stock asignado por defecto (20 unidades): {', '.join(sin_match)}")

    # =========================================================================
    # ROLES - PERMISOS
    # =========================================================================

    def _seed_roles_permisos(self):
        from apps.usuarios.models import Rol, Permiso, RolPermiso

        self.stdout.write("\n[8/6] Roles y permisos...")

        # Mapping: rol_nombre -> list of permiso codes to assign
        # Códigos según apps/usuarios/management/commands/seed_permisos.py (notación con punto).
        matriz = {
            "Administrador": [
                "ventas.ver", "ventas.crear", "ventas.anular",
                "cobros.ver", "cobros.registrar",
                "clientes.ver", "clientes.crear", "clientes.editar",
                "tarjetas.ver", "tarjetas.cargar_saldo", "tarjetas.asignar",
                "caja.ver", "caja.abrir", "caja.cerrar",
                "facturacion.ver", "facturacion.emitir", "facturacion.anular",
                "inventario.ver", "inventario.ajustar", "inventario.aprobar_ajuste",
                "productos.ver", "productos.crear", "productos.editar",
                "compras.ver", "compras.crear_oc", "compras.aprobar_oc",
                "almuerzos.ver", "almuerzos.gestionar_menu", "almuerzos.registrar_consumo",
                "reportes.ver", "reportes.exportar",
                "usuarios.ver", "usuarios.crear", "usuarios.editar", "usuarios.gestionar_roles",
                "configuracion.ver", "configuracion.editar",
            ],
            "Cajero": [
                "ventas.ver", "ventas.crear", "ventas.anular",
                "tarjetas.ver", "tarjetas.cargar_saldo",
                "caja.ver", "caja.abrir", "caja.cerrar",
                "reportes.ver",
            ],
            "Cocina": [
                "almuerzos.ver", "almuerzos.registrar_consumo",
                "reportes.ver",
            ],
        }

        permisos_map = {p.codigo_permiso: p for p in Permiso.objects.filter(estado=True)}
        total_creados = 0

        for rol_nombre, codigos in matriz.items():
            try:
                rol = Rol.objects.get(nombre_rol=rol_nombre)
            except Rol.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"    Rol '{rol_nombre}' no encontrado, saltando."))
                continue

            for codigo in codigos:
                permiso = permisos_map.get(codigo)
                if not permiso:
                    self.stdout.write(self.style.WARNING(f"    Permiso '{codigo}' no encontrado, saltando."))
                    continue

                _, created = RolPermiso.objects.get_or_create(
                    id_rol=rol,
                    id_permiso=permiso,
                )
                if created:
                    total_creados += 1

        self.stdout.write(f"    RolPermiso: {total_creados} asignaciones creadas")

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _log_created(self, model: str, name: str, created: bool):
        if created:
            self.stdout.write(f"    + {model}: {name}")
        else:
            self.stdout.write(f"    = {model}: {name} (ya existía)")
