"""
Tests para ConfiguracionSistema - ViewSets y Models
"""

from django.test import TestCase

import pytest  # type: ignore
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.core.models import ConfiguracionSistema
from apps.usuarios.models import Usuarios


class ConfiguracionSistemaModelTest(TestCase):
    """Tests para el modelo ConfiguracionSistema"""

    def test_crear_configuracion(self):
        """Test: Crear configuración del sistema"""
        # Use a key guaranteed not to exist in migration seed data
        ConfiguracionSistema.objects.filter(clave="MAX_INTENTOS_LOGIN").delete()
        config = ConfiguracionSistema.objects.create(
            clave="MAX_INTENTOS_LOGIN",
            valor="3",
            tipo="int",
            categoria="seguridad",
            descripcion="Máximo de intentos de login",
            valor_defecto="3",
            requerido=True,
        )

        self.assertEqual(config.clave, "MAX_INTENTOS_LOGIN")
        self.assertEqual(config.tipo, "int")
        self.assertTrue(config.estado)

    def test_configuracion_con_validacion(self):
        """Test: Configuración con validación de rango"""
        config = ConfiguracionSistema.objects.create(
            clave="TIMEOUT_SESSION",
            valor="30",
            tipo="int",
            categoria="seguridad",
            descripcion="Timeout de sesión en minutos",
            valor_min=5,
            valor_max=120,
            valor_defecto="30",
        )

        self.assertEqual(config.valor_min, 5)
        self.assertEqual(config.valor_max, 120)

    def test_configuracion_valores_permitidos(self):
        """Test: Configuración con valores permitidos"""
        config = ConfiguracionSistema.objects.create(
            clave="NIVEL_LOG",
            valor="INFO",
            tipo="string",
            categoria="sistema",
            descripcion="Nivel de logging",
            valores_permitidos=["DEBUG", "INFO", "WARNING", "ERROR"],
            valor_defecto="INFO",
        )

        self.assertIn("INFO", config.valores_permitidos)
        self.assertEqual(len(config.valores_permitidos), 4)

    def test_configuracion_requiere_reinicio(self):
        """Test: Configuración que requiere reinicio"""
        config = ConfiguracionSistema.objects.create(
            clave="DATABASE_POOL_SIZE",
            valor="10",
            tipo="int",
            categoria="sistema",
            descripcion="Tamaño del pool de conexiones",
            requiere_reinicio=True,
            valor_defecto="10",
        )

        self.assertTrue(config.requiere_reinicio)

    def test_configuracion_solo_superuser(self):
        """Test: Configuración solo para superusuarios"""
        config = ConfiguracionSistema.objects.create(
            clave="SECRET_KEY",
            valor="***",
            tipo="password",
            categoria="seguridad",
            descripcion="Clave secreta de la aplicación",
            solo_superuser=True,
            valor_defecto="changeme",
        )

        self.assertTrue(config.solo_superuser)


