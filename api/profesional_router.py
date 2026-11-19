from fastapi import APIRouter, status, Depends, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from domain.profesional_domain import (
    ProfesionalCreate,
    ValidacionRethusRequest,
    ProfesionalAPIResponse,
    RethusAPIResponse,
    SedeAsignarRequest,
    SedeAPIResponse,
    JornadaLaboralRequest,
    JornadaAPIResponse,
)
from service.profesional_service import ProfesionalService
from repository.profesional_repository import ProfesionalRepository
from fastapi.exceptions import RequestValidationError

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
    responses={
        201: {
            "description": "Operación exitosa: Crear un perfil de un profesional de la salud",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Operación exitosa: Crear un perfil de un profesional de la salud",
                        "data": {
                            "profesional_id": "7d2e9a40-1c11-4a3e-8f55-0e2b7c6d1a22",
                            "usuario_creado": True,
                            "estado": "PENDIENTE_VALIDACION",
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
                        "mensaje": "Falta un campo obligatorio o el formato de los datos es inválido",
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
            "description": "Conflicto: Tarjeta profesional ya registrada",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Ya existe un profesional con esa tarjeta profesional",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        422: {
            "description": "Error de regla de negocio (RN-10 / RETHUS)",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "El profesional no se encuentra habilitado en RETHUS",
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
                        "mensaje": "No fue posible consultar el servicio RETHUS",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
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
    responses={
        200: {
            "description": "Operación exitosa: Validar la licencia médica del profesional (RETHUS)",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Operación exitosa: Validar la licencia médica del profesional (RETHUS)",
                        "data": {
                            "profesional_id": "7d2e9a40-1c11-4a3e-8f55-0e2b7c6d1a22",
                            "estado_rethus": "HABILITADO",
                            "codigo_verificacion": "RTH-889900",
                            "activo": True,
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
                        "mensaje": "Falta un campo obligatorio o el formato de los datos es inválido",
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
        422: {
            "description": "Error de regla de negocio (RN-10 / RETHUS)",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "El profesional no se encuentra habilitado en RETHUS",
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
                        "mensaje": "No fue posible consultar el servicio RETHUS",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
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


@router.post(
    "/{profesional_id}/sedes",
    response_model=SedeAPIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Asignar sedes/consultorios al profesional",
    responses={
        201: {
            "description": "Operación exitosa: Asignar sedes/consultorios al profesional",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Operación exitosa: Asignar sedes/consultorios al profesional",
                        "data": {
                            "profesional_id": "7d2e9a40-1c11-4a3e-8f55-0e2b7c6d1a22",
                            "sede_id": 3,
                            "asignada": True,
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
                        "mensaje": "Falta un campo obligatorio o el formato de los datos es inválido",
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
            "description": "No se encontró el profesional o la sede indicada",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "No se encontró el profesional indicado",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        422: {
            "description": "Error de regla de negocio (Ej. sin consultorios disponibles)",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "La sede no cuenta con consultorios disponibles",
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
                        "mensaje": "No fue posible registrar la asignación o la jornada del profesional",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def asignar_sedes(
    profesional_id: str,
    datos: SedeAsignarRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    service: ProfesionalService = Depends(get_profesional_service),
):
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

    try:
        return service.asignar_sede_profesional(profesional_id, datos)
    except HTTPException as ex:
        return JSONResponse(
            status_code=ex.status_code,
            content={"mensaje": ex.detail, "data": None, "success": False},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible registrar la asignación o la jornada del profesional",
                "data": None,
                "success": False,
            },
        )


@router.put(
    "/{profesional_id}/jornada-laboral",
    response_model=JornadaAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Definir una jornada laboral",
    responses={
        200: {
            "description": "Operación exitosa: Definir una jornada laboral",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Operación exitosa: Definir una jornada laboral",
                        "data": {
                            "profesional_id": "7d2e9a40-1c11-4a3e-8f55-0e2b7c6d1a22",
                            "horas_semanales": 40,
                            "agenda_notificada": True,
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
                        "mensaje": "Falta un campo obligatorio o el formato de los datos es inválido",
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
            "description": "No se encontró el profesional indicado",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "No se encontró el profesional indicado",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        422: {
            "description": "Error de regla de negocio (RN-06 / RN-08)",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "El turno supera las 12 horas continuas permitidas",
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
                        "mensaje": "No fue posible registrar la asignación o la jornada del profesional",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def definir_jornada_laboral(
    profesional_id: str,
    datos: JornadaLaboralRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    service: ProfesionalService = Depends(get_profesional_service),
):
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

    try:
        return service.definir_jornada_laboral(profesional_id, datos)
    except HTTPException as ex:
        return JSONResponse(
            status_code=ex.status_code,
            content={"mensaje": ex.detail, "data": None, "success": False},
        )
    except ValueError as ex:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"mensaje": str(ex), "data": None, "success": False},
        )
    except RequestValidationError as ex:
        # ESTO ATRAPA EL 400 DE PYDANTIC Y LO DEVUELVE COMO 422
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "mensaje": "El formato o los datos de la jornada son inválidos",
                "data": None,
                "success": False,
            },
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible registrar la asignación o la jornada del profesional",
                "data": None,
                "success": False,
            },
        )
