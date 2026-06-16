"""
python manage.py seed_precios [--lista "Nombre Lista"] [--dry-run]

Crea la lista de precios por defecto y la puebla con los precios más recientes
encontrados en el historial de ventas de cada producto.

Los productos sin ventas previas quedan con el precio que el operador
indique en --precio-base (default 0) para que se carguen manualmente.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Crea la lista de precios por defecto y la carga desde historial de ventas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--lista",
            default="Lista General",
            help="Nombre de la lista de precios a crear/usar (default: 'Lista General')",
        )
        parser.add_argument(
            "--precio-base",
            type=int,
            default=0,
            help="Precio para productos sin historial de ventas (default: 0)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo muestra qué haría sin guardar nada",
        )

    def handle(self, *args, **options):
        from apps.productos.models import ListaPrecio, PrecioPorLista, Producto
        from apps.ventas.models import DetalleVenta

        nombre_lista = options["lista"]
        precio_base  = options["precio_base"]
        dry_run      = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("-- DRY RUN: no se guardan cambios --\n"))

        # ── 1. Precio más reciente por producto desde ventas ──────────────────
        # Para cada producto, tomamos el precio_unitario de la venta más reciente
        # (las ventas reales son la fuente de verdad del precio cobrado).
        from django.db.models import Max
        from apps.ventas.models import Venta

        ultimas_ventas = (
            DetalleVenta.objects
            .filter(venta__estado="ACTIVA")
            .values("producto_id")
            .annotate(ultima_venta=Max("venta__fecha"))
        )

        precio_por_producto: dict[int, int] = {}
        for row in ultimas_ventas:
            pid = row["producto_id"]
            ultima = row["ultima_venta"]
            detalle = (
                DetalleVenta.objects
                .filter(producto_id=pid, venta__fecha=ultima, venta__estado="ACTIVA")
                .order_by("-id")
                .values("precio_unitario")
                .first()
            )
            if detalle:
                precio_por_producto[pid] = int(detalle["precio_unitario"])

        # ── 2. Todos los productos activos ────────────────────────────────────
        productos = list(Producto.objects.filter(activo=True).order_by("descripcion"))

        self.stdout.write(f"\nProductos activos: {len(productos)}")
        self.stdout.write(f"Con historial de precios: {len(precio_por_producto)}")
        self.stdout.write(f"Sin historial (usarán Gs. {precio_base:,}): "
                          f"{len(productos) - len(precio_por_producto)}\n")

        self.stdout.write(f"{'Producto':<40} {'Precio':>12}  {'Fuente'}")
        self.stdout.write("-" * 65)
        for p in productos:
            precio = precio_por_producto.get(p.id, precio_base)
            fuente = "historial ventas" if p.id in precio_por_producto else "precio-base (sin ventas)"
            self.stdout.write(f"  {p.descripcion:<38} Gs. {precio:>8,}  {fuente}")

        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN terminado. Usa sin --dry-run para aplicar."))
            return

        # ── 3. Crear/actualizar lista por defecto ─────────────────────────────
        with transaction.atomic():
            lista, created = ListaPrecio.objects.get_or_create(
                nombre=nombre_lista,
                defaults={"es_por_defecto": True, "activo": True, "moneda": "PYG"},
            )
            if not created and not lista.es_por_defecto:
                lista.es_por_defecto = True
                lista.activo = True
                lista.save()
                self.stdout.write(f"\nLista '{nombre_lista}' marcada como por defecto.")
            elif created:
                self.stdout.write(self.style.SUCCESS(f"\nLista '{nombre_lista}' creada como por defecto."))
            else:
                self.stdout.write(f"\nLista '{nombre_lista}' ya existía y es por defecto.")

            # ── 4. Cargar precios ─────────────────────────────────────────────
            creados = actualizados = sin_cambio = 0
            for p in productos:
                precio = precio_por_producto.get(p.id, precio_base)
                obj, was_created = PrecioPorLista.objects.get_or_create(
                    producto=p,
                    lista=lista,
                    defaults={"precio_unitario": precio},
                )
                if was_created:
                    creados += 1
                elif int(obj.precio_unitario) != precio:
                    obj.precio_unitario = precio
                    obj.save(update_fields=["precio_unitario"])
                    actualizados += 1
                else:
                    sin_cambio += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nListo: {creados} creados, {actualizados} actualizados, {sin_cambio} sin cambio."
        ))
        self.stdout.write(
            f"Los productos con precio Gs. 0 deben actualizarse manualmente "
            f"desde Configuracion > Listas de Precios."
        )
