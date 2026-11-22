# REGLAS DE NEGOCIO HU-014 (Domain Layer)
# Generar los espacios de la agenda médica

from datetime import date, timedelta
from typing import Optional

from pydantic import BaseModel, Field, model_validator

# RN-24: se inserta un descanso de 30 minutos por cada 4 horas de atención.
DESCANSO_MIN = 30
CADA_MIN_DE_ATENCION = 4 * 60

# RN-25: la agenda se publica con 15 días de anticipación.
DIAS_ANTICIPACION_PUBLICACION = 15

# Límite de seguridad para no generar rangos enormes en una sola petición.
MAX_DIAS_RANGO = 90

# Horario de atención de las sedes (minutos desde 00:00, día ISO 1=lunes ... 7=domingo).
# PROVISIONAL: aún no existe el horario por sede; todas atienden de lunes a
# sábado de 06:00 a 20:00 hasta que se defina ese módulo.
HORARIO_SEDE_POR_DEFECTO = {dia: (6 * 60, 20 * 60) for dia in range(1, 7)}


def minutos_a_hora(minutos: int) -> str:
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def hora_a_minutos(hora: str) -> int:
    horas, minutos = hora.split(":")
    return int(horas) * 60 + int(minutos)


def fechas_del_rango(fecha_inicio: date, fecha_fin: date):
    dia = fecha_inicio
    while dia <= fecha_fin:
        yield dia
        dia += timedelta(days=1)


# Une bloques que se tocan (fin de uno = inicio del siguiente): son un solo turno.
def unir_contiguos(intervalos: list) -> list:
    unidos = []
    for inicio, fin in sorted(intervalos):
        if unidos and inicio <= unidos[-1][1]:
            unidos[-1] = (unidos[-1][0], max(unidos[-1][1], fin))
        else:
            unidos.append((inicio, fin))
    return unidos


# Cruza la jornada del médico con el horario de la sede.
def intersectar(intervalos: list, ventana: Optional[tuple]) -> list:
    if ventana is None:
        return []
    resultado = []
    for inicio, fin in intervalos:
        nuevo_inicio, nuevo_fin = max(inicio, ventana[0]), min(fin, ventana[1])
        if nuevo_inicio < nuevo_fin:
            resultado.append((nuevo_inicio, nuevo_fin))
    return resultado


# Subdivide cada turno en franjas de `duracion_min` e inserta el descanso
# de RN-24 (30 min cada 4 horas de atención). Solo se crean franjas completas.
def generar_franjas_dia(intervalos: list, duracion_min: int) -> list:
    franjas = []
    for inicio, fin in intervalos:
        cursor = inicio
        atendido = 0
        while cursor + duracion_min <= fin:
            if atendido >= CADA_MIN_DE_ATENCION:
                cursor += DESCANSO_MIN
                atendido = 0
                continue
            franjas.append((cursor, cursor + duracion_min))
            cursor += duracion_min
            atendido += duracion_min
    return franjas


# RN-21: un médico no puede tener franjas solapadas.
def hay_solapamiento(nuevas: list, existentes: list) -> bool:
    for n_inicio, n_fin in nuevas:
        for e_inicio, e_fin in existentes:
            if n_inicio < e_fin and e_inicio < n_fin:
                return True
    return False


# RN-25: fecha desde la cual el espacio puede publicarse.
def fecha_publicacion(fecha: date) -> date:
    return fecha - timedelta(days=DIAS_ANTICIPACION_PUBLICACION)


# ESQUEMAS PYDANTIC


class GenerarAgendaRequest(BaseModel):
    profesional_id: str = Field(
        ..., min_length=1, examples=["7d2e9a40-1c11-4a3e-8f55-0e2b7c6d1a22"]
    )
    sede_id: int = Field(..., gt=0, examples=[3])
    especialidad_id: int = Field(..., gt=0, examples=[4])
    fecha_inicio: date = Field(..., examples=["2026-11-15"])
    fecha_fin: date = Field(..., examples=["2026-11-30"])

    @model_validator(mode="after")
    def validar_rango(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de fin no puede ser anterior a la fecha de inicio")
        if (self.fecha_fin - self.fecha_inicio).days + 1 > MAX_DIAS_RANGO:
            raise ValueError(
                f"El rango de fechas no puede superar {MAX_DIAS_RANGO} días"
            )
        return self


class GenerarAgendaData(BaseModel):
    profesional_id: str
    total_espacios_generados: int


class GenerarAgendaAPIResponse(BaseModel):
    mensaje: str
    data: Optional[GenerarAgendaData] = None
    success: bool


# ---------------------------------------------------------------------------
# HU-015: Consultar la disponibilidad de la agenda
# ---------------------------------------------------------------------------

# HU-014 crea los espacios con estado "LIBRE": es el estado "Disponible" de HU-015.
ESTADO_DISPONIBLE = "LIBRE"


# Caso 4: el rango de fechas es válido si fecha_fin no es anterior a fecha_inicio.
def validar_rango_consulta(fecha_inicio: date, fecha_fin: date) -> bool:
    if fecha_fin < fecha_inicio:
        raise ValueError("El rango de fechas no es válido")
    return True


# Agrupa los espacios por médico y fecha. Ordena por médico, fecha y hora.
def agrupar_disponibilidad(espacios: list) -> list:
    grupos = {}
    for espacio in espacios:
        clave = (espacio["profesional_id"], espacio["fecha"])
        grupos.setdefault(clave, []).append(
            {
                "espacio_id": espacio["espacio_id"],
                "hora_inicio": espacio["hora_inicio"],
                "hora_fin": espacio["hora_fin"],
            }
        )
    return [
        {
            "profesional_id": profesional_id,
            "fecha": fecha,
            "espacios": sorted(lista, key=lambda e: e["hora_inicio"]),
        }
        for (profesional_id, fecha), lista in sorted(grupos.items())
    ]


class EspacioDisponible(BaseModel):
    espacio_id: str
    hora_inicio: str
    hora_fin: str


class DisponibilidadMedicoFecha(BaseModel):
    profesional_id: str
    fecha: str
    espacios: list[EspacioDisponible]


class DisponibilidadData(BaseModel):
    disponibilidad: list[DisponibilidadMedicoFecha]


class DisponibilidadAPIResponse(BaseModel):
    mensaje: str
    data: Optional[DisponibilidadData] = None
    success: bool
