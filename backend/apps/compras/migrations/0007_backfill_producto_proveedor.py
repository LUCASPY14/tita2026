"""
Backfill ProductoProveedor from existing DetalleCompra records.
Takes the most recent cost per (proveedor, producto) pair.
"""

from django.db import migrations


def backfill(apps, schema_editor):
    DetalleCompra = apps.get_model("compras", "DetalleCompra")
    ProductoProveedor = apps.get_model("compras", "ProductoProveedor")

    # Iterate oldest→newest so the last write per key is the most recent price
    seen = {}
    qs = (
        DetalleCompra.objects
        .select_related("compra")
        .order_by("compra__fecha", "id")
        .values("compra__proveedor_id", "producto_id", "costo_unitario", "compra__fecha")
    )
    for row in qs:
        key = (row["compra__proveedor_id"], row["producto_id"])
        seen[key] = {
            "precio_compra": row["costo_unitario"],
            "fecha_ultima_compra": row["compra__fecha"],
        }

    for (proveedor_id, producto_id), defaults in seen.items():
        ProductoProveedor.objects.get_or_create(
            proveedor_id=proveedor_id,
            producto_id=producto_id,
            defaults=defaults,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("compras", "0006_add_producto_proveedor"),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
