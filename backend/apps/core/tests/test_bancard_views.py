"""
Tests para los endpoints de Bancard vPOS.
Cubre: iniciar pago, retorno (mock), estado.
"""
from decimal import Decimal
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient


# ─── Fixtures locales ─────────────────────────────────────────────────────────

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def api_cliente_web(api_client, db):
    from apps.usuarios.models import Usuario
    u = Usuario.objects.create_user(
        email="padre@test.com",
        password="test1234",
        nombre="Padre",
        apellido="Test",
        rol=Usuario.Rol.CLIENTE_WEB,
    )
    api_client.force_authenticate(user=u)
    return api_client, u


@pytest.fixture
def hijo_con_tarjeta(db, cliente):
    from apps.clientes.models import Hijo
    from apps.core.models import Tarjeta
    hijo = Hijo.objects.create(
        nombre="Ana",
        apellido="García",
        cliente_responsable=cliente,
        activo=True,
    )
    tarjeta = Tarjeta.objects.create(
        nro_tarjeta="BANCARD001",
        hijo=hijo,
        saldo_actual=Decimal("50000"),
        estado=Tarjeta.Estado.ACTIVA,
    )
    return hijo, tarjeta


# ─── Tests iniciar pago ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBancardIniciar:

    def test_iniciar_sin_autenticacion_falla(self, api_client, hijo_con_tarjeta):
        _, tarjeta = hijo_con_tarjeta
        resp = api_client.post('/api/v1/core/bancard/iniciar/', {
            'nro_tarjeta': tarjeta.nro_tarjeta,
            'monto': 100000,
        })
        assert resp.status_code in (401, 403)

    def test_iniciar_monto_invalido_falla(self, api_cliente_web, hijo_con_tarjeta):
        client, _ = api_cliente_web
        _, tarjeta = hijo_con_tarjeta
        resp = client.post('/api/v1/core/bancard/iniciar/', {
            'nro_tarjeta': tarjeta.nro_tarjeta,
            'monto': 5000,  # < mínimo 10.000
        })
        assert resp.status_code == 400
        assert 'mínimo' in resp.data.get('detail', '').lower()

    def test_iniciar_monto_excesivo_falla(self, api_cliente_web, hijo_con_tarjeta):
        client, _ = api_cliente_web
        _, tarjeta = hijo_con_tarjeta
        resp = client.post('/api/v1/core/bancard/iniciar/', {
            'nro_tarjeta': tarjeta.nro_tarjeta,
            'monto': 10_000_000,
        })
        assert resp.status_code == 400

    def test_iniciar_tarjeta_inexistente_falla(self, api_cliente_web):
        client, _ = api_cliente_web
        resp = client.post('/api/v1/core/bancard/iniciar/', {
            'nro_tarjeta': 'NOEXISTE',
            'monto': 100000,
        })
        assert resp.status_code == 404

    def test_iniciar_tarjeta_bloqueada_falla(self, api_cliente_web, db, cliente):
        from apps.clientes.models import Hijo
        from apps.core.models import Tarjeta
        client, _ = api_cliente_web
        hijo = Hijo.objects.create(nombre="X", apellido="Y", cliente_responsable=cliente, activo=True)
        t = Tarjeta.objects.create(
            nro_tarjeta="BLOQ001",
            hijo=hijo,
            saldo_actual=Decimal("10000"),
            estado=Tarjeta.Estado.BLOQUEADA,
        )
        resp = client.post('/api/v1/core/bancard/iniciar/', {
            'nro_tarjeta': t.nro_tarjeta,
            'monto': 100000,
        })
        assert resp.status_code == 400
        assert 'bloqueada' in resp.data.get('detail', '').lower()

    @patch('apps.core.bancard_service.iniciar_pago')
    def test_iniciar_bancard_error_devuelve_502(self, mock_iniciar, api_cliente_web, hijo_con_tarjeta):
        mock_iniciar.return_value = {'status': 'error', 'messages': [{'dsc': 'Credenciales inválidas'}]}
        client, _ = api_cliente_web
        _, tarjeta = hijo_con_tarjeta
        resp = client.post('/api/v1/core/bancard/iniciar/', {
            'nro_tarjeta': tarjeta.nro_tarjeta,
            'monto': 100000,
        })
        assert resp.status_code == 502

    @patch('apps.core.bancard_service.iniciar_pago')
    def test_iniciar_bancard_ok_devuelve_redirect_url(self, mock_iniciar, api_cliente_web, hijo_con_tarjeta):
        mock_iniciar.return_value = {'status': 'success', 'process_id': 'proc-abc-123'}
        client, _ = api_cliente_web
        _, tarjeta = hijo_con_tarjeta
        resp = client.post('/api/v1/core/bancard/iniciar/', {
            'nro_tarjeta': tarjeta.nro_tarjeta,
            'monto': 150000,
        })
        assert resp.status_code == 201
        assert 'redirect_url' in resp.data
        assert 'shop_process_id' in resp.data
        assert 'proc-abc-123' in resp.data['redirect_url']

    @patch('apps.core.bancard_service.iniciar_pago')
    def test_iniciar_crea_pago_bancard_en_db(self, mock_iniciar, api_cliente_web, hijo_con_tarjeta):
        from apps.core.models import PagoBancard
        mock_iniciar.return_value = {'status': 'success', 'process_id': 'proc-xyz'}
        client, _ = api_cliente_web
        _, tarjeta = hijo_con_tarjeta
        client.post('/api/v1/core/bancard/iniciar/', {
            'nro_tarjeta': tarjeta.nro_tarjeta,
            'monto': 200000,
        })
        pago = PagoBancard.objects.filter(tarjeta=tarjeta).first()
        assert pago is not None
        assert pago.monto == 200000
        assert pago.estado == PagoBancard.Estado.PENDIENTE
        assert pago.process_id == 'proc-xyz'


