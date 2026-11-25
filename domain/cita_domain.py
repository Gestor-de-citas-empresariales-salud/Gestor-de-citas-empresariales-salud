# REGLAS DE NEGOCIO HU-018 (Domain Layer)
# Agendar una cita médica

from typing import Optional, Union
from datetime import datetime, timedelta
from typing import Annotated
import uuid

from pydantic import BaseModel, Field
from pydantic import StringConstraints

# RN-27: 3 inasistencias injustificadas en el año suspenden la reserva en línea.
MAX_INASISTENCIAS_INJUSTIFICADAS = 3

ESTADO_CITA_RESERVADA = "Reservada"
ESTADO_ESPACIO_OCUPADO = "OCUPADO"


def validar_inasistencias(cantidad: int) -> bool:
    if cantidad >= MAX_INASISTENCIAS_INJUSTIFICADAS:
        raise ValueError(
            "La reserva en línea está suspendida por inasistencias acumuladas"
        )
    return True


def validar_espacio_libre(estado: str, estado_libre: str) -> bool:
    if estado != estado_libre:
        raise ValueError("El espacio seleccionado ya no está disponible")
    return True


# RN-36: no se agenda con cargo a la EPS si el convenio está suspendido.
def validar_cobertura_eps(convenio_suspendido: bool) -> bool:
    if convenio_suspendido:
        raise ValueError(
            "No es posible agendar con cargo a la EPS: convenio suspendido"
        )
    return True


class ReservarCitaRequest(BaseModel):
    paciente_id: str = Field(
        ..., min_length=1, examples=["b3c1f1de-5a1e-4f0b-9d3a-2f7b1c9e8a10"]
    )
    espacio_id: Union[int, str] = Field(
        ..., examples=["c0a8012e-5b1f-4d7a-9a3e-2f6b8d1c4e90"]
    )


class CitaReservadaData(BaseModel):
    cita_id: str
    estado: str
    fecha: str
    hora_inicio: str
    profesional_id: str
    sede_id: int


class CitaAPIResponse(BaseModel):
    mensaje: str
    data: Optional[CitaReservadaData] = None
    success: bool


# ---------------------------------------------------------------------------
# HU-019: Reprogramar o cancelar una cita médica
# ---------------------------------------------------------------------------
ESTADO_CITA_CANCELADA = "Cancelada"

# RN-26: solo se puede reprogramar o cancelar con mínimo 2 horas de anticipación.
ANTICIPACION_MINIMA_HORAS = 2


def validar_formato_cita_id(cita_id: str) -> bool:
    try:
        uuid.UUID(str(cita_id))
    except ValueError:
        raise ValueError("El formato del campo cita_id no es válido")
    return True


def validar_estado_reservada(estado: str) -> bool:
    if estado != ESTADO_CITA_RESERVADA:
        raise ValueError(
            "La cita no se encuentra en un estado que permita esta operación"
        )
    return True


def fecha_hora_cita(cita: dict) -> datetime:
    return datetime.fromisoformat(f"{cita['fecha']}T{cita['hora_inicio']}")


def validar_anticipacion(cita: dict, ahora: datetime) -> bool:
    if fecha_hora_cita(cita) - ahora < timedelta(hours=ANTICIPACION_MINIMA_HORAS):
        raise ValueError(
            "La cita solo puede modificarse con mínimo 2 horas de anticipación"
        )
    return True


class ReprogramarCitaRequest(BaseModel):
    nuevo_espacio_id: Union[int, str] = Field(
        ..., examples=["c0a8012e-5b1f-4d7a-9a3e-2f6b8d1c4e90"]
    )


class CancelarCitaRequest(BaseModel):
    motivo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = Field(
        ..., examples=["No puedo asistir"]
    )


class CitaReprogramadaData(BaseModel):
    cita_id: str
    estado: str
    nuevo_espacio_id: Union[int, str]


class CitaReprogramadaAPIResponse(BaseModel):
    mensaje: str
    data: Optional[CitaReprogramadaData] = None
    success: bool


class CitaCanceladaData(BaseModel):
    cita_id: str
    estado: str
    espacio_liberado: bool


class CitaCanceladaAPIResponse(BaseModel):
    mensaje: str
    data: Optional[CitaCanceladaData] = None
    success: bool


# ---------------------------------------------------------------------------
# HU-020: Confirmar la llegada del paciente (check-in)
# ---------------------------------------------------------------------------
ESTADO_CITA_EN_SALA = "En Sala"


# El check-in solo puede realizarse el día programado de la cita.
def validar_dia_checkin(cita: dict, ahora: datetime) -> bool:
    if fecha_hora_cita(cita).date() != ahora.date():
        raise ValueError(
            "El check-in solo puede realizarse el día programado de la cita"
        )
    return True


class CheckinData(BaseModel):
    cita_id: str
    estado: str
    hora_llegada: str


class CheckinAPIResponse(BaseModel):
    mensaje: str
    data: Optional[CheckinData] = None
    success: bool
