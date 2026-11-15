# REGLAS DE NEGOCIO (Domain Layer)

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional


# Valida que el tipo de documento pertenezca al catálogo válido en Colombia (1, 2, 3, 4).
# Si no existe, la regla de negocio rechaza el valor.
def validar_tipo_documento(tipo_documento_id: int) -> bool:

    # 1: CC, 2: TI, 3: CE, 4: Pasaporte
    tipos_validos = {1, 2, 3, 4}
    if tipo_documento_id not in tipos_validos:
        raise ValueError("El tipo de documento especificado no es válido en el sistema")
    return True


# Valida que no exista previamente un número de documento igual en el sistema.
def validar_documento_duplicado(
    numero_documento: str, documentos_existentes: list
) -> bool:

    if numero_documento in documentos_existentes:
        raise ValueError(
            "Ya existe un profesional registrado con ese número de documento"
        )
    return True


# RN-10: Valida si el profesional se encuentra habilitado en RETHUS.
# Si la tarjeta es 'TP-INHABILITADA' o el documento es '00000000'
def validar_regla_rethus(tarjeta_profesional: str, numero_documento: str) -> bool:

    if (
        tarjeta_profesional.upper() == "TP-INHABILITADA"
        or numero_documento == "00000000"
    ):
        raise ValueError("El profesional no se encuentra habilitado en RETHUS")
    return True


# Valida que no exista previamente una tarjeta profesional igual en el sistema.
def validar_tarjeta_duplicada(
    tarjeta_profesional: str, tarjetas_existentes: list
) -> bool:

    if tarjeta_profesional.lower() in [t.lower() for t in tarjetas_existentes]:
        raise ValueError("Ya existe un profesional con esa tarjeta profesional")
    return True


# ESQUEMAS PYDANTIC


class ProfesionalCreate(BaseModel):
    tipo_documento_id: int = Field(..., examples=[1])
    numero_documento: str = Field(..., min_length=5, examples=["91234567"])
    nombres: str = Field(..., min_length=2, examples=["Andrés"])
    apellidos: str = Field(..., min_length=2, examples=["Pérez"])
    tarjeta_profesional: str = Field(..., min_length=5, examples=["TP-123456"])
    especialidad_id: int = Field(..., examples=[4])
    email: EmailStr = Field(..., examples=["andres.perez@clinica.com"])

    # Invoca la regla de negocio pura de la capa domain
    @field_validator("tipo_documento_id")
    @classmethod
    def validar_tipo_doc(cls, v: int) -> int:

        validar_tipo_documento(v)
        return v

    @field_validator("nombres", "apellidos", "tarjeta_profesional")
    @classmethod
    def validar_no_generico(cls, v: str) -> str:
        if not v or v.strip().lower() == "string":
            raise ValueError(
                "El campo no puede contener un valor genérico o estar vacío"
            )
        return v.strip()


class ProfesionalResponseData(BaseModel):
    profesional_id: str
    usuario_creado: bool
    estado: str


class ProfesionalAPIResponse(BaseModel):
    mensaje: str
    data: Optional[ProfesionalResponseData] = None
    success: bool


class ValidacionRethusRequest(BaseModel):
    numero_documento: str = Field(..., examples=["91234567"])
    tarjeta_profesional: str = Field(..., examples=["TP-123456"])


class RethusResponseData(BaseModel):
    profesional_id: str
    estado_rethus: str
    codigo_verificacion: str
    activo: bool


class RethusAPIResponse(BaseModel):
    mensaje: str
    data: Optional[RethusResponseData] = None
    success: bool
