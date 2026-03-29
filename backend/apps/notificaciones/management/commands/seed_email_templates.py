"""
Management command: seed_email_templates
Crea las plantillas de email transaccionales en la tabla plantillas_email.
Ejecutar una vez en cada entorno (dev, staging, producción).

Uso:
    python manage.py seed_email_templates
    python manage.py seed_email_templates --reset   # borra y recrea todas
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

TEMPLATES = [
    {
        'codigo': 'confirmacion_recarga',
        'nombre': 'Confirmación de Recarga',
        'descripcion': 'Email enviado al apoderado tras una recarga exitosa de saldo.',
        'asunto': '✅ Recarga Exitosa — Tarjeta {nro_tarjeta}',
        'cuerpo_html': """<p>Estimado/a <strong>{nombre_destinatario}</strong>,</p>
<p>Su recarga se procesó exitosamente:</p>
<ul>
  <li><strong>Estudiante:</strong> {nombre_hijo}</li>
  <li><strong>Tarjeta:</strong> {nro_tarjeta}</li>
  <li><strong>Monto acreditado:</strong> ₲{monto_acreditado}</li>
  <li><strong>Nuevo saldo:</strong> ₲{saldo_nuevo}</li>
  <li><strong>Método de pago:</strong> {metodo_pago}</li>
  <li><strong>Fecha:</strong> {fecha_recarga}</li>
</ul>""",
        'cuerpo_texto': (
            "RECARGA EXITOSA\n\n"
            "Estudiante: {nombre_hijo}\n"
            "Tarjeta: {nro_tarjeta}\n"
            "Monto acreditado: ₲{monto_acreditado}\n"
            "Nuevo saldo: ₲{saldo_nuevo}\n"
            "Método: {metodo_pago}\n"
            "Fecha: {fecha_recarga}"
        ),
        'variables': ['nombre_destinatario', 'nombre_hijo', 'nro_tarjeta',
                      'monto_acreditado', 'saldo_nuevo', 'metodo_pago', 'fecha_recarga'],
        'categoria': 'transaccional',
    },
    {
        'codigo': 'alerta_saldo_bajo',
        'nombre': 'Alerta de Saldo Bajo',
        'descripcion': 'Email enviado cuando el saldo de una tarjeta cae por debajo del límite configurado.',
        'asunto': '⚠️ Alerta de Saldo Bajo — Tarjeta {nro_tarjeta}',
        'cuerpo_html': """<p>Estimado/a <strong>{nombre_destinatario}</strong>,</p>
<p>El saldo de la tarjeta está por debajo del límite configurado:</p>
<ul>
  <li><strong>Estudiante:</strong> {nombre_hijo}</li>
  <li><strong>Tarjeta:</strong> {nro_tarjeta}</li>
  <li><strong>Saldo actual:</strong> ₲{saldo_actual}</li>
  <li><strong>Límite de alerta:</strong> ₲{saldo_alerta}</li>
</ul>
<p>Recomendamos realizar una recarga.</p>""",
        'cuerpo_texto': (
            "ALERTA DE SALDO BAJO\n\n"
            "Estudiante: {nombre_hijo}\n"
            "Tarjeta: {nro_tarjeta}\n"
            "Saldo actual: ₲{saldo_actual}\n"
            "Límite de alerta: ₲{saldo_alerta}"
        ),
        'variables': ['nombre_destinatario', 'nombre_hijo', 'nro_tarjeta',
                      'saldo_actual', 'saldo_alerta'],
        'categoria': 'alertas',
    },
    {
        'codigo': 'resumen_mensual_almuerzos',
        'nombre': 'Resumen Mensual de Almuerzos',
        'descripcion': 'Resumen mensual de la cuenta de almuerzos enviado al apoderado.',
        'asunto': '🍽️ Resumen de Almuerzos {nombre_mes} {anio} — {nombre_hijo}',
        'cuerpo_html': """<p>Estimado/a <strong>{nombre_destinatario}</strong>,</p>
