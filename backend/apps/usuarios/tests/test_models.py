"""
Tests de modelos de usuarios.
Cubre: __str__, @property, Manager edge cases, save() validation.
"""
import pytest
from django.utils import timezone


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def rol(db):
    from apps.usuarios.models import Rol
    return Rol.objects.create(nombre_rol="Cajero Test", descripcion="Rol de prueba")


@pytest.fixture
def permiso(db):
    from apps.usuarios.models import Permiso
    return Permiso.objects.create(
        codigo_permiso="VER_VENTAS",
        nombre="Ver Ventas",
        modulo="ventas",
    )


@pytest.fixture
def empleado(db, rol):
    from apps.usuarios.models import Empleado
    return Empleado.objects.create(
        nombre="Carlos",
        apellido="Test",
        id_rol=rol,
    )


# ── UsuarioManager ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUsuarioManager:

    def test_create_user_sin_email_falla(self):
        from apps.usuarios.models import Usuario
        with pytest.raises(ValueError, match="[Ee]mail"):
            Usuario.objects.create_user(email="", password="test1234")

    def test_create_superuser_crea_admin(self):
        from apps.usuarios.models import Usuario
        user = Usuario.objects.create_superuser(
            email="super@test.com", password="test1234"
        )
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.rol == Usuario.Rol.ADMIN


# ── Usuario __str__ y properties ─────────────────────────────────────────────

@pytest.mark.django_db
class TestUsuarioModel:

    def test_str(self, usuario_admin):
        assert "Admin" in str(usuario_admin)

    def test_es_cliente_web_true(self, db, cliente):
        from apps.usuarios.models import Usuario
        u = Usuario.objects.create_user(
            email="web@test.com", password="x",
            nombre="Web", apellido="User",
            rol=Usuario.Rol.CLIENTE_WEB,
            cliente=cliente,
        )
        assert u.es_cliente_web is True
        assert u.es_empleado is False

    def test_es_empleado_true(self, usuario_cajero):
        assert usuario_cajero.es_empleado is True
        assert usuario_cajero.es_cliente_web is False

    def test_save_superuser_no_admin_falla(self, db):
        from apps.usuarios.models import Usuario
        with pytest.raises(ValueError, match="ADMIN"):
            Usuario.objects.create(
                email="bad@test.com",
                nombre="Bad", apellido="User",
                rol=Usuario.Rol.CAJERO,
                is_superuser=True,
                is_active=True,
            )


# ── __str__ de todos los modelos de seguridad ─────────────────────────────────

