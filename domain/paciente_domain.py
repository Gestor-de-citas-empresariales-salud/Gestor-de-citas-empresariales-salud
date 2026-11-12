from pydantic import BaseModel, Field, EmailStr
from typing import Optional

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
    tutor_id: Optional[str] = Field(None, examples=["1098776542"]) # <--- ¡Este campo es obligatorio que esté aquí!

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