<p>Resumen de la cuenta de almuerzos de <strong>{nombre_hijo}</strong> — {nombre_mes} {anio}:</p>
<table>
  <tr><td>Total del mes</td><td>₲{monto_total}</td></tr>
  <tr><td>Pagado</td><td>₲{monto_pagado}</td></tr>
  <tr><td><strong>Saldo pendiente</strong></td><td><strong>₲{saldo_pendiente}</strong></td></tr>
  <tr><td>Estado</td><td>{estado}</td></tr>
</table>""",
        'cuerpo_texto': (
            "RESUMEN MENSUAL DE ALMUERZOS\n\n"
            "Estudiante: {nombre_hijo}\n"
            "Período: {nombre_mes} {anio}\n"
            "Total: ₲{monto_total}\n"
            "Pagado: ₲{monto_pagado}\n"
            "Saldo: ₲{saldo_pendiente}\n"
            "Estado: {estado}"
        ),
        'variables': ['nombre_destinatario', 'nombre_hijo', 'nombre_mes', 'anio',
                      'monto_total', 'monto_pagado', 'saldo_pendiente', 'estado'],
        'categoria': 'transaccional',
    },
    {
        'codigo': 'bienvenida_portal',
        'nombre': 'Bienvenida al Portal',
        'descripcion': 'Email de bienvenida enviado al apoderado cuando activa su cuenta en el portal.',
        'asunto': '👋 Bienvenido/a al Portal de Cantina Tita',
        'cuerpo_html': """<p>Estimado/a <strong>{nombre_destinatario}</strong>,</p>
<p>Su cuenta en el portal de Cantina Tita ha sido activada exitosamente.</p>
<p>Desde el portal podrá:</p>
<ul>
  <li>Consultar el saldo de las tarjetas de sus hijos</li>
  <li>Realizar recargas en línea</li>
  <li>Ver el historial de consumos</li>
  <li>Configurar alertas de saldo bajo</li>
</ul>
<p><strong>Usuario:</strong> {email_usuario}</p>""",
        'cuerpo_texto': (
            "BIENVENIDO/A AL PORTAL DE CANTINA TITA\n\n"
            "Estimado/a {nombre_destinatario},\n\n"
            "Su cuenta ha sido activada. Usuario: {email_usuario}\n\n"
            "Desde el portal puede consultar saldos, hacer recargas y ver consumos."
        ),
        'variables': ['nombre_destinatario', 'email_usuario'],
        'categoria': 'transaccional',
    },
]


class Command(BaseCommand):
    help = 'Crea las plantillas de email transaccionales en la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Borra y recrea todas las plantillas',
        )

    def handle(self, *args, **options):
        from apps.notificaciones.models import PlantillasEmail

        if options['reset']:
            deleted = PlantillasEmail.objects.filter(
                codigo__in=[t['codigo'] for t in TEMPLATES]
            ).delete()
            self.stdout.write(f'  Eliminadas {deleted[0]} plantillas existentes.')

        now = timezone.now()
        creadas = 0
        actualizadas = 0
        omitidas = 0

        for tmpl in TEMPLATES:
            obj, created = PlantillasEmail.objects.update_or_create(
                codigo=tmpl['codigo'],
                defaults={
                    'nombre': tmpl['nombre'],
                    'descripcion': tmpl['descripcion'],
                    'asunto': tmpl['asunto'],
                    'cuerpo_html': tmpl['cuerpo_html'],
                    'cuerpo_texto': tmpl['cuerpo_texto'],
                    'variables': tmpl['variables'],
                    'categoria': tmpl['categoria'],
                    'estado': True,
                    'created_at': now,
                    'updated_at': now,
                },
            )
            if created:
                self.stdout.write(f'  + Creada:       {tmpl["codigo"]}')
                creadas += 1
            else:
                self.stdout.write(f'  ~ Actualizada:  {tmpl["codigo"]}')
                actualizadas += 1

        self.stdout.write(
            f'\nListo. Creadas: {creadas}  Actualizadas: {actualizadas}  '
            f'Omitidas: {omitidas}\n'
            f'Total en DB: {PlantillasEmail.objects.count()} plantilla(s) de email.'
        )
