"""
Fase 2 — calendario lectivo y vigencia derivada.

Reglas:
- Cursos normales: la tarjeta no vence.
- Último curso: opera hasta el cierre del año lectivo (por defecto 31/12); desde
  la fecha de aviso (por defecto 01/10) se avisa saldos y deudas.
- Alumno dado de baja: no opera ni recibe recargas.
- Fecha de vencimiento manual (excepción): vence al final del día; sigue pudiendo
  recargarse.
"""
from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient


def _api(usuario):
    api = APIClient()
    api.force_authenticate(user=usuario)
    return api


@pytest.fixture
def grado_normal(db):
    from apps.clientes.models import Grado
    return Grado.objects.create(nombre="5° Grado V", nivel=3, orden=10, es_ultimo=False)


@pytest.fixture
def grado_ultimo(db):
    from apps.clientes.models import Grado
    return Grado.objects.create(nombre="3° AÑO V", nivel=5, orden=33, es_ultimo=True)


def _hijo(cliente, grado, nombre="Alu", activo=True):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre=nombre, apellido="Vigencia", cliente_responsable=cliente, grado=grado, activo=activo,
    )


def _tarjeta(hijo, nro, vencimiento=None, saldo=0):
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(
        nro_tarjeta=nro, hijo=hijo, fecha_vencimiento=vencimiento, saldo_actual=Decimal(saldo),
        permite_saldo_negativo=True,
    )


@pytest.mark.django_db
class TestEvaluarHijo:

    def test_curso_normal_no_vence(self, cliente, grado_normal):
        from apps.clientes.vigencia import evaluar_hijo
        h = _hijo(cliente, grado_normal)
        for dia in (date(2026, 3, 1), date(2026, 10, 15), date(2026, 12, 31), date(2027, 1, 5)):
            e = evaluar_hijo(h, hoy=dia)
            assert e.operativa and e.puede_recargar and e.aviso is None

    def test_alumno_dado_de_baja_no_opera_ni_recarga(self, cliente, grado_normal):
        from apps.clientes.vigencia import evaluar_hijo
        e = evaluar_hijo(_hijo(cliente, grado_normal, activo=False), hoy=date(2026, 5, 1))
        assert not e.operativa and not e.puede_recargar
        assert "dado de baja" in e.motivo

    def test_ultimo_curso_antes_del_aviso_sin_avisos(self, cliente, grado_ultimo):
        from apps.clientes.vigencia import evaluar_hijo
        e = evaluar_hijo(_hijo(cliente, grado_ultimo), hoy=date(2026, 9, 30))
        assert e.operativa and e.aviso is None

    def test_ultimo_curso_desde_el_aviso_opera_y_avisa(self, cliente, grado_ultimo):
        from apps.clientes.vigencia import evaluar_hijo
        e = evaluar_hijo(_hijo(cliente, grado_ultimo), hoy=date(2026, 10, 1))
        assert e.operativa and e.puede_recargar
        assert "31/12/2026" in e.aviso
        assert e.fecha_cierre == date(2026, 12, 31)

    def test_ultimo_curso_opera_hasta_el_ultimo_dia(self, cliente, grado_ultimo):
        from apps.clientes.vigencia import evaluar_hijo
        assert evaluar_hijo(_hijo(cliente, grado_ultimo), hoy=date(2026, 12, 31)).operativa

    def test_cierre_configurado_antes_del_31_12(self, cliente, grado_ultimo):
        from apps.clientes.models import CalendarioLectivo
        from apps.clientes.vigencia import evaluar_hijo
        CalendarioLectivo.objects.create(
            anio=2026, fecha_aviso_ultimo_curso=date(2026, 9, 15), fecha_cierre_lectivo=date(2026, 11, 20),
        )
        h = _hijo(cliente, grado_ultimo)
        assert evaluar_hijo(h, hoy=date(2026, 11, 20)).operativa
        e = evaluar_hijo(h, hoy=date(2026, 11, 21))
        assert not e.operativa and not e.puede_recargar
        assert "20/11/2026" in e.motivo
        assert "15/09/2026" not in (evaluar_hijo(h, hoy=date(2026, 9, 14)).aviso or "")
        assert evaluar_hijo(h, hoy=date(2026, 9, 15)).aviso is not None


