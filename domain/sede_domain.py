from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

TIPOS_CONSULTORIO_VALIDOS = {
    "CONSULTA_EXTERNA",
    "CONSULTA_EXTERNA_GENERAL",
    "PROCEDIMIENTOS_MENORES",
    "OFICINA",
}


# Valida que no exista otra sede con la misma dirección y ciudad.
def validar_sede_duplicada(
    direccion: str,
    ciudad: str,
    sedes_existentes: List[Dict[str, str]],
) -> bool:
    direccion_limpia = " ".join(direccion.strip().lower().split())
    ciudad_limpia = " ".join(ciudad.strip().lower().split())

    for sede in sedes_existentes:
        dir_existente = " ".join(str(sede.get("direccion", "")).strip().lower().split())
        ciu_existente = " ".join(str(sede.get("ciudad", "")).strip().lower().split())
        if dir_existente == direccion_limpia and ciu_existente == ciudad_limpia:
            raise ValueError("Ya existe una sede registrada en esa dirección")

    return True


# Valida rangos geográficos de latitud y longitud.
def validar_coordenadas_sede(latitud: float, longitud: float) -> tuple[float, float]:
    if isinstance(latitud, bool) or latitud < -90 or latitud > 90:
        raise ValueError("El campo 'latitud' debe estar entre -90 y 90")

    if isinstance(longitud, bool) or longitud < -180 or longitud > 180:
        raise ValueError("El campo 'longitud' debe estar entre -180 y 180")

    return float(latitud), float(longitud)


# Valida que la sede tenga capacidad física disponible para un nuevo consultorio.
def validar_capacidad_sede(consultorios_actuales: int, capacidad_maxima: int) -> bool:
    if capacidad_maxima <= 0 or consultorios_actuales >= capacidad_maxima:
        raise ValueError("La sede no tiene capacidad para alojar un nuevo consultorio")
    return True


# RN-17: Un consultorio de procedimientos menores no habilita consulta externa general.
def validar_tipo_consultorio_rn17(
    tipo_consultorio: str,
    tipo_sede: Optional[str] = None,
) -> str:
    tipo_limpio = tipo_consultorio.strip().upper()
    if not tipo_limpio or tipo_limpio == "STRING":
        raise ValueError("El campo 'tipo' es obligatorio o inválido")

    if tipo_limpio not in TIPOS_CONSULTORIO_VALIDOS:
        raise ValueError("El campo 'tipo' de consultorio no es válido")

    sede_tipo_limpio = str(tipo_sede or "").strip().upper()
    if sede_tipo_limpio == "PROCEDIMIENTOS_MENORES" and tipo_limpio in {
        "CONSULTA_EXTERNA",
        "CONSULTA_EXTERNA_GENERAL",
    }:
        raise ValueError(
            "Un consultorio de procedimientos menores no habilita consulta externa general"
        )

    return tipo_limpio


# ESQUEMAS PYDANTIC - SEDES (FUN-16)


class SedeCreate(BaseModel):
    nombre: str = Field(..., min_length=2, examples=["Sede Cabecera"])
    direccion: str = Field(..., min_length=4, examples=["Cra 33 # 42-10"])
    ciudad: str = Field(..., min_length=2, examples=["Bucaramanga"])
    latitud: float = Field(..., examples=[7.1193])
    longitud: float = Field(..., examples=[-73.1227])

    @field_validator("nombre", "direccion", "ciudad")
    @classmethod
    def validar_texto_obligatorio(cls, v: str) -> str:
        limpio = " ".join(v.strip().split())
        if not limpio or limpio.lower() == "string":
            raise ValueError("El campo es obligatorio o inválido")
        return limpio

    @field_validator("latitud", "longitud")
    @classmethod
    def validar_numero_coordenada(cls, v: float) -> float:
        if isinstance(v, bool):
            raise ValueError("El campo debe ser numérico")
        return v


class SedeCreadaData(BaseModel):
    sede_id: int
    nombre: str


class SedeRegistroAPIResponse(BaseModel):
    mensaje: str
    data: Optional[SedeCreadaData] = None
    success: bool


# ESQUEMAS PYDANTIC - CONSULTORIOS (FUN-17)


class ConsultorioCreate(BaseModel):
    codigo: str = Field(..., min_length=2, examples=["C-101"])
    tipo: str = Field(..., min_length=2, examples=["CONSULTA_EXTERNA"])

    @field_validator("codigo", "tipo")
    @classmethod
    def validar_campos_consultorio(cls, v: str) -> str:
        limpio = v.strip().upper()
        if not limpio or limpio == "STRING":
            raise ValueError("El campo es obligatorio o inválido")
        return limpio


class ConsultorioCreadoData(BaseModel):
    consultorio_id: int
    sede_id: int
    codigo: str
    tipo: str


class ConsultorioAPIResponse(BaseModel):
    mensaje: str
    data: Optional[ConsultorioCreadoData] = None
    success: bool
