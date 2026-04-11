"""
Recreate vista_stock_alerta using `estado` column (was renamed from `activo`
in migration core/0008_rename_activo_to_estado).  The original view still
referenced the old column name, causing MySQL error 1356.
"""
from django.db import migrations

_SQL_FIX = """
CREATE OR ALTER VIEW vista_stock_alerta AS
SELECT
    p.id_producto,
    p.codigo_barra,
    p.descripcion,
    c.nombre          AS categoria,
    s.cantidad        AS stock_actual,
    p.stock_minimo,
    (s.cantidad - p.stock_minimo) AS diferencia,
    CASE
        WHEN s.cantidad <= 0                  THEN 'CRITICO'
        WHEN s.cantidad < p.stock_minimo      THEN 'BAJO'
        ELSE                                       'NORMAL'
    END               AS nivel_alerta,
    s.fecha_ultima_actualizacion,
    u.nombre          AS unidad_medida
FROM productos p
JOIN categorias   c ON p.id_categoria    = c.id_categoria
JOIN stock_unico  s ON p.id_producto     = s.id_producto
LEFT JOIN unidades_medida u ON p.id_unidad_medida = u.id_unidad_medida
WHERE p.estado = 1
"""

_SQL_REVERSE = """
CREATE OR ALTER VIEW vista_stock_alerta AS
SELECT
    p.id_producto, p.codigo_barra, p.descripcion,
    c.nombre AS categoria, s.cantidad AS stock_actual,
    p.stock_minimo, (s.cantidad - p.stock_minimo) AS diferencia,
    CASE
        WHEN s.cantidad <= 0             THEN 'CRITICO'
        WHEN s.cantidad < p.stock_minimo THEN 'BAJO'
        ELSE                                  'NORMAL'
    END AS nivel_alerta,
    s.fecha_ultima_actualizacion,
    u.nombre AS unidad_medida
FROM productos p
JOIN categorias  c ON p.id_categoria    = c.id_categoria
JOIN stock_unico s ON p.id_producto     = s.id_producto
LEFT JOIN unidades_medida u ON p.id_unidad_medida = u.id_unidad_medida
WHERE p.activo = 1
"""


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0004_lotesproducto_alertasvencimiento_and_more'),
        ('core', '0008_rename_activo_to_estado'),
        ('productos', '0005_rename_activo_to_estado'),
    ]

    operations = [
        migrations.RunSQL(sql=_SQL_FIX, reverse_sql=_SQL_REVERSE),
    ]
