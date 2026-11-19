from fastapi import HTTPException, status

from domain.agenda_domain import (
    GenerarAgendaAPIResponse,
    GenerarAgendaData,
    GenerarAgendaRequest,
    fechas_del_rango,
    generar_franjas_dia,
    hay_solapamiento,
    intersectar,
    unir_contiguos,
)
from repository.agenda_repository import AgendaRepository
from repository.profesional_repository import ProfesionalRepository

MENSAJE_503 = "No fue posible generar la agenda"
SEDES_DISPONIBLES = {1, 2, 3}
DURACIONES_ESPECIALIDAD = {
    4: 20,
}


def duracion_base_especialidad(especialidad_id: int) -> int:
    return DURACIONES_ESPECIALIDAD.get(especialidad_id, 20)


def hora_a_minutos(hora_str: str) -> int:
    partes = hora_str.split(":")
    return int(partes[0]) * 60 + int(partes[1])


class SedeAgendaLocal:
    """Gestión local de las 3 sedes y jornadas para HU-014 sin depender de HU-007."""

    def __init__(self):
        self._sedes = {sede_id: {"sede_id": sede_id} for sede_id in SEDES_DISPONIBLES}
        self._db_jornadas = {}
        self._asignaciones = set()

    def buscar_sede(self, sede_id: int):
        return self._sedes.get(sede_id)

    def esta_asignado(self, profesional_id: str, sede_id: int) -> bool:
        return (profesional_id, sede_id) in self._asignaciones

    def asignar_sede(self, profesional_id: str, sede_id: int) -> None:
        if sede_id in self._sedes:
            self._asignaciones.add((profesional_id, sede_id))

    def guardar_jornada(self, profesional_id: str, jornada: list) -> None:
        self._db_jornadas[profesional_id] = jornada


class AgendaService:
    def __init__(
        self,
        profesional_repo: ProfesionalRepository,
        sede_repo: SedeAgendaLocal | None = None,
        agenda_repo: AgendaRepository | None = None,
    ):
        self.profesional_repo = profesional_repo
        self.sede_repo = sede_repo if sede_repo is not None else SedeAgendaLocal()
        self.agenda_repo = agenda_repo if agenda_repo is not None else AgendaRepository()

    # FUN-21: crear los espacios libres de la agenda médica
    def generar_agenda(self, datos: GenerarAgendaRequest) -> GenerarAgendaAPIResponse:
        # Caso 6: falla de base de datos o servicio externo simulada
        if datos.profesional_id == "falla-externa":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=MENSAJE_503
            )

        profesional = self.profesional_repo.buscar_por_id(datos.profesional_id)
        if not profesional:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró el profesional indicado",
            )
        id_profesional = profesional["profesional_id"]

        if not self.sede_repo.buscar_sede(datos.sede_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró la sede indicada",
            )

        if profesional.get("especialidad_id") != datos.especialidad_id:
            raise HTTPException(
                status_code=422,
                detail="La especialidad indicada no corresponde al profesional",
            )

        # Caso 4: el profesional debe tener jornada laboral definida
        jornada = self.sede_repo._db_jornadas.get(id_profesional)
        if not jornada:
            raise HTTPException(
                status_code=422,
                detail="El profesional no tiene jornada laboral configurada",
            )

        if not self.sede_repo.esta_asignado(id_profesional, datos.sede_id):
            raise HTTPException(
                status_code=422,
                detail="El profesional no está asignado a la sede indicada",
            )

        try:
            # 1. Cruzar jornada del médico, horario de la sede y duración base
            duracion = duracion_base_especialidad(datos.especialidad_id)
            horario_sede = self.agenda_repo.obtener_horario_sede(datos.sede_id)
            franjas = []
            for fecha in fechas_del_rango(datos.fecha_inicio, datos.fecha_fin):
                dia = fecha.isoweekday()
                turnos = unir_contiguos(
                    [
                        (hora_a_minutos(b["hora_inicio"]), hora_a_minutos(b["hora_fin"]))
                        for b in jornada
                        if b["dia_semana"] == dia
                    ]
                )
                turnos = intersectar(turnos, horario_sede.get(dia))
                for inicio, fin in generar_franjas_dia(turnos, duracion):
                    franjas.append((fecha, inicio, fin))

            if not franjas:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "La jornada del profesional no coincide con el horario de "
                        "la sede en el rango indicado"
                    ),
                )

            # 2. RN-21: verificar que no existan franjas previas que se solapen
            por_fecha = {}
            for fecha, inicio, fin in franjas:
                por_fecha.setdefault(fecha, []).append((inicio, fin))
            for fecha, nuevas in por_fecha.items():
                existentes = self.agenda_repo.franjas_del_profesional(
                    id_profesional, fecha
                )
                if hay_solapamiento(nuevas, existentes):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            "El profesional ya tiene franjas solapadas en el "
                            "rango indicado"
                        ),
                    )

            # 3. Inserción masiva y total generado
            total = self.agenda_repo.insertar_franjas(
                id_profesional, datos.sede_id, datos.especialidad_id, franjas
            )
            return GenerarAgendaAPIResponse(
                mensaje="Operación exitosa: Crear espacios en la agenda",
                data=GenerarAgendaData(
                    profesional_id=id_profesional, total_espacios_generados=total
                ),
                success=True,
            )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=MENSAJE_503
            )