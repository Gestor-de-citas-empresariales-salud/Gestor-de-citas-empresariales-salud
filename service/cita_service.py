from fastapi import HTTPException, status

from datetime import datetime

from domain.agenda_domain import ESTADO_DISPONIBLE
from domain.cita_domain import (
    CitaAPIResponse,
    CitaCanceladaAPIResponse,
    CitaCanceladaData,
    CitaReprogramadaAPIResponse,
    CitaReprogramadaData,
    CancelarCitaRequest,
    ReprogramarCitaRequest,
    validar_anticipacion,
    validar_estado_reservada,
    validar_formato_cita_id,
    CheckinAPIResponse,
    CheckinData,
    ESTADO_CITA_CANCELADA,
    validar_dia_checkin,
    CitaReservadaData,
    ReservarCitaRequest,
    ESTADO_ESPACIO_OCUPADO,
    validar_cobertura_eps,
    validar_espacio_libre,
    validar_inasistencias,
)
from repository.agenda_repository import AgendaRepository
from repository.cita_repository import CitaRepository

MENSAJE_503_CITA = "No fue posible agendar la cita"
MENSAJE_503_MODIFICAR_CITA = "No fue posible reprogramar o cancelar la cita"
MENSAJE_503_CHECKIN = "No fue posible registrar la llegada del paciente"


def ahora() -> datetime:
    # Reloj del servicio, separado para poder probar la regla de anticipación
    return datetime.now()


