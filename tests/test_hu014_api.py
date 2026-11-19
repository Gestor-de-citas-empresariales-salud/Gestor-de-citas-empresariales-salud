import pytest
from fastapi.testclient import TestClient

from api.agenda_router import get_agenda_service
from main import app
from repository.agenda_repository import AgendaRepository
from repository.profesional_repository import ProfesionalRepository
from service.agenda_service import AgendaService, SedeAgendaLocal

PROFESIONAL_ID = "7d2e9a40-1c11-4a3e-8f55-0e2b7c6d1a22"  # especialidad 4
HEADERS = {"Authorization": "Bearer token-de-prueba"}
HEADERS_SIN_PERMISO = {"Authorization": "Bearer token_sin_permiso"}
URL = "/api/v1/agendas/generar"

JORNADA_LUNES = [
    {"dia_semana": 1, "hora_inicio": "07:00", "hora_fin": "12:00"},
    {"dia_semana": 1, "hora_inicio": "14:00", "hora_fin": "18:00"},
]

BODY = {
    "profesional_id": PROFESIONAL_ID,
    "sede_id": 3,
    "especialidad_id": 4,
    "fecha_inicio": "2026-11-15",
    "fecha_fin": "2026-11-30",
}


@pytest.fixture
def servicio():
    return AgendaService(
        profesional_repo=ProfesionalRepository(),
        sede_repo=SedeAgendaLocal(),
        agenda_repo=AgendaRepository(),
    )


@pytest.fixture
def client(servicio):
    app.dependency_overrides[get_agenda_service] = lambda: servicio
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def listo(client, servicio):
    servicio.sede_repo.asignar_sede(PROFESIONAL_ID, 3)
    servicio.sede_repo.guardar_jornada(PROFESIONAL_ID, JORNADA_LUNES)
    return client


def generar(client, headers=HEADERS, **cambios):
    return client.post(URL, json={**BODY, **cambios}, headers=headers)


# ---------- Caso 1: éxito ----------
def test_caso1_generar_agenda_exitoso(listo):
    r = generar(listo)
    assert r.status_code == 201
    body = r.json()
    assert body["success"] is True
    assert "Operación exitosa" in body["mensaje"]
    assert body["data"]["profesional_id"] == PROFESIONAL_ID
    assert body["data"]["total_espacios_generados"] == 75


@pytest.mark.parametrize("sede_id", [1, 2, 3])
def test_tres_sedes_disponibles(client, servicio, sede_id):
    servicio.sede_repo.asignar_sede(PROFESIONAL_ID, sede_id)
    servicio.sede_repo.guardar_jornada(PROFESIONAL_ID, JORNADA_LUNES)
    r = generar(client, sede_id=sede_id, fecha_inicio="2026-11-16", fecha_fin="2026-11-16")
    assert r.status_code == 201
    assert r.json()["data"]["total_espacios_generados"] == 25


def test_franjas_con_descanso_y_publicacion(listo, servicio):
    generar(listo, fecha_inicio="2026-11-16", fecha_fin="2026-11-16")
    franjas = servicio.agenda_repo._db_franjas
    assert len(franjas) == 25
    assert all(f["estado"] == "LIBRE" for f in franjas)
    assert all(f["publicar_desde"] == "2026-11-01" for f in franjas)
    horas = [(f["hora_inicio"], f["hora_fin"]) for f in franjas]
    assert ("10:40", "11:00") in horas
    assert ("11:30", "11:50") in horas
    assert not any("11:00" <= i < "11:30" for i, _ in horas)


def test_rango_sin_dias_de_jornada_no_genera_nada(listo):
    r = generar(listo, fecha_inicio="2026-11-17", fecha_fin="2026-11-22")
    assert r.status_code == 422
    assert "no coincide con el horario de la sede" in r.json()["mensaje"]


def test_jornada_fuera_del_horario_de_la_sede(listo, servicio):
    servicio.sede_repo.guardar_jornada(
        PROFESIONAL_ID, [{"dia_semana": 7, "hora_inicio": "08:00", "hora_fin": "12:00"}]
    )
    r = generar(listo)
    assert r.status_code == 422


def test_jornada_parcialmente_fuera_del_horario_se_recorta(listo, servicio):
    servicio.sede_repo.guardar_jornada(
        PROFESIONAL_ID, [{"dia_semana": 1, "hora_inicio": "05:00", "hora_fin": "08:00"}]
    )
    r = generar(listo, fecha_inicio="2026-11-16", fecha_fin="2026-11-16")
    assert r.json()["data"]["total_espacios_generados"] == 6


def test_dos_rangos_distintos_son_validos(listo):
    assert generar(listo, fecha_inicio="2026-11-16", fecha_fin="2026-11-16").status_code == 201
    assert generar(listo, fecha_inicio="2026-11-23", fecha_fin="2026-11-23").status_code == 201