# ─── Tests estado pago ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBancardEstado:

    @patch('apps.core.bancard_service.iniciar_pago')
    def test_estado_pago_pendiente(self, mock_iniciar, api_cliente_web, hijo_con_tarjeta):
        from apps.core.models import PagoBancard
        mock_iniciar.return_value = {'status': 'success', 'process_id': 'proc-estado-1'}
        client, user = api_cliente_web
        _, tarjeta = hijo_con_tarjeta

        # Crear pago
        init_resp = client.post('/api/v1/core/bancard/iniciar/', {
            'nro_tarjeta': tarjeta.nro_tarjeta,
            'monto': 100000,
        })
        shop_pid = init_resp.data['shop_process_id']

        # Consultar estado
        resp = client.get(f'/api/v1/core/bancard/estado/{shop_pid}/')
        assert resp.status_code == 200
        assert resp.data['estado'] == PagoBancard.Estado.PENDIENTE
        assert resp.data['monto'] == 100000

    def test_estado_pago_inexistente_falla(self, api_cliente_web):
        client, _ = api_cliente_web
        resp = client.get('/api/v1/core/bancard/estado/NOEXISTE/')
        assert resp.status_code == 404

    def test_estado_sin_autenticacion_falla(self, api_client):
        resp = api_client.get('/api/v1/core/bancard/estado/CUALQUIER/')
        assert resp.status_code in (401, 403)