class CitaService:
    def __init__(self, paciente_repo, agenda_repo: AgendaRepository, cita_repo: CitaRepository):
        self.paciente_repo = paciente_repo
        self.agenda_repo = agenda_repo
        self.cita_repo = cita_repo

    # FUN-26: agendar una cita médica
    def reservar_cita(self, datos: ReservarCitaRequest) -> CitaAPIResponse:
        # Caso 7: falla de base de datos o servicio externo simulada
        if datos.paciente_id == "falla-externa":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=MENSAJE_503_CITA,
            )

        # 1. Validar al paciente (MOD-01)
        paciente = next(
            (p for p in self.paciente_repo._db_pacientes
             if p["paciente_id"] == datos.paciente_id),
            None,
        )
        if not paciente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró el paciente indicado",
            )
        id_paciente = paciente["paciente_id"]

        # RN-27: inasistencias injustificadas
        try:
            validar_inasistencias(
                self.cita_repo.contar_inasistencias_injustificadas(id_paciente)
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        # 2. Validar el espacio de la agenda (MOD-05)
        espacio = next(
            (f for f in self.agenda_repo._db_franjas
             if str(f["espacio_id"]) == str(datos.espacio_id)),
            None,
        )
        if not espacio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró el espacio indicado",
            )
        try:
            validar_espacio_libre(espacio["estado"], ESTADO_DISPONIBLE)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

        # 3. Validar la cobertura (MOD-08), RN-36
        try:
            validar_cobertura_eps(self.cita_repo.convenio_eps_suspendido(id_paciente))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        # 4. Transacción: ocupar el espacio y crear la cita; si algo falla se revierte
        estado_anterior = espacio["estado"]
        cita = None
        try:
            espacio["estado"] = ESTADO_ESPACIO_OCUPADO
            cita = self.cita_repo.crear_cita(id_paciente, espacio)
            self.cita_repo.emitir_evento_notificacion(cita)
        except Exception:
            espacio["estado"] = estado_anterior
            if cita:
                self.cita_repo.eliminar_cita(cita["cita_id"])
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=MENSAJE_503_CITA,
            )

        return CitaAPIResponse(
            mensaje="Operación exitosa: Agendar una cita médica",
            data=CitaReservadaData(
                cita_id=cita["cita_id"],
                estado=cita["estado"],
                fecha=cita["fecha"],
                hora_inicio=cita["hora_inicio"],
                profesional_id=cita["profesional_id"],
                sede_id=cita["sede_id"],
            ),
            success=True,
        )

    def _buscar_espacio(self, espacio_id):
        return next(
            (f for f in self.agenda_repo._db_franjas
             if str(f["espacio_id"]) == str(espacio_id)),
            None,
        )

    def _cita_a_modificar(self, cita_id: str, mensaje_503: str) -> dict:
        # Falla de base de datos o servicio externo simulada
        if cita_id == "falla-externa":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=mensaje_503
            )
        try:
            validar_formato_cita_id(cita_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        cita = self.cita_repo.buscar_cita(cita_id)
        if not cita:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró la cita indicada",
            )
        return cita

    def _validar_modificable(self, cita: dict) -> None:
        try:
            validar_estado_reservada(cita["estado"])
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
        try:
            validar_anticipacion(cita, ahora())
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

    # FUN-27: reprogramar una cita médica
    def reprogramar_cita(
        self, cita_id: str, datos: ReprogramarCitaRequest
    ) -> CitaReprogramadaAPIResponse:
        cita = self._cita_a_modificar(cita_id, MENSAJE_503_MODIFICAR_CITA)
        self._validar_modificable(cita)

        nuevo = self._buscar_espacio(datos.nuevo_espacio_id)
        if not nuevo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró el espacio indicado",
            )
        try:
            validar_espacio_libre(nuevo["estado"], ESTADO_DISPONIBLE)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

        # Transacción: libera el espacio anterior, ocupa el nuevo y actualiza la cita
        anterior = self._buscar_espacio(cita["espacio_id"])
        copia_cita = dict(cita)
        copia_historial = list(cita.get("historial", []))
        try:
            if anterior:
                anterior["estado"] = ESTADO_DISPONIBLE
            nuevo["estado"] = ESTADO_ESPACIO_OCUPADO
            self.cita_repo.reprogramar_cita(cita_id, nuevo)
            self.cita_repo.registrar_auditoria(
                cita_id, "REPROGRAMAR", {"espacio_nuevo": nuevo["espacio_id"]}
            )
        except Exception:
            cita.clear()
            cita.update(copia_cita)
            cita["historial"] = copia_historial
            if anterior:
                anterior["estado"] = ESTADO_ESPACIO_OCUPADO
            nuevo["estado"] = ESTADO_DISPONIBLE
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=MENSAJE_503_MODIFICAR_CITA,
            )

        return CitaReprogramadaAPIResponse(
            mensaje="Operación exitosa: Reprogramar una cita médica",
            data=CitaReprogramadaData(
                cita_id=cita_id,
                estado=cita["estado"],
                nuevo_espacio_id=datos.nuevo_espacio_id,
            ),
            success=True,
        )

    # FUN-28: cancelar una cita médica
    def cancelar_cita(
        self, cita_id: str, datos: CancelarCitaRequest
    ) -> CitaCanceladaAPIResponse:
        cita = self._cita_a_modificar(cita_id, MENSAJE_503_MODIFICAR_CITA)
        self._validar_modificable(cita)

        espacio = self._buscar_espacio(cita["espacio_id"])
        copia_cita = dict(cita)
        copia_historial = list(cita.get("historial", []))
        try:
            if espacio:
                espacio["estado"] = ESTADO_DISPONIBLE
            self.cita_repo.cancelar_cita(cita_id, datos.motivo)
            self.cita_repo.registrar_auditoria(
                cita_id, "CANCELAR", {"motivo": datos.motivo}
            )
        except Exception:
            cita.clear()
            cita.update(copia_cita)
            cita["historial"] = copia_historial
            if espacio:
                espacio["estado"] = ESTADO_ESPACIO_OCUPADO
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=MENSAJE_503_MODIFICAR_CITA,
            )

        return CitaCanceladaAPIResponse(
            mensaje="Operación exitosa: Cancelar una cita médica",
            data=CitaCanceladaData(
                cita_id=cita_id,
                estado=cita["estado"],
                espacio_liberado=espacio is not None,
            ),
            success=True,
        )

    # FUN-29: confirmar la llegada del paciente (check-in)
    def registrar_checkin(self, cita_id: str) -> CheckinAPIResponse:
        cita = self._cita_a_modificar(cita_id, MENSAJE_503_CHECKIN)
        # Una cita cancelada se trata como inexistente (no es una cita activa)
        if cita["estado"] == ESTADO_CITA_CANCELADA:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró una cita activa con el identificador indicado",
            )
        try:
            validar_estado_reservada(cita["estado"])
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

        momento = ahora()
        try:
            validar_dia_checkin(cita, momento)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        copia_cita = dict(cita)
        try:
            self.cita_repo.registrar_checkin(cita_id, momento)
            self.cita_repo.notificar_consola_medico(cita)
        except Exception:
            cita.clear()
            cita.update(copia_cita)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=MENSAJE_503_CHECKIN,
            )

        return CheckinAPIResponse(
            mensaje="Operación exitosa: Confirmar la llegada del paciente",
            data=CheckinData(
                cita_id=cita_id,
                estado=cita["estado"],
                hora_llegada=cita["hora_llegada"],
            ),
            success=True,
        )
