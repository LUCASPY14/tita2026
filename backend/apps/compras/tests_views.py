"""
Tests para apps/compras/views.py
Cubre ComprasViewSet acciones personalizadas y ProveedoresViewSet
"""
from unittest.mock import MagicMock, patch
from decimal import Decimal
from django.utils import timezone

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import ValidationError
from rest_framework import status
from django.contrib.auth.models import User

from apps.compras.models import Proveedores, Compras
from apps.compras.views import ComprasViewSet, ProveedoresViewSet


def crear_proveedor():
    return Proveedores.objects.create(
        razon_social='Proveedor Test',
        ruc='80012345-0',
        activo=True,
        fecha_registro=timezone.now(),
    )


class ComprasViewSetPerformCreateTest(TestCase):
    """Tests para ComprasViewSet.perform_create"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.proveedor = crear_proveedor()

    def _make_viewset_request(self, data):
        """Helper to make a POST request"""
        user = MagicMock()
        user.is_authenticated = True
        request = self.factory.post('/compras/', data, format='json')
        request.user = user
        return request

    def test_perform_create_sin_detalles_guarda_pendiente(self):
        """Sin detalles en request data, guarda directamente con estado Pendiente"""
        vs = ComprasViewSet()
        request = MagicMock()
        request.data = {}  # sin detalles
        vs.request = request

        serializer = MagicMock()
        vs.perform_create(serializer)
        serializer.save.assert_called_once_with(estado='Pendiente')

    def test_perform_create_con_detalles_validos(self):
        """Con detalles válidos, calcula totales y guarda"""
        vs = ComprasViewSet()
        request = MagicMock()
        request.data = {'detalles': [{'id_producto': 1, 'cantidad': 10, 'precio_unitario': 1000}]}
        vs.request = request

        serializer = MagicMock()

        with patch('apps.compras.views.CompraService.validar_compra',
                   return_value={'valido': True, 'errores': [], 'warnings': []}):
            with patch('apps.compras.views.CompraService.calcular_totales_compra',
                       return_value={'total': Decimal('10000.00')}):
                vs.perform_create(serializer)

        serializer.save.assert_called_once_with(
            monto_total=Decimal('10000.00'),
            saldo_pendiente=Decimal('10000.00'),
            estado='Pendiente',
        )

    def test_perform_create_con_detalles_invalidos_lanza_error(self):
        """Con detalles inválidos, lanza ValidationError"""
        vs = ComprasViewSet()
        request = MagicMock()
        request.data = {'detalles': [{'id_producto': 1, 'cantidad': 0, 'precio_unitario': 0}]}
        vs.request = request

        serializer = MagicMock()

        with patch('apps.compras.views.CompraService.validar_compra',
                   return_value={'valido': False, 'errores': ['cantidad inválida'], 'warnings': []}):
            with self.assertRaises(ValidationError):
                vs.perform_create(serializer)


class ComprasViewSetConfirmarTest(TestCase):
    """Tests para ComprasViewSet.confirmar action"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.proveedor = crear_proveedor()
        self.compra = Compras.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal('50000.00'),
            saldo_pendiente=Decimal('50000.00'),
            estado_pago='pendiente',
            id_proveedor=self.proveedor,
        )
        self.user = User.objects.create_user(username='testcompr', password='pass')

    def test_confirmar_sin_empleado_retorna_400(self):
        """Sin empleado asociado, retorna 400"""
        request = self.factory.post(f'/compras/{self.compra.id_compra}/confirmar/')
        request.user = self.user
        request.user.empleado = None

        vs = ComprasViewSet()
        vs.request = request
        vs.kwargs = {'pk': self.compra.id_compra}
        vs.format_kwarg = None
        vs.action = 'confirmar'
        vs.get_object = lambda: self.compra

        response = vs.confirmar(request, pk=self.compra.id_compra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirmar_exitoso(self):
        """Confirmar exitoso retorna 200"""
        empleado_mock = MagicMock()
        request = self.factory.post(f'/compras/{self.compra.id_compra}/confirmar/')
        request.user = self.user
        request.user.empleado = empleado_mock

        compra_confirmada_mock = MagicMock()

        vs = ComprasViewSet()
        vs.request = request
        vs.kwargs = {'pk': self.compra.id_compra}
        vs.format_kwarg = None
        vs.action = 'confirmar'
        vs.get_object = lambda: self.compra
        vs.get_serializer = MagicMock(return_value=MagicMock(data={'id': 1}))

        with patch('apps.compras.views.CompraService.confirmar_compra',
                   return_value=compra_confirmada_mock):
            response = vs.confirmar(request, pk=self.compra.id_compra)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_confirmar_lanza_validation_error_retorna_400(self):
        """Si CompraService.confirmar_compra lanza ValidationError, retorna 400"""
        empleado_mock = MagicMock()
        request = self.factory.post(f'/compras/{self.compra.id_compra}/confirmar/')
        request.user = self.user
        request.user.empleado = empleado_mock

        vs = ComprasViewSet()
        vs.request = request
        vs.kwargs = {'pk': self.compra.id_compra}
        vs.format_kwarg = None
        vs.action = 'confirmar'
        vs.get_object = lambda: self.compra

        with patch('apps.compras.views.CompraService.confirmar_compra',
                   side_effect=ValidationError('error')):
            response = vs.confirmar(request, pk=self.compra.id_compra)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ComprasViewSetPendientesTest(TestCase):
    """Tests para ComprasViewSet.pendientes action"""

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_pendientes_retorna_lista(self):
        request = self.factory.get('/compras/pendientes/')
        request.user = MagicMock()

        compras_mock = MagicMock()
        compras_mock.count.return_value = 2

        vs = ComprasViewSet()
        vs.request = request
        vs.get_serializer = MagicMock(return_value=MagicMock(data=[]))
        vs.format_kwarg = None
        vs.action = 'pendientes'

        with patch('apps.compras.views.CompraService.obtener_compras_pendientes_confirmacion',
                   return_value=compras_mock):
            response = vs.pendientes(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 2)


class ComprasViewSetCalcularTotalesTest(TestCase):
    """Tests para ComprasViewSet.calcular_totales action"""

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_sin_detalles_retorna_400(self):
        request = self.factory.post('/compras/calcular_totales/', {}, format='json')
        request.user = MagicMock()
        request.data = {}

        vs = ComprasViewSet()
        vs.request = request
        vs.format_kwarg = None

        response = vs.calcular_totales(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detalles_invalidos_retorna_400(self):
        request = self.factory.post('/compras/calcular_totales/', {'detalles': [{'x': 1}]}, format='json')
        request.user = MagicMock()
        request.data = {'detalles': [{'x': 1}]}

        vs = ComprasViewSet()
        vs.request = request
        vs.format_kwarg = None

        with patch('apps.compras.views.CompraService.validar_compra',
                   return_value={'valido': False, 'errores': ['error'], 'warnings': []}):
            response = vs.calcular_totales(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detalles_validos_retorna_totales(self):
        request = self.factory.post('/compras/calcular_totales/',
                                    {'detalles': [{'id_producto': 1, 'cantidad': 5, 'precio_unitario': 2000}]},
                                    format='json')
        request.user = MagicMock()
        request.data = {'detalles': [{'id_producto': 1, 'cantidad': 5, 'precio_unitario': 2000}]}

        vs = ComprasViewSet()
        vs.request = request
        vs.format_kwarg = None

        with patch('apps.compras.views.CompraService.validar_compra',
                   return_value={'valido': True, 'errores': [], 'warnings': []}):
            with patch('apps.compras.views.CompraService.calcular_totales_compra',
                       return_value={'total': Decimal('10000.00')}):
                response = vs.calcular_totales(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('totales', response.data)


class ProveedoresViewSetCuentaCorrienteTest(TestCase):
    """Tests para ProveedoresViewSet.cuenta_corriente action"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.proveedor = crear_proveedor()

    def test_cuenta_corriente_retorna_datos(self):
        request = self.factory.get(f'/proveedores/{self.proveedor.id_proveedor}/cuenta_corriente/')
        request.user = MagicMock()

        vs = ProveedoresViewSet()
        vs.request = request
        vs.kwargs = {'pk': self.proveedor.id_proveedor}
        vs.format_kwarg = None
        vs.action = 'cuenta_corriente'
        vs.get_object = lambda: self.proveedor

        cuenta_mock = {
            'total_compras': Decimal('100000.00'),
            'total_pagado': Decimal('50000.00'),
            'saldo_pendiente': Decimal('50000.00'),
        }

        with patch('apps.compras.views.CompraService.obtener_cuenta_corriente_proveedor',
                   return_value=cuenta_mock):
            response = vs.cuenta_corriente(request, pk=self.proveedor.id_proveedor)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('proveedor', response.data)
        self.assertEqual(response.data['proveedor']['id'], self.proveedor.id_proveedor)
