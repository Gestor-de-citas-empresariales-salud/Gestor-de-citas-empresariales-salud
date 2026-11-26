from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.agenda_router import agenda_repository
from api.paciente_router import paciente_repository as paciente_repo_compartido
from domain.cita_domain import CitaAPIResponse, ReservarCitaRequest
from domain.cita_domain import (
    CancelarCitaRequest,
    CheckinAPIResponse,
    CitaCanceladaAPIResponse,
    CitaReprogramadaAPIResponse,
    ReprogramarCitaRequest,
)
from repository.cita_repository import cita_repository
from service.cita_service import MENSAJE_503_CITA, CitaService
from service.cita_service import MENSAJE_503_MODIFICAR_CITA
from service.cita_service import MENSAJE_503_CHECKIN

router = APIRouter(prefix="/api/v1/citas", tags=["Citas"])

security = HTTPBearer(auto_error=False)


# Usa los mismos almacenes en memoria de pacientes y de agenda (HU-001 y HU-014)
def get_cita_service():
    return CitaService(
        paciente_repo=paciente_repo_compartido,
        agenda_repo=agenda_repository,
        cita_repo=cita_repository,
    )


def _respuesta_error(codigo: int, mensaje: str) -> JSONResponse:
    return JSONResponse(
        status_code=codigo,
        content={"mensaje": mensaje, "data": None, "success": False},
    )


def _ejemplo_error(descripcion: str, mensaje: str) -> dict:
    return {
        "description": descripcion,
        "content": {
            "application/json": {
                "example": {"mensaje": mensaje, "data": None, "success": False}
            }
        },
    }


@router.post(
    "/reservar",
    response_model=CitaAPIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agendar una cita médica",
    description=(
        ""
    ),
    responses={
        400: _ejemplo_error(
            "Datos o parámetros inválidos",
            "Error en el campo 'espacio_id': Field required",
        ),
        401: _ejemplo_error(
            "Token de autenticación inválido o ausente",
            "Token de autenticación inválido o ausente",
        ),
        403: _ejemplo_error(
            "Acceso denegado: el rol no tiene permiso (RBAC)",
            "No cuenta con permisos para esta operación",
        ),
        404: _ejemplo_error(
            "No existe el paciente o el espacio indicado",
            "No se encontró el paciente indicado",
        ),
        409: _ejemplo_error(
            "El espacio ya fue ocupado por otra reserva",
            "El espacio seleccionado ya no está disponible",
        ),
        422: _ejemplo_error(
            "Regla de negocio (RN-27 inasistencias o RN-36 convenio EPS)",
            "La reserva en línea está suspendida por inasistencias acumuladas",
        ),
        503: _ejemplo_error("Falla de base de datos o servicio externo", MENSAJE_503_CITA),
    },
)
def reservar_cita(
    datos: ReservarCitaRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    service: CitaService = Depends(get_cita_service),
):
    if not credentials or not credentials.credentials:
        return _respuesta_error(
            status.HTTP_401_UNAUTHORIZED, "Token de autenticación inválido o ausente"
        )

    if credentials.credentials == "token_sin_permiso":
        return _respuesta_error(
            status.HTTP_403_FORBIDDEN, "No cuenta con permisos para esta operación"
        )

    try:
        return service.reservar_cita(datos)
    except HTTPException as ex:
        return _respuesta_error(ex.status_code, ex.detail)
    except Exception:
        return _respuesta_error(status.HTTP_503_SERVICE_UNAVAILABLE, MENSAJE_503_CITA)


