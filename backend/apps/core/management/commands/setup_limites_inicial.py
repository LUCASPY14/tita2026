"""
Management command para configurar límites de transacción iniciales.

Uso:
    python manage.py setup_limites_inicial
"""

from django.core.management.base import BaseCommand
from decimal import Decimal
from apps.core.models import LimitesTransaccion
from apps.usuarios.models import Roles


class Command(BaseCommand):
    help = "Configura límites de transacción iniciales para todos los roles"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🔧 Configurando límites de transacción iniciales...\n"))

        # Obtener roles
        try:
            rol_admin = Roles.objects.get(nombre_rol="Admin")
            rol_gerente = Roles.objects.get(nombre_rol="Gerente")
            rol_cajero = Roles.objects.get(nombre_rol="Cajero")
        except Roles.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: No se encontró algún rol."))
            self.stdout.write(self.style.WARNING(f"   Asegúrate de tener roles: Admin, Gerente, Cajero"))
            self.stdout.write(self.style.WARNING(f"   Detalles: {e}"))
            return

        # Configuración de límites
        limites_config = [
            # CAJERO - Límites restrictivos
            {
                "rol": rol_cajero,
                "tipo_operacion": "venta",
                "monto": Decimal("500000"),  # Gs. 500,000
                "doble_auth": False,
                "autorizadores": [rol_gerente, rol_admin],
            },
            {
                "rol": rol_cajero,
                "tipo_operacion": "descuento",
                "monto": Decimal("50000"),  # Gs. 50,000
                "doble_auth": False,
                "autorizadores": [rol_gerente, rol_admin],
            },
            {
                "rol": rol_cajero,
                "tipo_operacion": "nota_credito_cliente",
                "monto": Decimal("100000"),  # Gs. 100,000
                "doble_auth": False,
                "autorizadores": [rol_gerente, rol_admin],
            },
            {
                "rol": rol_cajero,
                "tipo_operacion": "exceder_credito",
                "monto": Decimal("0"),  # No puede exceder nunca
                "doble_auth": True,
                "autorizadores": [rol_gerente, rol_admin],
            },
            {
                "rol": rol_cajero,
                "tipo_operacion": "anular_venta",
                "monto": Decimal("200000"),  # Gs. 200,000
                "doble_auth": False,
                "autorizadores": [rol_gerente, rol_admin],
            },
            {
                "rol": rol_cajero,
                "tipo_operacion": "retiro_caja",
                "monto": Decimal("100000"),  # Gs. 100,000
                "doble_auth": False,
                "autorizadores": [rol_gerente, rol_admin],
            },
            {
                "rol": rol_cajero,
                "tipo_operacion": "devolucion",
                "monto": Decimal("150000"),  # Gs. 150,000
                "doble_auth": False,
                "autorizadores": [rol_gerente, rol_admin],
            },
            # GERENTE - Límites moderados
            {
                "rol": rol_gerente,
                "tipo_operacion": "venta",
                "monto": Decimal("2000000"),  # Gs. 2,000,000
                "doble_auth": False,
                "autorizadores": [rol_admin],
            },
            {
                "rol": rol_gerente,
                "tipo_operacion": "descuento",
                "monto": Decimal("300000"),  # Gs. 300,000
                "doble_auth": False,
                "autorizadores": [rol_admin],
            },
            {
                "rol": rol_gerente,
                "tipo_operacion": "nota_credito_cliente",
                "monto": Decimal("500000"),  # Gs. 500,000
                "doble_auth": False,
                "autorizadores": [rol_admin],
            },
            {
                "rol": rol_gerente,
                "tipo_operacion": "exceder_credito",
                "monto": Decimal("500000"),  # Gs. 500,000
                "doble_auth": False,
                "autorizadores": [rol_admin],
            },
            {
                "rol": rol_gerente,
                "tipo_operacion": "anular_venta",
                "monto": Decimal("1000000"),  # Gs. 1,000,000
                "doble_auth": False,
                "autorizadores": [rol_admin],
            },
            {
                "rol": rol_gerente,
                "tipo_operacion": "retiro_caja",
                "monto": Decimal("500000"),  # Gs. 500,000
                "doble_auth": False,
                "autorizadores": [rol_admin],
            },
            {
                "rol": rol_gerente,
                "tipo_operacion": "devolucion",
                "monto": Decimal("800000"),  # Gs. 800,000
                "doble_auth": False,
                "autorizadores": [rol_admin],
            },
            {
                "rol": rol_gerente,
                "tipo_operacion": "ajuste_inventario",
                "monto": Decimal("1000000"),  # Gs. 1,000,000 (valor del ajuste)
                "doble_auth": False,
                "autorizadores": [rol_admin],
            },
            # ADMIN - Sin límites (o muy altos)
            {
                "rol": rol_admin,
                "tipo_operacion": "venta",
                "monto": Decimal("999999999"),  # Sin límite práctico
                "doble_auth": False,
                "autorizadores": [],
            },
            {
                "rol": rol_admin,
                "tipo_operacion": "descuento",
                "monto": Decimal("999999999"),
                "doble_auth": False,
                "autorizadores": [],
            },
            {
                "rol": rol_admin,
                "tipo_operacion": "nota_credito_cliente",
                "monto": Decimal("5000000"),  # Gs. 5,000,000 (con doble auth)
                "doble_auth": True,  # Para NC grandes, doble autorización
                "autorizadores": [],
            },
            {
                "rol": rol_admin,
                "tipo_operacion": "ajuste_inventario",
                "monto": Decimal("999999999"),
                "doble_auth": False,
                "autorizadores": [],
            },
        ]

        # Crear límites
        creados = 0
        actualizados = 0
        errores = 0

        for config in limites_config:
            try:
                limite, created = LimitesTransaccion.objects.update_or_create(
                    id_rol=config["rol"],
                    tipo_operacion=config["tipo_operacion"],
                    defaults={
                        "monto_maximo_sin_autorizacion": config["monto"],
                        "requiere_autorizacion_doble": config["doble_auth"],
                        "estado": True,
                        "observaciones": f"Configuración inicial - {config['tipo_operacion']}",
                    },
                )

                # Configurar roles autorizadores
                if config["autorizadores"]:
                    limite.roles_autorizadores.set(config["autorizadores"])

                if created:
                    creados += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Creado: {config['rol'].nombre_rol} - {config['tipo_operacion']} = Gs. {config['monto']:,.0f}"
                        )
                    )
                else:
                    actualizados += 1
                    self.stdout.write(
                        f"🔄 Actualizado: {config['rol'].nombre_rol} - {config['tipo_operacion']} = Gs. {config['monto']:,.0f}"
                    )

            except Exception as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(f"❌ Error: {config['rol'].nombre_rol} - {config['tipo_operacion']}: {e}")
                )

        self.stdout.write(f"\n📊 Resumen:")
        self.stdout.write(self.style.SUCCESS(f"   ✅ Creados: {creados}"))
        self.stdout.write(f"   🔄 Actualizados: {actualizados}")
        if errores > 0:
            self.stdout.write(self.style.ERROR(f"   ❌ Errores: {errores}"))

        self.stdout.write(self.style.SUCCESS("\n✨ Configuración inicial completada!\n"))
