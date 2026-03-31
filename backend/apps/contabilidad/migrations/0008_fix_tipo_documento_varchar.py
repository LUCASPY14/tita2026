"""
Migration 0008: convertir tipo_documento de ENUM a VARCHAR(20)

La columna original era ENUM('FISICO','ELECTRONICO') creada fuera de Django.
Ahora la convertimos a VARCHAR(20) para soportar: Factura, NotaCredito,
NotaDebito, Recibo, Factura-Anulada.
Los registros existentes de tipo FISICO o ELECTRONICO se mapean a 'Factura'.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contabilidad", "0007_facturacion_fisica"),
    ]

    operations = [
        # 1. Convertir la columna a VARCHAR(20) y migrar valores existentes
        migrations.RunSQL(
            sql="""
                ALTER TABLE documentos_tributarios
                MODIFY COLUMN tipo_documento VARCHAR(20) NOT NULL DEFAULT 'Factura';

                UPDATE documentos_tributarios
                SET tipo_documento = 'Factura'
                WHERE tipo_documento IN ('FISICO', 'ELECTRONICO', '');
            """,
            reverse_sql="""
                UPDATE documentos_tributarios
                SET tipo_documento = 'FISICO'
                WHERE tipo_documento NOT IN ('FISICO', 'ELECTRONICO');

                ALTER TABLE documentos_tributarios
                MODIFY COLUMN tipo_documento ENUM('FISICO','ELECTRONICO')
                NOT NULL DEFAULT 'FISICO';
            """,
        ),
        # 2. Sincronizar el estado de Django con el nuevo CharField(max_length=20)
        migrations.AlterField(
            model_name="documentostributarios",
            name="tipo_documento",
            field=models.CharField(default="Factura", max_length=20),
        ),
    ]
