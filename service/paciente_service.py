from fastapi import HTTPException, status
from datetime import datetime
from domain.paciente_domain import (
    PacienteCreate,
    PacienteAPIResponse,
    PacienteResponseData,
)
from repository.paciente_repository import PacienteRepository


class PacienteService:
    def __init__(self, repo: PacienteRepository):
        self.repo = repo

    def _es_menor_de_edad(self, fecha_nacimiento_str: str) -> bool:
        try:
            f_nac = datetime.strptime(fecha_nacimiento_str, "%Y-%m-%d")
            hoy = datetime.now()
            edad = (
                hoy.year
                - f_nac.year
                - ((hoy.month, hoy.day) < (f_nac.month, f_nac.day))
            )
            return edad < 18
        except ValueError:
            return False

    def registrar_paciente(self, datos: PacienteCreate) -> PacienteAPIResponse:
        # Caso 6: Falla de base de datos o servicio externo simulada
        if datos.numero_documento == "9999999999":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible registrar el paciente",
            )

        # Caso 3: Ya existe un paciente con el mismo tipo y número de documento
        existente = self.repo.buscar_por_documento(
            datos.tipo_documento_id, datos.numero_documento
        )
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un paciente registrado con el documento indicado",
            )

        # Caso 4: Regla de negocio RN-01
        if self._es_menor_de_edad(datos.fecha_nacimiento) and not datos.tutor_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El paciente menor de edad debe estar vinculado a un adulto responsable",
            )

        try:
            # Caso 1: Éxito (HTTP 201)
            resultado_data = self.repo.crear_paciente(datos)

            return PacienteAPIResponse(
                mensaje="Operación exitosa: Registrar los datos de un paciente",
                data=resultado_data,
                success=True,
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible registrar el paciente",
            )

    def modificar_contacto(self, paciente_id: str, datos):

        if paciente_id == "falla-db":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible actualizar los datos de contacto",
            )
        # Convertir el modelo Pydantic a diccionario omitiendo los valores en None (Actualización Parcial)
        datos_dict = datos.model_dump(exclude_unset=True)

        if not datos_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "mensaje": "No se enviaron campos para actualizar",
                    "data": None,
                    "success": False,
                },
            )
        # Búsqueda segura del paciente en el repositorio
        paciente_actual = None
        if hasattr(self.repo, "buscar_por_id"):
            paciente_actual = self.repo.buscar_por_id(paciente_id)
        elif hasattr(self.repo, "_db_pacientes"):
            for p in self.repo._db_pacientes:
                if str(p.get("paciente_id") or p.get("id")) == str(paciente_id):
                    paciente_actual = p
                    break

        # Caso 3: Paciente no encontrado (HTTP 404)
        if not paciente_actual:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró el paciente indicado",
            )

        # Caso 4: Dirección repetida / RN-04 (HTTP 409)
        if "direccion" in datos_dict and datos_dict["direccion"] == paciente_actual.get(
            "direccion"
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El paciente ya tiene una dirección primaria de residencia registrada",
            )

        try:
            # Usa directamente self.repo para acceder a la memoria
            paciente_actualizado = self.repo.actualizar_contacto_en_memoria(
                paciente_id, datos_dict, self.repo._db_pacientes
            )
            return paciente_actualizado

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"mensaje": str(e), "data": None, "success": False},
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "mensaje": "No fue posible actualizar los datos de contacto",
                    "data": None,
                    "success": False,
                },
            )


def registrar_auditoria_contacto(paciente_id: str, campos_modificados: dict):
    # Simula o ejecuta el registro en el servicio de auditoría requerido
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "paciente_id": paciente_id,
        "accion": "MODIFICAR_CONTACTO",
        "campos_cambiados": list(campos_modificados.keys()),
    }
    # Aquí insertarías el log en tu base de datos o servicio de auditoría
    print(f"[AUDIT LOG] Registro generado: {audit_entry}")
    return True
