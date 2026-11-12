import uuid
from domain.paciente_domain import PacienteCreate, PacienteResponseData

class PacienteRepository:
    def __init__(self):
        # 3 pacientes iniciales de prueba en memoria
        self._db_pacientes = [
            {
                "paciente_id": "b3c1f1de-5a1e-4f0b-9d3a-2f7b1c9e8a10",
                "tipo_documento_id": 1,
                "numero_documento": "1098765432",
                "nombres": "Laura",
                "apellidos": "Gómez Ríos",
                "fecha_nacimiento": "1995-04-12",
                "genero_id": 2,
                "email": "laura@correo.com",
                "telefono": "3001234567",
                "direccion": "Cra 27 # 10-15",
                "password": "hashedpassword"
            },
            {
                "paciente_id": "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
                "tipo_documento_id": 1,
                "numero_documento": "1012345678",
                "nombres": "Carlos",
                "apellidos": "Pérez Silva",
                "fecha_nacimiento": "1990-08-20",
                "genero_id": 1,
                "email": "carlos.perez@correo.com",
                "telefono": "3109876543",
                "direccion": "Calle 50 # 25-30",
                "password": "hashedpassword"
            },
            {
                "paciente_id": "f5e4d3c2-1b0a-9f8e-7d6c-5b4a3f2e1d0c",
                "tipo_documento_id": 2,
                "numero_documento": "987654321",
                "nombres": "Ana María",
                "apellidos": "Rodríguez",
                "fecha_nacimiento": "2005-12-05",
                "genero_id": 2,
                "email": "ana.rodriguez@correo.com",
                "telefono": "3201112233",
                "direccion": "Avenida iva 15",
                "password": "hashedpassword"
            }
        ]

    def buscar_por_documento(self, tipo_id: int, num_doc: str):
        for p in self._db_pacientes:
            if p["tipo_documento_id"] == tipo_id and p["numero_documento"] == num_doc:
                return p
        return None

    def crear_paciente(self, datos: PacienteCreate) -> PacienteResponseData:
        nuevo_id = str(uuid.uuid4())
        paciente_dict = datos.model_dump()
        paciente_dict["paciente_id"] = nuevo_id
        self._db_pacientes.append(paciente_dict)

        return PacienteResponseData(
            paciente_id=nuevo_id,
            numero_documento=datos.numero_documento,
            nombres=datos.nombres,
            apellidos=datos.apellidos,
            token_inicial="eyJhbGciOi..."
        )

paciente_repository = PacienteRepository()