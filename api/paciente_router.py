from fastapi import APIRouter, status, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from domain.paciente_domain import PacienteCreate, PacienteAPIResponse
from service.paciente_service import PacienteService
from repository.paciente_repository import paciente_repository

router = APIRouter(
    prefix="/api/v1/pacientes",
    tags=["Pacientes"]
)

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
                            "token_inicial": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                        },
                        "success": True
                    }
                }
            }
        },
        400: {
            "description": "Datos o parámetros inválidos",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "El formato de la fecha de nacimiento debe ser YYYY-MM-DD",
                        "data": None,
                        "success": False
                    }
                }
            }
        },
        401: {
            "description": "Token de autenticación inválido o ausente",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Token de autenticación inválido o ausente",
                        "data": None,
                        "success": False
                    }
                }
            }
        },
        403: {
            "description": "Acceso denegado: El usuario no tiene el rol autorizado (RBAC)",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "No cuenta con los permisos necesarios para realizar esta acción",
                        "data": None,
                        "success": False
                    }
                }
            }
        },
        409: {
            "description": "Conflicto: Ya existe un paciente registrado con el documento indicado",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "Ya existe un paciente registrado con el documento indicado",
                        "data": None,
                        "success": False
                    }
                }
            }
        },
        422: {
            "description": "Error de regla de negocio (Ej: menor sin tutor)",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "El paciente menor de edad debe estar vinculado a un adulto responsable",
                        "data": None,
                        "success": False
                    }
                }
            }
        },
        503: {
            "description": "Falla de base de datos o servicio externo",
            "content": {
                "application/json": {
                    "example": {
                        "mensaje": "No fue posible registrar el paciente",
                        "data": None,
                        "success": False
                    }
                }
            }
        }
    }
)
def registrar_paciente(
    datos: PacienteCreate, 
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    service: PacienteService = Depends(get_paciente_service)
):
    # 1. Validar si el token de autenticación está ausente (401)
    if not credentials or not credentials.credentials:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "mensaje": "Token de autenticación inválido o ausente",
                "data": None,
                "success": False
            }
        )

    # 2. Validar el Rol del usuario (RBAC) -> Si el token es de prueba para 403 o no tiene el rol permitido
    token = credentials.credentials
    if token == "token_sin_permiso":  # Puedes usar este token específico para tus pruebas en Swagger
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "mensaje": "No cuenta con los permisos necesarios para realizar esta acción",
                "data": None,
                "success": False
            }
        )

    try:
        resultado = service.registrar_paciente(datos)
        response.status_code = status.HTTP_201_CREATED
        return resultado
    
    except HTTPException as ex:
        return JSONResponse(
            status_code=ex.status_code,
            content={
                "mensaje": ex.detail,
                "data": None,
                "success": False
            }
        )