# REGLAS DE NEGOCIO HU-018 (Domain Layer)
# Agendar una cita médica

from typing import Optional, Union

from pydantic import BaseModel, Field

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
