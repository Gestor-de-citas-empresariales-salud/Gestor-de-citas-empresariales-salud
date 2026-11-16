# REGLAS DE NEGOCIO
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Optional
from datetime import datetime
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

    @field_validator("tipo_documento_id")
    @classmethod
    def validar_tipo_documento(cls, v: int) -> int:
        tipos_validos = [1, 2, 3]  # Ajusta los IDs según los que maneje Profesionales
        if v not in tipos_validos:
            raise ValueError("El tipo de documento de identidad no es válido")
        return v

    @field_validator("genero_id")
    @classmethod
    def validar_genero(cls, v: int) -> int:
        generos_validos = [1, 2]  # 1: Masculino, 2: Femenino (o los que apliquen)
        if v not in generos_validos:
            raise ValueError("El género especificado no es válido")
        return v

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


class ContactoEmergenciaSchema(BaseModel):
    nombre: str = Field(..., min_length=2, description="Nombre completo del contacto")
    parentesco: str = Field(..., min_length=4, description="Parentesco con el paciente")
    telefono: str = Field(..., description="Teléfono celular válido de 10 dígitos")

    @field_validator("nombre", "parentesco")
    @classmethod
    def validar_no_generico(cls, v: str) -> str:
        if not v or v.strip().lower() == "string":
            raise ValueError(
                "El campo no puede contener un valor genérico o estar vacío"
            )
        return v.strip()

    @field_validator("telefono")
    def validador_telefono(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 10 or not v.startswith("3"):
            raise ValueError("El teléfono del contacto no tiene un formato válido")
        return v


class GestionarContactosEmergenciaRequest(BaseModel):
    contactos: List[ContactoEmergenciaSchema] = Field(
        ..., description="Lista de contactos de emergencia"
    )


def es_menor_de_edad(fecha_nacimiento_str: str) -> bool:
    try:
        f_nac = datetime.strptime(fecha_nacimiento_str, "%Y-%m-%d")
        hoy = datetime.now()
        edad = hoy.year - f_nac.year - ((hoy.month, hoy.day) < (f_nac.month, f_nac.day))
        return edad < 18
    except ValueError:
        return False


def validar_direccion_repetida(
    nueva_direccion: str, direccion_actual: Optional[str]
) -> bool:
    if not nueva_direccion or not direccion_actual:
        return False
    return nueva_direccion == direccion_actual


def validar_limite_contactos(contactos_lista: list, max_permitidos: int = 2) -> bool:
    return len(contactos_lista) > max_permitidos


def validar_adulto_responsable_contacto(
    fecha_nacimiento: str, contactos_lista: list
) -> bool:
    if not es_menor_de_edad(fecha_nacimiento):
        return True
    parentescos_adultos = ["padre", "madre", "tutor", "acudiente", "responsable"]
    return any(c.parentesco.lower() in parentescos_adultos for c in contactos_lista)
