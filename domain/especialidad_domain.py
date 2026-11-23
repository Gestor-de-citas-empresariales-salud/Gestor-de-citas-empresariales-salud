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

DURACION_MINIMA_ALTA_COMPLEJIDAD_MINUTOS: int = 40


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


# HU-010 / RN-11: valida duración base y regla de primera vez en alta complejidad.
def validar_duracion_base_especialidad(minutos: int, alta_complejidad: bool) -> int:
    if minutos <= 0:
        raise ValueError("El campo 'minutos' debe ser mayor a cero")

    if alta_complejidad and minutos < DURACION_MINIMA_ALTA_COMPLEJIDAD_MINUTOS:
        raise ValueError(
            "La duración mínima para consultas de primera vez de alta complejidad es 40 minutos"
        )

    return minutos


# HU-010 (FUN-14): valida y limpia el texto de requisitos previos.
def validar_requisitos_previos_texto(texto: str) -> str:
    texto_limpio = texto.strip()
    if not texto_limpio or texto_limpio.lower() == "string":
        raise ValueError(
            "El campo 'texto' de requisitos previos es obligatorio o inválido"
        )
    return texto_limpio


# HU-010 (FUN-15): valida tarifa base (> 0) y moneda.
def validar_tarifa_base_especialidad(valor: float, moneda: str) -> tuple[float, str]:
    if valor <= 0:
        raise ValueError("La tarifa base debe ser mayor a cero")

    moneda_limpia = moneda.strip().upper()
    if not moneda_limpia or moneda_limpia == "STRING":
        raise ValueError("El campo 'moneda' es obligatorio o inválido")

    return valor, moneda_limpia


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


# ESQUEMAS PYDANTIC - HU-010 (DURACIÓN, REQUISITOS PREVIOS Y TARIFA BASE)


class DuracionBaseRequest(BaseModel):
    minutos: int = Field(..., examples=[40])

    @field_validator("minutos")
    @classmethod
    def validar_minutos_entrada(cls, v: int) -> int:
        if isinstance(v, bool) or v <= 0:
            raise ValueError(
                "El campo 'minutos' debe ser un número entero mayor a cero"
            )
        return v


class DuracionBaseData(BaseModel):
    especialidad_id: int
    duracion_base_minutos: int


class DuracionBaseAPIResponse(BaseModel):
    mensaje: str
    data: Optional[DuracionBaseData] = None
    success: bool


class RequisitosPreviosRequest(BaseModel):
    texto: str = Field(
        ...,
        min_length=3,
        examples=["Asistir con 8 horas de ayuno y traer exámenes previos."],
    )

    @field_validator("texto")
    @classmethod
    def validar_texto_entrada(cls, v: str) -> str:
        limpio = v.strip()
        if not limpio or limpio.lower() == "string":
            raise ValueError("El campo 'texto' es obligatorio o inválido")
        return limpio


class RequisitosPreviosData(BaseModel):
    especialidad_id: int
    requisitos_registrados: bool


class RequisitosPreviosAPIResponse(BaseModel):
    mensaje: str
    data: Optional[RequisitosPreviosData] = None
    success: bool


class TarifaBaseRequest(BaseModel):
    valor: float = Field(..., examples=[95000])
    moneda: str = Field(..., min_length=2, examples=["COP"])

    @field_validator("valor")
    @classmethod
    def validar_valor_entrada(cls, v: float) -> float:
        if isinstance(v, bool):
            raise ValueError("El campo 'valor' debe ser numérico")
        return v

    @field_validator("moneda")
    @classmethod
    def validar_moneda_entrada(cls, v: str) -> str:
        limpio = v.strip().upper()
        if not limpio or limpio.lower() == "string":
            raise ValueError("El campo 'moneda' es obligatorio o inválido")
        return limpio


class TarifaBaseData(BaseModel):
    especialidad_id: int
    tarifa_base: float
    moneda: str


class TarifaBaseAPIResponse(BaseModel):
    mensaje: str
    data: Optional[TarifaBaseData] = None
    success: bool
