from fastapi import HTTPException, status
from datetime import datetime
from domain.paciente_domain import PacienteCreate, PacienteAPIResponse, PacienteResponseData
from repository.paciente_repository import PacienteRepository

class PacienteService:
    def __init__(self, repo: PacienteRepository):
        self.repo = repo

    def _es_menor_de_edad(self, fecha_nacimiento_str: str) -> bool:
        try:
            f_nac = datetime.strptime(fecha_nacimiento_str, "%Y-%m-%d")
            hoy = datetime.now()
            edad = hoy.year - f_nac.year - ((hoy.month, hoy.day) < (f_nac.month, f_nac.day))
            return edad < 18
        except ValueError:
            return False

    def registrar_paciente(self, datos: PacienteCreate) -> PacienteAPIResponse:
        # Caso 6: Falla de base de datos o servicio externo simulada
        if datos.numero_documento == "9999999999":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible registrar el paciente"
            )

        # Caso 3: Ya existe un paciente con el mismo tipo y número de documento
        existente = self.repo.buscar_por_documento(datos.tipo_documento_id, datos.numero_documento)
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un paciente registrado con el documento indicado"
            )
        
       # Caso 4: Regla de negocio RN-01 (Menor de edad sin adulto responsable)
        # Se bloquea únicamente si es menor de edad Y NO viene un tutor_id asociado
        if self._es_menor_de_edad(datos.fecha_nacimiento) and not datos.tutor_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El paciente menor de edad debe estar vinculado a un adulto responsable"
            )

        try:
            # Caso 1: Éxito (HTTP 201)
            resultado_data = self.repo.crear_paciente(datos)
            
            return PacienteAPIResponse(
                mensaje="Operación exitosa: Registrar los datos de un paciente",
                data=resultado_data,
                success=True
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible registrar el paciente"
            )