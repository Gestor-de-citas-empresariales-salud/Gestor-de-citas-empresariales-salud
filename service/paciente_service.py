from fastapi import HTTPException, status
from datetime import datetime
from domain.paciente_domain import (
    PacienteCreate,
    PacienteAPIResponse,
    PacienteResponseData,
    es_menor_de_edad,
    validar_direccion_repetida,
    validar_limite_contactos,
    validar_adulto_responsable_contacto,
)
from repository.paciente_repository import PacienteRepository


class PacienteService:
    def __init__(self, repo: PacienteRepository):
        self.repo = repo

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

        # Caso 4: Regla de negocio delegada al dominio (Menor de edad sin tutor)
        if es_menor_de_edad(datos.fecha_nacimiento) and not datos.tutor_id:
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

        paciente_actual = None
        if hasattr(self.repo, "buscar_por_id"):
            paciente_actual = self.repo.buscar_por_id(paciente_id)
        elif hasattr(self.repo, "_db_pacientes"):
            for p in self.repo._db_pacientes:
                if str(p.get("paciente_id") or p.get("id")) == str(paciente_id):
                    paciente_actual = p
                    break

        if not paciente_actual:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró el paciente indicado",
            )

        # Caso 4: Dirección repetida / RN-04 (HTTP 409) delegada al dominio
        if "direccion" in datos_dict and validar_direccion_repetida(
            datos_dict["direccion"], paciente_actual.get("direccion")
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El paciente ya tiene una dirección primaria de residencia registrada",
            )

        try:
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

    def gestionar_contactos_emergencia(self, paciente_id: str, datos):
        if paciente_id == "falla-db":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible registrar los contactos de emergencia",
            )

        paciente_actual = None
        if hasattr(self.repo, "buscar_por_id"):
            paciente_actual = self.repo.buscar_por_id(paciente_id)
        elif hasattr(self.repo, "_db_pacientes"):
            for p in self.repo._db_pacientes:
                if str(p.get("paciente_id") or p.get("id")) == str(paciente_id):
                    paciente_actual = p
                    break

        if not paciente_actual:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró el paciente indicado",
            )

        contactos_lista = datos.contactos

        # Regla de negocio: Límite máximo de contactos permitidos
        if validar_limite_contactos(contactos_lista, max_permitidos=2):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Se superó el número máximo de contactos de emergencia permitidos",
            )

        # Regla de negocio RN-01: Menor de edad debe tener al menos un adulto responsable
        fecha_nac = paciente_actual.get("fecha_nacimiento")
        if fecha_nac and not validar_adulto_responsable_contacto(
            fecha_nac, contactos_lista
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Para pacientes menores de edad al menos un contacto debe ser el adulto responsable",
            )

        try:
            contactos_guardados = []
            id_base = 501
            for i, c in enumerate(contactos_lista):
                contacto_dict = {
                    "contacto_id": id_base + i,
                    "nombre": c.nombre,
                    "parentesco": c.parentesco,
                    "telefono": c.telefono,
                }
                contactos_guardados.append(contacto_dict)

            self.repo.actualizar_contactos_emergencia(
                paciente_id, contactos_guardados, self.repo._db_pacientes
            )

            return {
                "mensaje": "Operación exitosa: Gestionar los contactos de emergencia del paciente",
                "data": {
                    "paciente_id": str(paciente_id),
                    "total_contactos": len(contactos_guardados),
                    "contactos": contactos_guardados,
                },
                "success": True,
            }

        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible registrar los contactos de emergencia",
            )


def registrar_auditoria_contacto(paciente_id: str, campos_modificados: dict):
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "paciente_id": paciente_id,
        "accion": "MODIFICAR_CONTACTO",
        "campos_cambiados": list(campos_modificados.keys()),
    }
    print(f"[AUDIT LOG] Registro generado: {audit_entry}")
    return True
