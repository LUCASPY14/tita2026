"""
Comando de limpieza para mantenimiento del sistema de usuarios
Debe ejecutarse periódicamente vía cron job
"""

from django.core.management.base import BaseCommand

from apps.usuarios.services import PasswordRecoveryService, SessionService


class Command(BaseCommand):
    help = "Limpia datos expirados del sistema de usuarios (sesiones, tokens, etc.)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mostrar qué se limpiaría sin hacer cambios reales",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Mostrar información detallada",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        verbose = options["verbose"]

        if dry_run:
            self.stdout.write(self.style.WARNING("=== MODO DRY RUN - No se harán cambios reales ===\n"))

        self.stdout.write(self.style.MIGRATE_HEADING("=== Ejecutando Limpieza del Sistema de Usuarios ===\n"))

        total_limpiados = 0
        errores = []

        # 1. Limpiar sesiones expiradas e inactivas
        self.stdout.write("1. Limpiando sesiones expiradas...")
        try:
            if not dry_run:
                resultado_sesiones = SessionService.limpiar_sesiones_expiradas()
                if resultado_sesiones["success"]:
                    sesiones_cerradas = resultado_sesiones["sesiones_cerradas"]
                    total_limpiados += sesiones_cerradas
                    self.stdout.write(self.style.SUCCESS(f"   ✓ {sesiones_cerradas} sesiones cerradas"))

                    if verbose and sesiones_cerradas > 0:
                        self.stdout.write(f"     - Sesiones expiradas (>24h): cerradas")
                        self.stdout.write(f"     - Sesiones inactivas (>30min): cerradas\n")
                else:
                    errores.append(f'Sesiones: {resultado_sesiones["mensaje"]}')
                    self.stdout.write(self.style.ERROR(f'   ✗ Error: {resultado_sesiones["mensaje"]}'))
            else:
                # En dry-run, consultar cuántas se limpiarían
                from datetime import timedelta

                from django.utils import timezone

                from apps.usuarios.models import SesionesActivas

                ahora = timezone.now()
                expiradas = SesionesActivas.objects.filter(
                    activa=True, fecha_inicio__lt=ahora - timedelta(hours=24)
                ).count()

                inactivas = SesionesActivas.objects.filter(
                    activa=True, ultima_actividad__lt=ahora - timedelta(minutes=30)
                ).count()

                total_a_cerrar = expiradas + inactivas
                self.stdout.write(
                    self.style.WARNING(
                        f"   → Se cerrarían {total_a_cerrar} sesiones ({expiradas} expiradas, {inactivas} inactivas)\n"
                    )
                )

        except Exception as e:
            errores.append(f"Sesiones: {str(e)}")
            self.stdout.write(self.style.ERROR(f"   ✗ Error inesperado: {str(e)}\n"))

        # 2. Limpiar tokens de recuperación expirados
        self.stdout.write("2. Limpiando tokens de recuperación...")
        try:
            if not dry_run:
                resultado_tokens = PasswordRecoveryService.limpiar_tokens_expirados()
                if resultado_tokens["success"]:
                    tokens_eliminados = resultado_tokens["tokens_eliminados"]
                    total_limpiados += tokens_eliminados
                    self.stdout.write(self.style.SUCCESS(f"   ✓ {tokens_eliminados} tokens eliminados"))

                    if verbose and tokens_eliminados > 0:
                        self.stdout.write(f"     - Tokens de password recovery: eliminados")
                        self.stdout.write(f"     - Tokens de email verification: eliminados")
                        self.stdout.write(f"     - Criterio: expirados hace >7 días\n")
                else:
                    errores.append(f'Tokens: {resultado_tokens["mensaje"]}')
                    self.stdout.write(self.style.ERROR(f'   ✗ Error: {resultado_tokens["mensaje"]}'))
            else:
                # En dry-run, consultar cuántos se eliminarían
                from datetime import timedelta

                from django.utils import timezone

                from apps.usuarios.models import TokensRecuperacion

                ahora = timezone.now()
                tokens_a_eliminar = TokensRecuperacion.objects.filter(
                    fecha_expiracion__lt=ahora - timedelta(days=7)
                ).count()

                self.stdout.write(self.style.WARNING(f"   → Se eliminarían {tokens_a_eliminar} tokens\n"))

        except Exception as e:
            errores.append(f"Tokens: {str(e)}")
            self.stdout.write(self.style.ERROR(f"   ✗ Error inesperado: {str(e)}\n"))

        # 3. Limpiar intentos de login antiguos (opcional)
        self.stdout.write("3. Limpiando intentos de login antiguos...")
        try:
            if not dry_run:
                from datetime import timedelta

                from django.utils import timezone

                from apps.usuarios.models import IntentosLogin

                # Eliminar intentos de más de 30 días
                ahora = timezone.now()
                intentos_antiguos = IntentosLogin.objects.filter(fecha_intento__lt=ahora - timedelta(days=30))

                cantidad = intentos_antiguos.count()
                intentos_antiguos.delete()

                total_limpiados += cantidad
                self.stdout.write(self.style.SUCCESS(f"   ✓ {cantidad} intentos de login eliminados"))

                if verbose and cantidad > 0:
                    self.stdout.write(f"     - Criterio: >30 días de antigüedad\n")
            else:
                from datetime import timedelta

                from django.utils import timezone

                from apps.usuarios.models import IntentosLogin

                ahora = timezone.now()
                cantidad = IntentosLogin.objects.filter(fecha_intento__lt=ahora - timedelta(days=30)).count()

                self.stdout.write(self.style.WARNING(f"   → Se eliminarían {cantidad} intentos de login\n"))

        except Exception as e:
            errores.append(f"Intentos login: {str(e)}")
            self.stdout.write(self.style.ERROR(f"   ✗ Error inesperado: {str(e)}\n"))

        # 4. Limpiar intentos 2FA antiguos (opcional)
        self.stdout.write("4. Limpiando intentos 2FA antiguos...")
        try:
            if not dry_run:
                from datetime import timedelta

                from django.utils import timezone

                from apps.usuarios.models import Intentos2Fa

                # Eliminar intentos de más de 30 días
                ahora = timezone.now()
                intentos_2fa_antiguos = Intentos2Fa.objects.filter(fecha_intento__lt=ahora - timedelta(days=30))

                cantidad = intentos_2fa_antiguos.count()
                intentos_2fa_antiguos.delete()

                total_limpiados += cantidad
                self.stdout.write(self.style.SUCCESS(f"   ✓ {cantidad} intentos 2FA eliminados\n"))

                if verbose and cantidad > 0:
                    self.stdout.write(f"     - Criterio: >30 días de antigüedad\n")
            else:
                from datetime import timedelta

                from django.utils import timezone

                from apps.usuarios.models import Intentos2Fa

                ahora = timezone.now()
                cantidad = Intentos2Fa.objects.filter(fecha_intento__lt=ahora - timedelta(days=30)).count()

                self.stdout.write(self.style.WARNING(f"   → Se eliminarían {cantidad} intentos 2FA\n"))

        except Exception as e:
            errores.append(f"Intentos 2FA: {str(e)}")
            self.stdout.write(self.style.ERROR(f"   ✗ Error inesperado: {str(e)}\n"))

        # Resumen final
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Resumen de Limpieza ===\n"))

        if dry_run:
            self.stdout.write(self.style.WARNING("Modo dry-run: No se realizaron cambios reales\n"))
        else:
            if errores:
                self.stdout.write(self.style.WARNING(f"Total de elementos limpiados: {total_limpiados}"))
                self.stdout.write(self.style.ERROR(f"Errores encontrados: {len(errores)}\n"))
                for error in errores:
                    self.stdout.write(self.style.ERROR(f"  - {error}"))
                self.stdout.write("")
            else:
                self.stdout.write(self.style.SUCCESS(f"✅ Limpieza completada exitosamente"))
                self.stdout.write(self.style.SUCCESS(f"   Total de elementos limpiados: {total_limpiados}\n"))

        # Recomendaciones
        if not dry_run and total_limpiados > 0:
            self.stdout.write(self.style.MIGRATE_HEADING("=== Recomendaciones ===\n"))
            self.stdout.write("• Configure este comando en cron para ejecución automática:")
            self.stdout.write("  0 2 * * * cd /ruta/proyecto && python manage.py cleanup_usuarios")
            self.stdout.write("")
            self.stdout.write("• Frecuencia recomendada: Diariamente a las 2:00 AM")
            self.stdout.write("")
            self.stdout.write("• Para pruebas:")
            self.stdout.write("  python manage.py cleanup_usuarios --dry-run --verbose")
            self.stdout.write("")
