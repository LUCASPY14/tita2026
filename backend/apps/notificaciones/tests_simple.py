"""
Tests simples para la app notificaciones
Verifican estructura básica sin dependencias complejas de BD
"""
import pytest
from django.test import TestCase
from apps.notificaciones.models import (
    NotificacionesPortal,
    NotificacionesSaldo,
    AlertasSistema,
    PreferenciasNotificacion,
    EmailsEnviados,
    SmsEnviados
)


class TestModelosExisten(TestCase):
    """Verifica que los modelos estén correctamente definidos"""
    
    def test_notificaciones_portal_existe(self):
        """Test: NotificacionesPortal modelo existe"""
        self.assertTrue(hasattr(NotificacionesPortal, 'objects'))
        self.assertTrue(hasattr(NotificacionesPortal, 'id_notificacion'))
    
    def test_notificaciones_saldo_existe(self):
        """Test: NotificacionesSaldo modelo existe"""
        self.assertTrue(hasattr(NotificacionesSaldo, 'objects'))
        self.assertTrue(hasattr(NotificacionesSaldo, 'id_notificacion'))
    
    def test_alertas_sistema_existe(self):
        """Test: AlertasSistema modelo existe"""
        self.assertTrue(hasattr(AlertasSistema, 'objects'))
        self.assertTrue(hasattr(AlertasSistema, 'id_alerta'))
    
    def test_preferencias_notificacion_existe(self):
        """Test: PreferenciasNotificacion modelo existe"""
        self.assertTrue(hasattr(PreferenciasNotificacion, 'objects'))
        self.assertTrue(hasattr(PreferenciasNotificacion, 'id_preferencia'))


@pytest.mark.django_db
class TestEmailsEnviados:
    """Tests para el modelo EmailsEnviados"""
    
    def test_modelo_emails_enviados_estructura(self):
        """Test: EmailsEnviados tiene campos esperados"""
        assert hasattr(EmailsEnviados, 'email_destinatario')
        assert hasattr(EmailsEnviados, 'asunto')
        assert hasattr(EmailsEnviados, 'estado')
    
    def test_tabla_db_correcta(self):
        """Test: EmailsEnviados apunta a tabla correcta"""
        assert EmailsEnviados._meta.db_table == 'emails_enviados'


@pytest.mark.django_db
class TestSmsEnviados:
    """Tests para el modelo SmsEnviados"""
    
    def test_modelo_sms_enviados_estructura(self):
        """Test: SmsEnviados tiene campos esperados"""
        assert hasattr(SmsEnviados, 'telefono')
        assert hasattr(SmsEnviados, 'mensaje')
        assert hasattr(SmsEnviados, 'estado')
    
    def test_tabla_db_correcta(self):
        """Test: SmsEnviados apunta a tabla correcta"""
        assert SmsEnviados._meta.db_table == 'sms_enviados'