@pytest.mark.django_db
class TestEvaluarTarjeta:

    def test_sin_vencimiento_vigente(self, cliente, grado_normal):
        from apps.clientes.vigencia import evaluar_tarjeta
        t = _tarjeta(_hijo(cliente, grado_normal), "V-1")
        assert evaluar_tarjeta(t, hoy=date(2030, 1, 1)).operativa

    def test_vence_al_final_del_dia_indicado(self, cliente, grado_normal):
        from apps.clientes.vigencia import evaluar_tarjeta
        t = _tarjeta(_hijo(cliente, grado_normal), "V-2", vencimiento=date(2026, 11, 30))
        assert evaluar_tarjeta(t, hoy=date(2026, 11, 30)).operativa
        e = evaluar_tarjeta(t, hoy=date(2026, 12, 1))
        assert not e.operativa and "30/11/2026" in e.motivo

    def test_vencida_por_fecha_puede_seguir_recibiendo_recargas(self, cliente, grado_normal):
        from apps.clientes.vigencia import evaluar_tarjeta
        t = _tarjeta(_hijo(cliente, grado_normal), "V-3", vencimiento=date(2026, 11, 30))
        e = evaluar_tarjeta(t, hoy=date(2026, 12, 15))
        assert not e.operativa and e.puede_recargar

    def test_aviso_de_vencimiento_proximo(self, cliente, grado_normal):
        from apps.clientes.vigencia import evaluar_tarjeta
        t = _tarjeta(_hijo(cliente, grado_normal), "V-4", vencimiento=date(2026, 11, 30))
        assert "en 30 días" in evaluar_tarjeta(t, hoy=date(2026, 10, 31)).aviso
        assert evaluar_tarjeta(t, hoy=date(2026, 10, 30)).aviso is None

    def test_la_baja_del_alumno_manda_sobre_el_vencimiento(self, cliente, grado_normal):
        from apps.clientes.vigencia import evaluar_tarjeta
        t = _tarjeta(_hijo(cliente, grado_normal, activo=False), "V-5", vencimiento=date(2030, 1, 1))
        e = evaluar_tarjeta(t, hoy=date(2026, 6, 1))
        assert not e.operativa and not e.puede_recargar

    def test_tarjeta_de_docente_sin_alumno(self, cliente):
        from apps.core.models import Tarjeta
        from apps.clientes.vigencia import evaluar_tarjeta
        t = Tarjeta.objects.create(nro_tarjeta="V-DOC", cliente_directo=cliente)
        assert evaluar_tarjeta(t, hoy=date(2026, 6, 1)).operativa


