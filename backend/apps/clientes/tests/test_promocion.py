"""
Promoción anual de grados: sugerencia del grado siguiente, borrador, validaciones,
aplicación (solo después del cierre lectivo), historial, egresos y reincorporaciones.
"""
import pytest
from freezegun import freeze_time
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.cierre_cuentas.models import CierreCuentaAlumno
from apps.clientes import promocion as promo
from apps.clientes.models import Grado, Hijo, HistorialGrado, PromocionAlumno, PromocionAnual
from apps.clientes.tasks import dar_baja_alumnos_ultimo_curso

D = PromocionAlumno.Decision
BASE = "/api/v1/clientes"
ANTES_DEL_CIERRE = "2026-12-10 12:00:00"
DESPUES_DEL_CIERRE = "2027-01-02 12:00:00"


def _api(usuario):
    api = APIClient()
    api.force_authenticate(user=usuario)
    return api


@pytest.fixture
def usuario_supervisor(db):
    from apps.usuarios.models import Usuario
    return Usuario.objects.create_user(
        email="sup_promo@test.com", password="test1234", nombre="Sup", apellido="Promo",
        rol=Usuario.Rol.SUPERVISOR,
    )


@pytest.fixture
def grados(db):
    """Cadena mínima: Maternal → Pre-Jardin, 3° A → 4° A, 9° A (a 1° AÑO), 3° AÑO (último)."""
    def g(nombre, nivel, orden, **kw):
        return Grado.objects.create(nombre=nombre, nivel=nivel, orden=orden, **kw)
    return {
        "maternal": g("Maternal", 1, 1),
        "prejardin": g("Pre-Jardin", 1, 2),
        "g3": g("3° Grado A", 2, 3),
        "g4": g("4° Grado A", 2, 4),
        "g9": g("9° Grado A", 3, 9),
        "a1": g("1° AÑO Contabilidad", 4, 10),
        "a2": g("2° AÑO Contabilidad", 4, 11),
        "a3": g("3° AÑO Contabilidad", 4, 12, es_ultimo=True),
        "j": g("Jardin T", 1, 3),
        "pe": g("Pre-escolar T", 1, 4),
        "g1t": g("1° Grado T", 2, 1),
        "g2e": g("2° Grado E", 2, 2),
    }


def _hijo(cliente, grado, nombre, activo=True):
    return Hijo.objects.create(
        nombre=nombre, apellido="Promo", cliente_responsable=cliente, grado=grado, activo=activo,
    )


# ── Sugerencia del grado siguiente ───────────────────────────────────────────

