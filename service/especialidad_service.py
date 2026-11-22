from fastapi import HTTPException, status
from domain.especialidad_domain import (
    DuracionBaseAPIResponse,
    DuracionBaseData,
    DuracionBaseRequest,
    EspecialidadAPIResponse,
    EspecialidadCreadaData,
    EspecialidadCreate,
    EspecialidadCupsAPIResponse,
    EspecialidadCupsData,
    EspecialidadCupsRequest,
    RequisitosPreviosAPIResponse,
    RequisitosPreviosData,
    RequisitosPreviosRequest,
    TarifaBaseAPIResponse,
    TarifaBaseData,
    TarifaBaseRequest,
    validar_codigos_cups_vigentes,
    validar_duracion_base_especialidad,
    validar_nombre_especialidad_duplicado,
    validar_requisitos_previos_texto,
    validar_tarifa_base_especialidad,
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

    def actualizar_duracion_base(
        self, especialidad_id: int, datos: DuracionBaseRequest
    ) -> DuracionBaseAPIResponse:
        try:
            especialidad = self.repo.obtener_especialidad_por_id(especialidad_id)
        except RuntimeError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible actualizar los parámetros de la especialidad",
            )

        if especialidad is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró la especialidad indicada",
            )

        alta_complejidad = bool(especialidad.get("alta_complejidad", False))

        try:
            minutos_validos = validar_duracion_base_especialidad(
                minutos=datos.minutos,
                alta_complejidad=alta_complejidad,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )

        try:
            actualizado = self.repo.actualizar_duracion_base(
                especialidad_id=especialidad_id,
                duracion_base_minutos=minutos_validos,
            )
        except RuntimeError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible actualizar los parámetros de la especialidad",
            )

        return DuracionBaseAPIResponse(
            mensaje="Operación exitosa: Definir la duración base de la cita por especialidad",
            data=DuracionBaseData(
                especialidad_id=actualizado["especialidad_id"],
                duracion_base_minutos=actualizado["duracion_base_minutos"],
            ),
            success=True,
        )

    def actualizar_requisitos_previos(
        self, especialidad_id: int, datos: RequisitosPreviosRequest
    ) -> RequisitosPreviosAPIResponse:
        try:
            especialidad = self.repo.obtener_especialidad_por_id(especialidad_id)
        except RuntimeError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible actualizar los parámetros de la especialidad",
            )

        if especialidad is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró la especialidad indicada",
            )

        try:
            texto_valido = validar_requisitos_previos_texto(datos.texto)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )

        try:
            actualizado = self.repo.actualizar_requisitos_previos(
                especialidad_id=especialidad_id,
                texto_requisitos=texto_valido,
            )
        except RuntimeError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible actualizar los parámetros de la especialidad",
            )

        return RequisitosPreviosAPIResponse(
            mensaje="Operación exitosa: Parametrizar requisitos previos o preparación",
            data=RequisitosPreviosData(
                especialidad_id=actualizado["especialidad_id"],
                requisitos_registrados=actualizado["requisitos_registrados"],
            ),
            success=True,
        )

    def actualizar_tarifa_base(
        self, especialidad_id: int, datos: TarifaBaseRequest
    ) -> TarifaBaseAPIResponse:
        try:
            especialidad = self.repo.obtener_especialidad_por_id(especialidad_id)
        except RuntimeError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible actualizar los parámetros de la especialidad",
            )

        if especialidad is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró la especialidad indicada",
            )

        try:
            valor_valido, moneda_valida = validar_tarifa_base_especialidad(
                valor=datos.valor,
                moneda=datos.moneda,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )

        try:
            actualizado = self.repo.actualizar_tarifa_base(
                especialidad_id=especialidad_id,
                tarifa_base=valor_valido,
                moneda=moneda_valida,
            )
        except RuntimeError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible actualizar los parámetros de la especialidad",
            )

        return TarifaBaseAPIResponse(
            mensaje="Operación exitosa: Establecer una tarifa base para el copago",
            data=TarifaBaseData(
                especialidad_id=actualizado["especialidad_id"],
                tarifa_base=actualizado["tarifa_base"],
                moneda=actualizado["moneda"],
            ),
            success=True,
        )
