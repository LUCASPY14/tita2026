"""Tests para apps.usuarios.tasks — limpiar_audit_logs."""
import pytest
from datetime import timedelta
from django.utils import timezone


# ── limpiar_audit_logs ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLimpiarAuditLogs:

    def test_sin_registros_retorna_ceros(self, db):
        from apps.usuarios.tasks import limpiar_audit_logs
        result = limpiar_audit_logs()
        assert result == {
            "auditoria_operaciones": 0,
            "intentos_login": 0,
            "intentos_2fa": 0,
        }

    def test_auditoria_vieja_se_elimina(self, db, usuario_admin):
        from apps.usuarios.models import AuditoriaOperacion
        from apps.usuarios.tasks import limpiar_audit_logs
        op = AuditoriaOperacion.objects.create(
            usuario=usuario_admin,
            operacion="TEST",
            resultado="EXITO",
        )
        AuditoriaOperacion.objects.filter(pk=op.pk).update(
            fecha_operacion=timezone.now() - timedelta(days=366)
        )
        result = limpiar_audit_logs()
        assert result["auditoria_operaciones"] >= 1
        assert not AuditoriaOperacion.objects.filter(pk=op.pk).exists()

    def test_auditoria_reciente_no_se_elimina(self, db, usuario_admin):
        from apps.usuarios.models import AuditoriaOperacion
        from apps.usuarios.tasks import limpiar_audit_logs
        op = AuditoriaOperacion.objects.create(
            usuario=usuario_admin,
            operacion="RECIENTE",
            resultado="EXITO",
        )
        result = limpiar_audit_logs()
        assert result["auditoria_operaciones"] == 0
        assert AuditoriaOperacion.objects.filter(pk=op.pk).exists()

    def test_intento_login_viejo_se_elimina(self, db):
        from apps.usuarios.models import IntentoLogin
        from apps.usuarios.tasks import limpiar_audit_logs
        intento = IntentoLogin.objects.create(
            email="test@old.com",
            ip_address="127.0.0.1",
            exitoso=False,
        )
        IntentoLogin.objects.filter(pk=intento.pk).update(
            fecha_intento=timezone.now() - timedelta(days=91)
        )
        result = limpiar_audit_logs()
        assert result["intentos_login"] >= 1
        assert not IntentoLogin.objects.filter(pk=intento.pk).exists()

    def test_intento_login_reciente_no_se_elimina(self, db):
        from apps.usuarios.models import IntentoLogin
        from apps.usuarios.tasks import limpiar_audit_logs
        IntentoLogin.objects.create(
            email="test@reciente.com",
            ip_address="127.0.0.1",
            exitoso=True,
        )
        result = limpiar_audit_logs()
        assert result["intentos_login"] == 0

    def test_multiples_modelos_en_una_ejecucion(self, db, usuario_admin):
        from apps.usuarios.models import AuditoriaOperacion, IntentoLogin
        from apps.usuarios.tasks import limpiar_audit_logs
        op = AuditoriaOperacion.objects.create(usuario=usuario_admin, operacion="MULTI")
        AuditoriaOperacion.objects.filter(pk=op.pk).update(
            fecha_operacion=timezone.now() - timedelta(days=400)
        )
        intento = IntentoLogin.objects.create(email="multi@old.com", ip_address="10.0.0.1", exitoso=False)
        IntentoLogin.objects.filter(pk=intento.pk).update(
            fecha_intento=timezone.now() - timedelta(days=100)
        )
        result = limpiar_audit_logs()
        assert result["auditoria_operaciones"] >= 1
        assert result["intentos_login"] >= 1
