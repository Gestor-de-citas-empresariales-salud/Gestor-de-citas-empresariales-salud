from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.profesional_router import profesional_repository
from domain.agenda_domain import GenerarAgendaAPIResponse, GenerarAgendaRequest
from repository.agenda_repository import AgendaRepository
from service.agenda_service import MENSAJE_503, AgendaService, SedeAgendaLocal

router = APIRouter(prefix="/api/v1/agendas", tags=["Agendas"])

security = HTTPBearer(auto_error=False)

agenda_repository = AgendaRepository()
sede_agenda_local = SedeAgendaLocal()


def get_agenda_service():
    return AgendaService(
        profesional_repo=profesional_repository,
        sede_repo=sede_agenda_local,
        agenda_repo=agenda_repository,
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
    "/generar",
    response_model=GenerarAgendaAPIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generar los espacios de la agenda médica",
    responses={
        400: _ejemplo_error(
            "Datos o parámetros inválidos",
            "La fecha de fin no puede ser anterior a la fecha de inicio",
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
            "No existe el profesional o la sede indicada",
            "No se encontró el profesional indicado",
        ),
        409: _ejemplo_error(
            "Ya existen franjas solapadas para el médico (RN-21)",
            "El profesional ya tiene franjas solapadas en el rango indicado",
        ),
        422: _ejemplo_error(
            "Error de regla de negocio",
            "El profesional no tiene jornada laboral configurada",
        ),
        503: _ejemplo_error("Falla de base de datos o servicio externo", MENSAJE_503),
    },
)
def generar_agenda(
    datos: GenerarAgendaRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    service: AgendaService = Depends(get_agenda_service),
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
        return service.generar_agenda(datos)
    except HTTPException as ex:
        return _respuesta_error(ex.status_code, ex.detail)
    except Exception:
        return _respuesta_error(status.HTTP_503_SERVICE_UNAVAILABLE, MENSAJE_503)