"""
Crea datos demo completos para probar el portal de padres.
Idempotente: puede ejecutarse repetidas veces sin duplicar datos.

Crea:
  - Usuario portal@tita.local  (CLIENTE_WEB, demo1234)
  - Cliente "Demo Padre Portal" vinculado al usuario
  - 2 Hijos con sus tarjetas RFID (DEMO-001, DEMO-002)
  - 8 Ventas historicas con detalles (para el tab Cantina)
  - 2 Notificaciones de sistema no leidas

Uso:
    python manage.py seed_portal_demo
    python manage.py seed_portal_demo --reset   # elimina y recrea
"""

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


NRO_TARJETA_1 = "DEMO-001"
NRO_TARJETA_2 = "DEMO-002"
EMAIL_PORTAL  = "portal@tita.local"


class Command(BaseCommand):
    help = "Crea datos demo para el portal de padres."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Elimina los datos demo antes de recrearlos",
        )
        parser.add_argument(
            "--password",
            default="demo1234",
            help="Contrasena del usuario portal demo (default: demo1234)",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== seed_portal_demo ==="))

        with transaction.atomic():
            if options["reset"]:
                self._reset()

            usuario    = self._crear_usuario(options["password"])
            cliente    = self._crear_cliente(usuario)
            hijo1, hijo2 = self._crear_hijos(cliente)
            tarjeta1, tarjeta2 = self._crear_tarjetas(hijo1, hijo2)
            self._crear_ventas(cliente, hijo1, tarjeta1, hijo2, tarjeta2)
            self._crear_notificaciones(usuario)

        self.stdout.write(self.style.SUCCESS(
            f"\nListo. Credenciales: {EMAIL_PORTAL} / {options['password']}"
        ))

    # ── reset ─────────────────────────────────────────────────────────────────

    def _reset(self):
        from apps.usuarios.models import Usuario
        from apps.core.models import Tarjeta
        from apps.ventas.models import Venta
        from apps.notificaciones.models import Notificacion

        self.stdout.write("  Reseteando datos demo portal...")

        for nro in [NRO_TARJETA_1, NRO_TARJETA_2]:
            try:
                t = Tarjeta.objects.get(nro_tarjeta=nro)
                Venta.objects.filter(tarjeta=t).delete()
                t.delete()
            except Tarjeta.DoesNotExist:
                pass

        if Usuario.objects.filter(email=EMAIL_PORTAL).exists():
            u = Usuario.objects.get(email=EMAIL_PORTAL)
            Notificacion.objects.filter(usuario=u).delete()
            if hasattr(u, "cliente") and u.cliente:
                u.cliente.hijos.all().delete()
                u.cliente.delete()
            u.delete()

    # ── usuario portal ─────────────────────────────────────────────────────────

    def _crear_usuario(self, password: str):
        from apps.usuarios.models import Usuario

        user, created = Usuario.objects.get_or_create(
            email=EMAIL_PORTAL,
            defaults={
                "nombre": "Padre",
                "apellido": "Demo",
                "rol": Usuario.Rol.CLIENTE_WEB,
                "is_active": True,
                "email_verificado": True,
            },
        )
        user.set_password(password)
        if not created:
            user.rol = Usuario.Rol.CLIENTE_WEB
            user.is_active = True
        user.save()
        self._log("Usuario", EMAIL_PORTAL, created)
        return user

    # ── cliente ────────────────────────────────────────────────────────────────

    def _crear_cliente(self, usuario):
        from apps.clientes.models import Cliente, TipoCliente
        from apps.productos.models import ListaPrecio

        if getattr(usuario, "cliente", None):
            self.stdout.write("    = Cliente: ya vinculado")
            return usuario.cliente

        tipo = TipoCliente.objects.filter(activo=True).first()
        lista = ListaPrecio.objects.first()

        if not tipo or not lista:
            raise RuntimeError(
                "No hay TipoCliente o ListaPrecio en la DB. "
                "Ejecuta primero: python manage.py seed_negocio"
            )

        cliente = Cliente.objects.create(
            nombres="Padre",
            apellidos="Demo",
            ruc_ci="9999999-9",
            email=EMAIL_PORTAL,
            tipo_cliente=tipo,
            lista_precio=lista,
            activo=True,
        )
        usuario.cliente = cliente
        usuario.save(update_fields=["cliente"])
        self.stdout.write("    + Cliente: Padre Demo (ruc_ci=9999999-9)")
        return cliente

    # ── hijos ──────────────────────────────────────────────────────────────────

    def _crear_hijos(self, cliente):
        from apps.clientes.models import Hijo, Grado

        grado = Grado.objects.filter(activo=True).first()

        hijo1, c1 = Hijo.objects.get_or_create(
            cliente_responsable=cliente,
            nombre="Lucas",
            apellido="Demo",
            defaults={"grado": grado, "activo": True},
        )
        self._log("Hijo", "Lucas Demo", c1)

        hijo2, c2 = Hijo.objects.get_or_create(
            cliente_responsable=cliente,
            nombre="Sofia",
            apellido="Demo",
            defaults={"grado": grado, "activo": True},
        )
        self._log("Hijo", "Sofia Demo", c2)

        return hijo1, hijo2

    # ── tarjetas ───────────────────────────────────────────────────────────────

    def _crear_tarjetas(self, hijo1, hijo2):
        from apps.core.models import Tarjeta

        tarjeta1, c1 = Tarjeta.objects.get_or_create(
            nro_tarjeta=NRO_TARJETA_1,
            defaults={
                "hijo": hijo1,
                "saldo_actual": Decimal("85000"),
                "estado": Tarjeta.Estado.ACTIVA,
                "saldo_alerta": Decimal("20000"),
                "notificar_saldo_bajo": True,
            },
        )
        if not c1:
            tarjeta1.hijo = hijo1
            tarjeta1.save(update_fields=["hijo"])
        self._log("Tarjeta", f"{NRO_TARJETA_1} -> {hijo1}", c1)

        tarjeta2, c2 = Tarjeta.objects.get_or_create(
            nro_tarjeta=NRO_TARJETA_2,
            defaults={
                "hijo": hijo2,
                "saldo_actual": Decimal("12000"),
                "estado": Tarjeta.Estado.ACTIVA,
                "saldo_alerta": Decimal("20000"),
                "notificar_saldo_bajo": True,
            },
        )
        if not c2:
            tarjeta2.hijo = hijo2
            tarjeta2.save(update_fields=["hijo"])
        self._log("Tarjeta", f"{NRO_TARJETA_2} -> {hijo2}", c2)

        return tarjeta1, tarjeta2

    # ── ventas históricas ──────────────────────────────────────────────────────

    def _crear_ventas(self, cliente, hijo1, tarjeta1, hijo2, tarjeta2):
        from apps.ventas.models import Venta, DetalleVenta
        from apps.productos.models import Producto
        from apps.usuarios.models import Usuario

        if Venta.objects.filter(tarjeta__in=[tarjeta1, tarjeta2]).exists():
            self.stdout.write("    = Ventas: ya existen")
            return

        cajero = (
            Usuario.objects.filter(is_active=True, rol=Usuario.Rol.CAJERO).first()
            or Usuario.objects.filter(is_active=True).first()
        )
        productos = list(Producto.objects.filter(activo=True)[:5])
        if not productos:
            self.stdout.write(self.style.WARNING("    ! Sin productos activos, saltando ventas."))
            return

        def precio(p):
            return p.precio_actual or Decimal("5000")

        # 8 ventas distribuidas en los últimos 30 días
        # items: [(producto_idx, cantidad)] — índices únicos por venta (unique_together)
        ventas_spec = [
            (hijo1, tarjeta1, 28, [(0, 2), (2, 1)]),
            (hijo1, tarjeta1, 21, [(1, 1), (3, 2)]),
            (hijo1, tarjeta1, 14, [(0, 1), (4, 1)]),
            (hijo1, tarjeta1, 10, [(2, 3), (3, 1)]),
            (hijo1, tarjeta1,  3, [(0, 1), (1, 1), (4, 1)]),
            (hijo2, tarjeta2, 25, [(1, 1), (4, 2)]),
            (hijo2, tarjeta2, 12, [(0, 2), (3, 1)]),
            (hijo2, tarjeta2,  5, [(2, 1), (4, 1)]),
        ]

        creadas = 0
        for hijo, tarjeta, dias, items in ventas_spec:
            monto = sum(
                precio(productos[idx]) * cantidad
                for idx, cantidad in items
                if idx < len(productos)
            )
            fecha = timezone.now() - timedelta(days=dias)
            venta = Venta.objects.create(
                cliente=cliente,
                hijo=hijo,
                tarjeta=tarjeta,
                cajero=cajero,
                fecha=fecha,
                tipo=Venta.Tipo.CONTADO,
                estado=Venta.Estado.ACTIVA,
                estado_pago=Venta.EstadoPago.PAGADO,
                monto_total=monto,
            )
            for idx, cantidad in items:
                if idx >= len(productos):
                    continue
                prod = productos[idx]
                pu = precio(prod)
                DetalleVenta.objects.create(
                    venta=venta,
                    producto=prod,
                    cantidad=cantidad,
                    precio_unitario=pu,
                    subtotal=pu * cantidad,
                )
            creadas += 1

        self.stdout.write(f"    + Ventas: {creadas} creadas")

    # ── notificaciones ─────────────────────────────────────────────────────────

    def _crear_notificaciones(self, usuario):
        from apps.notificaciones.models import Notificacion

        if Notificacion.objects.filter(usuario=usuario).exists():
            self.stdout.write("    = Notificaciones: ya existen")
            return

        Notificacion.objects.create(
            usuario=usuario,
            tipo=Notificacion.Tipo.SALDO_BAJO,
            titulo="Saldo bajo en tarjeta",
            mensaje="El saldo de la tarjeta de Sofia Demo esta por debajo del umbral configurado (Gs. 12.000).",
            destino=Notificacion.Destino.SISTEMA,
            leida=False,
        )
        Notificacion.objects.create(
            usuario=usuario,
            tipo=Notificacion.Tipo.RECARGA,
            titulo="Recarga exitosa",
            mensaje="Se acredito Gs. 50.000 a la tarjeta de Lucas Demo.",
            destino=Notificacion.Destino.SISTEMA,
            leida=True,
        )
        self.stdout.write("    + Notificaciones: 2 creadas")

    # ── helpers ────────────────────────────────────────────────────────────────

    def _log(self, model: str, name: str, created: bool):
        prefix = "+" if created else "="
        self.stdout.write(f"    {prefix} {model}: {name}")
