from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status

from domain.auth_domain import (
    BLOQUEO_MINUTOS,
    EXPIRACION_SEGUNDOS,
    MAX_INTENTOS_FALLIDOS,
    LoginAPIResponse,
    LoginData,
    LoginRequest,
    firmar_jwt,
    tiene_rol,
    verificar_jwt,
    verificar_password,
)
from repository.auth_repository import AuthRepository

MENSAJE_401 = "Token de autenticación inválido o ausente"
MENSAJE_403 = "No cuenta con permisos para esta operación"
MENSAJE_BLOQUEO = "La cuenta se bloqueó temporalmente por 30 minutos"
MENSAJE_503_AUTH = "No fue posible validar las credenciales"


def ahora() -> datetime:
    # Reloj del servicio, separado para poder probar expiración y bloqueo
    return datetime.now()


class AuthService:
    def __init__(self, repo: AuthRepository):
        self.repo = repo

    # FUN-48: generar token JWT
    def login(self, datos: LoginRequest) -> LoginAPIResponse:
        email = str(datos.email).lower()

        # Falla de base de datos o servicio externo simulada
        if email == "falla-externa@clinica.com":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=MENSAJE_503_AUTH,
            )

        try:
            usuario = self.repo.buscar_por_email(email)
            momento = ahora()

            # RN-49: cuenta bloqueada temporalmente
            if usuario:
                hasta = self.repo.bloqueado_hasta(email)
                if hasta and momento < hasta:
                    raise HTTPException(status_code=423, detail=MENSAJE_BLOQUEO)
                if hasta:
                    self.repo.limpiar_bloqueo(email)

            if not usuario or not verificar_password(
                datos.password, usuario["password_hash"]
            ):
                if usuario:
                    intentos = self.repo.registrar_intento_fallido(email)
                    if intentos >= MAX_INTENTOS_FALLIDOS:
                        self.repo.bloquear(
                            email, momento + timedelta(minutes=BLOQUEO_MINUTOS)
                        )
                        raise HTTPException(status_code=423, detail=MENSAJE_BLOQUEO)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales incorrectas",
                )

            self.repo.limpiar_intentos(email)

            if not usuario["roles"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=MENSAJE_403
                )

            emitido = int(momento.timestamp())
            token = firmar_jwt(
                {
                    "sub": usuario["usuario_id"],
                    "email": usuario["email"],
                    "roles": usuario["roles"],
                    "iat": emitido,
                    "exp": emitido + EXPIRACION_SEGUNDOS,
                }
            )
            return LoginAPIResponse(
                mensaje="Operación exitosa: Generar token JWT",
                data=LoginData(
                    access_token=token,
                    token_type="Bearer",
                    expires_in=EXPIRACION_SEGUNDOS,
                    roles=usuario["roles"],
                ),
                success=True,
            )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=MENSAJE_503_AUTH,
            )

    # FUN-47: valida la firma, la expiración y los roles de un token
    def validar_token(self, token: Optional[str], rol_requerido: Optional[str] = None) -> dict:
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=MENSAJE_401)
        try:
            claims = verificar_jwt(token)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=MENSAJE_401)

        # RN-47: la sesión expira a los 15 minutos
        if claims.get("exp", 0) <= ahora().timestamp():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="La sesión expiró, inicie sesión nuevamente",
            )

        if not tiene_rol(claims.get("roles", []), rol_requerido):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=MENSAJE_403)
        return claims
