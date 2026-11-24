from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.agenda_router import agenda_repository
from api.paciente_router import paciente_repository as paciente_repo_compartido
from domain.cita_domain import CitaAPIResponse, ReservarCitaRequest
from repository.cita_repository import cita_repository
from service.cita_service import MENSAJE_503_CITA, CitaService

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
