from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
import re


# Restricción teléfono
def validar_formato_telefono(v: Optional[str], es_opcional: bool = False):
    if es_opcional and (v is None or v == "string" or v == ""):
        return v
    if not v or not re.match(r"^3\d{9}$", v):
        raise ValueError("El teléfono debe tener 10 dígitos y empezar por el número 3")
    return v


# Restricción correo
def validar_formato_correo(v: Optional[str], es_opcional: bool = False):
    if es_opcional and (v is None or v == "string" or v == ""):
        return v

    if v and "@" not in v:
        raise ValueError("El correo electrónico no tiene un formato válido")
    return v


class PacienteCreate(BaseModel):
    tipo_documento_id: int = Field(..., examples=[1])
    numero_documento: str = Field(..., min_length=5, examples=["1098765432"])
    nombres: str = Field(..., min_length=2, examples=["Laura"])
    apellidos: str = Field(..., min_length=2, examples=["Gómez Ríos"])
    fecha_nacimiento: str = Field(..., examples=["1995-04-12"])
    genero_id: int = Field(..., examples=[2])
    email: EmailStr = Field(..., examples=["laura@correo.com"])
    telefono: str = Field(..., min_length=7, examples=["3001234567"])
    direccion: str = Field(..., examples=["Cra 27 # 10-15"])
    password: str = Field(..., min_length=6, examples=["********"])
    tutor_id: Optional[str] = Field(None, examples=[""])

    @field_validator("telefono")
    @classmethod
    def check_telefono(cls, v):
        return validar_formato_telefono(v, es_opcional=False)

    @field_validator("email")
    @classmethod
    def check_email(cls, v):
        return validar_formato_correo(str(v), es_opcional=False)


class PacienteResponseData(BaseModel):
    paciente_id: str
    numero_documento: str
    nombres: str
    apellidos: str
    token_inicial: str


class PacienteAPIResponse(BaseModel):
    mensaje: str
    data: PacienteResponseData | None = None
    success: bool


class PacienteContactoUpdate(BaseModel):
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None

    @field_validator("telefono")
    @classmethod
    def check_telefono(cls, v):
        return validar_formato_telefono(v, es_opcional=True)

    @field_validator("email")
    @classmethod
    def check_email(cls, v):
        if v is not None:
            return validar_formato_correo(str(v), es_opcional=True)
        return v
