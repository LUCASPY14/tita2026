"""
Tests simplificados para permisos del módulo common
Tests básicos sin dependencias complejas de modelos
"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory
from apps.common.permissions import (
    IsAdminOrReadOnly,
    ReadOnly
)


class IsAdminOrReadOnlyTest(TestCase):
    """Tests para IsAdminOrReadOnly permission"""
    
    def setUp(self):
        """Setup users"""
        self.factory = APIRequestFactory()
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True
        )
        self.normal_user = User.objects.create_user(
            username='user',
            password='user123',
            is_staff=False
        )
    
    def test_authenticated_user_can_read(self):
        """Usuario autenticado puede leer (GET)"""
        permission = IsAdminOrReadOnly()
        request = self.factory.get('/test/')
        request.user = self.normal_user
        
        self.assertTrue(permission.has_permission(request, None))
    
    def test_authenticated_user_cannot_write(self):
        """Usuario normal no puede escribir (POST)"""
        permission = IsAdminOrReadOnly()
        request = self.factory.post('/test/')
        request.user = self.normal_user
        
        self.assertFalse(permission.has_permission(request, None))
    
    def test_admin_can_write(self):
        """Administrador puede escribir"""
        permission = IsAdminOrReadOnly()
        request = self.factory.post('/test/')
        request.user = self.admin_user
        
        self.assertTrue(permission.has_permission(request, None))
    
    def test_admin_can_delete(self):
        """Administrador puede eliminar"""
        permission = IsAdminOrReadOnly()
        request = self.factory.delete('/test/')
        request.user = self.admin_user
        
        self.assertTrue(permission.has_permission(request, None))


class ReadOnlyTest(TestCase):
    """Tests para ReadOnly permission"""
    
    def setUp(self):
        """Setup users"""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='test123'
        )
    
    def test_authenticated_user_can_read(self):
        """Usuario autenticado puede leer"""
        permission = ReadOnly()
        request = self.factory.get('/test/')
        request.user = self.user
        
        self.assertTrue(permission.has_permission(request, None))
    
    def test_authenticated_user_cannot_write(self):
        """Usuario autenticado no puede escribir"""
        permission = ReadOnly()
        request = self.factory.post('/test/')
        request.user = self.user
        
        self.assertFalse(permission.has_permission(request, None))
    
    def test_head_method_allowed(self):
        """Método HEAD permitido"""
        permission = ReadOnly()
        request = self.factory.head('/test/')
        request.user = self.user
        
        self.assertTrue(permission.has_permission(request, None))
    
    def test_options_method_allowed(self):
        """Método OPTIONS permitido"""
        permission = ReadOnly()
        request = self.factory.options('/test/')
        request.user = self.user
        
        self.assertTrue(permission.has_permission(request, None))
