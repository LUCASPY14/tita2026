"""
Management command para datos de negocio iniciales.

Seed data que no generan los otros comandos:
  - MediosPago (Efectivo, Tarjeta, Transferencia, QR, Cheque)
  - RestriccionesHorarias (horario comercial Mon-Sáb)

Uso:
    python manage.py seed_negocio
    python manage.py seed_negocio --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = "Carga datos de negocio iniciales: MediosPago y RestriccionesHorarias"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mostrar qué se crearía sin guardar nada",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("=== DRY RUN — no se guardan cambios ===\n"))

        self.stdout.write(self.style.MIGRATE_HEADING("=== Seed de datos de negocio ===\n"))

        creados = 0
        existentes = 0

        # ------------------------------------------------------------------
        # 1. Medios de Pago
        # ------------------------------------------------------------------
        self.stdout.write("1. Medios de Pago...")
        from apps.core.models import MediosPago

        medios = [
            {"descripcion": "Efectivo", "genera_comision": False, "requiere_validacion": False},
            {"descripcion": "Tarjeta de Débito", "genera_comision": False, "requiere_validacion": True},
            {"descripcion": "Tarjeta de Crédito", "genera_comision": True, "requiere_validacion": True},
            {"descripcion": "Transferencia Bancaria", "genera_comision": False, "requiere_validacion": False},
            {"descripcion": "Cheque", "genera_comision": False, "requiere_validacion": True},
            {"descripcion": "QR (SIPAP)", "genera_comision": False, "requiere_validacion": True},
            {"descripcion": "Cuenta Corriente", "genera_comision": False, "requiere_validacion": False},
        ]

        for m in medios:
            exists = MediosPago.objects.filter(descripcion=m["descripcion"]).exists()
            if exists:
                self.stdout.write(f'   -- Ya existe: {m["descripcion"]}')
                existentes += 1
            else:
                if not dry_run:
                    MediosPago.objects.create(**m, estado=True)
                self.stdout.write(self.style.SUCCESS(f'   ++ Creado: {m["descripcion"]}'))
                creados += 1

        # ------------------------------------------------------------------
        # 2. Restricciones Horarias (horario comercial general)
        # ------------------------------------------------------------------
        self.stdout.write("\n2. Restricciones Horarias...")
        from apps.notificaciones.models import RestriccionesHorarias

        now = timezone.now()

        dias_semana = [
            ("Lunes", "07:00", "20:00"),
            ("Martes", "07:00", "20:00"),
            ("Miércoles", "07:00", "20:00"),
            ("Jueves", "07:00", "20:00"),
            ("Viernes", "07:00", "20:00"),
            ("Sábado", "07:00", "15:00"),
        ]

        for dia, h_inicio, h_fin in dias_semana:
            exists = RestriccionesHorarias.objects.filter(
                tipo_usuario="empleado", dia_semana=dia
            ).exists()
            if exists:
                self.stdout.write(f"   -- Ya existe restriccion para empleado/{dia}")
                existentes += 1
            else:
                if not dry_run:
                    RestriccionesHorarias.objects.create(
                        tipo_usuario="empleado",
                        dia_semana=dia,
                        hora_inicio=h_inicio,
                        hora_fin=h_fin,
                        estado=True,
                        fecha_creacion=now,
                    )
                self.stdout.write(
                    self.style.SUCCESS(f"   ++ Creado: empleado/{dia} {h_inicio}-{h_fin}")
                )
                creados += 1

        # ------------------------------------------------------------------
        # 3. Clientes de muestra (datos ficticios Paraguay)
        # ------------------------------------------------------------------
        self.stdout.write("\n3. Clientes de muestra...")
        from apps.clientes.models import Clientes, TiposCliente
        from apps.productos.models import ListasPrecios

        lista_general, _ = ListasPrecios.objects.get_or_create(
            nombre_lista="General", defaults={"estado": True}
        )
        tipo_regular, _ = TiposCliente.objects.get_or_create(
            nombre_tipo="Regular", defaults={"estado": True}
        )
        tipo_empresa, _ = TiposCliente.objects.get_or_create(
            nombre_tipo="Empresa", defaults={"estado": True}
        )

        clientes_seed = [
            {
                "nombres": "Maria Elena",
                "apellidos": "Gonzalez Riquelme",
                "ruc_ci": "3456789-1",
                "telefono": "0981-234-567",
                "email": "mgonzalez@gmail.com",
                "limite_credito": 500000,
                "id_tipo_cliente": tipo_regular,
            },
            {
                "nombres": "Carlos Alberto",
                "apellidos": "Benitez Duarte",
                "ruc_ci": "4567890-2",
                "telefono": "0982-345-678",
                "email": "cbenitez@hotmail.com",
                "limite_credito": 750000,
                "id_tipo_cliente": tipo_regular,
            },
            {
                "nombres": "Ana Sofia",
                "apellidos": "Martinez Soria",
                "ruc_ci": "5678901-3",
                "telefono": "0983-456-789",
                "email": "amartinez@gmail.com",
                "limite_credito": 300000,
                "id_tipo_cliente": tipo_regular,
            },
            {
                "nombres": "Luis Fernando",
                "apellidos": "Ayala Cabral",
                "ruc_ci": "6789012-4",
                "telefono": "0984-567-890",
                "email": "layala@gmail.com",
                "limite_credito": 1000000,
                "id_tipo_cliente": tipo_regular,
            },
            {
                "nombres": "Patricia Raquel",
                "apellidos": "Romero Villalba",
                "ruc_ci": "7890123-5",
                "telefono": "0985-678-901",
                "email": "promero@yahoo.com",
                "limite_credito": 600000,
                "id_tipo_cliente": tipo_regular,
            },
            {
                "nombres": "Jorge Daniel",
                "apellidos": "Acosta Mendoza",
                "ruc_ci": "8901234-6",
                "telefono": "0986-789-012",
                "email": "jacosta@gmail.com",
                "limite_credito": 450000,
                "id_tipo_cliente": tipo_regular,
            },
            {
                "nombres": "Claudia Viviana",
                "apellidos": "Sanabria Perez",
                "ruc_ci": "9012345-7",
                "telefono": "0987-890-123",
                "email": "csanabria@gmail.com",
                "limite_credito": 800000,
                "id_tipo_cliente": tipo_regular,
            },
            {
                "nombres": "Roberto Eduardo",
                "apellidos": "Garay Leiva",
                "ruc_ci": "10123456-8",
                "telefono": "0988-901-234",
                "email": "rgaray@hotmail.com",
                "limite_credito": 550000,
                "id_tipo_cliente": tipo_regular,
            },
            {
                "nombres": "Cantina",
                "apellidos": "Escuela ABC",
                "ruc_ci": "80012345-6",
                "telefono": "021-234-567",
                "email": "cantina@escuelaabc.edu.py",
                "limite_credito": 5000000,
                "id_tipo_cliente": tipo_empresa,
                "razon_social": "Cooperadora Escuela ABC S.R.L.",
            },
            {
                "nombres": "Asociacion",
                "apellidos": "de Padres",
                "ruc_ci": "80098765-1",
                "telefono": "021-876-543",
                "email": "apepadres@gmail.com",
                "limite_credito": 3000000,
                "id_tipo_cliente": tipo_empresa,
                "razon_social": "Asociacion de Padres y Tutores",
            },
        ]

        for c in clientes_seed:
            ruc = c.pop("ruc_ci")
            exists = Clientes.objects.filter(ruc_ci=ruc).exists()
            if exists:
                self.stdout.write(f"   -- Ya existe: {c['apellidos']}, {c['nombres']}")
                existentes += 1
                c["ruc_ci"] = ruc
            else:
                if not dry_run:
                    Clientes.objects.create(
                        ruc_ci=ruc,
                        id_lista=lista_general,
                        estado=True,
                        **c,
                    )
                self.stdout.write(
                    self.style.SUCCESS(f"   ++ Creado: {c['apellidos']}, {c['nombres']}")
                )
                creados += 1
                c["ruc_ci"] = ruc  # restaurar por si loop lo usa

        # ------------------------------------------------------------------
        # 5. Resumen
        # ------------------------------------------------------------------
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Resumen ==="))
        self.stdout.write(f"  Registros creados:   {creados}")
        self.stdout.write(f"  Ya existían:         {existentes}")

        if dry_run:
            transaction.set_rollback(True)
            self.stdout.write(self.style.WARNING("\nDRY RUN: rollback aplicado, nada guardado."))
        else:
            self.stdout.write(self.style.SUCCESS("\nOK Seed completado.\n"))
            self.stdout.write("Próximos pasos recomendados:")
            self.stdout.write("  python manage.py crear_roles_iniciales")
            self.stdout.write("  python manage.py init_usuarios")
