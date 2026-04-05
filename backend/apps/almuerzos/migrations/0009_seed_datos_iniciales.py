"""
Seed initial tipos_almuerzo, tarifas_comision and alertas_automaticas.

These tables were empty and block core functionality:
  - tipos_almuerzo: can't create almuerzo plans without at least one type
  - tarifas_comision: credit/debit-card commission always 0% without entries
  - alertas_automaticas: Celery alert tasks have no definitions to run against
"""
from django.db import migrations
from django.utils import timezone


# ─── tipos_almuerzo ───────────────────────────────────────────────────────────

def seed_tipos_almuerzo(apps, schema_editor):
    TiposAlmuerzo = apps.get_model('almuerzos', 'TiposAlmuerzo')
    ahora = timezone.now()
    tipos = [
        {
            'nombre': 'Almuerzo Completo',
            'descripcion': 'Plato principal, postre y bebida incluidos',
            'precio_unitario': 15000,
            'incluye_plato_principal': True,
            'incluye_postre': True,
            'incluye_bebida': True,
        },
        {
            'nombre': 'Almuerzo Simple',
            'descripcion': 'Solo plato principal',
            'precio_unitario': 10000,
            'incluye_plato_principal': True,
            'incluye_postre': False,
            'incluye_bebida': False,
        },
        {
            'nombre': 'Media Porción',
            'descripcion': 'Porción reducida, recomendada para niños pequeños',
            'precio_unitario': 7000,
            'incluye_plato_principal': True,
            'incluye_postre': False,
            'incluye_bebida': False,
        },
    ]
    for t in tipos:
        TiposAlmuerzo.objects.get_or_create(
            nombre=t['nombre'],
            defaults={**t, 'fecha_creacion': ahora, 'estado': True},
        )


# ─── tarifas_comision ─────────────────────────────────────────────────────────

def seed_tarifas_comision(apps, schema_editor):
    TarifasComision = apps.get_model('contabilidad', 'TarifasComision')
    MediosPago = apps.get_model('core', 'MediosPago')
    ahora = timezone.now()

    # Tarjeta de Crédito 3 %, Tarjeta de Débito 1.5 %
    tarifas = [
        {'descripcion_medio': 'Tarjeta de Crédito', 'porcentaje': '0.0300'},
        {'descripcion_medio': 'Tarjeta de Débito',  'porcentaje': '0.0150'},
    ]
    for t in tarifas:
        medio = MediosPago.objects.filter(descripcion=t['descripcion_medio']).first()
        if medio and not TarifasComision.objects.filter(id_medio_pago=medio).exists():
            TarifasComision.objects.create(
                fecha_inicio_vigencia=ahora,
                fecha_fin_vigencia=None,
                porcentaje_comision=t['porcentaje'],
                monto_fijo_comision=None,
                estado=True,
                id_medio_pago=medio,
            )


# ─── alertas_automaticas ──────────────────────────────────────────────────────

def seed_alertas_automaticas(apps, schema_editor):
    AlertasAutomaticas = apps.get_model('notificaciones', 'AlertasAutomaticas')
    alertas = [
        {
            'nombre': 'Saldo Bajo de Tarjeta',
            'descripcion': 'Detecta tarjetas cuyo saldo actual cayó por debajo del umbral de alerta configurado por el cliente.',
            'condicion': 'tarjetas.saldo_actual <= tarjetas.saldo_alerta',
            'tipo_alerta': 'saldo_bajo',
            'criticidad': 'ALTA',
            'frecuencia_min': 60,
        },
        {
            'nombre': 'Stock Mínimo de Producto',
            'descripcion': 'Detecta productos cuyo stock en depósito cayó por debajo del mínimo configurado.',
            'condicion': 'stock_unico.cantidad <= productos.stock_minimo',
            'tipo_alerta': 'stock_minimo',
            'criticidad': 'MEDIA',
            'frecuencia_min': 120,
        },
        {
            'nombre': 'Vencimiento de Timbrado',
            'descripcion': 'Alerta cuando el timbrado vigente está próximo a vencer (30, 15 y 5 días antes).',
            'condicion': 'timbrados.fecha_fin <= NOW() + INTERVAL 30 DAY',
            'tipo_alerta': 'vencimiento',
            'criticidad': 'ALTA',
            'frecuencia_min': 1440,  # once a day
        },
        {
            'nombre': 'Producto Próximo a Vencer',
            'descripcion': 'Detecta lotes de inventario cuya fecha de vencimiento está dentro del período de alerta configurado.',
            'condicion': 'lotes_inventario.fecha_vencimiento <= NOW() + INTERVAL dias_alerta DAY',
            'tipo_alerta': 'vencimiento_producto',
            'criticidad': 'MEDIA',
            'frecuencia_min': 720,
        },
    ]
    for a in alertas:
        AlertasAutomaticas.objects.get_or_create(
            nombre=a['nombre'],
            defaults={**a, 'estado': True, 'ultima_verificacion': None},
        )


def reverse_seeds(apps, schema_editor):
    """Remove only the seeded rows (safe to leave existing data alone)."""
    TiposAlmuerzo = apps.get_model('almuerzos', 'TiposAlmuerzo')
    TarifasComision = apps.get_model('contabilidad', 'TarifasComision')
    AlertasAutomaticas = apps.get_model('notificaciones', 'AlertasAutomaticas')

    TiposAlmuerzo.objects.filter(
        nombre__in=['Almuerzo Completo', 'Almuerzo Simple', 'Media Porción']
    ).delete()
    TarifasComision.objects.filter(
        id_medio_pago__descripcion__in=['Tarjeta de Crédito', 'Tarjeta de Débito']
    ).delete()
    AlertasAutomaticas.objects.filter(
        nombre__in=[
            'Saldo Bajo de Tarjeta', 'Stock Mínimo de Producto',
            'Vencimiento de Timbrado', 'Producto Próximo a Vencer',
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('almuerzos', '0008_factura_comprobante_cuenta'),
        ('contabilidad', '0010_alter_documentostributarios_nro_preimpreso_interno_and_more'),
        ('notificaciones', '0002_rename_activo_to_estado'),
    ]

    operations = [
        migrations.RunPython(seed_tipos_almuerzo, migrations.RunPython.noop),
        migrations.RunPython(seed_tarifas_comision, migrations.RunPython.noop),
        migrations.RunPython(seed_alertas_automaticas, migrations.RunPython.noop),
    ]
