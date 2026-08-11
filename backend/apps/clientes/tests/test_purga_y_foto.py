"""
Tests para:
- HijoViewSet.foto — endpoint protegido de la foto del alumno (solo ADMIN/CAJERO)
- HijoSerializer — foto_url en vez de URL cruda, foto_perfil write_only
- perform_update — fecha_baja se completa sola al desactivar un alumno
- services.purgar_alumno — anonimización de datos sensibles
- HijoViewSet.pendientes_purga / aprobar_purga — flujo de aprobación (solo ADMIN)
- tasks.dar_baja_alumnos_ultimo_curso / marcar_alumnos_pendientes_purga
"""
from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from apps.clientes.models import Grado, Hijo, RestriccionHijo
from apps.clientes.services import purgar_alumno

# PNG 1x1 transparente válido — necesario porque ImageField valida el contenido.
_PNG_1X1 = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
    b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def api_admin(api_client, usuario_admin):
    api_client.force_authenticate(user=usuario_admin)
    return api_client


@pytest.fixture
def api_cajero(api_client, usuario_cajero):
    api_client.force_authenticate(user=usuario_cajero)
    return api_client


@pytest.fixture
def usuario_supervisor(db):
    from apps.usuarios.models import Usuario
    return Usuario.objects.create_user(
        email="supervisor@purga.test", password="test1234",
        nombre="Sup", apellido="Ervisor", rol=Usuario.Rol.SUPERVISOR,
    )


@pytest.fixture
def api_supervisor(api_client, usuario_supervisor):
    api_client.force_authenticate(user=usuario_supervisor)
    return api_client


@pytest.fixture
def hijo_con_foto(db, cliente):
    foto = SimpleUploadedFile("foto.png", _PNG_1X1, content_type="image/png")
    return Hijo.objects.create(
        nombre="Ana", apellido="Gómez", cliente_responsable=cliente, foto_perfil=foto,
    )


@pytest.fixture
def hijo_sin_foto(db, cliente):
    return Hijo.objects.create(nombre="Luis", apellido="Ruiz", cliente_responsable=cliente)


@pytest.fixture
def hijo_pendiente_purga(db, cliente):
    return Hijo.objects.create(
        nombre="Marta", apellido="Díaz", cliente_responsable=cliente,
        activo=False,
        fecha_baja=timezone.now() - timedelta(days=400),
        purga_solicitada_en=timezone.now() - timedelta(days=5),
    )


@pytest.mark.django_db
class TestFotoEndpoint:

    def test_admin_puede_ver_foto(self, api_admin, hijo_con_foto):
        resp = api_admin.get(f"/api/v1/clientes/hijos/{hijo_con_foto.pk}/foto/")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "image/jpeg"

    def test_cajero_puede_ver_foto(self, api_cajero, hijo_con_foto):
        resp = api_cajero.get(f"/api/v1/clientes/hijos/{hijo_con_foto.pk}/foto/")
        assert resp.status_code == 200

    def test_supervisor_no_puede_ver_foto(self, api_supervisor, hijo_con_foto):
        resp = api_supervisor.get(f"/api/v1/clientes/hijos/{hijo_con_foto.pk}/foto/")
        assert resp.status_code == 403

    def test_sin_foto_devuelve_404(self, api_admin, hijo_sin_foto):
        resp = api_admin.get(f"/api/v1/clientes/hijos/{hijo_sin_foto.pk}/foto/")
        assert resp.status_code == 404

    def test_sin_autenticacion_falla(self, api_client, hijo_con_foto):
        resp = api_client.get(f"/api/v1/clientes/hijos/{hijo_con_foto.pk}/foto/")
        assert resp.status_code in (401, 403)


@pytest.mark.django_db
class TestHijoSerializerFoto:

    def test_foto_url_presente_cuando_hay_foto(self, api_admin, hijo_con_foto):
        resp = api_admin.get(f"/api/v1/clientes/hijos/{hijo_con_foto.pk}/")
        assert resp.data["foto_url"] == f"/clientes/hijos/{hijo_con_foto.pk}/foto/"

    def test_foto_url_none_sin_foto(self, api_admin, hijo_sin_foto):
        resp = api_admin.get(f"/api/v1/clientes/hijos/{hijo_sin_foto.pk}/")
        assert resp.data["foto_url"] is None

    def test_foto_perfil_no_aparece_en_la_respuesta(self, api_admin, hijo_con_foto):
        resp = api_admin.get(f"/api/v1/clientes/hijos/{hijo_con_foto.pk}/")
        assert "foto_perfil" not in resp.data


