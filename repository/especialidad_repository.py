from typing import Dict, List, Optional
from domain.especialidad_domain import CATALOGO_CUPS_VIGENTES


class EspecialidadRepository:
    def __init__(self) -> None:
        self._especialidades: Dict[int, dict] = {
            1: {
                "especialidad_id": 1,
                "nombre": "Medicina Interna",
                "descripcion": "Atención médica integral de adultos",
                "alta_complejidad": False,
            },
            2: {
                "especialidad_id": 2,
                "nombre": "Pediatría",
                "descripcion": "Atención médica infantil y del adolescente",
                "alta_complejidad": False,
            },
            3: {
                "especialidad_id": 3,
                "nombre": "Ginecología y Obstetricia",
                "descripcion": "Salud femenina, control prenatal y obstetricia",
                "alta_complejidad": False,
            },
            4: {
                "especialidad_id": 4,
                "nombre": "Cirugía General",
                "descripcion": "Procedimientos quirúrgicos generales",
                "alta_complejidad": True,
            },
            5: {
                "especialidad_id": 5,
                "nombre": "Ortopedia y Traumatología",
                "descripcion": "Atención del sistema musculoesquelético y traumas",
                "alta_complejidad": False,
            },
            6: {
                "especialidad_id": 6,
                "nombre": "Medicina Familiar",
                "descripcion": "Atención primaria y seguimiento integral familiar",
                "alta_complejidad": False,
            },
            7: {
                "especialidad_id": 7,
                "nombre": "Dermatología",
                "descripcion": "Diagnóstico y tratamiento de enfermedades de la piel",
                "alta_complejidad": False,
            },
            8: {
                "especialidad_id": 8,
                "nombre": "Oftalmología",
                "descripcion": "Salud visual y patologías oculares",
                "alta_complejidad": False,
            },
            9: {
                "especialidad_id": 9,
                "nombre": "Otorrinolaringología",
                "descripcion": "Atención de oído, nariz y garganta",
                "alta_complejidad": False,
            },
            10: {
                "especialidad_id": 10,
                "nombre": "Neurología",
                "descripcion": "Trastornos del sistema nervioso central y periférico",
                "alta_complejidad": True,
            },
        }
        self._cups_por_especialidad: Dict[int, List[str]] = {
            1: ["890201"],
            2: ["890301"],
            3: ["890281"],
            4: ["890401"],
            5: ["890201"],
            6: ["890201"],
            7: ["890201"],
            8: ["890201"],
            9: ["890201"],
            10: ["890381"],
        }

        self._catalogo_cups: Dict[str, bool] = dict(CATALOGO_CUPS_VIGENTES)
        self._siguiente_id: int = 11
        self._simular_falla_bd: bool = False

    def configurar_falla_bd(self, falla_activa: bool) -> None:
        self._simular_falla_bd = falla_activa

    def _verificar_disponibilidad(self) -> None:
        if self._simular_falla_bd:
            raise RuntimeError("No fue posible registrar la especialidad")

    def obtener_nombres_especialidades(self) -> List[str]:
        self._verificar_disponibilidad()
        return [esp["nombre"] for esp in self._especialidades.values()]

    def crear_especialidad(
        self,
        nombre: str,
        descripcion: Optional[str],
        alta_complejidad: bool,
    ) -> dict:
        self._verificar_disponibilidad()

        if nombre.strip().lower() == "falla-db":
            raise RuntimeError("No fue posible registrar la especialidad")

        especialidad_id = self._siguiente_id
        self._siguiente_id += 1

        registro = {
            "especialidad_id": especialidad_id,
            "nombre": nombre,
            "descripcion": descripcion,
            "alta_complejidad": alta_complejidad,
        }
        self._especialidades[especialidad_id] = registro
        self._cups_por_especialidad[especialidad_id] = []
        return registro

    def obtener_especialidad_por_id(self, especialidad_id: int) -> Optional[dict]:
        self._verificar_disponibilidad()
        if especialidad_id == 99999999:
            raise RuntimeError("No fue posible registrar la especialidad")
        return self._especialidades.get(especialidad_id)

    def obtener_catalogo_cups(self) -> Dict[str, bool]:
        self._verificar_disponibilidad()
        return self._catalogo_cups

    def asociar_codigos_cups(
        self, especialidad_id: int, codigos_cups: List[str]
    ) -> dict:
        self._verificar_disponibilidad()
        actuales = self._cups_por_especialidad.get(especialidad_id, [])

        for codigo in codigos_cups:
            if codigo not in actuales:
                actuales.append(codigo)

        self._cups_por_especialidad[especialidad_id] = actuales
        return {
            "especialidad_id": especialidad_id,
            "total_codigos": len(actuales),
            "codigos_cups": list(actuales),
        }
