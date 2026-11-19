from fastapi import HTTPException, status
from domain.especialidad_domain import (
    EspecialidadAPIResponse,
    EspecialidadCreadaData,
    EspecialidadCreate,
    EspecialidadCupsAPIResponse,
    EspecialidadCupsData,
    EspecialidadCupsRequest,
    validar_codigos_cups_vigentes,
    validar_nombre_especialidad_duplicado,
)
from repository.especialidad_repository import EspecialidadRepository


class EspecialidadService:
    def __init__(self, repo: EspecialidadRepository) -> None:
        self.repo = repo

    def crear_especialidad(self, datos: EspecialidadCreate) -> EspecialidadAPIResponse:
        nombres_existentes = self.repo.obtener_nombres_especialidades()

        try:
            validar_nombre_especialidad_duplicado(datos.nombre, nombres_existentes)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            )

        creada = self.repo.crear_especialidad(
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            alta_complejidad=datos.alta_complejidad,
        )

        return EspecialidadAPIResponse(
            mensaje="Operación exitosa: Crear una nueva especialidad",
            data=EspecialidadCreadaData(
                especialidad_id=creada["especialidad_id"],
                nombre=creada["nombre"],
            ),
            success=True,
        )

    def asociar_cups_especialidad(
        self, especialidad_id: int, datos: EspecialidadCupsRequest
    ) -> EspecialidadCupsAPIResponse:
        especialidad = self.repo.obtener_especialidad_por_id(especialidad_id)
        if especialidad is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró la especialidad indicada",
            )

        catalogo_cups = self.repo.obtener_catalogo_cups()

        try:
            codigos_validos = validar_codigos_cups_vigentes(
                datos.codigos_cups, catalogo_cups
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )

        asociacion = self.repo.asociar_codigos_cups(especialidad_id, codigos_validos)

        return EspecialidadCupsAPIResponse(
            mensaje="Operación exitosa: Asociar el código CUPS correspondiente",
            data=EspecialidadCupsData(
                especialidad_id=asociacion["especialidad_id"],
                total_codigos=asociacion["total_codigos"],
                codigos_cups=asociacion["codigos_cups"],
            ),
            success=True,
        )