@pytest.mark.django_db
class TestBloqueosEnLosFlujos:

    def _vender(self, cliente, cajero, producto, tarjeta):
        from apps.ventas.services import VentaService
        return VentaService.registrar_venta(
            cliente=cliente, cajero=cajero, tipo="CONTADO", tarjeta=tarjeta,
            items=[{"producto": producto, "cantidad": Decimal("1")}],
        )

    def test_venta_rechazada_si_el_alumno_esta_de_baja(
        self, cliente, usuario_cajero, producto, stock_producto, grado_normal,
    ):
        t = _tarjeta(_hijo(cliente, grado_normal, activo=False), "B-1")
        with pytest.raises(ValidationError, match="dado de baja"):
            self._vender(cliente, usuario_cajero, producto, t)

    def test_venta_rechazada_con_la_tarjeta_vencida(
        self, cliente, usuario_cajero, producto, stock_producto, grado_normal,
    ):
        t = _tarjeta(_hijo(cliente, grado_normal), "B-2", vencimiento=date(2020, 1, 1))
        with pytest.raises(ValidationError, match="vencida el 01/01/2020"):
            self._vender(cliente, usuario_cajero, producto, t)

    def test_venta_normal_sigue_funcionando(
        self, cliente, usuario_cajero, producto, stock_producto, grado_normal,
    ):
        t = _tarjeta(_hijo(cliente, grado_normal), "B-3")
        assert self._vender(cliente, usuario_cajero, producto, t) is not None

    @freeze_time("2026-12-31 15:00:00")
    def test_venta_del_ultimo_curso_el_ultimo_dia_funciona(
        self, cliente, usuario_cajero, producto, stock_producto, grado_ultimo,
    ):
        t = _tarjeta(_hijo(cliente, grado_ultimo), "B-4")
        assert self._vender(cliente, usuario_cajero, producto, t) is not None

    def test_el_comedor_rechaza_a_un_alumno_de_baja(self, cliente, usuario_cajero, grado_normal):
        from apps.almuerzos.services import AlmuerzoService
        h = _hijo(cliente, grado_normal, activo=False)
        t = _tarjeta(h, "B-5")
        with pytest.raises(ValidationError, match="dado de baja"):
            AlmuerzoService.registrar_consumo(
                hijo=h, fecha_consumo=date.today(), nro_tarjeta=t, registrado_por=usuario_cajero,
            )

    def test_recarga_de_caja_rechazada_para_alumno_de_baja(self, cliente, usuario_cajero, grado_normal):
        t = _tarjeta(_hijo(cliente, grado_normal, activo=False), "B-6")
        resp = _api(usuario_cajero).post(
            "/api/v1/core/cargas-saldo/",
            {"tarjeta": t.nro_tarjeta, "monto_cargado": 20000, "metodo_pago": "TRANSFERENCIA"},
            format="json",
        )
        assert resp.status_code == 400
        assert "dado de baja" in str(resp.data)

    def test_recarga_de_almuerzo_rechazada_para_alumno_de_baja(self, cliente, usuario_cajero, grado_normal):
        h = _hijo(cliente, grado_normal, activo=False)
        resp = _api(usuario_cajero).post(
            "/api/v1/almuerzos/recargas-saldo/",
            {"hijo": h.pk, "monto_cargado": 20000, "metodo_pago": "TRANSFERENCIA"},
            format="json",
        )
        assert resp.status_code == 400
        assert "dado de baja" in str(resp.data)

    def test_recarga_permitida_con_la_tarjeta_vencida_por_fecha(self, cliente, usuario_cajero, grado_normal):
        t = _tarjeta(_hijo(cliente, grado_normal), "B-7", vencimiento=date(2020, 1, 1))
        resp = _api(usuario_cajero).post(
            "/api/v1/core/cargas-saldo/",
            {"tarjeta": t.nro_tarjeta, "monto_cargado": 20000, "metodo_pago": "TRANSFERENCIA"},
            format="json",
        )
        assert resp.status_code == 201

    def test_el_padre_no_puede_iniciar_un_pago_para_un_alumno_de_baja(self, cliente, grado_normal):
        from apps.usuarios.models import Usuario
        t = _tarjeta(_hijo(cliente, grado_normal, activo=False), "B-8")
        padre = Usuario.objects.create_user(
            email="padre_vig@test.com", password="x12345678", nombre="P", apellido="V",
            rol=Usuario.Rol.CLIENTE_WEB, cliente=cliente,
        )
        resp = _api(padre).post(
            "/api/v1/core/bancard/iniciar/", {"nro_tarjeta": t.nro_tarjeta, "monto": 50000}, format="json",
        )
        assert resp.status_code == 400
        assert "dado de baja" in str(resp.data)


@pytest.mark.django_db
class TestCampoVigenciaEnLaTarjeta:

    @freeze_time("2026-10-10 15:00:00")
    def test_serializa_el_estado_y_el_aviso(self, cliente, grado_ultimo):
        from apps.core.serializers import TarjetaSerializer
        t = _tarjeta(_hijo(cliente, grado_ultimo), "S-1")
        v = TarjetaSerializer(t).data["vigencia"]
        assert v["operativa"] is True and "31/12/2026" in v["aviso"]
        assert v["fecha_cierre"] == "2026-12-31"


