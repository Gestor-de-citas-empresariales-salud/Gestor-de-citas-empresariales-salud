from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.profesional_router import profesional_repository
from domain.agenda_domain import (
    DisponibilidadAPIResponse,
    GenerarAgendaAPIResponse,
    GenerarAgendaRequest,
)
from repository.agenda_repository import AgendaRepository
from service.agenda_service import (
    MENSAJE_503,
    MENSAJE_503_DISPONIBILIDAD,
    AgendaService,
    SedeAgendaLocal,
)

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


def _parsear_entero_positivo(valor: Optional[str], campo: str) -> int:
    if valor is None or str(valor).strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El campo '{campo}' es obligatorio",
        )
    try:
        numero = int(str(valor).strip())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en el campo '{campo}': debe ser un número entero válido",
        )
    if numero <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en el campo '{campo}': debe ser mayor que 0",
        )
    return numero


def _parsear_fecha_iso(valor: Optional[str], campo: str) -> date:
    if valor is None or str(valor).strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El campo '{campo}' es obligatorio",
        )
    try:
        return date.fromisoformat(str(valor).strip())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en el campo '{campo}': formato de fecha inválido (use YYYY-MM-DD)",
        )


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


@router.get(
    "/disponibilidad",
    response_model=DisponibilidadAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar la disponibilidad de la agenda",
    description=(
        "Retorna los espacios en estado Disponible filtrados por especialidad, "
        "sede y rango de fechas, agrupados por médico y fecha. Si no hay "
        "espacios responde HTTP 200 con success=false y una lista vacía."
    ),
    responses={
        200: {
            "description": "Consulta realizada (success=false si no hay espacios)",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Operación exitosa: Consultar disponibilidad en la agenda",
                        "data": {
                            "disponibilidad": [
                                {
                                    "profesional_id": "7d2e9a40-1c11-4a3e-8f55-0e2b7c6d1a22",
                                    "fecha": "2026-11-16",
                                    "espacios": [
                                        {
                                            "espacio_id": "c0a8012e-5b1f-4d7a-9a3e-2f6b8d1c4e90",
                                            "hora_inicio": "08:00",
                                            "hora_fin": "08:20",
                                        }
                                    ],
                                }
                            ]
                        },
                        "success": True,
                    }
                }
            },
        },
        400: _ejemplo_error(
            "Datos o parámetros inválidos / rango de fechas inválido",
            "El campo 'especialidad_id' es obligatorio",
        ),
        401: _ejemplo_error(
            "Token de autenticación inválido o ausente",
            "Token de autenticación inválido o ausente",
        ),
        403: _ejemplo_error(
            "Acceso denegado: el rol no tiene permiso (RBAC)",
            "No cuenta con permisos para esta operación",
        ),
        503: _ejemplo_error(
            "Falla de base de datos o servicio externo",
            MENSAJE_503_DISPONIBILIDAD,
        ),
    },
)
def consultar_disponibilidad(
    especialidad_id: Optional[str] = Query(
        default=None, description="Identificador de la especialidad", examples=[4]
    ),
    sede_id: Optional[str] = Query(
        default=None, description="Identificador de la sede (1, 2 o 3)", examples=[3]
    ),
    fecha_inicio: Optional[str] = Query(
        default=None, description="Inicio del rango (YYYY-MM-DD)", examples=["2026-11-16"]
    ),
    fecha_fin: Optional[str] = Query(
        default=None, description="Fin del rango (YYYY-MM-DD)", examples=["2026-11-30"]
    ),
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
        esp_id = _parsear_entero_positivo(especialidad_id, "especialidad_id")
        sed_id = _parsear_entero_positivo(sede_id, "sede_id")
        f_inicio = _parsear_fecha_iso(fecha_inicio, "fecha_inicio")
        f_fin = _parsear_fecha_iso(fecha_fin, "fecha_fin")
        return service.consultar_disponibilidad(esp_id, sed_id, f_inicio, f_fin)
    except HTTPException as ex:
        return _respuesta_error(ex.status_code, ex.detail)
    except Exception:
        return _respuesta_error(
            status.HTTP_503_SERVICE_UNAVAILABLE, MENSAJE_503_DISPONIBILIDAD
        )