# REGLAS DE NEGOCIO HU-031 (Domain Layer)
# Autenticarse y validar permisos por rol

import base64
import hashlib
import hmac
import json
import os
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

# RN-49: la cuenta se bloquea 30 minutos tras 3 intentos fallidos consecutivos.
MAX_INTENTOS_FALLIDOS = 3
BLOQUEO_MINUTOS = 30

# RN-47: la sesión expira a los 15 minutos.
EXPIRACION_SEGUNDOS = 15 * 60


def clave_secreta() -> str:
    return os.getenv("SECRET_KEY", "cambia-este-valor-en-produccion")


def _b64(datos: bytes) -> str:
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode("ascii")


def _b64_decodificar(texto: str) -> bytes:
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


def _firma(contenido: str, clave: Optional[str]) -> str:
    llave = (clave or clave_secreta()).encode("utf-8")
    return _b64(hmac.new(llave, contenido.encode("ascii"), hashlib.sha256).digest())


# JWT HS256: cabecera.payload.firma (ID, email, roles y expiración en el payload)
def firmar_jwt(payload: dict, clave: Optional[str] = None) -> str:
    cabecera = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    cuerpo = _b64(json.dumps(payload, separators=(",", ":")).encode())
    return f"{cabecera}.{cuerpo}.{_firma(cabecera + '.' + cuerpo, clave)}"


def verificar_jwt(token: str, clave: Optional[str] = None) -> dict:
    try:
        cabecera, cuerpo, firma = token.split(".")
        if not hmac.compare_digest(_firma(cabecera + "." + cuerpo, clave), firma):
            raise ValueError("firma inválida")
        return json.loads(_b64_decodificar(cuerpo))
    except Exception:
        raise ValueError("Token inválido")


def hashear_password(password: str, sal: Optional[bytes] = None) -> str:
    sal = sal or os.urandom(16)
    derivado = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), sal, 100_000)
    return sal.hex() + ":" + derivado.hex()


def verificar_password(password: str, almacenado: str) -> bool:
    sal_hex, hash_hex = almacenado.split(":")
    derivado = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(sal_hex), 100_000
    )
    return hmac.compare_digest(derivado.hex(), hash_hex)


# Compara el rol requerido (uno o varios separados por coma) contra los del token.
def tiene_rol(roles_token: list, rol_requerido: Optional[str]) -> bool:
    if not rol_requerido:
        return True
    requeridos = {r.strip().upper() for r in rol_requerido.split(",") if r.strip()}
    return bool(requeridos & {r.upper() for r in roles_token})


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["andres.perez@clinica.com"])
    password: str = Field(..., min_length=1, examples=["Clave12345!"])


class LoginData(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    roles: list[str]


class LoginAPIResponse(BaseModel):
    mensaje: str
    data: Optional[LoginData] = None
    success: bool


class PermisosData(BaseModel):
    autorizado: bool
    usuario_id: str
    roles: list[str]


class PermisosAPIResponse(BaseModel):
    mensaje: str
    data: Optional[PermisosData] = None
    success: bool