class TestSugerencias:
    def test_reglas_por_nombre(self, grados):
        por_nombre = {g.nombre: g for g in Grado.objects.all()}
        assert promo.sugerir_siguiente(grados["g3"], por_nombre) == ("OK", grados["g4"], "")
        assert promo.sugerir_siguiente(grados["a1"], por_nombre) == ("OK", grados["a2"], "")
        assert promo.sugerir_siguiente(grados["j"], por_nombre) == ("OK", grados["pe"], "")
        assert promo.sugerir_siguiente(grados["pe"], por_nombre) == ("OK", grados["g1t"], "")
        assert promo.sugerir_siguiente(grados["maternal"], por_nombre)[:2] == ("OK", grados["prejardin"])

    def test_casos_especiales(self, grados):
        por_nombre = {g.nombre: g for g in Grado.objects.all()}
        assert promo.sugerir_siguiente(grados["a3"], por_nombre)[0] == "EGRESA"
        assert promo.sugerir_siguiente(grados["g9"], por_nombre)[0] == "ELEGIR"
        assert promo.sugerir_siguiente(grados["prejardin"], por_nombre)[0] == "AMBIGUO"
        # 2° Grado E no tiene 3° Grado E en esta cadena.
        assert promo.sugerir_siguiente(grados["g2e"], por_nombre)[0] == "AMBIGUO"

    def test_solo_completa_lo_vacio_y_nunca_pisa(self, grados):
        grados["g3"].siguiente = grados["g9"]  # configuración manual distinta a la sugerida
        grados["g3"].save()
        resultado = promo.sugerir_siguientes()
        grados["g3"].refresh_from_db()
        grados["a1"].refresh_from_db()
        assert grados["g3"].siguiente == grados["g9"]
        assert grados["a1"].siguiente == grados["a2"]
        assert resultado["ya_configurados"] == 1
        assert {p["grado"] for p in resultado["pendientes"]} >= {"9° Grado A", "Pre-Jardin", "2° Grado E"}

    def test_vista_previa_no_guarda(self, grados):
        resultado = promo.sugerir_siguientes(aplicar=False)
        assert resultado["asignados"]
        assert not Grado.objects.filter(siguiente__isnull=False).exists()

    def test_api_solo_admin(self, grados, usuario_admin, usuario_supervisor):
        assert _api(usuario_supervisor).post(f"{BASE}/grados/sugerir-siguientes/").status_code == 403
        r = _api(usuario_admin).post(f"{BASE}/grados/sugerir-siguientes/")
        assert r.status_code == 200 and r.data["asignados"]
        assert Grado.objects.filter(siguiente__isnull=False).exists()

    def test_serializer_rechaza_siguiente_invalido(self, grados, usuario_admin):
        api = _api(usuario_admin)
        g3, g4, a3 = grados["g3"], grados["g4"], grados["a3"]
        assert api.patch(f"{BASE}/grados/{g3.pk}/", {"siguiente": g3.pk}, format="json").status_code == 400
        assert api.patch(f"{BASE}/grados/{a3.pk}/", {"siguiente": g4.pk}, format="json").status_code == 400
        r = api.patch(f"{BASE}/grados/{g3.pk}/", {"siguiente": g4.pk}, format="json")
        assert r.status_code == 200 and r.data["siguiente_nombre"] == "4° Grado A"


# ── Borrador ─────────────────────────────────────────────────────────────────

@pytest.fixture
def escenario(grados, cliente, usuario_admin):
    """3° A → 4° A, 9° A sin destino (bachillerato a elegir), 3° AÑO (último)."""
    promo.sugerir_siguientes()
    return {
        "g": grados,
        "ana": _hijo(cliente, grados["g3"], "Ana"),
        "beto": _hijo(cliente, grados["g9"], "Beto"),
        "caro": _hijo(cliente, grados["a3"], "Caro"),
        "admin": usuario_admin,
    }


class TestBorrador:
    def test_decisiones_por_defecto(self, escenario):
        promocion, creada = promo.generar_borrador(2026, escenario["admin"])
        assert creada
        lineas = {x.hijo.nombre: x for x in promocion.lineas.select_related("hijo")}
        assert lineas["Ana"].decision == D.PROMUEVE and lineas["Ana"].grado_destino == escenario["g"]["g4"]
        assert lineas["Beto"].decision == D.PROMUEVE and lineas["Beto"].grado_destino is None
        assert lineas["Caro"].decision == D.EGRESA and lineas["Caro"].grado_destino is None

    def test_solo_admin_prepara(self, escenario, usuario_supervisor):
        from rest_framework.exceptions import PermissionDenied
        with pytest.raises(PermissionDenied):
            promo.generar_borrador(2026, usuario_supervisor)

    def test_excluye_inactivos_y_sin_grado(self, escenario, cliente):
        _hijo(cliente, escenario["g"]["g3"], "Baja", activo=False)
        _hijo(cliente, None, "SinGrado")
        promocion, _ = promo.generar_borrador(2026, escenario["admin"])
        assert set(promocion.lineas.values_list("hijo__nombre", flat=True)) == {"Ana", "Beto", "Caro"}

    def test_regenerar_es_idempotente_y_no_pisa_decisiones(self, escenario, cliente):
        promocion, _ = promo.generar_borrador(2026, escenario["admin"])
        linea = promocion.lineas.get(hijo__nombre="Ana")
        promo.actualizar_linea(linea, D.REPITE)
        nuevo = _hijo(cliente, escenario["g"]["g3"], "Nuevo")
        otra, creada = promo.generar_borrador(2026, escenario["admin"])
        assert not creada and otra.pk == promocion.pk
        assert promocion.lineas.count() == 4
        assert promocion.lineas.get(hijo=nuevo).decision == D.PROMUEVE
        assert promocion.lineas.get(hijo__nombre="Ana").decision == D.REPITE

    def test_egresado_dado_de_baja_por_la_tarea_entra_como_egresa(self, escenario):
        with freeze_time("2027-01-01 05:00:00"):
            dar_baja_alumnos_ultimo_curso()
        caro = Hijo.objects.get(nombre="Caro")
        assert not caro.activo
        with freeze_time(DESPUES_DEL_CIERRE):
            promocion, _ = promo.generar_borrador(2026, escenario["admin"])
        assert promocion.lineas.get(hijo=caro).decision == D.EGRESA