# ─── Tests retorno ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBancardRetorno:

    def test_retorno_sin_shop_process_id_redirige(self, api_client):
        resp = api_client.get('/api/v1/core/bancard/retorno/')
        # Debe redirigir (302) al portal con estado=error
        assert resp.status_code == 302
        assert 'error' in resp['Location']

    def test_retorno_shop_process_id_inexistente_redirige(self, api_client):
        resp = api_client.get('/api/v1/core/bancard/retorno/', {'shop_process_id': 'NOEXISTE'})
        assert resp.status_code == 302
        assert 'error' in resp['Location']

    @patch('apps.core.bancard_service.confirmar_pago')
    @patch('apps.core.bancard_service.iniciar_pago')
    def test_retorno_aprobado_acredita_saldo(
        self, mock_iniciar, mock_confirmar, api_cliente_web, hijo_con_tarjeta
    ):
        mock_iniciar.return_value = {'status': 'success', 'process_id': 'proc-retorno-ok'}
        mock_confirmar.return_value = {
            'status': 'success',
            'confirmation': {'response_code': '00', 'payment_id': '999'},
        }

        client, _ = api_cliente_web
        _, tarjeta = hijo_con_tarjeta
        saldo_inicial = tarjeta.saldo_actual

        # Crear pago
        init_resp = client.post('/api/v1/core/bancard/iniciar/', {
            'nro_tarjeta': tarjeta.nro_tarjeta,
            'monto': 100000,
        })
        shop_pid = init_resp.data['shop_process_id']

        # Simular retorno desde Bancard
        anon_client = APIClient()
        resp = anon_client.get('/api/v1/core/bancard/retorno/', {'shop_process_id': shop_pid})
        assert resp.status_code == 302
        assert 'aprobado' in resp['Location']

        # Verificar saldo acreditado
        tarjeta.refresh_from_db()
        assert tarjeta.saldo_actual == saldo_inicial + Decimal('100000')

    @patch('apps.core.bancard_service.confirmar_pago')
    @patch('apps.core.bancard_service.iniciar_pago')
    def test_retorno_rechazado_no_acredita(
        self, mock_iniciar, mock_confirmar, api_cliente_web, hijo_con_tarjeta
    ):
        mock_iniciar.return_value = {'status': 'success', 'process_id': 'proc-retorno-bad'}
        mock_confirmar.return_value = {'status': 'error', 'messages': [{'dsc': 'Fondos insuficientes'}]}

        client, _ = api_cliente_web
        _, tarjeta = hijo_con_tarjeta
        saldo_inicial = tarjeta.saldo_actual

        init_resp = client.post('/api/v1/core/bancard/iniciar/', {
            'nro_tarjeta': tarjeta.nro_tarjeta,
            'monto': 100000,
        })
        shop_pid = init_resp.data['shop_process_id']

        anon_client = APIClient()
        resp = anon_client.get('/api/v1/core/bancard/retorno/', {'shop_process_id': shop_pid})
        assert resp.status_code == 302
        assert 'rechazado' in resp['Location']

        tarjeta.refresh_from_db()
        assert tarjeta.saldo_actual == saldo_inicial  # sin cambio

    @patch('apps.core.bancard_service.iniciar_pago')
    def test_retorno_pago_ya_aprobado_redirige_sin_reprocessar(
        self, mock_iniciar, api_cliente_web, hijo_con_tarjeta
    ):
        """Pago ya en estado APROBADO — segundo retorno redirige directamente."""
        from apps.core.models import PagoBancard
        mock_iniciar.return_value = {'status': 'success', 'process_id': 'proc-doble'}

        client, _ = api_cliente_web
        _, tarjeta = hijo_con_tarjeta

        init_resp = client.post('/api/v1/core/bancard/iniciar/', {
            'nro_tarjeta': tarjeta.nro_tarjeta,
            'monto': 100000,
        })
        shop_pid = init_resp.data['shop_process_id']

        # Marcar como aprobado directamente en DB
        PagoBancard.objects.filter(shop_process_id=shop_pid).update(
            estado=PagoBancard.Estado.APROBADO
        )

        anon_client = APIClient()
        resp = anon_client.get('/api/v1/core/bancard/retorno/', {'shop_process_id': shop_pid})
        assert resp.status_code == 302
        assert 'aprobado' in resp['Location']

    @patch('apps.core.bancard_service.confirmar_pago')
    @patch('apps.core.bancard_service.iniciar_pago')
    def test_retorno_error_acreditacion_registra_error(
        self, mock_iniciar, mock_confirmar, api_cliente_web, hijo_con_tarjeta
    ):
        """Fallo en acreditar_saldo → estado ERROR, redirige con estado=error."""
        from apps.core.models import PagoBancard
        mock_iniciar.return_value = {'status': 'success', 'process_id': 'proc-acr-err'}
        mock_confirmar.return_value = {
            'status': 'success',
            'confirmation': {'response_code': '00'},
        }

        client, _ = api_cliente_web
        _, tarjeta = hijo_con_tarjeta

        init_resp = client.post('/api/v1/core/bancard/iniciar/', {
            'nro_tarjeta': tarjeta.nro_tarjeta,
            'monto': 100000,
        })
        shop_pid = init_resp.data['shop_process_id']

        with patch('apps.core.bancard_service.acreditar_saldo', side_effect=Exception("acreditación fallida")):
            anon_client = APIClient()
            resp = anon_client.get('/api/v1/core/bancard/retorno/', {'shop_process_id': shop_pid})

        assert resp.status_code == 302
        assert 'error' in resp['Location']
        pago = PagoBancard.objects.get(shop_process_id=shop_pid)
        assert pago.estado == PagoBancard.Estado.ERROR


