"""
management command: create_year_partition

Crea las particiones del año indicado para las tablas históricas particionadas.
Debe ejecutarse una vez al año, idealmente el 1 de diciembre del año anterior.

Uso:
    python manage.py create_year_partition --year 2027
    python manage.py create_year_partition --year 2027 --dry-run

Tablas gestionadas:
    - core_movimientotarjeta
    - usuarios_auditoriaoperacion

IMPORTANTE: Este comando solo funciona DESPUÉS de haber ejecutado
scripts/setup_partitions.sql para convertir las tablas a particionadas.
Si las tablas aún no están particionadas, el comando avisa y no hace nada.
"""

from django.core.management.base import BaseCommand
from django.db import connection


PARTITIONED_TABLES = [
    {
        "raiz": "core_movimientotarjeta",
        "columna": "fecha",
    },
    {
        "raiz": "usuarios_auditoriaoperacion",
        "columna": "timestamp",
    },
]


def tabla_esta_particionada(cursor, nombre_tabla: str) -> bool:
    cursor.execute("""
        SELECT relkind
        FROM pg_class
        WHERE relname = %s AND relkind = 'p'
    """, [nombre_tabla])
    return cursor.fetchone() is not None


def particion_existe(cursor, nombre_particion: str) -> bool:
    cursor.execute("""
        SELECT 1 FROM pg_class
        WHERE relname = %s AND relkind = 'r'
    """, [nombre_particion])
    return cursor.fetchone() is not None


def crear_particion_anio(cursor, tabla_raiz: str, anio: int, dry_run: bool) -> str:
    nombre = f"{tabla_raiz}_{anio}"
    desde = f"{anio}-01-01 00:00:00+00"
    hasta = f"{anio + 1}-01-01 00:00:00+00"

    sql = (
        f"CREATE TABLE {nombre} "
        f"PARTITION OF {tabla_raiz} "
        f"FOR VALUES FROM ('{desde}') TO ('{hasta}');"
    )

    if dry_run:
        return f"[DRY-RUN] {sql}"

    cursor.execute(sql)
    return f"Creada: {nombre} ({desde} → {hasta})"


class Command(BaseCommand):
    help = "Crea particiones del año indicado para tablas históricas particionadas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--year",
            type=int,
            required=True,
            help="Año a crear (ej: 2027)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Mostrar las sentencias SQL sin ejecutarlas.",
        )

    def handle(self, *args, **options):
        anio = options["year"]
        dry_run = options["dry_run"]

        if anio < 2024 or anio > 2099:
            self.stderr.write(self.style.ERROR(f"Año {anio} fuera de rango válido (2024-2099)."))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING("Modo DRY-RUN — no se realizarán cambios.\n"))

        with connection.cursor() as cursor:
            for tabla in PARTITIONED_TABLES:
                tabla_raiz = tabla["raiz"]
                nombre_particion = f"{tabla_raiz}_{anio}"

                self.stdout.write(f"\n── {tabla_raiz} ──")

                # Verificar que la tabla raíz está particionada
                if not tabla_esta_particionada(cursor, tabla_raiz):
                    self.stdout.write(self.style.WARNING(
                        f"  ⚠ La tabla '{tabla_raiz}' NO está particionada. "
                        f"Ejecutar primero: scripts/setup_partitions.sql"
                    ))
                    continue

                # Verificar si ya existe la partición
                if particion_existe(cursor, nombre_particion):
                    self.stdout.write(self.style.SUCCESS(
                        f"  ✓ Partición '{nombre_particion}' ya existe — sin acción."
                    ))
                    continue

                # Crear la partición
                try:
                    msg = crear_particion_anio(cursor, tabla_raiz, anio, dry_run)
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {msg}"))
                except Exception as exc:
                    self.stderr.write(self.style.ERROR(
                        f"  ✗ Error creando '{nombre_particion}': {exc}"
                    ))

        self.stdout.write(f"\n{'[DRY-RUN] ' if dry_run else ''}Operación completada para año {anio}.\n")