# ── Validación de líneas ─────────────────────────────────────────────────────

class TestLineas:
    @pytest.fixture
    def prom(self, escenario):
        promocion, _ = promo.generar_borrador(2026, escenario["admin"])
        return promocion, escenario

    def _linea(self, prom, nombre):
        return prom[0].lineas.select_related("hijo", "grado_origen", "promocion").get(hijo__nombre=nombre)

    def test_promueve_exige_destino(self, prom):
        with pytest.raises(ValidationError):
            promo.actualizar_linea(self._linea(prom, "Beto"), D.PROMUEVE)

    def test_promueve_con_destino_elegido(self, prom):
        destino = prom[1]["g"]["a1"]
        linea = promo.actualizar_linea(self._linea(prom, "Beto"), D.PROMUEVE, destino)
        assert linea.grado_destino == destino

    def test_repite_conserva_el_grado(self, prom):
        linea = promo.actualizar_linea(self._linea(prom, "Ana"), D.REPITE)
        assert linea.grado_destino == prom[1]["g"]["g3"]

    def test_cambia_exige_grado_distinto(self, prom):
        ana = self._linea(prom, "Ana")
        with pytest.raises(ValidationError):
            promo.actualizar_linea(ana, D.CAMBIA)
        with pytest.raises(ValidationError):
            promo.actualizar_linea(ana, D.CAMBIA, prom[1]["g"]["g3"])
        assert promo.actualizar_linea(ana, D.CAMBIA, prom[1]["g"]["g4"]).decision == D.CAMBIA

    def test_egresa_solo_desde_el_ultimo_curso(self, prom):
        with pytest.raises(ValidationError):
            promo.actualizar_linea(self._linea(prom, "Ana"), D.EGRESA)
        assert promo.actualizar_linea(self._linea(prom, "Ana"), D.NO_CONTINUA).grado_destino is None

    def test_ultimo_curso_no_promueve(self, prom):
        with pytest.raises(ValidationError):
            promo.actualizar_linea(self._linea(prom, "Caro"), D.PROMUEVE, prom[1]["g"]["a1"])

    def test_decision_masiva_por_grado(self, prom, cliente):
        _hijo(cliente, prom[1]["g"]["g3"], "Otro")
        promo.refrescar(prom[0])
        resultado = promo.actualizar_grupo(prom[0], prom[1]["g"]["g3"], D.REPITE)
        assert resultado["actualizadas"] == 2 and not resultado["omitidas"]
        assert set(prom[0].lineas.filter(grado_origen=prom[1]["g"]["g3"]).values_list("decision", flat=True)) == {D.REPITE}

    def test_no_se_edita_una_promocion_aplicada(self, prom):
        PromocionAnual.objects.filter(pk=prom[0].pk).update(estado=PromocionAnual.Estado.APLICADA)
        linea = self._linea(prom, "Ana")
        linea.promocion.refresh_from_db()
        with pytest.raises(ValidationError):
            promo.actualizar_linea(linea, D.REPITE)