@pytest.mark.django_db
class TestCalendarioLectivoApi:

    URL = "/api/v1/clientes/calendarios-lectivos/"

    def _payload(self, **kw):
        base = {"anio": 2027, "fecha_aviso_ultimo_curso": "2027-10-01", "fecha_cierre_lectivo": "2027-12-31"}
        base.update(kw)
        return base

    def test_admin_crea_y_edita(self, usuario_admin):
        api = _api(usuario_admin)
        r = api.post(self.URL, self._payload(), format="json")
        assert r.status_code == 201
        r2 = api.patch(f"{self.URL}{r.data['id_calendario']}/", {"fecha_cierre_lectivo": "2027-12-15"}, format="json")
        assert r2.status_code == 200 and r2.data["fecha_cierre_lectivo"] == "2027-12-15"

    def test_el_aviso_debe_ser_anterior_al_cierre(self, usuario_admin):
        r = _api(usuario_admin).post(
            self.URL, self._payload(fecha_aviso_ultimo_curso="2027-12-31"), format="json",
        )
        assert r.status_code == 400

    def test_las_fechas_deben_estar_en_el_anio(self, usuario_admin):
        r = _api(usuario_admin).post(
            self.URL, self._payload(fecha_cierre_lectivo="2028-01-10"), format="json",
        )
        assert r.status_code == 400

    def test_solo_admin_escribe(self, usuario_cajero):
        assert _api(usuario_cajero).post(self.URL, self._payload(), format="json").status_code == 403

    def test_no_se_puede_borrar(self, usuario_admin):
        api = _api(usuario_admin)
        cal = api.post(self.URL, self._payload(), format="json").data
        assert api.delete(f"{self.URL}{cal['id_calendario']}/").status_code == 405

    def test_actual_devuelve_los_valores_por_defecto_si_no_hay_fila(self, usuario_cajero):
        with freeze_time("2026-06-01 12:00:00"):
            r = _api(usuario_cajero).get(f"{self.URL}actual/")
        assert r.status_code == 200
        assert r.data["configurado"] is False
        assert r.data["fecha_aviso_ultimo_curso"] == "2026-10-01"
        assert r.data["fecha_cierre_lectivo"] == "2026-12-31"

    def test_el_padre_no_accede(self, cliente):
        from apps.usuarios.models import Usuario
        padre = Usuario.objects.create_user(
            email="padre_cal@test.com", password="x12345678", nombre="P", apellido="C",
            rol=Usuario.Rol.CLIENTE_WEB, cliente=cliente,
        )
        assert _api(padre).get(self.URL).status_code == 403
        assert _api(padre).get(f"{self.URL}actual/").status_code == 403

    def test_cambios_quedan_auditados(self, usuario_admin):
        from apps.usuarios.models import AuditoriaOperacion
        _api(usuario_admin).post(self.URL, self._payload(), format="json")
        assert AuditoriaOperacion.objects.filter(operacion="CREAR_CALENDARIO_LECTIVO").exists()


# ── Tareas ───────────────────────────────────────────────────────────────────

def _con_saldos(hijo, cantina=0, almuerzo=0):
    from apps.almuerzos.models import SaldoAlmuerzo
    from apps.core.models import Tarjeta
    Tarjeta.objects.filter(hijo=hijo).update(saldo_actual=Decimal(cantina))
    if almuerzo:
        SaldoAlmuerzo.objects.update_or_create(hijo=hijo, defaults={"saldo_actual": Decimal(almuerzo)})


