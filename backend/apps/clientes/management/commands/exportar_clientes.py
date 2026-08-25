"""
Exporta clientes (padres/tutores) e hijos a un CSV, una fila por hijo con los
datos del cliente responsable repetidos. Pensado como contraparte de
`importar_clientes` — mismo layout de columnas, para poder exportar, editar
en una planilla y reimportar.

Uso:
    python manage.py exportar_clientes salida.csv
    python manage.py exportar_clientes salida.csv --todos   # incluye inactivos
"""

import csv

from django.core.management.base import BaseCommand

from apps.clientes.models import Hijo


class Command(BaseCommand):
    help = "Exporta clientes e hijos a CSV (una fila por hijo)."

    COLUMNAS = [
        "cliente_id", "ruc_ci", "cliente_nombres", "cliente_apellidos",
        "cliente_email", "cliente_telefono", "cliente_direccion", "cliente_ciudad",
        "cliente_tipo", "cliente_lista_precio", "cliente_activo",
        "hijo_id", "hijo_nombre", "hijo_apellido", "hijo_fecha_nacimiento",
        "hijo_grado", "hijo_activo",
    ]

    def add_arguments(self, parser):
        parser.add_argument("csv_path", help="Ruta del archivo CSV de salida")
        parser.add_argument(
            "--todos", action="store_true",
            help="Incluir hijos inactivos (por defecto solo se exportan los activos)",
        )

    def handle(self, *args, **options):
        qs = Hijo.objects.select_related("cliente_responsable", "grado", "cliente_responsable__tipo_cliente",
                                          "cliente_responsable__lista_precio")
        if not options["todos"]:
            qs = qs.filter(activo=True)
        qs = qs.order_by("cliente_responsable__apellidos", "cliente_responsable__nombres", "apellido", "nombre")

        total = 0
        with open(options["csv_path"], "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=self.COLUMNAS)
            writer.writeheader()
            for hijo in qs.iterator():
                c = hijo.cliente_responsable
                writer.writerow({
                    "cliente_id": c.id,
                    "ruc_ci": c.ruc_ci,
                    "cliente_nombres": c.nombres,
                    "cliente_apellidos": c.apellidos,
                    "cliente_email": c.email or "",
                    "cliente_telefono": c.telefono or "",
                    "cliente_direccion": c.direccion or "",
                    "cliente_ciudad": c.ciudad or "",
                    "cliente_tipo": c.tipo_cliente.nombre,
                    "cliente_lista_precio": c.lista_precio.nombre,
                    "cliente_activo": c.activo,
                    "hijo_id": hijo.id,
                    "hijo_nombre": hijo.nombre,
                    "hijo_apellido": hijo.apellido,
                    "hijo_fecha_nacimiento": hijo.fecha_nacimiento.isoformat() if hijo.fecha_nacimiento else "",
                    "hijo_grado": hijo.grado.nombre if hijo.grado else "",
                    "hijo_activo": hijo.activo,
                })
                total += 1

        self.stdout.write(self.style.SUCCESS(f"Exportados {total} hijo(s) a {options['csv_path']}"))
