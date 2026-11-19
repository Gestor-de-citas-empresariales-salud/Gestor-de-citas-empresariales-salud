from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

# Catálogo maestro local de códigos CUPS vigentes: {codigo: vigente}
CATALOGO_CUPS_VIGENTES: Dict[str, bool] = {
    "890281": True,
    "890381": True,
    "890201": True,
    "890301": True,
    "890401": True,
    "890299": False,  # Código CUPS inactivo / no vigente para pruebas de regla de negocio
}


# Valida que no exista otra especialidad con el mismo nombre.
def validar_nombre_especialidad_duplicado(
    nombre: str, nombres_existentes: List[str]
) -> bool:
    nombre_normalizado = nombre.strip().lower()
    for existente in nombres_existentes:
        if existente.strip().lower() == nombre_normalizado:
            raise ValueError("Ya existe una especialidad con ese nombre")
    return True


# RN-15: valida que haya al menos un código CUPS y que todos existan y estén vigentes.
def validar_codigos_cups_vigentes(
    codigos_cups: List[str],
    catalogo_cups: Optional[Dict[str, bool]] = None,
) -> List[str]:
    if not codigos_cups or len(codigos_cups) == 0:
        raise ValueError("Uno o más códigos CUPS no existen o no están vigentes")

    catalogo = catalogo_cups if catalogo_cups is not None else CATALOGO_CUPS_VIGENTES
    codigos_limpios: List[str] = []

    for codigo in codigos_cups:
        codigo_str = str(codigo).strip()
        if not codigo_str or codigo_str.lower() == "string":
            raise ValueError("Uno o más códigos CUPS no existen o no están vigentes")

        esta_vigente = catalogo.get(codigo_str, False)
        if esta_vigente is not True:
            raise ValueError("Uno o más códigos CUPS no existen o no están vigentes")

        if codigo_str not in codigos_limpios:
            codigos_limpios.append(codigo_str)

    if len(codigos_limpios) == 0:
        raise ValueError("Uno o más códigos CUPS no existen o no están vigentes")

    return codigos_limpios


# ESQUEMAS PYDANTIC - CREAR ESPECIALIDAD


class EspecialidadCreate(BaseModel):
    nombre: str = Field(..., min_length=2, examples=["Cardiología"])
    descripcion: Optional[str] = Field(
        default=None, examples=["Atención cardiovascular"]
    )
    alta_complejidad: bool = Field(..., examples=[True])

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, v: str) -> str:
        limpio = v.strip()
        if not limpio or limpio.lower() == "string":
            raise ValueError("El campo 'nombre' es obligatorio o inválido")
        return limpio

    @field_validator("descripcion")
    @classmethod
    def validar_descripcion(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        limpio = v.strip()
        if limpio.lower() == "string":
            return None
        return limpio


class EspecialidadCreadaData(BaseModel):
    especialidad_id: int
    nombre: str


class EspecialidadAPIResponse(BaseModel):
    mensaje: str
    data: Optional[EspecialidadCreadaData] = None
    success: bool


# ESQUEMAS PYDANTIC - ASOCIAR CÓDIGOS CUPS


class EspecialidadCupsRequest(BaseModel):
    codigos_cups: List[str] = Field(..., examples=[["890281", "890381"]])

    @field_validator("codigos_cups")
    @classmethod
    def validar_lista_cups(cls, v: List[str]) -> List[str]:
        if not v or len(v) == 0:
            raise ValueError("Debe enviar al menos un código CUPS")
        return v


class EspecialidadCupsData(BaseModel):
    especialidad_id: int
    total_codigos: int
    codigos_cups: List[str]


class EspecialidadCupsAPIResponse(BaseModel):
    mensaje: str
    data: Optional[EspecialidadCupsData] = None
    success: bool
