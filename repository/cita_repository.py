import uuid
from datetime import datetime

from domain.cita_domain import ESTADO_CITA_RESERVADA
from domain.cita_domain import ESTADO_CITA_CANCELADA
from domain.cita_domain import ESTADO_CITA_EN_SALA


class CitaRepository:
    # Base de datos en memoria para las citas médicas
    def __init__(self):
        self._db_citas = []
        # Eventos asíncronos de notificación emitidos al paciente
        self._eventos_notificacion = []
        # Auditoría de operaciones sobre las citas y mensajes a la consola del médico
        self._auditoria = []
        self._eventos_consola_medico = []
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

    # HU-019: la cita devuelta es el registro guardado (el servicio lo actualiza)
    def buscar_cita(self, cita_id: str):
        for cita in self._db_citas:
            if cita["cita_id"] == cita_id:
                return cita
        return None

    def reprogramar_cita(self, cita_id: str, espacio: dict) -> dict:
        cita = self.buscar_cita(cita_id)
        cita.setdefault("historial", []).append(
            {
                "accion": "REPROGRAMADA",
                "espacio_anterior": cita["espacio_id"],
                "espacio_nuevo": espacio["espacio_id"],
                "fecha_anterior": cita["fecha"],
                "hora_anterior": cita["hora_inicio"],
                "fecha_nueva": espacio["fecha"],
                "hora_nueva": espacio["hora_inicio"],
            }
        )
        for campo in ("espacio_id", "profesional_id", "sede_id", "especialidad_id",
                      "fecha", "hora_inicio", "hora_fin"):
            cita[campo] = espacio[campo]
        return cita

    def cancelar_cita(self, cita_id: str, motivo: str) -> dict:
        cita = self.buscar_cita(cita_id)
        cita.setdefault("historial", []).append(
            {"accion": "CANCELADA", "motivo": motivo, "espacio_anterior": cita["espacio_id"]}
        )
        cita["estado"] = ESTADO_CITA_CANCELADA
        cita["motivo_cancelacion"] = motivo
        return cita

    def registrar_auditoria(self, cita_id: str, accion: str, detalle: dict) -> None:
        self._auditoria.append(
            {
                "cita_id": cita_id,
                "accion": accion,
                "detalle": detalle,
                "fecha_registro": datetime.now().isoformat(timespec="seconds"),
            }
        )

    # HU-020: marca la llegada del paciente
    def registrar_checkin(self, cita_id: str, momento: datetime) -> dict:
        cita = self.buscar_cita(cita_id)
        cita["estado"] = ESTADO_CITA_EN_SALA
        cita["hora_llegada"] = momento.replace(microsecond=0).isoformat()
        return cita

    # HU-020: mensaje a la consola del profesional asignado
    def notificar_consola_medico(self, cita: dict) -> None:
        self._eventos_consola_medico.append(
            {
                "evento": "PACIENTE_EN_SALA",
                "profesional_id": cita["profesional_id"],
                "cita_id": cita["cita_id"],
            }
        )
        print(f"[CONSOLA MEDICO] Paciente en sala para la cita {cita['cita_id']} (profesional {cita['profesional_id']}).")


cita_repository = CitaRepository()
