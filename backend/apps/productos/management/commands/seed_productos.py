"""
Management command: seed_productos
Completa los datos faltantes de productos:
  1. PreciosPorLista para las 5 listas (60 entradas faltantes)
  2. StockUnico para productos sin registro de stock
  3. Corrige DatosEmpresa si tiene datos placeholder

Uso:
    python manage.py seed_productos
    python manage.py seed_productos --dry-run
"""

from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


def _gs(valor):
    """Redondea a centena de Guaranies (100 Gs)."""
    return Decimal(str(round(int(valor) / 100) * 100)).quantize(Decimal("0.01"))


class Command(BaseCommand):
    help = "Completa seeds faltantes: PreciosPorLista, Stock, DatosEmpresa"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mostrar que se crearia sin guardar nada",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("=== DRY RUN - no se guardan cambios ===\n"))

        self.stdout.write(self.style.MIGRATE_HEADING("=== Seed de Productos ===\n"))

        creados = 0
        existentes = 0

        # ------------------------------------------------------------------
        # 1. PreciosPorLista
        # ------------------------------------------------------------------
        self.stdout.write("1. PreciosPorLista...")

        from apps.productos.models import ListasPrecios, PreciosPorLista, Productos

        listas = {l.id_lista: l for l in ListasPrecios.objects.all()}
        lista_general = listas.get(1)
        if not lista_general:
            self.stdout.write(self.style.ERROR("   ERROR: Lista General (id=1) no encontrada."))
            return

        # Factores de descuento por lista
        # Lista 1 = base, Lista 1001 = igual a 1, VIP=10% dto, Est=8%, Doc=10%
        FACTORES = {
            1: Decimal("1.00"),     # Lista General - base
            1001: Decimal("1.00"),  # General (misma politica que lista 1)
            2: Decimal("0.90"),     # Lista VIP - 10% descuento
            3: Decimal("0.92"),     # Lista Estudiante - 8% descuento
            4: Decimal("0.90"),     # Lista Personal Docente - 10% descuento
        }

        # Util escolar: sin descuentos (precio de mercado fijo)
        LISTAS_SIN_DESCUENTO_CATEGORIAS = ["Utiles Escolares", "Otros"]

        for producto in Productos.objects.select_related("id_categoria").all():
            cat_nombre = producto.id_categoria.nombre if producto.id_categoria else ""
            sin_descuento = cat_nombre in LISTAS_SIN_DESCUENTO_CATEGORIAS

            precio_base = PreciosPorLista.objects.filter(
                id_producto=producto, id_lista=lista_general
            ).first()

            if not precio_base:
                self.stdout.write(
                    f"   SKIP {producto.descripcion}: sin precio base en Lista General"
                )
                continue

            base = precio_base.precio_unitario

            for id_lista, lista in listas.items():
                if id_lista == 1:
                    continue  # ya existe

                exists = PreciosPorLista.objects.filter(
                    id_producto=producto, id_lista=lista
                ).exists()
                if exists:
                    existentes += 1
                    continue

                factor = Decimal("1.00") if sin_descuento else FACTORES.get(id_lista, Decimal("1.00"))
                precio = _gs(base * factor)

                if not dry_run:
                    PreciosPorLista.objects.create(
                        id_producto=producto,
                        id_lista=lista,
                        precio_unitario=precio,
                        fecha_vigencia=timezone.now().date(),
                    )
                self.stdout.write(
                    f"   ++ {producto.descripcion[:28]:28} | {lista.nombre_lista:20} | Gs.{precio:>10}"
                )
                creados += 1

        self.stdout.write(
            self.style.SUCCESS(f"   Precios: {creados} creados, {existentes} ya existian")
        )

        # ------------------------------------------------------------------
        # 2. StockUnico - productos sin registro
        # ------------------------------------------------------------------
        self.stdout.write("\n2. StockUnico (productos sin stock)...")

        from apps.inventario.models import StockUnico

        stock_creados = 0
        for producto in Productos.objects.all():
            existe = StockUnico.objects.filter(id_producto=producto).exists()
            if not existe:
                cantidad_inicial = Decimal("0.00")
                if not dry_run:
                    StockUnico.objects.create(
                        id_producto=producto,
                        cantidad=cantidad_inicial,
                        fecha_ultima_actualizacion=timezone.now(),
                    )
                self.stdout.write(
                    self.style.SUCCESS(f"   ++ Stock creado: {producto.descripcion} = {cantidad_inicial}")
                )
                stock_creados += 1

        if stock_creados == 0:
            self.stdout.write("   -- Todos los productos ya tienen stock registrado")

        # ------------------------------------------------------------------
        # 3. DatosEmpresa - corregir encoding o datos placeholder
        # ------------------------------------------------------------------
        self.stdout.write("\n3. DatosEmpresa...")

        from apps.contabilidad.models import DatosEmpresa

        empresa = DatosEmpresa.objects.first()
        if empresa:
            placeholder = (
                empresa.ruc == "80000000-0"
                or "Instituci" in empresa.razon_social
                or empresa.email == "info@institucion.edu.py"
            )
            if placeholder:
                self.stdout.write(
                    "   Actualizando datos placeholder de DatosEmpresa..."
                )
                if not dry_run:
                    empresa.razon_social = "Cantina Tita"
                    empresa.direccion = "Asuncion, Paraguay"
                    empresa.ciudad = "Asuncion"
                    empresa.pais = "Paraguay"
                    empresa.email = "admin@cantinatita.com"
                    empresa.save()
                self.stdout.write(
                    self.style.SUCCESS("   ++ DatosEmpresa actualizado: Cantina Tita")
                )
                creados += 1
            else:
                self.stdout.write(f"   -- DatosEmpresa ya configurado: {empresa.razon_social}")
        else:
            self.stdout.write("   -- No hay registro de DatosEmpresa, creando...")
            if not dry_run:
                DatosEmpresa.objects.create(
                    ruc="80000000-0",
                    razon_social="Cantina Tita",
                    direccion="Asuncion, Paraguay",
                    ciudad="Asuncion",
                    pais="Paraguay",
                    telefono="+595 21 000000",
                    email="admin@cantinatita.com",
                    estado=True,
                )
            self.stdout.write(self.style.SUCCESS("   ++ DatosEmpresa creado"))
            creados += 1

        # ------------------------------------------------------------------
        # 4. Resumen
        # ------------------------------------------------------------------
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Resumen ==="))
        self.stdout.write(f"  Precios creados:     {creados}")
        self.stdout.write(f"  Ya existian:         {existentes}")
        self.stdout.write(f"  Stocks creados:      {stock_creados}")

        if dry_run:
            transaction.set_rollback(True)
            self.stdout.write(self.style.WARNING("\nDRY RUN: rollback aplicado, nada guardado."))
        else:
            # Verificar totales finales
            total_precios = PreciosPorLista.objects.count()
            total_prods = Productos.objects.count()
            total_listas = ListasPrecios.objects.count()
            total_stock = StockUnico.objects.count()
            esperados = total_prods * total_listas

            self.stdout.write(self.style.SUCCESS("\nOK Seed completado."))
            self.stdout.write(
                f"  PreciosPorLista: {total_precios}/{esperados} "
                f"({'completo' if total_precios >= esperados else 'INCOMPLETO'})"
            )
            self.stdout.write(f"  StockUnico: {total_stock}/{total_prods}")
