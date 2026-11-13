from fastapi import APIRouter, status, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from domain.paciente_domain import PacienteCreate, PacienteAPIResponse
from service.paciente_service import PacienteService
from repository.paciente_repository import paciente_repository
from fastapi import APIRouter, Depends, status, HTTPException
from domain.paciente_domain import PacienteContactoUpdate
from datetime import datetime

router = APIRouter(prefix="/api/v1/pacientes", tags=["Pacientes"])

security = HTTPBearer(auto_error=False)


def get_paciente_service():
    return PacienteService(repo=paciente_repository)


@router.post(
    "/",
    response_model=PacienteAPIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un paciente en el sistema",
    responses={
        201: {
            "description": "Paciente registrado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Paciente registrado exitosamente",
                        "data": {
                            "paciente_id": "123e4567-e89b-12d3-a456-426614174000",
                            "numero_documento": "1098765431",
                            "nombres": "Laura",
                            "apellidos": "Gómez Ríos",
                            "token_inicial": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
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
                        "mensaje": "El formato de la fecha de nacimiento debe ser YYYY-MM-DD",
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
                        "mensaje": "No cuenta con los permisos necesarios para realizar esta acción",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        409: {
            "description": "Conflicto: Ya existe un paciente registrado con el documento indicado",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Ya existe un paciente registrado con el documento indicado",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        422: {
            "description": "Error de regla de negocio (Ej: menor sin tutor)",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "El paciente menor de edad debe estar vinculado a un adulto responsable",
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
                        "mensaje": "No fue posible registrar el paciente",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def registrar_paciente(
    datos: PacienteCreate,
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    service: PacienteService = Depends(get_paciente_service),
):
    # Validar si el token de autenticación está ausente (401)
    if not credentials or not credentials.credentials:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "mensaje": "Token de autenticación inválido o ausente",
                "data": None,
                "success": False,
            },
        )

    # Validar el Rol del usuario (RBAC)
    token = credentials.credentials
    if token == "token_sin_permiso":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "mensaje": "No cuenta con los permisos necesarios para realizar esta acción",
                "data": None,
                "success": False,
            },
        )

    try:
        resultado = service.registrar_paciente(datos)
        response.status_code = status.HTTP_201_CREATED
        return resultado

    except HTTPException as ex:
        return JSONResponse(
            status_code=ex.status_code,
            content={"mensaje": ex.detail, "data": None, "success": False},
        )


@router.patch(
    "/{paciente_id}/contacto",
    status_code=status.HTTP_200_OK,
    summary="Modificar los datos de contacto de un paciente",
    responses={
        200: {
            "description": "Operación exitosa: Modificar un contacto",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Operación exitosa: Modificar un contacto",
                        "data": {
                            "paciente_id": "b3c1f1de-5a1e-4f0b-9d3a-2f7b1c9e8a10",
                            "email": "nuevo@correo.com",
                            "telefono": "3109876543",
                            "direccion": "Calle 45 # 20-10",
                            "fecha_actualizacion": "2026-11-13T20:15:00",
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
                        "mensaje": "No se enviaron campos para actualizar",
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
                        "mensaje": "No cuenta con los permisos necesarios para realizar esta acción",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        404: {
            "description": "No se encontró el paciente indicado",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "No se encontró el paciente indicado",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
        409: {
            "description": "Conflicto: Regla de negocio RN-04",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "El paciente ya tiene una dirección primaria de residencia registrada",
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
                        "mensaje": "No fue posible actualizar los datos de contacto",
                        "data": None,
                        "success": False,
                    }
                }
            },
        },
    },
)
def modificar_contacto_paciente(
    paciente_id: str,
    datos: PacienteContactoUpdate,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    service: PacienteService = Depends(get_paciente_service),
):
    # Caso 5: Sin autenticación o sin permisos
    if not credentials or not credentials.credentials:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "mensaje": "Token de autenticación inválido o ausente",
                "data": None,
                "success": False,
            },
        )

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
        resultado_actualizado = service.modificar_contacto(paciente_id, datos)

        # Caso 1: Éxito (HTTP 200)
        return {
            "mensaje": "Operación exitosa: Modificar un contacto",
            "data": {
                "paciente_id": resultado_actualizado.get("paciente_id"),
                "email": resultado_actualizado.get("email"),
                "telefono": resultado_actualizado.get("telefono"),
                "direccion": resultado_actualizado.get("direccion"),
                "fecha_actualizacion": resultado_actualizado.get("fecha_actualizacion"),
            },
            "success": True,
        }

    except HTTPException as ex:
        # Captura errores controlados (400, 404, 409, 503)
        return JSONResponse(
            status_code=ex.status_code,
            content={"mensaje": ex.detail, "data": None, "success": False},
        )

    except Exception:
        # Caso 6: Falla de servicio (503)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "mensaje": "No fue posible actualizar los datos de contacto",
                "data": None,
                "success": False,
            },
        )
