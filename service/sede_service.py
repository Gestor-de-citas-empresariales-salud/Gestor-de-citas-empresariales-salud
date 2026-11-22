from fastapi import HTTPException, status
from domain.sede_domain import (
    ConsultorioAPIResponse,
    ConsultorioCreadoData,
    ConsultorioCreate,
    SedeCreadaData,
    SedeCreate,
    SedeRegistroAPIResponse,
    validar_capacidad_sede,
    validar_coordenadas_sede,
    validar_sede_duplicada,
    validar_tipo_consultorio_rn17,
)
from repository.sede_repository import SedeRepository


class SedeService:
    def __init__(self, repo: SedeRepository) -> None:
        self.repo = repo

    def registrar_sede(self, datos: SedeCreate) -> SedeRegistroAPIResponse:
        try:
            sedes_existentes = self.repo.obtener_sedes_existentes()
        except RuntimeError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible registrar la sede o el consultorio",
            )

        try:
            validar_sede_duplicada(
                direccion=datos.direccion,
                ciudad=datos.ciudad,
                sedes_existentes=sedes_existentes,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            )

        try:
            latitud_valida, longitud_valida = validar_coordenadas_sede(
                latitud=datos.latitud,
                longitud=datos.longitud,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )

        try:
            creada = self.repo.crear_sede(
                nombre=datos.nombre,
                direccion=datos.direccion,
                ciudad=datos.ciudad,
                latitud=latitud_valida,
                longitud=longitud_valida,
            )
        except RuntimeError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible registrar la sede o el consultorio",
            )

        return SedeRegistroAPIResponse(
            mensaje="Operación exitosa: Registrar una sede física",
            data=SedeCreadaData(
                sede_id=creada["sede_id"],
                nombre=creada["nombre"],
            ),
            success=True,
        )

    def crear_consultorio(
        self, sede_id: int, datos: ConsultorioCreate
    ) -> ConsultorioAPIResponse:
        try:
            sede = self.repo.obtener_sede_por_id(sede_id)
        except RuntimeError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible registrar la sede o el consultorio",
            )

        if sede is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró la sede indicada",
            )

        try:
            actuales = self.repo.contar_consultorios_sede(sede_id)
        except RuntimeError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible registrar la sede o el consultorio",
            )

        capacidad_maxima = int(sede.get("capacidad_maxima", 0))

        try:
            validar_capacidad_sede(
                consultorios_actuales=actuales,
                capacidad_maxima=capacidad_maxima,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )

        try:
            tipo_valido = validar_tipo_consultorio_rn17(
                tipo_consultorio=datos.tipo,
                tipo_sede=sede.get("tipo_sede"),
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )

        try:
            creado = self.repo.crear_consultorio(
                sede_id=sede_id,
                codigo=datos.codigo,
                tipo=tipo_valido,
            )
        except RuntimeError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible registrar la sede o el consultorio",
            )

        return ConsultorioAPIResponse(
            mensaje="Operación exitosa: Crear un consultorio u oficina",
            data=ConsultorioCreadoData(
                consultorio_id=creado["consultorio_id"],
                sede_id=creado["sede_id"],
                codigo=creado["codigo"],
                tipo=creado["tipo"],
            ),
            success=True,
        )
