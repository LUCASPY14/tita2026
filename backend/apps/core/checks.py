from django.conf import settings
from django.core.checks import Error, Warning, register, Tags
from django.db import OperationalError, ProgrammingError


@register(Tags.database)
def check_partitioned_tables(app_configs, **kwargs):
    """
    Verifica que las tablas de alto volumen estén particionadas por año.
    Las tablas requieren ejecutar scripts/setup_partitions.sql después del primer migrate.

    En producción (DEBUG=False) emite Error para impedir el arranque.
    En desarrollo (DEBUG=True) emite Warning para no bloquear el entorno local.
    """
    from django.db import connection

    errors = []
    # (warn_code, err_code) — W en dev, E en prod
    expected = {
        "core_movimientotarjeta":      ("core.W001", "core.E001"),
        "auditoria_operaciones":       ("core.W002", "core.E002"),
    }
    try:
        with connection.cursor() as cursor:
            for table, (warn_code, err_code) in expected.items():
                cursor.execute(
                    "SELECT relkind FROM pg_class WHERE relname = %s", [table]
                )
                row = cursor.fetchone()
                if row and row[0] != "p":
                    is_prod = not settings.DEBUG
                    cls = Error if is_prod else Warning
                    code = err_code if is_prod else warn_code
                    errors.append(
                        cls(
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