@pytest.mark.django_db
class TestBajaDelUltimoCurso:

    def test_no_da_de_baja_antes_del_cierre(self, cliente, grado_ultimo):
        from apps.clientes.tasks import dar_baja_alumnos_ultimo_curso
        h = _hijo(cliente, grado_ultimo)
        with freeze_time("2026-12-31 15:00:00"):
            assert dar_baja_alumnos_ultimo_curso() == {"dados_de_baja": 0}
        h.refresh_from_db()
        assert h.activo is True

    def test_da_de_baja_al_pasar_el_cierre_solo_al_ultimo_curso(self, cliente, grado_ultimo, grado_normal):
        from apps.clientes.tasks import dar_baja_alumnos_ultimo_curso
        egresado = _hijo(cliente, grado_ultimo, "Egresa")
        sigue = _hijo(cliente, grado_normal, "Sigue")
        with freeze_time("2027-01-01 08:00:00"):
            assert dar_baja_alumnos_ultimo_curso() == {"dados_de_baja": 1}
        egresado.refresh_from_db(); sigue.refresh_from_db()
        assert egresado.activo is False and egresado.fecha_baja is not None
        assert sigue.activo is True

    def test_una_sola_vez_por_anio(self, cliente, grado_ultimo):
        from apps.clientes.models import CalendarioLectivo
        from apps.clientes.tasks import dar_baja_alumnos_ultimo_curso
        _hijo(cliente, grado_ultimo, "Uno")
        with freeze_time("2027-01-01 08:00:00"):
            dar_baja_alumnos_ultimo_curso()
        assert CalendarioLectivo.objects.get(anio=2026).baja_ultimo_curso_aplicada is True
        # Una nueva cohorte llega al último grado en enero: no debe recibir la baja del año anterior.
        nuevo = _hijo(cliente, grado_ultimo, "Cohorte nueva")
        with freeze_time("2027-01-15 08:00:00"):
            assert dar_baja_alumnos_ultimo_curso() == {"dados_de_baja": 0}
        nuevo.refresh_from_db()
        assert nuevo.activo is True

    def test_no_aplica_un_cierre_muy_atrasado(self, cliente, grado_ultimo):
        from apps.clientes.tasks import dar_baja_alumnos_ultimo_curso
        h = _hijo(cliente, grado_ultimo)
        with freeze_time("2027-03-15 08:00:00"):
            assert dar_baja_alumnos_ultimo_curso() == {"dados_de_baja": 0}
        h.refresh_from_db()
        assert h.activo is True

    def test_respeta_un_cierre_configurado_antes(self, cliente, grado_ultimo):
        from apps.clientes.models import CalendarioLectivo
        from apps.clientes.tasks import dar_baja_alumnos_ultimo_curso
        CalendarioLectivo.objects.create(
            anio=2026, fecha_aviso_ultimo_curso=date(2026, 9, 1), fecha_cierre_lectivo=date(2026, 11, 20),
        )
        h = _hijo(cliente, grado_ultimo)
        with freeze_time("2026-11-21 08:00:00"):
            assert dar_baja_alumnos_ultimo_curso() == {"dados_de_baja": 1}
        h.refresh_from_db()
        assert h.activo is False

    def test_avisa_a_los_admin_los_saldos_pendientes_sin_tocarlos(self, cliente, grado_ultimo, usuario_admin):
        from apps.clientes.tasks import dar_baja_alumnos_ultimo_curso
        from apps.core.models import Tarjeta
        from apps.notificaciones.models import Notificacion
        h = _hijo(cliente, grado_ultimo, "Deudor")
        _tarjeta(h, "BJ-1")
        _con_saldos(h, cantina=-30000, almuerzo=50000)
        with freeze_time("2027-01-01 08:00:00"):
            dar_baja_alumnos_ultimo_curso()
        n = Notificacion.objects.get(usuario=usuario_admin)
        assert "Deudor" in n.mensaje and "30,000 en deuda" in n.mensaje and "50,000 a favor" in n.mensaje
        assert Tarjeta.objects.get(nro_tarjeta="BJ-1").saldo_actual == Decimal("-30000")

    def test_sin_saldos_no_notifica(self, cliente, grado_ultimo, usuario_admin):
        from apps.clientes.tasks import dar_baja_alumnos_ultimo_curso
        from apps.notificaciones.models import Notificacion
        _hijo(cliente, grado_ultimo)
        with freeze_time("2027-01-01 08:00:00"):
            dar_baja_alumnos_ultimo_curso()
        assert not Notificacion.objects.filter(usuario=usuario_admin).exists()