@pytest.mark.django_db
class TestFechaBajaAutomatica:

    def test_desactivar_alumno_completa_fecha_baja(self, api_admin, hijo_sin_foto):
        assert hijo_sin_foto.fecha_baja is None
        resp = api_admin.patch(
            f"/api/v1/clientes/hijos/{hijo_sin_foto.pk}/", {"activo": False}, format="json",
        )
        assert resp.status_code == 200
        hijo_sin_foto.refresh_from_db()
        assert hijo_sin_foto.activo is False
        assert hijo_sin_foto.fecha_baja is not None

    def test_no_pisa_fecha_baja_existente(self, api_admin, hijo_sin_foto):
        fecha_original = timezone.now() - timedelta(days=100)
        hijo_sin_foto.activo = False
        hijo_sin_foto.fecha_baja = fecha_original
        hijo_sin_foto.save()
        resp = api_admin.patch(
            f"/api/v1/clientes/hijos/{hijo_sin_foto.pk}/", {"nombre": "Luis Actualizado"}, format="json",
        )
        assert resp.status_code == 200
        hijo_sin_foto.refresh_from_db()
        assert hijo_sin_foto.fecha_baja == fecha_original

    def test_reactivar_no_toca_fecha_baja(self, api_admin, hijo_sin_foto):
        hijo_sin_foto.activo = False
        hijo_sin_foto.fecha_baja = timezone.now() - timedelta(days=5)
        hijo_sin_foto.save()
        fecha = hijo_sin_foto.fecha_baja
        resp = api_admin.patch(
            f"/api/v1/clientes/hijos/{hijo_sin_foto.pk}/", {"activo": True}, format="json",
        )
        assert resp.status_code == 200
        hijo_sin_foto.refresh_from_db()
        assert hijo_sin_foto.activo is True
        assert hijo_sin_foto.fecha_baja == fecha


@pytest.mark.django_db
class TestPurgarAlumnoService:

    def test_purga_borra_restricciones_y_anonimiza(self, hijo_con_foto, usuario_admin):
        RestriccionHijo.objects.create(
            hijo=hijo_con_foto, tipo="ALERGIA", descripcion="Maní", severidad="CRITICA",
        )
        grado = Grado.objects.create(nombre="6to purga", nivel=6, orden=6, es_ultimo=True)
        hijo_con_foto.grado = grado
        hijo_con_foto.fecha_nacimiento = "2015-01-01"
        hijo_con_foto.save()

        resultado = purgar_alumno(hijo_con_foto, aprobado_por=usuario_admin)

        assert resultado.datos_purgados is True
        assert resultado.nombre == "Alumno purgado"
        assert str(resultado.pk) in resultado.apellido
        assert resultado.fecha_nacimiento is None
        assert resultado.grado_id is None
        assert not resultado.foto_perfil
        assert RestriccionHijo.objects.filter(hijo=resultado).count() == 0

    def test_purga_mantiene_la_fila_del_alumno(self, hijo_sin_foto, usuario_admin):
        pk = hijo_sin_foto.pk
        purgar_alumno(hijo_sin_foto, aprobado_por=usuario_admin)
        assert Hijo.objects.filter(pk=pk).exists()


@pytest.mark.django_db
class TestPendientesPurga:

    def test_admin_ve_lista_de_pendientes(self, api_admin, hijo_pendiente_purga, hijo_sin_foto):
        resp = api_admin.get("/api/v1/clientes/hijos/pendientes-purga/")
        assert resp.status_code == 200
        ids = [h["id"] for h in resp.data]
        assert hijo_pendiente_purga.pk in ids
        assert hijo_sin_foto.pk not in ids

    def test_cajero_no_puede_ver_pendientes(self, api_cajero, hijo_pendiente_purga):
        resp = api_cajero.get("/api/v1/clientes/hijos/pendientes-purga/")
        assert resp.status_code == 403

    def test_ya_purgado_no_aparece_en_pendientes(self, api_admin, hijo_pendiente_purga):
        hijo_pendiente_purga.datos_purgados = True
        hijo_pendiente_purga.save()
        resp = api_admin.get("/api/v1/clientes/hijos/pendientes-purga/")
        ids = [h["id"] for h in resp.data]
        assert hijo_pendiente_purga.pk not in ids


