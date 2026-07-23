from django.core.checks import Warning, register, Tags
from django.db import OperationalError, ProgrammingError


@register(Tags.database)
def check_partitioned_tables(app_configs, **kwargs):
    """
    Verifica que las tablas de alto volumen estén particionadas por año.
    Las tablas requieren ejecutar scripts/setup_partitions.sql después del primer migrate.
    """
    from django.db import connection

    errors = []
    expected = {
        "core_movimientotarjeta": "core.W001",
        "usuarios_auditoriaoperacion": "core.W002",
    }
    try:
        with connection.cursor() as cursor:
            for table, code in expected.items():
                cursor.execute(
                    "SELECT relkind FROM pg_class WHERE relname = %s", [table]
                )
                row = cursor.fetchone()
                if row and row[0] != "p":
                    errors.append(
                        Warning(
                            f"La tabla '{table}' existe pero NO está particionada por año. "
                            "Los insertos fuera del rango de partición activa fallarán.",
                            hint=(
                                "Ejecutar scripts/setup_partitions.sql en la DB y luego "
                                "python manage.py create_year_partition."
                            ),
                            id=code,
                        )
                    )
    except (OperationalError, ProgrammingError):
        pass
    return errors