@pytest.mark.django_db
class TestModelosStr:

    def test_empleado_str(self, empleado):
        assert "Carlos" in str(empleado)

    def test_rol_str(self, rol):
        assert "Cajero Test" in str(rol)

    def test_permiso_str(self, permiso):
        assert "VER_VENTAS" in str(permiso)

    def test_rol_permiso_str(self, db, rol, permiso):
        from apps.usuarios.models import RolPermiso
        rp = RolPermiso.objects.create(id_rol=rol, id_permiso=permiso)
        assert "Cajero Test" in str(rp)

    def test_perfil_usuario_str(self, db, usuario_admin):
        from apps.usuarios.models import PerfilUsuario
        p = PerfilUsuario.objects.create(usuario=usuario_admin)
        assert "Admin" in str(p)

    def test_autenticacion_2fa_str(self, db, usuario_admin):
        from apps.usuarios.models import Autenticacion2FA
        a = Autenticacion2FA.objects.create(
            usuario=usuario_admin, secret_key="TESTSECRET"
        )
        assert "admin@test.com" in str(a)

    def test_intento_2fa_str(self, db, usuario_admin):
        from apps.usuarios.models import Intento2FA
        i = Intento2FA.objects.create(
            usuario=usuario_admin, codigo_ingresado="123456", exitoso=True
        )
        s = str(i)
        assert "exitoso" in s or "fallido" in s

    def test_intento_login_str(self, db):
        from apps.usuarios.models import IntentoLogin
        i = IntentoLogin.objects.create(
            email="test@test.com", ip_address="127.0.0.1", exitoso=False
        )
        assert "test@test.com" in str(i)

    def test_sesion_activa_str(self, db, usuario_admin):
        from apps.usuarios.models import SesionActiva
        s = SesionActiva.objects.create(
            usuario=usuario_admin, session_key="abc123", activa=True
        )
        assert "admin@test.com" in str(s)

    def test_renovacion_sesion_str(self, db, usuario_admin):
        from apps.usuarios.models import RenovacionSesion
        r = RenovacionSesion.objects.create(usuario=usuario_admin)
        assert "admin@test.com" in str(r)

    def test_patron_acceso_str(self, db, usuario_admin):
        from apps.usuarios.models import PatronAcceso
        p = PatronAcceso.objects.create(
            usuario=usuario_admin, ip_address="192.168.1.1"
        )
        assert "admin@test.com" in str(p)

    def test_bloqueo_cuenta_str(self, db, usuario_admin):
        from apps.usuarios.models import BloqueoCuenta
        b = BloqueoCuenta.objects.create(
            usuario=usuario_admin, motivo="Test bloqueo"
        )
        assert "admin@test.com" in str(b)

    def test_token_recuperacion_str(self, db, usuario_admin):
        from apps.usuarios.models import TokenRecuperacion
        t = TokenRecuperacion.objects.create(
            usuario=usuario_admin,
            token="abc123xyz",
            fecha_expiracion=timezone.now() + timezone.timedelta(hours=24),
        )
        assert "admin@test.com" in str(t)

    def test_token_recuperacion_es_valido(self, db, usuario_admin):
        from apps.usuarios.models import TokenRecuperacion
        t = TokenRecuperacion.objects.create(
            usuario=usuario_admin,
            token="valido123",
            fecha_expiracion=timezone.now() + timezone.timedelta(hours=24),
            usado=False,
        )
        assert t.es_valido is True

    def test_token_recuperacion_expirado(self, db, usuario_admin):
        from apps.usuarios.models import TokenRecuperacion
        t = TokenRecuperacion.objects.create(
            usuario=usuario_admin,
            token="expirado123",
            fecha_expiracion=timezone.now() - timezone.timedelta(hours=1),
            usado=False,
        )
        assert t.es_valido is False

    def test_token_verificacion_str(self, db, usuario_admin):
        from apps.usuarios.models import TokenVerificacion
        t = TokenVerificacion.objects.create(
            usuario=usuario_admin,
            token="verif_abc",
            expira_en=timezone.now() + timezone.timedelta(hours=24),
        )
        assert "admin@test.com" in str(t)

    def test_token_verificacion_es_valido(self, db, usuario_admin):
        from apps.usuarios.models import TokenVerificacion
        t = TokenVerificacion.objects.create(
            usuario=usuario_admin,
            token="verif_valid",
            expira_en=timezone.now() + timezone.timedelta(hours=24),
            usado=False,
        )
        assert t.es_valido is True

    def test_auditoria_empleado_str(self, db, empleado):
        from apps.usuarios.models import AuditoriaEmpleado
        a = AuditoriaEmpleado.objects.create(
            empleado=empleado,
            campo_modificado="telefono",
        )
        assert "telefono" in str(a)

    def test_auditoria_operacion_str(self, db, usuario_admin):
        from apps.usuarios.models import AuditoriaOperacion
        a = AuditoriaOperacion.objects.create(
            usuario=usuario_admin,
            operacion="CREAR_VENTA",
            resultado="EXITO",
        )
        assert "CREAR_VENTA" in str(a)

    def test_auditoria_usuario_web_str(self, db, cliente):
        from apps.usuarios.models import AuditoriaUsuarioWeb
        a = AuditoriaUsuarioWeb.objects.create(
            cliente=cliente,
            campo_modificado="email",
        )
        assert "email" in str(a)
