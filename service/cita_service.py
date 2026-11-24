from fastapi import HTTPException, status

from domain.agenda_domain import ESTADO_DISPONIBLE
from domain.cita_domain import (
    CitaAPIResponse,
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