@pytest.mark.django_db
class TestAprobarPurga:

    def test_admin_aprueba_purga(self, api_admin, hijo_pendiente_purga):
        resp = api_admin.post(f"/api/v1/clientes/hijos/{hijo_pendiente_purga.pk}/aprobar-purga/")
        assert resp.status_code == 200
        hijo_pendiente_purga.refresh_from_db()
        assert hijo_pendiente_purga.datos_purgados is True

    def test_cajero_no_puede_aprobar(self, api_cajero, hijo_pendiente_purga):
        resp = api_cajero.post(f"/api/v1/clientes/hijos/{hijo_pendiente_purga.pk}/aprobar-purga/")
        assert resp.status_code == 403

    def test_no_pendiente_devuelve_400(self, api_admin, hijo_sin_foto):
        resp = api_admin.post(f"/api/v1/clientes/hijos/{hijo_sin_foto.pk}/aprobar-purga/")
        assert resp.status_code == 400

    def test_ya_purgado_devuelve_400(self, api_admin, hijo_pendiente_purga):
        hijo_pendiente_purga.datos_purgados = True
        hijo_pendiente_purga.save()
        resp = api_admin.post(f"/api/v1/clientes/hijos/{hijo_pendiente_purga.pk}/aprobar-purga/")
        assert resp.status_code == 400

    def test_aprobacion_queda_en_auditoria(self, api_admin, hijo_pendiente_purga):
        from apps.usuarios.models import AuditoriaOperacion
        api_admin.post(f"/api/v1/clientes/hijos/{hijo_pendiente_purga.pk}/aprobar-purga/")
        assert AuditoriaOperacion.objects.filter(operacion="PURGAR_DATOS_ALUMNO").exists()


@pytest.mark.django_db
class TestDarBajaAlumnosUltimoCurso:

    def test_da_de_baja_solo_alumnos_del_ultimo_curso(self, cliente):
        from apps.clientes.tasks import dar_baja_alumnos_ultimo_curso

        ultimo = Grado.objects.create(nombre="6to baja", nivel=6, orden=6, es_ultimo=True)
        otro = Grado.objects.create(nombre="5to baja", nivel=5, orden=5, es_ultimo=False)
        egresado = Hijo.objects.create(
            nombre="Ega", apellido="Sada", cliente_responsable=cliente, grado=ultimo, activo=True,
        )
        no_egresado = Hijo.objects.create(
            nombre="No", apellido="Ega", cliente_responsable=cliente, grado=otro, activo=True,
        )

        resultado = dar_baja_alumnos_ultimo_curso()

        egresado.refresh_from_db()
        no_egresado.refresh_from_db()
        assert egresado.activo is False
        assert egresado.fecha_baja is not None
        assert no_egresado.activo is True
        assert resultado["dados_de_baja"] == 1


@pytest.mark.django_db
class TestMarcarAlumnosPendientesPurga:

    def test_marca_alumnos_elegibles_y_notifica_admin(self, cliente, usuario_admin):
        from apps.clientes.tasks import marcar_alumnos_pendientes_purga
        from apps.notificaciones.models import Notificacion

        elegible = Hijo.objects.create(
            nombre="Vieja", apellido="Baja", cliente_responsable=cliente,
            activo=False, fecha_baja=timezone.now() - timedelta(days=400),
        )
        muy_reciente = Hijo.objects.create(
            nombre="Nueva", apellido="Baja", cliente_responsable=cliente,
            activo=False, fecha_baja=timezone.now() - timedelta(days=10),
        )

        resultado = marcar_alumnos_pendientes_purga()

        elegible.refresh_from_db()
        muy_reciente.refresh_from_db()
        assert elegible.purga_solicitada_en is not None
        assert muy_reciente.purga_solicitada_en is None
        assert resultado["marcados"] == 1
        assert Notificacion.objects.filter(
            usuario=usuario_admin, titulo__icontains="pendiente de purga",
        ).exists()

    def test_no_remarca_alumnos_ya_marcados(self, cliente):
        from apps.clientes.tasks import marcar_alumnos_pendientes_purga

        Hijo.objects.create(
            nombre="Ya", apellido="Marcada", cliente_responsable=cliente,
            activo=False, fecha_baja=timezone.now() - timedelta(days=400),
            purga_solicitada_en=timezone.now() - timedelta(days=2),
        )
        resultado = marcar_alumnos_pendientes_purga()
        assert resultado["marcados"] == 0

    def test_no_marca_ya_purgados(self, cliente):
        from apps.clientes.tasks import marcar_alumnos_pendientes_purga

        Hijo.objects.create(
            nombre="Ya", apellido="Purgada", cliente_responsable=cliente,
            activo=False, fecha_baja=timezone.now() - timedelta(days=400),
            datos_purgados=True,
        )
        resultado = marcar_alumnos_pendientes_purga()
        assert resultado["marcados"] == 0

    def test_sin_candidatos_no_falla(self, cliente):
        from apps.clientes.tasks import marcar_alumnos_pendientes_purga
        resultado = marcar_alumnos_pendientes_purga()
        assert resultado["marcados"] == 0
