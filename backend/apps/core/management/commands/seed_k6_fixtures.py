"""
seed_k6_fixtures — Datos mínimos para ejecutar los tests de carga k6.

Crea / asegura (idempotente):
  - 5 clientes k6 con sus hijos (RUC-CI: K6C-001…K6C-005)
  - 5 tarjetas: 10000001…10000005  (saldo 1.000.000 Gs, ACTIVA)
  - 1 producto activo (usa pk=1 si existe, si no crea uno)
  - 5 cajas: "Caja K6-1"…"Caja K6-5"
  - 5 cajeros: cajero1@cantina.test…cajero5@cantina.test  (pass: Test1234!)
  - 5 CierreCaja ABIERTOS: uno por cajero

Al finalizar imprime los IDs necesarios para ejecutar k6:
  k6 run --env BASE_URL=http://localhost:8000 \\
         --env K6_CLIENTE_ID=<id> \\
         tests/load/k6/caja.js

Uso:
    python manage.py seed_k6_fixtures
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone


class Command(BaseCommand):
    help = "Seed de fixtures para tests de carga k6 (idempotente)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("═══ seed_k6_fixtures ═══\n"))

        with transaction.atomic():
            lista, tipo, grado = self._seed_prereqs()
            clientes, hijos = self._seed_clientes(lista, tipo, grado)
            self._seed_tarjetas(hijos)
            producto_pk = self._seed_producto()
            cajas = self._seed_cajas()
            cajeros = self._seed_cajeros()
            self._seed_cierres(cajeros, cajas)

        cliente_id = clientes[0].pk
        self.stdout.write(self.style.SUCCESS("\n═══ seed_k6_fixtures completado ═══\n"))
        self.stdout.write(
            f"Cajeros : cajero1@cantina.test … cajero5@cantina.test  (pass: Test1234!)\n"
            f"Tarjetas: 10000001 … 10000005  (saldo: Gs 1.000.000 c/u)\n"
            f"Producto: pk={producto_pk}\n"
            f"Cliente : pk={cliente_id}  (K6C-001)\n\n"
            "Ejecutar k6:\n"
            f"  k6 run --env BASE_URL=http://localhost:8000 \\\n"
            f"         --env K6_CLIENTE_ID={cliente_id} \\\n"
            f"         tests/load/k6/caja.js\n"
        )

    # =========================================================================
    # 1. PRERREQUISITOS
    # =========================================================================

    def _seed_prereqs(self):
        from apps.clientes.models import Grado, TipoCliente
        from apps.productos.models import ListaPrecio

        lista = (
            ListaPrecio.objects.filter(es_por_defecto=True, activo=True).first()
            or ListaPrecio.objects.filter(activo=True).first()
        )
        if not lista:
            lista, _ = ListaPrecio.objects.get_or_create(
                nombre="Lista General",
                defaults={"moneda": "PYG", "activo": True, "es_por_defecto": True},
            )

        tipo = (
            TipoCliente.objects.filter(nombre="Familia", activo=True).first()
            or TipoCliente.objects.filter(activo=True).first()
        )
        if not tipo:
            tipo, _ = TipoCliente.objects.get_or_create(
                nombre="Familia", defaults={"activo": True}
            )

        grado = Grado.objects.filter(activo=True).first()
        if not grado:
            grado, _ = Grado.objects.get_or_create(
                nombre="1° Grado A", defaults={"activo": True}
            )

        return lista, tipo, grado

    # =========================================================================
    # 2. CLIENTES + HIJOS
    # =========================================================================

    def _seed_clientes(self, lista, tipo, grado):
        from apps.clientes.models import Cliente, Hijo

        clientes, hijos = [], []
        for i in range(1, 6):
            cliente, _ = Cliente.objects.get_or_create(
                ruc_ci=f"K6C-{i:03d}",
                defaults={
                    "nombres": "Cliente",
                    "apellidos": f"K6-{i}",
                    "email": f"cliente.k6.{i}@cantina.test",
                    "tipo_cliente": tipo,
                    "lista_precio": lista,
                    "activo": True,
                },
            )
            clientes.append(cliente)

            hijo, _ = Hijo.objects.get_or_create(
                cliente_responsable=cliente,
                nombre="Alumno",
                apellido=f"K6-{i}",
                defaults={"grado": grado, "activo": True},
            )
            hijos.append(hijo)

        self.stdout.write(f"  Clientes k6 : {len(clientes)} asegurados")
        return clientes, hijos

    # =========================================================================
    # 3. TARJETAS
    # =========================================================================

    def _seed_tarjetas(self, hijos):
        from apps.core.models import Tarjeta

        numeros = ["10000001", "10000002", "10000003", "10000004", "10000005"]
        creadas = 0
        for nro, hijo in zip(numeros, hijos):
            _, created = Tarjeta.objects.get_or_create(
                nro_tarjeta=nro,
                defaults={
                    "hijo": hijo,
                    "saldo_actual": Decimal("1000000"),
                    "estado": Tarjeta.Estado.ACTIVA,
                    "saldo_alerta": Decimal("10000"),
                    "notificar_saldo_bajo": False,
                },
            )
            if created:
                creadas += 1

        self.stdout.write(
            f"  Tarjetas    : {creadas} nuevas / {5 - creadas} ya existían"
        )

    # =========================================================================
    # 4. PRODUCTO
    # =========================================================================

    def _seed_producto(self):
        from apps.productos.models import (
            Categoria, ListaPrecio, PrecioPorLista, Producto, UnidadMedida,
        )

        # El k6 test usa `producto: 1` de forma fija — asegurar que pk=1 exista.
        if Producto.objects.filter(pk=1).exists():
            prod = Producto.objects.get(pk=1)
            # Asegurar al menos un precio en alguna lista activa
            if not PrecioPorLista.objects.filter(producto=prod).exists():
                lista = ListaPrecio.objects.filter(activo=True).first()
                if lista:
                    PrecioPorLista.objects.create(
                        producto=prod,
                        lista=lista,
                        precio_unitario=Decimal("5000"),
                    )
            self.stdout.write(f"  Producto    : pk=1 '{prod.descripcion}' (ya existe)")
            return 1

        # No existe pk=1 — crear uno con ese id exacto y corregir la secuencia
        cat, _ = Categoria.objects.get_or_create(
            nombre="Comidas", defaults={"activo": True}
        )
        unidad, _ = UnidadMedida.objects.get_or_create(
            abreviatura="Un", defaults={"nombre": "Unidad", "activo": True}
        )
        lista, _ = ListaPrecio.objects.get_or_create(
            nombre="Lista General",
            defaults={"moneda": "PYG", "activo": True, "es_por_defecto": True},
        )
        prod = Producto(
            id=1,
            codigo="K6-001",
            descripcion="Empanada k6",
            categoria=cat,
            unidad_medida=unidad,
            activo=True,
            requiere_stock=False,
            stock_minimo=Decimal("0"),
        )
        prod.save(force_insert=True)
        PrecioPorLista.objects.create(
            producto=prod,
            lista=lista,
            precio_unitario=Decimal("5000"),
        )
        self._reset_sequence("productos_producto")
        self.stdout.write("  Producto    : pk=1 'Empanada k6' (creado)")
        return 1

    # =========================================================================
    # 5. CAJAS
    # =========================================================================

    def _seed_cajas(self):
        from apps.contabilidad.models import Caja

        cajas = []
        for i in range(1, 6):
            caja, created = Caja.objects.get_or_create(
                nombre=f"Caja K6-{i}",
                defaults={"ubicacion": f"k6 VU-{i}", "activo": True},
            )
            cajas.append(caja)

        self.stdout.write(f"  Cajas k6    : {len(cajas)} aseguradas")
        return cajas

    # =========================================================================
    # 6. CAJEROS
    # =========================================================================

    def _seed_cajeros(self):
        from apps.usuarios.models import Usuario

        cajeros = []
        for i in range(1, 6):
            cajero, created = Usuario.objects.get_or_create(
                email=f"cajero{i}@cantina.test",
                defaults={
                    "nombre": "Cajero",
                    "apellido": f"K6-{i}",
                    "rol": Usuario.Rol.CAJERO,
                    "is_active": True,
                    "email_verificado": True,
                },
            )
            if created:
                cajero.set_password("Test1234!")
                cajero.save()
            cajeros.append(cajero)

        self.stdout.write(f"  Cajeros     : {len(cajeros)} asegurados")
        return cajeros

    # =========================================================================
    # 7. CIERRES DE CAJA
    # =========================================================================

    def _seed_cierres(self, cajeros, cajas):
        from apps.contabilidad.models import CierreCaja

        creados = 0
        for cajero, caja in zip(cajeros, cajas):
            existe = CierreCaja.objects.filter(
                empleado=cajero,
                estado=CierreCaja.Estado.ABIERTO,
            ).exists()
            if not existe:
                CierreCaja.objects.create(
                    caja=caja,
                    empleado=cajero,
                    fecha_apertura=timezone.now(),
                    monto_inicial=Decimal("0"),
                    estado=CierreCaja.Estado.ABIERTO,
                )
                creados += 1

        ya = 5 - creados
        self.stdout.write(
            f"  CierreCaja  : {creados} nuevos / {ya} ya estaban abiertos"
        )

    # =========================================================================
    # UTILIDADES
    # =========================================================================

    def _reset_sequence(self, table_name):
        """Sincroniza la secuencia autoincrement tras insertar con ID explícito."""
        with connection.cursor() as cur:
            cur.execute(
                f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), "
                f"GREATEST(MAX(id), 1)) FROM {table_name}"
            )