@pytest.mark.django_db
class TestBancardIniciarEdgeCases:

    def test_iniciar_sin_params_falla(self, api_cliente_web):
        client, _ = api_cliente_web
        resp = client.post('/api/v1/core/bancard/iniciar/', {}, format='json')
        assert resp.status_code == 400

    def test_iniciar_monto_no_numerico_falla(self, api_cliente_web, hijo_con_tarjeta):
        client, _ = api_cliente_web
        _, tarjeta = hijo_con_tarjeta
        resp = client.post('/api/v1/core/bancard/iniciar/', {
            'nro_tarjeta': tarjeta.nro_tarjeta,
            'monto': 'no_es_numero',
        })
        assert resp.status_code == 400

    def test_iniciar_sin_claves_bancard_devuelve_503(self, api_cliente_web, hijo_con_tarjeta):
        from django.test import override_settings
        client, _ = api_cliente_web
        _, tarjeta = hijo_con_tarjeta
        with override_settings(BANCARD_PUBLIC_KEY='', BANCARD_PRIVATE_KEY=''):
            resp = client.post('/api/v1/core/bancard/iniciar/', {
                'nro_tarjeta': tarjeta.nro_tarjeta,
                'monto': 100000,
            })
        assert resp.status_code == 503


@pytest.mark.django_db
class TestBancardEstadoPermiso:

    @patch('apps.core.bancard_service.iniciar_pago')
    def test_estado_otro_cliente_devuelve_403(self, mock_iniciar, hijo_con_tarjeta, cliente, db):
        """Un CLIENTE_WEB que no es dueño del pago recibe 403."""
        from apps.usuarios.models import Usuario
        from rest_framework.test import APIClient

        mock_iniciar.return_value = {'status': 'success', 'process_id': 'proc-ajeno'}

        # Crear dueño del pago — usuario vinculado al cliente fixture
        owner = Usuario.objects.create_user(
            email="owner_bancard@test.com",
            password="test1234",
            nombre="Owner",
            apellido="Test",
            rol=Usuario.Rol.CLIENTE_WEB,
            cliente=cliente,
        )
        owner_client = APIClient()
        owner_client.force_authenticate(user=owner)

        _, tarjeta = hijo_con_tarjeta
        init_resp = owner_client.post('/api/v1/core/bancard/iniciar/', {
            'nro_tarjeta': tarjeta.nro_tarjeta,
            'monto': 100000,
        })
        shop_pid = init_resp.data['shop_process_id']

        # Otro usuario sin ese cliente
        otro_user = Usuario.objects.create_user(
            email="otro_bancard@test.com",
            password="test1234",
            nombre="Otro",
            apellido="Sin cliente",
            rol=Usuario.Rol.CAJERO,
        )
        otro_client = APIClient()
        otro_client.force_authenticate(user=otro_user)

        resp = otro_client.get(f'/api/v1/core/bancard/estado/{shop_pid}/')
        assert resp.status_code == 403
