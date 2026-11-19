# REGLAS DE NEGOCIO (Domain Layer)

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Optional


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


# RN-06: La jornada no puede superponer horas de trabajo y descanso ni superar 12 horas continuas
# Asumiendo formato "HH:MM"
def validar_turno_maximo_12_horas(bloques: list) -> bool:
    horas_por_dia: dict = {}
    rangos_por_dia: dict = {}

    for bloque in bloques:
        try:
            dia = bloque.get("dia_semana")
            h_ini_h, h_ini_m = map(int, bloque.get("hora_inicio", "00:00").split(":"))
            h_fin_h, h_fin_m = map(int, bloque.get("hora_fin", "00:00").split(":"))

            minutos_inicio = h_ini_h * 60 + h_ini_m
            minutos_fin = h_fin_h * 60 + h_fin_m
            duracion_minutos = minutos_fin - minutos_inicio
            duracion_horas = duracion_minutos / 60

            if duracion_horas <= 0:
                raise ValueError("La hora de inicio debe ser anterior a la hora de fin")

            if duracion_horas > 12:
                raise ValueError("El turno supera las 12 horas continuas permitidas")

            # Verificar solapamiento de horarios en el mismo día
            if dia not in rangos_por_dia:
                rangos_por_dia[dia] = []

            for ini_existente, fin_existente in rangos_por_dia[dia]:
                if minutos_inicio < fin_existente and minutos_fin > ini_existente:
                    raise ValueError(
                        "La jornada no puede superponer horas de trabajo y descanso"
                    )

            rangos_por_dia[dia].append((minutos_inicio, minutos_fin))

            # Acumular total de horas del día
            if dia not in horas_por_dia:
                horas_por_dia[dia] = 0.0

            horas_por_dia[dia] += duracion_horas

            if horas_por_dia[dia] > 12:
                raise ValueError("El turno supera las 12 horas continuas permitidas")

        except ValueError as ve:
            mensaje = str(ve)
            if (
                "supera las 12 horas" in mensaje
                or "anterior" in mensaje
                or "superponer" in mensaje
            ):
                raise ve
            raise ValueError("Formato de hora inválido, use HH:MM")

    return True


def calcular_horas_totales(bloques: list) -> int:
    total_minutos_semanales = 0

    for bloque in bloques:
        try:
            h_ini_h, h_ini_m = map(int, bloque.get("hora_inicio", "00:00").split(":"))
            h_fin_h, h_fin_m = map(int, bloque.get("hora_fin", "00:00").split(":"))
            minutos = (h_fin_h * 60 + h_fin_m) - (h_ini_h * 60 + h_ini_m)
            if minutos > 0:
                total_minutos_semanales += minutos
        except Exception:
            pass

    horas_semanales = total_minutos_semanales // 60

    # Aplicando tu lógica exacta: 160 horas mensuales / 4 semanas = 40 horas semanales máximas
    if horas_semanales > 40:
        raise ValueError("El profesional supera el máximo de 160 horas mensuales")

    return int(horas_semanales)


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


# ESQUEMAS PYDANTIC PARA SEDES Y JORNADA


class SedeAsignarRequest(BaseModel):
    sede_id: int = Field(..., examples=[3])

    @field_validator("sede_id")
    @classmethod
    def validar_sede(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("El identificador de la sede no es válido")
        return v


class SedeResponseData(BaseModel):
    profesional_id: str
    sede_id: int
    asignada: bool


class SedeAPIResponse(BaseModel):
    mensaje: str
    data: Optional[SedeResponseData] = None
    success: bool


class BloqueJornada(BaseModel):
    dia_semana: int = Field(
        ...,
        ge=1,
        le=7,
        examples=[1],
        description="Día de la semana (1: Lunes a 7: Domingo)",
    )
    hora_inicio: str = Field(..., examples=["07:00"])
    hora_fin: str = Field(..., examples=["12:00"])


class JornadaLaboralRequest(BaseModel):
    bloques: List[BloqueJornada]

    @field_validator("bloques")
    @classmethod
    def validar_bloques(cls, v: List[BloqueJornada]) -> List[BloqueJornada]:
        if not v:
            raise ValueError("Debe proporcionar al menos un bloque de jornada laboral")
        return v


class JornadaResponseData(BaseModel):
    profesional_id: str
    horas_semanales: int
    agenda_notificada: bool


class JornadaAPIResponse(BaseModel):
    mensaje: str
    data: Optional[JornadaResponseData] = None
    success: bool


# ESQUEMAS PYDANTIC PARA PROFESIONALES


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
