import uuid
from domain.profesional_domain import ProfesionalCreate


class ProfesionalRepository:
    # Base de datos en memoria inicial para profesionales
    def __init__(self):

        self._db_profesionales = [
            {
                "profesional_id": "7d2e9a40-1c11-4a3e-8f55-0e2b7c6d1a22",
                "tipo_documento_id": 1,
                "numero_documento": "91234567",
                "nombres": "Andrés",
                "apellidos": "Pérez",
                "tarjeta_profesional": "TP-123456",
                "especialidad_id": 4,
                "email": "andres.perez@clinica.com",
                "estado": "PENDIENTE_VALIDACION",
                "activo": False,
                "estado_rethus": None,
                "codigo_verificacion": None,
            },
            {
                "profesional_id": "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
                "tipo_documento_id": 1,
                "numero_documento": "1098770654",
                "nombres": "María Fernanda",
                "apellidos": "Rodriguez",
                "tarjeta_profesional": "TP-166671",
                "especialidad_id": 2,
                "email": "mafer@clinica.com",
                "estado": "PENDIENTE_VALIDACION",
                "activo": False,
                "estado_rethus": None,
                "codigo_verificacion": None,
            },
            {
                "profesional_id": "b3c1f1de-5a1e-4f0b-9d3a-2f7b1c9e8a10",
                "tipo_documento_id": 1,
                "numero_documento": "1097887563",
                "nombres": "Laura",
                "apellidos": "Pedraza",
                "tarjeta_profesional": "TP-156678",
                "especialidad_id": 4,
                "email": "lalis@clinica.com",
                "estado": "PENDIENTE_VALIDACION",
                "activo": False,
                "estado_rethus": None,
                "codigo_verificacion": None,
            },
        ]

    def buscar_por_tarjeta_profesional(self, tarjeta_profesional: str):
        for prof in self._db_profesionales:
            if prof["tarjeta_profesional"].lower() == tarjeta_profesional.lower():
                return prof
        return None

    def buscar_por_id(self, profesional_id: str):
        for prof in self._db_profesionales:
            if str(prof.get("profesional_id")) == str(profesional_id):
                return prof
        return None

    def crear_profesional(self, datos: ProfesionalCreate) -> dict:
        nuevo_id = str(uuid.uuid4())
        profesional_dict = datos.model_dump()
        profesional_dict["profesional_id"] = nuevo_id
        profesional_dict["estado"] = "PENDIENTE_VALIDACION"
        profesional_dict["activo"] = False
        profesional_dict["estado_rethus"] = None
        profesional_dict["codigo_verificacion"] = None

        self._db_profesionales.append(profesional_dict)
        return profesional_dict

    def actualizar_rethus(
        self,
        profesional_id: str,
        estado_rethus: str,
        codigo_verificacion: str,
        activo: bool,
    ):
        profesional = self.buscar_por_id(profesional_id)
        if not profesional:
            return None

        profesional["estado_rethus"] = estado_rethus
        profesional["codigo_verificacion"] = codigo_verificacion
        profesional["activo"] = activo
        profesional["estado"] = "HABILITADO" if activo else "INHABILITADO"
        return profesional

    def asignar_sede(self, profesional_id: str, sede_id: int):
        profesional = self.buscar_por_id(profesional_id)
        if not profesional:
            return None

        # Inicializamos lista de sedes si no existe
        if "sedes" not in profesional:
            profesional["sedes"] = []

        if sede_id not in profesional["sedes"]:
            profesional["sedes"].append(sede_id)

        return {"profesional_id": profesional_id, "sede_id": sede_id, "asignada": True}

    def guardar_jornada(self, profesional_id: str, bloques: list, horas_semanales: int):
        profesional = self.buscar_por_id(profesional_id)
        if not profesional:
            return None

        profesional["jornada_laboral"] = bloques
        profesional["horas_semanales"] = horas_semanales

        return {
            "profesional_id": profesional_id,
            "horas_semanales": horas_semanales,
            "agenda_notificada": True,
        }


profesional_repository = ProfesionalRepository()