# ── Requisitos y aplicación ──────────────────────────────────────────────────

def _completar(promocion, escenario):
    promo.actualizar_linea(
        promocion.lineas.select_related("hijo", "grado_origen", "promocion").get(hijo__nombre="Beto"),
        D.PROMUEVE, escenario["g"]["a1"],
    )


class TestAplicar:
    def test_antes_del_cierre_solo_se_puede_preparar(self, escenario):
        with freeze_time(ANTES_DEL_CIERRE):
            promocion, _ = promo.generar_borrador(2026, escenario["admin"])
            _completar(promocion, escenario)
            req = promo.requisitos(promocion)
            assert not req["errores"] and not req["puede_aplicar"] and req["avisos"]
            with pytest.raises(ValidationError):
                promo.aplicar(promocion, escenario["admin"])
        assert Hijo.objects.get(nombre="Ana").grado == escenario["g"]["g3"]

    def test_bloquea_si_falta_destino_o_hay_activos_sin_grado(self, escenario, cliente):
        _hijo(cliente, None, "SinGrado")
        with freeze_time(DESPUES_DEL_CIERRE):
            promocion, _ = promo.generar_borrador(2026, escenario["admin"])
            req = promo.requisitos(promocion)
            assert len(req["errores"]) == 2 and not req["puede_aplicar"]
            with pytest.raises(ValidationError):
                promo.aplicar(promocion, escenario["admin"])

    def test_solo_admin_aplica(self, escenario, usuario_supervisor):
        from rest_framework.exceptions import PermissionDenied
        promocion, _ = promo.generar_borrador(2026, escenario["admin"])
        with pytest.raises(PermissionDenied):
            promo.aplicar(promocion, usuario_supervisor)

    def test_aplica_promociones_repeticiones_egresos_e_historial(self, escenario, cliente):
        g = escenario["g"]
        repite = _hijo(cliente, g["g3"], "Repite")
        sale = _hijo(cliente, g["g4"], "Sale")
        with freeze_time(DESPUES_DEL_CIERRE):
            promocion, _ = promo.generar_borrador(2026, escenario["admin"])
            _completar(promocion, escenario)
            lineas = promocion.lineas.select_related("hijo", "grado_origen", "promocion")
            promo.actualizar_linea(lineas.get(hijo=repite), D.REPITE, motivo="Reprobó matemática")
            promo.actualizar_linea(lineas.get(hijo=sale), D.NO_CONTINUA, motivo="Se muda")
            resumen = promo.aplicar(promocion, escenario["admin"])

        assert resumen[D.PROMUEVE] == 2 and resumen[D.REPITE] == 1 and resumen[D.EGRESA] == 1
        assert Hijo.objects.get(nombre="Ana").grado == g["g4"]
        assert Hijo.objects.get(nombre="Beto").grado == g["a1"]
        assert Hijo.objects.get(pk=repite.pk).grado == g["g3"]

        caro = Hijo.objects.get(nombre="Caro")
        sale.refresh_from_db()
        assert not caro.activo and caro.fecha_baja and not sale.activo and sale.fecha_baja
        assert CierreCuentaAlumno.objects.filter(hijo__in=[caro, sale], anio=2026).count() == 2

        promocion.refresh_from_db()
        assert promocion.estado == PromocionAnual.Estado.APLICADA
        assert promocion.aplicada_por == escenario["admin"] and promocion.fecha_aplicacion

        hist = HistorialGrado.objects.get(hijo__nombre="Ana")
        assert (hist.grado_anterior, hist.grado_nuevo, hist.anio_escolar) == ("3° Grado A", "4° Grado A", 2027)
        assert hist.motivo == "PROMOCION" and hist.promocion == promocion
        assert hist.usuario_registro == escenario["admin"].email
        rep = HistorialGrado.objects.get(hijo=repite)
        assert rep.motivo == "REPITE" and rep.grado_nuevo == "3° Grado A" and rep.observaciones == "Reprobó matemática"
        assert HistorialGrado.objects.get(hijo=sale).motivo == "EGRESO"

    def test_solo_se_aplica_una_vez_por_anio(self, escenario):
        with freeze_time(DESPUES_DEL_CIERRE):
            promocion, _ = promo.generar_borrador(2026, escenario["admin"])
            _completar(promocion, escenario)
            promo.aplicar(promocion, escenario["admin"])
            with pytest.raises(ValidationError):
                promo.aplicar(promocion, escenario["admin"])
            assert HistorialGrado.objects.filter(hijo__nombre="Ana").count() == 1

    def test_reincorpora_al_egresado_que_repite(self, escenario):
        with freeze_time("2027-01-01 05:00:00"):
            dar_baja_alumnos_ultimo_curso()
        caro = Hijo.objects.get(nombre="Caro")
        assert not caro.activo
        with freeze_time(DESPUES_DEL_CIERRE):
            promocion, _ = promo.generar_borrador(2026, escenario["admin"])
            _completar(promocion, escenario)
            linea = promocion.lineas.select_related("hijo", "grado_origen", "promocion").get(hijo=caro)
            promo.actualizar_linea(linea, D.REPITE)
            promo.aplicar(promocion, escenario["admin"])
        caro.refresh_from_db()
        assert caro.activo and caro.fecha_baja is None and caro.grado == escenario["g"]["a3"]

    def test_todo_o_nada(self, escenario, monkeypatch):
        """Si falla una línea a mitad de camino no queda ninguna aplicada."""
        original = promo._aplicar_linea
        llamadas = []

        def falla_en_la_segunda(*args, **kwargs):
            llamadas.append(1)
            if len(llamadas) == 2:
                raise RuntimeError("fallo simulado")
            return original(*args, **kwargs)

        monkeypatch.setattr(promo, "_aplicar_linea", falla_en_la_segunda)
        with freeze_time(DESPUES_DEL_CIERRE):
            promocion, _ = promo.generar_borrador(2026, escenario["admin"])
            _completar(promocion, escenario)
            with pytest.raises(RuntimeError):
                promo.aplicar(promocion, escenario["admin"])
        promocion.refresh_from_db()
        assert promocion.estado == PromocionAnual.Estado.BORRADOR
        assert not HistorialGrado.objects.exists()
        assert Hijo.objects.get(nombre="Ana").grado == escenario["g"]["g3"]


