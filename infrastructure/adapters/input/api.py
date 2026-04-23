"""
Adaptador de entrada: FastAPI HTTP Controllers.
Expone los casos de uso como endpoints REST.
"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.use_cases.use_cases import (
    GestionarExperimento,
    MonitorearAmbiente,
    ObtenerEstadoHuerto,
)
from backend.domain.entities.sensor_reading import Experimento, LecturaSensor
from backend.domain.ports.ports import SensorPublisher
from backend.infrastructure.adapters.input.mqtt_adapter import MQTTSensorAdapter
from backend.infrastructure.adapters.output.motor_ia import crear_motor
from backend.infrastructure.adapters.output.repositories import (
    AlertaRepositoryPostgres,
    ExperimentoRepositoryPostgres,
    SensorRepositoryPostgres,
    crear_engine,
    crear_session_factory,
    inicializar_tablas,
)
from backend.config import Settings

settings = Settings()

engine = crear_engine(settings.DATABASE_URL)
SessionFactory = crear_session_factory(engine)


# ── Dependency injection ──────────────────────────────────────────────────────

async def get_session() -> AsyncSession:
    async with SessionFactory() as session:
        yield session


def get_motor_ia():
    return crear_motor(0)   # En producción consultar conteo real de BD


# ── Publisher observable ──────────────────────────────────────────────────────

class SensorEventPublisher(SensorPublisher):
    """Recibe lecturas del MQTT y dispara el caso de uso MonitorearAmbiente."""

    def __init__(self):
        self._use_case: MonitorearAmbiente | None = None

    def registrar_use_case(self, uc: MonitorearAmbiente):
        self._use_case = uc

    async def publicar(self, lectura: LecturaSensor) -> None:
        if self._use_case:
            await self._use_case.ejecutar(lectura)


publisher = SensorEventPublisher()


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await inicializar_tablas(engine)

    loop = asyncio.get_event_loop()
    mqtt_adapter = MQTTSensorAdapter(
        broker_host=settings.MQTT_HOST,
        broker_port=settings.MQTT_PORT,
        publisher=publisher,
        loop=loop,
    )
    mqtt_adapter.iniciar()
    app.state.mqtt = mqtt_adapter

    yield

    mqtt_adapter.detener()
    await engine.dispose()


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="SmartGardenSchool API",
    description="Sistema de huerto inteligente escolar — Arquitectura Hexagonal",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas Pydantic ──────────────────────────────────────────────────────────

class LecturaRequest(BaseModel):
    temperatura: float = Field(..., ge=-10, le=60)
    humedad_suelo: float = Field(..., ge=0, le=100)
    humedad_ambiental: float = Field(..., ge=0, le=100)
    luminosidad: float = Field(..., ge=0, le=100_000)


class ExperimentoRequest(BaseModel):
    titulo: str = Field(..., min_length=3, max_length=200)
    descripcion: str
    estudiante: str = Field(..., min_length=2, max_length=150)
    observaciones: str = ""


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/lecturas", status_code=201, tags=["Sensores"])
async def registrar_lectura(
    body: LecturaRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Registra manualmente una lectura de sensor.
    (El flujo normal llega por MQTT desde el ESP32.)
    """
    lectura = LecturaSensor(
        temperatura=body.temperatura,
        humedad_suelo=body.humedad_suelo,
        humedad_ambiental=body.humedad_ambiental,
        luminosidad=body.luminosidad,
    )
    uc = MonitorearAmbiente(
        sensor_repo=SensorRepositoryPostgres(session),
        alerta_repo=AlertaRepositoryPostgres(session),
        motor_ia=get_motor_ia(),
    )
    lectura_guardada, recomendaciones, alertas = await uc.ejecutar(lectura)
    return {
        "lectura": lectura_guardada,
        "recomendaciones": recomendaciones,
        "alertas_generadas": alertas,
    }


@app.get("/huerto/estado", tags=["Dashboard"])
async def estado_huerto(session: AsyncSession = Depends(get_session)):
    """
    Devuelve la última lectura, historial, alertas activas y predicción de humedad.
    Fuente de verdad oficial del contrato — congelado durante sprints activos.
    """
    uc = ObtenerEstadoHuerto(
        sensor_repo=SensorRepositoryPostgres(session),
        alerta_repo=AlertaRepositoryPostgres(session),
        motor_ia=get_motor_ia(),
    )
    return await uc.ejecutar()


@app.get("/lecturas/historial", tags=["Sensores"])
async def historial(
    desde: datetime | None = None,
    hasta: datetime | None = None,
    session: AsyncSession = Depends(get_session),
):
    repo = SensorRepositoryPostgres(session)
    if desde and hasta:
        return await repo.obtener_por_rango(desde, hasta)
    return await repo.obtener_ultimas(50)


@app.get("/alertas", tags=["Alertas"])
async def listar_alertas(session: AsyncSession = Depends(get_session)):
    repo = AlertaRepositoryPostgres(session)
    return await repo.obtener_recientes(20)


@app.post("/experimentos", status_code=201, tags=["STEAM"])
async def crear_experimento(
    body: ExperimentoRequest,
    session: AsyncSession = Depends(get_session),
):
    uc = GestionarExperimento(ExperimentoRepositoryPostgres(session))
    experimento = Experimento(
        titulo=body.titulo,
        descripcion=body.descripcion,
        estudiante=body.estudiante,
        observaciones=body.observaciones,
    )
    return await uc.crear(experimento)


@app.get("/experimentos", tags=["STEAM"])
async def listar_experimentos(session: AsyncSession = Depends(get_session)):
    uc = GestionarExperimento(ExperimentoRepositoryPostgres(session))
    return await uc.listar()


@app.get("/experimentos/{id}", tags=["STEAM"])
async def obtener_experimento(
    id: int, session: AsyncSession = Depends(get_session)
):
    uc = GestionarExperimento(ExperimentoRepositoryPostgres(session))
    exp = await uc.obtener(id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experimento no encontrado")
    return exp


@app.get("/health", tags=["Sistema"])
async def health():
    return {"status": "ok", "sistema": "SmartGardenSchool", "version": "1.0.0"}
