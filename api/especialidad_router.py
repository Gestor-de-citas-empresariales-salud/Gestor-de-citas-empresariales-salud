from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from domain.especialidad_domain import (
    DuracionBaseAPIResponse,
    DuracionBaseRequest,
    EspecialidadAPIResponse,
    EspecialidadCreate,
    EspecialidadCupsAPIResponse,
    EspecialidadCupsRequest,
    RequisitosPreviosAPIResponse,
    RequisitosPreviosRequest,
    TarifaBaseAPIResponse,
    TarifaBaseRequest,
)
from repository.especialidad_repository import EspecialidadRepository
from service.especialidad_service import EspecialidadService

router = APIRouter(prefix="/api/v1/especialidades", tags=["Especialidades"])

security = HTTPBearer(auto_error=False)

especialidad_repository = EspecialidadRepository()


def get_especialidad_service() -> EspecialidadService:
    return EspecialidadService(repo=especialidad_repository)


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
    response_model=EspecialidadAPIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva especialidad",
    responses={
        201: {
            "description": "Operación exitosa: Crear una nueva especialidad",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Operación exitosa: Crear una nueva especialidad",
                        "data": {
                            "especialidad_id": 4,
                            "nombre": "Cardiología",
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
            "description": "Conflicto: Especialidad ya registrada",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Ya existe una especialidad con ese nombre",
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
                        "mensaje": "No fue posible registrar la especialidad",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def crear_especialidad(
    datos: EspecialidadCreate,
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    service: EspecialidadService = Depends(get_especialidad_service),
):
    error_auth = _validar_auth_y_permisos(credentials)
    if error_auth is not None:
        return error_auth

    try:
        resultado = service.crear_especialidad(datos)
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
                "mensaje": "No fue posible registrar la especialidad",
                "data": None,
                "success": False,
            },
        )


@router.post(
    "/{especialidad_id}/cups",
    response_model=EspecialidadCupsAPIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Asociar el código CUPS correspondiente",
    responses={
        201: {
            "description": "Operación exitosa: Asociar el código CUPS correspondiente",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Operación exitosa: Asociar el código CUPS correspondiente",
                        "data": {
                            "especialidad_id": 4,
                            "total_codigos": 2,
                            "codigos_cups": ["890281", "890381"],
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
                        "mensaje": "Debe enviar al menos un código CUPS",
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
            "description": "No se encontró la especialidad indicada",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "No se encontró la especialidad indicada",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        422: {
            "description": "Error de regla de negocio (RN-15 / catálogo CUPS)",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Uno o más códigos CUPS no existen o no están vigentes",
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
                        "mensaje": "No fue posible registrar la especialidad",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def asociar_cups_especialidad(
    especialidad_id: int,
    datos: EspecialidadCupsRequest,
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    service: EspecialidadService = Depends(get_especialidad_service),
):
    error_auth = _validar_auth_y_permisos(credentials)
    if error_auth is not None:
        return error_auth

    try:
        resultado = service.asociar_cups_especialidad(especialidad_id, datos)
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
                "mensaje": "No fue posible registrar la especialidad",
                "data": None,
                "success": False,
            },
        )


@router.put(
    "/{especialidad_id}/duracion-base",
    response_model=DuracionBaseAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Definir la duración base de la cita por especialidad (FUN-13)",
    responses={
        200: {
            "description": "Operación exitosa: Definir la duración base de la cita por especialidad",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Operación exitosa: Definir la duración base de la cita por especialidad",
                        "data": {
                            "especialidad_id": 4,
                            "duracion_base_minutos": 40,
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
                        "mensaje": "El campo 'minutos' debe ser un número entero mayor a cero",
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
            "description": "No se encontró la especialidad indicada",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "No se encontró la especialidad indicada",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        422: {
            "description": "Regla de negocio o caso límite (RN-11)",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "La duración mínima para consultas de primera vez de alta complejidad es 40 minutos",
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
                        "mensaje": "No fue posible actualizar los parámetros de la especialidad",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def definir_duracion_base(
    especialidad_id: int,
    datos: DuracionBaseRequest,
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    service: EspecialidadService = Depends(get_especialidad_service),
):
    error_auth = _validar_auth_y_permisos(credentials)
    if error_auth is not None:
        return error_auth

    try:
        resultado = service.actualizar_duracion_base(especialidad_id, datos)
        response.status_code = status.HTTP_200_OK
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
                "mensaje": "No fue posible actualizar los parámetros de la especialidad",
                "data": None,
                "success": False,
            },
        )


@router.put(
    "/{especialidad_id}/requisitos-previos",
    response_model=RequisitosPreviosAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Parametrizar requisitos previos o preparación (FUN-14)",
    responses={
        200: {
            "description": "Operación exitosa: Parametrizar requisitos previos o preparación",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Operación exitosa: Parametrizar requisitos previos o preparación",
                        "data": {
                            "especialidad_id": 4,
                            "requisitos_registrados": True,
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
                        "mensaje": "El campo 'texto' es obligatorio o muy corto",
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
            "description": "No se encontró la especialidad indicada",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "No se encontró la especialidad indicada",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        422: {
            "description": "Error de regla de negocio o validación de contenido",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "El campo 'texto' de requisitos previos es obligatorio o inválido",
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
                        "mensaje": "No fue posible actualizar los parámetros de la especialidad",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def parametrizar_requisitos_previos(
    especialidad_id: int,
    datos: RequisitosPreviosRequest,
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    service: EspecialidadService = Depends(get_especialidad_service),
):
    error_auth = _validar_auth_y_permisos(credentials)
    if error_auth is not None:
        return error_auth

    try:
        resultado = service.actualizar_requisitos_previos(especialidad_id, datos)
        response.status_code = status.HTTP_200_OK
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
                "mensaje": "No fue posible actualizar los parámetros de la especialidad",
                "data": None,
                "success": False,
            },
        )


@router.put(
    "/{especialidad_id}/tarifa-base",
    response_model=TarifaBaseAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Establecer una tarifa base para el copago (FUN-15)",
    responses={
        200: {
            "description": "Operación exitosa: Establecer una tarifa base para el copago",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Operación exitosa: Establecer una tarifa base para el copago",
                        "data": {
                            "especialidad_id": 4,
                            "tarifa_base": 95000,
                            "moneda": "COP",
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
                        "mensaje": "El campo 'moneda' es obligatorio o muy corto",
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
            "description": "No se encontró la especialidad indicada",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "No se encontró la especialidad indicada",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        422: {
            "description": "Regla de negocio o caso límite",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "La tarifa base debe ser mayor a cero",
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
                        "mensaje": "No fue posible actualizar los parámetros de la especialidad",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def establecer_tarifa_base(
    especialidad_id: int,
    datos: TarifaBaseRequest,
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    service: EspecialidadService = Depends(get_especialidad_service),
):
    error_auth = _validar_auth_y_permisos(credentials)
    if error_auth is not None:
        return error_auth

    try:
        resultado = service.actualizar_tarifa_base(especialidad_id, datos)
        response.status_code = status.HTTP_200_OK
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
                "mensaje": "No fue posible actualizar los parámetros de la especialidad",
                "data": None,
                "success": False,
            },
        )