def _validar_acceso(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> Optional[JSONResponse]:
    if not credentials or not credentials.credentials:
        return _respuesta_error(
            status.HTTP_401_UNAUTHORIZED, "Token de autenticación inválido o ausente"
        )
    if credentials.credentials == "token_sin_permiso":
        return _respuesta_error(
            status.HTTP_403_FORBIDDEN, "No cuenta con permisos para esta operación"
        )
    return None


_RESPUESTAS_AUTH = {
    401: _ejemplo_error(
        "Token de autenticación inválido o ausente",
        "Token de autenticación inválido o ausente",
    ),
    403: _ejemplo_error(
        "Acceso denegado: el rol no tiene permiso (RBAC)",
        "No cuenta con permisos para esta operación",
    ),
}


@router.put(
    "/{cita_id}/reprogramar",
    response_model=CitaReprogramadaAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Reprogramar una cita médica",
    description=(
        ""
    ),
    responses={
        400: _ejemplo_error(
            "Datos o parámetros inválidos",
            "Error en el campo 'nuevo_espacio_id': Field required",
        ),
        404: _ejemplo_error(
            "No existe la cita o el nuevo espacio", "No se encontró la cita indicada"
        ),
        409: _ejemplo_error(
            "La cita no está Reservada o el nuevo espacio no está disponible",
            "La cita no se encuentra en un estado que permita esta operación",
        ),
        422: _ejemplo_error(
            "Faltan menos de 2 horas para la cita (RN-26)",
            "La cita solo puede modificarse con mínimo 2 horas de anticipación",
        ),
        503: _ejemplo_error(
            "Falla de base de datos o servicio externo", MENSAJE_503_MODIFICAR_CITA
        ),
        **_RESPUESTAS_AUTH,
    },
)
def reprogramar_cita(
    cita_id: str,
    datos: ReprogramarCitaRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    service: CitaService = Depends(get_cita_service),
):
    acceso = _validar_acceso(credentials)
    if acceso:
        return acceso
    try:
        return service.reprogramar_cita(cita_id, datos)
    except HTTPException as ex:
        return _respuesta_error(ex.status_code, ex.detail)
    except Exception:
        return _respuesta_error(
            status.HTTP_503_SERVICE_UNAVAILABLE, MENSAJE_503_MODIFICAR_CITA
        )


@router.delete(
    "/{cita_id}",
    response_model=CitaCanceladaAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancelar una cita médica",
    description=(
        ""
    ),
    responses={
        400: _ejemplo_error(
            "Datos o parámetros inválidos",
            "Error en el campo 'motivo': Field required",
        ),
        404: _ejemplo_error("No existe la cita", "No se encontró la cita indicada"),
        409: _ejemplo_error(
            "La cita no está Reservada",
            "La cita no se encuentra en un estado que permita esta operación",
        ),
        422: _ejemplo_error(
            "Faltan menos de 2 horas para la cita (RN-26)",
            "La cita solo puede modificarse con mínimo 2 horas de anticipación",
        ),
        503: _ejemplo_error(
            "Falla de base de datos o servicio externo", MENSAJE_503_MODIFICAR_CITA
        ),
        **_RESPUESTAS_AUTH,
    },
)
def cancelar_cita(
    cita_id: str,
    datos: CancelarCitaRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    service: CitaService = Depends(get_cita_service),
):
    acceso = _validar_acceso(credentials)
    if acceso:
        return acceso
    try:
        return service.cancelar_cita(cita_id, datos)
    except HTTPException as ex:
        return _respuesta_error(ex.status_code, ex.detail)
    except Exception:
        return _respuesta_error(
            status.HTTP_503_SERVICE_UNAVAILABLE, MENSAJE_503_MODIFICAR_CITA
        )


@router.post(
    "/{cita_id}/check-in",
    response_model=CheckinAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirmar la llegada del paciente (check-in)",
    description=(
        ""
    ),
    responses={
        400: _ejemplo_error(
            "Datos o parámetros inválidos",
            "El formato del campo cita_id no es válido",
        ),
        404: _ejemplo_error(
            "La cita no existe o ya fue cancelada",
            "No se encontró una cita activa con el identificador indicado",
        ),
        409: _ejemplo_error(
            "La cita no está Reservada",
            "La cita no se encuentra en un estado que permita esta operación",
        ),
        422: _ejemplo_error(
            "La fecha actual no corresponde al día de la cita",
            "El check-in solo puede realizarse el día programado de la cita",
        ),
        503: _ejemplo_error(
            "Falla de base de datos o servicio externo", MENSAJE_503_CHECKIN
        ),
        **_RESPUESTAS_AUTH,
    },
)
def confirmar_llegada(
    cita_id: str,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    service: CitaService = Depends(get_cita_service),
):
    acceso = _validar_acceso(credentials)
    if acceso:
        return acceso
    try:
        return service.registrar_checkin(cita_id)
    except HTTPException as ex:
        return _respuesta_error(ex.status_code, ex.detail)
    except Exception:
        return _respuesta_error(status.HTTP_503_SERVICE_UNAVAILABLE, MENSAJE_503_CHECKIN)
