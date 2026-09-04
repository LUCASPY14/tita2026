"""
Exporta clientes (padres/tutores) e hijos a un CSV, una fila por familia con
los hijos en columnas repetidas (hijo1_*, hijo2_*, ...) — la cantidad de
columnas hijoN se ajusta sola al máximo de hijos que tenga alguna familia en
el resultado. Contraparte de `importar_clientes` — mismo layout, para poder
exportar, editar en una planilla y reimportar.

Uso:
    python manage.py exportar_clientes salida.csv
    python manage.py exportar_clientes salida.csv --todos   # incluye hijos inactivos
"""

import csv
from collections import defaultdict

from django.core.management.base import BaseCommand

from apps.clientes.models import Hijo

COLUMNAS_CLIENTE = [
    "cliente_id", "ruc_ci", "cliente_nombres", "cliente_apellidos",
    "cliente_email", "cliente_telefono", "cliente_direccion", "cliente_ciudad",
    "cliente_tipo", "cliente_lista_precio", "cliente_activo",
]
COLUMNAS_HIJO = ["nombre", "apellido", "fecha_nacimiento", "grado", "activo", "id"]


class Command(BaseCommand):
    help = "Exporta clientes e hijos a CSV (una fila por familia, hijos en columnas hijoN_*)."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", help="Ruta del archivo CSV de salida")
        parser.add_argument(
            "--todos", action="store_true",
            help="Incluir hijos inactivos (por defecto solo se exportan los activos)",
        )

    def handle(self, *args, **options):
        qs = Hijo.objects.select_related(
            "cliente_responsable", "grado", "tarjeta",
            "cliente_responsable__tipo_cliente", "cliente_responsable__lista_precio",
            "cliente_responsable__ciudad",
        )
        if not options["todos"]:
            qs = qs.filter(activo=True)
        qs = qs.order_by("cliente_responsable__apellidos", "cliente_responsable__nombres", "apellido", "nombre")

        por_cliente = defaultdict(list)
        for hijo in qs.iterator():
            por_cliente[hijo.cliente_responsable].append(hijo)

        max_hijos = max((len(h) for h in por_cliente.values()), default=1)
        columnas = COLUMNAS_CLIENTE + [
            f"hijo{n}_{campo}"
            for n in range(1, max_hijos + 1)
            for campo in ["nombre", "apellido", "fecha_nacimiento", "grado", "tarjeta"]
        ]

        with open(options["csv_path"], "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=columnas)
            writer.writeheader()
            for cliente, hijos in por_cliente.items():
                fila = {
                    "cliente_id": cliente.id_cliente,
                    "ruc_ci": cliente.ruc_ci,
                    "cliente_nombres": cliente.nombres,
                    "cliente_apellidos": cliente.apellidos,
                    "cliente_email": cliente.email or "",
                    "cliente_telefono": cliente.telefono or "",
                    "cliente_direccion": cliente.direccion or "",
                    "cliente_ciudad": cliente.ciudad.nombre if cliente.ciudad else "",
                    "cliente_tipo": cliente.tipo_cliente.nombre,
                    "cliente_lista_precio": cliente.lista_precio.nombre,
                    "cliente_activo": cliente.activo,
                }
                for n, hijo in enumerate(hijos, start=1):
                    tarjeta = getattr(hijo, "tarjeta", None)
                    fila[f"hijo{n}_nombre"] = hijo.nombre
                    fila[f"hijo{n}_apellido"] = hijo.apellido
                    fila[f"hijo{n}_fecha_nacimiento"] = hijo.fecha_nacimiento.isoformat() if hijo.fecha_nacimiento else ""
                    fila[f"hijo{n}_grado"] = hijo.grado.nombre if hijo.grado else ""
                    fila[f"hijo{n}_tarjeta"] = tarjeta.nro_tarjeta if tarjeta else ""
                writer.writerow(fila)

        self.stdout.write(self.style.SUCCESS(
            f"Exportadas {len(por_cliente)} familia(s) / {sum(len(h) for h in por_cliente.values())} hijo(s) a {options['csv_path']}"
        ))
