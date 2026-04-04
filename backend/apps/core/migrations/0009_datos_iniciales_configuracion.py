"""
Migration 0008: datos iniciales de ConfiguracionSistema.

Pobla la tabla con las configuraciones operativas más comunes de la cantina.
Los valores son ejemplos — el admin puede editarlos desde /configuracion.
"""
from django.db import migrations
from django.utils import timezone


CONFIGURACIONES = [
    # ── Empresa ──────────────────────────────────────────────────────────────
    {
        "clave": "EMPRESA_NOMBRE",
        "valor": "Cantina Educativa",
        "tipo": "texto",
        "categoria": "Empresa",
        "descripcion": "Nombre o razón social de la institución",
        "valor_defecto": "Cantina Educativa",
        "requerido": True,
        "validacion": "",
        "valores_permitidos": None,
        "valor_min": "",
        "valor_max": "",
        "requiere_reinicio": False,
        "solo_superuser": False,
    },
    {
        "clave": "EMPRESA_RUC",
        "valor": "80000000-0",
        "tipo": "texto",
        "categoria": "Empresa",
        "descripcion": "RUC de la institución emisora de facturas",
        "valor_defecto": "",
        "requerido": True,
        "validacion": "",
        "valores_permitidos": None,
        "valor_min": "",
        "valor_max": "",
        "requiere_reinicio": False,
        "solo_superuser": True,
    },
    {
        "clave": "EMPRESA_DIRECCION",
        "valor": "Asunción, Paraguay",
        "tipo": "texto",
        "categoria": "Empresa",
        "descripcion": "Dirección física de la empresa",
        "valor_defecto": "",
        "requerido": False,
        "validacion": "",
        "valores_permitidos": None,
        "valor_min": "",
        "valor_max": "",
        "requiere_reinicio": False,
        "solo_superuser": False,
    },
    {
        "clave": "EMPRESA_TELEFONO",
        "valor": "+595 21 000000",
        "tipo": "texto",
        "categoria": "Empresa",
        "descripcion": "Teléfono de contacto",
        "valor_defecto": "",
        "requerido": False,
        "validacion": "",
        "valores_permitidos": None,
        "valor_min": "",
        "valor_max": "",
        "requiere_reinicio": False,
        "solo_superuser": False,
    },
    # ── Almuerzos ─────────────────────────────────────────────────────────────
    {
        "clave": "ALMUERZO_PRECIO_DEFAULT",
        "valor": "25000",
        "tipo": "entero",
        "categoria": "Almuerzos",
        "descripcion": "Precio por defecto del almuerzo mensual (Gs.)",
        "valor_defecto": "25000",
        "requerido": True,
        "validacion": "min:1000,max:500000",
        "valores_permitidos": None,
        "valor_min": "1000",
        "valor_max": "500000",
        "requiere_reinicio": False,
        "solo_superuser": False,
    },
    {
        "clave": "ALMUERZO_DIAS_VENCIMIENTO",
        "valor": "10",
        "tipo": "entero",
        "categoria": "Almuerzos",
        "descripcion": "Días del mes para pagar antes del vencimiento",
        "valor_defecto": "10",
        "requerido": True,
        "validacion": "min:1,max:28",
        "valores_permitidos": None,
        "valor_min": "1",
        "valor_max": "28",
        "requiere_reinicio": False,
        "solo_superuser": False,
    },
    # ── Tarjetas / Saldo ──────────────────────────────────────────────────────
    {
        "clave": "TARJETA_SALDO_MAXIMO",
        "valor": "500000",
        "tipo": "entero",
        "categoria": "Tarjetas",
        "descripcion": "Saldo máximo permitido por tarjeta (Gs.)",
        "valor_defecto": "500000",
        "requerido": True,
        "validacion": "min:10000,max:5000000",
        "valores_permitidos": None,
        "valor_min": "10000",
        "valor_max": "5000000",
        "requiere_reinicio": False,
        "solo_superuser": False,
    },
    {
        "clave": "TARJETA_SALDO_MINIMO_ALERTA",
        "valor": "5000",
        "tipo": "entero",
        "categoria": "Tarjetas",
        "descripcion": "Saldo mínimo para mostrar alerta de recarga (Gs.)",
        "valor_defecto": "5000",
        "requerido": True,
        "validacion": "min:0,max:100000",
        "valores_permitidos": None,
        "valor_min": "0",
        "valor_max": "100000",
        "requiere_reinicio": False,
        "solo_superuser": False,
    },
    {
        "clave": "RECARGA_MONTO_MINIMO",
        "valor": "10000",
        "tipo": "entero",
        "categoria": "Tarjetas",
        "descripcion": "Monto mínimo de recarga (Gs.)",
        "valor_defecto": "10000",
        "requerido": True,
        "validacion": "min:1000,max:100000",
        "valores_permitidos": None,
        "valor_min": "1000",
        "valor_max": "100000",
        "requiere_reinicio": False,
        "solo_superuser": False,
    },
    {
        "clave": "RECARGA_MONTO_MAXIMO",
        "valor": "500000",
        "tipo": "entero",
        "categoria": "Tarjetas",
        "descripcion": "Monto máximo de recarga por operación (Gs.)",
        "valor_defecto": "500000",
        "requerido": True,
        "validacion": "min:10000,max:2000000",
        "valores_permitidos": None,
        "valor_min": "10000",
        "valor_max": "2000000",
        "requiere_reinicio": False,
        "solo_superuser": False,
    },
    # ── POS / Ventas ──────────────────────────────────────────────────────────
    {
        "clave": "POS_PERMITE_FIADO",
        "valor": "false",
        "tipo": "booleano",
        "categoria": "Ventas",
        "descripcion": "Permitir ventas al fiado (sin saldo suficiente)",
        "valor_defecto": "false",
        "requerido": True,
        "validacion": "",
        "valores_permitidos": ["true", "false"],
        "valor_min": "",
        "valor_max": "",
        "requiere_reinicio": False,
        "solo_superuser": False,
    },
    {
        "clave": "POS_DESCUENTO_MAXIMO",
        "valor": "20",
        "tipo": "entero",
        "categoria": "Ventas",
        "descripcion": "Porcentaje máximo de descuento aplicable en POS (%)",
        "valor_defecto": "20",
        "requerido": True,
        "validacion": "min:0,max:100",
        "valores_permitidos": None,
        "valor_min": "0",
        "valor_max": "100",
        "requiere_reinicio": False,
        "solo_superuser": False,
    },
    # ── Notificaciones ────────────────────────────────────────────────────────
    {
        "clave": "NOTIF_SALDO_BAJO_ACTIVO",
        "valor": "true",
        "tipo": "booleano",
        "categoria": "Notificaciones",
        "descripcion": "Enviar notificación cuando el saldo de la tarjeta esté bajo",
        "valor_defecto": "true",
        "requerido": True,
        "validacion": "",
        "valores_permitidos": ["true", "false"],
        "valor_min": "",
        "valor_max": "",
        "requiere_reinicio": False,
        "solo_superuser": False,
    },
]


def crear_configuraciones(apps, schema_editor):
    ConfiguracionSistema = apps.get_model("core", "ConfiguracionSistema")
    now = timezone.now()
    for cfg in CONFIGURACIONES:
        ConfiguracionSistema.objects.get_or_create(
            clave=cfg["clave"],
            defaults={
                **cfg,
                "valores_permitidos": cfg["valores_permitidos"] if cfg["valores_permitidos"] is not None else [],
                "estado": True,
                "updated_at": now,
                "updated_by": None,
            },
        )


def eliminar_configuraciones(apps, schema_editor):
    ConfiguracionSistema = apps.get_model("core", "ConfiguracionSistema")
    claves = [c["clave"] for c in CONFIGURACIONES]
    ConfiguracionSistema.objects.filter(clave__in=claves).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_rename_activo_to_estado"),
    ]

    operations = [
        migrations.RunPython(crear_configuraciones, eliminar_configuraciones),
    ]
