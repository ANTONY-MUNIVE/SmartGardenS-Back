"""
Puertos del dominio (contratos abstractos).
Ninguna clase aquí importa tecnologías externas.
Todo apunta al centro — el dominio no conoce a nadie.
"""
from abc import ABC, abstractmethod
from datetime import datetime

from backend.domain.entities.sensor_reading import (
    Alerta,
    Experimento,
    LecturaSensor,
    Recomendacion,
)


# ── Puertos de SALIDA (driven) ────────────────────────────────────────────────

class SensorRepository(ABC):
    @abstractmethod
    async def guardar(self, lectura: LecturaSensor) -> LecturaSensor: ...

    @abstractmethod
    async def obtener_ultimas(self, n: int = 20) -> list[LecturaSensor]: ...

    @abstractmethod
    async def obtener_por_rango(
        self, desde: datetime, hasta: datetime
    ) -> list[LecturaSensor]: ...


class AlertaRepository(ABC):
    @abstractmethod
    async def guardar(self, alerta: Alerta) -> Alerta: ...

    @abstractmethod
    async def obtener_recientes(self, n: int = 10) -> list[Alerta]: ...


class ExperimentoRepository(ABC):
    @abstractmethod
    async def guardar(self, experimento: Experimento) -> Experimento: ...

    @abstractmethod
    async def listar(self) -> list[Experimento]: ...

    @abstractmethod
    async def obtener_por_id(self, id: int) -> Experimento | None: ...


class MotorIA(ABC):
    """Puerto hacia cualquier implementación de IA (reglas o ML)."""
    @abstractmethod
    def analizar(self, lectura: LecturaSensor) -> list[Recomendacion]: ...

    @abstractmethod
    def predecir_humedad(
        self, historial: list[LecturaSensor]
    ) -> float | None: ...


# ── Puertos de ENTRADA (driving) ─────────────────────────────────────────────

class SensorPublisher(ABC):
    """Contrato para publicar eventos cuando llega una lectura nueva."""
    @abstractmethod
    async def publicar(self, lectura: LecturaSensor) -> None: ...
