from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class CultivoEstado(str, Enum):
    OPTIMO = "optimo"
    ALERTA = "alerta"
    CRITICO = "critico"


@dataclass
class LecturaSensor:
    """Entidad core del dominio — no depende de ninguna tecnología externa."""
    temperatura: float        # °C
    humedad_suelo: float      # % (0-100)
    humedad_ambiental: float  # % (0-100)
    luminosidad: float        # lux
    timestamp: datetime = field(default_factory=datetime.utcnow)
    id: int | None = None

    def es_valida(self) -> bool:
        return (
            -10 <= self.temperatura <= 60
            and 0 <= self.humedad_suelo <= 100
            and 0 <= self.humedad_ambiental <= 100
            and 0 <= self.luminosidad <= 100_000
        )


@dataclass
class Alerta:
    tipo: str           # "riego_urgente" | "temperatura_alta" | "luz_baja"
    mensaje: str
    prioridad: str      # "alta" | "media" | "baja"
    lectura_id: int | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    id: int | None = None


@dataclass
class Recomendacion:
    accion: str
    razon: str
    confianza: float    # 0.0 – 1.0
    fuente: str         # "reglas" | "ml"
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Experimento:
    titulo: str
    descripcion: str
    estudiante: str
    fecha_inicio: datetime = field(default_factory=datetime.utcnow)
    fecha_fin: datetime | None = None
    observaciones: str = ""
    id: int | None = None
