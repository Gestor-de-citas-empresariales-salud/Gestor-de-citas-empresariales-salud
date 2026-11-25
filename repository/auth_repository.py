from datetime import datetime
from typing import Optional

from domain.auth_domain import hashear_password


class AuthRepository:
    # Base de datos en memoria para usuarios, intentos fallidos y bloqueos
    def __init__(self):
        # PROVISIONAL: usuarios de ejemplo con la contraseña Clave12345!
        # (guardada con hash PBKDF2, nunca en texto plano).
        clave = hashear_password("Clave12345!")
        self._usuarios = {
            "andres.perez@clinica.com": {
                "usuario_id": "7d2e9a40-1c11-4a3e-8f55-0e2b7c6d1a22",
                "email": "andres.perez@clinica.com",
                "password_hash": clave,
                "roles": ["MEDICO"],
            },
            "recepcion@clinica.com": {
                "usuario_id": "1f0a9c2e-6b7d-4e3a-8c51-9d2b4a7e6f30",
                "email": "recepcion@clinica.com",
                "password_hash": clave,
                "roles": ["RECEPCIONISTA"],
            },
            "admin@clinica.com": {
                "usuario_id": "2a7c5e91-3d8b-4f60-a1c4-7e9b0d3f5a28",
                "email": "admin@clinica.com",
                "password_hash": clave,
                "roles": ["ADMINISTRADOR"],
            },
            "sin.rol@clinica.com": {
                "usuario_id": "3c9e1b74-5a2d-4d80-b6f3-1a8c7e0d9b45",
                "email": "sin.rol@clinica.com",
                "password_hash": clave,
                "roles": [],
            },
        }
        self._intentos_fallidos = {}
        self._bloqueos = {}

    def buscar_por_email(self, email: str) -> Optional[dict]:
        return self._usuarios.get(email)

    def registrar_intento_fallido(self, email: str) -> int:
        self._intentos_fallidos[email] = self._intentos_fallidos.get(email, 0) + 1
        return self._intentos_fallidos[email]

    def limpiar_intentos(self, email: str) -> None:
        self._intentos_fallidos.pop(email, None)

    def bloquear(self, email: str, hasta: datetime) -> None:
        self._bloqueos[email] = hasta
        self._intentos_fallidos.pop(email, None)

    def bloqueado_hasta(self, email: str) -> Optional[datetime]:
        return self._bloqueos.get(email)

    def limpiar_bloqueo(self, email: str) -> None:
        self._bloqueos.pop(email, None)


auth_repository = AuthRepository()