@pytest.mark.django_db
class TestAvisoDeCierre:

    @pytest.fixture
    def escenario(self, cliente, grado_ultimo, usuario_admin, usuario_cajero):
        from apps.usuarios.models import Usuario
        padre = Usuario.objects.create_user(
            email="padre_aviso@test.com", password="x12345678", nombre="P", apellido="A",
            rol=Usuario.Rol.CLIENTE_WEB, cliente=cliente,
        )
        h = _hijo(cliente, grado_ultimo, "Ultimo")
        _tarjeta(h, "AV-1")
        _con_saldos(h, cantina=-15000, almuerzo=40000)
        return {"padre": padre, "hijo": h}

    def test_fuera_del_periodo_no_avisa(self, escenario):
        from apps.clientes.tasks import avisar_cierre_ultimo_curso
        with freeze_time("2026-09-30 12:00:00"):
            assert avisar_cierre_ultimo_curso()["avisados"] == 0
        with freeze_time("2027-01-02 12:00:00"):
            assert avisar_cierre_ultimo_curso()["avisados"] == 0

    def test_el_dia_del_aviso_notifica_al_padre_y_al_personal(self, escenario, usuario_admin, usuario_cajero):
        from apps.clientes.tasks import avisar_cierre_ultimo_curso
        from apps.notificaciones.models import Notificacion
        with freeze_time("2026-10-01 12:00:00"):
            assert avisar_cierre_ultimo_curso() == {"avisados": 1}
        n_padre = Notificacion.objects.get(usuario=escenario["padre"])
        assert "31/12/2026" in n_padre.mensaje
        assert "15,000 en deuda" in n_padre.mensaje and "40,000 a favor" in n_padre.mensaje
        for staff in (usuario_admin, usuario_cajero):
            resumen = Notificacion.objects.get(usuario=staff)
            assert "Deuda total Gs. 15,000" in resumen.mensaje and "a favor Gs. 40,000" in resumen.mensaje

    def test_avisa_una_vez_por_semana(self, escenario):
        from apps.clientes.tasks import avisar_cierre_ultimo_curso
        with freeze_time("2026-10-02 12:00:00"):
            assert avisar_cierre_ultimo_curso()["avisados"] == 0
        with freeze_time("2026-10-08 12:00:00"):
            assert avisar_cierre_ultimo_curso()["avisados"] == 1

    def test_no_avisa_a_alumnos_sin_saldo_ni_a_cursos_normales(self, cliente, grado_ultimo, grado_normal):
        from apps.clientes.tasks import avisar_cierre_ultimo_curso
        _hijo(cliente, grado_ultimo, "SinSaldo")
        normal = _hijo(cliente, grado_normal, "Normal")
        _tarjeta(normal, "AV-N")
        _con_saldos(normal, cantina=-99999)
        with freeze_time("2026-10-01 12:00:00"):
            assert avisar_cierre_ultimo_curso()["avisados"] == 0

    def test_los_alumnos_siguen_operando_mientras_tanto(self, escenario):
        from apps.clientes.vigencia import evaluar_hijo
        assert evaluar_hijo(escenario["hijo"], hoy=date(2026, 10, 15)).operativa

    def test_estan_registradas_en_el_beat(self):
        from backend.celery_app import app
        tareas = {v["task"]: v["schedule"] for v in app.conf.beat_schedule.values()}
        assert "apps.clientes.tasks.avisar_cierre_ultimo_curso" in tareas
        assert "apps.clientes.tasks.dar_baja_alumnos_ultimo_curso" in tareas
