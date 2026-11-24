import uuid

from domain.cita_domain import ESTADO_CITA_RESERVADA


class CitaRepository:
    # Base de datos en memoria para las citas médicas
    def __init__(self):
        self._db_citas = []
        # Eventos asíncronos de notificación emitidos al paciente
        self._eventos_notificacion = []
        # PROVISIONAL: los módulos de inasistencias (MOD-06) y de cobertura
        # (MOD-08) aún no existen. Carlos Pérez tiene 3 inasistencias
        # injustificadas y el convenio EPS de Ana María está suspendido.
        self._inasistencias_injustificadas = {
            "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d": 3
        }
        self._convenios_eps_suspendidos = {"f5e4d3c2-1b0a-9f8e-7d6c-5b4a3f2e1d0c"}

    def contar_inasistencias_injustificadas(self, paciente_id: str) -> int:
        return self._inasistencias_injustificadas.get(paciente_id, 0)

    def convenio_eps_suspendido(self, paciente_id: str) -> bool:
        return paciente_id in self._convenios_eps_suspendidos

    def crear_cita(self, paciente_id: str, espacio: dict) -> dict:
        cita = {
            "cita_id": str(uuid.uuid4()),
            "paciente_id": paciente_id,
            "espacio_id": espacio["espacio_id"],
            "profesional_id": espacio["profesional_id"],
            "sede_id": espacio["sede_id"],
            "especialidad_id": espacio["especialidad_id"],
            "fecha": espacio["fecha"],
            "hora_inicio": espacio["hora_inicio"],
            "hora_fin": espacio["hora_fin"],
            "estado": ESTADO_CITA_RESERVADA,
        }
        self._db_citas.append(cita)
        return dict(cita)

    def eliminar_cita(self, cita_id: str) -> None:
        self._db_citas = [c for c in self._db_citas if c["cita_id"] != cita_id]

    def emitir_evento_notificacion(self, cita: dict) -> None:
        self._eventos_notificacion.append(
            {"evento": "CITA_RESERVADA", "cita_id": cita["cita_id"],
             "paciente_id": cita["paciente_id"]}
        )
        print(f"[NOTIFICACION] Cita {cita['cita_id']} reservada para el paciente {cita['paciente_id']}.")


cita_repository = CitaRepository()
