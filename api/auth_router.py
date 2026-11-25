from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

from domain.auth_domain import (
    LoginAPIResponse,
    LoginRequest,
    PermisosAPIResponse,
    PermisosData,
)
from repository.auth_repository import auth_repository
from service.auth_service import (
    MENSAJE_401,
    MENSAJE_503_AUTH,
    AuthService,
)

router = APIRouter(tags=["Autenticación"])

security = HTTPBearer(auto_error=False)

auth_service = AuthService(repo=auth_repository)


def get_auth_service():
    return auth_service


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


# Rutas internas entre módulos: la validación de token y roles ocurre aquí, antes
# del controlador, y no en la lógica de negocio. Las demás rutas pasan sin cambios.
PREFIJO_RUTAS_PROTEGIDAS = "/internal/"


class RBACMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith(PREFIJO_RUTAS_PROTEGIDAS):
            return await call_next(request)

        autorizacion = request.headers.get("authorization", "")
        token = autorizacion[7:].strip() if autorizacion.lower().startswith("bearer ") else None
        try:
            request.state.claims = auth_service.validar_token(
                token, request.query_params.get("rol_requerido")
            )
        except HTTPException as ex:
            return _respuesta_error(ex.status_code, ex.detail)
        except Exception:
            return _respuesta_error(status.HTTP_503_SERVICE_UNAVAILABLE, MENSAJE_503_AUTH)
        return await call_next(request)


@router.post(
    "/api/v1/auth/login",
    response_model=LoginAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Generar token JWT",
    description=(
        ""
    ),
    responses={
        400: _ejemplo_error(
            "Datos o parámetros inválidos",
            "Error en el campo 'password': Field required",
        ),
        401: _ejemplo_error("Credenciales inválidas", "Credenciales incorrectas"),
        403: _ejemplo_error(
            "El usuario no tiene un rol con permiso",
            "No cuenta con permisos para esta operación",
        ),
        423: _ejemplo_error(
            "Cuenta bloqueada por intentos fallidos (RN-49)",
            "La cuenta se bloqueó temporalmente por 30 minutos",
        ),
        503: _ejemplo_error("Falla de base de datos o servicio externo", MENSAJE_503_AUTH),
    },
)
def login(datos: LoginRequest, service: AuthService = Depends(get_auth_service)):
    try:
        return service.login(datos)
    except HTTPException as ex:
        return _respuesta_error(ex.status_code, ex.detail)
    except Exception:
        return _respuesta_error(status.HTTP_503_SERVICE_UNAVAILABLE, MENSAJE_503_AUTH)


@router.get(
    "/internal/auth/validar-permisos",
    response_model=PermisosAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Validar los permisos de rol (uso interno entre módulos)",
    description=(
        ""
    ),
    responses={
        401: _ejemplo_error("Token inválido, vencido o ausente", MENSAJE_401),
        403: _ejemplo_error(
            "El rol del token no está entre los requeridos",
            "No cuenta con permisos para esta operación",
        ),
        503: _ejemplo_error("Falla de base de datos o servicio externo", MENSAJE_503_AUTH),
    },
)
def validar_permisos(
    request: Request,
    rol_requerido: Optional[str] = Query(
        None, description="Rol (o roles separados por coma) exigidos", examples=["MEDICO"]
    ),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    claims = getattr(request.state, "claims", None)
    if not claims:
        return _respuesta_error(status.HTTP_401_UNAUTHORIZED, MENSAJE_401)
    return PermisosAPIResponse(
        mensaje="Operación exitosa: Validar los permisos de rol",
        data=PermisosData(
            autorizado=True, usuario_id=claims["sub"], roles=claims["roles"]
        ),
        success=True,
    )
