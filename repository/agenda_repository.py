import uuid
from datetime import date

from domain.agenda_domain import (
    HORARIO_SEDE_POR_DEFECTO,
    fecha_publicacion,
    minutos_a_hora,
)


class AgendaRepository:
    # Base de datos en memoria para los espacios (franjas) de la agenda
    def __init__(self):
        self._db_franjas = []

    # Horario de atención de la sede: {dia ISO: (inicio_min, fin_min)}
    # PROVISIONAL: todas las sedes usan el mismo horario por defecto.
    def obtener_horario_sede(self, sede_id: int) -> dict:
        return HORARIO_SEDE_POR_DEFECTO

    # Franjas ya existentes del profesional en una fecha: [(inicio_min, fin_min)]
    def franjas_del_profesional(self, profesional_id: str, fecha: date) -> list:
        return [
            (f["_inicio_min"], f["_fin_min"])
            for f in self._db_franjas
            if f["profesional_id"] == profesional_id and f["fecha"] == fecha.isoformat()
        ]

    # Inserción masiva: recibe todas las franjas nuevas y las guarda de una vez.
    # `franjas` es una lista de (fecha, inicio_min, fin_min).
    def insertar_franjas(
        self, profesional_id: str, sede_id: int, especialidad_id: int, franjas: list
    ) -> int:
        nuevas = [
            {
                "espacio_id": str(uuid.uuid4()),
                "profesional_id": profesional_id,
                "sede_id": sede_id,
                "especialidad_id": especialidad_id,
                "fecha": fecha.isoformat(),
                "hora_inicio": minutos_a_hora(inicio),
                "hora_fin": minutos_a_hora(fin),
                "estado": "LIBRE",
                "publicar_desde": fecha_publicacion(fecha).isoformat(),
                "_inicio_min": inicio,
                "_fin_min": fin,
            }
            for fecha, inicio, fin in franjas
        ]
        self._db_franjas.extend(nuevas)
        return len(nuevas)


agenda_repository = AgendaRepository()
