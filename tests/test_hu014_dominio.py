from datetime import date

import pytest
from pydantic import ValidationError

from domain.agenda_domain import (
    GenerarAgendaRequest,
    fecha_publicacion,
    fechas_del_rango,
    generar_franjas_dia,
    hay_solapamiento,
    intersectar,
    minutos_a_hora,
    unir_contiguos,
)

H = 60  # minutos por hora


def test_bloque_de_4_horas_no_lleva_descanso():
    franjas = generar_franjas_dia([(14 * H, 18 * H)], 20)
    assert len(franjas) == 12
    assert franjas[0] == (14 * H, 14 * H + 20)
    assert franjas[-1][1] == 18 * H


def test_rn24_descanso_de_30_min_cada_4_horas():
    # 07:00-12:00 con franjas de 20 min: 12 franjas hasta 11:00,
    # descanso 11:00-11:30 y una franja final 11:30-11:50
    franjas = generar_franjas_dia([(7 * H, 12 * H)], 20)
    assert len(franjas) == 13
    assert franjas[11][1] == 11 * H  # termina la 12.ª franja a las 11:00
    assert franjas[12] == (11 * H + 30, 11 * H + 50)  # sigue tras el descanso


def test_no_se_crea_descanso_al_final_del_turno():
    franjas = generar_franjas_dia([(8 * H, 12 * H)], 30)
    assert len(franjas) == 8
    assert franjas[-1][1] == 12 * H


def test_el_descanso_se_reinicia_entre_turnos():
    franjas = generar_franjas_dia([(7 * H, 11 * H), (13 * H, 17 * H)], 30)
    assert len(franjas) == 16  # 8 + 8, sin descansos


def test_solo_se_crean_franjas_completas():
    # 50 minutos con franjas de 20: caben 2 completas (40 min)
    assert len(generar_franjas_dia([(8 * H, 8 * H + 50)], 20)) == 2


def test_turno_mas_corto_que_la_franja_no_genera_nada():
    assert generar_franjas_dia([(8 * H, 8 * H + 10)], 20) == []


def test_no_hay_franjas_solapadas_entre_si():
    franjas = generar_franjas_dia([(6 * H, 20 * H)], 20)
    for (_, fin_a), (inicio_b, _) in zip(franjas, franjas[1:]):
        assert inicio_b >= fin_a


def test_unir_contiguos():
    assert unir_contiguos([(6 * H, 12 * H), (12 * H, 19 * H)]) == [(6 * H, 19 * H)]
    assert unir_contiguos([(6 * H, 12 * H), (13 * H, 19 * H)]) == [
        (6 * H, 12 * H),
        (13 * H, 19 * H),
    ]


def test_intersectar_con_horario_de_la_sede():
    ventana = (6 * H, 20 * H)
    assert intersectar([(5 * H, 8 * H)], ventana) == [(6 * H, 8 * H)]
    assert intersectar([(19 * H, 22 * H)], ventana) == [(19 * H, 20 * H)]
    assert intersectar([(21 * H, 22 * H)], ventana) == []
    assert intersectar([(8 * H, 9 * H)], None) == []  # sede cerrada ese día


def test_hay_solapamiento():
    existentes = [(8 * H, 9 * H)]
    assert hay_solapamiento([(8 * H + 30, 9 * H + 30)], existentes)
    assert not hay_solapamiento([(9 * H, 10 * H)], existentes)  # se tocan, no se pisan
    assert not hay_solapamiento([(7 * H, 8 * H)], existentes)


def test_fechas_del_rango_es_inclusivo():
    dias = list(fechas_del_rango(date(2026, 11, 15), date(2026, 11, 30)))
    assert len(dias) == 16
    assert dias[0] == date(2026, 11, 15) and dias[-1] == date(2026, 11, 30)


def test_rn25_publicacion_15_dias_antes():
    assert fecha_publicacion(date(2026, 11, 30)) == date(2026, 11, 15)


def test_minutos_a_hora():
    assert minutos_a_hora(7 * H) == "07:00"
    assert minutos_a_hora(11 * H + 50) == "11:50"


def _req(**cambios):
    datos = {
        "profesional_id": "x",
        "sede_id": 3,
        "especialidad_id": 4,
        "fecha_inicio": "2026-11-15",
        "fecha_fin": "2026-11-30",
    }
    datos.update(cambios)
    return GenerarAgendaRequest(**datos)


def test_request_valido():
    assert _req().fecha_fin == date(2026, 11, 30)


def test_request_fecha_fin_anterior():
    with pytest.raises(ValidationError, match="anterior a la fecha de inicio"):
        _req(fecha_fin="2026-11-01")


def test_request_rango_demasiado_grande():
    with pytest.raises(ValidationError, match="90 días"):
        _req(fecha_fin="2027-06-01")


def test_request_un_solo_dia_es_valido():
    assert _req(fecha_fin="2026-11-15")
