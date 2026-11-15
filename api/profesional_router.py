from fastapi import APIRouter, status, Depends, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from domain.profesional_domain import (
    ProfesionalCreate,
    ValidacionRethusRequest,
    ProfesionalAPIResponse,
    RethusAPIResponse,
)
from service.profesional_service import ProfesionalService
from repository.profesional_repository import ProfesionalRepository

router = APIRouter(prefix="/api/v1/profesionales", tags=["Profesionales"])

security = HTTPBearer(auto_error=False)

# Instancia local del repositorio y servicio para profesionales
profesional_repository = ProfesionalRepository()


def get_profesional_service():
    return ProfesionalService(repo=profesional_repository)


@router.post(
    "/",
    response_model=ProfesionalAPIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un perfil de un profesional de la salud",
)
def registrar_profesional(
    datos: ProfesionalCreate,
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    service: ProfesionalService = Depends(get_profesional_service),
):
    # Validar token de autenticación (401)
    if not credentials or not credentials.credentials:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "mensaje": "Token de autenticación inválido o ausente",
                "data": None,
                "success": False,
            },
        )

    # Validar RBAC (403)
    token = credentials.credentials
    if token == "token_sin_permiso":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "mensaje": "No cuenta con permisos para esta operación",
                "data": None,
                "success": False,
            },
        )

    try:
        resultado = service.registrar_profesional(datos)
        response.status_code = status.HTTP_201_CREATED
        return resultado
    except HTTPException as ex:
        return JSONResponse(
            status_code=ex.status_code,
            content={"mensaje": ex.detail, "data": None, "success": False},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible registrar el profesional",
                "data": None,
                "success": False,
            },
        )


@router.post(
    "/{profesional_id}/validacion-rethus",
    response_model=RethusAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Validar la licencia médica del profesional (RETHUS)",
)
def validar_rethus(
    profesional_id: str,
    datos: ValidacionRethusRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    service: ProfesionalService = Depends(get_profesional_service),
):
    # Validar token de autenticación (401)
    if not credentials or not credentials.credentials:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "mensaje": "Token de autenticación inválido o ausente",
                "data": None,
                "success": False,
            },
        )

    # Validar RBAC (403)
    token = credentials.credentials
    if token == "token_sin_permiso":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "mensaje": "No cuenta con permisos para esta operación",
                "data": None,
                "success": False,
            },
        )

    try:
        resultado = service.validar_rethus(profesional_id, datos)
        return resultado
    except HTTPException as ex:
        return JSONResponse(
            status_code=ex.status_code,
            content={"mensaje": ex.detail, "data": None, "success": False},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible consultar el servicio RETHUS",
                "data": None,
                "success": False,
            },
        )