# ── Convivencia con la baja automática ───────────────────────────────────────

class TestBajaAutomatica:
    def test_quien_repite_o_cambia_no_es_dado_de_baja(self, escenario, cliente):
        g = escenario["g"]
        repite = _hijo(cliente, g["a3"], "Repite")
        cambia = _hijo(cliente, g["a3"], "Cambia")
        promocion, _ = promo.generar_borrador(2026, escenario["admin"])
        lineas = promocion.lineas.select_related("hijo", "grado_origen", "promocion")
        promo.actualizar_linea(lineas.get(hijo=repite), D.REPITE)
        promo.actualizar_linea(lineas.get(hijo=cambia), D.CAMBIA, g["a2"])
        with freeze_time("2027-01-01 05:00:00"):
            dar_baja_alumnos_ultimo_curso()
        assert Hijo.objects.get(pk=repite.pk).activo and Hijo.objects.get(pk=cambia.pk).activo
        assert not Hijo.objects.get(nombre="Caro").activo

    def test_sin_borrador_todo_el_ultimo_curso_egresa(self, escenario):
        with freeze_time("2027-01-01 05:00:00"):
            dar_baja_alumnos_ultimo_curso()
        assert not Hijo.objects.get(nombre="Caro").activo

    def test_no_abre_cierre_a_quien_repite(self, escenario, cliente):
        from apps.cierre_cuentas.services import CierreCuentaService
        repite = _hijo(cliente, escenario["g"]["a3"], "Repite")
        promocion, _ = promo.generar_borrador(2026, escenario["admin"])
        promo.actualizar_linea(
            promocion.lineas.select_related("hijo", "grado_origen", "promocion").get(hijo=repite), D.REPITE,
        )
        CierreCuentaService.abrir_masivo(2026, escenario["admin"])
        assert not CierreCuentaAlumno.objects.filter(hijo=repite).exists()
        assert CierreCuentaAlumno.objects.filter(hijo__nombre="Caro").exists()


