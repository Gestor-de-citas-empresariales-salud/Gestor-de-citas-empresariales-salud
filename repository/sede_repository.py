from typing import Dict, List, Optional


class SedeRepository:
    def __init__(self) -> None:
        self._sedes: Dict[int, dict] = {
            1: {
                "sede_id": 1,
                "nombre": "Sede Principal",
                "direccion": "Calle 45 # 20-15",
                "ciudad": "Bucaramanga",
                "latitud": 7.1254,
                "longitud": -73.1198,
                "capacidad_maxima": 6,
                "tipo_sede": "GENERAL",
            },
            2: {
                "sede_id": 2,
                "nombre": "Sede Cañaveral",
                "direccion": "Cra 27 # 36-14",
                "ciudad": "Floridablanca",
                "latitud": 7.0622,
                "longitud": -73.0861,
                "capacidad_maxima": 2,
                "tipo_sede": "GENERAL",
            },
            3: {
                "sede_id": 3,
                "nombre": "Centro de Procedimientos Menores",
                "direccion": "Calle 36 # 18-24",
                "ciudad": "Bucaramanga",
                "latitud": 7.1189,
                "longitud": -73.1245,
                "capacidad_maxima": 4,
                "tipo_sede": "PROCEDIMIENTOS_MENORES",
            },
        }
        self._consultorios: Dict[int, dict] = {
            25: {
                "consultorio_id": 25,
                "sede_id": 1,
                "codigo": "C-101",
                "tipo": "CONSULTA_EXTERNA",
            },
            26: {
                "consultorio_id": 26,
                "sede_id": 1,
                "codigo": "C-102",
                "tipo": "CONSULTA_EXTERNA",
            },
            27: {
                "consultorio_id": 27,
                "sede_id": 1,
                "codigo": "C-103",
                "tipo": "OFICINA",
            },
            28: {
                "consultorio_id": 28,
                "sede_id": 2,
                "codigo": "C-201",
                "tipo": "CONSULTA_EXTERNA",
            },
            29: {
                "consultorio_id": 29,
                "sede_id": 2,
                "codigo": "C-202",
                "tipo": "CONSULTA_EXTERNA",
            },
            30: {
                "consultorio_id": 30,
                "sede_id": 3,
                "codigo": "PM-301",
                "tipo": "PROCEDIMIENTOS_MENORES",
            },
        }
        self._siguiente_sede_id: int = 4
        self._siguiente_consultorio_id: int = 31
        self._simular_falla_bd: bool = False

    def configurar_falla_bd(self, falla_activa: bool) -> None:
        self._simular_falla_bd = falla_activa

    def _verificar_disponibilidad(self) -> None:
        if self._simular_falla_bd:
            raise RuntimeError("No fue posible registrar la sede o el consultorio")

    def obtener_sedes_existentes(self) -> List[dict]:
        self._verificar_disponibilidad()
        return list(self._sedes.values())

    def obtener_sede_por_id(self, sede_id: int) -> Optional[dict]:
        self._verificar_disponibilidad()
        if sede_id == 99999999:
            raise RuntimeError("No fue posible registrar la sede o el consultorio")
        return self._sedes.get(sede_id)

    def crear_sede(
        self,
        nombre: str,
        direccion: str,
        ciudad: str,
        latitud: float,
        longitud: float,
        capacidad_maxima: int = 10,
        tipo_sede: str = "GENERAL",
    ) -> dict:
        self._verificar_disponibilidad()

        if (
            nombre.strip().lower() == "falla-db"
            or direccion.strip().lower() == "falla-db"
        ):
            raise RuntimeError("No fue posible registrar la sede o el consultorio")

        sede_id = self._siguiente_sede_id
        self._siguiente_sede_id += 1

        registro = {
            "sede_id": sede_id,
            "nombre": nombre,
            "direccion": direccion,
            "ciudad": ciudad,
            "latitud": latitud,
            "longitud": longitud,
            "capacidad_maxima": capacidad_maxima,
            "tipo_sede": tipo_sede,
        }
        self._sedes[sede_id] = registro
        return dict(registro)

    def contar_consultorios_sede(self, sede_id: int) -> int:
        self._verificar_disponibilidad()
        total = 0
        for consultorio in self._consultorios.values():
            if consultorio.get("sede_id") == sede_id:
                total += 1
        return total

    def tiene_consultorios_disponibles(self, sede_id: int) -> bool:
        sede = self.obtener_sede_por_id(sede_id)
        if not sede:
            return False
        actuales = self.contar_consultorios_sede(sede_id)
        capacidad = int(sede.get("capacidad_maxima", 0))
        return actuales < capacidad

    def crear_consultorio(
        self,
        sede_id: int,
        codigo: str,
        tipo: str,
    ) -> dict:
        self._verificar_disponibilidad()

        if codigo.strip().upper() == "FALLA-DB":
            raise RuntimeError("No fue posible registrar la sede o el consultorio")

        consultorio_id = self._siguiente_consultorio_id
        self._siguiente_consultorio_id += 1

        registro = {
            "consultorio_id": consultorio_id,
            "sede_id": sede_id,
            "codigo": codigo,
            "tipo": tipo,
        }
        self._consultorios[consultorio_id] = registro
        return dict(registro)


sede_repository = SedeRepository()
