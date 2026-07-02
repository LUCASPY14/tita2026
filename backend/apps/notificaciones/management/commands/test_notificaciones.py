"""
Management command para probar los canales de notificación configurados.

Uso:
    python manage.py test_notificaciones --email destino@gmail.com
    python manage.py test_notificaciones --whatsapp 595981234567
    python manage.py test_notificaciones --email destino@gmail.com --whatsapp 595981234567
"""

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Envía mensajes de prueba por email y/o WhatsApp para verificar la configuración."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            metavar="DIRECCION",
            help="Destinatario del email de prueba (ej. tu@gmail.com)",
        )
        parser.add_argument(
            "--whatsapp",
            metavar="NUMERO",
            help="Número de WhatsApp destino en formato internacional (ej. 595981234567)",
        )

    def handle(self, *args, **options):
        email = options.get("email")
        whatsapp = options.get("whatsapp")

        if not email and not whatsapp:
            raise CommandError(
                "Especificá al menos un canal: --email <dir> y/o --whatsapp <número>"
            )

        if email:
            self._test_email(email)

        if whatsapp:
            self._test_whatsapp(whatsapp)

    def _test_email(self, destinatario):
        from django.conf import settings
        from django.core.mail import send_mail

        self.stdout.write(f"Enviando email de prueba a {destinatario}...")
        self.stdout.write(
            f"  Backend : {getattr(settings, 'EMAIL_BACKEND', '?')}"
        )
        self.stdout.write(
            f"  Host    : {getattr(settings, 'EMAIL_HOST', '?')}:{getattr(settings, 'EMAIL_PORT', '?')}"
        )
        self.stdout.write(
            f"  Usuario : {getattr(settings, 'EMAIL_HOST_USER', '?')}"
        )

        try:
            send_mail(
                subject="[Cantina Tita] Prueba de email",
                message=(
                    "Este es un email de prueba enviado desde el sistema de Cantina Tita.\n\n"
                    "Si recibís este mensaje, la configuración de Gmail SMTP está correcta.\n\n"
                    "-- Cantina Tita Dev"
                ),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", ""),
                recipient_list=[destinatario],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS("  OK Email enviado correctamente."))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"  ERROR Error al enviar email: {exc}"))
            self._hint_email(exc)

    def _test_whatsapp(self, numero):
        from apps.notificaciones.services import enviar_whatsapp

        self.stdout.write(f"Enviando WhatsApp de prueba a {numero}...")

        try:
            resultado = enviar_whatsapp(
                numero=numero,
                mensaje=(
                    "*Cantina Tita* — Mensaje de prueba\n\n"
                    "Si recibes este mensaje, la integracion con WAHA esta funcionando correctamente."
                ),
            )
            self.stdout.write(self.style.SUCCESS(f"  OK WhatsApp enviado. Respuesta: {resultado}"))
        except RuntimeError as exc:
            self.stdout.write(self.style.ERROR(f"  ERROR Evolution API no configurada: {exc}"))
            self._hint_whatsapp()
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"  ERROR Error al enviar WhatsApp: {exc}"))
            self._hint_whatsapp()

    def _hint_email(self, exc):
        msg = str(exc).lower()
        if "authentication" in msg or "username" in msg or "password" in msg:
            self.stdout.write(
                self.style.WARNING(
                    "\n  Posible causa: App Password incorrecta o la cuenta no tiene 2FA activado.\n"
                    "  Pasos:\n"
                    "    1. myaccount.google.com → Seguridad → Verificación en 2 pasos → ACTIVAR\n"
                    "    2. Mismo menú → Contraseñas de aplicaciones → Nombre: 'Cantina Tita' → Generar\n"
                    "    3. Copiar las 16 letras (sin espacios) en EMAIL_HOST_PASSWORD del .env\n"
                    "    4. Reiniciar el backend (python manage.py runserver)\n"
                )
            )
        elif "connection" in msg or "refused" in msg:
            self.stdout.write(
                self.style.WARNING(
                    "\n  Posible causa: no hay conexión a smtp.gmail.com:587.\n"
                    "  Verificá que el firewall/antivirus no bloquee el puerto 587.\n"
                )
            )

    def _hint_whatsapp(self):
        self.stdout.write(
            self.style.WARNING(
                "\n  Para iniciar Evolution API:\n"
                "    docker run -d --name evolution-api -p 8080:8080 \\\n"
                "      -e AUTHENTICATION_API_KEY=cantina123 \\\n"
                "      atendai/evolution-api:latest\n\n"
                "  Luego crear la instancia y conectar WhatsApp:\n"
                "    POST http://localhost:8080/instance/create\n"
                "    Headers: apikey: cantina123\n"
                "    Body: {\"instanceName\": \"tita-dev\", \"qrcode\": true}\n\n"
                "  Escaneá el QR con tu WhatsApp personal (menú ⋮ → Dispositivos vinculados)\n"
                "  Después de escanear, volver a correr este comando.\n"
            )
        )