class ConfiguracionSistemaViewSetTest(APITestCase):
    """Tests para ConfiguracionSistemaViewSet"""

    def setUp(self):
        """Configuración inicial"""
        # Crear superusuario
        self.superuser = Usuarios.objects.create(
            username="admin",
            email="admin@cantina.com",
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )
        self.superuser.set_password("admin123")
        self.superuser.save()

        # Crear usuario normal
        self.normal_user = Usuarios.objects.create(username="user", email="user@cantina.com", is_active=True)
        self.normal_user.set_password("user123")
        self.normal_user.save()

        # Crear configuraciones de prueba
        # Limpiar datos semilla de migraciones para que los conteos sean predecibles
        ConfiguracionSistema.objects.all().delete()
        self.config1 = ConfiguracionSistema.objects.create(
            clave="TIMEOUT_SESSION",
            valor="30",
            tipo="int",
            categoria="seguridad",
            descripcion="Timeout de sesión",
            valor_defecto="30",
            updated_by=self.superuser,
        )

        self.config2 = ConfiguracionSistema.objects.create(
            clave="SMTP_HOST",
            valor="smtp.gmail.com",
            tipo="string",
            categoria="email",
            descripcion="Servidor SMTP",
            valor_defecto="localhost",
            updated_by=self.superuser,
        )

        self.config3 = ConfiguracionSistema.objects.create(
            clave="SECRET_KEY",
            valor="***secret***",
            tipo="password",
            categoria="seguridad",
            descripcion="Clave secreta",
            solo_superuser=True,
            valor_defecto="changeme",
            updated_by=self.superuser,
        )

        self.client = APIClient()

    def test_listar_configuraciones_superuser(self):
        """Test: Listar configuraciones como superusuario"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get("/api/v1/configuracion/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

    def test_listar_configuraciones_usuario_normal(self):
        """Test: Usuario normal no ve configs de superuser"""
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get("/api/v1/configuracion/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Solo debe ver 2 configuraciones (sin SECRET_KEY)
        self.assertEqual(len(response.data["results"]), 2)

    def test_filtrar_por_categoria(self):
        """Test: Filtrar configuraciones por categoría"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get("/api/v1/configuracion/", {"categoria": "seguridad"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_obtener_por_categoria_action(self):
        """Test: GET /api/v1/configuracion/por_categoria/"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get("/api/v1/configuracion/por_categoria/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("seguridad", response.data)
        self.assertIn("email", response.data)

    def test_actualizar_valor_config(self):
        """Test: POST /api/v1/configuracion/{id}/actualizar_valor/"""
        self.client.force_authenticate(user=self.superuser)
        url = f"/api/v1/configuracion/{self.config1.id_configuracion}/actualizar_valor/"
        data = {"valor": "60"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar actualización
        self.config1.refresh_from_db()
        self.assertEqual(self.config1.valor, "60")
        self.assertEqual(self.config1.updated_by, self.superuser)

    def test_resetear_a_default(self):
        """Test: POST /api/v1/configuracion/{id}/resetear_default/"""
        self.client.force_authenticate(user=self.superuser)

        # Cambiar valor primero
        self.config1.valor = "120"
        self.config1.save()

        url = f"/api/v1/configuracion/{self.config1.id_configuracion}/resetear_default/"
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que volvió al default
        self.config1.refresh_from_db()
        self.assertEqual(self.config1.valor, "30")

    def test_usuario_normal_no_puede_actualizar_superuser_config(self):
        """Test: Usuario normal no puede actualizar config de superuser"""
        self.client.force_authenticate(user=self.normal_user)
        url = f"/api/v1/configuracion/{self.config3.id_configuracion}/actualizar_valor/"
        data = {"valor": "hacked"}

        response = self.client.post(url, data)

        # Debe fallar
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])


@pytest.mark.django_db
class TestConfiguracionIntegration:
    """Tests de integración para ConfiguracionSistema"""

    def test_flujo_completo_configuracion(self):
        """Test: Flujo completo de manejo de configuración"""
        # Crear superusuario
        admin = Usuarios.objects.create(username="admin", email="admin@test.com", is_superuser=True, is_active=True)

        # 1. Crear configuración
        config = ConfiguracionSistema.objects.create(
            clave="MAX_FILE_SIZE",
            valor="5242880",  # 5MB
            tipo="int",
            categoria="sistema",
            descripcion="Tamaño máximo de archivo en bytes",
            valor_defecto="5242880",
            valor_min=1048576,  # 1MB
            valor_max=10485760,  # 10MB
            updated_by=admin,
        )

        # 2. Actualizar valor
        config.valor = "10485760"  # Cambiar a 10MB
        config.save()

        assert config.valor == "10485760"

        # 3. Resetear a default
        config.valor = config.valor_defecto
        config.save()

        assert config.valor == "5242880"

        # 4. Verificar validación de rango
        assert int(config.valor) >= config.valor_min
        assert int(config.valor) <= config.valor_max

    def test_agrupar_por_categoria(self):
        """Test: Agrupar configuraciones por categoría"""
        admin = Usuarios.objects.create(username="admin2", email="admin2@test.com", is_superuser=True, is_active=True)

        # Crear varias configs en diferentes categorías
        ConfiguracionSistema.objects.create(
            clave="SMTP_PORT",
            valor="587",
            tipo="int",
            categoria="email",
            valor_defecto="587",
            updated_by=admin,
        )
        ConfiguracionSistema.objects.create(
            clave="SMTP_HOST",
            valor="smtp.gmail.com",
            tipo="string",
            categoria="email",
            valor_defecto="localhost",
            updated_by=admin,
        )
        ConfiguracionSistema.objects.create(
            clave="SESSION_TIMEOUT",
            valor="30",
            tipo="int",
            categoria="seguridad",
            valor_defecto="30",
            updated_by=admin,
        )

        # Agrupar por categoría
        from django.db.models import Count

        categorias = ConfiguracionSistema.objects.values("categoria").annotate(total=Count("id_config"))

        assert len(categorias) >= 2
        email_configs = [c for c in categorias if c["categoria"] == "email"]
        assert len(email_configs) > 0
        assert email_configs[0]["total"] == 2