# ---------- Caso 2: datos inválidos (400) ----------
@pytest.mark.parametrize(
    "cambios",
    [
        {"fecha_inicio": "15-11-2026"},
        {"fecha_inicio": "no-es-fecha"},
        {"fecha_fin": "2026-11-01"},
        {"fecha_fin": "2027-06-01"},
        {"sede_id": 0},
        {"sede_id": "tres"},
        {"especialidad_id": -1},
        {"profesional_id": ""},
    ],
)
def test_caso2_datos_invalidos(listo, cambios):
    r = generar(listo, **cambios)
    assert r.status_code == 400
    assert r.json()["success"] is False
    assert r.json()["data"] is None


def test_caso2_campo_faltante(listo):
    cuerpo = {k: v for k, v in BODY.items() if k != "fecha_fin"}
    r = listo.post(URL, json=cuerpo, headers=HEADERS)
    assert r.status_code == 400
    assert "fecha_fin" in r.json()["mensaje"]


# ---------- Caso 3: franjas solapadas (409, RN-21) ----------
def test_caso3_franjas_solapadas_409(listo):
    assert generar(listo).status_code == 201
    r = generar(listo)
    assert r.status_code == 409
    assert r.json()["success"] is False
    assert (
        "El profesional ya tiene franjas solapadas en el rango indicado"
        in r.json()["mensaje"]
    )


def test_caso3_solapamiento_con_franjas_de_otra_sede(listo, servicio):
    servicio.sede_repo.asignar_sede(PROFESIONAL_ID, 1)
    assert generar(listo, sede_id=1).status_code == 201
    assert generar(listo, sede_id=3).status_code == 409


def test_un_409_no_inserta_franjas_parciales(listo, servicio):
    generar(listo, fecha_inicio="2026-11-23", fecha_fin="2026-11-23")
    antes = len(servicio.agenda_repo._db_franjas)
    assert generar(listo, fecha_inicio="2026-11-16", fecha_fin="2026-11-30").status_code == 409
    assert len(servicio.agenda_repo._db_franjas) == antes


# ---------- Caso 4: sin jornada (422) ----------
def test_caso4_sin_jornada_laboral_422(client, servicio):
    servicio.sede_repo.asignar_sede(PROFESIONAL_ID, 3)
    r = generar(client)
    assert r.status_code == 422
    assert r.json()["success"] is False
    assert (
        "El profesional no tiene jornada laboral configurada" in r.json()["mensaje"]
    )


def test_sin_jornada_ni_sede_sigue_siendo_el_mensaje_del_caso4(client):
    r = generar(client)
    assert r.status_code == 422
    assert "no tiene jornada laboral configurada" in r.json()["mensaje"]


# ---------- Otras validaciones ----------
def test_profesional_inexistente_404(listo):
    r = generar(listo, profesional_id="no-existe")
    assert r.status_code == 404
    assert r.json()["mensaje"] == "No se encontró el profesional indicado"


def test_sede_inexistente_404(listo):
    r = generar(listo, sede_id=999)
    assert r.status_code == 404
    assert r.json()["mensaje"] == "No se encontró la sede indicada"


def test_especialidad_que_no_corresponde_422(listo):
    r = generar(listo, especialidad_id=2)
    assert r.status_code == 422
    assert "no corresponde al profesional" in r.json()["mensaje"]


def test_profesional_no_asignado_a_la_sede_422(client, servicio):
    servicio.sede_repo.guardar_jornada(PROFESIONAL_ID, JORNADA_LUNES)
    r = generar(client)
    assert r.status_code == 422
    assert "no está asignado a la sede" in r.json()["mensaje"]


# ---------- Caso 5: autenticación y permisos ----------
def test_caso5_sin_token_401(listo):
    r = listo.post(URL, json=BODY)
    assert r.status_code == 401
    assert r.json()["success"] is False
    assert r.json()["mensaje"] == "Token de autenticación inválido o ausente"


def test_caso5_sin_permiso_403(listo):
    r = generar(listo, headers=HEADERS_SIN_PERMISO)
    assert r.status_code == 403
    assert r.json()["success"] is False
    assert r.json()["mensaje"] == "No cuenta con permisos para esta operación"


# ---------- Caso 6: falla de base de datos (503) ----------
def test_caso6_falla_externa_503(listo):
    r = generar(listo, profesional_id="falla-externa")
    assert r.status_code == 503
    assert r.json()["success"] is False
    assert "No fue posible generar la agenda" in r.json()["mensaje"]


def test_error_inesperado_se_responde_503(listo, servicio, monkeypatch):
    def falla(*args, **kwargs):
        raise RuntimeError("base de datos caída")

    monkeypatch.setattr(servicio.agenda_repo, "insertar_franjas", falla)
    r = generar(listo)
    assert r.status_code == 503
    assert "No fue posible generar la agenda" in r.json()["mensaje"]


# ---------- Documentación Swagger ----------
def test_endpoint_documentado_en_openapi(client):
    post = client.get("/openapi.json").json()["paths"]["/api/v1/agendas/generar"]["post"]
    for codigo in ("201", "400", "401", "403", "404", "409", "422", "503"):
        assert codigo in post["responses"]
    assert post["summary"]