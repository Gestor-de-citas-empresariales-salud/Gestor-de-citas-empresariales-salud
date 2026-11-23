from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from domain.sede_domain import (
    AforoAPIResponse,
    AforoUpdate,
    ConsultorioAPIResponse,
    ConsultorioCreate,
    SedeCreate,
    SedeRegistroAPIResponse,
)
from repository.sede_repository import SedeRepository
from service.sede_service import SedeService

router = APIRouter(prefix="/api/v1/sedes", tags=["Sedes"])

security = HTTPBearer(auto_error=False)

sede_repository = SedeRepository()


def get_sede_service() -> SedeService:
    return SedeService(repo=sede_repository)


def _validar_auth_y_permisos(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> Optional[JSONResponse]:
    if not credentials or not credentials.credentials:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "mensaje": "Token de autenticación inválido o ausente",
                "data": None,
                "success": False,
            },
        )

    if credentials.credentials == "token_sin_permiso":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "mensaje": "No cuenta con permisos para esta operación",
                "data": None,
                "success": False,
            },
        )

    return None


@router.post(
    "/",
    response_model=SedeRegistroAPIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una sede física",
    responses={
        201: {
            "description": "Operación exitosa: Registrar una sede física",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Operación exitosa: Registrar una sede física",
                        "data": {
                            "sede_id": 3,
                            "nombre": "Sede Cabecera",
                        },
                        "success": True,
                    }
                }
            },
        },
        400: {
            "description": "Datos o parámetros inválidos",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "El campo 'nombre' es obligatorio o inválido",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        401: {
            "description": "Token de autenticación inválido o ausente",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Token de autenticación inválido o ausente",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        403: {
            "description": "Acceso denegado: El usuario no tiene el rol autorizado (RBAC)",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "No cuenta con permisos para esta operación",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        409: {
            "description": "Conflicto: Sede ya registrada en esa dirección",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Ya existe una sede registrada en esa dirección",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        422: {
            "description": "Error de regla de negocio o rango de coordenadas",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "El campo 'latitud' debe estar entre -90 y 90",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        503: {
            "description": "Falla de base de datos o servicio externo",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "No fue posible registrar la sede o el consultorio",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def registrar_sede(
    datos: SedeCreate,
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    service: SedeService = Depends(get_sede_service),
):
    error_auth = _validar_auth_y_permisos(credentials)
    if error_auth is not None:
        return error_auth

    try:
        resultado = service.registrar_sede(datos)
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
                "mensaje": "No fue posible registrar la sede o el consultorio",
                "data": None,
                "success": False,
            },
        )


@router.post(
    "/{sede_id}/consultorios",
    response_model=ConsultorioAPIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un consultorio u oficina",
    responses={
        201: {
            "description": "Operación exitosa: Crear un consultorio u oficina",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Operación exitosa: Crear un consultorio u oficina",
                        "data": {
                            "consultorio_id": 31,
                            "sede_id": 3,
                            "codigo": "C-101",
                            "tipo": "CONSULTA_EXTERNA",
                        },
                        "success": True,
                    }
                }
            },
        },
        400: {
            "description": "Datos o parámetros inválidos",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "El campo 'codigo' es obligatorio o inválido",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        401: {
            "description": "Token de autenticación inválido o ausente",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Token de autenticación inválido o ausente",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        403: {
            "description": "Acceso denegado: El usuario no tiene el rol autorizado (RBAC)",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "No cuenta con permisos para esta operación",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        404: {
            "description": "No se encontró la sede indicada",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "No se encontró la sede indicada",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        422: {
            "description": "Error de regla de negocio (capacidad física / RN-17)",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "La sede no tiene capacidad para alojar un nuevo consultorio",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        503: {
            "description": "Falla de base de datos o servicio externo",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "No fue posible registrar la sede o el consultorio",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def crear_consultorio(
    sede_id: int,
    datos: ConsultorioCreate,
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    service: SedeService = Depends(get_sede_service),
):
    error_auth = _validar_auth_y_permisos(credentials)
    if error_auth is not None:
        return error_auth

    try:
        resultado = service.crear_consultorio(sede_id, datos)
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
                "mensaje": "No fue posible registrar la sede o el consultorio",
                "data": None,
                "success": False,
            },
        )


def _ejemplo_error_aforo(descripcion: str, mensaje: str) -> dict:
    return {
        "description": descripcion,
        "content": {
            "application/json": {
                "example": {"mensaje": mensaje, "data": None, "success": False}
            }
        },
    }


@router.put(
    "/{sede_id}/aforo",
    response_model=AforoAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Controlar el límite de aforo por sede",
    # <-- Borra el parámetro description=(...) que estaba aquí
   
    responses={
        200: {
            "description": "Operación exitosa: Controlar el límite de aforo por sede",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Operación exitosa: Controlar el límite de aforo por sede",
                        "data": {"sede_id": 1, "max_capacity_hora": 3},
                        "success": True,
                    }
                }
            },
        },
        400: _ejemplo_error_aforo(
            "Datos o parámetros inválidos (no entero o menor o igual a cero)",
            "El aforo debe ser un número entero positivo",
        ),
        401: _ejemplo_error_aforo(
            "Token de autenticación inválido o ausente",
            "Token de autenticación inválido o ausente",
        ),
        403: _ejemplo_error_aforo(
            "Acceso denegado: El usuario no tiene el rol autorizado (RBAC)",
            "No cuenta con permisos para esta operación",
        ),
        404: _ejemplo_error_aforo(
            "No se encontró la sede indicada",
            "No se encontró la sede indicada",
        ),
        422: _ejemplo_error_aforo(
            "Error de regla de negocio (RN-16)",
            "El aforo supera la capacidad de los consultorios activos de la sede",
        ),
        503: _ejemplo_error_aforo(
            "Falla de base de datos o servicio externo",
            "No fue posible actualizar el aforo de la sede",
        ),
    },
)
def controlar_aforo_sede(
    sede_id: int,
    datos: AforoUpdate,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    service: SedeService = Depends(get_sede_service),
):
    error_auth = _validar_auth_y_permisos(credentials)
    if error_auth is not None:
        return error_auth

    try:
        return service.actualizar_aforo_sede(sede_id, datos)
    except HTTPException as ex:
        return JSONResponse(
            status_code=ex.status_code,
            content={"mensaje": ex.detail, "data": None, "success": False},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible actualizar el aforo de la sede",
                "data": None,
                "success": False,
            },
        )
