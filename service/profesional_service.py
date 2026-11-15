from fastapi import HTTPException, status
from domain.profesional_domain import (
    ProfesionalCreate,
    ValidacionRethusRequest,
    ProfesionalAPIResponse,
    ProfesionalResponseData,
    RethusAPIResponse,
    RethusResponseData,
    validar_regla_rethus,
    validar_tarjeta_duplicada,
    validar_documento_duplicado,
)
from repository.profesional_repository import ProfesionalRepository


class ProfesionalService:
    def __init__(self, repo: ProfesionalRepository):
        self.repo = repo

    # Caso 7: Falla de base de datos o servicio externo simulada
    def registrar_profesional(self, datos: ProfesionalCreate) -> ProfesionalAPIResponse:

        if datos.numero_documento == "99999999":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible registrar el profesional",
            )
        # Aplicar regla de negocio de documento duplicado (Dominio)
        documentos_existentes = [
            p["numero_documento"] for p in self.repo._db_profesionales
        ]
        try:
            validar_documento_duplicado(datos.numero_documento, documentos_existentes)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )

        # Aplicar regla de negocio de tarjeta duplicada (Dominio)
        tarjetas_existentes = [
            p["tarjeta_profesional"] for p in self.repo._db_profesionales
        ]
        try:
            validar_tarjeta_duplicada(datos.tarjeta_profesional, tarjetas_existentes)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )

        # Aplicar regla de negocio de tarjeta duplicada (Dominio)
        tarjetas_existentes = [
            p["tarjeta_profesional"] for p in self.repo._db_profesionales
        ]
        try:
            validar_tarjeta_duplicada(datos.tarjeta_profesional, tarjetas_existentes)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )

        try:
            # Caso 1: Éxito – Crear perfil (HTTP 201)
            profesional_creado = self.repo.crear_profesional(datos)

            print(
                f"[AUTH SYSTEM] Usuario médico creado para el email: {datos.email} con rol 'Médico'."
            )

            return ProfesionalAPIResponse(
                mensaje="Operación exitosa: Crear un perfil de un profesional de la salud",
                data=ProfesionalResponseData(
                    profesional_id=profesional_creado["profesional_id"],
                    usuario_creado=True,
                    estado=profesional_creado["estado"],
                ),
                success=True,
            )
        except HTTPException as he:
            raise he
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible registrar el profesional",
            )

    # Caso 7: Falla simulada de servicio externo RETHUS
    def validar_rethus(
        self, profesional_id: str, datos: ValidacionRethusRequest
    ) -> RethusAPIResponse:

        if profesional_id == "falla-externa" or datos.numero_documento == "99999999":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible consultar el servicio RETHUS",
            )

        # Buscar el profesional en el repositorio
        profesional = self.repo.buscar_por_id(profesional_id)
        if not profesional:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró el profesional indicado",
            )

        # Aplicar regla de negocio RETHUS (Dominio - RN-10)
        try:
            validar_regla_rethus(datos.tarjeta_profesional, datos.numero_documento)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e),
            )

        try:
            # Caso 2: Éxito – Validación RETHUS (HTTP 200)
            estado_rethus = "HABILITADO"
            codigo_verificacion = "RTH-889900"
            activo = True

            actualizado = self.repo.actualizar_rethus(
                profesional_id=profesional_id,
                estado_rethus=estado_rethus,
                codigo_verificacion=codigo_verificacion,
                activo=activo,
            )

            return RethusAPIResponse(
                mensaje="Operación exitosa: Validar la licencia médica del profesional (RETHUS)",
                data=RethusResponseData(
                    profesional_id=actualizado["profesional_id"],
                    estado_rethus=actualizado["estado_rethus"],
                    codigo_verificacion=actualizado["codigo_verificacion"],
                    activo=actualizado["activo"],
                ),
                success=True,
            )
        except HTTPException as he:
            raise he
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible consultar el servicio RETHUS",
            )