# ── API ──────────────────────────────────────────────────────────────────────

class TestApi:
    def test_permisos(self, escenario, usuario_supervisor, usuario_cajero):
        for usuario in (usuario_supervisor, usuario_cajero):
            api = _api(usuario)
            assert api.get(f"{BASE}/promociones/").status_code == 403
            assert api.post(f"{BASE}/promociones/", {"anio": 2026}, format="json").status_code == 403

    def test_flujo_completo(self, escenario):
        api = _api(escenario["admin"])
        g = escenario["g"]
        with freeze_time(DESPUES_DEL_CIERRE):
            r = api.post(f"{BASE}/promociones/", {"anio": 2026}, format="json")
            assert r.status_code == 201 and len(r.data["lineas"]) == 3
            pid = r.data["id_promocion"]
            assert not r.data["requisitos"]["puede_aplicar"]  # Beto sin bachillerato
            beto = next(x for x in r.data["lineas"] if x["hijo_nombre"].startswith("Beto"))

            r = api.patch(
                f"{BASE}/promociones/{pid}/lineas/{beto['id_promocion_alumno']}/",
                {"decision": "PROMUEVE", "grado_destino": g["a1"].pk}, format="json",
            )
            assert r.status_code == 200 and r.data["requisitos"]["puede_aplicar"]

            r = api.patch(
                f"{BASE}/promociones/{pid}/lineas/{beto['id_promocion_alumno']}/",
                {"decision": "EGRESA"}, format="json",
            )
            assert r.status_code == 400
            api.patch(
                f"{BASE}/promociones/{pid}/lineas/{beto['id_promocion_alumno']}/",
                {"decision": "PROMUEVE", "grado_destino": g["a1"].pk}, format="json",
            )

            r = api.post(f"{BASE}/promociones/{pid}/lineas-masivas/",
                         {"grado_origen": g["g3"].pk, "decision": "REPITE"}, format="json")
            assert r.status_code == 200 and r.data["resultado"]["actualizadas"] == 1

            r = api.post(f"{BASE}/promociones/{pid}/aplicar/")
            assert r.status_code == 200 and r.data["estado"] == "APLICADA"
            assert api.post(f"{BASE}/promociones/{pid}/aplicar/").status_code == 400
            assert api.delete(f"{BASE}/promociones/{pid}/").status_code == 400

    def test_descartar_borrador(self, escenario):
        api = _api(escenario["admin"])
        pid = api.post(f"{BASE}/promociones/", {"anio": 2026}, format="json").data["id_promocion"]
        assert api.delete(f"{BASE}/promociones/{pid}/").status_code == 204
        assert not PromocionAnual.objects.exists()
        assert not PromocionAlumno.objects.exists()

    def test_linea_inexistente(self, escenario):
        api = _api(escenario["admin"])
        pid = api.post(f"{BASE}/promociones/", {"anio": 2026}, format="json").data["id_promocion"]
        r = api.patch(f"{BASE}/promociones/{pid}/lineas/999999/", {"decision": "REPITE"}, format="json")
        assert r.status_code == 404

    def test_refrescar_agrega_alumnos_nuevos(self, escenario, cliente):
        api = _api(escenario["admin"])
        pid = api.post(f"{BASE}/promociones/", {"anio": 2026}, format="json").data["id_promocion"]
        _hijo(cliente, escenario["g"]["g3"], "Nuevo")
        r = api.post(f"{BASE}/promociones/{pid}/refrescar/")
        assert r.status_code == 200 and r.data["agregados"] == 1 and len(r.data["lineas"]) == 4
